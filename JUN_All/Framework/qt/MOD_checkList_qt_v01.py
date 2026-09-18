# -*- coding: utf-8 -*-
"""
JUN_mod_checkList_qt_v01 - 체크박스가 달린 QListWidget 에 **다중 선택 + 다중 체크** 를 붙인다.

위젯이 아니라 **동작(behavior)** 이다. 이미 만들어 둔 QListWidget 에 붙이기만 하면 되고,
목록 · 필터(`JUN_mod_filter_qt`) · 개수 라벨은 그대로 둔다.

    self.chk_attrs = JUN_mod_checkList_qt.JUN_mod_checkList_qt_v01(self.lw_attrs)

붙이면 이렇게 동작한다
--------------------
- **Shift / Ctrl 클릭으로 여러 행을 고른다** (`ExtendedSelection` 으로 바꾼다).
- 고른 행 중 **하나의 체크박스를 누르면 고른 행 전부**가 같은 상태가 된다. 고른 것은 그대로 남는다.
- 고르지 않은 행의 체크박스를 누르면 **그 행 하나만** 바뀐다(선택도 바뀌지 않는다).
- **Space** 는 고른 행 전부의 체크를 뒤집는다(첫 행 기준으로 전부 같은 상태로).

왜 공용인가 - Qt 기본 처리의 함정
-------------------------------
QListWidget 에 맡기면 체크박스 위 **누르기가 선택을 그 한 행으로 풀어 버린다**(A00275 에서
오프스크린 QTest 로 실측). 첫 클릭은 여러 행에 전파돼도 그 뒤로는 한 행씩만 바뀐다.
그래서 체크박스 위 누르기/놓기/더블클릭은 viewport eventFilter 에서 **직접 먹고**, 놓을 때 한 번만 뒤집는다.

"보이는 것이 작업 대상"
----------------------
Shift 범위 선택은 **필터에 가려진 행까지** 고른다(Qt 는 숨긴 행도 선택을 유지한다). 가려진 행의
체크까지 바꾸면 사용자가 보지 못한 것을 건드리게 되므로, 전파는 **보이는 선택 행에만** 한다.

신호
----
여러 행을 한 번에 바꿀 때는 `itemChanged` 를 행마다 쏘지 않는다(목록이 크면 호출부 갱신이
N 번 돈다). 신호를 막고 바꾼 뒤 **`itemChanged` 를 누른 행 하나로 한 번** 쏘고, 바뀐 행 전부는
`checksChanged(list)` 로 알린다. 코드에서 `setCheckState` 를 부르는 것(Check All 등)은 전파하지 않는다.
"""

from Framework.qt.qt import *


class JUN_mod_checkList_qt_v01(QObject):
    """QListWidget 에 다중 선택 + 다중 체크 동작을 붙인다."""

    #: 사용자가 체크를 바꾼 행들 (QListWidgetItem 리스트)
    checksChanged = Signal(list)

    def __init__(self, list_widget, parent=None):
        super(JUN_mod_checkList_qt_v01, self).__init__(parent or list_widget)

        self.list_widget = list_widget
        self._pressed = None

        list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        list_widget.viewport().installEventFilter(self)
        list_widget.installEventFilter(self)

    # ------------------------------------------------------------------ 조회

    def check_hit(self, pos):
        """viewport 좌표 pos 가 어느 항목의 체크박스 위면 그 항목, 아니면 None."""
        lw = self.list_widget
        item = lw.itemAt(pos)
        if item is None or not (item.flags() & Qt.ItemIsUserCheckable):
            return None
        opt = QStyleOptionViewItem()
        opt.initFrom(lw)
        opt.rect = lw.visualItemRect(item)
        opt.features = (QStyleOptionViewItem.HasCheckIndicator |
                        QStyleOptionViewItem.HasDisplay)
        rect = lw.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator, opt, lw)
        return item if rect.contains(pos) else None

    def visible_selected(self):
        """보이는(필터에 안 가려진) 선택 행, 목록 순서대로."""
        lw = self.list_widget
        return [lw.item(i) for i in range(lw.count())
                if lw.item(i).isSelected() and not lw.item(i).isHidden()
                and lw.item(i).flags() & Qt.ItemIsUserCheckable]

    # ------------------------------------------------------------------ 변경

    def set_checked(self, items, state, anchor=None):
        """items 를 state 로. 신호는 막고 바꾼 뒤 itemChanged(anchor) 한 번 + checksChanged."""
        lw = self.list_widget
        changed = [it for it in items if it.checkState() != state]
        if not changed:
            return []
        lw.blockSignals(True)
        try:
            for it in changed:
                it.setCheckState(state)
        finally:
            lw.blockSignals(False)
        lw.itemChanged.emit(anchor if anchor in changed else changed[0])
        self.checksChanged.emit(changed)
        return changed

    def _toggle_from(self, item):
        """item 의 체크를 뒤집는다. item 이 고른 행이면 보이는 고른 행 전부를 같은 상태로."""
        state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        targets = [item]
        if item.isSelected():
            targets = self.visible_selected() or [item]
        self.set_checked(targets, state, anchor=item)

    # ------------------------------------------------------------------ 이벤트

    def eventFilter(self, obj, event):
        try:
            return self._filter(obj, event)
        except RuntimeError:
            # 창을 닫을 때 리스트가 먼저 지워진 뒤에도 이벤트가 한 번 더 온다
            # (mayapy 실측: "Internal C++ object already deleted") - 그냥 넘긴다.
            return False

    def _filter(self, obj, event):
        lw = self.list_widget
        etype = event.type()

        # Space : 고른 행 전부 (기본 처리는 current 한 행만 뒤집는다)
        if obj is lw and etype in (QEvent.KeyPress, QEvent.KeyRelease):
            if event.key() != Qt.Key_Space or event.modifiers() & ~Qt.KeypadModifier:
                return False
            if etype == QEvent.KeyPress and not event.isAutoRepeat():
                targets = self.visible_selected()
                if targets:
                    state = (Qt.Unchecked if targets[0].checkState() == Qt.Checked
                             else Qt.Checked)
                    self.set_checked(targets, state, anchor=targets[0])
            return True

        if obj is not lw.viewport():
            return False
        if etype not in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
                         QEvent.MouseButtonDblClick):
            return False
        if event.button() != Qt.LeftButton:
            return False

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        item = self.check_hit(pos)

        # 체크박스 위 누르기는 먹는다 - 기본 처리가 선택을 그 한 행으로 풀어 버린다.
        if etype == QEvent.MouseButtonPress:
            self._pressed = item
            return item is not None
        if etype == QEvent.MouseButtonDblClick:
            return item is not None

        pressed, self._pressed = self._pressed, None
        if item is None or item is not pressed:
            # 체크박스에서 누르고 밖에서 놓았으면 아무 일도 없던 것으로 한다.
            return pressed is not None
        self._toggle_from(item)
        return True
