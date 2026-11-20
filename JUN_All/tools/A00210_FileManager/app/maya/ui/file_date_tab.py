# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00210_FileManager / Maya 탭 / File Date - 체크한 파일의 "수정한 날짜"만 바꾼다 (v01.54)
#
#   위   : 공용 폴더 트리 (Reference · Export 와 같은 JUN_mod_fileTree_qt_v01 - 경로 입력 · Build · 파일 체크, 기본 타입 ma/mb/fbx)
#   가운데: 체크한 파일 표 - 이름 · 폴더 · 지금 수정한 날짜 · 바뀔 날짜 (트리에서 체크하면 바로 바뀐다)
#   아래 : New date(기본 오늘, [Today]) · Time(각 파일의 원래 시각 유지 / 고른 시각) · [Set Date] [Undo Last]
#
# 내용은 건드리지 않는다 - 코어 core/file_dates.py (os.utime). 모든 UI 문자열은 영어. (한국어는 주석/독스트링만)

import datetime
import os

from Framework.qt.qt import (
    Qt,
    QDate,
    QTime,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QDateEdit,
    QTimeEdit,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
)
from Framework.qt import path_context
from Framework.qt.MOD_fileTree_qt_v01 import JUN_mod_fileTree_qt_v01

from ..core import file_dates as fd
from ...core.paths import ui_path

DEFAULT_TYPES = ("ma", "mb", "fbx")
COL_NAME, COL_FOLDER, COL_NOW, COL_NEW = range(4)


class FileDateTab(QWidget):

    def __init__(self, log=None, parent=None):
        super().__init__(parent)
        self._log_callback = log
        self._last = []                 # 마지막 Set Date 결과 [DateChange] - Undo Last 용
        self.confirm = True             # 확인 창 (시험에서 끈다)
        self.build_ui()
        self._refresh_table()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        desc = QLabel("Change only the modified date of the checked files - the contents stay as they are.\n"
                      "Check .ma / .mb / .fbx files in the tree, pick the date (today by default), press Set Date.")
        desc.setWordWrap(True)
        root.addWidget(desc)

        self.file_tree = JUN_mod_fileTree_qt_v01(checkable_files=True, default_types=DEFAULT_TYPES,
                                                 tree_hint_height=220)
        self.file_tree.tree.setMinimumHeight(80)
        self.file_tree.checksChanged.connect(lambda *_a: self._refresh_table())

        files_box = QGroupBox("Checked Files")
        files_layout = QVBoxLayout(files_box)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File", "Folder", "Modified now", "Will be"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)                   # 긴 폴더 경로가 두 줄로 접혀 행이 높아지지 않게 - 가운데를 ... 로
        self.table.setTextElideMode(Qt.ElideMiddle)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(COL_NAME, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_FOLDER, QHeaderView.Stretch)
        hdr.setSectionResizeMode(COL_NOW, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_NEW, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(80)
        path_context.attach_path_context(self.table, self._row_path, title="File")
        files_layout.addWidget(self.table, stretch=1)
        btn_row = QHBoxLayout()
        self.lbl_count = QLabel("")
        btn_row.addWidget(self.lbl_count, 1)
        self.btn_uncheck = QPushButton("Uncheck All")
        self.btn_uncheck.setToolTip("Uncheck every file in the tree.")
        self.btn_uncheck.clicked.connect(lambda *_a: self.file_tree.clear_checks())
        btn_row.addWidget(self.btn_uncheck)
        files_layout.addLayout(btn_row)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.file_tree)
        splitter.addWidget(files_box)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, stretch=1)

        root.addWidget(self._build_date_box())

    def _build_date_box(self):
        box = QGroupBox("New Modified Date")
        lay = QVBoxLayout(box)

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Date"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setToolTip("The new modified date. Today by default.")
        self.date_edit.dateChanged.connect(lambda *_a: self._refresh_table())
        date_row.addWidget(self.date_edit)
        self.btn_today = QPushButton("Today")
        self.btn_today.setToolTip("Set the date back to today.")
        self.btn_today.clicked.connect(lambda *_a: self.date_edit.setDate(QDate.currentDate()))
        date_row.addWidget(self.btn_today)
        date_row.addStretch(1)
        lay.addLayout(date_row)

        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("Time"))
        self.time_buttons = QButtonGroup(self)
        self.rb_keep_time = QRadioButton("Keep each file's time")
        self.rb_keep_time.setToolTip("Only the date changes - every file keeps its own hour : minute : second.")
        self.rb_keep_time.setChecked(True)
        self.rb_set_time = QRadioButton("Set time")
        self.rb_set_time.setToolTip("Every file gets the same time of day (set on the right).")
        self.time_buttons.addButton(self.rb_keep_time)
        self.time_buttons.addButton(self.rb_set_time)
        self.time_edit = QTimeEdit(QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setToolTip("The time of day used when 'Set time' is on.")
        for w in (self.rb_keep_time, self.rb_set_time):
            w.toggled.connect(lambda *_a: self._sync_time_enabled())
        self.time_edit.timeChanged.connect(lambda *_a: self._refresh_table())
        time_row.addWidget(self.rb_keep_time)
        time_row.addWidget(self.rb_set_time)
        time_row.addWidget(self.time_edit)
        time_row.addStretch(1)
        lay.addLayout(time_row)
        self._sync_time_enabled()

        action_row = QHBoxLayout()
        self.btn_set = QPushButton("Set Date")
        self.btn_set.setMinimumHeight(32)
        self.btn_set.setToolTip("Change the modified date of the checked files. The file contents are not touched.")
        self.btn_set.clicked.connect(self.on_set_date)
        self.btn_undo = QPushButton("Undo Last")
        self.btn_undo.setMinimumHeight(32)
        self.btn_undo.setToolTip("Put back the modified dates the last Set Date changed.")
        self.btn_undo.clicked.connect(self.on_undo_last)
        action_row.addWidget(self.btn_set, 2)
        action_row.addWidget(self.btn_undo, 1)
        lay.addLayout(action_row)
        self._sync_buttons()
        return box

    # ==================================================================
    # 값
    # ==================================================================

    def new_date(self):
        d = self.date_edit.date()
        return datetime.date(d.year(), d.month(), d.day())

    def new_time(self):
        """고른 시각, 또는 None(각 파일의 원래 시각 유지)."""
        if self.rb_keep_time.isChecked():
            return None
        t = self.time_edit.time()
        return datetime.time(t.hour(), t.minute(), t.second())

    def checked_targets(self):
        """(바꿀 파일, [(건너뛸 파일, 이유)])."""
        return fd.split_targets(self.file_tree.checked_paths())

    # ==================================================================
    # 표
    # ==================================================================

    def _sync_time_enabled(self):
        self.time_edit.setEnabled(self.rb_set_time.isChecked())
        self._refresh_table()

    def _sync_buttons(self):
        if not hasattr(self, "btn_set"):
            return
        n = len(self.checked_targets()[0])
        self.btn_set.setText("Set Date ({0} file(s))".format(n) if n else "Set Date")
        self.btn_set.setEnabled(bool(n))
        self.btn_undo.setEnabled(any(c.ok for c in self._last))

    def _refresh_table(self):
        if not hasattr(self, "table") or not hasattr(self, "date_edit"):
            return
        keep, skipped = self.checked_targets()
        date, tod = self.new_date(), self.new_time()
        self.table.setRowCount(0)
        for path in keep:
            row = self.table.rowCount()
            self.table.insertRow(row)
            now = fd.modified(path)
            will = fd.new_timestamp(now, date, tod)
            values = (os.path.basename(path), ui_path(os.path.dirname(path)), fd.format_time(now), fd.format_time(will))
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, path)
                item.setToolTip(ui_path(path))
                self.table.setItem(row, col, item)
        note = "{0} file(s)".format(len(keep))
        if skipped:
            note += "  ({0} other checked file(s) are not .ma / .mb / .fbx and are left out)".format(len(skipped))
        self.lbl_count.setText(note)
        self._sync_buttons()

    def _row_path(self, item):
        return (item.data(Qt.UserRole) or "") if item is not None else ""

    # ==================================================================
    # 동작
    # ==================================================================

    def on_set_date(self, *_args):
        keep, skipped = self.checked_targets()
        if not keep:
            self._log("[WARN] Check .ma / .mb / .fbx files in the tree first.")
            return
        date, tod = self.new_date(), self.new_time()
        when = date.isoformat() + ("" if tod is None else " " + tod.strftime("%H:%M:%S"))
        if self.confirm:
            answer = QMessageBox.question(
                self, "Set Date",
                "Change the modified date of {0} file(s) to {1}{2}?\n\nThe file contents are not changed.".format(
                    len(keep), when, "" if tod is not None else " (each keeps its own time of day)"),
                QMessageBox.Yes | QMessageBox.No)
            if answer != QMessageBox.Yes:
                return
        results = fd.set_dates(keep, date, tod)
        self._last = results
        ok = [c for c in results if c.ok]
        for c in results:
            if not c.ok:
                self._log("[FAIL] {0} : {1}".format(os.path.basename(c.path), c.error))
        for path, why in skipped:
            self._log("[SKIP] {0} : {1}".format(os.path.basename(path), why))
        self._log("[OK] Set the modified date of {0} of {1} file(s) to {2}.".format(len(ok), len(keep), when))
        self._refresh_table()

    def on_undo_last(self, *_args):
        if not any(c.ok for c in self._last):
            self._log("[WARN] Nothing to undo.")
            return
        n = fd.restore(self._last)
        self._last = []
        self._log("[OK] Put back the modified date of {0} file(s).".format(n))
        self._refresh_table()

    def _log(self, message):
        if self._log_callback:
            self._log_callback(message)
