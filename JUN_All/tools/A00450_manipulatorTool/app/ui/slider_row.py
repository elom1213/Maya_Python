# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00450_manipulatorTool - 라벨 + 슬라이더 + 스핀박스 한 줄 위젯
#
# QSlider 는 정수만 다루므로 1/step 배로 확대해서 정수 칸으로 쓴다(step=0.1 -> 10배).
# 슬라이더와 스핀박스는 서로의 신호로 되쓰기 때문에, 갱신할 때는 항상 blockSignals 로 막는다.

from Framework.qt.qt import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QDoubleSpinBox,
    Qt,
    Signal,
)


# 테마 qss 는 QSlider 를 꾸미지 않아 어두운 배경에서 홈(groove)이 묻힌다(핸들만 보임).
# brown_dark 의 accent(#ad9276)에 맞춰 홈·핸들을 직접 그린다.
SLIDER_STYLE = (
    "QSlider:horizontal { min-height: 20px; }"
    "QSlider::groove:horizontal {"
    " height: 6px; margin: 0 4px;"
    " background: #38352f; border: 1px solid #ad9276; border-radius: 3px; }"
    "QSlider::sub-page:horizontal {"
    " background: #5f5449; border: 1px solid #ad9276; border-radius: 3px; }"
    "QSlider::add-page:horizontal {"
    " background: #38352f; border: 1px solid #ad9276; border-radius: 3px; }"
    "QSlider::handle:horizontal {"
    " width: 12px; margin: -6px 0;"
    " background: #cbb79c; border: 1px solid #ad9276; border-radius: 3px; }"
    "QSlider::handle:horizontal:hover { background: #ffffff; }"
)


class SliderRow(QWidget):
    """label + slider + spin box. 슬라이더를 끄는 동안 valueChanged 가 계속 나간다(라이브)."""

    valueChanged = Signal(float)

    def __init__(self, label, minimum, maximum, step=0.1, label_width=64, parent=None):

        super(SliderRow, self).__init__(parent)

        self.step = float(step)
        self.minimum = float(minimum)
        self.maximum = float(maximum)

        self._label_text = label

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.label = QLabel(label)
        self.label.setFixedWidth(label_width)
        row.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self._to_int(self.minimum))
        self.slider.setMaximum(self._to_int(self.maximum))
        self.slider.setStyleSheet(SLIDER_STYLE)
        self.slider.valueChanged.connect(self._on_slider)
        row.addWidget(self.slider, stretch=1)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(self.minimum, self.maximum)
        self.spin.setSingleStep(self.step)
        self.spin.setDecimals(self._decimals())
        self.spin.setFixedWidth(66)

        # 타이핑 도중 값이 되쓰이면 "0.1" 이 "0.100" 으로 잘리므로 편집이 끝날 때만 신호를 받는다.
        self.spin.setKeyboardTracking(False)
        self.spin.valueChanged.connect(self._on_spin)

        row.addWidget(self.spin)

    # ------------------------------------------------------------------
    # 단위 변환
    # ------------------------------------------------------------------

    def _to_int(self, value):
        return int(round(float(value) / self.step))

    def _to_float(self, value):
        return float(value) * self.step

    def _decimals(self):
        return 2 if self.step < 0.1 else 1

    # ------------------------------------------------------------------
    # 신호
    # ------------------------------------------------------------------

    def _on_slider(self, int_value):

        value = self._to_float(int_value)

        self.spin.blockSignals(True)
        self.spin.setValue(value)
        self.spin.blockSignals(False)

        self.valueChanged.emit(value)

    def _on_spin(self, value):

        self.slider.blockSignals(True)
        self.slider.setValue(self._to_int(value))
        self.slider.blockSignals(False)

        self.valueChanged.emit(float(value))

    # ------------------------------------------------------------------
    # 값
    # ------------------------------------------------------------------

    def value(self):
        return float(self.spin.value())

    def set_value(self, value, silent=True):
        """silent=True 면 valueChanged 를 내지 않는다(마야 값 -> UI 반영용)."""
        value = max(self.minimum, min(self.maximum, float(value)))

        self.slider.blockSignals(True)
        self.spin.blockSignals(True)

        self.slider.setValue(self._to_int(value))
        self.spin.setValue(value)

        self.slider.blockSignals(False)
        self.spin.blockSignals(False)

        if not silent:
            self.valueChanged.emit(value)

    # ------------------------------------------------------------------
    # 강조 (활성 도구 표시)
    # ------------------------------------------------------------------

    def set_active(self, active):
        """지금 마야에서 활성인 도구의 줄을 굵게 + accent 색으로 표시한다."""
        if active:
            self.label.setText("\u25b8 " + self._label_text)
            self.label.setStyleSheet("color: #cbb79c; font-weight: bold;")
        else:
            self.label.setText(self._label_text)
            self.label.setStyleSheet("")
