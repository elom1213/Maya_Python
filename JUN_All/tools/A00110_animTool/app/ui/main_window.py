# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-15
# A00110_animTool - Qt UI

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00110_animTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00110_animTool.app.core import KeyframeManager
from tools.A00110_animTool.app.core import HotkeyManager
from tools.A00110_animTool.app.core import PoseKeyManager
from tools.A00110_animTool.app.core import CopyKeyManager


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00110_animTool_window"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width  = 520
        self.win_height = 600
        self.win_title  = f"Anim Key Tool v{VERSION}"

        self.resize(self.win_width, self.win_height)

        self.build_ui()

        # 툴 실행 중 Shift+A 핫키 바인딩 (창 종료 시 closeEvent 에서 복원)
        self.hotkey_mgr = HotkeyManager()
        self._enable_hotkey(self.cb_hotkey.isChecked())

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)

        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowStaysOnTopHint
        )

        main_layout = QVBoxLayout(self)

        # -------------------------
        # 메뉴 바 (Help > About)
        # jointTool 의 cmds.menu('Help') / cmds.menuItem('About') 패턴을 Qt 로 옮김
        # -------------------------

        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # -------------------------
        # 탭: Key Edit / Pose Key
        # (참고로 든 BSTool 의 cmds.tabLayout 을 Qt QTabWidget 으로 대응)
        # -------------------------

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_key_edit_tab(), "Key Edit")
        self.tabs.addTab(self._build_pose_key_tab(), "Pose Key")
        self.tabs.addTab(self._build_copy_key_tab(), "Copy Key")
        main_layout.addWidget(self.tabs)

        # -------------------------
        # 로그 (두 탭 공유)
        # -------------------------

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        main_layout.addWidget(self.te_log)

        # -------------------------
        # 저작권 (공통)
        # -------------------------

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------
    # Tab builders
    # --------------------------------------------------

    def _build_key_edit_tab(self):
        """기존 키 이동/삭제/hold 기능 탭."""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Frame range / offset 입력
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)

        row = QHBoxLayout()

        row.addWidget(QLabel("Start"))
        self.le_start = QLineEdit()
        self.le_start.setValidator(validator)
        self.le_start.setPlaceholderText("4")
        row.addWidget(self.le_start)

        row.addWidget(QLabel("End"))
        self.le_end = QLineEdit()
        self.le_end.setValidator(validator)
        self.le_end.setPlaceholderText("10")
        row.addWidget(self.le_end)

        row.addWidget(QLabel("Offset"))
        self.le_offset = QLineEdit()
        self.le_offset.setValidator(QIntValidator(0, 1000000, self))
        self.le_offset.setPlaceholderText("5")
        row.addWidget(self.le_offset)

        tab_layout.addLayout(row)

        # -------------------------
        # 이동 버튼
        # -------------------------

        row = QHBoxLayout()

        self.btn_move_back = QPushButton("◀ Earlier (-)")
        self.btn_move_fwd  = QPushButton("Later (+) ▶")

        row.addWidget(self.btn_move_back)
        row.addWidget(self.btn_move_fwd)

        tab_layout.addLayout(row)

        # -------------------------
        # 삭제 버튼
        # -------------------------

        self.btn_delete = QPushButton("Delete Keys in Range")
        tab_layout.addWidget(self.btn_delete)

        # -------------------------
        # Graph Editor 구간 유지(hold)
        # -------------------------

        grp = QGroupBox("Graph Editor")
        grp_layout = QVBoxLayout(grp)

        self.btn_hold = QPushButton("Hold Selected Range")
        grp_layout.addWidget(self.btn_hold)

        self.cb_hotkey = QCheckBox("Shift+A hotkey")
        self.cb_hotkey.setChecked(True)
        grp_layout.addWidget(self.cb_hotkey)

        self.lbl_hotkey = QLabel("")
        grp_layout.addWidget(self.lbl_hotkey)

        tab_layout.addWidget(grp)

        tab_layout.addStretch(1)

        # -------------------------
        # Signal
        # -------------------------

        self.btn_move_back.clicked.connect(lambda: self.on_move(-1))
        self.btn_move_fwd.clicked.connect(lambda: self.on_move(+1))
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_hold.clicked.connect(self.on_hold)
        self.cb_hotkey.toggled.connect(self.on_toggle_hotkey)

        return tab

    def _build_pose_key_tab(self):
        """선택 오브젝트 현재 프레임에 6축 pose 키를 설정하는 탭.
        축마다 체크박스가 있고, 체크된 축만 입력값으로 키를 설정한다.
        기본 체크: rotate X, rotate Z, translate Y. (A00030 원본 3축)"""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        grp = QGroupBox("Set Pose Key (current frame)")
        grp_layout = QVBoxLayout(grp)

        # 기본 체크 축
        default_on = {"rx", "rz", "ty"}

        # attr -> (checkbox, lineedit)
        self.pose_rows = {}

        for attr, label in PoseKeyManager.AXES:

            row = QHBoxLayout()

            cb = QCheckBox()
            cb.setChecked(attr in default_on)
            row.addWidget(cb)

            lbl = QLabel(label)
            lbl.setMinimumWidth(80)
            row.addWidget(lbl)

            le = QLineEdit("0")
            le.setValidator(QDoubleValidator(-1000000.0, 1000000.0, 4, self))
            row.addWidget(le)

            grp_layout.addLayout(row)

            self.pose_rows[attr] = (cb, le)

        tab_layout.addWidget(grp)

        self.btn_set_pose = QPushButton("Set Pose Key")
        tab_layout.addWidget(self.btn_set_pose)

        tab_layout.addStretch(1)

        self.btn_set_pose.clicked.connect(self.on_set_pose)

        return tab

    def _build_copy_key_tab(self):
        """Base -> Target 으로 시간 범위 애니메이션 키를 복사하고 축별로 값을 반전하는 탭.
        레거시 JUN_PY_CopyPasteKey_V03_01 의 Copy Key Tool 을 Qt 로 포팅.
        Base/Target 리스트는 재사용 위젯 JUN_mod_tsl_qt_v01 2개로 구성한다."""

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Base / Target 리스트 (재사용 위젯, 가로 2분할)
        # Select / Add / Del / Up / Down / Sort / 카운트 / 씬 선택은 위젯이 내장.
        # -------------------------

        self.base_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Base", select_label="Select Base", log_callback=self.log)
        self.tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Target", select_label="Select Targets", log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.base_tsl)
        list_row.addWidget(self.tgt_tsl)
        tab_layout.addLayout(list_row)

        # -------------------------
        # Time range (start / end). 기본값은 현재 playback 범위.
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)

        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Start"))
        self.le_copy_start = QLineEdit(str(time_str))
        self.le_copy_start.setValidator(validator)
        range_row.addWidget(self.le_copy_start)

        range_row.addWidget(QLabel("End"))
        self.le_copy_end = QLineEdit(str(time_end))
        self.le_copy_end.setValidator(validator)
        range_row.addWidget(self.le_copy_end)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Paste Option (cmds.pasteKey option). 기본 "insert".
        # -------------------------

        option_row = QHBoxLayout()
        option_row.addWidget(QLabel("Paste Option"))
        self.cmb_paste_option = QComboBox()
        self.cmb_paste_option.addItems(CopyKeyManager.PASTE_OPTIONS)
        self.cmb_paste_option.setCurrentText("insert")
        option_row.addWidget(self.cmb_paste_option)
        option_row.addStretch(1)
        tab_layout.addLayout(option_row)

        # -------------------------
        # Reverse 체크박스 (Translate X/Y/Z, Rotate X/Y/Z). 기본 모두 off.
        # -------------------------

        rev_grp = QGroupBox("Reverse")
        rev_layout = QHBoxLayout(rev_grp)

        # attr key -> checkbox. CopyKeyManager.AXES 키와 일치.
        self.copy_reverse = {}

        rev_layout.addWidget(QLabel("Translate"))
        for key, label in (("tx", "X"), ("ty", "Y"), ("tz", "Z")):
            cb = QCheckBox(label)
            self.copy_reverse[key] = cb
            rev_layout.addWidget(cb)

        rev_layout.addSpacing(12)

        rev_layout.addWidget(QLabel("Rotate"))
        for key, label in (("rx", "X"), ("ry", "Y"), ("rz", "Z")):
            cb = QCheckBox(label)
            self.copy_reverse[key] = cb
            rev_layout.addWidget(cb)

        rev_layout.addStretch(1)
        tab_layout.addWidget(rev_grp)

        # -------------------------
        # Copy 버튼
        # -------------------------

        self.btn_copy_key = QPushButton("Copy Key")
        tab_layout.addWidget(self.btn_copy_key)

        tab_layout.addStretch(1)

        self.btn_copy_key.clicked.connect(self.on_copy_key)

        return tab

    # --------------------------------------------------
    # Helper
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def _read_range(self):
        """start, end 파싱. 실패 시 None."""
        s_txt = self.le_start.text().strip()
        e_txt = self.le_end.text().strip()

        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return None

        start = int(s_txt)
        end = int(e_txt)

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return None

        return (start, end)

    def _read_offset(self):
        """offset(양수) 파싱. 실패 시 None."""
        o_txt = self.le_offset.text().strip()

        if o_txt == "":
            self.log("[Warning] Enter Offset.")
            return None

        return abs(int(o_txt))

    # --------------------------------------------------
    # Handlers
    # --------------------------------------------------

    def on_move(self, sign):

        rng = self._read_range()
        if rng is None:
            return

        offset = self._read_offset()
        if offset is None:
            return

        start, end = rng
        offset = sign * offset   # 앞으로(-) / 뒤로(+)

        count, msg = KeyframeManager.move_keys(start, end, offset)
        self.log(msg)

    def on_delete(self):

        rng = self._read_range()
        if rng is None:
            return

        start, end = rng

        count, msg = KeyframeManager.delete_keys(start, end)
        self.log(msg)

    def on_hold(self):

        count, msg = KeyframeManager.hold_selected_keys()
        self.log(msg)

    def on_set_pose(self):

        # 체크된 축만 모은다. 체크됐는데 값이 비어 있으면 경고 후 중단.
        axis_values = {}
        for attr, (cb, le) in self.pose_rows.items():
            if not cb.isChecked():
                continue
            txt = le.text().strip()
            if txt == "":
                self.log(f"[Warning] {attr} is checked but empty.")
                return
            axis_values[attr] = float(txt)

        if not axis_values:
            self.log("[Warning] No axis checked.")
            return

        count, msg = PoseKeyManager.set_pose_keys(axis_values)
        self.log(msg)

    def on_copy_key(self):

        base = self.base_tsl.get_all_items()
        tgt = self.tgt_tsl.get_all_items()

        if not base or not tgt:
            self.log("[Warning] Fill both Base and Target lists.")
            return

        # Start / End 파싱 (Copy 탭 전용).
        s_txt = self.le_copy_start.text().strip()
        e_txt = self.le_copy_end.text().strip()

        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return

        start = int(s_txt)
        end = int(e_txt)

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return

        reverse_flags = {key: cb.isChecked() for key, cb in self.copy_reverse.items()}
        paste_option = self.cmb_paste_option.currentText()

        count, msg = CopyKeyManager.copy_keys(base, tgt, start, end, reverse_flags, paste_option)
        self.log(msg)

    def show_about(self, *args):
        # jointTool 의 show_about(confirmDialog) 패턴을 Qt 로 옮김
        QMessageBox.information(
            self,
            "About",
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}",
        )

    # --------------------------------------------------
    # Hotkey
    # --------------------------------------------------

    def on_toggle_hotkey(self, checked):
        self._enable_hotkey(checked)

    def _enable_hotkey(self, on):
        """체크 상태에 따라 Shift+A 핫키를 설치/복원하고 상태 라벨을 갱신."""
        if on:
            ok, msg = self.hotkey_mgr.install()
            self.lbl_hotkey.setText("Shift+A : ON" if ok else "Shift+A : unavailable")
        else:
            self.hotkey_mgr.restore()
            msg = "Shift+A hotkey disabled."
            self.lbl_hotkey.setText("Shift+A : OFF")

        self.log(msg)

    # --------------------------------------------------
    # Teardown
    # --------------------------------------------------

    def closeEvent(self, event):
        # 창이 닫힐 때 Shift+A 를 원래 바인딩으로 복원
        try:
            if getattr(self, "hotkey_mgr", None):
                self.hotkey_mgr.restore()
        finally:
            super().closeEvent(event)
