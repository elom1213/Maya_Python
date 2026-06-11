# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00120_FKIK - Qt UI (레거시 PY_JUN_makeUI_FKIKTool 대체)

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00120_FKIK.app.config.version import VERSION
from tools.A00120_FKIK.app.core import (
    FKIKSetup,
    FKIKMatcher,
    search_by_token,
)


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.win_width  = 480
        self.win_height = 760
        self.win_title  = f"FKIK Tool v{VERSION}"

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    # ==================================================
    # UI 구성
    # ==================================================

    def build_ui(self):

        self.setWindowTitle(self.win_title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        root = QVBoxLayout(self)

        self._build_setup_section(root)
        self._build_limb_section(root)
        self._build_lists_section(root)
        self._build_search_section(root)
        self._build_match_bake_section(root)
        self._build_log_section(root)

    # --------------------------------------------------
    # Setup
    # --------------------------------------------------

    def _build_setup_section(self, root):

        box = QGroupBox("Setup")
        layout = QVBoxLayout(box)

        row = QHBoxLayout()

        self.lw_rig = QListWidget()
        self.lw_rig.setFixedHeight(50)
        self.lw_rig.setSelectionMode(QAbstractItemView.ExtendedSelection)
        row.addWidget(self.lw_rig)

        self.btn_setup = QPushButton("Select Objects")
        self.btn_setup.clicked.connect(self.on_setup)
        row.addWidget(self.btn_setup)

        layout.addLayout(row)

        self.lbl_state = QLabel("State : Waiting...")
        self.lbl_state.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._set_state("State : Waiting...", ok=None)
        layout.addWidget(self.lbl_state)

        root.addWidget(box)

    # --------------------------------------------------
    # Limb checkboxes
    # --------------------------------------------------

    def _build_limb_section(self, root):

        row = QHBoxLayout()

        arm_box = QGroupBox("Arm")
        arm_layout = QVBoxLayout(arm_box)
        self.cb_arm_l = QCheckBox("Arm Left")
        self.cb_arm_r = QCheckBox("Arm Right")
        self.cb_arm_l.setChecked(True)
        self.cb_arm_r.setChecked(True)
        arm_layout.addWidget(self.cb_arm_l)
        arm_layout.addWidget(self.cb_arm_r)
        row.addWidget(arm_box)

        leg_box = QGroupBox("Leg")
        leg_layout = QVBoxLayout(leg_box)
        self.cb_leg_l = QCheckBox("Leg Left")
        self.cb_leg_r = QCheckBox("Leg Right")
        self.cb_leg_l.setChecked(True)
        self.cb_leg_r.setChecked(True)
        leg_layout.addWidget(self.cb_leg_l)
        leg_layout.addWidget(self.cb_leg_r)
        row.addWidget(leg_box)

        root.addLayout(row)

    # --------------------------------------------------
    # Targets / Followers lists
    # --------------------------------------------------

    def _build_lists_section(self, root):

        row = QHBoxLayout()

        # 재사용 PySide tsl 위젯(Framework.qt.MOD_tsl_qt_v01) 사용.
        # A00140_ConnectClosest 와 동일한 형식. Select/Add/Del/Up/Down/Sort/씬 선택은 위젯이 자체 처리한다.
        self.tsl_targets = self._make_edit_list("Targets")
        self.tsl_followers = self._make_edit_list("Followers")

        row.addWidget(self.tsl_targets)
        row.addWidget(self.tsl_followers)

        root.addLayout(row)

    def _make_edit_list(self, title):
        """A00140_ConnectClosest 와 동일한 형식의 재사용 tsl 위젯(Select/Add/Del/Up/Down/Sort)."""

        return JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title=title)

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def _build_search_section(self, root):

        box = QGroupBox("Search")
        row = QHBoxLayout(box)

        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("token")
        row.addWidget(self.le_search)

        self.cb_invert = QCheckBox("Invert")
        row.addWidget(self.cb_invert)

        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self.on_search)
        row.addWidget(self.btn_search)

        root.addWidget(box)

    # --------------------------------------------------
    # Match / Bake
    # --------------------------------------------------

    def _build_match_bake_section(self, root):

        box = QGroupBox("Match / Bake")
        layout = QVBoxLayout(box)

        # frame range
        frame_row = QHBoxLayout()
        frame_row.addWidget(QLabel("Start"))
        self.sb_start = QSpinBox()
        self.sb_start.setRange(-1000000, 1000000)
        frame_row.addWidget(self.sb_start)
        frame_row.addWidget(QLabel("End"))
        self.sb_end = QSpinBox()
        self.sb_end.setRange(-1000000, 1000000)
        frame_row.addWidget(self.sb_end)
        layout.addLayout(frame_row)

        self._init_frame_range()

        # match
        match_row = QHBoxLayout()
        self.btn_match_ik = QPushButton("Match IK")
        self.btn_match_fk = QPushButton("Match FK")
        self.btn_match_ik.clicked.connect(lambda: self.on_match(ik_to_fk=True))
        self.btn_match_fk.clicked.connect(lambda: self.on_match(ik_to_fk=False))
        match_row.addWidget(self.btn_match_ik)
        match_row.addWidget(self.btn_match_fk)
        layout.addLayout(match_row)

        # bake
        bake_row = QHBoxLayout()
        self.btn_bake_ik = QPushButton("Bake IK")
        self.btn_bake_fk = QPushButton("Bake FK")
        self.btn_bake_ik.clicked.connect(lambda: self.on_bake(ik_to_fk=True))
        self.btn_bake_fk.clicked.connect(lambda: self.on_bake(ik_to_fk=False))
        bake_row.addWidget(self.btn_bake_ik)
        bake_row.addWidget(self.btn_bake_fk)
        layout.addLayout(bake_row)

        self.btn_bake_constraint = QPushButton("Bake (Constraint)")
        self.btn_bake_constraint.clicked.connect(self.on_bake_constraint)
        layout.addWidget(self.btn_bake_constraint)

        root.addWidget(box)

    # --------------------------------------------------
    # Log
    # --------------------------------------------------

    def _build_log_section(self, root):

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setFixedHeight(90)
        root.addWidget(self.te_log)

    # ==================================================
    # Helpers
    # ==================================================

    def log(self, text):
        self.te_log.append(text)

    def _init_frame_range(self):
        try:
            start = int(cmds.playbackOptions(q=True, minTime=True))
            end = int(cmds.playbackOptions(q=True, maxTime=True))
            self.sb_start.setValue(start)
            self.sb_end.setValue(end)
        except Exception:
            pass

    def _set_state(self, text, ok=None):
        self.lbl_state.setText(text)
        if ok is True:
            color = "background-color: rgb(60, 170, 60); color: black;"
        elif ok is False:
            color = "background-color: rgb(200, 60, 60); color: black;"
        else:
            color = "background-color: rgb(220, 220, 220); color: black;"
        self.lbl_state.setStyleSheet(color)

    def _set_list_items(self, lw, items):
        # Setup 의 lw_rig(일반 QListWidget) 채우기용. (Targets/Followers 는 tsl 위젯 사용)
        lw.blockSignals(True)
        lw.clear()
        for it in items:
            lw.addItem(it)
        lw.blockSignals(False)

    # ==================================================
    # Handlers
    # ==================================================

    def on_setup(self):
        selection = cmds.ls(sl=True, fl=True)

        self._set_list_items(self.lw_rig, selection or [])

        result = FKIKSetup.resolve(selection)

        if not result["ok"]:
            self._set_state("State : " + result["message"], ok=False)
            self.log(result["message"])
            return

        self.tsl_targets.set_items(result["targets"])
        self.tsl_followers.set_items(result["followers"])

        self._set_state("State : Success", ok=True)
        self.log(
            f"Setup success : {len(result['targets'])} targets / "
            f"{len(result['followers'])} followers"
        )

    def on_search(self):
        token = self.le_search.text().strip()
        if not token:
            self.log("[Warning] Enter a search token.")
            return

        invert = self.cb_invert.isChecked()
        matched_all = []

        for tsl in (self.tsl_targets, self.tsl_followers):
            matched = search_by_token(tsl.get_all_items(), token, invert)
            tsl.select_by_texts(matched)
            matched_all.extend(matched)

        if matched_all:
            cmds.select(matched_all)

        self.log(f"Search '{token}' (invert={invert}) : {len(matched_all)} matched")

    def on_match(self, ik_to_fk):
        all_t = self.tsl_targets.get_all_items()
        all_f = self.tsl_followers.get_all_items()

        tgt, flw = FKIKMatcher.build_pairs(
            all_t, all_f,
            self.cb_arm_l.isChecked(), self.cb_arm_r.isChecked(),
            self.cb_leg_l.isChecked(), self.cb_leg_r.isChecked(),
            ik_to_fk,
        )

        if not tgt or not flw:
            self.log("[Warning] No pairs to match. Run Setup and check limb options.")
            return

        self.tsl_targets.select_by_texts(tgt)
        self.tsl_followers.select_by_texts(flw)

        count = FKIKMatcher.match(tgt, flw)

        mode = "IK" if ik_to_fk else "FK"
        self.log(f"Match {mode} : {count} pairs matched")

    def on_bake(self, ik_to_fk):
        all_t = self.tsl_targets.get_all_items()
        all_f = self.tsl_followers.get_all_items()

        tgt, flw = FKIKMatcher.build_pairs(
            all_t, all_f,
            self.cb_arm_l.isChecked(), self.cb_arm_r.isChecked(),
            self.cb_leg_l.isChecked(), self.cb_leg_r.isChecked(),
            ik_to_fk,
        )

        if not tgt or not flw:
            self.log("[Warning] No pairs to bake. Run Setup and check limb options.")
            return

        start = self.sb_start.value()
        end = self.sb_end.value()

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return

        self.tsl_targets.select_by_texts(tgt)
        self.tsl_followers.select_by_texts(flw)

        frames = FKIKMatcher.bake(tgt, flw, start, end)

        mode = "IK" if ik_to_fk else "FK"
        self.log(f"Bake {mode} : {frames} frames baked [{start}-{end}]")

    def on_bake_constraint(self):
        tgt = self.tsl_targets.selected_items()
        flw = self.tsl_followers.selected_items()

        if not tgt or not flw:
            self.log("[Warning] Select matching items in both Targets and Followers.")
            return

        if len(tgt) != len(flw):
            self.log(
                f"[Warning] Count mismatch : {len(tgt)} targets vs {len(flw)} followers."
            )
            return

        count = FKIKMatcher.bake_constraint(tgt, flw)
        self.log(f"Bake (Constraint) : {count} pairs baked")
