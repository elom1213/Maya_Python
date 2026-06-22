# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00250_SceneMemo - Qt UI

import time

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00250_SceneMemo.app.config.version import VERSION, LAST_UPDATE
from tools.A00250_SceneMemo.app.core import MemoStore
from tools.A00250_SceneMemo.app.core import memo_io


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00250_SceneMemo_window"


class MainWindow(QWidget):

    def __init__(self):

        # 마야 메인 윈도우에 parent 하되 Qt.Window 플래그로 독립 창처럼 띄운다.
        super().__init__(maya_main_window())
        self.setWindowFlags(Qt.Window)

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.store = MemoStore()

        self.win_title = f"Scene Memo  v{VERSION}"
        self.resize(560, 640)
        self.setWindowTitle(self.win_title)

        self._rows = []     # 현재 테이블에 표시 중인 메모 dict 목록
        self._total = 0     # 필터 전 전체 개수

        self.build_ui()
        self.refresh()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        layout = QVBoxLayout(self)

        # 상단 버튼
        top = QHBoxLayout()
        self.btn_add = QPushButton("Add Selected")
        self.btn_remove = QPushButton("Remove")
        self.btn_refresh = QPushButton("Refresh")
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_remove)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        # 검색
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter by object name or memo")
        search_row.addWidget(self.search)
        layout.addLayout(search_row)

        # 테이블
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Object", "Memo", "Updated"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 여러 행을 선택해 하나의 메모를 일괄 작성할 수 있도록 다중 선택 허용.
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        # 행 우클릭 컨텍스트 메뉴 (Select in Scene)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # 메모 에디터
        layout.addWidget(QLabel("Memo:"))
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write a memo for the selected row (Korean supported)...")
        layout.addWidget(self.editor)

        # 에디터 버튼 (Select in Scene 은 행 우클릭 메뉴로 제공)
        mid = QHBoxLayout()
        self.btn_save = QPushButton("Save Memo")
        mid.addWidget(self.btn_save)
        layout.addLayout(mid)

        # 부가 도구
        tools_row = QHBoxLayout()
        self.btn_clean = QPushButton("Clean Orphans")
        self.btn_export = QPushButton("Export")
        self.btn_import = QPushButton("Import")
        tools_row.addWidget(self.btn_clean)
        tools_row.addWidget(self.btn_export)
        tools_row.addWidget(self.btn_import)
        layout.addLayout(tools_row)

        # 상태 표시줄
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        # 시그널
        self.btn_add.clicked.connect(self.on_add_selected)
        self.btn_remove.clicked.connect(self.on_remove)
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_save.clicked.connect(self.on_save_memo)
        self.btn_clean.clicked.connect(self.on_clean_orphans)
        self.btn_export.clicked.connect(self.on_export)
        self.btn_import.clicked.connect(self.on_import)
        self.table.itemSelectionChanged.connect(self.on_row_changed)
        self.search.textChanged.connect(self.refresh)

    # --------------------------------------------------
    # helpers
    # --------------------------------------------------

    @staticmethod
    def _fmt_ts(ts):
        if not ts:
            return ""
        try:
            return time.strftime("%y-%m-%d %H:%M", time.localtime(ts))
        except Exception:
            return ""

    def _current_indices(self):
        return sorted(idx.row() for idx in self.table.selectionModel().selectedRows())

    def _current_uuids(self):
        return [self._rows[i]["uuid"]
                for i in self._current_indices()
                if 0 <= i < len(self._rows)]

    def _select_uuids(self, uuids):
        """주어진 UUID 들에 해당하는 행들을 모두 선택 상태로 복원."""
        if not uuids:
            return

        want = set(uuids)
        sel_model = self.table.selectionModel()
        model = self.table.model()

        self.table.blockSignals(True)
        self.table.clearSelection()

        last = -1
        for i, r in enumerate(self._rows):
            if r["uuid"] in want:
                sel_model.select(
                    model.index(i, 0),
                    QItemSelectionModel.Select | QItemSelectionModel.Rows
                )
                last = i

        if last >= 0:
            sel_model.setCurrentIndex(model.index(last, 0), QItemSelectionModel.NoUpdate)

        self.table.blockSignals(False)

        # 시그널을 막은 채 선택을 복원했으므로 에디터를 수동으로 동기화.
        self.on_row_changed()

    def _set_status(self, msg):
        self.status.setText(msg)

    def _update_status_count(self):
        if len(self._rows) == self._total:
            self.status.setText(f"{self._total} memo(s).")
        else:
            self.status.setText(f"{len(self._rows)} / {self._total} memo(s) shown.")

    # --------------------------------------------------
    # refresh
    # --------------------------------------------------

    def refresh(self):

        keep_uuids = self._current_uuids()

        all_rows = self.store.list_memos()
        self._total = len(all_rows)

        filt = (self.search.text() or "").lower().strip()
        if filt:
            def match(r):
                name = (r["node"] or r["name_hint"] or "").lower()
                return filt in name or filt in (r["memo"] or "").lower()
            rows = [r for r in all_rows if match(r)]
        else:
            rows = all_rows

        self._rows = rows

        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            if r["node"]:
                name = r["node"].split("|")[-1]
            else:
                name = "(missing) " + (r["name_hint"] or "?")

            preview = (r["memo"] or "").replace("\n", " ")
            if len(preview) > 40:
                preview = preview[:40] + "..."

            item_name = QTableWidgetItem(name)
            item_memo = QTableWidgetItem(preview)
            item_ts = QTableWidgetItem(self._fmt_ts(r["ts"]))

            if r["missing"]:
                for it in (item_name, item_memo, item_ts):
                    it.setForeground(QColor(150, 150, 150))

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, item_memo)
            self.table.setItem(row, 2, item_ts)

        self.table.blockSignals(False)

        if keep_uuids:
            self._select_uuids(keep_uuids)

        self._update_status_count()

    # --------------------------------------------------
    # actions
    # --------------------------------------------------

    def on_row_changed(self):
        rows = self._current_indices()

        if not rows:
            self.editor.clear()
            return

        memos = {self._rows[i]["memo"] or ""
                 for i in rows if 0 <= i < len(self._rows)}

        # 선택 행들의 메모가 모두 같으면 그 값을, 다르면 비워서 (일괄 덮어쓰기 입력용) 보여준다.
        if len(memos) == 1:
            self.editor.setPlainText(next(iter(memos)))
        else:
            self.editor.clear()

        if len(rows) > 1:
            self._set_status(
                f"{len(rows)} rows selected — Save Memo writes the same memo to all of them."
            )

    def on_add_selected(self):
        added, touched = self.store.add_selected()
        self.refresh()

        if not touched:
            self._set_status("Nothing selected in the scene.")
            return

        self._select_uuids(touched)
        self._set_status(f"Added {added} new object(s). Remember to save the Maya file (Ctrl+S).")

    def on_remove(self):
        uuids = self._current_uuids()
        if not uuids:
            self._set_status("Select one or more rows to remove.")
            return

        for uuid in uuids:
            self.store.remove(uuid)

        self.refresh()
        self._set_status(f"Removed {len(uuids)} memo(s). Remember to save the Maya file (Ctrl+S).")

    def on_save_memo(self):
        uuids = self._current_uuids()
        if not uuids:
            self._set_status("Select one or more rows first.")
            return

        text = self.editor.toPlainText()

        for uuid in uuids:
            # 각 노드의 짧은 이름을 hint 로 스냅샷 (노드가 나중에 삭제돼도 식별용)
            nodes = cmds.ls(uuid) or []
            hint = nodes[0].split("|")[-1] if nodes else None
            self.store.set_memo(uuid, text, name_hint=hint)

        self.refresh()
        self._select_uuids(uuids)
        self._set_status(
            f"Saved the memo to {len(uuids)} object(s). "
            "Remember to save the Maya file (Ctrl+S)."
        )

    def on_table_context_menu(self, pos):
        # 우클릭한 행이 현재 선택에 없으면 그 행만 선택 (일반적인 우클릭 동작)
        index = self.table.indexAt(pos)
        if index.isValid() and index.row() not in self._current_indices():
            self.table.selectRow(index.row())

        if not self._current_uuids():
            return

        menu = QMenu(self.table)
        act_select = menu.addAction("Select in Scene")
        chosen = menu.exec_(self.table.viewport().mapToGlobal(pos))

        if chosen == act_select:
            self.on_select_in_scene()

    def on_select_in_scene(self):
        uuids = self._current_uuids()
        if not uuids:
            self._set_status("Select one or more rows first.")
            return

        found = self.store.select_in_scene(uuids)

        if not found:
            self._set_status("No nodes found in the current scene (missing).")
        elif found < len(uuids):
            self._set_status(f"Selected {found} node(s); some are missing.")

    def on_clean_orphans(self):
        n = self.store.clean_orphans()
        self.refresh()
        self._set_status(f"Removed {n} orphan memo(s).")

    def on_export(self):
        path = memo_io.export_sidecar(self.store)
        if not path:
            self._set_status("Save the scene first, then export.")
            return
        self._set_status(f"Exported: {path}")

    def on_import(self):
        result = memo_io.import_sidecar(self.store)
        if result is None:
            self._set_status("No sidecar file found for this scene (JUN_memo/<scene>_memo.json).")
            return

        added, updated = result
        self.refresh()
        self._set_status(f"Imported (added {added}, updated {updated}).")
