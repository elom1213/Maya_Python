# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# A00540_JaliLipSync - Qt UI (in-Maya)
#
# JUN_JALI 의 VisemeNet Converter 가 만든 txt(+json) 와 음성 wav 를 골라 JALI 리그에 키를 건다.
#   Data    : Viseme TXT / Audio WAV (txt 를 고르면 json 의 source_wav 또는 같은 이름 wav 를 자동으로)
#   Target  : Auto(리그 네임스페이스 콤보 — 매핑 json 의 phonemes 노드를 표식으로 찾는다)
#             / Manual(역할 3칸 Phonemes · Coartic · JaLi 를 씬 선택으로 채움, 빈 역할은 건너뜀) + 매핑 json 콤보
#   Options : 시작 프레임 · 비짐 배율 · JaLi(데이터 + JaLi 배율 / 고정 Jaw Lip) · 오디오 붙이기 · 재생 범위
#             배율 · Fixed 범위의 기본값은 매핑 json 이 정하고, 매핑을 바꾸면 스핀박스가 리셋된다.
#   Apply / Remove Keys / Select Controls + 로그
# 모든 UI 문자열 · 로그는 영어. 계획: JUN_JALI/docs/0030_tool_plan.md §5, docs/plans/A00540_JaliLipSync_v0101_rules_manual_plan.md

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
ROLE_LABELS = (("phonemes", "Phonemes"), ("coartic", "Coartic"), ("jali", "JaLi"))


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("JALI LipSync v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(480, 700)

        self._data = None
        self._build_ui()
        self.on_mapping_changed()
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
        self.rb_auto = QRadioButton("Auto")
        self.rb_manual = QRadioButton("Manual")
        self.rb_auto.setChecked(True)
        self.rb_auto.setToolTip("Find the rig by the mapping's phonemes node (namespaces listed in Rig).")
        self.rb_manual.setToolTip("Pick the nodes yourself (any names). Empty roles are skipped.")
        self.rb_manual.toggled.connect(self._on_mode_changed)

        self.cmb_rig = QComboBox()
        self.cmb_rig.setToolTip("Namespaces that contain the mapping's phonemes node.")
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.on_refresh_rigs)
        tgrid.addWidget(self.rb_auto, 0, 0)
        tgrid.addWidget(QLabel("Rig"), 0, 1)
        tgrid.addWidget(self.cmb_rig, 0, 2)
        tgrid.addWidget(self.btn_refresh, 0, 3)

        self.le_roles = {}
        self.manual_widgets = []
        for i, (role, label) in enumerate(ROLE_LABELS):
            le = QLineEdit()
            le.setToolTip("Node that has the {0} attributes of the mapping. Empty = skip this role.".format(label))
            btn_sel = QPushButton("<< Sel")
            btn_sel.setToolTip("Use the first selected node")
            btn_sel.clicked.connect(lambda _=False, r=role: self.on_pick_role(r))
            btn_clear = QPushButton("x")
            btn_clear.setFixedWidth(24)
            btn_clear.clicked.connect(lambda _=False, w=le: w.clear())
            row = 1 + i
            if i == 0:
                tgrid.addWidget(self.rb_manual, row, 0)
            lb = QLabel(label)
            tgrid.addWidget(lb, row, 1)
            tgrid.addWidget(le, row, 2)
            hb = QHBoxLayout()
            hb.setContentsMargins(0, 0, 0, 0)
            hb.addWidget(btn_sel)
            hb.addWidget(btn_clear)
            tgrid.addLayout(hb, row, 3)
            self.le_roles[role] = le
            self.manual_widgets += [lb, le, btn_sel, btn_clear]

        self.cmb_mapping = QComboBox()
        self.cmb_mapping.addItems(mapping_mod.list_mappings())
        self.cmb_mapping.setToolTip("Model columns -> rig attributes (app/mappings/*.json). "
                                    "Sets the default scales and the JaLi Fixed range.")
        self.cmb_mapping.currentTextChanged.connect(self.on_mapping_changed)
        tgrid.addWidget(QLabel("Mapping"), 4, 1)
        tgrid.addWidget(self.cmb_mapping, 4, 2, 1, 2)
        tgrid.setColumnStretch(2, 1)
        layout.addWidget(tgt_box)

        # --- Options
        opt_box = QGroupBox("Options")
        ogrid = QGridLayout(opt_box)
        self.sb_start = QSpinBox()
        self.sb_start.setRange(-100000, 100000)
        self.sb_start.setValue(1)
        self.ds_scale = QDoubleSpinBox()
        self.ds_scale.setRange(0.0, 100.0)
        self.ds_scale.setDecimals(2)
        self.ds_scale.setSingleStep(0.1)
        self.ds_scale.setToolTip("Model values (0-1) x this = viseme keys. Default comes from the mapping.")
        ogrid.addWidget(QLabel("Start frame"), 0, 0)
        ogrid.addWidget(self.sb_start, 0, 1)
        ogrid.addWidget(QLabel("Viseme scale"), 0, 2)
        ogrid.addWidget(self.ds_scale, 0, 3)

        self.rb_jali_data = QRadioButton("From data")
        self.rb_jali_fixed = QRadioButton("Fixed")
        self.rb_jali_data.setChecked(True)
        self.rb_jali_fixed.setToolTip("Do not use the model's Jaw / Lip curves - key the JaLi node to fixed values.\n"
                                      "Viseme timing stays from the data, the speaking style is yours.")
        self.ds_jali_scale = QDoubleSpinBox()
        self.ds_jali_scale.setRange(0.0, 100.0)
        self.ds_jali_scale.setDecimals(2)
        self.ds_jali_scale.setSingleStep(0.1)
        self.ds_jali_scale.setToolTip("Model Jaw / Lip (0-1) x this = JaLi keys. Default comes from the mapping.")
        self.ds_jaw = QDoubleSpinBox()
        self.ds_lip = QDoubleSpinBox()
        for w in (self.ds_jaw, self.ds_lip):
            w.setDecimals(2)
            w.setSingleStep(0.1)
            w.setEnabled(False)
        self.rb_jali_fixed.toggled.connect(self._on_jali_mode_changed)
        jrow = QHBoxLayout()
        jrow.addWidget(self.rb_jali_data)
        jrow.addWidget(QLabel("JaLi scale"))
        jrow.addWidget(self.ds_jali_scale)
        jrow.addSpacing(8)
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

        self._on_mode_changed()
        self._on_jali_mode_changed()

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

    def is_manual(self):
        return self.rb_manual.isChecked()

    def _node_map(self):
        """Manual 모드면 {역할: 노드 이름 또는 None}, Auto 면 None."""
        if not self.is_manual():
            return None
        return {role: (le.text().strip() or None) for role, le in self.le_roles.items()}

    def _target_desc(self, node_map):
        if node_map is None:
            return self._namespace() or "(root)"
        return ", ".join("{0}={1}".format(r, n) for r, n in node_map.items() if n)

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

    def _on_mode_changed(self, *args):
        manual = self.is_manual()
        self.cmb_rig.setEnabled(not manual)
        self.btn_refresh.setEnabled(not manual)
        for w in self.manual_widgets:
            w.setEnabled(manual)

    def _on_jali_mode_changed(self, *args):
        fixed = self.rb_jali_fixed.isChecked()
        self.ds_jali_scale.setEnabled(not fixed)
        self.ds_jaw.setEnabled(fixed)
        self.ds_lip.setEnabled(fixed)

    def on_mapping_changed(self, *args):
        """매핑 json 의 기본값으로 배율 · Fixed 범위를 리셋하고 Manual 칸의 플레이스홀더를 채운다."""
        try:
            mapping = self._mapping()
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return
        jali = mapping["jali"]
        self.ds_scale.setValue(mapping["viseme_scale"])
        self.ds_jali_scale.setValue(jali["scale"])
        lo, hi = jali["range"]
        for w, val in ((self.ds_jaw, jali["fixed_default"][0]), (self.ds_lip, jali["fixed_default"][1])):
            w.setRange(lo, hi)
            w.setValue(val)
        for role, le in self.le_roles.items():
            le.setPlaceholderText(mapping["nodes"].get(role, "(not in this mapping)"))
        self._log("[INFO] Mapping '{0}': viseme scale {1:g}, JaLi scale {2:g}, Jaw/Lip {3:g}-{4:g}".format(
            mapping["name"], mapping["viseme_scale"], jali["scale"], lo, hi))
        self.on_refresh_rigs()

    def on_refresh_rigs(self, *args):
        current = self.cmb_rig.currentText()
        try:
            marker = scene.marker_of(self._mapping())
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return
        rigs = scene.find_rigs(marker)
        self.cmb_rig.clear()
        for ns in rigs:
            self.cmb_rig.addItem(ns or "(root)")
        if current and self.cmb_rig.findText(current) >= 0:
            self.cmb_rig.setCurrentText(current)
        if not rigs:
            self._log("[WARN] No rig with '{0}' in the scene (Auto). Use Manual to pick nodes.".format(marker))

    def on_pick_role(self, role):
        sel = cmds.ls(selection=True, long=False) or []
        if not sel:
            self._log("[WARN] Select a node first.")
            return
        self.le_roles[role].setText(sel[0])

    # ------------------------------------------------------------------ 실행

    def on_apply(self, *args):
        if self._data is None:
            if self.le_txt.text().strip():
                self._load_txt(auto_wav=not self.le_wav.text().strip())
            if self._data is None:
                self._log("[ERROR] No viseme data - pick a TXT first.")
                return
        try:
            mapping = self._mapping()
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return

        node_map = self._node_map()
        if node_map is not None and not any(node_map.values()):
            self._log("[ERROR] Manual target: fill at least one node (Phonemes / Coartic / JaLi).")
            return
        if node_map is None and self.cmb_rig.count() == 0:
            self.on_refresh_rigs()
            if self.cmb_rig.count() == 0:
                self._log("[ERROR] No rig in the scene (Auto). Use Manual to pick nodes.")
                return

        ns = self._namespace()
        start = self.sb_start.value()
        jali = (self.ds_jaw.value(), self.ds_lip.value()) if self.rb_jali_fixed.isChecked() else None
        wav = self.le_wav.text().strip()
        if wav and not os.path.isfile(wav):
            self._log("[ERROR] WAV not found: {0}".format(wav))
            return

        targets, _ = keyer.resolve_targets(mapping, ns, node_map)
        for attr, scale, mx in keyer.scale_warnings(targets, mapping, self.ds_scale.value(),
                                                    self.ds_jali_scale.value()):
            self._log("[WARN] {0}: scale {1:g} exceeds the attribute maximum {2:g}".format(attr, scale, mx))

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            res = keyer.apply(self._data, mapping, ns, start, viseme_scale=self.ds_scale.value(),
                              jali_scale=self.ds_jali_scale.value(), jali_fixed=jali, node_map=node_map)
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

        self._log("[DONE] {0} attributes keyed on '{1}': frames {2}-{3} @ {4:g} fps ({5} keys, JaLi {6}){7}".format(
            res["attrs"], self._target_desc(node_map), res["start"], res["end"], res["fps"], res["keys"],
            "fixed {0:g} / {1:g}".format(*jali) if jali else "from data x {0:g}".format(self.ds_jali_scale.value()),
            ", skipped: {0}".format(", ".join(res["skipped"])) if res["skipped"] else ""))
        self._log("[INFO] The model output ends about 0.32 s before the audio (VisemeNet limit).")

    def on_remove(self, *args):
        try:
            mapping = self._mapping()
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return
        node_map = self._node_map()
        if node_map is not None and not any(node_map.values()):
            self._log("[ERROR] Manual target: fill at least one node (Phonemes / Coartic / JaLi).")
            return
        if self._data is not None:
            start = self.sb_start.value()
            end = start + int(self._data.seconds * keyer.scene_fps())
            n = keyer.remove(mapping, self._namespace(), start, end, node_map=node_map)
            self._log("[OK] Removed keys on {0} attribute(s), frames {1}-{2}".format(n, start, end))
        else:
            n = keyer.remove(mapping, self._namespace(), node_map=node_map)
            self._log("[OK] Removed all keys on {0} attribute(s)".format(n))

    def on_select_controls(self, *args):
        try:
            nodes = [n for n in keyer.controls(self._mapping(), self._namespace(), self._node_map())
                     if cmds.objExists(n)]
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
            "Keys VisemeNet viseme curves onto a JALI rig - the nodes named\n"
            "in the mapping json (e.g. CNT_PHONEMES or DUMMY_IN_PHONEMES).\n\n"
            "1. Make the TXT with VisemeNet Converter (JUN_JALI).\n"
            "2. Pick the TXT - the WAV is found from the .visemenet.json\n"
            "   or a file with the same name.\n"
            "3. Target: Auto finds the rig by name, Manual lets you pick\n"
            "   the Phonemes / Coartic / JaLi nodes (empty = skipped).\n"
            "4. Apply (one undo step).\n\n"
            "Keys are sampled at the scene fps. Re-applying clears the range first.\n"
            "Scales and the Fixed range reset to the mapping's defaults.\n"
            "New rigs = a new json in app/mappings.\n\n"
            "Written by Ji Hun Park.").format(VERSION, LAST_UPDATE))
