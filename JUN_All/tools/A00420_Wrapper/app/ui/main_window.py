# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-10
# A00420_Wrapper - Qt UI
#
# 토폴로지가 다른 두 메시를 **커브 가이드**로 짝지어 소스를 타깃 형태로 래핑한다.
# Wrap3D 로 치면 SelectPointPairs(가이드) + Wrapping(래핑) 을 한 창에 넣은 것이고,
# 다른 점은 가이드가 낱개 포인트가 아니라 **커브 쌍**이라는 것이다.
#
# 화면 흐름: Meshes(소스/타깃) -> Guide Pairs(커브 쌍 목록) -> 설정 -> Wrap.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_collapsible_qt

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00420_Wrapper.app.config.version import VERSION, LAST_UPDATE

# core 는 numpy 를 쓴다(Maya 2022+ 내장). 없으면 창은 뜨되 기능을 막고 이유를 알린다.
try:
    from tools.A00420_Wrapper.app.core import wrap_manager as wrap_mgr
    from tools.A00420_Wrapper.app.core import guide_sampler as guide_mod
    CORE_ERROR = ""
except Exception as _e:                                   # pragma: no cover
    wrap_mgr = None
    guide_mod = None
    CORE_ERROR = str(_e)


WINDOW_OBJECT_NAME = "JUN_A00420_Wrapper_window"

_WARN_COLOR = "#ffb454"
_OK_COLOR = "#8bd450"

# Guide Pairs 트리 컬럼
COL_ON = 0
COL_SOURCE = 1
COL_TARGET = 2
COL_FLIP = 3
COL_INFO = 4


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Wrapper v{0}".format(VERSION)
        self.resize(460, 860)

        # 가이드 쌍 목록 (트리 행 순서와 1:1)
        self.pairs = []
        self._updating = False

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        root.addWidget(self._build_mesh_box())
        root.addWidget(self._build_guide_box(), 1)
        root.addWidget(self._build_guide_settings())
        root.addWidget(self._build_wrap_settings())
        root.addWidget(self._build_output_box())

        self.btn_wrap = QPushButton("Wrap")
        self.btn_wrap.setMinimumHeight(38)
        self.btn_wrap.setToolTip(
            "Warp the source mesh onto the target using the guide pairs,\n"
            "then project it onto the target surface.")
        self.btn_wrap.clicked.connect(self.on_wrap)
        root.addWidget(self.btn_wrap)

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(110)
        root.addWidget(self.te_log)

        if CORE_ERROR:
            self.btn_wrap.setEnabled(False)
            self.log("Core modules failed to load: {0}".format(CORE_ERROR), warn=True)
            self.log("This tool needs numpy (bundled with Maya 2022+).", warn=True)
        else:
            self.log("Wrapper v{0} ({1}) ready. Set Source / Target meshes, then add "
                     "guide curve pairs.".format(VERSION, LAST_UPDATE))

    # ---------------- meshes ----------------

    def _build_mesh_box(self):
        box = QGroupBox("Meshes")
        lay = QVBoxLayout(box)

        self.le_source = QLineEdit()
        self.le_source.setPlaceholderText("mesh to be deformed")
        lay.addLayout(self._mesh_row("Source", self.le_source))

        self.le_target = QLineEdit()
        self.le_target.setPlaceholderText("mesh to match")
        lay.addLayout(self._mesh_row("Target", self.le_target))

        return box

    def _mesh_row(self, label, line_edit):
        row = QHBoxLayout()

        tag = QLabel(label)
        tag.setMinimumWidth(48)
        row.addWidget(tag)
        row.addWidget(line_edit, 1)

        btn = QPushButton("<<")
        btn.setFixedWidth(34)
        btn.setToolTip("Load the selected mesh.")
        btn.clicked.connect(lambda: self.on_load_mesh(line_edit))
        row.addWidget(btn)

        sel = QPushButton("Sel")
        sel.setFixedWidth(38)
        sel.setToolTip("Select this mesh in the scene.")
        sel.clicked.connect(lambda: self.on_select_field(line_edit))
        row.addWidget(sel)

        return row

    # ---------------- guide pairs ----------------

    def _build_guide_box(self):
        box = QGroupBox("Guide Pairs  (source curve  ->  target curve)")
        lay = QVBoxLayout(box)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["On", "Source", "Target", "Flip", "Info"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setMinimumHeight(150)
        self.tree.itemChanged.connect(self.on_item_changed)

        header = self.tree.header()
        self.tree.setColumnWidth(COL_ON, 34)
        self.tree.setColumnWidth(COL_FLIP, 40)
        header.setStretchLastSection(True)
        lay.addWidget(self.tree, 1)

        row1 = QHBoxLayout()
        for label, slot, tip in (
            ("Add Curve Pair", self.on_add_curve_pair,
             "Select the source curve first, then the target curve.\n"
             "Selecting 4, 6, ... curves adds them as consecutive pairs."),
            ("Add Point Pair", self.on_add_point_pair,
             "Select a source point (vertex / locator / transform), then a target point."),
        ):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            row1.addWidget(btn)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        for label, slot, tip in (
            ("Curve from Edges", self.on_curve_from_edges,
             "Build a guide curve along the selected mesh edges (A00400_CurveTool)."),
            ("Remove", self.on_remove_pair, "Remove the selected rows."),
            ("Clear", self.on_clear_pairs, "Remove every guide pair."),
        ):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            row2.addWidget(btn)
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        btn_prev = QPushButton("Show Guide Links")
        btn_prev.setToolTip(
            "Draw a line from every source sample to its matching target sample.\n"
            "Crossed lines mean the curve direction or start point does not match.")
        btn_prev.clicked.connect(self.on_preview)
        row3.addWidget(btn_prev)

        btn_clear_prev = QPushButton("Clear Links")
        btn_clear_prev.clicked.connect(self.on_clear_preview)
        row3.addWidget(btn_clear_prev)
        lay.addLayout(row3)

        return box

    # ---------------- guide settings ----------------

    def _build_guide_settings(self):
        sec = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01("Guide Settings", True)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.sp_samples = QSpinBox()
        self.sp_samples.setRange(2, 500)
        self.sp_samples.setValue(24)
        self.sp_samples.setToolTip(
            "How many points each curve is sampled into (evenly by arc length).\n"
            "More samples = tighter control along the curve.")
        form.addRow("Samples per curve", self.sp_samples)

        self.chk_auto_align = QCheckBox("Auto align direction / start point")
        self.chk_auto_align.setChecked(True)
        self.chk_auto_align.setToolTip(
            "Try both curve directions (and, for closed curves, every start point)\n"
            "and keep the combination whose shapes match best.\n"
            "Turn off to use the per-row Flip checkbox instead.")
        form.addRow("", self.chk_auto_align)

        self.chk_snap = QCheckBox("Snap guide samples to the mesh surface")
        self.chk_snap.setChecked(True)
        self.chk_snap.setToolTip(
            "Pull every sample onto the closest point of its own mesh, so the warp\n"
            "maps surface to surface even if the curves float slightly off.")
        form.addRow("", self.chk_snap)

        sec.add_layout(form)
        return sec

    # ---------------- wrap settings ----------------

    def _build_wrap_settings(self):
        sec = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01("Wrap Settings", True)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.dsp_smooth = self._dspin(0.0, 0.0, 10.0, 0.01, 3)
        self.dsp_smooth.setToolTip(
            "Thin plate spline regularisation.\n"
            "0 = the warp passes exactly through every guide sample.\n"
            "Raise it when the two curves differ a lot and the result buckles.")
        form.addRow("Smoothness", self.dsp_smooth)

        self.sp_iterations = QSpinBox()
        self.sp_iterations.setRange(0, 100)
        self.sp_iterations.setValue(5)
        self.sp_iterations.setToolTip(
            "Surface projection passes after the warp. 0 = warp only.")
        form.addRow("Projection steps", self.sp_iterations)

        self.dsp_strength = self._dspin(1.0, 0.0, 1.0, 0.05, 2)
        self.dsp_strength.setToolTip(
            "How far each vertex travels toward the closest target point per pass.")
        form.addRow("Projection strength", self.dsp_strength)

        self.dsp_relax = self._dspin(0.3, 0.0, 1.0, 0.05, 2)
        self.dsp_relax.setToolTip(
            "Laplacian smoothing applied to the projection movement.\n"
            "Higher keeps the mesh even but follows the target less tightly.")
        form.addRow("Relax", self.dsp_relax)

        self.sp_relax_steps = QSpinBox()
        self.sp_relax_steps.setRange(0, 20)
        self.sp_relax_steps.setValue(2)
        form.addRow("Relax steps", self.sp_relax_steps)

        self.dsp_max_dist = self._dspin(0.0, 0.0, 100000.0, 0.1, 3)
        self.dsp_max_dist.setToolTip(
            "Vertices farther than this from the target surface are left alone.\n"
            "0 = no limit. Useful when the source mesh reaches past the target.")
        form.addRow("Max distance", self.dsp_max_dist)

        self.dsp_angle = self._dspin(90.0, 0.0, 180.0, 5.0, 1)
        self.dsp_angle.setToolTip(
            "Skip a vertex when the target surface normal differs by more than this,\n"
            "which stops the outer skin from grabbing an inner surface. 0 = no check.")
        form.addRow("Normal angle limit", self.dsp_angle)

        sec.add_layout(form)
        return sec

    # ---------------- output ----------------

    def _build_output_box(self):
        box = QGroupBox("Output")
        lay = QVBoxLayout(box)

        row = QHBoxLayout()
        self.rb_new = QRadioButton("New mesh (duplicate)")
        self.rb_new.setChecked(True)
        self.rb_new.setToolTip("Keep the source untouched and write the result to a copy.")
        self.rb_in_place = QRadioButton("In place")
        self.rb_in_place.setToolTip("Move the source mesh vertices directly.")
        row.addWidget(self.rb_new)
        row.addWidget(self.rb_in_place)
        lay.addLayout(row)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.le_suffix = QLineEdit("_wrap")
        form.addRow("Suffix", self.le_suffix)

        self.dsp_amount = self._dspin(1.0, 0.0, 1.0, 0.05, 2)
        self.dsp_amount.setToolTip(
            "Blend between the original shape (0) and the wrapped shape (1).")
        form.addRow("Amount", self.dsp_amount)

        lay.addLayout(form)
        return box

    @staticmethod
    def _dspin(value, low, high, step, decimals):
        sp = QDoubleSpinBox()
        sp.setRange(low, high)
        sp.setSingleStep(step)
        sp.setDecimals(decimals)
        sp.setValue(value)
        # 값을 되쓰는 스핀박스는 타이핑 중 값이 잘리지 않도록 keyboardTracking 을 끈다.
        sp.setKeyboardTracking(False)
        return sp

    # ==============================================================
    # mesh fields
    # ==============================================================

    def on_load_mesh(self, line_edit):
        sel = cmds.ls(sl=True, long=True) or []
        if not sel:
            self.log("Select a mesh first.", warn=True)
            return

        from tools.A00420_Wrapper.app.core.mesh_utils import mesh_shape_of

        node = sel[0].split(".")[0]
        if not mesh_shape_of(node):
            self.log("'{0}' is not a polygon mesh.".format(node.split("|")[-1]), warn=True)
            return

        line_edit.setText(node)
        self.log("Loaded {0}.".format(node.split("|")[-1]))

    def on_select_field(self, line_edit):
        name = line_edit.text().strip()
        if name and cmds.objExists(name):
            cmds.select(name, replace=True)
        else:
            self.log("Nothing to select.", warn=True)

    # ==============================================================
    # guide pairs
    # ==============================================================

    def _add_pair(self, kind, source, target):
        pair = guide_mod.GuidePair(kind, source, target)
        self.pairs.append(pair)
        self._append_row(pair)

    def _append_row(self, pair):
        self._updating = True
        try:
            item = QTreeWidgetItem(self.tree)
            item.setCheckState(COL_ON, Qt.Checked if pair.enabled else Qt.Unchecked)
            item.setText(COL_SOURCE, pair.source.split("|")[-1])
            item.setText(COL_TARGET, pair.target.split("|")[-1])
            item.setCheckState(COL_FLIP, Qt.Checked if pair.flip else Qt.Unchecked)
            item.setText(COL_INFO, "point" if pair.kind == guide_mod.KIND_POINT else "curve")
        finally:
            self._updating = False

    def on_item_changed(self, item, column):
        if self._updating:
            return

        row = self.tree.indexOfTopLevelItem(item)
        if row < 0 or row >= len(self.pairs):
            return

        pair = self.pairs[row]
        if column == COL_ON:
            pair.enabled = item.checkState(COL_ON) == Qt.Checked
        elif column == COL_FLIP:
            pair.flip = item.checkState(COL_FLIP) == Qt.Checked

    def on_add_curve_pair(self):
        from tools.A00420_Wrapper.app.core.mesh_utils import curve_shape_of

        sel = cmds.ls(sl=True, long=True) or []
        curves = [s for s in sel if curve_shape_of(s)]

        if len(curves) < 2 or len(curves) % 2:
            self.log("Select curves in pairs: source curve first, then target curve "
                     "(2, 4, 6 ... curves).", warn=True)
            return

        for i in range(0, len(curves), 2):
            self._add_pair(guide_mod.KIND_CURVE, curves[i], curves[i + 1])

        self.log("Added {0} curve pair(s).".format(len(curves) // 2))

    def on_add_point_pair(self):
        sel = cmds.ls(sl=True, long=True, flatten=True) or []

        if len(sel) < 2 or len(sel) % 2:
            self.log("Select points in pairs: source point first, then target point.",
                     warn=True)
            return

        for i in range(0, len(sel), 2):
            self._add_pair(guide_mod.KIND_POINT, sel[i], sel[i + 1])

        self.log("Added {0} point pair(s).".format(len(sel) // 2))

    def on_curve_from_edges(self):
        """선택한 메시 엣지를 따라 가이드 커브를 만든다 (A00400_CurveTool 재사용)."""
        try:
            from tools.A00400_CurveTool.app.core import curve_manager
        except Exception as e:
            self.log("A00400_CurveTool is not available: {0}".format(e), warn=True)
            return

        try:
            with undo_chunk():
                created, groups = curve_manager.curves_from_selected_edges(
                    prefix="guideCurve", degree=1)
        except ValueError as e:
            self.log(str(e), warn=True)
            return
        except Exception as e:
            self.log("Curve creation failed: {0}".format(e), warn=True)
            return

        self.log("Created {0} guide curve(s) from {1} edge group(s): {2}".format(
            len(created), groups, ", ".join(created)))
        self.log("Pair them up with 'Add Curve Pair' once both sides exist.")

    def on_remove_pair(self):
        rows = sorted((self.tree.indexOfTopLevelItem(i)
                       for i in self.tree.selectedItems()), reverse=True)
        if not rows:
            self.log("Select rows to remove.", warn=True)
            return

        for row in rows:
            self.tree.takeTopLevelItem(row)
            del self.pairs[row]

        self.log("Removed {0} guide pair(s).".format(len(rows)))

    def on_clear_pairs(self):
        self.tree.clear()
        self.pairs = []
        self.log("Guide pair list cleared.")

    # ==============================================================
    # preview
    # ==============================================================

    def on_preview(self):
        source, target = self._meshes()
        if not source:
            return
        if not self.pairs:
            self.log("Add at least one guide pair first.", warn=True)
            return

        options = self._options()

        try:
            with undo_chunk():
                made, group = wrap_mgr.build_preview(
                    source, target, self.pairs, options, log=self.log)
        except Exception as e:
            self.log("Preview failed: {0}".format(e), warn=True)
            return

        self._refresh_info()
        self.log("Guide links: {0} line(s) under '{1}'. Red line = first sample "
                 "(start point).".format(made, group))

    def on_clear_preview(self):
        with undo_chunk():
            removed = wrap_mgr.clear_preview()
        self.log("Guide links cleared." if removed else "No guide links to clear.")

    def _refresh_info(self):
        """마지막 샘플링에서 실제로 쓰인 방향/시작점 정보를 Info 컬럼에 반영한다."""
        self._updating = True
        try:
            for row, pair in enumerate(self.pairs):
                item = self.tree.topLevelItem(row)
                if item is not None and pair.resolved:
                    item.setText(COL_INFO, pair.resolved)
        finally:
            self._updating = False

    # ==============================================================
    # wrap
    # ==============================================================

    def _meshes(self):
        source = self.le_source.text().strip()
        target = self.le_target.text().strip()

        if not source or not cmds.objExists(source):
            self.log("Source mesh is not set.", warn=True)
            return None, None
        if not target or not cmds.objExists(target):
            self.log("Target mesh is not set.", warn=True)
            return None, None

        return source, target

    def _options(self):
        opt = wrap_mgr.WrapOptions()

        opt.samples = self.sp_samples.value()
        opt.auto_align = self.chk_auto_align.isChecked()
        opt.snap_guides = self.chk_snap.isChecked()

        opt.smoothness = self.dsp_smooth.value()
        opt.iterations = self.sp_iterations.value()
        opt.strength = self.dsp_strength.value()
        opt.relax = self.dsp_relax.value()
        opt.relax_steps = self.sp_relax_steps.value()
        opt.max_distance = self.dsp_max_dist.value()
        opt.angle_limit = self.dsp_angle.value()

        opt.output = (wrap_mgr.OUTPUT_NEW if self.rb_new.isChecked()
                      else wrap_mgr.OUTPUT_IN_PLACE)
        opt.suffix = self.le_suffix.text().strip() or "_wrap"
        opt.amount = self.dsp_amount.value()

        return opt

    def on_wrap(self):
        source, target = self._meshes()
        if not source:
            return

        if not self.pairs:
            self.log("Add at least one guide pair first.", warn=True)
            return

        options = self._options()

        self.btn_wrap.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            with undo_chunk():
                result = wrap_mgr.wrap(source, target, self.pairs, options,
                                       log=self.log, progress=self._progress)
        except Exception as e:
            self.log("Wrap failed: {0}".format(e), warn=True)
            return
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_wrap.setEnabled(True)
            self._refresh_info()

        self.log("Wrapped {0} vertex(es) -> {1}".format(
            result.vertex_count, result.node.split("|")[-1]), ok=True)

        if options.output == wrap_mgr.OUTPUT_NEW and cmds.objExists(result.node):
            cmds.select(result.node, replace=True)

    def _progress(self, step, total, gap):
        self.log("  projection {0}/{1}  mean gap {2:.5f}".format(step, total, gap))
        QApplication.processEvents()

    # ==============================================================
    # log / about
    # ==============================================================

    @staticmethod
    def _esc(text):
        return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def log(self, text, warn=False, ok=False):
        if warn:
            self.te_log.append(
                '<span style="color:{0};">{1}</span>'.format(_WARN_COLOR, self._esc(text)))
        elif ok:
            self.te_log.append(
                '<span style="color:{0};">{1}</span>'.format(_OK_COLOR, self._esc(text)))
        else:
            self.te_log.append(text)

        self.te_log.moveCursor(QTextCursor.End)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Wrapper\nv{0}  ({1})\n\n"
            "Wrap a source mesh onto a target mesh of different topology,\n"
            "guided by pairs of curves (lips, eye rims, nose ...).\n\n"
            "1. Guide curves become matching control points.\n"
            "2. A thin plate spline warps the source onto the target.\n"
            "3. The warped mesh is projected onto the target surface.\n\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))
