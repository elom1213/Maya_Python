# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-28
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
#   - v01.17 : 로컬(data/rules) + 공유(shared/rules, git 추적 · PC 별 경로 가능) 두 폴더를 함께 보인다.
#     Scope 열 Local / Shared, 행은 파일 경로로 가른다(같은 이름이 양쪽에 있어도 두 줄). Rename · Delete ·
#     Update 는 규칙이 있는 폴더 안에서, 공유 규칙은 한 번 더 묻는다. Share(로컬 -> 공유 이동) ·
#     Copy to Local(공유 -> 로컬 복사). New Rule 은 로컬에.
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
    QSizePolicy,
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

from ..core import prefs as prefs_mod
from ..core import select_rules as rules_mod
from ..core import maya_select


TITLE = "Selection Tool"

MISSING_HEX = "#e05050"      # 씬에 없는 오브젝트 행 글자색 (공용 TSL 의 (Null) 빨강과 같은 뜻)
AMBIGUOUS_HEX = "#e0a040"    # 같은 이름이 둘 이상인 오브젝트 행 글자색


def _short_dir(path):
    """'.../data/rules' - 경로의 끝 두 폴더만 (상태 줄이 창 폭을 잡아 늘리지 않게)."""
    parts = [p for p in os.path.normpath(path).replace("\\", "/").split("/") if p]
    return ".../" + "/".join(parts[-2:]) if len(parts) > 2 else path


class RulesTab(QWidget):
    """규칙 목록 + 고른 규칙의 오브젝트 + 편집 버튼. 규칙은 data/rules/*.json (로컬) + 공유 rules/*.json (v01.17)."""

    COL_NAME, COL_SCOPE, COL_COUNT, COL_FILE = 0, 1, 2, 3

    def __init__(self, log_callback=None, rules_dir=None, shared_dir=None, parent=None):
        super().__init__(parent)
        self._log = log_callback or (lambda _msg: None)
        # 테스트가 임시 폴더를 넘길 수 있게 둔다. None 이면 툴의 data/rules.
        self._rules_dir = rules_dir or prefs_mod.rules_dir(prefs_mod.SCOPE_LOCAL)
        # 공유 폴더 (v01.17) : 직접 주면 그것. rules_dir 만 준 경우(시험)는 공유를 안 본다 - 실제 공유 폴더를
        # 건드리지 않게. 둘 다 None 이면 매번 prefs 에서 읽는다(View > Shared Folder... 로 바뀔 수 있다).
        self._shared_dir_fixed = shared_dir
        self._shared_from_prefs = rules_dir is None and shared_dir is None
        self._rules = []
        self._build_ui()
        self.reload()

    def shared_dir(self):
        """지금 보는 공유 규칙 폴더 (없으면 None)."""
        if self._shared_dir_fixed:
            return self._shared_dir_fixed
        if self._shared_from_prefs:
            return prefs_mod.rules_dir(prefs_mod.SCOPE_SHARED)
        return None

    def _is_shared_rule(self, rule):
        return getattr(rule, "scope", prefs_mod.SCOPE_LOCAL) == prefs_mod.SCOPE_SHARED

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
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Name", "Scope", "Objects", "File"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        header = self.tree.header()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_SCOPE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_COUNT, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_FILE, QHeaderView.ResizeToContents)
        self.tree.setToolTip(
            "One rule = one json file in the rules folder.\n"
            "Scope 'Local' = this PC (data/rules), 'Shared' = the shared folder (tracked by git).\n"
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

        # 로컬 <-> 공유 (v01.17)
        share_row = QHBoxLayout()
        self.btn_share = QPushButton("Share")
        self.btn_share.setToolTip(
            "Move the highlighted LOCAL rule(s) into the shared folder,\n"
            "so they can be committed / pushed (or read from your shared path on other PCs).")
        self.btn_share.clicked.connect(self.on_share)
        self.btn_copy_local = QPushButton("Copy to Local")
        self.btn_copy_local.setToolTip(
            "Copy the highlighted SHARED rule(s) into this PC's local rules (data/rules).")
        self.btn_copy_local.clicked.connect(self.on_copy_to_local)
        share_row.addStretch(1)
        share_row.addWidget(self.btn_share)
        share_row.addWidget(self.btn_copy_local)
        root.addLayout(share_row)

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
        # v01.12 : 폴더 **전체 경로**를 여기 쓰면 공백 없는 한 단어라 줄이 안 바뀌고, 그 길이가 창의 최소
        # 폭이 됐다(탭 위젯은 안 보이는 탭까지 가장 넓은 페이지에 맞춘다 - Buttons 탭에서도 창이 안 줄었다).
        # 글자는 짧게(끝 두 폴더), 전체 경로는 툴팁 · Show Folder 로. 가로 크기 요구도 무시하게 둔다.
        self.lbl_folder.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
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
        """로컬 + 공유 규칙 폴더를 다시 읽어 표를 채운다. 고르던 규칙은 파일 경로로 유지.

        규칙마다 `scope` 속성("local" / "shared")을 붙인다. 같은 이름이 양쪽에 있어도 두 줄이다.
        """
        keep = set(os.path.normcase(r.path) for r in self.selected_rules())
        local, errors = rules_mod.load_rules(self._rules_dir)
        for rule in local:
            rule.scope = prefs_mod.SCOPE_LOCAL
        shared, shared_errors = [], []
        shared_dir = self.shared_dir()
        if shared_dir:
            shared, shared_errors = rules_mod.load_rules(shared_dir)
            for rule in shared:
                rule.scope = prefs_mod.SCOPE_SHARED
        self._rules = local + shared

        self.tree.blockSignals(True)
        self.tree.clear()
        for rule in self._rules:
            scope_text = "Shared" if self._is_shared_rule(rule) else "Local"
            item = QTreeWidgetItem([rule.name, scope_text, str(len(rule.objects)), rule.file_name])
            item.setTextAlignment(self.COL_COUNT, Qt.AlignRight | Qt.AlignVCenter)
            tip = rule.path
            if rule.description:
                tip = rule.description + "\n" + tip
            for col in range(4):
                item.setToolTip(col, tip)
            item.setData(0, Qt.UserRole, rule.path)
            self.tree.addTopLevelItem(item)
            if os.path.normcase(rule.path) in keep:
                item.setSelected(True)
        self.tree.blockSignals(False)

        text = "{0} local".format(len(local))
        if shared_dir:
            text += " + {0} shared".format(len(shared))
        self.lbl_folder.setText(text + " rule(s)  ({0})".format(_short_dir(self._rules_dir)))
        self.lbl_folder.setToolTip("Local : {0}\nShared : {1}".format(self._rules_dir, shared_dir or "-"))
        for file_name, message in errors + shared_errors:
            self._log("[WARN] Rule '{0}' not loaded : {1}".format(file_name, message))
        self._on_rule_selection_changed()

    def selected_rules(self):
        """표에서 고른 규칙들 (표 순서). 행은 파일 경로로 가른다 (같은 이름이 로컬 · 공유에 있어도)."""
        picked = set()
        for item in self.tree.selectedItems():
            picked.add(os.path.normcase(item.data(0, Qt.UserRole) or ""))
        return [r for r in self._rules if os.path.normcase(r.path) in picked]

    def select_rule_by_name(self, name, scope=None):
        """표에서 이름으로 규칙 하나를 고른다 (새로 만든 뒤 등). scope 를 주면 그 scope 에서만."""
        self.tree.clearSelection()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            rule = self._rules[i] if i < len(self._rules) else None
            if rule is None or rule.name != name:
                continue
            if scope is not None and getattr(rule, "scope", None) != scope:
                continue
            item.setSelected(True)
            self.tree.setCurrentItem(item)
            return True
        return False

    def _confirm_shared(self, action, rules):
        """공유 규칙이 섞여 있으면 한 번 더 묻는다 (v01.17). 공유가 없으면 True."""
        shared = [r for r in rules if self._is_shared_rule(r)]
        if not shared:
            return True
        return QMessageBox.question(
            self, TITLE,
            "{0} SHARED rule(s) (shared folder, tracked by git):\n  {1}\n"
            "{2} them here changes them for everyone who pulls them. Continue?".format(
                len(shared), "\n  ".join(r.name for r in shared[:8]), action),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes

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
        self.btn_share.setEnabled(any(not self._is_shared_rule(r) for r in rules) and bool(self.shared_dir()))
        self.btn_copy_local.setEnabled(any(self._is_shared_rule(r) for r in rules))

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
        self.select_rule_by_name(rule.name, prefs_mod.SCOPE_LOCAL)
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
        if not self._confirm_shared("Renaming", [rule]):
            return
        old_file = rule.file_name
        scope = getattr(rule, "scope", prefs_mod.SCOPE_LOCAL)
        try:
            # 규칙이 있는 폴더 안에서 (로컬 / 공유)
            rules_mod.rename_rule(rule, name, rules_dir=os.path.dirname(rule.path))
        except (ValueError, OSError) as e:
            QMessageBox.warning(self, TITLE, "Cannot rename rule: {0}".format(e))
            return
        self.reload()
        self.select_rule_by_name(rule.name, scope)
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
            if not self._confirm_shared("Deleting", rules):
                return
        deleted, failed = [], []
        for rule in rules:                           # 규칙마다 자기 폴더 안에서만 지운다
            d, f = rules_mod.delete_rules([rule], rules_dir=os.path.dirname(rule.path))
            deleted += d
            failed += f
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

    def on_share(self, *_args):
        """고른 로컬 규칙을 공유 폴더로 옮긴다 (v01.17). 공유 규칙은 건너뛴다."""
        shared_dir = self.shared_dir()
        rules = [r for r in self.selected_rules() if not self._is_shared_rule(r)]
        if not shared_dir or not rules:
            return
        moved = []
        for rule in rules:
            try:
                new = rules_mod.share_rule(rule, shared_dir)
                moved.append(new)
            except (ValueError, OSError) as e:
                self._log("[WARN] Cannot share rule '{0}' : {1}".format(rule.name, e))
        self.reload()
        for rule in moved:
            self._log("[OK] Shared rule '{0}' -> {1}".format(rule.name, rule.path))
        if moved:
            self._log("    Commit and push those files to share them through git.")
            self.select_rule_by_name(moved[0].name, prefs_mod.SCOPE_SHARED)

    def on_copy_to_local(self, *_args):
        """고른 공유 규칙을 로컬로 복사한다 (v01.17). 로컬 규칙은 건너뛴다."""
        rules = [r for r in self.selected_rules() if self._is_shared_rule(r)]
        if not rules:
            return
        copied = []
        for rule in rules:
            try:
                copied.append(rules_mod.copy_rule_to(rule, self._rules_dir))
            except (ValueError, OSError) as e:
                self._log("[WARN] Cannot copy rule '{0}' : {1}".format(rule.name, e))
        self.reload()
        for rule in copied:
            self._log("[OK] Copied shared rule '{0}' to local -> {1}".format(rule.name, rule.path))
        if copied:
            self.select_rule_by_name(copied[0].name, prefs_mod.SCOPE_LOCAL)

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
        act_share = menu.addAction("Share")
        act_share.setEnabled(self.btn_share.isEnabled())
        act_share.triggered.connect(self.on_share)
        act_copy = menu.addAction("Copy to Local")
        act_copy.setEnabled(self.btn_copy_local.isEnabled())
        act_copy.triggered.connect(self.on_copy_to_local)
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
