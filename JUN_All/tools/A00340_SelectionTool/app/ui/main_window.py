# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# A00340_SelectionTool - Qt UI (in-Maya)
#
# 마야에서 선택된 오브젝트들을 버튼 하나로 빠르게 다시 선택하는 툴.
#   - 버튼은 현재 선택을 캡처해 만든다. 클릭하면 그 오브젝트들이 씬에서 선택된다.
#   - A00240_PathTool 처럼 카테고리/버튼을 자유롭게 추가·삭제·순서변경 하고,
#     Profile 로 원하는 종류끼리 버튼 세트를 나눠 보관한다.
#   - 화면은 상하 스플리터로 [컨트롤(Profile/Create/Color)] / [버튼 모음] 분리.
#     컨트롤 3칸은 하나의 접이식 'Controls' 박스로 묶여 한 번에 접힌다.
#     로그창은 v01.09 부터 창 맨 아래(스플리터 밖) - Controls 를 숨겨도 보인다.
#     위 칸은 처음 보일 때 Controls 내용 높이에 맞춰져 스크롤 없이 전부 보인다.
#   - View > Show Controls (v01.07~): 접어도 남던 Controls 영역을 아예 없앤다.
#     끄면 위 pane 과 스플리터 핸들이 사라지고 버튼 모음이 창 전체를 쓴다.
#   - v01.11: 최상위 탭 `Buttons`(기존 전부) / `Rules`(규칙 하나 = json 하나, 어느 씬에서든
#     그 이름 목록을 선택). 마지막에 보던 탭은 active.json 에 남긴다.
# 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMenuBar,
    QGroupBox,
    QPlainTextEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QScrollArea,
    QFrame,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.pin_style import apply_pin_style
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.core import file_opener

from tools.A00340_SelectionTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00340_SelectionTool.app.core import prefs as prefs_mod
from tools.A00340_SelectionTool.app.ui.selection_tab import SelectionTab
from tools.A00340_SelectionTool.app.ui.rules_tab import RulesTab
from tools.A00340_SelectionTool.app.core import select_rules as rules_mod


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00340_SelectionTool_window"

# active.json 에 저장하는 창 설정 키: 마지막에 보던 최상위 탭 인덱스 (v01.11).
ACTIVE_TAB_KEY = "active_tab"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Selection Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(360, 620)

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Always on Top 토글(우)
        # 코너 위젯 대신 QHBoxLayout 으로 배치해 토글 시 위치/크기가 고정되도록 한다.
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)

        # View : Controls pane 표시/숨김. 공용 메뉴 바가 툴 메뉴를 Help 왼쪽에 놓는다.
        # 체크 상태는 탭을 만든 뒤 실제 상태로 맞춘다(지난번에 숨겨 두었을 수 있다).
        view_menu = self.menu_bar.addMenu("View")
        view_menu.setToolTipsVisible(True)      # QMenu 는 기본으로 항목 툴팁을 숨긴다
        self.act_show_controls = view_menu.addAction("Show Controls")
        self.act_show_controls.setCheckable(True)
        self.act_show_controls.setToolTip(
            "Show or hide the Controls pane (Profile / Create / Color).\n"
            "Hidden, it takes no space at all - the button area fills the window.")
        self.act_show_controls.toggled.connect(self.on_show_controls_toggled)

        # Show Profile (v01.10) : 이 PC 에서 쓰는 활성 프로파일 json 을 탐색기에서 선택한 채로 연다.
        view_menu.addSeparator()
        act_show_profile = view_menu.addAction("Show Profile")
        act_show_profile.setToolTip(
            "Open Explorer with the active profile's JSON file selected\n"
            "(the file this tool reads and writes on this PC).")
        act_show_profile.triggered.connect(self.on_show_profile)

        # Show Rules Folder (v01.11) : 규칙 json 들이 있는 폴더. 다른 PC 와는 이 폴더를 복사해 공유.
        act_show_rules = view_menu.addAction("Show Rules Folder")
        act_show_rules.setToolTip(
            "Open Explorer at the rules folder (one json per rule).\n"
            "Copy files from here to share rules with another PC.")
        act_show_rules.triggered.connect(self.on_show_rules_folder)

        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)

        # 항상 위(Always on Top) 토글 버튼
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        # 고정 크기 — "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록 (넓은 라벨 기준)
        # 높이는 글씨가 잘리지 않도록 넉넉히 (테마 qss padding 포함).
        self.pin_button.setFixedSize(72, 28)
        # v01.13 : 켜진(Pinned) 동안 연한 빨강 - 다른 툴과 같은 공용 qss (Framework.qt.pin_style)
        apply_pin_style(self.pin_button)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        # 공용 로그창. 탭의 콜백이 여기에 쓰므로 탭보다 먼저 만든다. 자리는 창 맨 아래.
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Selection Tool - Log",
            object_name="JUN_A00340_SelectionTool_log_window")
        self.log_view.setFixedHeight(90)

        # 최상위 탭 (v01.11) : Buttons = 기존 선택 버튼 화면 전부, Rules = 규칙 json.
        self.tabs = QTabWidget()
        self.selection_tab = SelectionTab(log_callback=self._log)
        self.tabs.addTab(self.selection_tab, "Buttons")
        self.rules_tab = RulesTab(log_callback=self._log)
        # v01.12 : Rules 페이지는 스크롤 칸에 담는다(Buttons 탭은 원래 스크롤 칸). 탭 위젯의 최소 폭은
        # 안 보이는 페이지까지 가장 넓은 것을 따르므로, 버튼 줄이 긴 Rules 가 창을 그 폭 아래로 못 줄이게 했다.
        # 이제 좁히면 Rules 에 가로 스크롤바가 생기고 창은 자유롭게 줄어든다.
        rules_scroll = QScrollArea()
        rules_scroll.setWidgetResizable(True)
        rules_scroll.setFrameShape(QFrame.NoFrame)
        rules_scroll.setWidget(self.rules_tab)
        self.tabs.addTab(rules_scroll, "Rules")
        self.tabs.setTabToolTip(0, "Buttons grouped in categories, one profile json per set.")
        self.tabs.setTabToolTip(1, "Named object lists, one json file per rule - select them in any scene.")
        main_layout.addWidget(self.tabs, stretch=1)

        # 마지막에 보던 탭으로 연다. 바뀌면 저장.
        last_tab = prefs_mod.get_setting(ACTIVE_TAB_KEY, 0)
        if isinstance(last_tab, int) and 0 <= last_tab < self.tabs.count():
            self.tabs.setCurrentIndex(last_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # 로그는 툴 맨 아래 고정 - Controls 를 접거나 숨겨도 늘 보인다.
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # 메뉴 체크를 탭의 실제 상태(저장된 설정)에 맞춘다. 시그널은 막고 맞춘다 -
        # 여기서 토글 핸들러가 돌면 같은 값을 다시 저장하고 로그만 남긴다.
        self.act_show_controls.blockSignals(True)
        self.act_show_controls.setChecked(self.selection_tab.controls_visible())
        self.act_show_controls.blockSignals(False)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setWordWrap(True)        # v01.12 : 좁히면 두 줄로 - 한 줄 폭이 창의 최소 폭이 되지 않게
        main_layout.addWidget(footer)

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _on_tab_changed(self, index):
        prefs_mod.set_setting(ACTIVE_TAB_KEY, int(index))

    def on_show_rules_folder(self, *args):
        """View > Show Rules Folder. 규칙 폴더를 탐색기로 연다 (없으면 만든다)."""
        self.rules_tab.on_show_folder()

    def on_show_controls_toggled(self, checked):
        """View > Show Controls. 로그창은 창 맨 아래라 숨겨도 그대로 보인다."""
        visible = self.selection_tab.set_controls_visible(checked)
        self._log("Controls pane: {0}".format("shown" if visible else "hidden"))

    def on_show_profile(self, *args):
        """View > Show Profile. 활성 프로파일 json 을 탐색기에서 선택해 연다.

        파일이 없으면(지워졌거나 아직 저장 전) profiles 폴더를, 그것도 없으면 data 폴더를 연다.
        """
        name = prefs_mod.get_active()
        path = prefs_mod.profile_path(name)
        for candidate in (path, prefs_mod.PROFILES_DIR, prefs_mod.PREFS_DIR):
            try:
                file_opener.open_path(candidate)
            except (OSError, ValueError):
                continue
            if candidate == path:
                self._log("Show Profile: '{0}' -> {1}".format(name, path))
            else:
                self._log("[WARN] Profile file not found: {0} - opened {1}".format(
                    path, candidate))
            return
        self._log("[ERR] Show Profile: cannot open {0}".format(path))

    def toggle_always_on_top(self, enabled):
        # WindowStaysOnTopHint 를 켜고/끄고, 플래그 변경 후 다시 show() (안 하면 창이 사라짐)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()
        self._log(
            "Always on Top: {0}".format("ON" if enabled else "OFF")
        )

    def show_about(self, *args):
        message = (
            "Selection Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Quickly re-select saved sets of objects with a click.\n"
            "\n"
            "- Selection button : captures the current Maya selection.\n"
            "  Click it to select those objects again ('Add' to accumulate).\n"
            "- Category         : groups buttons; right-click to rename /\n"
            "  reorder / delete.\n"
            "- Profile          : separate button sets per character / asset\n"
            "  (each is its own JSON under the tool's data/ folder).\n"
            "- Right-click a button to rename, reorder, change category,\n"
            "  update / append its objects from the current selection,\n"
            "  set / reset its color, or delete it.\n"
            "- Set Color uses a palette with an eyedropper (Pick Screen\n"
            "  Color). Turn on 'Color Select' to check multiple buttons\n"
            "  across categories and Apply one color to all of them.\n"
            "- Layout : controls on top, buttons below, log at the bottom.\n"
            "  Drag the splitter to rebalance; click the 'Controls' bar to\n"
            "  collapse Profile / Create / Color all at once.\n"
            "- View > Show Controls : hide the whole control pane so the\n"
            "  button area fills the window (remembered for next time).\n"
            "- View > Show Profile : open Explorer with the active profile's\n"
            "  JSON file selected.\n"
            "\n"
            "Rules tab (v01.11) : a rule is a named list of objects saved as\n"
            "  ONE json file (data/rules/<name>.json). 'New Rule from\n"
            "  Selection' saves the current selection; 'Select' (or double-\n"
            "  click) selects those objects in any scene - missing names are\n"
            "  skipped, duplicate names select every match with a warning.\n"
            "  Rename changes the file name too; Delete removes the file.\n"
            "  Share rules between PCs by copying the json files\n"
            "  (View > Show Rules Folder), then press Reload.\n"
            "\n"
            "All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
