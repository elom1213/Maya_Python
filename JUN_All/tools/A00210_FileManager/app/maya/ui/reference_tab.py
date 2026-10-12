# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
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
#   mayapy [............................] [Browse...] [Detect]
#   [x] Remove All Namespace  [x] Backup
#   [Get Reference]                         [Import Reference]
#
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
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QBrush,
    QColor,
)
from Framework.qt import path_context
from Framework.qt.MOD_fileTree_qt_v01 import JUN_mod_fileTree_qt_v01
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01, null_item_color

from ..core import ref_scanner
from ..core import ref_importer
from ..core import mayapy_runner
from . import mayapy_process
from .reference_tree import ReferenceTree

DEFAULT_TYPES = ("ma", "mb", "fbx")        # 결정 ⑧
FILE_FILTER = "Maya Files (*.ma *.mb);;All Files (*)"
MAYAPY_FILTER = "mayapy (mayapy.exe);;All Files (*)"


class ReferenceTab(QWidget):

    def __init__(self, log=None, prefs=None, parent=None):
        """prefs : {"load": fn()->dict, "save": fn(dict)} - mayapy 경로를 기억할 곳(없으면 세션 안에서만)."""
        super().__init__(parent)
        self._log_callback = log
        self._prefs = prefs
        self._scan = None                 # 마지막 Get Reference 결과
        self.build_ui()
        self._load_mayapy_pref()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        self.splitter = QSplitter(Qt.Vertical)
        root.addWidget(self.splitter, stretch=1)

        # ---- 위: 폴더 트리 (공용) -------------------------------------
        self.file_tree = JUN_mod_fileTree_qt_v01(
            checkable_files=True, default_types=DEFAULT_TYPES)
        self.file_tree.tree.setMinimumHeight(140)
        self.file_tree.checksChanged.connect(self._on_tree_checks_changed)
        self.splitter.addWidget(self.file_tree)

        # ---- 아래: Maya File | Reference ------------------------------
        lower = QWidget()
        lower_layout = QVBoxLayout(lower)
        lower_layout.setContentsMargins(0, 0, 0, 0)

        add_row = QHBoxLayout()
        self.btn_add_checked = QPushButton("Add Checked")
        self.btn_add_checked.setToolTip(
            "Add the files checked in the tree above to the Maya File list.")
        self.btn_add_checked.clicked.connect(self.on_add_checked)
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setToolTip("Pick Maya files with a file dialog (several at once).")
        self.btn_browse.clicked.connect(self.on_browse)
        self.lbl_checked = QLabel("Checked in tree: 0")
        add_row.addWidget(self.btn_add_checked)
        add_row.addWidget(self.btn_browse)
        add_row.addWidget(self.lbl_checked)
        add_row.addStretch(1)
        lower_layout.addLayout(add_row)

        lists = QSplitter(Qt.Horizontal)

        # Maya File - 공용 TSL. 씬 노드가 아니므로 UUID · 선택 동기화 · 재정렬 버튼은 끈다
        # (Up/Down/Sort 는 UUID 역할만 옮겨 경로 데이터를 잃는다).
        self.maya_list = JUN_mod_tsl_qt_v01(
            title="Maya File", show_select=False, show_add=False, show_del=True,
            show_up=False, show_down=False, show_sort=False, show_order=False,
            attach_uuids=False, list_min_height=120, log_callback=self._log)
        self.maya_list.list_widget.setToolTip(
            "Maya files to work on. Select rows and press Get Reference.\n"
            "Double-click: open in File Explorer.")
        try:
            self.maya_list.list_widget.itemSelectionChanged.disconnect(
                self.maya_list._on_selection_changed)
        except (RuntimeError, TypeError):
            pass
        self.maya_list.add_button("Clear", self.on_clear_files)
        path_context.attach_path_context(
            self.maya_list.list_widget, lambda item: item.data(Qt.UserRole) or "",
            title="Maya File")
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

        # ---- mayapy 행 ---------------------------------------------------
        py_row = QHBoxLayout()
        py_row.addWidget(QLabel("mayapy"))
        self.ipf_mayapy = QLineEdit()
        self.ipf_mayapy.setPlaceholderText("mayapy.exe - reads .mb files and imports references (auto-detected)")
        self.ipf_mayapy.setToolTip(
            "This app runs outside Maya. Reading .mb files and importing references is done by\n"
            "mayapy.exe (Maya's Python) in the background. Leave empty to use the newest Maya found\n"
            "under Program Files\\Autodesk. Saved with the profile.")
        self.ipf_mayapy.editingFinished.connect(self._save_mayapy_pref)
        py_row.addWidget(self.ipf_mayapy, stretch=1)
        self.btn_mayapy_browse = QPushButton("Browse...")
        self.btn_mayapy_browse.clicked.connect(self.on_browse_mayapy)
        py_row.addWidget(self.btn_mayapy_browse)
        self.btn_mayapy_detect = QPushButton("Detect")
        self.btn_mayapy_detect.setToolTip("Find mayapy.exe under Program Files\\Autodesk (newest Maya first).")
        self.btn_mayapy_detect.clicked.connect(self.on_detect_mayapy)
        py_row.addWidget(self.btn_mayapy_detect)
        root.addLayout(py_row)

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
    # mayapy
    # ==================================================================

    def mayapy_path(self):
        """칸의 경로가 실제 파일이면 그것, 아니면 자동 탐색. 없으면 ""."""
        return mayapy_runner.find_mayapy(self.ipf_mayapy.text().strip())

    def on_browse_mayapy(self):
        start = os.path.dirname(self.ipf_mayapy.text().strip()) or r"C:\Program Files\Autodesk"
        path, _flt = QFileDialog.getOpenFileName(self, "Select mayapy.exe", start, MAYAPY_FILTER)
        if path:
            self.ipf_mayapy.setText(os.path.normpath(path))
            self._save_mayapy_pref()

    def on_detect_mayapy(self):
        found = mayapy_runner.candidates()
        if not found:
            self._log("[WARN] No mayapy.exe found under Program Files\\Autodesk. Use Browse...")
            return
        self.ipf_mayapy.setText(found[0])
        self._save_mayapy_pref()
        self._log("mayapy : {0}{1}".format(
            found[0], "" if len(found) == 1 else "  (+{0} more)".format(len(found) - 1)))

    def _load_mayapy_pref(self):
        if not self._prefs:
            return
        try:
            path = (self._prefs["load"]() or {}).get("mayapy_path", "") or ""
        except Exception:  # noqa: BLE001
            path = ""
        self.ipf_mayapy.setText(path)

    def _save_mayapy_pref(self):
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

    def _require_mayapy(self):
        mayapy = self.mayapy_path()
        if not mayapy:
            self._log("[WARN] mayapy.exe not found - set it in the mayapy box (Browse... / Detect).")
            QMessageBox.warning(self, "mayapy", "mayapy.exe was not found.\n\n"
                                "Reading .mb files and importing references needs Maya's Python.\n"
                                "Set the path in the mayapy box (Browse... or Detect).")
        return mayapy

    # ==================================================================
    # Maya File list
    # ==================================================================

    def file_rows(self):
        """[(표시 이름, 절대경로), ...]"""
        lw = self.maya_list.list_widget
        out = []
        for i in range(lw.count()):
            item = lw.item(i)
            out.append((item.text(), item.data(Qt.UserRole) or ""))
        return out

    def file_paths(self):
        return [p for _n, p in self.file_rows() if p]

    def selected_file_paths(self):
        return [item.data(Qt.UserRole) for item in self.maya_list.list_widget.selectedItems()
                if item.data(Qt.UserRole)]

    def add_files(self, paths):
        """중복 없이 담는다(경로 기준). 같은 이름이 다른 폴더에 있으면 이름 뒤에 폴더를 붙인다."""
        existing = {ref_scanner.norm_path(p) for p in self.file_paths()}
        names = {n for n, _p in self.file_rows()}
        added = 0
        for path in paths or []:
            if not path:
                continue
            path = os.path.normpath(os.path.abspath(path))
            key = ref_scanner.norm_path(path)
            if key in existing:
                self._log("{0} is already in the list.".format(os.path.basename(path)))
                continue
            if not ref_scanner.is_maya_scene(path):
                self._log("[WARN] Not a Maya scene, skipped : {0}".format(path))
                continue
            name = os.path.basename(path)
            if name in names:
                name = "{0}  ({1})".format(name, os.path.basename(os.path.dirname(path)))
            item = self.maya_list._add_item(name)
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            if not os.path.isfile(path):
                item.setForeground(QBrush(QColor(null_item_color())))
                item.setToolTip(path + "\nFile not found")
            existing.add(key)
            names.add(name)
            added += 1
        self.maya_list._update_number()
        if added:
            self._log("Added {0} Maya file(s).".format(added))
        return added

    def on_add_checked(self):
        paths = self.file_tree.checked_paths()
        if not paths:
            self._log("Nothing is checked in the tree.")
            return
        self.add_files(paths)

    def on_browse(self):
        start = ""
        rows = self.file_paths()
        if rows:
            start = os.path.dirname(rows[-1])
        paths, _flt = QFileDialog.getOpenFileNames(self, "Select Maya Files", start, FILE_FILTER)
        if paths:
            self.add_files(paths)

    def on_clear_files(self):
        self.maya_list.clear()

    def _on_tree_checks_changed(self, paths):
        self.lbl_checked.setText("Checked in tree: {0}".format(len(paths)))

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
