# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00540_JaliLipSync - Qt UI (in-Maya)
#
# JUN_JALI 의 VisemeNet Converter 가 만든 txt(+json) 와 음성 wav 를 골라 JALI 리그에 키를 건다.
#   Data    : 클립 표 (v01.02) - TXT 여러 개를 Add 로 넣고 Up / Down 으로 순서를 정한다. WAV 는 json 의 source_wav 또는
#             같은 이름 wav 를 자동으로 찾고, Set WAV 로 바꿀 수 있다. 표의 Start 열 = 그 클립이 시작하는 프레임.
#   Target  : Auto(리그 네임스페이스 콤보 — 매핑 json 의 phonemes 노드를 표식으로 찾는다)
#             / Manual(역할 3칸 Phonemes · Coartic · JaLi 를 씬 선택으로 채움, 빈 역할은 건너뜀) + 매핑 json 콤보
#   Options : 시작 프레임 · Hold(클립 사이 정지 프레임) · 비짐 배율 · JaLi(데이터 + JaLi 배율 / 고정 Jaw Lip)
#             · 오디오 붙이기(클립이 여럿이면 wav 하나로 합쳐 Sequence WAV 경로에 쓴다) · 재생 범위
#             배율 · Fixed 범위의 기본값은 매핑 json 이 정하고, 매핑을 바꾸면 스핀박스가 리셋된다.
#   Apply / Remove Keys / Select Controls + 로그
# 모든 UI 문자열 · 로그는 영어. 계획: JUN_JALI/docs/0030_tool_plan.md §5, docs/plans/A00540_JaliLipSync_v0101_rules_manual_plan.md

import os
import re

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.core import file_opener

from tools.A00540_JaliLipSync.app.config.version import VERSION, LAST_UPDATE
from Framework.jali import lipsync_data, mapping as mapping_mod, keyer, scene, sequence   # v01.03: 공용 코어


WINDOW_OBJECT_NAME = "JUN_A00540_JaliLipSync_window"
OPT_LAST_DIR = "JUN_A00540_lastDir"
GUIDE_DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))), "docs", "A00540_JaliLipSync.md")
ROLE_LABELS = (("phonemes", "Phonemes"), ("coartic", "Coartic"), ("jali", "JaLi"))
COLUMNS = ("#", "Start", "Viseme TXT", "Audio WAV", "Length")
COL_NUM, COL_START, COL_TXT, COL_WAV, COL_LEN = range(5)


def _natural_key(path):
    """파일 이름의 숫자를 숫자로 비교 (clip_2 < clip_10)."""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", os.path.basename(path))]


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("JALI LipSync v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(560, 760)

        self.clips = []                     # [sequence.Clip] - 표의 순서 = 타임라인 순서
        self._build_ui()
        self.on_mapping_changed()
        self._log("[INFO] Add one or more VisemeNet TXT files (from the JUN_JALI VisemeNet Converter).")

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Open Guide", self.on_open_guide)
        help_menu.addAction("About", self.show_about)
        layout.setMenuBar(self.menu_bar)

        # --- Data (클립 표)
        data_box = QGroupBox("Data - clips in timeline order")
        dlay = QVBoxLayout(data_box)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(90)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_TXT, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_WAV, QHeaderView.Stretch)
        for c in (COL_NUM, COL_START, COL_LEN):
            header.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.setToolTip("Clips are keyed in this order. Start = first frame of the clip (Start frame + "
                              "previous clips + Hold). Double-click a row to change its WAV.")
        self.table.itemDoubleClicked.connect(lambda _item: self.on_set_wav())
        dlay.addWidget(self.table)

        brow = QHBoxLayout()
        self.btn_add = QPushButton("Add TXT...")
        self.btn_add.setToolTip("Add one or more <name>.txt files (sorted by name). The WAV is found from the "
                                ".visemenet.json or a file with the same name.")
        self.btn_add.clicked.connect(self.on_add_txt)
        btn_wav = QPushButton("Set WAV...")
        btn_wav.setToolTip("Pick the audio for the selected clip (optional).")
        btn_wav.clicked.connect(self.on_set_wav)
        btn_nowav = QPushButton("No WAV")
        btn_nowav.setToolTip("Remove the audio from the selected clips (keys only).")
        btn_nowav.clicked.connect(self.on_clear_wav)
        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self.on_remove_clip)
        btn_up = QPushButton("Up")
        btn_up.clicked.connect(lambda _=False: self.on_move(-1))
        btn_down = QPushButton("Down")
        btn_down.clicked.connect(lambda _=False: self.on_move(1))
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.on_clear_clips)
        for b in (self.btn_add, btn_wav, btn_nowav, btn_remove, btn_up, btn_down, btn_clear):
            brow.addWidget(b)
        dlay.addLayout(brow)
        self.lb_info = QLabel("No clips")
        self.lb_info.setWordWrap(True)
        dlay.addWidget(self.lb_info)
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
            btn_clear_role = QPushButton("x")
            btn_clear_role.setFixedWidth(24)
            btn_clear_role.clicked.connect(lambda _=False, w=le: w.clear())
            row = 1 + i
            if i == 0:
                tgrid.addWidget(self.rb_manual, row, 0)
            lb = QLabel(label)
            tgrid.addWidget(lb, row, 1)
            tgrid.addWidget(le, row, 2)
            hb = QHBoxLayout()
            hb.setContentsMargins(0, 0, 0, 0)
            hb.addWidget(btn_sel)
            hb.addWidget(btn_clear_role)
            tgrid.addLayout(hb, row, 3)
            self.le_roles[role] = le
            self.manual_widgets += [lb, le, btn_sel, btn_clear_role]

        self.cmb_mapping = QComboBox()
        self.cmb_mapping.addItems(mapping_mod.list_mappings())
        self.cmb_mapping.setToolTip("Model columns -> rig attributes (Framework/jali/mappings/*.json). "
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
        self.sb_start.setToolTip("First frame of the first clip.")
        self.sb_start.valueChanged.connect(self._refresh_table)
        self.sb_hold = QSpinBox()
        self.sb_hold.setRange(0, 100000)
        self.sb_hold.setValue(0)
        self.sb_hold.setToolTip("Frames of pause between clips. The last value of a clip is held until the "
                                "next clip starts (silence in the audio).")
        self.sb_hold.valueChanged.connect(self._refresh_table)
        self.ds_scale = QDoubleSpinBox()
        self.ds_scale.setRange(0.0, 100.0)
        self.ds_scale.setDecimals(2)
        self.ds_scale.setSingleStep(0.1)
        self.ds_scale.setToolTip("Model values (0-1) x this = viseme keys. Default comes from the mapping.")
        srow = QHBoxLayout()
        srow.addWidget(self.sb_start)
        srow.addSpacing(8)
        srow.addWidget(QLabel("Hold (frames)"))
        srow.addWidget(self.sb_hold)
        srow.addSpacing(8)
        srow.addWidget(QLabel("Viseme scale"))
        srow.addWidget(self.ds_scale)
        ogrid.addWidget(QLabel("Start frame"), 0, 0)
        ogrid.addLayout(srow, 0, 1, 1, 3)

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

        self.le_seq_wav = QLineEdit()
        self.le_seq_wav.setPlaceholderText("<first clip folder>/jali_sequence.wav")
        self.le_seq_wav.setToolTip("With more than one clip the clip WAVs are written into this one WAV at their "
                                   "frame positions (silence in the holds) and attached as one sound node.\n"
                                   "Empty = jali_sequence.wav next to the first TXT. A single clip uses its own WAV.")
        btn_seq = QPushButton("...")
        btn_seq.setFixedWidth(32)
        btn_seq.clicked.connect(self.on_browse_seq_wav)
        ogrid.addWidget(QLabel("Sequence WAV"), 3, 0)
        ogrid.addWidget(self.le_seq_wav, 3, 1, 1, 2)
        ogrid.addWidget(btn_seq, 3, 3)
        layout.addWidget(opt_box)

        # --- 버튼
        row = QHBoxLayout()
        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setMinimumHeight(32)
        self.btn_apply.clicked.connect(self.on_apply)
        btn_remove_keys = QPushButton("Remove Keys")
        btn_remove_keys.setToolTip("Delete the keys of every mapped attribute in the sequence range.")
        btn_remove_keys.clicked.connect(self.on_remove)
        btn_select = QPushButton("Select Controls")
        btn_select.clicked.connect(self.on_select_controls)
        row.addWidget(self.btn_apply, 2)
        row.addWidget(btn_remove_keys, 1)
        row.addWidget(btn_select, 1)
        layout.addLayout(row)

        log_box = QGroupBox("Log")
        log_layout = QVBoxLayout(log_box)
        self.log_view = JUN_mod_log_qt_v01(window_title="JALI LipSync - Log",
                                           object_name="JUN_A00540_JaliLipSync_log_window")
        self.log_view.setMinimumHeight(120)
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
            raise ValueError("No mapping json in Framework/jali/mappings")
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

    def _segments(self):
        """현재 표 · Start frame · Hold · 씬 fps 로 클립을 배치한 [Segment]."""
        return sequence.layout(self.clips, self.sb_start.value(), self.sb_hold.value(), keyer.scene_fps())

    def _selected_rows(self):
        return sorted({i.row() for i in self.table.selectedIndexes()})

    def _seq_wav_path(self):
        return self.le_seq_wav.text().strip() or sequence.sequence_wav_path(self.clips)

    # ------------------------------------------------------------------ Data

    def add_txt(self, path, wav_path=None):
        """txt 하나를 표 끝에 넣는다. wav_path None = 자동. 실패하면 로그 후 None. Returns Clip."""
        path = os.path.normpath(path)
        try:
            clip = sequence.load_clip(path, wav_path)
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return None
        self.clips.append(clip)
        if clip.wav_path:
            self._log("[OK] {0}: {1} rows ({2:.2f} s){3} + {4}".format(
                clip.label, len(clip.data.rows), clip.data.seconds, " + json" if clip.data.meta else "",
                os.path.basename(clip.wav_path)))
        else:
            self._log("[WARN] {0}: {1} rows ({2:.2f} s) - no matching WAV found (Set WAV..., optional)".format(
                clip.label, len(clip.data.rows), clip.data.seconds))
        self._refresh_table()
        return clip

    def on_add_txt(self, *args):
        paths, _ = QFileDialog.getOpenFileNames(self, "Viseme TXT (one or more)", self._last_dir(),
                                                "VisemeNet output (*.txt);;All files (*.*)")
        if not paths:
            return
        cmds.optionVar(sv=(OPT_LAST_DIR, os.path.dirname(paths[0])))
        for path in sorted(paths, key=_natural_key):
            self.add_txt(path)
        self.table.selectRow(self.table.rowCount() - 1)

    def on_set_wav(self, *args):
        rows = self._selected_rows()
        if not rows:
            self._log("[WARN] Select a clip first.")
            return
        clip = self.clips[rows[-1]]
        start = os.path.dirname(clip.wav_path or clip.txt_path)
        path, _ = QFileDialog.getOpenFileName(self, "Audio WAV for {0}".format(clip.label), start,
                                              "WAV (*.wav);;All files (*.*)")
        if path:
            clip.set_wav(os.path.normpath(path))
            self._log("[OK] {0}: audio {1}".format(clip.label, os.path.basename(clip.wav_path)))
            self._refresh_table()

    def on_clear_wav(self, *args):
        rows = self._selected_rows()
        if not rows:
            self._log("[WARN] Select a clip first.")
            return
        for r in rows:
            self.clips[r].set_wav("")
        self._refresh_table()

    def on_remove_clip(self, *args):
        rows = self._selected_rows()
        if not rows:
            self._log("[WARN] Select a clip first.")
            return
        for r in reversed(rows):
            del self.clips[r]
        self._refresh_table()

    def on_move(self, delta):
        rows = self._selected_rows()
        if not rows:
            self._log("[WARN] Select a clip first.")
            return
        r = rows[-1] if delta > 0 else rows[0]
        new = r + delta
        if new < 0 or new >= len(self.clips):
            return
        self.clips[r], self.clips[new] = self.clips[new], self.clips[r]
        self._refresh_table()
        self.table.selectRow(new)

    def on_clear_clips(self, *args):
        self.clips = []
        self._refresh_table()

    def on_browse_seq_wav(self, *args):
        path, _ = QFileDialog.getSaveFileName(self, "Sequence WAV", self._seq_wav_path() or self._last_dir(),
                                              "WAV (*.wav)")
        if path:
            self.le_seq_wav.setText(os.path.normpath(path))

    def _refresh_table(self, *args):
        """표를 다시 채운다 (Start 열은 layout 결과). 정보 줄도 갱신."""
        fps = keyer.scene_fps()
        segments = self._segments()
        self.table.setRowCount(len(segments))
        for i, seg in enumerate(segments):
            clip = seg.clip
            items = [QTableWidgetItem(str(i + 1)), QTableWidgetItem(str(seg.start)),
                     QTableWidgetItem(clip.label),
                     QTableWidgetItem(os.path.basename(clip.wav_path) if clip.wav_path else "(none)"),
                     QTableWidgetItem("{0:.2f} s / {1} f".format(clip.seconds, seg.span))]
            items[COL_TXT].setToolTip(clip.txt_path)
            items[COL_WAV].setToolTip(clip.wav_path or "No audio - keys only")
            if clip.wav_path and clip.wav_seconds is None:
                items[COL_WAV].setText(items[COL_WAV].text() + " (cannot read)")
            gap = (clip.wav_seconds or 0) - clip.data.seconds
            if clip.wav_seconds is not None and (gap > 0.5 or gap < -0.05):
                items[COL_LEN].setText(items[COL_LEN].text() + " (check the pair: {0:+.2f} s)".format(gap))
            for c, item in enumerate(items):
                if c in (COL_NUM, COL_START, COL_LEN):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, c, item)
        if not segments:
            self.lb_info.setText("No clips")
            return
        total = segments[-1].end - segments[0].start + 1
        self.lb_info.setText("{0} clip(s): frames {1}-{2} ({3} frames = {4:.2f} s at {5:g} fps), hold {6}, "
                             "audio on {7} clip(s)".format(
                                 len(segments), segments[0].start, segments[-1].end, total, total / fps, fps,
                                 self.sb_hold.value(), sum(1 for s in segments if s.wav_path)))

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
        if not self.clips:
            self._log("[ERROR] No clips - add at least one TXT.")
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
        hold = self.sb_hold.value()
        jali = (self.ds_jaw.value(), self.ds_lip.value()) if self.rb_jali_fixed.isChecked() else None
        for clip in self.clips:
            if clip.wav_path and not os.path.isfile(clip.wav_path):
                self._log("[ERROR] WAV not found: {0}".format(clip.wav_path))
                return
        segments = self._segments()
        self._refresh_table()

        targets, _ = keyer.resolve_targets(mapping, ns, node_map)
        for attr, scale, mx in keyer.scale_warnings(targets, mapping, self.ds_scale.value(),
                                                    self.ds_jali_scale.value()):
            self._log("[WARN] {0}: scale {1:g} exceeds the attribute maximum {2:g}".format(attr, scale, mx))

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            res = keyer.apply_sequence(segments, mapping, ns, viseme_scale=self.ds_scale.value(),
                                       jali_scale=self.ds_jali_scale.value(), jali_fixed=jali, node_map=node_map,
                                       hold=hold)
            for i, (label, s, e) in enumerate(res["clips"]):
                self._log("[OK] {0}/{1} {2}: frames {3}-{4}".format(i + 1, len(res["clips"]), label, s, e))
            if self.cb_range.isChecked():
                cmds.playbackOptions(minTime=res["start"], maxTime=res["end"])
            if self.cb_audio.isChecked():
                self._attach_audio(segments)
        except keyer.KeyingError as e:
            self._log("[ERROR] {0}".format(e))
            return
        except (RuntimeError, ValueError) as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            return
        finally:
            QApplication.restoreOverrideCursor()

        self._log("[DONE] {0} attributes keyed on '{1}': {2} clip(s), frames {3}-{4} @ {5:g} fps, hold {6} "
                  "({7} keys, JaLi {8}){9}".format(
                      res["attrs"], self._target_desc(node_map), len(res["clips"]), res["start"], res["end"],
                      res["fps"], hold, res["keys"],
                      "fixed {0:g} / {1:g}".format(*jali) if jali else "from data x {0:g}".format(self.ds_jali_scale.value()),
                      ", skipped: {0}".format(", ".join(res["skipped"])) if res["skipped"] else ""))
        self._log("[INFO] The model output ends about 0.32 s before each clip's audio (VisemeNet limit).")

    def _attach_audio(self, segments):
        """클립이 하나면 그 wav 를, 여럿이면 합친 wav 를 사운드 노드 하나로 붙인다."""
        with_wav = [s for s in segments if s.wav_path]
        if not with_wav:
            self._log("[WARN] No clip has audio - nothing attached.")
            return
        if len(segments) == 1:
            wav = segments[0].wav_path
        else:
            wav = self._seq_wav_path()
            sequence.write_sequence_wav(segments, wav, keyer.scene_fps())
            self._log("[OK] Sequence WAV written: {0} ({1} clip(s) with audio)".format(wav, len(with_wav)))
        node = scene.attach_sound(wav, segments[0].start)
        self._log("[OK] Audio '{0}' at frame {1}".format(node, segments[0].start))

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
        if self.clips:
            segments = self._segments()
            start, end = segments[0].start, segments[-1].end
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
            "1. Make the TXT files with VisemeNet Converter (JUN_JALI).\n"
            "2. Add the TXT files and put them in order (Up / Down) - the WAV\n"
            "   is found from the .visemenet.json or a file with the same name.\n"
            "3. Hold = frames of pause between clips (last pose held).\n"
            "4. Target: Auto finds the rig by name, Manual lets you pick\n"
            "   the Phonemes / Coartic / JaLi nodes (empty = skipped).\n"
            "5. Apply (one undo step). Several clips -> one sequence WAV.\n\n"
            "Keys are sampled at the scene fps. Re-applying clears the range first.\n"
            "Scales and the Fixed range reset to the mapping's defaults.\n"
            "New rigs = a new json in Framework/jali/mappings.\n\n"
            "Written by Ji Hun Park.").format(VERSION, LAST_UPDATE))
