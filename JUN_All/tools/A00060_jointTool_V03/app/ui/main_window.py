# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-25
# A00060_jointTool_V03 - Qt UI
#
# A00060_jointTool_V02 의 **탭 재분류판**.
# 기능은 하나도 빼거나 더하지 않고, 평평한 상위 탭 5개(그 안에 접이식 6섹션)를
# **상위 탭 = 카테고리 / 하위 탭 = 기능** 의 2단 구조로 다시 나눈다.
# 계획서: docs/plans/A00060_jointTool_V02_tab_reorg_plan.md
#
#   Create : From Curve  · From Object · Divide          (조인트가 생긴다)
#   Orient : Aim         · Set Orient  · Orient / Rotate (방향만 바뀐다)
#   Chain  : Reverse     · IK Edit                       (체인 구조를 고친다)
#   Curve  : Edit Curve  · Clusters                      (커브·디포머를 다룬다)
#   Select : Unused Joints                               (씬을 바꾸지 않는다)
#
# 이전 이력(v01.00~v01.05)은 A00060_jointTool_V02/CHANGELOG.md 참고.
# 버전은 폴더명(_V03)에 맞춰 03.xx 로 센다 — V02 가 폴더는 _V02 인데
# 버전이 01.xx 로 남아 있던 예외를 여기서 바로잡는다.
# v03.00 : 탭 재분류. V02 의 Curve 탭(조인트 생성 + 오리엔트 + 클러스터가 뒤섞임)과
#          Hair 탭(커브 편집 + 체인 편집 + 선택이 뒤섞임)을 해체하고, 다섯 기능이
#          나눠 쓰던 공용 리스트(tsl_curve / tsl_hair)를 하위 탭마다 자기 리스트로 쪼갰다.
#          접이식(CollapsibleBox)은 전부 하위 탭이 되어 사라졌다.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00060_jointTool_V03.app.config.version import VERSION, LAST_UPDATE
from tools.A00060_jointTool_V03.app.core import curve_joint_manager as crv_mgr
from tools.A00060_jointTool_V03.app.core import obj_joint_manager as obj_mgr
from tools.A00060_jointTool_V03.app.core import divide_manager as div_mgr
from tools.A00060_jointTool_V03.app.core import aim_manager as aim_mgr
from tools.A00060_jointTool_V03.app.core import hair_manager as hair_mgr
from tools.A00060_jointTool_V03.app.core import ik_edit_manager as ike_mgr


# 재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00060_jointTool_V03_window"

# point type 라디오 -> core enum
_POINT_TYPES = [
    ("Control Vertex (Omit [1], [-2])", crv_mgr.POINT_TYPE_CV_OMIT),
    ("Control Vertex", crv_mgr.POINT_TYPE_CV),
    ("Edit Point", crv_mgr.POINT_TYPE_EP),
]

# IK Edit 토글 버튼의 상태 표시 (A00275 Edit Mesh 와 같은 규칙)
IK_EDIT_ON_STYLE = (
    "QPushButton { background-color: #c85a28; color: #ffffff;"
    " border: 1px solid #f09050; font-weight: bold; }"
    "QPushButton:hover { background-color: #d96a34; }"
    "QPushButton:pressed { background-color: #a8441c; }"
)
IK_EDIT_ON_TEXT = "EDIT ON  -  move the chain, then press again"
IK_EDIT_OFF_TEXT = "EDIT IK CHAIN"

# 폴 벡터 갱신 방법 라벨 -> core 상수
_PV_MODES = [
    ("Constraint offset (keep the target where it is)", ike_mgr.PV_MODE_OFFSET),
    ("Move the pole vector target", ike_mgr.PV_MODE_TARGET),
]

# 핸들을 무엇으로 옮길지
_SNAP_MODES = [
    ("IK handle", ike_mgr.SNAP_HANDLE),
    ("Handle's parent", ike_mgr.SNAP_PARENT),
]


# ==================================================================
# 탭 분류표 — 상위 탭 = 카테고리, 하위 탭 = 기능
#
# 탭을 더할 때는 아래 표에 줄만 넣는다. 상위 탭에 기능 하나를 직접 올리지 않는다.
# (하위 탭 라벨, 툴팁 = 전체 이름/설명, 빌더 메서드 이름)
# ==================================================================

CREATE_PAGES = (
    ("From Curve",
     "From Curve - build a joint chain on the points of a NURBS curve.",
     "_build_create_from_curve_tab"),
    ("From Object",
     "From Object - build a joint at each listed object or vertex, with axis options.",
     "_build_create_from_object_tab"),
    ("Divide",
     "Divide - build evenly spaced joints between a start and an end joint.",
     "_build_divide_tab"),
)

ORIENT_PAGES = (
    ("Aim",
     "Aim - re-orient a chain so that the chosen axis points at a pole target.",
     "_build_aim_tab"),
    ("Set Orient",
     "Set Orient - set jointOrient on a chain by axis and degree.",
     "_build_set_orient_tab"),
    ("Orient / Rotate",
     "Orient / Rotate - swap values between jointOrient and rotate.",
     "_build_orient_swap_tab"),
)

CHAIN_PAGES = (
    ("Reverse",
     "Reverse - rebuild a joint chain in the opposite order.",
     "_build_chain_reverse_tab"),
    ("IK Edit",
     "IK Edit - edit the bone chain while the IK handle and its pole vector stay in place.",
     "_build_ik_edit_tab"),
)

CURVE_PAGES = (
    ("Edit Curve",
     "Edit Curve - separate, remove by length, and rebuild NURBS curves.",
     "_build_curve_edit_tab"),
    ("Clusters",
     "Clusters - create one cluster deformer per CV of the listed curves.",
     "_build_curve_cluster_tab"),
)

SELECT_PAGES = (
    ("Unused Joints",
     "Unused Joints - select the listed joints that no skinCluster uses.",
     "_build_select_unused_tab"),
)

# (상위 탭 라벨, 툴팁, 하위 페이지 표, 하위 QTabWidget 을 담을 속성 이름)
CATEGORIES = (
    ("Create",
     "Create new joints.",
     CREATE_PAGES, "create_tabs"),
    ("Orient",
     "Change the orientation of joints that already exist. Nothing is moved and no "
     "joint is added.",
     ORIENT_PAGES, "orient_tabs"),
    ("Chain",
     "Rebuild or edit a joint chain that already exists.",
     CHAIN_PAGES, "chain_tabs"),
    ("Curve",
     "Prepare the curves that joints get built on. No joint is touched.",
     CURVE_PAGES, "curve_tabs"),
    ("Select",
     "Find joints. The scene is not changed.",
     SELECT_PAGES, "select_tabs"),
)

# CHAIN_PAGES 안에서 IK Edit 의 자리. 하위 탭은 위젯이 아니라 이 상수로 판단한다
# (chain_tabs.widget(i) 는 페이지가 아니라 QScrollArea 래퍼를 돌려준다).
IKE_SUB_INDEX = 1


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 560
        self.win_height = 720
        self.win_title = "Joint Tool v{0}".format(VERSION)

        self.resize(self.win_width, self.win_height)

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

        # 탭 : 상위 = 카테고리, 하위 = 기능
        self.tabs = QTabWidget()
        self.tabs.tabBar().setElideMode(Qt.ElideRight)

        for label, tip, pages, attr in CATEGORIES:
            index = self.tabs.addTab(self._build_category_tab(pages, attr), label)
            self.tabs.setTabToolTip(index, tip)
            if label == "Chain":
                self.chain_page = self.tabs.widget(index)

        # IK 편집 상태는 UI 가 아니라 씬(ikHandle 노드)에 있다. 탭이 보일 때 다시 읽는다.
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.chain_tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tabs)

        main_layout.addWidget(self.te_log)

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------------------
    # 탭 골격 (A00110 / A00145 / A00275 와 같은 구성)
    # --------------------------------------------------------------

    def _build_category_tab(self, pages, attr):
        """카테고리 상위 탭 하나 - 기능들을 하위 탭으로 담는다."""
        tabs = self._build_sub_tabs(pages)
        setattr(self, attr, tabs)
        return tabs

    def _build_sub_tabs(self, pages):
        tabs = QTabWidget()
        tabs.tabBar().setElideMode(Qt.ElideRight)   # 폭이 모자라면 라벨을 자른다
        for label, tip, builder in pages:
            index = tabs.addTab(self._scrolled(getattr(self, builder)()), label)
            tabs.setTabToolTip(index, tip)
        return tabs

    def _scrolled(self, widget):
        """페이지를 스크롤 영역에 담는다 (창이 작아도 위젯이 겹치지 않도록).

        스크롤은 **하위 페이지에만** 건다 - 상위 카테고리 페이지는 QTabWidget 자체라
        스크롤이 두 겹으로 겹치지 않는다.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    def _tsl(self, title):
        """이 툴의 하위 탭이 쓰는 리스트 위젯 - 하위 탭마다 자기 것을 갖는다.

        V02 는 리스트 하나를 다섯 기능이 나눠 썼고, 그래서 같은 리스트에 커브 ·
        오브젝트 · 조인트가 번갈아 담겼다. 탭마다 자기 리스트를 두면 제목이 곧
        무엇을 담아야 하는지를 말해 준다.
        """
        return JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title=title, select_label="Select",
            show_sort=False, list_min_height=160, log_callback=self.log)

    # --------------------------------------------------------------
    # Create > From Curve
    # --------------------------------------------------------------

    def _build_create_from_curve_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_create_crv = self._tsl("Curves")
        layout.addWidget(self.tsl_create_crv)

        self.rb_point_group = QButtonGroup(self)
        for i, (label, _enum) in enumerate(_POINT_TYPES):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self.rb_point_group.addButton(rb, i)
            layout.addWidget(rb)

        self.btn_joints_to_crv = QPushButton("Joints to Crv")
        self.btn_joints_to_crv.setToolTip(
            "Create a joint at each point of the listed NURBS curves, in order.")
        self.btn_joints_to_crv.clicked.connect(self.on_joints_to_crv)
        layout.addWidget(self.btn_joints_to_crv)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Create > From Object
    # --------------------------------------------------------------

    def _build_create_from_object_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_create_obj = self._tsl("Objects")
        layout.addWidget(self.tsl_create_obj)

        self.rb_match_group = QButtonGroup(self)
        match_row = QHBoxLayout()
        for i, label in enumerate(["Connect", "Separate"]):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self.rb_match_group.addButton(rb, i)
            match_row.addWidget(rb)
        layout.addLayout(match_row)

        self.cmb_fwd_axis = self._axis_combo(["+X", "+Y", "+Z"], "+X")
        self.cmb_secd_axis = self._axis_combo(["+X", "+Y", "+Z"], "+Y")
        self.cmb_secd_ori = self._axis_combo(
            ["+X", "-X", "+Y", "-Y", "+Z", "-Z"], "+Y")

        layout.addLayout(self._labeled("Foward axis :", self.cmb_fwd_axis))
        layout.addLayout(self._labeled("Secondary axis :", self.cmb_secd_axis))
        layout.addLayout(self._labeled("Secondary axis orient :", self.cmb_secd_ori))

        # 왼쪽 = 리스트에 담긴 항목 / 오른쪽 = 지금 씬에서 선택한 것
        match_btn_row = QHBoxLayout()
        self.btn_match_obj = QPushButton("Match to Obj")
        self.btn_match_obj.setToolTip(
            "Create joints at the objects/vertices listed above.")
        self.btn_match_obj.clicked.connect(self.on_match_to_obj)
        self.btn_match_sel = QPushButton("Match to Sel")
        self.btn_match_sel.setToolTip(
            "Create joints at the objects/vertices selected in the scene right now,\n"
            "without listing them first.\n"
            "With 'Order' checked, vertices are processed in the order you picked them.")
        self.btn_match_sel.clicked.connect(self.on_match_to_sel)
        match_btn_row.addWidget(self.btn_match_obj)
        match_btn_row.addWidget(self.btn_match_sel)
        layout.addLayout(match_btn_row)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Create > Divide
    # --------------------------------------------------------------

    def _build_divide_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_div_start = self._tsl("Start")
        self.tsl_div_end = self._tsl("End")

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_div_start)
        list_row.addWidget(self.tsl_div_end)
        layout.addLayout(list_row)

        pair_row = QHBoxLayout()
        btn_sel_se = QPushButton("Select Start End")
        btn_add_se = QPushButton("Add Start End")
        btn_sel_se.clicked.connect(self.on_div_select_startend)
        btn_add_se.clicked.connect(self.on_div_add_startend)
        pair_row.addWidget(btn_sel_se)
        pair_row.addWidget(btn_add_se)
        layout.addLayout(pair_row)

        num_row = QHBoxLayout()
        num_row.addWidget(QLabel("Joints Number"))
        self.sb_div_num = QSpinBox()
        self.sb_div_num.setRange(1, 1000)
        self.sb_div_num.setValue(5)
        num_row.addWidget(self.sb_div_num)
        btn_make_div = QPushButton("Make Joint Divided")
        btn_make_div.clicked.connect(self.on_make_divided)
        num_row.addWidget(btn_make_div)
        layout.addLayout(num_row)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Orient > Aim
    # --------------------------------------------------------------

    def _build_aim_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_aim_start = self._tsl("Start")
        self.tsl_aim_end = self._tsl("End")
        self.tsl_aim_pole = self._tsl("pole tgt")

        list_row = QHBoxLayout()
        list_row.addWidget(self.tsl_aim_start)
        list_row.addWidget(self.tsl_aim_end)
        list_row.addWidget(self.tsl_aim_pole)
        layout.addLayout(list_row)

        pair_row = QHBoxLayout()
        btn_sel_se = QPushButton("Select Start End")
        btn_add_se = QPushButton("Add Start End")
        btn_sel_se.clicked.connect(self.on_aim_select_startend)
        btn_add_se.clicked.connect(self.on_aim_add_startend)
        pair_row.addWidget(btn_sel_se)
        pair_row.addWidget(btn_add_se)
        layout.addLayout(pair_row)

        # 옵션 : pole tgt 을 향할 보조축 (primary 는 +X down-bone 고정)
        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("Aim axis :"))
        self.cmb_aim_axis = self._axis_combo(["X", "Y", "Z"], "Y")
        opt_row.addWidget(self.cmb_aim_axis)
        opt_row.addStretch(1)
        layout.addLayout(opt_row)

        btn_make_aim = QPushButton("Make Joint Aim")
        btn_make_aim.clicked.connect(self.on_make_aim)
        layout.addWidget(btn_make_aim)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Orient > Set Orient
    # --------------------------------------------------------------

    def _build_set_orient_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_orient_set = self._tsl("Joints")
        layout.addWidget(self.tsl_orient_set)

        self.cmb_orient_axis = self._axis_combo(["X", "Y", "Z"], "X")
        layout.addLayout(self._labeled("Orient axis :", self.cmb_orient_axis))

        self.dsb_orient_deg = QDoubleSpinBox()
        self.dsb_orient_deg.setRange(-360.0, 360.0)
        self.dsb_orient_deg.setDecimals(3)
        layout.addLayout(self._labeled("Orient degree :", self.dsb_orient_deg))

        self.btn_set_orient = QPushButton("Set joints orientation")
        self.btn_set_orient.setToolTip(
            "Unparent the chain from the leaf up, write jointOrient on every joint,\n"
            "then parent it back.")
        self.btn_set_orient.clicked.connect(self.on_set_orient)
        layout.addWidget(self.btn_set_orient)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Orient > Orient / Rotate
    # --------------------------------------------------------------

    def _build_orient_swap_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_orient_swap = self._tsl("Joints")
        layout.addWidget(self.tsl_orient_swap)

        self.btn_ori_to_rot = QPushButton("joint orient to rotate")
        self.btn_ori_to_rot.setToolTip(
            "Zero jointOrient and add its value into rotate.")
        self.btn_ori_to_rot.clicked.connect(self.on_swap_ori_to_rot)
        layout.addWidget(self.btn_ori_to_rot)

        self.btn_rot_to_ori = QPushButton("rotate to joint orient")
        self.btn_rot_to_ori.setToolTip(
            "Zero rotate and add its value into jointOrient.")
        self.btn_rot_to_ori.clicked.connect(self.on_swap_rot_to_ori)
        layout.addWidget(self.btn_rot_to_ori)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Chain > Reverse
    # --------------------------------------------------------------

    def _build_chain_reverse_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_chain_reverse = self._tsl("Root Joints")
        layout.addWidget(self.tsl_chain_reverse)

        self.cb_remove_origin = QCheckBox("Remove origin")
        self.cb_remove_origin.setChecked(True)
        self.cb_remove_origin.setToolTip(
            "Delete the original chain once the reversed one is built.")
        layout.addWidget(self.cb_remove_origin)

        self.btn_reverse = QPushButton("Reverse joint chain")
        self.btn_reverse.setToolTip(
            "Rebuild each listed root chain in the opposite order, keeping the world\n"
            "position and the radius of every joint.")
        self.btn_reverse.clicked.connect(self.on_chain_reverse)
        layout.addWidget(self.btn_reverse)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Chain > IK Edit
    # --------------------------------------------------------------

    def _build_ik_edit_tab(self):
        """이미 설치된 ikHandle 을 그대로 둔 채 본 체인을 고치는 탭.

        토글 한 번으로 IK 를 내리고, 다시 눌러 확정할 때 핸들과 폴 벡터를 편집된 체인에
        맞춘다. 상태는 UI 가 아니라 ikHandle 노드에 있으므로 툴을 껐다 켜도 이어진다.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.ike_targets = []

        # ---- 대상 ----
        grp_tgt = QGroupBox("IK Handle")
        tgt_layout = QVBoxLayout(grp_tgt)

        row = QHBoxLayout()
        self.btn_ike_load = QPushButton("Load Selection")
        self.btn_ike_load.setToolTip(
            "Pick up IK handles from the current selection. You can select the handle\n"
            "itself, any joint of the IK chain, or the control that drives the handle.")
        self.btn_ike_load.clicked.connect(self.on_ike_load)
        row.addWidget(self.btn_ike_load)

        self.btn_ike_clear = QPushButton("Clear")
        self.btn_ike_clear.clicked.connect(self.on_ike_clear)
        row.addWidget(self.btn_ike_clear)

        self.btn_ike_select = QPushButton("Select Handle")
        self.btn_ike_select.setToolTip("Select the loaded handles in the viewport.")
        self.btn_ike_select.clicked.connect(self.on_ike_select)
        row.addWidget(self.btn_ike_select)
        tgt_layout.addLayout(row)

        self.lbl_ike_target = QLabel("No IK handle loaded.")
        self.lbl_ike_target.setWordWrap(True)
        tgt_layout.addWidget(self.lbl_ike_target)

        layout.addWidget(grp_tgt)

        # ---- 옵션 ----
        grp_opt = QGroupBox("On Finish")
        opt_layout = QVBoxLayout(grp_opt)

        self.cmb_ike_pv = QComboBox()
        for label, _ in _PV_MODES:
            self.cmb_ike_pv.addItem(label)
        self.cmb_ike_pv.setToolTip(
            "How to point the pole vector at the edited chain plane.\n\n"
            "Constraint offset : the constraint and its target stay exactly where they\n"
            "  are and only the offset is updated - the same idea as the Update Offset\n"
            "  button on a parent constraint in Maya 2024.\n"
            "Move the pole vector target : the target object is moved onto the new\n"
            "  chain plane and the offset is left at zero. Cleaner for a rig that\n"
            "  should carry no baked offsets, but it moves an animator's control.")
        opt_layout.addLayout(self._labeled("Pole vector", self.cmb_ike_pv))

        self.cmb_ike_snap = QComboBox()
        for label, _ in _SNAP_MODES:
            self.cmb_ike_snap.addItem(label)
        self.cmb_ike_snap.setToolTip(
            "What to move so that the handle sits on the new end of the chain.\n\n"
            "IK handle : move the handle itself.\n"
            "Handle's parent : move the parent instead, so a handle that sits at local\n"
            "  zero under an IK control stays at local zero.")
        opt_layout.addLayout(self._labeled("Snap", self.cmb_ike_snap))

        self.chk_ike_preferred = QCheckBox("Set preferred angles from the edited pose")
        self.chk_ike_preferred.setChecked(True)
        self.chk_ike_preferred.setToolTip(
            "Runs Set Preferred Angle on every chain joint, so later solves keep bending\n"
            "the way the edited chain bends.")
        opt_layout.addWidget(self.chk_ike_preferred)

        layout.addWidget(grp_opt)

        # ---- 토글 ----
        self.btn_ike_edit = QPushButton(IK_EDIT_OFF_TEXT)
        self.btn_ike_edit.setCheckable(True)
        self.btn_ike_edit.setMinimumHeight(44)
        self.btn_ike_edit.setToolTip(
            "ON  : IK is switched off for this handle so the chain joints move freely.\n"
            "OFF : the handle is snapped to the new end of the chain and the pole vector\n"
            "      is re-derived from the edited chain plane, so the chain keeps exactly\n"
            "      the shape you just gave it. The pole vector constraint is kept.\n"
            "Each press is a single undo step.")
        self.btn_ike_edit.clicked.connect(self.on_ike_edit_clicked)
        layout.addWidget(self.btn_ike_edit)

        self.btn_ike_cancel = QPushButton("Cancel Edit (restore chain)")
        self.btn_ike_cancel.setToolTip(
            "Leave edit mode and put the chain, the handle and the pole vector back the\n"
            "way they were when EDIT IK CHAIN was pressed.")
        self.btn_ike_cancel.clicked.connect(self.on_ike_cancel)
        layout.addWidget(self.btn_ike_cancel)

        self.btn_ike_update = QPushButton("Update Now (no edit session)")
        self.btn_ike_update.setToolTip(
            "Match the handle and the pole vector to the chain as it is right now,\n"
            "without starting an edit session. Use this when the chain was already\n"
            "edited some other way.")
        self.btn_ike_update.clicked.connect(self.on_ike_update_now)
        layout.addWidget(self.btn_ike_update)

        self.lbl_ike_state = QLabel("")
        self.lbl_ike_state.setAlignment(Qt.AlignCenter)
        self.lbl_ike_state.setWordWrap(True)
        layout.addWidget(self.lbl_ike_state)

        layout.addStretch(1)

        self._adopt_scene_ik_edits()
        self._update_ike_state()

        return tab

    # --------------------------------------------------------------
    # Curve > Edit Curve
    # --------------------------------------------------------------

    def _build_curve_edit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_curve_edit = self._tsl("Curves")
        layout.addWidget(self.tsl_curve_edit)

        self.btn_curve_separate = QPushButton("Separate Curve")
        self.btn_curve_separate.setToolTip(
            "Split every curve shape out into its own transform (hairCrv).")
        self.btn_curve_separate.clicked.connect(self.on_curve_separate)
        layout.addWidget(self.btn_curve_separate)

        len_row = QHBoxLayout()
        len_row.addWidget(QLabel("Max Length :"))
        self.dsb_max_len = QDoubleSpinBox()
        self.dsb_max_len.setRange(0.0, 100000.0)
        self.dsb_max_len.setDecimals(3)
        self.dsb_max_len.setValue(0.8)
        len_row.addWidget(self.dsb_max_len)
        self.btn_curve_remove = QPushButton("Remove Curve")
        self.btn_curve_remove.setToolTip(
            "Delete every listed curve shorter than Max Length.")
        self.btn_curve_remove.clicked.connect(self.on_curve_remove)
        len_row.addWidget(self.btn_curve_remove)
        layout.addLayout(len_row)

        intv_row = QHBoxLayout()
        intv_row.addWidget(QLabel("Interval :"))
        self.dsb_interval = QDoubleSpinBox()
        self.dsb_interval.setRange(0.001, 100000.0)
        self.dsb_interval.setDecimals(3)
        self.dsb_interval.setValue(2.5)
        intv_row.addWidget(self.dsb_interval)
        intv_row.addWidget(QLabel("Max joints :"))
        self.sb_max_jnts = QSpinBox()
        self.sb_max_jnts.setRange(1, 1000)
        self.sb_max_jnts.setValue(5)
        intv_row.addWidget(self.sb_max_jnts)
        layout.addLayout(intv_row)

        self.btn_curve_rebuild = QPushButton("Rebuild Curve")
        self.btn_curve_rebuild.setToolTip(
            "Rebuild every listed curve, deriving the span count from its length and\n"
            "the Interval, capped by Max joints.")
        self.btn_curve_rebuild.clicked.connect(self.on_curve_rebuild)
        layout.addWidget(self.btn_curve_rebuild)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Curve > Clusters
    # --------------------------------------------------------------

    def _build_curve_cluster_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_curve_cluster = self._tsl("Curves")
        layout.addWidget(self.tsl_curve_cluster)

        self.btn_clusters = QPushButton("Clusters")
        self.btn_clusters.setToolTip(
            "Create one cluster deformer per CV of the listed curves, so the curve can\n"
            "be shaped by hand. No joint is created.")
        self.btn_clusters.clicked.connect(self.on_clusters)
        layout.addWidget(self.btn_clusters)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Select > Unused Joints
    # --------------------------------------------------------------

    def _build_select_unused_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_select_unused = self._tsl("Joints")
        layout.addWidget(self.tsl_select_unused)

        self.btn_select_unused = QPushButton("Select Unused Joints")
        self.btn_select_unused.setToolTip(
            "Highlight the listed joints that no skinCluster uses, and select them in\n"
            "the scene. Nothing is deleted.")
        self.btn_select_unused.clicked.connect(self.on_select_unused)
        layout.addWidget(self.btn_select_unused)

        layout.addStretch(1)
        return tab

    # ==============================================================
    # 탭 전환
    # ==============================================================

    def _on_tab_changed(self, *_):
        """IK 편집 상태는 씬에 있다. Chain > IK Edit 이 보일 때 다시 읽어 화면을 맞춘다.

        상위/하위 두 QTabWidget 이 같은 슬롯에 물려 있다. 상위는 **위젯 동일성**으로,
        하위는 CHAIN_PAGES 순서와 묶인 상수로 판단한다 - 상위 탭 인덱스로 비교하면
        탭이 늘고 줄 때 뜻이 조용히 변한다.
        """
        if self.tabs.currentWidget() is not self.chain_page:
            return
        if self.chain_tabs.currentIndex() != IKE_SUB_INDEX:
            return

        self._adopt_scene_ik_edits()
        self._update_ike_state()

    # ==============================================================
    # Handlers : IK Edit
    # ==============================================================

    def _ike_pv_mode(self):
        return _PV_MODES[self.cmb_ike_pv.currentIndex()][1]

    def _ike_snap_mode(self):
        return _SNAP_MODES[self.cmb_ike_snap.currentIndex()][1]

    def _log_all(self, messages):
        for m in messages or []:
            self.log(m)

    def _adopt_scene_ik_edits(self):
        """툴 밖(다른 세션 / 툴 재실행)에서 시작된 편집을 되찾는다."""
        if self.ike_targets:
            return
        editing = ike_mgr.find_editing_in_scene()
        if not editing:
            return
        self.ike_targets = editing
        self.log("[Info] Found {0} IK handle(s) still in edit mode: {1}".format(
            len(editing), ", ".join(h.split("|")[-1] for h in editing)))
        # ikSystem 의 solve 플래그는 씬이 아니라 세션 상태라 마야를 다시 켜면 살아난다.
        self._log_all(ike_mgr.reassert_disabled(editing))

    def _update_ike_state(self):
        """씬의 실제 편집 상태를 읽어 버튼/라벨을 맞춘다."""
        editing = ike_mgr.editing_of(self.ike_targets)
        on = bool(editing)

        self.btn_ike_edit.setChecked(on)
        self.btn_ike_edit.setText(IK_EDIT_ON_TEXT if on else IK_EDIT_OFF_TEXT)
        self.btn_ike_edit.setStyleSheet(IK_EDIT_ON_STYLE if on else "")
        self.btn_ike_edit.setEnabled(bool(self.ike_targets))

        self.btn_ike_cancel.setEnabled(on)
        self.btn_ike_update.setEnabled(bool(self.ike_targets) and not on)
        self.btn_ike_select.setEnabled(bool(self.ike_targets))
        # 편집 중에 대상을 바꾸면 IK 가 꺼진 핸들이 씬에 남는다. 끝낼 때까지 잠근다.
        self.btn_ike_load.setEnabled(not on)
        self.btn_ike_clear.setEnabled(not on)

        self.lbl_ike_target.setText(ike_mgr.describe(self.ike_targets))

        if on:
            self.lbl_ike_state.setText(
                "Edit mode is ON - IK is off, so the chain moves freely. Move it, then "
                "press the button again to keep it.")
        elif self.ike_targets:
            self.lbl_ike_state.setText("Ready.")
        else:
            self.lbl_ike_state.setText(
                "Select an IK handle, a chain joint or the IK control, then press "
                "Load Selection.")

    def on_ike_load(self):
        try:
            self.ike_targets = ike_mgr.resolve_targets()
        except Exception as e:
            self.ike_targets = []
            self.log("[ERR] {0}".format(e))
        self._update_ike_state()

        if not self.ike_targets:
            return

        self.log("[OK] Loaded {0} IK handle(s): {1}".format(
            len(self.ike_targets),
            ", ".join(h.split("|")[-1] for h in self.ike_targets)))
        # 편집을 시작하기 전에 무엇이 막히는지 미리 알려 준다.
        for h in self.ike_targets:
            info = ike_mgr.inspect(h)
            for b in info["blockers"]:
                self.log("[Warning] {0}: {1}".format(h.split("|")[-1], b))
            for n in info["notes"]:
                self.log("[Info] {0}: {1}".format(h.split("|")[-1], n))

    def on_ike_clear(self):
        self.ike_targets = []
        self._update_ike_state()
        self.log("IK Edit target cleared.")

    def on_ike_select(self):
        alive = [h for h in self.ike_targets if cmds.objExists(h)]
        if alive:
            cmds.select(alive, replace=True)

    def on_ike_edit_clicked(self):
        if not self.ike_targets:
            self._update_ike_state()
            return

        editing = ike_mgr.editing_of(self.ike_targets)
        try:
            if editing:
                results, messages = ike_mgr.end_edit(
                    editing,
                    snap_mode=self._ike_snap_mode(),
                    pv_mode=self._ike_pv_mode(),
                    set_preferred=self.chk_ike_preferred.isChecked())
                self._log_all(messages)
            else:
                self._log_all(ike_mgr.begin_edit(self.ike_targets))
        except Exception as e:
            self.log("[ERR] {0}".format(e))
            cmds.warning(str(e))

        self._update_ike_state()

    def on_ike_cancel(self):
        try:
            self._log_all(ike_mgr.cancel_edit(ike_mgr.editing_of(self.ike_targets)))
        except Exception as e:
            self.log("[ERR] {0}".format(e))
            cmds.warning(str(e))
        self._update_ike_state()

    def on_ike_update_now(self):
        if not self.ike_targets:
            return
        try:
            results, messages = ike_mgr.update_now(
                self.ike_targets,
                snap_mode=self._ike_snap_mode(),
                pv_mode=self._ike_pv_mode(),
                set_preferred=self.chk_ike_preferred.isChecked())
            self._log_all(messages)
        except Exception as e:
            self.log("[ERR] {0}".format(e))
            cmds.warning(str(e))
        self._update_ike_state()

    # ==============================================================
    # UI helpers
    # ==============================================================

    def _axis_combo(self, items, default):
        cmb = QComboBox()
        cmb.addItems(items)
        cmb.setCurrentText(default)
        return cmb

    def _labeled(self, text, widget):
        row = QHBoxLayout()
        lbl = QLabel(text)
        lbl.setMinimumWidth(150)
        row.addWidget(lbl)
        row.addWidget(widget)
        return row

    def log(self, text):
        self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Joint Tool v{0}\nWritten by Ji Hun Park\nUpdate date : {1}".format(
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
    # Handlers : Create
    # ==============================================================

    def _selected_point_type(self):
        return _POINT_TYPES[self.rb_point_group.checkedId()][1]

    def on_joints_to_crv(self):
        curves = self.tsl_create_crv.get_all_items()
        pt = self._selected_point_type()
        self._run("Joints to Crv",
                  lambda: crv_mgr.joints_to_curves(curves, pt))

    def _match_to_objs(self, label, objs):
        """From Object 축 옵션을 읽어 objs 순서대로 조인트를 만든다."""
        separate = (self.rb_match_group.checkedId() == 1)
        fwd = self.cmb_fwd_axis.currentIndex() + 1
        secd = self.cmb_secd_axis.currentIndex() + 1
        secd_ori = self.cmb_secd_ori.currentIndex() + 1
        self._run(label,
                  lambda: obj_mgr.joints_to_objs(objs, separate, fwd, secd, secd_ori))

    def on_match_to_obj(self):
        self._match_to_objs("Match to Obj", self.tsl_create_obj.get_all_items())

    def on_match_to_sel(self):
        """리스트를 거치지 않고 **지금 씬에서 선택한** 오브젝트/버텍스로 바로 실행.

        읽는 것은 리스트 내용이 아니라 **이 탭 리스트 위젯의 Order 체크박스**다.
        켜져 있으면 `ls(orderedSelection=True)` 로 **고른 순서**를 그대로 쓴다
        (버텍스 여러 개를 찍은 순서대로 체인이 생긴다). 꺼져 있으면 Maya 기본 순서
        - 컴포넌트는 인덱스 순서다.
        """
        objs = self.tsl_create_obj.maya_selection()
        if not objs:
            self.log("[ERR] Match to Sel : nothing selected in the scene")
            cmds.warning("Select objects or vertices first")
            return

        if not self.tsl_create_obj.is_order_tracking() and len(objs) > 1:
            self.log("[INFO] Match to Sel : 'Order' is off - using Maya's default order "
                     "(components come in index order).")

        self._match_to_objs("Match to Sel ({0})".format(len(objs)), objs)

    def on_div_select_startend(self):
        sel = cmds.ls(sl=True) or []
        starts, ends = div_mgr.pairs_from_selection(sel)
        self.tsl_div_start.set_items(starts)
        self.tsl_div_end.set_items(ends)
        self.log("[OK] Select Start End : {0} pair(s)".format(len(starts)))

    def on_div_add_startend(self):
        sel = cmds.ls(sl=True) or []
        if len(sel) != 2:
            self.log("[ERR] Add Start End : must select exactly 2 objects")
            cmds.warning("Must select 2 objects to Add")
            return
        self.tsl_div_start.append_unique([sel[0]])
        self.tsl_div_end.append_unique([sel[1]])
        self.log("[OK] Add Start End")

    def on_make_divided(self):
        starts = self.tsl_div_start.get_all_items()
        ends = self.tsl_div_end.get_all_items()
        num = self.sb_div_num.value()
        self._run("Make Joint Divided",
                  lambda: div_mgr.make_joints_divided(starts, ends, num))

    # ==============================================================
    # Handlers : Orient
    # ==============================================================

    def on_aim_select_startend(self):
        sel = cmds.ls(sl=True) or []
        starts, ends = div_mgr.pairs_from_selection(sel)
        self.tsl_aim_start.set_items(starts)
        self.tsl_aim_end.set_items(ends)
        self.log("[OK] Select Start End : {0} pair(s)".format(len(starts)))

    def on_aim_add_startend(self):
        sel = cmds.ls(sl=True) or []
        if len(sel) != 2:
            self.log("[ERR] Add Start End : must select exactly 2 objects")
            cmds.warning("Must select 2 objects to Add")
            return
        self.tsl_aim_start.append_unique([sel[0]])
        self.tsl_aim_end.append_unique([sel[1]])
        self.log("[OK] Add Start End")

    def on_make_aim(self):
        starts = self.tsl_aim_start.get_all_items()
        ends = self.tsl_aim_end.get_all_items()
        poles = self.tsl_aim_pole.get_all_items()
        aim_axis = self.cmb_aim_axis.currentIndex() + 1  # 1-base (1=X,2=Y,3=Z)
        self._run("Make Joint Aim",
                  lambda: aim_mgr.make_joint_aim(starts, ends, poles, aim_axis))

    def on_set_orient(self):
        joints = self.tsl_orient_set.get_all_items()
        axis_idx = self.cmb_orient_axis.currentIndex() + 1
        deg = self.dsb_orient_deg.value()
        self._run("Set joints orientation",
                  lambda: obj_mgr.set_joint_orient(joints, axis_idx, deg))

    def on_swap_ori_to_rot(self):
        joints = self.tsl_orient_swap.get_all_items()
        self._run("joint orient -> rotate",
                  lambda: obj_mgr.swap_rotate_orient(joints, "jointOrient", "rotate"))

    def on_swap_rot_to_ori(self):
        joints = self.tsl_orient_swap.get_all_items()
        self._run("rotate -> joint orient",
                  lambda: obj_mgr.swap_rotate_orient(joints, "rotate", "jointOrient"))

    # ==============================================================
    # Handlers : Chain
    # ==============================================================

    def on_chain_reverse(self):
        roots = self.tsl_chain_reverse.get_all_items()
        remove_origin = self.cb_remove_origin.isChecked()
        self._run("Reverse joint chain",
                  lambda: hair_mgr.reverse_joints(roots, remove_origin))

    # ==============================================================
    # Handlers : Curve
    # ==============================================================

    def on_curve_separate(self):
        curves = self.tsl_curve_edit.get_all_items()
        self._run("Separate Curve",
                  lambda: hair_mgr.separate_curves(curves))

    def on_curve_remove(self):
        curves = self.tsl_curve_edit.get_all_items()
        max_len = self.dsb_max_len.value()
        self._run("Remove Curve",
                  lambda: hair_mgr.remove_curves_by_length(curves, max_len))

    def on_curve_rebuild(self):
        curves = self.tsl_curve_edit.get_all_items()
        interval = self.dsb_interval.value()
        max_jnts = self.sb_max_jnts.value()
        self._run("Rebuild Curve",
                  lambda: hair_mgr.rebuild_curves_by_interval(curves, interval, max_jnts))

    def on_clusters(self):
        curves = self.tsl_curve_cluster.get_all_items()
        self._run("Clusters", lambda: crv_mgr.clusters_to_curves(curves))

    # ==============================================================
    # Handlers : Select
    # ==============================================================

    def on_select_unused(self):
        joints = self.tsl_select_unused.get_all_items()
        unused = hair_mgr.unused_joints(joints)
        self.tsl_select_unused.select_by_texts(unused)
        if unused:
            cmds.select(unused)
        else:
            cmds.select(clear=True)
        self.log("[OK] Select Unused Joints : {0}".format(len(unused)))
