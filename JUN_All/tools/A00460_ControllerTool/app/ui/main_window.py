# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00460_ControllerTool - Qt UI
#
# 키프레임 애니메이션용 컨트롤러를 제작자 편의에 맞춰 생성하는 in-Maya PySide 툴.
# 첫 기능은 FK — 리스트업한 조인트/오브젝트에 zro > con > ctl > tgt 계층을 만들고
# 조인트가 그 계층을 따라오게 컨스트레인트한다. 자세한 구조는 core/fk_manager.py 참고.
#
# 탭은 상위 = 카테고리, 하위 = 기능으로 두 단계다 (A00110_animTool_V02 · A00400 과 같은 규칙).
#   Create > FK   - 씬에 새 컨트롤러 계층을 만든다
# 지금은 하위가 FK 하나지만 하위 탭 바를 그대로 둔다 — 기능 이름이 화면에 남고,
# IK / Space Switch 같은 기능이 늘어도 구조가 그대로다.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00460_ControllerTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00460_ControllerTool.app.core import fk_manager as fk_mgr


WINDOW_OBJECT_NAME = "JUN_A00460_ControllerTool_window"

_WARN_COLOR = "#ffb454"


class MainWindow(QWidget):

    # ==================================================================
    # 탭 분류표 — 상위 탭 = 카테고리, 하위 탭 = 기능
    # 기준은 "씬에 무엇을 하는가" 다. (A00400_CurveTool 과 같은 규칙)
    # ==================================================================

    CREATE_PAGES = (
        ("FK",
         "FK - build a zro > con > ctl > tgt controller hierarchy for the "
         "listed joints and constrain the joints to it.",
         "_build_fk_tab"),
    )

    CATEGORIES = (
        ("Create", "Create - build new controller rigs in the scene",
         CREATE_PAGES, "create_tabs"),
    )

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Controller Tool v{0}".format(VERSION)
        self.resize(380, 640)

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        # 메뉴 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        # 로그창은 탭 빌더가 self.log 를 부를 수 있어 탭보다 먼저 만든다(둘이 공유).
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(120)

        self.tabs = QTabWidget()
        for label, tip, pages, attr in self.CATEGORIES:
            index = self.tabs.addTab(self._build_category_tab(pages, attr), label)
            self.tabs.setTabToolTip(index, tip)
        root.addWidget(self.tabs, 1)

        root.addWidget(self.te_log)

        self.lbl_copyright = QLabel(
            "Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_copyright)

        self.log("Controller Tool v{0} ({1}) ready. List joints and click "
                 "'Create FK Controls'.".format(VERSION, LAST_UPDATE))

    # --------------------------------------------------------------
    # 카테고리 상위 탭 / 기능 하위 탭
    # --------------------------------------------------------------

    def _build_category_tab(self, pages, attr):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = self._build_sub_tabs(pages)
        setattr(self, attr, tabs)
        layout.addWidget(tabs)

        return page

    def _build_sub_tabs(self, pages):
        tabs = QTabWidget()
        tabs.tabBar().setElideMode(Qt.ElideRight)
        for label, tip, builder in pages:
            index = tabs.addTab(getattr(self, builder)(), label)
            tabs.setTabToolTip(index, tip)
        return tabs

    # --------------------------------------------------------------
    # Create > FK
    # --------------------------------------------------------------

    def _build_fk_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        # ---------------- 대상 리스트 ----------------
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints / Objects",
            select_label="List Selected",
            show_reverse=True,
            log_callback=self.log)
        root.addWidget(self.tsl, 1)

        # ---------------- 대상 해석 모드 ----------------
        mode_box = QGroupBox("Mode")
        mode_row = QHBoxLayout(mode_box)
        self.mode_group = QButtonGroup(self)

        self.rb_root = QRadioButton("Bone Root")
        self.rb_root.setChecked(True)
        self.rb_root.setToolTip(
            "Each listed node is a chain ROOT: the controls are built for that\n"
            "node and every joint under it, following the scene hierarchy.\n"
            "Branches are handled - each child gets its own stack.")

        self.rb_chain = QRadioButton("Bone Chain")
        self.rb_chain.setToolTip(
            "The listed nodes are ONE chain: they are linked in LIST order,\n"
            "no matter how they sit in the scene (reorder with Up/Down).")

        self.mode_group.addButton(self.rb_root)
        self.mode_group.addButton(self.rb_chain)
        mode_row.addWidget(self.rb_root)
        mode_row.addWidget(self.rb_chain)
        mode_row.addStretch(1)
        root.addWidget(mode_box)

        # ---------------- 만들 노드 ----------------
        node_box = QGroupBox("Nodes to Build")
        node_lay = QVBoxLayout(node_box)

        node_row = QHBoxLayout()
        self.chk_zro = QCheckBox("zro")
        self.chk_zro.setChecked(True)
        self.chk_zro.setToolTip(
            "Zero-out null placed at the joint (position + rotation).")

        self.chk_con = QCheckBox("con")
        self.chk_con.setChecked(True)
        self.chk_con.setToolTip("Offset null between zro and ctl.")

        self.chk_tgt = QCheckBox("tgt")
        self.chk_tgt.setChecked(True)
        self.chk_tgt.setToolTip(
            "Null under the control. This is what constrains the joint,\n"
            "and the next joint's stack hangs from it.")

        for chk in (self.chk_zro, self.chk_con, self.chk_tgt):
            node_row.addWidget(chk)
        node_row.addStretch(1)
        node_lay.addLayout(node_row)

        lbl_ctl = QLabel("ctl (cube control curve) is always created.")
        lbl_ctl.setStyleSheet("color: {0};".format(_WARN_COLOR))
        node_lay.addWidget(lbl_ctl)

        # 컨트롤러 커브 크기.
        # 모양은 **정육면체 테두리** 고정이다(A00145_RigConnect Match 탭과 같은 CV 데이터).
        # 큐브는 90도 회전 대칭이라 축을 골라도 결과가 같으므로 Shape Axis 는 두지 않는다.
        shape_row = QHBoxLayout()
        shape_row.addWidget(QLabel("Control Size"))
        self.sb_size = QDoubleSpinBox()
        self.sb_size.setRange(0.001, 1000.0)
        self.sb_size.setDecimals(3)
        self.sb_size.setSingleStep(0.1)
        self.sb_size.setValue(fk_mgr.DEFAULT_SIZE)
        # 값을 되쓰지 않아도 타이핑 중 잘리는 것을 막는다.
        self.sb_size.setKeyboardTracking(False)
        self.sb_size.setToolTip(
            "Half the cube edge length - so 1.0 gives a cube reaching 1 unit\n"
            "from the joint in every direction (same feel as a radius).")
        shape_row.addWidget(self.sb_size)
        shape_row.addStretch(1)
        node_lay.addLayout(shape_row)

        root.addWidget(node_box)

        # ---------------- 컨스트레인트 ----------------
        con_box = QGroupBox("Constraint (joint follows the last node)")
        con_lay = QVBoxLayout(con_box)

        con_row = QHBoxLayout()
        self.chk_parent = QCheckBox("Parent")
        self.chk_parent.setChecked(True)
        self.chk_parent.setToolTip("parentConstraint - translate + rotate.")

        self.chk_point = QCheckBox("Point")
        self.chk_point.setToolTip("pointConstraint - translate only.")

        self.chk_orient = QCheckBox("Orient")
        self.chk_orient.setToolTip("orientConstraint - rotate only.")

        self.chk_scale = QCheckBox("Scale")
        self.chk_scale.setToolTip(
            "scaleConstraint - scale only. Parent does NOT drive scale,\n"
            "so add this if the controls need to scale the joints.")

        for chk in (self.chk_parent, self.chk_point,
                    self.chk_orient, self.chk_scale):
            con_row.addWidget(chk)
        con_row.addStretch(1)
        con_lay.addLayout(con_row)

        root.addWidget(con_box)

        # ---------------- 실행 ----------------
        self.btn_create = QPushButton("Create FK Controls")
        self.btn_create.setToolTip(
            "Build the controller hierarchy for the listed nodes and constrain\n"
            "them to it. One undo step.")
        self.btn_create.clicked.connect(self.on_create_fk)
        root.addWidget(self.btn_create)

        return tab

    # ==============================================================
    # actions
    # ==============================================================

    def _selected_constraints(self):
        types = []
        if self.chk_parent.isChecked():
            types.append(fk_mgr.CON_PARENT)
        if self.chk_point.isChecked():
            types.append(fk_mgr.CON_POINT)
        if self.chk_orient.isChecked():
            types.append(fk_mgr.CON_ORIENT)
        if self.chk_scale.isChecked():
            types.append(fk_mgr.CON_SCALE)
        return types

    def on_create_fk(self):
        nodes = self.tsl.get_all_nodes() or self.tsl.get_all_items()
        if not nodes:
            self.log("Nothing listed. Select joints in the scene and click "
                     "'List Selected'.", warn=True)
            return

        mode = fk_mgr.MODE_ROOT if self.rb_root.isChecked() else fk_mgr.MODE_CHAIN

        # 공용 undo_chunk 는 인자를 받지 않는다(Framework/core/maya_undo.py).
        # 마지막 select 도 **chunk 안에서** 한다 — 밖에서 하면 select 가 별도 undo
        # 스텝이 되어 Ctrl+Z 를 한 번 눌렀을 때 선택만 되돌아가고 컨트롤러는 남는다.
        with undo_chunk():
            result = fk_mgr.build_fk_controls(
                nodes,
                mode=mode,
                use_zro=self.chk_zro.isChecked(),
                use_con=self.chk_con.isChecked(),
                use_tgt=self.chk_tgt.isChecked(),
                constraints=self._selected_constraints(),
                size=self.sb_size.value(),
            )
            if result["roots"]:
                cmds.select(result["roots"], replace=True)

        self._report(result, mode)

    def _report(self, result, mode):
        for node in result["missing"]:
            self.log("Not in the scene, skipped: {0}".format(node), warn=True)

        for wanted, actual in result["renamed"]:
            self.log("Name '{0}' was taken - Maya used '{1}'.".format(
                wanted, actual), warn=True)

        for msg in result["warnings"]:
            self.log(msg, warn=True)

        controls = [c for c in result["controls"] if c]
        if not controls:
            self.log("Nothing was built.", warn=True)
            return

        self.log(
            "FK built ({0} mode): {1} control(s) over {2} joint(s), "
            "{3} root hierarchy(ies), {4} constraint node(s).".format(
                "Bone Root" if mode == fk_mgr.MODE_ROOT else "Bone Chain",
                len(controls), len(result["driven"]),
                len(result["roots"]), len(result["constraints"])))

    # ==============================================================
    # 공용
    # ==============================================================

    def log(self, message, warn=False):
        if warn:
            self.te_log.append(
                '<span style="color:{0};">{1}</span>'.format(
                    _WARN_COLOR, message))
        else:
            self.te_log.append(message)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Controller Tool\n"
            "Version {0}\n"
            "Last update {1}\n\n"
            "Build animation controllers.\n"
            "FK: <joint>_zro > _con > _ctl > _tgt, joint follows _tgt.\n"
            "Controls are cube outline curves.\n\n"
            "Python Script by Ji Hun Park".format(VERSION, LAST_UPDATE))
