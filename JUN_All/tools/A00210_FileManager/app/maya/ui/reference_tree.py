# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00210_FileManager / Maya 탭 - Reference 트리 위젯 (QTreeWidget)
#
# 스캔 결과(ref_scanner.scan)를 보여 준다.
#   최상위 행 = 스캔한 마야 파일들이 **직접** 부르는 레퍼런스 파일(경로로 중복 제거) - 체크박스.
#              열 2 `Used by` 에 그 레퍼런스를 부르는 마야 파일 이름들. 툴팁에 절대경로.
#   자식 행   = 그 레퍼런스 파일이 또 부르는 레퍼런스(중첩, 재귀). **기본 전부 접힘.**
#              체크박스 없음(결정 2026-10-12 ④) - 부모를 임포트하면 중첩은 자동으로 함께 임포트된다.
#   끊긴 경로 = 빨강 + 체크 불가. 순환 = `[cycle]` 표시, 더 내려가지 않는다.
# Shift 다중 체크는 공용 JUN_mod_checkTree_qt_v01, 우클릭 Reveal / Copy · 더블클릭은 공용 path_context.

import os

from Framework.qt.qt import (
    Qt,
    QTreeWidget,
    QTreeWidgetItem,
    QBrush,
    QColor,
    QHeaderView,
    Signal,
)
from Framework.qt import path_context
from Framework.qt.MOD_checkTree_qt_v01 import JUN_mod_checkTree_qt_v01
from Framework.qt.MOD_tsl_qt_v01 import null_item_color

ROLE_KEY = Qt.UserRole + 2        # 스캔 결과의 norm 키
NESTED_COLOR = "#9a9a9a"


class ReferenceTree(QTreeWidget):

    #: 체크된 최상위 레퍼런스 키 목록이 바뀌었다
    checksChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels(["Reference", "Used by"])
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.setRootIsDecorated(True)
        self.setToolTip(
            "References used by the scanned Maya files. Open a row to see the references\n"
            "that file uses itself (nested - imported together with its parent).\n"
            "Check the references to import. Select several rows (Shift / Ctrl) and click\n"
            "one check box to check or uncheck them all.\n"
            "Double-click: open in File Explorer.")

        self._scan = None
        self._behavior = JUN_mod_checkTree_qt_v01(self)
        self._behavior.checksChanged.connect(lambda _items: self.checksChanged.emit(self.checked_keys()))
        path_context.attach_path_context(
            self, lambda item: item.data(0, Qt.UserRole) or "", title="Reference")

        self._brush_missing = QBrush(QColor(null_item_color()))
        self._brush_nested = QBrush(QColor(NESTED_COLOR))

    # ------------------------------------------------------------------ fill

    def load(self, scan_result):
        """스캔 결과를 그린다(전부 접힘). 이전 체크는 같은 키면 유지한다."""
        previous = set(self.checked_keys())
        self._scan = scan_result
        self.clear()
        if not scan_result:
            return
        nodes = scan_result.get("nodes", {})

        # 최상위: 스캔 순서대로, 경로로 한 번만
        order = []
        for maya_file in scan_result.get("files", []):
            for key in scan_result["roots"].get(maya_file, []):
                if key not in order:
                    order.append(key)

        for key in order:
            node = nodes.get(key)
            if node is None:
                continue
            item = self._make_item(node, nested=False)
            used = ", ".join(os.path.basename(f) for f in node.get("used_by", []))
            item.setText(1, used)
            item.setToolTip(1, "\n".join(node.get("used_by", [])))
            if node.get("exists", True):
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked if key in previous else Qt.Unchecked)
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
            self.addTopLevelItem(item)
            self._add_nested(item, node, nodes, {key})

        self.collapseAll()

    def _make_item(self, node, nested):
        item = QTreeWidgetItem([node["name"], ""])
        item.setData(0, Qt.UserRole, node["path"])
        item.setData(0, ROLE_KEY, _key_of(node))
        tip = node["path"]
        if not node.get("exists", True):
            tip += "\nFile not found"
            item.setForeground(0, self._brush_missing)
        elif nested:
            item.setForeground(0, self._brush_nested)
            item.setForeground(1, self._brush_nested)
        if node.get("error"):
            tip += "\n" + node["error"]
        item.setToolTip(0, tip)
        return item

    def _add_nested(self, parent_item, node, nodes, ancestors):
        for child_key in node.get("children", []):
            child = nodes.get(child_key)
            if child is None:
                continue
            item = self._make_item(child, nested=True)
            item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)   # 자식은 체크 없음 (④)
            label = "(nested)"
            if child_key in ancestors or child.get("cycle"):
                label = "(nested) [cycle]"
            item.setText(1, label)
            parent_item.addChild(item)
            if child_key in ancestors:
                continue                                        # 순환 - 더 내려가지 않는다
            self._add_nested(item, child, nodes, ancestors | {child_key})

    # ------------------------------------------------------------------ query

    def top_items(self):
        return [self.topLevelItem(i) for i in range(self.topLevelItemCount())]

    def checked_keys(self):
        return [it.data(0, ROLE_KEY) for it in self.top_items()
                if it.data(0, Qt.CheckStateRole) is not None and it.checkState(0) == Qt.Checked]

    def checked_names(self):
        return [it.text(0) for it in self.top_items()
                if it.data(0, Qt.CheckStateRole) is not None and it.checkState(0) == Qt.Checked]

    def set_all_checked(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        self.blockSignals(True)
        try:
            for it in self.top_items():
                if it.data(0, Qt.CheckStateRole) is not None:
                    it.setCheckState(0, state)
        finally:
            self.blockSignals(False)
        self.checksChanged.emit(self.checked_keys())

    def scan_result(self):
        return self._scan


def _key_of(node):
    # ref_scanner 의 norm_path 와 같은 규칙 - 결과 dict 에 키가 따로 없으므로 경로로 다시 만든다.
    path = node.get("path", "")
    return os.path.normcase(os.path.normpath(os.path.abspath(path))) if path else ""
