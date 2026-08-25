# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-30
# A00060_jointTool_V02 - Qt UI
#
# MEL JointTool V05.03 의 3탭(Curve / Divide / Aim)을 PySide 로 포팅하고,
# A00060 jointTool 의 헤어 기능을 Hair 탭으로 추가한다(총 4탭).
#
# v01.01 : Aim 탭 개선 - Aim axis 드롭박스(X/Y/Z)로 pole tgt 을 향할 보조축 선택.
#          aimConstraint(부모->자식 cycle) 대신 벡터 연산으로 jointOrient 직접 계산.
# v01.04 : Curve 탭 joint to obj 에 "Match to Sel" 버튼 추가 - 리스트를 거치지 않고
#          지금 씬에서 선택한 오브젝트/버텍스로 바로 실행. Order 가 켜져 있으면
#          버텍스를 고른 순서대로 처리.
# v01.05 : IK Edit 탭 추가 - 이미 설치된 ikHandle 과 폴 벡터 컨스트레인트를 그대로 둔 채
#          본 체인을 수정한다. 토글 버튼(EDIT IK CHAIN)으로 편집 시작/확정.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00060_jointTool_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00060_jointTool_V02.app.core import curve_joint_manager as crv_mgr
from tools.A00060_jointTool_V02.app.core import obj_joint_manager as obj_mgr
from tools.A00060_jointTool_V02.app.core import divide_manager as div_mgr
from tools.A00060_jointTool_V02.app.core import aim_manager as aim_mgr
from tools.A00060_jointTool_V02.app.core import hair_manager as hair_mgr
from tools.A00060_jointTool_V02.app.core import ik_edit_manager as ike_mgr
from tools.A00060_jointTool_V02.app.ui.collapsible import CollapsibleBox


# 재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00060_jointTool_V02_window"

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


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width = 540
        self.win_height = 820
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

        # 탭
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_curve_tab(), "Curve")
        self.tabs.addTab(self._build_divide_tab(), "Divide")
        self.tabs.addTab(self._build_aim_tab(), "Aim")
        self.tabs.addTab(self._build_hair_tab(), "Hair")
        self.tabs.addTab(self._build_ik_edit_tab(), "IK Edit")
        main_layout.addWidget(self.tabs)

        main_layout.addWidget(self.te_log)

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------------------
    # Tab : Curve
    # --------------------------------------------------------------

    def _build_curve_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 메인 리스트
        self.tsl_curve = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Selections", select_label="Select",
            show_sort=False, list_min_height=160, log_callback=self.log)
        layout.addWidget(self.tsl_curve)

        # frame : joint to Crv
        box_crv = CollapsibleBox("Tool : joint to Crv")

        self.rb_point_group = QButtonGroup(self)
        for i, (label, _enum) in enumerate(_POINT_TYPES):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self.rb_point_group.addButton(rb, i)
            box_crv.addWidget(rb)

        row = QHBoxLayout()
        btn_jnt_crv = QPushButton("Joints to Crv")
        btn_clusters = QPushButton("Clusters")
        btn_jnt_crv.clicked.connect(self.on_joints_to_crv)
        btn_clusters.clicked.connect(self.on_clusters)
        row.addWidget(btn_jnt_crv)
        row.addWidget(btn_clusters)
        box_crv.addLayout(row)
        layout.addWidget(box_crv)

        # frame : joint to obj
        box_obj = CollapsibleBox("Tool : joint to obj")

        self.rb_match_group = QButtonGroup(self)
        match_row = QHBoxLayout()
        for i, label in enumerate(["Connect", "Separate"]):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self.rb_match_group.addButton(rb, i)
            match_row.addWidget(rb)
        box_obj.addLayout(match_row)

        self.cmb_fwd_axis = self._axis_combo(["+X", "+Y", "+Z"], "+X")
        self.cmb_secd_axis = self._axis_combo(["+X", "+Y", "+Z"], "+Y")
        self.cmb_secd_ori = self._axis_combo(
            ["+X", "-X", "+Y", "-Y", "+Z", "-Z"], "+Y")

        box_obj.addLayout(self._labeled("Foward axis :", self.cmb_fwd_axis))
        box_obj.addLayout(self._labeled("Secondary axis :", self.cmb_secd_axis))
        box_obj.addLayout(self._labeled("Secondary axis orient :", self.cmb_secd_ori))

        # 왼쪽 = 리스트에 담긴 항목 / 오른쪽 = 지금 씬에서 선택한 것
        match_btn_row = QHBoxLayout()
        btn_match = QPushButton("Match to Obj")
        btn_match.setToolTip("Create joints at the objects/vertices listed above.")
        btn_match.clicked.connect(self.on_match_to_obj)
        btn_match_sel = QPushButton("Match to Sel")
        btn_match_sel.setToolTip(
            "Create joints at the objects/vertices selected in the scene right now,\n"
            "without listing them first.\n"
            "With 'Order' checked, vertices are processed in the order you picked them.")
        btn_match_sel.clicked.connect(self.on_match_to_sel)
        match_btn_row.addWidget(btn_match)
        match_btn_row.addWidget(btn_match_sel)
        box_obj.addLayout(match_btn_row)
        layout.addWidget(box_obj)

        # frame : joint orient and rotate
        box_swap = CollapsibleBox("Tool : joint orient and rotate")
        btn_ori_to_rot = QPushButton("joint orient to rotate")
        btn_rot_to_ori = QPushButton("rotate to joint orient")
        btn_ori_to_rot.clicked.connect(self.on_swap_ori_to_rot)
        btn_rot_to_ori.clicked.connect(self.on_swap_rot_to_ori)
        box_swap.addWidget(btn_ori_to_rot)
        box_swap.addWidget(btn_rot_to_ori)
        layout.addWidget(box_swap)

        # frame : Set Orient (기본 접힘)
        box_set = CollapsibleBox("Tool : Set Orient", collapsed=True)
        self.cmb_orient_axis = self._axis_combo(["X", "Y", "Z"], "X")
        box_set.addLayout(self._labeled("Orient axis :", self.cmb_orient_axis))
        self.dsb_orient_deg = QDoubleSpinBox()
        self.dsb_orient_deg.setRange(-360.0, 360.0)
        self.dsb_orient_deg.setDecimals(3)
        box_set.addLayout(self._labeled("Orient degree :", self.dsb_orient_deg))
        btn_set_ori = QPushButton("Set joints orientation")
        btn_set_ori.clicked.connect(self.on_set_orient)
        box_set.addWidget(btn_set_ori)
        layout.addWidget(box_set)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Tab : Divide
    # --------------------------------------------------------------

    def _build_divide_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_div_start = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Start", select_label="Select",
            show_sort=False, list_min_height=160, log_callback=self.log)
        self.tsl_div_end = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="End", select_label="Select",
            show_sort=False, list_min_height=160, log_callback=self.log)

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
    # Tab : Aim
    # --------------------------------------------------------------

    def _build_aim_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_aim_start = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Start", select_label="Select",
            show_sort=False, list_min_height=160, log_callback=self.log)
        self.tsl_aim_end = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="End", select_label="Select",
            show_sort=False, list_min_height=160, log_callback=self.log)
        self.tsl_aim_pole = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="pole tgt", select_label="Select",
            show_sort=False, list_min_height=160, log_callback=self.log)

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
    # Tab : Hair  (A00060 jointTool)
    # --------------------------------------------------------------

    def _build_hair_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tsl_hair = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joint Tool", select_label="Select",
            show_sort=False, list_min_height=160, log_callback=self.log)
        layout.addWidget(self.tsl_hair)

        # Sub Tool : Curve
        box_crv = CollapsibleBox("Sub Tool : Curve")

        btn_separate = QPushButton("Separate Curve")
        btn_separate.clicked.connect(self.on_hair_separate)
        box_crv.addWidget(btn_separate)

        len_row = QHBoxLayout()
        len_row.addWidget(QLabel("Max Length :"))
        self.dsb_max_len = QDoubleSpinBox()
        self.dsb_max_len.setRange(0.0, 100000.0)
        self.dsb_max_len.setDecimals(3)
        self.dsb_max_len.setValue(0.8)
        len_row.addWidget(self.dsb_max_len)
        btn_remove = QPushButton("Remove Curve")
        btn_remove.clicked.connect(self.on_hair_remove)
        len_row.addWidget(btn_remove)
        box_crv.addLayout(len_row)

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
        box_crv.addLayout(intv_row)

        btn_rebuild = QPushButton("Rebuild Curve")
        btn_rebuild.clicked.connect(self.on_hair_rebuild)
        box_crv.addWidget(btn_rebuild)
        layout.addWidget(box_crv)

        # Tool : Edit
        box_edit = CollapsibleBox("Tool : Edit")
        self.cb_remove_origin = QCheckBox("Remove origin")
        self.cb_remove_origin.setChecked(True)
        box_edit.addWidget(self.cb_remove_origin)

        btn_reverse = QPushButton("Reverse joint chain")
        btn_reverse.clicked.connect(self.on_hair_reverse)
        box_edit.addWidget(btn_reverse)

        btn_unused = QPushButton("Select Unused Joints")
        btn_unused.clicked.connect(self.on_hair_select_unused)
        box_edit.addWidget(btn_unused)
        layout.addWidget(box_edit)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------------------
    # Tab : IK Edit
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
    # Handlers : Curve
    # ==============================================================

    def _selected_point_type(self):
        return _POINT_TYPES[self.rb_point_group.checkedId()][1]

    def on_joints_to_crv(self):
        curves = self.tsl_curve.get_all_items()
        pt = self._selected_point_type()
        self._run("Joints to Crv",
                  lambda: crv_mgr.joints_to_curves(curves, pt))

    def on_clusters(self):
        curves = self.tsl_curve.get_all_items()
        self._run("Clusters", lambda: crv_mgr.clusters_to_curves(curves))

    def _match_to_objs(self, label, objs):
        """joint to obj 축 옵션을 읽어 objs 순서대로 조인트를 만든다."""
        separate = (self.rb_match_group.checkedId() == 1)
        fwd = self.cmb_fwd_axis.currentIndex() + 1
        secd = self.cmb_secd_axis.currentIndex() + 1
        secd_ori = self.cmb_secd_ori.currentIndex() + 1
        self._run(label,
                  lambda: obj_mgr.joints_to_objs(objs, separate, fwd, secd, secd_ori))

    def on_match_to_obj(self):
        self._match_to_objs("Match to Obj", self.tsl_curve.get_all_items())

    def on_match_to_sel(self):
        """리스트를 거치지 않고 **지금 씬에서 선택한** 오브젝트/버텍스로 바로 실행.

        Selections 리스트의 **Order** 체크박스가 켜져 있으면 `ls(orderedSelection=True)`
        로 **고른 순서**를 그대로 쓴다(버텍스 여러 개를 찍은 순서대로 체인이 생긴다).
        Order 가 꺼져 있으면 Maya 기본 순서 — 컴포넌트는 인덱스 순서다.
        """
        objs = self.tsl_curve.maya_selection()
        if not objs:
            self.log("[ERR] Match to Sel : nothing selected in the scene")
            cmds.warning("Select objects or vertices first")
            return

        if not self.tsl_curve.is_order_tracking() and len(objs) > 1:
            self.log("[INFO] Match to Sel : 'Order' is off - using Maya's default order "
                     "(components come in index order).")

        self._match_to_objs("Match to Sel ({0})".format(len(objs)), objs)

    def on_swap_ori_to_rot(self):
        joints = self.tsl_curve.get_all_items()
        self._run("joint orient -> rotate",
                  lambda: obj_mgr.swap_rotate_orient(joints, "jointOrient", "rotate"))

    def on_swap_rot_to_ori(self):
        joints = self.tsl_curve.get_all_items()
        self._run("rotate -> joint orient",
                  lambda: obj_mgr.swap_rotate_orient(joints, "rotate", "jointOrient"))

    def on_set_orient(self):
        joints = self.tsl_curve.get_all_items()
        axis_idx = self.cmb_orient_axis.currentIndex() + 1
        deg = self.dsb_orient_deg.value()
        self._run("Set joints orientation",
                  lambda: obj_mgr.set_joint_orient(joints, axis_idx, deg))

    # ==============================================================
    # Handlers : Divide
    # ==============================================================

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
    # Handlers : Aim
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

    # ==============================================================
    # Handlers : Hair
    # ==============================================================

    def on_hair_separate(self):
        curves = self.tsl_hair.get_all_items()
        self._run("Separate Curve",
                  lambda: hair_mgr.separate_curves(curves))

    def on_hair_remove(self):
        curves = self.tsl_hair.get_all_items()
        max_len = self.dsb_max_len.value()
        self._run("Remove Curve",
                  lambda: hair_mgr.remove_curves_by_length(curves, max_len))

    def on_hair_rebuild(self):
        curves = self.tsl_hair.get_all_items()
        interval = self.dsb_interval.value()
        max_jnts = self.sb_max_jnts.value()
        self._run("Rebuild Curve",
                  lambda: hair_mgr.rebuild_curves_by_interval(curves, interval, max_jnts))

    def on_hair_reverse(self):
        roots = self.tsl_hair.get_all_items()
        remove_origin = self.cb_remove_origin.isChecked()
        self._run("Reverse joint chain",
                  lambda: hair_mgr.reverse_joints(roots, remove_origin))

    def on_hair_select_unused(self):
        joints = self.tsl_hair.get_all_items()
        unused = hair_mgr.unused_joints(joints)
        self.tsl_hair.select_by_texts(unused)
        if unused:
            cmds.select(unused)
        else:
            cmds.select(clear=True)
        self.log("[OK] Select Unused Joints : {0}".format(len(unused)))
