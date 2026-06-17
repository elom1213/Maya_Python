# -*- coding: utf-8 -*-
"""
Connect Closest Tool - PySide(Qt) UI.

A00020_move_skineWeightTool 의 좌/우 2-리스트 UI 개념을 PySide 로 재구성한다.
왼쪽 리스트 = Driven, 오른쪽 리스트 = Driver. Connect 를 누르면 각 driver 에 대해
가장 가까운 driven 을 1:1 로 매칭해 constraint 로 연결한다.

로직은 app/core 에 위임하고 이 모듈은 위젯 구성과 시그널 연결, 로그 출력만 담당한다.
모든 UI 문자열(버튼/체크박스/로그)은 영어.
"""

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt

from tools.A00140_ConnectClosest.app.config.version import VERSION, LAST_UPDATE
from tools.A00140_ConnectClosest.app.core import (
    CONSTRAINT_TYPES,
    connect_closest,
)


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())

        self.setWindowTitle("Connect Closest Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(520, 640)

        self._build_ui()
        self._connect_signals()

    # ================================================================
    # UI 구성
    # ================================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        # 메뉴 바 (Help > About) — A00110_animTool 의 QMenuBar 패턴.
        # QWidget 이므로 setMenuBar 로 레이아웃 상단에 붙인다.
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        root.addWidget(self._build_list_group())
        root.addWidget(self._build_option_group())
        root.addWidget(self._build_connect_button())
        root.addWidget(self._build_log_group(), stretch=1)

        footer = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

    def _build_list_group(self):
        group = QGroupBox("Set Up")
        layout = QHBoxLayout(group)

        # 재사용 PySide tsl 위젯(Framework.qt.MOD_tsl_qt_v01). 왼쪽=Driven, 오른쪽=Driver.
        # Select/Add/Del/Up/Down/Sort 버튼과 씬 선택 연동은 위젯이 자체 처리한다.
        self.driven_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Driven")
        self.driver_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(title="Driver")

        layout.addWidget(self.driven_tsl)
        layout.addWidget(self.driver_tsl)

        return group

    def _build_option_group(self):
        group = QGroupBox("Constraint Type")
        layout = QVBoxLayout(group)

        # constraint 체크박스 (다중 선택). CONSTRAINT_TYPES 순서/라벨과 1:1.
        cb_row = QHBoxLayout()
        self.constraint_checkboxes = {}
        for key, label, _method in CONSTRAINT_TYPES:
            cb = QCheckBox(label)
            self.constraint_checkboxes[key] = cb
            cb_row.addWidget(cb)
        # 기본값: Parent 체크
        self.constraint_checkboxes["parent"].setChecked(True)
        layout.addLayout(cb_row)

        # maintain offset 옵션
        self.cb_maintain_offset = QCheckBox("Maintain Offset")
        self.cb_maintain_offset.setChecked(True)
        layout.addWidget(self.cb_maintain_offset)

        return group

    def _build_connect_button(self):
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setMinimumHeight(32)
        return self.btn_connect

    def _build_log_group(self):
        group = QGroupBox("Log")
        layout = QVBoxLayout(group)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        return group

    def _connect_signals(self):
        # 리스트 위젯(Select/Add/Del/Up/Down/Sort, 씬 선택)은 자체 처리하므로
        # 여기서는 Connect 버튼만 연결한다.
        self.btn_connect.clicked.connect(self.on_connect)

    # ================================================================
    # helpers
    # ================================================================

    def _log(self, message):
        self.log_view.appendPlainText(message)

    # ================================================================
    # 슬롯 : Connect
    # ================================================================

    def _checked_constraint_keys(self):
        return [key for key, cb in self.constraint_checkboxes.items()
                if cb.isChecked()]

    def on_connect(self):
        drivers = self.driver_tsl.get_all_items()
        drivens = self.driven_tsl.get_all_items()
        constraint_keys = self._checked_constraint_keys()
        maintain_offset = self.cb_maintain_offset.isChecked()

        self._log("--- Connect Closest ---")

        results, errors = connect_closest(
            drivers, drivens, constraint_keys, maintain_offset)

        for err in errors:
            self._log("[WARN] {0}".format(err))

        for r in results:
            self._log(
                "Connected: {driver} -> {driven} "
                "(dist {dist:.3f}, {cons})".format(
                    driver=r["driver"],
                    driven=r["driven"],
                    dist=r["distance"],
                    cons=", ".join(r["constraints"]),
                )
            )

        self._log("Done. {0} connection(s) made.".format(len(results)))

    # ================================================================
    # 슬롯 : Help > About
    # A00110_animTool 의 show_about(QMessageBox) 패턴.
    # ================================================================

    def show_about(self, *args):
        message = (
            "Connect Closest Tool v{version}\n"
            "Update date: {update}\n"
            "\n"
            "For each driver, finds the closest driven object (1:1 matching)\n"
            "and connects them with constraints so the driven follows the driver.\n"
            "\n"
            "How to use:\n"
            "1. Add driven objects to the left list (Driven).\n"
            "2. Add driver objects to the right list (Driver).\n"
            "3. Check one or more constraint types (Parent / Point / Orient / Scale).\n"
            "4. Toggle Maintain Offset if needed.\n"
            "5. Press Connect. Results are shown in the Log panel.\n"
            "\n"
            "Note: matching is 1:1 - each driven is used by only one driver.\n"
            "\n"
            "Written by Ji Hun Park."
        ).format(version=VERSION, update=LAST_UPDATE)

        QMessageBox.information(self, "About", message)
