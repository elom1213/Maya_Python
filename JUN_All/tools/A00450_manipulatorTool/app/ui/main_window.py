# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00450_manipulatorTool - Qt UI (in-Maya)
#
# 이동/회전/스케일 매니퓰레이터의 축(빨강/파랑/초록) 굵기를 슬라이더로 라이브 조절하고,
# Reset 으로 원래 굵기로 되돌린다.
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

from tools.A00450_manipulatorTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00450_manipulatorTool.app.ui.manip_tab import ManipTab


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00450_manipulatorTool_window"


class MainWindow(QWidget):

    def __init__(self):

        super(MainWindow, self).__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.setWindowTitle("Manipulator Tool v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(400, 620)

        self.build_ui()

    def build_ui(self):

        main_layout = QVBoxLayout(self)

        # 상단 헤더 행 : 메뉴 바(좌) + Always on Top 토글(우)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        help_menu.addAction("How it works").triggered.connect(self.show_how_it_works)

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
        self.log_view.setFixedHeight(90)

        self.manip_tab = ManipTab(log_view=self.log_view)
        main_layout.addWidget(self.manip_tab, stretch=1)
        main_layout.addWidget(self.log_view)

    # ==================================================================
    # 창 동작
    # ==================================================================

    def toggle_always_on_top(self, checked):
        """Qt 창 플래그를 바꾸면 창이 숨겨지므로 다시 show() 한다."""
        self.pin_button.setText("Pinned" if checked else "Pin")

        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def closeEvent(self, event):
        """창이 닫히면 도구 감시 scriptJob 을 끊는다. 굵기 값은 그대로 둔다."""
        try:
            self.manip_tab.shutdown()
        except Exception:
            pass

        super(MainWindow, self).closeEvent(event)

    # ==================================================================
    # Help
    # ==================================================================

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Manipulator Tool v{0}\nLast update : {1}\n\n"
            "Live control over the thickness and pick radius of the Move, Rotate "
            "and Scale manipulator axes.".format(VERSION, LAST_UPDATE),
        )

    def show_how_it_works(self):
        QMessageBox.information(
            self,
            "How it works",
            "Maya exposes only one global manipulator setting (manipOptions),\n"
            "so Move / Rotate / Scale cannot really hold different thicknesses.\n\n"
            "This tool remembers a value per tool and pushes it to Maya the moment\n"
            "you switch to that tool. The active tool is marked with an arrow.\n\n"
            "Thickness  : how thick the axis is drawn (minimum 1.0, Maya clamps below that)\n"
            "Pick Radius: how far from the axis a click still grabs it\n"
            "Handle Size: size of the arrow heads / boxes at the axis ends\n"
            "Manip Scale: overall size of the whole manipulator\n\n"
            "Reset        restores the values this window started with.\n"
            "Maya Default restores 2.0 / 4.0 / 30.0 / 1.0.",
        )
