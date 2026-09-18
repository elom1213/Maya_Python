# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00240_PathTool - main window (Qt, standalone)
#
# 사용자가 만든 카테고리/경로 버튼을 눌러 탐색기로 경로를 여는 툴.
# 탭으로 구성되며(현재 "ShortCut" 1개), 탭은 앞으로 계속 늘어날 예정이라
# QTabWidget 에 addTab 만 추가하면 확장된다.
#
# v01.10 : 메뉴 바(Help 공통 항목) + Shrink 토글.
#   Shrink 는 A00220_BackupTool 의 Shrink 를 따른다. 탭을 감추고 창을
#   **A00220 이 줄었을 때의 가로(350) x 세로의 절반(155 / 2 = 78)** 으로 줄인다.
#   줄어든 동안 헤더 행 왼쪽 자리(`anim_area`)에 파일 트리 애니메이션이 재생된다(v01.11)
#   - 계획서: docs/plans/A00240_PathTool_shrink_animation_plan.md

from Framework.qt.qt import (
    Qt,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QIcon,
    QSizePolicy,
)
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01

from ..config.version import VERSION
from ..config.app_meta import icon_path
from .shortcut_tab import ShortcutTab
from .tree_tab import TreeTab
from .file_tree_anim import FileTreeAnimWidget


#: 줄어든 창 크기. A00220_BackupTool 이 줄었을 때 350 x 155 (green_mid 테마 실측)
#: - 가로는 같게, 세로는 절반.
SHRINK_WIDTH = 350
SHRINK_HEIGHT = 78

#: 줄어든 동안의 창 안쪽 여백. 7행 트리를 78px 에 넣으려고 11 -> 2 (한 행 약 10px, 계획서 2장 B 안)
SHRINK_MARGIN = 2


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

        # Shrink 전 창 크기 · 창 여백 (되돌릴 때 쓴다)
        self._full_size = None
        self._full_margins = None

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # 메뉴 바 - 공용 위젯이라 모든 툴과 같은 Help 공통 항목(Copy Tool Name 등)이 저절로 붙는다.
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        self.menu_bar.addMenu("Help")
        root.setMenuBar(self.menu_bar)

        # 상단 헤더 행 : Shrink · Pin(항상 위) 토글.
        # 탭의 코너 위젯 대신 별도 행에 둔다 - 토글로 라벨이 바뀌어도 위치·크기가 흔들리지
        # 않는다(다른 Qt 툴들과 같은 방식).
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other windows")
        # 고정 크기 - "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록(넓은 라벨 기준).
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        self.shrink_button = QPushButton("Shrink")
        self.shrink_button.setCheckable(True)
        self.shrink_button.setToolTip(
            "Hide the tabs and make the window small.\n"
            "Press again to bring the tabs back.")
        self.shrink_button.setFixedSize(72, 28)
        self.shrink_button.toggled.connect(self.toggle_shrink)

        # 줄어든 동안만 보이는 자리 - 파일 트리 애니메이션(v01.11).
        # 세로 78px 창에서 버튼 행 아래로 따로 두면 그릴 높이가 거의 남지 않아서,
        # 버튼과 **같은 행의 왼쪽**에 둔다(계획서 2장).
        self.anim_area = FileTreeAnimWidget()
        self.anim_area.setObjectName("A00240_shrink_anim_area")
        # 남는 가로 · 세로를 전부 차지해야 그릴 자리가 나온다(안 그러면 버튼 높이 28px 로 묶인다).
        self.anim_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.anim_area.hide()

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(self.anim_area, 1)
        # 가중치 0 : 평소(anim_area 숨김)에는 버튼을 오른쪽으로 밀고, 줄었을 때는
        # 남는 폭을 anim_area(가중치 1)가 전부 가져간다.
        header_row.addStretch(0)
        header_row.addWidget(self.shrink_button, 0, Qt.AlignTop)
        header_row.addWidget(self.pin_button, 0, Qt.AlignTop)
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

    def toggle_shrink(self, enabled):
        """Shrink 토글 - 탭과 메뉴 바를 감추고 창을 SHRINK_WIDTH x SHRINK_HEIGHT 로.

        A00220 과 같은 순서다: 감추기 -> 레이아웃 최소 크기 다시 계산 -> resize.
        (다시 계산하지 않으면 옛 최소 크기에 막혀 창이 줄지 않는다.)
        되돌릴 때는 줄이기 전 크기(가로 · 세로 둘 다)로 돌아간다.
        """
        root = self.layout()
        if enabled:
            self._full_size = (self.width(), self.height())
            self._full_margins = root.contentsMargins()
            root.setContentsMargins(SHRINK_MARGIN, SHRINK_MARGIN,
                                    SHRINK_MARGIN, SHRINK_MARGIN)
            self.tabs.hide()
            self.menu_bar.hide()
            self.anim_area.show()
        else:
            self.anim_area.stop()
            self.anim_area.hide()
            if self._full_margins is not None:
                root.setContentsMargins(self._full_margins)
            self.menu_bar.show()
            self.tabs.show()

        self.shrink_button.setText("Shrunk" if enabled else "Shrink")

        root.invalidate()
        root.activate()
        if enabled:
            self.resize(SHRINK_WIDTH, SHRINK_HEIGHT)
            # 켤 때마다 처음부터 - 파일 0 만 보이다가 0.5 초 간격으로 자란다.
            self.anim_area.start()
        elif self._full_size:
            self.resize(*self._full_size)
