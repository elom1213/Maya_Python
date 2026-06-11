# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-11
# A00110_animTool - Qt UI

from Framework.qt.qt import *

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00110_animTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00110_animTool.app.core import KeyframeManager
from tools.A00110_animTool.app.core import HotkeyManager


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00110_animTool_window"


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width  = 380
        self.win_height = 460
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

        main_layout.addLayout(row)

        # -------------------------
        # 이동 버튼
        # -------------------------

        row = QHBoxLayout()

        self.btn_move_back = QPushButton("◀ Earlier (-)")
        self.btn_move_fwd  = QPushButton("Later (+) ▶")

        row.addWidget(self.btn_move_back)
        row.addWidget(self.btn_move_fwd)

        main_layout.addLayout(row)

        # -------------------------
        # 삭제 버튼
        # -------------------------

        self.btn_delete = QPushButton("Delete Keys in Range")
        main_layout.addWidget(self.btn_delete)

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

        main_layout.addWidget(grp)

        # -------------------------
        # 로그
        # -------------------------

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        main_layout.addWidget(self.te_log)

        # -------------------------
        # 저작권
        # -------------------------

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

        # -------------------------
        # Signal
        # -------------------------

        self.btn_move_back.clicked.connect(lambda: self.on_move(-1))
        self.btn_move_fwd.clicked.connect(lambda: self.on_move(+1))
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_hold.clicked.connect(self.on_hold)
        self.cb_hotkey.toggled.connect(self.on_toggle_hotkey)

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
