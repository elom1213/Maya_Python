# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - Batch 탭 (PySide): 변환 결과 폴더 -> 클립 .mb N 개
#
#   Source [폴더][...][Scan]   Controller [.ma][...]   Output [폴더][...] (비면 <source>/maya)
#   표 ☑ | Clip | Start | Frames | WAV | Status     - Start 열은 클립마다 손으로 고친다(매니페스트에 남는다). 이름은 읽지 않는다.
#   Start (all) · fps(콤보, 편집 가능 · 기본 30) · Mapping · JaLi Data/Fixed · Existing(Skip/Overwrite/backup) · Copy WAV · Skip edited
#   [Run]  [Open Output]  [All] [None]
# 로직은 ../core (source_scan · manifest · jobs). 마야 일은 부모의 run_worker(job, title) 로 (mayapy 워커).

import os

from Framework.qt.qt import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QRadioButton, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QFileDialog,
    QMessageBox, QColor, QBrush, Qt, Signal,
)
from Framework.core import file_opener
from Framework.jali import mapping as mapping_mod

from ..config.version import VERSION
from ..core import source_scan, manifest, jobs

COLUMNS = ("", "Clip", "Start", "Frames", "WAV", "Status")
COL_CHECK, COL_NAME, COL_START, COL_FRAMES, COL_WAV, COL_STATUS = range(6)
TOOL_TAG = "A00560_JaliBatch {0}".format(VERSION)
STATUS_COLORS = {"failed": "#d05050", "edited": "#d0a040", "generated": "#5aa05a", "exists": "#5aa05a"}


class BatchTab(QWidget):
    generated = Signal(str)          # 출력 폴더 (Validate 탭이 받는다)

    def __init__(self, log=None, run_worker=None, prefs=None, parent=None):
        super().__init__(parent)
        self._log_cb = log
        self._run_worker = run_worker
        self._prefs = prefs or {}
        self.scan_result = None
        self.manifest = None
        self._updating = False
        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        root = QVBoxLayout(self)

        paths = QGroupBox("Paths")
        grid = QGridLayout(paths)
        self.le_source = QLineEdit()
        self.le_source.setPlaceholderText("VisemeNet Converter output folder (<name>.txt 22 columns + .visemenet.json + .wav)")
        btn_src = QPushButton("...")
        btn_src.setFixedWidth(32)
        btn_src.clicked.connect(self.on_browse_source)
        self.btn_scan = QPushButton("Scan")
        self.btn_scan.setToolTip("List the clips in the Source folder. Only 22-column VisemeNet txt files count.")
        self.btn_scan.clicked.connect(self.scan)
        self.le_controller = QLineEdit()
        self.le_controller.setPlaceholderText("JALI slider controller .ma / .mb (A0030_jali_slider_ctl_direct_arkit.ma)")
        self.le_controller.setToolTip("Referenced into every clip as namespace JALI. Keys go to DUMMY_IN_* and are baked onto the controllers.")
        btn_ctl = QPushButton("...")
        btn_ctl.setFixedWidth(32)
        btn_ctl.clicked.connect(self.on_browse_controller)
        self.le_output = QLineEdit()
        self.le_output.setPlaceholderText("<source>/maya")
        self.le_output.setToolTip("Clip .mb files, wav copies, backup/ and jali_clips.manifest.json go here.")
        btn_out = QPushButton("...")
        btn_out.setFixedWidth(32)
        btn_out.clicked.connect(self.on_browse_output)
        grid.addWidget(QLabel("Source"), 0, 0)
        grid.addWidget(self.le_source, 0, 1)
        grid.addWidget(btn_src, 0, 2)
        grid.addWidget(self.btn_scan, 0, 3)
        grid.addWidget(QLabel("Controller"), 1, 0)
        grid.addWidget(self.le_controller, 1, 1)
        grid.addWidget(btn_ctl, 1, 2)
        grid.addWidget(QLabel("Output"), 2, 0)
        grid.addWidget(self.le_output, 2, 1)
        grid.addWidget(btn_out, 2, 2)
        grid.setColumnStretch(1, 1)
        root.addWidget(paths)

        clips = QGroupBox("Clips")
        clay = QVBoxLayout(clips)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(160)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_WAV, QHeaderView.Stretch)
        for c in (COL_CHECK, COL_START, COL_FRAMES, COL_STATUS):
            header.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.setToolTip("Start = first frame of that clip (edit the cell; saved in the manifest). Frames = at the fps below.\n"
                              "Status: exists / edited (fixed by hand in A00570) / failed / - ")
        self.table.itemChanged.connect(self._on_item_changed)
        clay.addWidget(self.table)
        crow = QHBoxLayout()
        btn_all = QPushButton("All")
        btn_all.clicked.connect(lambda _=False: self.set_all_checked(True))
        btn_none = QPushButton("None")
        btn_none.clicked.connect(lambda _=False: self.set_all_checked(False))
        self.lb_info = QLabel("No clips - press Scan")
        self.lb_info.setWordWrap(True)
        crow.addWidget(btn_all)
        crow.addWidget(btn_none)
        crow.addWidget(self.lb_info, 1)
        clay.addLayout(crow)
        root.addWidget(clips, 1)

        opt = QGroupBox("Settings")
        og = QGridLayout(opt)
        self.sb_start = QSpinBox()
        self.sb_start.setRange(-100000, 100000)
        self.sb_start.setValue(1)
        self.sb_start.setToolTip("Start frame for ALL clips (fills the Start column). Edit single cells after.")
        btn_apply_start = QPushButton("Apply to all")
        btn_apply_start.clicked.connect(self.apply_start_to_all)
        self.cmb_fps = QComboBox()
        self.cmb_fps.setEditable(True)
        self.cmb_fps.addItems(jobs.FPS_CHOICES)
        self.cmb_fps.setCurrentText("30")
        self.cmb_fps.setToolTip("Scene fps of every clip (keys are sampled at this rate). Default 30 (ntsc). Type any number.")
        self.cmb_fps.currentTextChanged.connect(self._refresh_frames)
        self.cmb_mapping = QComboBox()
        self.cmb_mapping.addItems(mapping_mod.list_mappings())
        self.cmb_mapping.setToolTip("Framework/jali/mappings/*.json - model columns -> controller DUMMY_IN attributes.")
        self.cmb_mapping.currentTextChanged.connect(self._on_mapping_changed)
        og.addWidget(QLabel("Start"), 0, 0)
        srow = QHBoxLayout()
        srow.addWidget(self.sb_start)
        srow.addWidget(btn_apply_start)
        srow.addSpacing(10)
        srow.addWidget(QLabel("fps"))
        srow.addWidget(self.cmb_fps)
        srow.addSpacing(10)
        srow.addWidget(QLabel("Mapping"))
        srow.addWidget(self.cmb_mapping, 1)
        og.addLayout(srow, 0, 1)

        self.rb_jali_data = QRadioButton("From data")
        self.rb_jali_fixed = QRadioButton("Fixed")
        self.rb_jali_data.setChecked(True)
        self.rb_jali_fixed.setToolTip("Ignore the model's Jaw / Lip - key the JaLi box to fixed values (rig units, 0-1 on the slider rig).")
        self.ds_jaw = QDoubleSpinBox()
        self.ds_lip = QDoubleSpinBox()
        for w in (self.ds_jaw, self.ds_lip):
            w.setDecimals(2)
            w.setSingleStep(0.1)
            w.setRange(0.0, 15.0)
            w.setValue(0.6)
        self.rb_jali_fixed.toggled.connect(self._on_jali_mode)
        jrow = QHBoxLayout()
        jrow.addWidget(self.rb_jali_data)
        jrow.addWidget(self.rb_jali_fixed)
        jrow.addWidget(QLabel("Jaw"))
        jrow.addWidget(self.ds_jaw)
        jrow.addWidget(QLabel("Lip"))
        jrow.addWidget(self.ds_lip)
        jrow.addStretch(1)
        og.addWidget(QLabel("JaLi"), 1, 0)
        og.addLayout(jrow, 1, 1)

        self.cmb_overwrite = QComboBox()
        for label, value in jobs.OVERWRITE_LABELS:
            self.cmb_overwrite.addItem(label, value)
        self.cmb_overwrite.setToolTip("What to do when <name>.mb already exists. Backup = backup/<name>_NN.mb first.")
        self.cb_copy_wav = QCheckBox("Copy WAV next to clip")
        self.cb_copy_wav.setChecked(True)
        self.cb_copy_wav.setToolTip("The sound node points at a copy in the output folder, so the folder can move as one.")
        self.cb_skip_edited = QCheckBox("Keep edited clips")
        self.cb_skip_edited.setChecked(True)
        self.cb_skip_edited.setToolTip("Clips marked 'edited' (keys fixed by hand in A00570) are not overwritten.")
        erow = QHBoxLayout()
        erow.addWidget(self.cmb_overwrite)
        erow.addWidget(self.cb_copy_wav)
        erow.addWidget(self.cb_skip_edited)
        erow.addStretch(1)
        og.addWidget(QLabel("Existing"), 2, 0)
        og.addLayout(erow, 2, 1)
        og.setColumnStretch(1, 1)
        root.addWidget(opt)

        brow = QHBoxLayout()
        self.btn_run = QPushButton("Run")
        self.btn_run.setMinimumHeight(32)
        self.btn_run.setToolTip("Generate the checked clips with mayapy (one process, Cancel stops after the current clip).")
        self.btn_run.clicked.connect(self.run)
        btn_open = QPushButton("Open Output Folder")
        btn_open.clicked.connect(self.on_open_output)
        brow.addWidget(self.btn_run, 2)
        brow.addWidget(btn_open, 1)
        root.addLayout(brow)
        self._on_jali_mode()
        self._on_mapping_changed()

    # ------------------------------------------------------------------ helpers

    def _log(self, message):
        if self._log_cb:
            self._log_cb(message)

    def source_dir(self):
        return os.path.normpath(self.le_source.text().strip()) if self.le_source.text().strip() else ""

    def output_dir(self):
        text = self.le_output.text().strip()
        if text:
            return os.path.normpath(text)
        src = self.source_dir()
        return os.path.join(src, "maya") if src else ""

    def controller(self):
        return os.path.normpath(self.le_controller.text().strip()) if self.le_controller.text().strip() else ""

    def fps(self):
        return jobs.parse_fps(self.cmb_fps.currentText())

    def overwrite_policy(self):
        return self.cmb_overwrite.currentData()

    def set_overwrite_policy(self, value):
        i = self.cmb_overwrite.findData(value)
        if i >= 0:
            self.cmb_overwrite.setCurrentIndex(i)

    def _on_jali_mode(self, *args):
        fixed = self.rb_jali_fixed.isChecked()
        self.ds_jaw.setEnabled(fixed)
        self.ds_lip.setEnabled(fixed)

    def _on_mapping_changed(self, *args):
        name = self.cmb_mapping.currentText()
        if not name:
            return
        try:
            mp = mapping_mod.load_mapping(name)
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return
        lo, hi = mp["jali"]["range"]
        for w, v in ((self.ds_jaw, mp["jali"]["fixed_default"][0]), (self.ds_lip, mp["jali"]["fixed_default"][1])):
            w.setRange(lo, hi)
            w.setValue(v)

    # ------------------------------------------------------------------ prefs

    def load_prefs(self, p):
        self.le_source.setText(p.get("source_dir", ""))
        self.le_controller.setText(p.get("controller", ""))
        self.le_output.setText(p.get("output_dir", ""))
        self.cmb_fps.setCurrentText(str(p.get("fps", "30")))
        self.sb_start.setValue(int(p.get("default_start", 1)))
        if p.get("mapping") and self.cmb_mapping.findText(p["mapping"]) >= 0:
            self.cmb_mapping.setCurrentText(p["mapping"])
        (self.rb_jali_fixed if p.get("jali_mode") == jobs.JALI_FIXED else self.rb_jali_data).setChecked(True)
        fixed = p.get("jali_fixed") or [0.6, 0.6]
        self.ds_jaw.setValue(float(fixed[0]))
        self.ds_lip.setValue(float(fixed[1]))
        self.set_overwrite_policy(p.get("overwrite", jobs.OVERWRITE_SKIP))
        self.cb_copy_wav.setChecked(bool(p.get("copy_wav", True)))
        self.cb_skip_edited.setChecked(bool(p.get("skip_edited", True)))

    def save_prefs(self, p):
        p["source_dir"] = self.le_source.text().strip()
        p["controller"] = self.le_controller.text().strip()
        p["output_dir"] = self.le_output.text().strip()
        p["fps"] = self.cmb_fps.currentText().strip()
        p["default_start"] = self.sb_start.value()
        p["mapping"] = self.cmb_mapping.currentText()
        p["jali_mode"] = jobs.JALI_FIXED if self.rb_jali_fixed.isChecked() else jobs.JALI_DATA
        p["jali_fixed"] = [self.ds_jaw.value(), self.ds_lip.value()]
        p["overwrite"] = self.overwrite_policy()
        p["copy_wav"] = self.cb_copy_wav.isChecked()
        p["skip_edited"] = self.cb_skip_edited.isChecked()

    # ------------------------------------------------------------------ browse

    def on_browse_source(self, *args):
        path = QFileDialog.getExistingDirectory(self, "VisemeNet Converter output folder", self.source_dir() or "")
        if path:
            self.le_source.setText(os.path.normpath(path))
            self.scan()

    def on_browse_controller(self, *args):
        start = os.path.dirname(self.controller()) if self.controller() else ""
        path, _ = QFileDialog.getOpenFileName(self, "JALI controller", start, "Maya scene (*.ma *.mb);;All files (*.*)")
        if path:
            self.le_controller.setText(os.path.normpath(path))

    def on_browse_output(self, *args):
        path = QFileDialog.getExistingDirectory(self, "Clip output folder", self.output_dir() or self.source_dir() or "")
        if path:
            self.le_output.setText(os.path.normpath(path))
            self._load_manifest()
            self._refresh_status()

    def on_open_output(self, *args):
        out = self.output_dir()
        if not out or not os.path.isdir(out):
            self._log("[WARN] Output folder does not exist yet: {0}".format(out))
            return
        try:
            file_opener.open_path(out)
        except (OSError, ValueError) as e:
            self._log("[WARN] {0}".format(e))

    # ------------------------------------------------------------------ Scan · 표

    def set_source(self, path):
        self.le_source.setText(os.path.normpath(path))

    def _load_manifest(self):
        out = self.output_dir()
        try:
            self.manifest = manifest.load(out, VERSION) if out else manifest.empty(VERSION)
        except ValueError as e:
            self._log("[WARN] {0} - starting a new manifest".format(e))
            self.manifest = manifest.empty(VERSION)

    def scan(self, *args):
        src = self.source_dir()
        try:
            self.scan_result = source_scan.scan(src)
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            self.scan_result = None
            self.table.setRowCount(0)
            self.lb_info.setText("No clips")
            return
        self._load_manifest()
        res = self.scan_result
        for fname, why in res.skipped:
            self._log("[INFO] {0}: skipped - {1}".format(fname, why))
        for clip in res.clips:
            for level, msg in clip.problems:
                self._log("[{0}] {1}: {2}".format(level, clip.name, msg))
        if res.hint:
            self._log("[WARN] {0}".format(res.hint))
        self._fill_table()
        self._log("[OK] Scan: {0} in {1}".format(res.summary(), src))

    def _fill_table(self):
        res = self.scan_result
        self._updating = True
        try:
            self.table.setRowCount(0)
            if res is None:
                self.lb_info.setText("No clips")
                return
            default = self.sb_start.value()
            self.table.setRowCount(len(res.clips))
            for i, clip in enumerate(res.clips):
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                chk.setCheckState(Qt.Checked if clip.ok else Qt.Unchecked)
                if not clip.ok:
                    chk.setFlags(Qt.ItemIsSelectable)
                name = QTableWidgetItem(clip.name)
                name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                name.setToolTip(clip.txt + ("\n" + "\n".join("{0}: {1}".format(l, m) for l, m in clip.problems) if clip.problems else ""))
                start = QTableWidgetItem(str(manifest.start_of(self.manifest, clip.name, default)))
                start.setTextAlignment(Qt.AlignCenter)
                frames = QTableWidgetItem("")
                frames.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                frames.setTextAlignment(Qt.AlignCenter)
                wav = QTableWidgetItem(os.path.basename(clip.wav) if clip.wav else "(none)")
                wav.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                wav.setToolTip(clip.wav or "no WAV - excluded")
                status = QTableWidgetItem("")
                status.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                status.setTextAlignment(Qt.AlignCenter)
                for c, item in enumerate((chk, name, start, frames, wav, status)):
                    self.table.setItem(i, c, item)
                if not clip.ok:
                    for c in range(len(COLUMNS)):
                        self.table.item(i, c).setForeground(QBrush(QColor("#d05050")))
        finally:
            self._updating = False
        self._refresh_frames()
        self._refresh_status()

    def _refresh_frames(self, *args):
        if self.scan_result is None or self._updating:
            return
        try:
            fps = self.fps()
        except ValueError:
            return
        total = 0
        for i, clip in enumerate(self.scan_result.clips):
            n = clip.frames(fps)
            total += n
            self.table.item(i, COL_FRAMES).setText(str(n))
        self.lb_info.setText("{0} - {1} clip(s) checked, {2} frames total at {3:g} fps".format(
            self.scan_result.summary(), len(self.checked_rows()), total, fps))

    def _refresh_status(self):
        if self.scan_result is None or self.manifest is None:
            return
        out = self.output_dir()
        for i, clip in enumerate(self.scan_result.clips):
            st = manifest.status_of(self.manifest, clip.name)
            exists = bool(out) and os.path.isfile(os.path.join(out, clip.name + ".mb"))
            text = st if st in ("edited", "failed") else ("exists" if exists else "-")
            item = self.table.item(i, COL_STATUS)
            item.setText(text)
            color = STATUS_COLORS.get(text)
            item.setForeground(QBrush(QColor(color)) if color else QBrush())
            err = (manifest.clip(self.manifest, clip.name) or {}).get("error", "")
            item.setToolTip(err or "")

    def _on_item_changed(self, item):
        if self._updating or item.column() not in (COL_START, COL_CHECK):
            return
        if item.column() == COL_START:
            try:
                int(item.text())
            except ValueError:
                self._updating = True
                item.setText(str(self.sb_start.value()))
                self._updating = False
                self._log("[WARN] Start must be an integer frame.")
        self._refresh_frames()

    def apply_start_to_all(self, *args):
        self._updating = True
        for i in range(self.table.rowCount()):
            self.table.item(i, COL_START).setText(str(self.sb_start.value()))
        self._updating = False
        self._refresh_frames()

    def set_all_checked(self, checked):
        self._updating = True
        for i in range(self.table.rowCount()):
            item = self.table.item(i, COL_CHECK)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self._updating = False
        self._refresh_frames()

    def checked_rows(self):
        return [i for i in range(self.table.rowCount()) if self.table.item(i, COL_CHECK).checkState() == Qt.Checked]

    def start_of_row(self, row):
        return int(self.table.item(row, COL_START).text())

    def set_start_of_row(self, row, value):
        self.table.item(row, COL_START).setText(str(int(value)))

    # ------------------------------------------------------------------ Run

    def build_job(self, rows=None):
        """체크된 클립으로 generate job. 문제가 있으면 ValueError. edited 클립은 Keep edited 가 켜져 있으면 뺀다."""
        if self.scan_result is None:
            raise ValueError("Press Scan first")
        rows = self.checked_rows() if rows is None else rows
        out = self.output_dir()
        ctl = self.controller()
        if not ctl or not os.path.isfile(ctl):
            raise ValueError("Controller file not found: {0}".format(ctl or "(empty)"))
        fps = self.fps()
        clips = []
        kept = []
        for i in rows:
            clip = self.scan_result.clips[i]
            if not clip.ok:
                continue
            if self.cb_skip_edited.isChecked() and manifest.status_of(self.manifest, clip.name) == manifest.STATUS_EDITED:
                kept.append(clip.name)
                continue
            clips.append(clip.as_job_clip(self.start_of_row(i), out))
        if kept:
            self._log("[INFO] Kept {0} edited clip(s): {1}".format(len(kept), ", ".join(kept)))
        job = jobs.generate_job(ctl, self.cmb_mapping.currentText(), fps, self.sb_start.value(),
                                jobs.JALI_FIXED if self.rb_jali_fixed.isChecked() else jobs.JALI_DATA,
                                (self.ds_jaw.value(), self.ds_lip.value()), None, None, self.overwrite_policy(),
                                self.cb_copy_wav.isChecked(), out, manifest.path_for(out), TOOL_TAG, clips)
        return job

    def _confirm_edited_overwrite(self, job):
        """Keep edited 가 꺼진 채 edited 클립을 덮으려 하면 한 번 더 묻는다 (평가서 §2-8)."""
        if job["overwrite"] == jobs.OVERWRITE_SKIP:
            return True
        names = manifest.edited_names(self.manifest, [c["name"] for c in job["clips"]])
        if not names:
            return True
        answer = QMessageBox.question(
            self, "Overwrite edited clips?",
            "{0} clip(s) were edited by hand (status 'edited'):\n\n{1}\n\nOverwriting them throws those edits away. Continue?".format(
                len(names), "\n".join(names)), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return answer == QMessageBox.Yes

    def run(self, *args):
        try:
            job = self.build_job()
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return None
        if not self._confirm_edited_overwrite(job):
            self._log("Run cancelled.")
            return None
        out = job["out_dir"]
        # 매니페스트: 설정 + 표의 Start 를 먼저 적는다 (워커가 클립마다 상태를 더한다)
        manifest.set_settings(self.manifest, {"controller": job["controller"], "mapping": job["mapping"], "fps": job["fps"],
                                              "default_start": job["default_start"], "jali": job["jali"],
                                              "copy_wav": job["copy_wav"], "tool": TOOL_TAG})
        for c in job["clips"]:
            manifest.update_clip(self.manifest, c["name"], start=c["start"], txt=c["txt"], wav=c["wav"])
        try:
            manifest.save(out, self.manifest)
        except OSError as e:
            self._log("[ERROR] Cannot write to the output folder: {0}".format(e))
            return None
        self._log("Run: {0} clip(s) -> {1}".format(len(job["clips"]), out))
        outcome = self._run_worker(job, "JALI Batch - Generate") if self._run_worker else None
        if outcome is None:
            return None
        summary = outcome.result
        if outcome.error and summary is None:
            self._log("[ERROR] Generate failed : {0}".format(outcome.error))
        if summary:
            tag = "[OK]" if not summary["failed"] and not summary["cancelled"] else "[WARN]"
            self._log("{0} Generate done - {1} generated, {2} skipped, {3} failed{4}.".format(
                tag, summary["generated"], summary["skipped"], summary["failed"],
                " (cancelled)" if summary["cancelled"] else ""))
            self.generated.emit(out)
        self._load_manifest()
        self._refresh_status()
        return outcome
