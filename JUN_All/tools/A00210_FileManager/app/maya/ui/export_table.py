# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - 파일 표 (QTableWidget)  (v01.41)
#
#   ☑ │ File │ Set │ Start │ End │ FPS │ Ver │ Output │ Status
#   - 편집 가능 = ☑ · Start · End 만. File 은 UserRole 에 절대 경로, 더블클릭 = Reveal (공용 path_context).
#   - Set 열은 Check Sets(probe) 결과 `Bake (1 -> 78)`; 없으면 `-` + 빨강, 체크 해제, Status `no set`.
#   - Ver 는 2023 미만이면 노랑([WARN] 색). exported 는 초록, failed · collision · invalid 는 빨강.
#   - Output 은 export_naming.preview 의 결과(실행 전에도 보인다).
# API: set_files(paths) · apply_probe(result) · set_output(rows) · fill_range(mode, custom) · checked_rows() · set_status(file, text, level)
#      · probed(file) · existing_outputs()

import os

from Framework.qt.qt import (
    Qt,
    Signal,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QBrush,
    QColor,
)
from Framework.qt import path_context
from Framework.qt.MOD_tsl_qt_v01 import null_item_color
from Framework.core import log_levels

from ..core import export_jobs
from ..core import export_naming

COLUMNS = ("", "File", "Set", "Start", "End", "FPS", "Ver", "Output", "Status")
COL_CHECK, COL_FILE, COL_SET, COL_START, COL_END, COL_FPS, COL_VER, COL_OUT, COL_STATUS = range(len(COLUMNS))
MIN_VERSION = 2023


def _color(level):
    try:
        from Framework.themes.theme_manager import ThemeManager
        dark = ThemeManager.is_dark_theme()
    except Exception:  # noqa: BLE001
        dark = True
    return log_levels.color(level, dark) or "#ff6b6b"


class ExportTable(QTableWidget):

    rangeEdited = Signal()

    def __init__(self, parent=None):
        super().__init__(0, len(COLUMNS), parent)
        self.setHorizontalHeaderLabels(COLUMNS)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_FILE, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_OUT, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_SET, QHeaderView.Interactive)
        self.setMinimumHeight(110)
        self.setToolTip(
            "One row per Maya file. Check Sets fills Set / Start / End / FPS / Ver.\n"
            "Start and End can be edited. Output is the FBX name from the Naming rule.\n"
            "Double-click a file: open in File Explorer.")
        self._probe = {}          # path -> probe 항목
        self._rows = {}           # path -> export_naming.Row
        self._status = {}         # path -> (text, level)
        self._block = False
        self.itemChanged.connect(self._on_item_changed)
        path_context.attach_path_context(self, lambda item: self._path_of_row(item.row()), title="Maya File")

    # ------------------------------------------------------------------ rows
    def _path_of_row(self, row):
        item = self.item(row, COL_FILE)
        return (item.data(Qt.UserRole) or "") if item else ""

    def _row_of(self, path):
        key = os.path.normcase(path)
        for r in range(self.rowCount()):
            if os.path.normcase(self._path_of_row(r)) == key:
                return r
        return -1

    def paths(self):
        return [self._path_of_row(r) for r in range(self.rowCount())]

    def set_files(self, paths):
        """목록을 맞춘다 - 있던 행은 그대로(probe 값 · 체크 유지), 새 행 추가, 빠진 행 제거."""
        self._block = True
        try:
            wanted = [os.path.normcase(p) for p in paths]
            for r in reversed(range(self.rowCount())):
                if os.path.normcase(self._path_of_row(r)) not in wanted:
                    self.removeRow(r)
            have = {os.path.normcase(p) for p in self.paths()}
            for path in paths:
                if os.path.normcase(path) in have:
                    continue
                r = self.rowCount()
                self.insertRow(r)
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                chk.setCheckState(Qt.Checked)
                self.setItem(r, COL_CHECK, chk)
                f = QTableWidgetItem(os.path.basename(path))
                f.setData(Qt.UserRole, path)
                f.setToolTip(path)
                self.setItem(r, COL_FILE, f)
                for c in (COL_SET, COL_FPS, COL_VER, COL_OUT, COL_STATUS):
                    self.setItem(r, c, self._ro("-"))
                for c in (COL_START, COL_END):
                    it = QTableWidgetItem("")
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(r, c, it)
                if path in self._probe:
                    self._apply_probe_row(r, self._probe[path])
        finally:
            self._block = False

    @staticmethod
    def _ro(text):
        it = QTableWidgetItem(text)
        it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        return it

    # ------------------------------------------------------------------ probe
    def apply_probe(self, result, range_mode=export_jobs.RANGE_TIMELINE, custom=(0, 100)):
        for item in (result or {}).get("files", []):
            self._probe[item["file"]] = item
            r = self._row_of(item["file"])
            if r >= 0:
                self._apply_probe_row(r, item)
        self.fill_range(range_mode, custom)

    def _apply_probe_row(self, r, item):
        self._block = True
        try:
            if not item.get("ok"):
                self.item(r, COL_SET).setText("-")
                self._paint(r, COL_SET, "ERROR")
                self.item(r, COL_CHECK).setCheckState(Qt.Unchecked)
                self.set_status(self._path_of_row(r), "failed ({0})".format(item.get("error", "?")), "ERROR")
                return
            sets = item.get("sets") or []
            if sets:
                text = ", ".join("{0} ({1} -> {2})".format(s["name"], s["members"], s["nodes"]) for s in sets)
                self.item(r, COL_SET).setText(text)
                self.item(r, COL_SET).setToolTip("set (members -> transforms incl. descendants)")
                self._paint(r, COL_SET, None)
            else:
                self.item(r, COL_SET).setText("-")
                self.item(r, COL_SET).setToolTip("No set matches the rule - this file is skipped.")
                self._paint(r, COL_SET, "ERROR")
                self.item(r, COL_CHECK).setCheckState(Qt.Unchecked)
            fps = item.get("fps")
            self.item(r, COL_FPS).setText(_num(fps) if fps is not None else "?")
            self.item(r, COL_FPS).setToolTip("time unit : {0}".format(item.get("unit", "?")))
            ver = item.get("version") or "?"
            self.item(r, COL_VER).setText(ver)
            try:
                old = int(str(ver)[:4]) < MIN_VERSION
            except ValueError:
                old = False
            self._paint(r, COL_VER, "WARN" if old else None)
            self.item(r, COL_VER).setToolTip("saved with Maya {0}{1}".format(ver, " - older than 2023" if old else ""))
            refs = item.get("references") or {}
            self.item(r, COL_FILE).setToolTip("{0}\nreferences : {1} loaded, {2} unloaded\nplayback {3} - {4}, anim {5} - {6}".format(
                item["file"], refs.get("loaded", 0), refs.get("unloaded", 0),
                _num(item["playback"][0]), _num(item["playback"][1]), _num(item["anim"][0]), _num(item["anim"][1])))
        finally:
            self._block = False
        self._refresh_status_row(r)

    def probed(self, path):
        return path in self._probe and self._probe[path].get("ok", False)

    def fill_range(self, mode, custom=(0, 100)):
        """Start/End 를 probe 값(또는 Custom)으로 채운다. probe 가 없는 행은 Custom 일 때만."""
        self._block = True
        try:
            for r in range(self.rowCount()):
                path = self._path_of_row(r)
                item = self._probe.get(path)
                if mode == export_jobs.RANGE_CUSTOM:
                    rng = custom
                elif item and item.get("ok"):
                    rng = item["anim"] if mode == export_jobs.RANGE_ANIM else item["playback"]
                else:
                    continue
                self.item(r, COL_START).setText(_num(rng[0]))
                self.item(r, COL_END).setText(_num(rng[1]))
        finally:
            self._block = False

    # ------------------------------------------------------------------ output names
    def set_output(self, rows):
        """export_naming.preview 결과."""
        self._rows = {r.file: r for r in rows}
        self._block = True
        try:
            for r in range(self.rowCount()):
                row = self._rows.get(self._path_of_row(r))
                if row is None:
                    continue
                it = self.item(r, COL_OUT)
                it.setText(row.out_name)
                it.setToolTip(row.out_path + ("\n" + "\n".join(row.notes) if row.notes else ""))
                self._paint(r, COL_OUT, "ERROR" if not row.ok else None)
        finally:
            self._block = False
        for r in range(self.rowCount()):
            self._refresh_status_row(r)

    def existing_outputs(self):
        """체크된 · 준비된 행 중 이미 디스크에 있는 출력 경로."""
        return [row["out_fbx"] for row in self.checked_rows() if os.path.isfile(row["out_fbx"])]

    # ------------------------------------------------------------------ status
    def _refresh_status_row(self, r):
        path = self._path_of_row(r)
        if path in self._status and self._status[path][0] in (export_jobs.STATUS_EXPORTED, export_jobs.STATUS_SKIPPED) \
                or (path in self._status and self._status[path][0].startswith(export_jobs.STATUS_FAILED)):
            return                                      # 실행 결과는 다음 변경까지 남긴다
        row = self._rows.get(path)
        item = self._probe.get(path)
        if row is not None and row.invalid:
            self.set_status(path, export_jobs.STATUS_INVALID, "ERROR", remember=False)
        elif row is not None and row.collision:
            self.set_status(path, export_jobs.STATUS_COLLISION, "ERROR", remember=False)
        elif item is not None and item.get("ok") and not item.get("sets"):
            self.set_status(path, export_jobs.STATUS_NO_SET, "SKIP", remember=False)
        elif item is not None and item.get("ok"):
            self.set_status(path, export_jobs.STATUS_READY, "OK", remember=False)
        elif item is None:
            self.set_status(path, "-", None, remember=False)

    def set_status(self, path, text, level=None, remember=True):
        r = self._row_of(path)
        if r < 0:
            return
        self.item(r, COL_STATUS).setText(text)
        self._paint(r, COL_STATUS, level)
        if remember:
            self._status[path] = (text, level)
        else:
            self._status.pop(path, None)

    def clear_results(self):
        """실행 결과 표시를 지우고 준비 상태로 되돌린다 (Naming · 규칙이 바뀌었을 때)."""
        self._status = {}
        for r in range(self.rowCount()):
            self._refresh_status_row(r)

    def reset_probe(self):
        """규칙이 바뀌면 Set 열을 비운다 (다시 Check Sets)."""
        self._probe = {}
        self._status = {}
        self._block = True
        try:
            for r in range(self.rowCount()):
                self.item(r, COL_SET).setText("-")
                self._paint(r, COL_SET, None)
                self.item(r, COL_CHECK).setCheckState(Qt.Checked)
        finally:
            self._block = False
        for r in range(self.rowCount()):
            self._refresh_status_row(r)

    def apply_results(self, result):
        for res in (result or {}).get("results", []):
            status = res.get("status", "")
            if status == export_jobs.STATUS_EXPORTED:
                self.set_status(res["file"], status, "OK")
            elif status == export_jobs.STATUS_SKIPPED:
                self.set_status(res["file"], "{0} ({1})".format(status, res.get("error", "")), "SKIP")
            else:
                self.set_status(res["file"], "{0} ({1})".format(status, res.get("error", "")), "ERROR")

    def _paint(self, r, c, level):
        item = self.item(r, c)
        if item is None:
            return
        if level:
            item.setForeground(QBrush(QColor(_color(level) if level != "ERROR" else null_item_color())))
        else:
            item.setData(Qt.ForegroundRole, None)

    # ------------------------------------------------------------------ rows out
    def checked_rows(self):
        """체크됐고 Status 가 ready 인 행 -> [{"file", "start", "end", "out_fbx"}]."""
        out = []
        for r in range(self.rowCount()):
            if self.item(r, COL_CHECK).checkState() != Qt.Checked:
                continue
            path = self._path_of_row(r)
            row = self._rows.get(path)
            item = self._probe.get(path)
            if row is None or not row.ok or item is None or not item.get("ok") or not item.get("sets"):
                continue
            out.append({"file": path, "start": self.item(r, COL_START).text().strip(),
                        "end": self.item(r, COL_END).text().strip(), "out_fbx": row.out_path})
        return out

    def unprobed_checked(self):
        """체크됐는데 Check Sets 를 안 한 파일들."""
        return [self._path_of_row(r) for r in range(self.rowCount())
                if self.item(r, COL_CHECK).checkState() == Qt.Checked and not self.probed(self._path_of_row(r))]

    def _on_item_changed(self, item):
        if self._block:
            return
        if item.column() in (COL_START, COL_END):
            self.rangeEdited.emit()


def _num(value):
    if value is None:
        return "?"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return "{0:g}".format(value)
