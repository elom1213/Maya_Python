# Python Script by Ji Hun Park
# last Update date : 2026-06-17
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
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QFont,
)

from ..core import path_structure as ps_mod
from ..core.store import OutsideProjectRootError


class PathStructureTab(QWidget):

    def __init__(self, get_store, get_project_root, get_store_dir, log):
        super().__init__()

        self._get_store = get_store              # () -> MetaStore
        self._get_project_root = get_project_root  # () -> str
        self._get_store_dir = get_store_dir        # () -> str
        self._log = log                            # (msg) -> None

        self._pending = None                       # Capture 했으나 아직 저장 안 한 PathStructure
        self._scanned_base = None                   # 폴더 체크리스트를 마지막으로 스캔한 base 경로

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

        # Recursive + Capture + Save
        action_row = QHBoxLayout()
        self.chk_recursive = QCheckBox("Recursive (capture full nested tree)")
        btn_capture = QPushButton("Capture")
        btn_capture.clicked.connect(self.on_capture)
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.on_save)
        action_row.addWidget(self.chk_recursive)
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
        layout.addWidget(self.list_structs, stretch=1)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.on_refresh)
        btn_recreate = QPushButton("Recreate")
        btn_recreate.clicked.connect(self.on_recreate)
        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(self.on_delete)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_recreate)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("Preview"))
        self.txt_preview = QPlainTextEdit()
        self.txt_preview.setReadOnly(True)
        # 트리뷰 정렬을 위해 고정폭 폰트 + 줄바꿈 끄기.
        self.txt_preview.setFont(QFont("Consolas"))
        self.txt_preview.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(self.txt_preview, stretch=1)

        return group

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
                base, store, self.chk_recursive.isChecked(), include_top=include_top)
        except OutsideProjectRootError:
            QMessageBox.warning(self, "Path Structure", "Base folder is outside the project root.")
            return

        self._pending = structure

        # 캡처 결과를 (미저장 상태로) preview 에 보여준다. 목록 선택은 해제.
        self.list_structs.blockSignals(True)
        self.list_structs.setCurrentRow(-1)
        self.list_structs.blockSignals(False)
        self._show_preview(structure, header="Captured (not saved yet)")
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
            self.txt_preview.clear()

    def on_select_structure(self, *_):
        name = self._selected_name()
        if not name:
            self.txt_preview.clear()
            return

        structure = ps_mod.load(self._get_store_dir(), name)
        if structure is None:
            self.txt_preview.clear()
            return

        self._show_preview(structure)

    def _show_preview(self, structure, header=None):
        lines = []
        if header:
            lines.append(header)
        lines += [
            f"Base (relative to project root): {structure.base_rel}",
            f"Recursive: {structure.recursive}",
            f"Folders ({len(structure.folders)}):",
        ]
        if structure.folders:
            lines.extend(ps_mod.build_tree_lines(structure.folders))
        else:
            lines.append("(none - base folder only)")
        self.txt_preview.setPlainText("\n".join(lines))

    # ============================================================== recreate

    def on_recreate(self):
        name = self._selected_name()
        if not name:
            QMessageBox.warning(self, "Path Structure", "Select a structure first.")
            return

        project_root = self._get_project_root()
        if not project_root:
            QMessageBox.warning(self, "Path Structure", "Set Project Root first (File Manager tab).")
            return

        structure = ps_mod.load(self._get_store_dir(), name)
        if structure is None:
            QMessageBox.warning(self, "Path Structure", "Structure not found (refresh).")
            self.on_refresh()
            return

        created, existing = ps_mod.recreate(structure, project_root)

        self._log(f"Recreate '{name}': {len(created)} created, {len(existing)} already existed.")
        for path in created:
            self._log(f"  + {path}")
        QMessageBox.information(
            self,
            "Path Structure",
            f"Created {len(created)} folder(s), {len(existing)} already existed.",
        )

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
