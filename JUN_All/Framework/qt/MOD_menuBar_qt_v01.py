# -*- coding: utf-8 -*-
"""
JUN_mod_menuBar_qt_v01 - 모든 툴이 공통 메뉴 항목을 갖는 PySide 메뉴 바.

툴 창 위의 `QMenuBar` 를 대체한다. 만들자마자 **공통 메뉴**(`Help` 등)와 그 안의
**공통 항목**(`Copy Tool Name` 등)이 들어 있고, 툴은 예전처럼 자기 항목을 더하면 된다.
공통 항목의 목록은 `Framework/core/tool_menu.py` 의 `COMMON_MENUS` 한 곳에 있다 —
거기에 한 줄 더하면 이 위젯을 쓰는 모든 툴에 생긴다.

왜 드롭인(drop-in) 교체가 되는가
--------------------------------
저장소의 PySide 툴은 전부 같은 두 줄로 메뉴를 만든다.

    self.menu_bar = QMenuBar()
    help_menu = self.menu_bar.addMenu("Help")
    help_menu.addAction("About").triggered.connect(self.show_about)

그래서 **`addMenu(제목)` 을 "있으면 돌려주고, 없으면 만든다"** 로 바꿨다. 공통 메뉴 `Help` 는
이미 있으므로 툴의 `addMenu("Help")` 가 **그 메뉴를 그대로 받는다** — 툴 코드는 생성 한 줄만
바꾸면 되고, 나머지(`addAction` · `addSeparator` · `addMenu` 로 하위 메뉴)는 전부 그대로다.

★ 공통 항목은 늘 **메뉴 맨 아래**
--------------------------------
공통 항목은 생성자에서 들어가므로, 툴이 나중에 넣는 `About` 는 그 **아래**에 붙는다. 툴마다
위치가 달라지지 않도록 메뉴가 열릴 때(`aboutToShow`) **구분선 + 공통 항목을 맨 뒤로 옮긴다.**
툴 항목이 하나도 없으면 구분선은 숨긴다. 액션 객체는 그대로이므로 연결이 끊기지 않는다.

★ 툴이 새로 만든 메뉴는 **공통 메뉴의 왼쪽**
------------------------------------------
`A00180_abSymMesh` 처럼 `addMenu("Operations")` 를 부르면, 뒤에 붙이지 않고 **첫 공통 메뉴 앞에
끼운다.** 그래서 늘 `Operations | Help` 순서 — 툴 메뉴가 먼저, `Help` 가 끝이다.

툴 이름
-------
`tool_file=__file__` 을 주면 그 경로에서 **툴 폴더 이름**(`A00060_jointTool_V03`)을 찾는다
(부모가 `tools` 인 폴더, 없으면 `app` 폴더를 담은 폴더). 직접 주려면 `tool_name=`.

지금 보이는 탭 경로 (2026-10-29)
-----------------------------
`Help > Copy Tool Name + Tabs` 는 **지금 보고 있는 탭의 라벨**을 툴 이름 뒤에 붙인다 —
`A00110_animTool_V02 / Transfer / Follow`. 창 안의 `QTabWidget` 들 중 **보이는 사슬**만 고른다:
바깥 탭 위젯의 `currentWidget()` 안에 들어 있는 탭 위젯만 다음 단계로 인정하고(다른 탭 페이지 속
탭 위젯은 제외), 숨긴 위젯(접힌 그룹 · Shrink 등)도 제외한다. 모듈 함수 `visible_tab_path(window)`.
메뉴 바는 탭보다 먼저 만들어지므로 **누를 때** 센다.

결과 알림
---------
`Copy Tool Name` 같은 항목의 결과는 **창 안의 공용 로그창(`JUN_mod_log_qt_v01`)** 에 한 줄 남긴다.
로그창이 없는 창이면 `print`(마야 Script Editor). 메뉴 바는 로그창보다 먼저 만들어지는 경우가 많아
**누를 때 찾는다.**

사용법
------
    from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01

    self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
    help_menu = self.menu_bar.addMenu("Help")          # 공통 Help 를 그대로 받는다
    help_menu.addAction("About").triggered.connect(self.show_about)

Maya 밖에서도 import / 생성이 가능하도록 maya 의존이 없다.
"""

from Framework.qt.qt import *

from Framework.core import tool_menu


def _plain_title(title):
    """`&Help` 같은 니모닉 표시를 떼고 비교한다."""
    return (title or "").replace("&", "")


def _ancestor_tabs(tab_widget, window):
    """창까지 올라가며 만나는 **조상 QTabWidget 들**(바깥 → 안쪽 순)."""
    found = []
    parent = tab_widget.parentWidget()
    while parent is not None and parent is not window:
        if isinstance(parent, QTabWidget):
            found.append(parent)
        parent = parent.parentWidget()
    found.reverse()
    return found


def _is_on_visible_chain(tab_widget, window):
    """조상 탭 위젯마다 이 위젯이 **현재 페이지** 안에 있는지 - 하나라도 아니면 안 보이는 탭 속."""
    parent = tab_widget.parentWidget()
    while parent is not None and parent is not window:
        if isinstance(parent, QTabWidget):
            # 탭 위젯의 직접 자식은 QStackedWidget 이므로 **처음 위젯**이 현재 페이지 안에 있는지 본다
            current = parent.currentWidget()
            if current is None or not current.isAncestorOf(tab_widget):
                return False
        parent = parent.parentWidget()
    return True


def visible_tab_path(window):
    """창에서 **지금 보이는 탭 라벨**들을 바깥 → 안쪽 순으로.

    - 바깥 `QTabWidget` 의 현재 탭 라벨, 그 페이지 안의 `QTabWidget` 의 현재 탭 라벨, ... 순.
    - 다른(안 보이는) 탭 페이지 속 탭 위젯 · 숨긴 위젯(`isVisibleTo(window)` 가 False)은 제외.
    - 같은 페이지에 보이는 탭 위젯이 둘이면 둘 다 - 사슬 단위로 묶어서(바깥 탭의 안쪽 탭들을 다 적은
      뒤 다음 형제), 순서는 findChildren(생성) 순서.
    - 탭이 없거나 `window` 가 None 이면 빈 리스트. `&File` 의 니모닉 표시는 뗀다.
    """
    if window is None:
        return []

    try:
        tab_widgets = window.findChildren(QTabWidget)
    except Exception:
        return []

    order = {}
    for index, tab_widget in enumerate(tab_widgets):
        order[id(tab_widget)] = index

    rows = []
    for tab_widget in tab_widgets:
        try:
            if tab_widget.count() == 0 or tab_widget.currentIndex() < 0:
                continue
            if not tab_widget.isVisibleTo(window):
                continue
            if not _is_on_visible_chain(tab_widget, window):
                continue
            label = _plain_title(tab_widget.tabText(tab_widget.currentIndex())).strip()
            # 정렬 키 = 조상 탭 위젯들의 순번 + 자기 순번 → 한 사슬(바깥 → 안쪽)이 붙어서 나온다
            chain = _ancestor_tabs(tab_widget, window) + [tab_widget]
            key = tuple(order.get(id(t), len(order)) for t in chain)
        except Exception:
            continue
        if not label:
            continue
        rows.append((key, label))

    rows.sort(key=lambda row: row[0])
    return [label for _key, label in rows]


class JUN_mod_menuBar_qt_v01(QMenuBar):

    def __init__(self, tool_file=None, tool_name=None, parent=None):
        super().__init__(parent)

        self.tool_dir = tool_menu.tool_dir_from_path(tool_file) if tool_file else None
        self.tool_name = tool_name or (
            tool_menu.tool_name_from_path(tool_file) if tool_file else None)

        # 메뉴 제목 -> {"menu", "separator", "actions"}
        self._common = {}
        self._common_order = []

        # 바로 아래 메뉴들 : (제목, QMenu). ★ QAction.menu() 로 되찾지 않는다 - PySide2 에서
        #   이 서브클래스의 메뉴 액션에 menu() 를 부르면 C++ QMenu 가 지워진다(실측).
        self._menus = []

        for title in tool_menu.common_menu_titles():
            self._build_common_menu(title)

    # ------------------------------------------------------------------
    # 공통 메뉴
    # ------------------------------------------------------------------

    def _build_common_menu(self, title):
        menu = QMenu(title, self)
        super().addMenu(menu)
        self._menus.append((title, menu))
        menu.setToolTipsVisible(True)

        separator = QAction(menu)
        separator.setSeparator(True)
        menu.addAction(separator)

        actions = []
        for spec in tool_menu.common_items(title):
            action = QAction(spec.label, menu)
            if spec.tooltip:
                action.setToolTip(spec.tooltip)
                action.setStatusTip(spec.tooltip)
            # triggered(bool) 의 checked 인자를 spec 으로 받지 않도록 기본 인자로 고정
            action.triggered.connect(lambda _checked=False, s=spec: self.run_item(s))
            menu.addAction(action)
            actions.append(action)

        self._common[title] = {"menu": menu, "separator": separator, "actions": actions}
        self._common_order.append(title)

        menu.aboutToShow.connect(lambda m=menu, t=title: self.arrange_common_items(t))
        self.arrange_common_items(title)
        return menu

    def arrange_common_items(self, title):
        """구분선 + 공통 항목을 그 메뉴의 **맨 뒤**로. 툴 항목이 없으면 구분선을 숨긴다."""
        entry = self._common.get(title)
        if not entry:
            return

        menu = entry["menu"]
        tail = [entry["separator"]] + entry["actions"]

        current = menu.actions()
        if current[-len(tail):] != tail:
            for action in tail:
                menu.removeAction(action)
            for action in tail:
                menu.addAction(action)

        own = [a for a in menu.actions() if a not in tail]
        entry["separator"].setVisible(bool(own))

    def common_menu(self, title="Help"):
        """공통 메뉴(QMenu). 없으면 None."""
        entry = self._common.get(title)
        return entry["menu"] if entry else None

    def common_actions(self, title="Help"):
        """그 공통 메뉴의 공통 항목 액션들."""
        entry = self._common.get(title)
        return list(entry["actions"]) if entry else []

    def find_menu(self, title):
        """바로 아래 메뉴 중 제목이 같은 것. 없으면 None."""
        wanted = _plain_title(title)
        for menu_title, menu in self._menus:
            if _plain_title(menu_title) == wanted:
                return menu
        return None

    def menu_titles(self):
        """메뉴 바에 보이는 순서대로의 메뉴 제목들."""
        return [_plain_title(action.text()) for action in self.actions()]

    # ------------------------------------------------------------------
    # QMenuBar 대체
    # ------------------------------------------------------------------

    def addMenu(self, *args):
        """`addMenu("제목")` 은 **있으면 돌려주고 없으면 만든다.**

        새로 만드는 메뉴는 첫 공통 메뉴의 **앞(왼쪽)** 에 끼운다. `addMenu(QMenu)` ·
        `addMenu(icon, "제목")` 은 Qt 원래 동작 그대로다.
        """
        if len(args) != 1 or not isinstance(args[0], str):
            result = super().addMenu(*args)
            if isinstance(args[0], QMenu):
                self._menus.append((args[0].title(), args[0]))
            elif isinstance(result, QMenu):
                self._menus.append((result.title(), result))
            return result

        title = args[0]
        existing = self.find_menu(title)
        if existing is not None:
            return existing

        menu = QMenu(title, self)
        self._menus.append((title, menu))
        before = self._first_common_action()
        if before is None:
            super().addMenu(menu)
        else:
            self.insertMenu(before, menu)
        return menu

    def _first_common_action(self):
        for title in self._common_order:
            menu = self._common[title]["menu"]
            return menu.menuAction()
        return None

    # ------------------------------------------------------------------
    # 실행
    # ------------------------------------------------------------------

    def context(self):
        window = self.window()
        return tool_menu.MenuContext(
            tool_name=self.tool_name,
            tool_dir=self.tool_dir,
            window=window,
            log=self.log,
            tab_path=lambda: visible_tab_path(window))

    def tab_path(self):
        """지금 창에서 보이는 탭 라벨들(바깥 → 안쪽). `Copy Tool Name + Tabs` 가 쓰는 값."""
        return visible_tab_path(self.window())

    def run_item(self, spec):
        """공통 항목 실행. 콜백이 던진 예외는 로그로 알리고 삼킨다(메뉴가 툴을 죽이지 않게)."""
        try:
            return spec.callback(self.context())
        except Exception as exc:
            self.log("[{0}] Failed : {1}".format(spec.label, exc))
            return None

    def log(self, message):
        """창 안의 공용 로그창에 한 줄. 없으면 print."""
        log_view = self._find_log_view()
        if log_view is not None:
            try:
                log_view.appendPlainText(message)
                return
            except Exception:
                pass
        print(message)

    def _find_log_view(self):
        try:
            from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
        except ImportError:
            return None

        window = self.window()
        if window is None or window is self:
            return None
        found = window.findChildren(JUN_mod_log_qt_v01)
        return found[0] if found else None
