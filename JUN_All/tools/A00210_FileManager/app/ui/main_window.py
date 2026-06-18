# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - main window (Qt, standalone)
#
# Maya 씬 파일(.mb/.ma)의 작업 기록을 관리한다.
#  - 경로 지정 → 파일 목록
#  - 파일별 작업자 / 작업 기록(log) 보기·편집
#  - 화면 영역 캡쳐로 썸네일 저장
#  - 기록(records/thumbs)을 git 으로 pull/push (원본 mb/ma 는 push 대상 아님)

import os
import time

from Framework.qt.qt import (
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QSplitter,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QPixmap,
    Qt,
)

from ..config.version import VERSION, LAST_UPDATE
from ..config import data_repo
from ..core import scanner, prefs as prefs_mod
from ..core.store import MetaStore, OutsideProjectRootError
from ..core.git_sync import GitSync
from ..core.models import FileRecord, LogEntry
from .file_table import FileTable
from .region_capture import RegionCapture
from .path_structure_tab import PathStructureTab
from .lineage_tab import LineageTab


THUMB_W = 320
THUMB_H = 180


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"JUN File Manager  v{VERSION}")
        self.resize(1080, 680)

        self._prefs = prefs_mod.load()

        self._current_entry = None      # 선택된 파일 entry dict
        self._current_record = None     # 편집 중인 FileRecord
        self._capture = None            # RegionCapture 참조 유지용

        self._build_ui()
        self._load_prefs_to_ui()

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)

        # 로그 위젯은 탭 밖(하단)에 두어 모든 탭에서 보이게 한다.
        # 새 탭이 self.log 를 캡처하므로 탭보다 먼저 생성한다.
        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(120)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_file_manager_tab(), "File Manager")

        self.path_structure_tab = PathStructureTab(
            get_store=self._make_store,
            get_project_root=self.get_project_root,
            get_store_dir=self.get_store_dir,
            log=self.log,
        )
        self.tabs.addTab(self.path_structure_tab, "Path Structure")

        self.lineage_tab = LineageTab(
            get_store=self._make_store,
            get_project_root=self.get_project_root,
            get_store_dir=self.get_store_dir,
            log=self.log,
        )
        self.tabs.addTab(self.lineage_tab, "Lineage")

        root.addWidget(self.tabs, stretch=1)
        root.addWidget(self.log_widget)

    def _build_file_manager_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(self._build_settings_group())

        splitter = QSplitter(Qt.Horizontal)
        self.file_table = FileTable()
        self.file_table.file_selected.connect(self._on_file_selected)
        splitter.addWidget(self.file_table)
        splitter.addWidget(self._build_detail_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, stretch=1)

        layout.addWidget(self._build_git_group())

        return page

    def _build_settings_group(self):
        group = QGroupBox("Settings")
        grid = QGridLayout(group)

        # Project Root
        self.ipf_project_root = QLineEdit()
        btn_root = QPushButton("Browse...")
        btn_root.clicked.connect(lambda: self._browse_dir(self.ipf_project_root))
        grid.addWidget(QLabel("Project Root"), 0, 0)
        grid.addWidget(self.ipf_project_root, 0, 1)
        grid.addWidget(btn_root, 0, 2)

        # Store Repo
        self.ipf_store_dir = QLineEdit()
        btn_store = QPushButton("Browse...")
        btn_store.clicked.connect(lambda: self._browse_dir(self.ipf_store_dir))
        grid.addWidget(QLabel("Store Repo"), 1, 0)
        grid.addWidget(self.ipf_store_dir, 1, 1)
        grid.addWidget(btn_store, 1, 2)

        # Scan Dir + Scan
        self.ipf_scan_dir = QLineEdit()
        btn_scan_browse = QPushButton("Browse...")
        btn_scan_browse.clicked.connect(lambda: self._browse_dir(self.ipf_scan_dir))
        grid.addWidget(QLabel("Scan Dir"), 2, 0)
        grid.addWidget(self.ipf_scan_dir, 2, 1)
        grid.addWidget(btn_scan_browse, 2, 2)

        scan_row = QHBoxLayout()
        self.chk_recursive = QCheckBox("Recursive")
        btn_scan = QPushButton("Scan")
        btn_scan.clicked.connect(self.on_scan)
        scan_row.addWidget(self.chk_recursive)
        scan_row.addStretch(1)
        scan_row.addWidget(btn_scan)
        grid.addLayout(scan_row, 3, 1, 1, 2)

        # Remote / Branch / Author / Save settings
        meta_row = QHBoxLayout()
        self.ipf_remote = QLineEdit()
        self.ipf_remote.setFixedWidth(120)
        self.ipf_branch = QLineEdit()
        self.ipf_branch.setFixedWidth(120)
        self.ipf_author = QLineEdit()
        btn_save_settings = QPushButton("Save Settings")
        btn_save_settings.clicked.connect(self.on_save_settings)
        meta_row.addWidget(QLabel("Remote"))
        meta_row.addWidget(self.ipf_remote)
        meta_row.addWidget(QLabel("Branch"))
        meta_row.addWidget(self.ipf_branch)
        meta_row.addWidget(QLabel("Author"))
        meta_row.addWidget(self.ipf_author)
        meta_row.addWidget(btn_save_settings)
        grid.addLayout(meta_row, 4, 0, 1, 3)

        # Remote URL (중앙 데이터 리포 git URL). 보통 번들 기본값 그대로 — 첫 Pull 시
        # Store Repo 가 비어 있으면 이 URL 을 기본 경로로 자동 clone 한다.
        self.ipf_remote_url = QLineEdit()
        self.ipf_remote_url.setPlaceholderText("data repo git URL (auto-clone on first Pull)")
        grid.addWidget(QLabel("Remote URL"), 5, 0)
        grid.addWidget(self.ipf_remote_url, 5, 1, 1, 2)

        return group

    def _build_detail_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_file)

        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(THUMB_W, THUMB_H)
        self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setStyleSheet("border: 1px solid #555;")
        self.lbl_thumb.setText("No thumbnail")
        layout.addWidget(self.lbl_thumb, alignment=Qt.AlignHCenter)

        thumb_btns = QHBoxLayout()
        self.btn_capture = QPushButton("Capture Region")
        self.btn_capture.clicked.connect(self.on_capture_region)
        self.btn_load_image = QPushButton("Load Image...")
        self.btn_load_image.clicked.connect(self.on_load_image)
        thumb_btns.addWidget(self.btn_capture)
        thumb_btns.addWidget(self.btn_load_image)
        layout.addLayout(thumb_btns)

        layout.addWidget(QLabel("Author"))
        self.ipf_record_author = QLineEdit()
        layout.addWidget(self.ipf_record_author)

        layout.addWidget(QLabel("Log history"))
        self.txt_log_history = QPlainTextEdit()
        self.txt_log_history.setReadOnly(True)
        layout.addWidget(self.txt_log_history, stretch=1)

        layout.addWidget(QLabel("New note"))
        self.txt_new_note = QPlainTextEdit()
        self.txt_new_note.setMaximumHeight(60)
        layout.addWidget(self.txt_new_note)

        record_btns = QHBoxLayout()
        self.btn_add_log = QPushButton("Add Log Entry")
        self.btn_add_log.clicked.connect(self.on_add_log)
        self.btn_save_record = QPushButton("Save Record")
        self.btn_save_record.clicked.connect(self.on_save_record)
        record_btns.addWidget(self.btn_add_log)
        record_btns.addWidget(self.btn_save_record)
        layout.addLayout(record_btns)

        self._set_detail_enabled(False)

        return panel

    def _build_git_group(self):
        group = QGroupBox("Git Sync  (records / thumbnails only — originals are never pushed)")
        row = QHBoxLayout(group)

        btn_pull = QPushButton("Pull")
        btn_pull.clicked.connect(self.on_pull)
        btn_push = QPushButton("Push")
        btn_push.clicked.connect(self.on_push)

        self.lbl_git_status = QLabel("")

        row.addWidget(btn_pull)
        row.addWidget(btn_push)
        row.addWidget(self.lbl_git_status, stretch=1)

        return group

    # ============================================================== prefs

    def _load_prefs_to_ui(self):
        self.ipf_project_root.setText(self._prefs.get("project_root", ""))
        self.ipf_store_dir.setText(self._prefs.get("store_dir", ""))
        self.ipf_scan_dir.setText(self._prefs.get("scan_dir", ""))
        self.ipf_remote.setText(self._prefs.get("remote", data_repo.DATA_REPO_REMOTE))
        self.ipf_branch.setText(self._prefs.get("branch", data_repo.DATA_REPO_BRANCH))
        self.ipf_remote_url.setText(self._prefs.get("remote_url", data_repo.DATA_REPO_URL))
        self.ipf_author.setText(self._prefs.get("author", ""))
        self.chk_recursive.setChecked(bool(self._prefs.get("recursive", False)))

    def _collect_prefs(self):
        return {
            "project_root": self.ipf_project_root.text().strip(),
            "store_dir": self.ipf_store_dir.text().strip(),
            "scan_dir": self.ipf_scan_dir.text().strip(),
            "remote": self.ipf_remote.text().strip() or data_repo.DATA_REPO_REMOTE,
            "branch": self.ipf_branch.text().strip() or data_repo.DATA_REPO_BRANCH,
            "remote_url": self.ipf_remote_url.text().strip(),
            "author": self.ipf_author.text().strip(),
            "recursive": self.chk_recursive.isChecked(),
        }

    def on_save_settings(self):
        self._prefs = self._collect_prefs()
        path = prefs_mod.save(self._prefs)
        self.log(f"Settings saved: {path}")

    # ============================================================ helpers

    def get_project_root(self):
        return self.ipf_project_root.text().strip()

    def get_store_dir(self):
        return self.ipf_store_dir.text().strip()

    def _make_store(self):
        return MetaStore(
            self.ipf_store_dir.text().strip(),
            self.ipf_project_root.text().strip(),
        )

    def _make_git(self):
        return GitSync(
            self.ipf_store_dir.text().strip(),
            self.ipf_remote.text().strip() or data_repo.DATA_REPO_REMOTE,
            self.ipf_branch.text().strip() or data_repo.DATA_REPO_BRANCH,
        )

    def _ensure_default_store_dir(self):
        """Store Repo 가 비어 있으면 번들 기본 경로로 채운다(배포 사용자 원클릭 Pull)."""
        if not self.ipf_store_dir.text().strip():
            self.ipf_store_dir.setText(data_repo.DEFAULT_STORE_DIR)

    def _browse_dir(self, line_edit):
        start = line_edit.text().strip() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Directory", start)
        if path:
            line_edit.setText(path)

    def _set_detail_enabled(self, enabled):
        for w in (
            self.btn_capture,
            self.btn_load_image,
            self.ipf_record_author,
            self.txt_new_note,
            self.btn_add_log,
            self.btn_save_record,
        ):
            w.setEnabled(enabled)

    def log(self, message):
        self.log_widget.appendPlainText(str(message))

    @staticmethod
    def _now_iso():
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ============================================================== scan

    def on_scan(self):
        store = self._make_store()
        scan_dir = self.ipf_scan_dir.text().strip()

        if not scan_dir or not os.path.isdir(scan_dir):
            QMessageBox.warning(self, "Scan", "Please select a valid Scan Dir.")
            return

        if not store.project_root:
            QMessageBox.warning(self, "Scan", "Please set Project Root first.")
            return

        entries = scanner.scan(
            scan_dir,
            store,
            recursive=self.chk_recursive.isChecked(),
        )
        self.file_table.set_entries(entries)
        self.log(f"Scanned {len(entries)} Maya file(s) in {scan_dir}")

    # ===================================================== file selection

    def _on_file_selected(self, entry):
        self._current_entry = entry
        self._current_record = None

        if entry is None:
            self.lbl_file.setText("No file selected")
            self._clear_detail()
            self._set_detail_enabled(False)
            return

        self.lbl_file.setText(entry["file_name"])

        if not entry.get("in_root", True):
            self._clear_detail()
            self._set_detail_enabled(False)
            self.lbl_thumb.setText("File is outside project root")
            return

        store = self._make_store()
        key = entry["key"]

        record = store.load(key)
        if record is None:
            record = FileRecord(
                key=key,
                file_name=entry["file_name"],
                author=self.ipf_author.text().strip(),
            )

        self._current_record = record
        self._populate_detail(record, store)
        self._set_detail_enabled(True)

    def _populate_detail(self, record, store):
        self.ipf_record_author.setText(record.author)
        self.txt_new_note.clear()
        self._refresh_log_history(record)
        self._refresh_thumb(record, store)

    def _refresh_log_history(self, record):
        lines = []
        for entry in record.logs:
            lines.append(f"[{entry.timestamp}] {entry.author}")
            lines.append(entry.note)
            lines.append("")
        self.txt_log_history.setPlainText("\n".join(lines).strip())

    def _refresh_thumb(self, record, store):
        thumb_path = store.thumb_abs(record.key)
        if os.path.isfile(thumb_path):
            pix = QPixmap(thumb_path).scaled(
                THUMB_W,
                THUMB_H,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.lbl_thumb.setPixmap(pix)
        else:
            self.lbl_thumb.setText("No thumbnail")

    def _clear_detail(self):
        self.ipf_record_author.clear()
        self.txt_log_history.clear()
        self.txt_new_note.clear()
        self.lbl_thumb.clear()
        self.lbl_thumb.setText("No thumbnail")

    # ============================================================ thumbnail

    def on_capture_region(self):
        if not self._require_record():
            return

        self._capture = RegionCapture()
        self._capture.captured.connect(self._on_thumb_captured)
        self._capture.cancelled.connect(lambda: self.log("Capture cancelled."))
        self._capture.show()

    def _on_thumb_captured(self, tmp_path):
        try:
            self._apply_thumb(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    def on_load_image(self):
        if not self._require_record():
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            os.path.expanduser("~"),
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if path:
            self._apply_thumb(path)

    def _apply_thumb(self, src_path):
        store = self._make_store()
        record = self._current_record

        thumb_rel = store.save_thumb(record.key, src_path)
        record.thumb_rel = thumb_rel

        # 썸네일은 곧바로 기록에 반영해 저장한다.
        self._stamp_and_save(record, store)
        self._refresh_thumb(record, store)
        self._refresh_table_row()
        self.log(f"Thumbnail saved: {thumb_rel}")

    # =============================================================== record

    def on_add_log(self):
        if not self._require_record():
            return

        note = self.txt_new_note.toPlainText().strip()
        if not note:
            QMessageBox.information(self, "Add Log", "Please write a note first.")
            return

        author = self.ipf_record_author.text().strip() or self.ipf_author.text().strip()
        self._current_record.logs.append(
            LogEntry(timestamp=self._now_iso(), author=author, note=note)
        )
        self.txt_new_note.clear()
        self._refresh_log_history(self._current_record)
        self.log("Log entry added (remember to Save Record).")

    def on_save_record(self):
        if not self._require_record():
            return

        store = self._make_store()
        record = self._current_record
        record.author = self.ipf_record_author.text().strip()
        self._stamp_and_save(record, store)
        self._refresh_table_row()
        self.log(f"Record saved: {record.key}")

    def _stamp_and_save(self, record, store):
        record.updated_by = self.ipf_author.text().strip()
        record.updated_at = self._now_iso()
        store.save(record)

    def _require_record(self):
        if self._current_record is None:
            QMessageBox.warning(self, "File Manager", "Select a file (inside project root) first.")
            return False
        return True

    def _refresh_table_row(self):
        # 간단하게 전체 재스캔으로 상태(작업자/썸네일) 갱신.
        self.on_scan()

    # ================================================================ git

    def on_pull(self):
        self._ensure_default_store_dir()
        git = self._make_git()
        if not git.store_dir:
            QMessageBox.warning(self, "Git", "Set Store Repo first.")
            return

        if not git.is_repo():
            # repo 가 없으면 Remote URL 로 자동 clone(빈 기본 경로에 받아온다).
            ok, out = git.ensure_repo(self.ipf_remote_url.text().strip())
            self.log(out)
            if not ok:
                self.lbl_git_status.setText("Clone failed")
                return

        ok, out = git.pull()
        self.log(out)
        self.lbl_git_status.setText("Pull OK" if ok else "Pull failed")
        if ok:
            self.on_scan()

    def on_push(self):
        self._ensure_default_store_dir()
        git = self._make_git()
        if not git.store_dir:
            QMessageBox.warning(self, "Git", "Set Store Repo first.")
            return

        if not git.is_repo():
            ok, out = git.ensure_repo(self.ipf_remote_url.text().strip())
            self.log(out)
            if not ok:
                self.lbl_git_status.setText("Clone failed")
                return

        author = self.ipf_author.text().strip() or "unknown"
        message = f"Update records by {author} ({self._now_iso()})"

        ok, out = git.push(message)
        self.log(out)
        self.lbl_git_status.setText("Push OK" if ok else "Push failed")
