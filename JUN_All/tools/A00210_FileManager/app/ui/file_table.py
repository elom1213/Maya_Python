# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - file list widget (Qt)
#
# 스캔된 Maya 파일 목록을 표시한다. 각 행에 파일명/작업자/썸네일유무/수정시각.
# 선택 시 file_selected(entry dict) 시그널을 보낸다.

import time

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    Qt,
    Signal,
)


class FileTable(QWidget):

    file_selected = Signal(object)   # entry dict

    HEADERS = ["File", "Author", "Thumb", "Record", "Modified"]

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(self.HEADERS))
        self.tree.setHeaderLabels(self.HEADERS)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionBehavior(QTreeWidget.SelectRows)
        self.tree.currentItemChanged.connect(self._on_current_changed)

        layout.addWidget(self.tree)

    def set_entries(self, entries):
        """scanner.scan() 결과 리스트를 표시."""
        self.tree.clear()

        for entry in entries:
            item = QTreeWidgetItem()
            item.setText(0, entry["file_name"])
            item.setText(1, entry.get("author", ""))
            item.setText(2, "O" if entry.get("has_thumb") else "")
            item.setText(3, "O" if entry.get("has_record") else "")

            mtime = entry.get("mtime", 0)
            if mtime:
                item.setText(
                    4,
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime)),
                )

            if not entry.get("in_root", True):
                # 프로젝트 루트 밖: 회색 처리 + 안내
                item.setForeground(0, Qt.gray)
                item.setText(1, "(out of project root)")

            item.setData(0, Qt.UserRole, entry)
            self.tree.addTopLevelItem(item)

        for col in range(len(self.HEADERS)):
            self.tree.resizeColumnToContents(col)

    def current_entry(self):
        item = self.tree.currentItem()
        if item is None:
            return None
        return item.data(0, Qt.UserRole)

    def _on_current_changed(self, current, _previous):
        if current is None:
            self.file_selected.emit(None)
            return
        self.file_selected.emit(current.data(0, Qt.UserRole))
