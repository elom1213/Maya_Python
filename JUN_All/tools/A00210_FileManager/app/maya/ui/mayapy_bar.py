# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 - mayapy 칸 (하위탭 공용, v01.41). reference_tab.py 에 있던 행을 그대로 뽑았다.
#
#   mayapy [............................] [Browse...] [Detect]
#
# 값은 prefs 프로파일 `mayapy_path` 에 저장(비면 자동 탐색). 하위탭은 `path()` 콜러블로 경로를 얻고, 없을 때의 안내는 `require(parent)`.

import os

from Framework.qt.qt import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from ..core import mayapy_runner

MAYAPY_FILTER = "mayapy (mayapy.exe);;All Files (*)"


class MayapyBar(QWidget):

    def __init__(self, prefs=None, log=None, parent=None):
        """prefs : {"load": fn()->dict, "save": fn(dict)} 또는 None(세션 안에서만 기억)."""
        super().__init__(parent)
        self._prefs = prefs
        self._log_callback = log
        self.build_ui()
        self._load_pref()

    def build_ui(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QLabel("mayapy"))
        self.ipf_mayapy = QLineEdit()
        self.ipf_mayapy.setPlaceholderText("mayapy.exe - runs the Maya work in the background (auto-detected)")
        self.ipf_mayapy.setToolTip(
            "This app runs outside Maya. Reading .mb files, importing references, checking sets and\n"
            "baking / exporting FBX are done by mayapy.exe (Maya's Python) in the background.\n"
            "Leave empty to use the newest Maya found under Program Files\\Autodesk. Saved with the profile.")
        self.ipf_mayapy.editingFinished.connect(self._save_pref)
        row.addWidget(self.ipf_mayapy, stretch=1)
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self.on_browse)
        row.addWidget(self.btn_browse)
        self.btn_detect = QPushButton("Detect")
        self.btn_detect.setToolTip("Find mayapy.exe under Program Files\\Autodesk (newest Maya first).")
        self.btn_detect.clicked.connect(self.on_detect)
        row.addWidget(self.btn_detect)

    # ------------------------------------------------------------------
    def path(self):
        """칸의 경로가 실제 파일이면 그것, 아니면 자동 탐색. 없으면 ""."""
        return mayapy_runner.find_mayapy(self.ipf_mayapy.text().strip())

    def require(self, parent=None):
        """경로를 돌려주되, 없으면 로그 + 경고 팝업 뒤 ""."""
        mayapy = self.path()
        if not mayapy:
            self._log("[WARN] mayapy.exe not found - set it in the mayapy box (Browse... / Detect).")
            QMessageBox.warning(parent or self, "mayapy", "mayapy.exe was not found.\n\n"
                                "This step needs Maya's Python.\n"
                                "Set the path in the mayapy box (Browse... or Detect).")
        return mayapy

    def on_browse(self, *_args):
        start = os.path.dirname(self.ipf_mayapy.text().strip()) or r"C:\Program Files\Autodesk"
        path, _flt = QFileDialog.getOpenFileName(self, "Select mayapy.exe", start, MAYAPY_FILTER)
        if path:
            self.ipf_mayapy.setText(os.path.normpath(path))
            self._save_pref()

    def on_detect(self, *_args):
        found = mayapy_runner.candidates()
        if not found:
            self._log("[WARN] No mayapy.exe found under Program Files\\Autodesk. Use Browse...")
            return
        self.ipf_mayapy.setText(found[0])
        self._save_pref()
        self._log("mayapy : {0}{1}".format(
            found[0], "" if len(found) == 1 else "  (+{0} more)".format(len(found) - 1)))

    # ------------------------------------------------------------------
    def _load_pref(self):
        if not self._prefs:
            return
        try:
            path = (self._prefs["load"]() or {}).get("mayapy_path", "") or ""
        except Exception:  # noqa: BLE001
            path = ""
        self.ipf_mayapy.setText(path)

    def _save_pref(self):
        if not self._prefs:
            return
        try:
            data = self._prefs["load"]() or {}
            text = self.ipf_mayapy.text().strip()
            if data.get("mayapy_path", "") != text:
                data["mayapy_path"] = text
                self._prefs["save"](data)
        except Exception as exc:  # noqa: BLE001
            self._log("[WARN] Could not save the mayapy path : {0}".format(exc))

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
