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
        self.resize(760, 820)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
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
        layout.addWidget(self.tabs, 1)

        log_box = QGroupBox("Log")
        log_layout = QVBoxLayout(log_box)
        log_layout.addWidget(self.log_view)
        layout.addWidget(log_box)

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _on_tab_changed(self, index):
        # 다른 탭으로 가면 Pose Map 의 Solo preview 를 원복한다.
        if self.tabs.widget(index) is not self.pose_tab and hasattr(self.pose_tab, "stop_preview"):
            self.pose_tab.stop_preview()
        if self.tabs.widget(index) is self.bw_tab:
            self.bw_tab.refresh_nodes()

    def closeEvent(self, event):
        if hasattr(self.pose_tab, "stop_preview"):
            self.pose_tab.stop_preview()
        super().closeEvent(event)

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
