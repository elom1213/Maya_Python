# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# A00370_ToolLauncher - Qt UI (in-Maya)
#
# 자주 쓰는 JUN 툴들을 버튼 하나로 팝업시키는 숏컷 런처.
#   - 버튼은 '실행할 툴 폴더 경로' 하나를 담는다. 클릭하면 그 툴이 실행된다.
#     (셸프 아이콘을 하나하나 만들지 않고, 이 창 하나에서 골라 띄운다.)
#   - A00340_SelectionTool 처럼 카테고리/버튼을 자유롭게 추가·삭제·순서변경 하고,
#     Profile 로 상황(리깅/페이셜/UE 익스포트 등)별 버튼 세트를 나눠 보관한다.
#   - 화면은 상하 스플리터로 [컨트롤(Profile/Create/Color/Log)] / [버튼 모음] 분리.
#     컨트롤 4칸은 하나의 접이식 'Controls' 박스로 묶여 한 번에 접힌다. 로그창도
#     그 안에 들어가므로 log_view 를 탭에 넘겨준다.
#   - 메뉴 바: Profile > Show Profiles Folder (프로파일 json 폴더를 탐색기로, v01.09) · Help.
#   - Shrink(v01.11): A00220_BackupTool · A00240_PathTool 의 Shrink 를 따른다. 메뉴 바 · 탭 ·
#     저작권 줄을 감추고 창을 **272 x 155** 로 줄인다(세로는 A00220 과 같고, 가로는 Pin 이
#     Shrunk 아래로 내려가 한 칸 좁다 - v01.12). 줄어든 동안
#     헤더 행 왼쪽 자리(`anim_area`)에서 이 툴 아이콘의 로켓이 발사되기를 무한 반복한다
#     (app/ui/rocket_anim.py).
# 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 모든 UI 문자열/로그는 영어.

import os

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QMenuBar,
    QPlainTextEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    Qt,
)
from Framework.core import file_opener
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01

from tools.A00370_ToolLauncher.app.config.version import VERSION, LAST_UPDATE
from tools.A00370_ToolLauncher.app.core import prefs as prefs_mod
from tools.A00370_ToolLauncher.app.ui.launcher_tab import LauncherTab
from tools.A00370_ToolLauncher.app.ui.rocket_anim import RocketAnimWidget


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00370_ToolLauncher_window"

# Shrink 로 줄었을 때 창 크기 - A00220_BackupTool(v01.20) · A00240_PathTool(v01.25) 이 줄었을 때와
# 같다. 가로는 350 에서 Pin 버튼 한 칸(72 + 간격 6)만큼 좁힌 값 - 줄었을 때 Pin 이 Shrunk 아래로
# 내려가 그 자리가 비기 때문이다(v01.12).
SHRINK_WIDTH = 272
SHRINK_HEIGHT = 155


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Tool Launcher v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(380, 640)

        # Shrink 전 창 크기 (되돌릴 때 쓴다)
        self._full_size = None

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Always on Top 토글(우)
        # 코너 위젯 대신 QHBoxLayout 으로 배치해 토글 시 위치/크기가 고정되도록 한다.
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        # Profile 메뉴(Help 왼쪽): 프로파일 json 이 저장된 폴더를 탐색기로 연다(v01.09).
        # A00550 의 Library > Show Libraries Folder 와 같은 모양.
        profile_menu = self.menu_bar.addMenu("Profile")
        profile_menu.setToolTipsVisible(True)
        act_profiles = profile_menu.addAction("Show Profiles Folder")
        act_profiles.setToolTip(
            "Open the folder of the saved profile JSON files (data/profiles/*.json) in Explorer")
        act_profiles.triggered.connect(self.on_show_profiles_folder)
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)

        # 항상 위(Always on Top) 토글 버튼
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        # 고정 크기 — "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록 (넓은 라벨 기준)
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        # Shrink : 켜면 메뉴 바 · 탭 · 저작권 줄을 감추고 창을 작게 (아래 toggle_shrink, v01.11).
        self.shrink_button = QPushButton("Shrink")
        self.shrink_button.setCheckable(True)
        self.shrink_button.setToolTip(
            "Hide the buttons and make the window small.\n"
            "Press again to bring them back.")
        self.shrink_button.setFixedSize(72, 28)
        self.shrink_button.toggled.connect(self.toggle_shrink)

        # 줄어든 동안만 보이는 자리 - 로켓 발사 애니메이션(v01.11). 메뉴 바가 있던 자리를
        # 그대로 물려받아 남는 가로 · 세로를 전부 차지한다(안 그러면 버튼 높이 28px 로 묶인다).
        self.anim_area = RocketAnimWidget()
        self.anim_area.setObjectName("A00370_shrink_anim_area")
        self.anim_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.anim_area.hide()

        # 버튼 둘은 작은 그리드에 둔다 - 평소엔 한 줄 [Shrink][Pin], 줄었을 때는 Pin 을
        # Shrink 아래 칸으로 옮겨 세로로 쌓는다(v01.12). 그래서 줄었을 때 가로가 한 칸 좁다.
        self.button_grid = QGridLayout()
        self.button_grid.setContentsMargins(0, 0, 0, 0)
        self.button_grid.addWidget(self.shrink_button, 0, 0)
        self.button_grid.addWidget(self.pin_button, 0, 1)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.anim_area, stretch=1)
        header_row.addLayout(self.button_grid)
        header_row.setAlignment(self.button_grid, Qt.AlignTop)
        main_layout.addLayout(header_row)

        # 공용 로그창. 탭이 상단 컨트롤의 접이식 'Log' 섹션에 담으므로 탭보다 먼저 생성.
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Tool Launcher - Log",
            object_name="JUN_A00370_ToolLauncher_log_window")
        self.log_view.setFixedHeight(90)

        # 툴 버튼 탭 (컨트롤 pane + 버튼 pane 을 상하 스플리터로 분리, 로그도 그 안에)
        self.launcher_tab = LauncherTab(
            log_callback=self._log, log_widget=self.log_view)
        main_layout.addWidget(self.launcher_tab, stretch=1)

        # 저작권
        self.footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.footer)

        # Shrink 가 감추는 것들 (로켓과 Shrink · Pin 버튼만 남는다)
        self._shrink_hidden = (self.menu_bar, self.launcher_tab, self.footer)

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def on_show_profiles_folder(self, *args):
        """Profile > Show Profiles Folder. 프로파일 json 폴더를 탐색기로 연다(없으면 만든다)."""
        folder = prefs_mod.PROFILES_DIR
        try:
            os.makedirs(folder, exist_ok=True)
            file_opener.open_path(folder)
        except (OSError, ValueError) as exc:
            self._log("[ERROR] Cannot open {0}: {1}".format(folder, exc))
            return
        self._log("[OK] Profiles folder: {0}".format(folder))

    def toggle_always_on_top(self, enabled):
        # WindowStaysOnTopHint 를 켜고/끄고, 플래그 변경 후 다시 show() (안 하면 창이 사라짐)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()
        self._log(
            "Always on Top: {0}".format("ON" if enabled else "OFF")
        )

    def toggle_shrink(self, enabled):
        """Shrink 토글 - 메뉴 바 · 탭 · 저작권 줄을 감추고 창을 SHRINK_WIDTH x SHRINK_HEIGHT 로.

        A00220 · A00240 과 같은 순서다: 감추기 -> 레이아웃 최소 크기 다시 계산 -> resize.
        (다시 계산하지 않으면 옛 최소 크기에 막혀 창이 줄지 않는다.)
        되돌릴 때는 줄이기 전 크기(가로 · 세로 둘 다)로 돌아간다. 감추는 것은 화면뿐이라
        프로파일 · 버튼 · 로그는 그대로다.
        """
        root = self.layout()
        # Pin 버튼 자리: 줄었을 때는 Shrink 아래(1, 0), 평소엔 오른쪽(0, 1).
        self.button_grid.removeWidget(self.pin_button)
        if enabled:
            self._full_size = (self.width(), self.height())
            for widget in self._shrink_hidden:
                widget.hide()
            self.button_grid.addWidget(self.pin_button, 1, 0)
            self.anim_area.show()
        else:
            self.anim_area.stop()
            self.anim_area.hide()
            self.button_grid.addWidget(self.pin_button, 0, 1)
            for widget in self._shrink_hidden:
                widget.show()

        self.shrink_button.setText("Shrunk" if enabled else "Shrink")

        root.invalidate()
        root.activate()
        if enabled:
            self.resize(SHRINK_WIDTH, SHRINK_HEIGHT)
            # 켤 때마다 처음부터 - 발사대에서 점화한 뒤 위로 날아가기를 되풀이한다.
            self.anim_area.start()
        elif self._full_size:
            self.resize(*self._full_size)

        self._log("Shrink: {0}".format("ON" if enabled else "OFF"))

    def show_about(self, *args):
        message = (
            "Tool Launcher v{version}\n"
            "Update date: {update}\n"
            "\n"
            "One window of shortcut buttons that pop up your JUN tools —\n"
            "no need to install a separate shelf icon for each tool.\n"
            "\n"
            "- Tool button : holds one tool folder path (e.g. the folder of\n"
            "  A00080_KWI_creator_V03). Click it to launch that tool. The\n"
            "  button shows the tool's own icon next to its name.\n"
            "- Add a button with 'Tool' : pick the tool folder with Browse,\n"
            "  give it a name, choose a category. Any JUN tool folder that\n"
            "  exposes run() works — it is fully extensible.\n"
            "- Category : groups buttons; right-click to rename / reorder /\n"
            "  delete.\n"
            "- Profile  : separate button sets per situation (rigging /\n"
            "  facial / UE export). Each is its own JSON under data/profiles/;\n"
            "  menu 'Profile > Show Profiles Folder' opens it in Explorer.\n"
            "- Right-click a button to rename, reorder, change its path or\n"
            "  category, reveal its folder, set / reset its color, or delete.\n"
            "- Color Select mode paints many buttons across categories at once.\n"
            "- 'Reload on launch' re-imports the tool before showing it (dev).\n"
            "- 'Shrink' folds the window down to a small box (272 x 155, Pin\n"
            "  moves under Shrunk) with a looping rocket-launch animation;\n"
            "  press again to restore.\n"
            "\n"
            "All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
