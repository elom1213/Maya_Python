# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00220_BackupTool - main window (Qt, standalone)
#
# 컴퓨터 비정상 종료에 대비해 지정 파일들을 주기적으로 자동 백업한다.
#  - 대상 파일 목록 / 백업 폴더명 / 접미사 / 분·초 주기 설정
#  - 덮어쓰기 또는 버전업(최근 N개 유지) 모드
#  - 상태 표시: Deactive / Active...(점 애니메이션) / Saving

import os
import time

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QPlainTextEdit,
    QFileDialog,
    QMessageBox,
    QTimer,
    QApplication,
    Qt,
)

from Framework.qt import JUN_mod_collapsible_qt

from ..config.version import VERSION
from ..core import backup_manager, prefs as prefs_mod


# 상태 상수
STATE_DEACTIVE = "deactive"
STATE_ACTIVE = "active"
STATE_SAVING = "saving"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"JUN Backup Tool  v{VERSION}")
        # 원본(560)보다 좁은 세로형 창. (좌우 나열 grid 구조라 정확히 절반까지는
        # 못 줄지만, 라디오/분·초를 세로로 쌓아 최대한 좁혔다.)
        self.resize(350, 680)

        self._prefs = prefs_mod.load()
        self._state = STATE_DEACTIVE
        self._dot_count = 1
        self._next_save_ts = 0.0     # 다음 저장 예정 시각(time.monotonic 기준)
        # Settings 가 접혀 있을 때의 최신 창 높이(펼칠 때 정확히 복원하기 위함).
        self._collapsed_h = None

        # 주기 백업 타이머
        self._backup_timer = QTimer(self)
        self._backup_timer.timeout.connect(self._do_backup_cycle)

        # Active 상태 점(...) 애니메이션 타이머
        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(500)
        self._dot_timer.timeout.connect(self._tick_dots)

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

        section.add_layout(grid)
        return section

    def _build_control_group(self):
        group = QGroupBox("Control")
        layout = QVBoxLayout(group)

        row = QHBoxLayout()
        self.btn_toggle = QPushButton("Start")
        self.btn_toggle.setMinimumHeight(36)
        self.btn_toggle.clicked.connect(self.on_toggle)
        row.addWidget(self.btn_toggle)

        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        row.addWidget(self.lbl_status, stretch=1)
        layout.addLayout(row)

        # 다음 저장까지 남은 시간 카운트다운
        self.lbl_countdown = QLabel()
        self.lbl_countdown.setStyleSheet("font-size: 13px;")
        self.lbl_countdown.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_countdown)

        return group

    # ============================================================== prefs

    def _load_prefs_to_ui(self):
        for path in self._prefs.get("files", []):
            self.list_files.addItem(path)
        self.ipf_folder.setText(self._prefs.get("folder_name", "backup"))
        self.ipf_suffix.setText(self._prefs.get("suffix", "BU"))
        versioned = bool(self._prefs.get("versioned", False))
        self.rb_version.setChecked(versioned)
        self.rb_overwrite.setChecked(not versioned)
        self.spn_max.setValue(int(self._prefs.get("max_versions", 10)))
        self.spn_min.setValue(int(self._prefs.get("minutes", 5)))
        self.spn_sec.setValue(int(self._prefs.get("seconds", 0)))

    def _collect_prefs(self):
        return {
            "files": self._files(),
            "folder_name": self.ipf_folder.text().strip() or "backup",
            "suffix": self.ipf_suffix.text().strip() or "BU",
            "versioned": self.rb_version.isChecked(),
            "max_versions": self.spn_max.value(),
            "minutes": self.spn_min.value(),
            "seconds": self.spn_sec.value(),
        }

    def _save_prefs(self):
        self._prefs = self._collect_prefs()
        prefs_mod.save(self._prefs)

    # ============================================================ helpers

    def _files(self):
        return [self.list_files.item(i).text()
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
                self.list_files.addItem(path)
                existing.add(path)

    def on_remove_selected(self):
        for item in self.list_files.selectedItems():
            self.list_files.takeItem(self.list_files.row(item))

    def on_clear_files(self):
        self.list_files.clear()

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

        self._set_state(STATE_ACTIVE)
        self._dot_timer.start()
        self._countdown_timer.start()
        self._backup_timer.start(interval)

        m, s = self.spn_min.value(), self.spn_sec.value()
        self.log(f"Started. Backing up {self.list_files.count()} file(s) every {m}m {s}s.")

        # 즉각 피드백을 위해 시작 직후 1회 백업.
        self._do_backup_cycle()

    def on_stop(self):
        self._backup_timer.stop()
        self._dot_timer.stop()
        self._countdown_timer.stop()
        self.btn_toggle.setText("Start")
        self._set_settings_enabled(True)
        self._set_state(STATE_DEACTIVE)
        self.log("Stopped.")

    def _do_backup_cycle(self):
        # 다음 저장 예정 시각을 갱신(주기 타이머 fire 시점 기준).
        self._next_save_ts = time.monotonic() + self._interval_ms() / 1000.0

        # Saving 상태를 화면에 보이게 갱신 후 복사.
        self._set_state(STATE_SAVING)
        QApplication.processEvents()

        folder = self.ipf_folder.text().strip() or "backup"
        suffix = self.ipf_suffix.text().strip() or "BU"
        versioned = self.rb_version.isChecked()
        max_versions = self.spn_max.value()

        ok = 0
        for src in self._files():
            try:
                dst = backup_manager.backup_one(
                    src, folder, suffix, versioned, max_versions
                )
                self.log(f"Backed up: {os.path.basename(dst)}")
                ok += 1
            except FileNotFoundError:
                self.log(f"[skip] File not found: {src}")
            except Exception as exc:  # noqa: BLE001 - 어떤 IO 오류도 다음 파일로 진행
                self.log(f"[error] {src}: {exc}")

        self.log(f"Cycle done ({ok}/{self.list_files.count()}).")

        # 백업 종료 후 다시 Active 로(정지되지 않았다면).
        if self._backup_timer.isActive() or self._state == STATE_SAVING:
            if self.btn_toggle.text() == "Stop":
                self._set_state(STATE_ACTIVE)

    # =============================================================== status

    def _set_state(self, state):
        self._state = state
        if state == STATE_DEACTIVE:
            self.lbl_status.setText("Deactive")
            self.lbl_countdown.setText("Next save in  --:--")
        elif state == STATE_SAVING:
            self.lbl_status.setText("Saving")
            self.lbl_countdown.setText("Next save in  00:00")
        else:
            self._dot_count = 1
            self._render_active()
            self._tick_countdown()

    def _tick_dots(self):
        if self._state != STATE_ACTIVE:
            return
        self._dot_count = self._dot_count % 3 + 1
        self._render_active()

    def _render_active(self):
        self.lbl_status.setText("Active" + "." * self._dot_count)

    def _tick_countdown(self):
        if self._state == STATE_DEACTIVE:
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
        ):
            w.setEnabled(enabled)
        # Max Versions 는 Version Up 일 때만 켠다.
        if enabled:
            self.spn_max.setEnabled(self.rb_version.isChecked())

    # ================================================================ close

    def closeEvent(self, event):
        self._backup_timer.stop()
        self._dot_timer.stop()
        try:
            self._save_prefs()
        finally:
            super().closeEvent(event)
