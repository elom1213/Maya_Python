# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00380_MeshTool - Quad Patch 탭 (v01.21)
#
# 구멍을 쿼드 그리드로 메운다. 로직은 app/core/quad_patch.py.
#
# 흐름: 선택 -> Start 버튼(Edge Border / Faces / Extrude) -> 슬라이더로 모양 조절(초록 와이어 미리보기)
#       -> Patch It (원본 메시에 면을 붙인다, Ctrl+Z 한 번) / Cancel (미리보기만 지운다).
# 미리보기는 undo 큐에 남지 않는다. 설정(Relax · Inset · Smooth · 옵션)은 optionVar 로 기억한다.
# 로그는 A00380 창의 로그창을 쓴다(`log(text, warn=False, ok=False)` 콜백).

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt.MOD_progress_qt_v01 import JUN_mod_progress_qt_v01

from tools.A00380_MeshTool.app.core import quad_patch as qp


OV = "JUN_A00380_quad_"          # optionVar 접두사

# 이 수보다 많은 면을 붙일 때만 진행 팝업 (면당 수 ms ~ 수십 ms)
_PROGRESS_FACES = 60

NOTES_TEXT = (
    "Quad Patch fills a hole with a grid of quads.\n\n"
    "Start\n"
    "  Edge Border  select a border edge of a hole (one is enough - the\n"
    "               whole hole is used). The hole needs an even edge count.\n"
    "  Faces        select a connected patch of faces. They are deleted and\n"
    "               refilled with a grid that follows the old surface and\n"
    "               keeps its UVs.\n"
    "  Extrude      select a run of border edges. A grid grows from them\n"
    "               into the hole by Rows; the rest of the hole stays open.\n\n"
    "Grid\n"
    "  Rotation     where the grid corners sit along the border.\n"
    "  Proportion   how many edges the first side gets (the other side\n"
    "               gets the rest). Auto picks the squarest corners.\n"
    "  Inset        rings of quads around the grid (smoother flow).\n\n"
    "Shape\n"
    "  Relax        smooths the new points (Faces: they stay on the old\n"
    "               surface).\n"
    "  Smooth Border  also rounds the hole border itself (moves existing\n"
    "               vertices - shown in the preview only as the patch edge).\n\n"
    "Patch It adds the faces to the original mesh: same transform, same\n"
    "shape node, history kept if it had any (one node per face then).\n"
    "One Ctrl+Z undoes it. The green preview is not in the undo queue.")


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


class _IntRow(object):
    """라벨 + 슬라이더 + 스핀박스 (정수). changed(value) 콜백."""

    def __init__(self, grid, row, label, tip, lo, hi, value, changed, style=None):
        self._sync = False
        self.label = QLabel(label)
        self.label.setToolTip(tip)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setToolTip(tip)
        if style:
            self.slider.setStyleSheet(style)
        self.spin = QSpinBox()
        self.spin.setToolTip(tip)
        self.spin.setKeyboardTracking(False)
        self.spin.setMinimumWidth(56)
        self.set_range(lo, hi)
        self.set_value(value)
        self._changed = changed
        self.slider.valueChanged.connect(self._from_slider)
        self.spin.valueChanged.connect(self._from_spin)
        grid.addWidget(self.label, row, 0)
        grid.addWidget(self.slider, row, 1)
        grid.addWidget(self.spin, row, 2)

    def set_range(self, lo, hi):
        self._sync = True
        self.slider.setRange(lo, hi)
        self.spin.setRange(lo, hi)
        self._sync = False

    def set_value(self, v):
        self._sync = True
        self.slider.setValue(v)
        self.spin.setValue(v)
        self._sync = False

    def value(self):
        return self.spin.value()

    def set_enabled(self, on):
        for w in (self.label, self.slider, self.spin):
            w.setEnabled(on)

    def _from_slider(self, v):
        if self._sync:
            return
        self._sync = True
        self.spin.setValue(v)
        self._sync = False
        self._changed(v)

    def _from_spin(self, v):
        if self._sync:
            return
        self._sync = True
        self.slider.setValue(v)
        self._sync = False
        self._changed(v)


class QuadPatchTab(QWidget):
    """Quad Patch 탭. `log(text, warn=False, ok=False)` 는 A00380 창의 로그."""

    def __init__(self, log, slider_style=None, parent=None):
        super().__init__(parent)
        self.log = log
        self.session = None
        self._style = slider_style
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(15)
        self._timer.timeout.connect(self._refresh)
        self._build()
        self._load_settings()
        self._sync_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def _build(self):
        layout = QVBoxLayout(self)

        # ---- Start -------------------------------------------------------
        box = QGroupBox("Start From Selection")
        row = QHBoxLayout(box)
        self.btn_edge = QPushButton("Edge Border")
        self.btn_edge.setToolTip("Fill a hole. Select one or more border edges of it -\n"
                                 "the whole hole is used. Even edge count needed.")
        self.btn_face = QPushButton("Faces")
        self.btn_face.setToolTip("Replace the selected faces with a quad grid that follows\n"
                                 "their surface and keeps their UVs.")
        self.btn_extrude = QPushButton("Extrude")
        self.btn_extrude.setToolTip("Grow a grid from a run of border edges into the hole.\n"
                                    "The rest of the hole stays open.")
        self.btn_edge.clicked.connect(lambda: self.on_start(qp.MODE_EDGE))
        self.btn_face.clicked.connect(lambda: self.on_start(qp.MODE_FACE))
        self.btn_extrude.clicked.connect(lambda: self.on_start(qp.MODE_EXTRUDE))
        for b in (self.btn_edge, self.btn_face, self.btn_extrude):
            row.addWidget(b)
        layout.addWidget(box)

        self.lbl_status = QLabel("No patch.  Select edges or faces, then press a Start button.")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        # ---- Grid --------------------------------------------------------
        box = QGroupBox("Grid")
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        self.row_rot = _IntRow(
            grid, 0, "Rotation", "Moves the grid corners along the border.",
            0, 1, 0, self._changed, self._style)
        self.row_side = _IntRow(
            grid, 1, "Proportion", "Edges on the first side of the grid.\n"
            "The neighbouring side gets the rest.", 1, 1, 1, self._changed, self._style)
        self.row_rows = _IntRow(
            grid, 2, "Rows", "Extrude: how many rows grow into the hole.",
            1, 1, 1, self._changed, self._style)
        self.row_rings = _IntRow(
            grid, 3, "Inset", "Rings of quads around the grid.",
            0, 5, 0, self._changed, self._style)
        self.btn_auto = QPushButton("Auto Corners")
        self.btn_auto.setToolTip("Pick Rotation and Proportion so the corners sit on the\n"
                                 "sharpest turns and the cells are closest to square.")
        self.btn_auto.clicked.connect(self.on_auto)
        grid.addWidget(self.btn_auto, 4, 0, 1, 3)
        layout.addWidget(box)

        # ---- Shape -------------------------------------------------------
        box = QGroupBox("Shape")
        grid = QGridLayout(box)
        grid.setColumnStretch(1, 1)
        self.row_relax = _IntRow(
            grid, 0, "Relax", "Smoothing passes on the new points.\n"
            "Faces mode keeps them on the old surface.", 0, 100, 10, self._changed, self._style)
        self.row_smooth = _IntRow(
            grid, 1, "Smooth Border %", "Also rounds the hole border itself.\n"
            "Moves existing vertices when you press Patch It.",
            0, 100, 0, self._changed, self._style)
        layout.addWidget(box)

        # ---- 옵션 · 실행 ------------------------------------------------
        row = QHBoxLayout()
        self.cb_soft = QCheckBox("Soft edges")
        self.cb_soft.setToolTip("Soften the new edges and the border edges.")
        self.cb_uvs = QCheckBox("UVs")
        self.cb_uvs.setToolTip("Edge Border / Extrude: planar projection on the new faces.\n"
                               "Faces: UVs read from the deleted faces and sewn to the border.")
        row.addWidget(self.cb_soft)
        row.addWidget(self.cb_uvs)
        row.addStretch(1)
        layout.addLayout(row)

        row = QHBoxLayout()
        self.btn_apply = QPushButton("Patch It")
        self.btn_apply.setMinimumHeight(32)
        self.btn_apply.setToolTip("Add the patch to the mesh (one Ctrl+Z).")
        self.btn_apply.clicked.connect(self.on_apply)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setMinimumHeight(32)
        self.btn_cancel.setToolTip("Drop the preview. The mesh is not touched.")
        self.btn_cancel.clicked.connect(self.on_cancel)
        row.addWidget(self.btn_apply, 2)
        row.addWidget(self.btn_cancel, 1)
        layout.addLayout(row)
        layout.addStretch(1)

    # ==================================================================
    # 설정
    # ==================================================================

    def _load_settings(self):
        self.row_relax.set_value(_ov_get("relax", 10))
        self.row_rings.set_value(_ov_get("rings", 0))
        self.row_smooth.set_value(_ov_get("smooth", 0))
        self.cb_soft.setChecked(_ov_get("soft", True))
        self.cb_uvs.setChecked(_ov_get("uvs", True))

    def _save_settings(self):
        _ov_set("relax", self.row_relax.value())
        _ov_set("rings", self.row_rings.value())
        _ov_set("smooth", self.row_smooth.value())
        _ov_set("soft", self.cb_soft.isChecked())
        _ov_set("uvs", self.cb_uvs.isChecked())

    def _sync_ui(self):
        s = self.session
        active = s is not None
        extrude = active and s.mode == qp.MODE_EXTRUDE
        grid = active and not extrude
        self.row_rot.set_enabled(grid)
        self.row_side.set_enabled(grid)
        self.btn_auto.setEnabled(grid)
        self.row_rings.set_enabled(not extrude)
        self.row_smooth.set_enabled(not extrude)
        self.row_rows.set_enabled(extrude)
        self.btn_apply.setEnabled(active)
        self.btn_cancel.setEnabled(active)

    def _params(self):
        return dict(rot=self.row_rot.value(), side=self.row_side.value(),
                    rows=self.row_rows.value(), rings=self.row_rings.value(),
                    relax_iter=self.row_relax.value(),
                    smooth=self.row_smooth.value() / 100.0)

    # ==================================================================
    # 동작
    # ==================================================================

    def on_start(self, mode):
        self.discard()
        try:
            self.session = qp.QuadPatchSession.from_selection(mode)
        except qp.PatchError as e:
            self.log(str(e), warn=True)
            self._sync_ui()
            return
        except Exception as e:
            self.log("Start failed: {0}".format(e), warn=True)
            self._sync_ui()
            return

        s = self.session
        n = s.edge_count
        self.row_rot.set_range(0, n - 1)
        self.row_side.set_range(1, max(1, n // 2 - 1))
        self.row_rows.set_range(1, s.max_rows())
        if s.mode == qp.MODE_EXTRUDE:
            self.row_rows.set_value(min(max(1, self.row_rows.value()), s.max_rows()))
        else:
            rot, side = s.auto_split()
            self.row_rot.set_value(rot)
            self.row_side.set_value(side)
        self._sync_ui()
        label = {qp.MODE_EDGE: "Edge Border", qp.MODE_FACE: "Faces",
                 qp.MODE_EXTRUDE: "Extrude"}[s.mode]
        self.log("Quad Patch ({0}) on {1}: border {2} edges{3}.".format(
            label, s.short_name(), n,
            ", chain {0}".format(s.chain_len) if s.mode == qp.MODE_EXTRUDE else
            ", {0} faces to replace".format(len(s.region)) if s.mode == qp.MODE_FACE else ""))
        self._refresh()

    def on_auto(self):
        if self.session is None:
            return
        rot, side = self.session.auto_split()
        self.row_rot.set_value(rot)
        self.row_side.set_value(side)
        self._refresh()

    def _changed(self, _value=None):
        if self.session is not None:
            self._timer.start()

    def _refresh(self):
        s = self.session
        if s is None:
            return
        try:
            faces, new_pts = s.preview(**self._params())
        except qp.PatchError as e:
            self.lbl_status.setText(str(e))
            return
        except Exception as e:
            self.lbl_status.setText("Preview failed: {0}".format(e))
            return
        p = self._params()
        if s.mode == qp.MODE_EXTRUDE:
            shape = "chain {0} x {1} rows".format(s.chain_len, p["rows"])
        else:
            shape = "{0} x {1}".format(p["side"], s.edge_count // 2 - p["side"])
            if p["rings"]:
                shape += " + {0} inset".format(p["rings"])
        self.lbl_status.setText("{0}: {1} border edges, grid {2} - {3} faces, {4} new points.".format(
            s.short_name(), s.edge_count, shape, faces, new_pts))

    def on_apply(self):
        s = self.session
        if s is None:
            return
        self._save_settings()
        params = self._params()
        try:
            faces = len(s.build(**params)[1])
        except qp.PatchError as e:
            self.log(str(e), warn=True)
            return

        dlg = None
        progress = None
        if faces > _PROGRESS_FACES:
            dlg = JUN_mod_progress_qt_v01(self.window(), title="Quad Patch",
                                          phases=[("Adding faces", 1)])
            dlg.start()
            dlg.begin_phase()
            progress = dlg.callback()
        try:
            res = s.commit(soft_edges=self.cb_soft.isChecked(), uvs=self.cb_uvs.isChecked(),
                           progress=progress, **params)
        except qp.PatchError as e:
            self.log(str(e), warn=True)
            self._after_session()
            return
        except Exception as e:
            self.log("Patch failed (nothing changed): {0}".format(e), warn=True)
            self._after_session()
            return
        finally:
            if dlg is not None:
                dlg.finish()

        self.log("Patched {0}: {1} faces, {2} new points ({3:.2f}s){4}.  Ctrl+Z undoes it.".format(
            s.short_name(), res["faces"], res["new_vertices"], res["seconds"],
            ", history kept" if res["history_kept"] else ""), ok=True)
        if res["history_kept"]:
            self.log("The mesh has history (deformers) - each new face added one "
                     "polyAppendVertex node. New points are not skinned.", warn=True)
        # 확정 뒤 선택을 바꾸지 않는다 - cmds.select 도 undo 큐에 들어가 Ctrl+Z 한 번이 깨진다
        self._after_session()

    def on_cancel(self):
        if self.session is not None:
            self.log("Quad Patch cancelled - the mesh was not touched.")
        self.discard()

    def _after_session(self):
        self.session = None
        self.lbl_status.setText("No patch.  Select edges or faces, then press a Start button.")
        self._sync_ui()

    def discard(self):
        """미리보기를 지우고 세션을 끝낸다 (창을 닫을 때도 부른다)."""
        self._timer.stop()
        if self.session is not None:
            try:
                self.session.discard()
            except Exception:
                pass
        self._after_session()
