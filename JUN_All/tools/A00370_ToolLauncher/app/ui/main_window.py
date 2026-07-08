# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-08
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
# 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMenuBar,
    QPlainTextEdit,
    QMessageBox,
    QPushButton,
    Qt,
)
from Framework.qt.maya_window import maya_main_window

from tools.A00370_ToolLauncher.app.config.version import VERSION, LAST_UPDATE
from tools.A00370_ToolLauncher.app.ui.launcher_tab import LauncherTab


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00370_ToolLauncher_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Tool Launcher v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(380, 640)

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Always on Top 토글(우)
        # 코너 위젯 대신 QHBoxLayout 으로 배치해 토글 시 위치/크기가 고정되도록 한다.
        self.menu_bar = QMenuBar()
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

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        # 공용 로그창. 탭이 상단 컨트롤의 접이식 'Log' 섹션에 담으므로 탭보다 먼저 생성.
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(90)

        # 툴 버튼 탭 (컨트롤 pane + 버튼 pane 을 상하 스플리터로 분리, 로그도 그 안에)
        self.launcher_tab = LauncherTab(
            log_callback=self._log, log_widget=self.log_view)
        main_layout.addWidget(self.launcher_tab, stretch=1)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

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
            "  facial / UE export). Each is its own JSON under data/.\n"
            "- Right-click a button to rename, reorder, change its path or\n"
            "  category, reveal its folder, set / reset its color, or delete.\n"
            "- Color Select mode paints many buttons across categories at once.\n"
            "- 'Reload on launch' re-imports the tool before showing it (dev).\n"
            "\n"
            "All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
