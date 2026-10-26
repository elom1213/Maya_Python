# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - 세트 규칙 New / Edit 대화상자  (v01.41)
#
#   Name [Bake      ]   Set name [Bake      ]   Match [Exact ▾]   [x] Ignore namespace
#   Description [                                 ]
#   (error line)                                  [OK] [Cancel]
# OK 는 set_rules.validate 를 통과해야 닫힌다(regex 컴파일 포함). 결과는 values() -> dict.

from Framework.qt.qt import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QLabel,
    QDialogButtonBox,
)

from ..core import set_rules


class SetRuleDialog(QDialog):

    def __init__(self, rule=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Set Rule" if rule else "New Set Rule")
        self.setMinimumWidth(420)
        form = QFormLayout(self)

        self.le_name = QLineEdit(rule.name if rule else "")
        self.le_name.setPlaceholderText("e.g. Bake")
        self.le_name.setToolTip("Rule name - also the json file name (one json per rule).")
        form.addRow("Name:", self.le_name)

        self.le_set = QLineEdit(rule.set_name if rule else "")
        self.le_set.setPlaceholderText("e.g. Bake")
        self.le_set.setToolTip("Name of the objectSet to look for in every Maya file.\n"
                               "Top-level or inside another set - every set in the scene is checked by its leaf name.")
        form.addRow("Set name:", self.le_set)

        self.cmb_match = QComboBox()
        for key in set_rules.MATCHES:
            self.cmb_match.addItem(set_rules.MATCH_LABELS[key], key)
        if rule:
            self.cmb_match.setCurrentIndex(max(0, list(set_rules.MATCHES).index(rule.match)))
        self.cmb_match.setToolTip("Exact : leaf name equals Set name\nContains : Set name is part of the leaf name\n"
                                  "Regex : Set name is a regular expression matched against the whole leaf name")
        form.addRow("Match:", self.cmb_match)

        self.chk_ns = QCheckBox("Ignore namespace")
        self.chk_ns.setChecked(rule.ignore_namespace if rule else True)
        self.chk_ns.setToolTip("ON : 'CHN:rig:Bake' is compared as 'Bake' (sets inside references match).")
        form.addRow("", self.chk_ns)

        self.le_desc = QLineEdit(rule.description if rule else "")
        self.le_desc.setPlaceholderText("optional")
        form.addRow("Description:", self.le_desc)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #ff6b6b;")
        self.lbl_error.setWordWrap(True)
        form.addRow(self.lbl_error)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return {"name": self.le_name.text().strip(), "set_name": self.le_set.text().strip(),
                "match": self.cmb_match.currentData(), "ignore_namespace": self.chk_ns.isChecked(),
                "description": self.le_desc.text().strip()}

    def _on_ok(self, *_args):
        v = self.values()
        errors = set_rules.validate(v["name"], v["set_name"], v["match"])
        if errors:
            self.lbl_error.setText(" ".join(errors))
            return
        self.accept()
