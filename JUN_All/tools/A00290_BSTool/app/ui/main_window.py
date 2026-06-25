# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00290_BSTool - Qt UI (레거시 JUN_PY_BSTool_V01_01 의 PySide 재작성)
#
# 탭 구성:
#   1) Edit BS     : blendShape 노드 리스트 → 모든 타겟 키 / 타겟 메시 추출
#   2) Base Shape  : blendShape 의 타겟을 리스트업 → 선택 타겟의 weight=value 모양을
#                    weight=1.0 기본 모양으로 재정의(델타 스케일)

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00290_BSTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00290_BSTool.app.core import EditBSManager, BaseShapeManager
from tools.A00290_BSTool.app.core import blendshape_utils as bsu


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00290_BSTool_window"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 460
        self.win_height = 640
        self.win_title = f"BS Tool v{VERSION}"

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 탭
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_edit_bs_tab(), "Edit BS")
        self.tabs.addTab(self._build_base_shape_tab(), "Base Shape")
        main_layout.addWidget(self.tabs)

        # 공용 로그
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(80)
        self.te_log.setMaximumHeight(140)
        main_layout.addWidget(self.te_log)

        # 저작권
        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # ==================================================
    # Tab 1 : Edit BS
    # ==================================================

    def _build_edit_bs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # blendShape 노드 리스트 (씬 선택 연동)
        self.tsl_bs_nodes = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="BlendShape Nodes",
            select_label="Select BlendShape Nodes",
            log_callback=self.log)
        layout.addWidget(self.tsl_bs_nodes)

        # 동작 버튼
        btn_key = QPushButton("Key every target")
        btn_key.setToolTip(
            "Keyframe each target so it shows one at a time: frame i = 1, i-1/i+1 = 0.")
        btn_key.clicked.connect(self.on_key_every_target)
        layout.addWidget(btn_key)

        btn_copy = QPushButton("Copy every target")
        btn_copy.setToolTip(
            "Key every target, then duplicate the base mesh at each frame to extract\n"
            "each target shape as a mesh (visibility off), grouped under <node>_targets.")
        btn_copy.clicked.connect(self.on_copy_every_target)
        layout.addWidget(btn_copy)

        # --- Copy every frame (구간 베이크) ---------------------------------
        # 정해진 [Start, End] 구간을 1프레임마다 베이스 메시를 복제(visibility off).
        # 구간 입력 UI 는 A00110 Follow 탭의 Start/End + Get Current 패턴을 따른다.
        validator = QIntValidator(-1000000, 1000000, self)
        t_min = int(cmds.playbackOptions(query=True, minTime=True))
        t_max = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Start"))
        self.le_copy_start = QLineEdit(str(t_min))
        self.le_copy_start.setValidator(validator)
        range_row.addWidget(self.le_copy_start)
        btn_get_start = QPushButton("Get Current")
        btn_get_start.clicked.connect(lambda: self._set_current_frame(self.le_copy_start))
        range_row.addWidget(btn_get_start)
        range_row.addWidget(QLabel("End"))
        self.le_copy_end = QLineEdit(str(t_max))
        self.le_copy_end.setValidator(validator)
        range_row.addWidget(self.le_copy_end)
        btn_get_end = QPushButton("Get Current")
        btn_get_end.clicked.connect(lambda: self._set_current_frame(self.le_copy_end))
        range_row.addWidget(btn_get_end)
        layout.addLayout(range_row)

        btn_copy_frame = QPushButton("Copy every frame")
        btn_copy_frame.setToolTip(
            "Duplicate the SELECTED mesh(es) in the scene at every frame in\n"
            "[Start, End] (visibility off), grouped under <mesh>_frames.")
        btn_copy_frame.clicked.connect(self.on_copy_every_frame)
        layout.addWidget(btn_copy_frame)

        layout.addStretch(1)
        return tab

    # ==================================================
    # Tab 2 : Base Shape
    # ==================================================

    def _build_base_shape_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # blendShape 노드 지정 행
        node_row = QHBoxLayout()
        lbl = QLabel("BlendShape Node")
        lbl.setMinimumWidth(110)
        node_row.addWidget(lbl)
        self.le_bs_node = QLineEdit()
        self.le_bs_node.setPlaceholderText("Pick a blendShape node or a mesh, then <- Set")
        node_row.addWidget(self.le_bs_node)
        btn_set = QPushButton("<- Set")
        btn_set.setToolTip("Set the blendShape from the current selection (node or mesh).")
        btn_set.clicked.connect(self.on_set_bs_node)
        node_row.addWidget(btn_set)
        layout.addLayout(node_row)

        # List Targets 버튼
        btn_list = QPushButton("List Targets")
        btn_list.setToolTip("Populate the list below with this blendShape's targets.")
        btn_list.clicked.connect(self.on_list_targets)
        layout.addWidget(btn_list)

        # 타겟 리스트 (씬 오브젝트가 아니므로 일반 QListWidget)
        header = QHBoxLayout()
        lbl_t = QLabel("Targets")
        f = lbl_t.font()
        f.setBold(True)
        lbl_t.setFont(f)
        header.addWidget(lbl_t)
        header.addStretch(1)
        self.lbl_tgt_number = QLabel("Number: 0")
        header.addWidget(self.lbl_tgt_number)
        layout.addLayout(header)

        self.lw_targets = QListWidget()
        self.lw_targets.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_targets.setMinimumHeight(220)
        layout.addWidget(self.lw_targets)

        # 전체 선택 / 해제
        sel_row = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_all.clicked.connect(self.lw_targets.selectAll)
        btn_none = QPushButton("Clear Selection")
        btn_none.clicked.connect(self.lw_targets.clearSelection)
        sel_row.addWidget(btn_all)
        sel_row.addWidget(btn_none)
        layout.addLayout(sel_row)

        # 값 입력 행
        val_row = QHBoxLayout()
        lbl_v = QLabel("Value")
        lbl_v.setMinimumWidth(110)
        val_row.addWidget(lbl_v)
        self.dsb_value = QDoubleSpinBox()
        self.dsb_value.setDecimals(3)
        self.dsb_value.setRange(-10.0, 10.0)
        self.dsb_value.setSingleStep(0.1)
        self.dsb_value.setValue(0.5)
        self.dsb_value.setToolTip(
            "The shape currently seen at this weight value becomes the new weight=1.0 shape.\n"
            "Internally the target deltas are scaled by this factor (must be non-zero).")
        val_row.addWidget(self.dsb_value)
        val_row.addStretch(1)
        layout.addLayout(val_row)

        # 설명
        info = QLabel(
            "Make the shape at <Value> become the default (weight 1.0) shape\n"
            "for the selected targets. e.g. Value 0.5 halves the target; 1.3 exaggerates it.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Apply
        btn_apply = QPushButton("Apply  (Value -> 1.0)")
        btn_apply.setMinimumHeight(36)
        btn_apply.clicked.connect(self.on_apply_base_shape)
        layout.addWidget(btn_apply)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def _update_target_number(self):
        self.lbl_tgt_number.setText("Number: {0}".format(self.lw_targets.count()))

    def _set_current_frame(self, line_edit):
        """Get Current 버튼: 현재 Maya 프레임으로 해당 Start/End LineEdit 을 갱신."""
        line_edit.setText(str(int(round(cmds.currentTime(query=True)))))

    # --------------------------------------------------
    # Handlers : Edit BS
    # --------------------------------------------------

    def on_key_every_target(self):
        nodes = self.tsl_bs_nodes.get_all_items()
        if not nodes:
            self.log("[Warning] Add blendShape nodes to the list first.")
            return
        _n, msg = EditBSManager.key_every_target(nodes)
        self.log(msg)

    def on_copy_every_target(self):
        nodes = self.tsl_bs_nodes.get_all_items()
        if not nodes:
            self.log("[Warning] Add blendShape nodes to the list first.")
            return
        _n, msg = EditBSManager.copy_every_target(nodes)
        self.log(msg)

    def on_copy_every_frame(self):
        meshes = cmds.ls(selection=True, long=False) or []
        if not meshes:
            self.log("[Warning] Select mesh(es) in the scene first.")
            return

        s_txt = self.le_copy_start.text().strip()
        e_txt = self.le_copy_end.text().strip()
        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return

        start, end = int(s_txt), int(e_txt)
        if start > end:
            self.log("[Warning] Start ({0}) is greater than End ({1}).".format(start, end))
            return

        _n, msg = EditBSManager.copy_every_frame(meshes, start, end)
        self.log(msg)

    # --------------------------------------------------
    # Handlers : Base Shape
    # --------------------------------------------------

    def on_set_bs_node(self):
        found = bsu.find_blendshapes_from_selection()
        if not found:
            self.log("[Warning] Select a blendShape node or a mesh driven by one.")
            return
        self.le_bs_node.setText(found[0])
        if len(found) > 1:
            self.log("[Info] {0} blendShapes found; using '{1}'.".format(
                len(found), found[0]))
        # 지정과 동시에 타겟도 채워준다
        self.on_list_targets()

    def on_list_targets(self):
        bs_node = self.le_bs_node.text().strip()
        if not bsu.is_blendshape(bs_node):
            self.log("[Warning] '{0}' is not a valid blendShape node.".format(bs_node))
            return
        targets = BaseShapeManager.list_targets(bs_node)
        self.lw_targets.clear()
        self.lw_targets.addItems(targets)
        self._update_target_number()
        self.log("[List Targets] '{0}' : {1} target(s).".format(bs_node, len(targets)))

    def on_apply_base_shape(self):
        bs_node = self.le_bs_node.text().strip()
        if not bsu.is_blendshape(bs_node):
            self.log("[Warning] '{0}' is not a valid blendShape node.".format(bs_node))
            return

        target_names = [item.text() for item in self.lw_targets.selectedItems()]
        if not target_names:
            self.log("[Warning] Select target(s) in the list first.")
            return

        value = self.dsb_value.value()
        _done, msg = BaseShapeManager.apply_value_as_default(bs_node, target_names, value)
        self.log(msg)

    # --------------------------------------------------
    # About
    # --------------------------------------------------

    def show_about(self, *args):
        QMessageBox.information(
            self,
            "About",
            f"BS Tool v{VERSION}\n"
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}",
        )
