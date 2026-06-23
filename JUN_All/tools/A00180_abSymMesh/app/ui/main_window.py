# -*- coding: utf-8 -*-
"""
abSymMesh - PySide(Qt) UI.

기존 maya.cmds UI(abSymMesh_v01.py)를 PySide 로 재작업한 버전.
로직(app/core: mesh_io / sym_core / undo_*)은 그대로 재사용하고 화면만 Qt 로 바꾼다.
Framework.qt.qt 가 PySide6 -> PySide2 폴백을 처리하므로 Maya 2023(PySide2)~최신 호환.

UI 문자열/로그는 영어. 씬 선택/Undo 청크는 maya.cmds, 정점 I/O 는 app.core 가 담당.
"""

import math
from contextlib import contextmanager

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window

from ..config.version import VERSION, LAST_UPDATE
from ..core import mesh_io
from ..core import sym_core
from ..core import snap_core
from ..core import mesh_ops


WINDOW_OBJECT_NAME = "JUN_A00180_abSymMesh_window"


class _ProgressCancelled(Exception):
    """진행률 팝업에서 Cancel 을 누르면 무거운 코어 루프를 빠져나오기 위한 신호."""
    pass

_AXIS_LETTER = ["X", "Y", "Z"]
# revert 팝업 % 값(1111 은 divider).
_REVERT_PCTS = [1, 2, 3, 4, 5, None, 10, 20, 30, 40, 50, 60, 70, 80, 90]
_SLIDER_STEPS = 1000


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("abSymMesh v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(300, 640)

        # 상태(원본 전역 대체)
        self.sbg = ""          # base geometry
        self.alt_sbg = ""      # alternate base
        self.sym = None        # compute_symmetry 결과

        # revert 슬라이더 드래그 상태
        self._drag_active = False
        self._drag = None
        self._overshoot = False

        self._dep_widgets = []   # base 의존 위젯

        self._build_ui()

        # undo 커맨드 플러그인 로드(실패해도 창은 뜨고, 실제 편집 직전 재시도된다).
        try:
            mesh_io.ensure_undo_plugin()
        except Exception as exc:
            self._warn("Undo plugin not loaded yet: {0}".format(exc))

    # ==================================================================
    # UI 구성
    # ==================================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        root.setMenuBar(self._build_menu_bar())

        # 탭: abSymMesh(기존) / Snap to Sym(신규). 향후 기능은 새 탭으로 추가.
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_absym_tab(), "abSymMesh")
        self.tabs.addTab(self._build_snap_tab(), "Snap to Sym")
        self.tabs.addTab(self._build_mirrordeform_tab(), "Mirror Deform")
        root.addWidget(self.tabs)

        # 로그 / 푸터는 탭 공용(항상 보임).
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(90)
        root.addWidget(self.log_view)

        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

        self._set_dep_enabled(False)

    def _build_absym_tab(self):
        """기존 abSymMesh 기능 전체를 담는 탭."""
        tab = QWidget()
        root = QVBoxLayout(tab)

        root.addLayout(self._build_axis_row())
        root.addLayout(self._build_tol_row())
        root.addWidget(self._hline())

        self.btn_base = QPushButton("Select Base Geometry")
        self.btn_base.clicked.connect(self.on_select_base)
        root.addWidget(self.btn_base)
        self.le_base = QLineEdit()
        self.le_base.setReadOnly(True)
        root.addWidget(self.le_base)
        root.addWidget(self._hline())

        self.btn_check = QPushButton("Check Symmetry")
        self.btn_check.clicked.connect(self.on_check_symmetry)
        root.addWidget(self.btn_check)

        self.btn_selmirror = self._dep_button("Selection Mirror", self.on_selection_mirror)
        root.addWidget(self.btn_selmirror)
        self.btn_selmoved = self._dep_button("Select Moved Verts", lambda: self.on_select_moved(False))
        root.addWidget(self.btn_selmoved)
        root.addWidget(self._hline())

        self.btn_mirror = self._dep_button("Mirror Selected", self.on_mirror)
        root.addWidget(self.btn_mirror)
        self.btn_flip = self._dep_button("Flip Selected", self.on_flip)
        root.addWidget(self.btn_flip)

        self.btn_revert = self._dep_button("Revert Selected to Base", lambda: self.on_revert(1.0))
        self.btn_revert.setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn_revert.customContextMenuRequested.connect(self._show_revert_menu)
        root.addWidget(self.btn_revert)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(_SLIDER_STEPS)
        self.slider.setValue(self._bias_to_slider(1.0))
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.slider.setContextMenuPolicy(Qt.CustomContextMenu)
        self.slider.customContextMenuRequested.connect(self._show_base_menu)
        self._dep_widgets.append(self.slider)
        root.addWidget(self.slider)
        root.addWidget(self._hline())

        self.cb_neg2pos = QCheckBox("Operate -X to +X")
        root.addWidget(self.cb_neg2pos)
        self.cb_usepiv = QCheckBox("Use Pivot as Origin")
        self.cb_usepiv.setChecked(True)
        root.addWidget(self.cb_usepiv)

        root.addStretch(1)
        return tab

    # ------------------------------------------------------------------
    # Snap to Sym 탭 (nearpoint 스냅 + 기하학적 대칭 레퍼런스 생성)
    # ------------------------------------------------------------------

    def _build_snap_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        root.addWidget(QLabel(
            "Snap an asymmetric mesh onto a symmetric reference\n"
            "(Houdini nearpoint style). Topology need not match."))

        # Source (수정 대상)
        src_row = QHBoxLayout()
        self.btn_snap_src = QPushButton("Set Source")
        self.btn_snap_src.clicked.connect(self.on_snap_set_source)
        self.le_snap_src = QLineEdit()
        self.le_snap_src.setReadOnly(True)
        self.le_snap_src.setPlaceholderText("Source (mesh to modify)")
        src_row.addWidget(self.btn_snap_src)
        src_row.addWidget(self.le_snap_src)
        root.addLayout(src_row)

        # Reference (대칭 레퍼런스)
        ref_row = QHBoxLayout()
        self.btn_snap_ref = QPushButton("Set Reference")
        self.btn_snap_ref.clicked.connect(self.on_snap_set_reference)
        self.le_snap_ref = QLineEdit()
        self.le_snap_ref.setReadOnly(True)
        self.le_snap_ref.setPlaceholderText("Reference (symmetric mesh)")
        ref_row.addWidget(self.btn_snap_ref)
        ref_row.addWidget(self.le_snap_ref)
        root.addLayout(ref_row)

        root.addWidget(self._hline())

        # 스냅 모드 (기본: 최근접 정점)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Snap to"))
        self.snap_mode_group = QButtonGroup(self)
        rb_vtx = QRadioButton("Nearest Vertex")
        rb_srf = QRadioButton("Closest Surface")
        rb_vtx.setChecked(True)
        self.snap_mode_group.addButton(rb_vtx, 0)   # 0 = nearest vertex
        self.snap_mode_group.addButton(rb_srf, 1)   # 1 = closest surface
        mode_row.addWidget(rb_vtx)
        mode_row.addWidget(rb_srf)
        mode_row.addStretch(1)
        root.addLayout(mode_row)

        self.cb_snap_selected = QCheckBox("Selected vertices only")
        root.addWidget(self.cb_snap_selected)

        self.btn_snap_apply = QPushButton("Snap Source to Reference")
        self.btn_snap_apply.clicked.connect(self.on_snap_apply)
        root.addWidget(self.btn_snap_apply)

        root.addWidget(self._hline())

        # 대칭 레퍼런스 생성
        root.addWidget(QLabel("Make Symmetric Reference"))
        sym_row = QHBoxLayout()
        sym_row.addWidget(QLabel("Mirror Axis"))
        self.snap_axis_group = QButtonGroup(self)
        for idx, label in enumerate(["X", "Y", "Z"]):
            rb = QRadioButton(label)
            self.snap_axis_group.addButton(rb, idx)   # 0/1/2 = X/Y/Z
            sym_row.addWidget(rb)
            if idx == 0:
                rb.setChecked(True)
        sym_row.addStretch(1)
        root.addLayout(sym_row)

        # Method(미러/평균) + 소스 면 방향
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Method"))
        self.cmb_sym_method = QComboBox()
        # 0 = Mirror one side(정점 위치 복사), 1 = Average both(평균),
        # 2 = Mirror geometry(반 잘라 미러, 토폴로지 재생성)
        self.cmb_sym_method.addItems(
            ["Mirror one side", "Average both", "Mirror geometry (cut)"])
        method_row.addWidget(self.cmb_sym_method)
        method_row.addWidget(QLabel("Source"))
        self.cmb_sym_side = QComboBox()
        # 0 = +to-, 1 = -to+ (Mirror one side 일 때만 의미)
        self.cmb_sym_side.addItems(["+ to -", "- to +"])
        method_row.addWidget(self.cmb_sym_side)
        method_row.addStretch(1)
        root.addLayout(method_row)
        # Average 모드(1)에선 소스 면 선택이 의미 없으므로 비활성.
        self.cmb_sym_method.currentIndexChanged.connect(
            lambda i: self.cmb_sym_side.setEnabled(i != 1))

        # 대칭 평면 원점 + 시임 허용오차(Mirror geometry 용)
        origin_row = QHBoxLayout()
        origin_row.addWidget(QLabel("Origin"))
        self.cmb_sym_origin = QComboBox()
        # 0 = Object Pivot, 1 = World 0, 2 = BBox Center
        self.cmb_sym_origin.addItems(["Object Pivot", "World 0", "BBox Center"])
        origin_row.addWidget(self.cmb_sym_origin)
        origin_row.addWidget(QLabel("Seam tol"))
        self.spin_seam_tol = QDoubleSpinBox()
        self.spin_seam_tol.setDecimals(4)
        self.spin_seam_tol.setRange(0.0, 1.0)
        self.spin_seam_tol.setSingleStep(0.001)
        self.spin_seam_tol.setValue(0.001)
        self.spin_seam_tol.setToolTip(
            "Mirror geometry: seam snap / merge tolerance "
            "(verts within this distance of the plane are treated as the seam).")
        origin_row.addWidget(self.spin_seam_tol)
        origin_row.addStretch(1)
        root.addLayout(origin_row)

        self.btn_make_symref = QPushButton("Make Symmetric Reference from Source")
        self.btn_make_symref.clicked.connect(self.on_make_symref)
        root.addWidget(self.btn_make_symref)

        root.addStretch(1)
        return tab

    # ------------------------------------------------------------------
    # Mirror Deform 탭 (변형량을 미러 평면 건너편으로 반사)
    # ------------------------------------------------------------------

    def _build_mirrordeform_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        root.addWidget(QLabel(
            "Mirror a deformation across the plane (Houdini nearpoint style).\n"
            "Base = original, Deformed = same mesh with one region changed.\n"
            "Both must share topology (same vertex count/order)."))

        # Base (input0)
        base_row = QHBoxLayout()
        self.btn_md_base = QPushButton("Set Base")
        self.btn_md_base.clicked.connect(self.on_md_set_base)
        self.le_md_base = QLineEdit()
        self.le_md_base.setReadOnly(True)
        self.le_md_base.setPlaceholderText("Base (input 0, original)")
        base_row.addWidget(self.btn_md_base)
        base_row.addWidget(self.le_md_base)
        root.addLayout(base_row)

        # Deformed (input1)
        def_row = QHBoxLayout()
        self.btn_md_def = QPushButton("Set Deformed")
        self.btn_md_def.clicked.connect(self.on_md_set_deformed)
        self.le_md_def = QLineEdit()
        self.le_md_def.setReadOnly(True)
        self.le_md_def.setPlaceholderText("Deformed (input 1, edited region)")
        def_row.addWidget(self.btn_md_def)
        def_row.addWidget(self.le_md_def)
        root.addLayout(def_row)

        root.addWidget(self._hline())

        # Mirror axis + 대응 방식
        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Mirror Axis"))
        self.md_axis_group = QButtonGroup(self)
        for idx, label in enumerate(["X", "Y", "Z"]):
            rb = QRadioButton(label)
            self.md_axis_group.addButton(rb, idx)   # 0/1/2 = X/Y/Z
            axis_row.addWidget(rb)
            if idx == 0:
                rb.setChecked(True)
        axis_row.addWidget(QLabel("Match"))
        self.cmb_md_match = QComboBox()
        # 0 = Nearest Vertex(정점 스냅), 1 = Closest Surface(표면 보간, wrap 식)
        self.cmb_md_match.addItems(["Nearest Vertex", "Closest Surface"])
        self.cmb_md_match.setToolTip(
            "Nearest Vertex: mirror partner = nearest base vertex (nearpoint).\n"
            "Closest Surface: closest point on base surface + per-face IDW "
            "interpolation (smooth, wrap/mesh-flow style).")
        axis_row.addWidget(self.cmb_md_match)
        axis_row.addStretch(1)
        root.addLayout(axis_row)

        # Apply onto + Origin
        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("Apply onto"))
        self.cmb_md_onto = QComboBox()
        # 0 = Base(반사만, VEX 그대로), 1 = Deformed(대칭화: 원본 변형 유지 + 반대쪽 반사)
        self.cmb_md_onto.addItems(["Base (reflect)", "Deformed (symmetrize)"])
        self.cmb_md_onto.setToolTip(
            "Base: reflect the deformation onto the opposite side on the base "
            "(VEX behavior).\n"
            "Deformed: keep the original deformation and add the mirrored one "
            "(both sides).")
        opt_row.addWidget(self.cmb_md_onto)
        opt_row.addWidget(QLabel("Origin"))
        self.cmb_md_origin = QComboBox()
        self.cmb_md_origin.addItems(["Object Pivot", "World 0", "BBox Center"])
        opt_row.addWidget(self.cmb_md_origin)
        opt_row.addStretch(1)
        root.addLayout(opt_row)

        self.cb_md_selected = QCheckBox("Selected vertices only")
        self.cb_md_selected.setToolTip(
            "Write the mirrored deformation only into the currently selected "
            "vertices (on Base or Deformed). Other vertices keep their anchor "
            "(base, or deformed when 'Apply onto = Deformed').")
        root.addWidget(self.cb_md_selected)

        self.btn_md_apply = QPushButton("Mirror Deformation")
        self.btn_md_apply.clicked.connect(self.on_mirror_deform)
        root.addWidget(self.btn_md_apply)

        root.addStretch(1)
        return tab

    def _build_menu_bar(self):
        bar = QMenuBar()
        op_menu = bar.addMenu("Operations")
        op_menu.addAction("Copy A to B", lambda: self.on_add_sub_copy(2))
        op_menu.addAction("Add A to B", lambda: self.on_add_sub_copy(1))
        op_menu.addAction("Subtract A from B", lambda: self.on_add_sub_copy(0))
        help_menu = bar.addMenu("Help")
        help_menu.addAction("About", self.show_about)
        return bar

    def _build_axis_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel("Mirror Plane"))
        self.axis_group = QButtonGroup(self)
        for idx, label in enumerate(["YZ", "XZ", "XY"]):
            rb = QRadioButton(label)
            self.axis_group.addButton(rb, idx)   # id 0/1/2 == axis_index
            row.addWidget(rb)
            if idx == 0:
                rb.setChecked(True)
        self.axis_group.buttonClicked.connect(self.on_axis_change)
        row.addStretch(1)
        return row

    def _build_tol_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel("Global Tolerance"))
        self.tol_spin = QDoubleSpinBox()
        self.tol_spin.setRange(0.0, 1.0)
        self.tol_spin.setDecimals(4)
        self.tol_spin.setSingleStep(0.001)
        self.tol_spin.setValue(0.001)
        row.addWidget(self.tol_spin)
        row.addStretch(1)
        return row

    def _hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _dep_button(self, label, callback):
        btn = QPushButton(label)
        btn.clicked.connect(lambda: callback())
        self._dep_widgets.append(btn)
        return btn

    def _set_dep_enabled(self, state):
        for w in self._dep_widgets:
            w.setEnabled(state)

    # ==================================================================
    # 진행률 팝업 (긴 작업용)
    # ==================================================================

    @contextmanager
    def _progress(self, label, total):
        """게이지바 팝업을 띄우고 (i, n) 콜백을 yield 한다.

        - 짧은 작업(<400ms)에서는 팝업이 뜨지 않는다(setMinimumDuration).
        - Cancel 을 누르면 콜백이 _ProgressCancelled 를 던져 코어 루프를 중단한다.
        - 코어 함수에 progress=콜백 으로 넘겨서 쓴다.
        """
        dlg = QProgressDialog(label, "Cancel", 0, max(1, total), self)
        dlg.setWindowTitle("abSymMesh")
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(400)
        dlg.setAutoClose(False)
        dlg.setAutoReset(False)
        dlg.setValue(0)

        def cb(i, n):
            if dlg.maximum() != n:
                dlg.setMaximum(max(1, n))
            dlg.setValue(i)
            QApplication.processEvents()
            if dlg.wasCanceled():
                raise _ProgressCancelled()

        try:
            yield cb
        finally:
            dlg.reset()
            dlg.deleteLater()

    # ==================================================================
    # 로그 / 경고
    # ==================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _warn(self, message):
        cmds.warning(message)
        self._log("[WARN] " + message)

    def _info(self, message):
        self._log(message)

    # ==================================================================
    # 공통 옵션 조회
    # ==================================================================

    def _axis(self):
        return self.axis_group.checkedId()   # 0/1/2 == axis_index

    def _tol(self):
        return self.tol_spin.value()

    def _neg_to_pos(self):
        return self.cb_neg2pos.isChecked()

    def _use_piv(self):
        return self.cb_usepiv.isChecked()

    def _revert_base(self):
        return self.alt_sbg if self.alt_sbg != "" else self.sbg

    # ==================================================================
    # 선택 해석 (origin.mel abSymCtl 의 selection 로직)
    # ==================================================================

    def _resolve_selection(self, allow_multi=False):
        sel = cmds.ls(sl=True, fl=True) or []
        objs = (cmds.filterExpand(sel, sm=12) or []) if sel else []
        sel_mesh = ""
        verts = []

        if len(objs) > 1:
            if not allow_multi:
                self._warn("Select one polygon object")
                return "", [], True
            return "", [], False
        elif len(objs) == 1:
            sel_mesh = objs[0]

        if sel_mesh == "":
            hilite = cmds.ls(hilite=True) or []
            if len(hilite) == 1:
                sel_mesh = hilite[0]
                _m, verts = mesh_io.selected_vertices()
            elif len(hilite) > 1:
                self._warn("Only one object can be hilited in component mode")
                return "", [], True
        else:
            cmds.select(sel_mesh)

        return sel_mesh, verts, False

    # ==================================================================
    # mid 계산 헬퍼
    # ==================================================================

    def _base_mid(self, base, axis):
        if self._use_piv():
            return mesh_io.axis_pivot(base, axis)
        return mesh_io.axis_bbox_mid(base, axis)

    def _obj_mid(self, obj, axis):
        if self._use_piv():
            return mesh_io.axis_pivot(obj, axis)
        return 0.0

    # ==================================================================
    # 슬롯 : Select Base Geometry
    # ==================================================================

    def on_select_base(self):
        sel_mesh, _verts, warned = self._resolve_selection()
        if warned:
            return
        if sel_mesh == "":
            self._clear_base()
            return

        axis = self._axis()
        tol = self._tol()
        mid = self._base_mid(sel_mesh, axis)

        pts = mesh_io.get_points(sel_mesh, world=True)
        self.sym = sym_core.compute_symmetry(pts, axis, tol, mid)
        self.sbg = sel_mesh
        self.alt_sbg = ""

        self.le_base.setText(sel_mesh)
        self._set_dep_enabled(True)

        if self.sym.get("bad_mid"):
            self._warn("'{0}' bounding box / pivot is invalid (NaN). The mesh likely has "
                       "NaN vertices; clean it before building symmetry.".format(sel_mesh))
            return
        invalid = self.sym.get("invalid", 0)
        if invalid:
            self._warn("{0} vertex(es) on '{1}' have invalid (NaN/inf) coordinates and were "
                       "skipped. Clean the mesh for correct symmetry.".format(invalid, sel_mesh))

        if self.sym["symmetrical"]:
            self._info("Base geometry is symmetrical")
        else:
            self._warn("Base geometry is not symmetrical, not all vertices can be mirrored")

    def _clear_base(self):
        self.sym = None
        self.sbg = ""
        self.alt_sbg = ""
        self.le_base.setText("")
        self._set_dep_enabled(False)

    # ==================================================================
    # 슬롯 : Check Symmetry
    # ==================================================================

    def on_check_symmetry(self):
        sel_mesh, _verts, warned = self._resolve_selection()
        if warned or sel_mesh == "":
            return
        axis = self._axis()
        tol = self._tol()
        mid = mesh_io.axis_pivot(sel_mesh, axis) if self._use_piv() else 0.0

        pts = mesh_io.get_points(sel_mesh, world=True)
        res = sym_core.compute_symmetry(pts, axis, tol, mid)
        asym = res["asym"]
        if asym:
            cmds.selectMode(component=True)
            cmds.select(mesh_io.vtx_names(sel_mesh, asym))
            self._info("{0} asymmetric vert(s)".format(len(asym)))
        else:
            cmds.select(sel_mesh)
            self._info("{0} is symmetrical".format(sel_mesh))

    # ==================================================================
    # 슬롯 : Selection Mirror
    # ==================================================================

    def on_selection_mirror(self):
        if not self.sym:
            self._warn("No Base Geometry Selected")
            return
        sel_mesh, verts, warned = self._resolve_selection()
        if warned or not verts:
            return
        midx = sym_core.selection_mirror(self.sym["pair"], verts)
        cmds.select(mesh_io.vtx_names(sel_mesh, midx))

    # ==================================================================
    # 슬롯 : Select Moved Verts
    # ==================================================================

    def on_select_moved(self, use_alt=False):
        sel_mesh, _verts, warned = self._resolve_selection()
        if warned or sel_mesh == "":
            return
        base = self._revert_base() if use_alt else self.sbg
        if base == "":
            self._warn("Select a base mesh first.")
            return
        tol = self._tol()
        obj_pts = mesh_io.get_points(sel_mesh, world=False)
        base_pts = mesh_io.get_points(base, world=False)
        idx = sym_core.moved_vertices(obj_pts, base_pts, tol)
        if idx:
            cmds.selectMode(component=True)
            cmds.select(mesh_io.vtx_names(sel_mesh, idx))
            self._info("{0} moved vert(s)".format(len(idx)))
        else:
            cmds.select(sel_mesh)
            self._info("No moved verts")

    # ==================================================================
    # 슬롯 : Mirror / Flip Selected
    # ==================================================================

    def on_mirror(self):
        self._mirror_or_flip(flip=False)

    def on_flip(self):
        self._mirror_or_flip(flip=True)

    def _mirror_or_flip(self, flip):
        if not self.sym:
            self._warn("No Base Geometry Selected")
            return
        base = self.sbg
        axis = self._axis()
        tol = self._tol()
        neg2pos = self._neg_to_pos()

        base_pts = mesh_io.get_points(base, world=True)
        base_mid = self._base_mid(base, axis)

        with undo_chunk():
            sel = cmds.ls(sl=True, fl=True) or []
            objs = (cmds.filterExpand(sel, sm=12) or []) if sel else []

            if flip and len(objs) > 1:
                for obj in objs:
                    verts = sym_core.side_indices(base_pts, axis, base_mid, neg2pos, tol)
                    self._apply_mirror(obj, base_pts, verts, axis, base_mid, neg2pos, flip, tol)
                return

            sel_mesh, verts, warned = self._resolve_selection(allow_multi=False)
            if warned or sel_mesh == "":
                return
            if not verts:
                verts = sym_core.side_indices(base_pts, axis, base_mid, neg2pos, tol)
            self._apply_mirror(sel_mesh, base_pts, verts, axis, base_mid, neg2pos, flip, tol)

    def _apply_mirror(self, obj, base_pts, verts, axis, base_mid, neg2pos, flip, tol):
        obj_pts = mesh_io.get_points(obj, world=True)
        mid = self._obj_mid(obj, axis)
        new = sym_core.mirror_points(
            obj_pts, base_pts, self.sym["pair"], verts,
            axis, mid, base_mid, neg2pos, flip, tol)
        mesh_io.set_points_undoable(obj, new, world=True)

    # ==================================================================
    # 슬롯 : Revert Selected to Base
    # ==================================================================

    def on_revert(self, bias=1.0):
        sel_mesh, verts, warned = self._resolve_selection()
        if warned or sel_mesh == "":
            return
        base = self._revert_base()
        if base == "":
            self._warn("Select a base mesh first.")
            return
        axis = self._axis()
        tol = self._tol()

        with undo_chunk():
            if not verts:
                base_pts_w = mesh_io.get_points(base, world=True)
                base_mid = self._base_mid(base, axis)
                verts = sym_core.side_indices(base_pts_w, axis, base_mid, 2, tol)

            obj_pts = mesh_io.get_points(sel_mesh, world=False)
            base_pts = mesh_io.get_points(base, world=False)
            new = sym_core.revert_points(obj_pts, base_pts, verts, bias)
            mesh_io.set_points_undoable(sel_mesh, new, world=False)

    # ==================================================================
    # 슬롯 : Revert 슬라이더 (인터랙티브)
    # ==================================================================

    def on_slider_pressed(self):
        self._drag_active = True
        self._build_drag_cache()
        cmds.undoInfo(stateWithoutFlush=False)   # 드래그 중 undo 기록 off

    def on_slider_moved(self, value):
        if not self._drag_active or not self._drag:
            return
        bias = self._slider_to_bias(value)
        pts = sym_core.revert_interactive_points(
            self._drag["full"], self._drag["indices"],
            self._drag["pos_table"], self._drag["base_table"], bias)
        mesh_io.set_points_direct(self._drag["mesh"], pts, world=False)

    def on_slider_released(self):
        if self._drag_active:
            self._drag_active = False
            cmds.undoInfo(stateWithoutFlush=True)   # undo 기록 on

    def _build_drag_cache(self):
        self._drag = None
        verts = cmds.filterExpand(sm=31) or []
        if not verts:
            self._warn("Select vertices on one polygon object.")
            return
        mesh = verts[0].split(".vtx[")[0]
        base = self._revert_base()
        if base == "":
            self._warn("Select a base mesh first.")
            return

        full = mesh_io.get_points(mesh, world=False)
        base_full = mesh_io.get_points(base, world=False)
        tol = 0.001
        indices, pos_table, base_table = [], [], []
        for v in verts:
            i = mesh_io.parse_vtx_index(v)
            o = full[i]
            b = base_full[i]
            if (abs(o[0] - b[0]) > tol or abs(o[1] - b[1]) > tol or abs(o[2] - b[2]) > tol):
                indices.append(i)
                pos_table.append(o)
                base_table.append(b)

        self._drag = {
            "mesh": mesh, "full": full,
            "indices": indices, "pos_table": pos_table, "base_table": base_table,
        }

    # 슬라이더 값 <-> bias 매핑 (overshoot 면 -0.5..1.5)
    def _bias_range(self):
        return (-0.5, 1.5) if self._overshoot else (0.0, 1.0)

    def _slider_to_bias(self, value):
        lo, hi = self._bias_range()
        return lo + (hi - lo) * (value / float(_SLIDER_STEPS))

    def _bias_to_slider(self, bias):
        lo, hi = self._bias_range()
        return int(round((bias - lo) / (hi - lo) * _SLIDER_STEPS))

    # ==================================================================
    # 슬롯 : Operations (Copy / Add / Subtract)
    # ==================================================================

    def on_add_sub_copy(self, operation):
        if self.sbg == "":
            self._warn("You must select a base mesh first.")
            return
        sel = cmds.ls(sl=True) or []
        if len(sel) != 2:
            self._warn("Select two mesh objects (source and target).")
            return

        base_n = mesh_io.vertex_count(self.sbg)
        for mesh in sel:
            if mesh == self.sbg:
                self._warn("The basemesh cannot be used as a source or target. Try revert instead.")
                return
            if cmds.listRelatives(mesh, type="mesh") is None:
                self._warn("{0} is not a mesh. Unable to proceed.".format(mesh))
                return
            if mesh_io.vertex_count(mesh) != base_n:
                self._warn("{0} topology doesn't match the base object. Unable to proceed.".format(mesh))
                return

        with undo_chunk():
            base_pts = mesh_io.get_points(self.sbg, world=False)
            src_pts = mesh_io.get_points(sel[0], world=False)
            tgt_pts = mesh_io.get_points(sel[1], world=False)
            new = sym_core.add_sub_copy_points(base_pts, src_pts, tgt_pts, operation)
            mesh_io.set_points_undoable(sel[1], new, world=False)
            self._info("Operation done on '{0}'.".format(sel[1]))

    # ==================================================================
    # 슬롯 : Alternate base / Axis
    # ==================================================================

    def on_use_alt_base(self, use_alt):
        if use_alt:
            sel = cmds.filterExpand(sm=12) or []
            if len(sel) != 1:
                self._warn("Select a mesh to use as a base object.")
                return
            if self.sbg == "" or mesh_io.vertex_count(sel[0]) != mesh_io.vertex_count(self.sbg):
                self._warn("The new base mesh must have the same number of vertices as the current base mesh.")
                return
            self.alt_sbg = sel[0]
            self._info("Using {0} as revert base.".format(self.alt_sbg))
        else:
            self.alt_sbg = ""
            self._info("Using original base.")

    def on_axis_change(self):
        self._clear_base()
        letter = _AXIS_LETTER[self._axis()]
        self.cb_neg2pos.setText("Operate -{0} to +{0}".format(letter))

    # ==================================================================
    # 컨텍스트 메뉴 (revert % / base 옵션)
    # ==================================================================

    def _show_revert_menu(self, pos):
        menu = QMenu(self)
        for v in _REVERT_PCTS:
            if v is None:
                menu.addSeparator()
                continue
            frac = v / 100.0
            menu.addAction("{0}%".format(v), lambda f=frac: self.on_revert(f))
        menu.exec_(self.btn_revert.mapToGlobal(pos))

    def _show_base_menu(self, pos):
        menu = QMenu(self)
        cur = "Using {0} as Base".format(self.alt_sbg) if self.alt_sbg else "Using Original Base"
        head = menu.addAction(cur)
        head.setEnabled(False)
        menu.addSeparator()
        menu.addAction("Use Selected as Base", lambda: self.on_use_alt_base(True))
        act_orig = menu.addAction("Use Original Base", lambda: self.on_use_alt_base(False))
        act_orig.setEnabled(self.alt_sbg != "")
        act_moved = menu.addAction("Select Moved from Revert Base", lambda: self.on_select_moved(True))
        act_moved.setEnabled(self.alt_sbg != "")
        menu.addSeparator()
        act_over = menu.addAction("Use Overshoot")
        act_over.setCheckable(True)
        act_over.setChecked(self._overshoot)
        act_over.triggered.connect(self._toggle_overshoot)
        menu.exec_(self.slider.mapToGlobal(pos))

    def _toggle_overshoot(self, checked):
        # bias 가 유지되도록 현재 슬라이더 값을 bias 로 환산한 뒤 범위 변경.
        bias = self._slider_to_bias(self.slider.value())
        self._overshoot = checked
        self.slider.setValue(self._bias_to_slider(bias))

    # ==================================================================
    # 슬롯 : Snap to Sym 탭
    # ==================================================================

    def _selected_single_mesh(self):
        """현재 선택에서 단일 폴리곤 메시명을 반환(아니면 "" + 경고)."""
        sel = cmds.filterExpand(sm=12) or []
        if len(sel) != 1:
            self._warn("Select exactly one polygon mesh.")
            return ""
        return sel[0]

    def _is_mesh(self, name):
        return bool(name) and cmds.objExists(name) and \
            cmds.listRelatives(name, type="mesh") is not None

    def on_snap_set_source(self):
        mesh = self._selected_single_mesh()
        if mesh:
            self.le_snap_src.setText(mesh)

    def on_snap_set_reference(self):
        mesh = self._selected_single_mesh()
        if mesh:
            self.le_snap_ref.setText(mesh)

    def _snap_selected_indices(self, src):
        """'Selected vertices only' 체크 시, src 의 선택 정점 인덱스(없으면 None=전체)."""
        if not self.cb_snap_selected.isChecked():
            return None
        mesh, indices = mesh_io.selected_vertices()
        if not indices:
            self._warn("No vertices selected. Select source vertices or "
                       "uncheck 'Selected vertices only'.")
            return False
        return indices

    def on_snap_apply(self):
        src = self.le_snap_src.text().strip()
        ref = self.le_snap_ref.text().strip()
        if not self._is_mesh(src):
            self._warn("Source is not a valid mesh. Press 'Set Source'.")
            return
        if not self._is_mesh(ref):
            self._warn("Reference is not a valid mesh. Press 'Set Reference'.")
            return
        if src == ref:
            self._warn("Source and Reference must be different meshes.")
            return

        indices = self._snap_selected_indices(src)
        if indices is False:
            return

        nearest_vertex = self.snap_mode_group.checkedId() == 0

        try:
            with undo_chunk(), self._progress(
                    "Snap to Reference", mesh_io.vertex_count(src)) as prog:
                src_pts = mesh_io.get_points(src, world=True)

                bad = snap_core.count_invalid(src_pts)
                if bad:
                    self._warn("'{0}' has {1} NaN/inf vertex(es); they are left "
                               "unchanged. Clean the mesh (Mesh > Cleanup)."
                               .format(src, bad))

                # 다른 메시의 정점이 선택돼 있어도 범위를 벗어난 인덱스는 버린다.
                if indices is not None:
                    indices = [i for i in indices if 0 <= i < len(src_pts)]
                    if not indices:
                        self._warn("Selected vertices are not on the Source mesh.")
                        return

                if nearest_vertex:
                    ref_pts = mesh_io.get_points(ref, world=True)
                    new, moved = snap_core.snap_to_nearest_vertex(
                        src_pts, ref_pts, indices, progress=prog)
                else:
                    idx = range(len(src_pts)) if indices is None else indices
                    idx = list(idx)
                    query = [src_pts[i] for i in idx]
                    closest = mesh_io.closest_surface_points(
                        ref, query, world=True, progress=prog)
                    new = [tuple(p) for p in src_pts]
                    for k, i in enumerate(idx):
                        new[i] = closest[k]
                    moved = len(idx)

                mesh_io.set_points_undoable(src, new, world=True)
        except _ProgressCancelled:
            self._info("Snap cancelled.")
            return

        mode = "nearest vertex" if nearest_vertex else "closest surface"
        self._info("Snapped {0} vert(s) of '{1}' to '{2}' ({3}).".format(
            moved, src, ref, mode))

    def _sym_origin_mid(self, mesh, axis):
        """Origin 콤보 선택대로 대칭 평면 원점(축 성분값)을 계산한다."""
        choice = self.cmb_sym_origin.currentIndex()
        if choice == 1:       # World 0
            return 0.0
        if choice == 2:       # BBox Center
            return mesh_io.axis_bbox_mid(mesh, axis)
        return mesh_io.axis_pivot(mesh, axis)   # 0 = Object Pivot

    def on_make_symref(self):
        src = self.le_snap_src.text().strip()
        if not self._is_mesh(src):
            src = self._selected_single_mesh()
            if not self._is_mesh(src):
                self._warn("Set a valid Source mesh first.")
                return

        axis = self.snap_axis_group.checkedId()
        method_idx = self.cmb_sym_method.currentIndex()   # 0 mirror, 1 avg, 2 geometry
        positive_source = self.cmb_sym_side.currentIndex() == 0   # "+ to -"
        name = "{0}_symRef".format(src.split("|")[-1].split(":")[-1])

        # 원점(mid)을 먼저 구해 검증한다. NaN 정점이 있는 메시는 bbox/pivot 이
        # NaN 이 될 수 있고, 그러면 전 정점이 깨지므로 시작 전에 막는다.
        mid = self._sym_origin_mid(src, axis)
        if not math.isfinite(mid):
            self._warn("Symmetry origin is invalid (NaN/inf) for '{0}'. The mesh "
                       "likely has broken vertices; clean it (Mesh > Cleanup) or "
                       "use Origin = World 0.".format(src))
            return

        # 모드 2: 반 잘라 미러(지오메트리 재생성).
        if method_idx == 2:
            seam = self.spin_seam_tol.value()
            try:
                with undo_chunk():
                    dup = cmds.duplicate(src, name=name)[0]
                    result = mesh_ops.mirror_geometry(
                        dup, axis, mid, positive_source, seam, seam)
                    result = cmds.rename(result, name)
            except Exception as exc:
                self._warn("Mirror geometry failed: {0}".format(exc))
                return
            self.le_snap_ref.setText(result)
            cmds.select(result)
            self._info("Created symmetric reference '{0}' (geometry mirror "
                       "{1}, axis {2}).".format(
                           result, "+to-" if positive_source else "-to+",
                           _AXIS_LETTER[axis]))
            return

        # 모드 0/1: 정점 위치 기반(토폴로지 유지).
        # 무거운 계산을 먼저 끝내고(취소 가능) 마지막에 복제+적용한다.
        # (복제를 먼저 만들면 계산 중 Cancel 시 변형 안 된 복제본이 씬에 남는다.)
        try:
            with undo_chunk(), self._progress(
                    "Make Symmetric Reference",
                    mesh_io.vertex_count(src)) as prog:
                pts = mesh_io.get_points(src, world=True)

                bad = snap_core.count_invalid(pts)
                if bad:
                    self._warn("'{0}' has {1} NaN/inf vertex(es); they are left "
                               "unchanged. Clean the mesh (Mesh > Cleanup)."
                               .format(src, bad))

                if method_idx == 0:
                    new = snap_core.mirror_one_side_points(
                        pts, axis, mid, positive_source, progress=prog)
                else:
                    new = snap_core.make_symmetric_points(
                        pts, axis, mid, progress=prog)

                dup = cmds.duplicate(src, name=name)[0]
                mesh_io.set_points_undoable(dup, new, world=True)
        except _ProgressCancelled:
            self._info("Make Symmetric Reference cancelled.")
            return

        self.le_snap_ref.setText(dup)
        cmds.select(dup)
        method = ("mirror {0}".format("+to-" if positive_source else "-to+")
                  if method_idx == 0 else "average")
        self._info("Created symmetric reference '{0}' (axis {1}, {2}).".format(
            dup, _AXIS_LETTER[axis], method))

    # ==================================================================
    # 슬롯 : Mirror Deform 탭
    # ==================================================================

    def on_md_set_base(self):
        mesh = self._selected_single_mesh()
        if mesh:
            self.le_md_base.setText(mesh)

    def on_md_set_deformed(self):
        mesh = self._selected_single_mesh()
        if mesh:
            self.le_md_def.setText(mesh)

    def _md_selected_indices(self):
        """'Selected vertices only' 체크 시, 선택 정점 인덱스(없으면 None=전체)."""
        if not self.cb_md_selected.isChecked():
            return None
        _mesh, indices = mesh_io.selected_vertices()
        if not indices:
            self._warn("No vertices selected. Select vertices (on Base or "
                       "Deformed) or uncheck 'Selected vertices only'.")
            return False
        return indices

    def _md_origin_mid(self, mesh, axis):
        choice = self.cmb_md_origin.currentIndex()
        if choice == 1:       # World 0
            return 0.0
        if choice == 2:       # BBox Center
            return mesh_io.axis_bbox_mid(mesh, axis)
        return mesh_io.axis_pivot(mesh, axis)   # 0 = Object Pivot

    def on_mirror_deform(self):
        base = self.le_md_base.text().strip()
        deformed = self.le_md_def.text().strip()
        if not self._is_mesh(base):
            self._warn("Base is not a valid mesh. Press 'Set Base'.")
            return
        if not self._is_mesh(deformed):
            self._warn("Deformed is not a valid mesh. Press 'Set Deformed'.")
            return
        if mesh_io.vertex_count(base) != mesh_io.vertex_count(deformed):
            self._warn("Base and Deformed must share topology (vertex count "
                       "differs). Deformed must be an edited copy of Base.")
            return

        axis = self.md_axis_group.checkedId()
        onto_deformed = self.cmb_md_onto.currentIndex() == 1
        surface_match = self.cmb_md_match.currentIndex() == 1

        mid = self._md_origin_mid(base, axis)
        if not math.isfinite(mid):
            self._warn("Mirror origin is invalid (NaN/inf). Clean the mesh or "
                       "use Origin = World 0.")
            return

        name = "{0}_mirrorDef".format(
            base.split("|")[-1].split(":")[-1])
        n = mesh_io.vertex_count(base)

        indices = self._md_selected_indices()
        if indices is False:
            return
        if indices is not None:
            # 다른 메시의 정점이 선택돼 있어도 범위를 벗어난 인덱스는 버린다.
            indices = [i for i in indices if 0 <= i < n]
            if not indices:
                self._warn("Selected vertices are not on the Base/Deformed mesh.")
                return

        try:
            with undo_chunk(), self._progress("Mirror Deformation", n) as prog:
                base_pts = mesh_io.get_points(base, world=True)
                def_pts = mesh_io.get_points(deformed, world=True)

                if surface_match:
                    # 표면 최근접점 + 면 정점 IDW 보간(wrap/mesh-flow 식).
                    offsets = [(d[0] - b[0], d[1] - b[1], d[2] - b[2])
                               for b, d in zip(base_pts, def_pts)]
                    mirror_pos = [snap_core.reflect(b, axis, mid)
                                  for b in base_pts]
                    interp = mesh_io.closest_surface_offsets(
                        base, mirror_pos, offsets, world=True,
                        indices=indices, progress=prog)
                    new = snap_core.apply_mirrored_offsets(
                        base_pts, def_pts, interp, axis, onto_deformed,
                        indices=indices)
                else:
                    # 최근접 정점(nearpoint).
                    new = snap_core.mirror_deformation(
                        base_pts, def_pts, axis, mid, onto_deformed,
                        indices=indices, progress=prog)

                # 결과는 base 토폴로지의 새 메시로 출력(원본 둘 다 보존).
                dup = cmds.duplicate(base, name=name)[0]
                mesh_io.set_points_undoable(dup, new, world=True)
        except _ProgressCancelled:
            self._info("Mirror Deformation cancelled.")
            return

        self.le_snap_ref.setText(dup)   # 바로 스냅 레퍼런스로 쓸 수 있게 연계.
        cmds.select(dup)
        scope = ("{0} selected vert(s)".format(len(indices))
                 if indices is not None else "all verts")
        self._info(
            "Mirrored deformation -> '{0}' (axis {1}, {2}, onto {3}, {4}).".format(
                dup, _AXIS_LETTER[axis],
                "surface" if surface_match else "vertex",
                "deformed" if onto_deformed else "base", scope))

    # ==================================================================
    # Help
    # ==================================================================

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "abSymMesh v{0}  (PySide / OpenMaya 2.0)\n"
            "Update date: {1}\n\n"
            "Build symmetrical / asymmetrical blendshapes:\n"
            "check symmetry, mirror, flip and revert polygon geometry.\n\n"
            "Select a symmetrical mesh and press 'Select Base Geometry' first,\n"
            "then operate on duplicates with the same vertex order.\n\n"
            "Re-implementation of Brendan Ross's abSymMesh. Written by Ji Hun Park.".format(
                VERSION, LAST_UPDATE))
