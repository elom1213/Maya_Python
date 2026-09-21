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
# ── 라이브 (v01.20) ──────────────────────────────────────────────────────
# `Live` 가 켜져 있으면(기본) 슬라이더를 끄는 **그 순간 씬의 커브가 따라 변한다.**
# 한 번의 조작을 `ShapeTransformSession` 이 들고 있다 — 세션이 잡아 둔 **CV 원위치에서
# 매번 다시 계산**하므로 슬라이더를 왕복해도 누적되지 않는다(2배로 키웠다 1.5배로 끌면
# 원본의 1.5배다).
#
# undo 는 코어의 규칙을 그대로 따른다 — 끄는 동안은 **undo 큐에 안 쌓이고**, 손을 떼거나
# 조작이 멎으면(디바운스) 그때까지의 결과가 **한 항목**으로 기록된다. 그래서 드래그 한 번에
# `Ctrl+Z` 한 번이다.
#
# 세션은 **리스트가 바뀌거나 씬이 어긋나면**(사용자가 `Ctrl+Z` 를 눌렀거나 커브를 따로
# 건드렸다) 버리고 새로 만든다. 세션을 닫을 때는 값 칸을 중립으로 되돌린다 — 값을 그대로
# 두면 다음 세션이 **새 원위치에 같은 배율을 다시 걸어** 두 배가 되기 때문이다.
#
# `Apply to Shapes` 는 라이브 중이면 **지금 모양을 확정**만 한다(또 걸지 않는다).
# `Live` 를 끄면 예전처럼 `Apply` 를 눌러야 씬이 바뀐다.

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

    def zero(self):
        """값만 중립으로. 축 체크와 슬라이더 범위는 사용자가 둔 그대로 남긴다."""
        for entry in self.axis_rows:
            entry.set_value(entry.neutral)

    def reset(self):
        for entry in self.axis_rows:
            entry.reset()


class ShapeTransformTab(QWidget):
    """커브 셰이프 변환 탭. 로그는 툴 창의 것을 그대로 쓴다(log_callback)."""

    #: 조작이 멎고 이만큼 지나면 그때까지의 미리보기를 undo 큐에 한 항목으로 기록한다.
    SETTLE_MS = 350

    def __init__(self, log_callback=None, parent=None):
        super(ShapeTransformTab, self).__init__(parent)

        self._log = log_callback or (lambda text: None)

        # 라이브 미리보기 한 세션(슬라이더를 움직이는 동안). 없으면 None.
        self._session = None
        # 세션을 만들 때의 커브 목록 - 리스트가 바뀌면 세션을 새로 만든다.
        self._session_nodes = []
        # 값을 코드가 바꾸는 중인지(사용자 조작과 구분). 켜져 있으면 미리보기를 걸지 않는다.
        self._updating = False

        self.build_ui()

        # 조작이 멎으면 한 번만 기록(디바운스). A00110 Stagger Offset 과 같은 방식.
        self._settle_timer = QTimer(self)
        self._settle_timer.setSingleShot(True)
        self._settle_timer.setInterval(self.SETTLE_MS)
        self._settle_timer.timeout.connect(self._settle)

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

        # 리스트가 바뀌면 라이브 세션을 확정하고 닫는다(세션은 시작 시점의 CV 를 들고 있다).
        model = self.tsl.list_widget.model()
        model.rowsInserted.connect(self._on_list_changed)
        model.rowsRemoved.connect(self._on_list_changed)
        model.modelReset.connect(self._on_list_changed)

        root.addWidget(self._build_xform_group())

        self.chk_live = QCheckBox("Live - the curves follow the sliders")
        self.chk_live.setChecked(True)
        self.chk_live.setToolTip(
            "On (default) : the listed curves change in the scene while you drag,\n"
            "               always recalculated from the shape you started with\n"
            "               (dragging back and forth does not pile up).\n"
            "               The drag itself is not put in the undo queue - when you\n"
            "               stop, the result goes in as ONE undo step.\n"
            "Off          : nothing happens until you press 'Apply to Shapes'.\n"
            "               Worth turning off for a very long curve list.")
        self.chk_live.toggled.connect(self._on_live_toggled)
        root.addWidget(self.chk_live)

        btn_row = QHBoxLayout()

        self.btn_apply = QPushButton("Apply to Shapes")
        self.btn_apply.setMinimumHeight(32)
        self.btn_apply.setToolTip(
            "Live on  : keep the shape you see in the scene and start over from it\n"
            "           (the values go back to 1 / 0 - it is NOT applied twice).\n"
            "Live off : apply the ticked rows to every listed curve, each around its\n"
            "           own pivot. Click again to apply once more (scale multiplies,\n"
            "           move and rotate add up).\n"
            "Either way it is one undo step.")
        self.btn_apply.clicked.connect(self.on_apply)
        btn_row.addWidget(self.btn_apply, 1)

        self.btn_reset = QPushButton("Reset Values")
        self.btn_reset.setToolTip(
            "Put the fields back to scale 1 / move 0 / rotate 0, and the sliders "
            "back to their\ndefault range.\n"
            "While a live drag is going on it also puts the curves back to the "
            "shape they\nhad when the slider was first moved (one undo step).")
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

        # 값·축·줄이 바뀌면 곧바로 씬에 반영한다(라이브가 켜져 있을 때).
        for entry in (self.row_scale, self.row_move, self.row_rotate):
            entry.enable.toggled.connect(self._live_update)
            for axis_row in entry.axis_rows:
                axis_row.valueChanged.connect(self._live_update)
                axis_row.check.toggled.connect(self._live_update)
                # 슬라이더에서 손을 떼면 기다리지 않고 바로 기록한다.
                axis_row.slider.sliderReleased.connect(self._settle)

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

    def _values(self):
        """(scale, rotate, translate) — 꺼진 줄은 None, 끈 축은 중립값."""
        return (self.row_scale.values(),
                self.row_rotate.values(),
                self.row_move.values())

    # ==================================================================
    # 라이브 미리보기 (v01.19)
    # ==================================================================

    def _begin_session(self):
        """지금 리스트로 세션을 준비한다. 만들 수 없으면 None.

        이미 있는 세션이라도 **리스트가 바뀌었거나 씬이 어긋났으면**(사용자가 Ctrl+Z 를
        눌렀거나 커브를 따로 건드렸다) 버리고 새로 만든다 — 낡은 원위치로 계속 쓰면
        사용자가 되돌린 것을 덮어쓰게 된다.
        """
        nodes = self._nodes()
        if not nodes:
            return None

        if self._session is not None:
            if nodes != self._session_nodes:
                # 리스트 신호를 놓친 경우의 대비. 값은 건드리지 않는다 — 지금 이 호출이
                # 사용자가 방금 정한 값이라, 여기서 0 으로 돌리면 그 조작이 사라진다.
                self._close_session(zero=False)
            elif not self._session.scene_in_sync():
                # 씬이 세션의 가정과 다르다 = 밖에서 바뀌었다(사용자 Ctrl+Z 등).
                # 값 칸은 **건드리지 않고** 세션만 버린다 — 지금 씬 모양을 새 원위치로 삼아
                # 사용자가 맞춰 둔 값을 그대로 다시 건다.
                self._settle_timer.stop()
                self._session = None

        if self._session is None:
            session, skipped = xform_mgr.ShapeTransformSession.create(nodes)
            if session is None:
                for name, why in skipped:
                    self._log("[WARN] {0} : {1}".format(name, why))
                return None

            self._session = session
            self._session_nodes = list(nodes)

            for name, why in skipped:
                self._log("[WARN] {0} : {1}".format(name, why))

        return self._session

    def _live_update(self, *_args):
        """값이 바뀔 때마다 씬에 즉시 반영. **원위치에서 다시** 계산하므로 누적되지 않는다.

        기록(undo)은 여기서 하지 않는다 — 조작이 멎으면 타이머가 `_settle` 을 불러
        그때까지의 결과를 **한 항목**으로 기록한다.
        """
        if self._updating or not self.chk_live.isChecked():
            return

        session = self._begin_session()
        if session is None:
            return

        scale, rotate, move = self._values()
        session.preview(scale=scale, rotate=rotate, translate=move)
        self._settle_timer.start()

    def _settle(self):
        """조작이 멎은 시점에 지금까지의 미리보기를 undo 큐에 한 항목으로 기록한다."""
        self._settle_timer.stop()

        session = self._session
        if session is None:
            return

        if not session.scene_in_sync():
            # 밖에서 씬이 바뀌었다. 기록하면 그걸 덮어쓰므로 세션만 버린다.
            self._session = None
            return

        # ★ 위젯이 아니라 **세션이 실제로 씬에 건 값**(applied)을 기록한다.
        #   리스트를 바꾸거나 값을 고치는 순간에도 불릴 수 있어서, 그때 위젯 값은 이미
        #   다음 조작의 값이다 — 그걸 기록하면 엉뚱한 값이 커브에 굳는다.
        scale, rotate, move = session.applied
        _written, msg = session.settle(scale=scale, rotate=rotate, translate=move)
        if msg:
            self._log(msg)

    def _on_list_changed(self, *_args):
        """커브 리스트가 바뀌면 지금 세션을 확정하고 닫는다.

        세션은 시작 시점의 **CV 원위치**를 들고 있으므로 리스트가 바뀌면 더는 맞지 않는다.
        커브는 지금 모양 그대로 남고, 값 칸은 0 으로 돌아가 다음 조작이 **새 리스트의
        지금 모양**에서 시작한다.
        """
        if self._session is not None:
            self._close_session("the curve list changed")

    def _close_session(self, reason="", zero=True):
        """세션을 확정하고 닫는다. 값 칸은 중립으로 돌려 다음 조작이 지금 모양에서 시작하게.

        커브는 **지금 모양 그대로** 남는다. 값을 그대로 두면 다음 세션이 새 원위치에
        같은 배율을 다시 걸어 두 배가 되므로 닫을 때 0 으로 되돌린다 — 다만 지금 들어온
        값 변경 때문에 닫는 경우(`zero=False`)는 그 조작을 지우면 안 되므로 그대로 둔다.
        """
        session = self._session
        if session is None:
            return

        self._settle_timer.stop()

        if session.scene_in_sync():
            # 위젯이 아니라 **세션이 씬에 건 값**을 확정한다(`_settle` 과 같은 이유).
            scale, rotate, move = session.applied
            _written, msg = session.settle(scale=scale, rotate=rotate, translate=move)
            if msg:
                self._log(msg)

        self._session = None
        self._session_nodes = []

        if zero:
            self._zero_values()

        if reason:
            self._log("Live session closed ({0}). The shape stays as it is - the "
                      "values start from 1 / 0 again.".format(reason))

    def _zero_values(self):
        """값 칸만 중립으로(축 체크·슬라이더 범위는 그대로). 미리보기를 다시 걸지 않는다."""
        self._updating = True
        try:
            self.row_scale.zero()
            self.row_move.zero()
            self.row_rotate.zero()
        finally:
            self._updating = False

    def _on_live_toggled(self, on):
        """Live 를 끄면 지금까지의 미리보기를 확정하고 세션을 닫는다."""
        if on:
            return
        if self._session is not None:
            self._close_session("Live switched off")

    @staticmethod
    def _fmt(values):
        return "({0})".format(", ".join("{0:g}".format(v) for v in values))

    # ==================================================================
    # 버튼
    # ==================================================================

    def on_reset(self):
        """값 칸을 기본으로. 라이브로 변형 중이었다면 **커브도 원래 모양으로 되돌린다**."""
        session = self._session

        if session is not None:
            self._settle_timer.stop()
            if session.scene_in_sync():
                written = session.restore()
                if written:
                    self._log("Reset : {0} shape(s) back to the shape they had when "
                              "the slider was first moved (one undo step).".format(
                                  written))
            self._session = None
            self._session_nodes = []

        self._updating = True
        try:
            self.row_scale.reset()
            self.row_move.reset()
            self.row_rotate.reset()
        finally:
            self._updating = False

        self._log("Shape Transform values reset (scale 1 / move 0 / rotate 0).")

    def on_apply(self):
        nodes = self._nodes()
        if not nodes:
            self._log("[WARN] Curve list is empty - select curve(s) in the scene "
                      "and click 'List Selected Curves'.")
            return

        # 라이브로 이미 씬에 들어가 있는 경우: 한 번 더 걸지 않고 **지금 모양을 확정**한다.
        # (여기서 또 적용하면 두 배가 된다)
        if self._session is not None:
            self._close_session("applied")
            self._log("Applied - the curves keep the shape shown in the scene.")
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
