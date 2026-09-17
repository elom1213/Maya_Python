# -*- coding: utf-8 -*-
"""
JUN_mod_log_qt_v01 - 재사용 PySide 로그창.

읽기 전용 텍스트 + **작은 버튼 4개**(Expand / Shrink / Clear / Copy)를 한 줄에 얹은 위젯이다.
툴마다 `QTextEdit` / `QPlainTextEdit` 를 하나씩 놓고 "읽기 전용 + 높이 고정" 을 반복하던
것을 하나로 모은다.

  - **Expand** : 로그를 **별도 창으로 옮겨** 크게 본다(다시 누르면 그 창을 앞으로).
  - **Shrink** : 로그를 **접어 숨긴다**(토글). 누르면 버튼 줄만 남고 라벨이 `Show` 가 되며,
                 다시 누르면 로그가 돌아온다. 툴 창도 그만큼 줄었다가 다시 늘어난다.
  - **Clear**  : 로그를 비운다.
  - **Copy**   : 로그 **전문**을 클립보드로.

왜 드롭인(drop-in) 교체가 되는가
--------------------------------
저장소의 기존 로그창은 두 계열이고, 호출하는 메서드는 사실상 정해져 있다.

    QTextEdit 계열(te_log · log_widget · txt_log) : append · setReadOnly ·
        setMaximumHeight / setMinimumHeight / setFixedHeight · clear · setFont ·
        setLineWrapMode · moveCursor
    QPlainTextEdit 계열(log_view)                  : appendPlainText · setReadOnly ·
        setFixedHeight / setMinimumHeight

그래서 이 위젯은 **그 이름들을 전부 그대로 받는다.**

  - 내부는 **`QTextEdit`** 이다. `A00300_meshDoctor` · `A00430_DemBone` ·
    `A00410_SecondaryMotion` 이 `append('<span style="color:…">…')` 로 **색깔 로그**를
    쓰고 있어서, 내부를 `QPlainTextEdit` 로 두면 그 세 툴에서 태그가 그대로 보인다.
  - `QPlainTextEdit` 에만 있는 **`appendPlainText` 는 직접 구현**한다(HTML 로 해석하지
    않고 글자 그대로 한 줄 추가). 두 계열이 같은 위젯에 그대로 얹히는 이유가 이것이다.
  - 그 밖에 `QWidget` 에 없는 이름은 `__getattr__` 로 **내부 텍스트에 위임**하므로
    `toPlainText` · `moveCursor` · `verticalScrollBar` 같은 호출도 그대로 동작한다.

★ 높이 지정은 **내부 텍스트**에 건다
------------------------------------
`setFixedHeight(110)` 을 이 위젯(컨테이너)에 그대로 걸면 **버튼 줄이 그 110 을 나눠 먹어**
로그가 보이던 것보다 줄어든다(공용 TSL 에서 겪은 것과 같은 함정). 그래서 높이 계열 메서드는
전부 내부 텍스트로 넘긴다 — **로그가 보이는 줄 수는 교체 전과 같고**, 창이 버튼 줄 높이만큼
커진다.

★ 확장 창에서는 그 높이 제약을 **푼다**
-------------------------------------
위 제약은 "툴 창 안에서 로그가 차지할 몫" 이지 확장 창에서까지 지킬 값이 아니다.
그대로 두면 **창을 아무리 늘려도 로그는 상한에 묶여** 남는 자리가 빈 공간이 된다 —
크게 보려고 누른 버튼인데 크게 안 보인다. 그래서 `expand()` 가 제약을 담아 두고 풀어,
확장 창에서는 로그가 **창 높이를 그대로 따라간다**(`collapse()` 가 되돌린다).

Expand 는 복제가 아니라 이동이다
--------------------------------
`MOD_expand_qt_v01` 과 같은 방식이다. 텍스트 위젯을 **그대로 새 창으로 옮기므로** 두 벌을
동기화할 일이 없다 — 확장 중에 들어온 로그도 당연히 같은 위젯에 쌓이고, 툴 코드는
`self.log_view` 참조를 그대로 쓰면 된다. (공용 Expand 패널을 쓰지 않고 여기에 다시 구현한
것은, 그 패널이 버튼 하나를 위한 전용 줄을 갖는 구조라 **버튼 여러 개를 한 줄에** 두려는 이
위젯의 요구와 맞지 않기 때문이다.)

창이 미아로 남지 않게, 툴 창의 Close 를 감시해 자동으로 접는다.

Shrink 는 숨기기 + 높이 제약 치우기 + 창 줄이기다
------------------------------------------------
텍스트를 `setVisible(False)` 만 하면 로그는 안 보여도 **자리는 그대로** 남는다 — 위 ★ 에서
컨테이너에도 `높이 + 버튼 줄` 의 min/max 를 걸어 두었기 때문이다. 그래서 접을 때 컨테이너의
(min, max) 를 담아 두고 **버튼 줄 높이로** 바꾸고, 펼 때 되돌린다(Expand 의 `_text_limits` 와
같은 방식). 접혀 있는 동안 툴이 높이를 바꾸면 **되돌릴 값만** 갱신한다.

그래도 **툴 창 크기는 레이아웃이 알아서 줄이지 않는다**(최상위 창은 사용자가 정한 크기를
지킨다). 그러면 비운 자리가 스트레치나 다른 위젯으로 넘어갈 뿐 "줄어든" 느낌이 없다. 그래서
최상위 창이면 **줄어든 만큼 창 높이를 줄이고**, 펼 때 **실제로 줄인 만큼만** 다시 늘린다
(최소 높이에 걸려 덜 줄었으면 덜 늘린다). 최대화 · 전체 화면 창은 건드리지 않는다.
`resize_window_on_shrink=False` 로 끌 수 있다.

Expand 와 겹쳐도 된다: 접힌 채 Expand 하면 확장 창에는 로그가 보이고(자리 안내 라벨만 숨는다),
접힌 채 확장 창을 닫으면 로그는 제자리로 돌아오되 **접힌 상태를 유지**한다.

사용법
------
    from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01

    self.log_view = JUN_mod_log_qt_v01(
        window_title="Material Tool - Log",
        object_name="JUN_A00470_MaterialTool_log_window")
    self.log_view.setMinimumHeight(180)
    layout.addWidget(self.log_view)

    self.log_view.appendPlainText("hello")   # 기존 호출 그대로
    self.log_view.append("<b>hello</b>")     # 색깔 로그도 그대로

Maya 밖에서도 import / 생성이 가능하도록 maya 의존이 없다.
"""

from Framework.qt.qt import *


# 버튼은 "작게" - 로그창의 주인공은 글이지 버튼이 아니다.
BUTTON_HEIGHT = 20

# ★ 테마 qss 가 `QPushButton { padding: 8px; }` 를 준다. 그 패딩은 버튼 높이를 20px 로
#   고정한 순간 위아래 16px + 테두리 2px 로 20px 를 다 먹어, **글자가 들어갈 자리가 남지
#   않는다**(글자가 아예 안 보인다). 그래서 이 버튼들만 패딩을 덮어쓴다 - 색·테두리·호버는
#   테마 규칙 그대로 남는다(Qt 스타일시트는 지정한 속성만 덮어쓴다).
BUTTON_STYLE = "padding: 0px 6px; margin: 0px;"

# 폭은 고정하지 않는다. 글자 폭은 테마의 font-size 에 따라 달라지므로, 고정 폭으로 잘라 두면
# 폰트가 커지는 테마에서 이번과 같은 일이 가로로 되풀이된다. 최소 폭만 주고 나머지는 맡긴다.
BUTTON_MIN_WIDTH = 58

# Qt 가 "제한 없음" 으로 쓰는 값(`QWIDGETSIZE_MAX`). 바인딩에 따라 이 이름이 노출되지 않아
# 상수로 적어 둔다 - 확장 창에서 높이 제약을 풀 때 쓴다.
WIDGET_MAX_HEIGHT = 16777215


class _LogWindow(QWidget):
    """로그 텍스트를 넘겨받아 띄우는 독립 창. 닫히면 로그 위젯에게 알린다."""

    def __init__(self, panel, title, object_name, size):
        super(_LogWindow, self).__init__(panel.window(), Qt.Window)

        self._panel = panel
        self.setObjectName(object_name)
        self.setWindowTitle(title)
        if size:
            self.resize(size[0], size[1])

        layout = QVBoxLayout(self)
        # 넘겨받은 텍스트가 들어갈 자리
        self.body = QVBoxLayout()
        layout.addLayout(self.body, 1)

    def closeEvent(self, event):
        self._panel.collapse()
        super(_LogWindow, self).closeEvent(event)


class JUN_mod_log_qt_v01(QWidget):
    """Expand / Shrink / Clear / Copy 버튼을 갖춘 읽기 전용 로그창.

    Args:
        window_title: Expand 로 띄우는 창의 제목.
        object_name: 그 창의 objectName. 툴마다 유일해야 재실행 시 옛 창을 찾아 닫을 수
            있다. None 이면 제목에서 만든다.
        title: 버튼 줄 왼쪽에 붙일 라벨. None(기본)이면 라벨 없이 버튼만 둔다 -
            기존 로그창을 교체할 때 화면이 달라지지 않도록.
        expand_size: 확장 창의 초기 크기 (w, h).
        buttons_on_top: True(기본)면 버튼 줄이 로그 위에, False 면 아래에 온다.
        read_only: 기본 True. 로그는 읽는 것이다.
        resize_window_on_shrink: True(기본)면 Shrink 로 접을 때 최상위 툴 창 높이도
            그만큼 줄이고, 펼 때 되돌린다.
    """

    expanded_changed = Signal(bool)
    shrunk_changed = Signal(bool)
    cleared = Signal()
    copied = Signal(int)

    SHRINK_LABEL = "Shrink"
    SHOW_LABEL = "Show"

    def __init__(self, window_title="Log", object_name=None, title=None,
                 expand_size=(620, 520), buttons_on_top=True, read_only=True,
                 resize_window_on_shrink=True, parent=None):
        super(JUN_mod_log_qt_v01, self).__init__(parent)

        self._window_title = window_title
        self._object_name = object_name or "JUN_log_{0}_window".format(
            "".join(ch for ch in window_title if ch.isalnum()) or "panel")
        self._expand_size = expand_size
        self._window = None
        self._filtered = None          # Close 를 감시 중인 툴 창
        # 확장 중에 풀어 둔 내부 텍스트의 (min, max). 접혀 있으면 None.
        self._text_limits = None
        # Shrink 로 접는 동안 치워 둔 컨테이너의 (min, max). 펼쳐져 있으면 None.
        self._container_limits = None
        self._resize_window_on_shrink = bool(resize_window_on_shrink)
        # 접을 때 툴 창을 **실제로** 줄인 높이(펼 때 그만큼만 되돌린다).
        self._window_shrink_delta = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        # ---- 버튼 줄
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        if title:
            label = QLabel(title)
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            row.addWidget(label)

        row.addStretch(1)

        self.btn_expand = self._make_button(
            row, "Expand",
            "Show the log in a separate, resizable window.\n"
            "The log is moved, not copied - new messages keep going to the same "
            "place.\nClose that window to bring it back here.")
        self.btn_shrink = self._make_button(
            row, self.SHRINK_LABEL,
            "Hide the log and keep only this button row (the window gets shorter).\n"
            "Click again (Show) to bring the log back.\n"
            "Messages keep arriving while it is hidden.")
        # 토글 - 체크 상태 = 접힘. 라벨로도 상태를 보인다(테마가 :checked 를 칠하지 않는다).
        self.btn_shrink.setCheckable(True)
        self.btn_clear = self._make_button(
            row, "Clear", "Remove everything from the log.")
        self.btn_copy = self._make_button(
            row, "Copy", "Copy the whole log to the clipboard.")

        self.btn_expand.clicked.connect(self.toggle_expand)
        # clicked 는 checked bool 을 넘기지만 toggled 가 더 정확하다(setChecked 로 바뀌어도 온다).
        self.btn_shrink.toggled.connect(self.set_shrunk)
        self.btn_clear.clicked.connect(self.clear_log)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)

        # ---- 로그가 확장 창에 나가 있는 동안 자리를 지키는 안내
        self.placeholder = QLabel("The log is shown in the expanded window.")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setWordWrap(True)
        self.placeholder.setVisible(False)

        # ---- 본문 (통째로 옮겨 다니는 텍스트)
        self.text = QTextEdit()
        self.text.setReadOnly(read_only)

        if buttons_on_top:
            outer.addLayout(row)
            outer.addWidget(self.placeholder)
            outer.addWidget(self.text, 1)
        else:
            outer.addWidget(self.placeholder)
            outer.addWidget(self.text, 1)
            outer.addLayout(row)

        self._outer = outer
        self._row = row
        self._text_index = outer.indexOf(self.text)

    def _make_button(self, row, label, tooltip):
        button = QPushButton(label)
        button.setFixedHeight(BUTTON_HEIGHT)
        button.setMinimumWidth(BUTTON_MIN_WIDTH)
        # 테마의 큰 패딩을 이 버튼에서만 줄인다(위 BUTTON_STYLE 주석 참고).
        button.setStyleSheet(BUTTON_STYLE)
        button.setToolTip(tooltip)
        row.addWidget(button)
        return button

    # ==================================================================
    # 버튼 동작
    # ==================================================================

    def clear_log(self):
        """로그를 비운다(Clear 버튼과 같은 동작)."""
        self.text.clear()
        self.cleared.emit()

    def copy_to_clipboard(self):
        """로그 전문을 클립보드로. 복사한 글자 수를 돌려준다(빈 로그면 0).

        비어 있으면 **클립보드를 건드리지 않는다** - 남의 클립보드를 빈 값으로 덮는 것이
        도움이 되는 경우는 없다.
        """
        text = self.text.toPlainText()
        if not text:
            return 0

        try:
            QApplication.clipboard().setText(text)
        except Exception:
            return 0

        self.copied.emit(len(text))
        return len(text)

    def toggle_expand(self):
        """떠 있으면 앞으로 가져오고, 없으면 띄운다.

        (닫기는 창의 X 로 한다. 버튼이 '닫기' 로 변하면 창을 찾다가 버튼을 누른 사용자가
        창을 잃어버린다.)
        """
        if self._window is not None:
            self._window.raise_()
            self._window.activateWindow()
            return
        self.expand()

    def expand(self):
        """로그 텍스트를 별도 창으로 옮긴다."""
        if self._window is not None:
            return

        window = _LogWindow(self, self._window_title, self._object_name,
                            self._expand_size)

        # ★ 툴 창에서 걸어 둔 높이 제약을 **확장 창에서는 푼다.**
        #   그 제약(예: `setMaximumHeight(160)`)은 "툴 창 안에서 로그가 차지할 몫" 이지
        #   확장 창에서까지 지킬 값이 아니다. 그대로 두면 **창을 아무리 늘려도 로그는 160px
        #   에 묶여** 남는 자리가 빈 공간이 된다 - 크게 보려고 누른 버튼인데 크게 안 보인다.
        #   원래 값은 담아 두었다가 collapse 에서 되돌린다.
        self._text_limits = (self.text.minimumHeight(), self.text.maximumHeight())
        self.text.setMinimumHeight(0)
        self.text.setMaximumHeight(WIDGET_MAX_HEIGHT)

        # addWidget 이 텍스트를 이 위젯에서 떼어 창으로 옮긴다(복제가 아니다).
        window.body.addWidget(self.text)
        self._window = window

        self._sync_body_visibility()
        self._watch_owner_close()
        window.show()
        self.expanded_changed.emit(True)

    def collapse(self):
        """로그 텍스트를 원래 자리로 되돌린다(확장 창은 정리된다)."""
        if self._window is None:
            return

        window, self._window = self._window, None

        # 확장하며 풀어 둔 높이 제약을 되돌린다(제자리에서는 원래 몫만 차지해야 한다).
        if self._text_limits is not None:
            low, high = self._text_limits
            self._text_limits = None
            self.text.setMinimumHeight(low)
            self.text.setMaximumHeight(high)

        self._outer.insertWidget(self._text_index, self.text, 1)
        # 접힌 채 돌아왔으면 계속 숨겨 둔다.
        self._sync_body_visibility()
        window.deleteLater()
        self.expanded_changed.emit(False)

    def is_expanded(self):
        return self._window is not None

    def toggle_shrink(self):
        """Shrink 버튼과 같은 동작 - 접혀 있으면 펴고, 펴져 있으면 접는다."""
        self.set_shrunk(not self.is_shrunk())

    def set_shrunk(self, shrunk):
        """로그를 접거나(True) 편다(False). 이미 그 상태면 아무것도 안 한다.

        버튼의 체크 상태 · 라벨도 함께 맞추므로 코드에서 불러도 화면이 어긋나지 않는다.
        """
        shrunk = bool(shrunk)

        if self.btn_shrink.isChecked() != shrunk:
            # setChecked -> toggled -> 다시 여기로 들어온다. 그쪽에서 처리하게 두고 끝낸다.
            self.btn_shrink.setChecked(shrunk)
            return
        if shrunk == self.is_shrunk():
            return

        self.btn_shrink.setText(self.SHOW_LABEL if shrunk else self.SHRINK_LABEL)
        before = self.height()

        if shrunk:
            # 컨테이너의 min/max(= 텍스트 높이 + 버튼 줄)를 치워야 자리가 실제로 빈다.
            self._container_limits = (self.minimumHeight(), self.maximumHeight())
            self._sync_body_visibility()
            collapsed = self._row.sizeHint().height()
            super(JUN_mod_log_qt_v01, self).setMinimumHeight(0)
            super(JUN_mod_log_qt_v01, self).setMaximumHeight(max(collapsed, BUTTON_HEIGHT))
            self._resize_owner(shrink_by=max(before - max(collapsed, BUTTON_HEIGHT), 0))
        else:
            # ★ 창 높이는 제약을 되돌리기 **전에** 재 둔다. 되돌리는 순간 Qt 가 창을 새 최소
            #   높이까지 먼저 키우므로, 그 뒤에 재서 delta 를 더하면 두 번 커진다.
            owner = self.window()
            owner_height = owner.height() if owner is not None else 0
            low, high = self._container_limits
            self._container_limits = None
            super(JUN_mod_log_qt_v01, self).setMinimumHeight(low)
            super(JUN_mod_log_qt_v01, self).setMaximumHeight(high)
            self._sync_body_visibility()
            self._resize_owner(shrink_by=None, owner_height=owner_height)

        self.shrunk_changed.emit(shrunk)

    def is_shrunk(self):
        return self._container_limits is not None

    # ==================================================================
    # 로그 쓰기
    # ==================================================================

    def log(self, message):
        """한 줄 추가(새 코드용 이름). 글자는 그대로 들어간다."""
        self.appendPlainText(message)

    def appendPlainText(self, message):
        """`QPlainTextEdit` 과 같은 이름 - 들어온 글을 **그대로** 한 줄 추가한다.

        내부가 `QTextEdit` 이라 `append()` 는 HTML 로 해석된다. 로그 문자열에 `<` 가
        들어 있어도 먹히지 않도록, 이 메서드는 커서로 **평문**을 넣는다.
        """
        text = "" if message is None else str(message)

        cursor = self.text.textCursor()
        cursor.movePosition(QTextCursor.End)
        if not self.text.document().isEmpty():
            cursor.insertBlock()
        cursor.insertText(text)

        self.text.setTextCursor(cursor)
        self.text.ensureCursorVisible()

    def append(self, message):
        """`QTextEdit` 과 같은 이름 - **HTML 로 해석**해 한 줄 추가(색깔 로그용)."""
        self.text.append("" if message is None else str(message))

    def toPlainText(self):
        return self.text.toPlainText()

    def setPlainText(self, message):
        self.text.setPlainText("" if message is None else str(message))

    def clear(self):
        """`QTextEdit.clear` 와 같은 이름 - Clear 버튼과 같은 동작."""
        self.clear_log()

    def setReadOnly(self, value):
        self.text.setReadOnly(bool(value))

    # ==================================================================
    # ★ 높이 · 폰트는 내부 텍스트에 걸고, **컨테이너에도 버튼 줄만큼 더해 건다**
    # ==================================================================
    # 내부 텍스트에만 거는 이유: 이 위젯에 그대로 걸면 버튼 줄이 그 높이를 나눠 먹어
    # 교체 전보다 로그가 줄어든다. 그래서 요청한 높이는 텍스트가 그대로 받는다.
    #
    # ★ 그런데 **텍스트에만** 걸면 이번엔 컨테이너의 상한이 없어진다. 툴 창을 세로로
    #   늘리면 레이아웃이 컨테이너를 끝없이 늘리고, 텍스트는 상한에서 멈추므로 그 차이가
    #   **빈 공간**으로 남는다 - 로그는 그대로인데 로그창이 자리를 다 먹고 다른 UI 가
    #   밀려 스크롤이 생긴다(교체 전 `QTextEdit` 에 직접 걸 때는 없던 일이다. 그때는
    #   위젯 자신이 상한을 가졌다). 그래서 컨테이너에도 **버튼 줄 높이를 더해** 같은
    #   제약을 건다 - 보이는 줄 수는 요청한 그대로면서 창을 늘려도 로그창은 커지지 않는다.
    #
    # 높이를 아예 지정하지 않은 툴(로그를 늘어나는 칸으로 쓰는 템플릿 등)은 그대로
    # 늘어난다. 그쪽은 텍스트도 같이 늘어나므로 빈 공간이 생기지 않는다.

    def _chrome_height(self):
        """버튼 줄 + 그 아래 간격. 높이 요청을 컨테이너 크기로 옮길 때 더한다."""
        row = self._row.sizeHint().height()
        if row <= 0:
            row = BUTTON_HEIGHT
        return row + self._outer.spacing()

    # 확장 중에는 텍스트를 자유롭게 두어야 하므로(창 높이를 따라가야 한다) 값을 텍스트에
    # 걸지 않고 **되돌아갈 때 쓸 값**만 갱신한다. 컨테이너 쪽은 언제든 그대로 건다.

    # Shrink 로 접혀 있는 동안에도 같다 - 컨테이너에는 걸지 않고 **펼 때 쓸 값**만 갱신한다.

    def setFixedHeight(self, height):
        if self._text_limits is None:
            self.text.setFixedHeight(height)
        else:
            self._text_limits = (height, height)
        total = height + self._chrome_height()
        if self._container_limits is None:
            super(JUN_mod_log_qt_v01, self).setFixedHeight(total)
        else:
            self._container_limits = (total, total)

    def setMinimumHeight(self, height):
        if self._text_limits is None:
            self.text.setMinimumHeight(height)
        else:
            self._text_limits = (height, self._text_limits[1])
        total = height + self._chrome_height()
        if self._container_limits is None:
            super(JUN_mod_log_qt_v01, self).setMinimumHeight(total)
        else:
            self._container_limits = (total, self._container_limits[1])

    def setMaximumHeight(self, height):
        if self._text_limits is None:
            self.text.setMaximumHeight(height)
        else:
            self._text_limits = (self._text_limits[0], height)
        total = height + self._chrome_height()
        if self._container_limits is None:
            super(JUN_mod_log_qt_v01, self).setMaximumHeight(total)
        else:
            self._container_limits = (self._container_limits[0], total)

    def setFont(self, font):
        self.text.setFont(font)

    # ==================================================================
    # 나머지는 내부 텍스트로
    # ==================================================================

    def __getattr__(self, name):
        """`QWidget` 에 없는 이름은 내부 텍스트에 넘긴다(기존 호출부 호환).

        `moveCursor` · `verticalScrollBar` · `setLineWrapMode` · `document` 처럼
        툴이 쓰던 호출이 그대로 동작한다. 단 `copy()` 는 `QTextEdit` 의 **선택 영역
        복사**이므로, 전문 복사는 `copy_to_clipboard()` 를 쓴다.
        """
        text = self.__dict__.get("text")
        if text is None:
            raise AttributeError(name)
        return getattr(text, name)

    # ==================================================================
    # 내부
    # ==================================================================

    def _sync_body_visibility(self):
        """텍스트 · 자리 안내 라벨의 표시 여부를 (확장, 접힘) 상태에 맞춘다.

            확장 X / 접힘 X : 텍스트 보임
            확장 X / 접힘 O : 둘 다 숨김(버튼 줄만)
            확장 O / 접힘 X : 확장 창의 텍스트 보임 + 제자리에 안내 라벨
            확장 O / 접힘 O : 확장 창의 텍스트 보임, 제자리는 비운다
        """
        expanded = self._window is not None
        shrunk = self._container_limits is not None
        self.text.setVisible(expanded or not shrunk)
        self.placeholder.setVisible(expanded and not shrunk)

    @staticmethod
    def _activate_layout(owner):
        """owner 의 최상위 레이아웃을 지금 계산시킨다.

        ★ `owner.layout()` 으로 부르지 않는다 - 툴 창이 `self.layout = QVBoxLayout(self)` 처럼
        같은 이름의 **속성**을 두면 메서드가 가려져 `'QVBoxLayout' object is not callable` 이 난다
        (A00004_base_QT 템플릿이 그렇다). 클래스 메서드로 직접 부른다.
        """
        layout = QWidget.layout(owner)
        if layout is not None:
            layout.activate()

    def _resize_owner(self, shrink_by, owner_height=None):
        """최상위 툴 창 높이를 Shrink 에 맞춰 줄이거나(shrink_by=int) 되돌린다(None).

        줄일 때는 **실제로 줄어든 양**을 기억한다 - 창 최소 높이에 걸려 덜 줄었는데 펼 때 전부
        더하면 창이 누를 때마다 조금씩 커진다. 되돌릴 때는 owner_height(제약을 풀기 전에 잰
        창 높이)에 그 양을 더한다.
        """
        owner = self.window()
        usable = (self._resize_window_on_shrink and owner is not None and owner is not self
                  and owner.isWindow()
                  and not (owner.windowState() & (Qt.WindowMaximized | Qt.WindowFullScreen)))

        if shrink_by is None:
            delta, self._window_shrink_delta = self._window_shrink_delta, 0
            if usable and delta > 0:
                self._activate_layout(owner)
                base = owner_height if owner_height else owner.height()
                owner.resize(owner.width(), max(base + delta, owner.height()))
            return

        self._window_shrink_delta = 0
        if not usable or shrink_by <= 0:
            return
        # 방금 바꾼 표시/제약이 창의 최소 크기에 반영되게 레이아웃을 먼저 돌린다.
        self._activate_layout(owner)
        before = owner.height()
        target = max(before - shrink_by, owner.minimumSizeHint().height(), owner.minimumHeight())
        if target < before:
            owner.resize(owner.width(), target)
            self._window_shrink_delta = before - owner.height()

    def _watch_owner_close(self):
        """툴 창이 닫히면 자동으로 접는다.

        로그가 확장 창에 가 있는 채로 툴 창이 파괴되면 텍스트까지 함께 사라진다.
        각 툴이 closeEvent 에 정리 코드를 넣지 않아도 되도록 여기서 감시한다.
        """
        owner = self.window()
        if owner is None or owner is self._filtered:
            return
        owner.installEventFilter(self)
        self._filtered = owner

    def eventFilter(self, watched, event):
        if watched is self._filtered and event.type() == QEvent.Close:
            self.collapse()
        return super(JUN_mod_log_qt_v01, self).eventFilter(watched, event)
