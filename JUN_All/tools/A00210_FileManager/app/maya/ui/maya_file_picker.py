# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 - 마야 파일 고르기 (하위탭 공용, v01.41). reference_tab.py 의 트리 + Add Checked / Browse + Maya File TSL 을 뽑았다.
#
# 세 조각을 만들어 두고 **배치는 하위탭이** 한다 (Reference 는 트리 | (Maya File | Reference 트리), Export 는 트리 / Maya File | Rule):
#   picker.tree      : 공용 폴더 트리 (JUN_mod_fileTree_qt_v01, 파일 체크, 기본 타입 ma/mb/fbx)
#   picker.add_bar   : [Add Checked] [Browse...]  Checked in tree: 0
#   picker.maya_list : Maya File TSL (UUID · 재정렬 끔 - 재정렬은 UUID 역할만 옮겨 UserRole 의 경로를 잃는다), [Clear]
# API: file_rows() · file_paths() · selected_file_paths() · add_files(paths) · clear() · filesChanged(list) 신호.

import os

from Framework.qt.qt import (
    Qt,
    Signal,
    QObject,
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QBrush,
    QColor,
)
from Framework.qt import path_context
from Framework.qt.MOD_fileTree_qt_v01 import JUN_mod_fileTree_qt_v01
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01, null_item_color

from ..core import ref_scanner

DEFAULT_TYPES = ("ma", "mb", "fbx")        # Reference 계획 결정 ⑧
FILE_FILTER = "Maya Files (*.ma *.mb);;All Files (*)"


class MayaFilePicker(QObject):

    filesChanged = Signal(list)         # Maya File 목록이 바뀌면 (절대경로 목록)

    def __init__(self, log=None, list_tooltip=None, parent=None):
        super().__init__(parent)
        self._log_callback = log

        # ---- 폴더 트리 -------------------------------------------------
        self.tree = JUN_mod_fileTree_qt_v01(checkable_files=True, default_types=DEFAULT_TYPES)
        self.tree.tree.setMinimumHeight(140)
        self.tree.checksChanged.connect(self._on_tree_checks_changed)

        # ---- Add Checked / Browse 행 -------------------------------------
        self.add_bar = QWidget()
        add_row = QHBoxLayout(self.add_bar)
        add_row.setContentsMargins(0, 0, 0, 0)
        self.btn_add_checked = QPushButton("Add Checked")
        self.btn_add_checked.setToolTip("Add the files checked in the tree above to the Maya File list.")
        self.btn_add_checked.clicked.connect(self.on_add_checked)
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setToolTip("Pick Maya files with a file dialog (several at once).")
        self.btn_browse.clicked.connect(self.on_browse)
        self.lbl_checked = QLabel("Checked in tree: 0")
        add_row.addWidget(self.btn_add_checked)
        add_row.addWidget(self.btn_browse)
        add_row.addWidget(self.lbl_checked)
        add_row.addStretch(1)

        # ---- Maya File TSL ----------------------------------------------
        self.maya_list = JUN_mod_tsl_qt_v01(
            title="Maya File", show_select=False, show_add=False, show_del=True,
            show_up=False, show_down=False, show_sort=False, show_order=False,
            attach_uuids=False, list_min_height=120, log_callback=self._log)
        self.maya_list.list_widget.setToolTip(
            list_tooltip or "Maya files to work on.\nDouble-click: open in File Explorer.")
        try:
            self.maya_list.list_widget.itemSelectionChanged.disconnect(self.maya_list._on_selection_changed)
        except (RuntimeError, TypeError):
            pass
        self.maya_list.add_button("Clear", self.clear)
        path_context.attach_path_context(
            self.maya_list.list_widget, lambda item: item.data(Qt.UserRole) or "", title="Maya File")
        # Del 버튼 · Clear 로 줄어드는 것도 알린다
        self.maya_list.list_widget.model().rowsRemoved.connect(self._emit_changed)
        self.maya_list.list_widget.model().modelReset.connect(self._emit_changed)

    # ==================================================================
    def file_rows(self):
        """[(표시 이름, 절대경로), ...]"""
        lw = self.maya_list.list_widget
        return [(lw.item(i).text(), lw.item(i).data(Qt.UserRole) or "") for i in range(lw.count())]

    def file_paths(self):
        return [p for _n, p in self.file_rows() if p]

    def selected_file_paths(self):
        return [item.data(Qt.UserRole) for item in self.maya_list.list_widget.selectedItems()
                if item.data(Qt.UserRole)]

    def add_files(self, paths):
        """중복 없이 담는다(경로 기준). 같은 이름이 다른 폴더에 있으면 이름 뒤에 폴더를 붙인다."""
        existing = {ref_scanner.norm_path(p) for p in self.file_paths()}
        names = {n for n, _p in self.file_rows()}
        added = 0
        for path in paths or []:
            if not path:
                continue
            path = os.path.normpath(os.path.abspath(path))
            key = ref_scanner.norm_path(path)
            if key in existing:
                self._log("{0} is already in the list.".format(os.path.basename(path)))
                continue
            if not ref_scanner.is_maya_scene(path):
                self._log("[WARN] Not a Maya scene, skipped : {0}".format(path))
                continue
            name = os.path.basename(path)
            if name in names:
                name = "{0}  ({1})".format(name, os.path.basename(os.path.dirname(path)))
            item = self.maya_list._add_item(name)
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            if not os.path.isfile(path):
                item.setForeground(QBrush(QColor(null_item_color())))
                item.setToolTip(path + "\nFile not found")
            existing.add(key)
            names.add(name)
            added += 1
        self.maya_list._update_number()
        if added:
            self._log("Added {0} Maya file(s).".format(added))
            self._emit_changed()
        return added

    def clear(self, *_args):
        self.maya_list.clear()
        self._emit_changed()

    def on_add_checked(self, *_args):
        paths = self.tree.checked_paths()
        if not paths:
            self._log("Nothing is checked in the tree.")
            return
        self.add_files(paths)

    def on_browse(self, *_args):
        start = ""
        rows = self.file_paths()
        if rows:
            start = os.path.dirname(rows[-1])
        paths, _flt = QFileDialog.getOpenFileNames(self.add_bar, "Select Maya Files", start, FILE_FILTER)
        if paths:
            self.add_files(paths)

    # ==================================================================
    def _on_tree_checks_changed(self, paths):
        self.lbl_checked.setText("Checked in tree: {0}".format(len(paths)))

    def _emit_changed(self, *_args):
        self.filesChanged.emit(self.file_paths())

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
