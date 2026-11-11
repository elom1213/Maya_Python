# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-11
# Framework.qt - Alt + 가운데 버튼 드래그로 리스트 · 트리 뷰를 위아래로 끌어 옮기기 (마야 아웃라이너와 같은 조작)
#
#   JUN_mod_altPan_qt_v01(tree)        # 한 줄. 부모 = 뷰라 따로 들고 있을 필요 없다.
#
# 동작:
#   - **Alt + 가운데 버튼 누른 채 드래그** = 내용이 마우스를 따라 움직인다(잡아 끄는 방향, 마야 아웃라이너와 같다).
#     Alt 는 누를 때만 보면 된다 - 드래그 중에 Alt 를 떼도 버튼을 놓을 때까지 계속.
#   - 그 누르기 · 놓기는 뷰에 넘기지 않는다 → 선택 · 드래그 앤 드롭이 일어나지 않는다.
#   - 스크롤 모드가 항목 단위(ScrollPerItem, QTreeWidget 기본)여도 된다 - 픽셀 이동을 행 높이로 나눠 옮긴다.
#     뷰의 스크롤 모드는 바꾸지 않는다(휠 동작이 그대로).
#   - horizontal=True 면 좌우도 함께(기본 끔 - 아웃라이너는 위아래가 주 용도).
#
# QAbstractScrollArea 계열(QTreeWidget · QListWidget · QTableWidget · QTreeView ...) 공용.

from Framework.qt.qt import (
    Qt,
    QObject,
    QEvent,
    QPoint,
    QAbstractItemView,
)


def _pos(event):
    """마우스 위치(QPoint) - PySide6 는 position(), PySide2 는 pos()."""
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()


class JUN_mod_altPan_qt_v01(QObject):
    """뷰 하나에 Alt + 가운데 버튼 드래그 이동을 붙인다."""

    MODIFIER = Qt.AltModifier
    BUTTON = Qt.MiddleButton

    def __init__(self, view, horizontal=False, parent=None):
        super().__init__(parent or view)
        self.view = view
        self.horizontal = bool(horizontal)
        self._panning = False
        self._start = QPoint()
        self._start_v = 0
        self._start_h = 0
        self._row_px = 1
        view.viewport().installEventFilter(self)

    # ------------------------------------------------------------------

    def is_panning(self):
        return self._panning

    def _step_px(self):
        """스크롤바 값 1 이 몇 픽셀인가. 항목 단위 스크롤이면 첫 보이는 행 높이."""
        view = self.view
        if not isinstance(view, QAbstractItemView):
            return 1
        if view.verticalScrollMode() == QAbstractItemView.ScrollPerPixel:
            return 1
        index = view.indexAt(QPoint(2, 2))
        height = view.visualRect(index).height() if index.isValid() else 0
        return max(1, height or view.fontMetrics().height())

    def _begin(self, pos):
        self._panning = True
        self._start = QPoint(pos)
        self._start_v = self.view.verticalScrollBar().value()
        self._start_h = self.view.horizontalScrollBar().value()
        self._row_px = self._step_px()
        self.view.viewport().setCursor(Qt.ClosedHandCursor)

    def _move(self, pos):
        delta = pos - self._start
        # 잡아 끄는 방향: 아래로 끌면 내용이 내려온다 = 스크롤 값이 줄어든다
        bar = self.view.verticalScrollBar()
        bar.setValue(self._start_v - int(round(delta.y() / float(self._row_px))))
        if self.horizontal:
            self.view.horizontalScrollBar().setValue(self._start_h - delta.x())

    def _end(self):
        self._panning = False
        self.view.viewport().unsetCursor()

    # ------------------------------------------------------------------

    def eventFilter(self, obj, event):
        etype = event.type()
        if etype == QEvent.MouseButtonPress:
            if event.button() == self.BUTTON and (event.modifiers() & self.MODIFIER):
                self._begin(_pos(event))
                return True
        elif etype == QEvent.MouseMove:
            if self._panning:
                if event.buttons() & self.BUTTON:
                    self._move(_pos(event))
                else:                       # 놓기를 놓쳤다(창 밖에서 놓음 등)
                    self._end()
                return True
        elif etype == QEvent.MouseButtonRelease:
            if self._panning and event.button() == self.BUTTON:
                self._end()
                return True
        elif etype == QEvent.MouseButtonDblClick:
            # 빠르게 두 번 누르면 두 번째 누르기가 DblClick 으로 온다 - 이것도 드래그 시작
            if event.button() == self.BUTTON and (event.modifiers() & self.MODIFIER):
                self._begin(_pos(event))
                return True
        return False
