# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00540_JaliLipSync - Qt UI (in-Maya)
#
# JUN_JALI 의 VisemeNet Converter 가 만든 txt(+json) 와 음성 wav 를 골라 JALI 리그에 키를 건다.
#   Data    : Viseme TXT / Audio WAV (txt 를 고르면 json 의 source_wav 또는 같은 이름 wav 를 자동으로)
#   Target  : 리그(네임스페이스) 콤보 + 매핑 json 콤보
#   Options : 시작 프레임 · 비짐 배율 · JaLi(데이터 / 고정) · 오디오 붙이기 · 재생 범위
#   Apply / Remove Keys / Select Controls + 로그
# 모든 UI 문자열 · 로그는 영어. 계획: JUN_JALI/docs/0030_tool_plan.md §5

import os

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.core import file_opener

from tools.A00540_JaliLipSync.app.config.version import VERSION, LAST_UPDATE
from tools.A00540_JaliLipSync.app.core import lipsync_data, mapping as mapping_mod, keyer, scene


WINDOW_OBJECT_NAME = "JUN_A00540_JaliLipSync_window"
OPT_LAST_DIR = "JUN_A00540_lastDir"
GUIDE_DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))), "docs", "A00540_JaliLipSync.md")


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("JALI LipSync v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(460, 620)

        self._data = None
        self._build_ui()
        self.on_refresh_rigs()
        self._log("[INFO] Pick a VisemeNet TXT (from the JUN_JALI VisemeNet Converter).")

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Open Guide", self.on_open_guide)
        help_menu.addAction("About", self.show_about)
        layout.setMenuBar(self.menu_bar)

        # --- Data
        data_box = QGroupBox("Data")
        grid = QGridLayout(data_box)
        self.le_txt = QLineEdit()
        self.le_txt.setPlaceholderText("<name>.txt from VisemeNet Converter")
        self.le_txt.editingFinished.connect(self._on_txt_edited)
        btn_txt = QPushButton("...")
        btn_txt.setFixedWidth(32)
        btn_txt.clicked.connect(self.on_browse_txt)
        self.le_wav = QLineEdit()
        self.le_wav.setPlaceholderText("Optional - the same speech (44.1 kHz WAV)")
        btn_wav = QPushButton("...")
        btn_wav.setFixedWidth(32)
        btn_wav.clicked.connect(self.on_browse_wav)
        grid.addWidget(QLabel("Viseme TXT"), 0, 0)
        grid.addWidget(self.le_txt, 0, 1)
        grid.addWidget(btn_txt, 0, 2)
        grid.addWidget(QLabel("Audio WAV"), 1, 0)
        grid.addWidget(self.le_wav, 1, 1)
        grid.addWidget(btn_wav, 1, 2)
        self.lb_info = QLabel("No data")
        self.lb_info.setWordWrap(True)
        grid.addWidget(self.lb_info, 2, 0, 1, 3)
        layout.addWidget(data_box)

        # --- Target
        tgt_box = QGroupBox("Target")
        tgrid = QGridLayout(tgt_box)
        self.cmb_rig = QComboBox()
        self.cmb_rig.setToolTip("Namespaces that contain CNT_PHONEMES (a JALI rig).")
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.on_refresh_rigs)
        self.cmb_mapping = QComboBox()
        self.cmb_mapping.addItems(mapping_mod.list_mappings())
        self.cmb_mapping.setToolTip("Model columns -> rig attributes (app/mappings/*.json).")
        tgrid.addWidget(QLabel("Rig"), 0, 0)
        tgrid.addWidget(self.cmb_rig, 0, 1)
        tgrid.addWidget(btn_refresh, 0, 2)
        tgrid.addWidget(QLabel("Mapping"), 1, 0)
        tgrid.addWidget(self.cmb_mapping, 1, 1, 1, 2)
        layout.addWidget(tgt_box)

        # --- Options
        opt_box = QGroupBox("Options")
        ogrid = QGridLayout(opt_box)
        self.sb_start = QSpinBox()
        self.sb_start.setRange(-100000, 100000)
        self.sb_start.setValue(1)
        self.ds_scale = QDoubleSpinBox()
        self.ds_scale.setRange(0.0, 12.0)
        self.ds_scale.setSingleStep(0.5)
        self.ds_scale.setValue(10.0)
        self.ds_scale.setToolTip("Model values (0-1) x this = viseme keys. Rig maximum is 12; 10 = original.")
        ogrid.addWidget(QLabel("Start frame"), 0, 0)
        ogrid.addWidget(self.sb_start, 0, 1)
        ogrid.addWidget(QLabel("Viseme scale"), 0, 2)
        ogrid.addWidget(self.ds_scale, 0, 3)

        self.rb_jali_data = QRadioButton("From data")
        self.rb_jali_fixed = QRadioButton("Fixed")
        self.rb_jali_data.setChecked(True)
        self.rb_jali_fixed.setToolTip("Do not use the model's Jaw / Lip curves - key CNT_JaLi to fixed values.\n"
                                      "Viseme timing stays from the data, the speaking style is yours.")
        self.ds_jaw = QDoubleSpinBox()
        self.ds_lip = QDoubleSpinBox()
        for w in (self.ds_jaw, self.ds_lip):
            w.setRange(0.0, 15.0)
            w.setValue(9.0)
            w.setEnabled(False)
        self.rb_jali_fixed.toggled.connect(lambda on: (self.ds_jaw.setEnabled(on), self.ds_lip.setEnabled(on)))
        jrow = QHBoxLayout()
        jrow.addWidget(self.rb_jali_data)
        jrow.addWidget(self.rb_jali_fixed)
        jrow.addWidget(QLabel("Jaw"))
        jrow.addWidget(self.ds_jaw)
        jrow.addWidget(QLabel("Lip"))
        jrow.addWidget(self.ds_lip)
        ogrid.addWidget(QLabel("JaLi"), 1, 0)
        ogrid.addLayout(jrow, 1, 1, 1, 3)

        self.cb_audio = QCheckBox("Attach audio")
        self.cb_audio.setChecked(True)
        self.cb_range = QCheckBox("Set playback range")
        self.cb_range.setChecked(True)
        ogrid.addWidget(self.cb_audio, 2, 1)
        ogrid.addWidget(self.cb_range, 2, 2, 1, 2)
        layout.addWidget(opt_box)

        # --- 버튼
        row = QHBoxLayout()
        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setMinimumHeight(32)
        self.btn_apply.clicked.connect(self.on_apply)
        btn_remove = QPushButton("Remove Keys")
        btn_remove.setToolTip("Delete the keys of every mapped attribute in the data range.")
        btn_remove.clicked.connect(self.on_remove)
        btn_select = QPushButton("Select Controls")
        btn_select.clicked.connect(self.on_select_controls)
        row.addWidget(self.btn_apply, 2)
        row.addWidget(btn_remove, 1)
        row.addWidget(btn_select, 1)
        layout.addLayout(row)

        log_box = QGroupBox("Log")
        log_layout = QVBoxLayout(log_box)
        self.log_view = JUN_mod_log_qt_v01(window_title="JALI LipSync - Log",
                                           object_name="JUN_A00540_JaliLipSync_log_window")
        self.log_view.setMinimumHeight(140)
        log_layout.addWidget(self.log_view)
        layout.addWidget(log_box, 1)

    # ------------------------------------------------------------------ 도우미

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _last_dir(self):
        if cmds.optionVar(exists=OPT_LAST_DIR):
            return cmds.optionVar(q=OPT_LAST_DIR)
        return ""

    def _namespace(self):
        text = self.cmb_rig.currentText()
        return "" if text in ("", "(root)") else text

    def _mapping(self):
        name = self.cmb_mapping.currentText()
        if not name:
            raise ValueError("No mapping json in app/mappings")
        return mapping_mod.load_mapping(name)

    # ------------------------------------------------------------------ Data

    def on_browse_txt(self, *args):
        path, _ = QFileDialog.getOpenFileName(self, "Viseme TXT", self._last_dir(),
                                              "VisemeNet output (*.txt);;All files (*.*)")
        if path:
            cmds.optionVar(sv=(OPT_LAST_DIR, os.path.dirname(path)))
            self.le_txt.setText(os.path.normpath(path))
            self._load_txt(auto_wav=True)

    def _on_txt_edited(self):
        if self.le_txt.text().strip() and (self._data is None or
                                           os.path.normpath(self._data.txt_path) != os.path.normpath(self.le_txt.text().strip())):
            self._load_txt(auto_wav=not self.le_wav.text().strip())

    def on_browse_wav(self, *args):
        start = os.path.dirname(self.le_txt.text()) or self._last_dir()
        path, _ = QFileDialog.getOpenFileName(self, "Audio WAV", start, "WAV (*.wav);;All files (*.*)")
        if path:
            self.le_wav.setText(os.path.normpath(path))
            self._update_info()

    def _load_txt(self, auto_wav):
        path = self.le_txt.text().strip()
        try:
            self._data = lipsync_data.load(path)
        except ValueError as e:
            self._data = None
            self.lb_info.setText("No data")
            self._log("[ERROR] {0}".format(e))
            return
        if auto_wav:
            wav = lipsync_data.find_wav(path, self._data)
            self.le_wav.setText(os.path.normpath(wav) if wav else "")
            if wav:
                self._log("[INFO] Audio found: {0}".format(wav))
            else:
                self._log("[WARN] No matching WAV found - pick it with '...' (optional).")
        self._log("[OK] {0}: {1} rows ({2:.2f} s @ {3:g} fps){4}".format(
            os.path.basename(path), len(self._data.rows), self._data.seconds, self._data.fps,
            " + json" if self._data.meta else ""))
        self._update_info()

    def _update_info(self):
        if self._data is None:
            self.lb_info.setText("No data")
            return
        fps = keyer.scene_fps()
        frames = int(self._data.seconds * fps)
        text = "{0} rows = {1:.2f} s -> {2} frames at {3:g} fps".format(
            len(self._data.rows), self._data.seconds, frames, fps)
        wav = self.le_wav.text().strip()
        if wav:
            sec = lipsync_data.wav_seconds(wav)
            if sec is None:
                text += "  |  WAV: cannot read length"
            else:
                text += "  |  WAV {0:.2f} s".format(sec)
                gap = sec - self._data.seconds
                if gap > 0.5 or gap < -0.05:
                    text += " (check the pair: {0:+.2f} s)".format(gap)
        self.lb_info.setText(text)

    # ------------------------------------------------------------------ Target

    def on_refresh_rigs(self, *args):
        current = self.cmb_rig.currentText()
        rigs = scene.find_rigs()
        self.cmb_rig.clear()
        for ns in rigs:
            self.cmb_rig.addItem(ns or "(root)")
        if current and self.cmb_rig.findText(current) >= 0:
            self.cmb_rig.setCurrentText(current)
        if not rigs:
            self._log("[WARN] No JALI rig (CNT_PHONEMES) in the scene.")

    # ------------------------------------------------------------------ 실행

    def on_apply(self, *args):
        if self._data is None:
            if self.le_txt.text().strip():
                self._load_txt(auto_wav=not self.le_wav.text().strip())
            if self._data is None:
                self._log("[ERROR] No viseme data - pick a TXT first.")
                return
        if self.cmb_rig.count() == 0:
            self.on_refresh_rigs()
            if self.cmb_rig.count() == 0:
                self._log("[ERROR] No JALI rig in the scene.")
                return
        try:
            mapping = self._mapping()
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return

        ns = self._namespace()
        start = self.sb_start.value()
        jali = (self.ds_jaw.value(), self.ds_lip.value()) if self.rb_jali_fixed.isChecked() else None
        wav = self.le_wav.text().strip()
        if wav and not os.path.isfile(wav):
            self._log("[ERROR] WAV not found: {0}".format(wav))
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            res = keyer.apply(self._data, mapping, ns, start, viseme_scale=self.ds_scale.value(), jali_fixed=jali)
            if self.cb_range.isChecked():
                cmds.playbackOptions(minTime=res["start"], maxTime=res["end"])
            if wav and self.cb_audio.isChecked():
                node = scene.attach_sound(wav, start)
                self._log("[OK] Audio '{0}' at frame {1}".format(node, start))
        except keyer.KeyingError as e:
            self._log("[ERROR] {0}".format(e))
            return
        except RuntimeError as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            return
        finally:
            QApplication.restoreOverrideCursor()

        self._log("[DONE] {0} attributes keyed on '{1}': frames {2}-{3} @ {4:g} fps ({5} keys, JaLi {6})".format(
            res["attrs"], ns or "(root)", res["start"], res["end"], res["fps"], res["keys"],
            "fixed {0:g} / {1:g}".format(*jali) if jali else "from data"))
        self._log("[INFO] The model output ends about 0.32 s before the audio (VisemeNet limit).")

    def on_remove(self, *args):
        try:
            mapping = self._mapping()
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return
        if self._data is not None:
            start = self.sb_start.value()
            end = start + int(self._data.seconds * keyer.scene_fps())
            n = keyer.remove(mapping, self._namespace(), start, end)
            self._log("[OK] Removed keys on {0} attribute(s), frames {1}-{2}".format(n, start, end))
        else:
            n = keyer.remove(mapping, self._namespace())
            self._log("[OK] Removed all keys on {0} attribute(s)".format(n))

    def on_select_controls(self, *args):
        try:
            nodes = [n for n in keyer.controls(self._mapping(), self._namespace()) if cmds.objExists(n)]
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return
        if nodes:
            cmds.select(nodes)
            self._log("[OK] Selected {0}".format(", ".join(nodes)))
        else:
            self._log("[WARN] Controls not found in the scene.")

    # ------------------------------------------------------------------ Help

    def on_open_guide(self, *args):
        try:
            file_opener.open_path(GUIDE_DOC)
        except (OSError, ValueError):
            self._log("[WARN] Guide not found: {0}".format(GUIDE_DOC))

    def show_about(self, *args):
        QMessageBox.information(self, "About", (
            "JALI LipSync v{0}\nUpdate date: {1}\n\n"
            "Keys VisemeNet viseme curves onto a JALI rig\n"
            "(CNT_JaLi / CNT_PHONEMES / CNT_COARTIC).\n\n"
            "1. Make the TXT with VisemeNet Converter (JUN_JALI).\n"
            "2. Pick the TXT - the WAV is found from the .visemenet.json\n"
            "   or a file with the same name.\n"
            "3. Pick the rig and press Apply (one undo step).\n\n"
            "Keys are sampled at the scene fps. Re-applying clears the range first.\n"
            "New rigs = a new json in app/mappings.\n\n"
            "Written by Ji Hun Park.").format(VERSION, LAST_UPDATE))
