# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-13
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
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01

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

        # 선택 버튼 탭 (컨트롤 pane + 버튼 pane 을 상하 스플리터로 분리)
        self.selection_tab = SelectionTab(log_callback=self._log)
        main_layout.addWidget(self.selection_tab, stretch=1)

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
        main_layout.addWidget(footer)

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def on_show_controls_toggled(self, checked):
        """View > Show Controls. 로그창은 창 맨 아래라 숨겨도 그대로 보인다."""
        visible = self.selection_tab.set_controls_visible(checked)
        self._log("Controls pane: {0}".format("shown" if visible else "hidden"))

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
            "\n"
            "All UI text is English.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
