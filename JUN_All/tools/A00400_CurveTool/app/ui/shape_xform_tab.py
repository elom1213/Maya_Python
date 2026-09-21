# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-21
# A00400_CurveTool - Display > Transform 탭 (커브 셰이프를 피벗 기준으로 크게/작게 · 이동 · 회전)
#
# 리스트업한 커브마다 **그 커브의 피벗**을 기준으로 CV 전체를 스케일 / 이동 / 회전한다.
# 뷰포트에서 커브의 CV 를 전부 골라 Scale / Move / Rotate 툴을 쓴 것과 같은 결과이고,
# 트랜스폼의 scale / rotate / translate 채널은 **전혀 건드리지 않는다**(컨트롤러의 채널은
# 기본값으로 남아 있어야 하므로). 계산은 `app/core/shape_xform_manager.py`.
#
# 세 가지(Scale / Move / Rotate)를 각각 체크박스로 켜고 끈다. **기본은 Scale 만 켬** —
# 실제로 제일 자주 하는 일이 컨트롤 크기 조절이고, 셋 다 켜져 있으면 크기만 바꾸려다
# 위치까지 움직이는 사고가 난다.
#
# 축은 줄마다 X / Y / Z 체크박스로 고른다. 끈 축은 중립값(스케일 1, 이동·회전 0)이 되어
# 그 축은 그대로다. Scale 의 `Uniform` 은 한 칸에 친 값을 켜 둔 다른 축에도 그대로
# 넣어 준다 — 대부분은 세 축을 같은 배율로 키우기 때문이다.
#
# ── 값 칸마다 슬라이더 (v01.19) ───────────────────────────────────────────
# 아홉 개 값(3가지 × XYZ)을 **전부 슬라이더로 끌어서** 정한다. 숫자를 쳐 넣는 것보다
# "조금 크게" 를 찾는 데 훨씬 빠르고, 그게 이 탭에서 실제로 하는 일이다.
#
# 슬라이더 범위는 **자주 쓰는 구간**이고(스케일 0~5 · 이동 ±10 · 회전 ±180), 스핀박스는
# 예전 그대로 **전체 범위**(스케일 ±1000 · 이동 ±100000 · 회전 ±3600)를 받는다.
# 슬라이더 범위 밖의 값을 쳐 넣으면 **슬라이더 범위가 그 값까지 늘어난다** — 잘라 버리면
# 사용자가 친 값이 조용히 바뀌고, 처음부터 넓게 잡으면 한 픽셀이 수십 단위가 되어
# 슬라이더가 쓸모없어진다. `Reset Values` 는 범위도 기본값으로 되돌린다.
#
# 슬라이더는 값만 정한다 — 씬은 예전처럼 `Apply to Shapes` 에서만 바뀐다.

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from Framework.core.maya_undo import undo_chunk
from tools.A00400_CurveTool.app.core import shape_xform_manager as xform_mgr


#: 값 칸 폭 — 슬라이더가 자리를 갖도록 숫자 칸은 좁게.
SPIN_WIDTH = 72

#: 축 라벨
AXIS_LABELS = ("X", "Y", "Z")


class _AxisSlider(QWidget):
    """축 한 줄 — [축 체크박스 X] [슬라이더] [스핀박스].

    QSlider 는 정수만 다루므로 `slider_step` 으로 나눠 정수 칸으로 쓴다(0.01 -> 100배).
    슬라이더와 스핀박스는 서로의 신호로 값을 되쓰므로 갱신할 때는 `blockSignals` 로 막는다.
    """

    valueChanged = Signal(float)

    def __init__(self, axis, neutral, decimals, spin_step, spin_min, spin_max,
                 slider_min, slider_max, slider_step, axis_tip, parent=None):

        super().__init__(parent)

        self.neutral = float(neutral)
        self.slider_step = float(slider_step)
        # Reset 때 되돌릴 기본 슬라이더 범위.
        self.home_range = (float(slider_min), float(slider_max))

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        self.check = QCheckBox(axis)
        self.check.setChecked(True)
        self.check.setToolTip(axis_tip)
        self.check.toggled.connect(self._on_axis_toggled)
        row.addWidget(self.check)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self._to_int(slider_min))
        self.slider.setMaximum(self._to_int(slider_max))
        self.slider.setValue(self._to_int(self.neutral))
        self.slider.valueChanged.connect(self._on_slider)
        row.addWidget(self.slider, 1)

        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(decimals)
        self.spin.setSingleStep(spin_step)
        self.spin.setRange(spin_min, spin_max)
        self.spin.setValue(self.neutral)
        self.spin.setFixedWidth(SPIN_WIDTH)
        # 타이핑 도중(한 글자마다) 값이 튀지 않게 - 엔터/포커스 이동에서만 반영.
        self.spin.setKeyboardTracking(False)
        self.spin.valueChanged.connect(self._on_spin)
        row.addWidget(self.spin)

    # ------------------------------------------------------------------
    # 단위 변환 / 범위
    # ------------------------------------------------------------------

    def _to_int(self, value):
        return int(round(float(value) / self.slider_step))

    def _to_float(self, value):
        return float(value) * self.slider_step

    def _grow_range(self, value):
        """슬라이더 범위 밖의 값이 오면 그 값까지 범위를 넓힌다(잘라내지 않는다)."""
        ticks = self._to_int(value)

        if ticks < self.slider.minimum():
            self.slider.setMinimum(ticks)
        elif ticks > self.slider.maximum():
            self.slider.setMaximum(ticks)

    # ------------------------------------------------------------------
    # 신호
    # ------------------------------------------------------------------

    def _on_slider(self, ticks):
        value = self._to_float(ticks)

        blocked = self.spin.blockSignals(True)
        self.spin.setValue(value)
        self.spin.blockSignals(blocked)

        self.valueChanged.emit(value)

    def _on_spin(self, value):
        self._grow_range(value)

        blocked = self.slider.blockSignals(True)
        self.slider.setValue(self._to_int(value))
        self.slider.blockSignals(blocked)

        self.valueChanged.emit(float(value))

    def _on_axis_toggled(self, on):
        """축을 끄면 그 줄의 슬라이더/숫자를 회색으로 — 값이 안 쓰인다는 표시.

        줄(Scale/Move/Rotate) 자체가 꺼져 있으면 축 체크박스도 비활성이므로, 그 상태를
        그대로 따른다(Reset 이 축을 다시 켜도 꺼진 줄이 살아나지 않게).
        """
        enabled = bool(on) and self.check.isEnabled()
        self.slider.setEnabled(enabled)
        self.spin.setEnabled(enabled)

    # ------------------------------------------------------------------
    # 값
    # ------------------------------------------------------------------

    def is_checked(self):
        return self.check.isChecked()

    def value(self):
        return float(self.spin.value())

    def set_value(self, value, silent=True):
        """슬라이더/스핀박스를 함께 맞춘다. silent=True 면 valueChanged 를 내지 않는다."""
        value = float(value)
        self._grow_range(value)

        s_blocked = self.slider.blockSignals(True)
        p_blocked = self.spin.blockSignals(True)

        self.spin.setValue(value)
        self.slider.setValue(self._to_int(self.spin.value()))

        self.slider.blockSignals(s_blocked)
        self.spin.blockSignals(p_blocked)

        if not silent:
            self.valueChanged.emit(float(self.spin.value()))

    def set_row_enabled(self, on):
        """줄(Scale/Move/Rotate) 자체가 꺼지면 축 체크박스까지 전부 비활성."""
        self.check.setEnabled(on)
        self.slider.setEnabled(on and self.check.isChecked())
        self.spin.setEnabled(on and self.check.isChecked())

    def reset(self):
        """값과 슬라이더 범위를 기본으로 되돌린다."""
        self.check.setChecked(True)
        self.slider.setMinimum(self._to_int(self.home_range[0]))
        self.slider.setMaximum(self._to_int(self.home_range[1]))
        self.set_value(self.neutral)


class _XformRow(object):
    """Scale / Move / Rotate 한 묶음 — 켜기 체크박스 + 축 슬라이더 3줄."""

    def __init__(self, label, tip, neutral, decimals, step, minimum, maximum,
                 slider_min, slider_max, slider_step):
        self.neutral = neutral

        self.enable = QCheckBox(label)
        self.enable.setToolTip(tip)

        self.axis_rows = []

        for axis in AXIS_LABELS:
            entry = _AxisSlider(
                axis, neutral=neutral, decimals=decimals, spin_step=step,
                spin_min=minimum, spin_max=maximum,
                slider_min=slider_min, slider_max=slider_max,
                slider_step=slider_step,
                axis_tip="Apply {0} on the {1} axis. Unticked = this axis is "
                         "left alone.".format(label, axis))
            self.axis_rows.append(entry)

        self.enable.toggled.connect(self._on_enable)
        self._on_enable(self.enable.isChecked())

    # ------------------------------------------------------------------

    def _on_enable(self, on):
        for entry in self.axis_rows:
            entry.set_row_enabled(on)

    def values(self):
        """켜 둔 축은 입력값, 끈 축은 중립값. 줄 자체가 꺼져 있으면 None."""
        if not self.enable.isChecked():
            return None

        return tuple(entry.value() if entry.is_checked() else self.neutral
                     for entry in self.axis_rows)

    def reset(self):
        for entry in self.axis_rows:
            entry.reset()


class ShapeTransformTab(QWidget):
    """커브 셰이프 변환 탭. 로그는 툴 창의 것을 그대로 쓴다(log_callback)."""

    def __init__(self, log_callback=None, parent=None):
        super(ShapeTransformTab, self).__init__(parent)

        self._log = log_callback or (lambda text: None)

        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)

        note = QLabel(
            "Resize, move and rotate the curve shape itself, around each curve's\n"
            "own pivot - the same result as picking all of its CVs and using the\n"
            "Scale / Move / Rotate tool. The transform channels are not touched.")
        note.setAlignment(Qt.AlignCenter)
        root.addWidget(note)

        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Curves", select_label="List Selected Curves",
            show_sort=False, list_min_height=150, log_callback=self._log)
        root.addWidget(self.tsl, 1)

        root.addWidget(self._build_xform_group())

        btn_row = QHBoxLayout()

        self.btn_apply = QPushButton("Apply to Shapes")
        self.btn_apply.setMinimumHeight(32)
        self.btn_apply.setToolTip(
            "Apply the ticked rows to every listed curve, each around its own "
            "pivot.\nClick again to apply once more (scale multiplies, move and "
            "rotate add up).\nOne undo step.")
        self.btn_apply.clicked.connect(self.on_apply)
        btn_row.addWidget(self.btn_apply, 1)

        self.btn_reset = QPushButton("Reset Values")
        self.btn_reset.setToolTip(
            "Put the fields back to scale 1 / move 0 / rotate 0, and the sliders "
            "back to their\ndefault range. The curves in the scene are not changed.")
        self.btn_reset.clicked.connect(self.on_reset)
        btn_row.addWidget(self.btn_reset)

        root.addLayout(btn_row)

        return self

    def _build_xform_group(self):
        box = QGroupBox("Shape Transform (about each curve's pivot)")
        outer = QVBoxLayout(box)

        slider_tip = ("Drag to set the value. The slider covers the range you "
                      "normally work in;\ntyping a bigger number in the box "
                      "extends it. Nothing changes in the scene\nuntil you press "
                      "'Apply to Shapes'.")

        self.row_scale = _XformRow(
            "Scale", "Grow or shrink the shape around the pivot. 1 = no change, "
            "2 = twice as big,\n0.5 = half. A negative value mirrors the shape on "
            "that axis.",
            neutral=1.0, decimals=3, step=0.1, minimum=-1000.0, maximum=1000.0,
            slider_min=0.0, slider_max=5.0, slider_step=0.01)
        self.row_move = _XformRow(
            "Move", "Slide the shape away from the pivot, in the curve's own axes "
            "(scene units).",
            neutral=0.0, decimals=3, step=0.1, minimum=-100000.0, maximum=100000.0,
            slider_min=-10.0, slider_max=10.0, slider_step=0.01)
        self.row_rotate = _XformRow(
            "Rotate", "Turn the shape around the pivot, in degrees (XYZ order), "
            "in the curve's own axes.",
            neutral=0.0, decimals=3, step=5.0, minimum=-3600.0, maximum=3600.0,
            slider_min=-180.0, slider_max=180.0, slider_step=0.5)

        # Uniform 은 Scale 줄에만 붙는다 - 머리 줄에 함께 둔다.
        self.chk_uniform = QCheckBox("Uniform")
        self.chk_uniform.setChecked(True)
        self.chk_uniform.setToolTip(
            "Scale only: set one axis - by slider or by number - and the other "
            "ticked axes follow.\nUntick to scale each axis by a different amount.")

        for entry in (self.row_scale, self.row_move, self.row_rotate):
            head = QHBoxLayout()
            head.addWidget(entry.enable)
            if entry is self.row_scale:
                head.addWidget(self.chk_uniform)
            head.addStretch(1)
            outer.addLayout(head)

            for axis_row in entry.axis_rows:
                axis_row.slider.setToolTip(slider_tip)
                outer.addWidget(axis_row)

        # 기본은 크기 조절만. 켜 둔 줄만 적용된다.
        self.row_scale.enable.setChecked(True)
        self.row_move.enable.setChecked(False)
        self.row_rotate.enable.setChecked(False)

        for index, axis_row in enumerate(self.row_scale.axis_rows):
            axis_row.valueChanged.connect(
                lambda value, i=index: self._on_scale_value(i, value))

        return box

    # ==================================================================
    # 동작
    # ==================================================================

    def _on_scale_value(self, index, value):
        """Uniform 이면 방금 정한 값(슬라이더든 숫자든)을 켜 둔 다른 축에도 넣는다."""
        if not self.chk_uniform.isChecked():
            return

        for other, axis_row in enumerate(self.row_scale.axis_rows):
            if other == index or not axis_row.is_checked():
                continue
            if abs(axis_row.value() - value) < 1e-9:
                continue

            # 되먹임(서로가 서로를 다시 세팅)을 막으려고 신호 없이 넣는다.
            axis_row.set_value(value)

    def _nodes(self):
        """TSL 에 담긴 노드들. UUID 로 지금 이름을 되찾는다(리네임·리페어런트 안전)."""
        return self.tsl.get_all_nodes() or self.tsl.get_all_items()

    @staticmethod
    def _fmt(values):
        return "({0})".format(", ".join("{0:g}".format(v) for v in values))

    def on_reset(self):
        self.row_scale.reset()
        self.row_move.reset()
        self.row_rotate.reset()
        self._log("Shape Transform values reset (scale 1 / move 0 / rotate 0).")

    def on_apply(self):
        nodes = self._nodes()
        if not nodes:
            self._log("[WARN] Curve list is empty - select curve(s) in the scene "
                      "and click 'List Selected Curves'.")
            return

        scale = self.row_scale.values()
        move = self.row_move.values()
        rotate = self.row_rotate.values()

        if scale is None and move is None and rotate is None:
            self._log("[WARN] Nothing is ticked - tick Scale, Move or Rotate first.")
            return

        if xform_mgr.is_identity(scale, rotate, move):
            self._log("[WARN] The ticked values do nothing (scale 1 / move 0 / "
                      "rotate 0). Change a value first.")
            return

        try:
            with undo_chunk():
                changed, skipped = xform_mgr.transform_shapes(
                    nodes, scale=scale, rotate=rotate, translate=move)
        except Exception as exc:                            # noqa: BLE001
            self._log("[WARN] Shape transform failed: {0}".format(exc))
            return

        parts = []
        if scale is not None:
            parts.append("scale " + self._fmt(scale))
        if rotate is not None:
            parts.append("rotate " + self._fmt(rotate))
        if move is not None:
            parts.append("move " + self._fmt(move))

        self._log("Shape transform on {0} shape(s) about their own pivot: {1}".format(
            len(changed), ", ".join(parts)))

        if skipped:
            details = ", ".join("{0} ({1})".format(name, why) for name, why in skipped)
            self._log("[WARN] Skipped {0}: {1}".format(len(skipped), details))
