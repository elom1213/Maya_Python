# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00120_FKIK - Qt UI (레거시 PY_JUN_makeUI_FKIKTool 대체)

from Framework.qt.qt import *

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00120_FKIK.app.config.version import VERSION
from tools.A00120_FKIK.app.core import (
    FKIKSetup,
    FKIKMatcher,
    search_by_token,
    selection_utils,
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

        self.lw_targets = self._make_edit_list("Targets")
        self.lw_followers = self._make_edit_list("Followers")

        row.addWidget(self.lw_targets["box"])
        row.addWidget(self.lw_followers["box"])

        root.addLayout(row)

    def _make_edit_list(self, title):
        """제목 + QListWidget + Add/Type/Del/Up/Down 버튼행 묶음 생성."""

        box = QGroupBox(title)
        layout = QVBoxLayout(box)

        lw = QListWidget()
        lw.setSelectionMode(QAbstractItemView.ExtendedSelection)
        lw.setMinimumHeight(180)
        lw.itemSelectionChanged.connect(lambda w=lw: self.on_list_selection(w))
        layout.addWidget(lw)

        btn_row = QHBoxLayout()

        btn_add  = QPushButton("Add")
        btn_type = QPushButton("Type")
        btn_del  = QPushButton("Del")
        btn_up   = QPushButton("Up")
        btn_down = QPushButton("Down")

        btn_add.clicked.connect(lambda _=False, w=lw: self.on_add_selected(w))
        btn_type.clicked.connect(lambda _=False, w=lw: self.on_add_by_type(w))
        btn_del.clicked.connect(lambda _=False, w=lw: self.on_del_selected(w))
        btn_up.clicked.connect(lambda _=False, w=lw: self.on_move_up(w))
        btn_down.clicked.connect(lambda _=False, w=lw: self.on_move_down(w))

        for b in (btn_add, btn_type, btn_del, btn_up, btn_down):
            btn_row.addWidget(b)

        layout.addLayout(btn_row)

        return {"box": box, "lw": lw}

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

    def _list_items(self, lw):
        return [lw.item(i).text() for i in range(lw.count())]

    def _selected_indices(self, lw):
        return sorted(lw.row(item) for item in lw.selectedItems())

    def _selected_texts(self, lw):
        return [item.text() for item in lw.selectedItems()]

    def _set_list_items(self, lw, items):
        lw.blockSignals(True)
        lw.clear()
        for it in items:
            lw.addItem(it)
        lw.blockSignals(False)

    def _select_rows(self, lw, indices):
        lw.blockSignals(True)
        lw.clearSelection()
        for idx in indices:
            if 0 <= idx < lw.count():
                lw.item(idx).setSelected(True)
        lw.blockSignals(False)

    def _select_texts(self, lw, texts):
        target = set(texts)
        lw.blockSignals(True)
        lw.clearSelection()
        for i in range(lw.count()):
            if lw.item(i).text() in target:
                lw.item(i).setSelected(True)
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

        self._set_list_items(self.lw_targets["lw"], result["targets"])
        self._set_list_items(self.lw_followers["lw"], result["followers"])

        self._set_state("State : Success", ok=True)
        self.log(
            f"Setup success : {len(result['targets'])} targets / "
            f"{len(result['followers'])} followers"
        )

    def on_list_selection(self, lw):
        texts = self._selected_texts(lw)
        if texts:
            cmds.select(texts)

    def on_add_selected(self, lw):
        existing = set(self._list_items(lw))
        sel = cmds.ls(sl=True, fl=True) or []
        for obj in sel:
            if obj in existing:
                self.log(f"{obj} is already in the list.")
                continue
            lw.addItem(obj)
            existing.add(obj)

    def on_add_by_type(self, lw):
        """현재 씬 선택의 각 objectType 별 첫 오브젝트만 추가. (레거시 add_type 정리)"""
        existing = set(self._list_items(lw))
        sel = cmds.ls(sl=True, fl=True) or []

        seen_types = set()
        for obj in sel:
            obj_type = cmds.objectType(obj)
            if obj_type in seen_types:
                continue
            seen_types.add(obj_type)
            if obj in existing:
                continue
            lw.addItem(obj)
            existing.add(obj)

    def on_del_selected(self, lw):
        for idx in sorted(self._selected_indices(lw), reverse=True):
            lw.takeItem(idx)

    def on_move_up(self, lw):
        items = self._list_items(lw)
        indices = self._selected_indices(lw)
        new_items, new_indices = selection_utils.move_up(items, indices)
        self._set_list_items(lw, new_items)
        self._select_rows(lw, new_indices)

    def on_move_down(self, lw):
        items = self._list_items(lw)
        indices = self._selected_indices(lw)
        new_items, new_indices = selection_utils.move_down(items, indices)
        self._set_list_items(lw, new_items)
        self._select_rows(lw, new_indices)

    def on_search(self):
        token = self.le_search.text().strip()
        if not token:
            self.log("[Warning] Enter a search token.")
            return

        invert = self.cb_invert.isChecked()
        matched_all = []

        for entry in (self.lw_targets, self.lw_followers):
            lw = entry["lw"]
            matched = search_by_token(self._list_items(lw), token, invert)
            self._select_texts(lw, matched)
            matched_all.extend(matched)

        if matched_all:
            cmds.select(matched_all)

        self.log(f"Search '{token}' (invert={invert}) : {len(matched_all)} matched")

    def on_match(self, ik_to_fk):
        all_t = self._list_items(self.lw_targets["lw"])
        all_f = self._list_items(self.lw_followers["lw"])

        tgt, flw = FKIKMatcher.build_pairs(
            all_t, all_f,
            self.cb_arm_l.isChecked(), self.cb_arm_r.isChecked(),
            self.cb_leg_l.isChecked(), self.cb_leg_r.isChecked(),
            ik_to_fk,
        )

        if not tgt or not flw:
            self.log("[Warning] No pairs to match. Run Setup and check limb options.")
            return

        self._select_texts(self.lw_targets["lw"], tgt)
        self._select_texts(self.lw_followers["lw"], flw)

        count = FKIKMatcher.match(tgt, flw)

        mode = "IK" if ik_to_fk else "FK"
        self.log(f"Match {mode} : {count} pairs matched")

    def on_bake(self, ik_to_fk):
        all_t = self._list_items(self.lw_targets["lw"])
        all_f = self._list_items(self.lw_followers["lw"])

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

        self._select_texts(self.lw_targets["lw"], tgt)
        self._select_texts(self.lw_followers["lw"], flw)

        frames = FKIKMatcher.bake(tgt, flw, start, end)

        mode = "IK" if ik_to_fk else "FK"
        self.log(f"Bake {mode} : {frames} frames baked [{start}-{end}]")

    def on_bake_constraint(self):
        tgt = self._selected_texts(self.lw_targets["lw"])
        flw = self._selected_texts(self.lw_followers["lw"])

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
