# Python Script by Ji Hun Park
# last Update date : 2026-07-01
# A00220_BackupTool - main window (Qt, standalone)
#
# 컴퓨터 비정상 종료에 대비해 지정 파일들을 주기적으로 자동 백업한다.
#  - 대상 파일 목록 / 백업 폴더명 / 접미사 / 분·초 주기 설정
#  - 덮어쓰기 또는 버전업(최근 N개 유지) 모드
#  - 상태 표시: Chrome-Dino 애니메이션(정지=서있음 / 동작=달리기 /
#    저장 감지=강조색 톡 점프 / 백업 성공=공중 360° 회전)

import os
import time

from Framework.core.file_opener import open_path
from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QTimer,
    QFileSystemWatcher,
    QApplication,
    QIcon,
    Qt,
)

from Framework.qt import JUN_mod_collapsible_qt

from ..config.version import VERSION
from ..config.app_meta import icon_path
from ..core import backup_manager, prefs as prefs_mod
from .dino_widget import DinoWidget


# 상태 상수
STATE_DEACTIVE = "deactive"
STATE_ACTIVE = "active"
STATE_SAVING = "saving"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"JUN Backup Tool  v{VERSION}")

        # 창/작업표시줄 아이콘. launch.py 가 app 전역으로도 설정하지만, 다른 진입점으로
        # 이 창을 직접 띄우는 경우까지 대비해 창 자체에도 지정한다(없으면 조용히 무시).
        _sIcon = icon_path()
        if _sIcon:
            self.setWindowIcon(QIcon(_sIcon))
        # 원본(560)보다 좁은 세로형 창. (좌우 나열 grid 구조라 정확히 절반까지는
        # 못 줄지만, 라디오/분·초를 세로로 쌓아 최대한 좁혔다.)
        self.resize(350, 680)

        self._prefs = prefs_mod.load()
        self._state = STATE_DEACTIVE
        self._next_save_ts = 0.0     # 다음 저장 예정 시각(time.monotonic 기준)
        # Settings 가 접혀 있을 때의 최신 창 높이(펼칠 때 정확히 복원하기 위함).
        self._collapsed_h = None
        # Auto Backup 용: 파일별 '마지막으로 백업한 시점의 mtime'. 이 값과 달라졌을
        # 때만(=사용자가 수정) 백업한다. 시작할 때 비우므로 첫 사이클은 전부 백업된다.
        self._last_mtimes = {}

        # 주기 백업 타이머
        self._backup_timer = QTimer(self)
        self._backup_timer.timeout.connect(self._do_backup_cycle)

        # Auto Backup 용 파일 감시자: 대상 파일이 디스크에서 바뀌는 순간(=사용자가
        # 저장하는 순간)을 감지한다. 주기 타이머는 감시자가 놓친 변경을 잡는 fallback.
        self._fs_watcher = QFileSystemWatcher(self)
        self._fs_watcher.fileChanged.connect(self._on_fs_changed)
        # 저장을 감지해도 '즉시' 백업하지 않고 파일별로 (지금 + Save Delay)초 뒤에
        # 백업을 예약한다({path: due_monotonic}). PC 가 저장 직후 크래시로 종료되면
        # 이 예약 백업도 프로세스와 함께 사라져 손상된 파일을 백업하지 않는다(직전의
        # 정상 백업본이 보존됨). 지연 중 같은 파일이 다시 저장되면 그 파일만 재예약해
        # '마지막 저장 + Delay' 시점에 settle 된 상태로 백업한다.
        self._pending_backup = {}
        self._delay_timer = QTimer(self)
        self._delay_timer.setInterval(1000)   # 1초 폴링(예약이 있을 때만 동작)
        self._delay_timer.timeout.connect(self._process_pending_backups)

        # 저장 감지 mtime 폴링(fallback). QFileSystemWatcher.fileChanged 는 Windows 10
        # 이나 임시파일 교체식(atomic replace) 저장에서 안정적으로 발화하지 않아, 저장
        # 순간을 놓치는 일이 있다. 감시 중인 파일의 mtime 을 주기적으로 직접 확인해
        # 변화를 잡으면 OS/저장 방식과 무관하게 저장을 감지한다(공룡 톡 점프 + 백업 예약).
        # {path: 마지막으로 관측한 mtime} — 저장 감지 전용 기준선(백업용 _last_mtimes 와 별개).
        self._watch_mtimes = {}
        self._save_poll_timer = QTimer(self)
        self._save_poll_timer.setInterval(500)   # 0.5초 폴링(감시 중일 때만 동작)
        self._save_poll_timer.timeout.connect(self._poll_saves)

        # (상태 표시는 텍스트 대신 Chrome-Dino 애니메이션. 자체 타이머로 동작.)

        # 다음 저장까지 남은 시간 카운트다운 타이머(1초)
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick_countdown)

        self._build_ui()
        self._load_prefs_to_ui()
        self._set_state(STATE_DEACTIVE)

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)

        # -------------------------
        # 상단 헤더 행 : Always on Top(Pin) 토글(우측). A00110_animTool 과 동일 패턴 —
        # 켜면 이 창이 다른 창들보다 항상 위에 유지된다(Qt.WindowStaysOnTopHint).
        # 기본은 정상 Z-order 라, 필요할 때만 켠다.
        # -------------------------
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other windows")
        # 고정 크기 — "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록 (넓은 라벨 기준)
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addStretch(1)
        header_row.addWidget(self.pin_button)
        root.addLayout(header_row)

        root.addWidget(self._build_files_group())
        root.addWidget(self._build_settings_group())
        root.addWidget(self._build_control_group())

        root.addWidget(QLabel("Log"))
        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(140)
        root.addWidget(self.log_widget)

    def _on_settings_toggled(self, expanded):
        """Settings 를 접고/펼칠 때, 사라지거나 나타나는 본문 높이만큼만 '창'을
        줄이거나 늘린다. 창을 sizeHint 로 다시 맞추면 늘어난 공간을 위쪽 파일 목록
        (expanding)이 흡수해 크기가 변하므로, 그 대신 정확히 본문 높이만큼만 창을
        움직여 파일 목록 등 다른 위젯의 크기는 그대로 유지한다.
        (사용자가 직접 창 크기를 바꿀 때는 파일 목록이 expanding 으로 그에 맞춰 늘고
        줄어드는 동작은 그대로다 — resizeEvent 가 접힘 상태 높이를 계속 추적한다.)

        - 접을 때: 현재(펼친) 높이에서 본문 높이를 뺀다. 단, 본문을 숨긴 직후엔 창의
          최소 높이가 아직 갱신되지 않아 곧바로 줄이면 옛 최소값에 막히므로(clamp),
          invalidate()+activate() 로 레이아웃 최소 크기를 먼저 강제로 다시 계산한다.
        - 펼칠 때: 본문을 보이는 순간 창이 새 최소 높이로 자동으로 커져버려 현재 높이를
          그대로 쓰면 본문 높이를 두 번 더하게 된다. 그래서 '마지막 접힘 높이'에 본문
          높이를 더해 복원한다."""
        delta = self._settings_section.body_height()
        if expanded:
            base = self._collapsed_h if self._collapsed_h is not None \
                else (self.height() - delta)
            target_h = base + delta
        else:
            target_h = self.height() - delta

        self._settings_section.updateGeometry()
        self.layout().invalidate()
        self.layout().activate()
        self.resize(self.width(), target_h)

    def resizeEvent(self, event):
        """접힘 상태에서의 창 높이를 기억해 둔다(펼칠 때 그만큼 복원하기 위함).
        사용자가 직접 창 크기를 바꿔도 이 값이 갱신되므로 파일 목록은 창에 맞춰 변한다."""
        super().resizeEvent(event)
        section = getattr(self, "_settings_section", None)
        if section is not None and not section.is_expanded():
            self._collapsed_h = self.height()

    def _build_files_group(self):
        group = QGroupBox("Target Files")
        layout = QVBoxLayout(group)

        self.list_files = QListWidget()
        self.list_files.setSelectionMode(QListWidget.ExtendedSelection)
        # 우클릭 → Reveal in File Explorer 컨텍스트 메뉴
        self.list_files.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_files.customContextMenuRequested.connect(
            self._on_files_context_menu)
        layout.addWidget(self.list_files)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("Add...")
        btn_add.clicked.connect(self.on_add_files)
        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self.on_remove_selected)
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.on_clear_files)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addWidget(btn_clear)
        layout.addLayout(btn_row)

        return group

    def _build_settings_group(self):
        # 접이식 Settings 섹션(A00110 의 JUN_mod_collapsible_qt 패턴).
        # 헤더 클릭으로 접고/펼치며, 토글 시 접힌/펼친 높이만큼 창을 줄이거나 늘린다.
        section = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            "Settings", expanded=True)
        self._settings_section = section
        section.toggled.connect(self._on_settings_toggled)

        grid = QGridLayout()

        # Backup folder name
        grid.addWidget(QLabel("Folder Name"), 0, 0)
        self.ipf_folder = QLineEdit("backup")
        grid.addWidget(self.ipf_folder, 0, 1, 1, 3)

        # Suffix
        grid.addWidget(QLabel("Suffix"), 1, 0)
        self.ipf_suffix = QLineEdit("BU")
        grid.addWidget(self.ipf_suffix, 1, 1, 1, 3)

        # Save mode
        grid.addWidget(QLabel("Save Mode"), 2, 0)
        self.rb_overwrite = QRadioButton("Overwrite")
        self.rb_version = QRadioButton("Version Up")
        self.rb_overwrite.setChecked(True)
        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self.rb_overwrite)
        self._mode_group.addButton(self.rb_version)
        self.rb_version.toggled.connect(self._on_mode_changed)
        # 라디오를 세로로 쌓아 가로폭을 줄인다(원본은 좌우 나열이었음).
        mode_col = QVBoxLayout()
        mode_col.addWidget(self.rb_overwrite)
        mode_col.addWidget(self.rb_version)
        grid.addLayout(mode_col, 2, 1, 1, 3)

        # Max versions
        grid.addWidget(QLabel("Max Versions"), 3, 0)
        self.spn_max = QSpinBox()
        self.spn_max.setRange(1, 999)
        self.spn_max.setValue(10)
        self.spn_max.setEnabled(False)
        self.spn_max.setFixedWidth(70)
        grid.addWidget(self.spn_max, 3, 1)

        # Interval (minutes / seconds)
        grid.addWidget(QLabel("Interval"), 4, 0)
        self.spn_min = QSpinBox()
        self.spn_min.setRange(0, 999)
        self.spn_min.setValue(5)
        self.spn_min.setFixedWidth(60)
        self.spn_sec = QSpinBox()
        self.spn_sec.setRange(0, 59)
        self.spn_sec.setValue(0)
        self.spn_sec.setFixedWidth(56)
        # 분/초를 두 줄로 나눠 가로폭을 줄인다(라디오 세로 배치와 같은 취지).
        min_row = QHBoxLayout()
        min_row.addWidget(self.spn_min)
        min_row.addWidget(QLabel("min"))
        min_row.addStretch(1)
        grid.addLayout(min_row, 4, 1, 1, 3)
        sec_row = QHBoxLayout()
        sec_row.addWidget(self.spn_sec)
        sec_row.addWidget(QLabel("sec"))
        sec_row.addStretch(1)
        grid.addLayout(sec_row, 5, 1, 1, 3)

        # Save Delay (Auto Backup 전용): 저장 감지 후 실제 백업까지의 지연.
        grid.addWidget(QLabel("Save Delay"), 6, 0)
        self.spn_delay = QSpinBox()
        self.spn_delay.setRange(0, 600)
        self.spn_delay.setValue(10)
        self.spn_delay.setFixedWidth(60)
        self.spn_delay.setToolTip(
            "Auto Backup only. Wait this many seconds after a save is detected "
            "before backing the file up. If the PC crashes within this window "
            "the pending backup dies with the tool, so a corrupted half-saved "
            "file is not copied over the last good backup. 0 = back up on the "
            "next poll (~1s).")
        delay_row = QHBoxLayout()
        delay_row.addWidget(self.spn_delay)
        delay_row.addWidget(QLabel("sec"))
        delay_row.addStretch(1)
        grid.addLayout(delay_row, 6, 1, 1, 3)

        section.add_layout(grid)
        return section

    def _build_control_group(self):
        group = QGroupBox("Control")
        layout = QVBoxLayout(group)

        # Auto Backup: 켜져 있으면 '마지막 백업 이후 수정된(변경된) 파일만' 백업하고,
        # 변경이 없으면 아무 동작도 하지 않는다. 끄면 매 주기마다 전 파일을 백업.
        self.chk_auto = QCheckBox("Auto Backup")
        self.chk_auto.setChecked(True)
        self.chk_auto.setToolTip(
            "Back up each file the moment it is saved (changed on disk); idle "
            "files are skipped. Off = back up every file each interval.")
        self.chk_auto.toggled.connect(self._on_auto_toggled)
        layout.addWidget(self.chk_auto)

        row = QHBoxLayout()
        self.btn_toggle = QPushButton("Start")
        self.btn_toggle.setMinimumHeight(36)
        self.btn_toggle.clicked.connect(self.on_toggle)
        row.addWidget(self.btn_toggle)
        layout.addLayout(row)

        # 상태 표시: 글자 대신 Chrome-Dino. Active 면 달리며 주기적으로 점프,
        # 정지면 가만히 서 있는다. 저장 감지 순간엔 강조색 톡 점프(notify_save),
        # 실제 백업 순간엔 360° 스핀(spin)으로 구분해 알린다.
        self.dino = DinoWidget(px=3)
        layout.addWidget(self.dino)

        # 다음 저장까지 남은 시간 카운트다운
        self.lbl_countdown = QLabel()
        self.lbl_countdown.setStyleSheet("font-size: 13px;")
        self.lbl_countdown.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_countdown)

        return group

    # ========================================================== always-on-top

    def toggle_always_on_top(self, enabled):
        """Always on Top(Pin) 토글. WindowStaysOnTopHint 를 켜고/끄고, 플래그 변경 후
        다시 show() 한다(플래그를 바꾸면 창이 숨는 Qt 특성 회피). A00110_animTool 과 동일."""
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()
        self.log(f"Always on Top: {'ON' if enabled else 'OFF'}")

    # ============================================================== prefs

    def _load_prefs_to_ui(self):
        for path in self._prefs.get("files", []):
            self._add_file_item(path)
        self.ipf_folder.setText(self._prefs.get("folder_name", "backup"))
        self.ipf_suffix.setText(self._prefs.get("suffix", "BU"))
        versioned = bool(self._prefs.get("versioned", False))
        self.rb_version.setChecked(versioned)
        self.rb_overwrite.setChecked(not versioned)
        self.spn_max.setValue(int(self._prefs.get("max_versions", 10)))
        self.spn_min.setValue(int(self._prefs.get("minutes", 5)))
        self.spn_sec.setValue(int(self._prefs.get("seconds", 0)))
        self.spn_delay.setValue(int(self._prefs.get("save_delay", 10)))
        self.chk_auto.setChecked(bool(self._prefs.get("auto_backup", True)))

    def _collect_prefs(self):
        return {
            "files": self._files(),
            "folder_name": self.ipf_folder.text().strip() or "backup",
            "suffix": self.ipf_suffix.text().strip() or "BU",
            "versioned": self.rb_version.isChecked(),
            "max_versions": self.spn_max.value(),
            "minutes": self.spn_min.value(),
            "seconds": self.spn_sec.value(),
            "save_delay": self.spn_delay.value(),
            "auto_backup": self.chk_auto.isChecked(),
        }

    def _save_prefs(self):
        self._prefs = self._collect_prefs()
        prefs_mod.save(self._prefs)

    # ============================================================ helpers

    def _add_file_item(self, path):
        """파일을 목록에 추가한다. 표시는 파일명만, 전체 경로는 UserRole 에 보관한다.

        목록이 좁아도 이름만 보이게 하고, 실제 경로(백업·중복검사·탐색기 열기용)는
        Qt.UserRole 로 들고 있는다. 같은 이름의 다른 폴더 파일을 구분할 수 있도록
        전체 경로를 툴팁으로 보여준다."""
        item = QListWidgetItem(os.path.basename(path))
        item.setData(Qt.UserRole, path)
        item.setToolTip(path)
        self.list_files.addItem(item)

    def _files(self):
        return [self.list_files.item(i).data(Qt.UserRole)
                for i in range(self.list_files.count())]

    def _interval_ms(self):
        return (self.spn_min.value() * 60 + self.spn_sec.value()) * 1000

    def log(self, message):
        self.log_widget.appendPlainText(str(message))

    def _on_mode_changed(self, checked):
        self.spn_max.setEnabled(self.rb_version.isChecked())

    # ============================================================ file list

    def on_add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Back Up", os.path.expanduser("~")
        )
        existing = set(self._files())
        for path in paths:
            if path not in existing:
                self._add_file_item(path)
                existing.add(path)

    def on_remove_selected(self):
        for item in self.list_files.selectedItems():
            self.list_files.takeItem(self.list_files.row(item))

    def on_clear_files(self):
        self.list_files.clear()

    def _on_files_context_menu(self, pos):
        """Target Files 우클릭 메뉴 — 'Reveal in File Explorer'.

        클릭한 항목의 전체 경로(UserRole)를 탐색기에서 선택 상태로 연다."""
        item = self.list_files.itemAt(pos)
        if item is None:
            return

        menu = QMenu(self.list_files)
        act_reveal = menu.addAction("Reveal in File Explorer")
        chosen = menu.exec_(self.list_files.viewport().mapToGlobal(pos))
        if chosen != act_reveal:
            return

        path = item.data(Qt.UserRole)
        if not path or not os.path.exists(path):
            QMessageBox.warning(
                self, "Reveal in File Explorer",
                "File not found:\n%s" % path)
            return
        if not self._reveal_in_explorer(path):
            QMessageBox.warning(
                self, "Reveal in File Explorer",
                "Failed to open File Explorer for:\n%s" % path)

    @staticmethod
    def _reveal_in_explorer(path):
        """OS 파일 탐색기에서 파일을 선택 상태로 연다(Framework.file_opener 위임)."""
        try:
            open_path(path)
            return True
        except (OSError, ValueError):
            return False

    # ============================================================== control

    def on_toggle(self):
        if self._state == STATE_DEACTIVE:
            self.on_start()
        else:
            self.on_stop()

    def on_start(self):
        if self.list_files.count() == 0:
            QMessageBox.warning(self, "Backup", "Please add at least one file.")
            return

        interval = self._interval_ms()
        if interval <= 0:
            QMessageBox.warning(self, "Backup", "Interval must be greater than 0.")
            return

        self._save_prefs()
        self._set_settings_enabled(False)
        self.btn_toggle.setText("Stop")

        # 새 세션이므로 변경 추적을 초기화 → 첫 사이클은 전 파일을 백업(기준선).
        self._last_mtimes = {}

        self._set_state(STATE_ACTIVE)
        self._countdown_timer.start()
        self._backup_timer.start(interval)
        # Auto Backup 이면 저장 즉시 백업하도록 파일 감시 시작.
        if self.chk_auto.isChecked():
            self._start_watching()

        m, s = self.spn_min.value(), self.spn_sec.value()
        mode = "Auto Backup (on save)" if self.chk_auto.isChecked() \
            else "every file"
        self.log(
            f"Started. Watching {self.list_files.count()} file(s), interval "
            f"{m}m {s}s - {mode}.")

        # 즉각 피드백을 위해 시작 직후 1회 백업.
        self._do_backup_cycle()

    def on_stop(self):
        self._backup_timer.stop()
        self._countdown_timer.stop()
        self._stop_watching()
        self.btn_toggle.setText("Start")
        self._set_settings_enabled(True)
        self._set_state(STATE_DEACTIVE)
        self.log("Stopped.")

    def _do_backup_cycle(self):
        # 다음 저장 예정 시각을 갱신(주기 타이머 fire 시점 기준).
        self._next_save_ts = time.monotonic() + self._interval_ms() / 1000.0

        auto = self.chk_auto.isChecked()
        files = self._files()
        # Auto Backup: 마지막 백업 이후 수정된 파일만 대상으로. (변경 추적이 비어 있는
        # 첫 사이클은 모든 파일이 '변경'으로 잡혀 전부 백업된다.)
        targets = [f for f in files if self._is_changed(f)] if auto else files

        if not targets:
            # 변경된 파일이 없으면 아무 동작도 하지 않는다(방치 상태 = 명령 없음).
            return

        self._backup_targets(targets)

    def _backup_targets(self, targets):
        """주어진 파일들을 1회 백업한다(주기 사이클 / 저장 감지 공용)."""
        if not targets:
            return

        # Saving 상태를 화면에 보이게 갱신 후 복사.
        self._set_state(STATE_SAVING)
        QApplication.processEvents()

        folder = self.ipf_folder.text().strip() or "backup"
        suffix = self.ipf_suffix.text().strip() or "BU"
        versioned = self.rb_version.isChecked()
        max_versions = self.spn_max.value()

        ok = 0
        for src in targets:
            try:
                dst = backup_manager.backup_one(
                    src, folder, suffix, versioned, max_versions
                )
                # 백업 성공한 파일의 mtime 을 기록해 다음부터 변경 여부를 비교.
                self._last_mtimes[src] = self._safe_mtime(src)
                self.log(f"Backed up: {os.path.basename(dst)}")
                ok += 1
            except FileNotFoundError:
                self.log(f"[skip] File not found: {src}")
            except Exception as exc:  # noqa: BLE001 - 어떤 IO 오류도 다음 파일로 진행
                self.log(f"[error] {src}: {exc}")

        self.log(f"Cycle done ({ok}/{len(targets)} backed up).")

        # 파일이 실제로 한 개라도 백업됐으면 공룡이 공중에서 360° 회전해 알린다.
        if ok:
            self.dino.spin()

        # 백업 종료 후 다시 Active 로(정지되지 않았다면).
        if self._backup_timer.isActive() or self._state == STATE_SAVING:
            if self.btn_toggle.text() == "Stop":
                self._set_state(STATE_ACTIVE)

    # ============================================================ file watch

    def _on_auto_toggled(self, checked):
        """실행 중에 Auto Backup 을 켜고/끌 때 파일 감시를 시작/정지한다."""
        if self._state == STATE_DEACTIVE:
            return
        if checked:
            self._start_watching()
        else:
            self._stop_watching()

    def _start_watching(self):
        """대상 파일들을 감시 목록에 올린다(기존 목록은 비우고 다시 등록)."""
        current = self._fs_watcher.files()
        if current:
            self._fs_watcher.removePaths(current)
        paths = [f for f in self._files() if os.path.isfile(f)]
        if paths:
            self._fs_watcher.addPaths(paths)

        # mtime 폴링 fallback 기준선을 현재 값으로 잡고(=지금은 '변경 없음') 폴링 시작.
        self._watch_mtimes = {f: self._safe_mtime(f) for f in paths}
        self._save_poll_timer.start()

    def _stop_watching(self):
        self._delay_timer.stop()
        self._save_poll_timer.stop()
        self._watch_mtimes = {}
        self._pending_backup.clear()
        current = self._fs_watcher.files()
        if current:
            self._fs_watcher.removePaths(current)

    def _on_fs_changed(self, path):
        """QFileSystemWatcher 가 파일 변경(저장 순간)을 알릴 때 호출된다."""
        self._on_save_detected(path)

    def _poll_saves(self):
        """mtime 폴링 fallback — 감시 중인 파일의 수정시각이 바뀌면 저장으로 감지한다.

        QFileSystemWatcher 가 (특히 Windows 10 / 임시파일 교체식 저장에서) 놓치는 저장을
        여기서 잡는다. 기준선(_watch_mtimes)과 달라진 파일만 저장으로 처리한다.
        """
        for f in self._files():
            if not os.path.isfile(f):
                continue
            mtime = self._safe_mtime(f)
            if mtime is None:
                continue
            if f not in self._watch_mtimes:
                # 감시 중 새로 나타난 파일: 기준선만 잡고 이번엔 저장으로 치지 않는다.
                self._watch_mtimes[f] = mtime
                continue
            if mtime != self._watch_mtimes[f]:
                self._on_save_detected(f)

    def _on_save_detected(self, path):
        """파일이 디스크에서 바뀐(저장) 순간의 공통 처리. QFileSystemWatcher 와 mtime
        폴링 양쪽에서 호출되며, 같은 저장이 양쪽에서 중복 발화해도 mtime 으로 한 번만 처리한다.

        곧바로 백업하지 않고 (지금 + Save Delay)초 뒤로 백업을 예약한다. 지연 중 같은
        파일이 다시 저장되면 due 를 갱신해 '마지막 저장 + Delay' 시점으로 미룬다(settle).
        지연 중 PC 가 크래시로 종료되면 이 예약 백업도 함께 사라져, 손상된(반쯤 저장된)
        파일이 정상 백업본을 덮어쓰는 사고를 막는다."""
        # 중복 발화 방지: 이미 같은 mtime 을 처리했으면(watcher+폴링 동시 발화 등) 무시.
        mtime = self._safe_mtime(path)
        if mtime is not None:
            if self._watch_mtimes.get(path) == mtime:
                return
            self._watch_mtimes[path] = mtime

        delay = self.spn_delay.value()
        self._pending_backup[path] = time.monotonic() + delay
        if not self._delay_timer.isActive():
            self._delay_timer.start()
        # 사용자가 파일을 저장한 '순간' 을 공룡이 강조색 톡 점프로 알린다(실제 백업 순간의
        # 360° 스핀과 눈으로 구분되게). 실제 백업은 Save Delay 뒤 _backup_targets 에서 일어난다.
        self.dino.notify_save()
        # 임시파일 교체식 저장은 감시 경로를 떨궈내므로, 다음 저장을 놓치지 않도록
        # 지연을 기다리지 말고 곧바로 다시 등록한다.
        self._rewatch_files()

    def _process_pending_backups(self):
        """1초마다 폴링 — due 시각이 지난 예약 파일을 백업한다.

        due 가 지난 파일만 골라 백업하고, 아직 남은 예약이 없으면 타이머를 멈춘다.
        (예약이 있을 때만 타이머가 돈다.)"""
        if self._state == STATE_DEACTIVE or not self.chk_auto.isChecked():
            self._pending_backup.clear()
            self._delay_timer.stop()
            return

        now = time.monotonic()
        due = [p for p, due_ts in self._pending_backup.items() if due_ts <= now]
        for p in due:
            self._pending_backup.pop(p, None)

        targets = [p for p in due if os.path.isfile(p)]
        if targets:
            self._backup_targets(targets)
            # 임시파일 교체식 저장 대비 감시 경로 복원.
            self._rewatch_files()

        if not self._pending_backup:
            self._delay_timer.stop()

    def _rewatch_files(self):
        """현재 감시되지 않는 대상 파일을 다시 감시 목록에 올린다."""
        watched = set(self._fs_watcher.files())
        to_add = [f for f in self._files()
                  if f not in watched and os.path.isfile(f)]
        if to_add:
            self._fs_watcher.addPaths(to_add)

    def _is_changed(self, src):
        """src 가 마지막 백업 이후 수정됐는지(mtime 변화). 접근 불가/없음이면 False."""
        mtime = self._safe_mtime(src)
        if mtime is None:
            return False
        return self._last_mtimes.get(src) != mtime

    @staticmethod
    def _safe_mtime(src):
        try:
            return os.path.getmtime(src)
        except OSError:
            return None

    # =============================================================== status

    def _set_state(self, state):
        self._state = state
        if state == STATE_DEACTIVE:
            self.dino.set_running(False)             # 공룡 정지(서 있음)
            self.lbl_countdown.setText("Next save in  --:--")
        elif state == STATE_SAVING:
            self.dino.set_running(True)
            # 회전(360° spin)은 파일이 '실제로' 백업된 순간(_backup_targets)에 트리거한다.
            # Auto Backup 모드는 카운트다운 대신 'Auto save' 문구.
            self.lbl_countdown.setText(
                "Auto save" if self.chk_auto.isChecked() else "Next save in  00:00")
        else:                                        # ACTIVE: 달리기 + 주기적 점프
            self.dino.set_running(True)
            self._tick_countdown()

    def _tick_countdown(self):
        if self._state == STATE_DEACTIVE:
            return
        # Auto Backup 모드: 다음 저장까지 카운트다운 대신 'Auto save' 만 표시.
        if self.chk_auto.isChecked():
            self.lbl_countdown.setText("Auto save")
            return
        remaining = max(0, int(round(self._next_save_ts - time.monotonic())))
        m, s = divmod(remaining, 60)
        self.lbl_countdown.setText(f"Next save in  {m:02d}:{s:02d}")

    def _set_settings_enabled(self, enabled):
        for w in (
            self.list_files,
            self.ipf_folder,
            self.ipf_suffix,
            self.rb_overwrite,
            self.rb_version,
            self.spn_max,
            self.spn_min,
            self.spn_sec,
            self.spn_delay,
        ):
            w.setEnabled(enabled)
        # Max Versions 는 Version Up 일 때만 켠다.
        if enabled:
            self.spn_max.setEnabled(self.rb_version.isChecked())

    # ================================================================ close

    def closeEvent(self, event):
        self._backup_timer.stop()
        try:
            self._save_prefs()
        finally:
            super().closeEvent(event)
