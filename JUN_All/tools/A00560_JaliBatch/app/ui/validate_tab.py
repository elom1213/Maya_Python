# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - Validate 탭 (PySide): 클립 폴더의 .mb 를 mayapy 로 열어 점검 · 컨트롤러 Repath
#
#   Clip folder [폴더][...][Scan]      - .mb 목록 (backup/ 제외) + 매니페스트 상태
#   표 Clip | Manifest | Controller | Loaded | Failed edits | Baked | Keys | DUMMY_IN | Stamp | Result
#   Repath controller [.ma][...]  [Validate] [Repath]
# Validate 는 열기만 한다(저장 없음). Repath 는 컨트롤러 레퍼런스 경로를 바꾸고 **그때만** 저장한다 (평가서 §2-3).

import os

from Framework.qt.qt import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QFileDialog, QMessageBox, QColor, QBrush, Qt,
)

from ..config.version import VERSION
from ..core import manifest, jobs

COLUMNS = ("Clip", "Manifest", "Controller", "Loaded", "Failed edits", "Baked", "Keys", "DUMMY_IN", "Stamp", "Result")
(COL_NAME, COL_MANIFEST, COL_CTL, COL_LOADED, COL_FAILED, COL_BAKED, COL_KEYS, COL_DUMMY, COL_STAMP, COL_RESULT) = range(10)
TOOL_TAG = "A00560_JaliBatch {0}".format(VERSION)
RED, YELLOW, GREEN = "#d05050", "#d0a040", "#5aa05a"


class ValidateTab(QWidget):

    def __init__(self, log=None, run_worker=None, prefs=None, parent=None):
        super().__init__(parent)
        self._log_cb = log
        self._run_worker = run_worker
        self.paths = []
        self.manifest = None
        self.rows = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        top = QGroupBox("Clips")
        grid = QGridLayout(top)
        self.le_folder = QLineEdit()
        self.le_folder.setPlaceholderText("Clip folder (the Batch output folder with jali_clips.manifest.json)")
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(32)
        btn_browse.clicked.connect(self.on_browse_folder)
        btn_scan = QPushButton("Scan")
        btn_scan.clicked.connect(self.scan)
        grid.addWidget(QLabel("Clip folder"), 0, 0)
        grid.addWidget(self.le_folder, 0, 1)
        grid.addWidget(btn_browse, 0, 2)
        grid.addWidget(btn_scan, 0, 3)
        grid.setColumnStretch(1, 1)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(180)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_CTL, QHeaderView.Stretch)
        for c in (COL_MANIFEST, COL_LOADED, COL_FAILED, COL_BAKED, COL_KEYS, COL_DUMMY, COL_STAMP):
            header.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.setToolTip("Failed edits > 0 (red) = the controller changed names; Stamp 'changed' (yellow) = the controller\n"
                              "file was modified after the clip was made (fine if only values changed).")
        grid.addWidget(self.table, 1, 0, 1, 4)
        self.lb_info = QLabel("No clips - press Scan")
        grid.addWidget(self.lb_info, 2, 0, 1, 4)
        root.addWidget(top, 1)

        rep = QGroupBox("Controller")
        rg = QGridLayout(rep)
        self.le_repath = QLineEdit()
        self.le_repath.setPlaceholderText("New controller .ma / .mb for Repath (optional)")
        self.le_repath.setToolTip("Repath = switch the JALI reference of the selected (or all) clips to this file and save them.")
        btn_rep = QPushButton("...")
        btn_rep.setFixedWidth(32)
        btn_rep.clicked.connect(self.on_browse_repath)
        rg.addWidget(QLabel("Repath to"), 0, 0)
        rg.addWidget(self.le_repath, 0, 1)
        rg.addWidget(btn_rep, 0, 2)
        rg.setColumnStretch(1, 1)
        root.addWidget(rep)

        brow = QHBoxLayout()
        self.btn_validate = QPushButton("Validate")
        self.btn_validate.setMinimumHeight(32)
        self.btn_validate.setToolTip("Open the selected clips (all if none selected) in mayapy and check them. Nothing is saved.")
        self.btn_validate.clicked.connect(lambda _=False: self.validate(repath=False))
        self.btn_repath = QPushButton("Repath")
        self.btn_repath.setMinimumHeight(32)
        self.btn_repath.setToolTip("Switch the controller reference to 'Repath to' and save the selected clips (all if none selected).")
        self.btn_repath.clicked.connect(lambda _=False: self.validate(repath=True))
        brow.addWidget(self.btn_validate, 2)
        brow.addWidget(self.btn_repath, 1)
        root.addLayout(brow)

    # ------------------------------------------------------------------ helpers

    def _log(self, message):
        if self._log_cb:
            self._log_cb(message)

    def folder(self):
        return os.path.normpath(self.le_folder.text().strip()) if self.le_folder.text().strip() else ""

    def load_prefs(self, p):
        self.le_folder.setText(p.get("validate_dir", ""))
        self.le_repath.setText(p.get("repath_controller", ""))

    def save_prefs(self, p):
        p["validate_dir"] = self.le_folder.text().strip()
        p["repath_controller"] = self.le_repath.text().strip()

    def set_folder(self, folder):
        """Batch 탭이 끝나면 부른다 - 폴더를 채우고 목록을 새로 읽는다."""
        self.le_folder.setText(os.path.normpath(folder))
        self.scan()

    def on_browse_folder(self, *args):
        path = QFileDialog.getExistingDirectory(self, "Clip folder", self.folder() or "")
        if path:
            self.le_folder.setText(os.path.normpath(path))
            self.scan()

    def on_browse_repath(self, *args):
        start = os.path.dirname(self.le_repath.text().strip()) if self.le_repath.text().strip() else ""
        path, _ = QFileDialog.getOpenFileName(self, "New controller", start, "Maya scene (*.ma *.mb);;All files (*.*)")
        if path:
            self.le_repath.setText(os.path.normpath(path))

    # ------------------------------------------------------------------ Scan

    def scan(self, *args):
        folder = self.folder()
        if not folder or not os.path.isdir(folder):
            self._log("[ERROR] Clip folder not found: {0}".format(folder or "(empty)"))
            self.paths = []
            self.table.setRowCount(0)
            return
        try:
            self.manifest = manifest.load(folder, VERSION)
        except ValueError as e:
            self._log("[WARN] {0}".format(e))
            self.manifest = manifest.empty(VERSION)
        names = sorted((f for f in os.listdir(folder) if f.lower().endswith(".mb")),
                       key=lambda n: [int(p) if p.isdigit() else p.lower() for p in __import__("re").split(r"(\d+)", n)])
        self.paths = [os.path.join(folder, n) for n in names]
        self.rows = {}
        self.table.setRowCount(len(self.paths))
        for i, path in enumerate(self.paths):
            name = os.path.splitext(os.path.basename(path))[0]
            entry = manifest.clip(self.manifest, name) or {}
            values = [name, entry.get("status", "-"), os.path.basename(entry.get("controller", "")) or "?", "", "", "", "", "", "", ""]
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                if c not in (COL_NAME, COL_CTL):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, c, item)
            self.table.item(i, COL_NAME).setToolTip(path)
            if entry.get("status") == manifest.STATUS_EDITED:
                self.table.item(i, COL_MANIFEST).setForeground(QBrush(QColor(YELLOW)))
            elif entry.get("status") == manifest.STATUS_FAILED:
                self.table.item(i, COL_MANIFEST).setForeground(QBrush(QColor(RED)))
        self.lb_info.setText("{0} clip(s), {1} in manifest".format(len(self.paths), len(self.manifest["clips"])))
        self._log("[OK] Scan: {0} clip(s) in {1}".format(len(self.paths), folder))

    def selected_paths(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        return [self.paths[r] for r in rows] if rows else list(self.paths)

    # ------------------------------------------------------------------ Validate · Repath

    def validate(self, repath=False):
        paths = self.selected_paths()
        if not paths:
            self._log("[WARN] Press Scan first.")
            return None
        new_ctl = ""
        if repath:
            new_ctl = os.path.normpath(self.le_repath.text().strip()) if self.le_repath.text().strip() else ""
            if not new_ctl or not os.path.isfile(new_ctl):
                self._log("[ERROR] Repath to: controller file not found: {0}".format(new_ctl or "(empty)"))
                return None
            answer = QMessageBox.question(
                self, "Repath controller",
                "{0} clip(s) will be opened in mayapy, their JALI reference switched to\n{1}\nand saved in place. Continue?".format(
                    len(paths), new_ctl), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                self._log("Repath cancelled.")
                return None
        job = jobs.validate_job(paths, manifest.path_for(self.folder()), TOOL_TAG, repath=new_ctl)
        self._log("{0}: {1} clip(s)".format("Repath" if repath else "Validate", len(paths)))
        outcome = self._run_worker(job, "JALI Batch - {0}".format("Repath" if repath else "Validate")) if self._run_worker else None
        if outcome is None:
            return None
        if outcome.error and outcome.result is None:
            self._log("[ERROR] {0} failed : {1}".format("Repath" if repath else "Validate", outcome.error))
            return outcome
        if outcome.result:
            self.apply_result(outcome.result)
            res = outcome.result
            tag = "[OK]" if not res["warn"] and not res["failed"] and not res["cancelled"] else "[WARN]"
            self._log("{0} {1} done - {2} ok, {3} warn, {4} failed{5}.".format(
                tag, "Repath" if repath else "Validate", res["ok"], res["warn"], res["failed"],
                " (cancelled)" if res["cancelled"] else ""))
        return outcome

    def apply_result(self, result):
        """워커 결과 rows 를 표에 (경로로 행을 찾는다)."""
        by_path = {os.path.normcase(os.path.normpath(p)): i for i, p in enumerate(self.paths)}
        for row in result.get("rows", []):
            i = by_path.get(os.path.normcase(os.path.normpath(row.get("mb", ""))))
            if i is None:
                continue
            self.rows[i] = row
            ctl = row.get("controller") or ""
            self.table.item(i, COL_CTL).setText(os.path.basename(ctl) or "?")
            self.table.item(i, COL_CTL).setToolTip(ctl)
            self.table.item(i, COL_LOADED).setText("yes" if row.get("loaded") else "no")
            failed = row.get("failed_edits", 0) or 0
            self.table.item(i, COL_FAILED).setText(str(failed))
            self.table.item(i, COL_FAILED).setForeground(QBrush(QColor(RED)) if failed else QBrush())
            self.table.item(i, COL_FAILED).setToolTip("\n".join(row.get("failed_edit_samples", [])))
            self.table.item(i, COL_BAKED).setText(str(row.get("baked_channels", "")))
            self.table.item(i, COL_KEYS).setText(str(row.get("keys", "")))
            dummy = row.get("dummy_in_curves", 0) or 0
            self.table.item(i, COL_DUMMY).setText(str(dummy))
            self.table.item(i, COL_DUMMY).setForeground(QBrush(QColor(RED)) if dummy else QBrush())
            stamp = row.get("stamp")
            if not stamp:
                stamp_text, color = "none", RED
            elif row.get("controller_changed"):
                stamp_text, color = "changed", YELLOW
            else:
                stamp_text, color = "ok", None
            self.table.item(i, COL_STAMP).setText(stamp_text)
            self.table.item(i, COL_STAMP).setForeground(QBrush(QColor(color)) if color else QBrush())
            if stamp:
                self.table.item(i, COL_STAMP).setToolTip("start {0} end {1} fps {2:g}\nmade {3}\n{4}".format(
                    stamp.get("start"), stamp.get("end"), float(stamp.get("fps", 0)), stamp.get("generated_at"), stamp.get("controller")))
            status = row.get("status", "")
            text = "; ".join(row.get("problems", [])) or ("ok" + (" (repathed)" if row.get("repathed") else ""))
            self.table.item(i, COL_RESULT).setText(text)
            self.table.item(i, COL_RESULT).setToolTip(text)
            self.table.item(i, COL_RESULT).setForeground(QBrush(QColor({"ok": GREEN, "warn": YELLOW}.get(status, RED))))
