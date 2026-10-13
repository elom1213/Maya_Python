# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-13
# A00480_FileTool - Import 탭 (in-Maya)
#
# v01.10 부터 **하위 탭** 둘이다:
#   CSV : A00200_CSV_tool (ARKit Facial Import) 이식 - ui/import_csv_page.py
#   FBX : A00030_quickTool_V02 `Import option` 의 Import FBX normal (SECTIONS 표, 예전 Import 탭 내용 그대로)
#
# FBX 쪽에 버튼을 더할 때는 SECTIONS 에 한 줄. 새 파일 형식은 하위 탭 하나를 더한다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from tools.A00480_FileTool.app import core
from tools.A00480_FileTool.app.ui.button_section import build_button_section
from tools.A00480_FileTool.app.ui.import_csv_page import CsvImportPage


class FbxImportPage(QWidget):
    """Import > FBX : 임포트 설정 버튼들 (SECTIONS 표)."""

    # (섹션 제목, [(라벨, 핸들러 이름, 툴팁), ...])
    SECTIONS = (
        ("FBX Import Option", (
            ("Import FBX normal", "on_import_fbx_normal",
             "Make FBX import use the normals stored in the file.\n"
             "This is a global FBX setting - it applies to the next import."),
        )),
    )

    def __init__(self, log=None, parent=None):
        super(FbxImportPage, self).__init__(parent)
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


class ImportTab(QWidget):
    """Import 탭 = 하위 탭 CSV / FBX."""

    def __init__(self, log=None, parent=None):
        super(ImportTab, self).__init__(parent)
        self._log_callback = log
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.csv_page = CsvImportPage(log=self._log_callback)
        self.fbx_page = FbxImportPage(log=self._log_callback)
        self.tabs.addTab(self.csv_page, "CSV")
        self.tabs.addTab(self.fbx_page, "FBX")
        self.tabs.setTabToolTip(0, "ARKit facial CSV (Live Link Face) -> keyframes on a node, plus audio.")
        self.tabs.setTabToolTip(1, "FBX import settings.")
        layout.addWidget(self.tabs)

        # 예전 ImportTab.buttons 와 같은 접근 경로 유지 (테스트 · 외부 접근용)
        self.buttons = self.fbx_page.buttons

    # ---- 호환 (v01.09 까지의 핸들러 이름) --------------------------------

    def on_import_fbx_normal(self):
        self.fbx_page.on_import_fbx_normal()
