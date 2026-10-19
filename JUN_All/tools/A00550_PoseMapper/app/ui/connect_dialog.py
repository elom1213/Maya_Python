# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - Connect To... 대화상자 (계획서 §3.5)
#
# 저장한 관계(라이브러리)를 임의의 노드 쌍에 연결한다. 이름이 같은 음소 · 타겟만 쓰고, 없는 것은 미리 보여 주고 건너뛴다.
# 이미 다른 것이 연결된 타겟: Skip(기본) / Replace / Add.

import copy

import maya.cmds as cmds

from Framework.qt.qt import *

from ..core import attrs as attrs_mod
from ..core import network


class ConnectDialog(QDialog):

    def __init__(self, lib, log, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect Library")
        self.lib = lib
        self._log = log
        self.result_net = None
        self._build()
        self.update_preview()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Library  {0}   ({1} phonemes, {2} targets)".format(
            self.lib.name, len(self.lib.poses), len(self.lib.targets_used()))))
        grid = QGridLayout()
        self.le_src = QLineEdit()
        self.le_tgt = QLineEdit()
        self.le_src.setPlaceholderText("node with the phoneme attributes")
        self.le_tgt.setPlaceholderText("blendShape or any node with the target attributes")
        for row, (label, le) in enumerate((("Source", self.le_src), ("Target", self.le_tgt))):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(le, row, 1)
            btn = QPushButton("<< Sel")
            btn.clicked.connect(lambda _=False, w=le: self._pick(w))
            grid.addWidget(btn, row, 2)
            le.editingFinished.connect(self.update_preview)
        self.le_prefix = QLineEdit()
        self.le_prefix.setPlaceholderText("node name prefix, e.g. avatarA_")
        grid.addWidget(QLabel("Prefix"), 2, 0)
        grid.addWidget(self.le_prefix, 2, 1, 1, 2)
        self.ds_ref = QDoubleSpinBox()
        self.ds_ref.setDecimals(3)
        self.ds_ref.setRange(0.001, 100000.0)
        self.ds_ref.setValue(self.lib.ref_value)
        self.ds_ref.setToolTip("Phoneme value at which a pose is reached (the library's value by default)")
        grid.addWidget(QLabel("Ref value"), 3, 0)
        grid.addWidget(self.ds_ref, 3, 1)
        layout.addLayout(grid)

        ex_box = QGroupBox("Target already driven by something else")
        ex = QHBoxLayout(ex_box)
        self.rb_skip = QRadioButton("Skip")
        self.rb_replace = QRadioButton("Replace")
        self.rb_add = QRadioButton("Add (sum)")
        self.rb_skip.setChecked(True)
        for rb in (self.rb_skip, self.rb_replace, self.rb_add):
            ex.addWidget(rb)
        layout.addWidget(ex_box)

        self.lb_preview = QLabel()
        self.lb_preview.setWordWrap(True)
        self.lb_preview.setMinimumWidth(420)
        layout.addWidget(self.lb_preview)

        row = QHBoxLayout()
        btn_check = QPushButton("Check")
        btn_check.clicked.connect(self.update_preview)
        btn_ok = QPushButton("Connect")
        btn_ok.clicked.connect(self.on_connect)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        row.addWidget(btn_check)
        row.addStretch(1)
        row.addWidget(btn_ok)
        row.addWidget(btn_cancel)
        layout.addLayout(row)

    def _pick(self, line_edit):
        sel = cmds.ls(sl=True) or []
        if sel:
            line_edit.setText(sel[0])
            self.update_preview()

    def on_existing(self):
        return "replace" if self.rb_replace.isChecked() else "add" if self.rb_add.isChecked() else "skip"

    def update_preview(self):
        src, tgt = self.le_src.text().strip(), self.le_tgt.text().strip()
        lines = []
        if src and cmds.objExists(src):
            have = set(attrs_mod.numeric_user_attrs(src))
            need = list(self.lib.poses)
            miss = [p for p in need if p not in have]
            lines.append("{0} / {1} source attributes found{2}".format(
                len(need) - len(miss), len(need), "  (missing: {0})".format(", ".join(miss)) if miss else ""))
        else:
            lines.append("Source: not found" if src else "Source: -")
        if tgt and cmds.objExists(tgt):
            have = set(attrs_mod.target_attrs(tgt))
            need = self.lib.targets_used()
            miss = [t for t in need if t not in have]
            driven = [t for t in need if t in have and attrs_mod.incoming(attrs_mod.plug(tgt, t))]
            lines.append("{0} / {1} targets found{2}".format(
                len(need) - len(miss), len(need), "  (missing: {0})".format(", ".join(miss)) if miss else ""))
            if driven:
                lines.append("{0} target(s) already driven -> {1}".format(len(driven), self.on_existing()))
        else:
            lines.append("Target: not found" if tgt else "Target: -")
        self.lb_preview.setText("\n".join(lines))

    def on_connect(self):
        src, tgt = self.le_src.text().strip(), self.le_tgt.text().strip()
        lib = copy.deepcopy(self.lib)
        lib.ref_value = self.ds_ref.value()
        try:
            net, rep = network.build(lib, src, tgt, prefix=self.le_prefix.text().strip(),
                                     on_existing=self.on_existing())
        except (ValueError, RuntimeError) as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            return
        log_report(self._log, rep, src, tgt)
        self.result_net = net
        self.accept()


def log_report(log, rep, src, tgt):
    """network.build / sync 의 report 를 로그로."""
    n = len(rep["built"]) + len(rep["updated"])
    log("[DONE] {0} -> {1}: {2} target(s) connected ({3} new, {4} updated, {5} removed)".format(
        src, tgt, n, len(rep["built"]), len(rep["updated"]), len(rep["removed"])))
    if rep["skipped_existing"]:
        log("[WARN] Skipped {0} target(s) already driven (choose Replace or Add to override): {1}".format(
            len(rep["skipped_existing"]), ", ".join(t for t, _s in rep["skipped_existing"][:10]) +
            (" ..." if len(rep["skipped_existing"]) > 10 else "")))
    for key, label in (("replaced", "Replaced"), ("added", "Added to the existing driver")):
        if rep[key]:
            log("[INFO] {0}: {1}".format(label, ", ".join(t for t, _s in rep[key])))
    if rep["missing_targets"]:
        log("[WARN] Targets not on {0}: {1}".format(tgt, ", ".join(rep["missing_targets"])))
    if rep["missing_sources"]:
        log("[WARN] Phonemes not on {0}: {1}".format(src, ", ".join(rep["missing_sources"])))
