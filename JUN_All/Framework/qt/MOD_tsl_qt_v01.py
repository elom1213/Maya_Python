# -*- coding: utf-8 -*-
"""
JUN_mod_tsl_qt_v01 - 재사용 PySide textScrollList 위젯.

Framework/ui/MOD_tsl_01_01.py (maya.cmds 버전 JUN_mod_tsl_v01) 의 PySide 대응물.
UI 구성과 동작을 동일하게 맞추되 Qt 관용 생성자 방식으로 제공한다.

UI 순서 (MOD_tsl_01_01 과 동일):
    Select Objects 버튼 → 타이틀 + Number 라벨 → QListWidget(다중선택)
    → Add / Del / Up / Down 버튼 → Sort 버튼

각 버튼은 show_* 플래그로 개별 생성 여부를 제어한다.
Maya 접근(현재 선택 가져오기 / 씬에서 선택)은 위젯이 직접 maya.cmds 를 호출한다.
Maya 밖에서도 import / 위젯 생성이 가능하도록 cmds 는 메서드 내부에서 lazy import 하고,
실패하면 조용히 무시한다.
"""

from Framework.qt.qt import *


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None 반환."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


class JUN_mod_tsl_qt_v01(QWidget):

    def __init__(self, title="List",
                 show_select=True, show_add=True, show_del=True,
                 show_up=True, show_down=True, show_sort=True,
                 multi_select=True, list_min_height=None,
                 select_label="Select Objects",
                 log_callback=None, parent=None):
        super(JUN_mod_tsl_qt_v01, self).__init__(parent)

        self.title = title
        self.select_label = select_label
        self.show_select = show_select
        self.show_add = show_add
        self.show_del = show_del
        self.show_up = show_up
        self.show_down = show_down
        self.show_sort = show_sort
        self.multi_select = multi_select
        self.list_min_height = list_min_height
        # 중복 안내 등 메시지를 출력할 콜백. None 이면 print 사용(툴 로그창에 연결 가능).
        self.log_callback = log_callback

        self._build_ui()

    # ================================================================
    # UI 구성
    # ================================================================

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        # Select 버튼 (현재 선택으로 리스트 교체). 라벨은 select_label 로 커스텀 가능.
        if self.show_select:
            self.btn_select = QPushButton(self.select_label)
            self.btn_select.clicked.connect(self._on_select)
            layout.addWidget(self.btn_select)

        # 헤더 행: 타이틀(bold) + Number 라벨
        header = QHBoxLayout()
        lbl_title = QLabel(self.title)
        font = lbl_title.font()
        font.setBold(True)
        lbl_title.setFont(font)
        header.addWidget(lbl_title)
        header.addStretch(1)
        self.lbl_number = QLabel("Number: 0")
        header.addWidget(self.lbl_number)
        layout.addLayout(header)

        # 리스트 위젯
        self.list_widget = QListWidget()
        mode = (QAbstractItemView.ExtendedSelection
                if self.multi_select else QAbstractItemView.SingleSelection)
        self.list_widget.setSelectionMode(mode)
        if self.list_min_height:
            self.list_widget.setMinimumHeight(self.list_min_height)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        # 편집 버튼 행: Add / Del / Up / Down (+ add_button 으로 커스텀 버튼 추가 가능)
        self.edit_row = QHBoxLayout()
        if self.show_add:
            btn = QPushButton("Add")
            btn.clicked.connect(self._on_add)
            self.edit_row.addWidget(btn)
        if self.show_del:
            btn = QPushButton("Del")
            btn.clicked.connect(self._on_del)
            self.edit_row.addWidget(btn)
        if self.show_up:
            btn = QPushButton("Up")
            btn.clicked.connect(self._on_up)
            self.edit_row.addWidget(btn)
        if self.show_down:
            btn = QPushButton("Down")
            btn.clicked.connect(self._on_down)
            self.edit_row.addWidget(btn)
        # add_button 으로 나중에 버튼을 끼워넣을 수 있도록 항상 레이아웃을 추가한다.
        layout.addLayout(self.edit_row)

        # Sort 버튼
        if self.show_sort:
            self.btn_sort = QPushButton("Sort")
            self.btn_sort.clicked.connect(self._on_sort)
            layout.addWidget(self.btn_sort)

    # ================================================================
    # 공개 API
    # ================================================================

    def get_all_items(self):
        return [self.list_widget.item(i).text()
                for i in range(self.list_widget.count())]

    def set_items(self, items):
        # 프로그램적 채우기 중에는 시그널을 막아 불필요한 씬 선택을 방지한다.
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        if items:
            self.list_widget.addItems(items)
        self.list_widget.blockSignals(False)
        self._update_number()

    def append_unique(self, items):
        """중복 없이 추가. 이미 있으면 로그 콜백(없으면 print)으로 안내."""
        existing = self.get_all_items()
        for item in items or []:
            if item in existing:
                self._log("{0} is already in the list.".format(item))
            else:
                self.list_widget.addItem(item)
                existing.append(item)
        self._update_number()

    def selected_items(self):
        return [item.text() for item in self.list_widget.selectedItems()]

    def selected_rows(self):
        return sorted(idx.row() for idx in self.list_widget.selectedIndexes())

    def select_by_texts(self, texts):
        """주어진 텍스트와 일치하는 항목을 리스트에서 선택(씬 선택 시그널은 막음)."""
        target = set(texts or [])
        self.list_widget.blockSignals(True)
        self.list_widget.clearSelection()
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() in target:
                self.list_widget.item(i).setSelected(True)
        self.list_widget.blockSignals(False)

    def add_button(self, label, callback, index=None):
        """편집 버튼 행에 커스텀 버튼을 추가한다. index=None 이면 맨 뒤에 붙인다."""
        btn = QPushButton(label)
        btn.clicked.connect(callback)
        if index is None:
            self.edit_row.addWidget(btn)
        else:
            self.edit_row.insertWidget(index, btn)
        return btn

    def count(self):
        return self.list_widget.count()

    def clear(self):
        self.list_widget.clear()
        self._update_number()

    # ================================================================
    # 내부 슬롯 / 헬퍼
    # ================================================================

    def _update_number(self):
        self.lbl_number.setText("Number: {0}".format(self.list_widget.count()))

    def _log(self, message):
        if callable(self.log_callback):
            self.log_callback(message)
        else:
            print(message)

    def _maya_selection(self):
        cmds = _cmds()
        if cmds is None:
            return []
        return cmds.ls(sl=True, fl=True) or []

    def _on_select(self):
        """현재 Maya 선택으로 리스트를 교체."""
        self.set_items(self._maya_selection())

    def _on_add(self):
        """현재 Maya 선택을 중복 없이 추가."""
        self.append_unique(self._maya_selection())

    def _on_del(self):
        for row in reversed(self.selected_rows()):
            self.list_widget.takeItem(row)
        self._update_number()

    def _on_up(self):
        """선택 항목을 한 칸 위로 이동(MOD_tsl BF_LIST_moveUp_index 로직 이식)."""
        items = self.get_all_items()
        rows = self.selected_rows()
        if not rows:
            return
        result_rows = []
        for r in rows:
            if r - 1 < 0:
                result_rows.append(r)
                continue
            moved = items.pop(r)
            items.insert(r - 1, moved)
            result_rows.append(r - 1)
        self.set_items(items)
        self._reselect_rows(result_rows)

    def _on_down(self):
        """선택 항목을 한 칸 아래로 이동(MOD_tsl BF_LIST_moveDown_index 로직 이식)."""
        items = self.get_all_items()
        rows = self.selected_rows()
        if not rows:
            return
        result_rows = []
        for r in reversed(rows):
            if r + 1 >= len(items):
                result_rows.append(r)
                continue
            moved = items.pop(r)
            items.insert(r + 1, moved)
            result_rows.append(r + 1)
        self.set_items(items)
        self._reselect_rows(result_rows)

    def _on_sort(self):
        self.set_items(sorted(self.get_all_items()))

    def _on_selection_changed(self):
        """리스트 항목 선택 시 Maya 씬에서 선택."""
        cmds = _cmds()
        if cmds is None:
            return
        items = self.selected_items()
        if items:
            try:
                cmds.select(items)
            except Exception:
                pass

    def _reselect_rows(self, rows):
        for r in rows:
            if 0 <= r < self.list_widget.count():
                self.list_widget.item(r).setSelected(True)
