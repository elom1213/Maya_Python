# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00480_FileTool / Maya 탭 - 마야 파일(씬 파일 자체)을 다루는 명령을 모으는 탭. 하위탭을 담는다.
#
#   Reference : 여러 마야 파일의 레퍼런스를 보고, 체크한 것을 각 파일 안으로 임포트해 제자리 저장
#   (다음 하위탭은 여기에 addTab 한 줄로 는다)
#
# 이 탭은 `log` 콜백만 받는다(A00480 의 다른 탭과 같다). 나중에 독립 툴로 뗄 때는 이 위젯이 그 툴의
# 본체가 된다 - app/maya 폴더 밖을 가리키는 import 는 Framework 뿐이다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from .reference_tab import ReferenceTab


class MayaTab(QWidget):

    def __init__(self, log=None, parent=None):
        super().__init__(parent)
        self._log_callback = log
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.reference_tab = ReferenceTab(log=self._log)
        self.tabs.addTab(self.reference_tab, "Reference")
        self.tabs.setTabToolTip(
            0, "List the references of several Maya files and import the checked ones into each file.")
        layout.addWidget(self.tabs)

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
