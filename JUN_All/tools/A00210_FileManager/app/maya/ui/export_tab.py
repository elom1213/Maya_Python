# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export 하위탭 (PySide, standalone)  (v01.41)
#
# 마야 파일 여러 개에서 **규칙(세트 이름, 예 Bake)에 맞는 세트**가 있는 파일을 솎아내고(Check Sets), 파일마다 재생 범위 · fps · 버전을 보인 뒤
# Bake & Export(세트 멤버 + 자손의 T/R/S 를 bakeResults -> FBX) 또는 Export Only(베이크 없이 FBX). 마야 일은 전부 mayapy 워커
# (core/maya_worker.py `probe` · `export`). 원본 마야 파일은 저장하지 않는다.
#
#   ┌ Tree (공용 폴더 트리, 파일 체크) ──────────────────────────────┐
#   [Add Checked] [Browse...]  Checked in tree: 0
#   ┌ Maya File (TSL) ─┐  Rule [Bake ▾] [New] [Edit] [Rename] [Delete] [Rules Folder...]   set "Bake" · exact · ignore namespace
#   │                  │  [Check Sets]
#   ┌ Files 표 ☑ File Set Start End FPS Ver Output Status ───────────┐
#   Range [Timeline (per file) ▾]  Custom Start [ ] End [ ]
#   ┌ Naming  Find [ ] Replace [ ] [x] Case  /  Insert [Token ▾] after token [0] text [bake]  /  Preview: anim_01.mb -> bake_anim_01.fbx ┐
#   Export Folder [            ] [Browse...] [Open]
#   Bake [x] Translate [x] Rotate [x] Scale  [x] Joints Only  [ ] Euler Filter
#   [x] Import References & Remove Namespaces
#   Resources: CPU ... · RAM ... · GPU ...
#   [ Bake & Export ]  [ Export Only ]
#   (mayapy 칸은 Maya 탭 아래 공용 - mayapy_bar.py)
#
# 설계 · 결정: docs/plans/A00210_FileManager_maya_export_plan.md (§2 D1~D18, §6 UI, §13 사용자 답). 모든 UI 문자열은 영어.

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
    QComboBox,
    QSpinBox,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QProcess,
)
from Framework.qt import path_context

from ..core import set_rules
from ..core import export_naming
from ..core import export_jobs
from ..core import hw_info
from . import mayapy_process
from .maya_file_picker import MayaFilePicker
from .export_table import ExportTable
from .set_rule_dialog import SetRuleDialog

# 베이크 한 호출이 수 분이라 Cancel 뒤 프로세스를 끊기까지 넉넉히 (설계 §7)
EXPORT_CANCEL_GRACE_SEC = 1800


class ExportTab(QWidget):

    def __init__(self, log=None, prefs=None, mayapy_path=None, parent=None):
        """prefs : {"load": fn()->dict, "save": fn(dict)} 또는 None. mayapy_path : () -> 경로 콜러블 (MayapyBar.path)."""
        super().__init__(parent)
        self._log_callback = log
        self._prefs = prefs
        self._mayapy_path = mayapy_path
        self._rules = []
        self._rules_dir = ""
        self._loading = False
        self.build_ui()
        self.load_prefs()
        self._start_hw_probe()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        self.picker = MayaFilePicker(
            log=self._log, parent=self,
            list_tooltip="Maya files to check and export (one FBX per file).\nDouble-click: open in File Explorer.")
        self.picker.filesChanged.connect(self._on_files_changed)

        self.splitter = QSplitter(Qt.Vertical)
        root.addWidget(self.splitter, stretch=1)
        self.splitter.addWidget(self.picker.tree)

        lower = QWidget()
        lower_layout = QVBoxLayout(lower)
        lower_layout.setContentsMargins(0, 0, 0, 0)
        lower_layout.addWidget(self.picker.add_bar)

        mid = QSplitter(Qt.Horizontal)
        mid.addWidget(self.picker.maya_list)
        mid.addWidget(self._build_rule_box())
        mid.setStretchFactor(0, 2)
        mid.setStretchFactor(1, 3)
        lower_layout.addWidget(mid)

        files_box = QGroupBox("Files")
        files_layout = QVBoxLayout(files_box)
        self.table = ExportTable()
        self.table.rangeEdited.connect(lambda: None)
        files_layout.addWidget(self.table, stretch=1)
        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Range"))
        self.cmb_range = QComboBox()
        for key, label in export_jobs.RANGE_LABELS:
            self.cmb_range.addItem(label, key)
        self.cmb_range.setToolTip("Which frame range to bake / export for each file.\n"
                                  "Timeline = the file's playback range (min / max), Animation range = its ast / aet,\n"
                                  "Custom = the same Start / End for every file. Cells stay editable after.")
        self.cmb_range.currentIndexChanged.connect(self._on_range_mode)
        range_row.addWidget(self.cmb_range)
        range_row.addWidget(QLabel("Custom Start"))
        self.sb_cstart = QSpinBox()
        self.sb_cstart.setRange(-1000000, 1000000)
        self.sb_cend = QSpinBox()
        self.sb_cend.setRange(-1000000, 1000000)
        self.sb_cend.setValue(100)
        for sb in (self.sb_cstart, self.sb_cend):
            sb.valueChanged.connect(self._on_range_mode)
        range_row.addWidget(self.sb_cstart)
        range_row.addWidget(QLabel("End"))
        range_row.addWidget(self.sb_cend)
        range_row.addStretch(1)
        files_layout.addLayout(range_row)
        lower_layout.addWidget(files_box, stretch=2)

        self.splitter.addWidget(lower)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)

        root.addWidget(self._build_naming_box())
        root.addLayout(self._build_folder_row())
        root.addLayout(self._build_options_row())

        self.lbl_resources = QLabel("Resources: ...")
        self.lbl_resources.setWordWrap(True)
        self.lbl_resources.setToolTip(
            "Hardware on this PC (read-only). Joint baking is single-threaded DG evaluation in mayapy - the GPU is not used.\n"
            "Choosing hardware / running several mayapy workers in parallel is planned for a later version.")
        root.addWidget(self.lbl_resources)

        act_row = QHBoxLayout()
        self.btn_bake_export = QPushButton("Bake & Export")
        self.btn_bake_export.setToolTip(
            "For every checked, ready file: open it in mayapy, import references and remove namespaces (option),\n"
            "find the rule's set, bake translate / rotate / scale of its members and all descendants over Start - End\n"
            "(bakeResults, one call per file), move top bones to the scene root, and export them to one FBX.\n"
            "The Maya file itself is NOT saved. A bake of 6000 frames can take minutes with no progress inside the bake step.")
        self.btn_bake_export.clicked.connect(lambda: self.on_export(bake=True))
        act_row.addWidget(self.btn_bake_export, stretch=1)
        self.btn_export_only = QPushButton("Export Only")
        self.btn_export_only.setToolTip(
            "Same as Bake & Export but without baking - the keys already in the file are exported as they are.\n"
            "Joints driven only by constraints / IK will have no animation in the FBX.")
        self.btn_export_only.clicked.connect(lambda: self.on_export(bake=False))
        act_row.addWidget(self.btn_export_only, stretch=1)
        root.addLayout(act_row)

    def _build_rule_box(self):
        box = QGroupBox("Rule")
        layout = QVBoxLayout(box)
        row = QHBoxLayout()
        self.cmb_rule = QComboBox()
        self.cmb_rule.setToolTip("Which set to look for in each Maya file. One json per rule in the Rules Folder\n"
                                 "(copy the folder to share rules between PCs).")
        self.cmb_rule.currentIndexChanged.connect(self._on_rule_changed)
        row.addWidget(self.cmb_rule, stretch=1)
        self.btn_rule_new = QPushButton("New")
        self.btn_rule_new.clicked.connect(self.on_rule_new)
        self.btn_rule_edit = QPushButton("Edit")
        self.btn_rule_edit.clicked.connect(self.on_rule_edit)
        self.btn_rule_rename = QPushButton("Rename")
        self.btn_rule_rename.clicked.connect(self.on_rule_rename)
        self.btn_rule_delete = QPushButton("Delete")
        self.btn_rule_delete.clicked.connect(self.on_rule_delete)
        self.btn_rules_folder = QPushButton("Rules Folder...")
        self.btn_rules_folder.setToolTip("Pick the folder that holds the rule json files (default ~/.jun_filemanager/export_rules).\n"
                                         "Right-click: reveal / copy the current folder.")
        self.btn_rules_folder.clicked.connect(self.on_rules_folder)
        self.btn_rules_folder.setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn_rules_folder.customContextMenuRequested.connect(
            lambda pos: path_context.show_path_menu(self.btn_rules_folder, self.btn_rules_folder.mapToGlobal(pos),
                                                   self._rules_dir, title="Rules Folder"))
        for b in (self.btn_rule_new, self.btn_rule_edit, self.btn_rule_rename, self.btn_rule_delete, self.btn_rules_folder):
            row.addWidget(b)
        layout.addLayout(row)
        self.lbl_rule = QLabel("-")
        self.lbl_rule.setWordWrap(True)
        layout.addWidget(self.lbl_rule)
        self.btn_check = QPushButton("Check Sets")
        self.btn_check.setToolTip(
            "Open every Maya file in mayapy (background) and read: whether a set matching the rule exists\n"
            "(members -> transforms), the playback range, fps and the Maya version it was saved with.\n"
            "Files without a matching set are unchecked and skipped.")
        self.btn_check.clicked.connect(self.on_check_sets)
        layout.addWidget(self.btn_check)
        layout.addStretch(1)
        return box

    def _build_naming_box(self):
        box = QGroupBox("Naming")
        layout = QVBoxLayout(box)
        row = QHBoxLayout()
        row.addWidget(QLabel("Find"))
        self.le_find = QLineEdit()
        self.le_find.setPlaceholderText("text in the file name")
        row.addWidget(self.le_find, stretch=1)
        row.addWidget(QLabel("Replace"))
        self.le_replace = QLineEdit()
        row.addWidget(self.le_replace, stretch=1)
        self.chk_case = QCheckBox("Case")
        self.chk_case.setChecked(True)
        self.chk_case.setToolTip("Case-sensitive Find.")
        row.addWidget(self.chk_case)
        layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel("Insert"))
        self.cmb_mode = QComboBox()
        for key in export_naming.MODES:
            self.cmb_mode.addItem(export_naming.MODE_LABELS[key], key)
        self.cmb_mode.setToolTip("Token : insert as a new '_' token - 0 = first token, k = after the k-th token, -1 = last.\n"
                                 "Char : insert at a character position - 0 = front, n = after n characters, -1 = end.")
        row.addWidget(self.cmb_mode)
        self.lbl_position = QLabel("position")
        row.addWidget(self.lbl_position)
        self.sb_position = QSpinBox()
        self.sb_position.setRange(-99, 99)
        self.sb_position.setToolTip("0 = front (default: the inserted text becomes the first token).")
        row.addWidget(self.sb_position)
        row.addWidget(QLabel("text"))
        self.le_text = QLineEdit("bake")
        self.le_text.setToolTip("Text to insert (empty = nothing inserted).")
        self.le_text.setMaximumWidth(120)
        row.addWidget(self.le_text)
        row.addStretch(1)
        layout.addLayout(row)
        self.lbl_preview = QLabel("Preview: -")
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setToolTip("First file -> its FBX name. Every row's Output column shows the rest.")
        layout.addWidget(self.lbl_preview)
        for w in (self.le_find, self.le_replace, self.le_text):
            w.textChanged.connect(self._on_naming_changed)
        self.chk_case.toggled.connect(self._on_naming_changed)
        self.cmb_mode.currentIndexChanged.connect(self._on_naming_changed)
        self.sb_position.valueChanged.connect(self._on_naming_changed)
        return box

    def _build_folder_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel("Export Folder"))
        self.le_folder = QLineEdit()
        self.le_folder.setPlaceholderText("empty = next to each Maya file")
        self.le_folder.setToolTip("Where the FBX files go. Empty = next to each source Maya file.")
        self.le_folder.textChanged.connect(self._on_naming_changed)
        row.addWidget(self.le_folder, stretch=1)
        self.btn_folder = QPushButton("Browse...")
        self.btn_folder.clicked.connect(self.on_browse_folder)
        row.addWidget(self.btn_folder)
        self.btn_open_folder = QPushButton("Open")
        self.btn_open_folder.setToolTip("Open the Export Folder in File Explorer.")
        self.btn_open_folder.clicked.connect(self.on_open_folder)
        row.addWidget(self.btn_open_folder)
        return row

    def _build_options_row(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(QLabel("Bake"))
        self.chk_channels = {}
        for key, label in (("translate", "Translate"), ("rotate", "Rotate"), ("scale", "Scale")):
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.toggled.connect(self.save_prefs)
            self.chk_channels[key] = cb
            row.addWidget(cb)
        row.addSpacing(12)
        self.chk_joints_only = QCheckBox("Joints Only")
        self.chk_joints_only.setChecked(True)
        self.chk_joints_only.setToolTip("Drop non-joint nodes found under joints (meshes, locators, groups and what is under them)\n"
                                        "from the bake and the FBX. Constraint nodes are always dropped.")
        self.chk_joints_only.toggled.connect(self.save_prefs)
        row.addWidget(self.chk_joints_only)
        self.chk_euler = QCheckBox("Euler Filter")
        self.chk_euler.setToolTip("Run filterCurve on the baked rotation curves (removes 360-degree flips).")
        self.chk_euler.toggled.connect(self.save_prefs)
        row.addWidget(self.chk_euler)
        row.addStretch(1)
        outer.addLayout(row)
        row = QHBoxLayout()
        self.chk_import_refs = QCheckBox("Import References & Remove Namespaces")
        self.chk_import_refs.setChecked(True)
        self.chk_import_refs.setToolTip(
            "Before baking, import every loaded reference and merge all namespaces into the root (in memory only - the file\n"
            "is not saved). Keeps bone names clean for Unreal ('root' instead of 'CHN:root') and avoids thousands of\n"
            "reference edits when baking referenced joints.")
        self.chk_import_refs.toggled.connect(self.save_prefs)
        row.addWidget(self.chk_import_refs)
        row.addStretch(1)
        outer.addLayout(row)
        return outer

    # ==================================================================
    # prefs
    # ==================================================================

    def _pref_data(self):
        if not self._prefs:
            return {}
        try:
            return self._prefs["load"]() or {}
        except Exception:  # noqa: BLE001
            return {}

    def load_prefs(self):
        data = self._pref_data()
        self._loading = True
        try:
            self._rules_dir = set_rules.rules_dir(data.get("export_rules_dir", ""))
            self.le_folder.setText(data.get("export_fbx_dir", "") or "")
            spec = export_naming.NamingSpec.from_dict(data.get("export_naming") or {})
            self.le_find.setText(spec.find)
            self.le_replace.setText(spec.replace)
            self.chk_case.setChecked(spec.case_sensitive)
            self.cmb_mode.setCurrentIndex(max(0, list(export_naming.MODES).index(spec.mode)))
            self.sb_position.setValue(spec.position)
            self.le_text.setText(spec.text)
            mode = data.get("export_range_mode", export_jobs.RANGE_TIMELINE)
            keys = [k for k, _l in export_jobs.RANGE_LABELS]
            self.cmb_range.setCurrentIndex(keys.index(mode) if mode in keys else 0)
            custom = data.get("export_custom_range") or [0, 100]
            self.sb_cstart.setValue(int(custom[0]))
            self.sb_cend.setValue(int(custom[1]))
            channels = data.get("export_bake_channels") or list(export_jobs.CHANNELS)
            for key, cb in self.chk_channels.items():
                cb.setChecked(key in channels)
            self.chk_joints_only.setChecked(bool(data.get("export_joints_only", True)))
            self.chk_euler.setChecked(bool(data.get("export_euler_filter", False)))
            self.chk_import_refs.setChecked(bool(data.get("export_import_references", True)))
            self._reload_rules(select=data.get("export_rule", "Bake"))
        finally:
            self._loading = False
        self._refresh_output()

    def save_prefs(self, *_args):
        if self._loading or not self._prefs:
            return
        data = self._pref_data()
        data["export_rules_dir"] = self._rules_dir if os.path.normcase(self._rules_dir) != os.path.normcase(set_rules.DEFAULT_RULES_DIR) else ""
        data["export_rule"] = self.cmb_rule.currentText()
        data["export_fbx_dir"] = self.le_folder.text().strip()
        data["export_naming"] = self.naming_spec().to_dict()
        data["export_range_mode"] = self.cmb_range.currentData()
        data["export_custom_range"] = [self.sb_cstart.value(), self.sb_cend.value()]
        data["export_bake_channels"] = self.channels()
        data["export_joints_only"] = self.chk_joints_only.isChecked()
        data["export_euler_filter"] = self.chk_euler.isChecked()
        data["export_import_references"] = self.chk_import_refs.isChecked()
        try:
            self._prefs["save"](data)
        except Exception as exc:  # noqa: BLE001
            self._log("[WARN] Could not save Export settings : {0}".format(exc))

    # ==================================================================
    # rules
    # ==================================================================

    def _reload_rules(self, select=None):
        select = select or self.cmb_rule.currentText()
        self._rules, errors = set_rules.load_rules(self._rules_dir)
        for path, msg in errors:
            self._log("[WARN] Rule file skipped : {0} ({1})".format(os.path.basename(path), msg))
        self.cmb_rule.blockSignals(True)
        self.cmb_rule.clear()
        for rule in self._rules:
            self.cmb_rule.addItem(rule.name)
        names = [r.name for r in self._rules]
        self.cmb_rule.setCurrentIndex(names.index(select) if select in names else 0)
        self.cmb_rule.blockSignals(False)
        self._on_rule_changed()

    def current_rule(self):
        return set_rules.find_rule(self._rules, self.cmb_rule.currentText())

    def _on_rule_changed(self, *_args):
        rule = self.current_rule()
        self.lbl_rule.setText(rule.summary() + ("  -  " + rule.description if rule.description else "") if rule else "-")
        self.lbl_rule.setToolTip(rule.path if rule else "")
        self.table.reset_probe()
        self.save_prefs()

    def on_rule_new(self, *_args):
        dlg = SetRuleDialog(parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        v = dlg.values()
        rule = set_rules.SetRule(v["name"], v["set_name"], v["match"], v["ignore_namespace"], v["description"])
        if os.path.exists(set_rules.rule_path(rule.name, self._rules_dir)):
            self._log("[WARN] A rule named {0!r} already exists.".format(rule.name))
            return
        set_rules.save_rule(rule, self._rules_dir)
        self._log("[OK] Rule saved : {0}".format(rule.path))
        self._reload_rules(select=rule.name)

    def on_rule_edit(self, *_args):
        rule = self.current_rule()
        if not rule:
            return
        dlg = SetRuleDialog(rule, parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        v = dlg.values()
        rule.set_name, rule.match, rule.ignore_namespace, rule.description = v["set_name"], v["match"], v["ignore_namespace"], v["description"]
        try:
            if v["name"] != rule.name:
                set_rules.rename_rule(rule, v["name"], self._rules_dir)
            else:
                set_rules.save_rule(rule, self._rules_dir)
        except (ValueError, OSError) as exc:
            self._log("[WARN] Could not save the rule : {0}".format(exc))
            return
        self._log("[OK] Rule saved : {0}".format(rule.path))
        self._reload_rules(select=rule.name)

    def on_rule_rename(self, *_args):
        rule = self.current_rule()
        if not rule:
            return
        name, ok = QInputDialog.getText(self, "Rename Rule", "New name:", text=rule.name)
        if not ok or not name.strip() or name.strip() == rule.name:
            return
        try:
            set_rules.rename_rule(rule, name.strip(), self._rules_dir)
        except (ValueError, OSError) as exc:
            self._log("[WARN] Could not rename the rule : {0}".format(exc))
            return
        self._log("[OK] Rule renamed -> {0}".format(rule.path))
        self._reload_rules(select=rule.name)

    def on_rule_delete(self, *_args):
        rule = self.current_rule()
        if not rule:
            return
        answer = QMessageBox.question(self, "Delete Rule", "Delete rule {0!r} ?\n\n{1}".format(rule.name, rule.path),
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            set_rules.delete_rule(rule, self._rules_dir)
        except (ValueError, OSError) as exc:
            self._log("[WARN] Could not delete the rule : {0}".format(exc))
            return
        self._log("Rule deleted : {0}".format(rule.name))
        self._reload_rules()

    def on_rules_folder(self, *_args):
        folder = QFileDialog.getExistingDirectory(self, "Rules Folder", self._rules_dir)
        if not folder:
            return
        self._rules_dir = set_rules.rules_dir(folder)
        self._log("Rules folder : {0}".format(self._rules_dir))
        self._reload_rules()

    # ==================================================================
    # files · naming · range
    # ==================================================================

    def _on_files_changed(self, paths):
        self.table.set_files(paths)
        self._refresh_output()

    def naming_spec(self):
        return export_naming.NamingSpec(self.le_find.text(), self.le_replace.text(), self.chk_case.isChecked(),
                                        self.cmb_mode.currentData(), self.sb_position.value(), self.le_text.text())

    def _on_naming_changed(self, *_args):
        self.lbl_position.setText("after token" if self.cmb_mode.currentData() == export_naming.MODE_TOKEN else "position")
        self._refresh_output()
        self.save_prefs()

    def _refresh_output(self):
        paths = self.table.paths()
        rows = export_naming.preview(paths, self.naming_spec(), self.le_folder.text().strip())
        self.table.clear_results()
        self.table.set_output(rows)
        if rows:
            self.lbl_preview.setText("Preview: {0}  ->  {1}{2}".format(
                os.path.basename(rows[0].file), rows[0].out_name,
                "   ({0})".format("; ".join(rows[0].notes)) if rows[0].notes else ""))
        else:
            self.lbl_preview.setText("Preview: -")

    def _on_range_mode(self, *_args):
        custom = self.cmb_range.currentData() == export_jobs.RANGE_CUSTOM
        self.sb_cstart.setEnabled(custom)
        self.sb_cend.setEnabled(custom)
        self.table.fill_range(self.cmb_range.currentData(), (self.sb_cstart.value(), self.sb_cend.value()))
        self.save_prefs()

    def channels(self):
        return [k for k in export_jobs.CHANNELS if self.chk_channels[k].isChecked()]

    def on_browse_folder(self, *_args):
        folder = QFileDialog.getExistingDirectory(self, "Export Folder", self.le_folder.text().strip())
        if folder:
            self.le_folder.setText(os.path.normpath(folder))

    def on_open_folder(self, *_args):
        folder = self.le_folder.text().strip()
        if not folder:
            self._log("Export Folder is empty - FBX files go next to each Maya file.")
            return
        path_context.reveal_path(self, folder, title="Export Folder")

    # ==================================================================
    # mayapy
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
                                "Checking sets, baking and exporting FBX need Maya's Python.\n"
                                "Set the path in the mayapy box (Browse... or Detect).")
        return mayapy

    # ==================================================================
    # Check Sets
    # ==================================================================

    def on_check_sets(self, *_args):
        paths = [p for p in self.table.paths() if os.path.isfile(p)]
        if not paths:
            self._log("[WARN] Add Maya files first (Add Checked / Browse...).")
            return
        rule = self.current_rule()
        if not rule:
            self._log("[WARN] Pick a rule first.")
            return
        mayapy = self._require_mayapy()
        if not mayapy:
            return
        try:
            job = export_jobs.probe_job(paths, rule.to_job())
        except ValueError as exc:
            self._log("[WARN] {0}".format(exc))
            return
        self._log("Check Sets : {0} file(s), rule {1!r} ({2}) - opening each file in mayapy...".format(
            len(paths), rule.name, rule.summary()))
        outcome = mayapy_process.run_job(self, mayapy, job, title="File Manager - Check Sets",
                                         message="Starting mayapy...", log=self._log)
        if outcome.error or outcome.result is None:
            self._log("[WARN] Check Sets failed : {0}".format(outcome.error or "no result"))
            return
        self.table.apply_probe(outcome.result, self.cmb_range.currentData(), (self.sb_cstart.value(), self.sb_cend.value()))
        self._refresh_output()
        files = outcome.result.get("files", [])
        with_set = sum(1 for f in files if f.get("ok") and f.get("sets"))
        without = sum(1 for f in files if f.get("ok") and not f.get("sets"))
        failed = sum(1 for f in files if not f.get("ok"))
        self._log("[OK] Check Sets : {0} file(s) - {1} with a matching set, {2} without{3}.".format(
            len(files), with_set, without, ", {0} could not be read".format(failed) if failed else ""))

    # ==================================================================
    # Bake & Export / Export Only
    # ==================================================================

    def on_export(self, bake=True):
        label = "Bake & Export" if bake else "Export Only"
        rule = self.current_rule()
        if not rule:
            self._log("[WARN] Pick a rule first.")
            return
        unprobed = self.table.unprobed_checked()
        if unprobed:
            self._log("[WARN] Press Check Sets first - {0} checked file(s) have not been checked ({1}).".format(
                len(unprobed), ", ".join(os.path.basename(p) for p in unprobed[:3])))
            QMessageBox.information(self, label, "Press Check Sets first.\n\n{0} checked file(s) have not been checked yet, "
                                    "so their frame range and set are unknown.".format(len(unprobed)))
            return
        rows = self.table.checked_rows()
        if not rows:
            self._log("[WARN] No file is ready - check files that have a matching set and a valid output name.")
            return
        mayapy = self._require_mayapy()
        if not mayapy:
            return
        folder = self.le_folder.text().strip()
        report = export_jobs.report_path(folder or os.path.dirname(rows[0]["file"]))
        try:
            job = export_jobs.export_job(rule.to_job(), rows, bake=bake, channels=self.channels(),
                                         joints_only=self.chk_joints_only.isChecked(), euler_filter=self.chk_euler.isChecked(),
                                         import_references=self.chk_import_refs.isChecked(), report_path=report)
        except ValueError as exc:
            self._log("[WARN] {0}".format(exc))
            QMessageBox.warning(self, label, str(exc))
            return

        # 이미 있는 출력 파일 - 경고 팝업 Overwrite / Cancel (사용자 결정 Q5)
        existing = self.table.existing_outputs()
        if existing:
            if not self._confirm_overwrite(existing, label):
                self._log("{0} cancelled - existing FBX file(s) kept.".format(label))
                return

        lines = ["{0}  {1} - {2}  ->  {3}".format(os.path.basename(i["file"]), i["start"], i["end"], os.path.basename(i["out_fbx"]))
                 for i in job["items"]]
        if len(lines) > 12:
            lines = lines[:12] + ["... and {0} more".format(len(job["items"]) - 12)]
        answer = QMessageBox.question(
            self, label,
            "{0} Maya file(s) will be opened in mayapy and exported to FBX (the Maya files are not saved):\n\n{1}\n\n"
            "Export Folder : {2}\nBake : {3}\nJoints Only : {4}\nImport References & Remove Namespaces : {5}\n\n"
            "A bake of thousands of frames takes minutes per file; the progress bar does not move inside a bake.\n\nContinue?".format(
                len(job["items"]), "\n".join(lines), folder or "(next to each Maya file)",
                ("ON ({0})".format(", ".join(job["channels"])) if bake else "OFF"),
                "ON" if job["joints_only"] else "OFF", "ON" if job["import_references"] else "OFF"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            self._log("{0} cancelled.".format(label))
            return

        self._log("{0} : {1} file(s)...".format(label, len(job["items"])))
        outcome = mayapy_process.run_job(self, mayapy, job, title="File Manager - {0}".format(label),
                                         message="Starting mayapy...", log=self._log, cancel_grace_sec=EXPORT_CANCEL_GRACE_SEC)
        result = outcome.result
        if outcome.error and result is None:
            self._log("[WARN] {0} failed : {1}".format(label, outcome.error))
            return
        if result:
            self.table.apply_results(result)
            tag = "[OK]" if not result.get("failed") and not result.get("cancelled") else "[WARN]"
            self._log("{0} {1} done - {2}.".format(tag, label, export_jobs.summarize(result)))
            if job.get("report") and os.path.isfile(job["report"]):
                self._log("Report : {0}".format(job["report"]))

    def _confirm_overwrite(self, existing, label):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(label)
        box.setText("{0} FBX file(s) already exist and will be overwritten:".format(len(existing)))
        shown = existing[:15] + (["... and {0} more".format(len(existing) - 15)] if len(existing) > 15 else [])
        box.setInformativeText("\n".join(shown))
        btn_over = box.addButton("Overwrite", QMessageBox.AcceptRole)
        btn_cancel = box.addButton("Cancel", QMessageBox.RejectRole)
        box.setDefaultButton(btn_cancel)
        box.exec_()
        return box.clickedButton() is btn_over

    # ==================================================================
    # resources (v1 read-only)
    # ==================================================================

    def _start_hw_probe(self):
        try:
            self._hw_proc = QProcess(self)
            self._hw_proc.setProcessChannelMode(QProcess.MergedChannels)
            self._hw_proc.finished.connect(self._on_hw_done)
            cmd = hw_info.command()
            self._hw_proc.start(cmd[0], cmd[1:])
        except Exception:  # noqa: BLE001
            self.lbl_resources.setText("Resources: (unavailable)")

    def _on_hw_done(self, *_args):
        try:
            text = bytes(self._hw_proc.readAllStandardOutput().data()).decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            text = ""
        summary = hw_info.parse(text)
        self.lbl_resources.setText("Resources: {0}".format(summary) if summary else "Resources: (unavailable)")

    # ==================================================================
    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
