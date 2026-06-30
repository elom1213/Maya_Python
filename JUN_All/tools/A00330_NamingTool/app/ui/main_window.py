# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-30
# A00330_NamingTool - Qt UI
#
# 레거시 maya.cmds 네이밍 툴(JUN_PY_NamingTool_V03_04)을 PySide + QTabWidget 으로 이식.
#   - Naming Dyn   탭 : 계층 토큰 네이밍 (legacy Naming Dynamics)
#   - Copy Name    탭 : base 이름을 target 에 prefix 부착 복사 (legacy Copy name)
#   - Quick Rename 탭 : Front Insert / Change New / Last Add / -1 trim (ref/ref_01.mel 이식, NEW)
# 리스트 UI 는 공용 위젯 JUN_mod_tsl_qt_v01, 로직은 app/core. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

from tools.A00330_NamingTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00330_NamingTool.app import core


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00330_NamingTool_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Naming Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(560, 720)

        self.build_ui()

    # ================================================================
    # UI
    # ================================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 공용 로그창 (탭 빌더가 self._log / TSL log_callback 을 쓰므로 탭보다 먼저 생성)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(110)

        # 탭: Naming Dyn / Copy Name / Quick Rename
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_naming_dyn_tab(), "Naming Dyn")
        self.tabs.addTab(self._build_copy_name_tab(), "Copy Name")
        self.tabs.addTab(self._build_quick_rename_tab(), "Quick Rename")
        main_layout.addWidget(self.tabs, stretch=1)

        # 로그창
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    # ================================================================
    # Tab 1 : Naming Dyn  (legacy Naming Dynamics)
    # ================================================================

    def _build_naming_dyn_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        # Objects 리스트 (Select / Add / Del / Up / Down / Sort)
        self.dyn_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="Select Base",
            log_callback=self._log)
        root.addWidget(self.dyn_tsl, stretch=1)

        # 토큰 / 인덱스 / 패딩 입력
        grid = QGridLayout()
        labels = ["Token 1", "Token 2", "Token 3", "Index 1", "Index 2"]
        for col, text in enumerate(labels):
            grid.addWidget(QLabel(text), 0, col)

        self.dyn_le_token1 = QLineEdit("dyn")
        self.dyn_le_token2 = QLineEdit("asset")
        self.dyn_le_token3 = QLineEdit("side")
        self.dyn_le_index1 = QLineEdit("0")
        self.dyn_le_index2 = QLineEdit("0")
        for col, widget in enumerate([
                self.dyn_le_token1, self.dyn_le_token2, self.dyn_le_token3,
                self.dyn_le_index1, self.dyn_le_index2]):
            grid.addWidget(widget, 1, col)

        # 패딩 행 (Index 1 / Index 2 아래에만)
        grid.addWidget(QLabel("pad 0"), 2, 3)
        grid.addWidget(QLabel("pad 0"), 2, 4)
        self.dyn_le_pad1 = QLineEdit("2")
        self.dyn_le_pad2 = QLineEdit("2")
        grid.addWidget(self.dyn_le_pad1, 3, 3)
        grid.addWidget(self.dyn_le_pad2, 3, 4)
        root.addLayout(grid)

        # 실행 버튼
        btn = QPushButton("Naming Dynamics")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Rename each object (and its transform descendants) to "
            "'Token1_Token2_Token3_Index1_Index2'. Index1 increments per root "
            "group, Index2 per item within a group.")
        btn.clicked.connect(self.on_dyn_rename)
        root.addWidget(btn)

        return tab

    def on_dyn_rename(self):
        objects = self.dyn_tsl.get_all_items()
        if not objects:
            self._log("[WARN] Objects list is empty. Use Select Base first.")
            return
        try:
            pad1 = int(self.dyn_le_pad1.text() or "0")
            pad2 = int(self.dyn_le_pad2.text() or "0")
            index1 = int(self.dyn_le_index1.text() or "0")
            index2 = int(self.dyn_le_index2.text() or "0")
        except ValueError:
            self._log("[WARN] Index / pad must be integers.")
            return

        with core.undo_chunk():
            count = core.rename_dynamics(
                objects,
                self.dyn_le_token1.text(),
                self.dyn_le_token2.text(),
                self.dyn_le_token3.text(),
                index1, index2, pad1, pad2)
        self._log("Naming Dynamics : {0} node(s) renamed.".format(count))

    # ================================================================
    # Tab 2 : Copy Name  (legacy Copy name)
    # ================================================================

    def _build_copy_name_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        # Base | Targets (좌우)
        self.copy_base_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Base", select_label="Select Base",
            log_callback=self._log)
        self.copy_tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Targets", select_label="Select Targets",
            log_callback=self._log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.copy_base_tsl)
        list_row.addWidget(self.copy_tgt_tsl)
        root.addLayout(list_row, stretch=1)

        # Prefix
        prefix_row = QHBoxLayout()
        prefix_row.addWidget(QLabel("Prefix :"))
        self.copy_le_prefix = QLineEdit()
        self.copy_le_prefix.setPlaceholderText("optional prefix for new names")
        prefix_row.addWidget(self.copy_le_prefix)
        root.addLayout(prefix_row)

        # 실행 버튼
        btn = QPushButton("Copy Name")
        btn.setMinimumHeight(32)
        btn.setToolTip(
            "Rename each Targets item to (Prefix + the matching Base item's "
            "leaf name), in list order.")
        btn.clicked.connect(self.on_copy_name)
        root.addWidget(btn)

        return tab

    def on_copy_name(self):
        base_items = self.copy_base_tsl.get_all_items()
        target_items = self.copy_tgt_tsl.get_all_items()
        if not base_items or not target_items:
            self._log("[WARN] Both Base and Targets lists must be filled.")
            return

        with core.undo_chunk():
            new_names, warning = core.copy_name(
                base_items, target_items, self.copy_le_prefix.text())
        if warning:
            self._log("[WARN] " + warning)

        # Targets 리스트를 새 이름으로 갱신
        if new_names:
            self.copy_tgt_tsl.set_items(new_names)
        self._log("Copy Name : {0} target(s) renamed.".format(len(new_names)))

    # ================================================================
    # Tab 3 : Quick Rename  (ref/ref_01.mel 이식, 현재 선택 기준)
    # ================================================================

    def _build_quick_rename_tab(self):
        tab = QWidget()
        root = QVBoxLayout(tab)

        note = QLabel("Operates on the current Maya selection.")
        note.setAlignment(Qt.AlignCenter)
        root.addWidget(note)

        # 상단: -1 Front / All Apply
        top_row = QHBoxLayout()
        btn_trim_front = QPushButton("-1 Front")
        btn_trim_front.setToolTip("Remove the first character of each name.")
        btn_trim_front.clicked.connect(self.on_trim_front)
        top_row.addWidget(btn_trim_front)
        btn_all = QPushButton("All Apply")
        btn_all.setToolTip("Apply Change New, then Front Insert, then Last Add.")
        btn_all.clicked.connect(self.on_all_apply)
        top_row.addWidget(btn_all)
        root.addLayout(top_row)

        # 입력 + 개별 적용 버튼
        form = QGridLayout()

        form.addWidget(QLabel("Front Insert"), 0, 0)
        self.qr_le_insert = QLineEdit()
        form.addWidget(self.qr_le_insert, 0, 1)
        btn_insert = QPushButton("Insert Apply")
        btn_insert.setToolTip("Prepend the text to each selected name.")
        btn_insert.clicked.connect(self.on_insert_apply)
        form.addWidget(btn_insert, 0, 2)

        form.addWidget(QLabel("Change New"), 1, 0)
        self.qr_le_new = QLineEdit()
        form.addWidget(self.qr_le_new, 1, 1)
        btn_new = QPushButton("New Apply")
        btn_new.setToolTip(
            "Rename to the new name + incrementing index. With Start empty: "
            "multiple selection appends 01, 02, ...; single selection has no "
            "number.")
        btn_new.clicked.connect(self.on_new_apply)
        form.addWidget(btn_new, 1, 2)

        form.addWidget(QLabel("Start (Index)"), 2, 0)
        self.qr_le_index = QLineEdit()
        self.qr_le_index.setPlaceholderText("empty = auto from 1")
        self.qr_le_index.setFixedWidth(120)
        form.addWidget(self.qr_le_index, 2, 1)

        form.addWidget(QLabel("Last Add"), 3, 0)
        self.qr_le_add = QLineEdit()
        form.addWidget(self.qr_le_add, 3, 1)
        btn_add = QPushButton("Add Apply")
        btn_add.setToolTip("Append the text to each selected name.")
        btn_add.clicked.connect(self.on_add_apply)
        form.addWidget(btn_add, 3, 2)

        root.addLayout(form)

        # 하단: -1 Rear
        btn_trim_rear = QPushButton("-1 Rear")
        btn_trim_rear.setToolTip("Remove the last character of each name.")
        btn_trim_rear.clicked.connect(self.on_trim_rear)
        root.addWidget(btn_trim_rear)

        root.addStretch(1)
        return tab

    def on_insert_apply(self):
        with core.undo_chunk():
            count = core.insert_front(self.qr_le_insert.text())
        self._log("Front Insert : {0} renamed.".format(count))

    def on_add_apply(self):
        with core.undo_chunk():
            count = core.add_rear(self.qr_le_add.text())
        self._log("Last Add : {0} renamed.".format(count))

    def on_new_apply(self):
        with core.undo_chunk():
            count, error = core.change_new(
                self.qr_le_new.text(), self.qr_le_index.text())
        if error:
            self._log("[WARN] " + error)
        else:
            self._log("Change New : {0} renamed.".format(count))

    def on_trim_front(self):
        with core.undo_chunk():
            count = core.trim_front()
        self._log("-1 Front : {0} renamed.".format(count))

    def on_trim_rear(self):
        with core.undo_chunk():
            count = core.trim_rear()
        self._log("-1 Rear : {0} renamed.".format(count))

    def on_all_apply(self):
        with core.undo_chunk():
            messages = core.all_apply(
                self.qr_le_new.text(), self.qr_le_index.text(),
                self.qr_le_insert.text(), self.qr_le_add.text())
        for message in messages:
            self._log("All Apply " + message)

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def show_about(self, *args):
        message = (
            "Naming Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Qt port of legacy JUN_PY_NamingTool_V03_04, plus a new tab.\n"
            "\n"
            "[Naming Dyn] hierarchy token naming:\n"
            "  Token1_Token2_Token3_Index1_Index2 over each object and its\n"
            "  transform descendants.\n"
            "\n"
            "[Copy Name] copy Base leaf names onto Targets with a prefix.\n"
            "\n"
            "[Quick Rename] (ported from ref/ref_01.mel, current selection):\n"
            "  Front Insert / Change New (+index) / Last Add / -1 trim / All Apply.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
