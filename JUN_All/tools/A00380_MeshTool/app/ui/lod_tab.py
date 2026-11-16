# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-16
# A00380_MeshTool - LOD 탭 (v01.20)
#
# 재생용 저폴리 프록시(LOD) 메시를 빠르게 만든다. 로직은 app/core/lod_manager.py.
# 계획서: JUN_All/docs/plans/A00380_MeshTool_LOD_plan.md
#
# 화면: Sources 리스트(공용 TSL) → LOD 수 · 비율(또는 삼각형 수) → Method · Source pose ·
# 옵션 체크 → Build LODs → 결과 표. 설정은 optionVar 로 기억한다.
# 로그는 A00380 창의 로그창을 쓴다(`log(text, warn=False, ok=False)` 콜백).

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01
from Framework.qt.MOD_progress_qt_v01 import JUN_mod_progress_qt_v01

from tools.A00380_MeshTool.app.core import lod_manager as lm


OV = "JUN_A00380_lod_"          # optionVar 접두사

DEFAULT_TRIS = (20000, 10000, 5000, 2500, 1000)

NOTES_TEXT = (
    "LOD builds low-poly copies of meshes for fast playback.\n"
    "Nothing is bound - rebind the LODs with A00275_skinTool_V01\n"
    "(Copy Weights from the source mesh).\n\n"
    "Method\n"
    "  Fast     grid clustering + quadric error per cell (numpy).\n"
    "           5 - 18x faster than polyReduce. Triangles only, approximate\n"
    "           UVs, thin parts can merge at very low ratios.\n"
    "  Quality  Maya polyReduce on a copy of the source. Slow, clean.\n\n"
    "Source pose\n"
    "  Bind     reads the orig (pre-deformer) shape, so the LOD sits in the\n"
    "           bind pose and lines up with the joints for rebinding.\n"
    "  Current  reads the deformed mesh as it looks now.\n\n"
    "Every LOD mesh records its source in attributes:\n"
    "  junLodSource (source UUID), junLodLevel, junLodTarget, junLodMethod.")


def _ov_get(key, default):
    name = OV + key
    if not cmds.optionVar(exists=name):
        return default
    value = cmds.optionVar(q=name)
    try:
        return type(default)(value)
    except Exception:
        return default


def _ov_set(key, value):
    name = OV + key
    if isinstance(value, bool):
        cmds.optionVar(iv=(name, int(value)))
    elif isinstance(value, int):
        cmds.optionVar(iv=(name, value))
    elif isinstance(value, float):
        cmds.optionVar(fv=(name, value))
    else:
        cmds.optionVar(sv=(name, str(value)))


class LodTab(QWidget):
    """LOD 탭. `log(text, warn=False, ok=False)` 는 A00380 창의 로그."""

    def __init__(self, log, parent=None):
        super().__init__(parent)
        self.log = log
        self._last_group = None
        self._build()
        self._load_settings()
        self._sync_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def _build(self):
        layout = QVBoxLayout(self)

        self.tsl = JUN_mod_tsl_qt_v01(
            title="Sources", select_label="List Selected", show_order=False,
            list_min_height=90, log_callback=self.log)
        self.tsl.setToolTip(
            "Meshes to build LODs for.  Groups are expanded - add the avatar's\n"
            "geometry group to get every mesh under it.")
        layout.addWidget(self.tsl)

        # ---- LOD 수 · 값 --------------------------------------------------
        box = QGroupBox("Levels")
        grid = QGridLayout(box)
        grid.addWidget(QLabel("LOD count"), 0, 0)
        self.sp_count = QSpinBox()
        self.sp_count.setRange(1, lm.MAX_LODS)
        self.sp_count.valueChanged.connect(self._sync_ui)
        grid.addWidget(self.sp_count, 0, 1)

        self.rb_ratio = QRadioButton("Ratio %")
        self.rb_tris = QRadioButton("Triangles")
        self.rb_ratio.setToolTip("Each LOD keeps this percentage of the source triangles.")
        self.rb_tris.setToolTip("Each LOD aims at this triangle count (per mesh).")
        grp_mode = QButtonGroup(self)
        grp_mode.addButton(self.rb_ratio)
        grp_mode.addButton(self.rb_tris)
        self.rb_ratio.toggled.connect(self._on_mode_changed)
        grid.addWidget(self.rb_ratio, 0, 2)
        grid.addWidget(self.rb_tris, 0, 3)

        self.lbl_values = []
        self.sp_values = []
        for i in range(lm.MAX_LODS):
            lbl = QLabel("LOD{0}".format(i + 1))
            sp = QDoubleSpinBox()
            sp.setKeyboardTracking(False)
            row, col = 1 + i // 3, (i % 3)
            cell = QHBoxLayout()
            cell.addWidget(lbl)
            cell.addWidget(sp, 1)
            w = QWidget()
            w.setLayout(cell)
            cell.setContentsMargins(0, 0, 0, 0)
            grid.addWidget(w, row, col if col < 2 else 2, 1, 1 if col < 2 else 2)
            self.lbl_values.append(w)
            self.sp_values.append(sp)
        layout.addWidget(box)

        # ---- Method · Pose · 옵션 ---------------------------------------
        box = QGroupBox("Options")
        grid = QGridLayout(box)
        grid.addWidget(QLabel("Method"), 0, 0)
        self.rb_fast = QRadioButton("Fast (Cluster)")
        self.rb_quality = QRadioButton("Quality (polyReduce)")
        self.rb_fast.setToolTip("Grid clustering with a quadric point per cell (numpy).\n"
                                "Much faster. Triangles only, approximate UVs.")
        self.rb_quality.setToolTip("Maya polyReduce on a copy of the source. Slow but clean.")
        g = QButtonGroup(self)
        g.addButton(self.rb_fast)
        g.addButton(self.rb_quality)
        self.rb_fast.toggled.connect(self._sync_ui)
        grid.addWidget(self.rb_fast, 0, 1)
        grid.addWidget(self.rb_quality, 0, 2)

        grid.addWidget(QLabel("Source pose"), 1, 0)
        self.rb_bind = QRadioButton("Bind")
        self.rb_current = QRadioButton("Current")
        self.rb_bind.setToolTip("Read the orig (pre-deformer) shape - the LOD lines up with\n"
                                "the joints in bind pose, ready to rebind.")
        self.rb_current.setToolTip("Read the deformed mesh as it looks at the current frame.")
        g = QButtonGroup(self)
        g.addButton(self.rb_bind)
        g.addButton(self.rb_current)
        grid.addWidget(self.rb_bind, 1, 1)
        grid.addWidget(self.rb_current, 1, 2)

        self.cb_uvs = QCheckBox("Approx UVs")
        self.cb_uvs.setToolTip("Fast: one UV per vertex - textures stretch at UV seams.\n"
                               "Off = no UVs (fastest). Quality always keeps UVs.")
        self.cb_mats = QCheckBox("Copy materials")
        self.cb_mats.setToolTip("Assign the source shading groups face by face.")
        self.cb_thin = QCheckBox("Keep thin parts")
        self.cb_thin.setToolTip("Fast: faces looking opposite ways (cloth layers, fingers) are\n"
                                "not merged together. May leave tiny cracks.")
        self.cb_combine = QCheckBox("Combine per LOD")
        self.cb_combine.setToolTip("One mesh per LOD for all sources (fewer skinClusters on\n"
                                   "playback). Rebinding then needs weights from several sources.")
        self.cb_overwrite = QCheckBox("Overwrite")
        self.cb_overwrite.setToolTip("Delete an existing <root>_LOD_grp before building.")
        grid.addWidget(self.cb_uvs, 2, 0)
        grid.addWidget(self.cb_mats, 2, 1)
        grid.addWidget(self.cb_thin, 2, 2)
        grid.addWidget(self.cb_combine, 3, 0)
        grid.addWidget(self.cb_overwrite, 3, 1)
        row = QHBoxLayout()
        row.addWidget(QLabel("Min triangles"))
        self.sp_min = QSpinBox()
        self.sp_min.setRange(0, 1000000)
        self.sp_min.setToolTip("Meshes at or below this are copied as they are, and no LOD\n"
                               "goes below it (eyes, teeth do not vanish).")
        row.addWidget(self.sp_min, 1)
        w = QWidget()
        w.setLayout(row)
        row.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(w, 3, 2)
        layout.addWidget(box)

        # ---- 실행 ---------------------------------------------------------
        self.btn_build = QPushButton("Build LODs")
        self.btn_build.setMinimumHeight(32)
        self.btn_build.clicked.connect(self.on_build)
        layout.addWidget(self.btn_build)

        row = QHBoxLayout()
        self.btn_select = []
        for i in range(lm.MAX_LODS):
            b = QPushButton("LOD{0}".format(i + 1))
            b.setToolTip("Select the LOD{0} meshes of the last build.".format(i + 1))
            b.clicked.connect(lambda _=False, lv=i + 1: self.on_select(lv))
            row.addWidget(b)
            self.btn_select.append(b)
        self.btn_delete = QPushButton("Delete LODs")
        self.btn_delete.setToolTip("Delete the LOD group of the last build (undoable).")
        self.btn_delete.clicked.connect(self.on_delete)
        row.addWidget(self.btn_delete)
        layout.addLayout(row)

        # ---- 결과 표 ------------------------------------------------------
        self.tree = QTreeWidget()
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setMinimumHeight(80)
        self.tree.setMaximumHeight(170)
        self.tree.itemClicked.connect(self._on_row_clicked)
        layout.addWidget(self.tree)
        layout.addStretch(1)

        if not lm.has_numpy():
            self.btn_build.setEnabled(False)
            self.btn_build.setToolTip("numpy is not available in this Maya.")

    # ==================================================================
    # 설정
    # ==================================================================

    def _mode(self):
        return "ratio" if self.rb_ratio.isChecked() else "triangles"

    def _load_settings(self):
        self.sp_count.setValue(_ov_get("count", 3))
        mode = _ov_get("mode", "ratio")
        # 불러오는 중엔 모드 전환 핸들러가 빈 칸 값을 optionVar 에 덮어쓰지 않게 막는다
        self.rb_ratio.blockSignals(True)
        (self.rb_tris if mode == "triangles" else self.rb_ratio).setChecked(True)
        self.rb_ratio.blockSignals(False)
        (self.rb_quality if _ov_get("method", "fast") == "quality" else self.rb_fast).setChecked(True)
        (self.rb_current if _ov_get("pose", "bind") == "current" else self.rb_bind).setChecked(True)
        self.cb_uvs.setChecked(bool(_ov_get("uvs", 1)))
        self.cb_mats.setChecked(bool(_ov_get("mats", 1)))
        self.cb_thin.setChecked(bool(_ov_get("thin", 1)))
        self.cb_combine.setChecked(bool(_ov_get("combine", 0)))
        self.cb_overwrite.setChecked(bool(_ov_get("overwrite", 1)))
        self.sp_min.setValue(_ov_get("min_tris", 100))
        self._apply_value_mode(mode)

    def _apply_value_mode(self, mode):
        for i, sp in enumerate(self.sp_values):
            sp.blockSignals(True)
            if mode == "ratio":
                sp.setDecimals(2)
                sp.setRange(0.1, 100.0)
                sp.setSingleStep(5.0)
                sp.setSuffix(" %")
                sp.setValue(_ov_get("ratio{0}".format(i + 1), float(lm.DEFAULT_VALUES[i])))
            else:
                sp.setDecimals(0)
                sp.setRange(4, 10000000)
                sp.setSingleStep(500)
                sp.setSuffix("")
                sp.setValue(_ov_get("tris{0}".format(i + 1), float(DEFAULT_TRIS[i])))
            sp.blockSignals(False)

    def _save_settings(self):
        mode = self._mode()
        _ov_set("count", self.sp_count.value())
        _ov_set("mode", mode)
        _ov_set("method", "fast" if self.rb_fast.isChecked() else "quality")
        _ov_set("pose", "bind" if self.rb_bind.isChecked() else "current")
        _ov_set("uvs", self.cb_uvs.isChecked())
        _ov_set("mats", self.cb_mats.isChecked())
        _ov_set("thin", self.cb_thin.isChecked())
        _ov_set("combine", self.cb_combine.isChecked())
        _ov_set("overwrite", self.cb_overwrite.isChecked())
        _ov_set("min_tris", self.sp_min.value())
        for i, sp in enumerate(self.sp_values):
            _ov_set(("ratio{0}" if mode == "ratio" else "tris{0}").format(i + 1), float(sp.value()))

    def _on_mode_changed(self, _checked=None):
        # 떠나는 모드의 값을 저장하고, 들어가는 모드의 값을 불러온다
        old = "triangles" if self.rb_ratio.isChecked() else "ratio"
        for i, sp in enumerate(self.sp_values):
            _ov_set(("ratio{0}" if old == "ratio" else "tris{0}").format(i + 1), float(sp.value()))
        self._apply_value_mode(self._mode())

    def _sync_ui(self, *_):
        n = self.sp_count.value()
        for i in range(lm.MAX_LODS):
            self.lbl_values[i].setVisible(i < n)
            self.btn_select[i].setVisible(i < n)
        fast = self.rb_fast.isChecked()
        self.cb_uvs.setEnabled(fast)
        self.cb_thin.setEnabled(fast)

    def options(self):
        return lm.LodOptions(
            count=self.sp_count.value(),
            mode=self._mode(),
            values=tuple(sp.value() for sp in self.sp_values),
            method="fast" if self.rb_fast.isChecked() else "quality",
            source_pose="bind" if self.rb_bind.isChecked() else "current",
            approx_uvs=self.cb_uvs.isChecked(),
            copy_materials=self.cb_mats.isChecked(),
            keep_thin=self.cb_thin.isChecked(),
            combine=self.cb_combine.isChecked(),
            overwrite=self.cb_overwrite.isChecked(),
            min_tris=self.sp_min.value())

    # ==================================================================
    # 동작
    # ==================================================================

    def on_build(self):
        nodes = self.tsl.get_all_nodes()
        if not nodes:
            self.log("Add meshes (or the avatar's geometry group) to the Sources list.", warn=True)
            return
        self._save_settings()
        opts = self.options()
        dlg = JUN_mod_progress_qt_v01(self, title="Mesh Tool - Build LODs",
                                      phases=[("Building LODs", 100)])
        dlg.start()
        report = None
        try:
            dlg.begin_phase()
            report = lm.build_lods(nodes, opts, progress=dlg.callback())
        except Exception as e:
            self.log("Build LODs failed: {0}".format(e), warn=True)
            return
        finally:
            dlg.finish()

        self._last_group = report.group
        self._fill_table(report, opts)
        n_mesh = sum(len(r.lods) for r in report.results) + len(report.combined)
        self.log("Built {0} LOD mesh(es) from {1} source(s) in {2:.2f}s ({3}) -> {4}".format(
            n_mesh, len(report.results), report.seconds, opts.method,
            report.group.split("|")[-1]), ok=True)
        for r in report.results:
            for w in r.warnings:
                self.log("  {0}: {1}".format(r.source, w), warn=True)
        self.log("  Not bound - rebind with A00275_skinTool_V01 (Copy Weights from the source).")

    def _fill_table(self, report, opts):
        n = opts.count
        headers = ["Mesh", "Source"] + ["LOD{0}".format(i + 1) for i in range(n)] + ["Time"]
        self.tree.clear()
        self.tree.setColumnCount(len(headers))
        self.tree.setHeaderLabels(headers)
        for r in report.results:
            cols = [r.source, str(r.src_tris)]
            by = {lv: t for lv, _, t in r.lods}
            cols += [str(by.get(i + 1, "-")) for i in range(n)]
            cols.append("{0:.2f}s".format(r.seconds))
            item = QTreeWidgetItem(cols)
            item.setData(0, Qt.UserRole, [m for _, m, _ in r.lods])
            if r.warnings:
                item.setToolTip(0, "\n".join(r.warnings))
            self.tree.addTopLevelItem(item)
        if report.combined:
            by = {lv: t for lv, _, t in report.combined}
            cols = ["(combined)", str(sum(r.src_tris for r in report.results))]
            cols += [str(by.get(i + 1, "-")) for i in range(n)]
            cols.append("{0:.2f}s".format(report.seconds))
            item = QTreeWidgetItem(cols)
            item.setData(0, Qt.UserRole, [m for _, m, _ in report.combined])
            self.tree.addTopLevelItem(item)
        for c in range(len(headers)):
            self.tree.resizeColumnToContents(c)

    def _on_row_clicked(self, item, _col):
        meshes = [m for m in (item.data(0, Qt.UserRole) or []) if cmds.objExists(m)]
        if meshes:
            cmds.select(meshes, r=True)

    def _group(self):
        if self._last_group and cmds.objExists(self._last_group):
            return self._last_group
        # 창을 다시 연 뒤에는 씬의 LOD 그룹 중 마지막 것
        for g in reversed(cmds.ls("*_LOD_grp*", type="transform", l=True) or []):
            if lm.lod_meshes(g):
                return g
        return None

    def on_select(self, level):
        meshes = lm.lod_meshes(self._group(), level)
        if not meshes:
            self.log("No LOD{0} meshes found.".format(level), warn=True)
            return
        cmds.select(meshes, r=True)
        self.log("Selected {0} LOD{1} mesh(es).".format(len(meshes), level))

    def on_delete(self):
        group = self._group()
        if not group:
            self.log("No LOD group to delete.", warn=True)
            return
        lm.delete_group(group)
        self.log("Deleted {0} (Ctrl+Z to bring it back).".format(group.split("|")[-1]), ok=True)
        self._last_group = None
        self.tree.clear()
