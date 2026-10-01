# Python Script by Ji Hun Park
# last Update date : 2026-10-01
# A00490_KeyboardTool - key capture field
#
# 칸을 클릭하고 키를 누르면 그 키 이름이 들어간다 (Ctrl/Shift/Alt 조합 포함).
# 이름을 직접 못 치는 대신 오른쪽 ▾ 버튼 메뉴에서 고를 수 있다.
# Windows 의 nativeVirtualKey() 로 가상 키 코드를 그대로 받으므로 키보드 배열
# (한/영) 과 무관하다.

from Framework.qt.qt import (
    Qt, QEvent, QWidget, QHBoxLayout, QLineEdit, QToolButton, QMenu,
)

from ..core import keys

# 좌/우 구분 조합키 VK (단독으로는 기록하지 않는다)
_MOD_VKS = {0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5}

_MENU_GROUPS = (
    ("Arrows", ["Up", "Down", "Left", "Right"]),
    ("Navigation", ["PageUp", "PageDown", "Home", "End", "Insert", "Delete"]),
    ("Common", ["Enter", "Space", "Tab", "Esc", "Backspace"]),
    ("Function", ["F%d" % i for i in range(1, 13)]),
    ("Numpad", ["Num%d" % i for i in range(10)] + ["NumAdd", "NumSub", "NumMul", "NumDiv", "NumDec"]),
    ("Letters", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
    ("Digits", list("0123456789")),
)


class _CaptureLine(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click, then press a key")

    def event(self, ev):
        # Tab / Shift+Tab 은 포커스 이동으로 먼저 소비되므로 여기서 가로챈다
        if ev.type() == QEvent.KeyPress and ev.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            self.keyPressEvent(ev)
            return True
        return super().event(ev)

    def keyPressEvent(self, ev):
        vk = ev.nativeVirtualKey()
        if not vk or vk in _MOD_VKS:
            ev.accept()
            return
        m = ev.modifiers()
        mods = []
        if m & Qt.ControlModifier:
            mods.append("Ctrl")
        if m & Qt.ShiftModifier or ev.key() == Qt.Key_Backtab:
            mods.append("Shift")
        if m & Qt.AltModifier:
            mods.append("Alt")
        if m & Qt.MetaModifier:
            mods.append("Win")
        self.setText("+".join(mods + [keys.vk_name(vk)]))
        ev.accept()

    def focusInEvent(self, ev):
        super().focusInEvent(ev)
        self.selectAll()


class KeyCaptureEdit(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        self.line = _CaptureLine()
        self.line.setToolTip("Click here and press the key (combos like Ctrl+C work too).")
        lay.addWidget(self.line, 1)

        self.menu_button = QToolButton()
        self.menu_button.setText("...")
        self.menu_button.setToolTip("Pick a key from a list")
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(self.menu_button)
        for title, names in _MENU_GROUPS:
            sub = menu.addMenu(title)
            for name in names:
                act = sub.addAction(name)
                act.triggered.connect(lambda _=False, n=name: self.setText(n))
        self.menu_button.setMenu(menu)
        lay.addWidget(self.menu_button)

    def text(self):
        return self.line.text()

    def setText(self, text):
        self.line.setText(text)
