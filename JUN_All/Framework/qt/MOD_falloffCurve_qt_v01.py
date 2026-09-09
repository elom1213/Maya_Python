# -*- coding: utf-8 -*-
"""
JUN_mod_falloffCurve_qt_v01 - 재사용 PySide **falloff 커브** 편집기.

마야 Soft Select / Paint 툴의 "Falloff curve" 를 흉내낸 위젯. 마야의
`gradientControlNoAttr` 은 cmds 전용 컨트롤이라 PySide 창에 그대로 못 쓴다.

  - 가로 = 0~1 로 정규화된 축(툴마다 뜻이 다르다), 세로 = 그 자리의 값(0~1)
  - 포인트 드래그로 모양 조절, 빈 곳 더블클릭으로 추가, 우클릭으로 삭제
  - 양 끝 포인트는 x 가 고정(0 / 1)이고 세로로만 움직인다 — 마야와 같다
  - 포인트를 클릭해 고르면 **X / Y 를 숫자로 직접 입력**할 수 있다(패널의 `Point` 줄).
    드래그로는 "대충 0.1" 을 맞추기 어렵다 — 정확한 값이 필요한 작업(예: A00410 에서
    팁 배수를 정확히 0.1 로)에서는 숫자 입력이 유일한 방법이다.

값 계산은 **`Framework.core.falloff_curve`** 가 한다. 위젯(그리기)과 툴의 계산 로직이
**같은 함수**를 써야 화면 모양과 실제 결과가 어긋나지 않는다. 이 파일은 그리기/입력만 맡는다.

클래스 셋
--------
| 클래스 | 무엇 |
|--------|------|
| `JUN_mod_falloffCurve_qt_v01`       | 커브 캔버스(그리기 + 편집) |
| `JUN_mod_falloffCurvePanel_qt_v01`  | 캔버스 + **Point(X/Y 숫자 입력)** + **Interpolation** 콤보 + **Curve presets** 버튼 |
| `JUN_mod_falloffCurveDialog_qt_v01` | 패널을 담은 **비모달 팝업**(+ Reset / Close) |

패널을 쓰면 콤보와 커브를 맞춰 두는 동기화(프리셋이 보간까지 바꾼다)를 툴이 직접 하지
않아도 된다 — 승격 전 A00275 가 손으로 하던 일이다.

쓰는 법
------
    from Framework.qt import JUN_mod_falloffCurve_qt as JUN_falloff_qt
    from Framework.core import falloff_curve

    # (a) 탭 안에 박아 쓰기
    self.panel = JUN_falloff_qt.JUN_mod_falloffCurvePanel_qt_v01(title="Falloff curve")
    self.panel.changed.connect(self._on_curve_changed)
    layout.addWidget(self.panel)
    pts, interp = self.panel.points(), self.panel.interpolation()

    # (b) 버튼으로 띄우는 팝업 (커브가 **배수**라 기본이 평평한 툴)
    dlg = JUN_falloff_qt.JUN_mod_falloffCurveDialog_qt_v01(
        self, title="Stiffness curve",
        points=falloff_curve.FLAT_POINTS, interp=falloff_curve.FLAT_INTERP,
        info="X = chain root -> tip.   Y multiplies Stiffness.")
    dlg.changed.connect(self._schedule)
    dlg.show()          # 비모달 — 띄워 둔 채로 다른 값을 만질 수 있다

    # (c) 코드로 포인트 값을 정하기 — 화면의 X / Y 숫자 칸이 하는 일과 같다
    dlg.set_selected_index(1)              # 두 번째 포인트를 고르고
    dlg.set_point(1, x=1.0, y=0.1)         # 정확한 값으로 (범위는 알아서 클램프)

값을 읽는 쪽은 `points()` / `interpolation()` 을 그대로 `falloff_curve.evaluate()` 에 넘긴다.
"""

from Framework.qt.qt import *

from Framework.core import falloff_curve


# 포인트를 집을 수 있는 반경(픽셀).
GRAB_RADIUS = 8
# 커브 곡선을 그릴 샘플 수.
SAMPLE_COUNT = 96


class JUN_mod_falloffCurve_qt_v01(QWidget):
    """falloff 커브 캔버스.

    - `changed`          : 커브 모양이 바뀌었다
    - `selectionChanged` : 고른 포인트가 달라졌다(패널의 숫자 입력이 이걸 따라간다)
    """

    changed = Signal()
    selectionChanged = Signal()

    def __init__(self, parent=None, points=None, interp=None, tooltip=None):
        super(JUN_mod_falloffCurve_qt_v01, self).__init__(parent)

        self._points = falloff_curve.normalize_points(
            points if points is not None else falloff_curve.DEFAULT_POINTS)
        self._interp = interp if interp in falloff_curve.INTERPOLATIONS \
            else falloff_curve.DEFAULT_INTERP
        self._drag_index = None
        # 클릭으로 고른 포인트. 드래그가 끝나도 남는다(숫자로 계속 편집하기 위해).
        self._selected = None

        self.setMinimumHeight(110)
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setToolTip(tooltip or (
            "Falloff curve: X = normalised axis, Y = value.\n"
            "Drag a point to reshape, double-click to add, right-click to remove.\n"
            "The first and last points only move vertically.\n"
            "Click a point to select it, then type exact X / Y values below."))

    # ------------------------------------------------------------ 값 API

    def points(self):
        return [tuple(p) for p in self._points]

    def interpolation(self):
        return self._interp

    def set_points(self, points, quiet=False):
        self._points = falloff_curve.normalize_points(points)
        self._clamp_selection()
        self.update()
        if not quiet:
            self.changed.emit()

    def set_interpolation(self, interp, quiet=False):
        if interp not in falloff_curve.INTERPOLATIONS:
            interp = falloff_curve.DEFAULT_INTERP
        self._interp = interp
        self.update()
        if not quiet:
            self.changed.emit()

    def set_curve(self, points, interp, quiet=False):
        """포인트와 보간을 **한 번에** 바꾼다(시그널도 한 번만 나간다)."""
        self._points = falloff_curve.normalize_points(points)
        if interp in falloff_curve.INTERPOLATIONS:
            self._interp = interp
        self._clamp_selection()
        self.update()
        if not quiet:
            self.changed.emit()

    def set_preset(self, name, quiet=False):
        points, interp = falloff_curve.preset_points(name)
        self.set_curve(points, interp, quiet=quiet)

    def evaluate(self, t):
        return falloff_curve.evaluate(self._points, self._interp, t)

    def is_flat(self, value=1.0):
        return falloff_curve.is_flat(self._points, self._interp, value)

    # ------------------------------------------------------- 포인트 선택 / 숫자 편집

    def count(self):
        return len(self._points)

    def selected_index(self):
        """고른 포인트의 인덱스. 없으면 None."""
        return self._selected

    def selected_point(self):
        """고른 포인트의 (x, y). 없으면 None."""
        if self._selected is None:
            return None
        return tuple(self._points[self._selected])

    def set_selected_index(self, index, quiet=False):
        if index is not None:
            index = int(index)
            if not (0 <= index < len(self._points)):
                index = None
        if index == self._selected:
            return
        self._selected = index
        self.update()
        if not quiet:
            self.selectionChanged.emit()

    def is_end_point(self, index):
        """양 끝 포인트인가 — x 가 0 / 1 로 고정이라 세로로만 움직인다."""
        return index is not None and (index == 0 or index == len(self._points) - 1)

    def x_bounds(self, index):
        """그 포인트가 가질 수 있는 x 범위 (lo, hi).

        드래그와 **같은 규칙**이다 — 이웃을 넘어가면 정렬이 흐트러져 보간이 튄다.
        """
        if index is None or not (0 <= index < len(self._points)):
            return (0.0, 1.0)
        if index == 0:
            return (0.0, 0.0)
        if index == len(self._points) - 1:
            return (1.0, 1.0)
        return (self._points[index - 1][0] + 1e-4,
                self._points[index + 1][0] - 1e-4)

    def set_point(self, index, x=None, y=None, quiet=False):
        """포인트 하나를 **숫자로** 지정한다(x 나 y 만 줘도 된다).

        범위 규칙은 드래그와 같다: 양 끝은 x 고정, 가운데는 이웃 사이로 가둔다.
        반환: 실제로 적용된 (x, y).
        """
        if index is None or not (0 <= index < len(self._points)):
            return None
        cur_x, cur_y = self._points[index]
        new_x = cur_x if x is None else falloff_curve.clamp01(float(x))
        new_y = cur_y if y is None else falloff_curve.clamp01(float(y))

        lo, hi = self.x_bounds(index)
        new_x = min(max(new_x, lo), hi)

        if abs(new_x - cur_x) < 1e-12 and abs(new_y - cur_y) < 1e-12:
            return (cur_x, cur_y)

        self._points[index] = (new_x, new_y)
        self.update()
        if not quiet:
            self.changed.emit()
        return (new_x, new_y)

    def _clamp_selection(self):
        """포인트 목록이 바뀌면(프리셋 등) 선택이 범위를 벗어날 수 있다."""
        if self._selected is not None and self._selected >= len(self._points):
            self._selected = len(self._points) - 1 if self._points else None

    # ------------------------------------------------------- 좌표 변환

    def _plot_rect(self):
        """커브를 그리는 안쪽 사각형(테두리 여백을 뺀 영역)."""
        margin = 6
        return QRectF(margin, margin,
                      max(1.0, self.width() - margin * 2.0),
                      max(1.0, self.height() - margin * 2.0))

    def _to_screen(self, x, y):
        rect = self._plot_rect()
        return QPointF(rect.left() + x * rect.width(),
                       rect.bottom() - y * rect.height())

    def _to_value(self, pos):
        rect = self._plot_rect()
        x = (pos.x() - rect.left()) / rect.width()
        y = (rect.bottom() - pos.y()) / rect.height()
        return falloff_curve.clamp01(x), falloff_curve.clamp01(y)

    def _index_at(self, pos):
        for i, (x, y) in enumerate(self._points):
            screen = self._to_screen(x, y)
            if (abs(screen.x() - pos.x()) <= GRAB_RADIUS and
                    abs(screen.y() - pos.y()) <= GRAB_RADIUS):
                return i
        return None

    # ------------------------------------------------------------ 그리기

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self._plot_rect()
        palette = self.palette()
        base = palette.color(QPalette.Base)
        text = palette.color(QPalette.Text)

        painter.fillRect(self.rect(), base.darker(115))
        painter.setPen(QPen(text.darker(160), 1))
        painter.drawRect(rect)

        # 격자 (4x4)
        grid = QPen(text.darker(220), 1, Qt.DotLine)
        painter.setPen(grid)
        for k in range(1, 4):
            f = k / 4.0
            painter.drawLine(self._to_screen(f, 0.0), self._to_screen(f, 1.0))
            painter.drawLine(self._to_screen(0.0, f), self._to_screen(1.0, f))

        # 커브 + 아래 채움
        samples = falloff_curve.sample(self._points, self._interp, SAMPLE_COUNT)
        path = QPainterPath()
        fill = QPainterPath()
        fill.moveTo(self._to_screen(0.0, 0.0))
        for i, (t, value) in enumerate(samples):
            point = self._to_screen(t, value)
            if i == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
            fill.lineTo(point)
        fill.lineTo(self._to_screen(1.0, 0.0))
        fill.closeSubpath()

        accent = palette.color(QPalette.Highlight)
        shade = QColor(accent)
        shade.setAlpha(70)
        painter.fillPath(fill, shade)
        painter.setPen(QPen(accent, 2))
        painter.drawPath(path)

        # 컨트롤 포인트. 고른 포인트는 채우고 한 칸 크게 그린다 — 숫자 입력이
        # **어느 포인트를 건드리는지**가 화면에서 보여야 한다.
        for i, (x, y) in enumerate(self._points):
            center = self._to_screen(x, y)
            active = (i == self._drag_index or i == self._selected)
            painter.setPen(QPen(accent if i == self._selected else text,
                                2 if i == self._selected else 1))
            painter.setBrush(QBrush(accent if active else base))
            half = 5 if i == self._selected else 4
            painter.drawRect(QRectF(center.x() - half, center.y() - half,
                                    half * 2, half * 2))

        painter.end()

    # ------------------------------------------------------------ 입력

    def mousePressEvent(self, event):
        pos = event.position() if hasattr(event, "position") else event.pos()
        pos = QPointF(pos)
        index = self._index_at(pos)

        if event.button() == Qt.RightButton:
            # 끝점 두 개는 남겨 둔다(커브가 사라지면 편집 불가).
            if index is not None and 0 < index < len(self._points) - 1:
                del self._points[index]
                if self._selected is not None:
                    if self._selected == index:
                        self._selected = None
                    elif self._selected > index:
                        self._selected -= 1
                self.update()
                self.selectionChanged.emit()
                self.changed.emit()
            return

        if event.button() == Qt.LeftButton:
            self._drag_index = index
            if index != self._selected:
                self._selected = index
                self.selectionChanged.emit()
            self.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        pos = event.position() if hasattr(event, "position") else event.pos()
        pos = QPointF(pos)
        if self._index_at(pos) is not None:
            return
        x, y = self._to_value(pos)
        self._points.append((x, y))
        self._points = falloff_curve.normalize_points(self._points)
        self._drag_index = self._points.index((x, y)) if (x, y) in self._points else None
        # 방금 만든 포인트를 고른 상태로 둔다 — 바로 숫자로 다듬을 수 있게.
        self._selected = self._drag_index
        self.update()
        self.selectionChanged.emit()
        self.changed.emit()

    def mouseMoveEvent(self, event):
        if self._drag_index is None:
            return
        pos = event.position() if hasattr(event, "position") else event.pos()
        x, y = self._to_value(QPointF(pos))

        index = self._drag_index
        if index == 0:
            x = 0.0
        elif index == len(self._points) - 1:
            x = 1.0
        else:
            # 이웃을 넘어가지 않게 가둔다(정렬이 흐트러지면 보간이 튄다).
            left = self._points[index - 1][0]
            right = self._points[index + 1][0]
            x = min(max(x, left + 1e-4), right - 1e-4)

        self._points[index] = (x, y)
        self.update()
        self.changed.emit()

    def mouseReleaseEvent(self, event):
        if self._drag_index is not None:
            self._drag_index = None
            self.update()


class JUN_mod_falloffCurvePanel_qt_v01(QWidget):
    """커브 캔버스 + `Point`(X/Y 숫자 입력) + `Interpolation` 콤보 + `Curve presets` 버튼.

    프리셋은 **보간 방식까지** 바꾸므로, 커브가 어느 경로로 바뀌든 콤보를 맞춰 두어야
    화면 표기와 실제 계산이 어긋나지 않는다. 그 동기화를 이 패널이 맡는다.

    `Point` 줄은 캔버스에서 고른 포인트의 **X / Y 를 숫자로** 편집한다. 드래그로는
    "정확히 0.1" 을 맞출 수 없으므로, 값이 결과에 그대로 곱해지는 툴에서는 이쪽이 본길이다.
    아무것도 안 골랐으면 회색으로 꺼져 있다 — "비활성인데 값은 쓰인다" 는 상태를 만들지 않는다.
    """

    changed = Signal()
    selectionChanged = Signal()

    def __init__(self, parent=None, title="Falloff curve", points=None, interp=None,
                 presets=None, show_title=True, show_interp=True, show_presets=True,
                 show_point_fields=True, decimals=3, tooltip=None):
        super(JUN_mod_falloffCurvePanel_qt_v01, self).__init__(parent)

        self._presets = list(presets) if presets else list(falloff_curve.PRESETS)
        # 숫자 칸 -> 커브 -> 숫자 칸 되먹임을 막는 빗장.
        self._updating = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        curve_row = QHBoxLayout()
        if show_title and title:
            lbl = QLabel(title)
            lbl.setAlignment(Qt.AlignTop)
            curve_row.addWidget(lbl)
        self.curve = JUN_mod_falloffCurve_qt_v01(
            points=points, interp=interp, tooltip=tooltip)
        curve_row.addWidget(self.curve, 1)
        lay.addLayout(curve_row)

        # ---- Point : 고른 포인트를 숫자로
        self.sb_point_x = None
        self.sb_point_y = None
        self.lbl_point = None
        if show_point_fields:
            point_row = QHBoxLayout()
            point_row.addWidget(QLabel("Point"))
            self.lbl_point = QLabel("-")
            self.lbl_point.setMinimumWidth(52)
            self.lbl_point.setToolTip(
                "Which point the X / Y fields edit. Click a point on the curve.")
            point_row.addWidget(self.lbl_point)

            point_row.addWidget(QLabel("X"))
            self.sb_point_x = self._make_spin(decimals)
            self.sb_point_x.setToolTip(
                "X of the selected point.\n"
                "The first and last points are pinned to 0 / 1, and a middle point\n"
                "cannot pass its neighbours - the value is clamped to that range.")
            self.sb_point_x.valueChanged.connect(self._on_point_x)
            point_row.addWidget(self.sb_point_x)

            point_row.addWidget(QLabel("Y"))
            self.sb_point_y = self._make_spin(decimals)
            self.sb_point_y.setToolTip("Y (value) of the selected point.")
            self.sb_point_y.valueChanged.connect(self._on_point_y)
            point_row.addWidget(self.sb_point_y)

            point_row.addStretch(1)
            lay.addLayout(point_row)

        self.cmb_interp = None
        if show_interp:
            interp_row = QHBoxLayout()
            interp_row.addWidget(QLabel("Interpolation"))
            self.cmb_interp = QComboBox()
            for name in falloff_curve.INTERPOLATIONS:
                self.cmb_interp.addItem(name.capitalize())
            self.cmb_interp.setCurrentIndex(
                list(falloff_curve.INTERPOLATIONS).index(self.curve.interpolation()))
            self.cmb_interp.currentIndexChanged.connect(
                lambda i: self.curve.set_interpolation(
                    falloff_curve.INTERPOLATIONS[i]))
            interp_row.addWidget(self.cmb_interp)
            interp_row.addStretch(1)
            lay.addLayout(interp_row)

        if show_presets and self._presets:
            preset_row = QHBoxLayout()
            preset_row.addWidget(QLabel("Curve presets"))
            for label, _points, _interp in self._presets:
                btn = QPushButton(label)
                btn.setToolTip("Load the '{0}' curve.".format(label))
                btn.clicked.connect(
                    lambda _checked=False, name=label: self.set_preset(name))
                preset_row.addWidget(btn)
            preset_row.addStretch(1)
            lay.addLayout(preset_row)

        self.curve.changed.connect(self._on_curve_changed)
        self.curve.selectionChanged.connect(self._on_selection_changed)
        self._sync_point_fields()

    @staticmethod
    def _make_spin(decimals):
        sb = QDoubleSpinBox()
        sb.setDecimals(decimals)
        sb.setRange(0.0, 1.0)
        sb.setSingleStep(0.05)
        sb.setMaximumWidth(78)
        # 값을 되쓰는 칸이라 타이핑 중간값을 받으면 안 된다(0.1 -> 0.100 으로 잘린다).
        sb.setKeyboardTracking(False)
        return sb

    # ------------------------------------------------------------ 값 API
    # (캔버스에 그대로 넘긴다 — 호출부는 패널만 알면 된다)

    def points(self):
        return self.curve.points()

    def interpolation(self):
        return self.curve.interpolation()

    def set_points(self, points, quiet=False):
        self.curve.set_points(points, quiet=quiet)
        self._sync_combo()

    def set_interpolation(self, interp, quiet=False):
        self.curve.set_interpolation(interp, quiet=quiet)
        self._sync_combo()

    def set_curve(self, points, interp, quiet=False):
        self.curve.set_curve(points, interp, quiet=quiet)
        self._sync_combo()

    def set_preset(self, name, quiet=False):
        for label, points, interp in self._presets:
            if label == name:
                self.set_curve(points, interp, quiet=quiet)
                return
        self.set_curve(*falloff_curve.preset_points(name), quiet=quiet)

    def evaluate(self, t):
        return self.curve.evaluate(t)

    def is_flat(self, value=1.0):
        return self.curve.is_flat(value)

    # ------------------------------------------------- 포인트 선택 / 숫자 편집(위임)

    def selected_index(self):
        return self.curve.selected_index()

    def selected_point(self):
        return self.curve.selected_point()

    def set_selected_index(self, index, quiet=False):
        self.curve.set_selected_index(index, quiet=quiet)

    def set_point(self, index, x=None, y=None, quiet=False):
        applied = self.curve.set_point(index, x=x, y=y, quiet=quiet)
        self._sync_point_fields()
        return applied

    # ------------------------------------------------------------ 내부

    def _on_curve_changed(self):
        self._sync_combo()
        self._sync_point_fields()
        self.changed.emit()

    def _on_selection_changed(self):
        self._sync_point_fields()
        self.selectionChanged.emit()

    def _on_point_x(self, value):
        if self._updating:
            return
        index = self.curve.selected_index()
        if index is None:
            return
        # 클램프된 값이 칸에 되돌아와야 사용자가 "왜 안 들어가지" 하지 않는다.
        self.curve.set_point(index, x=value)
        self._sync_point_fields()

    def _on_point_y(self, value):
        if self._updating:
            return
        index = self.curve.selected_index()
        if index is None:
            return
        self.curve.set_point(index, y=value)
        self._sync_point_fields()

    def _sync_point_fields(self):
        """고른 포인트의 값을 숫자 칸에 반영(드래그 중에도 따라온다)."""
        if self.sb_point_x is None:
            return

        index = self.curve.selected_index()
        point = self.curve.selected_point()

        self._updating = True
        try:
            if point is None:
                self.lbl_point.setText("-")
                self.sb_point_x.setEnabled(False)
                self.sb_point_y.setEnabled(False)
            else:
                self.lbl_point.setText("{0} / {1}".format(
                    index + 1, self.curve.count()))
                # 양 끝은 x 가 0 / 1 로 고정이라 X 칸을 꺼 둔다(세로로만 움직인다).
                end = self.curve.is_end_point(index)
                self.sb_point_x.setEnabled(not end)
                self.sb_point_y.setEnabled(True)
                lo, hi = self.curve.x_bounds(index)
                self.sb_point_x.setRange(lo, hi)
                self.sb_point_x.setValue(point[0])
                self.sb_point_y.setValue(point[1])
        finally:
            self._updating = False

    def _sync_combo(self):
        if self.cmb_interp is None:
            return
        index = list(falloff_curve.INTERPOLATIONS).index(self.curve.interpolation())
        if self.cmb_interp.currentIndex() == index:
            return
        self.cmb_interp.blockSignals(True)
        self.cmb_interp.setCurrentIndex(index)
        self.cmb_interp.blockSignals(False)


class JUN_mod_falloffCurveDialog_qt_v01(QDialog):
    """패널을 담은 **비모달** 커브 팝업.

    비모달인 이유: 커브를 만지면서 툴의 다른 값(슬라이더)도 같이 보고 싶기 때문이다.
    닫아도 값은 남는다(호출부가 인스턴스를 들고 있다가 다시 `show()` 하면 그대로다).
    """

    changed = Signal()

    def __init__(self, parent=None, title="Falloff curve", points=None, interp=None,
                 reset_points=None, reset_interp=None, info="", presets=None,
                 size=(440, 390), tooltip=None):
        super(JUN_mod_falloffCurveDialog_qt_v01, self).__init__(parent)

        self._reset_points = list(
            reset_points if reset_points is not None
            else (points if points is not None else falloff_curve.DEFAULT_POINTS))
        self._reset_interp = (reset_interp if reset_interp is not None
                              else (interp or falloff_curve.DEFAULT_INTERP))

        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Window)
        self.resize(*size)

        lay = QVBoxLayout(self)

        if info:
            lbl = QLabel(info)
            lbl.setWordWrap(True)
            lay.addWidget(lbl)

        self.panel = JUN_mod_falloffCurvePanel_qt_v01(
            title="", points=points, interp=interp, presets=presets,
            show_title=False, tooltip=tooltip)
        self.panel.changed.connect(self.changed.emit)
        lay.addWidget(self.panel, 1)

        btn_row = QHBoxLayout()
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setToolTip("Back to the curve this panel opened with.")
        self.btn_reset.clicked.connect(self.reset)
        btn_row.addWidget(self.btn_reset)
        btn_row.addStretch(1)
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        btn_row.addWidget(self.btn_close)
        lay.addLayout(btn_row)

    # ------------------------------------------------------------ 값 API

    def points(self):
        return self.panel.points()

    def interpolation(self):
        return self.panel.interpolation()

    def set_curve(self, points, interp, quiet=False):
        self.panel.set_curve(points, interp, quiet=quiet)

    def evaluate(self, t):
        return self.panel.evaluate(t)

    def is_flat(self, value=1.0):
        return self.panel.is_flat(value)

    def selected_index(self):
        return self.panel.selected_index()

    def selected_point(self):
        return self.panel.selected_point()

    def set_selected_index(self, index, quiet=False):
        self.panel.set_selected_index(index, quiet=quiet)

    def set_point(self, index, x=None, y=None, quiet=False):
        return self.panel.set_point(index, x=x, y=y, quiet=quiet)

    def reset(self):
        self.panel.set_curve(self._reset_points, self._reset_interp)

    def popup(self):
        """띄우고 앞으로 가져온다(이미 떠 있으면 그 창을 다시 앞으로)."""
        self.show()
        self.raise_()
        self.activateWindow()
        return self
