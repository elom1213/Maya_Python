# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-03
# A00040_file_exporter_V02 - Qt UI
#
# 레거시 maya.cmds 툴(A00040_file_exporter/file_exporter_v01)을 PySide 로 재작업했다.
#   - Export path : FBX 를 저장할 폴더 선택
#   - Type Filter : 드롭다운 체크로 내보낼 노드 타입 포함/제외 (mesh / joint, 확장 가능) [NEW]
#   - Set's Name / File name : 내보낼 objectSet 목록과 결과 파일명(TSL)
#   - Naming      : 토큰 조합으로 파일명 자동 생성 (Custom / Set's Name 모드)
# 리스트 UI 는 공용 위젯 JUN_mod_tsl_qt_v01, 로직은 app/core. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

from tools.A00040_file_exporter_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00040_file_exporter_V02.app import core
from tools.A00040_file_exporter_V02.app.ui.type_filter_button import TypeFilterButton


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00040_file_exporter_V02_window"


# 레거시 6-토큰 기본값 (label = 표 헤더, text = Custom 모드 기본 문자열)
TOKEN_DEFAULTS = [
    {"label": "SK",      "text": "SK"},
    {"label": "MANU",    "text": "MANU"},
    {"label": "CH",      "text": "CH"},
    {"label": "Name",    "text": "Name"},
    {"label": "Type",    "text": "Basic"},
    {"label": "Version", "text": "Version"},
]

MODE_CUSTOM = "Custom"
MODE_SETNAME = "Set's Name"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("File Exporter v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(560, 720)

        self._token_rows = []  # [{"line": QLineEdit, "combo": QComboBox}, ...]

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

        # 공용 로그창 (TSL log_callback 이 self._log 를 쓰므로 먼저 생성)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(120)

        main_layout.addWidget(self._build_path_group())
        main_layout.addWidget(self._build_lists_group(), stretch=1)
        main_layout.addWidget(self._build_naming_group())
        main_layout.addWidget(self._build_export_group())

        # 로그창
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # 저작권
        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    # ---- Export path -------------------------------------------------

    def _build_path_group(self):
        group = QGroupBox("Export Path")
        layout = QHBoxLayout(group)

        self.le_path = QLineEdit()
        self.le_path.setReadOnly(True)
        self.le_path.setPlaceholderText("Select a folder to export FBX files")
        layout.addWidget(self.le_path, stretch=1)

        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.on_browse)
        layout.addWidget(btn_browse)

        return group

    # ---- Set's Name / File name TSLs --------------------------------

    def _build_lists_group(self):
        group = QGroupBox("Set Up")
        layout = QHBoxLayout(group)

        # 내보낼 objectSet 목록 (씬 선택에서 Select/Add)
        self.set_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Set's Name", select_label="Select Sets",
            log_callback=self._log)
        # 각 세트의 결과 파일명 (Naming 으로 자동 생성 / 수동 편집). 씬 Select 불필요.
        self.name_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="File name", show_select=False, show_add=False,
            log_callback=self._log)

        layout.addWidget(self.set_tsl)
        layout.addWidget(self.name_tsl)
        return group

    # ---- Naming (tokens) --------------------------------------------

    def _build_naming_group(self):
        group = QGroupBox("Naming")
        root = QVBoxLayout(group)

        grid = QGridLayout()
        for col, spec in enumerate(TOKEN_DEFAULTS):
            grid.addWidget(QLabel(spec["label"]), 0, col, alignment=Qt.AlignCenter)

            line = QLineEdit(spec["text"])
            grid.addWidget(line, 1, col)

            combo = QComboBox()
            combo.addItems([MODE_CUSTOM, MODE_SETNAME])
            # 모드 바뀌면 Custom 일 때만 편집 가능하게 토글
            combo.currentTextChanged.connect(
                lambda text, le=line: le.setEnabled(text == MODE_CUSTOM))
            grid.addWidget(combo, 2, col)

            self._token_rows.append({"line": line, "combo": combo})

        root.addLayout(grid)

        btn_set_name = QPushButton("Set Name")
        btn_set_name.setToolTip(
            "Build a file name for each set from the tokens above and fill the "
            "File name list. 'Custom' uses the text; 'Set's Name' uses the set name.")
        btn_set_name.clicked.connect(self.on_set_name)
        root.addWidget(btn_set_name)

        return group

    # ---- Type filter + Export ---------------------------------------

    def _build_export_group(self):
        group = QGroupBox("Export")
        layout = QHBoxLayout(group)

        layout.addWidget(QLabel("Type Filter :"))
        self.type_filter = TypeFilterButton(core.FILTER_TYPES)
        layout.addWidget(self.type_filter)
        layout.addStretch(1)

        btn_export = QPushButton("Export")
        btn_export.setMinimumHeight(32)
        btn_export.setToolTip(
            "Export each set's members to '<Export Path>/<File name>.fbx'. "
            "Unchecked types in Type Filter are excluded.")
        btn_export.clicked.connect(self.on_export)
        layout.addWidget(btn_export, stretch=1)

        return group

    # ================================================================
    # Handlers
    # ================================================================

    def on_browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if folder:
            self.le_path.setText(folder.replace("\\", "/"))

    def on_set_name(self):
        set_names = self.set_tsl.get_all_items()
        if not set_names:
            self._log("[WARN] Set's Name list is empty. Use Select Sets first.")
            return

        token_specs = []
        for row in self._token_rows:
            mode = "setname" if row["combo"].currentText() == MODE_SETNAME else "custom"
            token_specs.append({"mode": mode, "text": row["line"].text()})

        file_names = core.build_file_names(set_names, token_specs)
        self.name_tsl.set_items(file_names)
        self._log("Set Name : {0} file name(s) generated.".format(len(file_names)))

    def on_export(self):
        set_names = self.set_tsl.get_all_items()
        if not set_names:
            self._log("[WARN] Set's Name list is empty. Add objectSets first.")
            return

        export_path = self.le_path.text().strip()
        if not export_path:
            self._log("[WARN] Select an export path first.")
            return

        file_names = self.name_tsl.get_all_items()
        excluded = self.type_filter.excluded_keys()

        included = self.type_filter.included_keys()
        self._log("--- Export start (include: {0}) ---".format(
            ", ".join(included) if included else "none of the filtered types"))

        with core.undo_chunk():
            logs = core.export_sets(set_names, file_names, excluded, export_path)
        for line in logs:
            self._log(line)

    # ================================================================
    # Helper / About
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    def show_about(self, *args):
        message = (
            "File Exporter v{version}\n"
            "Update date: {update}\n"
            "\n"
            "Qt rework of legacy A00040_file_exporter (maya.cmds).\n"
            "\n"
            "Export objectSets to FBX, one file per set. Build file names from\n"
            "tokens (Custom / Set's Name). Members are moved to world, exported,\n"
            "then restored to their original parents.\n"
            "\n"
            "[Type Filter] choose node types to include/exclude. Unchecked types\n"
            "are excluded (e.g. uncheck Mesh + keep Joint -> meshes are skipped,\n"
            "everything else is exported). Types not listed are always included.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)
        QMessageBox.information(self, "About", message)
