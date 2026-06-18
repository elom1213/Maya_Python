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
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QListWidget,
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
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(lambda: self._browse_dir(self.ipf_base))
        base_row.addWidget(QLabel("Base Folder"))
        base_row.addWidget(self.ipf_base)
        base_row.addWidget(btn_browse)
        layout.addLayout(base_row)

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

        store = self._get_store()
        try:
            structure = ps_mod.capture(base, store, self.chk_recursive.isChecked())
        except OutsideProjectRootError:
            QMessageBox.warning(self, "Path Structure", "Base folder is outside the project root.")
            return

        self._pending = structure

        # 캡처 결과를 (미저장 상태로) preview 에 보여준다. 목록 선택은 해제.
        self.list_structs.blockSignals(True)
        self.list_structs.setCurrentRow(-1)
        self.list_structs.blockSignals(False)
        self._show_preview(structure, header="Captured (not saved yet)")
        self._log(f"Captured {len(structure.folders)} folder(s) from {base}")

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
