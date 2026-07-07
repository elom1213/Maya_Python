# Python Script by Ji Hun Park
# last Update date : 2026-07-07
# A00210_FileManager - "Path Structure" tab (Qt)
#
# 베이스 폴더의 하위 폴더 구조를 캡처해 store_dir 에 JSON 으로 저장하고(다른 PC 와 git 동기화),
# 다른 PC 에서 그 PC 의 project_root 아래에 폴더만 재생성한다.
#
# project_root / store_dir / 로그는 MainWindow 에서 콜러블로 주입받는다(단일 소스 유지).

import os
import time

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
)

from ..core import path_structure as ps_mod
from ..core.store import OutsideProjectRootError


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

    def __init__(self, get_store, get_project_root, get_store_dir, log):
        super().__init__()

        self._get_store = get_store              # () -> MetaStore
        self._get_project_root = get_project_root  # () -> str
        self._get_store_dir = get_store_dir        # () -> str
        self._log = log                            # (msg) -> None

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
        self.list_folders.setToolTip("Only checked folders are recorded.")
        self.list_folders.itemChanged.connect(self._on_folder_item_changed)
        layout.addWidget(self.list_folders)

        # Name
        name_row = QHBoxLayout()
        self.ipf_name = QLineEdit()
        name_row.addWidget(QLabel("Name"))
        name_row.addWidget(self.ipf_name)
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

        self.list_structs = QListWidget()
        self.list_structs.currentItemChanged.connect(self.on_select_structure)
        # 목록은 짧게(약 1/3), 나머지 세로 공간은 Preview 트리에 준다.
        self.list_structs.setMaximumHeight(120)
        layout.addWidget(self.list_structs, stretch=0)

        # 관리 버튼(Refresh/Rename/Delete)은 왼쪽에, 실제로 폴더를 '생성'하는 Recreate 는
        # 색을 달리해 오른쪽에 따로 둔다(파괴/생성 동작을 시각적으로 구분).
        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.on_refresh)
        btn_rename = QPushButton("Rename")
        btn_rename.setToolTip("Rename the selected saved structure.")
        btn_rename.clicked.connect(self.on_rename)
        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(self.on_delete)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_rename)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch(1)

        self.btn_recreate = QPushButton("Recreate")
        self.btn_recreate.setToolTip(
            "Create the checked folders (within the depth) directly inside 'Recreate To'.")
        self.btn_recreate.clicked.connect(self.on_recreate)
        self.btn_recreate.setStyleSheet(self._RECREATE_QSS)
        btn_row.addWidget(self.btn_recreate)
        layout.addLayout(btn_row)

        # Recreate 목적지: 체크된 폴더가 이 폴더 '바로 안'에 생성된다.
        # 구조를 선택하면 <Project Root>/<base_rel> 로 자동 채워지고, 다른 곳으로 바꿀 수 있다.
        recreate_row = QHBoxLayout()
        recreate_row.addWidget(QLabel("Recreate To"))
        self.ipf_recreate_to = QLineEdit()
        self.ipf_recreate_to.setPlaceholderText("Destination base folder for Recreate")
        self.ipf_recreate_to.setToolTip(
            "Destination base folder. Checked folders are created directly inside it.\n"
            "Auto-filled to <Project Root>/<base_rel> when a structure is selected; "
            "edit or Browse to redirect anywhere.")
        btn_recreate_browse = QPushButton("Browse...")
        btn_recreate_browse.clicked.connect(lambda: self._browse_dir(self.ipf_recreate_to))
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

        # 파일 표시 여부. 기본 OFF(폴더만). 파일은 로컬 파일시스템에서 읽어 보여만 준다.
        self.chk_show_files = QCheckBox("Show files")
        self.chk_show_files.setChecked(False)
        self.chk_show_files.setToolTip(
            "Off = folders only. Files are shown from disk (not recreated).")
        self.chk_show_files.toggled.connect(self._on_show_files_toggled)
        prev_row.addWidget(self.chk_show_files)

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

    def _browse_dir(self, line_edit):
        start = line_edit.text().strip() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Directory", start)
        if path:
            line_edit.setText(path)

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
        item = self.list_structs.currentItem()
        return item.text() if item is not None else ""

    @staticmethod
    def _now_iso():
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # =========================================================== capture/save

    def on_capture(self):
        base = self.ipf_base.text().strip()

        if not base or not os.path.isdir(base):
            QMessageBox.warning(self, "Path Structure", "Select a valid Base Folder.")
            return
        if not self._get_project_root():
            QMessageBox.warning(self, "Path Structure", "Set Project Root first (File Manager tab).")
            return

        # base 가 바뀐 채 Scan 을 안 눌렀을 수 있으니 목록을 최신화한다.
        self._scan_if_changed()

        # 체크된 최상위 폴더만 기록. (폴더가 있는데 하나도 체크 안 했으면 경고)
        include_top = self._checked_names()
        if self._all_names() and not include_top:
            QMessageBox.warning(
                self, "Path Structure",
                "No folders checked. Check the folders to record (or 'All').")
            return

        store = self._get_store()
        try:
            structure = ps_mod.capture(
                base, store, self.spn_capture_depth.value(), include_top=include_top)
        except OutsideProjectRootError:
            QMessageBox.warning(self, "Path Structure", "Base folder is outside the project root.")
            return

        self._pending = structure

        # 캡처 결과를 (미저장 상태로) preview 에 보여준다. 목록 선택은 해제.
        self.list_structs.blockSignals(True)
        self.list_structs.setCurrentRow(-1)
        self.list_structs.blockSignals(False)
        self._show_preview(structure, base_abs=base)
        self._log(
            f"Captured {len(structure.folders)} folder(s) from {base} "
            f"({len(include_top)} top-level selected)")

    def on_save(self):
        if self._pending is None:
            QMessageBox.warning(self, "Path Structure", "Capture first.")
            return

        name = self.ipf_name.text().strip()
        store_dir = self._get_store_dir()

        if not name:
            QMessageBox.warning(self, "Path Structure", "Enter a name.")
            return
        if not store_dir:
            QMessageBox.warning(self, "Path Structure", "Set Store Repo first (File Manager tab).")
            return

        if not self._pending.folders:
            ok = QMessageBox.question(
                self,
                "Path Structure",
                "No subfolders captured. Save anyway?\n(Recreate will only create the base folder.)",
            )
            if ok != QMessageBox.Yes:
                return

        if ps_mod.exists(store_dir, name):
            ok = QMessageBox.question(
                self,
                "Path Structure",
                f"A structure named '{name}' already exists. Overwrite?",
            )
            if ok != QMessageBox.Yes:
                return

        self._pending.name = name
        self._pending.created_at = self._now_iso()

        path = ps_mod.save(store_dir, self._pending)
        self._log(f"Path structure saved: {path}")
        self._log("Saved locally - use Push on the File Manager tab to sync.")
        self._pending = None
        self.on_refresh(select=name)

    # ============================================================== list/view

    def on_refresh(self, select=None):
        names = ps_mod.list_names(self._get_store_dir())

        keep = select if select is not None else self._selected_name()

        self.list_structs.blockSignals(True)
        self.list_structs.clear()
        self.list_structs.addItems(names)
        self.list_structs.blockSignals(False)

        if keep and keep in names:
            self.list_structs.setCurrentRow(names.index(keep))
        elif names:
            self.list_structs.setCurrentRow(0)
        else:
            self._clear_preview()

    def on_select_structure(self, *_):
        name = self._selected_name()
        if not name:
            self._clear_preview()
            return

        structure = ps_mod.load(self._get_store_dir(), name)
        if structure is None:
            self._clear_preview()
            return

        self._show_preview(structure, base_abs=self._saved_base_abs(structure))

    # -------------------------------------------------------- preview (tree)

    def _saved_base_abs(self, structure):
        """저장된 구조의 로컬 base 절대경로(project_root/base_rel). 파일 표시/스캔용."""
        project_root = self._get_project_root()
        if not project_root or not structure.base_rel:
            return ""
        return os.path.join(
            os.path.abspath(project_root), *structure.base_rel.split("/"))

    def _clear_preview(self):
        self._cur_structure = None
        self._cur_base_abs = ""
        self._excluded = set()
        self.tree_preview.clear()
        self.ipf_recreate_to.clear()

    def _show_preview(self, structure, base_abs=""):
        """새 구조를 Preview 대상으로 삼는다(제외 목록 초기화 후 트리 렌더)."""
        self._cur_structure = structure
        self._cur_base_abs = base_abs or ""
        self._excluded = set()
        # Recreate 목적지를 이 구조의 기본 경로(<Project Root>/<base_rel>, 또는 캡처 소스)로
        # 자동 채운다. 사용자가 그대로 두면 기존 동작과 동일, 바꾸면 그 폴더에 생성된다.
        self.ipf_recreate_to.setText(self._cur_base_abs)
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
                show_files=self.chk_show_files.isChecked(),
                max_depth=self._view_depth(),
            )
            root_item = self._make_preview_item(node)
            tree.addTopLevelItem(root_item)
            tree.expandAll()
        tree.blockSignals(False)

    def _make_preview_item(self, node):
        """트리 노드(dict) → QTreeWidgetItem. 폴더는 체크 가능(파일은 표시만)."""
        item = QTreeWidgetItem([node["name"]])
        item.setData(0, Qt.UserRole, node["rel"])
        item.setData(0, Qt.UserRole + 1, node["is_dir"])

        if node["is_dir"]:
            item.setIcon(0, self._icon_dir)
            # 루트(base, rel="")는 항상 생성되므로 체크박스를 두지 않는다.
            if node["rel"]:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                checked = node["rel"] not in self._excluded
                item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        else:
            item.setIcon(0, self._icon_file)

        for child in node["children"]:
            item.addChild(self._make_preview_item(child))
        return item

    def _set_excluded(self, rel, state):
        if state == Qt.Checked:
            self._excluded.discard(rel)
        else:
            self._excluded.add(rel)

    @staticmethod
    def _is_checkable_folder(item):
        """폴더(체크 가능)이고 루트(base)가 아닌 항목인지."""
        return bool(item.data(0, Qt.UserRole + 1)) and bool(item.data(0, Qt.UserRole))

    def _on_preview_item_changed(self, item, _col):
        """폴더 체크 상태 변경 → 제외 목록 갱신 + 다중 선택 시 선택된 폴더 일괄 토글."""
        if self._syncing_checks:
            return
        if not self._is_checkable_folder(item):     # 파일/루트는 무시
            return

        state = item.checkState(0)
        item_rel = item.data(0, Qt.UserRole)
        self._set_excluded(item_rel, state)

        tree = item.treeWidget()
        if tree is None:
            return

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
        """rels 에 해당하는 폴더 항목들의 체크 상태를 state 로 맞추고 제외 목록도 갱신."""
        relset = {r for r in rels if r}
        self._syncing_checks = True
        tree.blockSignals(True)

        def walk(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                if (child is not skip_item and self._is_checkable_folder(child)
                        and child.data(0, Qt.UserRole) in relset):
                    child.setCheckState(0, state)
                    self._set_excluded(child.data(0, Qt.UserRole), state)
                walk(child)

        walk(tree.invisibleRootItem())
        tree.blockSignals(False)
        self._syncing_checks = False

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

    def _on_show_files_toggled(self, _checked):
        self._fill_preview_tree(self.tree_preview)

    def on_expand(self):
        if self._cur_structure is None:
            QMessageBox.information(self, "Path Structure", "Select a structure first.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Path Structure — {self._cur_structure.base_rel}")
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

        structure = ps_mod.load(self._get_store_dir(), name)
        if structure is None:
            QMessageBox.warning(self, "Path Structure", "Structure not found (refresh).")
            self.on_refresh()
            return

        # 현재 Preview 옵션(Depth 제한 + 체크 해제한 폴더 제외)만 생성한다.
        folders = ps_mod.limit_depth(structure.folders, self._view_depth())
        folders = [f for f in folders if f not in self._excluded]

        # 목적지가 아직 없으면 새로 만들 것임을 알린다(오타로 엉뚱한 곳에 생성 방지).
        if not os.path.isdir(target):
            ok = QMessageBox.question(
                self,
                "Path Structure",
                f"'Recreate To' folder does not exist yet:\n{target}\n\nCreate it (and the structure) there?",
            )
            if ok != QMessageBox.Yes:
                return

        created, existing = ps_mod.recreate(structure, None, folders=folders, base_abs=target)

        self._log(f"Recreate '{name}' -> {target}: "
                  f"{len(created)} created, {len(existing)} already existed.")
        for path in created:
            self._log(f"  + {path}")
        QMessageBox.information(
            self,
            "Path Structure",
            f"Created {len(created)} folder(s), {len(existing)} already existed.",
        )

    # ================================================================ rename

    def on_rename(self):
        old = self._selected_name()
        if not old:
            QMessageBox.warning(self, "Path Structure", "Select a structure first.")
            return

        store_dir = self._get_store_dir()
        if not store_dir:
            QMessageBox.warning(self, "Path Structure", "Set Store Repo first (File Manager tab).")
            return

        new, ok = QInputDialog.getText(
            self, "Rename Structure", "New name:", text=old)
        if not ok:
            return
        new = new.strip()
        if not new or new == old:
            return

        try:
            ps_mod.rename(store_dir, old, new)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Path Structure", f"Rename failed: {exc}")
            return

        self._log(f"Path structure renamed: {old} -> {new}")
        self._log("Renamed locally - use Push on the File Manager tab to sync.")
        self.on_refresh(select=new)

    # ================================================================ delete

    def on_delete(self):
        name = self._selected_name()
        if not name:
            QMessageBox.warning(self, "Path Structure", "Select a structure first.")
            return

        ok = QMessageBox.question(self, "Path Structure", f"Delete structure '{name}'?")
        if ok != QMessageBox.Yes:
            return

        ps_mod.delete(self._get_store_dir(), name)
        self._log(f"Path structure deleted: {name}")
        self.on_refresh()
