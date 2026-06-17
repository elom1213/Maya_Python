# -*- coding: utf-8 -*-
"""
abSymMesh - PySide(Qt) UI.

기존 maya.cmds UI(abSymMesh_v01.py)를 PySide 로 재작업한 버전.
로직(app/core: mesh_io / sym_core / undo_*)은 그대로 재사용하고 화면만 Qt 로 바꾼다.
Framework.qt.qt 가 PySide6 -> PySide2 폴백을 처리하므로 Maya 2023(PySide2)~최신 호환.

UI 문자열/로그는 영어. 씬 선택/Undo 청크는 maya.cmds, 정점 I/O 는 app.core 가 담당.
"""

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window

from ..config.version import VERSION, LAST_UPDATE
from ..core import mesh_io
from ..core import sym_core


WINDOW_OBJECT_NAME = "JUN_A00180_abSymMesh_window"

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
        self.resize(260, 560)

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

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        root.addWidget(btn_close)

        # 로그
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(90)
        root.addWidget(self.log_view)

        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

        self._set_dep_enabled(False)

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

        cmds.undoInfo(openChunk=True)
        try:
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
        finally:
            cmds.undoInfo(closeChunk=True)

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

        cmds.undoInfo(openChunk=True)
        try:
            if not verts:
                base_pts_w = mesh_io.get_points(base, world=True)
                base_mid = self._base_mid(base, axis)
                verts = sym_core.side_indices(base_pts_w, axis, base_mid, 2, tol)

            obj_pts = mesh_io.get_points(sel_mesh, world=False)
            base_pts = mesh_io.get_points(base, world=False)
            new = sym_core.revert_points(obj_pts, base_pts, verts, bias)
            mesh_io.set_points_undoable(sel_mesh, new, world=False)
        finally:
            cmds.undoInfo(closeChunk=True)

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

        cmds.undoInfo(openChunk=True)
        try:
            base_pts = mesh_io.get_points(self.sbg, world=False)
            src_pts = mesh_io.get_points(sel[0], world=False)
            tgt_pts = mesh_io.get_points(sel[1], world=False)
            new = sym_core.add_sub_copy_points(base_pts, src_pts, tgt_pts, operation)
            mesh_io.set_points_undoable(sel[1], new, world=False)
            self._info("Operation done on '{0}'.".format(sel[1]))
        finally:
            cmds.undoInfo(closeChunk=True)

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
