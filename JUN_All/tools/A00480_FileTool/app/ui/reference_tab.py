# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-30
# A00480_FileTool - Reference 탭 (in-Maya)
#
# 하위 탭 `Default` : 현재 씬의 레퍼런스를 **중첩(이중 · 삼중)까지 트리**로 보여 주고,
# 고른 파일들을 탐색기에서 열거나(Open in Explorer / 더블클릭) 경로를 복사한다(Copy Path).
# 여러 행을 골라 한 번에 - 열기는 파일마다 탐색기 창, 복사는 한 줄에 하나.
# 레퍼런스를 읽는 것 · 열기 · 복사 문자열은 core.reference_ops, 클립보드 · 메뉴는 여기(Qt).
# `Show` 콤보(v01.16) : File 열을 **전체 경로 / 파일 이름만** 으로 바꿔 본다. 긴 경로가 같은 폴더를 반복하면
# 이름만 보는 쪽이 읽기 쉽다. 글자만 바뀌고 열기 · 복사는 그대로 전체 경로. 고른 모드는 optionVar 에 기억.
# 하위 탭 `Lineage`(v01.17) : 같은 레퍼런스 관계를 **노드 그래프**로 - `reference_lineage_page.py`
# (A00211_RefLineage 로 데이터, A00210 Lineage 탭의 노드 · 화살표 그대로, Export 로 A00210 에 보낸다).
# 새 하위 탭은 `ReferenceTab.build_ui` 에 addTab 한 줄.

import os

from Framework.qt.qt import (
    Qt,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QApplication,
    QMenu,
    QBrush,
    QColor,
)
from Framework.qt import path_context
from Framework.qt.MOD_tsl_qt_v01 import null_item_color

from tools.A00480_FileTool.app.core import reference_ops as ops
from tools.A00480_FileTool.app.ui.reference_lineage_page import ReferenceLineagePage

ROLE_PATH = Qt.UserRole + 1
UNLOADED_COLOR = "#9a9a9a"

COL_NAME, COL_FILE, COL_STATUS = 0, 1, 2

# `Show` 콤보의 항목 (라벨, core 의 보기 모드) - Lineage 페이지와 같은 목록 · 같은 optionVar
VIEW_CHOICES = ops.FILE_VIEW_CHOICES


class ReferenceDefaultPage(QWidget):
    """Reference > Default : 씬 레퍼런스 트리 + Open in Explorer / Copy Path."""

    def __init__(self, log=None, parent=None):
        super(ReferenceDefaultPage, self).__init__(parent)
        self._log_callback = log
        self.rows = []
        self.buttons = {}
        self._brush_missing = QBrush(QColor(null_item_color()))
        self._brush_unloaded = QBrush(QColor(UNLOADED_COLOR))
        self.file_view = ops.load_file_view()
        self.build_ui()

    # ------------------------------------------------------------------ UI

    def build_ui(self):
        layout = QVBoxLayout(self)

        head = QHBoxLayout()
        self.count_label = QLabel("Scene references (nested included)")
        head.addWidget(self.count_label, stretch=1)
        # File 열 보기 모드 - 전체 경로 / 파일 이름만 (v01.16)
        head.addWidget(QLabel("Show"))
        self.view_combo = QComboBox()
        for label, _view in VIEW_CHOICES:
            self.view_combo.addItem(label)
        self.view_combo.setCurrentIndex(self._view_index(self.file_view))
        self.view_combo.setToolTip(
            "What the File column shows.\n"
            "Full Path : the whole path of each reference file (Windows style).\n"
            "File Name : only the file name - easier to read when every reference "
            "sits in the same long folder.\n"
            "Open in Explorer / Copy Path always use the full path. The choice is remembered.")
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        head.addWidget(self.view_combo)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Read the references of the current scene again.")
        self.refresh_button.clicked.connect(self.refresh)
        self.buttons["Refresh"] = self.refresh_button
        head.addWidget(self.refresh_button)
        layout.addLayout(head)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Reference", self._file_header(), "Status"])
        header = self.tree.header()
        header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_FILE, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeToContents)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setRootIsDecorated(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setToolTip(
            "Every reference of the current scene. A row under another row is a reference\n"
            "inside that reference (nested). Unloaded references hide their nested ones\n"
            "until they are loaded.\n"
            "Select rows (Shift / Ctrl) and use the buttons or the right-click menu.\n"
            "Double-click: open the file in File Explorer.")
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree, stretch=1)

        row = QHBoxLayout()
        specs = (
            ("Open in Explorer", self.on_open,
             "Open the selected reference files in File Explorer (one window per file,\n"
             "the file is selected). A missing file opens its folder instead."),
            ("Copy Path", self.on_copy,
             "Copy the paths of the selected references to the clipboard, one per line."),
        )
        for label, handler, tip in specs:
            button = QPushButton(label)
            button.setToolTip(tip)
            button.clicked.connect(handler)
            self.buttons[label] = button
            row.addWidget(button)
        layout.addLayout(row)

    # ------------------------------------------------------------------ fill

    def refresh(self, *_args):
        """씬을 다시 읽어 트리를 채운다. 전부 펼친다."""
        self.rows, logs = ops.scene_references()
        self.tree.clear()
        items = {}
        for row in self.rows:
            item = self._make_item(row)
            items[row["node"]] = item
            parent_item = items.get(row["parent"])
            if parent_item is not None:
                parent_item.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
        self.tree.expandAll()
        self.count_label.setText(ops.summary(self.rows).replace("[Info] ", ""))
        self._log_all(logs)

    def showEvent(self, event):
        # 탭을 열 때마다 현재 씬 기준으로 - 다른 씬을 열고 와도 Refresh 를 안 눌러도 된다.
        super(ReferenceDefaultPage, self).showEvent(event)
        # Lineage 페이지에서 보기 모드를 바꿨으면 따라간다(같은 optionVar).
        view = ops.load_file_view()
        if view != self.file_view:
            self.set_file_view(view)
        self.refresh()

    # ------------------------------------------------------------------ file column view

    @staticmethod
    def _view_index(view):
        for i, (_label, v) in enumerate(VIEW_CHOICES):
            if v == view:
                return i
        return 0

    def _file_header(self):
        return "File Name" if self.file_view == ops.FILE_VIEW_NAME else "File"

    def set_file_view(self, view):
        """File 열을 `path`(전체 경로) / `name`(파일 이름만) 으로 바꾼다. 씬은 다시 읽지 않는다."""
        if view not in ops.FILE_VIEWS:
            return
        self.file_view = view
        if self.view_combo.currentIndex() != self._view_index(view):
            self.view_combo.setCurrentIndex(self._view_index(view))      # -> _on_view_changed 가 다시 들어온다
            return
        for item in self._all_items():
            item.setText(COL_FILE, ops.file_text(item.data(COL_NAME, ROLE_PATH) or "", view))
        self.tree.headerItem().setText(COL_FILE, self._file_header())
        ops.save_file_view(view)

    def _on_view_changed(self, index):
        self.set_file_view(VIEW_CHOICES[index][1] if 0 <= index < len(VIEW_CHOICES) else ops.FILE_VIEW_PATH)

    def _make_item(self, row):
        name = row["namespace"] + (row["copy"] or "")
        item = QTreeWidgetItem([name, ops.file_text(row["path"], self.file_view), row["status"]])
        item.setData(COL_NAME, ROLE_PATH, row["path"])
        tip = "Node : {0}\nPath : {1}".format(row["node"], row["path"])
        if row["stored"] and row["stored"] != row["path"]:
            tip += "\nStored as : {0}".format(row["stored"])
        if row["status"] == ops.STATUS_MISSING:
            tip += "\nThe file does not exist on disk."
        elif row["nested_hidden"]:
            tip += "\nUnloaded - its nested references appear once it is loaded."
        for col in (COL_NAME, COL_FILE, COL_STATUS):
            item.setToolTip(col, tip)
            if row["status"] == ops.STATUS_MISSING:
                item.setForeground(col, self._brush_missing)
            elif row["status"] == ops.STATUS_UNLOADED:
                item.setForeground(col, self._brush_unloaded)
        return item

    # ------------------------------------------------------------------ selection

    def selected_paths(self):
        """고른 행들의 파일 경로(트리 순서, 중복 포함 - core 가 걸러 준다)."""
        selected = self.tree.selectedItems()
        paths = []
        for item in self._all_items():
            if item in selected:
                paths.append(item.data(COL_NAME, ROLE_PATH) or "")
        return [p for p in paths if p]

    def _all_items(self):
        out = []

        def walk(item):
            out.append(item)
            for i in range(item.childCount()):
                walk(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i))
        return out

    # ------------------------------------------------------------------ handlers

    def on_open(self, *_args):
        self._log_all(ops.open_reference_files(self.selected_paths()))

    def on_copy(self, *_args):
        text, logs = ops.clipboard_text(self.selected_paths())
        if text:
            clipboard = QApplication.clipboard()
            if clipboard is None:
                logs = ["[WARN] Could not access the system clipboard."]
            else:
                clipboard.setText(text)
        self._log_all(logs)

    def _on_double_click(self, item, *_args):
        path = item.data(COL_NAME, ROLE_PATH) or ""
        if path:
            self._log_all(ops.open_reference_files([path]))

    def build_context_menu(self):
        """우클릭 메뉴를 만든다(띄우지는 않는다 - 시험용 분리). (QMenu, {action: 실행 함수})"""
        menu = QMenu(self.tree)
        count = len(ops.unique_paths(self.selected_paths()))
        suffix = " ({0} files)".format(count) if count > 1 else ""
        handlers = {}
        act = menu.addAction(path_context.MENU_REVEAL + suffix)
        act.setEnabled(count > 0)
        handlers[act] = self.on_open
        act = menu.addAction(path_context.MENU_COPY + suffix)
        act.setEnabled(count > 0)
        handlers[act] = self.on_copy
        menu.addSeparator()
        handlers[menu.addAction("Refresh")] = self.refresh
        return menu, handlers

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is not None and not item.isSelected():
            self.tree.setCurrentItem(item)
        menu, handlers = self.build_context_menu()
        handler = handlers.get(menu.exec_(self.tree.viewport().mapToGlobal(pos)))
        if handler:
            handler()

    # ------------------------------------------------------------------ helper

    def _log_all(self, messages):
        for message in (messages or []):
            if self._log_callback:
                self._log_callback(message)


class ReferenceTab(QWidget):
    """Reference 탭 = 하위 탭 Default(트리) + Lineage(노드 그래프, v01.17)."""

    def __init__(self, log=None, parent=None):
        super(ReferenceTab, self).__init__(parent)
        self._log_callback = log
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.default_page = ReferenceDefaultPage(log=self._log_callback)
        self.tabs.addTab(self.default_page, "Default")
        self.tabs.setTabToolTip(0, "List the references of the current scene (nested included), "
                                   "open them in File Explorer, copy their paths. The File column "
                                   "can show the full path or just the file name.")
        self.lineage_page = ReferenceLineagePage(log=self._log_callback)
        index = self.tabs.addTab(self.lineage_page, "Lineage")
        self.tabs.setTabToolTip(index, "The same references as a node graph - one node per file, "
                                       "dashed arrow from the referenced file to the file that "
                                       "references it (drawn like A00210_FileManager > Lineage). "
                                       "Export writes it as an A00210 lineage graph.")
        layout.addWidget(self.tabs)

        self.tree = self.default_page.tree
        self.buttons = self.default_page.buttons
        self.view_combo = self.default_page.view_combo

    def refresh(self):
        self.default_page.refresh()
