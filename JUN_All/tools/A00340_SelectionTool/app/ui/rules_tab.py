# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00340_SelectionTool - "Rules" tab (Qt, in-Maya)  (v01.11)
#
# 규칙(rule) = 어느 씬에서든 다시 선택할 오브젝트 이름 목록 하나. **규칙 하나 = json 파일 하나**
# (data/rules/<name>.json) 라 폴더를 복사하면 다른 PC 에서도 그대로 쓴다.
#
#   ┌ Rules ─────────────────────────┐ ┌ Objects ───────────────┐
#   │ Name        │ Objects │ File   │ │ jnt_01                 │
#   │ rule_01     │ 3       │ ...    │ │ jnt_02                 │
#   │ rule_02     │ 12      │ ...    │ │ jnt_03   (red=missing) │
#   └────────────────────────────────┘ └────────────────────────┘
#   Description [                                           ]
#   [New Rule from Selection] [Update Objects] [Rename] [Delete]
#   [          Select          ]  [ ] Add to current selection
#   [Reload] [Show Folder]
#
#   - New Rule from Selection : 현재 마야 선택을 이름으로 묻고 규칙 json 으로 저장.
#   - Select (또는 규칙 더블클릭) : 고른 규칙의 오브젝트를 씬에서 선택. 여러 규칙을 고르면 합집합.
#     없는 오브젝트는 건너뛰고, 동명 노드는 전부 선택하되 경고를 찍는다 (maya_select.select_names).
#   - Rename 은 json 안의 name 과 파일 이름을 함께 바꾼다. Delete 는 한 번 확인한 뒤 파일을 지운다.
#   - Description 은 포커스를 잃을 때 저장된다 (고른 규칙이 하나일 때만 편집 가능).
#   - 폴더를 밖에서 고쳤으면 Reload. 이 탭은 열릴 때마다 폴더를 다시 읽는다 (showEvent).
# 모든 UI 문자열/로그는 영어.

import os

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QInputDialog,
    QMessageBox,
    QMenu,
    QBrush,
    QColor,
    Qt,
)
from Framework.core import file_opener

from ..core import select_rules as rules_mod
from ..core import maya_select


TITLE = "Selection Tool"

MISSING_HEX = "#e05050"      # 씬에 없는 오브젝트 행 글자색 (공용 TSL 의 (Null) 빨강과 같은 뜻)
AMBIGUOUS_HEX = "#e0a040"    # 같은 이름이 둘 이상인 오브젝트 행 글자색


class RulesTab(QWidget):
    """규칙 목록 + 고른 규칙의 오브젝트 + 편집 버튼. 규칙은 data/rules/*.json."""

    COL_NAME, COL_COUNT, COL_FILE = 0, 1, 2

    def __init__(self, log_callback=None, rules_dir=None, parent=None):
        super().__init__(parent)
        self._log = log_callback or (lambda _msg: None)
        # 테스트가 임시 폴더를 넘길 수 있게 둔다. None 이면 툴의 data/rules.
        self._rules_dir = rules_dir or rules_mod.RULES_DIR
        self._rules = []
        self._build_ui()
        self.reload()

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        splitter = QSplitter(Qt.Horizontal)

        # 왼쪽 : 규칙 표
        rules_box = QGroupBox("Rules")
        rules_lay = QVBoxLayout(rules_box)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name", "Objects", "File"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        header = self.tree.header()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_COUNT, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_FILE, QHeaderView.ResizeToContents)
        self.tree.setToolTip(
            "One rule = one json file in the rules folder.\n"
            "Click a rule to see its objects, double-click to select them in Maya.\n"
            "Ctrl / Shift click several rules and 'Select' selects all of them together.")
        self.tree.itemSelectionChanged.connect(self._on_rule_selection_changed)
        self.tree.itemDoubleClicked.connect(lambda *_: self.on_select())
        self.tree.customContextMenuRequested.connect(self._show_rule_menu)
        rules_lay.addWidget(self.tree)
        splitter.addWidget(rules_box)

        # 오른쪽 : 고른 규칙의 오브젝트
        objs_box = QGroupBox("Objects")
        objs_lay = QVBoxLayout(objs_box)
        self.obj_list = QListWidget()
        self.obj_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.obj_list.setToolTip(
            "Objects of the highlighted rule(s), in saved order.\n"
            "Red = not in this scene (skipped on Select).\n"
            "Orange = more than one node has this name (all of them are selected, with a warning).")
        objs_lay.addWidget(self.obj_list)
        self.lbl_obj_summary = QLabel("")
        objs_lay.addWidget(self.lbl_obj_summary)
        splitter.addWidget(objs_box)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        # Description
        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("Description"))
        self.le_desc = QLineEdit()
        self.le_desc.setPlaceholderText("optional note, saved into the rule json")
        self.le_desc.setToolTip("Note for the highlighted rule. Saved when the field loses focus.")
        self.le_desc.editingFinished.connect(self._on_desc_edited)
        desc_row.addWidget(self.le_desc, 1)
        root.addLayout(desc_row)

        # 편집 버튼 행
        edit_row = QHBoxLayout()
        self.btn_new = QPushButton("New Rule from Selection")
        self.btn_new.setToolTip(
            "Save the current Maya selection as a new rule.\n"
            "Asks for the rule name; the json file is named after it.")
        self.btn_new.clicked.connect(self.on_new_rule)
        edit_row.addWidget(self.btn_new)
        self.btn_update = QPushButton("Update Objects")
        self.btn_update.setToolTip(
            "Replace the highlighted rule's objects with the current Maya selection.")
        self.btn_update.clicked.connect(lambda: self.on_update_objects(append=False))
        edit_row.addWidget(self.btn_update)
        self.btn_rename = QPushButton("Rename")
        self.btn_rename.setToolTip("Rename the highlighted rule - the json file is renamed too.")
        self.btn_rename.clicked.connect(self.on_rename)
        edit_row.addWidget(self.btn_rename)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setToolTip(
            "Delete the highlighted rule(s) - their json files are removed after one confirmation.\n"
            "This cannot be undone.")
        self.btn_delete.clicked.connect(self.on_delete)
        edit_row.addWidget(self.btn_delete)
        root.addLayout(edit_row)

        # Select 행
        sel_row = QHBoxLayout()
        self.btn_select = QPushButton("Select")
        self.btn_select.setMinimumHeight(32)
        self.btn_select.setToolTip(
            "Select the objects of the highlighted rule(s) in Maya.\n"
            "Objects missing from this scene are skipped and listed in the Log.")
        self.btn_select.clicked.connect(self.on_select)
        sel_row.addWidget(self.btn_select, 1)
        self.chk_add = QCheckBox("Add to current selection")
        self.chk_add.setToolTip("Keep what is selected now and add the rule's objects to it.")
        sel_row.addWidget(self.chk_add)
        root.addLayout(sel_row)

        # 폴더 행
        folder_row = QHBoxLayout()
        self.lbl_folder = QLabel()
        self.lbl_folder.setWordWrap(True)
        self.lbl_folder.setTextInteractionFlags(Qt.TextSelectableByMouse)
        folder_row.addWidget(self.lbl_folder, 1)
        btn_reload = QPushButton("Reload")
        btn_reload.setToolTip("Read the rules folder again (after copying json files into it).")
        btn_reload.clicked.connect(self.reload)
        folder_row.addWidget(btn_reload)
        btn_folder = QPushButton("Show Folder")
        btn_folder.setToolTip(
            "Open the rules folder in Explorer - copy json files from here to share rules\n"
            "with another PC, or drop files in and press Reload.")
        btn_folder.clicked.connect(self.on_show_folder)
        folder_row.addWidget(btn_folder)
        root.addLayout(folder_row)

    def showEvent(self, event):
        super().showEvent(event)
        # 탭을 다시 열 때마다 폴더를 다시 읽는다 - 밖에서 json 을 넣었을 수 있다.
        self.reload()

    # ============================================================== data

    def rules_dir(self):
        return self._rules_dir

    def reload(self, *_args):
        """규칙 폴더를 다시 읽어 표를 채운다. 고르던 규칙은 이름으로 유지."""
        keep = set(r.name for r in self.selected_rules())
        self._rules, errors = rules_mod.load_rules(self._rules_dir)

        self.tree.blockSignals(True)
        self.tree.clear()
        for rule in self._rules:
            item = QTreeWidgetItem([rule.name, str(len(rule.objects)), rule.file_name])
            item.setTextAlignment(self.COL_COUNT, Qt.AlignRight | Qt.AlignVCenter)
            tip = rule.path
            if rule.description:
                tip = rule.description + "\n" + tip
            for col in range(3):
                item.setToolTip(col, tip)
            item.setData(0, Qt.UserRole, rule.name)
            self.tree.addTopLevelItem(item)
            if rule.name in keep:
                item.setSelected(True)
        self.tree.blockSignals(False)

        self.lbl_folder.setText("{0} rule(s) in {1}".format(len(self._rules), self._rules_dir))
        for file_name, message in errors:
            self._log("[WARN] Rule '{0}' not loaded : {1}".format(file_name, message))
        self._on_rule_selection_changed()

    def selected_rules(self):
        """표에서 고른 규칙들 (표 순서)."""
        picked = set()
        for item in self.tree.selectedItems():
            picked.add(item.data(0, Qt.UserRole))
        return [r for r in self._rules if r.name in picked]

    def select_rule_by_name(self, name):
        """표에서 이름으로 규칙 하나를 고른다 (새로 만든 뒤 등)."""
        self.tree.clearSelection()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == name:
                item.setSelected(True)
                self.tree.setCurrentItem(item)
                return True
        return False

    def _single_rule(self, action):
        """정확히 하나를 골랐을 때 그 규칙, 아니면 안내하고 None."""
        rules = self.selected_rules()
        if len(rules) != 1:
            QMessageBox.information(
                self, TITLE, "Highlight exactly one rule to {0}.".format(action))
            return None
        return rules[0]

    # ============================================================== right pane

    def _on_rule_selection_changed(self, *_args):
        rules = self.selected_rules()
        objects = rules_mod.union_objects(rules)
        self._fill_objects(objects)

        single = len(rules) == 1
        self.le_desc.blockSignals(True)
        self.le_desc.setText(rules[0].description if single else "")
        self.le_desc.blockSignals(False)
        self.le_desc.setEnabled(single)
        self.btn_update.setEnabled(single)
        self.btn_rename.setEnabled(single)
        self.btn_delete.setEnabled(bool(rules))
        self.btn_select.setEnabled(bool(rules))

    def _fill_objects(self, objects):
        """오른쪽 목록. 없는 것은 빨강, 동명은 주황으로 칠한다 (씬 상태는 지금 기준)."""
        self.obj_list.clear()
        status = maya_select.name_status(objects)
        missing = ambiguous = 0
        for name in objects:
            item = QListWidgetItem(name)
            state = status.get(name, "ok")
            if state == "missing":
                item.setForeground(QBrush(QColor(MISSING_HEX)))
                item.setToolTip("Not in this scene")
                missing += 1
            elif state == "ambiguous":
                item.setForeground(QBrush(QColor(AMBIGUOUS_HEX)))
                item.setToolTip("More than one node has this name")
                ambiguous += 1
            self.obj_list.addItem(item)
        parts = ["{0} object(s)".format(len(objects))]
        if missing:
            parts.append("{0} missing".format(missing))
        if ambiguous:
            parts.append("{0} ambiguous".format(ambiguous))
        self.lbl_obj_summary.setText(", ".join(parts) if objects else "")

    # ============================================================== actions

    def on_new_rule(self, *_args):
        objects = maya_select.capture_selection()
        if not objects:
            QMessageBox.information(self, TITLE, "Select objects in Maya first.")
            return
        name = self._ask_name("New Rule", "Rule name ({0} object(s)):".format(len(objects)), "")
        if name is None:
            return
        try:
            rule = rules_mod.save_rule(name, objects, rules_dir=self._rules_dir)
        except ValueError as e:
            QMessageBox.warning(self, TITLE, "Cannot create rule: {0}".format(e))
            return
        self.reload()
        self.select_rule_by_name(rule.name)
        self._log("Rule '{0}' saved with {1} object(s) -> {2}".format(
            rule.name, len(rule.objects), rule.file_name))

    def on_update_objects(self, append=False):
        rule = self._single_rule("update")
        if rule is None:
            return
        objects = maya_select.capture_selection()
        if not objects:
            QMessageBox.information(self, TITLE, "Select objects in Maya first.")
            return
        new_objects = (rule.objects + objects) if append else objects
        try:
            rules_mod.update_rule(rule, objects=new_objects)
        except ValueError as e:
            QMessageBox.warning(self, TITLE, "Cannot update rule: {0}".format(e))
            return
        self.reload()
        self._log("Rule '{0}' now has {1} object(s){2}.".format(
            rule.name, len(rule.objects), " (appended)" if append else ""))

    def on_rename(self, *_args):
        rule = self._single_rule("rename")
        if rule is None:
            return
        name = self._ask_name("Rename Rule", "New name:", rule.name)
        if name is None or name == rule.name:
            return
        old_file = rule.file_name
        try:
            rules_mod.rename_rule(rule, name, rules_dir=self._rules_dir)
        except (ValueError, OSError) as e:
            QMessageBox.warning(self, TITLE, "Cannot rename rule: {0}".format(e))
            return
        self.reload()
        self.select_rule_by_name(rule.name)
        self._log("Rule renamed -> '{0}' ({1} -> {2})".format(rule.name, old_file, rule.file_name))

    def on_delete(self, confirm=True):
        rules = self.selected_rules()
        if not rules:
            QMessageBox.information(self, TITLE, "Highlight the rule(s) to delete.")
            return
        if confirm:
            names = "\n".join("  " + r.name for r in rules[:12])
            if len(rules) > 12:
                names += "\n  ... (+{0})".format(len(rules) - 12)
            answer = QMessageBox.question(
                self, TITLE,
                "Delete {0} rule(s)? The json file(s) will be removed.\n"
                "This cannot be undone.\n\n{1}".format(len(rules), names),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return
        deleted, failed = rules_mod.delete_rules(rules, rules_dir=self._rules_dir)
        self.reload()
        for path in deleted:
            self._log("Rule deleted : {0}".format(os.path.basename(path)))
        for path, reason in failed:
            self._log("[WARN] could not delete {0} : {1}".format(path, reason))

    def on_select(self, *_args):
        rules = self.selected_rules()
        if not rules:
            QMessageBox.information(self, TITLE, "Highlight a rule first.")
            return
        objects = rules_mod.union_objects(rules)
        add = self.chk_add.isChecked()
        result = maya_select.select_names(objects, add=add)

        label = rules[0].name if len(rules) == 1 else "{0} rules".format(len(rules))
        msg = "Selected {0} object(s) from '{1}'".format(len(result["found"]), label)
        if add:
            msg += " (added)"
        self._log(msg)
        missing = result["missing"]
        if missing:
            shown = ", ".join(missing[:8]) + (", ..." if len(missing) > 8 else "")
            self._log("[WARN] {0} missing in this scene: {1}".format(len(missing), shown))
        for name, matches in result["ambiguous"]:
            self._log("[WARN] '{0}' matches {1} nodes - all selected: {2}".format(
                name, len(matches), ", ".join(matches[:4]) + (", ..." if len(matches) > 4 else "")))
        # 씬이 바뀌었을 수 있으니 오른쪽 색을 다시 칠한다.
        self._fill_objects(objects)

    def on_show_folder(self, *_args):
        folder = self._rules_dir
        if not os.path.isdir(folder):
            try:
                os.makedirs(folder)
            except OSError:
                pass
        try:
            file_opener.open_path(folder)
            self._log("Show Folder: {0}".format(folder))
        except (OSError, ValueError) as e:
            self._log("[ERR] Show Folder: {0}".format(e))

    def _on_desc_edited(self, *_args):
        rules = self.selected_rules()
        if len(rules) != 1:
            return
        rule = rules[0]
        text = self.le_desc.text().strip()
        if text == rule.description:
            return
        try:
            rules_mod.update_rule(rule, description=text)
        except (ValueError, OSError) as e:
            self._log("[WARN] could not save description : {0}".format(e))
            return
        self.reload()
        self._log("Rule '{0}' description saved.".format(rule.name))

    # ============================================================== menus / helpers

    def _show_rule_menu(self, pos):
        rules = self.selected_rules()
        if not rules:
            return
        menu = QMenu(self)
        act_select = menu.addAction("Select")
        act_select.triggered.connect(self.on_select)
        menu.addSeparator()
        act_update = menu.addAction("Update Objects (replace)")
        act_update.triggered.connect(lambda: self.on_update_objects(append=False))
        act_append = menu.addAction("Add Objects (append)")
        act_append.triggered.connect(lambda: self.on_update_objects(append=True))
        act_rename = menu.addAction("Rename...")
        act_rename.triggered.connect(self.on_rename)
        for act in (act_update, act_append, act_rename):
            act.setEnabled(len(rules) == 1)
        menu.addSeparator()
        act_show = menu.addAction("Show File")
        act_show.setEnabled(len(rules) == 1)
        act_show.triggered.connect(lambda: self._show_file(rules[0]))
        menu.addSeparator()
        act_delete = menu.addAction("Delete...")
        act_delete.triggered.connect(self.on_delete)
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def _show_file(self, rule):
        try:
            file_opener.open_path(rule.path)
            self._log("Show File: {0}".format(rule.path))
        except (OSError, ValueError) as e:
            self._log("[ERR] Show File: {0}".format(e))

    def _ask_name(self, title, label, default):
        """이름 입력. 취소면 None, 빈 이름은 다시 묻는다."""
        while True:
            text, ok = QInputDialog.getText(self, title, label, QLineEdit.Normal, default)
            if not ok:
                return None
            text = text.strip()
            if text:
                return text
            QMessageBox.warning(self, TITLE, "Rule name is required.")
