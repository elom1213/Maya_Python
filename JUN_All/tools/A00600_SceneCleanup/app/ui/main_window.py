# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00600_SceneCleanup - Qt UI (in-Maya)
#
# 체크 목록(cleanup_items.ITEMS 그대로) + Check All / Uncheck All + Run Cleanup + 로그.
# 창을 열 때마다 항목은 item.default(전부 True) 로 체크된다 - 상태를 기억하지 않는다(요구: 기본 모두 체크).
# 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    Qt,
)
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_checkList_qt_v01 import JUN_mod_checkList_qt_v01
from Framework.qt.pin_style import apply_pin_style

from tools.A00600_SceneCleanup.app.config.version import VERSION, LAST_UPDATE
from tools.A00600_SceneCleanup.app.core import cleanup_items
from tools.A00600_SceneCleanup.app.core import cleanup_runner


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00600_SceneCleanup_window"

_KEY_ROLE = Qt.UserRole


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("Scene Cleanup v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(420, 460)

        # 확인 창 - 테스트에서 끌 수 있게 속성으로
        self.confirm_before_run = True

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Pin(우)
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)

        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)
        apply_pin_style(self.pin_button)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        main_layout.addWidget(QLabel("Cleanup Items"))

        # 항목 체크 목록 - ITEMS 에서 만든다(새 항목은 UI 수정 없이 생긴다)
        self.lw_items = QListWidget()
        for item in cleanup_items.ITEMS:
            row = QListWidgetItem(item.label)
            row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
            row.setCheckState(Qt.Checked if item.default else Qt.Unchecked)
            row.setToolTip(item.tooltip)
            row.setData(_KEY_ROLE, item.key)
            self.lw_items.addItem(row)
        self.chk_items = JUN_mod_checkList_qt_v01(self.lw_items)
        main_layout.addWidget(self.lw_items, stretch=1)

        check_row = QHBoxLayout()
        self.btn_check_all = QPushButton("Check All")
        self.btn_check_all.clicked.connect(lambda: self.set_all_checked(True))
        self.btn_uncheck_all = QPushButton("Uncheck All")
        self.btn_uncheck_all.clicked.connect(lambda: self.set_all_checked(False))
        check_row.addWidget(self.btn_check_all)
        check_row.addWidget(self.btn_uncheck_all)
        main_layout.addLayout(check_row)

        self.btn_run = QPushButton("Run Cleanup")
        self.btn_run.setMinimumHeight(34)
        self.btn_run.setToolTip("Run the checked items on the open scene, top to bottom.\n"
                                "One Ctrl+Z undoes the whole cleanup.")
        self.btn_run.clicked.connect(self.run_cleanup)
        main_layout.addWidget(self.btn_run)

        # 공용 로그 위젯(Expand / Clear / Copy)
        self.log_view = JUN_mod_log_qt_v01(
            window_title="Scene Cleanup - Log",
            object_name="JUN_A00600_SceneCleanup_log_window")
        self.log_view.setMinimumHeight(160)
        main_layout.addWidget(self.log_view, stretch=1)

    # ==================================================================
    # 항목
    # ==================================================================

    def set_all_checked(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.lw_items.count()):
            self.lw_items.item(i).setCheckState(state)

    def checked_items(self):
        """체크한 항목을 ITEMS 순서대로."""
        keys = set()
        for i in range(self.lw_items.count()):
            row = self.lw_items.item(i)
            if row.checkState() == Qt.Checked:
                keys.add(row.data(_KEY_ROLE))
        return [item for item in cleanup_items.ITEMS if item.key in keys]

    def log(self, msg):
        self.log_view.appendPlainText(msg)

    # ==================================================================
    # 실행
    # ==================================================================

    def run_cleanup(self):
        items = self.checked_items()
        if not items:
            self.log("[WARN] Nothing checked - check at least one item.")
            return
        if self.confirm_before_run:
            answer = QMessageBox.question(
                self,
                "Run Cleanup",
                "Run these cleanup items on the open scene?\n\n  - {0}\n\n"
                "One Ctrl+Z undoes the whole cleanup.".format("\n  - ".join(i.label for i in items)),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer != QMessageBox.Yes:
                self.log("Cancelled.")
                return
        self.log("--- Scene Cleanup ({0} item(s)) ---".format(len(items)))
        return cleanup_runner.run_items(items, log=self.log)

    # ==================================================================
    # 창 동작
    # ==================================================================

    def toggle_always_on_top(self, checked):
        """Qt 창 플래그를 바꾸면 창이 숨겨지므로 다시 show() 한다."""
        self.pin_button.setText("Pinned" if checked else "Pin")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Scene Cleanup v{0}\nLast update : {1}\n\n"
            "Clean the open scene with the checked items, top to bottom.\n"
            "Every item is checked when the window opens.\n"
            "One Ctrl+Z undoes the whole cleanup.\n\n{2}".format(
                VERSION, LAST_UPDATE,
                "\n".join("- {0}".format(i.label) for i in cleanup_items.ITEMS)),
        )
