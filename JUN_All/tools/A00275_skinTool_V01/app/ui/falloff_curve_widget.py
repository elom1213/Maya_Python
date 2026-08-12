# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-12
# A00275_skinTool_V01 - falloff 커브 편집 위젯 (Expand Bind 탭)
#
# 마야 Soft Select / Paint 툴의 "Falloff curve"(ref/ref_01.png) 를 흉내낸 위젯.
# 마야의 `gradientControlNoAttr` 은 cmds 전용 컨트롤이라 PySide 창에 그대로 못 쓴다.
#
#   - 가로 = 거리 / 반경 (0 ~ 1), 세로 = 웨이트 비중 (0 ~ 1)
#   - 포인트 드래그로 모양 조절, 빈 곳 더블클릭으로 추가, 우클릭으로 삭제
#   - 양 끝 포인트는 x 가 고정(0 / 1)이고 세로로만 움직인다 — 마야와 같다
#
# 커브 값 계산은 core/falloff.py 가 한다(바인드 로직과 **같은 함수**를 써야 화면과
# 결과가 어긋나지 않는다). 이 파일은 그리기/입력만 맡는다.

from Framework.qt.qt import *

from tools.A00275_skinTool_V01.app.core import falloff


# 포인트를 집을 수 있는 반경(픽셀).
GRAB_RADIUS = 8
# 커브 곡선을 그릴 샘플 수.
SAMPLE_COUNT = 96


class FalloffCurveWidget(QWidget):
    """falloff 커브 편집기. 값이 바뀌면 `changed` 를 낸다."""

    changed = Signal()

    def __init__(self, parent=None):
        super(FalloffCurveWidget, self).__init__(parent)

        self._points = list(falloff.DEFAULT_POINTS)
        self._interp = falloff.DEFAULT_INTERP
        self._drag_index = None

        self.setMinimumHeight(110)
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setToolTip(
            "Falloff curve: X = distance / radius, Y = weight share.\n"
            "Drag a point to reshape, double-click to add, right-click to remove.\n"
            "The first and last points only move vertically.")

    # ------------------------------------------------------------ 값 API

    def points(self):
        return [tuple(p) for p in self._points]

    def interpolation(self):
        return self._interp

    def set_points(self, points, quiet=False):
        self._points = falloff.normalize_points(points)
        self.update()
        if not quiet:
            self.changed.emit()

    def set_interpolation(self, interp, quiet=False):
        if interp not in falloff.INTERPOLATIONS:
            interp = falloff.DEFAULT_INTERP
        self._interp = interp
        self.update()
        if not quiet:
            self.changed.emit()

    def set_preset(self, name, quiet=False):
        points, interp = falloff.preset_points(name)
        self._points = falloff.normalize_points(points)
        self._interp = interp
        self.update()
        if not quiet:
            self.changed.emit()

    def evaluate(self, t):
        return falloff.evaluate(self._points, self._interp, t)

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
        return falloff.clamp01(x), falloff.clamp01(y)

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
        samples = falloff.sample(self._points, self._interp, SAMPLE_COUNT)
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

        # 컨트롤 포인트
        painter.setPen(QPen(text, 1))
        for i, (x, y) in enumerate(self._points):
            center = self._to_screen(x, y)
            painter.setBrush(QBrush(accent if i == self._drag_index else base))
            painter.drawRect(QRectF(center.x() - 4, center.y() - 4, 8, 8))

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
                self.update()
                self.changed.emit()
            return

        if event.button() == Qt.LeftButton:
            self._drag_index = index
            if index is not None:
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
        self._points = falloff.normalize_points(self._points)
        self._drag_index = self._points.index((x, y)) if (x, y) in self._points else None
        self.update()
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
