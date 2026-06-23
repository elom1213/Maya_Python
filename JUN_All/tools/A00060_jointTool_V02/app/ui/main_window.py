# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00060_jointTool_V02 - Qt UI
#
# MEL JointTool V05.03 의 3탭(Curve / Divide / Aim)을 PySide 로 포팅하고,
# A00060 jointTool 의 헤어 기능을 Hair 탭으로 추가한다(총 4탭).
#
# v01.01 : Aim 탭 개선 - Aim axis 드롭박스(X/Y/Z)로 pole tgt 을 향할 보조축 선택.
#          aimConstraint(부모->자식 cycle) 대신 벡터 연산으로 jointOrient 직접 계산.

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
from tools.A00060_jointTool_V02.app.ui.collapsible import CollapsibleBox


# 재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00060_jointTool_V02_window"

# point type 라디오 -> core enum
_POINT_TYPES = [
    ("Control Vertex (Omit [1], [-2])", crv_mgr.POINT_TYPE_CV_OMIT),
    ("Control Vertex", crv_mgr.POINT_TYPE_CV),
    ("Edit Point", crv_mgr.POINT_TYPE_EP),
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

        btn_match = QPushButton("Match to Obj")
        btn_match.clicked.connect(self.on_match_to_obj)
        box_obj.addWidget(btn_match)
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

    def on_match_to_obj(self):
        objs = self.tsl_curve.get_all_items()
        separate = (self.rb_match_group.checkedId() == 1)
        fwd = self.cmb_fwd_axis.currentIndex() + 1
        secd = self.cmb_secd_axis.currentIndex() + 1
        secd_ori = self.cmb_secd_ori.currentIndex() + 1
        self._run("Match to Obj",
                  lambda: obj_mgr.joints_to_objs(objs, separate, fwd, secd, secd_ori))

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
