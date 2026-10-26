# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Reference 하위탭 (PySide, standalone)
#
# 여러 마야 파일이 부르는 레퍼런스를 보고, 체크한 레퍼런스를 각 파일 안으로 임포트해 제자리 저장한다.
# A00210 은 마야 밖에서 도는 앱이라, maya.cmds 가 필요한 일(.mb 읽기 · 임포트)은 **mayapy 하위 프로세스**
# (core/maya_worker.py, ui/mayapy_process.py)로 한다. .ma 만 있으면 머리글 파싱으로 이 프로세스에서 바로 읽는다.
#
#   ┌ Tree (공용 폴더 트리 + 파일 체크박스, File Types 기본 ma/mb/fbx) ┐   <- 마야 파일을 고른다
#   [Add Checked] [Browse...]
#   ┌ Maya File (공용 TSL) ┐  ┌ Reference (트리, 체크박스, 중첩은 접힘) ┐
#   Scanned: ...
#   [x] Remove All Namespace  [x] Backup
#   [Get Reference]                         [Import Reference]
#   (mayapy 칸은 v01.41 부터 Maya 탭 아래에 하나 - mayapy_bar.py, 하위탭 공용)
#
# v01.41 : 파일 고르기(트리 · Add Checked · Maya File)를 maya_file_picker.MayaFilePicker 로, mayapy 칸을 mayapy_bar.MayapyBar 로 뽑아
#          Export 하위탭과 같이 쓴다. 동작은 그대로다 - file_rows / file_paths / selected_file_paths / add_files 는 picker 로 위임.
# 로직은 ../core (ref_scanner · ref_importer · backup · mayapy_runner). 이 파일은 화면과 흐름만.
# 설계 · 결정: docs/plans/A00210_FileManager_maya_reference_plan.md (§12 결정표, §14 A00210 이식).

import os

from Framework.qt.qt import (
    Qt,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QCheckBox,
    QSplitter,
    QMessageBox,
)

from ..core import ref_scanner
from ..core import ref_importer
from . import mayapy_process
from .maya_file_picker import MayaFilePicker
from .reference_tree import ReferenceTree


class ReferenceTab(QWidget):

    def __init__(self, log=None, prefs=None, mayapy_path=None, parent=None):
        """prefs : {"load", "save"} (지금은 mayapy_bar 가 쓴다 - 호환용으로 받아 둔다).
        mayapy_path : () -> mayapy 경로("" 가능) 콜러블 (MayaTab 의 MayapyBar.path). 없으면 자동 탐색."""
        super().__init__(parent)
        self._log_callback = log
        self._prefs = prefs
        self._mayapy_path = mayapy_path
        self._scan = None                 # 마지막 Get Reference 결과
        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        self.picker = MayaFilePicker(
            log=self._log, parent=self,
            list_tooltip="Maya files to work on. Select rows and press Get Reference.\nDouble-click: open in File Explorer.")
        self.file_tree = self.picker.tree
        self.maya_list = self.picker.maya_list

        self.splitter = QSplitter(Qt.Vertical)
        root.addWidget(self.splitter, stretch=1)
        self.splitter.addWidget(self.file_tree)

        # ---- 아래: Maya File | Reference ------------------------------
        lower = QWidget()
        lower_layout = QVBoxLayout(lower)
        lower_layout.setContentsMargins(0, 0, 0, 0)
        lower_layout.addWidget(self.picker.add_bar)

        lists = QSplitter(Qt.Horizontal)
        lists.addWidget(self.maya_list)

        ref_box = QGroupBox("Reference")
        ref_layout = QVBoxLayout(ref_box)
        self.ref_tree = ReferenceTree()
        self.ref_tree.setMinimumHeight(120)
        self.ref_tree.checksChanged.connect(self._update_counts)
        ref_layout.addWidget(self.ref_tree, stretch=1)
        ref_btns = QHBoxLayout()
        self.btn_check_all = QPushButton("Check All")
        self.btn_check_all.clicked.connect(lambda: self.ref_tree.set_all_checked(True))
        self.btn_uncheck_all = QPushButton("Uncheck All")
        self.btn_uncheck_all.clicked.connect(lambda: self.ref_tree.set_all_checked(False))
        self.lbl_ref_count = QLabel("Checked: 0 / 0")
        ref_btns.addWidget(self.btn_check_all)
        ref_btns.addWidget(self.btn_uncheck_all)
        ref_btns.addStretch(1)
        ref_btns.addWidget(self.lbl_ref_count)
        ref_layout.addLayout(ref_btns)
        lists.addWidget(ref_box)
        lists.setStretchFactor(0, 2)
        lists.setStretchFactor(1, 3)
        lower_layout.addWidget(lists, stretch=1)

        self.lbl_scanned = QLabel("Scanned: -")
        self.lbl_scanned.setWordWrap(True)
        self.lbl_scanned.setToolTip(
            "The Maya files the Reference list was read from. Import Reference works on these.")
        lower_layout.addWidget(self.lbl_scanned)

        self.splitter.addWidget(lower)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        # ---- 옵션 행 + 동작 행 ----------------------------------------------
        opt_row = QHBoxLayout()
        self.chk_remove_ns = QCheckBox("Remove All Namespace")
        self.chk_remove_ns.setChecked(True)
        self.chk_remove_ns.setToolTip(
            "After importing, merge every namespace in the scene into the root\n"
            "(namespaces of references that stay referenced cannot be removed and are kept).")
        opt_row.addWidget(self.chk_remove_ns)

        self.chk_backup = QCheckBox("Backup")
        self.chk_backup.setChecked(True)
        self.chk_backup.setToolTip(
            "Before saving, copy the original to <folder>/backup/<name>_REF_NN<ext>\n"
            "(the same backup folder A00220_BackupTool uses; _BU files are its own).")
        opt_row.addWidget(self.chk_backup)
        opt_row.addStretch(1)
        root.addLayout(opt_row)

        act_row = QHBoxLayout()
        self.btn_get = QPushButton("Get Reference")
        self.btn_get.setToolTip(
            "Read the references of the selected Maya files (all files if nothing is selected).\n"
            ".ma files are read from their header right here; .mb files (and nested .mb) are read\n"
            "by mayapy in the background (takes a moment to start Maya).")
        self.btn_get.clicked.connect(self.on_get_reference)
        act_row.addWidget(self.btn_get, stretch=1)

        self.btn_import = QPushButton("Import Reference")
        self.btn_import.setToolTip(
            "For every scanned Maya file: open it in mayapy, import the checked references it uses\n"
            "(nested references come along), remove namespaces, and save it in place.")
        self.btn_import.clicked.connect(self.on_import_reference)
        act_row.addWidget(self.btn_import, stretch=1)
        root.addLayout(act_row)

    # ==================================================================
    # mayapy (MayaTab 의 MayapyBar 에 위임)
    # ==================================================================

    def mayapy_path(self):
        if self._mayapy_path:
            return self._mayapy_path()
        from ..core import mayapy_runner
        return mayapy_runner.find_mayapy("")

    def _require_mayapy(self):
        mayapy = self.mayapy_path()
        if not mayapy:
            self._log("[WARN] mayapy.exe not found - set it in the mayapy box (Browse... / Detect).")
            QMessageBox.warning(self, "mayapy", "mayapy.exe was not found.\n\n"
                                "Reading .mb files and importing references needs Maya's Python.\n"
                                "Set the path in the mayapy box (Browse... or Detect).")
        return mayapy

    # ==================================================================
    # Maya File list (picker 위임)
    # ==================================================================

    def file_rows(self):
        return self.picker.file_rows()

    def file_paths(self):
        return self.picker.file_paths()

    def selected_file_paths(self):
        return self.picker.selected_file_paths()

    def add_files(self, paths):
        return self.picker.add_files(paths)

    def on_add_checked(self):
        self.picker.on_add_checked()

    def on_browse(self):
        self.picker.on_browse()

    def on_clear_files(self):
        self.picker.clear()

    # ==================================================================
    # Get Reference
    # ==================================================================

    def on_get_reference(self):
        paths = self.selected_file_paths() or self.file_paths()
        if not paths:
            self._log("[WARN] Add Maya files first (Add Checked / Browse...).")
            return
        paths = [p for p in paths if os.path.isfile(p)]
        if not paths:
            self._log("[WARN] None of the files exists on disk.")
            return

        # 1) 이 프로세스에서 머리글만 읽어 본다 - .mb 를 만나면 needs_maya.
        result = ref_scanner.scan(paths, log=None, allow_open=False)
        if result.get("needs_maya"):
            mayapy = self._require_mayapy()
            if not mayapy:
                return
            self._log("Get Reference : .mb file(s) involved - reading with mayapy...")
            outcome = mayapy_process.run_job(
                self, mayapy, {"job": "scan", "files": paths},
                title="File Manager - Get Reference", message="Starting mayapy...", log=self._log)
            if outcome.error or outcome.result is None:
                self._log("[WARN] Get Reference failed : {0}".format(outcome.error or "no result"))
                return
            result = outcome.result
        else:
            for line in result.get("logs", []):
                self._log(line)
            self._log("Get Reference : read from file headers (no .mb involved).")

        self._scan = result
        self.ref_tree.load(result)
        self._update_counts()
        names = [os.path.basename(f) for f in result["files"]]
        self.lbl_scanned.setText("Scanned: {0} ({1})".format(", ".join(names), len(names)))
        self._log("[OK] Get Reference : {0} file(s), {1} reference(s) listed.".format(
            len(result["files"]), self.ref_tree.topLevelItemCount()))

    # ==================================================================
    # Import Reference
    # ==================================================================

    def on_import_reference(self):
        if not self._scan:
            self._log("[WARN] Press Get Reference first.")
            return
        checked = self.ref_tree.checked_keys()
        if not checked:
            self._log("[WARN] Check at least one reference to import.")
            return
        jobs = ref_importer.plan(self._scan, checked)
        if not jobs:
            self._log("[WARN] None of the scanned files uses a checked reference.")
            return
        mayapy = self._require_mayapy()
        if not mayapy:
            return

        lines = ["{0}  <-  {1}".format(
            os.path.basename(f), ", ".join(self._scan["nodes"][k]["name"] for k in keys))
            for f, keys in jobs]
        answer = QMessageBox.question(
            self, "Import Reference",
            "{0} Maya file(s) will be opened in mayapy, modified and saved in place:\n\n{1}\n\n"
            "Backup : {2}\nRemove All Namespace : {3}\n\nContinue?".format(
                len(jobs), "\n".join(lines),
                "ON" if self.chk_backup.isChecked() else "OFF",
                "ON" if self.chk_remove_ns.isChecked() else "OFF"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            self._log("Import Reference cancelled.")
            return

        outcome = mayapy_process.run_job(
            self, mayapy,
            {"job": "import", "scan": self._scan, "checked": list(checked),
             "remove_namespaces": self.chk_remove_ns.isChecked(),
             "make_backup": self.chk_backup.isChecked()},
            title="File Manager - Import Reference", message="Starting mayapy...", log=self._log)

        summary = outcome.result
        if outcome.error and summary is None:
            self._log("[WARN] Import Reference failed : {0}".format(outcome.error))
            return
        if summary:
            tag = "[OK]" if not summary["failed"] and not summary["cancelled"] else "[WARN]"
            self._log("{0} Import Reference done - {1} saved, {2} skipped, {3} failed{4}.".format(
                tag, summary["saved"], summary["skipped"], summary["failed"],
                " (cancelled)" if summary["cancelled"] else ""))
            self._log("Press Get Reference again to refresh the list.")

    # ==================================================================
    # helpers
    # ==================================================================

    def _update_counts(self, *_args):
        total = sum(1 for it in self.ref_tree.top_items()
                    if it.data(0, Qt.CheckStateRole) is not None)
        self.lbl_ref_count.setText("Checked: {0} / {1}".format(
            len(self.ref_tree.checked_keys()), total))

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
