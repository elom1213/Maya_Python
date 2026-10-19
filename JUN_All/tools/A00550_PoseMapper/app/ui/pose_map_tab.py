# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - Pose Map 탭 (계획서 §3)
#
# Source(음소 노드) · Target(blendShape / 아무 노드) 를 고르고, 음소 하나를 골라 타겟 값을 슬라이더로 정한다.
#   - 슬라이더 = 라이브러리 값. 노드망이 있으면 그 타겟 체인만 바로 sync (노드 재생성 없음).
#   - Ref value = 포즈가 되는 음소 값 (기본 10, 임의의 실수). 바꾸면 weight 전체가 다시 계산된다.
#   - Solo preview = 고른 음소만 Ref, 나머지 0 (끄면 원래 값). Capture = 지금 씬의 결과를 포즈로.
#   - Save / Load = json, Connect To... = 다른 노드 쌍에.

import os

import maya.cmds as cmds

from Framework.qt.qt import *

from ..core import attrs as attrs_mod
from ..core import capture as capture_mod
from ..core import library as lib_mod
from ..core import network
from .connect_dialog import ConnectDialog, log_report


SLIDER_STEPS = 1000                 # 슬라이더 0~1000 = 값 0~1
VALUE_RANGE = (-2.0, 2.0)           # 스핀 박스 범위 (블렌드셰이프 과다 · 반대 방향 허용)
EXISTING = [("Skip", "skip"), ("Replace", "replace"), ("Add (sum)", "add")]
# 음소가 아닌 입력(JALI 의 턱 / 입술 배율 등) - 기본으로 체크 해제. Solo · Capture 가 0 으로 만들면 출력이 통째로 0 이 된다.
NOT_PHONEME_DEFAULT = ("jaw", "lip")


class PoseMapTab(QWidget):

    def __init__(self, log, parent=None):
        super().__init__(parent)
        self._log = log
        self.lib = lib_mod.PoseLibrary(name="untitled")
        self.lib_path = None
        self.net = None
        self.driver = None
        self._updating = False
        self._skip_warned = set()
        self._checked = {}                  # 어트리뷰트 -> 음소로 다룰지 (목록 체크)
        self._build()
        self._refresh_libraries()

    # ================================================================== UI

    def _build(self):
        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        # --- Source
        src_box = QGroupBox("Source (phonemes)")
        sl = QVBoxLayout(src_box)
        row = QHBoxLayout()
        self.le_source = QLineEdit()
        self.le_source.setPlaceholderText("e.g. JALI_IN")
        self.le_source.editingFinished.connect(self.on_nodes_changed)
        b = QPushButton("<< Sel")
        b.clicked.connect(lambda: self._pick(self.le_source))
        row.addWidget(QLabel("Node"))
        row.addWidget(self.le_source, 1)
        row.addWidget(b)
        sl.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel("Ref value"))
        self.ds_ref = QDoubleSpinBox()
        self.ds_ref.setDecimals(3)
        self.ds_ref.setRange(0.001, 100000.0)
        self.ds_ref.setValue(lib_mod.DEFAULT_REF)
        self.ds_ref.setToolTip("Phoneme value at which the pose is reached (default 10, any real number).\n"
                               "Solo preview turns the phoneme on to this value.")
        self.ds_ref.editingFinished.connect(self.on_ref_changed)
        row.addWidget(self.ds_ref)
        row.addStretch(1)
        sl.addLayout(row)
        self.lw_phonemes = QListWidget()
        self.lw_phonemes.setMinimumWidth(170)
        self.lw_phonemes.setToolTip("Checked = phoneme. Solo preview and Capture leave unchecked attributes\n"
                                    "untouched (e.g. JALI Jaw / Lip multipliers stay as they are).")
        self.lw_phonemes.itemChanged.connect(self._on_check_changed)
        self.lw_phonemes.currentItemChanged.connect(lambda *_: self.on_phoneme_changed())
        sl.addWidget(self.lw_phonemes, 1)
        self.cb_solo = QCheckBox("Solo preview")
        self.cb_solo.setToolTip("Only the selected phoneme = Ref value, all others = 0.\n"
                                "Turning it off (or leaving the tab) restores the previous values.")
        self.cb_solo.toggled.connect(self.on_solo_toggled)
        sl.addWidget(self.cb_solo)
        top.addWidget(src_box, 1)

        # --- Target
        tgt_box = QGroupBox("Target (blendShape or any node)")
        tl = QVBoxLayout(tgt_box)
        row = QHBoxLayout()
        self.le_target = QLineEdit()
        self.le_target.setPlaceholderText("e.g. BS_arkit")
        self.le_target.editingFinished.connect(self.on_nodes_changed)
        b = QPushButton("<< Sel")
        b.clicked.connect(lambda: self._pick(self.le_target))
        row.addWidget(QLabel("Node"))
        row.addWidget(self.le_target, 1)
        row.addWidget(b)
        tl.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel("Filter"))
        self.le_filter = QLineEdit()
        self.le_filter.textChanged.connect(lambda *_: self._apply_filter())
        self.cb_used = QCheckBox("Used only")
        self.cb_used.setToolTip("Only targets with a value in the selected phoneme")
        self.cb_used.toggled.connect(lambda *_: self._apply_filter())
        row.addWidget(self.le_filter, 1)
        row.addWidget(self.cb_used)
        tl.addLayout(row)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Target", "", "Value"])
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tl.addWidget(self.table, 1)
        row = QHBoxLayout()
        for label, slot, tip in (
                ("Zero Pose", self.on_zero_pose, "Set every target of the selected phoneme to 0"),
                ("Mirror L > R", self.on_mirror, "Copy ...Left values to ...Right for the selected phoneme"),
                ("Capture", self.on_capture, "Read the current scene result into the library:\n"
                                             "each listed phoneme = Ref value, others 0, minus all-zero")):
            b = QPushButton(label)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            row.addWidget(b)
        tl.addLayout(row)
        top.addWidget(tgt_box, 2)
        layout.addLayout(top, 1)

        # --- Library
        lib_row = QHBoxLayout()
        lib_row.addWidget(QLabel("Library"))
        self.cmb_lib = QComboBox()
        self.cmb_lib.setMinimumWidth(200)
        lib_row.addWidget(self.cmb_lib, 1)
        for label, slot in (("Load", self.on_load), ("Save", self.on_save), ("Save As...", self.on_save_as),
                            ("New", self.on_new)):
            b = QPushButton(label)
            b.clicked.connect(slot)
            lib_row.addWidget(b)
        self.cb_clamp = QCheckBox("Clamp 0-1")
        self.cb_clamp.setChecked(True)
        self.cb_clamp.toggled.connect(self.on_clamp_toggled)
        lib_row.addWidget(self.cb_clamp)
        layout.addLayout(lib_row)

        # --- Network
        net_row = QHBoxLayout()
        net_row.addWidget(QLabel("If target is driven"))
        self.cmb_existing = QComboBox()
        for label, _k in EXISTING:
            self.cmb_existing.addItem(label)
        self.cmb_existing.setToolTip("Skip (default) keeps the other driver. Replace disconnects it.\n"
                                     "Add keeps it as one more input of the sum.")
        net_row.addWidget(self.cmb_existing)
        self.btn_build = QPushButton("Build / Update Network")
        self.btn_build.setMinimumHeight(30)
        self.btn_build.clicked.connect(self.on_build)
        b_connect = QPushButton("Connect To...")
        b_connect.clicked.connect(self.on_connect_to)
        b_remove = QPushButton("Remove Network")
        b_remove.clicked.connect(self.on_remove)
        net_row.addWidget(self.btn_build, 2)
        net_row.addWidget(b_connect, 1)
        net_row.addWidget(b_remove, 1)
        layout.addLayout(net_row)
        self.lb_status = QLabel("No network")
        layout.addWidget(self.lb_status)

    # ================================================================== 도우미

    def _pick(self, line_edit):
        sel = cmds.ls(sl=True) or []
        if not sel:
            self._log("[WARN] Select a node first.")
            return
        line_edit.setText(sel[0])
        self.on_nodes_changed()

    def source(self):
        s = self.le_source.text().strip()
        return s if s and cmds.objExists(s) else None

    def target(self):
        t = self.le_target.text().strip()
        return t if t and cmds.objExists(t) else None

    def existing_mode(self):
        return EXISTING[self.cmb_existing.currentIndex()][1]

    def current_phoneme(self):
        item = self.lw_phonemes.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _status(self):
        if self.net and cmds.objExists(self.net):
            self.lb_status.setText("Network {0}: {1} target chain(s), ref {2:g}  |  library '{3}'{4}".format(
                self.net, len(network.chains(self.net)), self.lib.ref_value, self.lib.name,
                "  ({0})".format(self.lib_path) if self.lib_path else ""))
        else:
            self.net = None
            self.lb_status.setText("No network  |  library '{0}'".format(self.lib.name))

    # ================================================================== 노드

    def on_nodes_changed(self):
        self.stop_preview()
        src, tgt = self.source(), self.target()
        if self.le_source.text().strip() and not src:
            self._log("[ERROR] Source not found: {0}".format(self.le_source.text().strip()))
        if self.le_target.text().strip() and not tgt:
            self._log("[ERROR] Target not found: {0}".format(self.le_target.text().strip()))
        self.net = None
        if src and tgt:
            nets = network.find_networks(src, tgt)
            if nets:
                self.net = nets[0]
                self.lib = network.read_library(self.net)
                self.lib_path = None
                self.ds_ref.setValue(self.lib.ref_value)
                self.cb_clamp.blockSignals(True)
                self.cb_clamp.setChecked(self.lib.clamp)
                self.cb_clamp.blockSignals(False)
                self._log("[INFO] Found network {0} - the library now shows its weights.".format(self.net))
        self._fill_phonemes()
        self._fill_targets()
        self._status()

    def _fill_phonemes(self):
        keep = self.current_phoneme()
        self.lw_phonemes.blockSignals(True)
        self.lw_phonemes.clear()
        src = self.source()
        names = attrs_mod.numeric_user_attrs(src) if src else list(self.lib.source_attrs)
        for p in names:
            n = len(self.lib.pose(p))
            item = QListWidgetItem("{0}   ({1})".format(p, n) if n else p)
            item.setData(Qt.UserRole, p)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            on = self._checked.get(p, p.lower() not in NOT_PHONEME_DEFAULT)
            item.setCheckState(Qt.Checked if on else Qt.Unchecked)
            self.lw_phonemes.addItem(item)
        self.lw_phonemes.blockSignals(False)
        for i in range(self.lw_phonemes.count()):
            if self.lw_phonemes.item(i).data(Qt.UserRole) == keep:
                self.lw_phonemes.setCurrentRow(i)
                break
        else:
            if self.lw_phonemes.count():
                self.lw_phonemes.setCurrentRow(0)

    def _update_phoneme_label(self, phoneme):
        for i in range(self.lw_phonemes.count()):
            item = self.lw_phonemes.item(i)
            if item.data(Qt.UserRole) == phoneme:
                n = len(self.lib.pose(phoneme))
                item.setText("{0}   ({1})".format(phoneme, n) if n else phoneme)

    def _fill_targets(self):
        self._updating = True
        self.table.setRowCount(0)
        tgt = self.target()
        names = attrs_mod.target_attrs(tgt) if tgt else self.lib.targets_used()
        for r, t in enumerate(names):
            self.table.insertRow(r)
            item = QTableWidgetItem(t)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, item)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, SLIDER_STEPS)
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setRange(*VALUE_RANGE)
            spin.setSingleStep(0.01)
            slider.valueChanged.connect(lambda v, s=spin: s.setValue(v / float(SLIDER_STEPS)))
            spin.valueChanged.connect(lambda v, name=t, sl=slider: self._on_value(name, v, sl))
            self.table.setCellWidget(r, 1, slider)
            self.table.setCellWidget(r, 2, spin)
        self._updating = False
        self._load_pose_values()

    def _load_pose_values(self):
        p = self.current_phoneme()
        self._updating = True
        for r in range(self.table.rowCount()):
            t = self.table.item(r, 0).text()
            v = self.lib.get(p, t) if p else 0.0
            spin, slider = self.table.cellWidget(r, 2), self.table.cellWidget(r, 1)
            spin.setValue(v)
            slider.blockSignals(True)
            slider.setValue(int(round(max(0.0, min(1.0, v)) * SLIDER_STEPS)))
            slider.blockSignals(False)
        self._updating = False
        self._apply_filter()

    def _apply_filter(self):
        text = self.le_filter.text().strip().lower()
        used = self.cb_used.isChecked()
        p = self.current_phoneme()
        for r in range(self.table.rowCount()):
            t = self.table.item(r, 0).text()
            hide = (text and text not in t.lower()) or (used and abs(self.lib.get(p, t)) < lib_mod.EPS)
            self.table.setRowHidden(r, bool(hide))

    # ================================================================== 편집

    def on_phoneme_changed(self):
        self._load_pose_values()
        if self.driver is not None and self.driver.active and self.current_phoneme():
            self._solo(self.current_phoneme())

    def _on_value(self, target_name, value, slider):
        slider.blockSignals(True)
        slider.setValue(int(round(max(0.0, min(1.0, value)) * SLIDER_STEPS)))
        slider.blockSignals(False)
        if self._updating:
            return
        p = self.current_phoneme()
        if not p:
            return
        self.lib.set(p, target_name, value)
        self._update_phoneme_label(p)
        if self.net and cmds.objExists(self.net):
            try:
                rep = network.sync(self.net, self.lib, self.existing_mode(), only_targets=[target_name])
            except (ValueError, RuntimeError) as e:
                self._log("[ERROR] {0}".format(str(e).strip()))
                return
            if rep["skipped_existing"] and target_name not in self._skip_warned:
                self._skip_warned.add(target_name)
                self._log("[WARN] {0} is driven by {1} - skipped (set 'If target is driven' to Replace or Add)".format(
                    target_name, rep["skipped_existing"][0][1]))
            if rep["built"]:
                self._status()

    def on_ref_changed(self):
        ref = self.ds_ref.value()
        if abs(ref - self.lib.ref_value) < 1e-9:
            return
        self.lib.ref_value = ref
        if self.net and cmds.objExists(self.net):
            network.sync(self.net, self.lib, self.existing_mode())
            self._log("[OK] Ref value {0:g} - all weights recomputed".format(ref))
        if self.driver is not None and self.driver.active and self.current_phoneme():
            self._solo(self.current_phoneme())
        self._status()

    def on_clamp_toggled(self, on):
        self.lib.clamp = on
        if self.net and cmds.objExists(self.net):
            self._log("[INFO] Clamp applies to new chains. Remove and rebuild the network to change existing ones.")

    def on_zero_pose(self, *args):
        p = self.current_phoneme()
        if not p:
            return
        targets = list(self.lib.pose(p))
        self.lib.clear_pose(p)
        if self.net and targets:
            network.sync(self.net, self.lib, self.existing_mode(), only_targets=targets)
        self._load_pose_values()
        self._update_phoneme_label(p)
        self._log("[OK] {0}: pose cleared ({1} target(s))".format(p, len(targets)))

    def on_mirror(self, *args):
        p = self.current_phoneme()
        if not p:
            return
        changed = []
        for t, v in self.lib.pose(p).items():
            if t.endswith("Left"):
                right = t[:-4] + "Right"
                self.lib.set(p, right, v)
                changed.append(right)
        if self.net and changed:
            network.sync(self.net, self.lib, self.existing_mode(), only_targets=changed)
        self._load_pose_values()
        self._update_phoneme_label(p)
        self._log("[OK] {0}: mirrored {1} Left -> Right value(s)".format(p, len(changed)))

    # ================================================================== 미리보기 · 캡처

    def _phoneme_names(self):
        """체크된 어트리뷰트 = 음소 (Solo · Capture 대상)."""
        out = []
        for i in range(self.lw_phonemes.count()):
            item = self.lw_phonemes.item(i)
            if item.checkState() == Qt.Checked:
                out.append(item.data(Qt.UserRole))
        return out

    def _on_check_changed(self, item):
        self._checked[item.data(Qt.UserRole)] = item.checkState() == Qt.Checked
        if self.driver is not None:
            self.stop_preview()

    def _solo(self, phoneme):
        try:
            self.driver.solo(phoneme, self.ds_ref.value())
        except capture_mod.CaptureError as e:
            self._log("[ERROR] {0}".format(e))

    def on_solo_toggled(self, on):
        if on:
            src = self.source()
            if not src or self.current_phoneme() not in self._phoneme_names():
                self._log("[WARN] Pick a source node and a phoneme first.")
                self.cb_solo.blockSignals(True)
                self.cb_solo.setChecked(False)
                self.cb_solo.blockSignals(False)
                return
            self.driver = capture_mod.PhonemeDriver(src, self._phoneme_names())
            for p, why in self.driver.problems:
                self._log("[WARN] {0}: {1} - not previewed".format(p, why))
            self._solo(self.current_phoneme())
            self._log("[INFO] Solo preview on ({0:g}). Turn it off to restore the phoneme values.".format(
                self.ds_ref.value()))
        else:
            self.stop_preview()

    def stop_preview(self):
        if self.driver is not None:
            self.driver.restore()
            self.driver = None
            self._log("[INFO] Solo preview off - phoneme values restored.")
        if self.cb_solo.isChecked():
            self.cb_solo.blockSignals(True)
            self.cb_solo.setChecked(False)
            self.cb_solo.blockSignals(False)

    def on_capture(self, *args):
        src, tgt = self.source(), self.target()
        if not src or not tgt:
            self._log("[ERROR] Pick a source and a target first.")
            return
        self.stop_preview()
        phon = self._phoneme_names()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            lib, info = capture_mod.capture(src, phon, tgt, attrs_mod.target_attrs(tgt), self.ds_ref.value(),
                                            name=self.lib.name)
        except capture_mod.CaptureError as e:
            self._log("[ERROR] {0}".format(e))
            return
        finally:
            QApplication.restoreOverrideCursor()
        lib.clamp = self.cb_clamp.isChecked()
        self.lib = lib
        for p, why in info["problems"]:
            self._log("[WARN] {0}: {1} - not captured".format(p, why))
        if info["baseline"]:
            self._log("[INFO] Targets not zero with all phonemes at 0 (subtracted): {0}".format(
                ", ".join(sorted(info["baseline"]))))
        self._log("[OK] Captured {0} phoneme pose(s) from the scene at ref {1:g}".format(len(lib.poses), lib.ref_value))
        if self.net and cmds.objExists(self.net):
            self._log("[INFO] Press Build / Update Network to write these values into {0}.".format(self.net))
        self._fill_phonemes()
        self._load_pose_values()
        self._status()

    # ================================================================== 라이브러리

    def _refresh_libraries(self, keep=None):
        self.cmb_lib.clear()
        self.cmb_lib.addItems(lib_mod.list_libraries())
        if keep:
            self.cmb_lib.setCurrentText(keep)

    def _set_library(self, lib, path):
        self.lib = lib
        self.lib_path = path
        self.ds_ref.setValue(lib.ref_value)
        self.cb_clamp.blockSignals(True)
        self.cb_clamp.setChecked(lib.clamp)
        self.cb_clamp.blockSignals(False)
        self._fill_phonemes()
        self._fill_targets()
        self._status()

    def on_load(self, *args):
        name = self.cmb_lib.currentText()
        if not name:
            return
        try:
            lib = lib_mod.load(name)
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return
        self._set_library(lib, lib_mod.library_path(name))
        self._log("[OK] Loaded '{0}': {1} phonemes, {2} targets, ref {3:g}{4}".format(
            name, len(lib.poses), len(lib.targets_used()), lib.ref_value,
            " - press Build / Update Network to apply" if self.net else ""))

    def on_save(self, *args):
        path = self.lib_path or lib_mod.library_path(self.lib.name)
        self._write(path)

    def on_save_as(self, *args):
        path, _ = QFileDialog.getSaveFileName(self, "Save Library", lib_mod.library_path(self.lib.name),
                                              "Pose library (*.json)")
        if path:
            self.lib.name = os.path.splitext(os.path.basename(path))[0]
            self._write(path)

    def _write(self, path):
        self.lib.ref_value = self.ds_ref.value()
        self.lib.clamp = self.cb_clamp.isChecked()
        try:
            lib_mod.save(self.lib, path)
        except OSError as e:
            self._log("[ERROR] Cannot save {0}: {1}".format(path, e))
            return
        self.lib_path = path
        self._refresh_libraries(keep=self.lib.name)
        self._status()
        self._log("[OK] Saved '{0}' ({1} phonemes) -> {2}".format(self.lib.name, len(self.lib.poses), path))

    def on_new(self, *args):
        name, ok = QInputDialog.getText(self, "New Library", "Name:", text="untitled")
        if ok and name.strip():
            self._set_library(lib_mod.PoseLibrary(name=name.strip(), ref_value=self.ds_ref.value()), None)
            self._log("[OK] New empty library '{0}'".format(name.strip()))

    # ================================================================== 노드망

    def on_build(self, *args):
        src, tgt = self.source(), self.target()
        if not src or not tgt:
            self._log("[ERROR] Pick a source and a target first.")
            return
        self.lib.ref_value = self.ds_ref.value()
        self.lib.clamp = self.cb_clamp.isChecked()
        try:
            net, rep = network.build(self.lib, src, tgt, on_existing=self.existing_mode())
        except (ValueError, RuntimeError) as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            return
        self.net = net
        log_report(self._log, rep, src, tgt)
        self._status()

    def on_connect_to(self, *args):
        if not self.lib.poses:
            self._log("[WARN] The library is empty.")
            return
        dlg = ConnectDialog(self.lib, self._log, self)
        dlg.exec_() if hasattr(dlg, "exec_") else dlg.exec()

    def on_remove(self, *args):
        if not self.net or not cmds.objExists(self.net):
            self._log("[WARN] No network for this source / target.")
            return
        self.stop_preview()
        n = network.remove(self.net)
        self._log("[OK] Removed network {0} ({1} node(s)). Ctrl+Z brings it back.".format(self.net, n))
        self.net = None
        self._status()
