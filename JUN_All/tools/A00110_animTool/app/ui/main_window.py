# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00110_animTool - Qt UI

from Framework.qt.qt import *

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00110_animTool.app.config.version import VERSION
from tools.A00110_animTool.app.core import KeyframeManager


class MainWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.win_width  = 380
        self.win_height = 320
        self.win_title  = f"Anim Key Tool v{VERSION}"

        self.resize(self.win_width, self.win_height)

        self.build_ui()

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
        # 로그
        # -------------------------

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        main_layout.addWidget(self.te_log)

        # -------------------------
        # Signal
        # -------------------------

        self.btn_move_back.clicked.connect(lambda: self.on_move(-1))
        self.btn_move_fwd.clicked.connect(lambda: self.on_move(+1))
        self.btn_delete.clicked.connect(self.on_delete)

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
