# -*- coding: utf-8 -*-
"""
JUN_mod_tsl_qt_v01 - 재사용 PySide textScrollList 위젯.

Framework/ui/MOD_tsl_01_01.py (maya.cmds 버전 JUN_mod_tsl_v01) 의 PySide 대응물.
UI 구성과 동작을 동일하게 맞추되 Qt 관용 생성자 방식으로 제공한다.

UI 순서 (MOD_tsl_01_01 과 동일):
    Select Objects 버튼 → 타이틀 + (선택) Order 체크박스 + Number 라벨
    → QListWidget(다중선택) → Add / Del / Up / Down 버튼 → Sort 버튼 → (선택) Reverse 버튼

각 버튼은 show_* 플래그로 개별 생성 여부를 제어한다.
Reverse 버튼(show_reverse, 기본 꺼짐)은 리스트 항목의 정렬 순서를 통째로 뒤집는다.
Order 체크박스(show_order, 기본 켬 / 체크 상태는 기본 꺼짐)는 아래 "선택 순서 유지" 참고.
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
이름으로 동작하고, 씬에 없는 이름이면 조용히 건너뛴다. **애초에 노드 이름이 될 수 없는 모양**
(공백·`@` 처럼 마야가 이름에 허용하지 않는 글자, 숫자로 시작 등)이면 마야에 묻지도 않는다
(`_looks_like_node`) — 헛도는 마야 호출을 줄이고, `cmds.ls` 가 그런 문자열에 예외를 던지는
경우(예: `@cache pCube1`)도 피한다. A00145 의 스냅샷 항목이 이 경로로 리스트에 얹힌다.
`pCube1Shape.vtx[0]` 같은 컴포넌트는 `<uuid>.vtx[0]` 를 cmds.ls 로 되돌릴 수 없어서,
**노드 UUID + 컴포넌트 접미사**를 따로 보관했다가 선택할 때 다시 조립한다.

중복 UUID (다중 레퍼런스)
------------------------
UUID 는 보통 씬에서 유일하지만 **항상** 그렇진 않다. 같은 파일을 **레퍼런스**로 여러 번
걸면(네임스페이스만 다르게) 각 사본의 대응 노드가 **같은 UUID 를 공유**한다(import 는 UUID 를
재할당하지만 reference 는 원본 UUID 를 유지). 이 경우 `cmds.ls(uuid, long=True)` 가 **여러 노드**를
돌려주므로 `found[0]` 로 아무거나 고르면 안 된다(어느 항목을 눌러도 늘 첫 노드만 선택되는 버그).
`_node_of` 는 UUID 가 여러 노드로 잡히면 **담을 때의 표시 이름으로 그중 하나를 좁혀** 고르고
(`_match_by_text`), 이름으로도 못 좁히면 첫 번째로 폴백한다. UUID 가 유일할 때의 동작
(리네임/리페어런트 안전)은 그대로다.

요약 모드 (list_limit)
----------------------
`list_limit` 을 주면 항목이 그 수 **이상**일 때 리스트에 펼치지 않고 **요약 라벨 + List All 버튼**만
보여준다(기본 0 = 언제나 펼침). 수천 개를 QListWidget 에 넣는 것도 느리지만 진짜 비용은 항목마다
`cmds.ls(name, uuid=True)` 를 부르는 UUID 부착이다 — 항목 수만큼 마야 호출이 나간다.

요약 모드에서는 표시 텍스트만 파이썬 리스트로 들고 있으므로 Select/Add/Sort/set_items 가 항목 수와
거의 무관하게 끝난다. `get_all_items()` / `count()` / `set_items()` 는 그대로 동작하니 호출부는
바꿀 것이 없다. 대신 **UUID 를 붙이지 않는다** — 요약 모드의 `get_all_nodes()` 는 이름으로 해석하므로
담은 뒤 리네임된 항목은 빠진다. 전부 보고 싶으면(또는 UUID 이점이 필요하면) **List All** 을 누른다.
그때 리스트를 채우고 UUID 를 붙인다 — 느린 경로를 사용자가 명시적으로 고르는 셈이다.
(다시 Select 하면 항목 수에 따라 요약 모드로 돌아간다)


선택 순서 유지 (Order 토글)
--------------------------
`cmds.ls(sl=True)` 는 **컴포넌트**(vtx/edge/face)를 고른 순서가 아니라 **인덱스 순서**로
돌려준다. 버텍스를 5→0→3→1 로 찍어도 리스트에는 0,1,3,5 로 올라온다는 뜻이다
(오브젝트/트랜스폼은 pref 와 무관하게 이미 선택 순서를 유지한다 — 순서가 깨지는 건 컴포넌트뿐).

선택 순서를 얻으려면 Maya 의 **Track Selection Order** 프리퍼런스가 켜져 있어야 하고
(`cmds.selectPref(trackSelectionOrder=True)`), 그 뒤 `cmds.ls(orderedSelection=True)` 로 읽는다.
pref 가 꺼져 있으면 `ls(orderedSelection=True)` 는 **에러 없이 조용히 인덱스 순서**를 돌려주므로
"순서가 되는지"는 반환값이 아니라 pref 를 직접 조회해서 판단해야 한다.

이 pref 는 **Maya 전역 설정**이라 항상 켜두는 대신 헤더의 **Order 체크박스**로 켤 때만 켠다:

    - 체크 ON  : pref 를 켜고(원래 값 기억) Select/Add 가 `ls(orderedSelection=True, fl=True)` 사용
    - 체크 OFF : 우리가 켠 경우에만 pref 를 원래대로 되돌리고 기존 동작(`ls(sl=True)`)으로 복귀

pref 는 **켠 시점부터** 순서를 기록하므로, 체크한 뒤 **다시 선택해야** 순서가 잡힌다(로그로 안내).
여러 TSL 위젯이 동시에 켜는 경우를 위해 모듈 전역 refcount(`_ORDER_REF`)로 pref 를 관리한다.
"""

import re

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


# Track Selection Order 프리퍼런스 refcount.
#   count : 지금 이 pref 를 요구하고 있는 위젯 수
#   prev  : 첫 위젯이 켜기 직전의 원래 pref 값(마지막 위젯이 끌 때 이 값으로 되돌린다)
# 한 씬에 TSL 위젯이 여러 개 떠 있어도 하나가 꺼질 때 다른 위젯의 순서 추적이
# 끊기지 않도록 전역으로 관리한다.
_ORDER_REF = {"count": 0, "prev": None}


def _get_track_order():
    """Track Selection Order pref 값. Maya 밖이거나 조회 실패면 None."""
    cmds = _cmds()
    if cmds is None:
        return None
    try:
        return bool(cmds.selectPref(q=True, trackSelectionOrder=True))
    except Exception:
        return None


def _set_track_order(value):
    cmds = _cmds()
    if cmds is None:
        return False
    try:
        cmds.selectPref(trackSelectionOrder=bool(value))
        return True
    except Exception:
        return False


def _acquire_order_tracking():
    """순서 추적 사용을 선언. 첫 사용자면 pref 를 켜고 원래 값을 기억한다."""
    if _ORDER_REF["count"] == 0:
        prev = _get_track_order()
        _ORDER_REF["prev"] = prev
        if prev is False:
            _set_track_order(True)
    _ORDER_REF["count"] += 1


def _release_order_tracking():
    """사용 종료. 마지막 사용자면 우리가 켠 경우에 한해 pref 를 원래대로 되돌린다."""
    if _ORDER_REF["count"] <= 0:
        _ORDER_REF["count"] = 0
        return
    _ORDER_REF["count"] -= 1
    if _ORDER_REF["count"] == 0:
        if _ORDER_REF["prev"] is False:
            _set_track_order(False)
        _ORDER_REF["prev"] = None


# ---- 공개 API ----------------------------------------------------------
# TSL 위젯을 쓰지 않는 툴(예: A00420_Wrapper 의 Guide Pairs 트리)도 **같은 refcount 를
# 공유**해야 한다. 각자 selectPref 를 직접 켜고 끄면, 한 창이 닫힐 때 다른 창의 순서
# 추적까지 꺼져 버린다. 그래서 위 내부 헬퍼를 이 이름들로 열어 둔다.

def acquire_order_tracking():
    """Track Selection Order pref 사용을 선언(필요하면 켠다)."""
    _acquire_order_tracking()


def release_order_tracking():
    """사용 종료. 마지막 사용자면 우리가 켠 경우에 한해 원래 값으로 되돌린다."""
    _release_order_tracking()


def is_order_tracking():
    """지금 Track Selection Order pref 가 켜져 있는지(누가 켰든). 조회 실패면 False."""
    return bool(_get_track_order())


# 마야 노드/컴포넌트 이름이 될 수 있는 모양인가. 노드 이름은 글자나 `_` 로 시작하고
# (롱네임이면 `|`), 그 뒤로 글자/숫자/`_` 와 경로·네임스페이스·컴포넌트 구분자만 온다.
# 공백이나 `@` 같은 글자는 마야가 이름에 허용하지 않으므로 그런 문자열은 노드일 수 없다.
_NODE_NAME_RE = re.compile(r"^[|A-Za-z_][A-Za-z0-9_|:.\[\]]*$")


def _looks_like_node(name):
    """이 텍스트가 씬 노드 이름일 수 있는가. 아니면 마야에 물어볼 필요조차 없다."""
    return bool(name) and bool(_NODE_NAME_RE.match(name))


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
    if cmds is None or not _looks_like_node(name):
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
                 show_reverse=False, show_order=True, order_default=False,
                 multi_select=True, list_min_height=None, list_limit=0,
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
        # Reverse 버튼(리스트 순서 뒤집기). 기본 꺼짐 — 원하는 툴만 켠다.
        self.show_reverse = show_reverse
        # Order 체크박스(선택 순서 유지). 헤더 행에 들어가므로 세로 공간을 더 먹지 않는다.
        self.show_order = show_order
        self.multi_select = multi_select
        self.list_min_height = list_min_height
        # 항목이 이 수 **이상**이면 리스트에 펼치지 않고 요약만 보여준다(0 = 언제나 펼침).
        self.list_limit = int(list_limit or 0)
        # 중복 안내 등 메시지를 출력할 콜백. None 이면 print 사용(툴 로그창에 연결 가능).
        self.log_callback = log_callback

        # 순서 추적 상태(체크박스가 없어도 set_order_tracking 으로 켤 수 있다).
        # dict 로 두는 이유: destroyed 슬롯이 self 를 붙잡지 않도록 이 홀더만 캡처시킨다
        # (C++ 위젯이 먼저 파괴된 뒤 self 속성에 접근하면 위험하다).
        self._order_state = {"on": False}
        self.chk_order = None

        # 요약 모드에서 보관 중인 표시 텍스트들. None 이면 리스트에 그대로 펼쳐져 있다.
        self._deferred = None

        self._build_ui()

        # 위젯이 없어질 때 우리가 켠 pref 를 놓아준다(전역 설정을 남기지 않도록).
        self.destroyed.connect(
            lambda *_a, _s=self._order_state: _release_order_tracking() if _s["on"] else None)

        if order_default:
            self.set_order_tracking(True, quiet=True)

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

        # 헤더 행: 타이틀(bold) + (선택) Order 체크박스 + Number 라벨
        header = QHBoxLayout()
        lbl_title = QLabel(self.title)
        font = lbl_title.font()
        font.setBold(True)
        lbl_title.setFont(font)
        header.addWidget(lbl_title)
        header.addStretch(1)
        # Order 체크박스 — 켜면 Maya 에서 "고른 순서"대로 리스트에 담는다.
        if self.show_order:
            self.chk_order = QCheckBox("Order")
            self.chk_order.setToolTip(
                "List items in the order you picked them in Maya.\n"
                "Vertices/edges/faces are otherwise listed by index, not by pick order.\n"
                "While checked, Maya's 'Track Selection Order' preference is turned on\n"
                "(restored when unchecked). Re-pick after checking it - the order is\n"
                "only recorded from that point on.")
            self.chk_order.toggled.connect(self._on_order_toggled)
            header.addWidget(self.chk_order)
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

        # 요약 모드용 위젯 — list_limit 을 준 툴에서만 만든다(다른 툴의 레이아웃은 그대로).
        # 리스트 대신 이 라벨이 보이고, List All 을 누르면 그때 실제로 리스트를 채운다.
        self.lbl_summary = None
        self.btn_list_all = None
        if self.list_limit:
            self.lbl_summary = QLabel("")
            self.lbl_summary.setAlignment(Qt.AlignCenter)
            self.lbl_summary.setWordWrap(True)
            self.lbl_summary.setFrameShape(QFrame.StyledPanel)
            self.lbl_summary.setMinimumHeight(
                self.list_min_height or DEFAULT_LIST_MIN_HEIGHT)
            self.lbl_summary.hide()
            layout.addWidget(self.lbl_summary)

            self.btn_list_all = QPushButton("List All")
            self.btn_list_all.setToolTip(
                "List every stored item in the box above.\n"
                "Large selections are kept summarized because filling the list "
                "(and looking up a UUID for every item) is slow.\n"
                "The items are used by the tool either way - this only changes "
                "what you see.")
            self.btn_list_all.clicked.connect(self.show_all)
            self.btn_list_all.hide()
            layout.addWidget(self.btn_list_all)

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

        # Reverse 버튼 (선택) — 리스트에 올라온 항목들의 순서를 통째로 뒤집는다.
        if self.show_reverse:
            self.btn_reverse = QPushButton("Reverse")
            self.btn_reverse.setToolTip("Reverse the order of the listed items")
            self.btn_reverse.clicked.connect(self._on_reverse)
            layout.addWidget(self.btn_reverse)

    # ================================================================
    # 공개 API
    # ================================================================

    def get_all_items(self):
        """표시 텍스트(노드 이름) 목록. 하위호환을 위해 반환 타입은 그대로 문자열.

        요약 모드면 리스트 위젯이 비어 있어도 **보관 중인 전체 목록**을 돌려준다.
        """
        if self._deferred is not None:
            return list(self._deferred)
        return [self.list_widget.item(i).text()
                for i in range(self.list_widget.count())]

    def get_all_nodes(self):
        """UUID 로 해석한 **현재** 노드 경로 목록. 씬에서 사라진 항목은 제외한다.

        get_all_items() 와 달리 리네임/리페어런트 이후에도 올바른 경로를 준다.
        요약 모드는 UUID 를 붙이지 않으므로 **이름으로** 해석한다(리네임된 항목은 빠진다).
        """
        if self._deferred is not None:
            return self._nodes_by_name(self._deferred)
        return [n for n in (self._node_of(self.list_widget.item(i))
                            for i in range(self.list_widget.count()))
                if n]

    def set_items(self, items):
        """리스트를 items 로 교체. list_limit 이상이면 펼치지 않고 요약 모드로 보관한다."""
        texts = list(items or [])
        if self.list_limit and len(texts) >= self.list_limit:
            self._defer(texts)
            return
        self._fill_list(texts)

    def append_unique(self, items):
        """중복 없이 추가. 이미 있으면 로그 콜백(없으면 print)으로 안내.

        중복 판정은 **현재 씬 경로(실제 노드 정체)** 기준이다. 담긴 항목은 UUID 로 현재
        경로를 되찾아 비교하므로 리네임/리페어런트 뒤에도 같은 오브젝트를 잡아낸다.
        같은 파일을 여러 번 **레퍼런스**해 UUID 가 공유되는 씬에서도, 네임스페이스가 다른
        복사본은 경로가 달라 **서로 다른 오브젝트로 취급**되어 둘 다 담긴다(UUID 만으로
        판정하면 뒤엣것이 중복으로 잘못 걸러졌었다). 노드가 아닌 항목(어트리뷰트 이름 등)은
        텍스트로 판정한다.
        """
        incoming = list(items or [])

        # 요약 모드이거나 합쳐서 한계를 넘길 목록이면 **텍스트 기준**으로 합친다.
        # 아래의 기본 경로는 항목마다 cmds.ls 를 부르므로 큰 목록에서 느리다.
        if self._deferred is not None or (
                self.list_limit
                and self.list_widget.count() + len(incoming) >= self.list_limit):
            self._append_texts(incoming)
            return

        cmds = _cmds()
        existing = set()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            existing.add(self._node_of(item) or item.text())

        for text in incoming:
            key = None
            if cmds is not None and _looks_like_node(text):
                try:
                    found = cmds.ls(text, long=True) or []
                    key = found[0] if len(found) == 1 else None
                except Exception:
                    key = None
            if key is None:
                key = text
            if key in existing:
                self._log("{0} is already in the list.".format(text))
                continue

            self._add_item(text)
            existing.add(key)

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

    def is_order_tracking(self):
        """선택 순서 유지가 켜져 있는지."""
        return self._order_state["on"]

    def set_order_tracking(self, enabled, quiet=False):
        """선택 순서 유지 on/off (체크박스가 없어도 코드로 켤 수 있다).

        켜면 Maya 의 Track Selection Order pref 를 켜고, 끄면 우리가 켠 경우에만
        원래 값으로 되돌린다. pref 는 **켠 시점부터** 순서를 기록하므로 켠 뒤에 다시
        선택해야 순서가 잡힌다.
        """
        enabled = bool(enabled)

        # 체크박스와 상태를 동기화(코드에서 호출된 경우 시그널 루프 방지).
        if self.chk_order is not None and self.chk_order.isChecked() != enabled:
            self.chk_order.blockSignals(True)
            self.chk_order.setChecked(enabled)
            self.chk_order.blockSignals(False)

        if enabled == self._order_state["on"]:
            return

        self._order_state["on"] = enabled
        if enabled:
            _acquire_order_tracking()
            if not quiet:
                self._log("Selection order: ON - pick your objects/components again "
                          "so the order can be recorded.")
        else:
            _release_order_tracking()
            if not quiet:
                self._log("Selection order: OFF - items are listed in Maya's default order.")

    def maya_selection(self):
        """현재 Maya 선택(flatten). Order 가 켜져 있으면 **고른 순서**로 돌려준다.

        Select/Add 버튼이 쓰는 것과 같은 규칙이므로, 호출부가 "리스트 대신 지금
        선택한 것으로 바로 실행" 하는 버튼을 만들 때 순서 처리를 다시 구현하지 않아도
        된다. Order 가 꺼져 있으면 `ls(sl=True)` 와 같다(컴포넌트는 인덱스 순서).
        """
        return self._maya_selection()

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
        if self._deferred is not None:
            return len(self._deferred)
        return self.list_widget.count()

    def clear(self):
        self._deferred = None
        self.list_widget.clear()
        self._sync_summary()
        self._update_number()

    def is_deferred(self):
        """지금 요약 모드인지 — 항목은 들고 있지만 리스트에 펼치지는 않은 상태."""
        return self._deferred is not None

    def show_all(self):
        """요약 모드로 보관 중인 항목을 리스트에 모두 펼친다(느린 경로, 버튼/호출부용).

        여기서 처음으로 UUID 를 붙이므로 항목 수만큼 마야 호출이 나간다. 다음 Select 로
        목록이 다시 채워지면 항목 수에 따라 요약 모드로 돌아간다.
        """
        if self._deferred is None:
            return
        texts = list(self._deferred)
        self._log("Listing all {0} item(s) - this can take a moment.".format(
            len(texts)))
        self._fill_list(texts)

    # ================================================================
    # 내부 슬롯 / 헬퍼
    # ================================================================

    def _fill_list(self, texts):
        """리스트 위젯을 texts 로 채운다(요약 모드 해제). list_limit 을 보지 않는다.

        프로그램적 채우기 중에는 시그널을 막아 불필요한 씬 선택을 방지한다.
        addItems 로 한 번에 넣은 뒤 UUID 를 붙인다 — addItem 을 항목마다 부르면
        model 의 rowsInserted 가 항목 수만큼 발생해, 그걸 듣고 있는 툴들
        (A00150/A00160/A00170/A00290)의 훅이 불필요하게 여러 번 호출된다.
        """
        self._deferred = None
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        if texts:
            self.list_widget.addItems(texts)
            self._attach_uuids(texts)
        self.list_widget.blockSignals(False)
        self._sync_summary()
        self._update_number()

    def _defer(self, texts):
        """요약 모드로 들어간다 — 리스트는 비우고 텍스트만 보관(UUID 조회 없음)."""
        self._deferred = list(texts)
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        self.list_widget.blockSignals(False)
        self._sync_summary()
        self._update_number()
        self._log("{0} item(s) stored, not listed (limit {1}) - "
                  "press 'List All' to show them.".format(
                      len(self._deferred), self.list_limit))

    def _sync_summary(self):
        """요약 라벨 / List All 버튼 / 리스트 위젯의 표시 상태를 맞춘다."""
        if self.lbl_summary is None:
            return
        deferred = self._deferred is not None
        self.list_widget.setVisible(not deferred)
        self.lbl_summary.setVisible(deferred)
        self.btn_list_all.setVisible(deferred)
        if not deferred:
            return
        total = len(self._deferred)
        first = self._deferred[0].split("|")[-1] if total else ""
        self.lbl_summary.setText(
            "{0} item(s) stored, not listed.\n"
            "First: {1}\n"
            "They are used exactly as if they were listed.".format(total, first))
        self.btn_list_all.setText("List All ({0})".format(total))

    def _append_texts(self, incoming):
        """텍스트 기준으로 중복 없이 합친 뒤 set_items 로 되돌린다(요약 모드의 빠른 경로)."""
        merged = self.get_all_items()
        seen = set(merged)
        dupes = 0
        for text in incoming:
            if text in seen:
                dupes += 1
                continue
            seen.add(text)
            merged.append(text)
        if dupes:
            self._log("{0} item(s) already in the list were skipped.".format(dupes))
        self.set_items(merged)

    @staticmethod
    def _nodes_by_name(texts):
        """이름으로 현재 경로를 해석한다(요약 모드용). 씬에 없거나 애매하면 건너뛴다."""
        cmds = _cmds()
        if cmds is None:
            return []
        nodes = []
        for text in texts:
            if not _looks_like_node(text):
                continue
            try:
                found = cmds.ls(text, long=True) or []
            except Exception:
                found = []
            if found:
                nodes.append(found[0])
        return nodes

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

        UUID 가 **여러 노드**로 잡히는 경우(같은 파일을 네임스페이스만 달리해 여러 번
        **레퍼런스**하면 노드의 UUID 가 공유된다 — import 는 재할당되지만 reference 는 아님)
        에는 `found[0]` 로 아무거나 고르면 안 된다. 이때는 담을 때의 표시 이름으로 그중
        올바른 하나를 고른다.
        """
        cmds = _cmds()
        if cmds is None or item is None:
            return None

        data = item.data(UUID_ROLE)
        if data:
            uuid, comp = data
            found = cmds.ls(uuid, long=True) or []
            node = None
            if len(found) == 1:
                node = found[0]
            elif len(found) > 1:
                # 중복 UUID(다중 레퍼런스) — 이름으로 좁힌다.
                node = self._match_by_text(cmds, found, item.text())
            if node:
                return "{0}.{1}".format(node, comp) if comp else node
            return None

        text = item.text()
        if not _looks_like_node(text):
            return None
        try:
            return text if cmds.objExists(text) else None
        except Exception:
            return None

    @staticmethod
    def _match_by_text(cmds, found, text):
        """중복 UUID 로 여러 노드가 잡힐 때, 담을 때의 표시 이름으로 하나를 고른다.

        표시 이름(네임스페이스/부분 경로 포함)을 다시 조회해 `found` 와 교집합을 낸다.
        정확히 하나로 좁혀지면 그것을, 이름이 여전히 애매(리네임됐거나 동명 다수)하면
        첫 번째로 폴백해 예전 동작을 유지한다.
        """
        node_name, _ = _split_component(text)
        try:
            by_name = set(cmds.ls(node_name, long=True) or [])
        except Exception:
            by_name = set()
        matches = [f for f in found if f in by_name]
        if len(matches) == 1:
            return matches[0]
        return matches[0] if matches else found[0]

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
        self.lbl_number.setText("Number: {0}".format(self.count()))

    def _log(self, message):
        if callable(self.log_callback):
            self.log_callback(message)
        else:
            print(message)

    def _on_order_toggled(self, checked):
        self.set_order_tracking(checked)

    def _maya_selection(self):
        """현재 Maya 선택. Order 가 켜져 있으면 **고른 순서**로 돌려준다.

        `ls(orderedSelection=True)` 는 pref 가 꺼져 있으면 조용히 인덱스 순서를 주므로
        pref 는 set_order_tracking 에서 미리 켜둔다. 혹시 비어 오면 기존 경로로 폴백.
        """
        cmds = _cmds()
        if cmds is None:
            return []

        if self._order_state["on"]:
            try:
                ordered = cmds.ls(orderedSelection=True, flatten=True) or []
            except Exception:
                ordered = []
            if ordered:
                return ordered

        return cmds.ls(sl=True, fl=True) or []

    def _on_select(self):
        """현재 Maya 선택으로 리스트를 교체."""
        self.set_items(self._maya_selection())

    def _on_add(self):
        """현재 Maya 선택을 중복 없이 추가."""
        self.append_unique(self._maya_selection())

    def _edit_blocked(self):
        """요약 모드에서는 고를 항목이 없으니 편집 버튼을 막고 안내만 한다."""
        if self._deferred is None:
            return False
        self._log("Items are not listed - press 'List All' to edit them.")
        return True

    def _on_del(self):
        if self._edit_blocked():
            return
        for row in reversed(self.selected_rows()):
            self.list_widget.takeItem(row)
        self._update_number()

    def _on_up(self):
        """선택 항목을 한 칸 위로 이동(MOD_tsl BF_LIST_moveUp_index 로직 이식)."""
        if self._edit_blocked():
            return
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
        if self._edit_blocked():
            return
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
        # 요약 모드에서는 위젯을 건드리지 않고 보관 목록만 정렬한다(항목 수와 무관하게 즉시).
        if self._deferred is not None:
            self._deferred.sort()
            self._sync_summary()
            return
        self._set_records(sorted(self._records(), key=lambda rec: rec[0]))

    def _on_reverse(self):
        """리스트 항목의 순서를 통째로 뒤집는다(레코드로 옮겨 UUID 유지)."""
        if self._deferred is not None:
            self._deferred.reverse()
            self._sync_summary()
            return
        self._set_records(list(reversed(self._records())))

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
