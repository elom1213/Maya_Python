# last Update date : 15-JUN-2026
# Python Script by Ji Hun Park
#
# abSymMesh v01.00  (Python / OpenMaya 2.0 re-implementation)
# origin.mel (abSymMesh 1.7, Brendan Ross) 의 동작을 보존하면서 속도를 개선한 포팅.
#   - 정점 입출력을 MFnMesh.getPoints/setPoints 로 벌크화 (per-vtx xform 제거)
#   - 대칭 테이블을 공간 해시 O(N) + dict O(1) 조회로 (O(N^2)/선형탐색 제거)
#   - 정점 편집은 Undo 가능 커맨드(abSymSetPoints) 경유
# UI 문자열/로그는 영어, 주석은 한국어.

import maya.cmds as cmds

from Framework.ui import JUN_mod_colorThem
from .core import mesh_io
from .core import sym_core


class JUN_ToolUI_abSymMesh:

    WIN = "Junny_win_abSymMesh_v01"

    def __init__(self):
        self.str_headTitle = "abSymMesh V01.00"
        self.updated = "15-JUN-2026"

        # 상태(원본 전역 대체)
        self.sbg = ""          # base geometry (symmetry table 의 기준 메시)
        self.alt_sbg = ""      # alternate base (revert 기준 대체)
        self.sym = None        # compute_symmetry 결과 dict {pair, zero, asym, symmetrical}

        # revert 슬라이더 드래그 캐시
        self._drag_active = False
        self._drag = None      # {mesh, full, indices, pos_table, base_table}

        # color theme
        colorThem__ = JUN_mod_colorThem.ColorThemeRegistry.get("coral_01")
        self.color_mainDark = colorThem__.get("color_mainDark")
        self.color_btn = colorThem__.get("color_btn")

        # 베이스 의존 버튼 컨트롤 이름
        self._dep_buttons = []

    # ==================================================================
    # 공통 옵션 조회
    # ==================================================================

    def _axis(self):
        # radio 1/2/3 -> axis_index 0/1/2 (YZ->X, XZ->Y, XY->Z)
        return cmds.radioButtonGrp(self.rb_axis, q=True, select=True) - 1

    def _tol(self):
        return cmds.floatField(self.ff_tol, q=True, value=True)

    def _neg_to_pos(self):
        return cmds.checkBox(self.cb_neg2pos, q=True, value=True)

    def _use_piv(self):
        return cmds.checkBox(self.cb_usePiv, q=True, value=True)

    def _revert_base(self):
        return self.alt_sbg if self.alt_sbg != "" else self.sbg

    # ==================================================================
    # 선택 해석 (origin.mel abSymCtl 의 selection 로직)
    # ==================================================================

    def _resolve_selection(self, allow_multi=False):
        """반환: (sel_mesh, sel_vert_indices, warned).

        - 오브젝트 1개 선택 -> sel_mesh, 컴포넌트 없음
        - 오브젝트 여러 개 -> allow_multi 아니면 경고
        - 컴포넌트(정점) 선택 -> hilite 메시 + 정점 인덱스
        """
        sel = cmds.ls(sl=True, fl=True) or []
        objs = (cmds.filterExpand(sel, sm=12) or []) if sel else []
        sel_mesh = ""
        verts = []

        if len(objs) > 1:
            if not allow_multi:
                cmds.warning("Select one polygon object")
                return "", [], True
            return "", [], False  # 멀티 오브젝트는 호출측에서 sel 로 처리
        elif len(objs) == 1:
            sel_mesh = objs[0]

        if sel_mesh == "":
            hilite = cmds.ls(hilite=True) or []
            if len(hilite) == 1:
                sel_mesh = hilite[0]
                _m, verts = mesh_io.selected_vertices()
            elif len(hilite) > 1:
                cmds.warning("Only one object can be hilited in component mode")
                return "", [], True
        else:
            cmds.select(sel_mesh)  # 오브젝트로 축소

        return sel_mesh, verts, False

    # ==================================================================
    # mid 계산 헬퍼
    # ==================================================================

    def _base_mid(self, base, axis):
        if self._use_piv():
            return mesh_io.axis_pivot(base, axis)
        return mesh_io.axis_bbox_mid(base, axis)

    def _obj_mid(self, obj, axis):
        # 미러/플립 시 대상 메시의 대칭 평면(비-pivot 이면 월드 원점 0)
        if self._use_piv():
            return mesh_io.axis_pivot(obj, axis)
        return 0.0

    # ==================================================================
    # 슬롯 : Select Base Geometry
    # ==================================================================

    def on_select_base(self, *args):
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

        cmds.textField(self.tf_base, e=True, text=sel_mesh)
        self._set_dep_enabled(True)

        # NaN/inf 좌표 정점 경고(원본은 조용히 비대칭 처리 -> 여기선 명시 경고).
        if self.sym.get("bad_mid"):
            cmds.warning("'{0}' bounding box / pivot is invalid (NaN). "
                         "The mesh likely has NaN vertices; clean it (e.g. Mesh > Cleanup) "
                         "before building symmetry.".format(sel_mesh))
            return
        invalid = self.sym.get("invalid", 0)
        if invalid:
            cmds.warning("{0} vertex(es) on '{1}' have invalid (NaN/inf) coordinates and "
                         "were skipped. Clean the mesh for correct symmetry.".format(invalid, sel_mesh))

        if self.sym["symmetrical"]:
            print("Base geometry is symmetrical")
        else:
            cmds.warning("Base geometry is not symmetrical, not all vertices can be mirrored")

    def _clear_base(self):
        self.sym = None
        self.sbg = ""
        self.alt_sbg = ""
        cmds.textField(self.tf_base, e=True, text="")
        self._set_dep_enabled(False)

    def _set_dep_enabled(self, state):
        for b in self._dep_buttons:
            cmds.button(b, e=True, enable=state)

    # ==================================================================
    # 슬롯 : Check Symmetry
    # ==================================================================

    def on_check_symmetry(self, *args):
        sel_mesh, _verts, warned = self._resolve_selection()
        if warned or sel_mesh == "":
            return
        axis = self._axis()
        tol = self._tol()
        # 원본: usePiv 면 pivot, 아니면 0(원점 기준 대칭 측정)
        mid = mesh_io.axis_pivot(sel_mesh, axis) if self._use_piv() else 0.0

        pts = mesh_io.get_points(sel_mesh, world=True)
        res = sym_core.compute_symmetry(pts, axis, tol, mid)
        asym = res["asym"]
        if asym:
            cmds.selectMode(component=True)
            cmds.select(mesh_io.vtx_names(sel_mesh, asym))
            print("{0} asymmetric vert(s)".format(len(asym)))
        else:
            cmds.select(sel_mesh)
            print("{0} is symmetrical".format(sel_mesh))

    # ==================================================================
    # 슬롯 : Selection Mirror
    # ==================================================================

    def on_selection_mirror(self, *args):
        if not self.sym:
            cmds.warning("No Base Geometry Selected")
            return
        sel_mesh, verts, warned = self._resolve_selection()
        if warned or not verts:
            return
        midx = sym_core.selection_mirror(self.sym["pair"], verts)
        cmds.select(mesh_io.vtx_names(sel_mesh, midx))

    # ==================================================================
    # 슬롯 : Select Moved Verts
    # ==================================================================

    def on_select_moved(self, use_alt=False, *args):
        sel_mesh, _verts, warned = self._resolve_selection()
        if warned or sel_mesh == "":
            return
        base = self._revert_base() if use_alt else self.sbg
        if base == "":
            cmds.warning("Select a base mesh first.")
            return
        tol = self._tol()
        obj_pts = mesh_io.get_points(sel_mesh, world=False)
        base_pts = mesh_io.get_points(base, world=False)
        idx = sym_core.moved_vertices(obj_pts, base_pts, tol)
        if idx:
            cmds.selectMode(component=True)
            cmds.select(mesh_io.vtx_names(sel_mesh, idx))
            print("{0} moved vert(s)".format(len(idx)))
        else:
            cmds.select(sel_mesh)
            print("No moved verts")

    # ==================================================================
    # 슬롯 : Mirror / Flip Selected
    # ==================================================================

    def on_mirror(self, *args):
        self._mirror_or_flip(flip=False)

    def on_flip(self, *args):
        self._mirror_or_flip(flip=True)

    def _mirror_or_flip(self, flip):
        if not self.sym:
            cmds.warning("No Base Geometry Selected")
            return
        base = self.sbg
        axis = self._axis()
        tol = self._tol()
        neg2pos = self._neg_to_pos()

        # base 위치는 분류용으로 한 번만 읽는다.
        base_pts = mesh_io.get_points(base, world=True)
        base_mid = self._base_mid(base, axis)

        cmds.undoInfo(openChunk=True)
        try:
            sel = cmds.ls(sl=True, fl=True) or []
            objs = (cmds.filterExpand(sel, sm=12) or []) if sel else []

            if flip and len(objs) > 1:
                # 플립은 여러 오브젝트 처리 가능(원본과 동일)
                for obj in objs:
                    verts = sym_core.side_indices(base_pts, axis, base_mid, neg2pos, tol)
                    self._apply_mirror(obj, base_pts, verts, axis, base_mid, neg2pos, flip, tol)
                return

            sel_mesh, verts, warned = self._resolve_selection(allow_multi=False)
            if warned or sel_mesh == "":
                return
            if not verts:
                # 오브젝트 선택 -> 한쪽 면 정점을 소스로
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

    def on_revert(self, bias=1.0, *args):
        sel_mesh, verts, warned = self._resolve_selection()
        if warned or sel_mesh == "":
            return
        base = self._revert_base()
        if base == "":
            cmds.warning("Select a base mesh first.")
            return
        axis = self._axis()
        tol = self._tol()

        cmds.undoInfo(openChunk=True)
        try:
            if not verts:
                # 오브젝트 선택 -> 전체 정점
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

    def on_slider_drag(self, *args):
        if not self._drag_active:
            self._drag_active = True
            self._build_drag_cache()
            cmds.undoInfo(stateWithoutFlush=False)  # 드래그 중 undo 기록 off

        if not self._drag:
            return
        bias = cmds.floatSlider(self.sl_revert, q=True, value=True)
        pts = sym_core.revert_interactive_points(
            self._drag["full"], self._drag["indices"],
            self._drag["pos_table"], self._drag["base_table"], bias)
        mesh_io.set_points_direct(self._drag["mesh"], pts, world=False)

    def on_slider_change(self, *args):
        # 드래그 종료
        if self._drag_active:
            self._drag_active = False
            cmds.undoInfo(stateWithoutFlush=True)  # undo 기록 on

    def _build_drag_cache(self):
        self._drag = None
        verts = cmds.filterExpand(sm=31) or []
        if not verts:
            cmds.warning("Select vertices on one polygon object.")
            return
        mesh = verts[0].split(".vtx[")[0]
        base = self._revert_base()
        if base == "":
            cmds.warning("Select a base mesh first.")
            return

        full = mesh_io.get_points(mesh, world=False)
        base_full = mesh_io.get_points(base, world=False)
        tol = 0.001
        indices = []
        pos_table = []
        base_table = []
        for v in verts:
            i = mesh_io.parse_vtx_index(v)
            o = full[i]
            b = base_full[i]
            if (abs(o[0] - b[0]) > tol or abs(o[1] - b[1]) > tol or abs(o[2] - b[2]) > tol):
                indices.append(i)
                pos_table.append(o)
                base_table.append(b)

        self._drag = {
            "mesh": mesh,
            "full": full,
            "indices": indices,
            "pos_table": pos_table,
            "base_table": base_table,
        }

    # ==================================================================
    # 슬롯 : Operations (Copy / Add / Subtract)
    # ==================================================================

    def on_add_sub_copy(self, operation, *args):
        if self.sbg == "":
            cmds.warning("You must select a base mesh first.")
            return
        sel = cmds.ls(sl=True) or []
        if len(sel) != 2:
            cmds.warning("Select two mesh objects (source and target).")
            return

        base_n = mesh_io.vertex_count(self.sbg)
        for mesh in sel:
            if mesh == self.sbg:
                cmds.warning("The basemesh cannot be used as a source or target. Try using revert instead.")
                return
            if cmds.listRelatives(mesh, type="mesh") is None:
                cmds.warning("{0} is not a mesh. Unable to proceed.".format(mesh))
                return
            if mesh_io.vertex_count(mesh) != base_n:
                cmds.warning("{0} topology doesn't match the base object. Unable to proceed.".format(mesh))
                return

        cmds.undoInfo(openChunk=True)
        try:
            base_pts = mesh_io.get_points(self.sbg, world=False)
            src_pts = mesh_io.get_points(sel[0], world=False)
            tgt_pts = mesh_io.get_points(sel[1], world=False)
            new = sym_core.add_sub_copy_points(base_pts, src_pts, tgt_pts, operation)
            mesh_io.set_points_undoable(sel[1], new, world=False)
        finally:
            cmds.undoInfo(closeChunk=True)

    # ==================================================================
    # 슬롯 : Alternate base / Axis / Close
    # ==================================================================

    def on_use_alt_base(self, use_alt, *args):
        if use_alt:
            sel = cmds.filterExpand(sm=12) or []
            if len(sel) != 1:
                cmds.warning("Select a mesh to use as a base object.")
                return
            if self.sbg == "" or mesh_io.vertex_count(sel[0]) != mesh_io.vertex_count(self.sbg):
                cmds.warning("The new base mesh must have the same number of vertices as the current base mesh.")
                return
            self.alt_sbg = sel[0]
            cmds.menuItem(self.mi_curbase, e=True, label="Using {0} as Base".format(self.alt_sbg))
            cmds.menuItem(self.mi_origbase, e=True, enable=True)
            cmds.menuItem(self.mi_altmoved, e=True, enable=True)
        else:
            self.alt_sbg = ""
            cmds.menuItem(self.mi_curbase, e=True, label="Using Original Base")
            cmds.menuItem(self.mi_origbase, e=True, enable=False)
            cmds.menuItem(self.mi_altmoved, e=True, enable=False)

    def on_axis_change(self, *args):
        self._clear_base()
        axis = self._axis()
        letter = ["X", "Y", "Z"][axis]
        cmds.checkBox(self.cb_neg2pos, e=True, label="Operate -{0} to +{0}".format(letter))

    def on_close(self, *args):
        if cmds.window(self.WIN, exists=True):
            cmds.deleteUI(self.WIN, window=True)

    # ==================================================================
    # Help
    # ==================================================================

    def show_about(self, *args):
        cmds.confirmDialog(
            title="About",
            icon="information",
            button="OK",
            messageAlign="center",
            message=(
                "abSymMesh V01.00 (Python / OpenMaya 2.0)\n"
                "Update date: {0}\n\n"
                "Build symmetrical / asymmetrical blendshapes:\n"
                "check symmetry, mirror, flip and revert polygon geometry.\n\n"
                "Select a symmetrical mesh and press 'Select Base Geometry' first,\n"
                "then operate on duplicates with the same vertex order.\n\n"
                "Re-implementation of Brendan Ross's abSymMesh. "
                "Written by Ji Hun Park."
            ).format(self.updated)
        )

    # ==================================================================
    # UI build
    # ==================================================================

    def build(self):
        if cmds.window(self.WIN, exists=True):
            cmds.deleteUI(self.WIN, window=True)

        cmds.window(self.WIN, title=self.str_headTitle, menuBar=True,
                    bgc=self.color_mainDark, widthHeight=(220, 470))

        # Operations 메뉴
        cmds.menu(label="Operations")
        cmds.menuItem(label="Copy A to B", command=lambda *a: self.on_add_sub_copy(2))
        cmds.menuItem(label="Add A to B", command=lambda *a: self.on_add_sub_copy(1))
        cmds.menuItem(label="Subtract A from B", command=lambda *a: self.on_add_sub_copy(0))

        cmds.menu(label="Help")
        cmds.menuItem(label="About", command=self.show_about)

        cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5),
                          rowSpacing=5, bgc=self.color_mainDark)

        self.rb_axis = cmds.radioButtonGrp(
            numberOfRadioButtons=3, label1="YZ", label2="XZ", label3="XY",
            select=1, columnWidth3=(60, 60, 60),
            onCommand=lambda *a: self.on_axis_change())

        cmds.separator(style="in")

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(120, 80), adjustableColumn=2)
        cmds.text(label="Global Tolerance", align="left")
        self.ff_tol = cmds.floatField(minValue=0, maxValue=1, value=0.001)
        cmds.setParent("..")

        cmds.separator(style="in")

        self._mk_button("Select Base Geometry", self.on_select_base, dep=False)
        self.tf_base = cmds.textField(editable=False, text=self.sbg)

        cmds.separator(style="in")

        self._mk_button("Check Symmetry", self.on_check_symmetry, dep=False)
        self.btn_selmirror = self._mk_button("Selection Mirror", self.on_selection_mirror, dep=True)
        self.btn_selmoved = self._mk_button("Select Moved Verts", self.on_select_moved, dep=True)

        cmds.separator(style="in")

        self.btn_mirror = self._mk_button("Mirror Selected", self.on_mirror, dep=True)
        self.btn_flip = self._mk_button("Flip Selected", self.on_flip, dep=True)
        self.btn_revert = self._mk_button("Revert Selected to Base", self.on_revert, dep=True)

        self.sl_revert = cmds.floatSlider(
            value=1, minValue=0, maxValue=1,
            dragCommand=lambda *a: self.on_slider_drag(),
            changeCommand=lambda *a: self.on_slider_change())

        # revert 버튼 우클릭 % 팝업
        self._build_revert_popup()
        # base 메뉴 팝업(슬라이더에 부착)
        self._build_base_popup()

        cmds.separator(style="in")

        self.cb_neg2pos = cmds.checkBox(label="Operate -X to +X", value=False)
        self.cb_usePiv = cmds.checkBox(label="Use Pivot as Origin", value=True)

        self._mk_button("Close", self.on_close, dep=False, height=24)

        cmds.text(align="center", label="Copyright (c) Park Ji Hun. All rights reserved.")

        cmds.showWindow(self.WIN)

        # 시작 시 베이스가 없으면 의존 버튼 비활성
        self._set_dep_enabled(self.sbg != "" and self.sym is not None)

    def _mk_button(self, label, callback, dep=False, height=30):
        btn = cmds.button(label=label, height=height, bgc=self.color_btn,
                          command=lambda *a: callback())
        if dep:
            self._dep_buttons.append(btn)
        return btn

    def _build_revert_popup(self):
        pm = cmds.popupMenu(button=3, parent=self.btn_revert)
        vals = [1, 2, 3, 4, 5, None, 10, 20, 30, 40, 50, 60, 70, 80, 90]
        for v in vals:
            if v is None:
                cmds.menuItem(divider=True)
                continue
            frac = v / 100.0
            cmds.menuItem(parent=pm, label="{0}%".format(v),
                          command=lambda a=False, f=frac: self.on_revert(f))

    def _build_base_popup(self):
        pm = cmds.popupMenu(button=3, parent=self.sl_revert)
        self.mi_curbase = cmds.menuItem(parent=pm, label="Using Original Base", enable=False)
        cmds.menuItem(parent=pm, divider=True)
        cmds.menuItem(parent=pm, label="Use Selected as Base",
                      command=lambda *a: self.on_use_alt_base(True))
        self.mi_origbase = cmds.menuItem(parent=pm, label="Use Original Base", enable=False,
                                         command=lambda *a: self.on_use_alt_base(False))
        self.mi_altmoved = cmds.menuItem(parent=pm, label="Select Moved from Revert Base",
                                         enable=False, command=lambda *a: self.on_select_moved(True))
        cmds.menuItem(parent=pm, label="Commit Changes",
                      command=lambda *a: None)


def abSymMesh__():
    ui = JUN_ToolUI_abSymMesh()
    ui.build()


# Do not rename build__ function (launcher 가 호출)
def build__():
    abSymMesh__()
