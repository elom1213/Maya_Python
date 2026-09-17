# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - Import 탭 (in-Maya)
#
# 임포트 설정. 지금은 A00030_quickTool_V02 `Import option` 섹션의 버튼 하나다.
# 기능을 더할 때는 SECTIONS 에 한 줄 (섹션이 3~4개를 넘으면 하위 탭으로 나눈다).

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
)

from tools.A00480_FileTool.app import core
from tools.A00480_FileTool.app.ui.button_section import build_button_section


class ImportTab(QWidget):

    # (섹션 제목, [(라벨, 핸들러 이름, 툴팁), ...])
    SECTIONS = (
        ("FBX Import Option", (
            ("Import FBX normal", "on_import_fbx_normal",
             "Make FBX import use the normals stored in the file.\n"
             "This is a global FBX setting - it applies to the next import."),
        )),
    )

    def __init__(self, log=None, parent=None):
        super(ImportTab, self).__init__(parent)
        self._log_callback = log
        self.buttons = {}
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        for title, specs in self.SECTIONS:
            layout.addWidget(build_button_section(self, title, specs, self.buttons))
        layout.addStretch(1)

    # ---- Handlers ----------------------------------------------------

    def on_import_fbx_normal(self):
        self._log_all(core.import_fbx_normal())

    # ---- Helper ------------------------------------------------------

    def _log_all(self, messages):
        for message in (messages or []):
            if self._log_callback:
                self._log_callback(message)
