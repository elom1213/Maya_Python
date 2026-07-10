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

UUID 보관 (v01.01~)
-------------------
항목의 표시 텍스트는 예전처럼 노드 이름이지만, 씬 노드인 항목은 **UUID 도 함께** 보관한다
(`Qt.UserRole + 1`). 리스트에서 항목을 고를 때는 이름이 아니라 UUID 로 현재 경로를 되찾아
씬에서 선택한다. 이름 기반은 항목을 담은 뒤 씬이 바뀌면 조용히 실패했다:

    - 오브젝트를 리네임/리페어런트  -> "No object matches name"
    - 같은 이름 오브젝트가 하나 더 생김 -> "More than one object matches name"

UUID 는 리네임·리페어런트·이름 충돌과 무관하므로 두 경우 모두 해결된다.

노드가 아닌 항목(어트리뷰트 이름, 파일명, 노드 타입 이름 등)은 UUID 가 없으므로 예전처럼
이름으로 동작하고, 씬에 없는 이름이면 조용히 건너뛴다.
`pCube1Shape.vtx[0]` 같은 컴포넌트는 `<uuid>.vtx[0]` 를 cmds.ls 로 되돌릴 수 없어서,
**노드 UUID + 컴포넌트 접미사**를 따로 보관했다가 선택할 때 다시 조립한다.
"""

from Framework.qt.qt import *


# 리스트가 좁은 공간(예: 창 자동 fit, 로그창과의 공간 경쟁)에서 거의 0 높이로
# 찌그러지지 않도록 보장하는 기본 최소 높이. 호출부가 list_min_height 를 주면 그 값을,
# 안 주면 이 바닥값을 적용한다. (공간이 충분하면 위젯은 이보다 크게 늘어난다)
DEFAULT_LIST_MIN_HEIGHT = 100

# 항목에 (uuid, component) 를 보관하는 Qt 역할. 호출부가 Qt.UserRole 을 쓰는 경우와
# 겹치지 않도록 +1 을 쓴다.
UUID_ROLE = Qt.UserRole + 1


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None 반환."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


def _split_component(name):
    """'grpA|pCube1|pCube1Shape.vtx[0]' -> ('grpA|pCube1|pCube1Shape', 'vtx[0]').

    DAG 이름에는 '.' 이 들어갈 수 없으므로, 첫 '.' 앞이 노드 / 뒤가 컴포넌트다.
    """
    node, _, comp = name.partition(".")
    return node, comp


def _uuid_of(name):
    """이름 -> (uuid, component). 씬 노드가 아니거나 이름이 애매하면 (None, "").

    담는 시점에 이름이 애매하면(같은 이름 노드가 여럿) 어느 것인지 알 수 없으므로
    UUID 를 붙이지 않고 이름 폴백에 맡긴다.
    """
    cmds = _cmds()
    if cmds is None or not name:
        return None, ""

    node, comp = _split_component(name)
    try:
        found = cmds.ls(node, uuid=True) or []
    except Exception:
        return None, ""

    return (found[0], comp) if len(found) == 1 else (None, "")


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
        # 항상 최소 높이를 보장한다(명시값이 없으면 기본 바닥값). 창이 콘텐츠에 맞춰
        # 자동으로 줄거나 로그창과 공간을 나눌 때도 리스트가 사라질 만큼 작아지지 않게 한다.
        self.list_widget.setMinimumHeight(
            self.list_min_height or DEFAULT_LIST_MIN_HEIGHT)
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
        """표시 텍스트(노드 이름) 목록. 하위호환을 위해 반환 타입은 그대로 문자열."""
        return [self.list_widget.item(i).text()
                for i in range(self.list_widget.count())]

    def get_all_nodes(self):
        """UUID 로 해석한 **현재** 노드 경로 목록. 씬에서 사라진 항목은 제외한다.

        get_all_items() 와 달리 리네임/리페어런트 이후에도 올바른 경로를 준다.
        """
        return [n for n in (self._node_of(self.list_widget.item(i))
                            for i in range(self.list_widget.count()))
                if n]

    def set_items(self, items):
        # 프로그램적 채우기 중에는 시그널을 막아 불필요한 씬 선택을 방지한다.
        # addItems 로 한 번에 넣은 뒤 UUID 를 붙인다 — addItem 을 항목마다 부르면
        # model 의 rowsInserted 가 항목 수만큼 발생해, 그걸 듣고 있는 툴들
        # (A00150/A00160/A00170/A00290)의 훅이 불필요하게 여러 번 호출된다.
        texts = list(items or [])
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        if texts:
            self.list_widget.addItems(texts)
            self._attach_uuids(texts)
        self.list_widget.blockSignals(False)
        self._update_number()

    def append_unique(self, items):
        """중복 없이 추가. 이미 있으면 로그 콜백(없으면 print)으로 안내.

        중복 판정은 **UUID 우선**이다. 이름이 같아도 다른 오브젝트면 함께 담긴다
        (계층만 다른 동명 오브젝트를 양쪽에 담아야 하는 경우가 있다).
        """
        existing_uuids = set()
        existing_texts = set()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            uuid = self._uuid_of_item(item)
            if uuid:
                existing_uuids.add(uuid)
            else:
                existing_texts.add(item.text())

        for text in items or []:
            uuid, _comp = _uuid_of(text)
            duplicated = uuid in existing_uuids if uuid else text in existing_texts
            if duplicated:
                self._log("{0} is already in the list.".format(text))
                continue

            self._add_item(text)
            if uuid:
                existing_uuids.add(uuid)
            else:
                existing_texts.add(text)

        self._update_number()

    def selected_items(self):
        return [item.text() for item in self.list_widget.selectedItems()]

    def selected_nodes(self):
        """선택한 항목을 UUID 로 해석한 현재 노드 경로 목록(사라진 항목 제외)."""
        return [n for n in (self._node_of(item)
                            for item in self.list_widget.selectedItems()) if n]

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

    def _add_item(self, text):
        """텍스트로 항목을 만들고, 씬 노드면 (uuid, component) 를 함께 보관한다."""
        item = QListWidgetItem(text)
        uuid, comp = _uuid_of(text)
        if uuid:
            item.setData(UUID_ROLE, (uuid, comp))
        self.list_widget.addItem(item)
        return item

    def _attach_uuids(self, texts, offset=0):
        """이미 들어간 항목들(offset 부터)에 UUID 를 붙인다."""
        for i, text in enumerate(texts):
            uuid, comp = _uuid_of(text)
            if uuid:
                self.list_widget.item(offset + i).setData(UUID_ROLE, (uuid, comp))

    @staticmethod
    def _uuid_of_item(item):
        data = item.data(UUID_ROLE) if item is not None else None
        return data[0] if data else None

    def _node_of(self, item):
        """항목이 가리키는 **현재** 노드 경로. 씬에 없으면 None.

        UUID 가 있으면 그것으로 되찾고(리네임/리페어런트/동명 안전),
        없으면(어트리뷰트 이름 등 노드가 아닌 항목) 텍스트를 그대로 쓴다.
        """
        cmds = _cmds()
        if cmds is None or item is None:
            return None

        data = item.data(UUID_ROLE)
        if data:
            uuid, comp = data
            found = cmds.ls(uuid, long=True) or []
            if not found:
                return None
            return "{0}.{1}".format(found[0], comp) if comp else found[0]

        text = item.text()
        try:
            return text if cmds.objExists(text) else None
        except Exception:
            return None

    def _records(self):
        """[(텍스트, uuid데이터), ...] — 재정렬 시 UUID 를 잃지 않기 위한 스냅샷."""
        return [(self.list_widget.item(i).text(),
                 self.list_widget.item(i).data(UUID_ROLE))
                for i in range(self.list_widget.count())]

    def _set_records(self, records):
        # set_items 와 같은 이유로 addItems 한 번 + setData (rowsInserted 1회).
        # 여기서는 UUID 를 다시 조회하지 않고 기존 값을 그대로 옮긴다.
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        if records:
            self.list_widget.addItems([text for text, _ in records])
            for i, (_text, data) in enumerate(records):
                if data:
                    self.list_widget.item(i).setData(UUID_ROLE, data)
        self.list_widget.blockSignals(False)
        self._update_number()

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
        # 재정렬은 텍스트가 아니라 레코드로 옮긴다(항목의 UUID 를 잃지 않도록).
        items = self._records()
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
        self._set_records(items)
        self._reselect_rows(result_rows)

    def _on_down(self):
        """선택 항목을 한 칸 아래로 이동(MOD_tsl BF_LIST_moveDown_index 로직 이식)."""
        items = self._records()
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
        self._set_records(items)
        self._reselect_rows(result_rows)

    def _on_sort(self):
        self._set_records(sorted(self._records(), key=lambda rec: rec[0]))

    def _on_selection_changed(self):
        """리스트 항목 선택 시 Maya 씬에서 선택.

        UUID 로 현재 경로를 되찾아 선택하므로, 담은 뒤 리네임/리페어런트 됐거나
        같은 이름의 오브젝트가 늘어나도 정확히 그 오브젝트가 잡힌다.
        노드가 아닌 항목(어트리뷰트 이름 등)은 조용히 건너뛴다.
        """
        cmds = _cmds()
        if cmds is None:
            return

        items = self.list_widget.selectedItems()
        if not items:
            return

        nodes, missing = [], []
        for item in items:
            node = self._node_of(item)
            if node:
                nodes.append(node)
            elif self._uuid_of_item(item):
                # UUID 를 알고 있는데 못 찾는다 = 씬에서 삭제됨. 알릴 가치가 있다.
                missing.append(item.text())

        if nodes:
            try:
                cmds.select(nodes, replace=True)
            except Exception as e:
                self._log("Failed to select in the scene: {0}".format(e))

        if missing:
            self._log("Not in the scene anymore: {0}".format(", ".join(missing)))

    def _reselect_rows(self, rows):
        for r in rows:
            if 0 <= r < self.list_widget.count():
                self.list_widget.item(r).setSelected(True)
