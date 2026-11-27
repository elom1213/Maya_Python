# Python Script by Ji Hun Park
# last Update date : 2026-11-27
# A00210_FileManager - "Path Structure" tab (Qt)
#
# 베이스 폴더의 하위 폴더 구조를 캡처해 라이브러리(<repo>/path_structures)에 JSON 으로 저장하고(다른 PC 와 git 동기화),
# 다른 PC 에서 그 PC 의 project_root 아래에 재생성한다.
#
# project_root / 로그는 MainWindow 에서 콜러블로 주입받는다(단일 소스 유지). 라이브러리 위치는 v01.60 부터 탭이 직접 관리.
#
# v01.29 : 파일도 함께 캡처/재생성. 두 지점에 체크박스(둘 다 기본 켬) —
#          저장 쪽 "Include files"(캡처가 파일 목록도 기록) / 재생성 쪽 "Create files"
#          (기록된 파일을 0 바이트 빈 파일로 생성, 이름 끝에 "__" 표식).
# v01.32 : 'Recreate To' 를 Project Root(File Manager 탭)와 완전히 분리. 구조를 선택/새로고침해도
#          칸을 <Project Root>/<base_rel> 로 덮어쓰거나 지우지 않는다 - Recreate 는 오직 이 칸의
#          경로에 생성한다. 값은 프로파일에 따로 저장돼 다음 실행에 복원된다.
# v01.33 : Capture 도 Project Root 와 무관하다 - Base Folder 가 어느 경로든 캡처한다
#          (예전엔 Project Root 가 비었거나 Base Folder 가 그 밖이면 막았다).
# v01.60 : Saved Structures 를 File Manager 프로파일에서 독립 - 저장소 루트 path_structures/ 의 라이브러리
#          (core.structure_library). 프로파일 · Source Mode · Data Folder 를 바꿔도 목록이 그대로다.
#          목록 = 카테고리 트리(New Category · Rename · Delete · Move To...), 이 탭 전용 Pull / Push
#          (path_structures/ 만 올린다). 라이브러리 경로 · Recreate To 는 PC 단위 설정(core.library_settings).

import os
import time
import getpass

from Framework.qt.MOD_treeExpand_qt_v01 import JUN_mod_treeExpand_qt_v01
from Framework.qt import JUN_mod_checkList_qt
from Framework.qt.qt import (
    Qt,
    QEvent,
    QTimer,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QListWidget,
    QListWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QStyle,
    QBrush,
    QColor,
)

from ..core import path_structure as ps_mod
from ..core import structure_library as lib_mod
from ..core import library_settings as lset_mod
from ..core.git_sync import GitSync
from ..core.paths import ui_path, ui_text

# 트리 항목 종류 (UserRole 의 첫 값)
KIND_CAT = "cat"
KIND_STRUCT = "struct"
UNCAT_KEY = "__uncategorized__"   # Uncategorized 가상 노드의 id 자리


class PathStructureTab(QWidget):

    # Recreate 버튼(실제로 폴더를 생성하는 동작)을 다른 관리 버튼과 구분하기 위한 액센트.
    _RECREATE_QSS = (
        "QPushButton {"
        " background-color: #2e7d32; color: #ffffff; font-weight: bold;"
        " border: 1px solid #1b5e20; border-radius: 3px; padding: 4px 16px; }"
        "QPushButton:hover { background-color: #388e3c; }"
        "QPushButton:pressed { background-color: #1b5e20; }"
        "QPushButton:disabled { background-color: #4b5b4c; color: #9aa; }"
    )

    def __init__(self, get_store, get_project_root, get_seed_prefs, log, on_pulled=None):
        super().__init__()

        # get_store / get_project_root 는 Capture 의 base_rel(정보용)과 Preview 의 디스크 파일 위치에만 쓴다.
        # 목록 · 저장 위치는 프로파일과 무관한 라이브러리(v01.60).
        self._get_store = get_store              # () -> MetaStore
        self._get_project_root = get_project_root  # () -> str
        self._log = log                            # (msg) -> None
        self._on_pulled = on_pulled                # () -> None, 탭 Pull 성공 뒤(File Manager 목록 재스캔)

        # PC 단위 설정(없으면 활성 프로파일 값으로 한 번 채움) + 라이브러리
        seed = get_seed_prefs() if callable(get_seed_prefs) else None
        self._settings = lset_mod.load(seed)
        self._lib = lib_mod.StructureLibrary(self._settings.get("repo_dir", ""))
        self._legacy_warned = False

        self._pending = None                       # Capture 했으나 아직 저장 안 한 PathStructure
        self._scanned_base = None                   # 폴더 체크리스트를 마지막으로 스캔한 base 경로

        # Preview(트리) 상태
        self._cur_structure = None                  # 현재 Preview 중인 PathStructure
        self._cur_base_abs = ""                     # 그 구조의 로컬 base 절대경로(파일 스캔용)
        self._excluded = set()                      # Recreate 에서 제외할 폴더 rel(체크 해제)
        self._syncing_checks = False                # 다중 선택 일괄 토글 중 재진입 방지
        self._presel = None                         # (tree, [rel...]) 마우스 누름 직전 선택(붕괴 전)

        # 폴더/파일 아이콘(테마 무관, 1회 생성 후 재사용)
        self._icon_dir = self.style().standardIcon(QStyle.SP_DirIcon)
        self._icon_file = self.style().standardIcon(QStyle.SP_FileIcon)
        # 구조에 기록되지 않은(=재생성 대상이 아닌) 디스크 파일을 흐리게 표시할 색.
        self._brush_unrecorded = QBrush(QColor("#808080"))

        self._build_ui()
        self.on_refresh()

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(self._build_save_group())
        root.addWidget(self._build_saved_group(), stretch=1)

    def _build_save_group(self):
        group = QGroupBox("Save Structure")
        layout = QVBoxLayout(group)

        # Base folder + Browse
        base_row = QHBoxLayout()
        self.ipf_base = QLineEdit()
        self.ipf_base.editingFinished.connect(self._scan_if_changed)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._on_browse_base)
        base_row.addWidget(QLabel("Base Folder"))
        base_row.addWidget(self.ipf_base)
        base_row.addWidget(btn_browse)
        layout.addLayout(base_row)

        # 기록할 최상위 폴더 체크리스트 (+ 전체 선택 / 다시 스캔)
        # base 의 최상위 하위 폴더만 리스트업하고, 체크된 폴더만 기록한다.
        folders_row = QHBoxLayout()
        folders_row.addWidget(QLabel("Folders to record"))
        folders_row.addStretch(1)
        self.chk_all = QCheckBox("All")
        self.chk_all.setChecked(True)
        self.chk_all.setToolTip("Check to record every top-level folder.")
        self.chk_all.clicked.connect(self._on_toggle_all)
        btn_scan = QPushButton("Scan")
        btn_scan.setToolTip("Re-list the base folder's top-level subfolders.")
        btn_scan.clicked.connect(self._scan_folders)
        folders_row.addWidget(self.chk_all)
        folders_row.addWidget(btn_scan)
        layout.addLayout(folders_row)

        self.list_folders = QListWidget()
        self.list_folders.setToolTip(
            "Only checked folders are recorded.\n"
            "Shift / Ctrl click to select several rows - clicking the check box of a\n"
            "selected row (or Space) checks or unchecks every selected row.")
        self.list_folders.itemChanged.connect(self._on_folder_item_changed)
        # v01.31 : 고른 행 한꺼번에 체크 (Framework 공용 동작).
        self._check_folders = JUN_mod_checkList_qt.JUN_mod_checkList_qt_v01(
            self.list_folders)
        layout.addWidget(self.list_folders)

        # Name
        name_row = QHBoxLayout()
        self.ipf_name = QLineEdit()
        name_row.addWidget(QLabel("Name"))
        name_row.addWidget(self.ipf_name, stretch=1)
        # 저장할 카테고리 (v01.60). 기본 = 트리에서 지금 고른 카테고리.
        name_row.addWidget(QLabel("Category"))
        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumWidth(140)
        self.cmb_category.setToolTip("Category to save the structure in.")
        name_row.addWidget(self.cmb_category)
        layout.addLayout(name_row)

        # Capture Depth + Capture + Save
        # Depth = base 기준 캡처 깊이(최상위 폴더 = 1, 0 = 전체 트리).
        action_row = QHBoxLayout()
        action_row.addWidget(QLabel("Capture Depth"))
        self.spn_capture_depth = QSpinBox()
        self.spn_capture_depth.setRange(0, 99)
        self.spn_capture_depth.setValue(1)
        self.spn_capture_depth.setSpecialValueText("All")   # 0 → 'All'
        self.spn_capture_depth.setToolTip(
            "How many levels deep to capture (1 = top-level only, 0 = All).")
        action_row.addWidget(self.spn_capture_depth)

        # 파일도 기록할지. 기본 켬 — 폴더만 원하면 끄면 된다.
        # 기록하는 것은 **이름뿐**(내용은 담지 않는다). 재생성은 0 바이트 빈 파일.
        self.chk_include_files = QCheckBox("Include files")
        self.chk_include_files.setChecked(True)
        self.chk_include_files.setToolTip(
            "Record file names too, not just folders.\n"
            "Only names are stored - never file contents.\n"
            "Recreate makes them as empty 0-byte files marked with '{0}'.".format(
                ps_mod.RECREATED_SUFFIX))
        action_row.addWidget(self.chk_include_files)

        btn_capture = QPushButton("Capture")
        btn_capture.clicked.connect(self.on_capture)
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.on_save)
        action_row.addStretch(1)
        action_row.addWidget(btn_capture)
        action_row.addWidget(btn_save)
        layout.addLayout(action_row)

        return group

    def _build_saved_group(self):
        group = QGroupBox("Saved Structures")
        layout = QVBoxLayout(group)

        # Library 줄 (v01.60) - 프로파일과 무관한 라이브러리 위치 + 이 탭 전용 Pull / Push.
        lib_row = QHBoxLayout()
        lib_row.addWidget(QLabel("Library"))
        self.lbl_library = QLabel()
        self.lbl_library.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lib_row.addWidget(self.lbl_library, stretch=1)
        btn_lib_browse = QPushButton("Browse...")
        btn_lib_browse.setToolTip("Pick the local clone of the data repo that holds the library.\n"
                                  "Saved per PC - not part of any File Manager profile.")
        btn_lib_browse.clicked.connect(self.on_browse_library)
        lib_row.addWidget(btn_lib_browse)
        self.btn_pull = QPushButton("Pull")
        self.btn_pull.setToolTip("Get the latest saved structures and categories.\n"
                                 "(git pulls the whole branch - File Manager records may update too.)")
        self.btn_pull.clicked.connect(self.on_pull)
        self.btn_push = QPushButton("Push")
        self.btn_push.setToolTip("Share saved structures and categories.\n"
                                 "Only the path_structures folder is committed - nothing else.")
        self.btn_push.clicked.connect(self.on_push)
        lib_row.addWidget(self.btn_pull)
        lib_row.addWidget(self.btn_push)
        self.lbl_lib_status = QLabel("")
        lib_row.addWidget(self.lbl_lib_status)
        layout.addLayout(lib_row)

        # 카테고리 트리: 최상위 = 카테고리, 자식 = 구조.
        self.tree_structs = QTreeWidget()
        self.tree_structs.setHeaderHidden(True)
        self.tree_structs.setColumnCount(1)
        self.tree_structs.setSelectionMode(QAbstractItemView.ExtendedSelection)
        JUN_mod_treeExpand_qt_v01(self.tree_structs)
        self.tree_structs.currentItemChanged.connect(self.on_select_structure)
        self.tree_structs.itemSelectionChanged.connect(self._update_buttons)
        self.tree_structs.itemExpanded.connect(self._on_cat_expand_changed)
        self.tree_structs.itemCollapsed.connect(self._on_cat_expand_changed)
        self.tree_structs.setMaximumHeight(200)
        layout.addWidget(self.tree_structs, stretch=0)

        # 관리 버튼은 왼쪽에, 실제로 폴더를 '생성'하는 Recreate 는
        # 색을 달리해 오른쪽에 따로 둔다(파괴/생성 동작을 시각적으로 구분).
        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.on_refresh)
        btn_new_cat = QPushButton("New Category")
        btn_new_cat.clicked.connect(self.on_new_category)
        self.btn_rename = QPushButton("Rename")
        self.btn_rename.setToolTip("Rename the selected category or structure.")
        self.btn_rename.clicked.connect(self.on_rename)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setToolTip("Delete the selected category or structure(s).")
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_move = QPushButton("Move To...")
        self.btn_move.setToolTip("Move the selected structure(s) to another category.")
        self.btn_move.clicked.connect(self.on_move_to)
        for b in (btn_refresh, btn_new_cat, self.btn_rename, self.btn_delete, self.btn_move):
            btn_row.addWidget(b)
        btn_row.addStretch(1)

        self.btn_recreate = QPushButton("Recreate")
        self.btn_recreate.setToolTip(
            "Create the checked folders (within the depth) directly inside 'Recreate To'.")
        self.btn_recreate.clicked.connect(self.on_recreate)
        self.btn_recreate.setStyleSheet(self._RECREATE_QSS)
        btn_row.addWidget(self.btn_recreate)
        layout.addLayout(btn_row)

        # Recreate 목적지: 체크된 폴더가 이 폴더 '바로 안'에 생성된다.
        # Project Root / File Manager 탭과 무관하다 - 구조를 골라도 이 칸은 바뀌지 않는다(v01.32).
        recreate_row = QHBoxLayout()
        recreate_row.addWidget(QLabel("Recreate To"))
        self.ipf_recreate_to = QLineEdit()
        self.ipf_recreate_to.setPlaceholderText("Destination base folder for Recreate")
        self.ipf_recreate_to.setToolTip(
            "Destination base folder. Checked folders are created directly inside it.\n"
            "Independent of the Project Root and profiles (File Manager tab) - saved per PC,\n"
            "selecting a structure never changes this field.")
        self.ipf_recreate_to.setText(ui_path(self._settings.get("recreate_to", "")))
        self.ipf_recreate_to.editingFinished.connect(self.save_settings)
        btn_recreate_browse = QPushButton("Browse...")
        btn_recreate_browse.clicked.connect(self._on_browse_recreate_to)
        recreate_row.addWidget(self.ipf_recreate_to)
        recreate_row.addWidget(btn_recreate_browse)
        layout.addLayout(recreate_row)

        # Preview 옵션 행: Depth / Show files / Expand
        prev_row = QHBoxLayout()
        prev_row.addWidget(QLabel("Preview"))
        prev_row.addStretch(1)

        prev_row.addWidget(QLabel("Depth"))
        # Depth = 표시/재생성할 폴더 깊이(최상위 = 1, 0 = All). Recreate 도 이 깊이만 생성.
        self.spn_view_depth = QSpinBox()
        self.spn_view_depth.setRange(0, 99)
        self.spn_view_depth.setValue(0)
        self.spn_view_depth.setSpecialValueText("All")
        self.spn_view_depth.setToolTip(
            "Show/recreate folders up to this depth (0 = All).")
        self.spn_view_depth.valueChanged.connect(self._on_view_depth_changed)
        prev_row.addWidget(self.spn_view_depth)

        # 파일 표시 + 재생성 여부(하나의 토글). Depth 와 같은 규칙 — **트리에 보이는 것이
        # 만들어지는 것**이라, 안 보이는데 만들어지는 항목이 없다. 기본 켬.
        self.chk_create_files = QCheckBox("Create files")
        self.chk_create_files.setChecked(True)
        self.chk_create_files.setToolTip(
            "Show the structure's recorded files and create them on Recreate,\n"
            "as empty 0-byte files marked with '{0}' (test.ma -> test.ma{0}).\n"
            "Uncheck a file in the tree to skip just that one.\n"
            "Structures saved without files instead show the base folder's files on disk, "
            "greyed out (reference only - never created).".format(ps_mod.RECREATED_SUFFIX))
        self.chk_create_files.toggled.connect(self._on_create_files_toggled)
        prev_row.addWidget(self.chk_create_files)

        self.btn_expand = QPushButton("Expand")
        self.btn_expand.setToolTip("Open the tree in a larger window")
        self.btn_expand.clicked.connect(self.on_expand)
        prev_row.addWidget(self.btn_expand)

        layout.addLayout(prev_row)

        self.tree_preview = self._make_preview_widget()
        layout.addWidget(self.tree_preview, stretch=1)

        return group

    def _make_preview_widget(self):
        tree = QTreeWidget()
        JUN_mod_treeExpand_qt_v01(tree)  # 펼치기 = 한 단계, Shift = 아래 전부 (공용)
        tree.setHeaderLabels(["Name"])
        # Shift/Ctrl 로 여러 항목을 동시에 선택할 수 있게 한다(체크박스 일괄 토글용).
        tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree.itemChanged.connect(self._on_preview_item_changed)
        # 마우스 누름 시점(선택이 한 행으로 붕괴되기 전) 선택을 캡처하기 위한 필터.
        tree.viewport().installEventFilter(self)
        return tree

    def eventFilter(self, obj, event):
        # 트리 뷰포트에서 마우스가 눌리는 순간의 선택을 저장한다. 체크박스를 누르면
        # Qt 가 선택을 그 한 행으로 되돌리는데, 그 전에(=여기서) 원래 선택을 확보해 둔다.
        if event.type() == QEvent.MouseButtonPress:
            tree = obj.parent()
            if isinstance(tree, QTreeWidget):
                self._presel = (
                    tree, [it.data(0, Qt.UserRole) for it in tree.selectedItems()])
        return super().eventFilter(obj, event)

    # ============================================================ helpers

    def recreate_to(self):
        """'Recreate To' 칸 값."""
        return ui_path(self.ipf_recreate_to.text())

    def library(self):
        return self._lib

    def save_settings(self):
        """PC 단위 설정 저장(Recreate To · 라이브러리 경로 · 펼친 카테고리). 프로파일과 무관 (v01.60)."""
        self._settings["recreate_to"] = self.recreate_to()
        self._settings["repo_dir"] = ui_path(self._lib.repo_dir)
        try:
            lset_mod.save(self._settings)
        except OSError as exc:
            self._log(f"[Warning] Could not save Path Structure settings: {exc}")

    def _on_browse_recreate_to(self):
        self._browse_dir(self.ipf_recreate_to)
        self.save_settings()

    def _update_library_label(self):
        lib_dir = self._lib.lib_dir()
        self.lbl_library.setText(ui_path(lib_dir) if lib_dir else "(not set)")
        self.lbl_library.setToolTip(
            "Saved structures of every profile live here (repo root / path_structures).\n"
            "Repo clone: " + (ui_path(self._lib.repo_dir) or "(not set)"))

    def _set_repo_dir(self, repo_dir):
        self._lib = lib_mod.StructureLibrary(repo_dir)
        self._legacy_warned = False
        self.save_settings()
        self._update_library_label()

    def on_browse_library(self):
        start = self._lib.repo_dir or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Library Repo (data repo clone)", start)
        if not path:
            return
        if not os.path.isdir(os.path.join(path, ".git")):
            QMessageBox.information(
                self, "Path Structure",
                "Not a git clone. Pull will clone the data repo here if the folder is empty.")
        self._set_repo_dir(path)
        self._log("Path Structure library: " + (ui_path(self._lib.lib_dir()) or "(not set)"))
        self.on_refresh()

    # ------------------------------------------------------- tree selection

    def _current_info(self):
        """현재 항목 (kind, key) - kind 는 KIND_CAT / KIND_STRUCT, 없으면 (None, None)."""
        item = self.tree_structs.currentItem()
        if item is None:
            return None, None
        data = item.data(0, Qt.UserRole)
        if not data:
            return None, None
        return data[0], data[1]

    def _selected_struct_names(self):
        names = []
        for it in self.tree_structs.selectedItems():
            data = it.data(0, Qt.UserRole)
            if data and data[0] == KIND_STRUCT:
                names.append(data[1])
        return names

    def _current_category_id(self):
        """지금 고른 카테고리 id - 카테고리 노드면 그 id, 구조면 그 구조의 카테고리. 없으면 None."""
        kind, key = self._current_info()
        if kind == KIND_CAT:
            return lib_mod.UNCATEGORIZED if key == UNCAT_KEY else key
        if kind == KIND_STRUCT:
            item = self.tree_structs.currentItem()
            parent = item.parent() if item is not None else None
            if parent is not None:
                pdata = parent.data(0, Qt.UserRole)
                if pdata and pdata[0] == KIND_CAT:
                    return lib_mod.UNCATEGORIZED if pdata[1] == UNCAT_KEY else pdata[1]
        return None

    def _update_buttons(self):
        kind, key = self._current_info()
        names = self._selected_struct_names()
        is_uncat = (kind == KIND_CAT and key == UNCAT_KEY)
        self.btn_rename.setEnabled(kind is not None and not is_uncat)
        self.btn_delete.setEnabled(kind is not None and not is_uncat)
        self.btn_move.setEnabled(bool(names))

    def _on_cat_expand_changed(self, item):
        if getattr(self, "_filling_tree", False):
            return
        expanded = []
        for i in range(self.tree_structs.topLevelItemCount()):
            it = self.tree_structs.topLevelItem(i)
            if it.isExpanded():
                expanded.append(it.data(0, Qt.UserRole)[1])
        self._settings["expanded"] = expanded
        self.save_settings()

    def _fill_category_combo(self, select_id=None):
        """Save 그룹의 Category 콤보. select_id None = 지금 값 유지."""
        keep = self.cmb_category.currentData() if select_id is None else select_id
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        for cat in self._lib.list_categories():
            self.cmb_category.addItem(cat.name, cat.id)
        self.cmb_category.addItem(lib_mod.UNCATEGORIZED_LABEL, lib_mod.UNCATEGORIZED)
        idx = self.cmb_category.findData(keep) if keep is not None else -1
        self.cmb_category.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_category.blockSignals(False)

    def _category_choices(self):
        """[(이름, id)] - 카테고리 + Uncategorized(맨 뒤)."""
        out = [(c.name, c.id) for c in self._lib.list_categories()]
        out.append((lib_mod.UNCATEGORIZED_LABEL, lib_mod.UNCATEGORIZED))
        return out

    def _author(self):
        try:
            user = getpass.getuser()
        except Exception:  # noqa: BLE001
            user = ""
        return user or "unknown"

    def _need_library(self):
        if not self._lib.repo_dir:
            QMessageBox.warning(self, "Path Structure",
                                "Set the Library folder first (Browse... in Saved Structures).")
            return False
        return True

    SYNC_HINT = "use Push in the Saved Structures group to share it."

    def _browse_dir(self, line_edit):
        start = line_edit.text().strip() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Directory", start)
        if path:
            line_edit.setText(ui_path(path))

    def _on_browse_base(self):
        self._browse_dir(self.ipf_base)
        self._scan_folders()

    # ---------------------------------------------------- folder checklist

    def _all_names(self):
        return [self.list_folders.item(i).text() for i in range(self.list_folders.count())]

    def _checked_names(self):
        return [
            self.list_folders.item(i).text()
            for i in range(self.list_folders.count())
            if self.list_folders.item(i).checkState() == Qt.Checked
        ]

    def _scan_if_changed(self):
        """base 경로가 마지막 스캔과 다를 때만 재스캔(포커스 이동만으로 선택이 초기화되지 않게)."""
        if self.ipf_base.text().strip() != (self._scanned_base or ""):
            self._scan_folders()

    def _scan_folders(self):
        """Base 폴더의 최상위 하위 폴더를 체크박스 리스트에 채운다.

        다시 스캔해도 기존 체크 상태는 이름으로 보존하고, 새로 나타난 폴더는 체크 상태로 둔다.
        (처음 스캔이면 모두 체크 = 기존 '전체 기록' 동작과 동일.)
        """
        base = self.ipf_base.text().strip()
        prev_all = set(self._all_names())
        prev_checked = set(self._checked_names())

        names = ps_mod.list_top_level(base) if (base and os.path.isdir(base)) else []

        self.list_folders.blockSignals(True)
        self.list_folders.clear()
        for name in names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            # 기존 폴더는 이전 체크 상태 유지, 새 폴더(또는 첫 스캔)는 체크.
            checked = (name not in prev_all) or (name in prev_checked)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.list_folders.addItem(item)
        self.list_folders.blockSignals(False)

        self._scanned_base = base
        self._sync_all_checkbox()

    def _on_toggle_all(self, checked):
        """'All' 체크박스 클릭 → 모든 항목을 같은 상태로."""
        state = Qt.Checked if checked else Qt.Unchecked
        self.list_folders.blockSignals(True)
        for i in range(self.list_folders.count()):
            self.list_folders.item(i).setCheckState(state)
        self.list_folders.blockSignals(False)

    def _on_folder_item_changed(self, *_):
        self._sync_all_checkbox()

    def _sync_all_checkbox(self):
        """모든 항목이 체크됐을 때만 'All' 을 체크 상태로 반영(시그널 루프 방지)."""
        n = self.list_folders.count()
        all_checked = n > 0 and all(
            self.list_folders.item(i).checkState() == Qt.Checked for i in range(n)
        )
        self.chk_all.blockSignals(True)
        self.chk_all.setChecked(all_checked)
        self.chk_all.blockSignals(False)

    def _selected_name(self):
        """현재 항목이 구조면 그 이름, 아니면 ""."""
        kind, key = self._current_info()
        return key if kind == KIND_STRUCT else ""

    @staticmethod
    def _now_iso():
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # =========================================================== capture/save

    def on_capture(self):
        base = self.ipf_base.text().strip()

        if not base or not os.path.isdir(base):
            QMessageBox.warning(self, "Path Structure", "Select a valid Base Folder.")
            return
        # Project Root 와 무관하다(v01.33) - 루트가 비었거나 Base Folder 가 그 밖이어도 캡처한다.

        # base 가 바뀐 채 Scan 을 안 눌렀을 수 있으니 목록을 최신화한다.
        self._scan_if_changed()

        # 체크된 최상위 폴더만 기록. (폴더가 있는데 하나도 체크 안 했으면 경고)
        include_top = self._checked_names()
        if self._all_names() and not include_top:
            QMessageBox.warning(
                self, "Path Structure",
                "No folders checked. Check the folders to record (or 'All').")
            return

        structure = ps_mod.capture(
            base, self._get_store(), self.spn_capture_depth.value(),
            include_top=include_top,
            include_files=self.chk_include_files.isChecked())

        self._pending = structure

        # 캡처 결과를 (미저장 상태로) preview 에 보여준다. 목록 선택은 해제.
        self.tree_structs.blockSignals(True)
        self.tree_structs.setCurrentItem(None)
        self.tree_structs.clearSelection()
        self.tree_structs.blockSignals(False)
        self._update_buttons()
        self._show_preview(structure, base_abs=base)
        self._log(
            f"Captured {len(structure.folders)} folder(s), {len(structure.files)} file(s) "
            f"from {base} ({len(include_top)} top-level selected)")

    def on_save(self):
        if self._pending is None:
            QMessageBox.warning(self, "Path Structure", "Capture first.")
            return

        name = self.ipf_name.text().strip()
        cat_id = self.cmb_category.currentData() or lib_mod.UNCATEGORIZED
        cat_name = self.cmb_category.currentText() or lib_mod.UNCATEGORIZED_LABEL

        if not name:
            QMessageBox.warning(self, "Path Structure", "Enter a name.")
            return
        if not self._need_library():
            return

        if not self._pending.folders and not self._pending.files:
            ok = QMessageBox.question(
                self,
                "Path Structure",
                "No subfolders or files captured. Save anyway?\n"
                "(Recreate will only create the base folder.)",
            )
            if ok != QMessageBox.Yes:
                return

        if self._lib.exists(name):
            ok = QMessageBox.question(
                self,
                "Path Structure",
                f"A structure named '{name}' already exists. Overwrite?\n"
                f"It will be saved in category '{cat_name}'.",
            )
            if ok != QMessageBox.Yes:
                return

        self._pending.name = name
        self._pending.category = cat_id
        self._pending.created_by = self._pending.created_by or self._author()
        self._pending.created_at = self._now_iso()

        path = self._lib.save(self._pending)
        self._log(ui_text(f"Path structure saved: {path} [{cat_name}] "
                          f"({len(self._pending.folders)} folder(s), "
                          f"{len(self._pending.files)} file(s))"))
        self._log("Saved locally - " + self.SYNC_HINT)
        self._pending = None
        self.on_refresh(select=name)

    # ============================================================== list/view

    def on_refresh(self, select=None, select_cat=None):
        """라이브러리를 다시 읽어 카테고리 트리를 채운다.

        select     : 고를 구조 이름. None 이면 지금 선택(구조 / 카테고리) 유지.
        select_cat : 고를 카테고리 id (select 가 없을 때).
        """
        self._update_library_label()

        if select is None and select_cat is None:
            kind, key = self._current_info()
            if kind == KIND_STRUCT:
                select = key
            elif kind == KIND_CAT:
                select_cat = key

        groups = self._lib.grouped()
        expanded = self._settings.get("expanded")
        expanded = None if expanded is None else set(expanded)

        self._filling_tree = True
        tree = self.tree_structs
        tree.blockSignals(True)
        tree.clear()
        target = None
        first_struct = None
        for cat, names in groups:
            key = cat.id if cat is not None else UNCAT_KEY
            label = cat.name if cat is not None else lib_mod.UNCATEGORIZED_LABEL
            cat_item = QTreeWidgetItem([f"{label}  ({len(names)})"])
            cat_item.setData(0, Qt.UserRole, (KIND_CAT, key))
            cat_item.setIcon(0, self._icon_dir)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsUserCheckable)
            if cat is None:
                cat_item.setForeground(0, self._brush_unrecorded)
                cat_item.setToolTip(0, "Structures without a category (or whose category was deleted).")
            elif cat.created_by or cat.created_at:
                cat_item.setToolTip(0, f"Category '{cat.name}' - created by {cat.created_by or '?'} "
                                       f"{cat.created_at}".rstrip())
            tree.addTopLevelItem(cat_item)
            if select_cat is not None and key == select_cat and select is None:
                target = cat_item
            for name in names:
                it = QTreeWidgetItem([name])
                it.setData(0, Qt.UserRole, (KIND_STRUCT, name))
                it.setIcon(0, self._icon_file)
                it.setFlags(it.flags() & ~Qt.ItemIsUserCheckable)
                cat_item.addChild(it)
                if first_struct is None:
                    first_struct = it
                if select and name == select:
                    target = it
            # 펼침: 저장된 목록이 없으면 전부 펼침. 선택할 구조가 든 카테고리는 늘 펼친다.
            cat_item.setExpanded(expanded is None or key in expanded
                                 or (target is not None and target.parent() is cat_item))
        tree.blockSignals(False)
        self._filling_tree = False

        if target is None:
            target = first_struct
        if target is not None:
            tree.setCurrentItem(target)       # currentItemChanged -> Preview
            tree.scrollToItem(target)
        else:
            self._clear_preview()
        self._fill_category_combo(self._current_category_id())
        self._update_buttons()
        self._warn_legacy()

    def _warn_legacy(self):
        if self._legacy_warned:
            return
        legacy = self._lib.legacy_files()
        if legacy:
            self._legacy_warned = True
            self._log(f"[Warning] {len(legacy)} structure(s) still in the old per-profile folders "
                      f"(profiles/*/path_structures). Run the migration "
                      f"(dev/migrate_structure_library.py, see docs) - they are not listed here.")

    def on_select_structure(self, *_):
        self._update_buttons()
        cat_id = self._current_category_id()
        if cat_id is not None:
            self._fill_category_combo(cat_id)
        name = self._selected_name()
        if not name:
            self._clear_preview()
            return

        structure = self._lib.load(name)
        if structure is None:
            self._clear_preview()
            return

        self._show_preview(structure, base_abs=self._saved_base_abs(structure))

    # -------------------------------------------------------- preview (tree)

    def _saved_base_abs(self, structure):
        """저장된 구조의 로컬 base 절대경로. 파일 표시/스캔용.

        Project Root 안에서 캡처한 구조는 project_root/base_rel (PC 마다 루트가 달라도 맞는다).
        루트 밖에서 캡처한 구조(v01.33~)는 기록된 base_path 그대로 - 다른 PC 엔 없을 수 있고,
        없으면 트리는 기록된 폴더 · 파일만 보여준다.
        """
        project_root = self._get_project_root()
        if project_root and structure.base_rel:
            return os.path.join(
                os.path.abspath(project_root), *structure.base_rel.split("/"))
        return os.path.normpath(structure.base_path) if structure.base_path else ""

    def _clear_preview(self):
        self._cur_structure = None
        self._cur_base_abs = ""
        self._excluded = set()
        self.tree_preview.clear()

    def _show_preview(self, structure, base_abs=""):
        """새 구조를 Preview 대상으로 삼는다(제외 목록 초기화 후 트리 렌더)."""
        self._cur_structure = structure
        self._cur_base_abs = base_abs or ""
        self._excluded = set()
        # 'Recreate To' 는 건드리지 않는다(v01.32). 예전에는 여기서 <Project Root>/<base_rel> 로
        # 덮어써서, 경로를 적어 둬도 구조 선택/새로고침 한 번에 Project Root 쪽에 생성됐다.
        self._fill_preview_tree(self.tree_preview)

    def _view_depth(self):
        return self.spn_view_depth.value()

    def _fill_preview_tree(self, tree):
        """현재 구조/옵션(Depth · Show files · 제외 목록)으로 트리 위젯을 채운다."""
        tree.blockSignals(True)
        tree.clear()
        if self._cur_structure is not None:
            node = ps_mod.build_structure_tree(
                self._cur_structure,
                base_abs=self._cur_base_abs,
                show_files=self.chk_create_files.isChecked(),
                max_depth=self._view_depth(),
            )
            root_item = self._make_preview_item(node)
            tree.addTopLevelItem(root_item)
            tree.expandAll()
        tree.blockSignals(False)
        self._sync_blocked(tree)

    _BLOCKED_TIP = "Not created - a parent folder above it is unchecked."

    def _sync_blocked(self, tree):
        """상위 폴더가 체크 해제된 항목을 회색 + 툴팁으로 (v01.59). 체크 상태는 그대로 둔다 -
        상위를 다시 켜면 원래대로 만들어진다. Recreate 의 prune_excluded 와 같은 규칙."""
        if tree is None:
            return
        tree.blockSignals(True)

        def walk(parent, blocked):
            for i in range(parent.childCount()):
                child = parent.child(i)
                if self._is_checkable(child):
                    if blocked:
                        child.setForeground(0, self._brush_unrecorded)
                        child.setToolTip(0, self._BLOCKED_TIP)
                    elif child.toolTip(0) == self._BLOCKED_TIP:
                        child.setData(0, Qt.ForegroundRole, None)
                        child.setToolTip(0, "")
                    off = child.checkState(0) != Qt.Checked
                else:
                    off = False
                walk(child, blocked or off)

        walk(tree.invisibleRootItem(), False)
        tree.blockSignals(False)

    def _make_preview_item(self, node):
        """트리 노드(dict) → QTreeWidgetItem.

        **Recreate 대상(recorded)인 항목만 체크박스**를 갖는다 — 폴더, 그리고 구조에
        기록된 파일. 기록되지 않은(디스크에서 참고용으로 읽어온) 파일은 회색으로 표시해
        "이건 안 만들어진다"가 눈에 보이게 한다.
        """
        # 루트(base, rel="")는 항상 생성되므로 체크박스를 두지 않는다.
        recorded = bool(node.get("recorded", True))
        checkable = recorded and bool(node["rel"])

        item = QTreeWidgetItem([node["name"]])
        item.setData(0, Qt.UserRole, node["rel"])
        item.setData(0, Qt.UserRole + 1, node["is_dir"])
        item.setData(0, Qt.UserRole + 2, recorded)

        item.setIcon(0, self._icon_dir if node["is_dir"] else self._icon_file)

        if checkable:
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked if node["rel"] in self._excluded
                               else Qt.Checked)
        else:
            # QTreeWidgetItem 은 ItemIsUserCheckable 을 **기본으로 켠 채** 만들어진다.
            # (체크 상태를 안 주면 체크박스가 그려지지 않을 뿐이다.) 판정이 헐거워지지
            # 않도록 여기서 명시적으로 끈다.
            item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
            if not recorded:
                item.setForeground(0, self._brush_unrecorded)
                item.setToolTip(0, "On disk in the base folder - not part of this "
                                   "structure, so Recreate does not create it.")

        if not node["rel"]:
            # 루트 "." (v01.34) - 베이스 폴더 이름(A)을 보이면 재생성 때 A 가 새로 생긴다고 읽힌다.
            source = ps_mod.base_label(self._cur_structure) if self._cur_structure else ""
            tip = "'.' = the Recreate To folder itself - the items below are created inside it."
            if source:
                tip += "\nCaptured from: " + source
            item.setToolTip(0, tip)

        for child in node["children"]:
            item.addChild(self._make_preview_item(child))
        return item

    def _set_excluded(self, rel, state):
        if state == Qt.Checked:
            self._excluded.discard(rel)
        else:
            self._excluded.add(rel)

    @staticmethod
    def _is_checkable(item):
        """제외 대상이 될 수 있는 항목인지 — 체크박스가 달린 폴더/기록된 파일.

        루트(base, rel="")와 기록되지 않은 디스크 파일(recorded=False)은 제외 대상이
        아니므로 False. 플래그가 아니라 **저장해 둔 rel/recorded 로** 판정한다
        (ItemIsUserCheckable 은 Qt 기본값이 켜져 있어 판정 근거로 못 쓴다).
        """
        return (bool(item.data(0, Qt.UserRole))
                and bool(item.data(0, Qt.UserRole + 2)))

    def _on_preview_item_changed(self, item, _col):
        """체크 상태 변경 → 제외 목록 갱신 + 다중 선택 시 선택 항목 일괄 토글."""
        if self._syncing_checks:
            return
        if not self._is_checkable(item):     # 루트/표시전용 파일은 무시
            return

        state = item.checkState(0)
        item_rel = item.data(0, Qt.UserRole)
        self._set_excluded(item_rel, state)

        tree = item.treeWidget()
        if tree is None:
            return
        self._sync_blocked(tree)

        # 토글한 항목이 다중 선택에 포함돼 있으면 선택된 폴더 전체를 같은 상태로 맞춘다.
        # 키보드(스페이스) 토글이면 selectedItems() 가 온전하고, 마우스 클릭이면 이미 한 행으로
        # 붕괴됐으므로 누름 직전에 캡처한 _presel 을 쓴다.
        selected = tree.selectedItems()
        if len(selected) > 1 and item in selected:
            target_rels = [it.data(0, Qt.UserRole) for it in selected]
        elif (self._presel and self._presel[0] is tree
              and len(self._presel[1]) > 1 and item_rel in self._presel[1]):
            target_rels = self._presel[1]
        else:
            return

        self._apply_state_to_rels(tree, target_rels, state, skip_item=item)

        # 체크박스 클릭은 Qt 가 선택을 클릭한 한 행으로 되돌린다. 마우스 이벤트가 끝난 뒤
        # (singleShot 0) 원래 다중 선택을 복원해, 이어서 계속 토글할 수 있게 한다.
        rels = list(target_rels)
        QTimer.singleShot(0, lambda: self._restore_selection(tree, rels))

    def _apply_state_to_rels(self, tree, rels, state, skip_item=None):
        """rels 에 해당하는 항목들의 체크 상태를 state 로 맞추고 제외 목록도 갱신."""
        relset = {r for r in rels if r}
        self._syncing_checks = True
        tree.blockSignals(True)

        def walk(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                if (child is not skip_item and self._is_checkable(child)
                        and child.data(0, Qt.UserRole) in relset):
                    child.setCheckState(0, state)
                    self._set_excluded(child.data(0, Qt.UserRole), state)
                walk(child)

        walk(tree.invisibleRootItem())
        tree.blockSignals(False)
        self._syncing_checks = False
        self._sync_blocked(tree)

    def _restore_selection(self, tree, rels):
        relset = {r for r in rels if r}
        if not relset:
            return
        tree.clearSelection()

        def walk(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.data(0, Qt.UserRole) in relset:
                    child.setSelected(True)
                walk(child)

        walk(tree.invisibleRootItem())

    def _on_view_depth_changed(self, _value):
        self._fill_preview_tree(self.tree_preview)

    def _on_create_files_toggled(self, _checked):
        self._fill_preview_tree(self.tree_preview)

    def on_expand(self):
        if self._cur_structure is None:
            QMessageBox.information(self, "Path Structure", "Select a structure first.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Path Structure — {self._cur_structure.name or '(not saved)'}")
        dlg.resize(700, 600)

        v = QVBoxLayout(dlg)
        big = self._make_preview_widget()
        self._fill_preview_tree(big)
        v.addWidget(big, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dlg.reject)
        v.addWidget(buttons)

        dlg.exec_()
        # 큰 창에서 바꾼 체크 상태를 메인 트리에 반영.
        self._fill_preview_tree(self.tree_preview)

    # ============================================================== recreate

    def on_recreate(self):
        name = self._selected_name()
        if not name:
            QMessageBox.warning(self, "Path Structure", "Select a structure first.")
            return

        target = self.ipf_recreate_to.text().strip()
        if not target:
            QMessageBox.warning(
                self, "Path Structure",
                "Set the 'Recreate To' destination folder first.")
            return

        structure = self._lib.load(name)
        if structure is None:
            QMessageBox.warning(self, "Path Structure", "Structure not found (refresh).")
            self.on_refresh()
            return

        # 현재 Preview 옵션(Depth 제한 + 체크 해제한 항목 제외)만 생성한다.
        # 트리에 보이는 것 = 만들어지는 것. 'Create files' 를 끄면 파일은 트리에도 없고
        # 만들어지지도 않는다(Depth 규칙과 동일).
        # v01.59 - 체크 해제한 폴더의 **하위 전부**도 뺀다(아래가 체크돼 있어도). 예전엔 그 경로 자신만 빠져서
        # 하위가 체크돼 있으면 makedirs 가 부모까지 다시 만들었다.
        depth = self._view_depth()
        folders = ps_mod.prune_excluded(ps_mod.limit_depth(structure.folders, depth), self._excluded)
        files = []
        if self.chk_create_files.isChecked():
            files = ps_mod.prune_excluded(ps_mod.limit_depth(structure.files, depth), self._excluded)

        # 목적지가 아직 없으면 새로 만들 것임을 알린다(오타로 엉뚱한 곳에 생성 방지).
        if not os.path.isdir(target):
            ok = QMessageBox.question(
                self,
                "Path Structure",
                f"'Recreate To' folder does not exist yet:\n{target}\n\nCreate it (and the structure) there?",
            )
            if ok != QMessageBox.Yes:
                return

        result = ps_mod.recreate(
            structure, None, folders=folders, base_abs=target, files=files)

        self._log(
            f"Recreate '{name}' -> {target}: "
            f"{len(result.created)} folder(s) created, {len(result.existing)} existed; "
            f"{len(result.created_files)} file(s) created, "
            f"{len(result.existing_files)} existed.")
        for path in result.created:
            self._log(f"  + {path}")
        for path in result.created_files:
            self._log(f"  + {path}")

        msg = (f"Created {len(result.created)} folder(s), "
               f"{len(result.existing)} already existed.")
        if files:
            msg += (f"\nCreated {len(result.created_files)} empty file(s) "
                    f"marked '{ps_mod.RECREATED_SUFFIX}', "
                    f"{len(result.existing_files)} already existed.")
        QMessageBox.information(self, "Path Structure", msg)

    # ============================================================ categories

    def on_new_category(self):
        if not self._need_library():
            return
        raw, ok = QInputDialog.getText(self, "New Category", "Category name:")
        if not ok:
            return
        try:
            cat = self._lib.create_category(raw, author=self._author())
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Path Structure", f"Could not create the category: {exc}")
            return
        self._log(f"Category created: {cat.name}")
        self._log("Created locally - " + self.SYNC_HINT)
        self.on_refresh(select_cat=cat.id)

    def on_move_to(self):
        names = self._selected_struct_names()
        if not names:
            QMessageBox.warning(self, "Path Structure", "Select one or more structures first.")
            return
        choices = self._category_choices()
        labels = [c[0] for c in choices]
        cur = self._current_category_id()
        cur_idx = next((i for i, c in enumerate(choices) if c[1] == cur), 0)
        label, ok = QInputDialog.getItem(
            self, "Move To Category",
            f"Move {len(names)} structure(s) to:", labels, cur_idx, False)
        if not ok or label not in labels:
            return
        cat_id = choices[labels.index(label)][1]
        try:
            moved = self._lib.set_category(names, cat_id)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Path Structure", f"Move failed: {exc}")
            return
        self._log(f"Moved {len(moved)} structure(s) to '{label}': {', '.join(moved) if moved else '(already there)'}")
        if moved:
            self._log("Moved locally - " + self.SYNC_HINT)
        self.on_refresh(select=names[0])

    # ================================================================ rename

    def on_rename(self):
        kind, key = self._current_info()
        if kind == KIND_CAT:
            self._rename_category(key)
        elif kind == KIND_STRUCT:
            self._rename_structure(key)
        else:
            QMessageBox.warning(self, "Path Structure", "Select a category or a structure first.")

    def _rename_category(self, cat_id):
        if cat_id == UNCAT_KEY:
            return
        cat = self._lib.get_category(cat_id)
        if cat is None:
            self.on_refresh()
            return
        new, ok = QInputDialog.getText(self, "Rename Category", "New name:", text=cat.name)
        if not ok:
            return
        new = new.strip()
        if not new or new == cat.name:
            return
        try:
            self._lib.rename_category(cat_id, new)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Path Structure", f"Rename failed: {exc}")
            return
        self._log(f"Category renamed: {cat.name} -> {new}")
        self._log("Renamed locally - " + self.SYNC_HINT)
        self.on_refresh(select_cat=cat_id)

    def _rename_structure(self, old):
        if not self._need_library():
            return
        new, ok = QInputDialog.getText(
            self, "Rename Structure", "New name:", text=old)
        if not ok:
            return
        new = new.strip()
        if not new or new == old:
            return

        try:
            self._lib.rename(old, new)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Path Structure", f"Rename failed: {exc}")
            return

        self._log(f"Path structure renamed: {old} -> {new}")
        self._log("Renamed locally - " + self.SYNC_HINT)
        self.on_refresh(select=new)

    # ================================================================ delete

    def on_delete(self):
        kind, key = self._current_info()
        if kind == KIND_CAT:
            self._delete_category(key)
            return
        names = self._selected_struct_names()
        if not names:
            QMessageBox.warning(self, "Path Structure", "Select a category or a structure first.")
            return

        if len(names) == 1:
            text = f"Delete structure '{names[0]}'?"
        else:
            text = f"Delete {len(names)} structures?\n" + "\n".join(names)
        ok = QMessageBox.question(self, "Path Structure", text)
        if ok != QMessageBox.Yes:
            return

        cat_id = self._current_category_id()
        for name in names:
            self._lib.delete(name)
            self._log(f"Path structure deleted: {name}")
        self._log("Deleted locally - " + self.SYNC_HINT)
        self._clear_preview()
        self.tree_structs.setCurrentItem(None)
        self.on_refresh(select_cat=(UNCAT_KEY if cat_id == lib_mod.UNCATEGORIZED else cat_id)
                        if cat_id is not None else None)

    def _delete_category(self, cat_id):
        if cat_id == UNCAT_KEY:
            return
        cat = self._lib.get_category(cat_id)
        if cat is None:
            self.on_refresh()
            return
        names = [n for n, c in self._lib.list_structures() if c == cat_id]

        if not names:
            ok = QMessageBox.question(self, "Path Structure", f"Delete the empty category '{cat.name}'?")
            if ok != QMessageBox.Yes:
                return
            mode = "move"
        else:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("Path Structure")
            box.setText(f"Category '{cat.name}' has {len(names)} structure(s).")
            box.setInformativeText(
                "Move them to Uncategorized, or delete them together with the category?\n"
                "Deleting structures cannot be undone in the tool.")
            btn_move = box.addButton("Move to Uncategorized", QMessageBox.AcceptRole)
            btn_del = box.addButton("Delete Structures Too", QMessageBox.DestructiveRole)
            box.addButton(QMessageBox.Cancel)
            box.setDefaultButton(btn_move)
            box.exec_()
            clicked = box.clickedButton()
            if clicked is btn_move:
                mode = "move"
            elif clicked is btn_del:
                mode = "delete"
            else:
                return

        try:
            affected = self._lib.delete_category(cat_id, mode=mode)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Path Structure", f"Delete failed: {exc}")
            return
        if mode == "delete":
            self._log(f"Category deleted: {cat.name} (with {len(affected)} structure(s))")
        else:
            self._log(f"Category deleted: {cat.name} ({len(affected)} structure(s) moved to "
                      f"{lib_mod.UNCATEGORIZED_LABEL})")
        self._log("Deleted locally - " + self.SYNC_HINT)
        self._clear_preview()
        self.tree_structs.setCurrentItem(None)
        self.on_refresh(select_cat=UNCAT_KEY if (mode == "move" and affected) else None)

    # ============================================================ pull / push

    def _make_git(self):
        s = self._settings
        return GitSync(self._lib.repo_dir, s.get("remote"), s.get("branch"),
                       scope_rel=lib_mod.LIB_DIR)

    def _ready_git(self):
        """Pull / Push 전 검사(라이브러리 경로 · 클론 · 브랜치). 통과하면 GitSync, 아니면 None."""
        if not self._need_library():
            return None
        git = self._make_git()
        if not git.is_repo():
            if os.path.isdir(git.store_dir) and os.listdir(git.store_dir):
                msg = "The Library folder is not a git clone (and not empty) - pick the data repo clone."
                self._log("[Warning] " + msg)
                QMessageBox.warning(self, "Path Structure", msg)
                return None
            ok, out = git.ensure_repo(self._settings.get("remote_url", ""))
            self._log(ui_text(out))
            if not ok:
                self.lbl_lib_status.setText("Clone failed")
                return None
        ok, msg = git.check_branch()
        if not ok:
            self._log("[Warning] " + msg + " (use 'Switch to ...' on the File Manager tab)")
            self.lbl_lib_status.setText("Wrong branch")
            return None
        return git

    def _set_git_busy(self, busy):
        self.btn_pull.setEnabled(not busy)
        self.btn_push.setEnabled(not busy)

    def on_pull(self):
        git = self._ready_git()
        if git is None:
            return
        self._set_git_busy(True)
        try:
            ok, out = git.pull()
        finally:
            self._set_git_busy(False)
        self._log(ui_text(out) or ("Pull OK" if ok else "Pull failed"))
        self.lbl_lib_status.setText("Pull OK" if ok else "Pull failed")
        if ok:
            self._legacy_warned = False
            self.on_refresh()
            if callable(self._on_pulled):
                try:
                    self._on_pulled()
                except Exception as exc:  # noqa: BLE001 - 다른 탭 갱신 실패가 Pull 결과를 가리지 않게
                    self._log(f"Refresh after pull skipped: {exc}")

    def on_push(self):
        git = self._ready_git()
        if git is None:
            return
        pc = os.environ.get("COMPUTERNAME", "")
        message = "Update path structures by {0}{1} ({2}) [{3}]".format(
            self._author(), " on " + pc if pc else "", self._now_iso(), lib_mod.LIB_DIR)
        self._set_git_busy(True)
        try:
            ok, out = git.push(message)
        finally:
            self._set_git_busy(False)
        self._log(ui_text(out) or ("Push OK" if ok else "Push failed"))
        self.lbl_lib_status.setText("Push OK" if ok else "Push failed")
        if ok:
            self.on_refresh()
