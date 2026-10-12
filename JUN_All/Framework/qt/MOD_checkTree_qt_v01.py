# -*- coding: utf-8 -*-
"""
JUN_mod_checkTree_qt_v01 - 체크박스가 달린 QTreeWidget 에 **다중 선택 + 다중 체크** 를 붙인다.

`JUN_mod_checkList_qt_v01`(QListWidget 판) 과 **같은 규칙의 QTreeWidget 판**이다. 위젯이 아니라
**동작(behavior)** 이라, 이미 만들어 둔 QTreeWidget 에 붙이기만 하면 된다.

    self.chk_tree = JUN_mod_checkTree_qt.JUN_mod_checkTree_qt_v01(self.tree)

붙이면 이렇게 동작한다
--------------------
- **Shift / Ctrl 클릭으로 여러 행을 고른다** (`ExtendedSelection` 으로 바꾼다).
- 고른 행 중 **하나의 체크박스를 누르면 고른 행 전부**가 같은 상태가 된다. 고른 것은 그대로 남는다.
- 고르지 않은 행의 체크박스를 누르면 **그 행 하나만** 바뀐다(선택도 바뀌지 않는다).
- **Space** 는 고른 행 전부의 체크를 뒤집는다(첫 행 기준으로 전부 같은 상태로).
- 체크박스가 **없는 행**(폴더 · `...` · 정보 행 - `setCheckState` 를 한 적이 없거나 비활성)은
  누르기도 전파도 건너뛴다. (QTreeWidgetItem 은 기본 플래그에 `ItemIsUserCheckable` 이 들어 있어
  플래그로는 못 가른다 - 체크 상태 데이터의 유무로 가른다.) 체크박스는 **0 열**에 있다고 본다(`column` 으로 바꿀 수 있다).

왜 공용인가 - Qt 기본 처리의 함정
-------------------------------
리스트와 똑같이, 트리에서도 체크박스 위 **누르기가 선택을 그 한 행으로 풀어 버린다.** 그래서 체크박스
위 누르기/놓기/더블클릭은 viewport eventFilter 에서 **직접 먹고**, 놓을 때 한 번만 뒤집는다.
트리는 들여쓰기가 있어 체크박스 자리를 `visualItemRect`(들여쓰기 뒤부터) 기준으로 잰다.

"보이는 것이 작업 대상"
----------------------
전파는 **보이는 선택 행에만** 한다 - 필터로 숨긴 행(`isHidden`)과 접힌 부모 아래 행은 건드리지 않는다
(접힌 아래는 Shift 범위 선택에도 들어오지 않지만, 코드로 고른 경우를 위해 한 번 더 거른다).

신호
----
여러 행을 한 번에 바꿀 때 `itemChanged` 를 행마다 쏘지 않는다. 신호를 막고 바꾼 뒤 바뀐 행 전부를
**`checksChanged(list)`** 로 먼저 알리고, 그다음 **`itemChanged` 를 누른 행 하나로 한 번** 쏜다.
코드에서 `setCheckState` 를 부르는 것(Check All 등)은 전파하지 않는다.
"""

from Framework.qt.qt import *


class JUN_mod_checkTree_qt_v01(QObject):
    """QTreeWidget 에 다중 선택 + 다중 체크 동작을 붙인다."""

    #: 사용자가 체크를 바꾼 행들 (QTreeWidgetItem 리스트)
    checksChanged = Signal(list)

    def __init__(self, tree_widget, column=0, parent=None):
        super().__init__(parent or tree_widget)

        self.tree_widget = tree_widget
        self.column = int(column)
        self._pressed = None

        tree_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree_widget.viewport().installEventFilter(self)
        tree_widget.installEventFilter(self)

    # ------------------------------------------------------------------ 조회

    def _checkable(self, item):
        """사용자가 체크를 바꿀 수 있는 행인가(체크박스가 **실제로 있고** 활성).

        QTreeWidgetItem 은 기본 플래그에 ItemIsUserCheckable 이 **이미 들어 있다**(리스트와 다르다).
        플래그만 보면 폴더 · 정보 행도 체크 가능으로 잡혀 전파가 거기에 체크박스를 만들어 버린다.
        그래서 `setCheckState` 로 체크 상태 데이터가 있는 행만 체크박스가 있는 행으로 본다.
        """
        if item is None:
            return False
        flags = item.flags()
        if not (flags & Qt.ItemIsUserCheckable) or not (flags & Qt.ItemIsEnabled):
            return False
        return item.data(self.column, Qt.CheckStateRole) is not None

    def check_hit(self, pos):
        """viewport 좌표 pos 가 어느 항목의 체크박스 위면 그 항목, 아니면 None."""
        tw = self.tree_widget
        item = tw.itemAt(pos)
        if item is None or not self._checkable(item):
            return None
        if tw.columnAt(pos.x()) != self.column:
            return None
        opt = QStyleOptionViewItem()
        opt.initFrom(tw)
        opt.rect = tw.visualItemRect(item)
        if self.column:
            opt.rect = tw.visualRect(tw.indexFromItem(item, self.column))
        opt.features = (QStyleOptionViewItem.HasCheckIndicator |
                        QStyleOptionViewItem.HasDisplay)
        rect = tw.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator, opt, tw)
        return item if rect.contains(pos) else None

    def all_items(self):
        """트리의 모든 항목(위에서 아래, 깊이 우선)."""
        tw = self.tree_widget
        out = []
        stack = [tw.topLevelItem(i) for i in range(tw.topLevelItemCount() - 1, -1, -1)]
        while stack:
            item = stack.pop()
            out.append(item)
            for i in range(item.childCount() - 1, -1, -1):
                stack.append(item.child(i))
        return out

    def _visible(self, item):
        """숨기지 않았고, 조상이 모두 펼쳐져 있는가."""
        if item.isHidden():
            return False
        parent = item.parent()
        while parent is not None:
            if parent.isHidden() or not parent.isExpanded():
                return False
            parent = parent.parent()
        return True

    def visible_selected(self):
        """보이는 · 바꿀 수 있는 선택 행, 트리 순서대로."""
        return [it for it in self.all_items()
                if it.isSelected() and self._checkable(it) and self._visible(it)]

    # ------------------------------------------------------------------ 변경

    def set_checked(self, items, state, anchor=None):
        """items 를 state 로. 신호는 막고 바꾼 뒤 checksChanged(바뀐 전부) -> itemChanged(anchor) 한 번."""
        tw = self.tree_widget
        col = self.column
        changed = [it for it in items if it.checkState(col) != state]
        if not changed:
            return []
        tw.blockSignals(True)
        try:
            for it in changed:
                it.setCheckState(col, state)
        finally:
            tw.blockSignals(False)
        self.checksChanged.emit(changed)
        tw.itemChanged.emit(anchor if anchor in changed else changed[0], col)
        return changed

    def _toggle_from(self, item):
        """item 의 체크를 뒤집는다. item 이 고른 행이면 보이는 고른 행 전부를 같은 상태로."""
        state = Qt.Unchecked if item.checkState(self.column) == Qt.Checked else Qt.Checked
        targets = [item]
        if item.isSelected():
            targets = self.visible_selected() or [item]
        self.set_checked(targets, state, anchor=item)

    # ------------------------------------------------------------------ 이벤트

    def eventFilter(self, obj, event):
        try:
            return self._filter(obj, event)
        except RuntimeError:
            # 창을 닫을 때 트리가 먼저 지워진 뒤에도 이벤트가 한 번 더 온다 - 그냥 넘긴다.
            return False

    def _filter(self, obj, event):
        tw = self.tree_widget
        etype = event.type()

        # Space : 고른 행 전부 (기본 처리는 current 한 행만 뒤집는다)
        if obj is tw and etype in (QEvent.KeyPress, QEvent.KeyRelease):
            if event.key() != Qt.Key_Space or event.modifiers() & ~Qt.KeypadModifier:
                return False
            if etype == QEvent.KeyPress and not event.isAutoRepeat():
                targets = self.visible_selected()
                if targets:
                    state = (Qt.Unchecked
                             if targets[0].checkState(self.column) == Qt.Checked
                             else Qt.Checked)
                    self.set_checked(targets, state, anchor=targets[0])
            return True

        if obj is not tw.viewport():
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
