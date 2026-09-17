# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - Qt UI (in-Maya)
#
# 파일을 들여오고 · 내보내고 · 경로를 다루는 툴.
#   Export : A00040_file_exporter_V02 화면 그대로 (+ Export Path 의 Scene 버튼)
#   Import : A00030_quickTool_V02 의 Import FBX normal
#   Path   : A00030_quickTool_V02 의 Copy Scene Folder · Open Scene Folder
#
# 창은 메뉴 · Pin · 탭 · **공용 로그창 하나** · 푸터를 갖고, 탭은 log 콜백만 받는다.
# 원본 두 툴과 objectName 이 달라 동시에 띄울 수 있다. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01

from tools.A00480_FileTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00480_FileTool.app.ui.export_tab import ExportTab
from tools.A00480_FileTool.app.ui.import_tab import ImportTab
from tools.A00480_FileTool.app.ui.path_tab import PathTab


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00480_FileTool_window"



class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("File Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)

        self.build_ui()

        # A00040_file_exporter_V02 와 같은 값. 최소 크기보다 작아서 실제 크기는 fit_to_content() 가 정한다.
        self.resize(560, 720)

    def fit_to_content(self):
        """창을 레이아웃 최소 크기로 맞춘다 - A00040_V02 원본이 뜨는 크기와 같다(slate_dark 기준 960 x 853).

        테마 qss 는 show() 뒤 polish 때 자식에 적용되므로, 그 전에 재면 글자가 큰 상태의
        최소 크기(약 1280 폭)로 창이 커진다. launch.py 가 show() 다음 이벤트 루프에서 부른다.
        """
        self.resize(self.minimumSizeHint())

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)
        # 탭 테두리(좌우 2px)만큼 창 좌우 여백을 줄여 A00040_V02 원본과 같은 폭이 되게 한다.
        left, top, right, bottom = main_layout.getContentsMargins()
        main_layout.setContentsMargins(max(0, left - 2), top, max(0, right - 2), bottom)

        # 상단 헤더 행 : 메뉴 바(좌) + Pin 토글(우)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)

        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        # 고정 크기 - "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록(넓은 라벨 기준).
        # 높이는 메뉴 바 한 줄에 맞춘다(28 이면 헤더 행이 원본 A00040 의 메뉴 바보다 커진다).
        self.pin_button.setFixedSize(72, 22)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        # 공용 로그창 (Export 탭의 TSL 이 생성 때부터 로그를 쓰므로 탭보다 먼저)
        self.log_view = JUN_mod_log_qt_v01(
            window_title="File Tool - Log",
            object_name="JUN_A00480_FileTool_log_window")
        self.log_view.setFixedHeight(120)

        # 탭 : 사용 빈도 순 (Export 가 주력)
        self.tabs = QTabWidget()
        self.export_tab = ExportTab(log=self._log)
        self.import_tab = ImportTab(log=self._log)
        self.path_tab = PathTab(log=self._log)
        self.tabs.addTab(self.export_tab, "Export")
        self.tabs.addTab(self.import_tab, "Import")
        self.tabs.addTab(self.path_tab, "Path")
        self.tabs.setTabToolTip(0, "Export objectSets to FBX, one file per set.")
        self.tabs.setTabToolTip(1, "Import settings.")
        self.tabs.setTabToolTip(2, "Scene folder and path helpers.")

        main_layout.addWidget(self.tabs, stretch=1)
        main_layout.addWidget(self.log_view)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    # ==================================================================
    # Helper / 창 동작
    # ==================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def toggle_always_on_top(self, enabled):
        # WindowStaysOnTopHint 를 켜고/끄고, 플래그 변경 후 다시 show() (안 하면 창이 사라짐)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()
        self._log("Always on Top : {0}".format("ON" if enabled else "OFF"))

    def show_about(self, *args):
        message = (
            "File Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Import, export and path helpers in one window.\n"
            "\n"
            "[Export] Export objectSets to FBX, one file per set. File names are\n"
            "  built from tokens (Custom / Set's Name). Type Filter excludes node\n"
            "  types; 'Joints only under joints' keeps non-joints under a joint\n"
            "  out of the FBX. 'Scene' fills the export path with the scene folder.\n"
            "[Import] Import FBX normal - use the normals stored in the file.\n"
            "[Path] Copy Scene Folder / Open Scene Folder.\n"
            "\n"
            "Merged from A00040_file_exporter_V02 and the File / Import option\n"
            "buttons of A00030_quickTool_V02 (both tools are still available).\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
