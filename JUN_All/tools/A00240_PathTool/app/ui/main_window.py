# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# A00240_PathTool - main window (Qt, standalone)
#
# 사용자가 만든 카테고리/경로 버튼을 눌러 탐색기로 경로를 여는 툴.
# 탭으로 구성되며(현재 "ShortCut" 1개), 탭은 앞으로 계속 늘어날 예정이라
# QTabWidget 에 addTab 만 추가하면 확장된다.
#
# v01.10 : 메뉴 바(Help 공통 항목) + Shrink 토글.
#   Shrink 는 A00220_BackupTool 의 Shrink 를 따른다. 탭을 감추고 창을
#   **A00220 이 줄었을 때와 같은 350 x 155** 로 줄인다(v01.13 - 전에는 세로 절반 78).
#   줄어든 동안 헤더 행 왼쪽 자리(`anim_area`)에 파일 트리 애니메이션이 재생된다(v01.11)
#   - 계획서: docs/plans/A00240_PathTool_shrink_animation_plan.md
# v01.24 : File > Add to Start Menu (공용 Framework/core/shell_integration, Windows 10 · 11).
# v01.29 : 탭을 QScrollArea 에 담아 창을 자유롭게 줄일 수 있게(A00210 v01.36 과 같은 방식).
#   QTabWidget 의 최소 크기는 안 보이는 페이지까지 포함한 모든 페이지 최소의 최댓값이라(Junction 탭의
#   가로) 창이 그 폭 아래로 줄지 않았다. 여는 크기는 fit_to_content 가 예전과 같게 맞춘다.
# v01.30 : 스크롤 칸을 탭 전체 하나가 아니라 **페이지마다** 둔다. 바깥 하나로 감싸면 창을 좁혀도 탭 위젯이
#   가장 넓은 페이지(Junction) 폭으로 남아 ShortCut 페이지가 좁아지지 않았고(버튼 글자가 잘려 안 보임),
#   페이지마다 두면 각 페이지가 창 폭을 따라 줄다가 자기 최소 폭 아래에서만 가로 스크롤바가 생긴다.

from Framework.qt.qt import (
    Qt,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QTabWidget,
    QIcon,
    QSizePolicy,
    QAction,
    QApplication,
    QMessageBox,
    QScrollArea,
    QFrame,
    QStyle,
    QTimer,
    QGuiApplication,
)
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.pin_style import apply_pin_style
from Framework.core import shell_integration

from ..config.version import VERSION
from ..config.app_meta import (
    icon_path, APP_NAME, APP_USER_MODEL_ID, APP_DESCRIPTION, start_menu_launch_spec)
from .shortcut_tab import ShortcutTab
from .tree_tab import TreeTab
from .junction_tab import JunctionTab
from .file_tree_anim import FileTreeAnimWidget


#: 줄어든 창 크기. A00220_BackupTool · A00370_ToolLauncher 가 줄었을 때와 **같게**.
#: 세로 155 는 A00220 의 green_mid 테마 실측(v01.10 ~ 01.12 는 절반(78)이라 너무 작다는 피드백으로
#: v01.13 에 155 로). 가로는 v01.25 에 350 → 272 - 줄었을 때 Pin 이 Shrunk 아래로 내려가
#: 비는 Pin 칸(72 + 간격 6)만큼 좁혔다(A00370 v01.12 와 같은 모양).
SHRINK_WIDTH = 272
SHRINK_HEIGHT = 155


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

        # Shrink 전 창 크기 (되돌릴 때 쓴다)
        self._full_size = None
        # 첫 show 에 한 번만 fit_to_content (v01.29)
        self._fitted = False

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # 메뉴 바 - 공용 위젯이라 모든 툴과 같은 Help 공통 항목(Copy Tool Name 등)이 저절로 붙는다.
        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        self.menu_bar.addMenu("Help")
        root.setMenuBar(self.menu_bar)

        # File 메뉴 (v01.24) - 시작 메뉴 바로가기. 공용 메뉴 바라 Help 의 **왼쪽**에 끼워진다.
        file_menu = self.menu_bar.addMenu("File")
        self.act_start_menu = QAction("Add to Start Menu", self)
        self.act_start_menu.setToolTip(
            "Create a Start menu shortcut for this tool (and try to pin it to Start).\n"
            "Windows 10 / 11. Click again after moving the tool folder.")
        self.act_start_menu.setEnabled(shell_integration.is_supported())
        self.act_start_menu.triggered.connect(self.add_to_start_menu)
        file_menu.addAction(self.act_start_menu)

        # 상단 헤더 행 : Shrink · Pin(항상 위) 토글.
        # 탭의 코너 위젯 대신 별도 행에 둔다 - 토글로 라벨이 바뀌어도 위치·크기가 흔들리지
        # 않는다(다른 Qt 툴들과 같은 방식).
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other windows")
        # 고정 크기 - "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록(넓은 라벨 기준).
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)
        # 켜진 동안(Pinned) 연한 빨강 - 공용 Framework/qt/pin_style (v01.26).
        apply_pin_style(self.pin_button)

        self.shrink_button = QPushButton("Shrink")
        self.shrink_button.setCheckable(True)
        self.shrink_button.setToolTip(
            "Hide the tabs and make the window small.\n"
            "Press again to bring the tabs back.")
        self.shrink_button.setFixedSize(72, 28)
        self.shrink_button.toggled.connect(self.toggle_shrink)

        # 줄어든 동안만 보이는 자리 - 파일 트리 애니메이션(v01.11).
        # 버튼 행 아래가 아니라 **같은 행의 왼쪽**에 둔다 - 창 높이를 트리가 전부 쓴다
        # (v01.10 의 세로 78px 에선 아래로 두면 20px 뿐이었다, 계획서 2장).
        self.anim_area = FileTreeAnimWidget()
        self.anim_area.setObjectName("A00240_shrink_anim_area")
        # 남는 가로 · 세로를 전부 차지해야 그릴 자리가 나온다(안 그러면 버튼 높이 28px 로 묶인다).
        self.anim_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.anim_area.hide()

        # 버튼 둘은 작은 그리드에 둔다 - 평소엔 한 줄 [Shrink][Pin], 줄었을 때는 Pin 을
        # Shrink 아래 칸으로 옮겨 세로로 쌓는다(v01.25). 그래서 줄었을 때 가로가 한 칸 좁다.
        self.button_grid = QGridLayout()
        self.button_grid.setContentsMargins(0, 0, 0, 0)
        self.button_grid.addWidget(self.shrink_button, 0, 0)
        self.button_grid.addWidget(self.pin_button, 0, 1)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(self.anim_area, 1)
        # 가중치 0 : 평소(anim_area 숨김)에는 버튼을 오른쪽으로 밀고, 줄었을 때는
        # 남는 폭을 anim_area(가중치 1)가 전부 가져간다.
        header_row.addStretch(0)
        header_row.addLayout(self.button_grid)
        header_row.setAlignment(self.button_grid, Qt.AlignTop)
        root.addLayout(header_row)

        self.tabs = QTabWidget()
        # 페이지마다의 스크롤 칸 (v01.30). fit_to_content 가 페이지 최소 크기를 여기서 읽는다.
        self._page_scrolls = []

        # ShortCut 탭. 탭 추가 시 여기에 addTab 한 줄만 더하면 된다.
        self.shortcut_tab = ShortcutTab()
        self.tabs.addTab(self._wrap_page(self.shortcut_tab), "ShortCut")

        # Tree 탭: 입력 경로를 트리뷰로(깊이 제한·파일 토글·확장자 필터·Expand·우클릭 Reveal).
        self.tree_tab = TreeTab()
        self.tabs.addTab(self._wrap_page(self.tree_tab), "Tree")

        # Junction 탭 (v01.19): mklink /J 를 화면에서 - Create / Remove 하위 탭.
        # Create 의 Tree 팝업은 처음 열 때 Tree 탭에 적힌 경로로 시작한다 (v01.23).
        self.junction_tab = JunctionTab(
            tree_path_getter=lambda: self.tree_tab.ipf_path.text())
        self.tabs.addTab(self._wrap_page(self.junction_tab), "Junction")

        root.addWidget(self.tabs, stretch=1)

    def _wrap_page(self, page):
        """탭 페이지를 자기 스크롤 칸에 담는다 (v01.30).

        v01.29 는 탭 위젯 전체를 스크롤 칸 하나에 담았는데, 그러면 창을 좁혀도 탭 위젯이 가장 넓은
        페이지 폭으로 남아 ShortCut 페이지가 좁아지지 않았다. 페이지마다 담으면 QTabWidget 의 최소 크기가
        작아져 창이 자유롭고, 각 페이지는 창 폭을 따라 줄다가 **자기** 최소 폭 아래에서만 가로 스크롤바가
        생긴다. 스크롤 칸에 최소 폭을 걸지 않는다(걸면 그 아래로 못 줄인다 - A00550 v01.04).
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(page)
        self._page_scrolls.append(scroll)
        return scroll

    def _pages_min_size(self):
        """모든 페이지 최소 크기의 축별 최댓값과, 스크롤 칸 자체의 최소 크기 (fit_to_content 용)."""
        width = height = 0
        for scroll in self._page_scrolls:
            hint = scroll.widget().minimumSizeHint()
            width = max(width, hint.width())
            height = max(height, hint.height())
        scroll_min = self._page_scrolls[0].minimumSizeHint() if self._page_scrolls else None
        return width, height, scroll_min

    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        if not self._fitted:
            self._fitted = True
            # 테마가 자식에 입혀진(polish) 뒤에 재야 글자 크기가 맞는다 - 다음 이벤트 루프에서.
            QTimer.singleShot(0, self.fit_to_content)

    def fit_to_content(self):
        """처음 열 때의 크기 = 페이지를 스크롤 칸에 담기 전과 같은 크기(가장 넓은/높은 페이지 최소 + 탭 바 +
        헤더 행 + 여백), 단 모니터 작업 영역을 넘지 않는다. 그 뒤로는 사용자가 가장자리를 끌어 자유롭게 바꾼다
        (v01.29, A00210 v01.36 의 fit_to_content 와 같은 흐름 · v01.30 부터 페이지별 스크롤 칸 기준)."""
        base = self.minimumSizeHint()
        page_w, page_h, scroll_min = self._pages_min_size()
        if scroll_min is None:
            return
        full_w = base.width() - scroll_min.width() + page_w
        full_h = base.height() - scroll_min.height() + page_h

        screen = self.screen() if hasattr(self, "screen") else None
        if screen is None:
            screen = QGuiApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        frame_w = self.frameGeometry().width() - self.geometry().width()
        frame_h = self.frameGeometry().height() - self.geometry().height()
        max_w = avail.width() - max(frame_w, 0)
        max_h = avail.height() - max(frame_h, 0)

        width, height = min(full_w, max_w), min(full_h, max_h)
        # 내용보다 작게 열리면 스크롤바가 생긴다 - 그 폭만큼 넓혀 내용이 가로로 잘리지 않게(높이도 같은 이유).
        bar = self.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        if height < full_h:
            width = min(width + bar, max_w)
        if width < full_w:
            height = min(height + bar, max_h)
        self.resize(width, height)

        frame = self.frameGeometry()
        x = min(max(frame.left(), avail.left()), max(avail.left(), avail.right() - frame.width() + 1))
        y = min(max(frame.top(), avail.top()), max(avail.top(), avail.bottom() - frame.height() + 1))
        if (x, y) != (frame.left(), frame.top()):
            self.move(x, y)

    # ============================================================ start menu

    def _log(self, message):
        """이 창엔 로그창이 없다 - 공용 메뉴 바의 log(로그창이 있으면 거기, 없으면 print)."""
        self.menu_bar.log(message)

    def add_to_start_menu(self):
        """File > Add to Start Menu - 시작 메뉴에 이 툴의 바로가기(.lnk)를 만들고 시작 화면 고정을 시도한다.

        공용 Framework.core.shell_integration (JUN_Video_Tool 과 같은 방식, Windows 10 · 11).
        바로가기 대상은 pythonw.exe + launch.py(콘솔 창 없음) 또는 exe 자신, AppUserModelID 가
        들어가므로 바로가기로 띄운 창도 같은 작업표시줄 버튼 · 툴 아이콘으로 묶인다.
        툴 폴더를 옮겼으면 다시 눌러 경로를 갱신한다. 고정 동사가 없는 OS/빌드에선 수동 고정을 안내한다.
        """
        error = None
        pinned = "unavailable"
        lnk = ""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            lnk = shell_integration.add_to_start_menu(
                APP_NAME, APP_USER_MODEL_ID, start_menu_launch_spec(), APP_DESCRIPTION)
            pinned = shell_integration.pin_shortcut(lnk, "start")
        except shell_integration.ShellIntegrationError as exc:
            error = exc
        finally:
            QApplication.restoreOverrideCursor()

        if error is not None:
            self._log("Could not create the Start menu shortcut: {0}".format(error))
            QMessageBox.warning(
                self, "Start Menu",
                "Could not create the Start menu shortcut:\n{0}".format(error))
            return

        self._log("Start menu shortcut: {0} (pin to Start: {1})".format(lnk, pinned))
        QMessageBox.information(
            self, "Start Menu", shell_integration.start_menu_message(APP_NAME, pinned))

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
        # Pin 버튼 자리: 줄었을 때는 Shrink 아래(1, 0), 평소엔 오른쪽(0, 1).
        self.button_grid.removeWidget(self.pin_button)
        if enabled:
            self._full_size = (self.width(), self.height())
            self.tabs.hide()
            self.menu_bar.hide()
            self.button_grid.addWidget(self.pin_button, 1, 0)
            self.anim_area.show()
        else:
            self.anim_area.stop()
            self.anim_area.hide()
            self.button_grid.addWidget(self.pin_button, 0, 1)
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
