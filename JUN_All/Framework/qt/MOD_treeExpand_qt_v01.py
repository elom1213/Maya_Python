# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# Framework.qt - 트리 펼치기 · 접기 규칙 (QTreeWidget / QTreeView 공용)
#
#   JUN_mod_treeExpand_qt_v01(tree)        # 한 줄. 트리를 만든 직후에 붙인다(부모 = 트리라 따로 들고 있을 필요 없다).
#
# 규칙 (2026-11-05 사용자 지정 - 모든 툴의 트리 공통):
#   - 화살표(또는 더블클릭 · 오른쪽 화살표 키)로 **펼치면 한 단계만** 보인다 - 예전에 펼쳐 둔 하위가 있어도 접힌 채로.
#     (Qt 기본은 자식의 펼침 상태를 기억해서, 접었다 펼치면 아래가 전부 다시 열린다.)
#   - **Shift + 펼치기** = 그 아래 전부 펼친다.
#   - **Shift + 접기**   = 그 아래 전부 접는다(다음에 펼치면 한 단계부터).
#   - 키보드 `*`(Qt 의 '아래 전부 펼치기')도 Shift 와 같게.
#
# 사용자 입력(마우스 · 키)으로 생긴 펼침 · 접힘에만 반응한다. 코드가 부르는 expandAll() · setExpanded() ·
# expand() 는 손대지 않는다(툴이 처음에 전부 펼쳐 보여 주는 동작은 그대로).
#
# 게으른 트리(펼칠 때 자식을 채우는 파일 트리 등)도 된다 - Shift 전부 펼치기는 펼치면서 새로 생긴 자식까지 따라가되,
# 디스크 전체를 훑지 않게 max_nodes(기본 2000) 개에서 멈춘다.

from collections import deque

from Framework.qt.qt import (
    Qt,
    QObject,
    QEvent,
    QTimer,
    QApplication,
)


def _shift_held():
    try:
        return bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)
    except Exception:  # noqa: BLE001
        return False


class JUN_mod_treeExpand_qt_v01(QObject):
    """트리 하나에 펼치기 규칙을 붙인다. 같은 트리에 두 번 붙이면 처음 것을 그대로 쓴다(attach 참고)."""

    def __new__(cls, view, *args, **kwargs):
        existing = getattr(view, "_jun_tree_expand", None)
        if isinstance(existing, cls):
            return existing
        return super().__new__(cls)

    def __init__(self, view, max_nodes=2000, parent=None):
        if getattr(view, "_jun_tree_expand", None) is self:
            return                                   # 이미 붙어 있다
        super().__init__(parent or view)
        self.view = view
        self.max_nodes = int(max_nodes)
        self._user = False          # 지금 사용자 입력 처리 중인가
        self._recursive_key = False  # '*' 키
        self._shift = False         # 그 입력 이벤트에 Shift 가 눌려 있었나
        self._busy = False          # 우리가 펼치고 접는 중(재진입 방지)
        view._jun_tree_expand = self
        view.expanded.connect(self._on_expanded)
        view.collapsed.connect(self._on_collapsed)
        view.viewport().installEventFilter(self)
        view.installEventFilter(self)

    # ------------------------------------------------------------------ 사용자 입력 감지

    def eventFilter(self, obj, event):
        et = event.type()
        if et in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick, QEvent.KeyPress):
            self._user = True
            self._recursive_key = (et == QEvent.KeyPress and event.key() == Qt.Key_Asterisk)
            try:
                self._shift = bool(event.modifiers() & Qt.ShiftModifier)
            except Exception:  # noqa: BLE001
                self._shift = False
            # 이 이벤트를 Qt 가 처리하는 동안(그 안에서 expanded 가 온다)만 켜 두고 바로 끈다.
            QTimer.singleShot(0, self._end_user)
        return False

    def _end_user(self):
        self._user = False
        self._recursive_key = False
        self._shift = False

    # ------------------------------------------------------------------ 규칙

    def _on_expanded(self, index):
        if self._busy or not self._user:
            return
        if self._shift or _shift_held() or self._recursive_key:
            self.expand_all_below(index)
        else:
            self.collapse_children(index)

    def _on_collapsed(self, index):
        if self._busy or not self._user:
            return
        if self._shift or _shift_held():
            self.collapse_all_below(index)

    # ------------------------------------------------------------------ 동작 (코드에서도 쓸 수 있다)

    def _children(self, index):
        model = self.view.model()
        if model is None:
            return []
        return [model.index(r, 0, index) for r in range(model.rowCount(index))]

    def _run(self, func):
        self._busy = True
        self.view.setUpdatesEnabled(False)
        try:
            func()
        finally:
            self.view.setUpdatesEnabled(True)
            self._busy = False

    def collapse_children(self, index):
        """바로 아래 자식들을 접는다 - 펼친 항목은 한 단계만 보인다."""
        def go():
            for child in self._children(index):
                if self.view.isExpanded(child):
                    self.view.collapse(child)
        self._run(go)

    def collapse_all_below(self, index):
        """index 아래 전부 접는다(index 자신은 그대로)."""
        def go():
            stack = list(self._children(index))
            while stack:
                child = stack.pop()
                if self.view.isExpanded(child):
                    self.view.collapse(child)
                stack.extend(self._children(child))
        self._run(go)

    def expand_all_below(self, index):
        """index 와 그 아래 전부 펼친다. 펼치면서 새로 채워진 자식(게으른 트리)도 따라간다 - max_nodes 개까지.
        얕은 단계부터(너비 우선) - 한도에 걸려도 위쪽은 고르게 펼쳐진다."""
        def go():
            model = self.view.model()
            stack = deque([index])
            count = 0
            while stack and count < self.max_nodes:
                idx = stack.popleft()
                if idx.isValid() and not self.view.isExpanded(idx):
                    self.view.expand(idx)
                count += 1
                try:
                    if model.canFetchMore(idx):
                        model.fetchMore(idx)
                except Exception:  # noqa: BLE001
                    pass
                for child in self._children(idx):
                    if model.hasChildren(child):
                        stack.append(child)
        self._run(go)


def attach(view, **kwargs):
    """JUN_mod_treeExpand_qt_v01(view) 와 같다(이미 붙어 있으면 그것)."""
    return JUN_mod_treeExpand_qt_v01(view, **kwargs)
