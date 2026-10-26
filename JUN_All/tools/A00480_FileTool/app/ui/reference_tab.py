# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00480_FileTool - Reference 탭 (in-Maya)
#
# 하위 탭 `Default` : 현재 씬의 레퍼런스를 **중첩(이중 · 삼중)까지 트리**로 보여 주고,
# 고른 파일들을 탐색기에서 열거나(Open in Explorer / 더블클릭) 경로를 복사한다(Copy Path).
# 여러 행을 골라 한 번에 - 열기는 파일마다 탐색기 창, 복사는 한 줄에 하나.
# 레퍼런스를 읽는 것 · 열기 · 복사 문자열은 core.reference_ops, 클립보드 · 메뉴는 여기(Qt).
# 새 하위 탭(예: 경로 바꾸기)은 `ReferenceTab.build_ui` 에 addTab 한 줄.

import os

from Framework.qt.qt import (
    Qt,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
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

ROLE_PATH = Qt.UserRole + 1
UNLOADED_COLOR = "#9a9a9a"

COL_NAME, COL_FILE, COL_STATUS = 0, 1, 2


class ReferenceDefaultPage(QWidget):
    """Reference > Default : 씬 레퍼런스 트리 + Open in Explorer / Copy Path."""

    def __init__(self, log=None, parent=None):
        super(ReferenceDefaultPage, self).__init__(parent)
        self._log_callback = log
        self.rows = []
        self.buttons = {}
        self._brush_missing = QBrush(QColor(null_item_color()))
        self._brush_unloaded = QBrush(QColor(UNLOADED_COLOR))
        self.build_ui()

    # ------------------------------------------------------------------ UI

    def build_ui(self):
        layout = QVBoxLayout(self)

        head = QHBoxLayout()
        self.count_label = QLabel("Scene references (nested included)")
        head.addWidget(self.count_label, stretch=1)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Read the references of the current scene again.")
        self.refresh_button.clicked.connect(self.refresh)
        self.buttons["Refresh"] = self.refresh_button
        head.addWidget(self.refresh_button)
        layout.addLayout(head)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Reference", "File", "Status"])
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
        self.refresh()

    def _make_item(self, row):
        name = row["namespace"] + (row["copy"] or "")
        item = QTreeWidgetItem([name, os.path.normpath(row["path"]) if row["path"] else "", row["status"]])
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
    """Reference 탭 = 하위 탭 Default (앞으로 늘어난다)."""

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
                                   "open them in File Explorer, copy their paths.")
        layout.addWidget(self.tabs)

        self.tree = self.default_page.tree
        self.buttons = self.default_page.buttons

    def refresh(self):
        self.default_page.refresh()
