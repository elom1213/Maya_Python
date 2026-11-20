# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 속도 그래프 위젯 · 패널 (속도 그래프 계획서 §3 · §4-7, v01.04 / v01.05 스크럽 undo 큐 밖 · 키 선 끌기 없앰)
"""
SpeedGraphWidget — QPainter 로 그리는 그래프 (마야 비의존 - 데이터는 패널이 set_data 로 넣는다)
    가로 = 프레임, 세로 = 모드 값 (Speed: 경로 길이/프레임 · Position: X/Y/Z · Acceleration: 길이/프레임²)
    키 = 세로선 + 프레임 번호 (선택 키 주황), 현재 프레임 = 초록, 칠하는 동안 = 원래 곡선 회색 + 새 곡선

    마우스                                 시그널
    오른쪽 드래그 : Smooth 브러시           brush_started(f) · brush_dab(f) · brush_finished()
    왼쪽 · 곡선 밖 : 현재 프레임 스크럽        scrubbed(f)   (키 선 위도 - v01.05 에서 키 시간 끌기는 없앴다)
    왼쪽 · 곡선   : 그곳을 빠르게 / 느리게      speed_started(f) · speed_dragging(f, amount) · speed_finished()   (Speed 모드)
    휠 = 반경 · Shift+휠 = 세기 · 곡선 끄는 중 휠 = Reach      radius_changed · strength_changed · reach_changed
    Esc / 끄는 중 반대 버튼 = 그 드래그 취소   drag_cancelled()

SpeedPanel — 툴 창 `Speed` 탭. 그래프 데이터를 만들고, 획을 StrokeSession 에 넘긴다(획 하나 = undo 하나).
UI 문자열은 영어.
"""

import numpy as np

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt import JUN_mod_timeRange_qt

from tools.A00630_MotionPathEditor.app.core import arc_length as al
from tools.A00630_MotionPathEditor.app.core import draw_nodes
from tools.A00630_MotionPathEditor.app.core import refit
from tools.A00630_MotionPathEditor.app.core import speed_session as ss

MODE_SPEED = "speed"
MODE_POSITION = "position"
MODE_ACCEL = "accel"
RANGE_PATH = "path"
RANGE_SELECTED = "selected"
RANGE_AROUND = "around"
RANGE_CUSTOM = "custom"           # v01.06 [Start, End] 만
BRUSH_SPEED = "speed"
BRUSH_SHAPE = "shape"
BRUSH_ACCEL = "accel"            # v01.08 가속도 Smooth
_BRUSH_KIND = {BRUSH_SPEED: ss.MODE_SPEED, BRUSH_SHAPE: ss.MODE_SHAPE, BRUSH_ACCEL: ss.MODE_ACCEL}

_BG = QColor(38, 38, 38)
_PLOT_BG = QColor(30, 30, 30)
_GRID = QColor(60, 60, 60)
_TEXT = QColor(190, 190, 190)
_KEY = QColor(120, 120, 120)
_KEY_SEL = QColor(255, 170, 40)
_CURRENT = QColor(90, 220, 90)
_GHOST = QColor(130, 130, 130)
_BRUSH = QColor(120, 180, 255)
_AXIS_COLORS = (QColor(235, 90, 90), QColor(110, 220, 110), QColor(100, 150, 255))

CURVE_HIT_PX = 8


def _pos(event):
    return event.position() if hasattr(event, "position") else QPointF(event.pos())


def _qcolor(rgb, alpha=255):
    return QColor(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), alpha)


class SpeedGraphWidget(QWidget):

    scrubbed = Signal(float)
    brush_started = Signal(float)
    brush_dab = Signal(float)
    brush_finished = Signal()
    speed_started = Signal(float)
    speed_dragging = Signal(float, float)
    speed_finished = Signal()
    drag_cancelled = Signal()
    radius_changed = Signal(float)
    strength_changed = Signal(float)
    reach_changed = Signal(float)

    MARGIN_L = 46
    MARGIN_R = 10
    MARGIN_T = 22
    MARGIN_B = 22

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.data = {}
        self.radius = 8.0
        self.strength = 0.5
        self.reach = 10.0
        self.edit_curve = True           # 곡선 끌기 (Speed 모드만)
        self.hover = None                # 마우스 프레임 (브러시 띠)
        self._drag = None                # ("scrub",) / ("brush",) / ("speed", f, y0)
        self.y_max = 1.0

    def sizeHint(self):
        return QSize(420, 220)

    # ---------------------------------------------------------------- 데이터 · 좌표
    def set_data(self, data):
        self.data = data or {}
        # 그리는 동안 세로 범위가 흔들리지 않게 끄는 중에는 키우기만
        top = 0.0
        lo = 0.0
        for s in self.data.get("series", ()):
            if len(s["ys"]):
                top = max(top, float(np.nanmax(s["ys"])))
                lo = min(lo, float(np.nanmin(s["ys"])))
        ghost = self.data.get("ghost")
        if ghost is not None and len(ghost["ys"]):
            top = max(top, float(np.nanmax(ghost["ys"])))
        top = top * 1.1 if top > 1e-12 else 1.0
        self.y_min = lo * 1.1 if lo < 0 else 0.0
        self.y_max = max(top, self.y_max) if self._drag else top
        self.update()

    def _plot(self):
        return QRectF(self.MARGIN_L, self.MARGIN_T, max(self.width() - self.MARGIN_L - self.MARGIN_R, 10),
                      max(self.height() - self.MARGIN_T - self.MARGIN_B, 10))

    def _x_range(self):
        x0 = float(self.data.get("x0", 0.0))
        x1 = float(self.data.get("x1", 1.0))
        if x1 - x0 < 1e-6:
            x1 = x0 + 1.0
        return x0, x1

    def frame_to_x(self, f):
        r = self._plot()
        x0, x1 = self._x_range()
        return r.left() + (np.asarray(f, dtype="float64") - x0) / (x1 - x0) * r.width()

    def x_to_frame(self, x):
        r = self._plot()
        x0, x1 = self._x_range()
        return x0 + (float(x) - r.left()) / r.width() * (x1 - x0)

    def value_to_y(self, v):
        r = self._plot()
        lo = getattr(self, "y_min", 0.0)
        return r.bottom() - (np.asarray(v, dtype="float64") - lo) / max(self.y_max - lo, 1e-12) * r.height()

    def value_per_px(self):
        return (self.y_max - getattr(self, "y_min", 0.0)) / max(self._plot().height(), 1.0)

    # ---------------------------------------------------------------- 그리기
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), _BG)
        r = self._plot()
        p.fillRect(r, _PLOT_BG)
        d = self.data
        if not d.get("series"):
            p.setPen(_TEXT)
            p.drawText(self.rect(), Qt.AlignCenter, d.get("empty", "Add paths in the Paths list to see the graph."))
            p.end()
            return
        x0, x1 = self._x_range()
        # 가로 격자 · 값 글자
        p.setPen(QPen(_GRID, 1))
        lo = getattr(self, "y_min", 0.0)
        for i in range(5):
            v = lo + (self.y_max - lo) * i / 4.0
            y = float(self.value_to_y(v))
            p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
            p.setPen(_TEXT)
            p.drawText(QRectF(0, y - 8, self.MARGIN_L - 4, 16), Qt.AlignRight | Qt.AlignVCenter, "{0:.3g}".format(v))
            p.setPen(QPen(_GRID, 1))
        # 키 선 + 번호
        for t, selected in d.get("keys", ()):
            if t < x0 - 1e-6 or t > x1 + 1e-6:
                continue
            x = float(self.frame_to_x(t))
            p.setPen(QPen(_KEY_SEL if selected else _KEY, 1, Qt.SolidLine))
            p.drawLine(QPointF(x, r.top()), QPointF(x, r.bottom()))
            p.drawText(QRectF(x - 20, r.top() - 16, 40, 14), Qt.AlignCenter, "{0:g}".format(round(t, 2)))
        # 현재 프레임
        cur = d.get("current")
        if cur is not None and x0 <= cur <= x1:
            x = float(self.frame_to_x(cur))
            p.setPen(QPen(_CURRENT, 1))
            p.drawLine(QPointF(x, r.top()), QPointF(x, r.bottom()))
        # 원래 곡선 (칠하는 동안)
        ghost = d.get("ghost")
        p.setClipRect(r)
        if ghost is not None:
            self._polyline(p, ghost["xs"], ghost["ys"], QPen(_GHOST, 2.5))
        for s in d.get("series", ()):
            color = QColor(s["color"])
            if not s.get("active", True):
                color.setAlpha(110)
            self._polyline(p, s["xs"], s["ys"], QPen(color, 2.0 if s.get("active", True) else 1.0))
        p.setClipping(False)
        # 브러시 띠 (마우스 위치)
        if self.hover is not None and (self._drag is None or self._drag[0] in ("brush", "speed")):
            if self._drag and self._drag[0] == "speed":
                fc, width = self._drag[1], self.reach
            else:
                fc, width = self.hover, self.radius
            xa, xb = float(self.frame_to_x(fc - width)), float(self.frame_to_x(fc + width))
            band = QColor(_BRUSH)
            band.setAlpha(int(50 + 150 * min(max(self.strength, 0.0), 1.0)))
            p.fillRect(QRectF(xa, r.bottom() - 5, xb - xa, 5), band)
        # 글자 : 제목 · 브러시
        p.setPen(_TEXT)
        p.drawText(QRectF(4, 2, self.width() / 2, 16), Qt.AlignLeft | Qt.AlignVCenter, d.get("title", ""))
        info = "Radius {0:g}  Strength {1:.2f}".format(round(self.radius, 1), self.strength)
        if self._drag and self._drag[0] == "speed":
            info = "Reach {0:g}".format(round(self.reach, 1))
        p.drawText(QRectF(self.width() / 2, 2, self.width() / 2 - 6, 16), Qt.AlignRight | Qt.AlignVCenter, info)
        p.drawText(QRectF(r.left(), r.bottom() + 3, r.width(), 16), Qt.AlignLeft, "{0:g}".format(round(x0, 2)))
        p.drawText(QRectF(r.left(), r.bottom() + 3, r.width(), 16), Qt.AlignRight, "{0:g}".format(round(x1, 2)))
        p.end()

    def _polyline(self, p, xs, ys, pen):
        if len(xs) < 2:
            return
        px = self.frame_to_x(xs)
        py = self.value_to_y(ys)
        poly = QPolygonF([QPointF(float(a), float(b)) for a, b in zip(px, py) if np.isfinite(b)])
        p.setPen(pen)
        p.drawPolyline(poly)

    # ---------------------------------------------------------------- 맞히기
    def on_curve(self, x, y):
        for s in self.data.get("series", ()):
            if not s.get("active", True) or len(s["xs"]) < 2:
                continue
            v = float(np.interp(self.x_to_frame(x), s["xs"], s["ys"]))
            if abs(float(self.value_to_y(v)) - y) <= CURVE_HIT_PX:
                return True
        return False

    # ---------------------------------------------------------------- 마우스
    def mousePressEvent(self, event):
        self.setFocus()
        pt = _pos(event)
        f = self.x_to_frame(pt.x())
        if self._drag is not None:                     # 끄는 중 다른 버튼 = 취소
            self._cancel()
            return
        if not self.data.get("series"):
            return
        if event.button() == Qt.RightButton:
            self._drag = ("brush",)
            self.brush_started.emit(f)
            self.brush_dab.emit(f)
        elif event.button() == Qt.LeftButton:
            if self.edit_curve:
                if self.on_curve(pt.x(), pt.y()):
                    self._drag = ("speed", f, pt.y())
                    self.speed_started.emit(f)
                    self.update()
                    return
            self._drag = ("scrub",)
            self.scrubbed.emit(f)
        self.update()

    def mouseMoveEvent(self, event):
        pt = _pos(event)
        f = self.x_to_frame(pt.x())
        self.hover = f
        kind = self._drag[0] if self._drag else None
        if kind == "brush":
            self.brush_dab.emit(f)
        elif kind == "scrub":
            self.scrubbed.emit(f)
        elif kind == "speed":
            amount = (self._drag[2] - pt.y()) * self.value_per_px()
            self.speed_dragging.emit(self._drag[1], amount)
        self.update()

    def mouseReleaseEvent(self, event):
        drag, self._drag = self._drag, None
        if not drag:
            return
        if drag[0] == "brush" and event.button() == Qt.RightButton:
            self.brush_finished.emit()
        elif drag[0] == "speed" and event.button() == Qt.LeftButton:
            self.speed_finished.emit()
        self.update()

    def leaveEvent(self, event):
        if self._drag is None:
            self.hover = None
            self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self._drag is not None:
            self._cancel()
            return
        super().keyPressEvent(event)

    def _cancel(self):
        self._drag = None
        self.drag_cancelled.emit()
        self.update()

    def wheelEvent(self, event):
        steps = event.angleDelta().y() / 120.0
        if not steps:
            return
        factor = 1.15 ** steps
        if self._drag and self._drag[0] == "speed":
            self.reach = float(min(max(self.reach * factor, 1.0), 500.0))
            self.reach_changed.emit(self.reach)
        elif event.modifiers() & Qt.ShiftModifier:
            self.strength = float(min(max(self.strength + 0.05 * steps, 0.05), 1.0))
            self.strength_changed.emit(self.strength)
        else:
            self.radius = float(min(max(self.radius * factor, 1.0), 500.0))
            self.radius_changed.emit(self.radius)
        self.update()
        event.accept()


# ====================================================================== 패널
class SpeedPanel(QWidget):
    """툴 창 Speed 탭: 그래프 + 브러시 설정. manager 는 PathManager, watcher 는 Watcher."""

    def __init__(self, manager, watcher, log, save, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.watcher = watcher
        self.log = log
        self.save = save                 # save(key) - 설정을 optionVar 로
        self.session = None
        self._float = None
        self._syncing = False
        self._build()
        manager.listeners.append(self.refresh_graph)
        self.refresh_graph()

    # ---------------------------------------------------------------- UI
    def _build(self):
        s = self.manager.settings
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)

        row = QHBoxLayout()
        row.addWidget(QLabel("Path"))
        self.cmb_path = QComboBox()
        self.cmb_path.setToolTip("The path the graph edits (strokes, curve and key drags). Other paths are drawn faint.")
        self.cmb_path.currentIndexChanged.connect(lambda *_: self._on_active_changed())
        row.addWidget(self.cmb_path, 1)
        self.btn_pop = QPushButton("Pop Out")
        self.btn_pop.setToolTip("Show the graph in its own window (wider, e.g. on a second monitor). Click again to dock it.")
        self.btn_pop.clicked.connect(self.toggle_float)
        row.addWidget(self.btn_pop)
        lay.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Show"))
        self.mode_buttons = QButtonGroup(self)
        for label, value, tip in (
                ("Speed", MODE_SPEED, "How far the object moves on every frame. Paint here to even out the timing."),
                ("Position", MODE_POSITION, "World X / Y / Z of the active path (read only)."),
                ("Acceleration", MODE_ACCEL, "How fast the speed changes - pops and jitter stand out. Smooth them away.")):
            rb = QRadioButton(label)
            rb.setToolTip(tip)
            rb.setProperty("value", value)
            rb.setChecked(s["graph_mode"] == value)
            self.mode_buttons.addButton(rb)
            row.addWidget(rb)
        self.mode_buttons.buttonClicked.connect(lambda b: self._on_graph_mode(b.property("value")))
        row.addStretch(1)
        self.cmb_units = QComboBox()
        self.cmb_units.addItems(["per frame", "per second"])
        self.cmb_units.setToolTip("Speed / acceleration per frame or per second (scene fps).")
        self.cmb_units.setCurrentIndex(1 if s["graph_per_second"] else 0)
        self.cmb_units.currentIndexChanged.connect(lambda i: self._set("graph_per_second", bool(i)))
        row.addWidget(self.cmb_units)
        lay.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Frames"))
        self.range_buttons = QButtonGroup(self)
        for label, value, tip in (
                ("Whole Path", RANGE_PATH, "The whole range of the path."),
                ("Selected Keys", RANGE_SELECTED, "Between the selected keys (one key: the segments on both sides)."),
                ("Around Current", RANGE_AROUND, "The keys before and after the current frame."),
                ("Custom", RANGE_CUSTOM, "Only the frames from Start to End below.")):
            rb = QRadioButton(label)
            rb.setToolTip(tip)
            rb.setProperty("value", value)
            rb.setChecked(s["graph_range"] == value)
            self.range_buttons.addButton(rb)
            row.addWidget(rb)
        self.range_buttons.buttonClicked.connect(lambda b: self._on_range_mode(b.property("value")))
        row.addStretch(1)
        lay.addLayout(row)

        # v01.06 - Custom 범위: 공용 Start / End / Get Current / Get Sel Range (Path 탭 Range 와 같은 위젯)
        self.range_edit = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=int(s["graph_start"]), end_value=int(s["graph_end"]), log_callback=self._log)
        self.range_edit.setToolTip("Custom graph range. Get Current: the current frame. "
                                   "Get Sel Range: the first and last selected keyframe (Graph Editor / Time Slider).")
        self.range_edit.changed.connect(self._on_custom_range)
        lay.addWidget(self.range_edit)
        self.range_edit.set_inputs_enabled(s["graph_range"] == RANGE_CUSTOM)

        self.graph_holder = QWidget()
        hl = QVBoxLayout(self.graph_holder)
        hl.setContentsMargins(0, 0, 0, 0)
        self.graph = SpeedGraphWidget()
        self.graph.setToolTip(
            "Right-drag: smooth (wheel: radius, Shift+wheel: strength).\n"
            "Left-drag on the curve: faster / slower there (wheel while dragging: reach).\n"
            "Left-drag elsewhere (key lines too): scrub the current frame. Esc / the other button while dragging: cancel.\n"
            "Every stroke is one undo (Ctrl+Z in Maya).")
        self.graph.radius = float(s["brush_radius"])
        self.graph.strength = float(s["brush_strength"])
        hl.addWidget(self.graph)
        lay.addWidget(self.graph_holder, 1)
        g = self.graph
        g.scrubbed.connect(self._on_scrub)
        g.brush_started.connect(self._on_brush_started)
        g.brush_dab.connect(self._on_brush_dab)
        g.brush_finished.connect(self._on_stroke_finished)
        g.speed_started.connect(self._on_speed_started)
        g.speed_dragging.connect(self._on_speed_dragging)
        g.speed_finished.connect(self._on_stroke_finished)
        g.drag_cancelled.connect(self._on_cancelled)
        g.radius_changed.connect(self._on_radius_wheel)
        g.strength_changed.connect(self._on_strength_wheel)

        row = QHBoxLayout()
        row.addWidget(QLabel("Brush"))
        self.cmb_brush = QComboBox()
        self.cmb_brush.addItem("Smooth Speed", BRUSH_SPEED)
        self.cmb_brush.addItem("Smooth Shape", BRUSH_SHAPE)
        self.cmb_brush.addItem("Smooth Acceleration", BRUSH_ACCEL)
        self.cmb_brush.setToolTip(
            "Smooth Speed: evens out the timing - the path keeps its shape, the keys keep their frames,\n"
            "the poses slide along the path. A hold stays a hold.\n"
            "Smooth Shape: removes bumps from the path itself (big arcs stay).\n"
            "Smooth Acceleration: evens out the acceleration - pops, jitter and sharp turns get rounder\n"
            "(shape and timing change together). Picked by itself when Show is Acceleration.")
        self.cmb_brush.setCurrentIndex(max(self.cmb_brush.findData(s["brush_mode"]), 0))
        self.cmb_brush.currentIndexChanged.connect(lambda *_: self._set("brush_mode", self.cmb_brush.currentData()))
        row.addWidget(self.cmb_brush)
        row.addWidget(QLabel("Radius"))
        self.sp_radius = QDoubleSpinBox()
        self.sp_radius.setRange(1.0, 500.0)
        self.sp_radius.setDecimals(1)
        self.sp_radius.setSuffix(" fr")
        self.sp_radius.setValue(float(s["brush_radius"]))
        self.sp_radius.setToolTip("Brush radius in frames (mouse wheel over the graph).")
        self.sp_radius.valueChanged.connect(self._on_radius_spin)
        row.addWidget(self.sp_radius)
        row.addWidget(QLabel("Strength"))
        self.sl_strength = QSlider(Qt.Horizontal)
        self.sl_strength.setRange(5, 100)
        self.sl_strength.setValue(int(round(float(s["brush_strength"]) * 100)))
        self.sl_strength.setToolTip("How much one stroke smooths (Shift + mouse wheel over the graph).")
        self.sl_strength.valueChanged.connect(self._on_strength_slider)
        row.addWidget(self.sl_strength, 1)
        self.lbl_strength = QLabel("{0:.2f}".format(float(s["brush_strength"])))
        self.lbl_strength.setMinimumWidth(30)
        row.addWidget(self.lbl_strength)
        lay.addLayout(row)

        row = QHBoxLayout()
        self.cb_whole = QCheckBox("Whole Pose")
        self.cb_whole.setToolTip(
            "Speed strokes retime the rotate / scale keys too, with the same timing change -\n"
            "so the pose keeps up with the position (off: only the position moves, like the original add-on).")
        self.cb_whole.setChecked(bool(s["whole_pose"]))
        self.cb_whole.toggled.connect(lambda on: self._set("whole_pose", bool(on), graph=False))
        row.addWidget(self.cb_whole)
        row.addWidget(QLabel("Tolerance"))
        self.sp_tol = QDoubleSpinBox()
        self.sp_tol.setRange(0.01, 5.0)
        self.sp_tol.setDecimals(2)
        self.sp_tol.setSingleStep(0.05)
        self.sp_tol.setSuffix(" %")
        self.sp_tol.setValue(float(s["fit_tolerance"]))
        self.sp_tol.setToolTip(
            "How close the keys must follow the stroke, in % of the path size.\n"
            "Smaller = more exact, but more keys get added. Keys on every frame (mocap) are always exact.")
        self.sp_tol.valueChanged.connect(lambda v: self._set("fit_tolerance", float(v), graph=False))
        row.addWidget(self.sp_tol)
        row.addStretch(1)
        self.btn_smooth = QPushButton("Smooth Range")
        self.btn_smooth.setMinimumHeight(28)
        self.btn_smooth.setToolTip("Smooth every frame shown in the graph once with the brush settings (one undo).")
        self.btn_smooth.clicked.connect(self.smooth_range)
        row.addWidget(self.btn_smooth)
        lay.addLayout(row)

        self.lbl_info = QLabel("")
        self.lbl_info.setWordWrap(True)
        lay.addWidget(self.lbl_info)

    # ---------------------------------------------------------------- 설정
    def _set(self, key, value, graph=True):
        self.manager.settings[key] = value
        self.save(key)
        if graph:
            self.refresh_graph()

    def _on_radius_spin(self, v):
        self.graph.radius = float(v)
        self.graph.update()
        self._set("brush_radius", float(v), graph=False)

    def _on_radius_wheel(self, v):
        self.sp_radius.blockSignals(True)
        self.sp_radius.setValue(v)
        self.sp_radius.blockSignals(False)
        self._set("brush_radius", float(v), graph=False)

    def _on_strength_slider(self, v):
        self.graph.strength = v / 100.0
        self.lbl_strength.setText("{0:.2f}".format(v / 100.0))
        self.graph.update()
        self._set("brush_strength", v / 100.0, graph=False)

    def _on_strength_wheel(self, v):
        self.sl_strength.blockSignals(True)
        self.sl_strength.setValue(int(round(v * 100)))
        self.sl_strength.blockSignals(False)
        self.lbl_strength.setText("{0:.2f}".format(v))
        self._set("brush_strength", float(v), graph=False)

    def _log(self, text):
        self.log(text)

    def _on_graph_mode(self, value):
        """Show 바꾸기. v01.08 - Acceleration 을 보면 브러시도 Smooth Acceleration 으로(그 그래프를 칠하면 그 값이 고르게 되도록),
        Acceleration 에서 나오면 그 전 브러시로 되돌린다(그동안 사용자가 브러시를 바꿨으면 그대로)."""
        before = self.manager.settings["graph_mode"]
        brush = self.manager.settings["brush_mode"]
        if value == MODE_ACCEL and before != MODE_ACCEL and brush != BRUSH_ACCEL:
            self._brush_before_accel = brush
            self.cmb_brush.setCurrentIndex(self.cmb_brush.findData(BRUSH_ACCEL))
        elif value != MODE_ACCEL and before == MODE_ACCEL and brush == BRUSH_ACCEL:
            back = getattr(self, "_brush_before_accel", None)
            if back:
                self.cmb_brush.setCurrentIndex(self.cmb_brush.findData(back))
        self._set("graph_mode", value)

    def _on_range_mode(self, value):
        self.range_edit.set_inputs_enabled(value == RANGE_CUSTOM)
        self._set("graph_range", value)

    def _on_custom_range(self):
        """Start · End 칸이 바뀌면 저장하고 그래프를 다시 (빈 칸 · 숫자 아님은 이전 값 유지). 값이 같으면 아무것도 안 한다."""
        s = self.manager.settings
        start, end = self.range_edit.start(), self.range_edit.end()
        new = (start if start is not None else s["graph_start"], end if end is not None else s["graph_end"])
        if new == (s["graph_start"], s["graph_end"]):
            return
        s["graph_start"], s["graph_end"] = int(new[0]), int(new[1])
        self.save("graph_start")
        self.save("graph_end")
        if s["graph_range"] == RANGE_CUSTOM:
            self.refresh_graph()

    # ---------------------------------------------------------------- 경로 · 범위
    def active_cache(self):
        key = self.cmb_path.currentData()
        return self.manager.caches.get(key) if key else None

    def _sync_paths(self):
        caches = self.manager.cache_list()
        want = [(c.label + ("  (locked)" if c.locked else ""), c.key) for c in caches]
        have = [(self.cmb_path.itemText(i), self.cmb_path.itemData(i)) for i in range(self.cmb_path.count())]
        if want == have:
            return
        current = self.cmb_path.currentData()
        self._syncing = True
        try:
            self.cmb_path.clear()
            for text, key in want:
                self.cmb_path.addItem(text, key)
            keys = [k for _t, k in want]
            if current in keys:
                self.cmb_path.setCurrentIndex(keys.index(current))
            else:
                unlocked = [i for i, c in enumerate(caches) if not c.locked]
                self.cmb_path.setCurrentIndex(unlocked[0] if unlocked else 0)
        finally:
            self._syncing = False

    def _on_active_changed(self):
        if not self._syncing:
            self.session = None
            self.refresh_graph()

    def graph_range(self, cache):
        """그래프에 보일 프레임 [x0, x1]. Custom 이 경로와 1 프레임도 안 겹치면 None (v01.06)."""
        t0, t1 = float(cache.times[0]), float(cache.times[-1])
        mode = self.manager.settings["graph_range"]
        if mode == RANGE_CUSTOM:
            a, b = sorted((float(self.manager.settings["graph_start"]), float(self.manager.settings["graph_end"])))
            a, b = max(a, t0), min(b, t1)          # 경로 밖 프레임은 그릴 것이 없다
            return (a, b) if b - a >= 1.0 else None
        keys = [k.t for k in cache.keys]
        if mode == RANGE_SELECTED:
            sel = sorted(self.manager.selection.get(cache.key, ()))
            if len(sel) >= 2:
                return sel[0], sel[-1]
            if len(sel) == 1:
                before = [t for t in keys if t < sel[0] - 1e-6]
                after = [t for t in keys if t > sel[0] + 1e-6]
                return (before[-1] if before else t0), (after[0] if after else t1)
            mode = RANGE_AROUND
        if mode == RANGE_AROUND:
            cur = float(cmds.currentTime(q=True))
            before = [t for t in keys if t <= cur + 1e-6]
            after = [t for t in keys if t > cur + 1e-6]
            a = before[-1] if before else t0
            b = after[0] if after else t1
            if b - a >= 1.0:
                return a, b
        return t0, t1

    # ---------------------------------------------------------------- 그래프 데이터
    @staticmethod
    def _unit():
        return om.MDistance(1.0, om.MDistance.internalUnit()).asUnits(om.MDistance.uiUnit())

    def _unit_name(self):
        names = {om.MDistance.kCentimeters: "cm", om.MDistance.kMeters: "m", om.MDistance.kMillimeters: "mm",
                 om.MDistance.kInches: "in", om.MDistance.kFeet: "ft", om.MDistance.kYards: "yd",
                 om.MDistance.kKilometers: "km", om.MDistance.kMiles: "mi"}
        return names.get(om.MDistance.uiUnit(), "")

    def _values(self, mode, times, points, frames):
        scale = self._unit()
        per_s = self.manager.settings["graph_per_second"]
        fps = refit.fps()
        if mode == MODE_POSITION:
            return al.positions(times, points, frames) * scale
        if mode == MODE_ACCEL:
            return al.accel(times, points, frames) * scale * (fps * fps if per_s else 1.0)
        return al.speed(times, points, frames) * scale * (fps if per_s else 1.0)

    def refresh_graph(self):
        """매니저가 다시 그릴 때마다 (경로 · 시간 · 선택이 바뀔 때) 부른다."""
        try:
            self._sync_paths()
            self.graph.set_data(self._graph_data())
            self._show_info()
        except Exception as exc:                           # noqa: BLE001
            self.graph.set_data({"empty": "Graph error : {0}".format(exc)})

    def _graph_data(self):
        active = self.active_cache()
        if active is None or active.points is None:
            return {"empty": "Add paths in the Paths list to see the graph."}
        mode = self.manager.settings["graph_mode"]
        self.graph.edit_curve = mode == MODE_SPEED and not active.locked
        rng = self.graph_range(active)
        if rng is None:
            s = self.manager.settings
            return {"empty": "Start - End ({0} - {1}) is outside the path (frames {2:g} - {3:g}).".format(
                s["graph_start"], s["graph_end"], active.times[0], active.times[-1])}
        x0, x1 = rng
        per = "/s" if self.manager.settings["graph_per_second"] else "/frame"
        unit = self._unit_name()
        title = {MODE_SPEED: "Speed ({0}{1})".format(unit, per),
                 MODE_POSITION: "World position ({0}) - X red, Y green, Z blue".format(unit),
                 MODE_ACCEL: "Acceleration ({0}{1}²)".format(unit, per)}[mode]
        series = []
        ghost = None
        preview = self.manager.preview.get(active.key)
        frames_of = {}
        for i, c in enumerate(self.manager.cache_list()):
            if c.points is None:
                continue
            a, b = max(x0, c.times[0]), min(x1, c.times[-1])
            frames = np.arange(np.ceil(a), np.floor(b) + 1.0)
            if len(frames) < 2:
                continue
            frames_of[c.key] = frames
            is_active = c.key == active.key
            if mode == MODE_POSITION and not is_active:
                continue
            pts = preview if (is_active and preview is not None) else c.points
            vals = self._values(mode, c.times, pts, frames)
            if mode == MODE_POSITION:
                for k in range(3):
                    series.append({"xs": frames, "ys": vals[:, k], "color": _AXIS_COLORS[k], "active": True})
            else:
                color = _qcolor(draw_nodes.PALETTE[i % len(draw_nodes.PALETTE)])
                series.append({"xs": frames, "ys": vals, "color": color, "active": is_active})
            if is_active and preview is not None and mode != MODE_POSITION:
                ghost = {"xs": frames, "ys": self._values(mode, c.times, c.points, frames)}
        if mode != MODE_POSITION:
            series.sort(key=lambda s: s["active"])         # 활성 경로를 맨 위에
        selected = self.manager.selection.get(active.key, set())
        keys = [(k.t, k.t in selected) for k in active.keys]
        return {"x0": x0, "x1": x1, "series": series, "ghost": ghost, "keys": keys,
                "current": float(cmds.currentTime(q=True)), "title": title}

    def _show_info(self):
        c = self.active_cache()
        if c is None:
            self.lbl_info.setText("")
        elif c.locked:
            self.lbl_info.setText("Locked: {0}".format(c.lock_reason))
        else:
            self.lbl_info.setText("")

    # ---------------------------------------------------------------- 세션
    def _session(self, kind):
        """지금 경로 · 브러시에 맞는 세션 (없거나 낡았으면 새로). 못 만들면 None."""
        cache = self.active_cache()
        if cache is None:
            self.log("[WARN] Add a path first.")
            return None
        if cache.locked:
            self.log("[WARN] {0} : {1}.".format(cache.label, cache.lock_reason))
            return None
        s = self.manager.settings
        whole = bool(s["whole_pose"]) and kind == ss.MODE_SPEED
        tol = float(s["fit_tolerance"]) / 100.0
        cur = self.session
        if cur is None or cur.key != cache.key or cur.mode != kind or cur.whole_pose != whole or \
                abs(cur.tolerance_rel - tol) > 1e-12 or len(cur.times) != len(cache.times) or \
                np.abs(cur.times - np.asarray(cache.times)).max() > 1e-9 or not cur.valid():
            try:
                cur = ss.StrokeSession(cache, mode=kind, whole_pose=whole, tolerance_rel=tol)
            except Exception as exc:                       # noqa: BLE001
                self.log("[WARN] {0}".format(exc))
                return None
            self.session = cur
        return cur

    def _preview(self):
        s = self.session
        if s is None:
            return
        self.manager.preview[s.key] = s.preview_points()
        self.manager.redraw()

    def _on_brush_started(self, f):
        kind = _BRUSH_KIND.get(self.manager.settings["brush_mode"], ss.MODE_SPEED)
        s = self._session(kind)
        if s is not None:
            s.begin_stroke()

    def _on_brush_dab(self, f):
        s = self.session
        if s is None or not s.stroking:
            return
        s.dab(f, self.graph.radius, self.graph.strength)
        self._preview()

    def _on_speed_started(self, f):
        s = self._session(ss.MODE_SPEED)
        if s is not None:
            s.begin_stroke()
            keys = [k.t for k in s.cache.keys]
            before = [t for t in keys if t < f]
            after = [t for t in keys if t > f]
            if before and after:                           # 기본 Reach = 그 구간의 1/3 (원본과 같은 생각)
                self.graph.reach = max((after[0] - before[-1]) / 3.0, 2.0)

    def _on_speed_dragging(self, f, amount):
        s = self.session
        if s is None or not s.stroking:
            return
        scale = self._unit() * (refit.fps() if self.manager.settings["graph_per_second"] else 1.0)
        s.change_speed(f, amount / scale, self.graph.reach)
        self._preview()

    def _on_stroke_finished(self):
        s = self.session
        if s is None or not s.stroking:
            return
        self.watcher.busy = True
        try:
            wrote = s.end_stroke()
        except Exception as exc:                           # noqa: BLE001
            wrote = False
            self.log("[FAIL] Stroke failed : {0}".format(exc))
            self.session = None
        finally:
            self.watcher.busy = False
            self.manager.preview.pop(s.key, None)
        self.manager.redraw()
        if wrote:
            self._log_report(s)

    def _log_report(self, s):
        parts = []
        unit = self._unit()
        for name, err, added, msg in s.report:
            if msg:
                parts.append("{0}: skipped ({1})".format(name, msg))
                continue
            if name.startswith("translate"):
                parts.append("{0} {1:.4f} {2}{3}".format(name, err * unit, self._unit_name(),
                                                         ", +{0} key(s)".format(added) if added else ""))
            else:
                parts.append("{0}{1}".format(name, " +{0} key(s)".format(added) if added else ""))
        self.log("[OK] {0} : stroke applied (one undo) - max fit error {1}".format(s.cache.label, "; ".join(parts)))

    def _on_cancelled(self):
        s = self.session
        if s is not None and s.stroking:
            s.drop_stroke()
            self.manager.preview.pop(s.key, None)
            self.manager.redraw()
            self.log("[Info] Stroke cancelled.")

    def _on_scrub(self, f):
        """현재 프레임을 마우스로 (v01.05: undo 큐에 넣지 않는다).

        `cmds.currentTime` 은 스크립트에서 부르면 **부를 때마다 undo 하나**가 쌓인다(실측 - 마야 타임 슬라이더는 안 쌓인다).
        스크럽은 마우스 이동마다 부르므로 획 뒤에 그래프를 조금만 훑어도 Ctrl+Z 가 획이 아니라 시간 변경만 되돌렸다
        (그래프가 그대로 = "undo 가 안 된다"). API `MAnimControl.setCurrentTime` 은 큐에 남지 않고 timeChanged 도 보낸다.
        """
        frame = float(round(f))
        unit = om.MTime.uiUnit()
        if abs(oma.MAnimControl.currentTime().asUnits(unit) - frame) < 1e-9:
            return
        oma.MAnimControl.setCurrentTime(om.MTime(frame, unit))

    def smooth_range(self):
        """그래프에 보이는 프레임 전체를 브러시 설정으로 한 번 (undo 하나)."""
        cache = self.active_cache()
        if cache is None:
            self.log("[WARN] Add a path first.")
            return
        kind = _BRUSH_KIND.get(self.manager.settings["brush_mode"], ss.MODE_SPEED)
        s = self._session(kind)
        if s is None:
            return
        rng = self.graph_range(cache)
        if rng is None:
            self.log("[WARN] Start - End is outside the path - nothing to smooth.")
            return
        x0, x1 = rng
        r = self.graph.radius
        s.begin_stroke()
        for fc in np.arange(x0, x1 + 1e-6, max(r / 2.0, 1.0)):
            s.dab(fc, r, self.graph.strength)
        self._on_stroke_finished()

    # ---------------------------------------------------------------- 떼어 보기
    def toggle_float(self):
        if self._float is None:
            win = QWidget(self.window(), Qt.Tool)
            win.setWindowTitle("Motion Path Editor - Graph")
            win.setObjectName("JUN_A00630_MotionPathEditor_graph_window")
            lay = QVBoxLayout(win)
            lay.setContentsMargins(4, 4, 4, 4)
            lay.addWidget(self.graph)
            win.resize(max(self.graph.width(), 720), max(self.graph.height(), 300))
            win.closeEvent = lambda ev: (self._dock(), ev.accept())
            win.show()
            self._float = win
            self.btn_pop.setText("Dock")
        else:
            self._float.close()

    def _dock(self):
        if self._float is None:
            return
        self.graph_holder.layout().addWidget(self.graph)
        self._float.deleteLater()
        self._float = None
        self.btn_pop.setText("Pop Out")

    def shutdown(self):
        if self.refresh_graph in self.manager.listeners:
            self.manager.listeners.remove(self.refresh_graph)
        if self._float is not None:
            self._float.close()
