# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-26
# A00145_RigConnect - Qt UI
#
# MEL ConnectionTool V04.02 의 3탭(Constrain / Connect / List Connected)을 PySide 로
# 포팅하고, A00140 ConnectClosest 기능과 Match / Attribute 를 더한 것이다.
#
# 최상위 탭은 4개이고, 기능이 여럿인 탭은 **중첩 탭**으로 나눈다:
#   Match
#   Constrain : Constraint / Skin Weight / Group Create / Transfer / Target Edit
#   Connect   : Connect / List Connected / Connect Closest
#   Attribute
#
# 로직은 app/core 에 위임하고 이 모듈은 위젯 구성/시그널 연결/로그 출력만 담당한다.
# 모든 UI 문자열(버튼/라벨/로그)은 영어. (한국어는 주석/독스트링만)

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_filter_qt

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00145_RigConnect.app.config.version import VERSION, LAST_UPDATE
from tools.A00145_RigConnect.app.core import match_manager as mch_mgr
from tools.A00145_RigConnect.app.core import constrain_manager as con_mgr
from tools.A00145_RigConnect.app.core import matrix_constraint_manager as mtx_mgr
from tools.A00145_RigConnect.app.core import connect_manager as cnt_mgr
from tools.A00145_RigConnect.app.core import attribute_manager as att_mgr
from tools.A00145_RigConnect.app.core import stream_manager as stm_mgr
from tools.A00145_RigConnect.app.core import skin_constraint_manager as skn_mgr
from tools.A00145_RigConnect.app.core import group_create_manager as grp_mgr
from tools.A00145_RigConnect.app.core import constraint_transfer_manager as cxfer_mgr
from tools.A00145_RigConnect.app.core import constraint_target_manager as ctgt_mgr
from tools.A00145_RigConnect.app.core import attr_match
from tools.A00145_RigConnect.app.core import (
    CONSTRAINT_TYPES, connect_closest, find_closest_for_drivers)
from tools.A00145_RigConnect.app.ui.collapsible import CollapsibleBox


# 재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00145_RigConnect_window"


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 560
        self.win_height = 860
        self.win_title = "RigConnect v{0}".format(VERSION)

        # Connect 탭 src/dst 위젯 보관용. List Connected 의 stream 방향 상태.
        self._connect_widgets = {}
        self._stream_upstream = True

        self.resize(self.win_width, self.win_height)
        # 창이 의도치 않게 너무 작게 줄어들지 않도록 최소 크기를 보장한다.
        # (리스트/로그가 쓸만한 높이를 유지하도록 콘텐츠보다 약간 낮은 바닥값)
        self.setMinimumSize(480, 560)

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

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

        # 공유 로그창 (탭 빌더가 self.log 를 호출할 수 있어 탭보다 먼저 생성)
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(120)

        # 탭
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_match_tab(), "Match")
        self.tabs.addTab(self._build_constrain_tab(), "Constrain")
        self.tabs.addTab(self._build_connect_tab(), "Connect")
        self.tabs.addTab(self._build_attribute_tab(), "Attribute")
        main_layout.addWidget(self.tabs)

        main_layout.addWidget(self.te_log)

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------------------
    # Tab : Match  (MEL Match Tool V05.04 이식)
    # --------------------------------------------------------------

    def _build_match_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Targets / Followers (TSL 위젯이 cmds.ls(fl=True) 로 버텍스를 개별 항목으로 펼친다)
        self.tsl_match_tgt = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select",
            list_min_height=200, log_callback=self.log)
        self.tsl_match_flw = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=200, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_match_tgt)
        list_row.addWidget(self.tsl_match_flw)
        layout.addLayout(list_row)

        # Create : 타겟 수만큼 컨트롤을 만들어 타겟 위치/방향에 즉시 매칭(+ Followers 목록 채움).
        create_box = QGroupBox("Create (at target positions)")
        create_row = QHBoxLayout(create_box)
        for label, ctl_type in (("Locators", "locator"),
                                ("Sphere", "sphere"),
                                ("Cube", "cube")):
            btn = QPushButton(label)
            btn.clicked.connect(
                lambda _checked=False, t=ctl_type: self.on_match_create(t))
            create_row.addWidget(btn)
        layout.addWidget(create_box)

        # Match Options (DOOTOOL_PY_TOOL_Match 의 체크박스 이식).
        # Rotate Order / Rotate Axis 는 이 툴이 월드 행렬 기반 매칭이라 의미가 없어 제외.
        # 기본 체크 상태는 DOOTOOL 을 따른다: Translation/Rotation ON, Scale/Parent OFF.
        opt_box = QGroupBox("Match Options")
        opt_layout = QVBoxLayout(opt_box)

        tr_row = QHBoxLayout()
        self.cb_mt_translate = QCheckBox("Translation")
        self.cb_mt_translate.setChecked(True)
        self.cb_mt_translate.setToolTip(
            "Match the follower's world position to the target.")
        self.cb_mt_rotate = QCheckBox("Rotation")
        self.cb_mt_rotate.setChecked(True)
        self.cb_mt_rotate.setToolTip(
            "Match the follower's world rotation to the target (rotateOrder "
            "safe). For a vertex target, aligns the follower to the vertex "
            "normal instead.")
        tr_row.addWidget(self.cb_mt_translate)
        tr_row.addWidget(self.cb_mt_rotate)
        tr_row.addStretch(1)
        opt_layout.addLayout(tr_row)

        self.cb_mt_scale = QCheckBox("Scale (world space)")
        self.cb_mt_scale.setChecked(False)
        self.cb_mt_scale.setToolTip(
            "Match the follower's world scale to the target. Only meaningful "
            "for transform/joint targets (ignored for mesh/cluster/component/"
            "vertex targets).")
        opt_layout.addWidget(self.cb_mt_scale)

        self.cb_mt_parent = QCheckBox("Parent Followers to Targets")
        self.cb_mt_parent.setChecked(False)
        self.cb_mt_parent.setToolTip(
            "After matching, parent each follower under its target (under the "
            "owning object for a component target). Keeps the matched world "
            "position.")
        opt_layout.addWidget(self.cb_mt_parent)

        layout.addWidget(opt_box)

        # Match / Swap
        btn_row = QHBoxLayout()
        btn_match = QPushButton("Match")
        btn_match.setMinimumHeight(32)
        btn_match.clicked.connect(self.on_match)
        btn_swap = QPushButton("Swap")
        btn_swap.clicked.connect(self.on_match_swap)
        btn_row.addWidget(btn_match)
        btn_row.addWidget(btn_swap)
        layout.addLayout(btn_row)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Tab : Constrain
    # --------------------------------------------------------------

    # Constrain 하위 탭: (탭 라벨, 툴팁 = 전체 이름/설명, 빌더 메서드 이름).
    # 라벨을 짧게 두는 이유는 탭 바가 창 폭(기본 560)을 넘기지 않게 하기 위해서다.
    # 전체 이름은 툴팁에 싣는다.
    CONSTRAIN_PAGES = (
        ("Constraint", "Multi target -> follower constraints (+ Matrix Constraint)",
         "_build_constraint_page"),
        ("Skin Weight", "Skin Weight to Constraint - constrain by the skin weights "
         "of the selected vertices", "_build_skin_constraint_page"),
        ("Group Create", "Insert zero-out offset nodes above / below each object",
         "_build_group_create_page"),
        ("Transfer", "Constraint Transfer - move an existing constraint onto "
         "another object", "_build_constraint_transfer_page"),
        ("Target Edit", "Replace / add / remove the targets (drivers) of existing "
         "constraints", "_build_target_edit_page"),
    )

    def _build_constrain_tab(self):
        """Constrain 탭 — 기능별 **중첩 탭**.

        예전에는 접이식 박스(CollapsibleBox)를 위에서 아래로 쌓았는데, 기능이 5개로
        늘면서 원하는 것을 찾으려면 접었다 폈다 해야 했다. 이제 탭 하나에 기능 하나만
        보인다. 각 페이지는 따로 스크롤되므로 창을 줄여도 위젯이 겹치지 않는다.
        """
        self.constrain_tabs = self._build_sub_tabs(self.CONSTRAIN_PAGES)
        return self.constrain_tabs

    def _build_sub_tabs(self, pages):
        """(라벨, 툴팁, 빌더 메서드 이름) 목록을 중첩 탭 위젯으로 만든다.

        상위 탭 하나가 여러 기능을 품을 때 쓰는 공통 골격(Constrain / Connect).
        """
        tabs = QTabWidget()
        # 폭이 모자라면 라벨을 자른다(스크롤 화살표만 뜨는 것보다 읽기 쉽다).
        tabs.tabBar().setElideMode(Qt.ElideRight)

        for label, tip, builder in pages:
            index = tabs.addTab(self._scrolled(getattr(self, builder)()), label)
            tabs.setTabToolTip(index, tip)

        return tabs

    def _scrolled(self, widget):
        """위젯을 스크롤 영역에 담아 돌려준다 (창이 작아도 겹치지 않도록)."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    def _build_constraint_page(self):
        """기존 multi target -> follower constraint UI (Constrain 하위 탭)."""
        page = QWidget()
        layout = QVBoxLayout(page)

        self.tsl_targets = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select",
            list_min_height=200, log_callback=self.log)
        self.tsl_followers = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=200, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_targets)
        list_row.addWidget(self.tsl_followers)
        layout.addLayout(list_row)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        # 대부분의 리깅 작업이 오프셋 유지를 전제로 해 기본 체크 상태로 둔다.
        self.cb_con_maintain = QCheckBox("Maintain Offset")
        self.cb_con_maintain.setChecked(True)
        opt_layout.addWidget(self.cb_con_maintain)

        self.rb_con_group = QButtonGroup(self)
        rb_row = QHBoxLayout()
        for i, (key, label) in enumerate(con_mgr.CONSTRAIN_TYPES):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self.rb_con_group.addButton(rb, i)
            rb_row.addWidget(rb)
        opt_layout.addLayout(rb_row)

        # --- Matrix Constraint 모드 ---
        # 체크 시 *Constraint 노드 대신 multMatrix/decomposeMatrix 네트워크로 구속한다.
        self.cb_con_matrix = QCheckBox("Matrix Constraint")
        self.cb_con_matrix.setChecked(False)
        opt_layout.addWidget(self.cb_con_matrix)

        # Matrix 모드 전용 채널 토글(기본 전부 on). 일반 모드에선 비활성.
        mtx_row = QHBoxLayout()
        self.cb_mtx_t = QCheckBox("Translate")
        self.cb_mtx_r = QCheckBox("Rotate")
        self.cb_mtx_s = QCheckBox("Scale")
        for cb in (self.cb_mtx_t, self.cb_mtx_r, self.cb_mtx_s):
            cb.setChecked(True)
            mtx_row.addWidget(cb)
        opt_layout.addLayout(mtx_row)

        self.cb_con_matrix.toggled.connect(self._on_matrix_mode_toggled)
        self._on_matrix_mode_toggled(False)

        layout.addWidget(opt_box)

        btn = QPushButton("Constrain")
        btn.setMinimumHeight(32)
        btn.clicked.connect(self.on_constrain)
        layout.addWidget(btn)

        return page

    def _on_matrix_mode_toggled(self, enabled):
        """Matrix Constraint 모드 토글.

        Matrix on  : 채널(T/R/S) 체크박스 활성, 컨스트레인트 타입 라디오 비활성.
        Matrix off : 반대.
        """
        for cb in (self.cb_mtx_t, self.cb_mtx_r, self.cb_mtx_s):
            cb.setEnabled(enabled)
        for rb in self.rb_con_group.buttons():
            rb.setEnabled(not enabled)

    def _build_skin_constraint_page(self):
        """Skin Weight to Constraint UI (Constrain 하위 탭).

        선택 버텍스의 스킨 웨이트로 영향 joint 들을 그 비율의 weight 로
        follower 에 constraint 한다. constraint 타입은 라디오로 고른다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # 어떤 버텍스를 선택했는지 리스트업하는 TSL + follower 리스트.
        self.tsl_skin_verts = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Vertices", select_label="Select",
            list_min_height=180, log_callback=self.log)
        self.tsl_skin_followers = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Followers", select_label="Select",
            list_min_height=180, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_skin_verts)
        list_row.addWidget(self.tsl_skin_followers)
        layout.addLayout(list_row)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        # Max Influence : 사용할 최대 joint 개수 (0 = 제한 없음).
        mi_row = QHBoxLayout()
        mi_row.addWidget(QLabel("Max Influence"))
        self.sb_skin_max_inf = QSpinBox()
        self.sb_skin_max_inf.setRange(0, 100)
        self.sb_skin_max_inf.setValue(4)
        self.sb_skin_max_inf.setToolTip("Max number of influences to use (0 = no limit)")
        mi_row.addWidget(self.sb_skin_max_inf)
        mi_row.addStretch(1)
        opt_layout.addLayout(mi_row)

        self.cb_skin_maintain = QCheckBox("Maintain Offset")
        self.cb_skin_maintain.setChecked(True)
        opt_layout.addWidget(self.cb_skin_maintain)

        # 체크 시: vertices[i] 웨이트 -> followers[i] 1:1.
        # 해제 시: 모든 버텍스 웨이트 평균 -> 모든 follower 에 동일 적용.
        self.cb_skin_per_vertex = QCheckBox(
            "Per-vertex (vertex[i] -> follower[i], 1:1)")
        self.cb_skin_per_vertex.setChecked(False)
        opt_layout.addWidget(self.cb_skin_per_vertex)

        # 생성할 constraint 타입. 위 Constraint 박스와 같은 라디오 패턴.
        # (pointOnPoly 는 joint 가중 방식에 쓸 수 없어 목록에서 빠진다)
        self.rb_skin_con_group = QButtonGroup(self)
        rb_row = QHBoxLayout()
        for i, (key, label) in enumerate(skn_mgr.SKIN_CONSTRAIN_TYPES):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self.rb_skin_con_group.addButton(rb, i)
            rb_row.addWidget(rb)
        rb_row.addStretch(1)
        opt_layout.addLayout(rb_row)

        layout.addWidget(opt_box)

        btn_row = QHBoxLayout()

        btn = QPushButton("Skin Weight to Constraint")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Constrain the objects in the Followers list with the skin "
            "weights of the selected vertices.\n"
            "The constraint type is taken from the radio buttons above.")
        btn.clicked.connect(self.on_skin_weight_to_constraint)
        btn_row.addWidget(btn)

        # Locators : follower 를 직접 만들 필요 없이, 로케이터를 자동 생성하고
        # 동일한 스킨 웨이트 constraint 를 그 로케이터에 건다.
        btn_loc = QPushButton("Locators")
        btn_loc.setMinimumHeight(32)
        btn_loc.setToolTip(
            "Auto-create locators and run Skin Weight to Constraint on them "
            "(no Followers needed).\n"
            "Per-vertex: one locator per vertex at its position.\n"
            "Average: one locator at the centroid of selected vertices.")
        btn_loc.clicked.connect(self.on_skin_weight_to_locators)
        btn_row.addWidget(btn_loc)

        layout.addLayout(btn_row)

        return page

    def _build_group_create_page(self):
        """Group Create UI (Constrain 하위 탭).

        리스트업된 각 오브젝트에, 그 오브젝트와 위치·회전이 같은 오프셋 노드를
        부모 쪽/자식 쪽 계층에 삽입한다(zero-out). 노드명은 <obj>_<suffix>_01.
        Suffix / Count / Padding / 노드 타입(Group·오브젝트 타입) / 방향(Parent·Child)
        을 사용자가 지정한다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        self.tsl_group_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=180, log_callback=self.log)
        layout.addWidget(self.tsl_group_objs)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        # Suffix / Count / Padding (한 줄).
        row = QHBoxLayout()
        row.addWidget(QLabel("Suffix"))
        self.le_group_suffix = QLineEdit("zro")
        self.le_group_suffix.setMaximumWidth(80)
        self.le_group_suffix.setToolTip(
            "Name suffix for created nodes. Node name = <object>_<suffix>_01.")
        row.addWidget(self.le_group_suffix)

        row.addWidget(QLabel("Count"))
        self.sb_group_count = QSpinBox()
        self.sb_group_count.setRange(1, 50)
        self.sb_group_count.setValue(1)
        self.sb_group_count.setToolTip(
            "How many nested nodes to create per object (per side).\n"
            "_01 is the object's immediate parent (Parent) / child (Child).")
        row.addWidget(self.sb_group_count)

        row.addWidget(QLabel("Padding"))
        self.sb_group_padding = QSpinBox()
        self.sb_group_padding.setRange(1, 6)
        self.sb_group_padding.setValue(2)
        self.sb_group_padding.setToolTip(
            "Zero-padding width of the number (2 -> 01, 02; 3 -> 001, 002).")
        row.addWidget(self.sb_group_padding)
        row.addStretch(1)
        opt_layout.addLayout(row)

        # Type : Group(기본) 또는 오브젝트와 동일 타입.
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type"))
        self.rb_group_type = QButtonGroup(self)
        rb_grp = QRadioButton("Group")
        rb_grp.setChecked(True)
        rb_grp.setToolTip("Created nodes are empty groups (transforms).")
        rb_match = QRadioButton("Match object type")
        rb_match.setToolTip(
            "Created nodes use the object's own node type\n"
            "(e.g. a joint object -> joint offset nodes).")
        self.rb_group_type.addButton(rb_grp, 0)
        self.rb_group_type.addButton(rb_match, 1)
        type_row.addWidget(rb_grp)
        type_row.addWidget(rb_match)
        type_row.addStretch(1)
        opt_layout.addLayout(type_row)

        # Side : Parent(기본 on) / Child. 둘 다 켜면 양쪽 모두 삽입.
        side_row = QHBoxLayout()
        side_row.addWidget(QLabel("Side"))
        self.cb_group_parent = QCheckBox("Parent")
        self.cb_group_parent.setChecked(True)
        self.cb_group_parent.setToolTip(
            "Insert nodes between the object and its parent (object moves down).")
        self.cb_group_child = QCheckBox("Child")
        self.cb_group_child.setToolTip(
            "Insert nodes between the object and its children\n"
            "(existing children move down; none -> nodes hang under the object).")
        side_row.addWidget(self.cb_group_parent)
        side_row.addWidget(self.cb_group_child)
        side_row.addStretch(1)
        opt_layout.addLayout(side_row)

        layout.addWidget(opt_box)

        btn = QPushButton("Create Groups")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Insert offset node(s) (same world position/rotation) on the parent\n"
            "and/or child side of each listed object. Name = <object>_<suffix>_01.")
        btn.clicked.connect(self.on_group_create)
        layout.addWidget(btn)

        return page

    def _build_constraint_transfer_page(self):
        """Constraint Transfer UI (Constrain 하위 탭).

        왼쪽 목록의 constraint 를 오른쪽 목록의 오브젝트로 옮긴다(원본 삭제 + 동일
        세팅 재생성, maintainOffset 유지로 양쪽 모두 위치/회전 불변). UUID 기반.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # 왼쪽: 옮길 constraint(또는 constraint 가 걸린 트랜스폼).
        self.tsl_cxfer_cons = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Constraints", select_label="Select",
            list_min_height=180, log_callback=self.log)
        # 오른쪽: 새로 constraint 를 받을(driven) 오브젝트.
        self.tsl_cxfer_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Apply To", select_label="Select",
            list_min_height=180, log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_cxfer_cons)
        list_row.addWidget(self.tsl_cxfer_objs)
        layout.addLayout(list_row)

        btn = QPushButton("Transfer Constraint")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Delete each listed constraint and re-create the same constraint\n"
            "(type, targets, weights, maintain offset) on the right-side object.\n"
            "Both the old and the new object keep their world position/rotation.\n"
            "Left items may be constraint nodes or objects that carry constraints.\n"
            "Mapping: 1 object -> all constraints go to it; equal counts -> 1:1.")
        btn.clicked.connect(self.on_transfer_constraint)
        layout.addWidget(btn)

        return page

    def _build_target_edit_page(self):
        """Target Edit UI (Constrain 하위 탭) - 타깃 교체 / 추가 / 삭제.

        리스트업한 constraint 들이 쓰고 있는 타깃(드라이버)을 모아 보여 주고, 고른
        타깃을 씬의 다른 오브젝트로 갈아끼우거나(Replace), 지우거나(Remove), New
        Target 리스트의 오브젝트를 새 타깃으로 붙인다(Add). 그 타깃을 쓰지 않는
        constraint 는 건드리지 않는다.

        세 동작 모두 **Constraints 리스트에서 고른 항목만** 대상으로 한다(아무것도
        고르지 않으면 리스트 전체). 한 페이지에 모은 이유는 셋 다 같은 입력
        (constraint 목록 + 타깃 목록 + 새 타깃 목록)을 쓰기 때문이다.
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # 왼쪽: 대상 constraint(또는 constraint 가 걸린 트랜스폼).
        self.tsl_tedit_cons = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Constraints", select_label="Select",
            list_min_height=160, log_callback=self.log)
        self.tsl_tedit_cons.setToolTip(
            "Constraint nodes, or objects that carry constraints (expanded to "
            "their constraint children).\n"
            "Pick rows to work on a subset - with nothing picked the whole list "
            "is used.")

        # 오른쪽: 위 constraint 들이 쓰고 있는 타깃 목록.
        targets_col = QVBoxLayout()
        head = QHBoxLayout()
        lbl = QLabel("Targets")
        font = lbl.font()
        font.setBold(True)
        lbl.setFont(font)
        head.addWidget(lbl)
        head.addStretch(1)
        self.lbl_tedit_number = QLabel("Number: 0")
        head.addWidget(self.lbl_tedit_number)
        targets_col.addLayout(head)

        self.lw_tedit_targets = QListWidget()
        self.lw_tedit_targets.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_tedit_targets.setMinimumHeight(160)
        self.lw_tedit_targets.setToolTip(
            "Targets used by the constraints on the left.\n"
            "[n/m] = used by n of the m constraints (hover for the list).\n"
            "Pick rows here to replace or remove those targets.")
        targets_col.addWidget(self.lw_tedit_targets)

        self.flt_tedit = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            self.lw_tedit_targets, placeholder="Type any part of a target name",
            number_label=self.lbl_tedit_number)
        targets_col.addWidget(self.flt_tedit)

        btn_row = QHBoxLayout()
        btn_list = QPushButton("List Targets")
        btn_list.setToolTip(
            "Collect every target used by the constraints on the left.")
        btn_list.clicked.connect(self.on_tedit_list)
        btn_row.addWidget(btn_list)
        btn_pick = QPushButton("Select")
        btn_pick.setToolTip("Select the picked targets in the scene.")
        btn_pick.clicked.connect(self.on_tedit_select)
        btn_row.addWidget(btn_pick)
        targets_col.addLayout(btn_row)

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_tedit_cons)
        list_row.addLayout(targets_col)
        layout.addLayout(list_row)

        # 아래: 대신 들어갈 / 새로 붙일 오브젝트 (Replace 와 Add 가 공유).
        self.tsl_tedit_new = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="New Target (used by Replace / Add)", select_label="Select",
            list_min_height=110, log_callback=self.log)
        self.tsl_tedit_new.setToolTip(
            "Replace : the object(s) that take the picked target's place.\n"
            "Add     : the object(s) added as extra targets.")
        layout.addWidget(self.tsl_tedit_new)

        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)

        self.cb_tedit_keep = QCheckBox("Keep driven objects in place")
        self.cb_tedit_keep.setChecked(True)
        self.cb_tedit_keep.setToolTip(
            "On  : recompute the constraint offset so nothing moves when the "
            "targets change.\n"
            "Off : keep the original offset, so the driven object follows the "
            "new target set the same way it did before (it will jump).")
        opt_layout.addWidget(self.cb_tedit_keep)

        self.cb_tedit_rename = QCheckBox("Rename the weight attribute to the new target")
        self.cb_tedit_rename.setChecked(False)
        self.cb_tedit_rename.setToolTip(
            "Replace only. Rename the target weight attribute "
            "(tgt_A_02W0 -> tgt_B_02W0).\n"
            "Only auto-generated names are touched. Leave off if scripts refer "
            "to the weight by name.")
        opt_layout.addWidget(self.cb_tedit_rename)

        self.cb_tedit_delete_empty = QCheckBox(
            "Delete the constraint when its last target is removed")
        self.cb_tedit_delete_empty.setChecked(False)
        self.cb_tedit_delete_empty.setToolTip(
            "Remove only. Maya deletes a constraint node once its last target "
            "goes away\n"
            "(the driven object keeps the values it had).\n"
            "Off : such a constraint is skipped with a warning instead.")
        opt_layout.addWidget(self.cb_tedit_delete_empty)

        weight_row = QHBoxLayout()
        lbl_weight = QLabel("Added target weight")
        self.sb_tedit_weight = QDoubleSpinBox()
        self.sb_tedit_weight.setRange(0.0, 100.0)
        self.sb_tedit_weight.setSingleStep(0.1)
        self.sb_tedit_weight.setDecimals(3)
        self.sb_tedit_weight.setValue(1.0)
        self.sb_tedit_weight.setKeyboardTracking(False)
        self.sb_tedit_weight.setToolTip(
            "Add only. Constraint weight given to each added target.")
        weight_row.addWidget(lbl_weight)
        weight_row.addWidget(self.sb_tedit_weight)
        weight_row.addStretch(1)
        opt_layout.addLayout(weight_row)

        layout.addWidget(opt_box)

        btn_replace = QPushButton("Replace Target")
        btn_replace.setMinimumHeight(32)
        btn_replace.setToolTip(
            "Swap the picked target for the New Target on every constraint that "
            "uses it.\n"
            "Constraints without that target are left untouched.\n"
            "Weights, weight connections and the constraint node itself are kept.\n"
            "Mapping: 1 new target -> used for every picked target; equal counts "
            "-> 1:1.")
        btn_replace.clicked.connect(self.on_replace_target)
        layout.addWidget(btn_replace)

        edit_row = QHBoxLayout()

        btn_add = QPushButton("Add Target")
        btn_add.setMinimumHeight(32)
        btn_add.setToolTip(
            "Add every object in the New Target list as an extra target of every "
            "listed constraint.\n"
            "Targets a constraint already has are skipped.\n"
            "Weight aliases are created by Maya, so existing targets and their "
            "weights are kept.")
        btn_add.clicked.connect(self.on_add_target)
        edit_row.addWidget(btn_add)

        btn_remove = QPushButton("Remove Target")
        btn_remove.setMinimumHeight(32)
        btn_remove.setToolTip(
            "Remove the targets picked in the Targets list from the listed "
            "constraints.\n"
            "Constraints without those targets are left untouched.\n"
            "Removing a constraint's last target deletes the constraint - see "
            "the option above.")
        btn_remove.clicked.connect(self.on_remove_target)
        edit_row.addWidget(btn_remove)

        layout.addLayout(edit_row)

        return page

    # --------------------------------------------------------------
    # Tab : Connect  (하위 탭 : Connect / List Connected / Connect Closest)
    # --------------------------------------------------------------

    # Connect 페이지의 두 패널 역할 -> 화면에 쓰는 이름. 연결 방향 로그/라벨에 쓴다.
    ROLE_LABELS = {"src": "Source", "dst": "Destination"}

    # Connect 하위 탭: (탭 라벨, 툴팁 = 설명, 빌더 메서드 이름).
    CONNECT_PAGES = (
        ("Connect", "Connect attributes from the source objects to the "
         "destination objects (+ Match from Source, 52 facial)",
         "_build_connect_page"),
        ("List Connected", "Explore the nodes up / down stream of the listed "
         "objects, by node type", "_build_list_connected_page"),
        ("Connect Closest", "Constrain each driver to its nearest object (1:1)",
         "_build_connect_closest_page"),
    )

    def _build_connect_tab(self):
        """Connect 탭 — 어트리뷰트/노드 연결 기능을 하나로 묶은 **중첩 탭**.

        Connect / List Connected / Connect Closest 는 모두 "연결" 작업이라 최상위에
        따로 있을 이유가 없었다. Constrain 탭과 같은 방식으로 하위 탭에 모은다.
        """
        self.connect_tabs = self._build_sub_tabs(self.CONNECT_PAGES)
        return self.connect_tabs

    def _build_connect_page(self):
        """어트리뷰트 연결 UI (Connect 하위 탭). 양방향 모두 지원한다."""
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(self._build_connect_io("src", "Source Objects"))
        layout.addWidget(self._build_connect_io("dst", "Destination Objects"))

        # 두 방향을 나란히 둔다. 어느 쪽이 드라이버인지 화살표로 바로 읽힌다.
        dir_row = QHBoxLayout()

        btn_connect = QPushButton("Source  ->  Destination")
        btn_connect.setMinimumHeight(32)
        btn_connect.setToolTip(
            "Connect the selected Source attributes to the selected Destination\n"
            "attributes (Source drives Destination).")
        btn_connect.clicked.connect(self.on_connect_attrs)
        dir_row.addWidget(btn_connect)

        btn_connect_rev = QPushButton("Destination  ->  Source")
        btn_connect_rev.setMinimumHeight(32)
        btn_connect_rev.setToolTip(
            "The other way round: connect the selected Destination attributes to\n"
            "the selected Source attributes (Destination drives Source).\n"
            "Same pairing rules, only the direction is flipped.")
        btn_connect_rev.clicked.connect(self.on_connect_attrs_reverse)
        dir_row.addWidget(btn_connect_rev)

        layout.addLayout(dir_row)

        btn_facial = QPushButton("Connect 52 Facial Target")
        btn_facial.setToolTip(
            "Connect the 52 ARKit facial attributes by name, Source -> Destination.")
        btn_facial.clicked.connect(self.on_connect_52_facial)
        layout.addWidget(btn_facial)

        layout.addStretch(1)
        return page

    def _build_connect_io(self, role, title):
        """Connect 하위 탭의 Source/Destination 한 섹션을 만든다 (접이식).

        이 둘은 나란히 놓고 **동시에** 봐야 해서 탭이 아니라 접이식으로 둔다.
        """
        box = CollapsibleBox(title)

        tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=120, log_callback=self.log)

        attr_list = QListWidget()
        attr_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        attr_list.setMinimumHeight(120)

        btn_list = QPushButton("List Attributes")

        body = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(tsl)
        left.addWidget(btn_list)

        right = QVBoxLayout()
        head = QHBoxLayout()
        head.addWidget(QLabel("Attributes"))
        head.addStretch(1)
        lbl_number = QLabel("Number: 0")
        head.addWidget(lbl_number)
        right.addLayout(head)
        right.addWidget(attr_list)

        # 검색 = 공용 Filter 위젯. 입력하는 즉시 일치하는 것만 남고 나머지는 숨는다.
        flt = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            attr_list, placeholder="Type any part of an attribute name",
            number_label=lbl_number)
        right.addWidget(flt)

        btn_all = QPushButton("Select All")
        btn_all.setToolTip("Select every attribute currently visible in the list.")
        btn_all.clicked.connect(flt.select_all_visible)
        right.addWidget(btn_all)

        # Destination 쪽에만: 소스에서 고른 어트리뷰트와 **이름이 비슷한** 것을 찾아
        # 소스 순서 그대로 목록 맨 위에 정렬 + 선택한다. 곧바로 Connect 로 이어진다.
        if role == "dst":
            right.addLayout(self._build_match_row())

        body.addLayout(left)
        body.addLayout(right)
        box.addLayout(body)

        self._connect_widgets[role] = {
            "tsl": tsl,
            "attrs": attr_list,
            "filter": flt,
        }

        btn_list.clicked.connect(lambda: self.on_list_attrs(role))

        return box

    def _build_match_row(self):
        """Destination 패널의 'Match from Source' 행 (버튼 + 옵션)."""
        row = QHBoxLayout()

        btn = QPushButton("Match from Source")
        btn.setToolTip(
            "Find the destination attribute whose NAME is most similar to each "
            "source attribute.\n"
            "The matches are moved to the top of this list IN SOURCE ORDER and "
            "selected,\n"
            "so 'Connect Source to Destination' pairs them up right away.\n"
            "\n"
            "Example: source brow_up / brow_down against\n"
            "  lod0_mesh_body_eye_L_up, lod0_mesh_body_eye_L_down,\n"
            "  lod0_mesh_body_brow_up,  lod0_mesh_body_brow_down\n"
            "  ->  lod0_mesh_body_brow_up, lod0_mesh_body_brow_down\n"
            "\n"
            "Names are compared by tokens (brow_up == browUp), so a shared "
            "boilerplate\n"
            "prefix like lod0_mesh_body_ is ignored automatically.")
        btn.clicked.connect(self.on_match_from_source)
        row.addWidget(btn, 1)

        self.cb_match_unique = QCheckBox("Unique")
        self.cb_match_unique.setChecked(True)
        self.cb_match_unique.setToolTip(
            "On  : one destination attribute is never used twice.\n"
            "Off : two source attributes may match the same destination.")
        row.addWidget(self.cb_match_unique)

        row.addWidget(QLabel("Min"))
        self.sb_match_min = QDoubleSpinBox()
        self.sb_match_min.setRange(0.0, 1.0)
        self.sb_match_min.setSingleStep(0.05)
        self.sb_match_min.setDecimals(2)
        self.sb_match_min.setValue(attr_match.DEFAULT_MIN_SCORE)
        self.sb_match_min.setKeyboardTracking(False)
        self.sb_match_min.setMaximumWidth(70)
        self.sb_match_min.setToolTip(
            "How much of the source name must be explained by the match (0-1).\n"
            "1.00 = every distinctive word of the source appears in the match.\n"
            "Raise it to reject loose matches, lower it to force a best guess.")
        row.addWidget(self.sb_match_min)

        return row

    # --------------------------------------------------------------
    # Tab : Attribute
    # --------------------------------------------------------------

    def _build_attribute_tab(self):
        """소스 오브젝트의 어트리뷰트를 골라 타겟들에 같은 정의로 새로 만드는 탭.

        이름은 그대로 두거나 Prefix / Suffix 를 붙일 수 있다.
        """
        content = QWidget()
        layout = QVBoxLayout(content)

        # --- Source : 오브젝트 1개 + 그 오브젝트의 어트리뷰트 목록 ---
        src_box = QGroupBox("Source (attributes to copy)")
        src_layout = QHBoxLayout(src_box)

        self.tsl_attr_src = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Source Object", select_label="Select",
            list_min_height=150, log_callback=self.log)

        left = QVBoxLayout()
        left.addWidget(self.tsl_attr_src)
        btn_list = QPushButton("List Attributes")
        btn_list.setToolTip(
            "List the attributes of the first object in the Source list.")
        btn_list.clicked.connect(self.on_attr_list)
        left.addWidget(btn_list)

        # 어트리뷰트는 여러 개를 골라 한 번에 복사한다.
        self.lw_attr_src = QListWidget()
        self.lw_attr_src.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_attr_src.setMinimumHeight(150)
        self.lw_attr_src.itemSelectionChanged.connect(self._update_attr_preview)

        right = QVBoxLayout()
        head = QHBoxLayout()
        head.addWidget(QLabel("Attributes"))
        head.addStretch(1)
        self.lbl_attr_number = QLabel("Number: 0")
        head.addWidget(self.lbl_attr_number)
        right.addLayout(head)
        right.addWidget(self.lw_attr_src)

        # 기본값 ON : 리깅에서 복사할 대상은 거의 항상 사용자 정의 어트리뷰트다.
        # 끄면 translateX 같은 기본 어트리뷰트까지 전부 나온다.
        self.cb_attr_user_only = QCheckBox("User defined only")
        self.cb_attr_user_only.setChecked(True)
        self.cb_attr_user_only.setToolTip(
            "On  : only custom (user defined) attributes.\n"
            "Off : every attribute, including built-ins like translateX.")
        right.addWidget(self.cb_attr_user_only)

        # Connect 탭과 같은 공용 Filter. 예전에는 검색어가 목록을 다시 질의하는
        # 인자였는데(Enter -> 재조회), 이제는 이미 채워진 목록을 즉시 거른다.
        search_row = QHBoxLayout()
        self.flt_attr_src = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            self.lw_attr_src, placeholder="Type any part of an attribute name",
            number_label=self.lbl_attr_number)
        search_row.addWidget(self.flt_attr_src, 1)
        btn_all = QPushButton("Select All")
        btn_all.setToolTip("Select every attribute currently visible in the list.")
        btn_all.clicked.connect(self.flt_attr_src.select_all_visible)
        search_row.addWidget(btn_all)
        right.addLayout(search_row)

        src_layout.addLayout(left)
        src_layout.addLayout(right)
        layout.addWidget(src_box)

        # --- Targets : 어트리뷰트를 새로 만들 오브젝트들 ---
        self.tsl_attr_tgt = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets (new attributes here)", select_label="Select",
            list_min_height=150, log_callback=self.log)
        layout.addWidget(self.tsl_attr_tgt)

        # --- Options : 새 이름 규칙 ---
        opt_box = QGroupBox("New Attribute Name")
        opt_layout = QVBoxLayout(opt_box)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Prefix"))
        self.le_attr_prefix = QLineEdit()
        self.le_attr_prefix.setPlaceholderText("e.g. L_")
        self.le_attr_prefix.textChanged.connect(self._update_attr_preview)
        name_row.addWidget(self.le_attr_prefix)
        name_row.addWidget(QLabel("Suffix"))
        self.le_attr_suffix = QLineEdit()
        self.le_attr_suffix.setPlaceholderText("e.g. _ctrl")
        self.le_attr_suffix.textChanged.connect(self._update_attr_preview)
        name_row.addWidget(self.le_attr_suffix)
        opt_layout.addLayout(name_row)

        # 둘 다 비우면 소스와 같은 이름으로 만들어진다.
        self.lbl_attr_preview = QLabel("Preview : -")
        opt_layout.addWidget(self.lbl_attr_preview)

        self.cb_attr_value = QCheckBox("Copy current value")
        self.cb_attr_value.setChecked(True)
        self.cb_attr_value.setToolTip(
            "Also set the source's current value on the new attribute.")
        opt_layout.addWidget(self.cb_attr_value)

        layout.addWidget(opt_box)

        btn_copy = QPushButton("Copy Attributes to Targets")
        btn_copy.setMinimumHeight(32)
        btn_copy.setToolTip(
            "Create the selected attributes on every object in the Targets "
            "list, keeping type / range / default / keyable.\n"
            "Targets that already have the attribute are skipped.")
        btn_copy.clicked.connect(self.on_attr_copy)
        layout.addWidget(btn_copy)

        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    # --------------------------------------------------------------
    # Connect > List Connected
    # --------------------------------------------------------------

    def _build_list_connected_page(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        row = QHBoxLayout()

        # Objects
        self.tsl_stream_objs = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select",
            list_min_height=220, log_callback=self.log)
        row.addWidget(self.tsl_stream_objs)

        # Types
        types_box = QVBoxLayout()
        types_box.addWidget(QLabel("Types"))
        self.list_types = QListWidget()
        self.list_types.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_types.setMinimumHeight(180)
        types_box.addWidget(self.list_types)
        btn_up = QPushButton("List UpStream")
        btn_dn = QPushButton("List DownStream")
        btn_up.clicked.connect(lambda: self.on_list_stream(True))
        btn_dn.clicked.connect(lambda: self.on_list_stream(False))
        types_box.addWidget(btn_up)
        types_box.addWidget(btn_dn)
        row.addLayout(types_box)

        # Nodes
        nodes_box = QVBoxLayout()
        nodes_box.addWidget(QLabel("Nodes"))
        self.list_nodes = QListWidget()
        self.list_nodes.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_nodes.setMinimumHeight(180)
        self.list_nodes.itemSelectionChanged.connect(self.on_nodes_selection_changed)
        nodes_box.addWidget(self.list_nodes)
        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.on_search_nodes)
        nodes_box.addWidget(btn_search)
        row.addLayout(nodes_box)

        layout.addLayout(row)
        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Connect > Connect Closest  (A00140 ConnectClosest 이식)
    # --------------------------------------------------------------

    def _build_connect_closest_page(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        set_box = QGroupBox("Set Up")
        set_layout = QHBoxLayout(set_box)
        self.cc_driven = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Driven",
            list_min_height=200, log_callback=self.log)
        self.cc_driver = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Driver",
            list_min_height=200, log_callback=self.log)
        # 각 Driver 에 가장 가까운 오브젝트를 찾아 Driven 을 driver 순서대로 채운다.
        # 후보 풀: Driven 에 항목이 있으면 그걸, 없으면 현재 씬 선택.
        self.cc_driver.add_button("Get Closest", self.on_get_closest)
        set_layout.addWidget(self.cc_driven)
        set_layout.addWidget(self.cc_driver)
        layout.addWidget(set_box)

        opt_box = QGroupBox("Constraint Type")
        opt_layout = QVBoxLayout(opt_box)
        cb_row = QHBoxLayout()
        self.cc_checkboxes = {}
        for key, label, _method in CONSTRAINT_TYPES:
            cb = QCheckBox(label)
            self.cc_checkboxes[key] = cb
            cb_row.addWidget(cb)
        self.cc_checkboxes["parent"].setChecked(True)
        opt_layout.addLayout(cb_row)
        self.cc_maintain = QCheckBox("Maintain Offset")
        self.cc_maintain.setChecked(True)
        opt_layout.addWidget(self.cc_maintain)
        layout.addWidget(opt_box)

        btn = QPushButton("Connect")
        btn.setMinimumHeight(32)
        btn.clicked.connect(self.on_connect_closest)
        layout.addWidget(btn)

        layout.addStretch(1)
        return tab

    # ==============================================================
    # UI helpers
    # ==============================================================

    def _selected_texts(self, list_widget):
        return [it.text() for it in list_widget.selectedItems()]

    def _all_texts(self, list_widget):   # noqa: 유틸 (현재 호출부 없음)
        return [list_widget.item(i).text() for i in range(list_widget.count())]

    def log(self, text):
        self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "RigConnect v{0}\n"
            "Written by Ji Hun Park\n"
            "Update date : {1}\n"
            "\n"
            "Match       : match followers to targets (rotateOrder safe)\n"
            "              options: Translation / Rotation / Scale (world) / Parent\n"
            "              + create locators/sphere/cube at targets + vertex normal (+Y)\n"
            "Constrain   : sub-tabs -\n"
            "              Constraint   : multi target -> follower (+ Matrix)\n"
            "              Skin Weight  : constrain by the selected vertices'\n"
            "                             skin weights (+ auto Locators)\n"
            "              Group Create : zero-out offset nodes\n"
            "              Transfer     : move a constraint onto another object\n"
            "              Target Repl. : swap a constraint target, offset kept\n"
            "Connect     : sub-tabs -\n"
            "              Connect      : connect attributes BOTH ways\n"
            "                             (Source -> Destination and back),\n"
            "                             3 broadcast patterns + 52 facial\n"
            "                             + Match from Source (find look-alike\n"
            "                             destination attributes, in order)\n"
            "              List Conn.   : explore up/down stream nodes by type\n"
            "              Conn. Closest: 1:1 closest matching constraints\n"
            "                             + Get Closest\n"
            "Attribute   : copy selected attributes onto other objects,\n"
            "              same name or with a Prefix / Suffix".format(
                VERSION, LAST_UPDATE))

    def _run(self, label, func):
        """undo chunk 로 감싸 실행하고 결과를 로그에 남긴다."""
        with undo_chunk():
            try:
                func()
                self.log("[OK] {0}".format(label))
            except Exception as e:
                self.log("[ERR] {0} : {1}".format(label, e))
                cmds.warning(str(e))

    # ==============================================================
    # Handlers : Match
    # ==============================================================

    def on_match(self):
        targets = self.tsl_match_tgt.get_all_items()
        followers = self.tsl_match_flw.get_all_items()
        if len(targets) != len(followers):
            self.log("[WARN] Match : target/follower counts differ "
                     "({0} vs {1}) - matching {2} pair(s)".format(
                         len(targets), len(followers),
                         min(len(targets), len(followers))))

        translate = self.cb_mt_translate.isChecked()
        rotate = self.cb_mt_rotate.isChecked()
        scale = self.cb_mt_scale.isChecked()
        parent = self.cb_mt_parent.isChecked()
        if not (translate or rotate or scale or parent):
            self.log("[WARN] Match : no channel selected "
                     "(Translation/Rotation/Scale/Parent all off)")
            return

        def _do():
            matched, skipped = mch_mgr.match(
                targets, followers,
                translate=translate, rotate=rotate,
                scale=scale, parent=parent)
            self.log("       {0} matched, {1} skipped [{2}]".format(
                matched, skipped,
                "".join(c for c, on in (
                    ("T", translate), ("R", rotate),
                    ("S", scale), ("P", parent)) if on)))

        self._run("Match", _do)

    def on_match_create(self, ctl_type):
        targets = self.tsl_match_tgt.get_all_items()

        def _do():
            created = mch_mgr.create_and_match(targets, ctl_type)
            # 생성한 컨트롤을 Followers 목록에 채우고 씬에서 선택.
            self.tsl_match_flw.set_items(created)
            if created:
                cmds.select(created)
            self.log("       created and matched {0} {1}(s)".format(
                len(created), ctl_type))

        self._run("Create {0}".format(ctl_type), _do)

    def on_match_swap(self):
        targets = self.tsl_match_tgt.get_all_items()
        followers = self.tsl_match_flw.get_all_items()
        self.tsl_match_tgt.set_items(followers)
        self.tsl_match_flw.set_items(targets)
        self.log("[OK] Swap : targets <-> followers")

    # ==============================================================
    # Handlers : Constrain
    # ==============================================================

    def on_constrain(self):
        targets = self.tsl_targets.get_all_items()
        followers = self.tsl_followers.get_all_items()
        maintain_offset = self.cb_con_maintain.isChecked()

        if self.cb_con_matrix.isChecked():
            translate = self.cb_mtx_t.isChecked()
            rotate = self.cb_mtx_r.isChecked()
            scale = self.cb_mtx_s.isChecked()

            def _do():
                made, errors = mtx_mgr.matrix_constraint(
                    targets, followers, maintain_offset,
                    translate, rotate, scale)
                for err in errors:
                    self.log("[WARN] {0}".format(err))
                self.log("       {0} matrix constraint(s) created".format(
                    len(made)))

            self._run("Matrix Constraint", _do)
            return

        con_type = con_mgr.CONSTRAIN_TYPES[self.rb_con_group.checkedId()][0]
        self._run("Constrain",
                  lambda: con_mgr.constrain(
                      targets, followers, con_type, maintain_offset))

    def _skin_con_type(self):
        """Skin Weight to Constraint 박스에서 선택한 constraint 타입 key."""
        return skn_mgr.SKIN_CONSTRAIN_TYPES[self.rb_skin_con_group.checkedId()][0]

    def on_skin_weight_to_constraint(self):
        vertices = self.tsl_skin_verts.get_all_items()
        followers = self.tsl_skin_followers.get_all_items()
        max_influence = self.sb_skin_max_inf.value()
        maintain_offset = self.cb_skin_maintain.isChecked()
        per_vertex = self.cb_skin_per_vertex.isChecked()
        con_type = self._skin_con_type()

        def _do():
            made = skn_mgr.skin_weight_to_constraint(
                vertices, followers, max_influence, maintain_offset, per_vertex,
                con_type)
            self.log("       {0} {1} constraint(s) created".format(
                len(made), con_type))

        self._run("Skin Weight to Constraint", _do)

    def on_skin_weight_to_locators(self):
        vertices = self.tsl_skin_verts.get_all_items()
        max_influence = self.sb_skin_max_inf.value()
        maintain_offset = self.cb_skin_maintain.isChecked()
        per_vertex = self.cb_skin_per_vertex.isChecked()
        con_type = self._skin_con_type()

        def _do():
            created, made = skn_mgr.create_locators_and_constrain(
                vertices, max_influence, maintain_offset, per_vertex, con_type)
            # 생성한 로케이터를 Followers 목록에 채우고 씬에서 선택.
            self.tsl_skin_followers.set_items(created)
            if created:
                cmds.select(created)
            self.log("       {0} locator(s) created, "
                     "{1} constraint(s) applied".format(len(created), len(made)))

        self._run("Skin Weight to Locators", _do)

    def on_group_create(self):
        objs = self.tsl_group_objs.get_all_items()
        count = self.sb_group_count.value()
        suffix = self.le_group_suffix.text().strip()
        padding = self.sb_group_padding.value()
        match_type = (self.rb_group_type.checkedId() == 1)
        do_parent = self.cb_group_parent.isChecked()
        do_child = self.cb_group_child.isChecked()

        def _do():
            created, warns = grp_mgr.create_offset_nodes(
                objs, count=count, suffix=suffix, match_type=match_type,
                create_parent=do_parent, create_child=do_child, padding=padding)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            self.log("       {0} node(s) created for {1} object(s)".format(
                len(created), len(objs)))
            # 생성한 노드를 씬에서 선택.
            if created:
                cmds.select(created)

        self._run("Group Create", _do)

    def on_transfer_constraint(self):
        cons = self.tsl_cxfer_cons.get_all_items()
        objs = self.tsl_cxfer_objs.get_all_items()

        def _do():
            created, warns = cxfer_mgr.transfer_constraints(cons, objs)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            self.log("       {0} constraint(s) transferred".format(len(created)))

        self._run("Constraint Transfer", _do)

    # ==============================================================
    # Handlers : Target Replace
    # ==============================================================

    def _tedit_picked_targets(self, warn=False):
        """Targets 목록에서 **보이면서 선택된** 타깃 이름들.

        Qt 는 필터로 숨긴 항목의 선택도 유지하므로, 가려진 것까지 교체해 버리지
        않도록 걸러 낸다. 표시 텍스트에는 '[2/3]' 같은 사용 횟수가 붙으므로 실제
        노드 이름은 항목 데이터에서 꺼낸다.
        """
        names = []
        hidden = 0
        for item in self.lw_tedit_targets.selectedItems():
            if item.isHidden():
                hidden += 1
                continue
            names.append(item.data(Qt.UserRole) or item.text())
        if warn and hidden:
            self.log("[INFO] {0} picked target(s) hidden by the filter were "
                     "skipped".format(hidden))
        return names

    def _tedit_constraints(self, warn=False):
        """작업 대상 constraint 이름들 — 리스트에서 **고른 항목**, 없으면 전체.

        한 리스트로 여러 constraint 를 다루다 보면 그중 일부에만 타깃을 붙이고 싶을
        때가 많다. 고른 게 없으면 예전처럼 리스트 전체를 쓴다.
        """
        picked = self.tsl_tedit_cons.selected_items()
        if picked:
            if warn:
                self.log("[INFO] using {0} picked constraint(s) of {1}".format(
                    len(picked), self.tsl_tedit_cons.count()))
            return picked
        return self.tsl_tedit_cons.get_all_items()

    def on_tedit_list(self):
        cons = self._tedit_constraints(warn=True)
        if not cons:
            self.log("[ERR] List Targets : constraint list is empty")
            return
        try:
            rows, warns = ctgt_mgr.list_targets(cons)
        except Exception as e:
            self.log("[ERR] List Targets : {0}".format(e))
            cmds.warning(str(e))
            return

        for w in warns:
            self.log("[WARN] {0}".format(w))

        self.lw_tedit_targets.clear()
        for row in rows:
            item = QListWidgetItem("{0}   [{1}/{2}]".format(
                row["name"], len(row["constraints"]), row["total"]))
            item.setData(Qt.UserRole, row["name"])
            item.setToolTip("Used by:\n  {0}".format(
                "\n  ".join(row["constraints"])))
            self.lw_tedit_targets.addItem(item)

        shown, total = self.flt_tedit.refresh()
        msg = "[OK] List Targets : {0} target(s)".format(total)
        if shown != total:
            msg += " - filter '{0}' shows {1}".format(
                self.flt_tedit.text().strip(), shown)
        self.log(msg)

    def on_tedit_select(self):
        picked = self._tedit_picked_targets(warn=True)
        if not picked:
            self.log("[ERR] Select : pick target(s) in the Targets list")
            return
        try:
            cmds.select(picked, replace=True)
        except Exception as e:
            self.log("[ERR] Select : {0}".format(e))
            cmds.warning(str(e))
            return
        self.log("[OK] Select : {0} target(s)".format(len(picked)))

    def _tedit_refresh(self):
        """편집 결과가 바로 보이도록 Targets 목록을 다시 채운다."""
        if self.tsl_tedit_cons.count():
            self.on_tedit_list()

    def on_replace_target(self):
        cons = self._tedit_constraints(warn=True)
        picked = self._tedit_picked_targets(warn=True)
        new_targets = self.tsl_tedit_new.get_all_items()
        maintain_offset = self.cb_tedit_keep.isChecked()
        rename_weight = self.cb_tedit_rename.isChecked()

        def _do():
            results, warns = ctgt_mgr.replace_targets(
                cons, picked, new_targets, maintain_offset, rename_weight)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            for r in results:
                self.log("       {0} : {1} -> {2}{3}".format(
                    r["constraint"], r["old"], r["new"],
                    "  ({0})".format(r["note"]) if r["note"] else ""))
            self.log("       {0} target slot(s) replaced".format(len(results)))

        self._run("Replace Target", _do)
        self._tedit_refresh()

    def on_add_target(self):
        cons = self._tedit_constraints(warn=True)
        new_targets = self.tsl_tedit_new.get_all_items()
        maintain_offset = self.cb_tedit_keep.isChecked()
        weight = self.sb_tedit_weight.value()

        def _do():
            results, warns = ctgt_mgr.add_targets(
                cons, new_targets, maintain_offset, weight)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            for r in results:
                self.log("       {0} : + {1}{2}".format(
                    r["constraint"], r["target"],
                    "  ({0})".format(r["note"]) if r["note"] else ""))
            self.log("       {0} target(s) added".format(len(results)))

        self._run("Add Target", _do)
        self._tedit_refresh()

    def on_remove_target(self):
        cons = self._tedit_constraints(warn=True)
        picked = self._tedit_picked_targets(warn=True)
        maintain_offset = self.cb_tedit_keep.isChecked()
        delete_empty = self.cb_tedit_delete_empty.isChecked()

        def _do():
            results, warns = ctgt_mgr.remove_targets(
                cons, picked, maintain_offset, delete_empty)
            for w in warns:
                self.log("[WARN] {0}".format(w))
            removed = 0
            for r in results:
                removed += len(r["removed"])
                self.log("       {0} : - {1}{2}".format(
                    r["constraint"], ", ".join(r["removed"]),
                    "  ({0})".format(r["note"]) if r["note"] else ""))
            deleted = len([r for r in results if r["deleted"]])
            self.log("       {0} target(s) removed from {1} constraint(s)"
                     "{2}".format(removed, len(results),
                                  ", {0} constraint(s) deleted".format(deleted)
                                  if deleted else ""))

        self._run("Remove Target", _do)
        self._tedit_refresh()

    # ==============================================================
    # Handlers : Connect
    # ==============================================================

    def on_list_attrs(self, role):
        w = self._connect_widgets[role]
        objs = w["tsl"].get_all_items()
        if not objs:
            self.log("[ERR] List Attributes : object list is empty")
            return
        try:
            attrs = cnt_mgr.list_attrs(objs[0])
        except Exception as e:
            self.log("[ERR] List Attributes : {0}".format(e))
            cmds.warning(str(e))
            return
        w["attrs"].clear()
        w["attrs"].addItems(attrs)
        # 새로 채운 항목에도 현재 필터를 다시 먹인다(필터가 유지되도록).
        shown, total = w["filter"].refresh()

        msg = "[OK] List Attributes : {0} ({1} attrs)".format(objs[0], total)
        if shown != total:
            msg += " - filter '{0}' shows {1}".format(w["filter"].text().strip(), shown)
        self.log(msg)

    # ==============================================================
    # Handlers : Attribute
    # ==============================================================

    def _selected_src_attrs(self, warn=False):
        """Attribute 탭에서 **보이면서 선택된** 어트리뷰트 이름들.

        Qt 는 숨긴 항목의 선택을 유지하므로, 필터에 가려진 것까지 복사해 버리지
        않도록 걸러 낸다. warn=True 면 가려진 선택 수를 로그로 알린다(미리보기처럼
        자주 불리는 곳에서는 로그를 내지 않는다).
        """
        names, hidden = self.flt_attr_src.visible_selected()
        if warn and hidden:
            self.log("[INFO] {0} selected attribute(s) hidden by the filter "
                     "were skipped".format(hidden))
        return names

    def _update_attr_preview(self):
        """Prefix/Suffix 를 적용한 새 이름을 첫 선택 항목으로 미리 보여준다."""
        selected = self._selected_src_attrs()
        if not selected:
            self.lbl_attr_preview.setText("Preview : -")
            return
        new_name = att_mgr.build_new_name(
            selected[0],
            self.le_attr_prefix.text().strip(),
            self.le_attr_suffix.text().strip())
        more = ""
        if len(selected) > 1:
            more = "   (+{0} more)".format(len(selected) - 1)
        self.lbl_attr_preview.setText(
            "Preview : {0}  ->  {1}{2}".format(selected[0], new_name, more))

    def on_attr_list(self):
        objs = self.tsl_attr_src.get_all_items()
        if not objs:
            self.log("[ERR] List Attributes : Source list is empty")
            return

        user_only = self.cb_attr_user_only.isChecked()
        try:
            # 검색은 더 이상 조회 인자가 아니다 — 전부 받아 와서 Filter 로 거른다.
            attrs = att_mgr.list_attributes(objs[0], user_only)
        except Exception as e:
            self.log("[ERR] List Attributes : {0}".format(e))
            cmds.warning(str(e))
            return

        self.lw_attr_src.clear()
        self.lw_attr_src.addItems(attrs)
        # 새로 채운 항목에도 현재 필터를 다시 먹인다(필터가 유지되도록).
        shown, total = self.flt_attr_src.refresh()
        self._update_attr_preview()

        msg = "[OK] List Attributes : {0} ({1} attr(s){2})".format(
            objs[0], total, ", user defined" if user_only else "")
        if shown != total:
            msg += " - filter '{0}' shows {1}".format(
                self.flt_attr_src.text().strip(), shown)
        self.log(msg)

    def on_attr_copy(self):
        srcs = self.tsl_attr_src.get_all_items()
        source = srcs[0] if srcs else ""
        attrs = self._selected_src_attrs(warn=True)
        targets = self.tsl_attr_tgt.get_all_items()
        prefix = self.le_attr_prefix.text().strip()
        suffix = self.le_attr_suffix.text().strip()
        copy_value = self.cb_attr_value.isChecked()

        def _do():
            created, skipped = att_mgr.copy_attributes(
                source, attrs, targets, prefix, suffix, copy_value)
            for target, name, reason in skipped:
                self.log("[WARN] {0}.{1} : {2}".format(target, name, reason))
            self.log("       {0} attribute(s) created on {1} target(s)".format(
                len(created), len(targets)))

        self._run("Copy Attributes", _do)

    def _filtered_attrs(self, role, label):
        """Connect 탭 한쪽의 **보이면서 선택된** 어트리뷰트.

        Qt 는 숨긴 항목의 선택을 유지하므로, 필터에 가려진 항목까지 연결해 버리지
        않도록 여기서 걸러 낸다. 가려진 선택이 있으면 조용히 넘기지 않고 알린다.
        """
        names, hidden = self._connect_widgets[role]["filter"].visible_selected()
        if hidden:
            self.log("[INFO] {0} : {1} selected attribute(s) hidden by the filter "
                     "were skipped".format(label, hidden))
        return names

    def on_match_from_source(self):
        """소스에서 고른 어트리뷰트와 이름이 가장 비슷한 destination 어트리뷰트를 찾는다.

        찾은 것들을 **소스 순서 그대로** destination 목록 맨 위로 옮기고 선택한다.
        connect_attrs 가 `src[i] <-> dst[i]` 를 순서로 짝짓기 때문에, 이 상태에서 바로
        'Connect Source to Destination' 을 누르면 그대로 연결된다.
        """
        src = self._connect_widgets["src"]
        dst = self._connect_widgets["dst"]

        # 소스: 고른 게 있으면 그것, 없으면 지금 보이는 전체.
        sources, hidden = src["filter"].visible_selected()
        if hidden:
            self.log("[INFO] Match : {0} selected source attribute(s) hidden by the "
                     "filter were skipped".format(hidden))
        if not sources:
            sources = src["filter"].visible_texts()
            if sources:
                self.log("[INFO] Match : nothing selected in Source - using all "
                         "{0} visible attribute(s)".format(len(sources)))

        if not sources:
            self.log("[ERR] Match from Source : source attribute list is empty. "
                     "Press 'List Attributes' on the Source side first.")
            return

        dst_list = dst["attrs"]
        candidates = [dst_list.item(i).text() for i in range(dst_list.count())]
        if not candidates:
            self.log("[ERR] Match from Source : destination attribute list is empty. "
                     "Press 'List Attributes' on the Destination side first.")
            return

        unique = self.cb_match_unique.isChecked()
        min_score = self.sb_match_min.value()

        try:
            matches, unmatched = attr_match.match_attributes(
                sources, candidates, unique=unique, min_score=min_score)
        except Exception as e:
            self.log("[ERR] Match from Source : {0}".format(e))
            cmds.warning(str(e))
            return

        # 매칭된 것을 소스 순서대로 앞에, 나머지는 원래 순서대로 뒤에 놓는다.
        matched_rows = [m["index"] for m in matches]
        taken = set(matched_rows)
        ordered = ([candidates[i] for i in matched_rows]
                   + [c for i, c in enumerate(candidates) if i not in taken])

        # 선택이 필터에 가려지면 연결 대상에서 빠지므로 필터를 비운다.
        if dst["filter"].text().strip():
            self.log("[INFO] Match : destination filter cleared so the matched "
                     "attributes are all visible.")
            dst["filter"].clear()

        dst_list.clear()
        dst_list.addItems(ordered)
        dst["filter"].refresh()

        dst_list.clearSelection()
        for row in range(len(matches)):
            dst_list.item(row).setSelected(True)
        if matches:
            dst_list.scrollToItem(dst_list.item(0))

        self.log("[OK] Match from Source : {0}/{1} matched ({2}, min {3:.2f})".format(
            len(matches), len(sources),
            "unique" if unique else "duplicates allowed", min_score))
        for m in matches:
            self.log("       {0}  ->  {1}   ({2:.2f}{3})".format(
                m["source"], m["target"], m["score"],
                ", ambiguous" if m["ambiguous"] else ""))
        for u in unmatched:
            if u["best"]:
                self.log("[WARN] no match for '{0}' - closest was '{1}' "
                         "({2:.2f} < {3:.2f})".format(
                             u["source"], u["best"], u["score"], min_score))
            else:
                self.log("[WARN] no match for '{0}' - nothing similar in the "
                         "destination list.".format(u["source"]))

        if unmatched:
            self.log("[INFO] Match : source and destination selections no longer "
                     "line up 1:1 ({0} source attribute(s) unmatched). Deselect "
                     "those on the Source side before connecting.".format(
                         len(unmatched)))

    def on_connect_attrs(self):
        """Source 어트리뷰트 -> Destination 어트리뷰트."""
        self._connect_in_direction("src", "dst")

    def on_connect_attrs_reverse(self):
        """Destination 어트리뷰트 -> Source 어트리뷰트 (역방향)."""
        self._connect_in_direction("dst", "src")

    def _connect_in_direction(self, from_role, to_role):
        """한쪽 패널을 드라이버로, 다른 쪽을 구동 대상으로 연결한다.

        두 방향의 차이는 `connect_attrs` 에 넘기는 **인자 순서뿐**이다. 브로드캐스트
        패턴(오브젝트 1개 -> 다수 등)도 그대로 뒤집혀 적용된다.

        버튼 두 개를 각각 이 메서드로 감싼 이유: `clicked` 시그널은 `checked`(bool)를
        넘기므로, 방향을 기본 인자로 받는 단일 슬롯에 직접 연결하면 그 bool 이 방향
        인자로 들어갈 수 있다.
        """
        from_label = self.ROLE_LABELS[from_role]
        to_label = self.ROLE_LABELS[to_role]

        from_objs = self._connect_widgets[from_role]["tsl"].get_all_items()
        to_objs = self._connect_widgets[to_role]["tsl"].get_all_items()
        from_attrs = self._filtered_attrs(from_role, from_label)
        to_attrs = self._filtered_attrs(to_role, to_label)

        def _do():
            count, mode, report = cnt_mgr.connect_attrs(
                from_objs, to_objs, from_attrs, to_attrs)
            self.log("       {0} connection(s) [{1}]  {2} -> {3}".format(
                count, mode, from_label, to_label))
            self._log_connect_report(report, from_label, to_label)

        self._run("Connect {0} to {1}".format(from_label, to_label), _do)

    def _log_connect_report(self, report, from_label, to_label):
        """개수가 안 맞아 남겨 둔 항목과 실패한 연결을 로그로 알린다.

        조용히 넘기면 "왜 일부만 연결됐지?" 가 되므로, 무엇이 남았는지 이름까지 찍는다.
        """
        for key, label in (("unused_driver_attrs", from_label + " attribute"),
                           ("unused_driven_attrs", to_label + " attribute"),
                           ("unused_driver_objs", from_label + " object"),
                           ("unused_driven_objs", to_label + " object")):
            left = report.get(key) or []
            if not left:
                continue
            shown = ", ".join(left[:8])
            if len(left) > 8:
                shown += ", ... (+{0})".format(len(left) - 8)
            self.log("[INFO] {0} {1}(s) had no counterpart and were left "
                     "untouched: {2}".format(len(left), label, shown))

        for src_plug, dst_plug, reason in (report.get("failed") or []):
            self.log("[WARN] could not connect {0} -> {1} : {2}".format(
                src_plug, dst_plug, reason))

    def on_connect_52_facial(self):
        src = self._connect_widgets["src"]
        dst = self._connect_widgets["dst"]
        src_objs = src["tsl"].get_all_items()
        dst_objs = dst["tsl"].get_all_items()

        def _do():
            connected, skipped = cnt_mgr.connect_52_facial(src_objs, dst_objs)
            self.log("       {0} connected, {1} skipped".format(connected, skipped))

        self._run("Connect 52 Facial Target", _do)

    # ==============================================================
    # Handlers : List Connected
    # ==============================================================

    def on_list_stream(self, upstream):
        objs = self.tsl_stream_objs.get_all_items()
        if not objs:
            self.log("[ERR] List Stream : object list is empty")
            return
        self._stream_upstream = upstream
        try:
            types = stm_mgr.list_stream_types(objs, upstream)
        except Exception as e:
            self.log("[ERR] List Stream : {0}".format(e))
            cmds.warning(str(e))
            return
        self.list_types.clear()
        self.list_types.addItems(types)
        self.list_nodes.clear()
        self.log("[OK] List {0}Stream : {1} type(s)".format(
            "Up" if upstream else "Down", len(types)))

    def on_search_nodes(self):
        objs = self.tsl_stream_objs.get_all_items()
        types = self._selected_texts(self.list_types)
        if not objs:
            self.log("[ERR] Search Nodes : object list is empty")
            return
        if not types:
            self.log("[ERR] Search Nodes : select one or more types")
            return
        try:
            nodes = stm_mgr.nodes_by_types(objs, types, self._stream_upstream)
        except Exception as e:
            self.log("[ERR] Search Nodes : {0}".format(e))
            cmds.warning(str(e))
            return
        self.list_nodes.clear()
        self.list_nodes.addItems(nodes)
        self.log("[OK] Search Nodes : {0} node(s)".format(len(nodes)))

    def on_nodes_selection_changed(self):
        sel = self._selected_texts(self.list_nodes)
        try:
            if sel:
                cmds.select(sel)
            else:
                cmds.select(clear=True)
        except Exception as e:
            cmds.warning(str(e))

    # ==============================================================
    # Handlers : Connect Closest
    # ==============================================================

    def on_get_closest(self):
        """각 Driver 의 가장 가까운 오브젝트를 찾아 Driven 을 driver 순서대로 채운다.

        후보 풀은 Driven 리스트에 항목이 있으면 그것을, 없으면 현재 씬 선택을 쓴다.
        결과(찾은 오브젝트)는 뷰포트에서도 선택해 눈으로 확인할 수 있게 한다.
        매칭 로직은 connect_closest 와 동일(greedy 1:1)이라 Connect 결과의 미리보기다.
        """
        drivers = self.cc_driver.get_all_items()
        self.log("--- Get Closest ---")

        if not drivers:
            self.log("[WARN] Driver list is empty. Add objects to the Driver list.")
            return

        candidates = self.cc_driven.get_all_items()
        source = "Driven list"
        if not candidates:
            candidates = cmds.ls(sl=True, fl=True) or []
            source = "current selection"
        if not candidates:
            self.log("[WARN] No candidates. Fill the Driven list or "
                     "select objects in the scene.")
            return
        self.log("Candidate pool: {0} ({1} object(s))".format(
            source, len(candidates)))

        pairs, errors = find_closest_for_drivers(drivers, candidates)

        for err in errors:
            self.log("[WARN] {0}".format(err))

        if not pairs:
            self.log("No closest match found.")
            return

        drivens = [driven for _driver, driven, _dist in pairs]
        self.cc_driven.set_items(drivens)

        for driver, driven, dist in pairs:
            self.log("Closest: {0} -> {1} (dist {2:.3f})".format(
                driver, driven, dist))

        # 발견 검증용: 찾은 오브젝트를 뷰포트에서 선택.
        try:
            cmds.select(drivens, replace=True)
        except Exception:
            pass

        self.log("Done. {0} closest object(s) listed in Driven.".format(
            len(pairs)))

    def on_connect_closest(self):
        drivers = self.cc_driver.get_all_items()
        drivens = self.cc_driven.get_all_items()
        keys = [key for key, cb in self.cc_checkboxes.items() if cb.isChecked()]
        maintain_offset = self.cc_maintain.isChecked()

        self.log("--- Connect Closest ---")

        results, errors = connect_closest(
            drivers, drivens, keys, maintain_offset)

        for err in errors:
            self.log("[WARN] {0}".format(err))

        for r in results:
            self.log(
                "Connected: {driver} -> {driven} "
                "(dist {dist:.3f}, {cons})".format(
                    driver=r["driver"],
                    driven=r["driven"],
                    dist=r["distance"],
                    cons=", ".join(r["constraints"]),
                )
            )

        self.log("Done. {0} connection(s) made.".format(len(results)))
