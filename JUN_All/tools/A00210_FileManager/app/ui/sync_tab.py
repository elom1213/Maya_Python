# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00210_FileManager - "Sync" tab (Qt)
#
# v01.47 : PC 간 작업 파일 동기화 추적(Sync Tracker). 계획 docs/plans/A00210_FileManager_sync_tracker_plan.md
#   - 파일 자체는 각 PC 디스크에 두고, PC 마다 '가진 파일 목록(매니페스트)' 만 데이터 저장소로 주고받는다.
#   - 하위 탭: Status(비교 표) · Roots(추적 루트 여러 개, PC 별 경로) · Excluded(루트별 제외 경로 · 무시 패턴).
#   - 공유 값(루트 · 제외 경로 · 패턴)은 <데이터 폴더>/manifests/_sync_settings.json,
#     PC 별 값(루트 실제 경로 · 이 PC 만 제외 · 화면 상태)은 A00210 프로파일(prefs).
#   - 스캔(해시)은 QThread. git Pull / Push 는 MainWindow 가 주는 콜러블로(검사 · 클론은 MainWindow 쪽).
#
# UI 문자열은 영어, 주석은 한국어.

import copy
import os
import time

from Framework.core.file_opener import open_path
from Framework.qt.MOD_treeExpand_qt_v01 import JUN_mod_treeExpand_qt_v01
from Framework.qt.MOD_viewZoom_qt_v01 import JUN_mod_viewZoom_qt_v01
from Framework.qt.qt import (
    Qt,
    QThread,
    Signal,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QProgressBar,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QListWidget,
    QPlainTextEdit,
    QAbstractItemView,
    QHeaderView,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QMenu,
    QApplication,
    QBrush,
    QColor,
    QStyle,
    QSizePolicy,
)

from ..core import sync_settings as ss
from ..core import sync_manifest as sm
from ..core import sync_compare as sc
from ..core.paths import ui_path

# 상태 글자색(어두운 · 밝은 테마 모두에서 읽히는 중간 톤)
STATUS_COLORS = {
    sc.MISSING: "#e05555",
    sc.OUTDATED: "#e0904a",
    sc.CONFLICT: "#b07ee0",
    sc.AHEAD: "#4a9be0",
    sc.ONLY_HERE: "#4a9be0",
    sc.OK: "#8a8a8a",
}
EXCLUDED_COLOR = "#707070"
STALE_HOURS = 24
SUMMARY_PC_LIMIT = 4            # PC 가 이보다 많으면 요약 열(Latest on / Missing on / Outdated on)

ROLE_REL = Qt.UserRole
ROLE_KIND = Qt.UserRole + 1     # "file" | "dir" | "excluded"
ROLE_EXCL_SCOPE = Qt.UserRole + 2   # "shared" | "local"

SHOW_KEYS = (sc.MISSING, sc.OUTDATED, sc.CONFLICT, sc.AHEAD, sc.OK)


class _ScanThread(QThread):
    """sync_manifest.scan 을 백그라운드에서. 바이트 수가 int32 를 넘으므로 object 로 보낸다."""

    progressed = Signal(object, object, str)
    finished_scan = Signal(object, object, str)     # manifest, report, error ("" = ok, "cancelled")

    def __init__(self, kwargs, parent=None):
        super().__init__(parent)
        self._kw = kwargs
        self._cancel = False
        self._last = 0.0

    def cancel(self):
        self._cancel = True

    def _progress(self, done, total, rel):
        now = time.time()
        if done >= total or now - self._last > 0.1:
            self._last = now
            self.progressed.emit(done, total, rel)

    def run(self):
        try:
            manifest, report = sm.scan(progress=self._progress, cancel=lambda: self._cancel, **self._kw)
        except sm.ScanCancelled:
            self.finished_scan.emit(None, None, "cancelled")
        except Exception as exc:  # noqa: BLE001 - 스레드 밖으로 알린다
            self.finished_scan.emit(None, None, str(exc) or exc.__class__.__name__)
        else:
            self.finished_scan.emit(manifest, report, "")


class SyncTab(QWidget):

    def __init__(self, get_data_dir, get_project_root, is_git_mode, git_pull, git_push, get_author, log):
        super().__init__()
        self._get_data_dir = get_data_dir          # () -> str  (records 와 같은 데이터 폴더)
        self._get_project_root = get_project_root  # () -> str
        self._is_git_mode = is_git_mode            # () -> bool
        self._git_pull = git_pull                  # () -> bool
        self._git_push = git_push                  # (message) -> bool
        self._get_author = get_author              # () -> str
        self._log = log

        self._pc = ss.this_pc()
        self._settings = ss.default_settings()
        self._settings_dirty = False               # 기본 루트를 메모리에만 만든 상태(아직 저장 안 함)
        self._local_paths = {}                     # {root_id: path}   - 이 PC
        self._local_excluded = {}                  # {root_id: [rel]}  - 이 PC 만
        self._root_id = ""
        self._manifests = {}
        self._rows = []
        self._thread = None
        self._push_after_scan = False

        self._build_ui()

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Root"))
        self.cmb_root = QComboBox()
        self.cmb_root.setMinimumWidth(160)
        self.cmb_root.setToolTip("Tracked root shown in the Status table.\nManage roots in the Roots tab.")
        self.cmb_root.currentIndexChanged.connect(self._on_root_changed)
        top.addWidget(self.cmb_root)
        self.lbl_root_path = QLabel("")
        self.lbl_root_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        top.addWidget(self.lbl_root_path, 1)
        top.addWidget(QLabel("This PC: <b>{0}</b>".format(self._pc)))
        root.addLayout(top)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.addTab(self._build_status_page(), "Status")
        self.sub_tabs.addTab(self._build_roots_page(), "Roots")
        self.sub_tabs.addTab(self._build_excluded_page(), "Excluded")
        root.addWidget(self.sub_tabs, 1)

    # ---------------------------------------------------------------- Status
    def _build_status_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        self.lbl_pcs = QLabel("No manifests yet.")
        # 줄바꿈 라벨은 heightForWidth 경로라 탭 높이 맞춤(tabFit)이 16px 모자랐다(v01.48) - 한 줄 + 가로 Ignored
        # (PC 가 많아 길어져도 창 폭을 밀지 않는다, 전체는 툴팁).
        self.lbl_pcs.setTextFormat(Qt.RichText)
        self.lbl_pcs.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        lay.addWidget(self.lbl_pcs)

        act = QHBoxLayout()
        self.btn_scan_push = QPushButton("Scan && Push")
        self.btn_scan_push.setToolTip(
            "Scan this PC's files under the root (hash only changed files),\n"
            "save this PC's manifest and push it (Git mode).\n"
            "In Local mode the manifest is written to the Shared Folder.")
        self.btn_scan_push.clicked.connect(lambda: self.on_scan(push=True))
        self.btn_scan = QPushButton("Scan Only")
        self.btn_scan.setToolTip("Scan and save this PC's manifest without pushing.")
        self.btn_scan.clicked.connect(lambda: self.on_scan(push=False))
        self.btn_pull = QPushButton("Pull && Compare")
        self.btn_pull.setToolTip("Pull the other PCs' manifests (Git mode) and compare.")
        self.btn_pull.clicked.connect(self.on_pull_compare)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setToolTip("Re-read manifests from the data folder and compare (no git).")
        self.btn_refresh.clicked.connect(self.on_refresh)
        for b in (self.btn_scan_push, self.btn_scan, self.btn_pull, self.btn_refresh):
            act.addWidget(b)
        act.addStretch(1)
        lay.addLayout(act)

        prog = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(True)
        self.progress.setFormat("")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.on_cancel_scan)
        prog.addWidget(self.progress, 1)
        prog.addWidget(self.btn_cancel)
        self.progress_row = QWidget()
        self.progress_row.setLayout(prog)
        self.progress_row.hide()
        lay.addWidget(self.progress_row)

        opts = QHBoxLayout()
        opts.addWidget(QLabel("Compare"))
        self.cmb_compare = QComboBox()
        self.cmb_compare.addItem("This PC", "this")
        self.cmb_compare.addItem("All PCs", "all")
        self.cmb_compare.setToolTip(
            "This PC: status of this PC's copy.\n"
            "All PCs: every file that is out of sync on any PC.")
        self.cmb_compare.currentIndexChanged.connect(self._populate_tree)
        opts.addWidget(self.cmb_compare)
        opts.addSpacing(12)
        opts.addWidget(QLabel("Show"))
        self.chk_show = {}
        labels = {sc.MISSING: "Missing", sc.OUTDATED: "Outdated", sc.CONFLICT: "Conflict",
                  sc.AHEAD: "Ahead / Only here", sc.OK: "OK"}
        for key in SHOW_KEYS:
            cb = QCheckBox(labels[key])
            cb.setChecked(key != sc.OK)
            cb.toggled.connect(self._populate_tree)
            self.chk_show[key] = cb
            opts.addWidget(cb)
        self.chk_show_excluded = QCheckBox("Excluded")
        self.chk_show_excluded.setToolTip("Show excluded paths (grey) - right-click > Include Again.")
        self.chk_show_excluded.toggled.connect(self._populate_tree)
        opts.addWidget(self.chk_show_excluded)
        opts.addStretch(1)
        lay.addLayout(opts)

        frow = QHBoxLayout()
        frow.addWidget(QLabel("Filter"))
        self.le_filter = QLineEdit()
        self.le_filter.setPlaceholderText("Type any part of a path (e.g. KANA 0080)")
        self.le_filter.setToolTip("Show only files whose path contains every word (case-insensitive).")
        self.le_filter.textChanged.connect(self._populate_tree)
        frow.addWidget(self.le_filter, 1)
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.le_filter.clear)
        frow.addWidget(btn_clear)
        lay.addLayout(frow)

        self.tree = QTreeWidget()
        JUN_mod_treeExpand_qt_v01(self.tree)  # 펼치기 = 한 단계, Shift = 아래 전부 (공용)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_menu)
        self.tree.setUniformRowHeights(True)
        self.tree.setMinimumHeight(160)
        lay.addWidget(self.tree, 1)
        self.tree_zoom = JUN_mod_viewZoom_qt_v01(self.tree, key="A00210_sync_tree")
        self._icon_dir = self.style().standardIcon(QStyle.SP_DirIcon)
        self._icon_file = self.style().standardIcon(QStyle.SP_FileIcon)

        self.lbl_summary = QLabel("")
        lay.addWidget(self.lbl_summary)

        bottom = QHBoxLayout()
        btn_copy = QPushButton("Copy Paths")
        btn_copy.setToolTip("Copy the selected files' paths (or every visible file when nothing is selected).")
        btn_copy.clicked.connect(self.on_copy_paths)
        btn_export = QPushButton("Export List...")
        btn_export.setToolTip("Save the visible files with their status to a text file.")
        btn_export.clicked.connect(self.on_export_list)
        btn_reveal = QPushButton("Reveal in Explorer")
        btn_reveal.clicked.connect(self.on_reveal)
        btn_expand = QPushButton("Expand All")
        btn_expand.clicked.connect(self.tree.expandAll)
        btn_collapse = QPushButton("Collapse All")
        btn_collapse.clicked.connect(self.tree.collapseAll)
        for b in (btn_copy, btn_export, btn_reveal):
            bottom.addWidget(b)
        bottom.addStretch(1)
        bottom.addWidget(btn_expand)
        bottom.addWidget(btn_collapse)
        lay.addLayout(bottom)
        return page

    # ---------------------------------------------------------------- Roots
    def _build_roots_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        info = QLabel(
            "A root is a folder tracked on every PC. Its path can differ per PC "
            "(Set Path on This PC). Roots and exclusions are shared through the data folder.")
        info.setWordWrap(True)
        lay.addWidget(info)

        self.tbl_roots = QTableWidget(0, 6)
        self.tbl_roots.setHorizontalHeaderLabels(
            ["Name", "Path (this PC)", "Shared Default", "Files", "Last Scan", "PCs"])
        self.tbl_roots.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_roots.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_roots.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_roots.verticalHeader().setVisible(False)
        hh = self.tbl_roots.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_roots.setMinimumHeight(110)
        self.tbl_roots.itemSelectionChanged.connect(self._on_roots_selection)
        lay.addWidget(self.tbl_roots, 1)

        grid = QGridLayout()
        self.btn_add_root = QPushButton("Add Root...")
        self.btn_add_root.clicked.connect(self.on_add_root)
        self.btn_set_path = QPushButton("Set Path on This PC...")
        self.btn_set_path.setToolTip("Use a different folder for this root on this PC only.")
        self.btn_set_path.clicked.connect(self.on_set_local_path)
        self.btn_use_default = QPushButton("Use Shared Default")
        self.btn_use_default.setToolTip("Forget this PC's own path and use the shared default path.")
        self.btn_use_default.clicked.connect(self.on_use_default_path)
        self.btn_rename_root = QPushButton("Rename...")
        self.btn_rename_root.clicked.connect(self.on_rename_root)
        self.btn_remove_root = QPushButton("Remove")
        self.btn_remove_root.clicked.connect(self.on_remove_root)
        self.chk_follow = QCheckBox("Follow junctions inside this root")
        self.chk_follow.setToolTip(
            "Off (default): junctions / symlinked folders inside the root are skipped\n"
            "(avoids loops and double tracking). The root itself may be a junction.")
        self.chk_follow.toggled.connect(self._on_follow_toggled)
        grid.addWidget(self.btn_add_root, 0, 0)
        grid.addWidget(self.btn_set_path, 0, 1)
        grid.addWidget(self.btn_use_default, 0, 2)
        grid.addWidget(self.btn_rename_root, 1, 0)
        grid.addWidget(self.btn_remove_root, 1, 1)
        grid.addWidget(self.chk_follow, 1, 2)
        lay.addLayout(grid)
        return page

    # ---------------------------------------------------------------- Excluded
    def _build_excluded_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        info = QLabel("Excluded folders skip everything below them. Applied when scanning and when comparing.")
        info.setWordWrap(True)
        lay.addWidget(info)

        lists = QHBoxLayout()
        self.lst_shared, box_shared = self._excluded_box(
            "All PCs (shared)", "shared",
            "Shared through the data folder - push to apply on the other PCs.")
        self.lst_local, box_local = self._excluded_box(
            "This PC only", "local", "Saved in this PC's profile only.")
        lists.addLayout(box_shared, 1)
        lists.addLayout(box_local, 1)
        lay.addLayout(lists, 1)

        lay.addWidget(QLabel("Ignore patterns (all roots, shared) - one glob per line, e.g. **/backup/**"))
        self.txt_ignore = QPlainTextEdit()
        self.txt_ignore.setMaximumHeight(90)
        lay.addWidget(self.txt_ignore)
        row = QHBoxLayout()
        btn_save = QPushButton("Save Patterns")
        btn_save.clicked.connect(self.on_save_patterns)
        btn_reset = QPushButton("Reset to Default")
        btn_reset.clicked.connect(self.on_reset_patterns)
        row.addWidget(btn_save)
        row.addWidget(btn_reset)
        row.addStretch(1)
        lay.addLayout(row)
        return page

    def _excluded_box(self, title, scope, tip):
        box = QVBoxLayout()
        lbl = QLabel(title)
        lbl.setToolTip(tip)
        box.addWidget(lbl)
        lst = QListWidget()
        lst.setSelectionMode(QAbstractItemView.ExtendedSelection)
        lst.setToolTip(tip)
        lst.setMinimumHeight(90)
        box.addWidget(lst, 1)
        row = QHBoxLayout()
        b_dir = QPushButton("Add Folder...")
        b_dir.clicked.connect(lambda: self.on_add_excluded(scope, is_dir=True))
        b_file = QPushButton("Add File...")
        b_file.clicked.connect(lambda: self.on_add_excluded(scope, is_dir=False))
        b_rm = QPushButton("Remove")
        b_rm.clicked.connect(lambda: self.on_remove_excluded(scope))
        row.addWidget(b_dir)
        row.addWidget(b_file)
        row.addWidget(b_rm)
        box.addLayout(row)
        return lst, box

    # ============================================================== prefs (PC 별)

    def load_prefs(self, prefs):
        prefs = prefs or {}
        self._local_paths = {k: ui_path(v) for k, v in dict(prefs.get("sync_root_paths") or {}).items() if v}
        self._local_excluded = copy.deepcopy(dict(prefs.get("sync_local_excluded") or {}))
        self._root_id = prefs.get("sync_root") or ""
        idx = self.cmb_compare.findData(prefs.get("sync_compare") or "this")
        self.cmb_compare.blockSignals(True)
        self.cmb_compare.setCurrentIndex(max(idx, 0))
        self.cmb_compare.blockSignals(False)
        show = prefs.get("sync_show")
        if isinstance(show, list):
            for key, cb in self.chk_show.items():
                cb.blockSignals(True)
                cb.setChecked(key in show)
                cb.blockSignals(False)
        self.on_refresh(quiet=True)

    def prefs_values(self):
        return {
            "sync_root_paths": dict(self._local_paths),
            "sync_local_excluded": copy.deepcopy(self._local_excluded),
            "sync_root": self._root_id,
            "sync_compare": self.cmb_compare.currentData() or "this",
            "sync_show": [k for k, cb in self.chk_show.items() if cb.isChecked()],
        }

    # ============================================================== settings / roots

    def _data_dir(self):
        return self._get_data_dir() or ""

    def _load_settings(self):
        self._settings = ss.load_settings(self._data_dir())
        self._settings_dirty = False
        if not self._settings["roots"]:
            # 처음: Project Root 를 첫 루트로 제안(저장은 처음 스캔하거나 편집할 때).
            project_root = ui_path(self._get_project_root() or "")
            if project_root:
                self._settings["roots"].append(
                    ss.new_root(os.path.basename(project_root.rstrip("/")) or "Project", project_root))
                self._settings_dirty = True

    def _save_settings(self):
        data_dir = self._data_dir()
        if not data_dir:
            QMessageBox.warning(self, "Sync", "Set the data folder first (File Manager > Settings).")
            return False
        try:
            ss.save_settings(data_dir, self._settings)
        except (OSError, ValueError) as exc:
            self._log("Sync: failed to save settings: {0}".format(exc))
            return False
        self._settings_dirty = False
        return True

    def _current_root(self):
        return ss.find_root(self._settings, self._root_id)

    def _root_abs(self, root=None):
        root = root or self._current_root()
        return ss.root_path(root, self._local_paths)

    def _excluded_for(self, root=None):
        root = root or self._current_root()
        if not root:
            return []
        return list(root.get("excluded_paths") or []) + list(self._local_excluded.get(root["id"], []))

    def _refresh_root_combo(self):
        roots = self._settings["roots"]
        ids = [r["id"] for r in roots]
        if self._root_id not in ids:
            self._root_id = ids[0] if ids else ""
        self.cmb_root.blockSignals(True)
        self.cmb_root.clear()
        for r in roots:
            self.cmb_root.addItem(r["name"], r["id"])
        idx = self.cmb_root.findData(self._root_id)
        self.cmb_root.setCurrentIndex(max(idx, 0))
        self.cmb_root.blockSignals(False)
        self._update_root_label()

    def _update_root_label(self):
        path = self._root_abs()
        if not self._current_root():
            self.lbl_root_path.setText("(no root - add one in the Roots tab)")
        elif not path:
            self.lbl_root_path.setText("(path not set on this PC)")
        elif not os.path.isdir(path):
            self.lbl_root_path.setText("{0}  (not found on this PC)".format(path))
        else:
            self.lbl_root_path.setText(path)

    def _on_root_changed(self, _index=None):
        self._root_id = self.cmb_root.currentData() or ""
        self._update_root_label()
        self._load_manifests()
        self._refresh_excluded_lists()
        self._select_root_row()
        self._compare()

    # ============================================================== refresh / compare

    def on_refresh(self, quiet=False):
        """데이터 폴더에서 설정 · 매니페스트를 다시 읽어 비교(프로파일 · 데이터 폴더가 바뀌어도 이것)."""
        self._load_settings()
        self._refresh_root_combo()
        self._refresh_roots_table()
        self._refresh_excluded_lists()
        self.txt_ignore.setPlainText("\n".join(self._settings.get("ignore_patterns") or []))
        self._load_manifests()
        self._compare()
        if not quiet:
            self._log("Sync: compared {0} PC(s) for root '{1}'.".format(
                len(self._manifests), self._root_name()))

    def _root_name(self):
        r = self._current_root()
        return r["name"] if r else "-"

    def _load_manifests(self):
        data_dir = self._data_dir()
        self._manifests = sm.load_root_manifests(data_dir, self._root_id) if (data_dir and self._root_id) else {}

    def _compare(self):
        root = self._current_root()
        ignore = self._settings.get("ignore_patterns") or []
        self._rows = sc.compare(self._manifests, self._pc, self._excluded_for(root), ignore) if root else []
        self._update_pcs_label()
        self._populate_tree()

    def _pcs(self):
        """열 순서: 이 PC 먼저, 나머지 이름순. 이 PC 매니페스트가 없어도 열은 만든다."""
        pcs = sorted(self._manifests.keys(), key=lambda p: (p != self._pc, p.lower()))
        if self._pc not in pcs:
            pcs.insert(0, self._pc)
        return pcs

    def _update_pcs_label(self):
        if not self._current_root():
            self.lbl_pcs.setText("No tracked root. Add one in the Roots tab.")
            return
        parts = []
        now = time.time()
        for pc in self._pcs():
            m = self._manifests.get(pc)
            name = "{0} (this PC)".format(pc) if pc == self._pc else pc
            if not m:
                parts.append("<span style='color:{0}'>● {1}: not scanned</span>".format(STATUS_COLORS[sc.MISSING], name))
                continue
            epoch = m.get("scanned_epoch") or 0
            stale = epoch and (now - epoch) > STALE_HOURS * 3600
            color = STATUS_COLORS[sc.OUTDATED] if stale else "#5fae5f"
            age = _age_text(now - epoch) if epoch else "?"
            parts.append("<span style='color:{0}'>● {1}: scanned {2} ({3}){4}</span>".format(
                color, name, (m.get("scanned_at") or "")[5:16], age, " ⚠ stale" if stale else ""))
        self.lbl_pcs.setText("PCs: " + " &nbsp; ".join(parts))
        self.lbl_pcs.setToolTip("<br>".join(parts))

    # ============================================================== tree

    def _visible_rows(self):
        mode = self.cmb_compare.currentData() or "this"
        show = set(k for k, cb in self.chk_show.items() if cb.isChecked())
        if sc.AHEAD in show:
            show.add(sc.ONLY_HERE)
        words = [w for w in self.le_filter.text().lower().split() if w]
        out = []
        for r in self._rows:
            low = r.rel.lower()
            if words and not all(w in low for w in words):
                continue
            if mode == "all":
                if r.is_problem():
                    if not (set(r.pc_status.values()) & show):
                        continue
                elif sc.OK not in show:
                    continue
            elif r.status not in show:
                continue
            out.append(r)
        return out

    def _summary_mode(self):
        return len(self._pcs()) > SUMMARY_PC_LIMIT

    def _populate_tree(self, *_args):
        pcs = self._pcs()
        summary = self._summary_mode()
        if summary:
            headers = ["Path", "This PC", "Latest on", "Missing on", "Outdated on", "Status"]
        else:
            headers = ["Path"] + ["{0} (this PC)".format(p) if p == self._pc else p for p in pcs] + ["Status"]
        self.tree.clear()
        self.tree.setColumnCount(len(headers))
        self.tree.setHeaderLabels(headers)
        status_col = len(headers) - 1

        rows = self._visible_rows()
        folders = {}

        def folder_item(path):
            if not path:
                return None
            it = folders.get(path.lower())
            if it is not None:
                return it
            parent_path, _, name = path.rpartition("/")
            parent = folder_item(parent_path)
            it = QTreeWidgetItem([name])
            it.setIcon(0, self._icon_dir)
            it.setData(0, ROLE_REL, path + "/")
            it.setData(0, ROLE_KIND, "dir")
            it.setData(0, Qt.UserRole + 3, {})       # 하위 상태 개수
            (parent.addChild(it) if parent else self.tree.addTopLevelItem(it))
            folders[path.lower()] = it
            return it

        mode = self.cmb_compare.currentData() or "this"
        for r in rows:
            parent_path, _, name = r.rel.rpartition("/")
            parent = folder_item(parent_path)
            it = QTreeWidgetItem([name])
            it.setIcon(0, self._icon_file)
            it.setData(0, ROLE_REL, r.rel)
            it.setData(0, ROLE_KIND, "file")
            it.setToolTip(0, r.rel)
            if summary:
                self._fill_summary_cells(it, r)
            else:
                for col, pc in enumerate(pcs, start=1):
                    self._fill_pc_cell(it, col, r, pc)
            text, color = self._status_text(r, mode)
            it.setText(status_col, text)
            it.setForeground(status_col, QBrush(QColor(color)))
            (parent.addChild(it) if parent else self.tree.addTopLevelItem(it))
            # 폴더 뱃지용 개수
            key = r.status if mode == "this" else ("Out of sync" if r.is_problem() else sc.OK)
            p = parent
            while p is not None:
                counts = p.data(0, Qt.UserRole + 3) or {}
                counts[key] = counts.get(key, 0) + 1
                p.setData(0, Qt.UserRole + 3, counts)
                p = p.parent()

        for it in folders.values():
            counts = it.data(0, Qt.UserRole + 3) or {}
            order = [sc.MISSING, sc.OUTDATED, sc.CONFLICT, "Out of sync", sc.AHEAD, sc.ONLY_HERE]
            parts = ["{0} {1}".format(counts[k], k) for k in order if counts.get(k)]
            it.setText(status_col, " · ".join(parts))
            worst = next((k for k in order if counts.get(k)), sc.OK)
            it.setForeground(status_col, QBrush(QColor(STATUS_COLORS.get(worst, STATUS_COLORS[sc.MISSING]))))

        if self.chk_show_excluded.isChecked():
            self._add_excluded_items(folder_item)

        if len(rows) <= 500:
            self.tree.expandAll()
        else:
            for i in range(self.tree.topLevelItemCount()):
                self.tree.topLevelItem(i).setExpanded(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        for c in range(len(headers)):
            self.tree.resizeColumnToContents(c)
        self._update_summary(rows)

    def _add_excluded_items(self, folder_item):
        root = self._current_root()
        if not root:
            return
        items = [(e, "shared") for e in root.get("excluded_paths") or []]
        items += [(e, "local") for e in self._local_excluded.get(root["id"], [])]
        for rel, scope in items:
            is_dir = rel.endswith("/")
            parent_path, _, name = rel.rstrip("/").rpartition("/")
            parent = folder_item(parent_path)
            label = "{0}  (excluded{1})".format(name, "" if scope == "shared" else ", this PC")
            it = QTreeWidgetItem([label])
            it.setIcon(0, self._icon_dir if is_dir else self._icon_file)
            it.setForeground(0, QBrush(QColor(EXCLUDED_COLOR)))
            it.setData(0, ROLE_REL, rel)
            it.setData(0, ROLE_KIND, "excluded")
            it.setData(0, ROLE_EXCL_SCOPE, scope)
            it.setToolTip(0, "Excluded {0}: {1}".format("on all PCs" if scope == "shared" else "on this PC", rel))
            (parent.addChild(it) if parent else self.tree.addTopLevelItem(it))

    def _fill_pc_cell(self, it, col, row, pc):
        e = row.entries.get(pc)
        st = row.pc_status.get(pc, sc.MISSING) if pc in self._manifests else None
        if e:
            text = (e.get("mtime") or "")[5:16] or "?"
            tip = "{0}\nsize {1:,} bytes\nsha256 {2}\nmodified {3}".format(
                pc, e.get("size") or 0, (e.get("sha256") or "")[:16], e.get("mtime") or "?")
        else:
            text = "—"
            tip = "{0}: no file".format(pc) if pc in self._manifests else "{0}: not scanned".format(pc)
        if st:
            mark = "?" if row.uncertain.get(pc) else ""
            tip += "\nstatus: {0}{1}".format(st, mark)
            it.setForeground(col, QBrush(QColor(STATUS_COLORS.get(st, "#888"))))
        it.setText(col, text)
        it.setToolTip(col, tip)

    def _fill_summary_cells(self, it, row):
        e = row.entries.get(self._pc)
        it.setText(1, (e.get("mtime") or "")[5:16] if e else "—")
        it.setText(2, ", ".join(row.latest_on()))
        it.setText(3, ", ".join(row.pcs_with(sc.MISSING)))
        it.setText(4, ", ".join(row.pcs_with(sc.OUTDATED)))
        it.setForeground(3, QBrush(QColor(STATUS_COLORS[sc.MISSING])))
        it.setForeground(4, QBrush(QColor(STATUS_COLORS[sc.OUTDATED])))

    def _status_text(self, row, mode):
        if mode == "all" and row.is_problem():
            parts = []
            for st in (sc.MISSING, sc.OUTDATED, sc.CONFLICT):
                pcs = row.pcs_with(st)
                if pcs:
                    parts.append("{0}: {1}".format(st, ", ".join(pcs)))
            if not parts:
                parts.append("Send from: " + ", ".join(row.latest_on()))
            worst = next((s for s in (sc.MISSING, sc.OUTDATED, sc.CONFLICT) if row.pcs_with(s)), sc.AHEAD)
            return " · ".join(parts), STATUS_COLORS[worst]
        st = row.status
        text = st + ("?" if row.uncertain.get(self._pc) else "")
        if st in (sc.MISSING, sc.OUTDATED):
            src = row.latest_on() or [p for p in row.entries if p != self._pc]
            if src:
                text += "  (get from {0})".format(", ".join(src))
        elif st == sc.AHEAD:
            need = [p for p in row.pc_status if p != self._pc and row.pc_status[p] in (sc.MISSING, sc.OUTDATED)]
            if need:
                text += "  (send to {0})".format(", ".join(need))
        return text, STATUS_COLORS.get(st, "#888")

    def _update_summary(self, visible):
        if not self._current_root():
            self.lbl_summary.setText("")
            return
        cnt = sc.summarize(self._rows, self._pc if self._pc in self._manifests else None)
        if self._pc not in self._manifests:
            self.lbl_summary.setText(
                "This PC has not scanned this root yet - press Scan & Push.  ({0} files on other PCs)".format(len(self._rows)))
            return
        self.lbl_summary.setText(
            "This PC: Missing {0} · Outdated {1} · Conflict {2} · Ahead {3} · Only here {4} · OK {5}   "
            "(showing {6} of {7})".format(
                cnt[sc.MISSING], cnt[sc.OUTDATED], cnt[sc.CONFLICT], cnt[sc.AHEAD], cnt[sc.ONLY_HERE], cnt[sc.OK],
                len(visible), len(self._rows)))

    # ============================================================== scan

    def _busy(self, on):
        for b in (self.btn_scan_push, self.btn_scan, self.btn_pull, self.btn_refresh, self.cmb_root):
            b.setEnabled(not on)
        self.progress_row.setVisible(on)

    def on_scan(self, push=True):
        if self._thread is not None:
            return
        root = self._current_root()
        if not root:
            QMessageBox.warning(self, "Sync", "No tracked root. Add one in the Roots tab.")
            return
        path = self._root_abs(root)
        if not path or not os.path.isdir(path):
            QMessageBox.warning(self, "Sync", "Root folder not found on this PC:\n{0}\n\n"
                                "Use Roots > Set Path on This PC.".format(path or "(not set)"))
            return
        if self._settings_dirty and not self._save_settings():
            return
        data_dir = self._data_dir()
        if not data_dir:
            QMessageBox.warning(self, "Sync", "Set the data folder first (File Manager > Settings).")
            return
        prev = sm.load_manifest(sm.manifest_path(data_dir, root["id"], self._pc))
        kw = dict(root_abs=path, root_id=root["id"], pc=self._pc, user=self._get_author() or "",
                  excluded=self._excluded_for(root), ignore=self._settings.get("ignore_patterns") or [],
                  prev=prev, follow_junctions=bool(root.get("follow_junctions")))
        self._push_after_scan = push
        self._scan_root_id = root["id"]
        self._scan_started = time.time()
        self.progress.setValue(0)
        self.progress.setFormat("Listing files...")
        self._busy(True)
        self._log("Sync: scanning '{0}' ({1}) ...".format(root["name"], path))
        self._thread = _ScanThread(kw, self)
        self._thread.progressed.connect(self._on_scan_progress)
        self._thread.finished_scan.connect(self._on_scan_finished)
        self._thread.start()

    def on_cancel_scan(self):
        if self._thread is not None:
            self._thread.cancel()

    def _on_scan_progress(self, done, total, rel):
        frac = (float(done) / total) if total else 1.0
        self.progress.setValue(int(frac * 1000))
        self.progress.setFormat("Hashing {0:.0f}%  {1:.1f} / {2:.1f} MB  {3}".format(
            frac * 100, done / 1048576.0, total / 1048576.0, rel.rpartition("/")[2]))

    def _on_scan_finished(self, manifest, report, error):
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.wait(2000)
        self._busy(False)
        if error == "cancelled":
            self._log("Sync: scan cancelled - manifest not changed.")
            return
        if error:
            self._log("Sync: scan failed: {0}".format(error))
            return
        try:
            path = sm.save_manifest(self._data_dir(), manifest)
        except (OSError, ValueError) as exc:
            self._log("Sync: failed to save manifest: {0}".format(exc))
            return
        self._log("Sync: {0} files ({1} hashed, {2} unchanged) in {3:.1f}s -> {4}".format(
            report["files"], report["hashed"], report["reused"], time.time() - self._scan_started, ui_path(path)))
        if report["busy"]:
            self._log("Sync: changed while scanning (kept previous state, scan again later): " + ", ".join(report["busy"][:10]))
        for err in report["errors"][:10]:
            self._log("Sync: [WARN] " + err)
        if self._push_after_scan:
            if self._is_git_mode():
                author = self._get_author() or self._pc
                msg = "Update sync manifest by {0} on {1} ({2}) [{3}]".format(
                    author, self._pc, time.strftime("%Y-%m-%d %H:%M:%S"), self._scan_root_id)
                self._git_push(msg)
            else:
                self._log("Sync: Local mode - manifest written to the Shared Folder (no push).")
        if self._scan_root_id == self._root_id:
            self._load_manifests()
            self._compare()
        self._refresh_roots_table()

    def on_pull_compare(self):
        if self._is_git_mode():
            if not self._git_pull():
                self._log("Sync: pull failed - comparing with the manifests already here.")
        self.on_refresh()

    # ============================================================== tree actions

    def _selected_items(self):
        return self.tree.selectedItems()

    def _file_items(self, items=None):
        """선택(없으면 보이는 전부)의 파일 항목. 폴더를 고르면 그 아래 파일 전부."""
        out = []

        def walk(it):
            kind = it.data(0, ROLE_KIND)
            if kind == "file":
                out.append(it)
            elif kind == "dir":
                for i in range(it.childCount()):
                    walk(it.child(i))

        if items is None:
            items = self._selected_items() or [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
        for it in items:
            walk(it)
        seen, uniq = set(), []
        for it in out:
            rel = it.data(0, ROLE_REL)
            if rel not in seen:
                seen.add(rel)
                uniq.append(it)
        return uniq

    def _row_by_rel(self):
        return {r.rel: r for r in self._rows}

    def on_copy_paths(self):
        rels = [it.data(0, ROLE_REL) for it in self._file_items()]
        QApplication.clipboard().setText("\n".join(rels))
        self._log("Sync: copied {0} path(s).".format(len(rels)))

    def on_export_list(self):
        items = self._file_items([self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())])
        if not items:
            self._log("Sync: nothing to export.")
            return
        default = os.path.join(os.path.expanduser("~"), "Desktop",
                               "sync_{0}_{1}_{2}.txt".format(self._root_id, self._pc, time.strftime("%Y%m%d_%H%M")))
        path, _ = QFileDialog.getSaveFileName(self, "Export List", default, "Text (*.txt)")
        if not path:
            return
        rows = self._row_by_rel()
        lines = ["# root: {0} ({1})  this PC: {2}  {3}".format(
            self._root_name(), self._root_abs(), self._pc, time.strftime("%Y-%m-%d %H:%M:%S")),
            "# status\tpath\tdetails"]
        mode = self.cmb_compare.currentData() or "this"
        for it in items:
            r = rows.get(it.data(0, ROLE_REL))
            if r is None:
                continue
            text, _ = self._status_text(r, mode)
            lines.append("{0}\t{1}\t{2}".format(r.status, r.rel, text))
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        self._log("Sync: exported {0} file(s) -> {1}".format(len(lines) - 2, ui_path(path)))

    def on_reveal(self):
        items = self._selected_items()
        if not items:
            return
        base = self._root_abs()
        rel = items[0].data(0, ROLE_REL) or ""
        path = os.path.join(base, *rel.rstrip("/").split("/"))
        while path and not os.path.exists(path) and os.path.dirname(path) != path:
            path = os.path.dirname(path)      # 이 PC 에 없는 파일이면 있는 가장 가까운 폴더
        if not path or not os.path.exists(path):
            self._log("Sync: not found on this PC: {0}".format(rel))
            return
        try:
            open_path(path)
        except (OSError, ValueError) as exc:
            self._log("Sync: failed to open File Explorer: {0}".format(exc))

    def _on_tree_menu(self, pos):
        it = self.tree.itemAt(pos)
        if it is None:
            return
        if not it.isSelected():
            self.tree.clearSelection()
            it.setSelected(True)
        kind = it.data(0, ROLE_KIND)
        menu = QMenu(self)
        if kind == "excluded":
            act = menu.addAction("Include Again")
            act.triggered.connect(lambda: self._include_again(
                [(i.data(0, ROLE_REL), i.data(0, ROLE_EXCL_SCOPE)) for i in self._selected_items()
                 if i.data(0, ROLE_KIND) == "excluded"]))
        else:
            rels = [i.data(0, ROLE_REL) for i in self._selected_items() if i.data(0, ROLE_KIND) in ("file", "dir")]
            a1 = menu.addAction("Exclude from Sync (All PCs)")
            a1.triggered.connect(lambda: self._exclude(rels, "shared"))
            a2 = menu.addAction("Exclude on This PC Only")
            a2.triggered.connect(lambda: self._exclude(rels, "local"))
            menu.addSeparator()
            a3 = menu.addAction("Copy Paths")
            a3.triggered.connect(self.on_copy_paths)
            a4 = menu.addAction("Reveal in Explorer")
            a4.triggered.connect(self.on_reveal)
        run = getattr(menu, "exec_", None) or getattr(menu, "exec")
        run(self.tree.viewport().mapToGlobal(pos))

    # ============================================================== exclude

    def _exclude(self, rels, scope):
        root = self._current_root()
        if not root or not rels:
            return
        target = root.setdefault("excluded_paths", []) if scope == "shared" \
            else self._local_excluded.setdefault(root["id"], [])
        added = []
        for rel in rels:
            n = ss.norm_rel(rel)
            if n and n not in target and not ss.is_excluded(n, target):
                target.append(n)
                added.append(n)
        if not added:
            return
        if (scope == "shared" or self._settings_dirty) and not self._save_settings():
            return
        self._log("Sync: excluded ({0}): {1}{2}".format(
            "all PCs - push to share" if scope == "shared" else "this PC", ", ".join(added[:5]),
            " ..." if len(added) > 5 else ""))
        self._refresh_excluded_lists()
        self._compare()

    def _include_again(self, pairs):
        root = self._current_root()
        if not root or not pairs:
            return
        changed_shared = False
        for rel, scope in pairs:
            lst = root.get("excluded_paths", []) if scope == "shared" else self._local_excluded.get(root["id"], [])
            if rel in lst:
                lst.remove(rel)
                changed_shared = changed_shared or scope == "shared"
        if changed_shared and not self._save_settings():
            return
        self._log("Sync: included again: {0} - scan to track them.".format(", ".join(p[0] for p in pairs)))
        self._refresh_excluded_lists()
        self._compare()

    def _refresh_excluded_lists(self):
        root = self._current_root()
        self.lst_shared.clear()
        self.lst_local.clear()
        if not root:
            return
        self.lst_shared.addItems(root.get("excluded_paths") or [])
        self.lst_local.addItems(self._local_excluded.get(root["id"], []))

    def on_add_excluded(self, scope, is_dir=True):
        root = self._current_root()
        base = self._root_abs(root)
        if not root or not base or not os.path.isdir(base):
            QMessageBox.warning(self, "Sync", "The root folder is not available on this PC.")
            return
        if is_dir:
            chosen = QFileDialog.getExistingDirectory(self, "Exclude Folder", base)
            chosen = [chosen] if chosen else []
        else:
            chosen, _ = QFileDialog.getOpenFileNames(self, "Exclude Files", base)
        rels = []
        for c in chosen:
            rel = ss.rel_of(base, c)
            if rel is None:
                QMessageBox.warning(self, "Sync", "Outside the root:\n{0}".format(ui_path(c)))
                continue
            rels.append(ss.norm_rel(rel, is_dir=is_dir))
        self._exclude(rels, scope)

    def on_remove_excluded(self, scope):
        lst = self.lst_shared if scope == "shared" else self.lst_local
        rels = [i.text() for i in lst.selectedItems()]
        self._include_again([(r, scope) for r in rels])

    def on_save_patterns(self):
        pats = [l.strip() for l in self.txt_ignore.toPlainText().splitlines() if l.strip()]
        self._settings["ignore_patterns"] = pats
        if self._save_settings():
            self._log("Sync: saved {0} ignore pattern(s) - push to share.".format(len(pats)))
            self._compare()

    def on_reset_patterns(self):
        self.txt_ignore.setPlainText("\n".join(ss.DEFAULT_IGNORE))
        self.on_save_patterns()

    # ============================================================== roots page

    def _refresh_roots_table(self):
        roots = self._settings["roots"]
        data_dir = self._data_dir()
        self.tbl_roots.blockSignals(True)
        self.tbl_roots.setRowCount(len(roots))
        for row, r in enumerate(roots):
            path = self._root_abs(r)
            mans = sm.load_root_manifests(data_dir, r["id"]) if data_dir else {}
            mine = mans.get(self._pc) or {}
            local = r["id"] in self._local_paths
            cells = [
                r["name"],
                (path or "(not set)") + ("" if os.path.isdir(path or "") else "  (not found)") + ("  [this PC]" if local else ""),
                r.get("default_path") or "",
                str(len(mine.get("files") or {})) if mine else "-",
                (mine.get("scanned_at") or "-")[5:16] if mine else "-",
                str(len(mans)),
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, r["id"])
                self.tbl_roots.setItem(row, col, item)
        self.tbl_roots.blockSignals(False)
        self._select_root_row()

    def _select_root_row(self):
        for row in range(self.tbl_roots.rowCount()):
            it = self.tbl_roots.item(row, 0)
            if it and it.data(Qt.UserRole) == self._root_id:
                self.tbl_roots.blockSignals(True)
                self.tbl_roots.selectRow(row)
                self.tbl_roots.blockSignals(False)
                break
        root = self._current_root()
        self.chk_follow.blockSignals(True)
        self.chk_follow.setChecked(bool(root and root.get("follow_junctions")))
        self.chk_follow.setEnabled(root is not None)
        self.chk_follow.blockSignals(False)

    def _on_roots_selection(self):
        items = self.tbl_roots.selectedItems()
        if not items:
            return
        rid = items[0].data(Qt.UserRole)
        if rid and rid != self._root_id:
            idx = self.cmb_root.findData(rid)
            if idx >= 0:
                self.cmb_root.setCurrentIndex(idx)

    def on_add_root(self):
        start = self._root_abs() or self._get_project_root() or ""
        path = QFileDialog.getExistingDirectory(self, "Add Root", start)
        if not path:
            return
        path = ui_path(path)
        name, ok = QInputDialog.getText(self, "Add Root", "Root name:", text=os.path.basename(path.rstrip("/")))
        if not ok or not name.strip():
            return
        for r in self._settings["roots"]:
            other = self._root_abs(r)
            rel = ss.overlap(path, other)
            if rel == "same":
                QMessageBox.warning(self, "Add Root", "Already tracked as '{0}'.".format(r["name"]))
                return
            if rel == "inside":
                inner = ss.rel_of(other, path)
                ans = QMessageBox.question(
                    self, "Add Root",
                    "This folder is inside root '{0}'.\nExclude it from '{0}' so it is not tracked twice?".format(r["name"]))
                if ans == QMessageBox.Yes and inner:
                    r.setdefault("excluded_paths", []).append(ss.norm_rel(inner, is_dir=True))
        new = ss.new_root(name.strip(), path, [r["id"] for r in self._settings["roots"]])
        for r in self._settings["roots"]:
            other = self._root_abs(r)
            if ss.overlap(path, other) == "contains":
                inner = ss.rel_of(path, other)
                ans = QMessageBox.question(
                    self, "Add Root",
                    "Root '{0}' is inside this folder.\nExclude it from the new root so it is not tracked twice?".format(r["name"]))
                if ans == QMessageBox.Yes and inner:
                    new["excluded_paths"].append(ss.norm_rel(inner, is_dir=True))
        self._settings["roots"].append(new)
        if not self._save_settings():
            self._settings["roots"].remove(new)
            return
        self._root_id = new["id"]
        self._log("Sync: added root '{0}' ({1}) - push to share it with the other PCs.".format(new["name"], path))
        self.on_refresh(quiet=True)

    def on_set_local_path(self):
        root = self._current_root()
        if not root:
            return
        path = QFileDialog.getExistingDirectory(self, "Path on This PC - " + root["name"], self._root_abs(root))
        if not path:
            return
        self._local_paths[root["id"]] = ui_path(path)
        if self._settings_dirty:
            self._save_settings()
        self._log("Sync: root '{0}' on this PC = {1}".format(root["name"], ui_path(path)))
        self._update_root_label()
        self._refresh_roots_table()

    def on_use_default_path(self):
        root = self._current_root()
        if not root or root["id"] not in self._local_paths:
            return
        self._local_paths.pop(root["id"], None)
        self._log("Sync: root '{0}' on this PC = shared default {1}".format(root["name"], root.get("default_path")))
        self._update_root_label()
        self._refresh_roots_table()

    def on_rename_root(self):
        root = self._current_root()
        if not root:
            return
        name, ok = QInputDialog.getText(self, "Rename Root", "Root name:", text=root["name"])
        if not ok or not name.strip():
            return
        root["name"] = name.strip()      # id(폴더 이름)는 그대로 - 매니페스트 경로가 바뀌지 않게
        if self._save_settings():
            self.on_refresh(quiet=True)

    def on_remove_root(self):
        root = self._current_root()
        if not root:
            return
        ans = QMessageBox.question(
            self, "Remove Root",
            "Stop tracking '{0}' on every PC?\n\nThe files are not touched. "
            "Saved manifests stay in the data folder (manifests/{1}/).".format(root["name"], root["id"]))
        if ans != QMessageBox.Yes:
            return
        self._settings["roots"] = [r for r in self._settings["roots"] if r["id"] != root["id"]]
        if self._save_settings():
            self._local_paths.pop(root["id"], None)
            self._local_excluded.pop(root["id"], None)
            self._root_id = ""
            self._log("Sync: removed root '{0}' - push to share.".format(root["name"]))
            self.on_refresh(quiet=True)

    def _on_follow_toggled(self, on):
        root = self._current_root()
        if not root:
            return
        root["follow_junctions"] = bool(on)
        if self._save_settings():
            self._log("Sync: '{0}' follow junctions = {1} (applies from the next scan).".format(root["name"], bool(on)))

    # ============================================================== close

    def shutdown(self):
        """창을 닫을 때 - 스캔 중이면 멈추고 기다린다."""
        if self._thread is not None:
            self._thread.cancel()
            self._thread.wait(5000)


def _age_text(seconds):
    seconds = max(0, int(seconds))
    if seconds < 3600:
        return "{0} min ago".format(seconds // 60)
    if seconds < 86400:
        return "{0} h ago".format(seconds // 3600)
    return "{0} days ago".format(seconds // 86400)
