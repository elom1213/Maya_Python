# -*- coding: utf-8 -*-
"""
JUN_mod_filter_qt_v01 - QListWidget 용 재사용 검색(필터) 위젯.

A00290_BSTool 의 Base Shape / Shape Editor 탭에서 쓰던 Filter 를 공용으로 뽑았다.
**입력하는 즉시 일치하는 항목만 남고 나머지는 숨는다** — 항목을 지우는 게 아니라
`setHidden` 으로 가리므로, 필터를 비우면 그대로 되돌아온다.

    Filter [ inner            ] [Clear]      Number: 2 / 9

규칙
----
- **부분 일치**(`Inner` -> `browInnerUp`), **대소문자 무시**.
- 공백으로 나눈 여러 토큰은 **AND** 로 본다(`brow up` -> `browInnerUp`).
  한 단어만 쓰면 예전과 동일하게 동작한다.

"보이는 것이 작업 대상"
----------------------
Qt 는 항목을 **숨겨도 선택 상태를 유지**한다. 그래서 필터를 건 채 "선택된 것"을 그냥
쓰면 **가려서 안 보이는 항목까지 작업 대상이 된다** — 사용자가 예상할 수 없는 동작이다.
이 위젯은 그걸 막는 두 헬퍼를 제공한다:

    names, hidden = flt.visible_selected()   # 보이는 선택만 + 가려진 선택 수
    flt.select_all_visible()                 # QListWidget.selectAll 대체

`hidden` 이 0 이 아니면 호출부가 로그로 알려 주는 것까지가 이 규칙의 완성이다.

사용법
------
    from Framework.qt import JUN_mod_filter_qt

    self.flt = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
        self.lw_targets, number_label=self.lbl_number)
    layout.addWidget(self.flt)

    # 목록을 다시 채운 뒤에는 필터를 다시 먹인다(필터가 유지되도록)
    self.lw_targets.clear()
    self.lw_targets.addItems(names)
    self.flt.refresh()

number_label 을 주면 `Number: N`(필터 없음) / `Number: 보이는수 / 전체수`(필터 중)로
자동 갱신한다. 라벨을 안 쓰면 생략해도 된다.
"""

from Framework.qt.qt import *


class JUN_mod_filter_qt_v01(QWidget):

    #: 필터가 바뀔 때마다 (보이는 수, 전체 수) 로 발생
    filtered = Signal(int, int)

    def __init__(self, list_widget=None, label="Filter",
                 placeholder="Type any part of a name (e.g. Inner)",
                 show_clear=True, number_label=None, parent=None):
        super(JUN_mod_filter_qt_v01, self).__init__(parent)

        self.list_widget = None
        self.number_label = number_label

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        if label:
            row.addWidget(QLabel(label))

        self.le_filter = QLineEdit()
        self.le_filter.setPlaceholderText(placeholder)
        self.le_filter.setToolTip(
            "Show only entries whose name contains this text (case-insensitive).\n"
            "Space-separated words all have to match.\n"
            "Actions apply to the visible entries only.")
        self.le_filter.textChanged.connect(self._on_text_changed)
        row.addWidget(self.le_filter, 1)

        self.btn_clear = None
        if show_clear:
            self.btn_clear = QPushButton("Clear")
            self.btn_clear.setToolTip("Clear the filter and show every entry.")
            self.btn_clear.clicked.connect(self.le_filter.clear)
            row.addWidget(self.btn_clear)

        if list_widget is not None:
            self.attach(list_widget)

    # ================================================================
    # 연결 / 조회
    # ================================================================

    def attach(self, list_widget):
        """필터를 걸 QListWidget 을 지정하고 즉시 한 번 적용한다."""
        self.list_widget = list_widget
        self.refresh()

    def text(self):
        return self.le_filter.text()

    def set_text(self, text):
        self.le_filter.setText(text or "")

    def clear(self):
        self.le_filter.clear()

    # ================================================================
    # 필터 적용
    # ================================================================

    @staticmethod
    def _matches(name, tokens):
        low = name.lower()
        return all(t in low for t in tokens)

    def refresh(self):
        """현재 입력값으로 목록을 다시 거른다.

        목록을 새로 채운 뒤에 반드시 호출한다 — 새 항목은 숨김 상태가 초기화돼
        있으므로, 이걸 부르지 않으면 필터가 걸린 채로 전부 보이게 된다.
        """
        if self.list_widget is None:
            return 0, 0

        tokens = [t for t in self.le_filter.text().strip().lower().split() if t]
        total = self.list_widget.count()
        shown = 0

        for i in range(total):
            item = self.list_widget.item(i)
            hit = True if not tokens else self._matches(item.text(), tokens)
            item.setHidden(not hit)
            if hit:
                shown += 1

        self._update_number(shown, total)
        self.filtered.emit(shown, total)
        return shown, total

    def _on_text_changed(self, _text):
        self.refresh()

    def _update_number(self, shown, total):
        if self.number_label is None:
            return
        if shown == total:
            self.number_label.setText("Number: {0}".format(total))
        else:
            self.number_label.setText("Number: {0} / {1}".format(shown, total))

    # ================================================================
    # "보이는 것이 작업 대상"
    # ================================================================

    def visible_items(self):
        """지금 보이는 항목들."""
        if self.list_widget is None:
            return []
        return [self.list_widget.item(i) for i in range(self.list_widget.count())
                if not self.list_widget.item(i).isHidden()]

    def visible_texts(self):
        return [it.text() for it in self.visible_items()]

    def visible_selected(self):
        """(보이면서 선택된 이름들, 필터에 가려진 선택 수).

        Qt 는 숨긴 항목의 선택을 유지하므로, 작업 대상은 이 함수로 고른다.
        가려진 선택 수가 0 이 아니면 호출부가 로그로 알려 준다.
        """
        if self.list_widget is None:
            return [], 0
        names, hidden = [], 0
        for item in self.list_widget.selectedItems():
            if item.isHidden():
                hidden += 1
            else:
                names.append(item.text())
        return names, hidden

    def select_all_visible(self):
        """보이는 항목만 전체 선택(가려진 것까지 잡는 selectAll 대체)."""
        if self.list_widget is None:
            return
        self.list_widget.clearSelection()
        for item in self.visible_items():
            item.setSelected(True)
