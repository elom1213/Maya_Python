# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - Export 탭 (in-Maya)
#
# A00040_file_exporter_V02(v02.09) 의 화면을 **그대로** 옮긴 탭이다.
#   - Export path : FBX 를 저장할 폴더 (Browse / Paste / Scene)
#   - Set Up      : 내보낼 objectSet 목록(Set's Name)과 결과 파일명(File name)
#   - Naming      : 토큰 조합으로 파일명 자동 생성 (Custom / Set's Name 모드)
#   - Export      : Move to scene root · Joints only under joints · Type Filter
#
# 원본과 다른 점
#   - 메뉴 · 로그창 · 푸터는 창(main_window)이 갖는다. 탭은 log 콜백만 받는다.
#   - **Scene** 버튼 (신규) — 현재 씬 폴더를 Export Path 에 바로 채운다.
#     따로일 때는 quickTool 의 Copy Scene Folder → 여기 Paste 로 두 창을 오갔다.
#   - Paste 정규화는 core.normalize_pasted_path 로 내렸다(동작 동일).
#   - undo 는 공용 Framework.core.maya_undo.undo_chunk.

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.core.maya_undo import undo_chunk

from tools.A00480_FileTool.app import core
from tools.A00480_FileTool.app.ui.type_filter_button import TypeFilterButton


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


class ExportTab(QWidget):

    def __init__(self, log=None, parent=None):
        super(ExportTab, self).__init__(parent)

        # 로그 콜백 (창의 공용 로그창). TSL 이 생성 때부터 참조하므로 먼저 둔다.
        self._log_callback = log
        self._token_rows = []  # [{"line": QLineEdit, "combo": QComboBox}, ...]

        self.build_ui()

    # ================================================================
    # UI
    # ================================================================

    def build_ui(self):
        layout = QVBoxLayout(self)
        # 탭 테두리가 이미 한 겹 감싸므로 페이지 여백은 뺀다 → 창 크기가 A00040_V02 원본과 같아진다.
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._build_path_group())
        layout.addWidget(self._build_lists_group(), stretch=1)
        layout.addWidget(self._build_naming_group())
        layout.addWidget(self._build_export_group())

    # ---- Export path -------------------------------------------------

    def _build_path_group(self):
        group = QGroupBox("Export Path")
        layout = QHBoxLayout(group)

        self.le_path = QLineEdit()
        self.le_path.setReadOnly(True)
        self.le_path.setPlaceholderText("Select a folder to export FBX files")
        layout.addWidget(self.le_path, stretch=1)

        btn_browse = QPushButton("Browse")
        btn_browse.setToolTip("Pick the export folder with a file dialog.")
        btn_browse.clicked.connect(self.on_browse)
        layout.addWidget(btn_browse)

        btn_paste = QPushButton("Paste")
        btn_paste.setToolTip(
            "Paste a folder path from the clipboard.\n"
            "Copy the path in Explorer (or 'Copy as path') and press this - "
            "quotes and backslashes are handled.\n"
            "If the clipboard holds a file, its folder is used.")
        btn_paste.clicked.connect(self.on_paste_path)
        layout.addWidget(btn_paste)

        btn_scene = QPushButton("Scene")
        btn_scene.setToolTip(
            "Use the folder of the current scene as the export path.\n"
            "An unsaved scene leaves the path unchanged.")
        btn_scene.clicked.connect(self.on_scene_path)
        layout.addWidget(btn_scene)

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
        outer = QVBoxLayout(group)

        # 옵션 행: 씬 최상위로 빼기 토글 (기본 ON = 모두 월드 루트로)
        opt_row = QHBoxLayout()
        self.cb_move_to_root = QCheckBox("Move to scene root")
        self.cb_move_to_root.setChecked(True)
        self.cb_move_to_root.setToolTip(
            "On (default): export each object at the scene root (parents removed) "
            "-> 'grp>joint_01' becomes 'joint_01'.\n"
            "Off: keep the current scene hierarchy -> 'grp>joint_01' stays "
            "'grp>joint_01'.")
        opt_row.addWidget(self.cb_move_to_root)

        # joint 하위의 non-joint(메시/로케이터/컨스트레인트 노드/그룹)를 FBX 에서 뺀다.
        self.cb_joints_only = QCheckBox("Joints only under joints")
        self.cb_joints_only.setChecked(True)
        self.cb_joints_only.setToolTip(
            "On (default): when a joint is exported, everything parented under it "
            "that is not a joint (meshes, locators, constraint nodes, groups) is "
            "left out of the FBX, together with its children.\n"
            "Input connections (constraint drivers) are skipped as well, so a "
            "skeleton export stays joints-only.\n"
            "The scene is not modified: nothing is unparented or hidden, so the "
            "hierarchy under the joint is identical before and after the export.\n"
            "Off: export the whole hierarchy under each joint.")
        opt_row.addWidget(self.cb_joints_only)

        opt_row.addStretch(1)
        outer.addLayout(opt_row)

        # 실행 행: 타입 필터 + Export
        layout = QHBoxLayout()

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

        outer.addLayout(layout)
        return group

    # ================================================================
    # Handlers
    # ================================================================

    def on_browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if folder:
            self.le_path.setText(folder.replace("\\", "/"))

    def on_paste_path(self):
        """클립보드의 경로를 Export Path 에 넣는다. 다듬는 규칙은 core.normalize_pasted_path.

        클립보드가 비었으면 **기존 값을 건드리지 않는다.**
        """
        clipboard = QApplication.clipboard()
        text = clipboard.text() if clipboard is not None else ""
        path, logs = core.normalize_pasted_path(text)
        if path:
            self.le_path.setText(path)
        self._log_all(logs)

    def on_scene_path(self):
        """현재 씬 폴더를 Export Path 에 채운다. 미저장 씬이면 경로를 그대로 두고 경고."""
        folder, logs = core.scene_folder(native=False)
        self._log_all(logs)
        if not folder:
            return
        self.le_path.setText(folder)
        self._log("Export path : {0}".format(folder))

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
        keep_hierarchy = not self.cb_move_to_root.isChecked()
        joints_only = self.cb_joints_only.isChecked()

        included = self.type_filter.included_keys()
        self._log("--- Export start (include: {0} | hierarchy: {1} | "
                  "under joints: {2}) ---".format(
                      ", ".join(included) if included else "none of the filtered types",
                      "keep" if keep_hierarchy else "scene root",
                      "joints only" if joints_only else "everything"))

        with undo_chunk():
            logs = core.export_sets(
                set_names, file_names, excluded, export_path, keep_hierarchy,
                joints_only)
        self._log_all(logs)

    # ================================================================
    # Helper
    # ================================================================

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)

    def _log_all(self, messages):
        for message in (messages or []):
            self._log(message)
