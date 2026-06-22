# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00211_RefLineage - Maya 내 PySide UI
#
# 현재 Maya 씬의 reference 관계를 스캔해 트리로 미리 보고, A00210_FileManager 의
# Lineage 탭에서 그대로 열리는 lineage JSON 으로 내보낸다. 실제 변환/저장 로직은
# app/core/ref_scanner 에 있고(UI/로직 분리), 포맷은 A00210 모듈을 재사용해 보장한다.

import os

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QMessageBox,
    Qt,
)
from Framework.qt.maya_window import maya_main_window

from tools.A00211_RefLineage.app.config.version import VERSION
from tools.A00211_RefLineage.app.core import ref_scanner as rs
from tools.A00210_FileManager.app.core import lineage as lin


WINDOW_OBJECT_NAME = "A00211_RefLineageWindow"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle(f"Ref -> Lineage  v{VERSION}")
        self.resize(560, 560)

        self._collected = None
        self._store, self._prefs = rs.load_store()

        self._build_ui()
        self._refresh_store_label()
        # 창을 열면 곧바로 현재 씬을 스캔해 바로 확인할 수 있게 한다.
        self.on_scan()

    # ----------------------------------------------------------------- build

    def _build_ui(self):
        root = QVBoxLayout(self)

        root.addWidget(QLabel(
            "Scan the current Maya scene's reference relationships and export them "
            "as an A00210 Lineage graph."
        ))

        # 그래프 이름
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Graph name"))
        self.ipf_name = QLineEdit()
        self.ipf_name.setPlaceholderText("e.g. CHN_Basic (defaults to scene file name)")
        name_row.addWidget(self.ipf_name)
        root.addLayout(name_row)

        # 액션 버튼
        btn_row = QHBoxLayout()
        self.btn_scan = QPushButton("Scan Scene References")
        self.btn_scan.clicked.connect(self.on_scan)
        self.btn_export = QPushButton("Export to Lineage JSON")
        self.btn_export.clicked.connect(self.on_export)
        btn_row.addWidget(self.btn_scan)
        btn_row.addWidget(self.btn_export)
        root.addLayout(btn_row)

        # 저장 위치 안내(읽기 전용)
        self.lbl_store = QLabel("-")
        self.lbl_store.setWordWrap(True)
        self.lbl_store.setStyleSheet("color: #9aa; font-size: 11px;")
        root.addWidget(self.lbl_store)

        # 미리보기 트리(씬 -> 중첩 reference)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File", "Note"])
        self.tree.setColumnWidth(0, 320)
        root.addWidget(self.tree, stretch=1)

        # 로그
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(140)
        root.addWidget(self.txt_log)

    def log(self, text):
        self.txt_log.append(text)

    def _refresh_store_label(self):
        store_dir = self._store.store_dir or "(not set)"
        root = self._store.project_root or "(not set)"
        out_dir = os.path.join(store_dir, lin.LINEAGE_DIR) if self._store.store_dir else "(set Store Repo in A00210)"
        self.lbl_store.setText(
            f"Output: {out_dir}\\<name>.json\nProject root: {root}"
        )

    # ------------------------------------------------------------------ scan

    def on_scan(self):
        try:
            collected = rs.collect_scene_references()
        except ImportError:
            QMessageBox.warning(self, "Ref Lineage", "This tool must be run inside Maya.")
            return
        except Exception as exc:                      # Maya 쿼리 예외 방어
            QMessageBox.critical(self, "Ref Lineage", f"Scan failed:\n{exc}")
            self.log(f"Scan failed: {exc}")
            return

        self._collected = collected
        self._populate_tree(collected)

        scene = collected["scene"]
        if not self.ipf_name.text().strip():
            default = os.path.splitext(os.path.basename(scene))[0] if scene else ""
            self.ipf_name.setText(default)

        n_files = len(collected["paths"])
        n_edges = len(collected["edges"])
        scene_label = scene if scene else "(untitled scene)"
        self.log(f"Scanned {scene_label}: {n_files} file(s), {n_edges} reference link(s).")
        if n_edges == 0:
            self.log("No references found in the current scene.")

    def _populate_tree(self, collected):
        self.tree.clear()

        paths = collected["paths"]
        scene_norm = collected["scene_norm"]

        # owner -> [source...] 인접 리스트(트리 펼침용).
        children = {}
        for owner, source in collected["edges"]:
            children.setdefault(owner, []).append(source)

        root_item = self._make_tree_item(collected, scene_norm)
        self.tree.addTopLevelItem(root_item)
        self._add_children(root_item, scene_norm, children, collected, set())
        self.tree.expandAll()

    def _add_children(self, parent_item, owner_norm, children, collected, visited):
        # 같은 가지에서의 순환만 방어(다른 가지에는 같은 파일이 다시 나올 수 있다).
        if owner_norm in visited:
            return
        visited = visited | {owner_norm}
        for source_norm in sorted(children.get(owner_norm, [])):
            child_item = self._make_tree_item(collected, source_norm)
            parent_item.addChild(child_item)
            self._add_children(child_item, source_norm, children, collected, visited)

    def _make_tree_item(self, collected, norm):
        abs_path = collected["paths"].get(norm, "")
        is_scene = (norm == collected["scene_norm"])
        is_loaded = collected["loaded"].get(norm, True)

        name = os.path.basename(abs_path) if abs_path else "(untitled scene)"

        notes = []
        if is_scene:
            notes.append("current scene")
        if not is_loaded and not is_scene:
            notes.append("unloaded")
        if abs_path and self._store.project_root:
            try:
                self._store.make_key(abs_path)
            # ValueError: 다른 드라이브(Windows) → relpath 예외. 둘 다 '루트 밖'으로 본다.
            except (rs.OutsideProjectRootError, ValueError):
                notes.append("out of project root")
        elif abs_path and not self._store.project_root:
            notes.append("no project root set")

        item = QTreeWidgetItem([name, ", ".join(notes)])
        if abs_path:
            item.setToolTip(0, abs_path)
        return item

    # ---------------------------------------------------------------- export

    def on_export(self):
        if not self._store.store_dir:
            QMessageBox.warning(
                self, "Ref Lineage",
                "Store Repo is not set. Open A00210_FileManager and set it first.",
            )
            return

        if self._collected is None:
            self.on_scan()
            if self._collected is None:
                return

        name = self.ipf_name.text().strip()
        if not name:
            scene = self._collected["scene"]
            name = os.path.splitext(os.path.basename(scene))[0] if scene else ""
        if not name:
            QMessageBox.warning(self, "Ref Lineage", "Enter a graph name (scene is unsaved).")
            return

        if lin.exists(self._store.store_dir, name):
            ok = QMessageBox.question(
                self, "Ref Lineage",
                f"A lineage graph named '{name}' already exists. Overwrite?",
            )
            if ok != QMessageBox.Yes:
                return

        if not self._store.project_root:
            self.log("Warning: project root not set - nodes will have no record/thumbnail links.")

        try:
            graph = rs.build_graph(
                self._collected, self._store, name, self._prefs.get("author", ""),
            )
            path = lin.save(self._store.store_dir, graph)
        except Exception as exc:
            QMessageBox.critical(self, "Ref Lineage", f"Export failed:\n{exc}")
            self.log(f"Export failed: {exc}")
            return

        self.log(f"Exported: {path}")
        self.log(
            "Open the Lineage tab in A00210_FileManager and press Refresh to see it. "
            "Use Push there to sync."
        )
        QMessageBox.information(
            self, "Ref Lineage",
            f"Saved lineage graph '{name}'.\n\n{path}\n\n"
            "Open it from the Lineage tab in A00210_FileManager (press Refresh).",
        )
