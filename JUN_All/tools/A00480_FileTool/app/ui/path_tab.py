# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - Path 탭 (in-Maya)
#
# 경로 확인 · 조작. 지금은 A00030_quickTool_V02 `File` 섹션의 버튼 둘이다.
# 경로를 찾는 것은 core, 클립보드에 넣는 것은 여기(Qt).

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QApplication,
)

from tools.A00480_FileTool.app import core
from tools.A00480_FileTool.app.ui.button_section import build_button_section


class PathTab(QWidget):

    # (섹션 제목, [(라벨, 핸들러 이름, 툴팁), ...])
    SECTIONS = (
        ("Scene Folder", (
            ("Copy Scene Folder", "on_copy_scene_folder",
             "Copy the folder of the current scene to the clipboard."),
            ("Open Scene Folder", "on_open_scene_folder",
             "Open the folder of the current scene in the file explorer\n"
             "(the scene file is selected)."),
        )),
    )

    def __init__(self, log=None, parent=None):
        super(PathTab, self).__init__(parent)
        self._log_callback = log
        self.buttons = {}
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        for title, specs in self.SECTIONS:
            layout.addWidget(build_button_section(self, title, specs, self.buttons))
        layout.addStretch(1)

    # ---- Handlers ----------------------------------------------------

    def on_copy_scene_folder(self):
        folder, logs = core.scene_folder()
        self._log_all(logs)
        if not folder:
            return

        clipboard = QApplication.clipboard()
        if clipboard is None:
            self._log("[WARN] Could not access the system clipboard.")
            return

        clipboard.setText(folder)
        self._log("Copied to clipboard : {0}".format(folder))

    def on_open_scene_folder(self):
        self._log_all(core.open_scene_folder())

    # ---- Helper ------------------------------------------------------

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)

    def _log_all(self, messages):
        for message in (messages or []):
            self._log(message)
