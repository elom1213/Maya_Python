# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00240_PathTool - main window (Qt, standalone)
#
# 사용자가 만든 카테고리/경로 버튼을 눌러 탐색기로 경로를 여는 툴.
# 탭으로 구성되며(현재 "ShortCut" 1개), 탭은 앞으로 계속 늘어날 예정이라
# QTabWidget 에 addTab 만 추가하면 확장된다.

from Framework.qt.qt import (
    Qt,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QIcon,
)

from ..config.version import VERSION
from ..config.app_meta import icon_path
from .shortcut_tab import ShortcutTab
from .tree_tab import TreeTab


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"JUN Path Tool  v{VERSION}")
        self.resize(360, 560)

        # 창/작업표시줄 아이콘. launch.py 가 app 전역으로도 설정하지만, 다른 진입점으로
        # 이 창을 직접 띄우는 경우까지 대비해 창 자체에도 지정한다(없으면 조용히 무시).
        _sIcon = icon_path()
        if _sIcon:
            self.setWindowIcon(QIcon(_sIcon))

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # 상단 헤더 행 : Pin(항상 위) 토글.
        # 탭의 코너 위젯 대신 별도 행에 둔다 - 토글로 라벨이 바뀌어도 위치·크기가 흔들리지
        # 않는다(다른 Qt 툴들과 같은 방식).
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other windows")
        # 고정 크기 - "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록(넓은 라벨 기준).
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addStretch(1)
        header_row.addWidget(self.pin_button)
        root.addLayout(header_row)

        self.tabs = QTabWidget()

        # ShortCut 탭. 탭 추가 시 여기에 addTab 한 줄만 더하면 된다.
        self.shortcut_tab = ShortcutTab()
        self.tabs.addTab(self.shortcut_tab, "ShortCut")

        # Tree 탭: 입력 경로를 트리뷰로(깊이 제한·파일 토글·확장자 필터·Expand·우클릭 Reveal).
        self.tree_tab = TreeTab()
        self.tabs.addTab(self.tree_tab, "Tree")

        root.addWidget(self.tabs)

    # ------------------------------------------------------------------

    def toggle_always_on_top(self, enabled):
        """Pin - 이 창을 다른 창 위에 고정한다.

        플래그를 바꾸면 창이 숨으므로 **반드시 다시 show()** 한다(Qt 규칙).
        standalone 앱이라 마야 창이 아니라 OS 의 다른 창들 위에 선다.
        """
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()
