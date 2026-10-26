# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 - 마야 파일(씬 파일 자체)을 다루는 명령을 모으는 탭. 하위탭을 담는다.
#
#   Reference : 여러 마야 파일의 레퍼런스를 보고, 체크한 것을 각 파일 안으로 임포트해 제자리 저장          (v01.35)
#   Export    : 규칙(세트 이름)에 맞는 세트가 있는 파일을 솎아내 범위 · fps 를 보이고, 베이크 -> FBX / FBX 만    (v01.41)
#   (다음 하위탭은 여기에 addTab 한 줄로 는다)
#   mayapy 칸은 하위탭 아래에 **하나** (mayapy_bar.MayapyBar) - 하위탭은 `mayapy_path` 콜러블로 받는다.
#
# 이 탭은 `log` 콜백과 prefs 접근자만 받는다. 나중에 독립 툴로 뗄 때는 이 위젯이 그 툴의 본체가 된다 -
# app/maya 폴더 밖을 가리키는 import 는 Framework 와 (mayapy 경로 · Export 설정을 기억할) A00210 prefs 뿐이다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from .mayapy_bar import MayapyBar
from .reference_tab import ReferenceTab
from .export_tab import ExportTab


class MayaTab(QWidget):

    def __init__(self, log=None, prefs=None, parent=None):
        """prefs : {"load": fn()->dict, "save": fn(dict)} 또는 None. 없으면 A00210 의 prefs 모듈을 쓴다."""
        super().__init__(parent)
        self._log_callback = log
        if prefs is None:
            try:
                from ...core import prefs as prefs_mod
                prefs = {"load": prefs_mod.load, "save": prefs_mod.save}
            except Exception:  # noqa: BLE001 - 분리된 툴에서는 없다
                prefs = None
        self._prefs = prefs
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.mayapy_bar = MayapyBar(prefs=self._prefs, log=self._log)

        self.tabs = QTabWidget()
        self.reference_tab = ReferenceTab(log=self._log, prefs=self._prefs, mayapy_path=self.mayapy_bar.path)
        self.tabs.addTab(self.reference_tab, "Reference")
        self.tabs.setTabToolTip(
            0, "List the references of several Maya files and import the checked ones into each file.")
        self.export_tab = ExportTab(log=self._log, prefs=self._prefs, mayapy_path=self.mayapy_bar.path)
        self.tabs.addTab(self.export_tab, "Export")
        self.tabs.setTabToolTip(
            1, "Find the files that hold a set matching a rule (e.g. 'Bake'), show their frame range and fps,\n"
               "then bake the set's joints and export each file to FBX (or export without baking).")
        layout.addWidget(self.tabs, stretch=1)
        layout.addWidget(self.mayapy_bar)

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
