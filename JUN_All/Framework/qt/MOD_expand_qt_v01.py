# -*- coding: utf-8 -*-
"""
JUN_mod_expand_qt_v01 - 재사용 PySide "별도 창으로 빼서 보기(Expand)" 패널.

패널 안의 본문을 **독립 창으로 띄웠다가 제자리로 되돌리는** 위젯이다.
그래프 에디터·아웃라이너를 크게 띄워 놓고 툴의 한 부분만 옆에 두고 쓰는 배치에 쓴다.
A00290_BSTool 의 Shape Editor `Expand`, A00110_animTool_V02 의 Curve Filters `Expand`
에서 검증한 방식을 공용으로 올린 것이다.

핵심은 **복제가 아니라 이동**이다
--------------------------------
본문 위젯을 새 창으로 **그대로 옮긴다**(레이아웃에 add 하면 이전 부모에서 자동으로 떨어진다).
두 벌을 만들어 동기화하는 방식이 아니라서

  - 슬라이더 · 세션 · undo 규칙이 **완전히 같게** 동작하고,
  - 두 화면의 값이 어긋날 여지 자체가 없으며,
  - 툴 쪽 코드는 위젯 참조(`self.slider` 등)를 그대로 쓰면 된다.

되돌릴 자리는 `layout.indexOf` 로 미리 저장해 두었다가 `insertWidget` 으로 복귀한다.

창이 미아로 남지 않게
--------------------
확장 창은 툴 창의 자식(`QWidget(owner, Qt.Window)`)이다. 툴 창이 닫힐 때 본문이 확장 창에
들어가 있으면 본문까지 함께 파괴되므로, **툴 창의 Close 를 감시해 자동으로 접는다**
(각 툴이 closeEvent 에 정리 코드를 넣지 않아도 된다).

사용법
------
    panel = JUN_mod_expand_qt_v01(title="Curve Filters")
    panel.add_widget(some_widget)
    panel.add_layout(some_row)
    tab_layout.addWidget(panel)

    panel.expanded_changed.connect(lambda on: self._fit_window_later())   # 선택

Maya 밖에서도 import / 생성이 가능하도록 maya 의존이 없다.
"""

from Framework.qt.qt import *


class _ExpandedWindow(QWidget):
    """본문을 넘겨받아 띄우는 독립 창. 닫히면 패널에게 알린다."""

    def __init__(self, panel, title, object_name, size):
        super(_ExpandedWindow, self).__init__(panel.window(), Qt.Window)
        self._panel = panel
        self.setObjectName(object_name)
        self.setWindowTitle(title)
        if size:
            self.resize(size[0], size[1])

        layout = QVBoxLayout(self)
        # 패널에서 넘겨받은 본문이 들어갈 자리
        self.body = QVBoxLayout()
        layout.addLayout(self.body, 1)

    def closeEvent(self, event):
        self._panel.collapse()
        super(_ExpandedWindow, self).closeEvent(event)


class JUN_mod_expand_qt_v01(QWidget):
    """본문을 별도 창으로 빼서 볼 수 있는 패널.

    본문에는 `add_widget` / `add_layout` 으로 넣는다(공용 접이식 위젯과 같은 API).
    상태가 바뀌면 `expanded_changed(bool)` 를 방출하므로, 부모가 받아 창 크기를 다시
    맞출 수 있다(`_fit_window` 를 쓰는 툴이면 그대로 연결하면 된다).

    Args:
        title: 확장 창의 제목. 버튼 툴팁에도 쓰인다.
        button_label: 버튼에 쓸 글자(기본 "Expand").
        placeholder: 본문이 나가 있는 동안 제자리에 보여 줄 안내 문구.
                     None 이면 제목으로 기본 문구를 만든다.
        object_name: 확장 창의 objectName. 툴마다 유일해야 재실행 시 옛 창을 찾아 닫을 수
                     있다. None 이면 제목에서 만든다.
        size: 확장 창의 초기 크기 (w, h). None 이면 Qt 기본값.
        button_on_top: True(기본)면 버튼 줄을 본문 위에, False 면 아래에 둔다.
    """

    expanded_changed = Signal(bool)

    def __init__(self, title="Panel", button_label="Expand", placeholder=None,
                 object_name=None, size=(420, 460), button_on_top=True,
                 parent=None):
        super(JUN_mod_expand_qt_v01, self).__init__(parent)

        self._title = title
        self._object_name = object_name or "JUN_expand_{0}_window".format(
            "".join(ch for ch in title if ch.isalnum()) or "panel")
        self._size = size
        self._window = None
        self._filtered = None          # Close 를 감시 중인 툴 창

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        # ---- 버튼 줄
        row = QHBoxLayout()
        row.addStretch(1)
        self.button = QPushButton(button_label)
        self.button.setFixedWidth(90)
        self.button.setToolTip(
            "Show '{0}' in a separate, resizable window.\n"
            "The panel is moved, not copied - everything behaves exactly the "
            "same.\n"
            "Close that window (or press {1} again) to bring it back "
            "here.".format(title, button_label))
        self.button.clicked.connect(self.toggle)
        row.addWidget(self.button)

        # ---- 본문이 나가 있는 동안 자리를 지키는 안내
        self.placeholder = QLabel(
            placeholder or "{0} is shown in the expanded window.".format(title))
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setWordWrap(True)
        self.placeholder.setVisible(False)

        # ---- 본문(통째로 옮겨 다니는 위젯)
        self._content = QWidget()
        self.body = QVBoxLayout(self._content)
        self.body.setContentsMargins(0, 0, 0, 0)

        if button_on_top:
            outer.addLayout(row)
            outer.addWidget(self.placeholder)
            outer.addWidget(self._content)
        else:
            outer.addWidget(self.placeholder)
            outer.addWidget(self._content)
            outer.addLayout(row)

        self._outer = outer
        self._content_index = outer.indexOf(self._content)

    # ================================================================
    # 공개 API
    # ================================================================

    def add_widget(self, widget):
        self.body.addWidget(widget)

    def add_layout(self, layout):
        self.body.addLayout(layout)

    def content(self):
        """본문 위젯. 직접 다뤄야 할 때만 쓴다."""
        return self._content

    def is_expanded(self):
        return self._window is not None

    def toggle(self):
        """버튼 동작 — 떠 있으면 앞으로 가져오고, 없으면 띄운다.

        (닫기는 창의 X 로 한다. 버튼이 '닫기' 로 변하면, 창을 찾다가 버튼을 누른 사용자가
        창을 잃어버리기 때문이다.)
        """
        if self._window is not None:
            self._window.raise_()
            self._window.activateWindow()
            return
        self.expand()

    def expand(self):
        """본문을 별도 창으로 옮긴다."""
        if self._window is not None:
            return

        window = _ExpandedWindow(self, self._title, self._object_name, self._size)
        # addWidget 이 본문을 이 패널에서 떼어 창으로 옮긴다(복제가 아니다).
        window.body.addWidget(self._content)
        self._window = window

        self.placeholder.setVisible(True)
        self._watch_owner_close()
        window.show()
        self.expanded_changed.emit(True)

    def collapse(self):
        """본문을 패널의 원래 자리로 되돌린다(창은 정리된다)."""
        if self._window is None:
            return

        window, self._window = self._window, None
        self.placeholder.setVisible(False)
        self._outer.insertWidget(self._content_index, self._content)
        window.deleteLater()
        self.expanded_changed.emit(False)

    # ================================================================
    # 내부
    # ================================================================

    def _watch_owner_close(self):
        """툴 창이 닫히면 자동으로 접는다.

        본문이 확장 창에 가 있는 채로 툴 창이 파괴되면 본문까지 함께 사라진다. 각 툴이
        closeEvent 에 정리 코드를 넣지 않아도 되도록 여기서 감시한다.
        """
        owner = self.window()
        if owner is None or owner is self._filtered:
            return
        owner.installEventFilter(self)
        self._filtered = owner

    def eventFilter(self, watched, event):
        if watched is self._filtered and event.type() == QEvent.Close:
            self.collapse()
        return super(JUN_mod_expand_qt_v01, self).eventFilter(watched, event)
