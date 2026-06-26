# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00210_FileManager - main window (Qt, standalone)
#
# Maya 씬 파일(.mb/.ma)의 작업 기록을 관리한다.
#  - 경로 지정 → 파일 목록
#  - 파일별 작업자 / 작업 기록(log) 보기·편집
#  - 화면 영역 캡쳐로 썸네일 저장
#  - 기록(records/thumbs)을 git 으로 pull/push (원본 mb/ma 는 push 대상 아님)

import os
import time

from Framework.core.file_opener import open_path
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
    QComboBox,
    QPushButton,
    QCheckBox,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QScrollArea,
    QToolButton,
    QMenu,
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


class _BranchComboBox(QComboBox):
    """Branch 입력 콤보. 드롭다운을 열 때마다 현재 git 브랜치 목록으로 갱신한다.

    editable 이라 목록에 없는 브랜치를 직접 타이핑할 수도 있다(기존 동작 유지).
    fetch_branches 는 브랜치 이름 list 를 돌려주는 콜러블(보통 store repo 의 GitSync).
    """

    def __init__(self, fetch_branches, parent=None):
        super().__init__(parent)
        self._fetch = fetch_branches
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMinimumWidth(120)

    def showPopup(self):
        current = self.currentText()
        names = []
        try:
            names = self._fetch() or []
        except Exception:  # noqa: BLE001 - 목록 조회 실패해도 드롭다운은 떠야 한다
            names = []

        self.blockSignals(True)
        self.clear()
        self.addItems(names)
        # 현재 입력값이 목록에 없으면 맨 위에 추가해 보존.
        if current and current not in names:
            self.insertItem(0, current)
        self.setCurrentText(current)
        self.blockSignals(False)

        super().showPopup()


class _CheckableMenu(QMenu):
    """체크 가능한 항목을 토글해도 닫히지 않는 메뉴.

    기본 QMenu 는 항목 클릭 시 닫히므로 여러 확장자를 연속으로 체크/해제하기 불편하다.
    체크 가능한 항목 위에서 마우스를 떼면 닫지 않고 그 항목만 토글(trigger)한다.
    """

    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action is not None and action.isEnabled() and action.isCheckable():
            action.trigger()   # 체크 토글 + triggered(bool) 방출, 메뉴는 유지
            return
        super().mouseReleaseEvent(event)


class LogEditDialog(QDialog):
    """Log history 의 각 항목(작업자/메모)을 편집하거나 삭제하는 다이얼로그.

    timestamp 는 보존(읽기 전용 라벨), author/note 만 편집한다. 항목별 Delete 로 제거.
    OK 시 남은 항목을 화면 순서대로 LogEntry 리스트(result_logs)로 돌려준다.
    자유 텍스트 재파싱 대신 구조적으로 편집해 timestamp/구분이 깨지지 않게 한다.
    """

    def __init__(self, logs, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Log History")
        self.resize(640, 520)

        self._rows = []   # [{"timestamp", "author"(QLineEdit), "note"(QPlainTextEdit), "widget"}]

        outer = QVBoxLayout(self)
        outer.addWidget(QLabel(
            "Edit or delete past log entries. Timestamps are kept.\n"
            "Press OK, then Save Record to persist the changes."
        ))

        # 항목이 많아도 보이도록 스크롤 영역에 항목 박스를 쌓는다.
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        host = QWidget()
        self._vbox = QVBoxLayout(host)
        self._vbox.addStretch(1)         # 항목은 이 stretch 앞에 끼워 넣는다
        self._scroll.setWidget(host)
        outer.addWidget(self._scroll, stretch=1)

        for entry in logs:
            self._add_row(entry)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _add_row(self, entry):
        box = QGroupBox()
        v = QVBoxLayout(box)

        head = QHBoxLayout()
        head.addWidget(QLabel(f"[{entry.timestamp}]"))
        author_edit = QLineEdit(entry.author)
        author_edit.setPlaceholderText("author")
        author_edit.setFixedWidth(160)
        head.addWidget(author_edit)
        head.addStretch(1)
        btn_del = QPushButton("Delete")
        head.addWidget(btn_del)
        v.addLayout(head)

        note_edit = QPlainTextEdit(entry.note)
        note_edit.setMaximumHeight(80)
        v.addWidget(note_edit)

        row = {
            "timestamp": entry.timestamp,
            "author": author_edit,
            "note": note_edit,
            "widget": box,
        }
        # 끝의 stretch 앞에 삽입(추가 순서 = 표시 순서 유지).
        self._vbox.insertWidget(self._vbox.count() - 1, box)
        self._rows.append(row)
        btn_del.clicked.connect(lambda: self._remove_row(row))

    def _remove_row(self, row):
        row["widget"].setParent(None)
        row["widget"].deleteLater()
        self._rows.remove(row)

    def result_logs(self):
        """현재 남아있는 항목들을 화면 순서대로 LogEntry 리스트로 반환."""
        return [
            LogEntry(
                timestamp=r["timestamp"],
                author=r["author"].text().strip(),
                note=r["note"].toPlainText().strip(),
            )
            for r in self._rows
        ]


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"JUN File Manager  v{VERSION}")
        self.resize(1080, 680)

        # 활성 프로파일을 읽어 시작(집/회사 등 환경별 세팅 묶음 = JSON 1개).
        self._profile = prefs_mod.get_active()
        self._prefs = prefs_mod.load_profile(self._profile)

        self._current_entry = None      # 선택된 파일 entry dict
        self._current_record = None     # 편집 중인 FileRecord
        self._capture = None            # RegionCapture 참조 유지용
        self._scanned_entries = []      # 마지막 scan 결과 원본(필터 전). "Show Recorded
                                        # Only"·확장자 필터 토글 시 재스캔 없이 거르기 위함.
        self._type_states = {}          # 확장자(ext, 점 없음) -> 체크 여부. 재스캔 간 유지.
        self._type_actions = {}         # 확장자 -> File Types 메뉴의 QAction
        self._name_filter = ""          # 적용 중인 이름(제목) 키워드. 빈 값=전체.

        self._build_ui()
        self._load_prefs_to_ui()
        self._refresh_profiles()

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

        # Source Mode 콤보는 settings·git 그룹이 모두 만들어진 지금 연결한다
        # (빌드 중 addItem 으로 신호가 먼저 튀어 아직 없는 git 위젯을 건드리지 않도록).
        self.cmb_source_mode.currentIndexChanged.connect(self._on_source_mode_changed)

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

        layout.addWidget(self._build_profile_group())
        layout.addWidget(self._build_settings_group())

        # 파일 목록 위 이름 필터 바 — 스캔된 파일 중 제목에 키워드가 든 것만 표시.
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Name filter"))
        self.ipf_name_filter = QLineEdit()
        self.ipf_name_filter.setPlaceholderText(
            "Name contains...  (empty = all files)")
        self.ipf_name_filter.returnPressed.connect(self.on_apply_name_filter)
        self.btn_name_filter = QPushButton("Filter")
        self.btn_name_filter.setToolTip(
            "Show only files whose name contains the keyword (empty = all).")
        self.btn_name_filter.clicked.connect(self.on_apply_name_filter)
        filter_row.addWidget(self.ipf_name_filter, stretch=1)
        filter_row.addWidget(self.btn_name_filter)
        layout.addLayout(filter_row)

        splitter = QSplitter(Qt.Horizontal)
        self.file_table = FileTable()
        self.file_table.file_selected.connect(self._on_file_selected)
        self.file_table.reveal_requested.connect(self.on_reveal_in_explorer)
        splitter.addWidget(self.file_table)
        splitter.addWidget(self._build_detail_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, stretch=1)

        layout.addWidget(self._build_git_group())

        return page

    def _build_profile_group(self):
        """세팅 묶음을 이름붙여 저장/전환하는 Profile 그룹(콤보 + New/Rename/Delete)."""
        group = QGroupBox("Profile")
        row = QHBoxLayout(group)

        self.cmb_profile = QComboBox()
        self.cmb_profile.setToolTip(
            "Active settings profile (each is its own JSON in ~/.jun_filemanager/profiles).\n"
            "Switching loads that profile's Project Root / Store Repo / Scan Dir / etc.")
        self.cmb_profile.currentTextChanged.connect(self.on_profile_changed)

        btn_new = QPushButton("New")
        btn_new.setToolTip("Create a new profile from the current settings")
        btn_new.clicked.connect(self.on_new_profile)
        btn_rename = QPushButton("Rename")
        btn_rename.setToolTip("Rename the current profile")
        btn_rename.clicked.connect(self.on_rename_profile)
        btn_delete = QPushButton("Delete")
        btn_delete.setToolTip("Delete the current profile")
        btn_delete.clicked.connect(self.on_delete_profile)

        row.addWidget(QLabel("Profile"))
        row.addWidget(self.cmb_profile, stretch=1)
        row.addWidget(btn_new)
        row.addWidget(btn_rename)
        row.addWidget(btn_delete)

        return group

    def _build_settings_group(self):
        group = QGroupBox("Settings")
        grid = QGridLayout(group)

        # Source Mode — records/thumbnails 를 어디서 읽고 쓰는지 선택한다.
        #   git   : 중앙 git 데이터 리포(Pull/Push) — 기존 동작.
        #   local : 공유/NAS 폴더를 git 없이 직접 사용(폴더 동기화는 NAS 가 담당).
        self.cmb_source_mode = QComboBox()
        self.cmb_source_mode.addItem("Remote (Git)", "git")
        self.cmb_source_mode.addItem("Local (Shared / NAS)", "local")
        self.cmb_source_mode.setToolTip(
            "Where records/thumbnails are read from and written to.\n"
            "Remote (Git): sync a central git data-repo via Pull / Push.\n"
            "Local (Shared / NAS): use a shared folder directly — no git;\n"
            "the NAS keeps it in sync across the team.")
        grid.addWidget(QLabel("Source Mode"), 0, 0)
        grid.addWidget(self.cmb_source_mode, 0, 1)

        # Project Root
        self.ipf_project_root = QLineEdit()
        btn_root = QPushButton("Browse...")
        btn_root.clicked.connect(lambda: self._browse_dir(self.ipf_project_root))
        grid.addWidget(QLabel("Project Root"), 1, 0)
        grid.addWidget(self.ipf_project_root, 1, 1)
        grid.addWidget(btn_root, 1, 2)

        # Store Repo (git 모드 전용 — 중앙 데이터 리포의 로컬 clone)
        self.lbl_store = QLabel("Store Repo")
        self.ipf_store_dir = QLineEdit()
        self.btn_store = QPushButton("Browse...")
        self.btn_store.clicked.connect(lambda: self._browse_dir(self.ipf_store_dir))
        grid.addWidget(self.lbl_store, 2, 0)
        grid.addWidget(self.ipf_store_dir, 2, 1)
        grid.addWidget(self.btn_store, 2, 2)

        # Shared Folder (local 모드 전용 — NAS 등 공유 폴더를 git 없이 직접 읽고 쓴다)
        self.lbl_local = QLabel("Shared Folder")
        self.ipf_local_dir = QLineEdit()
        self.ipf_local_dir.setPlaceholderText(
            "local / NAS folder used directly (no git)")
        self.btn_local = QPushButton("Browse...")
        self.btn_local.clicked.connect(lambda: self._browse_dir(self.ipf_local_dir))
        grid.addWidget(self.lbl_local, 3, 0)
        grid.addWidget(self.ipf_local_dir, 3, 1)
        grid.addWidget(self.btn_local, 3, 2)

        # Scan Dir + Scan
        self.ipf_scan_dir = QLineEdit()
        btn_scan_browse = QPushButton("Browse...")
        btn_scan_browse.clicked.connect(lambda: self._browse_dir(self.ipf_scan_dir))
        grid.addWidget(QLabel("Scan Dir"), 4, 0)
        grid.addWidget(self.ipf_scan_dir, 4, 1)
        grid.addWidget(btn_scan_browse, 4, 2)

        scan_row = QHBoxLayout()
        self.chk_recursive = QCheckBox("Recursive")
        # 이 툴로 기록(Save Record)한 파일만 목록에 남긴다. Recursive 스캔에서 수많은
        # 파일이 잡힐 때 '관리 중인 파일'만 추리는 용도. 재스캔 없이 즉시 재필터.
        self.chk_recorded_only = QCheckBox("Show Recorded Only")
        self.chk_recorded_only.setToolTip(
            "List only files that have a saved record (created via Save Record).")
        self.chk_recorded_only.stateChanged.connect(self._apply_file_filter)
        # 스캔된 파일들에서 발견된 확장자 중 어떤 것만 표시할지 고르는 체크 드롭다운.
        # 메뉴는 scan 때마다 발견 확장자로 다시 채워진다(_rebuild_type_menu).
        self.btn_file_types = QToolButton()
        self.btn_file_types.setText("File Types")
        self.btn_file_types.setToolTip(
            "Choose which file extensions to list (populated after Scan).")
        self.btn_file_types.setPopupMode(QToolButton.InstantPopup)
        self._types_menu = _CheckableMenu(self.btn_file_types)
        self.btn_file_types.setMenu(self._types_menu)
        btn_scan = QPushButton("Scan")
        btn_scan.clicked.connect(self.on_scan)
        scan_row.addWidget(self.chk_recursive)
        scan_row.addWidget(self.chk_recorded_only)
        scan_row.addWidget(self.btn_file_types)
        scan_row.addStretch(1)
        scan_row.addWidget(btn_scan)
        grid.addLayout(scan_row, 5, 1, 1, 2)

        # Remote / Branch / Author / Save settings
        meta_row = QHBoxLayout()
        self.ipf_remote = QLineEdit()
        self.ipf_remote.setFixedWidth(120)
        # Branch: 드롭다운에서 현재 브랜치 중 고르거나 직접 입력(editable).
        self.ipf_branch = _BranchComboBox(self._branch_names)
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
        grid.addLayout(meta_row, 6, 0, 1, 3)

        # Remote URL (중앙 데이터 리포 git URL). 보통 번들 기본값 그대로 — 첫 Pull 시
        # Store Repo 가 비어 있으면 이 URL 을 기본 경로로 자동 clone 한다.
        self.ipf_remote_url = QLineEdit()
        self.ipf_remote_url.setPlaceholderText("data repo git URL (auto-clone on first Pull)")
        grid.addWidget(QLabel("Remote URL"), 7, 0)
        grid.addWidget(self.ipf_remote_url, 7, 1, 1, 2)

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

        # Log history 헤더 + Expand 버튼(좁은 패널에서 긴 로그를 큰 창으로 보기).
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Log history"))
        log_header.addStretch(1)
        self.btn_edit_log = QPushButton("Edit")
        self.btn_edit_log.setToolTip("Edit or delete past log entries")
        self.btn_edit_log.clicked.connect(self.on_edit_log)
        log_header.addWidget(self.btn_edit_log)
        self.btn_expand_log = QPushButton("Expand")
        self.btn_expand_log.setToolTip("Open the log history in a larger window")
        self.btn_expand_log.clicked.connect(self.on_expand_log)
        log_header.addWidget(self.btn_expand_log)
        layout.addLayout(log_header)

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
        self.git_group = QGroupBox(
            "Git Sync  (records / thumbnails only — originals are never pushed)")
        row = QHBoxLayout(self.git_group)

        self.btn_pull = QPushButton("Pull")
        self.btn_pull.clicked.connect(self.on_pull)
        self.btn_push = QPushButton("Push")
        self.btn_push.clicked.connect(self.on_push)

        self.lbl_git_status = QLabel("")

        row.addWidget(self.btn_pull)
        row.addWidget(self.btn_push)
        row.addWidget(self.lbl_git_status, stretch=1)

        return self.git_group

    # ============================================================== prefs

    def _load_prefs_to_ui(self):
        self.ipf_project_root.setText(self._prefs.get("project_root", ""))
        self.ipf_store_dir.setText(self._prefs.get("store_dir", ""))
        self.ipf_local_dir.setText(self._prefs.get("local_dir", ""))
        self.ipf_scan_dir.setText(self._prefs.get("scan_dir", ""))
        self.ipf_remote.setText(self._prefs.get("remote", data_repo.DATA_REPO_REMOTE))
        self.ipf_branch.setCurrentText(self._prefs.get("branch", data_repo.DATA_REPO_BRANCH))
        self.ipf_remote_url.setText(self._prefs.get("remote_url", data_repo.DATA_REPO_URL))
        self.ipf_author.setText(self._prefs.get("author", ""))
        self.chk_recursive.setChecked(bool(self._prefs.get("recursive", False)))
        self.chk_recorded_only.setChecked(
            bool(self._prefs.get("show_recorded_only", False)))

        # Source Mode: 콤보 값 복원 후 git/local 위젯 활성 상태를 갱신한다.
        mode = self._prefs.get("source_mode", "git")
        idx = self.cmb_source_mode.findData(mode)
        self.cmb_source_mode.blockSignals(True)
        self.cmb_source_mode.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_source_mode.blockSignals(False)
        self._apply_source_mode(self.cmb_source_mode.currentData())

    def _collect_prefs(self):
        return {
            "project_root": self.ipf_project_root.text().strip(),
            "source_mode": self.cmb_source_mode.currentData() or "git",
            "store_dir": self.ipf_store_dir.text().strip(),
            "local_dir": self.ipf_local_dir.text().strip(),
            "scan_dir": self.ipf_scan_dir.text().strip(),
            "remote": self.ipf_remote.text().strip() or data_repo.DATA_REPO_REMOTE,
            "branch": self.ipf_branch.currentText().strip() or data_repo.DATA_REPO_BRANCH,
            "remote_url": self.ipf_remote_url.text().strip(),
            "author": self.ipf_author.text().strip(),
            "recursive": self.chk_recursive.isChecked(),
            "show_recorded_only": self.chk_recorded_only.isChecked(),
        }

    def on_save_settings(self):
        self._prefs = self._collect_prefs()
        path = prefs_mod.save_profile(self._profile, self._prefs)
        self.log(f"Settings saved to profile '{self._profile}': {path}")

    def _save_current_to_active(self):
        """현재 UI 값을 활성 프로파일에 silent 저장(전환/종료 시 편집 유실 방지)."""
        self._prefs = self._collect_prefs()
        prefs_mod.save_profile(self._profile, self._prefs)

    # ============================================================ profiles

    def _refresh_profiles(self):
        """프로파일 콤보를 현재 목록으로 갱신하고 활성 프로파일을 선택한다."""
        self.cmb_profile.blockSignals(True)
        self.cmb_profile.clear()
        self.cmb_profile.addItems(prefs_mod.list_profiles())
        idx = self.cmb_profile.findText(self._profile)
        if idx >= 0:
            self.cmb_profile.setCurrentIndex(idx)
        self.cmb_profile.blockSignals(False)

    def on_profile_changed(self, name):
        """콤보에서 다른 프로파일 선택 → 현재 값 자동저장 후 새 프로파일 로드."""
        if not name or name == self._profile:
            return
        # 1) 떠나는 프로파일에 현재 UI 값을 자동 저장(유실 방지).
        self._save_current_to_active()
        # 2) 새 프로파일을 활성화하고 UI 에 로드.
        self._profile = name
        prefs_mod.set_active(name)
        self._prefs = prefs_mod.load_profile(name)
        self._load_prefs_to_ui()
        # 3) Store Repo 가 바뀌었으니 다른 탭의 저장 목록도 새 기준으로 새로고침.
        self._refresh_other_tabs()
        self.log(f"Switched to profile '{name}'.")

    def on_new_profile(self):
        raw, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if not ok:
            return
        name = prefs_mod.sanitize_name(raw)
        if not name:
            QMessageBox.warning(self, "Profile", "Enter a valid profile name.")
            return
        if name in prefs_mod.list_profiles():
            QMessageBox.warning(self, "Profile", f"Profile '{name}' already exists.")
            return
        # 떠나는 프로파일을 저장한 뒤, 현재 세팅을 그대로 담은 새 프로파일을 만든다.
        self._save_current_to_active()
        self._profile = name
        prefs_mod.set_active(name)
        prefs_mod.save_profile(name, self._collect_prefs())
        self._refresh_profiles()
        self.log(f"Created profile '{name}' (copied current settings).")

    def on_rename_profile(self):
        old = self._profile
        raw, ok = QInputDialog.getText(self, "Rename Profile", "New name:", text=old)
        if not ok:
            return
        new = prefs_mod.sanitize_name(raw)
        if not new or new == old:
            return
        if new in prefs_mod.list_profiles():
            QMessageBox.warning(self, "Profile", f"Profile '{new}' already exists.")
            return
        self._save_current_to_active()
        prefs_mod.rename_profile(old, new)
        self._profile = new
        self._refresh_profiles()
        self.log(f"Renamed profile '{old}' -> '{new}'.")

    def on_delete_profile(self):
        name = self._profile
        if len(prefs_mod.list_profiles()) <= 1:
            QMessageBox.warning(self, "Profile", "At least one profile must remain.")
            return
        ok = QMessageBox.question(
            self, "Profile", f"Delete profile '{name}'?")
        if ok != QMessageBox.Yes:
            return
        prefs_mod.delete_profile(name)
        remaining = prefs_mod.list_profiles()
        self._profile = remaining[0]
        prefs_mod.set_active(self._profile)
        self._prefs = prefs_mod.load_profile(self._profile)
        self._refresh_profiles()
        self._load_prefs_to_ui()
        self._refresh_other_tabs()
        self.log(f"Deleted profile '{name}'. Active is now '{self._profile}'.")

    def _refresh_other_tabs(self):
        """프로파일 전환으로 Store Repo 가 바뀌면 Lineage/Path Structure 목록을 갱신."""
        try:
            self.lineage_tab.on_refresh()
            self.path_structure_tab.on_refresh()
        except Exception as exc:  # noqa: BLE001 - 갱신 실패가 전환을 막지 않게
            self.log(f"Tab refresh skipped: {exc}")

    def closeEvent(self, event):
        # 창을 닫을 때 현재 UI 값을 활성 프로파일에 저장(다음 실행에 복원).
        try:
            self._save_current_to_active()
        except Exception:  # noqa: BLE001
            pass
        super().closeEvent(event)

    # ============================================================ helpers

    def get_project_root(self):
        return self.ipf_project_root.text().strip()

    def _effective_store_dir(self):
        """현재 Source Mode 에 따른 실제 데이터 폴더(records/thumbs 의 부모).

        git 모드면 Store Repo(로컬 clone), local 모드면 Shared Folder(NAS 등)를 쓴다.
        store/탭이 모두 이 경로를 통해 읽고 쓰므로 모드 전환이 자동으로 반영된다.
        """
        if self.cmb_source_mode.currentData() == "local":
            return self.ipf_local_dir.text().strip()
        return self.ipf_store_dir.text().strip()

    def get_store_dir(self):
        return self._effective_store_dir()

    def _make_store(self):
        return MetaStore(
            self._effective_store_dir(),
            self.ipf_project_root.text().strip(),
        )

    def _on_source_mode_changed(self):
        self._apply_source_mode(self.cmb_source_mode.currentData())
        # 데이터 폴더 기준이 바뀌었으니 다른 탭의 저장 목록도 새 기준으로 새로고침.
        self._refresh_other_tabs()

    def _apply_source_mode(self, mode):
        """Source Mode 에 맞춰 git/local 위젯의 활성 상태와 안내 문구를 갱신한다."""
        is_git = (mode != "local")

        # git 전용 입력/버튼.
        for w in (
            self.lbl_store, self.ipf_store_dir, self.btn_store,
            self.ipf_remote, self.ipf_branch, self.ipf_remote_url,
            self.btn_pull, self.btn_push,
        ):
            w.setEnabled(is_git)

        # local 전용 입력.
        for w in (self.lbl_local, self.ipf_local_dir, self.btn_local):
            w.setEnabled(not is_git)

        if is_git:
            self.git_group.setTitle(
                "Git Sync  (records / thumbnails only — originals are never pushed)")
            self.lbl_git_status.setText("")
        else:
            self.git_group.setTitle("Git Sync  (disabled in Local mode)")
            self.lbl_git_status.setText(
                "Local mode — records/thumbnails are read/written directly under "
                "the Shared Folder. No git; use Scan to refresh.")

    def _make_git(self):
        return GitSync(
            self.ipf_store_dir.text().strip(),
            self.ipf_remote.text().strip() or data_repo.DATA_REPO_REMOTE,
            self.ipf_branch.currentText().strip() or data_repo.DATA_REPO_BRANCH,
        )

    def _branch_names(self):
        """현재 Store Repo 의 git 브랜치 이름 목록(없으면 빈 목록). Branch 콤보용."""
        git = self._make_git()
        if not git.store_dir or not git.is_repo():
            return []
        ok, names = git.list_branches()
        return names if ok else []

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
            self.btn_expand_log,
            self.btn_edit_log,
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

        # extensions=None → .mb/.ma 뿐 아니라 모든 확장자의 파일을 리스트업한다
        # (.fbx/.obj/.png 등도 기록·썸네일 추적 대상이 될 수 있다).
        self._scanned_entries = scanner.scan(
            scan_dir,
            store,
            recursive=self.chk_recursive.isChecked(),
            extensions=None,
        )
        self.log(f"Scanned {len(self._scanned_entries)} file(s) in {scan_dir}")
        self._rebuild_type_menu()
        self._apply_file_filter()

    # --------------------------------------------------- File Types 확장자 필터

    def _rebuild_type_menu(self):
        """마지막 scan 에서 발견된 확장자들로 File Types 메뉴를 다시 만든다.

        이전에 사용자가 끄거나 켠 확장자 선택(self._type_states)은 이름 기준으로
        보존하고(여전히 존재하면), 새로 등장한 확장자는 기본 체크(표시) 상태로 둔다.
        """
        exts = sorted({(e.get("ext") or "") for e in self._scanned_entries})
        # 사라진 확장자는 버리고, 새 확장자는 기본 True 로 채운다.
        self._type_states = {x: self._type_states.get(x, True) for x in exts}

        self._types_menu.clear()
        self._type_actions = {}

        self.act_all_types = self._types_menu.addAction("All")
        self.act_all_types.setCheckable(True)
        self.act_all_types.triggered.connect(self._on_all_types_toggled)
        self._types_menu.addSeparator()

        for x in exts:
            label = ("." + x) if x else "(no ext)"
            act = self._types_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(self._type_states[x])
            act.triggered.connect(
                lambda checked, ex=x: self._on_type_toggled(ex, checked)
            )
            self._type_actions[x] = act

        self._sync_all_types_action()
        self._update_types_button_text()

    def _on_type_toggled(self, ext, checked):
        self._type_states[ext] = checked
        self._sync_all_types_action()
        self._update_types_button_text()
        self._apply_file_filter()

    def _on_all_types_toggled(self, checked):
        for ext, act in self._type_actions.items():
            act.setChecked(checked)
            self._type_states[ext] = checked
        self._update_types_button_text()
        self._apply_file_filter()

    def _sync_all_types_action(self):
        """'All' 항목 체크 상태를 개별 확장자들이 모두 켜져 있는지로 맞춘다."""
        all_on = all(self._type_states.values()) if self._type_states else True
        self.act_all_types.setChecked(all_on)

    def _update_types_button_text(self):
        """버튼 라벨에 현재 선택 요약을 표시한다(예: 'File Types: mb, ma')."""
        if not self._type_actions:
            self.btn_file_types.setText("File Types")
            return
        selected = [x for x, on in self._type_states.items() if on]
        if len(selected) == len(self._type_actions):
            self.btn_file_types.setText("File Types: All")
        elif not selected:
            self.btn_file_types.setText("File Types: none")
        else:
            shown = ", ".join((x or "(no ext)") for x in selected[:3])
            more = "" if len(selected) <= 3 else f" +{len(selected) - 3}"
            self.btn_file_types.setText(f"File Types: {shown}{more}")

    def on_reveal_in_explorer(self, entry):
        """파일 목록 우클릭 'Show in File Explorer' — 그 파일을 탐색기에서 선택해 연다."""
        if not entry:
            return
        path = entry.get("abs_path", "")
        if not path or not os.path.exists(path):
            QMessageBox.information(
                self, "Show in File Explorer",
                "File no longer exists at its scanned path.",
            )
            return
        if self._reveal_in_explorer(path):
            self.log(f"Shown in File Explorer: {path}")
        else:
            self.log(f"Failed to open File Explorer for: {path}")

    @staticmethod
    def _reveal_in_explorer(path):
        """OS 파일 탐색기에서 파일을 선택 상태로 연다(Framework.file_opener 위임)."""
        try:
            open_path(path)
            return True
        except (OSError, ValueError):
            return False

    def on_apply_name_filter(self):
        """이름 필터 입력값을 '적용 중'으로 확정하고 목록을 다시 거른다.

        비어 있으면 모든 파일, 키워드가 있으면 파일명(제목)에 그 키워드가 포함된
        파일만 남긴다(대소문자 무시). Filter 버튼 클릭 또는 Enter 로 적용한다.
        """
        self._name_filter = self.ipf_name_filter.text().strip()
        self._apply_file_filter()

    def _apply_file_filter(self):
        """마지막 scan 결과에 이름 + 확장자 + 'Show Recorded Only' 필터를 적용해
        테이블을 다시 채운다. 세 필터 모두 재스캔 없이 즉시 반영된다.
        """
        entries = self._scanned_entries

        # 0) 이름(제목) 키워드 필터 — 비어 있으면 전부.
        if self._name_filter:
            kw = self._name_filter.lower()
            entries = [
                e for e in entries if kw in e.get("file_name", "").lower()
            ]

        # 1) 확장자 필터 — 일부만 체크된 경우에만 거른다(전부 체크면 그대로).
        if self._type_actions:
            checked = {x for x, on in self._type_states.items() if on}
            if len(checked) < len(self._type_actions):
                entries = [e for e in entries if (e.get("ext") or "") in checked]

        # 2) record(Save Record)가 있는 파일만 보기.
        if self.chk_recorded_only.isChecked():
            entries = [e for e in entries if e.get("has_record")]

        self.file_table.set_entries(entries)
        # 시작 시 prefs 로드로도 불릴 수 있어, 스캔 결과가 있을 때만 로그를 남긴다.
        if self._scanned_entries:
            self.log(f"Showing {len(entries)} file(s).")

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

    @staticmethod
    def _log_history_text(record):
        """record.logs 를 'Log history' 표시용 텍스트로 만든다(인라인/Expand 팝업 공용)."""
        lines = []
        for entry in record.logs:
            lines.append(f"[{entry.timestamp}] {entry.author}")
            lines.append(entry.note)
            lines.append("")
        return "\n".join(lines).strip()

    def _refresh_log_history(self, record):
        self.txt_log_history.setPlainText(self._log_history_text(record))

    def on_edit_log(self):
        """선택된 파일의 Log history 를 항목 단위로 편집/삭제한다(구조 보존).

        OK 시 record.logs 를 새 목록으로 교체하고 인라인 표시를 갱신한다. 영속화는
        Add Log Entry 와 동일하게 Save Record 로(메모리 반영 후 안내)."""
        if not self._require_record():
            return
        record = self._current_record
        if not record.logs:
            QMessageBox.information(self, "Edit Log History", "No log entries to edit.")
            return

        dlg = LogEditDialog(record.logs, self)
        if dlg.exec_() != QDialog.Accepted:
            return

        record.logs = dlg.result_logs()
        self._refresh_log_history(record)
        self.log("Log history edited (remember to Save Record).")

    def on_expand_log(self):
        """현재 파일의 Log history 를 큰 읽기전용 창으로 띄운다.

        상세 패널이 좁아 로그가 길어지면 보기 어렵기에, 전체 폭의 리사이즈 가능한
        창에 같은 내용을 크게 보여준다(스냅샷 — 편집은 패널의 New note 로만).
        """
        record = self._current_record
        if record is None:
            QMessageBox.information(self, "Log history", "Select a file first.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Log history — {record.key}")
        dlg.resize(720, 560)

        v = QVBoxLayout(dlg)
        viewer = QPlainTextEdit()
        viewer.setReadOnly(True)
        viewer.setPlainText(self._log_history_text(record))
        v.addWidget(viewer, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dlg.reject)
        v.addWidget(buttons)

        dlg.exec_()

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
            self._thumbs_start_dir(),
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if path:
            self._apply_thumb(path)

    def _thumbs_start_dir(self):
        """Load Image 다이얼로그의 시작 경로 = Store Repo 의 thumbs 폴더.

        여기 이미 저장된 썸네일을 여러 파일에 재사용하기 쉽도록 그 폴더에서 열리게
        한다. Store Repo 미설정이거나 thumbs 폴더가 아직 없으면 홈으로 폴백한다.
        """
        store_dir = self.get_store_dir()
        if store_dir:
            thumbs = os.path.join(store_dir, MetaStore.THUMBS_DIR)
            if os.path.isdir(thumbs):
                return thumbs
        return os.path.expanduser("~")

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
        # 빈 공유/NAS 폴더라도 첫 저장에서 records/thumbs 가 함께 생기도록 보장.
        store.ensure_store()
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
        if self.cmb_source_mode.currentData() == "local":
            self.log("Local mode: Pull is disabled. Use Scan to refresh.")
            return
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
        if self.cmb_source_mode.currentData() == "local":
            self.log("Local mode: Push is disabled. Data is written directly to the Shared Folder.")
            return
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
