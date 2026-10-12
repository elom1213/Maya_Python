# -*- coding: utf-8 -*-
"""
JUN_mod_devMode_qt_v01 - 메뉴 바의 `Dev Mode` 메뉴 (Developer / Release 화면 전환).

A00330_NamingTool v01.26 의 `_build_dev_mode_menu` 를 공용으로 올린 것이다. 툴마다 "개발자가 보는
화면" 과 "배포본을 받은 사람이 보는 화면" 이 다를 때, 개발자가 **배포 화면을 그대로 미리 볼 수 있게**
창 맨 위 메뉴 바에 `Dev Mode` 메뉴를 둔다.

    Dev Mode
      (o) Developer
      ( ) Release (shared tool)

규칙
----
- **개발자 모드(`Framework.core.dev_mode.is_dev_mode`)에서만 메뉴를 만든다.** 배포본에는 메뉴 자체가
  없고 `is_developer()` 는 늘 False 다 - 배포 화면이 고정된다.
- 메뉴는 공통 메뉴(`Help`)의 **오른쪽**에 붙는다. 공용 메뉴 바의 `addMenu("제목")` 은 새 메뉴를
  `Help` 왼쪽에 끼우므로, QMenu 를 직접 넘겨 Qt 기본 동작(맨 오른쪽)을 쓴다.
- 화면 전환은 이 위젯이 하지 않는다. 툴이 `modeChanged(bool)` 을 받아 자기 위젯을 숨기고 보인다
  (`True` = Developer). 코드에서 모드가 바뀌면 `set_developer()` 로 체크를 맞춘다.

쓰는 법
------
    from Framework.qt.MOD_devMode_qt_v01 import JUN_mod_devMode_qt_v01

    self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
    ...
    self.dev_mode = JUN_mod_devMode_qt_v01(self.menu_bar, tool_file=__file__)
    self.dev_mode.modeChanged.connect(self.apply_view)      # apply_view(developer: bool)
    self.apply_view(self.dev_mode.is_developer())           # 처음 화면

Maya 밖에서도 import / 생성이 가능하도록 maya 의존이 없다.
"""

from Framework.qt.qt import *

from Framework.core import dev_mode as _dev_mode


class JUN_mod_devMode_qt_v01(QObject):
    """`Dev Mode` 메뉴 - Developer / Release (shared tool) 중 하나.

    Args:
        menu_bar: 메뉴를 붙일 QMenuBar (공용 `JUN_mod_menuBar_qt_v01` 권장).
        tool_file: 툴 안의 파일 경로(`__file__`). 개발자 모드 판정과 툴 폴더 찾기에 쓴다.
        developer: 개발자 모드일 때의 **처음 화면**. 기본 True(Developer).
        force_available: True 면 판정과 무관하게 메뉴를 만든다(테스트용).
    """

    #: 화면이 바뀔 때. True = Developer 화면, False = Release 화면.
    modeChanged = Signal(bool)

    MENU_TITLE = "Dev Mode"
    DEVELOPER_LABEL = "Developer"
    RELEASE_LABEL = "Release (shared tool)"

    def __init__(self, menu_bar, tool_file=None, developer=True,
                 developer_tooltip=None, release_tooltip=None,
                 force_available=False, parent=None):
        super().__init__(parent or menu_bar)

        self.menu_bar = menu_bar
        self.tool_file = tool_file
        self.menu = None
        self.act_developer = None
        self.act_release = None

        self._available = bool(force_available) or _dev_mode.is_dev_mode(tool_file)
        # 배포본(메뉴 없음)은 언제나 Release 화면.
        self._developer = bool(developer) if self._available else False

        if self._available:
            self._build_menu(developer_tooltip, release_tooltip)

    # ------------------------------------------------------------------
    # 메뉴
    # ------------------------------------------------------------------

    def _build_menu(self, developer_tooltip, release_tooltip):
        menu = QMenu(self.MENU_TITLE, self.menu_bar)
        menu.setToolTipsVisible(True)

        group = QActionGroup(menu)
        group.setExclusive(True)

        self.act_developer = QAction(self.DEVELOPER_LABEL, menu)
        self.act_developer.setToolTip(
            developer_tooltip or "Developer view - everything the tool has.")
        self.act_release = QAction(self.RELEASE_LABEL, menu)
        self.act_release.setToolTip(
            release_tooltip or "The view people get in the shared (release) tool.")

        for action in (self.act_developer, self.act_release):
            action.setCheckable(True)
            group.addAction(action)
            menu.addAction(action)

        # triggered(bool) 의 checked 인자를 받지 않도록 기본 인자로 고정
        self.act_developer.triggered.connect(lambda _c=False: self.set_developer(True))
        self.act_release.triggered.connect(lambda _c=False: self.set_developer(False))

        self._sync_checks()

        # QMenu 를 직접 넘긴다 - 공용 메뉴 바의 addMenu("제목") 은 Help 왼쪽에 끼우기 때문
        self.menu_bar.addMenu(menu)
        self.menu = menu

    def _sync_checks(self):
        if self.act_developer is None:
            return
        (self.act_developer if self._developer else self.act_release).setChecked(True)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def is_available(self):
        """메뉴가 있는지 (= 개발자 모드)."""
        return self._available

    def is_developer(self):
        """지금 Developer 화면이면 True. 배포본은 늘 False."""
        return self._developer

    def is_release(self):
        return not self._developer

    def set_developer(self, developer):
        """화면을 바꾼다. 배포본(메뉴 없음)에서는 Release 로 고정돼 아무 일도 하지 않는다.

        같은 값이면 시그널을 내지 않는다. 메뉴 체크는 늘 상태를 따른다(코드로 바꿔도).
        """
        developer = bool(developer)
        if not self._available:
            developer = False
        if developer == self._developer:
            self._sync_checks()
            return
        self._developer = developer
        self._sync_checks()
        self.modeChanged.emit(developer)

    def set_release(self, release=True):
        self.set_developer(not release)
