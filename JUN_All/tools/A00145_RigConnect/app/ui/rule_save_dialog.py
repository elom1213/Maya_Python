# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-13
# A00145_RigConnect - Connect > Transfer Connection 의 "Save as Rule..." 다이얼로그 (v01.60)
#
# Transfer Connection 탭에서 체크한 어트리뷰트 x 체크한 노드의 연결을 Connect by Rule 규칙
# (app/rules/connect/<file>.json) 으로 저장하기 전에 보여 주고 다듬는 창이다.
#
#   Name        [ Face Ctrl -> BlendShape      ]
#   File        [ face_ctrl_blendshape         ] .json
#   Description [ ...                          ]
#   Direction   (•) Source objects DRIVE the nodes   (n)   ( ) Nodes DRIVE the Source objects   (m)
#   ┌ [x] │ Source attr │ Destination attr │ Connections ┐
#   │ [x] │ jawOpen     │ jawOpen          │ 2           │
#   │ [x] │ smile       │ mouthSmile_L     │ 1           │
#   └─────┴─────────────┴──────────────────┴─────────────┘
#   Apply with Connect by Rule : Source Objects = the Source objects here, Destination Objects = the nodes.
#   [Check All] [Clear Checks]                                   [Save] [Cancel]
#
# 규칙은 "Source.a -> Destination.b" 한 방향이라 **방향을 하나만** 고른다 - downstream 이면 지금의
# Source 오브젝트가 규칙의 Source, upstream 이면 노드 쪽이 규칙의 Source 가 된다. 두 방향의 짝은
# 호출 쪽(core.rule_pairs) 이 따로 계산해 넘기고, 이 창은 cmds 를 쓰지 않는다.
#
# 파일 이름은 이름에서 자동으로 만들되(rule_file_name) 사용자가 손대면 그 뒤로는 따라가지 않는다.
# 같은 파일이 이미 있으면 Save 때 덮어쓸지 묻는다. 같은 이름의 규칙이 다른 파일에 있으면 경고만 한다.

import os

from Framework.qt.qt import *

from tools.A00145_RigConnect.app.core import connect_rules as crule_mgr


class RuleSaveDialog(QDialog):
    """규칙 저장 창. accept 뒤 `result_rule()` 로 (name, description, file_name, pairs, overwrite) 를 얻는다."""

    COL_CHECK, COL_SRC, COL_DST, COL_COUNT = 0, 1, 2, 3

    def __init__(self, down_pairs, up_pairs, parent=None, existing_rules=None):
        """
        Args:
            down_pairs: core.rule_pairs(..., downstream=True) 결과 - Source 오브젝트가 드라이버.
            up_pairs:   core.rule_pairs(..., upstream=True) 결과 - 노드가 드라이버.
            existing_rules: 이미 있는 ConnectRule 목록 (이름 겹침 경고용).
        """
        super(RuleSaveDialog, self).__init__(parent)
        self.setWindowTitle("Save as Rule")
        self.setMinimumWidth(560)

        self._pairs = {"down": list(down_pairs or []), "up": list(up_pairs or [])}
        self._existing = list(existing_rules or [])
        self._file_edited = False
        self._result = None

        layout = QVBoxLayout(self)
        form = QGridLayout()
        layout.addLayout(form)

        form.addWidget(QLabel("Name"), 0, 0)
        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText("Rule name shown in the Connect by Rule combo")
        self.le_name.textChanged.connect(self._on_name_changed)
        form.addWidget(self.le_name, 0, 1, 1, 2)

        form.addWidget(QLabel("File"), 1, 0)
        self.le_file = QLineEdit()
        self.le_file.setPlaceholderText("file name in app/rules/connect/")
        self.le_file.setToolTip(
            "File name of the rule json (made from the name until you edit it).\n"
            "Folder : {0}".format(crule_mgr.RULES_DIR))
        self.le_file.textEdited.connect(self._on_file_edited)
        form.addWidget(self.le_file, 1, 1)
        form.addWidget(QLabel(".json"), 1, 2)

        form.addWidget(QLabel("Description"), 2, 0)
        self.le_desc = QLineEdit()
        self.le_desc.setPlaceholderText("Shown in the combo tooltip (optional)")
        form.addWidget(self.le_desc, 2, 1, 1, 2)

        # --- 방향
        dir_box = QGroupBox("Direction")
        dir_row = QHBoxLayout(dir_box)
        self.rb_down = QRadioButton(
            "Source objects DRIVE the nodes  ({0})".format(len(self._pairs["down"])))
        self.rb_down.setToolTip(
            "Source.attr -> node.attr (downstream).\n"
            "Rule pairs = [Source attr, node attr].\n"
            "Apply with Connect by Rule : Source Objects = these Source objects,\n"
            "Destination Objects = the nodes.")
        self.rb_up = QRadioButton(
            "Nodes DRIVE the Source objects  ({0})".format(len(self._pairs["up"])))
        self.rb_up.setToolTip(
            "node.attr -> Source.attr (upstream).\n"
            "Rule pairs = [node attr, Source attr].\n"
            "Apply with Connect by Rule : Source Objects = the nodes,\n"
            "Destination Objects = these Source objects.")
        self.rb_down.setEnabled(bool(self._pairs["down"]))
        self.rb_up.setEnabled(bool(self._pairs["up"]))
        if self._pairs["down"] or not self._pairs["up"]:
            self.rb_down.setChecked(True)
        else:
            self.rb_up.setChecked(True)
        self.rb_down.toggled.connect(lambda _c: self._fill_table())
        dir_row.addWidget(self.rb_down)
        dir_row.addWidget(self.rb_up)
        dir_row.addStretch(1)
        layout.addWidget(dir_box)

        # --- 짝 표
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", "Source attr", "Destination attr", "Connections"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_CHECK, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_SRC, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_DST, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_COUNT, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(220)
        self.table.setToolTip(
            "The attribute pairs the rule will hold (checked rows only).\n"
            "Source attr -> Destination attr, as Connect by Rule applies them.\n"
            "Hover a row to see the connections it was read from.")
        layout.addWidget(self.table, 1)

        self.lbl_apply = QLabel()
        self.lbl_apply.setWordWrap(True)
        layout.addWidget(self.lbl_apply)

        # --- 버튼
        btn_row = QHBoxLayout()
        btn_all = QPushButton("Check All")
        btn_all.clicked.connect(lambda: self._set_all(True))
        btn_row.addWidget(btn_all)
        btn_none = QPushButton("Clear Checks")
        btn_none.clicked.connect(lambda: self._set_all(False))
        btn_row.addWidget(btn_none)
        btn_row.addStretch(1)
        self.btn_save = QPushButton("Save")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self.btn_save)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        self._fill_table()

    # ------------------------------------------------------------ state

    def direction(self):
        return "up" if self.rb_up.isChecked() else "down"

    def _on_name_changed(self, text):
        if not self._file_edited:
            self.le_file.blockSignals(True)
            self.le_file.setText(crule_mgr.rule_file_name(text) if text.strip() else "")
            self.le_file.blockSignals(False)

    def _on_file_edited(self, _text):
        self._file_edited = True

    def _fill_table(self):
        pairs = self._pairs[self.direction()]
        self.table.setRowCount(len(pairs))
        for r, entry in enumerate(pairs):
            tip = "\n".join(entry.get("plugs") or [])
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check.setCheckState(Qt.Checked)
            self.table.setItem(r, self.COL_CHECK, check)
            for col, text in ((self.COL_SRC, entry["src"]), (self.COL_DST, entry["dst"]),
                              (self.COL_COUNT, str(entry.get("count", 0)))):
                cell = QTableWidgetItem(text)
                cell.setToolTip(tip)
                self.table.setItem(r, col, cell)
        if self.direction() == "down":
            self.lbl_apply.setText(
                "Apply with Connect by Rule :  Source Objects = these Source objects,  "
                "Destination Objects = the nodes.")
        else:
            self.lbl_apply.setText(
                "Apply with Connect by Rule :  Source Objects = the nodes,  "
                "Destination Objects = these Source objects.")

    def _set_all(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        for r in range(self.table.rowCount()):
            self.table.item(r, self.COL_CHECK).setCheckState(state)

    def checked_pairs(self):
        """체크한 행의 (source_attr, destination_attr) - 표 순서."""
        out = []
        for r in range(self.table.rowCount()):
            if self.table.item(r, self.COL_CHECK).checkState() == Qt.Checked:
                out.append((self.table.item(r, self.COL_SRC).text(),
                            self.table.item(r, self.COL_DST).text()))
        return out

    # ------------------------------------------------------------ save

    def _on_save(self):
        name = self.le_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Save as Rule", "Give the rule a name.")
            return
        file_name = self.le_file.text().strip() or crule_mgr.rule_file_name(name)
        pairs = self.checked_pairs()
        if not pairs:
            QMessageBox.warning(self, "Save as Rule", "Check at least one attribute pair.")
            return

        path = crule_mgr.rule_path(file_name)
        overwrite = False
        if os.path.exists(path):
            answer = QMessageBox.question(
                self, "Save as Rule",
                "The file already exists :\n{0}\n\nOverwrite it?".format(path),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return
            overwrite = True

        same_name = [r for r in self._existing
                     if r.name == name and os.path.normcase(r.path) != os.path.normcase(path)]
        if same_name:
            answer = QMessageBox.question(
                self, "Save as Rule",
                "A rule named '{0}' already exists in another file :\n{1}\n\n"
                "Two rules with the same name are hard to tell apart in the combo.\n"
                "Save anyway?".format(name, same_name[0].path),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return

        self._result = {
            "name": name,
            "description": self.le_desc.text().strip(),
            "file_name": file_name,
            "pairs": pairs,
            "overwrite": overwrite,
            "direction": self.direction(),
        }
        self.accept()

    def result_rule(self):
        """accept 뒤의 입력. 취소면 None."""
        return self._result
