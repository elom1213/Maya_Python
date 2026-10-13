# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-13
# A00145_RigConnect - Connect > Connect by Rule 의 "Manage..." 다이얼로그 (v01.61)
#
# app/rules/connect/*.json 규칙을 표로 보여 주고, 체크한 규칙 파일을 지운다.
#
#   ┌ [x] │ Name                        │ Pairs │ File                       ┐
#   │ [ ] │ Apple ARKit 52 Facial Target│ 52    │ apple_arkit_52_facial.json │
#   │ [x] │ Face Ctrl -> BlendShape     │ 7     │ face_ctrl_blendshape.json  │
#   └─────┴─────────────────────────────┴───────┴────────────────────────────┘
#   [Check All] [Clear Checks]                         [Delete Checked] [Close]
#
# Delete Checked 는 지울 규칙 이름을 나열해 한 번 확인한 뒤 파일을 지운다(되돌릴 수 없다 - 휴지통이
# 아니라 os.remove). 지우기는 core.delete_rules 가 규칙 폴더 안의 .json 만 받는다.
# 창이 닫히면 호출 쪽(main_window) 이 콤보를 다시 읽는다 - 몇 개를 지웠는지는 deleted_count() 로.

import os

from Framework.qt.qt import *

from tools.A00145_RigConnect.app.core import connect_rules as crule_mgr


class RuleManageDialog(QDialog):
    """규칙 목록 표 + 체크한 규칙 삭제. 닫은 뒤 `deleted_count()` 가 0 보다 크면 콤보를 다시 읽을 것."""

    COL_CHECK, COL_NAME, COL_PAIRS, COL_FILE = 0, 1, 2, 3

    def __init__(self, parent=None, log=None):
        super(RuleManageDialog, self).__init__(parent)
        self.setWindowTitle("Manage Rules")
        self.setMinimumSize(640, 360)
        self._log = log or (lambda msg: None)
        self._rules = []
        self._deleted = 0

        layout = QVBoxLayout(self)

        self.lbl_folder = QLabel()
        self.lbl_folder.setWordWrap(True)
        layout.addWidget(self.lbl_folder)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", "Name", "Pairs", "File"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_CHECK, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_PAIRS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_FILE, QHeaderView.ResizeToContents)
        self.table.setToolTip(
            "Every rule json in the rule folder. Check the rules to delete.\n"
            "Hover a row for its description and the attribute pairs.")
        layout.addWidget(self.table, 1)

        self.lbl_errors = QLabel()
        self.lbl_errors.setWordWrap(True)
        self.lbl_errors.setStyleSheet("color: #e05050;")
        self.lbl_errors.hide()
        layout.addWidget(self.lbl_errors)

        btn_row = QHBoxLayout()
        btn_all = QPushButton("Check All")
        btn_all.clicked.connect(lambda: self._set_all(True))
        btn_row.addWidget(btn_all)
        btn_none = QPushButton("Clear Checks")
        btn_none.clicked.connect(lambda: self._set_all(False))
        btn_row.addWidget(btn_none)
        btn_row.addStretch(1)
        self.btn_delete = QPushButton("Delete Checked")
        self.btn_delete.setToolTip(
            "Delete the json files of the checked rules from the rule folder.\n"
            "Asks once; this cannot be undone.")
        self.btn_delete.clicked.connect(self.on_delete)
        btn_row.addWidget(self.btn_delete)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self.reload()

    # ------------------------------------------------------------ table

    def reload(self):
        """규칙 폴더를 다시 읽어 표를 채운다. 깨진 파일은 빨간 줄로 알린다 (지울 수는 없다 - 폴더에서 직접)."""
        rules, errors = crule_mgr.load_rules()
        self._rules = rules
        self.lbl_folder.setText("Folder : {0}".format(crule_mgr.RULES_DIR))

        self.table.setRowCount(len(rules))
        for r, rule in enumerate(rules):
            tip_lines = [rule.description or "(no description)", "", rule.path, ""]
            tip_lines += ["{0}  ->  {1}".format(s, d) for s, d in rule.pairs[:40]]
            if len(rule.pairs) > 40:
                tip_lines.append("... {0} more".format(len(rule.pairs) - 40))
            tip = "\n".join(tip_lines)

            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check.setCheckState(Qt.Unchecked)
            self.table.setItem(r, self.COL_CHECK, check)
            for col, text in ((self.COL_NAME, rule.name),
                              (self.COL_PAIRS, str(len(rule.pairs))),
                              (self.COL_FILE, os.path.basename(rule.path))):
                cell = QTableWidgetItem(text)
                cell.setToolTip(tip)
                self.table.setItem(r, col, cell)

        if errors:
            self.lbl_errors.setText("Not loaded (fix or remove by hand) : " + "   ".join(
                "{0} - {1}".format(f, m) for f, m in errors))
            self.lbl_errors.show()
        else:
            self.lbl_errors.hide()
        self.btn_delete.setEnabled(bool(rules))

    def _set_all(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        for r in range(self.table.rowCount()):
            self.table.item(r, self.COL_CHECK).setCheckState(state)

    def checked_rules(self):
        """체크한 행의 ConnectRule 들 (표 순서)."""
        out = []
        for r in range(self.table.rowCount()):
            if self.table.item(r, self.COL_CHECK).checkState() == Qt.Checked:
                out.append(self._rules[r])
        return out

    def deleted_count(self):
        return self._deleted

    # ------------------------------------------------------------ delete

    def on_delete(self, confirm=True):
        rules = self.checked_rules()
        if not rules:
            QMessageBox.information(self, "Manage Rules", "Check the rules to delete first.")
            return
        if confirm:
            names = "\n".join("  - {0}  ({1})".format(r.name, os.path.basename(r.path)) for r in rules)
            answer = QMessageBox.question(
                self, "Delete Rules",
                "Delete {0} rule file(s)? This cannot be undone.\n\n{1}".format(len(rules), names),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return

        deleted, failed = crule_mgr.delete_rules(rules)
        for path in deleted:
            self._log("[OK] Rule deleted : {0}".format(path))
        for path, reason in failed:
            self._log("[ERR] Rule not deleted : {0} - {1}".format(path, reason))
        self._deleted += len(deleted)
        self.reload()
