# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00470_MaterialTool - Qt UI (in-Maya)
#
#   Name Check : 리스트업한 메시의 머티리얼 이름이 프로파일(JSON) 규칙에 맞는지 진단
#
# 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QTabWidget,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01

from tools.A00470_MaterialTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00470_MaterialTool.app.core import profiles
from tools.A00470_MaterialTool.app.ui.name_check_tab import NameCheckTab


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00470_MaterialTool_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Material Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(520, 820)

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Always on Top 토글(우)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        help_menu.addAction("Profile Format").triggered.connect(self.show_profile_format)

        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        # 공용 로그 위젯(Expand / Clear / Copy). 탭보다 먼저 만들어 넘겨준다.
        # 탭들은 예전처럼 `appendPlainText` 를 부르면 된다 - 그대로 받는다.
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Material Tool - Log",
            object_name="JUN_A00470_MaterialTool_log_window")
        self.log_view.setMinimumHeight(180)

        self.tabs = QTabWidget()
        self.name_check_tab = NameCheckTab(log_view=self.log_view)
        self.tabs.addTab(self.name_check_tab, "Name Check")

        main_layout.addWidget(self.tabs, stretch=1)
        main_layout.addWidget(self.log_view)

    # ==================================================================
    # 창 동작
    # ==================================================================

    def toggle_always_on_top(self, checked):
        """Qt 창 플래그를 바꾸면 창이 숨겨지므로 다시 show() 한다."""
        self.pin_button.setText("Pinned" if checked else "Pin")

        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Material Tool v{0}\nLast update : {1}\n\n"
            "Name Check  Collect the materials of the listed meshes and check their\n"
            "names against a rule profile. The scene is only read, never changed.".format(
                VERSION, LAST_UPDATE),
        )

    def show_profile_format(self):
        QMessageBox.information(
            self,
            "Profile Format",
            "A rule profile is one JSON file in :\n{0}\n\n"
            "Each token of the name gets one rule, in order :\n"
            "  literal   the exact word            value\n"
            "  enum      one of a list             values\n"
            "  pattern   prefix + fixed digits     prefix, digits\n"
            "  regex     your own expression       regex\n"
            "  any       anything                  repeat : takes the rest\n\n"
            "'optional' lets a token be left out, 'repeat' lets it appear any number\n"
            "of times, and 'hint' replaces the text shown in the report.\n"
            "checks.trailing_digit warns when the name ends with a digit stuck to the\n"
            "last token ('..._Top2'), but allows a separated one ('..._Top_002').".format(
                profiles.profiles_dir()),
        )
