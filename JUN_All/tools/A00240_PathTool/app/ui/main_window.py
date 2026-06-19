# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00240_PathTool - main window (Qt, standalone)
#
# 사용자가 만든 카테고리/경로 버튼을 눌러 탐색기로 경로를 여는 툴.
# 탭으로 구성되며(현재 "ShortCut" 1개), 탭은 앞으로 계속 늘어날 예정이라
# QTabWidget 에 addTab 만 추가하면 확장된다.

from Framework.qt.qt import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from ..config.version import VERSION
from .shortcut_tab import ShortcutTab


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"JUN Path Tool  v{VERSION}")
        self.resize(360, 560)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        self.tabs = QTabWidget()

        # ShortCut 탭(현재 유일). 탭 추가 시 여기에 addTab 한 줄만 더하면 된다.
        self.shortcut_tab = ShortcutTab()
        self.tabs.addTab(self.shortcut_tab, "ShortCut")

        root.addWidget(self.tabs)
