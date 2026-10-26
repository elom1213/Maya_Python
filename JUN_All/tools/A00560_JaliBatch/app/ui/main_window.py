# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - main window (Qt, standalone)
#
# VisemeNet Converter 출력 폴더(22열 txt + json + wav, N 개) -> JALI 컨트롤러를 레퍼런스하고 키를 베이크한 클립 .mb N 개.
# 마야 일은 mayapy 워커(app/maya/worker.py)가 한 프로세스에서 순서대로 - 공용 Framework/qt/MOD_mayapyProcess_qt_v01.
#   - 헤더 행 Shrink · Pin : A00210 · A00220 · A00240 · A00370 과 같은 자리 · 크기 (줄이면 272 x 155, Pin 은 Shrunk 아래)
#   - File > Add to Start Menu : 공용 Framework/core/shell_integration (Windows 10 · 11)
#   - mayapy 줄은 두 탭이 같이 쓰므로 탭 위에 둔다. 탭은 페이지별 QScrollArea 라 창을 자유롭게 줄일 수 있다.
#   - Batch 탭 : 생성 (app/ui/batch_tab.py)   Validate 탭 : 점검 · Repath (app/ui/validate_tab.py)
# 모든 UI 문자열 · 로그는 영어. 계획: docs/plans/A00560_JaliBatch_plan.md, 안내: docs/A00560_JaliBatch.md

import os

from Framework.qt.qt import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QScrollArea, QFrame, QStyle, QGuiApplication, QApplication, QAction, QIcon, QTimer, Qt,
)
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt import MOD_mayapyProcess_qt_v01 as mayapy_process
from Framework.qt.pin_style import apply_pin_style
from Framework.core import shell_integration, mayapy_runner, file_opener

from ..config.version import VERSION, LAST_UPDATE
from ..config.app_meta import (icon_path, APP_NAME, APP_USER_MODEL_ID, APP_DESCRIPTION, start_menu_launch_spec,
                               worker_path, guide_doc)
from ..core import prefs as prefs_mod
from .batch_tab import BatchTab
from .validate_tab import ValidateTab

WINDOW_OBJECT_NAME = "JUN_A00560_JaliBatch_window"
SHRINK_WIDTH, SHRINK_HEIGHT = 272, 155
MAYAPY_FILTER = "mayapy (mayapy.exe);;All files (*.*)"
TOOL_TAG = "A00560_JaliBatch {0}".format(VERSION)


class MainWindow(QWidget):

    def __init__(self, run_job_func=None):
        super().__init__()
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("JUN JALI Batch  v{0}".format(VERSION))
        self.resize(960, 720)
        _icon = icon_path()
        if _icon:
            self.setWindowIcon(QIcon(_icon))

        # 시험에서 가짜 워커로 바꿔 끼울 수 있게 함수로 둔다 (기본 = 공용 QProcess 러너)
        self.run_job_func = run_job_func or mayapy_process.run_job
        self._prefs = prefs_mod.load()
        self._full_size = None
        self._fitted = False

        self._build_ui()
        self._load_prefs_to_ui()
        self.log("[INFO] Pick the VisemeNet Converter output folder (Source) and the JALI controller, then Scan.")

    # ============================================================== build

    def _build_ui(self):
        root = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        file_menu = self.menu_bar.addMenu("File")
        self.act_start_menu = QAction("Add to Start Menu", self)
        self.act_start_menu.setToolTip("Create a Start menu shortcut for this tool (and try to pin it to Start).\n"
                                       "Windows 10 / 11. Click again after moving the tool folder.")
        self.act_start_menu.setEnabled(shell_integration.is_supported())
        self.act_start_menu.triggered.connect(self.add_to_start_menu)
        file_menu.addAction(self.act_start_menu)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Open Guide", self.on_open_guide)
        help_menu.addAction("About", self.show_about)
        root.setMenuBar(self.menu_bar)

        # 헤더 행 : Shrink · Pin
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)
        apply_pin_style(self.pin_button)
        self.shrink_button = QPushButton("Shrink")
        self.shrink_button.setCheckable(True)
        self.shrink_button.setToolTip("Hide the tabs and the log and make the window small.\nPress again to bring them back.")
        self.shrink_button.setFixedSize(72, 28)
        self.shrink_button.toggled.connect(self.toggle_shrink)
        self.button_grid = QGridLayout()
        self.button_grid.setContentsMargins(0, 0, 0, 0)
        self.button_grid.addWidget(self.shrink_button, 0, 0)
        self.button_grid.addWidget(self.pin_button, 0, 1)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addStretch(1)
        header_row.addLayout(self.button_grid)
        header_row.setAlignment(self.button_grid, Qt.AlignTop)
        root.addLayout(header_row)

        # mayapy 줄 (두 탭 공용)
        self.mayapy_row = QWidget()
        mrow = QHBoxLayout(self.mayapy_row)
        mrow.setContentsMargins(0, 0, 0, 0)
        mrow.addWidget(QLabel("mayapy"))
        self.le_mayapy = QLineEdit()
        self.le_mayapy.setPlaceholderText("auto: Program Files\\Autodesk\\Maya*\\bin\\mayapy.exe (newest)")
        self.le_mayapy.setToolTip("mayapy.exe that generates / validates the clips. Empty = newest Maya found under Program Files.")
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(32)
        btn_browse.clicked.connect(self.on_browse_mayapy)
        btn_detect = QPushButton("Detect")
        btn_detect.clicked.connect(self.on_detect_mayapy)
        mrow.addWidget(self.le_mayapy, 1)
        mrow.addWidget(btn_browse)
        mrow.addWidget(btn_detect)
        root.addWidget(self.mayapy_row)

        # 로그는 탭보다 먼저 (탭이 self.log 를 받는다)
        self.log_widget = JUN_mod_log_qt_v01(window_title="JALI Batch - Log", object_name="JUN_A00560_JaliBatch_log_window")
        self.log_widget.setMaximumHeight(140)

        self.tabs = QTabWidget()
        self.batch_tab = BatchTab(log=self.log, run_worker=self.run_worker, prefs=self._prefs)
        self.validate_tab = ValidateTab(log=self.log, run_worker=self.run_worker, prefs=self._prefs)
        self.tabs.addTab(self._wrap_page(self.batch_tab), "Batch")
        self.tabs.addTab(self._wrap_page(self.validate_tab), "Validate")
        self.tabs.setTabToolTip(0, "VisemeNet output folder -> one clip .mb per wav (controller referenced, keys baked)")
        self.tabs.setTabToolTip(1, "Open every clip in mayapy and check controller path, failed edits, baked keys, stamp")
        self.batch_tab.generated.connect(self.validate_tab.set_folder)
        root.addWidget(self.tabs, stretch=1)
        root.addWidget(self.log_widget)

    @staticmethod
    def _wrap_page(page):
        """페이지마다 QScrollArea - 창을 내용보다 작게 줄일 수 있고(스크롤바), 탭 최소 크기가 숨은 페이지에 묶이지 않는다."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(page)
        return scroll

    # ============================================================== log · prefs

    def log(self, message):
        self.log_widget.appendPlainText(message)

    def _load_prefs_to_ui(self):
        self.le_mayapy.setText(self._prefs.get("mayapy_path", ""))
        self.batch_tab.load_prefs(self._prefs)
        self.validate_tab.load_prefs(self._prefs)

    def collect_prefs(self):
        self._prefs["mayapy_path"] = self.le_mayapy.text().strip()
        self.batch_tab.save_prefs(self._prefs)
        self.validate_tab.save_prefs(self._prefs)
        return self._prefs

    def save_prefs(self):
        prefs_mod.save(self.collect_prefs())

    def closeEvent(self, event):
        self.save_prefs()
        super().closeEvent(event)

    # ============================================================== mayapy

    def mayapy_path(self):
        return mayapy_runner.find_mayapy(self.le_mayapy.text().strip())

    def require_mayapy(self):
        path = self.mayapy_path()
        if not path:
            self.log("[ERROR] mayapy.exe not found - set it in the mayapy field (Browse / Detect).")
        return path

    def on_browse_mayapy(self, *args):
        start = os.path.dirname(self.le_mayapy.text().strip()) or r"C:\Program Files\Autodesk"
        path, _ = QFileDialog.getOpenFileName(self, "Select mayapy.exe", start, MAYAPY_FILTER)
        if path:
            self.le_mayapy.setText(os.path.normpath(path))
            self.save_prefs()

    def on_detect_mayapy(self, *args):
        found = mayapy_runner.candidates()
        if not found:
            self.log("[WARN] No mayapy.exe found under Program Files\\Autodesk. Use Browse...")
            return
        self.le_mayapy.setText(found[0])
        self.save_prefs()
        self.log("mayapy : {0}{1}".format(found[0], "" if len(found) == 1 else "  (+{0} more)".format(len(found) - 1)))

    def run_worker(self, job, title):
        """탭이 부른다. mayapy 워커를 돌리고 JobOutcome(result · error · cancelled)을 돌려준다. mayapy 가 없으면 None."""
        mayapy = self.require_mayapy()
        if not mayapy:
            return None
        self.save_prefs()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            return self.run_job_func(self, mayapy, job, worker_path(), title=title, message="Starting mayapy...",
                                     log=self.log, job_prefix="jun_jalibatch")
        finally:
            QApplication.restoreOverrideCursor()

    # ============================================================== Pin / Shrink / Start menu

    def add_to_start_menu(self):
        error, pinned, lnk = None, "unavailable", ""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            lnk = shell_integration.add_to_start_menu(APP_NAME, APP_USER_MODEL_ID, start_menu_launch_spec(), APP_DESCRIPTION)
            pinned = shell_integration.pin_shortcut(lnk, "start")
        except shell_integration.ShellIntegrationError as exc:
            error = exc
        finally:
            QApplication.restoreOverrideCursor()
        if error is not None:
            self.log("[WARN] Could not create the Start menu shortcut: {0}".format(error))
            QMessageBox.warning(self, "Start Menu", "Could not create the Start menu shortcut:\n{0}".format(error))
            return
        self.log("[OK] Start menu shortcut: {0} (pin to Start: {1})".format(lnk, pinned))
        QMessageBox.information(self, "Start Menu", shell_integration.start_menu_message(APP_NAME, pinned))

    def toggle_always_on_top(self, enabled):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()
        self.log("Always on Top: {0}".format("ON" if enabled else "OFF"))

    def toggle_shrink(self, enabled):
        root = self.layout()
        self.button_grid.removeWidget(self.pin_button)
        if enabled:
            self._full_size = (self.width(), self.height())
            self.menu_bar.hide()
            self.mayapy_row.hide()
            self.tabs.hide()
            self.log_widget.hide()
            self.button_grid.addWidget(self.pin_button, 1, 0)
        else:
            self.button_grid.addWidget(self.pin_button, 0, 1)
            self.menu_bar.show()
            self.mayapy_row.show()
            self.tabs.show()
            self.log_widget.show()
        self.shrink_button.setText("Shrunk" if enabled else "Shrink")
        root.invalidate()
        root.activate()
        if enabled:
            self.resize(SHRINK_WIDTH, SHRINK_HEIGHT)
        elif self._full_size:
            self.resize(*self._full_size)
        self.log("Shrink: {0}".format("ON" if enabled else "OFF"))

    # ============================================================== 창 크기

    def showEvent(self, event):
        super().showEvent(event)
        if not self._fitted:
            self._fitted = True
            QTimer.singleShot(0, self.fit_to_content)

    def fit_to_content(self):
        """처음 열 때 내용 크기(모니터 작업 영역까지), 그 뒤는 자유 크기 (A00210 v01.36 · A00240 v01.30 방식)."""
        pages = [self.batch_tab, self.validate_tab]
        content_w = max(p.minimumSizeHint().width() for p in pages) + self.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        content_h = max(p.minimumSizeHint().height() for p in pages) + self.tabs.tabBar().sizeHint().height()
        base = self.minimumSizeHint()
        tabs_min = self.tabs.minimumSizeHint()
        full_w = max(base.width() - tabs_min.width() + content_w, 820)
        full_h = base.height() - tabs_min.height() + content_h
        screen = self.screen() if hasattr(self, "screen") else None
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        frame_w = self.frameGeometry().width() - self.geometry().width()
        frame_h = self.frameGeometry().height() - self.geometry().height()
        width = min(full_w, avail.width() - max(frame_w, 0))
        height = min(full_h, avail.height() - max(frame_h, 0))
        self.resize(width, height)

    # ============================================================== Help

    def on_open_guide(self, *args):
        doc = guide_doc()
        try:
            file_opener.open_path(doc)
        except (OSError, ValueError):
            self.log("[WARN] Guide not found: {0}".format(doc))

    def show_about(self, *args):
        QMessageBox.information(self, "About", (
            "JUN JALI Batch v{0}\nUpdate date: {1}\n\n"
            "Turns a VisemeNet Converter output folder (txt + json + wav per line)\n"
            "into one Maya clip .mb per line: the JALI slider controller rig is\n"
            "referenced (namespace JALI), the viseme keys are baked onto the\n"
            "controllers, the wav becomes a sound node, and a stamp + manifest\n"
            "record how each clip was made.\n\n"
            "Batch    : Source folder + Controller -> Scan -> check clips -> Run\n"
            "           (one mayapy process, cancel at clip boundaries).\n"
            "Validate : open every clip in mayapy and check it; Repath switches\n"
            "           the controller file.\n"
            "Review the clips with A00570_JaliReview inside Maya.\n\n"
            "Written by Ji Hun Park.").format(VERSION, LAST_UPDATE))
