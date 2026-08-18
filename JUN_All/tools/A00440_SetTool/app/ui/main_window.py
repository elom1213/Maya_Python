# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00440_SetTool - Qt UI (in-Maya)
#
# 컴포넌트를 원소로 갖는 세트들끼리 집합론의 기본 연산을 수행한다.
#   Union ( ∪ ) / Intersection ( ∩ ) / Difference ( ∖ )
#   Split ( A ∖ S , A ∩ S )  - 씬 선택으로 세트를 두 조각으로 나눈다
# 창은 마야 메인 윈도우에 parent 되어 뷰포트 위에 뜬다. 모든 UI 문자열/로그는 영어.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenuBar,
    QPlainTextEdit,
    QMessageBox,
    QPushButton,
    Qt,
)
from Framework.qt.maya_window import maya_main_window

from tools.A00440_SetTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00440_SetTool.app.ui.set_tab import SetTab


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00440_SetTool_window"


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Set Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(380, 660)

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Always on Top 토글(우)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        help_menu.addAction("Set Notation").triggered.connect(self.show_notation)

        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        # 공용 로그창. 탭보다 먼저 만들어 넘겨준다.
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(110)

        self.set_tab = SetTab(log_view=self.log_view)
        main_layout.addWidget(self.set_tab, stretch=1)
        main_layout.addWidget(self.log_view)

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
            "Set Tool v{0}\nLast update : {1}\n\n"
            "Set algebra for Maya object sets whose elements are components.".format(
                VERSION, LAST_UPDATE),
        )

    def show_notation(self):
        QMessageBox.information(
            self,
            "Set Notation",
            "Union          A ∪ B   every element of any set\n"
            "Intersection   A ∩ B   elements present in every set\n"
            "Difference     A ∖ B   the first set minus the others\n\n"
            "Split          A = (A ∖ S) ⊔ (A ∩ S)\n"
            "  The two pieces form the partition of A induced by S.\n"
            "  A ∩ S is the trace of S on A.\n"
            "  A ∖ S is the relative complement of S in A.",
        )
