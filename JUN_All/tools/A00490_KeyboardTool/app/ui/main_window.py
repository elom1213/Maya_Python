# Python Script by Ji Hun Park
# last Update date : 2026-10-01
# A00490_KeyboardTool - main window (Qt, standalone)
#
# 키 여러 개를 순서대로, 키마다 정한 횟수 · 간격으로 누른다. 루프 가능.
# 대상 창을 고르면 그 창들에만 보낸다 (예: 크롬 A, B 에만 - C 는 그대로).
#
#   위   : Key Sequence 표 (Key | Count | Interval) + 프리셋
#   가운데: Target Windows (체크한 창에만) + Send Method
#   아래 : Loop · Start Delay · Start / Stop + 진행 상태 + 로그
#
# 실행은 core.runner.SequenceRunner (백그라운드 스레드). 콜백은 Qt 신호의 emit 이라
# 메인 스레드에서 처리된다.

import os

from Framework.qt.qt import (
    Qt, QObject, Signal,
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QLineEdit, QListWidget,
    QListWidgetItem, QRadioButton, QButtonGroup, QInputDialog, QMessageBox,
    QIcon, QSplitter,
)
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_checkList_qt_v01 import JUN_mod_checkList_qt_v01

from ..config.version import VERSION
from ..config.app_meta import icon_path
from ..core import keys, win32, presets
from ..core.runner import (SequenceRunner, Step, validate, METHOD_BACKGROUND,
                           METHOD_FOREGROUND, STOP_HOTKEY_NAME)
from .key_capture import KeyCaptureEdit


COL_KEY, COL_COUNT, COL_INTERVAL = 0, 1, 2

DEFAULT_STEPS = [Step("Down", 10, 1.0), Step("Up", 10, 1.0)]


class _Bridge(QObject):
    """러너 스레드 -> UI. 다른 스레드에서 emit 하면 큐 연결로 메인 스레드에서 받는다."""
    log = Signal(str)
    progress = Signal(str)
    finished = Signal(str)


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"JUN Keyboard Tool  v{VERSION}")
        self.resize(600, 900)

        _sIcon = icon_path()
        if _sIcon:
            self.setWindowIcon(QIcon(_sIcon))

        self._runner = None
        self._bridge = _Bridge()
        self._bridge.log.connect(self.log)
        self._bridge.progress.connect(self._on_progress)
        self._bridge.finished.connect(self._on_finished)

        self._build_ui()
        self._set_steps(DEFAULT_STEPS)
        self._reload_presets()
        self.refresh_windows()

        if not win32.IS_WINDOWS:
            self.log("[WARN] This tool works on Windows 10 / 11 only.")

    # ================================================================ UI

    def _build_ui(self):
        root = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        self.menu_bar.addMenu("Help")
        root.setMenuBar(self.menu_bar)

        # Pin - Run 상자의 상태 줄 오른쪽에 둔다 (헤더 행을 따로 두면 창이 그만큼 길어진다)
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self._build_sequence_box())
        splitter.addWidget(self._build_target_box())
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        root.addWidget(self._build_run_box())

        self.log_widget = JUN_mod_log_qt_v01(
            window_title="Keyboard Tool - Log",
            object_name="JUN_A00490_KeyboardTool_log_window")
        self.log_widget.setMinimumHeight(80)
        root.addWidget(self.log_widget)

    # ---------------------------------------------------------- sequence

    def _build_sequence_box(self):
        box = QGroupBox("Key Sequence")
        lay = QVBoxLayout(box)

        # 프리셋 행
        row = QHBoxLayout()
        row.addWidget(QLabel("Preset"))
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(160)
        row.addWidget(self.preset_combo, 1)
        for text, tip, slot in (
                ("Load", "Load the selected preset", self.load_preset),
                ("Save", "Save the current sequence as a preset", self.save_preset),
                ("Delete", "Delete the selected preset", self.delete_preset)):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            row.addWidget(b)
        lay.addLayout(row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Key", "Count", "Interval (s)"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(COL_KEY, QHeaderView.Stretch)
        hh.setSectionResizeMode(COL_COUNT, QHeaderView.Fixed)
        hh.setSectionResizeMode(COL_INTERVAL, QHeaderView.Fixed)
        self.table.setColumnWidth(COL_COUNT, 100)
        self.table.setColumnWidth(COL_INTERVAL, 110)
        self.table.setMinimumHeight(120)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setToolTip(
            "Key: click the field and press a key (Ctrl/Shift/Alt combos too),\n"
            "or type a name such as Down, Enter, F5, Ctrl+C.")
        lay.addWidget(self.table, 1)

        btns = QHBoxLayout()
        for text, tip, slot in (
                ("Add", "Add a key below the selected row", self.add_step),
                ("Remove", "Remove the selected row", self.remove_step),
                ("Up", "Move the selected row up", lambda: self.move_step(-1)),
                ("Down", "Move the selected row down", lambda: self.move_step(1)),
                ("Clear", "Remove all rows", self.clear_steps)):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            btns.addWidget(b)
        lay.addLayout(btns)
        return box

    def _make_row_widgets(self, step):
        key_edit = KeyCaptureEdit()
        key_edit.setText(step.key)
        cnt = QSpinBox()
        cnt.setRange(1, 1000000)
        cnt.setValue(step.count)
        itv = QDoubleSpinBox()
        itv.setRange(0.0, 86400.0)
        itv.setDecimals(2)
        itv.setSingleStep(0.1)
        itv.setValue(step.interval)
        itv.setToolTip("Seconds to wait after each press")
        return key_edit, cnt, itv

    def _insert_row(self, row, step):
        self.table.insertRow(row)
        key_edit, cnt, itv = self._make_row_widgets(step)
        self.table.setCellWidget(row, COL_KEY, key_edit)
        self.table.setCellWidget(row, COL_COUNT, cnt)
        self.table.setCellWidget(row, COL_INTERVAL, itv)

    def get_steps(self):
        steps = []
        for r in range(self.table.rowCount()):
            steps.append(Step(self.table.cellWidget(r, COL_KEY).text().strip(),
                              self.table.cellWidget(r, COL_COUNT).value(),
                              self.table.cellWidget(r, COL_INTERVAL).value()))
        return steps

    def _set_steps(self, steps, select=-1):
        # 셀 위젯은 행 이동이 안 되므로 목록으로 다시 그린다
        self.table.setRowCount(0)
        for i, s in enumerate(steps):
            self._insert_row(i, s)
        if 0 <= select < self.table.rowCount():
            self.table.selectRow(select)

    def _current_row(self):
        rows = self.table.selectionModel().selectedRows()
        return rows[0].row() if rows else self.table.rowCount() - 1

    def add_step(self):
        steps = self.get_steps()
        r = self._current_row() + 1
        base = steps[r - 1] if 0 < r <= len(steps) else Step("Down", 10, 1.0)
        steps.insert(r, Step(base.key, base.count, base.interval))
        self._set_steps(steps, r)

    def remove_step(self):
        steps = self.get_steps()
        r = self._current_row()
        if 0 <= r < len(steps):
            del steps[r]
            self._set_steps(steps, min(r, len(steps) - 1))

    def move_step(self, delta):
        steps = self.get_steps()
        r = self._current_row()
        n = r + delta
        if 0 <= r < len(steps) and 0 <= n < len(steps):
            steps[r], steps[n] = steps[n], steps[r]
            self._set_steps(steps, n)

    def clear_steps(self):
        self._set_steps([])

    # ---------------------------------------------------------- targets

    def _build_target_box(self):
        box = QGroupBox("Target Windows")
        lay = QVBoxLayout(box)

        mode_row = QHBoxLayout()
        self.rb_selected = QRadioButton("Checked windows only")
        self.rb_selected.setToolTip("Send keys only to the windows checked below.")
        self.rb_active = QRadioButton("Whatever window is active")
        self.rb_active.setToolTip(
            "Send keys like a real keyboard to the window that has focus at each press.")
        self.rb_selected.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_selected)
        grp.addButton(self.rb_active)
        self.rb_selected.toggled.connect(self._update_target_mode)
        mode_row.addWidget(self.rb_selected)
        mode_row.addWidget(self.rb_active)
        mode_row.addStretch(1)
        lay.addLayout(mode_row)

        filt_row = QHBoxLayout()
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter (title or process, e.g. chrome)")
        self.filter_edit.textChanged.connect(self._apply_filter)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Read the open windows again")
        self.refresh_button.clicked.connect(self.refresh_windows)
        filt_row.addWidget(self.filter_edit, 1)
        filt_row.addWidget(self.refresh_button)
        lay.addLayout(filt_row)

        self.window_list = QListWidget()
        self.window_list.setToolTip(
            "Check the windows that should receive the keys.\n"
            "Chrome tabs in the same window are one window - drag a tab out to make it separate.")
        self.window_list.setMinimumHeight(130)
        self._check_list = JUN_mod_checkList_qt_v01(self.window_list)
        self._check_list.checksChanged.connect(lambda _items: self._update_target_count())
        lay.addWidget(self.window_list, 1)

        sel_row = QHBoxLayout()
        for text, state in (("Check All", True), ("Uncheck All", False)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, s=state: self._check_visible(s))
            sel_row.addWidget(b)
        self.target_count_label = QLabel("")
        sel_row.addStretch(1)
        sel_row.addWidget(self.target_count_label)
        lay.addLayout(sel_row)

        meth_row = QHBoxLayout()
        meth_row.addWidget(QLabel("Send Method"))
        self.method_combo = QComboBox()
        self.method_combo.addItem("Background (no focus change)", METHOD_BACKGROUND)
        self.method_combo.addItem("Foreground (bring each window to front)", METHOD_FOREGROUND)
        self.method_combo.setToolTip(
            "Background: posts key messages to each window. Focus is not touched and\n"
            "all checked windows get the key at the same time. Works for browsers and\n"
            "most apps; key combos (Ctrl+...) and some games may ignore it.\n\n"
            "Foreground: brings each window to the front and presses the key like a real\n"
            "keyboard. Works almost everywhere, but focus jumps between the windows.")
        meth_row.addWidget(self.method_combo, 1)
        lay.addLayout(meth_row)
        return box

    def refresh_windows(self):
        checked = set(self.checked_hwnds())
        self.window_list.clear()
        own_pid = os.getpid()
        for w in win32.list_windows(exclude_pids={own_pid}):
            it = QListWidgetItem(w.label())
            it.setData(Qt.UserRole, w.hwnd)
            it.setToolTip("%s\nprocess: %s\nclass: %s\nhwnd: 0x%X"
                          % (w.title, w.process, w.class_name, w.hwnd))
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if w.hwnd in checked else Qt.Unchecked)
            self.window_list.addItem(it)
        self._apply_filter()
        self._update_target_count()

    def _apply_filter(self):
        text = self.filter_edit.text().strip().lower()
        for i in range(self.window_list.count()):
            it = self.window_list.item(i)
            it.setHidden(bool(text) and text not in it.text().lower())

    def _check_visible(self, state):
        items = [self.window_list.item(i) for i in range(self.window_list.count())]
        items = [it for it in items if not it.isHidden()]
        self._check_list.set_checked(items, Qt.Checked if state else Qt.Unchecked)
        self._update_target_count()

    def _checked_items(self):
        items = [self.window_list.item(i) for i in range(self.window_list.count())]
        return [it for it in items if it.checkState() == Qt.Checked]

    def checked_hwnds(self):
        return [it.data(Qt.UserRole) for it in self._checked_items()]

    def _update_target_count(self):
        self.target_count_label.setText("%d checked" % len(self._checked_items()))

    def _update_target_mode(self):
        on = self.rb_selected.isChecked()
        for w in (self.filter_edit, self.refresh_button, self.window_list, self.method_combo):
            w.setEnabled(on)

    # ---------------------------------------------------------- run

    def _build_run_box(self):
        box = QGroupBox("Run")
        grid = QGridLayout(box)

        self.loop_check = QCheckBox("Loop")
        self.loop_check.setToolTip("After the last key, start again from the first key.")
        self.loop_count = QSpinBox()
        self.loop_count.setRange(0, 1000000)
        self.loop_count.setSpecialValueText("Infinite")
        self.loop_count.setPrefix("Times: ")
        self.loop_count.setToolTip("How many times to run the whole sequence (0 = until Stop).")
        self.loop_check.toggled.connect(self.loop_count.setEnabled)
        self.loop_count.setEnabled(False)

        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 3600.0)
        self.delay_spin.setDecimals(1)
        self.delay_spin.setPrefix("Start Delay: ")
        self.delay_spin.setSuffix(" s")
        self.delay_spin.setToolTip("Wait this long after Start before the first press.")

        grid.addWidget(self.loop_check, 0, 0)
        grid.addWidget(self.loop_count, 0, 1)
        grid.addWidget(self.delay_spin, 0, 2)

        self.start_button = QPushButton("Start")
        self.start_button.setMinimumHeight(34)
        self.start_button.clicked.connect(self.start)
        self.stop_button = QPushButton("Stop  (%s)" % STOP_HOTKEY_NAME)
        self.stop_button.setMinimumHeight(34)
        self.stop_button.setToolTip(
            "Stop the run. %s also stops it from any window." % STOP_HOTKEY_NAME)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        grid.addWidget(self.start_button, 1, 0, 1, 2)
        grid.addWidget(self.stop_button, 1, 2)

        self.status_label = QLabel("Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.status_label, 2, 0, 1, 2)
        grid.addWidget(self.pin_button, 2, 2, Qt.AlignRight)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        return box

    def _collect(self):
        return {
            "steps": [s.to_dict() for s in self.get_steps()],
            "loop": self.loop_check.isChecked(),
            "loop_count": self.loop_count.value(),
            "start_delay": self.delay_spin.value(),
            "method": self.method_combo.currentData(),
        }

    def start(self):
        if self._runner and self._runner.is_running():
            return
        if not win32.IS_WINDOWS:
            self.log("[ERROR] Windows 10 / 11 only.")
            return

        steps = self.get_steps()
        errors = validate(steps)
        if errors:
            for _row, msg in errors:
                self.log("[ERROR] " + msg)
            return
        # 표기 정리 ('ctrl+c' -> 'Ctrl+C')
        for r, s in enumerate(steps):
            s.key = keys.normalize(s.key)
            self.table.cellWidget(r, COL_KEY).setText(s.key)

        targets = []
        method = self.method_combo.currentData()
        if self.rb_selected.isChecked():
            items = self._checked_items()
            if not items:
                self.log("[ERROR] No target window checked. Check windows or choose "
                         "'Whatever window is active'.")
                return
            targets = [(it.data(Qt.UserRole), it.text()) for it in items]
            if method == METHOD_BACKGROUND and any(keys.parse_key(s.key)[0] for s in steps):
                self.log("[WARN] Key combos (Ctrl/Shift/Alt+...) often do not work in "
                         "Background mode. Use Foreground if nothing happens.")
        else:
            method = METHOD_FOREGROUND

        self._runner = SequenceRunner(
            steps, targets, method=method,
            loop=self.loop_check.isChecked(), loop_count=self.loop_count.value(),
            start_delay=self.delay_spin.value(),
            on_log=self._bridge.log.emit, on_progress=self._bridge.progress.emit,
            on_finished=self._bridge.finished.emit)

        self.log("[OK] Start - %d step(s), %s, %s" % (
            len(steps),
            "%d window(s)" % len(targets) if targets else "active window",
            "foreground" if method == METHOD_FOREGROUND else "background"))
        for _h, label in targets:
            self.log("    target: %s" % label)
        if not self._runner.hotkey_enabled():
            self.log("[WARN] %s is in the sequence, so the %s stop key is off for this run. "
                     "Use the Stop button." % (STOP_HOTKEY_NAME, STOP_HOTKEY_NAME))
        self._set_running(True)
        self._runner.start()

    def stop(self):
        if self._runner:
            self._runner.stop()

    def _set_running(self, running):
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.table.setEnabled(not running)
        self.window_list.setEnabled(not running and self.rb_selected.isChecked())
        self.rb_selected.setEnabled(not running)
        self.rb_active.setEnabled(not running)
        if running:
            self.status_label.setText("Running")

    def _on_progress(self, text):
        self.status_label.setText(text)

    def _on_finished(self, reason):
        self._set_running(False)
        self.status_label.setText("Idle - " + reason)
        self.log("[OK] " + reason if reason.startswith(("Finished", "Stopped"))
                 else "[WARN] " + reason)

    # ---------------------------------------------------------- presets

    def _reload_presets(self, select=None):
        self.preset_combo.clear()
        names = presets.list_presets()
        self.preset_combo.addItems(names)
        if select in names:
            self.preset_combo.setCurrentText(select)

    def load_preset(self):
        name = self.preset_combo.currentText()
        data = presets.load_preset(name) if name else None
        if not data:
            self.log("[WARN] Could not read preset '%s'." % name)
            return
        self._set_steps([Step.from_dict(d) for d in data.get("steps", [])])
        self.loop_check.setChecked(bool(data.get("loop", False)))
        self.loop_count.setValue(int(data.get("loop_count", 0)))
        self.delay_spin.setValue(float(data.get("start_delay", 0.0)))
        idx = self.method_combo.findData(data.get("method", METHOD_BACKGROUND))
        if idx >= 0:
            self.method_combo.setCurrentIndex(idx)
        self.log("[OK] Preset loaded: %s" % name)

    def save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:",
                                        text=self.preset_combo.currentText())
        name = presets.sanitize_name(name)
        if not ok or not name:
            return
        if name in presets.list_presets():
            ans = QMessageBox.question(self, "Save Preset",
                                       "Preset '%s' exists. Overwrite?" % name)
            if ans != QMessageBox.Yes:
                return
        path = presets.save_preset(name, self._collect())
        self._reload_presets(name)
        self.log("[OK] Preset saved: %s" % path)

    def delete_preset(self):
        name = self.preset_combo.currentText()
        if not name:
            return
        ans = QMessageBox.question(self, "Delete Preset", "Delete preset '%s'?" % name)
        if ans != QMessageBox.Yes:
            return
        if presets.delete_preset(name):
            self.log("[OK] Preset deleted: %s" % name)
        self._reload_presets()

    # ---------------------------------------------------------- misc

    def log(self, text):
        self.log_widget.append(text)

    def toggle_always_on_top(self, enabled):
        """Pin - 플래그를 바꾸면 창이 숨으므로 다시 show() (Qt 규칙)."""
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()

    def closeEvent(self, event):
        # 창을 닫으면 실행도 멈춘다 (데몬 스레드라 프로세스와 함께 끝나지만, 키가 눌린 채
        # 남지 않게 먼저 멈추고 잠깐 기다린다)
        if self._runner and self._runner.is_running():
            self._runner.stop()
            if self._runner._thread:
                self._runner._thread.join(1.0)
        super().closeEvent(event)
