# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - Qt UI (in-Maya). 탭 2개 + 공용 로그.
#   Pose Map      : 음소 어트리뷰트 -> 블렌드셰이프 포즈 (app/ui/pose_map_tab.py)
#   Blend Weights : blendWeighted input / weight 편집 (app/ui/blend_weights_tab.py)
# 계획: JUN_All/docs/plans/A00550_PoseMapper_plan.md. 모든 UI 문자열 · 로그는 영어.

import os

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.core import file_opener

from tools.A00550_PoseMapper.app.config.version import VERSION, LAST_UPDATE
from tools.A00550_PoseMapper.app.ui.blend_weights_tab import BlendWeightsTab


WINDOW_OBJECT_NAME = "JUN_A00550_PoseMapper_window"
GUIDE_DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))), "docs", "A00550_PoseMapper.md")


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("Pose Mapper v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(760, 820)                       # 처음 보일 때 fit_to_content 가 내용에 맞춘다
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        lib_menu = self.menu_bar.addMenu("Library")
        lib_menu.setToolTipsVisible(True)
        act = lib_menu.addAction("Show Libraries Folder")
        act.setToolTip("Open the folder of the saved pose libraries (app/libraries/*.json) in Explorer")
        act.triggered.connect(self.on_show_libraries)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Open Guide", self.on_open_guide)
        help_menu.addAction("About", self.show_about)
        layout.setMenuBar(self.menu_bar)

        self.log_view = JUN_mod_log_qt_v01(window_title="Pose Mapper - Log",
                                           object_name="JUN_A00550_PoseMapper_log_window")
        self.log_view.setFixedHeight(130)

        self.tabs = QTabWidget()
        try:
            from tools.A00550_PoseMapper.app.ui.pose_map_tab import PoseMapTab
            self.pose_tab = PoseMapTab(self._log)
        except ImportError:                         # 진행 중(계획서 §10) - 탭이 아직 없을 때
            self.pose_tab = QLabel("Pose Map - not built yet")
        self.bw_tab = BlendWeightsTab(self._log)
        self.tabs.addTab(self.pose_tab, "Pose Map")
        self.tabs.addTab(self.bw_tab, "Blend Weights")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        # 탭을 스크롤 칸에 담는다 (v01.04). QTabWidget 의 최소 크기(안 보이는 탭까지 포함한 최댓값)가 창 최소로
        # 강제되면 창을 그보다 줄일 수 없고, Save 처럼 콤보 · 라벨 글자가 길어지는 명령이 그 최소를 키워 창이
        # 저절로 커졌다. 스크롤 칸은 최소가 작으므로 창은 언제든 자유롭게 줄이고 늘릴 수 있다(작으면 스크롤바).
        # 스크롤 칸에 최소 폭을 걸지 않는다 - 걸면 다시 그 폭 아래로 못 줄인다.
        self.tabs_scroll = QScrollArea()
        self.tabs_scroll.setWidgetResizable(True)
        self.tabs_scroll.setFrameShape(QFrame.NoFrame)
        self.tabs_scroll.setWidget(self.tabs)
        layout.addWidget(self.tabs_scroll, 1)

        log_box = QGroupBox("Log")
        log_layout = QVBoxLayout(log_box)
        log_layout.addWidget(self.log_view)
        layout.addWidget(log_box)

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _on_tab_changed(self, index):
        # Solo preview 는 탭을 옮겨도 유지한다 - 끄는 것은 체크박스 클릭(과 창 닫기)뿐 (v01.03).
        if self.tabs.widget(index) is self.bw_tab:
            self.bw_tab.refresh_nodes()

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_fitted", False):
            self._fitted = True
            # 테마 qss 가 입은 뒤(다음 이벤트 루프) 글자 크기로 재야 여는 크기가 맞다.
            QTimer.singleShot(0, self.fit_to_content)

    def fit_to_content(self):
        """처음 열 때만 창을 내용 크기에 맞춘다(화면 작업 영역까지). 그 뒤로는 크기를 건드리지 않는다."""
        content = QSize(self.tabs.minimumSizeHint().width(), self.tabs.sizeHint().height())
        extra_w = self.minimumSizeHint().width() - self.tabs_scroll.minimumSizeHint().width()
        extra_h = self.minimumSizeHint().height() - self.tabs_scroll.minimumSizeHint().height()
        width, height = max(content.width() + max(extra_w, 0), 360), content.height() + max(extra_h, 0)
        screen = self.screen() if hasattr(self, "screen") else None
        if screen is not None:
            avail = screen.availableGeometry()
            frame_h = max(self.frameGeometry().height() - self.geometry().height(), 0)
            width = min(width, avail.width())
            height = min(height, avail.height() - frame_h)
        self.resize(width, height)

    def closeEvent(self, event):
        if hasattr(self.pose_tab, "stop_preview"):
            self.pose_tab.stop_preview()
        super().closeEvent(event)

    def on_show_libraries(self, *args):
        """Library > Show Libraries Folder. 저장한 포즈 라이브러리 json 폴더를 탐색기로 연다 (없으면 만든다)."""
        from tools.A00550_PoseMapper.app.core.library import LIB_DIR
        try:
            os.makedirs(LIB_DIR, exist_ok=True)
            file_opener.open_path(LIB_DIR)
        except (OSError, ValueError) as e:
            self._log("[ERROR] Cannot open {0}: {1}".format(LIB_DIR, e))
            return
        self._log("[OK] Libraries folder: {0}".format(LIB_DIR))

    def on_open_guide(self, *args):
        try:
            file_opener.open_path(GUIDE_DOC)
        except (OSError, ValueError):
            self._log("[WARN] Guide not found: {0}".format(GUIDE_DOC))

    def show_about(self, *args):
        QMessageBox.information(self, "About", (
            "Pose Mapper v{0}\nUpdate date: {1}\n\n"
            "Pose Map : phoneme attributes (e.g. JALI_IN) -> blendShape targets.\n"
            "  Pick a phoneme, set the target values it gives at the reference value\n"
            "  (default 10), save the relation as json and connect it to any node pair.\n\n"
            "Blend Weights : blendWeighted inputs and weights. Inputs connected without\n"
            "  a weight element are computed as 1.0 but hidden in the Node Editor -\n"
            "  this tab shows them, adds inputs together with their weight, and\n"
            "  creates missing weights.\n\n"
            "Written by Ji Hun Park.").format(VERSION, LAST_UPDATE))
