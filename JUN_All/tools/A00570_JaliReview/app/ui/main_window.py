# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00570_JaliReview - Qt UI (in-Maya)
#
# A00560_JaliBatch 가 만든 클립 .mb 를 검수 씬(아바타 레퍼런스 + 클립 레퍼런스 ns CLIP)에서 하나씩 본다.
#   Clips   : 클립 폴더(매니페스트) -> 표 (Clip | Frames | Status), Prev / Next / Swap, Build Review Scene
#   Edits   : Allow edits on referenced animation curves 체크, 남은 편집 수 + 목록, Save Clip Edits, Discard Edits
#   Avatar  : 아바타 .mb 레퍼런스, BlendShape 콤보, 규칙 json(선택), Connect ARKIT_OUT -> BS, 보고
#   Open Clip : 클립을 직접 열고(임시 아바타 레퍼런스) Save Clip & Close
# 모든 UI 문자열 · 로그는 영어. 로직은 ../core (review_scene · arkit_connect), 매니페스트는 Framework.jali.clip_manifest.
# 계획: docs/plans/A00560_JaliBatch_plan.md §5, 안내: docs/A00570_JaliReview.md

import os

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.core import file_opener
from Framework.jali import clip_manifest

from tools.A00570_JaliReview.app.config.version import VERSION, LAST_UPDATE
from tools.A00570_JaliReview.app.core import review_scene as rs, arkit_connect, prefs

WINDOW_OBJECT_NAME = "JUN_A00570_JaliReview_window"
GUIDE_DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))), "docs", "A00570_JaliReview.md")
COLUMNS = ("Clip", "Frames", "Status")
COL_NAME, COL_FRAMES, COL_STATUS = range(3)
RED, YELLOW, GREEN = "#d05050", "#d0a040", "#5aa05a"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("JALI Review v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(620, 760)
        self.clips = []                 # 매니페스트 항목 (표 순서)
        self.manifest = None
        self._build_ui()
        self._load_prefs()
        self.refresh_state()
        self._log("[INFO] Pick the clip folder made by A00560_JaliBatch (jali_clips.manifest.json), then Build Review Scene.")

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Open Guide", self.on_open_guide)
        help_menu.addAction("About", self.show_about)
        layout.setMenuBar(self.menu_bar)

        # --- Clips
        clip_box = QGroupBox("Clips")
        cl = QVBoxLayout(clip_box)
        frow = QHBoxLayout()
        self.le_folder = QLineEdit()
        self.le_folder.setPlaceholderText("Clip folder (A00560 output with jali_clips.manifest.json)")
        btn_folder = QPushButton("...")
        btn_folder.setFixedWidth(32)
        btn_folder.clicked.connect(self.on_browse_folder)
        btn_reload = QPushButton("Reload")
        btn_reload.clicked.connect(self.load_folder)
        frow.addWidget(QLabel("Clips"))
        frow.addWidget(self.le_folder, 1)
        frow.addWidget(btn_folder)
        frow.addWidget(btn_reload)
        cl.addLayout(frow)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(140)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_FRAMES, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeToContents)
        self.table.itemDoubleClicked.connect(lambda _i: self.on_swap())
        self.table.setToolTip("Double-click a row (or Swap) to put that clip into the review scene. Status comes from the manifest.")
        cl.addWidget(self.table)
        nrow = QHBoxLayout()
        self.btn_build = QPushButton("Build Review Scene")
        self.btn_build.setToolTip("New scene -> reference the avatar (if set) and the selected clip as namespace CLIP.")
        self.btn_build.clicked.connect(self.on_build)
        btn_prev = QPushButton("< Prev")
        btn_prev.clicked.connect(lambda _=False: self.on_step(-1))
        btn_next = QPushButton("Next >")
        btn_next.clicked.connect(lambda _=False: self.on_step(1))
        self.btn_swap = QPushButton("Swap")
        self.btn_swap.setToolTip("Replace the CLIP reference with the selected clip (file -loadReference).\n"
                                 "Blocked while this clip has unsaved edits - Save Clip Edits or Discard first.")
        self.btn_swap.clicked.connect(self.on_swap)
        nrow.addWidget(self.btn_build, 2)
        nrow.addWidget(btn_prev)
        nrow.addWidget(btn_next)
        nrow.addWidget(self.btn_swap)
        cl.addLayout(nrow)
        self.lb_current = QLabel("Current: (no CLIP reference in the scene)")
        self.lb_current.setWordWrap(True)
        cl.addWidget(self.lb_current)
        layout.addWidget(clip_box)

        # --- Edits
        edit_box = QGroupBox("Edits (referenced animation curves)")
        el = QVBoxLayout(edit_box)
        self.cb_allow = QCheckBox("Allow edits on referenced animation curves (Maya preference)")
        self.cb_allow.setToolTip("animDisplay -refAnimCurvesEditable. Off = key edits on the clip are silently ignored.")
        self.cb_allow.toggled.connect(self.on_allow_toggled)
        el.addWidget(self.cb_allow)
        self.lb_edits = QLabel("Edits: 0")
        self.lst_edits = QListWidget()
        self.lst_edits.setMaximumHeight(72)
        el.addWidget(self.lb_edits)
        el.addWidget(self.lst_edits)
        erow = QHBoxLayout()
        self.btn_save = QPushButton("Save Clip Edits")
        self.btn_save.setToolTip("Write the edits into the clip .mb (file -saveReference) and mark it 'edited' in the manifest.\n"
                                 "Do this BEFORE Swap / reopening - Maya re-applies unsaved curve edits at wrong times on reload.")
        self.btn_save.clicked.connect(self.on_save_edits)
        self.btn_discard = QPushButton("Discard Edits")
        self.btn_discard.setToolTip("Throw the review edits away (unload -> remove edits -> load). The clip file is untouched.")
        self.btn_discard.clicked.connect(self.on_discard)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_state)
        erow.addWidget(self.btn_save, 2)
        erow.addWidget(self.btn_discard, 1)
        erow.addWidget(btn_refresh)
        el.addLayout(erow)
        layout.addWidget(edit_box)

        # --- Avatar · Connect
        av_box = QGroupBox("Avatar")
        ag = QGridLayout(av_box)
        self.le_avatar = QLineEdit()
        self.le_avatar.setPlaceholderText("Avatar scene (.mb / .ma) to reference")
        btn_av = QPushButton("...")
        btn_av.setFixedWidth(32)
        btn_av.clicked.connect(self.on_browse_avatar)
        self.btn_ref_avatar = QPushButton("Reference")
        self.btn_ref_avatar.setToolTip("Reference the avatar into the current scene (namespace = file name).")
        self.btn_ref_avatar.clicked.connect(self.on_reference_avatar)
        ag.addWidget(QLabel("Avatar"), 0, 0)
        ag.addWidget(self.le_avatar, 0, 1)
        ag.addWidget(btn_av, 0, 2)
        ag.addWidget(self.btn_ref_avatar, 0, 3)
        self.cmb_bs = QComboBox()
        self.cmb_bs.setToolTip("Target blendShape of the avatar (ARKit 52 aliases).")
        btn_bs = QPushButton("Refresh")
        btn_bs.clicked.connect(self.refresh_blendshapes)
        ag.addWidget(QLabel("BlendShape"), 1, 0)
        ag.addWidget(self.cmb_bs, 1, 1, 1, 2)
        ag.addWidget(btn_bs, 1, 3)
        self.le_rules = QLineEdit()
        self.le_rules.setPlaceholderText("Rules json (optional): {\"map\": {\"ARKIT attr\": \"target\"}}")
        btn_rules = QPushButton("...")
        btn_rules.setFixedWidth(32)
        btn_rules.clicked.connect(self.on_browse_rules)
        ag.addWidget(QLabel("Rules"), 2, 0)
        ag.addWidget(self.le_rules, 2, 1, 1, 2)
        ag.addWidget(btn_rules, 2, 3)
        crow = QHBoxLayout()
        self.btn_connect = QPushButton("Connect ARKIT_OUT -> BlendShape")
        self.btn_connect.setToolTip("Connect CLIP:JALI:ARKIT_OUT.<target> to the blendShape targets with the same alias.\n"
                                    "Already driven targets are skipped; missing targets are listed. One undo step.")
        self.btn_connect.clicked.connect(self.on_connect)
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self.on_disconnect)
        self.lb_connect = QLabel("")
        crow.addWidget(self.btn_connect, 2)
        crow.addWidget(self.btn_disconnect, 1)
        ag.addLayout(crow, 3, 0, 1, 4)
        ag.addWidget(self.lb_connect, 4, 0, 1, 4)
        ag.setColumnStretch(1, 1)
        layout.addWidget(av_box)

        # --- Open Clip
        orow = QHBoxLayout()
        self.btn_open = QPushButton("Open Clip...")
        self.btn_open.setToolTip("Open the selected clip .mb itself (deep edits) with the avatar as a temporary reference.")
        self.btn_open.clicked.connect(self.on_open_clip)
        self.btn_save_close = QPushButton("Save Clip & Close")
        self.btn_save_close.setToolTip("Remove the temporary avatar reference, save the clip in place and start a new scene.")
        self.btn_save_close.clicked.connect(self.on_save_close)
        orow.addWidget(self.btn_open, 1)
        orow.addWidget(self.btn_save_close, 1)
        layout.addLayout(orow)

        log_box = QGroupBox("Log")
        ll = QVBoxLayout(log_box)
        self.log_view = JUN_mod_log_qt_v01(window_title="JALI Review - Log", object_name="JUN_A00570_JaliReview_log_window")
        self.log_view.setMinimumHeight(100)
        ll.addWidget(self.log_view)
        layout.addWidget(log_box, 1)

    # ------------------------------------------------------------------ helpers

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def _load_prefs(self):
        self.le_folder.setText(prefs.get("clip_dir"))
        self.le_avatar.setText(prefs.get("avatar"))
        self.le_rules.setText(prefs.get("rules"))
        if self.le_folder.text().strip():
            self.load_folder()
        self.refresh_blendshapes()
        bs = prefs.get("blendshape")
        if bs and self.cmb_bs.findText(bs) >= 0:
            self.cmb_bs.setCurrentText(bs)

    def _save_prefs(self):
        prefs.set("clip_dir", self.le_folder.text().strip())
        prefs.set("avatar", self.le_avatar.text().strip())
        prefs.set("rules", self.le_rules.text().strip())
        prefs.set("blendshape", self.cmb_bs.currentText())

    def folder(self):
        return os.path.normpath(self.le_folder.text().strip()) if self.le_folder.text().strip() else ""

    def selected_row(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        return rows[0] if rows else -1

    def selected_clip(self):
        r = self.selected_row()
        return self.clips[r] if 0 <= r < len(self.clips) else None

    def clip_mb(self, entry):
        mb = entry.get("mb") or os.path.join(self.folder(), entry["name"] + ".mb")
        return os.path.normpath(mb)

    def current_rn(self):
        return rs.find_clip_ref()

    def _rules(self):
        path = self.le_rules.text().strip()
        return arkit_connect.load_rules(path) if path else {}

    # ------------------------------------------------------------------ Clips

    def on_browse_folder(self, *args):
        path = QFileDialog.getExistingDirectory(self, "Clip folder", self.folder() or "")
        if path:
            self.le_folder.setText(os.path.normpath(path))
            self.load_folder()

    def load_folder(self, *args):
        folder = self.folder()
        self.clips = []
        self.table.setRowCount(0)
        if not folder or not os.path.isdir(folder):
            self._log("[ERROR] Clip folder not found: {0}".format(folder or "(empty)"))
            return
        try:
            self.manifest = clip_manifest.load(folder)
        except ValueError as e:
            self._log("[WARN] {0}".format(e))
            self.manifest = clip_manifest.empty()
        entries = clip_manifest.ordered_clips(self.manifest)
        if not entries:
            # 매니페스트가 없으면 .mb 목록만
            names = sorted(f for f in os.listdir(folder) if f.lower().endswith(".mb"))
            entries = [{"name": os.path.splitext(n)[0], "mb": os.path.join(folder, n)} for n in names]
            if entries:
                self._log("[WARN] No manifest - listing .mb files (no start / end, playback range is not set on Swap).")
        self.clips = [e for e in entries if os.path.isfile(self.clip_mb(e))]
        missing = len(entries) - len(self.clips)
        self.table.setRowCount(len(self.clips))
        for i, e in enumerate(self.clips):
            name = QTableWidgetItem(e["name"])
            name.setToolTip(self.clip_mb(e))
            frames = QTableWidgetItem("{0}-{1}".format(e.get("start", "?"), e.get("end", "?")) if "start" in e else "")
            frames.setTextAlignment(Qt.AlignCenter)
            status = QTableWidgetItem(e.get("status", ""))
            status.setTextAlignment(Qt.AlignCenter)
            color = {"edited": YELLOW, "failed": RED, "generated": GREEN}.get(e.get("status"))
            if color:
                status.setForeground(QBrush(QColor(color)))
            for c, item in enumerate((name, frames, status)):
                self.table.setItem(i, c, item)
        self._save_prefs()
        self._log("[OK] {0} clip(s) in {1}{2}".format(len(self.clips), folder, " ({0} listed but missing on disk)".format(missing) if missing else ""))
        self._select_current_row()

    def _select_current_row(self):
        rn = self.current_rn()
        if not rn:
            if self.clips and self.selected_row() < 0:
                self.table.selectRow(0)
            return
        path = os.path.normcase(rs.clip_path(rn))
        for i, e in enumerate(self.clips):
            if os.path.normcase(self.clip_mb(e)) == path:
                self.table.selectRow(i)
                return

    def on_build(self, *args):
        entry = self.selected_clip()
        if entry is None:
            self._log("[ERROR] Select a clip first.")
            return
        if rs.scene_modified():
            answer = QMessageBox.question(self, "Build Review Scene", "The current scene has unsaved changes. Start a new scene anyway?",
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return
        rs.new_scene()
        if entry.get("fps"):
            rs.set_scene_fps(entry["fps"])
        avatar = self.le_avatar.text().strip()
        try:
            if avatar:
                arn = rs.reference_avatar(avatar)
                self._log("[OK] Avatar referenced: {0}".format(arn))
            rn = rs.reference_clip(self.clip_mb(entry))
        except rs.ReviewError as e:
            self._log("[ERROR] {0}".format(e))
            self.refresh_state()
            return
        except RuntimeError as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            self.refresh_state()
            return
        self._after_clip_change(entry, rn, "Review scene built")
        self.refresh_blendshapes()

    def on_step(self, delta):
        if not self.clips:
            return
        r = self.selected_row()
        new = min(max((r if r >= 0 else 0) + delta, 0), len(self.clips) - 1)
        self.table.selectRow(new)
        if self.current_rn():
            self.on_swap()

    def on_swap(self, *args):
        entry = self.selected_clip()
        if entry is None:
            self._log("[ERROR] Select a clip first.")
            return
        rn = self.current_rn()
        if not rn:
            self._log("[WARN] No CLIP reference in the scene - use Build Review Scene.")
            return
        target = self.clip_mb(entry)
        if os.path.normcase(rs.clip_path(rn)) == os.path.normcase(target):
            self._log("[INFO] {0} is already the current clip.".format(entry["name"]))
            return
        pending = rs.pending_edits(rn)
        if pending:
            box = QMessageBox(self)
            box.setWindowTitle("Unsaved clip edits")
            box.setText("{0} edit(s) on the current clip are not saved.\n\nSwapping with unsaved edits re-applies them at the wrong "
                        "times (Maya bug at non-24 fps). Save them into the clip, discard them, or cancel.".format(len(pending)))
            b_save = box.addButton("Save && Swap", QMessageBox.AcceptRole)
            b_discard = box.addButton("Discard && Swap", QMessageBox.DestructiveRole)
            box.addButton("Cancel", QMessageBox.RejectRole)
            box.exec_()
            if box.clickedButton() == b_save:
                if not self.on_save_edits():
                    return
            elif box.clickedButton() == b_discard:
                self.on_discard()
            else:
                self._log("Swap cancelled.")
                return
        try:
            if entry.get("fps") and abs(float(entry["fps"]) - (self._scene_fps() or 0)) > 1e-6:
                rs.set_scene_fps(entry["fps"])
                self._log("[INFO] Scene fps set to {0:g} (clip)".format(float(entry["fps"])))
            rs.swap_clip(rn, target)
        except (rs.ReviewError, RuntimeError) as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            self.refresh_state()
            return
        self._after_clip_change(entry, rn, "Swapped")

    def _scene_fps(self):
        from Framework.jali import time_units
        return time_units.fps_of_unit(rs.scene_unit())

    def _after_clip_change(self, entry, rn, verb):
        if "start" in entry and "end" in entry:
            rs.apply_range(int(entry["start"]), int(entry["end"]))
        snd = rs.attach_clip_sound()
        self._log("[OK] {0}: {1} ({2}){3}{4}".format(
            verb, entry["name"], rn,
            ", frames {0}-{1}".format(entry["start"], entry["end"]) if "start" in entry else "",
            ", sound {0}".format(snd) if snd else ", no sound node"))
        self.refresh_state()

    # ------------------------------------------------------------------ Edits

    def refresh_state(self, *args):
        rn = self.current_rn()
        self.cb_allow.blockSignals(True)
        self.cb_allow.setChecked(rs.anim_curve_edits_enabled())
        self.cb_allow.blockSignals(False)
        self.lst_edits.clear()
        if not rn:
            self.lb_current.setText("Current: (no CLIP reference in the scene)")
            self.lb_edits.setText("Edits: -")
            for b in (self.btn_swap, self.btn_save, self.btn_discard):
                b.setEnabled(False)
            return
        path = rs.clip_path(rn)
        self.lb_current.setText("Current: {0}  ({1}, {2})".format(os.path.basename(path), rn, "loaded" if rs.is_loaded(rn) else "unloaded"))
        self.lb_current.setToolTip(path)
        edits = rs.pending_edits(rn)
        failed = rs.pending_edits(rn, failed=True)
        self.lb_edits.setText("Edits: {0}{1}{2}".format(
            len(edits), " ({0} failed)".format(len(failed)) if failed else "",
            "" if self.cb_allow.isChecked() else "   [curve edits are OFF - keys cannot be changed]"))
        for e in edits + failed:
            self.lst_edits.addItem(rs.describe_edit(e))
        self.btn_swap.setEnabled(True)
        self.btn_save.setEnabled(bool(edits))
        self.btn_discard.setEnabled(bool(edits or failed))
        bs = self.cmb_bs.currentText()
        src = rs.arkit_out_node()
        if bs and src:
            self.lb_connect.setText("{0} -> {1}: {2} connected".format(src, bs, arkit_connect.connected_count(src, bs)))
        else:
            self.lb_connect.setText("")

    def on_allow_toggled(self, enabled):
        rs.set_anim_curve_edits(enabled)
        self._log("[OK] Allow edits on referenced animation curves: {0}".format("ON" if enabled else "OFF"))
        self.refresh_state()

    def on_save_edits(self, *args):
        rn = self.current_rn()
        if not rn:
            self._log("[WARN] No CLIP reference.")
            return False
        edits = rs.pending_edits(rn)
        if not edits:
            self._log("[INFO] Nothing to save.")
            return True
        try:
            path, _ = rs.save_clip_edits(rn)
        except (rs.ReviewError, RuntimeError) as e:
            self._log("[ERROR] Save Clip Edits: {0}".format(str(e).strip()))
            self.refresh_state()
            return False
        name = os.path.splitext(os.path.basename(path))[0]
        if self.manifest is not None and self.folder():
            import time
            clip_manifest.update_clip(self.manifest, name, status=clip_manifest.STATUS_EDITED,
                                      edited_at=time.strftime("%Y-%m-%d %H:%M:%S"))
            try:
                clip_manifest.save(self.folder(), self.manifest)
            except OSError as e:
                self._log("[WARN] Manifest not updated: {0}".format(e))
            for i, e in enumerate(self.clips):
                if e["name"] == name:
                    e["status"] = clip_manifest.STATUS_EDITED
                    self.table.item(i, COL_STATUS).setText("edited")
                    self.table.item(i, COL_STATUS).setForeground(QBrush(QColor(YELLOW)))
        self._log("[OK] Saved {0} edit(s) into {1}".format(len(edits), path))
        self.refresh_state()
        return True

    def on_discard(self, *args):
        rn = self.current_rn()
        if not rn:
            return
        try:
            n = rs.discard_edits(rn)
        except RuntimeError as e:
            self._log("[ERROR] Discard: {0}".format(str(e).strip()))
            return
        self._log("[OK] Discarded {0} edit(s) (clip file untouched)".format(n))
        self.refresh_state()

    # ------------------------------------------------------------------ Avatar · Connect

    def on_browse_avatar(self, *args):
        start = os.path.dirname(self.le_avatar.text().strip()) if self.le_avatar.text().strip() else ""
        path, _ = QFileDialog.getOpenFileName(self, "Avatar scene", start, "Maya scene (*.mb *.ma);;All files (*.*)")
        if path:
            self.le_avatar.setText(os.path.normpath(path))
            self._save_prefs()

    def on_browse_rules(self, *args):
        start = os.path.dirname(self.le_rules.text().strip()) if self.le_rules.text().strip() else ""
        path, _ = QFileDialog.getOpenFileName(self, "Connect rules json", start, "json (*.json);;All files (*.*)")
        if path:
            self.le_rules.setText(os.path.normpath(path))
            self._save_prefs()

    def on_reference_avatar(self, *args):
        try:
            rn = rs.reference_avatar(self.le_avatar.text().strip())
        except (rs.ReviewError, RuntimeError) as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            return
        self._save_prefs()
        self._log("[OK] Avatar referenced: {0}".format(rn))
        self.refresh_blendshapes()

    def refresh_blendshapes(self, *args):
        current = self.cmb_bs.currentText()
        self.cmb_bs.clear()
        self.cmb_bs.addItems(arkit_connect.list_blendshapes())
        if current and self.cmb_bs.findText(current) >= 0:
            self.cmb_bs.setCurrentText(current)
        self.refresh_state()

    def on_connect(self, *args):
        src = rs.arkit_out_node()
        bs = self.cmb_bs.currentText()
        if not src:
            self._log("[ERROR] No ARKIT_OUT in the scene (reference a clip first).")
            return None
        if not bs:
            self._log("[ERROR] Pick a blendShape.")
            return None
        try:
            res = arkit_connect.connect(src, bs, self._rules())
        except ValueError as e:
            self._log("[ERROR] {0}".format(e))
            return None
        self._save_prefs()
        self._log("[OK] Connect {0} -> {1}: {2} connected, {3} skipped, {4} missing{5}".format(
            src, bs, res["connected"], len(res["skipped"]), len(res["missing"]),
            ", {0} failed".format(len(res["failed"])) if res["failed"] else ""))
        if res["missing"]:
            self._log("[WARN] Not on the blendShape: {0}".format(", ".join(res["missing"])))
        for dst, why in res["skipped"]:
            self._log("[INFO] skipped {0}: {1}".format(dst, why))
        for dst, err in res["failed"]:
            self._log("[ERROR] {0}: {1}".format(dst, err))
        self.refresh_state()
        return res

    def on_disconnect(self, *args):
        src = rs.arkit_out_node()
        bs = self.cmb_bs.currentText()
        if not src or not bs:
            return
        n = arkit_connect.disconnect(src, bs)
        self._log("[OK] Disconnected {0} target(s)".format(n))
        self.refresh_state()

    # ------------------------------------------------------------------ Open Clip

    def on_open_clip(self, *args):
        entry = self.selected_clip()
        if entry is None:
            self._log("[ERROR] Select a clip first.")
            return
        if rs.scene_modified():
            answer = QMessageBox.question(self, "Open Clip", "The current scene has unsaved changes. Open the clip anyway?",
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return
        try:
            rs.open_clip(self.clip_mb(entry))
            avatar = self.le_avatar.text().strip()
            if avatar:
                rs.reference_temp_avatar(avatar)
                self._log("[OK] Temporary avatar reference ({0}) - removed by Save Clip & Close".format(rs.TEMP_AVATAR_NS))
        except (rs.ReviewError, RuntimeError) as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            return
        if "start" in entry and "end" in entry:
            rs.apply_range(int(entry["start"]), int(entry["end"]))
        self._log("[OK] Opened clip {0} - edit the controller keys directly, then Save Clip & Close.".format(entry["name"]))
        self.refresh_blendshapes()

    def on_save_close(self, *args):
        try:
            path = rs.save_open_clip()
        except (rs.ReviewError, RuntimeError) as e:
            self._log("[ERROR] {0}".format(str(e).strip()))
            return
        self._log("[OK] Saved {0}".format(path))
        name = os.path.splitext(os.path.basename(path))[0]
        if self.manifest is not None and any(e["name"] == name for e in self.clips):
            import time
            clip_manifest.update_clip(self.manifest, name, status=clip_manifest.STATUS_EDITED, edited_at=time.strftime("%Y-%m-%d %H:%M:%S"))
            try:
                clip_manifest.save(self.folder(), self.manifest)
            except OSError:
                pass
            self.load_folder()
        rs.new_scene()
        self.refresh_state()

    # ------------------------------------------------------------------ Help

    def on_open_guide(self, *args):
        try:
            file_opener.open_path(GUIDE_DOC)
        except (OSError, ValueError):
            self._log("[WARN] Guide not found: {0}".format(GUIDE_DOC))

    def show_about(self, *args):
        QMessageBox.information(self, "About", (
            "JALI Review v{0}\nUpdate date: {1}\n\n"
            "Reviews the JALI clip .mb files made by A00560_JaliBatch.\n\n"
            "1. Clips: pick the clip folder (manifest), set the Avatar, Build Review Scene.\n"
            "2. Connect ARKIT_OUT -> BlendShape (alias names; connections live on the avatar\n"
            "   reference, so they survive Swap).\n"
            "3. Turn on 'Allow edits on referenced animation curves' and fix keys.\n"
            "4. Save Clip Edits writes them into the clip (status 'edited'). Swap is blocked\n"
            "   while edits are unsaved - Maya would re-apply them at wrong times.\n"
            "5. Prev / Next / Swap to the next clip. Open Clip for deep edits.\n\n"
            "Written by Ji Hun Park.").format(VERSION, LAST_UPDATE))
