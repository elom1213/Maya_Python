# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00400_CurveTool - Create > From Hair 탭 (v01.32)
#
# 헤어 메시 가닥마다 중심선 커브 하나(cv[0] = 뿌리). 계산은 core/hair_curve_manager.py.
# Houdini hairShrink hip 의 foreach 루프를 대체한다 - 계획서
# docs/plans/A00400_CurveTool_hair_centerline_plan.md.
#
# 길이 칸(필터 · 다듬기 · 간격)은 **씬 길이 단위**로 받고 코어에는 내부 단위(cm)로 넘긴다.
# 옵션은 저장하지 않는다(이 툴의 다른 탭과 같게 - 창을 열 때마다 기본값).

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_progress_qt
from Framework.core.maya_undo import undo_chunk

from tools.A00400_CurveTool.app.core import hair_curve_manager as hair_mgr


# 진행 팝업을 띄우는 메시 개수 기준
PROGRESS_MIN_MESHES = 20

_METHODS = (
    ("Auto", hair_mgr.METHOD_AUTO),
    ("Rings", hair_mgr.METHOD_RINGS),
    ("Geodesic", hair_mgr.METHOD_GEODESIC),
)

_ROOTS = (
    ("Open end", hair_mgr.ROOT_OPEN_END),
    ("Highest Y", "+y"), ("Lowest Y", "-y"),
    ("Highest X", "+x"), ("Lowest X", "-x"),
    ("Highest Z", "+z"), ("Lowest Z", "-z"),
)

_POINTS = (
    ("Count", hair_mgr.POINTS_COUNT),
    ("Spacing", hair_mgr.POINTS_SPACING),
    ("Per Ring", hair_mgr.POINTS_PER_RING),
)


def _to_internal(value):
    """UI 길이 -> 내부 단위(cm)."""
    return om.MDistance.uiToInternal(float(value))


def _to_ui(value):
    return om.MDistance.internalToUI(float(value))


def _dspin(value, lo=0.0, hi=100000.0, decimals=3, step=0.1):
    sb = QDoubleSpinBox()
    sb.setRange(lo, hi)
    sb.setDecimals(decimals)
    sb.setSingleStep(step)
    sb.setValue(value)
    sb.setKeyboardTracking(False)
    return sb


def _ispin(value, lo, hi):
    sb = QSpinBox()
    sb.setRange(lo, hi)
    sb.setValue(value)
    sb.setKeyboardTracking(False)
    return sb


def _combo(pairs, tip=""):
    cb = QComboBox()
    for label, data in pairs:
        cb.addItem(label, data)
    if tip:
        cb.setToolTip(tip)
    return cb


class HairTab(QWidget):
    """From Hair 탭. 로그는 툴 창 것을 쓴다(log_callback(text, warn=False)).

    send_to_joints(curves, count_or_None) : 만든 커브를 Edit > Joints 로 넘기는 콜백(main_window 가 준다).
    """

    def __init__(self, log_callback=None, send_to_joints=None, parent=None):
        super(HairTab, self).__init__(parent)
        self._log_cb = log_callback or (lambda text, warn=False: None)
        self._send_to_joints = send_to_joints
        self._skipped_uuids = []
        self._last_curves = []         # 마지막 Create 커브 UUID
        self._last_count = None
        self.build_ui()
        self._sync_enabled()

    def _log(self, text, warn=False):
        try:
            self._log_cb(text, warn=warn)
        except TypeError:
            self._log_cb(text)

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)

        desc = QLabel(
            "One centerline curve through each hair strand mesh.\n"
            "The curve starts at the strand's open end (root) - cv[0] = root.")
        desc.setAlignment(Qt.AlignCenter)
        root.addWidget(desc)

        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Hair meshes", select_label="List Selected",
            show_sort=True, list_min_height=140, list_hint_height=140,
            log_callback=self._log)
        root.addWidget(self.tsl, 1)

        self.chk_children = QCheckBox("Include child meshes")
        self.chk_children.setChecked(True)
        self.chk_children.setToolTip(
            "Also use every mesh below the listed nodes.\n"
            "List just the hair group to process all of its strands.")
        root.addWidget(self.chk_children)

        # ---------------- Centerline ----------------
        cl_box = QGroupBox("Centerline")
        cl = QGridLayout(cl_box)

        self.cb_method = _combo(_METHODS,
            "How each strand is cut into cross-sections:\n"
            "  Rings    - edge rings counted from the root (exact for quad tubes)\n"
            "  Geodesic - equal surface-distance slices from the root\n"
            "             (for triangulated / irregular meshes)\n"
            "  Auto     - Rings when the strand is mostly quads with 1-2 open ends,\n"
            "             otherwise Geodesic")
        self.sb_slices = _ispin(30, 2, 1000)
        self.sb_slices.setToolTip("Number of cross-sections for Geodesic.")
        self.cb_root = _combo(_ROOTS,
            "Which end of the strand is the root (cv[0]).\n"
            "  Open end - the open border of the tube (the scalp side of a hair strand).\n"
            "             Falls back to Highest Y when a strand has no or several open ends.\n"
            "  Highest / Lowest - the end furthest along that world axis.\n"
            "Keep 'Open end' for hair that hangs and also for strands that curl upward -\n"
            "an axis rule would flip those.")
        cl.addWidget(QLabel("Method"), 0, 0)
        cl.addWidget(self.cb_method, 0, 1)
        cl.addWidget(QLabel("Slices"), 0, 2)
        cl.addWidget(self.sb_slices, 0, 3)
        cl.addWidget(QLabel("Root"), 1, 0)
        cl.addWidget(self.cb_root, 1, 1, 1, 3)

        self.sb_smooth_iter = _ispin(10, 0, 1000)
        self.sb_smooth_iter.setToolTip(
            "Smoothing passes on the centerline (ends stay fixed). 0 = off.")
        self.sb_smooth_str = _dspin(0.5, 0.0, 1.0, 2, 0.05)
        self.sb_smooth_str.setToolTip("How far each point moves toward its neighbours per pass.")
        cl.addWidget(QLabel("Smooth"), 2, 0)
        cl.addWidget(self.sb_smooth_iter, 2, 1)
        cl.addWidget(QLabel("Strength"), 2, 2)
        cl.addWidget(self.sb_smooth_str, 2, 3)

        self.sb_trim_root = _dspin(0.0)
        self.sb_trim_root.setToolTip("Cut this length off the root end (scene units).")
        self.sb_trim_tip = _dspin(0.0)
        self.sb_trim_tip.setToolTip("Cut this length off the tip end (scene units).")
        cl.addWidget(QLabel("Trim Root"), 3, 0)
        cl.addWidget(self.sb_trim_root, 3, 1)
        cl.addWidget(QLabel("Trim Tip"), 3, 2)
        cl.addWidget(self.sb_trim_tip, 3, 3)
        root.addWidget(cl_box)

        # ---------------- Output ----------------
        out_box = QGroupBox("Output")
        out = QGridLayout(out_box)

        self.cb_points = _combo(_POINTS,
            "Where the curve points go:\n"
            "  Count    - this many points, evenly spaced along the strand\n"
            "  Spacing  - the even spacing closest to this length\n"
            "  Per Ring - one point per cross-section, as computed")
        self.sb_count = _ispin(10, 2, 1000)
        self.sb_count.setToolTip(
            "Points per curve. With Degree 1 these are the CVs - build the same\n"
            "count in Edit > Joints (By parameter) to get one joint on every CV.")
        self.sb_spacing = _dspin(1.0, 0.001, 100000.0, 3, 0.1)
        self.sb_spacing.setToolTip("Target distance between points (scene units).")
        out.addWidget(QLabel("Points"), 0, 0)
        out.addWidget(self.cb_points, 0, 1)
        out.addWidget(QLabel("Count"), 0, 2)
        out.addWidget(self.sb_count, 0, 3)
        out.addWidget(QLabel("Spacing"), 1, 2)
        out.addWidget(self.sb_spacing, 1, 3)

        self.rb_linear = QRadioButton("1 Linear")
        self.rb_linear.setChecked(True)
        self.rb_linear.setToolTip("CVs are exactly the computed points.")
        self.rb_cubic = QRadioButton("3 Cubic")
        self.rb_cubic.setToolTip("A smooth curve that passes through the computed points.")
        deg_group = QButtonGroup(self)
        deg_group.addButton(self.rb_linear)
        deg_group.addButton(self.rb_cubic)
        deg_row = QHBoxLayout()
        deg_row.addWidget(self.rb_linear)
        deg_row.addWidget(self.rb_cubic)
        deg_row.addStretch(1)
        out.addWidget(QLabel("Degree"), 1, 0)
        out.addLayout(deg_row, 1, 1)

        self.le_name = QLineEdit(hair_mgr.NAME_DEFAULT)
        self.le_name.setToolTip(
            "Curve name. {mesh} = the mesh name (namespace removed).\n"
            "A mesh with several strands gets _s01, _s02 ...")
        out.addWidget(QLabel("Name"), 2, 0)
        out.addWidget(self.le_name, 2, 1, 1, 3)

        self.chk_group = QCheckBox("Group")
        self.chk_group.setChecked(True)
        self.le_group = QLineEdit(hair_mgr.GROUP_DEFAULT)
        self.le_group.setToolTip("Put the curves under this group (made if missing).")
        out.addWidget(self.chk_group, 3, 0)
        out.addWidget(self.le_group, 3, 1, 1, 3)

        self.chk_source = QCheckBox("Add source attribute")
        self.chk_source.setChecked(True)
        self.chk_source.setToolTip(
            "Store the source mesh name on each curve (string attribute '{0}').".format(
                hair_mgr.SOURCE_ATTR))
        out.addWidget(self.chk_source, 4, 0, 1, 4)
        root.addWidget(out_box)

        # ---------------- Filters ----------------
        flt_box = QGroupBox("Filters")
        flt = QGridLayout(flt_box)
        self.chk_min_size = QCheckBox("Skip meshes smaller than")
        self.chk_min_size.setChecked(True)
        self.sb_min_size = _dspin(1.0)
        self.chk_min_size.setToolTip("Bounding box diagonal of the strand (scene units).")
        self.chk_min_len = QCheckBox("Skip curves shorter than")
        self.chk_min_len.setChecked(True)
        self.sb_min_len = _dspin(1.0)
        self.chk_min_len.setToolTip("Centerline length after smoothing / trimming (scene units).")
        flt.addWidget(self.chk_min_size, 0, 0)
        flt.addWidget(self.sb_min_size, 0, 1)
        flt.addWidget(QLabel("(bounding box diagonal)"), 0, 2)
        flt.addWidget(self.chk_min_len, 1, 0)
        flt.addWidget(self.sb_min_len, 1, 1)
        flt.addWidget(QLabel("(centerline length)"), 1, 2)
        root.addWidget(flt_box)

        # ---------------- 버튼 ----------------
        row1 = QHBoxLayout()
        self.btn_analyze = QPushButton("Analyze")
        self.btn_analyze.setToolTip("Compute everything and report - the scene is not changed.")
        self.btn_create = QPushButton("Create Curves")
        self.btn_create.setMinimumHeight(30)
        self.btn_create.setToolTip("Create one curve per strand. One undo step.")
        row1.addWidget(self.btn_analyze)
        row1.addWidget(self.btn_create, 1)
        root.addLayout(row1)

        row2 = QHBoxLayout()
        self.btn_select_skipped = QPushButton("Select Skipped")
        self.btn_select_skipped.setToolTip("Select the meshes the last Analyze / Create skipped.")
        self.btn_send = QPushButton("Send to Joints")
        self.btn_send.setToolTip(
            "Put the curves from the last Create into Edit > Joints and open it.\n"
            "Count and 'By parameter' are set so every joint lands on a CV.")
        row2.addWidget(self.btn_select_skipped)
        row2.addWidget(self.btn_send)
        root.addLayout(row2)

        # 연결
        self.cb_method.currentIndexChanged.connect(self._sync_enabled)
        self.cb_points.currentIndexChanged.connect(self._sync_enabled)
        self.chk_min_size.toggled.connect(self._sync_enabled)
        self.chk_min_len.toggled.connect(self._sync_enabled)
        self.chk_group.toggled.connect(self._sync_enabled)
        self.btn_analyze.clicked.connect(lambda *_: self.on_analyze())
        self.btn_create.clicked.connect(lambda *_: self.on_create())
        self.btn_select_skipped.clicked.connect(lambda *_: self.on_select_skipped())
        self.btn_send.clicked.connect(lambda *_: self.on_send_to_joints())

    def _sync_enabled(self, *_):
        self.sb_slices.setEnabled(self.cb_method.currentData() != hair_mgr.METHOD_RINGS)
        mode = self.cb_points.currentData()
        self.sb_count.setEnabled(mode == hair_mgr.POINTS_COUNT)
        self.sb_spacing.setEnabled(mode == hair_mgr.POINTS_SPACING)
        self.sb_min_size.setEnabled(self.chk_min_size.isChecked())
        self.sb_min_len.setEnabled(self.chk_min_len.isChecked())
        self.le_group.setEnabled(self.chk_group.isChecked())
        self.btn_send.setEnabled(bool(self._last_curves) and self._send_to_joints is not None)
        self.btn_select_skipped.setEnabled(bool(self._skipped_uuids))

    # ==================================================================
    # 옵션
    # ==================================================================

    def options(self):
        return hair_mgr.HairOptions(
            method=self.cb_method.currentData(),
            slices=self.sb_slices.value(),
            root=self.cb_root.currentData(),
            smooth_iterations=self.sb_smooth_iter.value(),
            smooth_strength=self.sb_smooth_str.value(),
            trim_root=_to_internal(self.sb_trim_root.value()),
            trim_tip=_to_internal(self.sb_trim_tip.value()),
            points_mode=self.cb_points.currentData(),
            count=self.sb_count.value(),
            spacing=_to_internal(self.sb_spacing.value()),
            degree=3 if self.rb_cubic.isChecked() else 1,
            min_size_on=self.chk_min_size.isChecked(),
            min_size=_to_internal(self.sb_min_size.value()),
            min_length_on=self.chk_min_len.isChecked(),
            min_length=_to_internal(self.sb_min_len.value()),
            include_children=self.chk_children.isChecked(),
            name=self.le_name.text().strip() or hair_mgr.NAME_DEFAULT,
            group_on=self.chk_group.isChecked(),
            group_name=self.le_group.text().strip() or hair_mgr.GROUP_DEFAULT,
            source_attr=self.chk_source.isChecked())

    def _nodes(self):
        nodes = self.tsl.get_all_nodes() or self.tsl.get_all_items()
        if not nodes:
            self._log("The list is empty. Select hair meshes (or their group) and click "
                      "'List Selected'.", warn=True)
        return nodes

    # ==================================================================
    # 동작
    # ==================================================================

    def _run(self, create):
        nodes = self._nodes()
        if not nodes:
            return None
        opts = self.options()
        shapes, _ = hair_mgr.collect_meshes(nodes, opts.include_children)

        dlg = None
        calc_cb = create_cb = None
        if len(shapes) >= PROGRESS_MIN_MESHES:
            phases = [("Computing centerlines", 70)]
            if create:
                phases.append(("Creating curves", 30))
            dlg = JUN_mod_progress_qt.JUN_mod_progress_qt_v01(
                self, title="Create Curves" if create else "Analyze", phases=phases)
            step = dlg.callback()
            dlg.start()
            dlg.begin_phase()
            calc_cb = step
            if create:
                started = {"done": False}

                def create_cb(done, total, message=None):
                    if not started["done"]:
                        started["done"] = True
                        dlg.begin_phase()
                    step(done, total, message)
        try:
            if create:
                with undo_chunk():
                    report = hair_mgr.create_curves(nodes, opts, progress=calc_cb,
                                                    create_progress=create_cb)
            else:
                report = hair_mgr.analyze(nodes, opts, progress=calc_cb)
        except Exception as exc:
            self._log("From Hair failed: {0}".format(exc), warn=True)
            raise
        finally:
            if dlg is not None:
                dlg.finish()

        for text, warn in report.summary_lines(to_ui=_to_ui):
            self._log(text, warn=warn)

        self._skipped_uuids = []
        for mesh in report.skipped_meshes():
            uid = cmds.ls(mesh, uuid=True) or []
            if uid:
                self._skipped_uuids.append(uid[0])
        if create:
            self._last_curves = [u for c in report.curves for u in (cmds.ls(c, uuid=True) or [])]
            self._last_count = (opts.count if opts.points_mode == hair_mgr.POINTS_COUNT
                                and opts.degree == 1 else None)
        self._sync_enabled()
        return report

    def on_analyze(self):
        return self._run(create=False)

    def on_create(self):
        return self._run(create=True)

    def on_select_skipped(self):
        nodes = []
        for uid in self._skipped_uuids:
            nodes.extend(cmds.ls(uid, long=True) or [])
        if not nodes:
            self._log("No skipped meshes to select.")
            return []
        cmds.select(nodes, replace=True)
        self._log("Selected {0} skipped mesh(es).".format(len(nodes)))
        return nodes

    def on_send_to_joints(self):
        curves = [n for uid in self._last_curves for n in (cmds.ls(uid, long=True) or [])]
        if not curves:
            self._log("No curves from the last Create are left in the scene.", warn=True)
            return
        if self._send_to_joints:
            self._send_to_joints(curves, self._last_count)
