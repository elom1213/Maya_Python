# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-02
# A00340_SelectionTool - Qt UI (in-Maya)
#
# 마야에서 선택된 오브젝트들을 버튼 하나로 빠르게 다시 선택하는 툴.
#   - 버튼은 현재 선택을 캡처해 만든다. 클릭하면 그 오브젝트들이 씬에서 선택된다.
#   - A00240_PathTool 처럼 카테고리/버튼을 자유롭게 추가·삭제·순서변경 하고,
#     Profile 로 원하는 종류끼리 버튼 세트를 나눠 보관한다.
# 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QMenuBar,
    QPlainTextEdit,
    QMessageBox,
    Qt,
)
from Framework.qt.maya_window import maya_main_window

from tools.A00340_SelectionTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00340_SelectionTool.app.ui.selection_tab import SelectionTab


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00340_SelectionTool_window"


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

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 공용 로그창 (탭이 log_callback 으로 쓰므로 탭보다 먼저 생성)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(90)

        # 선택 버튼 탭 (Profile / Category / Selection buttons)
        self.selection_tab = SelectionTab(log_callback=self._log)
        main_layout.addWidget(self.selection_tab, stretch=1)

        # 로그창
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

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
            "  update / append its objects from the current selection, or\n"
            "  delete it.\n"
            "\n"
            "All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
