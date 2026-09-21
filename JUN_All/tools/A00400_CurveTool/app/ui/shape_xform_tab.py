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

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from Framework.core.maya_undo import undo_chunk
from tools.A00400_CurveTool.app.core import shape_xform_manager as xform_mgr


#: 값 칸 폭 — 세 축이 한 줄에 들어가도록.
SPIN_WIDTH = 72

#: 축 라벨
AXIS_LABELS = ("X", "Y", "Z")


class _XformRow(object):
    """Scale / Move / Rotate 한 줄 — 켜기 체크박스 + 축 체크박스 3개 + 값 칸 3개."""

    def __init__(self, label, tip, neutral, decimals, step, minimum, maximum):
        self.neutral = neutral

        self.enable = QCheckBox(label)
        self.enable.setToolTip(tip)

        self.axes = []
        self.spins = []

        for axis in AXIS_LABELS:
            check = QCheckBox()
            check.setChecked(True)
            check.setToolTip("Apply {0} on the {1} axis. Unticked = this axis is "
                             "left alone.".format(label, axis))

            spin = QDoubleSpinBox()
            spin.setDecimals(decimals)
            spin.setSingleStep(step)
            spin.setRange(minimum, maximum)
            spin.setValue(neutral)
            spin.setFixedWidth(SPIN_WIDTH)
            # 타이핑 도중(한 글자마다) 값이 튀지 않게 - 엔터/포커스 이동에서만 반영.
            spin.setKeyboardTracking(False)

            self.axes.append(check)
            self.spins.append(spin)

        self.enable.toggled.connect(self._on_enable)
        self._on_enable(self.enable.isChecked())

    # ------------------------------------------------------------------

    def _on_enable(self, on):
        for check, spin in zip(self.axes, self.spins):
            check.setEnabled(on)
            spin.setEnabled(on)

    def cell(self, index):
        """축 한 칸(체크박스 + 값 칸)을 담은 위젯."""
        holder = QWidget()
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.axes[index])
        layout.addWidget(self.spins[index])

        return holder

    def values(self):
        """켜 둔 축은 입력값, 끈 축은 중립값. 줄 자체가 꺼져 있으면 None."""
        if not self.enable.isChecked():
            return None

        return tuple(spin.value() if check.isChecked() else self.neutral
                     for check, spin in zip(self.axes, self.spins))

    def reset(self):
        for check, spin in zip(self.axes, self.spins):
            check.setChecked(True)
            spin.setValue(self.neutral)


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
            "Put the fields back to scale 1 / move 0 / rotate 0. The curves in "
            "the scene are not changed.")
        self.btn_reset.clicked.connect(self.on_reset)
        btn_row.addWidget(self.btn_reset)

        root.addLayout(btn_row)

        return self

    def _build_xform_group(self):
        box = QGroupBox("Shape Transform (about each curve's pivot)")
        grid = QGridLayout(box)

        for column, axis in enumerate(AXIS_LABELS):
            label = QLabel(axis)
            label.setAlignment(Qt.AlignCenter)
            grid.addWidget(label, 0, column + 1)

        self.row_scale = _XformRow(
            "Scale", "Grow or shrink the shape around the pivot. 1 = no change, "
            "2 = twice as big,\n0.5 = half. A negative value mirrors the shape on "
            "that axis.",
            neutral=1.0, decimals=3, step=0.1, minimum=-1000.0, maximum=1000.0)
        self.row_move = _XformRow(
            "Move", "Slide the shape away from the pivot, in the curve's own axes "
            "(scene units).",
            neutral=0.0, decimals=3, step=0.1, minimum=-100000.0, maximum=100000.0)
        self.row_rotate = _XformRow(
            "Rotate", "Turn the shape around the pivot, in degrees (XYZ order), "
            "in the curve's own axes.",
            neutral=0.0, decimals=3, step=5.0, minimum=-3600.0, maximum=3600.0)

        for row, entry in enumerate((self.row_scale, self.row_move, self.row_rotate), start=1):
            grid.addWidget(entry.enable, row, 0)
            for column in range(3):
                grid.addWidget(entry.cell(column), row, column + 1)

        # 기본은 크기 조절만. 켜 둔 줄만 적용된다.
        self.row_scale.enable.setChecked(True)
        self.row_move.enable.setChecked(False)
        self.row_rotate.enable.setChecked(False)

        self.chk_uniform = QCheckBox("Uniform")
        self.chk_uniform.setChecked(True)
        self.chk_uniform.setToolTip(
            "Scale only: type a value in one axis and the other ticked axes "
            "follow.\nUntick to scale each axis by a different amount.")
        grid.addWidget(self.chk_uniform, 1, 4)

        for index, spin in enumerate(self.row_scale.spins):
            spin.valueChanged.connect(
                lambda value, i=index: self._on_scale_value(i, value))

        grid.setColumnStretch(5, 1)

        return box

    # ==================================================================
    # 동작
    # ==================================================================

    def _on_scale_value(self, index, value):
        """Uniform 이면 방금 친 값을 켜 둔 다른 축에도 그대로 넣는다."""
        if not self.chk_uniform.isChecked():
            return

        for other, spin in enumerate(self.row_scale.spins):
            if other == index or not self.row_scale.axes[other].isChecked():
                continue
            if abs(spin.value() - value) < 1e-9:
                continue

            # 되먹임(서로가 서로를 다시 세팅)을 막는다.
            blocked = spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(blocked)

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
