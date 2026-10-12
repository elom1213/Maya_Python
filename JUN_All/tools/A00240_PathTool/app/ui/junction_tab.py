# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00240_PathTool - "Junction" tab (Qt, standalone)
#
# `cmd /c mklink /J` 를 화면에서 한다. 하위 탭 둘:
#   Create : Sources 리스트(원본 폴더들) x Create In 리스트(만들 폴더들) -> 미리보기 표 -> Create.
#            n -> 1 (전부 한 폴더 안에) / n -> n (행 순서로 짝). 정션 이름은 원본 폴더 이름.
#            n -> n 에서 "Target row is the junction path" 를 켜면 타깃 행이 정션 경로 그 자체가 된다
#            (mklink 의 <Link> 처럼 이름까지 정한다).
#   Remove : 정션 목록(Junction | Target 표) -> Remove. **정션인 행만** 지운다 - 실제 폴더는 표에서
#            빨갛게 "not a junction" 으로 보이고 건드리지 않는다. Scan 으로 폴더 안의 정션을 찾아 담는다.
#
# 리스트에는 Add...(폴더 선택) · Paste(클립보드의 경로 줄들) · 탐색기에서 **끌어다 놓기**로 담는다.
# 로직은 core/junction.py (UI 비의존). 로그창은 하위 탭 둘이 함께 쓴다.

import os

from Framework.qt.qt import (
    Qt,
    QEvent,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QRadioButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QColor,
    QBrush,
)
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.core import log_levels
from Framework.themes.theme_manager import ThemeManager

from ..core import junction
from ..core import path_opener


def _level_color(level):
    return QColor(log_levels.color(level, ThemeManager.is_dark_theme()) or "#ffffff")


def _dropped_paths(event):
    """드롭 이벤트에서 로컬 경로들을 꺼낸다(파일 URL 만)."""
    mime = event.mimeData()
    if mime is None or not mime.hasUrls():
        return []
    out = []
    for url in mime.urls():
        if url.isLocalFile():
            out.append(os.path.normpath(url.toLocalFile()))
    return out


def _clipboard_paths():
    """클립보드 텍스트의 줄들 중 존재하는 경로만."""
    clipboard = QApplication.clipboard()
    text = clipboard.text() if clipboard is not None else ""
    out = []
    for line in (text or "").splitlines():
        line = line.strip().strip('"')
        if line and os.path.exists(line):
            out.append(os.path.normpath(line))
    return out


class _PathList(QWidget):
    """폴더 경로 리스트 - 공용 TSL 에 Add...(폴더 선택) · Paste · 드롭을 얹은 것.

    TSL 의 마야 전용 버튼(Select / Add = 씬 선택)은 끄고, 그 자리에 경로용 버튼을 둔다.
    항목은 경로 문자열 그대로다(UUID 부착 없음).
    """

    def __init__(self, title, log, browse_title="Select Folder", parent=None):
        super().__init__(parent)
        self._log = log
        self._browse_title = browse_title
        self._last_dir = os.path.expanduser("~")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tsl = JUN_mod_tsl_qt_v01(
            title=title, show_select=False, show_add=False, show_order=False,
            show_sort=False, attach_uuids=False, log_callback=log)
        self.tsl.add_button("Add...", self._on_browse, index=0)
        btn_paste = self.tsl.add_button("Paste", self._on_paste, index=1)
        btn_paste.setToolTip("Add the paths on the clipboard (one per line).")
        layout.addWidget(self.tsl)

        self.list_widget = self.tsl.list_widget
        self.list_widget.setAcceptDrops(True)
        self.list_widget.viewport().setAcceptDrops(True)
        self.list_widget.viewport().installEventFilter(self)
        self.list_widget.setToolTip(
            "Drag folders here from File Explorer, or use Add... / Paste.")

    # ---- items

    def paths(self):
        return self.tsl.get_all_items()

    def add_paths(self, paths):
        paths = [p for p in paths if p]
        if paths:
            self.tsl.append_unique(paths)

    def clear(self):
        self.tsl.clear()

    def model(self):
        return self.list_widget.model()

    # ---- input

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, self._browse_title, self._last_dir)
        if path:
            path = os.path.normpath(path)
            self._last_dir = os.path.dirname(path) or path
            self.add_paths([path])

    def _on_paste(self):
        paths = _clipboard_paths()
        if not paths:
            self._log("[WARN] Clipboard has no existing path (one per line).")
            return
        self.add_paths(paths)

    def eventFilter(self, watched, event):
        et = event.type()
        if et in (QEvent.DragEnter, QEvent.DragMove):
            if event.mimeData() is not None and event.mimeData().hasUrls():
                event.acceptProposedAction()
                return True
        elif et == QEvent.Drop:
            paths = _dropped_paths(event)
            if paths:
                self.add_paths(paths)
                event.acceptProposedAction()
                return True
        return super().eventFilter(watched, event)


# ====================================================================== Create

class _CreateTab(QWidget):

    def __init__(self, log, on_created=None, parent=None):
        super().__init__(parent)
        self._log = log
        self._on_created = on_created
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        lists = QHBoxLayout()
        self.src_list = _PathList("Sources", self._log, "Select Source Folder")
        self.src_list.list_widget.setToolTip(
            "Original folders to link. Drag from File Explorer, Add..., or Paste.\n"
            "A junction links a folder - a file here is skipped.")
        self.tgt_list = _PathList("Create In", self._log, "Select Folder to Create Junctions In")
        self.tgt_list.list_widget.setToolTip(
            "Folders where the junctions are created (named after the source).\n"
            "n -> 1 uses the first row only; n -> n pairs rows by order.")
        lists.addWidget(self.src_list)
        lists.addWidget(self.tgt_list)
        root.addLayout(lists)

        # 모드 행
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode"))
        self.rad_n1 = QRadioButton("n -> 1")
        self.rad_n1.setToolTip("Every source gets a junction inside the first 'Create In' folder.")
        self.rad_n1.setChecked(True)
        self.rad_nn = QRadioButton("n -> n")
        self.rad_nn.setToolTip("Source row i gets its junction in 'Create In' row i.")
        mode_row.addWidget(self.rad_n1)
        mode_row.addWidget(self.rad_nn)
        self.chk_target_is_link = QCheckBox("Target row is the junction path")
        self.chk_target_is_link.setToolTip(
            "n -> n only. Each 'Create In' row is the full path of the junction itself\n"
            "(like mklink's <Link>), so you choose the name too. Its parent folder must exist.")
        self.chk_target_is_link.setEnabled(False)
        mode_row.addWidget(self.chk_target_is_link)
        mode_row.addStretch(1)
        root.addLayout(mode_row)

        # 미리보기 표
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Source", "Junction", "Status"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setToolTip("What 'Create Junctions' will do. Only 'ready' rows are made.")
        root.addWidget(self.table, stretch=1)

        btn_row = QHBoxLayout()
        self.lbl_summary = QLabel("")
        btn_row.addWidget(self.lbl_summary, stretch=1)
        self.btn_create = QPushButton("Create Junctions")
        self.btn_create.setToolTip("Run  cmd /c mklink /J <junction> <source>  for every 'ready' row.")
        self.btn_create.clicked.connect(self.on_create)
        btn_row.addWidget(self.btn_create)
        root.addLayout(btn_row)

        # 리스트·모드가 바뀌면 미리보기를 다시 만든다
        for lst in (self.src_list, self.tgt_list):
            m = lst.model()
            m.rowsInserted.connect(self._refresh)
            m.rowsRemoved.connect(self._refresh)
            m.modelReset.connect(self._refresh)
        self.rad_n1.toggled.connect(self._on_mode_changed)
        self.chk_target_is_link.toggled.connect(self._refresh)
        self._refresh()

    # ---- plan

    def _mode(self):
        return "n1" if self.rad_n1.isChecked() else "nn"

    def _on_mode_changed(self, _checked):
        nn = self._mode() == "nn"
        self.chk_target_is_link.setEnabled(nn)
        self._refresh()

    def _plan(self):
        return junction.plan(
            self.src_list.paths(), self.tgt_list.paths(), self._mode(),
            target_is_link=self._mode() == "nn" and self.chk_target_is_link.isChecked())

    def _refresh(self, *_args):
        rows = self._plan()
        self.table.setRowCount(len(rows))
        ready = 0
        ok_color = _level_color("OK")
        bad_color = _level_color("ERROR")
        for r, (src, link, status) in enumerate(rows):
            is_ready = status == junction.READY
            ready += is_ready
            for c, text in enumerate((src, link, status)):
                cell = QTableWidgetItem(text)
                cell.setToolTip(text)
                if c == 2:
                    cell.setForeground(QBrush(ok_color if is_ready else bad_color))
                self.table.setItem(r, c, cell)
        self.lbl_summary.setText(
            "{0} ready / {1} row(s)".format(ready, len(rows)) if rows else "")
        self.btn_create.setEnabled(ready > 0)

    # ---- create

    def on_create(self):
        rows = [row for row in self._plan() if row[2] == junction.READY]
        if not rows:
            self._log("[WARN] Nothing to create - no 'ready' row.")
            return
        created = []
        for src, link, _status in rows:
            ok, msg = junction.create_junction(link, src)
            if ok:
                created.append(link)
                self._log("[OK] {0}  <<===>>  {1}".format(link, src))
            else:
                self._log("[ERROR] {0}  ->  {1}".format(link, msg or "failed"))
        self._log("[INFO] Created {0} of {1} junction(s).".format(len(created), len(rows)))
        if created and callable(self._on_created):
            self._on_created(created)
        self._refresh()


# ====================================================================== Remove

class _RemoveTab(QWidget):

    COL_LINK, COL_TARGET = 0, 1

    def __init__(self, log, parent=None):
        super().__init__(parent)
        self._log = log
        self._last_dir = os.path.expanduser("~")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        group = QGroupBox("Junctions")
        g = QVBoxLayout(group)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Junction", "Target (original folder)"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setToolTip(
            "Junctions to remove. Only the link is deleted - the target folder and its\n"
            "contents stay. Rows that are not a junction are shown in red and skipped.\n"
            "Drag folders here, Add..., Paste, or Scan a folder. Double-click: open in Explorer.")
        self.table.setAcceptDrops(True)
        self.table.viewport().setAcceptDrops(True)
        self.table.viewport().installEventFilter(self)
        self.table.itemDoubleClicked.connect(
            lambda item: self._reveal(self.table.item(item.row(), self.COL_LINK).text()))
        g.addWidget(self.table, stretch=1)

        btns = QHBoxLayout()
        btn_add = QPushButton("Add...")
        btn_add.setToolTip("Pick a junction folder.")
        btn_add.clicked.connect(self._on_browse)
        btn_paste = QPushButton("Paste")
        btn_paste.setToolTip("Add the paths on the clipboard (one per line).")
        btn_paste.clicked.connect(self._on_paste)
        btn_del = QPushButton("Del")
        btn_del.setToolTip("Take the selected rows off the list (nothing on disk changes).")
        btn_del.clicked.connect(self._on_del_rows)
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(lambda: self.table.setRowCount(0))
        btn_recheck = QPushButton("Recheck")
        btn_recheck.setToolTip("Read every row again from disk.")
        btn_recheck.clicked.connect(self._recheck)
        for b in (btn_add, btn_paste, btn_del, btn_clear, btn_recheck):
            btns.addWidget(b)
        btns.addStretch(1)
        g.addLayout(btns)
        root.addWidget(group, stretch=1)

        # Scan : 폴더 안의 정션을 찾아 담는다
        scan = QGroupBox("Scan a folder for junctions")
        s = QHBoxLayout(scan)
        self.ipf_scan = QLineEdit()
        self.ipf_scan.setPlaceholderText("Folder to look in")
        self.ipf_scan.returnPressed.connect(self.on_scan)
        s.addWidget(self.ipf_scan, stretch=1)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._on_browse_scan)
        s.addWidget(btn_browse)
        self.chk_recursive = QCheckBox("Recursive")
        self.chk_recursive.setToolTip("Also look inside subfolders (not inside junctions).")
        s.addWidget(self.chk_recursive)
        btn_scan = QPushButton("Scan")
        btn_scan.clicked.connect(self.on_scan)
        s.addWidget(btn_scan)
        root.addWidget(scan)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn_remove = QPushButton("Remove Junctions")
        self.btn_remove.setToolTip(
            "Delete the listed junctions (links only). The original folders are not touched.\n"
            "Rows that are not a junction are skipped.")
        self.btn_remove.clicked.connect(self.on_remove)
        btn_row.addWidget(self.btn_remove)
        root.addLayout(btn_row)

    # ---- rows

    def links(self):
        return [self.table.item(r, self.COL_LINK).text() for r in range(self.table.rowCount())]

    def add_links(self, paths):
        """경로들을 표에 더한다(중복 제외). 정션이 아닌 것도 담되 빨갛게 표시한다."""
        known = {os.path.normcase(p) for p in self.links()}
        for path in paths:
            if not path:
                continue
            path = os.path.normpath(path)
            key = os.path.normcase(path)
            if key in known:
                self._log("{0} is already in the list.".format(path))
                continue
            known.add(key)
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, self.COL_LINK, QTableWidgetItem(path))
            self.table.setItem(r, self.COL_TARGET, QTableWidgetItem(""))
            self._fill_row(r)

    def _fill_row(self, r):
        link = self.table.item(r, self.COL_LINK).text()
        cell = self.table.item(r, self.COL_TARGET)
        if junction.is_junction(link):
            target = junction.junction_target(link)
            cell.setText(target)
            cell.setForeground(QBrush(_level_color("OK" if os.path.isdir(target) else "WARN")))
            cell.setToolTip(target if os.path.isdir(target) else "Target is not reachable (broken junction)")
        else:
            cell.setText("(not a junction)" if os.path.lexists(link) else "(does not exist)")
            cell.setForeground(QBrush(_level_color("ERROR")))
            cell.setToolTip("Not a junction - will be skipped, nothing is deleted.")
        self.table.item(r, self.COL_LINK).setToolTip(link)

    def _recheck(self):
        for r in range(self.table.rowCount()):
            self._fill_row(r)

    def _on_del_rows(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    # ---- input

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Junction", self._last_dir)
        if path:
            path = os.path.normpath(path)
            self._last_dir = os.path.dirname(path) or path
            self.add_links([path])

    def _on_paste(self):
        paths = _clipboard_paths()
        if not paths:
            self._log("[WARN] Clipboard has no existing path (one per line).")
            return
        self.add_links(paths)

    def _on_browse_scan(self):
        start = self.ipf_scan.text().strip() or self._last_dir
        path = QFileDialog.getExistingDirectory(self, "Select Folder to Scan", start)
        if path:
            self.ipf_scan.setText(os.path.normpath(path))
            self.on_scan()

    def on_scan(self):
        folder = self.ipf_scan.text().strip()
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Junction", "Select a valid folder to scan.")
            return
        found = junction.find_junctions(folder, recursive=self.chk_recursive.isChecked())
        if not found:
            self._log("[INFO] No junction in {0}".format(folder))
            return
        before = self.table.rowCount()
        self.add_links(found)
        self._log("[INFO] Scan: {0} junction(s) found, {1} added.".format(
            len(found), self.table.rowCount() - before))

    def eventFilter(self, watched, event):
        et = event.type()
        if et in (QEvent.DragEnter, QEvent.DragMove):
            if event.mimeData() is not None and event.mimeData().hasUrls():
                event.acceptProposedAction()
                return True
        elif et == QEvent.Drop:
            paths = _dropped_paths(event)
            if paths:
                self.add_links(paths)
                event.acceptProposedAction()
                return True
        return super().eventFilter(watched, event)

    def _reveal(self, path):
        if not path:
            return
        try:
            path_opener.open_path(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Junction", "Could not open path:\n{0}".format(exc))

    # ---- remove

    def on_remove(self):
        links = self.links()
        targets = [l for l in links if junction.is_junction(l)]
        if not targets:
            self._log("[WARN] Nothing to remove - no row is a junction.")
            return
        skipped = len(links) - len(targets)
        msg = ("Remove {0} junction(s)?\n\nOnly the links are deleted. The original folders "
               "and their contents are not touched.".format(len(targets)))
        if skipped:
            msg += "\n\n{0} row(s) that are not a junction will be skipped.".format(skipped)
        if QMessageBox.question(self, "Remove Junctions", msg,
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return

        removed = 0
        for r in reversed(range(self.table.rowCount())):
            link = self.table.item(r, self.COL_LINK).text()
            if not junction.is_junction(link):
                self._log("[SKIP] {0} - not a junction, left untouched".format(link))
                continue
            ok, text = junction.remove_junction(link)
            if ok:
                removed += 1
                self._log("[OK] {0} - {1}".format(link, text))
                self.table.removeRow(r)
            else:
                self._log("[ERROR] {0} - {1}".format(link, text))
        self._log("[INFO] Removed {0} of {1} junction(s).".format(removed, len(targets)))
        self._recheck()


# ====================================================================== tab

class JunctionTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)

        self.log_widget = JUN_mod_log_qt_v01(
            window_title="Path Tool - Junction Log",
            object_name="JUN_A00240_PathTool_junction_log_window")
        self.log_widget.setMaximumHeight(120)

        self.tabs = QTabWidget()
        self.remove_tab = _RemoveTab(self._log)
        self.create_tab = _CreateTab(self._log, on_created=self._on_created)
        self.tabs.addTab(self.create_tab, "Create")
        self.tabs.addTab(self.remove_tab, "Remove")
        root.addWidget(self.tabs, stretch=1)
        root.addWidget(self.log_widget)

    def _log(self, message):
        self.log_widget.log(message)

    def _on_created(self, links):
        """방금 만든 정션을 Remove 탭에 담아 둔다 - 되돌리기 쉽게."""
        self.remove_tab.add_links(links)
        self._log("[INFO] Added to the Remove tab: {0} junction(s).".format(len(links)))
