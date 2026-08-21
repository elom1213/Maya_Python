# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-06
# A00110_animTool_V02 - Qt UI

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_collapsible_qt
from Framework.qt import JUN_mod_timeRange_qt
from Framework.qt import JUN_mod_filter_qt
from Framework.qt import JUN_mod_expand_qt
from Framework.qt.maya_window import maya_main_window
from Framework.core.maya_refresh import force_refresh

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00110_animTool_V02.app.config.version import VERSION, LAST_UPDATE
from tools.A00110_animTool_V02.app.core import KeyframeManager
from tools.A00110_animTool_V02.app.core import HotkeyManager
from tools.A00110_animTool_V02.app.core import PoseKeyManager
from tools.A00110_animTool_V02.app.core import CopyKeyManager
from tools.A00110_animTool_V02.app.core import MirrorKeyManager
from tools.A00110_animTool_V02.app.core import MirrorTokenStore
from tools.A00110_animTool_V02.app.core import BakeManager
from tools.A00110_animTool_V02.app.core import FollowMatchManager
from tools.A00110_animTool_V02.app.core import OffsetHoldManager
from tools.A00110_animTool_V02.app.core import StaggerOffsetSession
from tools.A00110_animTool_V02.app.core import EulerFilterManager
from tools.A00110_animTool_V02.app.core import GraphViewManager
from tools.A00110_animTool_V02.app.core import GraphFocusManager
from tools.A00110_animTool_V02.app.core import FillKeyManager
from tools.A00110_animTool_V02.app.core import CURRENT_LAYER
from tools.A00110_animTool_V02.app.core import CurveFilterSession
from tools.A00110_animTool_V02.app.core import (
    CF_EASE_IN, CF_EASE_OUT, CF_LINEAR, CF_EASE_IN_OUT,
    cf_selected_channel_attrs,
)
from tools.A00110_animTool_V02.app.core import NoiseNodeManager, NoiseSession
from tools.A00110_animTool_V02.app.core import noise_generator as noise_gen


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00110_animTool_V02_window"

# Curve > Filters 를 따로 띄우는 창(Expand)의 objectName.
# 창 자체는 공용 위젯(Framework.qt JUN_mod_expand_qt)이 만든다.
CURVE_FILTERS_WINDOW_OBJECT_NAME = "JUN_A00110_animTool_V02_curveFilters_window"


# Stagger Offset 슬라이더가 담당하는 프레임 범위(±). 더 큰 값은 옆 스핀박스로 넣는다.
STAGGER_SLIDER_RANGE = 60

# 값(value) 오프셋 슬라이더: QSlider 는 정수만 다루므로 SCALE 배로 담는다(0.01 해상도).
# 담당 범위는 ±STAGGER_VALUE_SLIDER_STEPS/SCALE = ±10.0, 그보다 큰 값은 스핀박스로 넣는다.
STAGGER_VALUE_SLIDER_SCALE = 100
STAGGER_VALUE_SLIDER_STEPS = 1000

# 슬라이더/스핀박스 조작이 이만큼 멎으면 그때까지의 미리보기를 undo 큐에 '한 항목' 으로
# 기록한다. 드래그 중에는 기록하지 않아 undo 항목이 수백 개 쌓이는 걸 막는다.
STAGGER_SETTLE_MS = 350


# ---- Create > Noise ----------------------------------------------------------
# 슬라이더는 정수만 다루므로 SCALE 배로 담는다. 요청상 Smoothness/Offset 에는 최소·최대가
# 없어야 하므로, **슬라이더는 '자주 쓰는 구간' 만 담당**하고 그 밖의 값은 옆 스핀박스로 넣는다
# (Stagger 와 같은 구성).
#   Smoothness: ±3.0 (0.01 해상도). 실효 구간이 대략 -1 ~ +2 라 이 정도면 충분하다.
#   Offset    : ±500 프레임 (0.1 해상도).
NOISE_SMOOTH_SLIDER_SCALE = 100
NOISE_SMOOTH_SLIDER_STEPS = 300
NOISE_OFFSET_SLIDER_SCALE = 10
NOISE_OFFSET_SLIDER_STEPS = 5000

NOISE_SETTLE_MS = 350

# Stagger 슬라이더 전용 스타일 (A00290_BSTool Shape Editor 슬라이더 참고).
# 테마 qss 가 QSlider 를 스타일링하지 않아, 어두운 배경에선 Maya 네이티브 홈(groove)이 배경에
# 묻혀 "가로 구간이 어디부터 어디까지인지 안 보인다". 그래서 홈을 직접 그린다. 이 슬라이더는
# 중앙이 0 인 양방향이라, 한쪽만 채우는 sub-page fill 은 0 에서도 절반 찬 것처럼 보여 오해를 준다
# → sub/add-page 를 같은 색으로 덮어 좌우 균일한 한 줄로만 그리고, 0 위치는 중앙 눈금(TicksBelow)이
# 표시한다. blue_dark 테마 accent(#7f9ec8)에 맞췄다.
STAGGER_SLIDER_STYLE = (
    "QSlider:horizontal { min-height: 20px; }"
    "QSlider::groove:horizontal {"
    " height: 6px; margin: 0 4px;"
    " background: #34373d; border: 1px solid #7f9ec8; border-radius: 3px; }"
    "QSlider::sub-page:horizontal, QSlider::add-page:horizontal {"
    " background: #34373d; border: 1px solid #7f9ec8; border-radius: 3px; }"
    "QSlider::handle:horizontal {"
    " width: 12px; margin: -6px 0;"
    " background: #a9c4e6; border: 1px solid #7f9ec8; border-radius: 3px; }"
    "QSlider::handle:horizontal:hover { background: #ffffff; }"
    "QSlider::groove:horizontal:disabled,"
    " QSlider::sub-page:horizontal:disabled,"
    " QSlider::add-page:horizontal:disabled {"
    " background: #2f2f2f; border: 1px solid #454545; }"
    "QSlider::handle:horizontal:disabled {"
    " background: #5a5a5a; border: 1px solid #454545; }"
)


class MainWindow(QWidget):

    def __init__(self):

        # 마야 메인 윈도우에 parent. 뷰포트 위에는 떠 있되 다른 툴 창과는 정상 Z-order
        # (밑의 창을 클릭하면 위로 올라온다). WindowStaysOnTopHint 의 대체.
        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_width  = 620
        self.win_height = 600
        self.win_title  = f"Anim Key Tool V02 v{VERSION}"

        self.resize(self.win_width, self.win_height)

        # Stagger Offset 라이브 세션. 슬라이더/스핀박스를 만지는 동안만 살아 있고,
        # Apply/Reset/리스트·구간 변경/창 닫기에서 정리된다. (build_ui 보다 먼저 —
        # 위젯 시그널이 곧바로 이 값을 참조한다)
        self._stagger_session = None
        self._stagger_updating = False

        # 조작이 멎으면 그때까지의 미리보기를 undo 큐에 한 항목으로 기록하는 디바운스 타이머.
        # (드래그 중 매 틱마다 기록하면 Ctrl+Z 를 수백 번 눌러야 원위치가 된다)
        self._stagger_settle_timer = QTimer(self)
        self._stagger_settle_timer.setSingleShot(True)
        self._stagger_settle_timer.setInterval(STAGGER_SETTLE_MS)
        self._stagger_settle_timer.timeout.connect(self._stagger_settle)

        self.build_ui()

        # 툴 실행 중 Shift+A 핫키 바인딩 (창 종료 시 closeEvent 에서 복원)
        self.hotkey_mgr = HotkeyManager()
        self._enable_hotkey(self.cb_hotkey.isChecked())

        # 선택 시 그래프 에디터 자동 프레이밍 (기본 OFF, 창 종료 시 scriptJob 정리)
        self.graph_focus_mgr = GraphFocusManager()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)

        # parent(마야 메인 윈도우)가 있어도 임베드되지 않고 독립 창으로 유지.
        # (isWindow()==True 이므로 launch.py 의 topLevelWidgets() 정리 로직도 그대로 동작)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # -------------------------
        # 상단 헤더 행 : 메뉴 바(좌, Help > About) + Always on Top 토글(우)
        # jointTool 의 cmds.menu('Help') / cmds.menuItem('About') 패턴을 Qt 로 옮김.
        # 코너 위젯 대신 QHBoxLayout 으로 배치해 토글 시 위치/크기가 고정되도록 한다.
        # -------------------------

        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)

        # 항상 위(Always on Top) 토글 버튼 — 켜면 이 창이 다른 마야 창 위에 유지된다.
        # (이 툴은 기본적으로 WindowStaysOnTopHint 를 쓰지 않는 정상 Z-order 라, 필요할 때만 켠다)
        self.pin_button = QPushButton("Pin")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Keep this window above other Maya windows")
        # 고정 크기 — "Pin"/"Pinned" 토글 시 버튼 크기가 변하지 않도록 (넓은 라벨 기준)
        self.pin_button.setFixedSize(72, 28)
        self.pin_button.toggled.connect(self.toggle_always_on_top)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 6, 0)
        header_row.addWidget(self.menu_bar, stretch=1)
        header_row.addWidget(self.pin_button)
        main_layout.addLayout(header_row)

        # -------------------------
        # 로그 (모든 탭 공유)
        # 탭 빌더가 생성 중 self.log() 를 호출할 수 있으므로 탭보다 먼저 생성한다.
        # (레이아웃 추가는 탭 아래에 한다)
        # -------------------------

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        # 창이 콘텐츠에 맞춰 줄어들 때도 로그창이 쓸만한 높이를 유지하도록 최소 높이 지정.
        # 최대 높이도 막아, 창을 다시 키울 때 남는 공간을 로그가 독식해 비대해지는 걸 방지한다.
        # (남는 공간은 탭/리스트 영역으로 간다)
        self.te_log.setMinimumHeight(90)
        self.te_log.setMaximumHeight(160)

        # -------------------------
        # 탭 : 카테고리 6개 (Key / Timing / Curve / Transfer / Bake / View)
        # 분류는 아래 CATEGORIES 표가 정한다.
        # -------------------------

        self.tabs = QTabWidget()
        for label, tip, pages, attr in self.CATEGORIES:
            index = self.tabs.addTab(self._build_category_tab(pages, attr), label)
            self.tabs.setTabToolTip(index, tip)
        main_layout.addWidget(self.tabs)

        # 탭 전환 시에는 '현재 탭' 콘텐츠에 맞추되 줄이지 않고 필요할 때만 늘린다(grow_only).
        # 사용자가 리스트업 후 창을 키워 둔 상태에서 탭을 눌렀다고 창이 갑자기 작아지지 않게 한다.
        self.tabs.currentChanged.connect(
            lambda *_: self._fit_window_later(grow_only=True))

        # 로그창을 탭 아래에 배치
        main_layout.addWidget(self.te_log)

        # -------------------------
        # Force Refresh : 뷰포트가 멈춰(커브 편집이 프레임 이동 전까지 반영 안 됨) 있을 때
        # 막힌 전역 refresh suspend 를 풀고 한 번 다시 그린다.
        # -------------------------

        self.btn_force_refresh = QPushButton("Force Refresh (Unfreeze Viewport)")
        self.btn_force_refresh.setToolTip(
            "Clear a stuck viewport refresh-suspend and redraw once.\n"
            "Use if Graph Editor edits don't show until you scrub frames.")
        self.btn_force_refresh.clicked.connect(self.on_force_refresh)
        main_layout.addWidget(self.btn_force_refresh)

        # -------------------------
        # 저작권 (공통)
        # -------------------------

        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # --------------------------------------------------
    # Window sizing (접이식 섹션 토글 / 탭 전환 시 창 크기 자동 조정)
    # --------------------------------------------------

    def _fit_window_later(self, *args, grow_only=False):
        """레이아웃이 보임/숨김을 반영한 다음 이벤트 루프에서 창 높이를 콘텐츠에 맞춘다.
        (토글/탭전환 시점엔 새 가시성이 아직 레이아웃에 반영되지 않을 수 있어 한 틱 미룬다.)
        grow_only=True 면 필요할 때만 늘리고 줄이지는 않는다(탭 전환용)."""
        QTimer.singleShot(0, lambda: self._fit_window(grow_only=grow_only))

    def _fit_window(self, grow_only=False):
        """현재 탭 콘텐츠 높이에 맞춰 창 높이를 조정(너비는 유지).
        탭 페이지는 JUN_mod_fit_tab_page_v01 라 숨은 탭은 sizeHint 0 → 창이 현재 탭에만 맞춰진다.
        page.adjustSize() 만으로는 QTabWidget 내부 QStackedLayout 의 캐시된 sizeHint 가
        갱신되지 않으므로(섹션 접을 때 창이 안 줄어듦), tabs.adjustSize() 로 강제 재계산한다.

        grow_only=True 면 콘텐츠가 현재 창보다 클 때만 늘리고 줄이지는 않는다. 섹션 토글(접기)
        때는 grow_only=False 로 호출해 빈 공간을 회수한다(접으면 창이 줄어드는 동작 유지)."""
        page = self.tabs.currentWidget()
        if page is not None:
            page.adjustSize()
        self.tabs.adjustSize()
        self.tabs.updateGeometry()
        self.layout().activate()
        target_h = self.sizeHint().height()
        if grow_only:
            target_h = max(self.height(), target_h)
        self.resize(self.width(), target_h)

    # --------------------------------------------------
    # Tab builders
    # --------------------------------------------------

    # ==================================================================
    # 탭 분류 (V02 v02.00~) — **상위 탭 = 카테고리 / 하위 탭 = 기능** 하나로 통일.
    #
    # V01(A00110_animTool, v01.41) 에서는 `Key Edit` 만 하위 탭 8개를 가진 카테고리이고 나머지 5개(Copy Key /
    # Mirror Key / Bake / Follow / Graph Focus)는 기능 하나짜리 상위 탭이었다. 그래서
    # 새 기능이 전부 `Key Edit` 로 들어가 비대해지고(Euler·Pose Key 가 실제로 그렇게
    # 내려왔다), 정작 같은 개념인 Copy/Mirror/Follow 는 흩어져 있었다.
    #
    # 분류 기준은 **"사용자가 무엇을 바꾸려 하는가"** 하나다:
    #   Key      - 키의 존재(만들고 지운다)
    #   Timing   - 키의 시점(시간축 재배치)
    #   Curve    - 커브의 값·형태
    #   Transfer - 다른 오브젝트로 옮기기
    #   Bake     - 키로 굽기
    #   View     - 보기 보조(씬을 바꾸지 않는 유일한 카테고리)
    #
    # 계획서: docs/plans/A00110_animTool_V02_tab_reorg_plan.md
    #
    # 각 항목은 (탭 라벨, 툴팁 = 전체 이름/설명, 빌더 메서드 이름).
    # 라벨을 짧게 두는 이유는 탭 바가 창 폭(기본 520)을 넘기지 않게 하기 위해서다 —
    # 전체 이름은 툴팁에 싣는다. 각 카테고리의 **첫 하위 탭이 대표 기능**이다.
    # ==================================================================

    KEY_PAGES = (
        ("Pose Key", "Pose Key - set a 6-axis pose key on the selected objects "
         "at the current frame", "_build_pose_key_page"),
        ("Fill Keys", "Fill Keys - put a key on every frame of a range for the "
         "chosen channels, leaving the existing keys alone",
         "_build_fill_keys_page"),
        ("Delete All", "Delete All Keys - delete every keyframe of the listed "
         "objects", "_build_delete_all_page"),
    )

    TIMING_PAGES = (
        ("Move", "Move Keys - shift the keys in a frame range, or delete "
         "that range", "_build_move_keys_page"),
        ("Hold", "Hold - hold the key range selected in the Graph Editor "
         "(+ Shift+A hotkey)", "_build_graph_editor_page"),
        ("Offset", "Offset & Hold - rebuild the listed controllers' keys "
         "as a hold + offset structure", "_build_offset_hold_page"),
        ("Stagger", "Stagger Offset - shift each listed controller by "
         "'list order x offset' (follow-through / wave)",
         "_build_stagger_offset_page"),
    )

    CURVE_PAGES = (
        ("Euler", "Euler Filter - run an euler filter on the listed controllers, "
         "limited to a frame range", "_build_euler_filter_page"),
        ("Filters", "Curve Filters - Smooth / Intensity / Interpolate on the keys "
         "you selected in the Graph Editor", "_build_curve_filters_page"),
    )

    # Create 는 다른 카테고리와 성격이 다르다 — 기존 애니메이션을 손보는 게 아니라
    # **없던 애니메이션 소스를 씬에 새로 만든다.** 입주 기준을 좁게 못 박아 둔다:
    # "씬에 새 노드를 만들어 애니메이션 소스를 공급하는 기능" 만 여기 들어온다.
    # (Key Edit 이 잡동사니 서랍이 됐던 전례를 반복하지 않기 위한 규칙 — 탭 재분류 계획서 §1)
    CREATE_PAGES = (
        ("Noise", "Noise - create nodes whose 'output' plays deterministic, "
         "seamless noise over time", "_build_noise_tab"),
    )

    # 아래 넷은 v01.41 까지 **상위 탭**이었다. 빌더가 이미
    # JUN_mod_fit_tab_page_v01 을 반환하므로 그대로 하위 탭 페이지로 쓴다.
    TRANSFER_PAGES = (
        ("Copy Key", "Copy Key - copy a frame range of keys from Base[i] to "
         "Target[i], with an optional per-axis reverse", "_build_copy_key_tab"),
        ("Mirror Key", "Mirror Key - mirror keys onto the opposite controller "
         "(frame range or current frame, token pairing)",
         "_build_mirror_key_tab"),
        ("Follow", "Follow - bake the followers onto their targets over a range, "
         "with a 0-1 blend", "_build_follow_tab"),
    )

    BAKE_PAGES = (
        ("Bake", "Bake - bake the listed objects down to dense keys over a "
         "frame range", "_build_bake_tab"),
    )

    VIEW_PAGES = (
        ("Graph Focus", "Graph Focus - frame the Graph Editor around the current "
         "frame (+ auto-focus when the selection changes)",
         "_build_graph_focus_tab"),
    )

    # (상위 탭 라벨, 툴팁, 하위 페이지 표, 하위 QTabWidget 을 담을 속성 이름)
    CATEGORIES = (
        ("Key", "Key - create and delete keys", KEY_PAGES, "key_tabs"),
        ("Timing", "Timing - move keys along the time axis",
         TIMING_PAGES, "timing_tabs"),
        ("Curve", "Curve - clean up the shape and the values of the curves",
         CURVE_PAGES, "curve_tabs"),
        ("Create", "Create - build new animation sources in the scene",
         CREATE_PAGES, "create_tabs"),
        ("Transfer", "Transfer - move animation onto other objects",
         TRANSFER_PAGES, "transfer_tabs"),
        ("Bake", "Bake - bake the result down to keys", BAKE_PAGES, "bake_tabs"),
        ("View", "View - viewing helpers; these change nothing in the scene",
         VIEW_PAGES, "view_tabs"),
    )

    def _build_category_tab(self, pages, attr):
        """카테고리 상위 탭 하나 — 기능들을 **하위 탭**으로 담는다.

        하위 페이지가 하나뿐인 카테고리(Curve / Bake / View)도 하위 탭 바를 그대로 둔다.
        탭 하나를 위한 탭 바가 낭비처럼 보일 수 있지만, ① 그래야 기능 이름이 화면에 남고
        (Euler·Bake 페이지에는 제목 그룹박스가 없다), ② 나중에 기능이 늘어도 구조가
        그대로다.

        A00145_RigConnect 의 Constrain 탭과 같은 구성이지만 **스크롤 영역은 쓰지 않는다** —
        이 툴은 창을 콘텐츠 높이에 맞춰 자동으로 늘리고 줄이기 때문이다(`_fit_window`).
        그래서 바깥 페이지도 하위 페이지도 `JUN_mod_fit_tab_page_v01` 로 둔다. 숨은 페이지가
        sizeHint 0 을 보고해야 창이 '지금 보이는' 페이지에만 맞춰진다.
        """
        page = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        layout = QVBoxLayout(page)

        tabs = self._build_sub_tabs(pages)
        setattr(self, attr, tabs)
        layout.addWidget(tabs)

        return page

    def _build_sub_tabs(self, pages):
        """(라벨, 툴팁, 빌더 메서드 이름) 목록을 중첩 탭 위젯으로 만든다."""
        tabs = QTabWidget()
        # 폭이 모자라면 라벨을 자른다(스크롤 화살표만 뜨는 것보다 읽기 쉽다).
        tabs.tabBar().setElideMode(Qt.ElideRight)

        for label, tip, builder in pages:
            index = tabs.addTab(getattr(self, builder)(), label)
            tabs.setTabToolTip(index, tip)

        # 하위 탭을 바꿔도 창을 내용에 맞춘다(상위 탭 전환과 같은 규칙: 줄이지는 않는다).
        tabs.currentChanged.connect(
            lambda *_: self._fit_window_later(grow_only=True))

        return tabs

    def _sub_page(self):
        """하위 탭 페이지 하나를 만든다. (페이지 위젯, 세로 레이아웃)"""
        page = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        return page, QVBoxLayout(page)

    # ---------------- Timing > Move ----------------

    def _build_move_keys_page(self):
        """키 위치 이동 / 구간 삭제 (Timing > Move)."""
        page, layout = self._sub_page()

        row = QHBoxLayout()
        # Start/End 구간 입력 = 공용 위젯(JUN_mod_timeRange_qt). le_start/le_end 는
        # 하위 코드가 그대로 .text() 를 읽도록 위젯의 내부 QLineEdit 을 가리키게 둔다.
        self.move_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_placeholder="4", end_placeholder="10", log_callback=self.log)
        self.le_start = self.move_range.start_edit
        self.le_end = self.move_range.end_edit
        row.addWidget(self.move_range)

        row.addWidget(QLabel("Offset"))
        self.le_offset = QLineEdit()
        self.le_offset.setValidator(QIntValidator(0, 1000000, self))
        self.le_offset.setPlaceholderText("5")
        row.addWidget(self.le_offset)
        layout.addLayout(row)

        row = QHBoxLayout()
        self.btn_move_back = QPushButton("◀ Earlier (-)")
        self.btn_move_fwd = QPushButton("Later (+) ▶")
        row.addWidget(self.btn_move_back)
        row.addWidget(self.btn_move_fwd)
        layout.addLayout(row)

        self.btn_delete = QPushButton("Delete Keys in Range")
        layout.addWidget(self.btn_delete)

        layout.addStretch(1)

        self.btn_move_back.clicked.connect(lambda: self.on_move(-1))
        self.btn_move_fwd.clicked.connect(lambda: self.on_move(+1))
        self.btn_delete.clicked.connect(self.on_delete)

        return page

    # ---------------- Key > Fill Keys ----------------

    def _build_fill_keys_page(self):
        """구간의 모든 프레임에 키를 채우는 페이지 (Key > Fill Keys).

        어트리뷰트 목록 UI 는 A00145_RigConnect 의 Connect 탭과 같은 구성이다 —
        왼쪽에 오브젝트 리스트 + `List Attributes`, 오른쪽에 어트리뷰트 목록 + Filter +
        `Select All`.
        """
        page, layout = self._sub_page()

        body = QHBoxLayout()

        # --- 왼쪽: 대상 오브젝트 ---
        left = QVBoxLayout()
        self.fill_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Objects", select_label="List Selected Objects",
            list_min_height=130, log_callback=self.log)
        left.addWidget(self.fill_tsl)

        btn_list = QPushButton("List Attributes")
        btn_list.setToolTip(
            "List the keyable channels of the listed objects (union).\n"
            "Only channels that are keyable, shown in the channel box and "
            "unlocked are listed.")
        btn_list.clicked.connect(self.on_fill_list_attrs)
        left.addWidget(btn_list)
        body.addLayout(left)

        # --- 오른쪽: 어트리뷰트 목록 ---
        right = QVBoxLayout()
        head = QHBoxLayout()
        head.addWidget(QLabel("Attributes"))
        head.addStretch(1)
        self.lbl_fill_number = QLabel("Number: 0")
        head.addWidget(self.lbl_fill_number)
        right.addLayout(head)

        self.lw_fill_attrs = QListWidget()
        self.lw_fill_attrs.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_fill_attrs.setMinimumHeight(130)
        right.addWidget(self.lw_fill_attrs)

        self.flt_fill = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            self.lw_fill_attrs, placeholder="Type any part of a channel name",
            number_label=self.lbl_fill_number)
        right.addWidget(self.flt_fill)

        btn_all = QPushButton("Select All")
        btn_all.setToolTip("Select every channel currently visible in the list.")
        btn_all.clicked.connect(self.flt_fill.select_all_visible)
        right.addWidget(btn_all)

        body.addLayout(right)
        layout.addLayout(body)

        # --- 구간 ---
        self.fill_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_placeholder="1", end_placeholder="24", log_callback=self.log)
        layout.addWidget(self.fill_range)

        # --- 애니메이션 레이어 ---
        layer_row = QHBoxLayout()
        layer_row.addWidget(QLabel("Anim Layer"))
        self.cmb_fill_layer = QComboBox()
        self.cmb_fill_layer.setToolTip(
            "Which animation layer the new keys go on.\n"
            "'(current)' leaves it to Maya - the layer selected in the Anim Layer "
            "editor.")
        layer_row.addWidget(self.cmb_fill_layer, 1)

        btn_layers = QPushButton("Refresh")
        btn_layers.setToolTip("Re-scan the scene for animation layers.")
        btn_layers.clicked.connect(self.on_fill_refresh_layers)
        layer_row.addWidget(btn_layers)
        layout.addLayout(layer_row)

        self.on_fill_refresh_layers(quiet=True)

        # --- 실행 ---
        # 실행 버튼 2개 — Curve > Euler 탭과 같은 구성.
        #   위 : 원버튼. 리스트업·채널 고르기·구간 입력 없이 **그래프 에디터에서 고른 키**를
        #        그대로 읽어 실행한다(고른 키가 곧 오브젝트·채널·구간을 다 말해 준다).
        #   아래: 기존 버튼. 리스트 + 고른 채널 + Start/End 로 실행한다.
        self.btn_fill_keys_sel = QPushButton("Fill Keys from Selection")
        self.btn_fill_keys_sel.setMinimumHeight(32)
        self.btn_fill_keys_sel.setToolTip(
            "One click: objects, channels and range all come from the keys you\n"
            "selected in the Graph Editor - no listing, no Start / End typing.\n"
            "What it used is written back into the list, the channels and the\n"
            "range above, so you can see it and re-run with the button below.")
        self.btn_fill_keys_sel.clicked.connect(self.on_fill_keys_from_selection)
        layout.addWidget(self.btn_fill_keys_sel)

        self.btn_fill_keys = QPushButton("Fill Keys in Range")
        self.btn_fill_keys.setMinimumHeight(32)
        self.btn_fill_keys.setToolTip(
            "Put a key on every frame of [Start, End] for the selected channels.\n"
            "Frames that already have a key are left untouched; empty frames get "
            "a key\n"
            "holding the value they already show, so the animation does not "
            "change.\n"
            "Runs as a single undo step.")
        self.btn_fill_keys.clicked.connect(self.on_fill_keys)
        layout.addWidget(self.btn_fill_keys)

        layout.addStretch(1)
        return page

    # ---------------- Timing > Hold ----------------

    def _build_graph_editor_page(self):
        """그래프 에디터에서 선택한 키 구간 Hold (Timing > Hold)."""
        page, layout = self._sub_page()

        self.btn_hold = QPushButton("Hold Selected Range")
        layout.addWidget(self.btn_hold)

        self.cb_hotkey = QCheckBox("Shift+A hotkey")
        self.cb_hotkey.setChecked(True)
        layout.addWidget(self.cb_hotkey)

        self.lbl_hotkey = QLabel("")
        layout.addWidget(self.lbl_hotkey)

        layout.addStretch(1)

        self.btn_hold.clicked.connect(self.on_hold)
        self.cb_hotkey.toggled.connect(self.on_toggle_hotkey)

        return page

    # ---------------- Timing > Offset ----------------

    def _build_offset_hold_page(self):
        """리스트업한 컨트롤러 키를 hold(유지) + offset(보간) 구조로 재배치.

        대상은 씬 선택이 아니라 리스트의 항목. 로직은 OffsetHoldManager.
        """
        page, layout = self._sub_page()

        self.oh_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Offset/Hold List", select_label="Select Objects", log_callback=self.log)
        layout.addWidget(self.oh_tsl)

        oh_nonneg = QIntValidator(0, 1000000, self)

        oh_row = QHBoxLayout()
        oh_row.addWidget(QLabel("Hold"))
        self.le_oh_hold = QLineEdit()
        self.le_oh_hold.setValidator(oh_nonneg)
        self.le_oh_hold.setPlaceholderText("20")
        oh_row.addWidget(self.le_oh_hold)

        oh_row.addWidget(QLabel("Offset"))
        self.le_oh_offset = QLineEdit()
        self.le_oh_offset.setValidator(oh_nonneg)
        self.le_oh_offset.setPlaceholderText("30")
        oh_row.addWidget(self.le_oh_offset)

        # Start: 비우면 오브젝트별 첫 키 프레임을 앵커로 사용.
        oh_row.addWidget(QLabel("Start"))
        self.le_oh_start = QLineEdit()
        self.le_oh_start.setValidator(QIntValidator(-1000000, 1000000, self))
        self.le_oh_start.setPlaceholderText("(first key)")
        oh_row.addWidget(self.le_oh_start)
        layout.addLayout(oh_row)

        self.btn_oh_apply = QPushButton("Apply Offset & Hold")
        layout.addWidget(self.btn_oh_apply)

        layout.addStretch(1)

        self.btn_oh_apply.clicked.connect(self.on_offset_hold)

        return page

    # ---------------- Timing > Stagger ----------------

    def _build_stagger_offset_page(self):
        """리스트업한 컨트롤러의 [Start, End] 구간 키를 '리스트 순서 x Offset' 만큼
        계단식으로 민다(0번 제자리 / 1번 +1배 / 2번 +2배 ...). 팔로우스루·웨이브용.

        슬라이더/스핀박스로 맞춘 값이 그대로 최종 결과다(별도 Apply 없음). 슬라이더에서
        손을 떼면 그 값이 undo 큐에 한 항목으로 기록되고 **거기서 확정된다** — 그 뒤
        리스트를 다시 담거나 구간을 고쳐도 되돌아가지 않는다(v02.07~). 되돌리려면
        Reset 이나 Ctrl+Z. 값은 누적되지 않는다(세션 안에서는 늘 시작 상태 기준 재계산).
        로직은 StaggerOffsetSession.
        """
        page, layout = self._sub_page()

        self.st_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Stagger List (order = offset step)",
            select_label="List Selected Objects",
            show_reverse=True, log_callback=self.log)
        layout.addWidget(self.st_tsl)

        st_row = QHBoxLayout()
        self.st_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_placeholder="0", end_placeholder="5", log_callback=self.log)
        self.le_st_start = self.st_range.start_edit
        self.le_st_end = self.st_range.end_edit
        st_row.addWidget(self.st_range)
        layout.addLayout(st_row)

        # 슬라이더 + 스핀박스 = 같은 값을 가리키는 두 얼굴(A00290_BSTool Shape Editor 패턴).
        # 어느 쪽을 움직이든 즉시 씬에 반영하고 반대쪽 위젯을 맞춘다. 슬라이더는 손으로 훑기
        # 좋은 범위(±STAGGER_SLIDER_RANGE)만 담당하고, 그보다 큰 값은 스핀박스로 넣는다.
        st_row2 = QHBoxLayout()
        st_row2.addWidget(QLabel("Offset per Item"))

        self.sld_stagger = QSlider(Qt.Horizontal)
        self.sld_stagger.setRange(-STAGGER_SLIDER_RANGE, STAGGER_SLIDER_RANGE)
        self.sld_stagger.setValue(0)
        # 양 끝과 중앙(0)에 눈금을 찍어 0 위치를 눈으로 찾을 수 있게 한다.
        self.sld_stagger.setTickPosition(QSlider.TicksBelow)
        self.sld_stagger.setTickInterval(STAGGER_SLIDER_RANGE)
        self.sld_stagger.setSingleStep(1)
        self.sld_stagger.setPageStep(5)
        self.sld_stagger.setMinimumWidth(140)
        # 테마 qss 가 홈을 안 그려 배경에 묻히므로 직접 그린다(구간이 보이게).
        self.sld_stagger.setStyleSheet(STAGGER_SLIDER_STYLE)
        self.sld_stagger.setToolTip(
            "Stagger the key FRAMES: item 0 stays, item 1 moves +1x, item 2 +2x ...\n"
            "Releasing the slider commits that value - re-listing objects or editing\n"
            "Start/End no longer takes it back. Use Reset or Ctrl+Z to undo it.")
        st_row2.addWidget(self.sld_stagger, 1)

        self.sb_stagger = QSpinBox()
        self.sb_stagger.setRange(-10000, 10000)
        self.sb_stagger.setValue(0)
        self.sb_stagger.setSuffix(" f")
        self.sb_stagger.setFixedWidth(78)
        self.sb_stagger.setKeyboardTracking(False)   # 타이핑 도중 매 글자마다 반영되지 않게
        st_row2.addWidget(self.sb_stagger)

        st_row2.addWidget(QLabel("f"))
        layout.addLayout(st_row2)

        # 값(value) 쪽 계단식 오프셋. 시간과 **같은 배수 규칙**(리스트 순서 x 값)이라
        # 0번은 제자리, 1번 +1x, 2번 +2x ... 로 값이 올라간다. 시간과 독립적으로 쓸 수
        # 있어(한쪽만 0) '값만 계단식으로' 도 된다.
        st_row3 = QHBoxLayout()
        st_row3.addWidget(QLabel("Value per Item"))

        self.sld_stagger_value = QSlider(Qt.Horizontal)
        self.sld_stagger_value.setRange(-STAGGER_VALUE_SLIDER_STEPS,
                                        STAGGER_VALUE_SLIDER_STEPS)
        self.sld_stagger_value.setValue(0)
        self.sld_stagger_value.setTickPosition(QSlider.TicksBelow)
        self.sld_stagger_value.setTickInterval(STAGGER_VALUE_SLIDER_STEPS)
        self.sld_stagger_value.setSingleStep(1)
        self.sld_stagger_value.setPageStep(10)
        self.sld_stagger_value.setMinimumWidth(140)
        self.sld_stagger_value.setStyleSheet(STAGGER_SLIDER_STYLE)
        self.sld_stagger_value.setToolTip(
            "Stagger the key VALUES the same way as the frames:\n"
            "item 0 stays, item 1 gets +1x, item 2 gets +2x ...\n"
            "Works on its own - leave the frame offset at 0 to shift values only.\n"
            "Releasing the slider commits that value - re-listing objects or editing\n"
            "Start/End no longer takes it back. Use Reset or Ctrl+Z to undo it.")
        st_row3.addWidget(self.sld_stagger_value, 1)

        self.sb_stagger_value = QDoubleSpinBox()
        self.sb_stagger_value.setRange(-100000.0, 100000.0)
        self.sb_stagger_value.setDecimals(3)
        self.sb_stagger_value.setSingleStep(0.1)
        self.sb_stagger_value.setValue(0.0)
        self.sb_stagger_value.setFixedWidth(88)
        self.sb_stagger_value.setKeyboardTracking(False)
        self.sb_stagger_value.setToolTip(
            "Value added per list step. Applies to the same channels as the frame\n"
            "offset (channel box selection, else every animated curve).")
        st_row3.addWidget(self.sb_stagger_value)

        self.btn_st_reset = QPushButton("Reset")
        self.btn_st_reset.setToolTip(
            "Put the keys back to their original frames AND values (undoable).\n"
            "This undoes the CURRENT session only - offsets committed before the list\n"
            "or range last changed are already final, so use Ctrl+Z for those.")
        st_row3.addWidget(self.btn_st_reset)
        layout.addLayout(st_row3)

        # Apply 버튼 없음: 슬라이더/스핀박스로 맞춘 값이 곧 최종 결과다. 조작이 멎으면
        # 자동으로 undo 큐에 기록된다(_stagger_settle: sliderReleased / editingFinished /
        # 디바운스 타이머 / 창 닫기).

        layout.addStretch(1)

        # 슬라이더/스핀박스 = 실시간 미리보기(같은 값의 두 얼굴), 조작이 멎으면 자동 기록.
        # valueChanged 는 바인딩/버전에 따라 인자 타입이 달라 위젯에서 직접 읽는다.
        self.sld_stagger.valueChanged.connect(self.on_stagger_slider_changed)
        self.sb_stagger.valueChanged.connect(self.on_stagger_spin_changed)
        self.sld_stagger_value.valueChanged.connect(
            self.on_stagger_value_slider_changed)
        self.sb_stagger_value.valueChanged.connect(
            self.on_stagger_value_spin_changed)
        self.sld_stagger_value.sliderReleased.connect(self._stagger_settle)
        self.sb_stagger_value.editingFinished.connect(self._stagger_settle)
        # 드래그를 놓거나 타이핑을 끝낸 순간은 기다릴 것 없이 바로 기록한다.
        self.sld_stagger.sliderReleased.connect(self._stagger_settle)
        self.sb_stagger.editingFinished.connect(self._stagger_settle)
        self.btn_st_reset.clicked.connect(self.on_stagger_reset)

        # 리스트/구간이 바뀌면 세션의 전제(순서·구간)가 깨지므로 세션을 닫는다.
        # **씬에 적용된 offset 은 그대로 둔다** — 손을 뗀 순간 이미 확정된 결과다.
        self.le_st_start.textChanged.connect(self._stagger_invalidate)
        self.le_st_end.textChanged.connect(self._stagger_invalidate)
        st_model = self.st_tsl.list_widget.model()
        st_model.rowsInserted.connect(self._stagger_invalidate)
        st_model.rowsRemoved.connect(self._stagger_invalidate)
        st_model.modelReset.connect(self._stagger_invalidate)

        return page

    # ---------------- Key > Delete All ----------------

    def _build_delete_all_page(self):
        """리스트업한 오브젝트의 '모든' 키프레임을 일괄 삭제.

        대상은 씬 선택이 아니라 리스트의 항목. 파괴적이라 확인 다이얼로그를 둔다.
        """
        page, layout = self._sub_page()

        self.delall_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Delete-All List", select_label="List Selected Objects", log_callback=self.log)
        layout.addWidget(self.delall_tsl)

        self.btn_delete_all = QPushButton("Delete All Keyframes of Listed")
        layout.addWidget(self.btn_delete_all)

        layout.addStretch(1)

        self.btn_delete_all.clicked.connect(self.on_delete_all)

        return page

    def _build_pose_key_page(self):
        """선택 오브젝트 현재 프레임에 6축 pose 키를 설정하는 탭.
        축마다 체크박스가 있고, 체크된 축만 입력값으로 키를 설정한다.
        기본 체크: rotate X, rotate Z, translate Y. (A00030 원본 3축)"""

        tab = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        tab_layout = QVBoxLayout(tab)

        grp = QGroupBox("Set Pose Key (current frame)")
        grp_layout = QVBoxLayout(grp)

        # 기본 체크 축
        default_on = {"rx", "rz", "ty"}

        # attr -> (checkbox, lineedit)
        self.pose_rows = {}

        for attr, label in PoseKeyManager.AXES:

            row = QHBoxLayout()

            cb = QCheckBox()
            cb.setChecked(attr in default_on)
            row.addWidget(cb)

            lbl = QLabel(label)
            lbl.setMinimumWidth(80)
            row.addWidget(lbl)

            le = QLineEdit("0")
            le.setValidator(QDoubleValidator(-1000000.0, 1000000.0, 4, self))
            row.addWidget(le)

            grp_layout.addLayout(row)

            self.pose_rows[attr] = (cb, le)

        tab_layout.addWidget(grp)

        self.btn_set_pose = QPushButton("Set Pose Key")
        tab_layout.addWidget(self.btn_set_pose)

        tab_layout.addStretch(1)

        self.btn_set_pose.clicked.connect(self.on_set_pose)

        return tab

    # ---------------- Create > Noise ----------------

    def _build_noise_tab(self):
        """프레임에 따라 결정론적 · 심리스 노이즈를 내보내는 노드를 만드는 탭.

        노이즈 유닛 하나 = 노드 2개(설정을 담은 transform + 그걸 구동하는 animCurveTU).
        **animCurve 인 것이 핵심**이다 — 마야 그래프 에디터는 animCurve 만 그리므로,
        표현식이나 플러그인 노드로 계산하면 결과를 눈으로 볼 수 없다.
        설계 전체는 docs/plans/A00110_animTool_V02_noise_tab_plan.md 참고.
        """
        page, layout = self._sub_page()

        # 슬라이더 세션(NoiseSession). 선택이 바뀌거나 씬이 어긋나면 새로 만든다.
        self._noise_sess = None
        # 위젯을 노드 값으로 채우는 동안 시그널이 되먹임되는 걸 막는 가드.
        self._noise_updating = False

        self._noise_settle_timer = QTimer(self)
        self._noise_settle_timer.setSingleShot(True)
        self._noise_settle_timer.setInterval(NOISE_SETTLE_MS)
        self._noise_settle_timer.timeout.connect(self._noise_settle)

        # -------------------------
        # 노이즈 노드 목록
        # 공용 TSL 대신 평범한 QListWidget 을 쓴다 — 이 리스트는 '씬 선택을 담는 곳' 이
        # 아니라 **툴이 만든 노드의 목록**이라 Select/Add/Del 동선이 맞지 않는다.
        # 대신 TSL 과 같은 이유로 **이름이 아니라 UUID 를 들고 있는다**(리네임/동명 안전).
        # -------------------------

        list_grp = QGroupBox("Noise Nodes")
        list_layout = QVBoxLayout(list_grp)

        self.noise_list = QListWidget()
        self.noise_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.noise_list.setMinimumHeight(90)
        self.noise_list.setToolTip(
            "Every noise node in the scene.\n"
            "Pick one to edit its settings below. Each node keeps its own\n"
            "waveform, so you can drive many channels with different noise.")
        list_layout.addWidget(self.noise_list)

        btn_row = QHBoxLayout()
        self.btn_noise_create = QPushButton("Create Noise Node")
        self.btn_noise_create.setToolTip(
            "Create a new noise node. Its 'output' attribute plays deterministic,\n"
            "seamless noise and is visible in the Graph Editor like any curve.")
        btn_row.addWidget(self.btn_noise_create)

        self.btn_noise_delete = QPushButton("Delete")
        self.btn_noise_delete.setToolTip("Delete the selected noise node(s) and their curves.")
        btn_row.addWidget(self.btn_noise_delete)

        self.btn_noise_reload = QPushButton("Refresh")
        self.btn_noise_reload.setToolTip(
            "Re-read the scene. Use it after opening a file, or after editing the\n"
            "settings straight in the Channel Box.")
        btn_row.addWidget(self.btn_noise_reload)

        self.btn_noise_select = QPushButton("Select")
        self.btn_noise_select.setToolTip("Select the highlighted noise node(s) in the scene.")
        btn_row.addWidget(self.btn_noise_select)

        list_layout.addLayout(btn_row)
        layout.addWidget(list_grp)

        # -------------------------
        # 선택 노드의 설정
        # -------------------------

        self.noise_set_grp = QGroupBox("Settings")
        set_layout = QVBoxLayout(self.noise_set_grp)

        # --- Type ---
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type"))
        self.cmb_noise_type = QComboBox()
        self.cmb_noise_type.addItems(list(noise_gen.NOISE_TYPES))
        self.cmb_noise_type.setToolTip(
            "Value    - random values per cell, smoothly interpolated. Good default.\n"
            "Perlin   - gradient noise; evenly paced, crosses zero at the cells.\n"
            "Simplex  - like Perlin with fewer grid artefacts.\n"
            "Worley   - distance to feature points; spiky, pulsing motion.\n"
            "Ridged   - folded Value noise; sharp peaks.")
        type_row.addWidget(self.cmb_noise_type, 1)
        set_layout.addLayout(type_row)

        # --- Smoothness ---
        sm_row = QHBoxLayout()
        sm_row.addWidget(QLabel("Smoothness"))

        self.sld_noise_smooth = QSlider(Qt.Horizontal)
        self.sld_noise_smooth.setRange(-NOISE_SMOOTH_SLIDER_STEPS, NOISE_SMOOTH_SLIDER_STEPS)
        self.sld_noise_smooth.setValue(int(noise_gen.DEFAULT_SMOOTHNESS * NOISE_SMOOTH_SLIDER_SCALE))
        self.sld_noise_smooth.setTickPosition(QSlider.TicksBelow)
        self.sld_noise_smooth.setTickInterval(NOISE_SMOOTH_SLIDER_STEPS)
        self.sld_noise_smooth.setMinimumWidth(140)
        self.sld_noise_smooth.setToolTip(
            "How much the value changes from one frame to the next.\n"
            "Positive = smoother, negative = rougher. There is no hard limit, but\n"
            "the effect saturates outside roughly -1 .. +2 (past that the noise is\n"
            "already a single slow wave, or already as rough as one key per frame allows).\n"
            "This is the spectral exponent: 0 = white, +1 = pink, +2 = brown, -1 = blue.")
        sm_row.addWidget(self.sld_noise_smooth, 1)

        self.sb_noise_smooth = QDoubleSpinBox()
        self.sb_noise_smooth.setRange(-1000.0, 1000.0)
        self.sb_noise_smooth.setDecimals(3)
        self.sb_noise_smooth.setSingleStep(0.05)
        self.sb_noise_smooth.setValue(noise_gen.DEFAULT_SMOOTHNESS)
        self.sb_noise_smooth.setFixedWidth(88)
        # 값을 되쓰는 스핀박스는 keyboardTracking 을 꺼야 타이핑 중에 값이 잘리지 않는다.
        self.sb_noise_smooth.setKeyboardTracking(False)
        sm_row.addWidget(self.sb_noise_smooth)
        set_layout.addLayout(sm_row)

        # --- Offset ---
        of_row = QHBoxLayout()
        of_row.addWidget(QLabel("Offset"))

        self.sld_noise_offset = QSlider(Qt.Horizontal)
        self.sld_noise_offset.setRange(-NOISE_OFFSET_SLIDER_STEPS, NOISE_OFFSET_SLIDER_STEPS)
        self.sld_noise_offset.setValue(0)
        self.sld_noise_offset.setTickPosition(QSlider.TicksBelow)
        self.sld_noise_offset.setTickInterval(NOISE_OFFSET_SLIDER_STEPS)
        self.sld_noise_offset.setMinimumWidth(140)
        self.sld_noise_offset.setToolTip(
            "Slide the noise along time, in frames. The waveform loops, so any\n"
            "offset stays seamless - use it to give two nodes the same character\n"
            "without them moving in step.")
        of_row.addWidget(self.sld_noise_offset, 1)

        self.sb_noise_offset = QDoubleSpinBox()
        self.sb_noise_offset.setRange(-1000000.0, 1000000.0)
        self.sb_noise_offset.setDecimals(3)
        self.sb_noise_offset.setSingleStep(1.0)
        self.sb_noise_offset.setValue(0.0)
        self.sb_noise_offset.setFixedWidth(88)
        self.sb_noise_offset.setKeyboardTracking(False)
        of_row.addWidget(self.sb_noise_offset)
        set_layout.addLayout(of_row)

        # --- Min / Max ---
        mm_row = QHBoxLayout()
        mm_row.addWidget(QLabel("Min / Max"))

        self.sb_noise_min = QDoubleSpinBox()
        self.sb_noise_min.setRange(-1000000.0, 1000000.0)
        self.sb_noise_min.setDecimals(3)
        self.sb_noise_min.setSingleStep(0.1)
        self.sb_noise_min.setValue(noise_gen.DEFAULT_MIN)
        self.sb_noise_min.setKeyboardTracking(False)
        self.sb_noise_min.setToolTip(
            "Lowest value the output reaches. The noise is stretched to fill\n"
            "[Min, Max] exactly, so it really does touch both ends.\n"
            "Min above Max is allowed - it simply flips the noise.\n"
            "On a rotation channel these are degrees, as you would expect.")
        mm_row.addWidget(self.sb_noise_min)

        self.sb_noise_max = QDoubleSpinBox()
        self.sb_noise_max.setRange(-1000000.0, 1000000.0)
        self.sb_noise_max.setDecimals(3)
        self.sb_noise_max.setSingleStep(0.1)
        self.sb_noise_max.setValue(noise_gen.DEFAULT_MAX)
        self.sb_noise_max.setKeyboardTracking(False)
        self.sb_noise_max.setToolTip("Highest value the output reaches.")
        mm_row.addWidget(self.sb_noise_max)

        mm_row.addStretch(1)
        set_layout.addLayout(mm_row)

        # --- Seed / Loop Length ---
        sl_row = QHBoxLayout()
        sl_row.addWidget(QLabel("Seed"))

        self.sb_noise_seed = QSpinBox()
        self.sb_noise_seed.setRange(0, 999999)
        self.sb_noise_seed.setValue(0)
        self.sb_noise_seed.setKeyboardTracking(False)
        self.sb_noise_seed.setToolTip(
            "Picks the waveform. The same seed always gives the same noise, on any\n"
            "machine - nothing here depends on a random number generator.")
        sl_row.addWidget(self.sb_noise_seed)

        self.btn_noise_seed = QPushButton("Randomize")
        self.btn_noise_seed.setToolTip("Jump to another waveform.")
        sl_row.addWidget(self.btn_noise_seed)

        sl_row.addSpacing(12)
        sl_row.addWidget(QLabel("Loop Length"))

        self.cmb_noise_length = QComboBox()
        for value in noise_gen.LOOP_LENGTHS:
            self.cmb_noise_length.addItem("{0} f".format(value), value)
        self.cmb_noise_length.setCurrentText("{0} f".format(noise_gen.DEFAULT_LOOP_LENGTH))
        self.cmb_noise_length.setToolTip(
            "How many frames pass before the noise repeats. It loops seamlessly,\n"
            "so playback never shows a seam - 1000 f is 33.3 s at 30 fps.")
        sl_row.addWidget(self.cmb_noise_length)

        self.btn_noise_reset = QPushButton("Reset")
        self.btn_noise_reset.setToolTip(
            "Put the settings back to what they were when this node was selected\n"
            "(undoable).")
        sl_row.addWidget(self.btn_noise_reset)

        sl_row.addStretch(1)
        set_layout.addLayout(sl_row)

        layout.addWidget(self.noise_set_grp)

        # -------------------------
        # 보기 / 출력
        # -------------------------

        self.btn_noise_graph = QPushButton("Show in Graph Editor")
        self.btn_noise_graph.setToolTip(
            "Select the node and frame its 'output' curve in the Graph Editor,\n"
            "so you can see exactly what the noise does.")
        layout.addWidget(self.btn_noise_graph)

        out_grp = QGroupBox("Output")
        out_layout = QVBoxLayout(out_grp)

        self.lbl_noise_targets = QLabel("Not connected.")
        self.lbl_noise_targets.setWordWrap(True)
        out_layout.addWidget(self.lbl_noise_targets)

        out_row = QHBoxLayout()
        self.btn_noise_connect = QPushButton("Connect output -> selected channel(s)")
        self.btn_noise_connect.setToolTip(
            "Select objects in the scene, highlight the attributes you want in the\n"
            "Channel Box, then press this. The node's output drives every one of them.")
        out_row.addWidget(self.btn_noise_connect)

        self.btn_noise_disconnect = QPushButton("Disconnect")
        self.btn_noise_disconnect.setToolTip("Break every connection this node's output drives.")
        out_row.addWidget(self.btn_noise_disconnect)
        out_layout.addLayout(out_row)

        layout.addWidget(out_grp)
        layout.addStretch(1)

        # -------------------------
        # 시그널
        # -------------------------

        self.btn_noise_create.clicked.connect(self.on_noise_create)
        self.btn_noise_delete.clicked.connect(self.on_noise_delete)
        self.btn_noise_reload.clicked.connect(self.on_noise_reload)
        self.btn_noise_select.clicked.connect(self.on_noise_select)
        self.noise_list.itemSelectionChanged.connect(self._noise_selection_changed)

        # 슬라이더/스핀박스 = 같은 값의 두 얼굴. 조작 중에는 미리보기, 멎으면 자동 기록.
        self.sld_noise_smooth.valueChanged.connect(self._noise_smooth_slider_changed)
        self.sb_noise_smooth.valueChanged.connect(self._noise_smooth_spin_changed)
        self.sld_noise_offset.valueChanged.connect(self._noise_offset_slider_changed)
        self.sb_noise_offset.valueChanged.connect(self._noise_offset_spin_changed)
        self.sb_noise_min.valueChanged.connect(self._noise_range_changed)
        self.sb_noise_max.valueChanged.connect(self._noise_range_changed)

        # 드래그를 놓거나 타이핑을 끝낸 순간은 기다릴 것 없이 바로 기록한다.
        for widget in (self.sld_noise_smooth, self.sld_noise_offset):
            widget.sliderReleased.connect(self._noise_settle)
        for widget in (self.sb_noise_smooth, self.sb_noise_offset,
                       self.sb_noise_min, self.sb_noise_max):
            widget.editingFinished.connect(self._noise_settle)

        # 콤보/시드는 한 번에 끝나는 조작이라 미리보기 없이 곧장 확정한다.
        # (loopLength 는 키 개수가 달라져 제자리 갱신 경로를 쓸 수 없기도 하다.)
        self.cmb_noise_type.currentIndexChanged.connect(self._noise_commit_combo)
        self.cmb_noise_length.currentIndexChanged.connect(self._noise_commit_combo)
        self.sb_noise_seed.valueChanged.connect(self._noise_commit_seed)
        self.btn_noise_seed.clicked.connect(self.on_noise_randomize)
        self.btn_noise_reset.clicked.connect(self.on_noise_reset)

        self.btn_noise_graph.clicked.connect(self.on_noise_show_graph)
        self.btn_noise_connect.clicked.connect(self.on_noise_connect)
        self.btn_noise_disconnect.clicked.connect(self.on_noise_disconnect)

        self._noise_fill_list()

        return page

    def _build_copy_key_tab(self):
        """Base -> Target 으로 시간 범위 애니메이션 키를 복사하고 축별로 값을 반전하는 탭.
        레거시 JUN_PY_CopyPasteKey_V03_01 의 Copy Key Tool 을 Qt 로 포팅.
        Base/Target 리스트는 재사용 위젯 JUN_mod_tsl_qt_v01 2개로 구성한다."""

        tab = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Base / Target 리스트 (재사용 위젯, 가로 2분할)
        # Select / Add / Del / Up / Down / Sort / 카운트 / 씬 선택은 위젯이 내장.
        # -------------------------

        self.base_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Base", select_label="Select Base", log_callback=self.log)
        self.tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Target", select_label="Select Targets", log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.base_tsl)
        list_row.addWidget(self.tgt_tsl)
        tab_layout.addLayout(list_row)

        # -------------------------
        # Time range (start / end). 기본값은 현재 playback 범위.
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)

        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        self.copy_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=time_str, end_value=time_end, log_callback=self.log)
        self.le_copy_start = self.copy_range.start_edit
        self.le_copy_end = self.copy_range.end_edit
        range_row.addWidget(self.copy_range)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Paste Option (cmds.pasteKey option). 기본 "insert".
        #   1 -> n : Base 가 1개일 때 그 하나를 **모든** Target 에 복사(기본 ON).
        #            Base 가 2개 이상이면 켜져 있어도 평소대로 n->n 이라 늘 켜 둬도 된다.
        # -------------------------

        option_row = QHBoxLayout()
        option_row.addWidget(QLabel("Paste Option"))
        self.cmb_paste_option = QComboBox()
        self.cmb_paste_option.addItems(CopyKeyManager.PASTE_OPTIONS)
        self.cmb_paste_option.setCurrentText("insert")
        option_row.addWidget(self.cmb_paste_option)

        option_row.addSpacing(12)
        self.cb_copy_one_to_many = QCheckBox("1 -> n")
        self.cb_copy_one_to_many.setChecked(True)
        self.cb_copy_one_to_many.setToolTip(
            "On (default): when Base holds exactly ONE object, its keys go to\n"
            "EVERY object in Target (1->n).\n"
            "With 2 or more objects in Base this does nothing - the copy stays\n"
            "index-matched, Base[i] -> Target[i] (n->n).")
        option_row.addWidget(self.cb_copy_one_to_many)

        option_row.addStretch(1)
        tab_layout.addLayout(option_row)

        # -------------------------
        # Attributes 체크박스 (Translate/Rotate/Scale X/Y/Z, 9개). 기본 모두 on.
        # 전부 켜져 있으면 필터를 걸지 않아 예전처럼 애니메이션된 어트리뷰트를 전부 복사한다.
        # -------------------------

        attr_grp = QGroupBox("Attributes")
        attr_layout = QHBoxLayout(attr_grp)

        # attr key -> checkbox. CopyKeyManager.COPY_ATTRS 키와 일치.
        self.copy_attrs = {}

        for group_label, keys in (
            ("Translate", (("tx", "X"), ("ty", "Y"), ("tz", "Z"))),
            ("Rotate", (("rx", "X"), ("ry", "Y"), ("rz", "Z"))),
            ("Scale", (("sx", "X"), ("sy", "Y"), ("sz", "Z"))),
        ):
            if self.copy_attrs:
                attr_layout.addSpacing(12)
            attr_layout.addWidget(QLabel(group_label))
            for key, label in keys:
                cb = QCheckBox(label)
                cb.setChecked(True)
                self.copy_attrs[key] = cb
                attr_layout.addWidget(cb)

        attr_grp.setToolTip(
            "Attributes to copy. All checked (default) copies EVERY animated\n"
            "attribute of Base - custom attributes included - like before.\n"
            "Uncheck any axis to copy only the checked ones.")

        attr_layout.addStretch(1)
        tab_layout.addWidget(attr_grp)

        # -------------------------
        # Reverse 체크박스 (Translate X/Y/Z, Rotate X/Y/Z). 기본 모두 off.
        # 복사하지 않는(위에서 체크를 푼) 축은 반전에서도 빠진다.
        # -------------------------

        rev_grp = QGroupBox("Reverse")
        rev_layout = QHBoxLayout(rev_grp)

        # attr key -> checkbox. CopyKeyManager.AXES 키와 일치.
        self.copy_reverse = {}

        rev_layout.addWidget(QLabel("Translate"))
        for key, label in (("tx", "X"), ("ty", "Y"), ("tz", "Z")):
            cb = QCheckBox(label)
            self.copy_reverse[key] = cb
            rev_layout.addWidget(cb)

        rev_layout.addSpacing(12)

        rev_layout.addWidget(QLabel("Rotate"))
        for key, label in (("rx", "X"), ("ry", "Y"), ("rz", "Z")):
            cb = QCheckBox(label)
            self.copy_reverse[key] = cb
            rev_layout.addWidget(cb)

        rev_layout.addStretch(1)
        tab_layout.addWidget(rev_grp)

        # -------------------------
        # Copy 버튼
        # -------------------------

        self.btn_copy_key = QPushButton("Copy Key")
        tab_layout.addWidget(self.btn_copy_key)

        tab_layout.addStretch(1)

        self.btn_copy_key.clicked.connect(self.on_copy_key)

        return tab

    def _build_mirror_key_tab(self):
        """컨트롤러 키프레임을 반대쪽 컨트롤러로 좌우 미러하는 탭.
        자동 페어링(토큰) + 수동 리스트 폴백. rotateOrder 무관 (worldMatrix 반사)."""

        tab = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Mode : Auto pair / Manual list
        # -------------------------

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode"))
        self.mir_mode_grp = QButtonGroup(self)
        self.rb_mir_auto = QRadioButton("Auto pair from selection")
        self.rb_mir_manual = QRadioButton("Manual list")
        self.rb_mir_auto.setChecked(True)
        self.mir_mode_grp.addButton(self.rb_mir_auto)
        self.mir_mode_grp.addButton(self.rb_mir_manual)
        mode_row.addWidget(self.rb_mir_auto)
        mode_row.addWidget(self.rb_mir_manual)
        mode_row.addStretch(1)
        tab_layout.addLayout(mode_row)

        # -------------------------
        # Base(Source) / Target 리스트 (수동 모드에서 노출). Copy Key 탭과 동일 위젯.
        # Auto 모드에서도 Resolve Pairs 결과 미리보기/수정에 쓸 수 있다.
        # -------------------------

        self.mir_base_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Source", select_label="Select Source", log_callback=self.log)
        self.mir_tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Target", select_label="Select Targets", log_callback=self.log)

        self.mir_list_row = QWidget()
        list_row = QHBoxLayout(self.mir_list_row)
        list_row.setContentsMargins(0, 0, 0, 0)
        list_row.addWidget(self.mir_base_tsl)
        list_row.addWidget(self.mir_tgt_tsl)
        tab_layout.addWidget(self.mir_list_row)

        self.btn_mir_resolve = QPushButton("Resolve Pairs from Selection")
        tab_layout.addWidget(self.btn_mir_resolve)

        # -------------------------
        # Mirror Axis (X / Y / Z)
        # -------------------------

        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("Mirror Axis"))
        self.mir_axis_grp = QButtonGroup(self)
        self.mir_axis_btns = {}
        for ax in ("X", "Y", "Z"):
            rb = QRadioButton(ax)
            self.mir_axis_grp.addButton(rb)
            self.mir_axis_btns[ax.lower()] = rb
            axis_row.addWidget(rb)
        self.mir_axis_btns["x"].setChecked(True)
        axis_row.addSpacing(12)

        # Channels (Translate / Rotate)
        axis_row.addWidget(QLabel("Channels"))
        self.cb_mir_translate = QCheckBox("Translate")
        self.cb_mir_rotate = QCheckBox("Rotate")
        self.cb_mir_translate.setChecked(True)
        self.cb_mir_rotate.setChecked(True)
        axis_row.addWidget(self.cb_mir_translate)
        axis_row.addWidget(self.cb_mir_rotate)
        axis_row.addStretch(1)
        tab_layout.addLayout(axis_row)

        # Method: Behavior (preserve target local axes) vs world reflection (legacy)
        method_row = QHBoxLayout()
        self.cb_mir_behavior = QCheckBox("Behavior (keep target local axes)")
        self.cb_mir_behavior.setChecked(True)  # 기본값 = 새 방식(behavior)
        self.cb_mir_behavior.setToolTip(
            "On: preserve the target controller's own forward/up axes,\n"
            "like mirror-behavior joints (rest-relative mirror).\n"
            "Off: pure world reflection (legacy).")
        method_row.addWidget(self.cb_mir_behavior)
        method_row.addStretch(1)
        tab_layout.addLayout(method_row)

        # -------------------------
        # Time range + time mode. 기본값은 현재 playback 범위.
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)
        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        self.mir_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=time_str, end_value=time_end, log_callback=self.log)
        self.le_mir_start = self.mir_range.start_edit
        self.le_mir_end = self.mir_range.end_edit
        range_row.addWidget(self.mir_range)

        range_row.addSpacing(12)
        range_row.addWidget(QLabel("Time"))
        self.mir_time_grp = QButtonGroup(self)
        self.rb_mir_srckeys = QRadioButton("Source keys")
        self.rb_mir_bake = QRadioButton("Bake")
        self.rb_mir_srckeys.setChecked(True)
        self.mir_time_grp.addButton(self.rb_mir_srckeys)
        self.mir_time_grp.addButton(self.rb_mir_bake)
        range_row.addWidget(self.rb_mir_srckeys)
        range_row.addWidget(self.rb_mir_bake)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Tokens (접이식) : 좌/우 토큰 쌍 편집 테이블 + Save/Reload -> mirror_tokens.json
        # -------------------------

        self.grp_mir_tokens = QGroupBox("L / R Tokens (mirror_tokens.json)")
        self.grp_mir_tokens.setCheckable(True)
        self.grp_mir_tokens.setChecked(False)
        tok_layout = QVBoxLayout(self.grp_mir_tokens)

        self.tbl_mir_tokens = QTableWidget(0, 2)
        self.tbl_mir_tokens.setHorizontalHeaderLabels(["Left", "Right"])
        self.tbl_mir_tokens.horizontalHeader().setStretchLastSection(True)
        self.tbl_mir_tokens.verticalHeader().setVisible(False)
        self.tbl_mir_tokens.setMaximumHeight(140)
        tok_layout.addWidget(self.tbl_mir_tokens)

        tok_btn_row = QHBoxLayout()
        self.btn_tok_add = QPushButton("Add Row")
        self.btn_tok_del = QPushButton("Remove Row")
        self.btn_tok_save = QPushButton("Save")
        self.btn_tok_reload = QPushButton("Reload")
        for b in (self.btn_tok_add, self.btn_tok_del, self.btn_tok_save, self.btn_tok_reload):
            tok_btn_row.addWidget(b)
        tok_layout.addLayout(tok_btn_row)
        tab_layout.addWidget(self.grp_mir_tokens)

        # -------------------------
        # Mirror 실행 버튼 (구간 미러)
        # -------------------------

        self.btn_mirror = QPushButton("Mirror Selected")
        tab_layout.addWidget(self.btn_mirror)

        # -------------------------
        # Current Frame : 현재 프레임만 미러 (autoKeyframe 재현)
        #   - Start/End/Time 과 무관. 키 있는 채널만 키 갱신, 없으면 포즈만(setAttr).
        # -------------------------

        cf_grp = QGroupBox("Current Frame")
        cf_layout = QVBoxLayout(cf_grp)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Keying"))
        self.mir_cf_key_grp = QButtonGroup(self)
        self.rb_mir_cf_channel = QRadioButton("Per-channel (auto-key)")
        self.rb_mir_cf_object = QRadioButton("Per-object")
        self.rb_mir_cf_channel.setChecked(True)   # 기본 = per-channel (autoKeyframe 동일)
        self.mir_cf_key_grp.addButton(self.rb_mir_cf_channel)
        self.mir_cf_key_grp.addButton(self.rb_mir_cf_object)
        key_row.addWidget(self.rb_mir_cf_channel)
        key_row.addWidget(self.rb_mir_cf_object)
        key_row.addStretch(1)
        cf_layout.addLayout(key_row)

        self.btn_mirror_current = QPushButton("Mirror Current Frame")
        cf_layout.addWidget(self.btn_mirror_current)

        tab_layout.addWidget(cf_grp)

        tab_layout.addStretch(1)

        # -------------------------
        # 상태 초기화 : 토큰 로드, 모드에 따른 리스트 표시
        # -------------------------

        self._mir_load_tokens()
        self._mir_update_mode()

        # -------------------------
        # Signal
        # -------------------------

        self.rb_mir_auto.toggled.connect(self._mir_update_mode)
        self.cb_mir_behavior.toggled.connect(self._mir_update_method)
        self.btn_mir_resolve.clicked.connect(self.on_mir_resolve)
        self.btn_mirror.clicked.connect(self.on_mirror_key)
        self.btn_mirror_current.clicked.connect(self.on_mirror_current_frame)
        self.btn_tok_add.clicked.connect(lambda: self._mir_add_token_row("", ""))
        self.btn_tok_del.clicked.connect(self._mir_del_token_row)
        self.btn_tok_save.clicked.connect(self.on_mir_save_tokens)
        self.btn_tok_reload.clicked.connect(self._mir_load_tokens)

        self._mir_update_method()  # behavior 초기 상태를 Mirror Axis 활성/비활성에 반영

        return tab

    def _build_bake_tab(self):
        """리스트업한 컨트롤러/오브젝트를 구간 dense 키로 굽는 탭.
        A00120_FKIK 의 native bakeResults 베이크를 이식(컨스트레인트 없는 범용 bake).
        대상은 씬 선택이 아니라 Bake List 위젯의 항목이다."""

        tab = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Bake List (재사용 위젯). 리스트업된 항목만 베이크된다.
        # -------------------------

        self.bake_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Bake List", select_label="Select Objects", log_callback=self.log)
        tab_layout.addWidget(self.bake_tsl)

        # -------------------------
        # Range : Current timeline / Custom range
        # -------------------------

        range_mode_row = QHBoxLayout()
        range_mode_row.addWidget(QLabel("Range"))
        self.bake_range_grp = QButtonGroup(self)
        self.rb_bake_timeline = QRadioButton("Current timeline")
        self.rb_bake_custom = QRadioButton("Custom range")
        self.rb_bake_timeline.setChecked(True)   # 기본 = 현재 타임라인 구간
        self.bake_range_grp.addButton(self.rb_bake_timeline)
        self.bake_range_grp.addButton(self.rb_bake_custom)
        range_mode_row.addWidget(self.rb_bake_timeline)
        range_mode_row.addWidget(self.rb_bake_custom)
        range_mode_row.addStretch(1)
        tab_layout.addLayout(range_mode_row)

        # Custom 구간 입력 (Custom 모드에서만 활성). 기본값 = 현재 playback 범위.
        validator = QIntValidator(-1000000, 1000000, self)
        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        self.bake_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=time_str, end_value=time_end, log_callback=self.log)
        self.le_bake_start = self.bake_range.start_edit
        self.le_bake_end = self.bake_range.end_edit
        range_row.addWidget(self.bake_range)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Channels (Translate / Rotate / Scale). 기본 T·R on, S off.
        # -------------------------

        ch_row = QHBoxLayout()
        ch_row.addWidget(QLabel("Channels"))
        self.cb_bake_t = QCheckBox("Translate")
        self.cb_bake_r = QCheckBox("Rotate")
        self.cb_bake_s = QCheckBox("Scale")
        self.cb_bake_t.setChecked(True)
        self.cb_bake_r.setChecked(True)
        ch_row.addWidget(self.cb_bake_t)
        ch_row.addWidget(self.cb_bake_r)
        ch_row.addWidget(self.cb_bake_s)
        ch_row.addStretch(1)
        tab_layout.addLayout(ch_row)

        # -------------------------
        # Options : Keep constraints (기본 ON -> disableImplicitControl=False), Simulation
        # -------------------------

        self.cb_bake_keep_con = QCheckBox("Keep constraints (insert blend)")
        self.cb_bake_keep_con.setChecked(True)   # 기본 유지 -> dic=False
        tab_layout.addWidget(self.cb_bake_keep_con)

        self.cb_bake_sim = QCheckBox("Simulation")
        self.cb_bake_sim.setChecked(True)
        tab_layout.addWidget(self.cb_bake_sim)

        # -------------------------
        # Smart bake : native bakeResults -smart (Maya 2020+). 허용오차 이내 중간 키를
        # C++ 내부에서 제거해 키 수를 줄인다. 끄면 매 프레임 dense.
        # -------------------------

        self.cb_bake_smart = QCheckBox("Smart bake (reduce keys)")
        self.cb_bake_smart.setChecked(False)
        tab_layout.addWidget(self.cb_bake_smart)

        smart_row = QHBoxLayout()
        smart_row.addWidget(QLabel("Tolerance"))
        self.le_bake_smart_tol = QLineEdit("0.5")
        self.le_bake_smart_tol.setValidator(QDoubleValidator(0.0, 1000.0, 3, self))
        smart_row.addWidget(self.le_bake_smart_tol)
        smart_row.addStretch(1)
        tab_layout.addLayout(smart_row)

        # -------------------------
        # Bake 버튼
        # -------------------------

        self.btn_bake = QPushButton("Bake List")
        tab_layout.addWidget(self.btn_bake)

        tab_layout.addStretch(1)

        # 초기 활성 상태 동기화 + 시그널
        self._bake_update_range_mode()
        self._bake_update_smart_mode()
        self.rb_bake_custom.toggled.connect(self._bake_update_range_mode)
        self.cb_bake_smart.toggled.connect(self._bake_update_smart_mode)
        self.btn_bake.clicked.connect(self.on_bake)

        return tab

    def _build_follow_tab(self):
        """좌(Target) / 우(Follower) 리스트로, follower 가 같은 인덱스의 target 의 월드
        위치/회전(/스케일)과 동일해지도록 구간 키를 굽는 탭. rotateOrder 무관.
        blend(0..1) 로 원본 follower 애니메이션과 매치 결과를 섞고, 선택된 애니메이션
        레이어에 키가 들어간다."""

        tab = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # Target / Follower 리스트 (재사용 위젯, 가로 2분할). Copy Key 탭과 동일 구성.
        # -------------------------

        self.follow_tgt_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Target", select_label="Select Targets", log_callback=self.log)
        self.follow_flw_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Follower", select_label="Select Followers", log_callback=self.log)

        list_row = QHBoxLayout()
        list_row.addWidget(self.follow_tgt_tsl)
        list_row.addWidget(self.follow_flw_tsl)
        tab_layout.addLayout(list_row)

        # -------------------------
        # Time range (start / end). 기본값은 현재 playback 범위.
        # -------------------------

        validator = QIntValidator(-1000000, 1000000, self)
        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        self.follow_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=time_str, end_value=time_end, log_callback=self.log)
        self.le_follow_start = self.follow_range.start_edit
        self.le_follow_end = self.follow_range.end_edit
        range_row.addWidget(self.follow_range)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Channels (Translate / Rotate / Scale). 기본 T·R on, S off. (Bake 탭과 동일)
        # -------------------------

        ch_row = QHBoxLayout()
        ch_row.addWidget(QLabel("Channels"))
        self.cb_follow_t = QCheckBox("Translate")
        self.cb_follow_r = QCheckBox("Rotate")
        self.cb_follow_s = QCheckBox("Scale")
        self.cb_follow_t.setChecked(True)
        self.cb_follow_r.setChecked(True)
        ch_row.addWidget(self.cb_follow_t)
        ch_row.addWidget(self.cb_follow_r)
        ch_row.addWidget(self.cb_follow_s)
        ch_row.addStretch(1)
        tab_layout.addLayout(ch_row)

        # -------------------------
        # Options
        #   Maintain Offset : start 프레임의 target↔follower 상대 거리/회전을 유지
        #                     (parentConstraint maintainOffset=True, 행렬 연산 구현).
        #   1<-n            : target 1개를 모든 follower 가 따름. off 면 n<-n(인덱스 1:1).
        # -------------------------

        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("Options"))
        self.cb_follow_offset = QCheckBox("Maintain Offset")
        self.cb_follow_one_to_many = QCheckBox("1 <- n")
        self.cb_follow_one_to_many.setToolTip(
            "On: every follower follows the single target (1<-n).\n"
            "Off: index-matched, Target[i] -> Follower[i] (n<-n).")
        opt_row.addWidget(self.cb_follow_offset)
        opt_row.addWidget(self.cb_follow_one_to_many)
        opt_row.addStretch(1)
        tab_layout.addLayout(opt_row)

        # -------------------------
        # Blend (0..1). LineEdit 와 Slider(0..100) 를 동기화. 기본 1.0(완전 매치).
        # -------------------------

        blend_row = QHBoxLayout()
        blend_row.addWidget(QLabel("Blend (0..1)"))
        self.le_follow_blend = QLineEdit("1.0")
        self.le_follow_blend.setValidator(QDoubleValidator(0.0, 1.0, 3, self))
        self.le_follow_blend.setMaximumWidth(60)
        blend_row.addWidget(self.le_follow_blend)

        self.sld_follow_blend = QSlider(Qt.Horizontal)
        self.sld_follow_blend.setRange(0, 100)
        self.sld_follow_blend.setValue(100)
        blend_row.addWidget(self.sld_follow_blend)
        tab_layout.addLayout(blend_row)

        # -------------------------
        # Match 버튼
        # -------------------------

        self.btn_follow = QPushButton("Match Follow")
        tab_layout.addWidget(self.btn_follow)

        tab_layout.addStretch(1)

        # Slider <-> LineEdit 동기화 + 실행 시그널
        # (Get Current / Get Sel Range 은 follow_range 위젯이 내부에서 처리한다.)
        self.sld_follow_blend.valueChanged.connect(self._follow_slider_to_le)
        self.le_follow_blend.editingFinished.connect(self._follow_le_to_slider)
        self.btn_follow.clicked.connect(self.on_follow_bake)

        return tab

    def _build_euler_filter_page(self):
        """리스트업한 컨트롤러의 회전 키에 **구간 한정 오일러 필터**를 적용하는 탭.

        마야 그래프 에디터의 `Curves > Euler Filter` 는 선택한 컨트롤러의 **키가 찍힌 전 구간**을
        한꺼번에 처리한다. 여기서는 TSL 로 대상을 고르고 Start/End 로 구간을 잡아 **그 구간 안의
        회전 키만** 필터하고, 나머지 구간은 그대로 둔다. 로직은 EulerFilterManager."""

        tab = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        tab_layout = QVBoxLayout(tab)

        # -------------------------
        # 대상 리스트 (재사용 위젯). 리스트업된 항목만 필터된다(씬 선택 아님).
        # -------------------------

        self.euler_tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Euler Filter List", select_label="List Selected Objects",
            log_callback=self.log)
        tab_layout.addWidget(self.euler_tsl)

        # -------------------------
        # Time range (start / end). 기본값은 현재 playback 범위.
        # -------------------------

        time_str = int(cmds.playbackOptions(query=True, minTime=True))
        time_end = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        self.euler_range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=time_str, end_value=time_end, log_callback=self.log)
        self.le_euler_start = self.euler_range.start_edit
        self.le_euler_end = self.euler_range.end_edit
        range_row.addWidget(self.euler_range)
        tab_layout.addLayout(range_row)

        # -------------------------
        # Anchor 옵션 (기본 ON)
        #   마야의 오일러 필터는 '구간 안 첫 키' 를 기준으로 뒤 키들을 맞춘다. 그래서 플립이
        #   Start 직전에서 시작하면 구간 안 키들끼리는 이미 일관돼 아무것도 고쳐지지 않는다.
        #   이 옵션은 필터 구간을 Start 직전 키까지 넓혀 그 키를 기준으로 삼는다(그 키 값은
        #   바뀌지 않으므로 구간 밖은 그대로다).
        # -------------------------

        self.cb_euler_anchor = QCheckBox("Anchor to the key before Start (seamless)")
        self.cb_euler_anchor.setChecked(True)
        self.cb_euler_anchor.setToolTip(
            "On: use the last key before Start as the reference, so the filtered\n"
            "range stays continuous with the animation in front of it.\n"
            "That key keeps its value - keys outside the range are never changed.\n"
            "Off: the first key inside the range is the reference.")
        tab_layout.addWidget(self.cb_euler_anchor)

        # -------------------------
        # 안내 : 무엇을 건드리고 무엇을 안 건드리는지
        # -------------------------

        self.lbl_euler_hint = QLabel(
            "Filters rotateX / Y / Z keys inside [Start, End] only.\n"
            "Keys outside the range keep their values, so a step can appear at End.")
        self.lbl_euler_hint.setWordWrap(True)
        tab_layout.addWidget(self.lbl_euler_hint)

        # -------------------------
        # 실행 버튼
        #   위 : 원버튼. 리스트/구간을 채우는 단계 없이 **씬 선택 + 선택한 키**를 그대로 읽어
        #        바로 실행한다(그래프 에디터에서 구간을 드래그로 고르는 실제 작업 흐름).
        #   아래: 기존 버튼. 리스트업한 대상 + 위 Start/End 칸의 구간으로 실행한다.
        # -------------------------

        self.btn_euler_filter_sel = QPushButton("Euler Filter from Selection")
        self.btn_euler_filter_sel.setToolTip(
            "One click: targets = objects selected in the scene,\n"
            "range = first / last frame of the keys selected in the\n"
            "Graph Editor or Time Slider.\n"
            "The list and Start / End above are filled with what was used.")
        tab_layout.addWidget(self.btn_euler_filter_sel)

        self.btn_euler_filter = QPushButton("Euler Filter in Range")
        self.btn_euler_filter.setToolTip(
            "Use the objects in the list above and the Start / End values.")
        tab_layout.addWidget(self.btn_euler_filter)

        tab_layout.addStretch(1)

        self.btn_euler_filter_sel.clicked.connect(self.on_euler_filter_from_selection)
        self.btn_euler_filter.clicked.connect(self.on_euler_filter)

        return tab

    # ---------------- Curve > Filters (Smooth / Intensity / Interp) ----------------
    #
    # 세 필터를 **한 화면**에 접이식 섹션으로 담는다(ref/ref_01.png 의 원본 UI 구성과 같다).
    # 보통 이 저장소는 섹션이 3개를 넘으면 하위 탭으로 가지만([[prefer-subtabs...]]), 여기서는
    # 섹션 하나가 슬라이더 한 줄 + 버튼 한 줄이라 작고, **셋을 번갈아 눌러 가며** 다듬는 작업이라
    # 탭을 오가는 편이 오히려 번거롭다.
    #
    # 대상은 **리스트도 Start/End 도 아니다** — 지금 **그래프 에디터에서 고른 키**(없으면 타임
    # 슬라이더 구간 + 씬 선택)다. 고른 것이 없으면 아무것도 하지 않는다.
    #
    # 조작 모델(A00110 Stagger Offset · A00380 Peak 에서 검증한 settle 커밋):
    #   드래그 중  : undo 를 기록하지 않고 **원본 스냅샷에서 다시 계산**해 미리보기(누적 없음)
    #   놓는 순간  : 그때까지의 결과를 **undo 한 항목**으로 확정하고 슬라이더를 0 으로 되돌린다

    def _cf_slider(self, left, right):
        """가운데가 0(변화 없음)인 양방향 슬라이더 한 줄. (row, slider)"""
        row = QHBoxLayout()
        lbl_left = QLabel(left)
        lbl_left.setMinimumWidth(58)
        row.addWidget(lbl_left)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(-100, 100)
        slider.setValue(0)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(100)
        slider.setPageStep(10)
        slider.setMinimumWidth(150)
        slider.setStyleSheet(STAGGER_SLIDER_STYLE)
        slider.setToolTip(
            "Drag to apply live; the middle (0) is 'no change'.\n"
            "Let go and the result is committed as ONE undo step and the slider\n"
            "returns to the middle - push again to apply another pass.")
        row.addWidget(slider, 1)

        lbl_right = QLabel(right)
        lbl_right.setAlignment(Qt.AlignRight)
        lbl_right.setMinimumWidth(72)
        row.addWidget(lbl_right)
        return row, slider

    def _cf_buttons(self, kind, entries):
        """원클릭 버튼 한 줄. entries = [(라벨, amount, shape), ...]"""
        row = QHBoxLayout()
        for label, amount, shape in entries:
            btn = QPushButton(label)
            btn.setToolTip("Apply in one click (one undo step).")
            btn.clicked.connect(
                lambda _checked=False, k=kind, a=amount, sh=shape:
                self._cf_apply_once(k, a, shape=sh))
            row.addWidget(btn)
        return row

    def _build_curve_filters_page(self):
        """Smooth / Intensity / Interpolate 를 한 화면에 담은 페이지."""
        page = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        page_layout = QVBoxLayout(page)

        # 필터 종류별 세션/타이머는 페이지와 수명을 같이한다(지연 생성하면 아직 없는
        # 상태를 호출측이 신경 써야 한다).
        self._cf_sessions = {}
        self._cf_timers = {}

        # ---- Expand : 본문을 별도 창으로 (공용 위젯 JUN_mod_expand_qt_v01)
        #      그래프 에디터를 크게 띄워 놓고 필터만 옆에 두는 배치를 위해서다.
        #      복제가 아니라 **이동**이라 슬라이더·세션·undo 가 한 벌뿐이다(공용 위젯 주석 참고).
        self.cf_panel = JUN_mod_expand_qt.JUN_mod_expand_qt_v01(
            title="Curve Filters",
            placeholder="Curve Filters are shown in the expanded window.",
            object_name=CURVE_FILTERS_WINDOW_OBJECT_NAME,
            size=(420, 460))
        self.cf_panel.expanded_changed.connect(
            lambda *_: self._fit_window_later())
        page_layout.addWidget(self.cf_panel)

        layout = self.cf_panel.body

        # ---- 대상 안내 + 공통 옵션
        hint = QLabel(
            "Works on the keys selected in the Graph Editor.\n"
            "Nothing selected? Highlight a range in the Time Slider and select the "
            "objects instead.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.cf_quat = QCheckBox("Use Quaternions")
        self.cf_quat.setChecked(True)
        self.cf_quat.setToolTip(
            "On (default): rotateX / Y / Z are filtered together as a quaternion, so the\n"
            "three axes cannot drift apart near gimbal lock. Converted back to the euler\n"
            "values nearest the originals, so no +-360 jump appears.\n"
            "Objects whose rotate keys sit on different frames fall back to per-channel\n"
            "and are reported.\n"
            "Off: every channel is filtered on its own.")
        layout.addWidget(self.cf_quat)

        # ---- Smooth
        sec_smooth = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            title="Smooth", expanded=True)

        opt = QHBoxLayout()
        opt.addWidget(QLabel("Iterations"))
        self.cf_smooth_iter = QSpinBox()
        self.cf_smooth_iter.setRange(1, 20)
        self.cf_smooth_iter.setValue(3)
        self.cf_smooth_iter.setKeyboardTracking(False)
        self.cf_smooth_iter.setToolTip(
            "How many smoothing passes. More passes reach further along the curve.")
        opt.addWidget(self.cf_smooth_iter)
        opt.addWidget(QLabel("Strength"))
        self.cf_smooth_strength = QSpinBox()
        self.cf_smooth_strength.setRange(0, 100)
        self.cf_smooth_strength.setValue(100)
        self.cf_smooth_strength.setSuffix(" %")
        self.cf_smooth_strength.setKeyboardTracking(False)
        self.cf_smooth_strength.setToolTip(
            "Overall scale on the slider amount. 100% = the slider means what it says.")
        opt.addWidget(self.cf_smooth_strength)
        opt.addStretch(1)
        sec_smooth.add_layout(opt)

        row, self.cf_smooth_slider = self._cf_slider("Rough", "Smooth")
        sec_smooth.add_layout(row)
        sec_smooth.add_layout(self._cf_buttons(
            "smooth", [("-100", -100, None), ("-50", -50, None),
                       ("50", 50, None), ("100", 100, None)]))
        layout.addWidget(sec_smooth)
        self.cf_sec_smooth = sec_smooth

        # ---- Intensity
        sec_intensity = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            title="Intensity", expanded=True)
        row, self.cf_intensity_slider = self._cf_slider("Minus", "Plus")
        sec_intensity.add_layout(row)
        sec_intensity.add_layout(self._cf_buttons(
            "intensity", [("-50", -50, None), ("-25", -25, None),
                          ("25", 25, None), ("50", 50, None)]))
        layout.addWidget(sec_intensity)
        self.cf_sec_intensity = sec_intensity

        # ---- Interpolate
        sec_interp = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            title="Interpolate", expanded=True)
        row_a, self.cf_interp_slider_a = self._cf_slider("Ease-In", "Ease-Out")
        sec_interp.add_layout(row_a)
        row_b, self.cf_interp_slider_b = self._cf_slider("Linear", "Ease-In-Out")
        sec_interp.add_layout(row_b)
        sec_interp.add_layout(self._cf_buttons(
            "interpolate", [("Ease-In", 100, CF_EASE_IN),
                            ("Ease-Out", 100, CF_EASE_OUT),
                            ("Linear", 100, CF_LINEAR),
                            ("Ease-In-Out", 100, CF_EASE_IN_OUT)]))
        layout.addWidget(sec_interp)
        self.cf_sec_interp = sec_interp

        page_layout.addStretch(1)

        # ---- 배선
        self._cf_connect("smooth", self.cf_smooth_slider)
        self._cf_connect("intensity", self.cf_intensity_slider)
        self._cf_connect("interpolate", self.cf_interp_slider_a)
        self._cf_connect("interpolate", self.cf_interp_slider_b)
        for section in (sec_smooth, sec_intensity, sec_interp):
            section.toggled.connect(self._fit_window_later)

        return page

    def _build_graph_focus_tab(self):
        """선택한 컨트롤러의 전체 키 구간을 다 보여주는 대신, 현재 프레임 기준
        ± margin 프레임만 그래프 에디터에 확대해서 보여주는 탭.

        토글이 켜져 있으면 SelectionChanged 를 감시하다가 선택이 바뀔 때마다
        그래프 에디터를 [현재프레임-margin, 현재프레임+margin] 구간으로 프레이밍한다.
        margin(예: 80) 은 아래 스핀박스로 사용자가 지정한다."""

        tab = JUN_mod_collapsible_qt.JUN_mod_fit_tab_page_v01()
        tab_layout = QVBoxLayout(tab)

        grp = QGroupBox("Focus Graph Editor around Current Frame")
        grp_layout = QVBoxLayout(grp)

        # -------------------------
        # On/Off 토글 버튼 (선택 시 자동 프레이밍)
        # -------------------------

        self.btn_graph_focus = QPushButton("Auto-Focus on Selection : OFF")
        self.btn_graph_focus.setCheckable(True)
        self.btn_graph_focus.setToolTip(
            "When ON, selecting a controller frames the Graph Editor to\n"
            "[current frame - margin, current frame + margin] instead of its\n"
            "whole keyed range.")
        grp_layout.addWidget(self.btn_graph_focus)

        # -------------------------
        # margin(± 프레임) 입력. 사용자가 '80' 같은 값을 여기서 정한다.
        # -------------------------

        margin_row = QHBoxLayout()
        margin_row.addWidget(QLabel("Frame margin (±)"))
        self.sb_graph_margin = QSpinBox()
        self.sb_graph_margin.setRange(1, 100000)
        self.sb_graph_margin.setValue(80)
        self.sb_graph_margin.setSuffix(" f")
        self.sb_graph_margin.setToolTip(
            "Frames to show before and after the current frame.\n"
            "e.g. current 500f, margin 80  ->  shows 420f ~ 580f")
        margin_row.addWidget(self.sb_graph_margin)
        margin_row.addStretch(1)
        grp_layout.addLayout(margin_row)

        # -------------------------
        # 세로(값) 축도 구간에 맞춰 자동으로 프레이밍할지 (기본 ON)
        # -------------------------

        self.cb_graph_fit_value = QCheckBox("Fit value (vertical) axis too")
        self.cb_graph_fit_value.setChecked(True)
        self.cb_graph_fit_value.setToolTip(
            "Also fit the vertical (value) axis to the curve values inside\n"
            "the visible window. Off: keep the current vertical zoom.")
        grp_layout.addWidget(self.cb_graph_fit_value)

        # -------------------------
        # 세로(값) 위/아래 여백(%) — 최댓값/최솟값이 뷰 가장자리에 딱 붙지 않도록.
        # 사용자가 5~10% 정도로 조절한다(기본 10%).
        # -------------------------

        pad_row = QHBoxLayout()
        pad_row.addWidget(QLabel("Value margin (%)"))
        self.sb_graph_value_pad = QSpinBox()
        self.sb_graph_value_pad.setRange(0, 100)
        self.sb_graph_value_pad.setValue(10)
        self.sb_graph_value_pad.setSuffix(" %")
        self.sb_graph_value_pad.setToolTip(
            "Top/bottom padding for the value axis, as a % of the value range.\n"
            "e.g. 10% keeps the min/max a little inside the top/bottom edges.")
        pad_row.addWidget(self.sb_graph_value_pad)
        pad_row.addStretch(1)
        grp_layout.addLayout(pad_row)

        # -------------------------
        # 토글과 무관하게 지금 한 번만 프레이밍
        # -------------------------

        self.btn_graph_focus_now = QPushButton("Focus Now")
        self.btn_graph_focus_now.setToolTip(
            "Frame the Graph Editor around the current frame once, without\n"
            "turning on the auto-focus toggle.")
        grp_layout.addWidget(self.btn_graph_focus_now)

        tab_layout.addWidget(grp)
        tab_layout.addStretch(1)

        # -------------------------
        # Signal
        # -------------------------

        self.btn_graph_focus.toggled.connect(self.on_toggle_graph_focus)
        self.btn_graph_focus_now.clicked.connect(self.on_graph_focus_now)
        # margin / fit / 여백 값이 바뀌면, 토글이 켜져 있을 때 즉시 다시 프레이밍한다.
        self.sb_graph_margin.valueChanged.connect(self._graph_focus_reapply)
        self.cb_graph_fit_value.toggled.connect(self._graph_focus_reapply)
        self.sb_graph_value_pad.valueChanged.connect(self._graph_focus_reapply)

        return tab

    # --------------------------------------------------
    # Helper
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def on_force_refresh(self):
        """막힌 전역 refresh suspend 를 풀고 뷰포트를 한 번 강제로 그린다."""
        force_refresh()
        self.log("Viewport refresh restored.")

    def _read_range(self):
        """start, end 파싱. 실패 시 None."""
        s_txt = self.le_start.text().strip()
        e_txt = self.le_end.text().strip()

        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return None

        start = int(s_txt)
        end = int(e_txt)

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return None

        return (start, end)

    def _read_offset(self):
        """offset(양수) 파싱. 실패 시 None."""
        o_txt = self.le_offset.text().strip()

        if o_txt == "":
            self.log("[Warning] Enter Offset.")
            return None

        return abs(int(o_txt))

    # --------------------------------------------------
    # Handlers
    # --------------------------------------------------

    # --------------------------------------------------
    # Handlers : Key > Fill Keys
    # --------------------------------------------------

    def on_fill_list_attrs(self):
        """리스트업한 오브젝트들의 키 가능 채널을 합집합으로 나열한다."""
        objs = self.fill_tsl.get_all_items()
        if not objs:
            self.log("[Warning] Add objects to the Objects list first.")
            return

        attrs = FillKeyManager.list_keyable_attrs(objs)

        self.lw_fill_attrs.clear()
        self.lw_fill_attrs.addItems(attrs)
        shown, total = self.flt_fill.refresh()

        if not attrs:
            self.log("[Warning] No keyable channel found on the listed objects.")
            return

        msg = "{0} channel(s) from {1} object(s).".format(total, len(objs))
        if shown != total:
            msg += " Filter '{0}' shows {1}.".format(
                self.flt_fill.text().strip(), shown)
        self.log(msg)

    def on_fill_refresh_layers(self, quiet=False):
        """씬의 애니메이션 레이어를 다시 훑어 콤보를 채운다.

        지금 고른 항목은 최대한 유지하고, 처음 채울 때는 **선택된 레이어**를 기본값으로 쓴다.
        """
        keep = self.cmb_fill_layer.currentText() if self.cmb_fill_layer.count() else ""

        layers, selected = FillKeyManager.list_anim_layers()

        self.cmb_fill_layer.blockSignals(True)
        self.cmb_fill_layer.clear()
        self.cmb_fill_layer.addItem(CURRENT_LAYER)
        self.cmb_fill_layer.addItems(layers)

        target = keep if keep in ([CURRENT_LAYER] + layers) else (
            selected or CURRENT_LAYER)
        self.cmb_fill_layer.setCurrentText(target)
        self.cmb_fill_layer.blockSignals(False)

        if not quiet:
            if layers:
                self.log("Anim layers: {0}  (using '{1}')".format(
                    ", ".join(layers), self.cmb_fill_layer.currentText()))
            else:
                self.log("No anim layer in the scene; keys go on the base curves.")

    def _fill_selected_attrs(self):
        """**보이면서 선택된** 채널 이름들.

        Qt 는 필터로 숨긴 항목의 선택도 유지하므로, 가려진 채널까지 키를 찍지 않도록 거른다.
        """
        names, hidden = self.flt_fill.visible_selected()
        if hidden:
            self.log("[Info] {0} selected channel(s) hidden by the filter were "
                     "skipped.".format(hidden))
        return names

    def on_fill_keys_from_selection(self):
        """원버튼 — **그래프 에디터에서 고른 키**가 대상·채널·구간을 모두 정한다.

        Curve > Euler 탭의 `Euler Filter from Selection` 과 같은 원리다. 실제 작업은
        "그래프 에디터에서 채울 구간의 키를 드래그로 고른다" 로 끝나는데, 기존 버튼은 그걸
        다시 List Selected Objects -> List Attributes -> 채널 고르기 -> Start/End 네 단계로
        옮겨 담아야 했다.

        감지한 값은 **위젯에도 채워 넣는다** — 무엇을 어느 구간으로 처리했는지 눈으로 확인되고,
        이어서 채널이나 레이어만 바꿔 아래 버튼으로 다시 돌릴 수 있다.

        고른 키가 없으면 **실행하지 않는다.** 대상을 못 정한 채 전 구간을 찍는 쪽이 위험하다
        (Euler 탭에서 세운 것과 같은 규칙).
        """
        objs, attrs, start, end, message = FillKeyManager.targets_from_selection()
        if message:
            self.log(("[Warning] " if objs is None else "") + message)
        if objs is None:
            return

        # 감지 결과를 위젯에 되채운다(리스트 -> 채널 목록 -> 채널 선택 -> 구간).
        self.fill_tsl.set_items(objs)
        self.on_fill_list_attrs()
        self.flt_fill.clear()          # 필터에 가려 선택이 무시되지 않도록 비운다
        selected = 0
        for i in range(self.lw_fill_attrs.count()):
            item = self.lw_fill_attrs.item(i)
            picked = item.text() in attrs
            item.setSelected(picked)
            selected += 1 if picked else 0
        self.fill_range.set_range(start, end)

        if not selected:
            self.log("[Warning] The selected keys drive channels that are not in "
                     "the list ({0}).".format(", ".join(attrs)))
            return

        self.log("[From Selection] {0} object(s) x {1} channel(s), range "
                 "[{2}-{3}f] from the selected keys.".format(
                     len(objs), selected, start, end))
        self.on_fill_keys()

    def on_fill_keys(self):
        objs = self.fill_tsl.get_all_items()
        if not objs:
            self.log("[Warning] Add objects to the Objects list first.")
            return

        attrs = self._fill_selected_attrs()
        if not attrs:
            self.log("[Warning] Select the channels to fill "
                     "(press 'List Attributes', then pick them).")
            return

        rng = self.fill_range.values()
        if rng is None:
            self.log("[Warning] Enter Start / End.")
            return
        start, end = rng

        layer = self.cmb_fill_layer.currentText()
        layer = None if layer == CURRENT_LAYER else layer
        if layer and not cmds.objExists(layer):
            self.log("[Warning] Anim layer '{0}' is gone; refreshing the "
                     "list.".format(layer))
            self.on_fill_refresh_layers()
            return

        try:
            added, skipped, messages = FillKeyManager.fill_keys(
                objs, attrs, start, end, layer=layer)
        except Exception as e:
            self.log("[Error] {0}".format(e))
            cmds.warning(str(e))
            return

        for m in messages:
            self.log(m)

        self.log("Fill Keys: {0} key(s) added, {1} frame(s) already keyed "
                 "(left alone)  [{2}-{3}f, {4} channel(s) x {5} object(s), "
                 "layer: {6}]".format(
                     added, skipped, min(start, end), max(start, end),
                     len(attrs), len(objs), layer or CURRENT_LAYER))

    def on_move(self, sign):

        rng = self._read_range()
        if rng is None:
            return

        offset = self._read_offset()
        if offset is None:
            return

        start, end = rng
        offset = sign * offset   # 앞으로(-) / 뒤로(+)

        count, msg = KeyframeManager.move_keys(start, end, offset)
        self.log(msg)

    def on_delete(self):

        rng = self._read_range()
        if rng is None:
            return

        start, end = rng

        count, msg = KeyframeManager.delete_keys(start, end)
        self.log(msg)

    def on_delete_all(self):

        objs = self.delall_tsl.get_all_items()   # 리스트업된 항목만 (씬 선택 아님)
        if not objs:
            self.log("[Warning] List objects first (List Selected Objects).")
            return

        # Create > Noise 로 만든 노드는 기본적으로 뺀다. 이 노드들의 '키' 는 애니메이션이
        # 아니라 **노이즈 그 자체**라, 여기서 지우면 커브가 통째로 날아가고 output 연결까지
        # 끊긴다. 지우고 싶으면 Noise 탭의 Delete 를 쓰는 게 맞다.
        noise_nodes = [o for o in objs if NoiseNodeManager.is_noise_node(o)]
        if noise_nodes:
            objs = [o for o in objs if o not in noise_nodes]
            self.log("[Warning] Skipping {0} noise node(s) - use Create > Noise > Delete "
                     "for those: {1}".format(len(noise_nodes), ", ".join(noise_nodes[:4])))
            if not objs:
                return

        # 파괴적: 전 구간·전 채널 키 삭제이므로 확인을 받는다(Undo 가능).
        answer = QMessageBox.question(
            self,
            "Delete All Keyframes",
            "Delete ALL keyframes of {0} listed object(s)?\n"
            "This removes every animation curve on them (undoable).".format(len(objs)),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        count, msg = KeyframeManager.delete_all_keys(objs)
        self.log(msg)

    def on_hold(self):

        count, msg = KeyframeManager.hold_selected_keys()
        self.log(msg)

    def on_set_pose(self):

        # 체크된 축만 모은다. 체크됐는데 값이 비어 있으면 경고 후 중단.
        axis_values = {}
        for attr, (cb, le) in self.pose_rows.items():
            if not cb.isChecked():
                continue
            txt = le.text().strip()
            if txt == "":
                self.log(f"[Warning] {attr} is checked but empty.")
                return
            axis_values[attr] = float(txt)

        if not axis_values:
            self.log("[Warning] No axis checked.")
            return

        count, msg = PoseKeyManager.set_pose_keys(axis_values)
        self.log(msg)

    # --------------------------------------------------
    # Create > Noise
    # --------------------------------------------------

    def _noise_fill_list(self, keep=None):
        """씬의 노이즈 노드로 리스트를 다시 채운다. keep 은 다시 고를 노드 이름."""
        if keep is None:
            keep = self._noise_current()

        self._noise_updating = True
        try:
            self.noise_list.clear()
            for node in NoiseNodeManager.find_all():
                item = QListWidgetItem(NoiseNodeManager.summary(node))
                # 이름이 아니라 UUID 를 들고 있는다 — 리네임이나 동명 노드에도 안전하다.
                item.setData(Qt.UserRole, cmds.ls(node, uuid=True)[0])
                self.noise_list.addItem(item)

            if keep:
                for row in range(self.noise_list.count()):
                    if self._noise_node_of(self.noise_list.item(row)) == keep:
                        self.noise_list.setCurrentRow(row)
                        break
            elif self.noise_list.count():
                self.noise_list.setCurrentRow(0)
        finally:
            self._noise_updating = False

        self._noise_load_settings()

    @staticmethod
    def _noise_node_of(item):
        """리스트 항목이 가리키는 노드의 **현재** 이름. 사라졌으면 None."""
        if item is None:
            return None
        uuid = item.data(Qt.UserRole)
        names = cmds.ls(uuid) if uuid else []
        return names[0] if names else None

    def _noise_current(self):
        """지금 편집 대상인 노드 하나(리스트에서 마지막으로 고른 것)."""
        return self._noise_node_of(self.noise_list.currentItem())

    def _noise_selected(self):
        """리스트에서 고른 노드 전부(삭제/선택용)."""
        found = []
        for item in self.noise_list.selectedItems():
            node = self._noise_node_of(item)
            if node and node not in found:
                found.append(node)
        return found

    def _noise_session(self):
        """지금 노드의 슬라이더 세션. 씬이 세션의 가정과 어긋나면 새로 만든다.

        사용자가 Ctrl+Z 를 눌렀거나 채널박스에서 값을 직접 고치면 세션의 전제가 깨진다.
        그 상태로 계속 밀면 엉뚱한 값을 기준으로 되돌리게 되므로 세션을 버린다.
        """
        node = self._noise_current()
        if not node:
            self._noise_sess = None
            return None

        sess = self._noise_sess
        if sess is None or sess.node != node or not sess.valid() or not sess.in_sync():
            sess = NoiseSession(node)
            self._noise_sess = sess
        return sess

    def _noise_load_settings(self):
        """선택 노드의 설정을 위젯에 채운다. 노드가 없으면 설정 영역을 비활성화."""
        node = self._noise_current()
        has = bool(node)

        self.noise_set_grp.setEnabled(has)
        self.btn_noise_graph.setEnabled(has)
        self.btn_noise_connect.setEnabled(has)
        self.btn_noise_disconnect.setEnabled(has)
        self.btn_noise_delete.setEnabled(bool(self._noise_selected()))

        if not has:
            self.lbl_noise_targets.setText("No noise node selected.")
            self._noise_sess = None
            return

        s = NoiseNodeManager.read_settings(node)

        self._noise_updating = True
        try:
            self.cmb_noise_type.setCurrentText(s["kind"])
            self.sb_noise_smooth.setValue(s["smoothness"])
            self.sld_noise_smooth.setValue(self._noise_clamp_slider(
                s["smoothness"] * NOISE_SMOOTH_SLIDER_SCALE, NOISE_SMOOTH_SLIDER_STEPS))
            self.sb_noise_offset.setValue(s["offset"])
            self.sld_noise_offset.setValue(self._noise_clamp_slider(
                s["offset"] * NOISE_OFFSET_SLIDER_SCALE, NOISE_OFFSET_SLIDER_STEPS))
            self.sb_noise_min.setValue(s["out_min"])
            self.sb_noise_max.setValue(s["out_max"])
            self.sb_noise_seed.setValue(s["seed"])
            self.cmb_noise_length.setCurrentText("{0} f".format(s["length"]))
        finally:
            self._noise_updating = False

        self._noise_sess = NoiseSession(node)
        self._noise_update_targets()

    @staticmethod
    def _noise_clamp_slider(value, steps):
        """슬라이더가 담당하는 구간 밖의 값은 끝에 붙여 둔다(값 자체는 스핀박스가 들고 있다)."""
        return int(max(-steps, min(steps, round(value))))

    def _noise_update_targets(self):
        """output 이 무엇을 구동 중인지 라벨에 적는다."""
        node = self._noise_current()
        targets = NoiseNodeManager.output_targets(node) if node else []
        if not targets:
            self.lbl_noise_targets.setText("Not connected.")
            return
        shown = ", ".join(targets[:6])
        if len(targets) > 6:
            shown += " (+{0} more)".format(len(targets) - 6)
        self.lbl_noise_targets.setText("Driving {0}: {1}".format(len(targets), shown))

    def _noise_widget_params(self):
        """위젯이 들고 있는 미리보기 대상 값들."""
        return {
            "smoothness": self.sb_noise_smooth.value(),
            "offset": self.sb_noise_offset.value(),
            "out_min": self.sb_noise_min.value(),
            "out_max": self.sb_noise_max.value(),
        }

    # ---------------- 리스트 조작 ----------------

    def on_noise_create(self):
        node, msg = NoiseNodeManager.create()
        self.log(msg)
        self._noise_fill_list(keep=node)

    def on_noise_delete(self):
        nodes = self._noise_selected()
        if not nodes:
            self.log("[Warning] Select a noise node in the list first.")
            return

        answer = QMessageBox.question(
            self, "Delete Noise Node",
            "Delete {0} noise node(s)?\n"
            "Anything they drive stops being animated (undoable).".format(len(nodes)),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return

        self._noise_settle_timer.stop()
        self._noise_sess = None
        _count, msg = NoiseNodeManager.delete(nodes)
        self.log(msg)
        self._noise_fill_list(keep=None)

    def on_noise_reload(self):
        self._noise_settle_timer.stop()
        self._noise_sess = None
        self._noise_fill_list()
        self.log("{0} noise node(s) in the scene.".format(self.noise_list.count()))

    def on_noise_select(self):
        nodes = self._noise_selected()
        if not nodes:
            self.log("[Warning] Select a noise node in the list first.")
            return
        cmds.select(nodes, replace=True)
        self.log("Selected {0} noise node(s).".format(len(nodes)))

    def _noise_selection_changed(self):
        if self._noise_updating:
            return
        # 다른 노드로 넘어가기 전에, 아직 기록되지 않은 미리보기를 확정한다.
        self._noise_settle_timer.stop()
        self._noise_settle()
        self._noise_sess = None
        self._noise_load_settings()

    # ---------------- 슬라이더 / 스핀박스 ----------------

    def _noise_preview(self):
        """위젯 값으로 즉시 반영(undo 미기록) + 확정 타이머 재시작."""
        sess = self._noise_session()
        if sess is None:
            return
        sess.preview(**self._noise_widget_params())
        self._noise_settle_timer.start()

    def _noise_smooth_slider_changed(self, *_a):
        if self._noise_updating:
            return
        self._noise_updating = True
        try:
            self.sb_noise_smooth.setValue(
                self.sld_noise_smooth.value() / float(NOISE_SMOOTH_SLIDER_SCALE))
        finally:
            self._noise_updating = False
        self._noise_preview()

    def _noise_smooth_spin_changed(self, *_a):
        if self._noise_updating:
            return
        self._noise_updating = True
        try:
            self.sld_noise_smooth.setValue(self._noise_clamp_slider(
                self.sb_noise_smooth.value() * NOISE_SMOOTH_SLIDER_SCALE,
                NOISE_SMOOTH_SLIDER_STEPS))
        finally:
            self._noise_updating = False
        self._noise_preview()

    def _noise_offset_slider_changed(self, *_a):
        if self._noise_updating:
            return
        self._noise_updating = True
        try:
            self.sb_noise_offset.setValue(
                self.sld_noise_offset.value() / float(NOISE_OFFSET_SLIDER_SCALE))
        finally:
            self._noise_updating = False
        self._noise_preview()

    def _noise_offset_spin_changed(self, *_a):
        if self._noise_updating:
            return
        self._noise_updating = True
        try:
            self.sld_noise_offset.setValue(self._noise_clamp_slider(
                self.sb_noise_offset.value() * NOISE_OFFSET_SLIDER_SCALE,
                NOISE_OFFSET_SLIDER_STEPS))
        finally:
            self._noise_updating = False
        self._noise_preview()

    def _noise_range_changed(self, *_a):
        if self._noise_updating:
            return
        self._noise_preview()

    def _noise_settle(self):
        """미리보기를 undo 큐에 한 항목으로 기록한다(조작이 멎었거나 손을 뗐을 때)."""
        self._noise_settle_timer.stop()

        sess = self._noise_sess
        if sess is None or not sess.valid():
            return

        _count, msg = sess.settle(**self._noise_widget_params())
        if msg:
            self.log(msg)
            self._noise_refresh_row()

    def _noise_refresh_row(self):
        """리스트에서 지금 노드의 요약 줄만 다시 쓴다(선택 상태를 건드리지 않는다)."""
        item = self.noise_list.currentItem()
        node = self._noise_node_of(item)
        if item and node:
            self._noise_updating = True
            try:
                item.setText(NoiseNodeManager.summary(node))
            finally:
                self._noise_updating = False

    # ---------------- 콤보 / 시드 / 리셋 ----------------

    def _noise_commit_combo(self, *_a):
        """Type · Loop Length 변경. 한 번에 끝나는 조작이라 곧장 확정한다."""
        if self._noise_updating:
            return
        sess = self._noise_session()
        if sess is None:
            return

        self._noise_settle_timer.stop()
        params = self._noise_widget_params()
        params["kind"] = self.cmb_noise_type.currentText()
        params["length"] = self.cmb_noise_length.currentData()

        _count, msg = sess.settle(**params)
        if msg:
            self.log(msg)
        self._noise_refresh_row()

    def _noise_commit_seed(self, *_a):
        if self._noise_updating:
            return
        sess = self._noise_session()
        if sess is None:
            return

        self._noise_settle_timer.stop()
        params = self._noise_widget_params()
        params["seed"] = self.sb_noise_seed.value()

        _count, msg = sess.settle(**params)
        if msg:
            self.log(msg)
        self._noise_refresh_row()

    def on_noise_randomize(self):
        node = self._noise_current()
        if not node:
            self.log("[Warning] Select a noise node in the list first.")
            return
        # setValue 가 _noise_commit_seed 를 부르므로 여기서 따로 확정하지 않는다.
        self.sb_noise_seed.setValue(NoiseNodeManager.seed_from_name(node))

    def on_noise_reset(self):
        sess = self._noise_sess
        if sess is None or not sess.valid():
            self.log("[Warning] Select a noise node in the list first.")
            return

        self._noise_settle_timer.stop()
        _count, msg = sess.restore()
        self.log(msg or "Noise settings restored.")
        self._noise_load_settings()
        self._noise_refresh_row()

    # ---------------- 보기 / 출력 ----------------

    def on_noise_show_graph(self):
        """노드를 선택하고 그래프 에디터에 output 커브를 띄운다."""
        node = self._noise_current()
        if not node:
            self.log("[Warning] Select a noise node in the list first.")
            return

        cmds.select(node, replace=True)

        editors = GraphViewManager.graph_editors()
        if not editors:
            try:
                import maya.mel as mel
                mel.eval("GraphEditor;")
            except Exception as exc:
                self.log("[Warning] Could not open the Graph Editor: {0}".format(exc))
            editors = GraphViewManager.graph_editors()

        length = NoiseNodeManager.read_settings(node)["length"]
        for editor in editors:
            try:
                cmds.animView(editor, edit=True, startTime=0, endTime=length)
            except Exception:
                pass

        self.log("'{0}.output' selected - the Graph Editor shows the noise curve "
                 "over [0, {1}f].".format(node, length))

    def on_noise_connect(self):
        node = self._noise_current()
        if not node:
            self.log("[Warning] Select a noise node in the list first.")
            return

        plugs = self._noise_target_plugs()
        _count, msg = NoiseNodeManager.connect_output(node, plugs)
        self.log(msg)
        self._noise_update_targets()

    def on_noise_disconnect(self):
        node = self._noise_current()
        if not node:
            self.log("[Warning] Select a noise node in the list first.")
            return
        _count, msg = NoiseNodeManager.disconnect_output(node)
        self.log(msg)
        self._noise_update_targets()

    @staticmethod
    def _noise_target_plugs():
        """채널박스에서 고른 어트리뷰트 x 씬 선택 오브젝트 = 연결 대상 플러그들.

        노이즈 노드 자신은 뺀다 — 자기 output 을 자기한테 물릴 수는 없고,
        'Select' 로 노드를 고른 직후 실수로 누르는 경우를 막는다.
        """
        attrs = cf_selected_channel_attrs() or []
        objs = cmds.ls(selection=True) or []
        objs = [o for o in objs if not NoiseNodeManager.is_noise_node(o)]

        plugs = []
        for obj in objs:
            for attr in attrs:
                plug = "{0}.{1}".format(obj, attr)
                if cmds.objExists(plug) and plug not in plugs:
                    plugs.append(plug)
        return plugs

    def on_copy_key(self):

        base = self.base_tsl.get_all_items()
        tgt = self.tgt_tsl.get_all_items()

        if not base or not tgt:
            self.log("[Warning] Fill both Base and Target lists.")
            return

        # Start / End 파싱 (Copy 탭 전용).
        s_txt = self.le_copy_start.text().strip()
        e_txt = self.le_copy_end.text().strip()

        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return

        start = int(s_txt)
        end = int(e_txt)

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return

        reverse_flags = {key: cb.isChecked() for key, cb in self.copy_reverse.items()}
        attr_flags = {key: cb.isChecked() for key, cb in self.copy_attrs.items()}
        paste_option = self.cmb_paste_option.currentText()

        one_to_many = self.cb_copy_one_to_many.isChecked()

        count, msg = CopyKeyManager.copy_keys(
            base, tgt, start, end, reverse_flags, paste_option,
            one_to_many=one_to_many, attr_flags=attr_flags)
        self.log(msg)

    # --------------------------------------------------
    # Mirror Key
    # --------------------------------------------------

    def _mir_update_mode(self, *args):
        """Auto/Manual 모드에 따라 Source/Target 리스트 표시를 토글."""
        manual = self.rb_mir_manual.isChecked()
        # Auto 모드에서도 Resolve 미리보기를 위해 리스트는 보이게 두되,
        # Manual 일 때만 직접 입력이 주가 된다. 여기서는 항상 표시(미리보기 겸용).
        self.mir_list_row.setVisible(True)
        self.btn_mir_resolve.setVisible(not manual)

    def _mir_update_method(self, *args):
        """Behavior(축 보존) 모드면 Mirror Axis 가 무의미하므로 X/Y/Z 라디오를 비활성화한다.
        (behavior 미러의 좌우 대칭은 레스트 차이에 내장돼 있어 반사축에 무관하다.)"""
        axis_enabled = not self.cb_mir_behavior.isChecked()
        for rb in self.mir_axis_btns.values():
            rb.setEnabled(axis_enabled)

    def _mir_axis(self):
        for ax, rb in self.mir_axis_btns.items():
            if rb.isChecked():
                return ax
        return "x"

    def _mir_read_range(self):
        """Mirror 탭 Start/End 파싱. 실패 시 None."""
        s_txt = self.le_mir_start.text().strip()
        e_txt = self.le_mir_end.text().strip()
        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return None
        start = int(s_txt)
        end = int(e_txt)
        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return None
        return (start, end)

    def _mir_token_pairs(self):
        """현재 토큰 테이블의 (left, right) 쌍 목록(빈 행 제외)."""
        pairs = []
        for r in range(self.tbl_mir_tokens.rowCount()):
            left_item = self.tbl_mir_tokens.item(r, 0)
            right_item = self.tbl_mir_tokens.item(r, 1)
            left = left_item.text().strip() if left_item else ""
            right = right_item.text().strip() if right_item else ""
            if left and right:
                pairs.append((left, right))
        return pairs

    def _mir_add_token_row(self, left="", right=""):
        r = self.tbl_mir_tokens.rowCount()
        self.tbl_mir_tokens.insertRow(r)
        self.tbl_mir_tokens.setItem(r, 0, QTableWidgetItem(left))
        self.tbl_mir_tokens.setItem(r, 1, QTableWidgetItem(right))

    def _mir_del_token_row(self):
        rows = sorted({idx.row() for idx in self.tbl_mir_tokens.selectedIndexes()}, reverse=True)
        if not rows:
            r = self.tbl_mir_tokens.rowCount() - 1
            if r >= 0:
                rows = [r]
        for r in rows:
            self.tbl_mir_tokens.removeRow(r)

    def _mir_load_tokens(self):
        """mirror_tokens.json -> 테이블."""
        pairs, msg = MirrorTokenStore.load()
        self.tbl_mir_tokens.setRowCount(0)
        for left, right in pairs:
            self._mir_add_token_row(left, right)
        self.log(msg)

    def on_mir_save_tokens(self):
        pairs = self._mir_token_pairs()
        if not pairs:
            self.log("[Warning] No valid token pairs to save.")
            return
        count, msg = MirrorTokenStore.save(pairs)
        self.log(msg)

    def on_mir_resolve(self):
        """현재 선택으로 자동 페어링해 Source/Target 리스트를 채운다(미리보기)."""
        sel = cmds.ls(sl=True) or []
        if not sel:
            self.log("[Warning] Select source controllers first.")
            return

        token_pairs = self._mir_token_pairs() or list(MirrorKeyManager.DEFAULT_TOKEN_PAIRS)
        pairs, unpaired, center = MirrorKeyManager.resolve_pairs(sel, token_pairs)

        self.mir_base_tsl.set_items([s for s, _ in pairs])
        self.mir_tgt_tsl.set_items([t for _, t in pairs])

        msg = f"{len(pairs)} pair(s) resolved."
        if center:
            msg += f" {len(center)} center (self-mirror)."
        if unpaired:
            msg += f" {len(unpaired)} unpaired: {', '.join(unpaired)}"
        self.log(msg)

    def _mir_resolve_pairs(self):
        """현재 모드(Auto/Manual)로 (src, tgt) 페어 리스트 반환. 실패 시 None(경고 로그).
        on_mirror_key(구간) / on_mirror_current_frame(현재 프레임) 가 공유한다.
        씬 선택과 무관하게 Source/Target 리스트의 오브젝트만 대상으로 한다."""
        base = self.mir_base_tsl.get_all_items()
        tgt = self.mir_tgt_tsl.get_all_items()

        if self.rb_mir_manual.isChecked():
            # 수동: Source/Target 리스트를 인덱스 매칭.
            if not base or not tgt:
                self.log("[Warning] Fill both Source and Target lists.")
                return None
            if len(base) != len(tgt):
                self.log(f"[Warning] Source({len(base)}) / Target({len(tgt)}) count mismatch.")
                return None
            return list(zip(base, tgt))

        # 자동: 씬 선택을 읽지 않고 Source 리스트를 기준으로 한다.
        if not base:
            self.log("[Warning] Source list is empty. Use 'Select Source' or 'Resolve Pairs'.")
            return None
        if tgt and len(tgt) == len(base):
            # 이미 페어가 채워져 있으면(Resolve 등) 그대로 사용.
            return list(zip(base, tgt))
        # Target 리스트가 비어 있으면 Source 리스트를 토큰으로 자동 페어링.
        token_pairs = self._mir_token_pairs() or list(MirrorKeyManager.DEFAULT_TOKEN_PAIRS)
        pairs, unpaired, center = MirrorKeyManager.resolve_pairs(base, token_pairs)
        if unpaired:
            self.log(f"[Warning] {len(unpaired)} unpaired (skipped): {', '.join(unpaired)}")
        if not pairs:
            self.log("[Warning] No pairs resolved.")
            return None
        return pairs

    def on_mirror_key(self):

        rng = self._mir_read_range()
        if rng is None:
            return
        start, end = rng

        do_t = self.cb_mir_translate.isChecked()
        do_r = self.cb_mir_rotate.isChecked()
        if not do_t and not do_r:
            self.log("[Warning] Enable Translate and/or Rotate.")
            return

        axis = self._mir_axis()
        time_mode = "bake" if self.rb_mir_bake.isChecked() else "source_keys"

        pairs = self._mir_resolve_pairs()
        if pairs is None:
            return

        count, msg = MirrorKeyManager.mirror_keys(
            pairs, start, end, mirror_axis=axis,
            do_translate=do_t, do_rotate=do_r, time_mode=time_mode,
            behavior=self.cb_mir_behavior.isChecked())
        self.log(msg)

    def on_mirror_current_frame(self):
        """현재 프레임의 포즈만 미러(autoKeyframe 재현). Start/End/Time 미사용."""
        do_t = self.cb_mir_translate.isChecked()
        do_r = self.cb_mir_rotate.isChecked()
        if not do_t and not do_r:
            self.log("[Warning] Enable Translate and/or Rotate.")
            return

        pairs = self._mir_resolve_pairs()
        if pairs is None:
            return

        count, msg = MirrorKeyManager.mirror_current_frame(
            pairs, mirror_axis=self._mir_axis(),
            do_translate=do_t, do_rotate=do_r,
            per_object=self.rb_mir_cf_object.isChecked(),
            behavior=self.cb_mir_behavior.isChecked(),
        )
        self.log(msg)

    # --------------------------------------------------
    # Bake
    # --------------------------------------------------

    def _bake_update_range_mode(self, *args):
        """Range 모드에 따라 Custom Start/End 입력 활성/비활성 토글."""
        custom = self.rb_bake_custom.isChecked()
        self.bake_range.set_inputs_enabled(custom)

    def _bake_update_smart_mode(self, *args):
        """Smart bake 체크 상태에 따라 Tolerance 입력 활성/비활성 토글."""
        self.le_bake_smart_tol.setEnabled(self.cb_bake_smart.isChecked())

    def _bake_resolve_range(self):
        """라디오에 따라 (start, end) 결정. 실패 시 None.
        Current timeline = playback min/maxTime, Custom = QLineEdit 입력."""
        if self.rb_bake_timeline.isChecked():
            start = int(cmds.playbackOptions(q=True, minTime=True))
            end = int(cmds.playbackOptions(q=True, maxTime=True))
            return (start, end)

        s_txt = self.le_bake_start.text().strip()
        e_txt = self.le_bake_end.text().strip()
        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return None
        start = int(s_txt)
        end = int(e_txt)
        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return None
        return (start, end)

    def on_bake(self):

        objs = self.bake_tsl.get_all_items()   # 리스트업된 항목만 (씬 선택 아님)
        if not objs:
            self.log("[Warning] Add controllers to the Bake List first.")
            return

        rng = self._bake_resolve_range()
        if rng is None:
            return
        start, end = rng

        channels = []
        if self.cb_bake_t.isChecked():
            channels += ["tx", "ty", "tz"]
        if self.cb_bake_r.isChecked():
            channels += ["rx", "ry", "rz"]
        if self.cb_bake_s.isChecked():
            channels += ["sx", "sy", "sz"]
        if not channels:
            self.log("[Warning] Enable at least one channel group.")
            return

        smart = self.cb_bake_smart.isChecked()
        smart_tol = BakeManager.DEFAULT_SMART_TOLERANCE
        if smart:
            tol_txt = self.le_bake_smart_tol.text().strip()
            try:
                smart_tol = float(tol_txt)
            except ValueError:
                self.log("[Warning] Invalid Tolerance, using {0}.".format(smart_tol))

        count, msg = BakeManager.bake(
            objs, start, end, channels=channels,
            simulation=self.cb_bake_sim.isChecked(),
            disable_implicit=not self.cb_bake_keep_con.isChecked(),  # 체크=유지 -> False
            smart=smart,
            smart_tolerance=smart_tol,
        )
        self.log(msg)

    # --------------------------------------------------
    # Follow (target match bake)
    # --------------------------------------------------

    def _follow_slider_to_le(self, value):
        """Slider(0..100) 변경 -> Blend LineEdit(0..1) 동기화."""
        self.le_follow_blend.setText("{0:.2f}".format(value / 100.0))

    def _follow_le_to_slider(self):
        """Blend LineEdit(0..1) 입력 확정 -> Slider(0..100) 동기화."""
        txt = self.le_follow_blend.text().strip()
        try:
            v = max(0.0, min(1.0, float(txt)))
        except ValueError:
            return
        self.sld_follow_blend.blockSignals(True)
        self.sld_follow_blend.setValue(int(round(v * 100)))
        self.sld_follow_blend.blockSignals(False)

    def on_follow_bake(self):

        targets = self.follow_tgt_tsl.get_all_items()
        followers = self.follow_flw_tsl.get_all_items()
        one_to_many = self.cb_follow_one_to_many.isChecked()
        maintain_offset = self.cb_follow_offset.isChecked()

        if not targets or not followers:
            self.log("[Warning] Fill both Target and Follower lists.")
            return
        if one_to_many:
            if len(targets) != 1:
                self.log("[Warning] 1<-n mode needs exactly 1 target "
                         "(got {0}).".format(len(targets)))
                return
        elif len(targets) != len(followers):
            self.log("[Warning] Target ({0}) / Follower ({1}) count mismatch.".format(
                len(targets), len(followers)))
            return

        # Start / End 파싱.
        s_txt = self.le_follow_start.text().strip()
        e_txt = self.le_follow_end.text().strip()
        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return
        start = int(s_txt)
        end = int(e_txt)
        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return

        do_t = self.cb_follow_t.isChecked()
        do_r = self.cb_follow_r.isChecked()
        do_s = self.cb_follow_s.isChecked()
        if not (do_t or do_r or do_s):
            self.log("[Warning] Enable at least one channel group.")
            return

        b_txt = self.le_follow_blend.text().strip()
        try:
            blend = float(b_txt)
        except ValueError:
            self.log("[Warning] Invalid Blend value.")
            return

        count, msg = FollowMatchManager.match_follow(
            targets, followers, start, end, blend,
            do_translate=do_t, do_rotate=do_r, do_scale=do_s,
            maintain_offset=maintain_offset, one_to_many=one_to_many)
        self.log(msg)

    # --------------------------------------------------
    # Euler Filter (구간 한정)
    # --------------------------------------------------

    def on_euler_filter(self):

        objs = self.euler_tsl.get_all_nodes()   # 리스트업된 항목만 (씬 선택 아님)
        if not objs:
            self.log("[Warning] Add controllers to the Euler Filter List first.")
            return

        rng = self.euler_range.values()
        if rng is None:
            self.log("[Warning] Enter Start / End.")
            return
        start, end = rng
        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return

        count, msg = EulerFilterManager.filter_range(
            objs, start, end,
            anchor_previous=self.cb_euler_anchor.isChecked())
        self.log(msg)

    def on_euler_filter_from_selection(self):
        """원버튼 — **씬 선택**(대상) + **선택한 키의 앞/뒤 프레임**(구간)을 스스로 감지해 실행.

        실제 작업은 "컨트롤러 몇 개를 고르고 그래프 에디터에서 문제 구간을 드래그로 선택" 으로
        끝나는데, 기존 버튼은 그걸 다시 List Selected Objects + Get Sel Range 로 옮겨야 했다.
        이 버튼은 그 두 단계를 대신한다.

        감지한 값은 **위젯에도 채워 넣는다** — 무엇을 대상으로 어느 구간을 처리했는지 눈으로
        확인되고, 이어서 Anchor 를 바꿔 아래 버튼으로 다시 돌려볼 수도 있다.

        씬 선택이 비어 있으면 리스트에 담긴 항목으로 폴백한다(구간은 항상 선택 키에서 온다).
        선택한 키가 없으면 조용히 전 구간을 처리하지 않고 경고만 남긴다 — '구간 한정' 이라는
        이 탭의 약속을 어기는 쪽이 더 위험하기 때문이다."""

        objs = EulerFilterManager.selected_objects()
        from_selection = bool(objs)
        if not objs:
            objs = self.euler_tsl.get_all_nodes()   # 폴백: 리스트업된 항목
            if not objs:
                self.log("[Warning] Select controllers in the scene "
                         "(or add them to the Euler Filter List) first.")
                return

        rng = EulerFilterManager.selected_key_range()
        if rng is None:
            self.log("[Warning] No keyframes selected. Drag-select the keys of the "
                     "range in the Graph Editor / Time Slider first.")
            return
        start, end = rng

        if from_selection:
            self.euler_tsl.set_items(objs)
        self.euler_range.set_range(start, end)

        source = ("scene selection" if from_selection
                  else "the list (nothing selected in the scene)")
        self.log("[From Selection] {0} target(s) from {1}, range [{2}-{3}f] "
                 "from the selected keys.".format(len(objs), source, start, end))

        count, msg = EulerFilterManager.filter_range(
            objs, start, end,
            anchor_previous=self.cb_euler_anchor.isChecked())
        self.log(msg)

    # --------------------------------------------------
    # Offset & Hold
    # --------------------------------------------------

    def on_offset_hold(self):

        objs = self.oh_tsl.get_all_items()   # 리스트업된 항목만 (씬 선택 아님)
        if not objs:
            self.log("[Warning] Add objects to the Offset/Hold List first.")
            return

        h_txt = self.le_oh_hold.text().strip()
        o_txt = self.le_oh_offset.text().strip()
        if h_txt == "" or o_txt == "":
            self.log("[Warning] Enter Hold and Offset.")
            return

        hold = int(h_txt)
        offset = int(o_txt)
        if hold + offset <= 0:
            self.log("[Warning] Hold + Offset must be greater than 0.")
            return

        # Start 비우면 None -> 오브젝트별 첫 키 프레임을 앵커로.
        s_txt = self.le_oh_start.text().strip()
        start = int(s_txt) if s_txt != "" else None

        count, msg = OffsetHoldManager.apply_offset_hold(objs, offset, hold, start=start)
        self.log(msg)

    # --------------------------------------------------
    # Stagger Offset
    #   슬라이더/스핀박스를 움직이면 '원래 위치 기준' 결과가 즉시 반영된다(누적 안 됨).
    #   조작이 멎으면(슬라이더에서 손을 떼면) 그 값이 자동으로 undo 큐에 한 항목으로
    #   기록되고 **그대로 확정된다**(별도 Apply 없음).
    #   Reset 으로 원위치. 리스트/구간이 바뀌면 세션만 닫히고 적용된 값은 남는다.
    # --------------------------------------------------

    def _stagger_read_range(self):
        """Stagger 구간(start, end) 파싱. 실패 시 None."""
        s_txt = self.le_st_start.text().strip()
        e_txt = self.le_st_end.text().strip()

        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Stagger Start / End.")
            return None

        start = int(s_txt)
        end = int(e_txt)

        if start > end:
            self.log(f"[Warning] Start ({start}) is greater than End ({end}).")
            return None

        return (start, end)

    def _stagger_show_value(self, value):
        """슬라이더/스핀박스에 값을 표시한다(시그널을 막아 되울림·재진입 없이).

        슬라이더는 담당 범위를 벗어나면 끝에 붙고, 실제 값은 스핀박스가 보여준다.
        (A00290_BSTool Shape Editor 의 _show_weight 와 같은 처리)
        """
        clamped = max(-STAGGER_SLIDER_RANGE, min(STAGGER_SLIDER_RANGE, value))
        self._stagger_updating = True
        try:
            for widget, new in ((self.sld_stagger, clamped), (self.sb_stagger, value)):
                widget.blockSignals(True)
                widget.setValue(new)
                widget.blockSignals(False)
        finally:
            self._stagger_updating = False

    def _stagger_show_value_offset(self, value):
        """값 오프셋 위젯 두 개를 같은 값으로 맞춘다(시그널 차단).

        슬라이더는 정수라 STAGGER_VALUE_SLIDER_SCALE 배로 담고, 담당 범위를 벗어나면
        끝에 붙는다(실제 값은 스핀박스가 보여준다).
        """
        ticks = int(round(value * STAGGER_VALUE_SLIDER_SCALE))
        clamped = max(-STAGGER_VALUE_SLIDER_STEPS,
                      min(STAGGER_VALUE_SLIDER_STEPS, ticks))
        self._stagger_updating = True
        try:
            self.sld_stagger_value.blockSignals(True)
            self.sld_stagger_value.setValue(clamped)
            self.sld_stagger_value.blockSignals(False)
            self.sb_stagger_value.blockSignals(True)
            self.sb_stagger_value.setValue(value)
            self.sb_stagger_value.blockSignals(False)
        finally:
            self._stagger_updating = False

    def _stagger_reset_spin(self):
        """오프셋 위젯을 0 으로 되돌린다(valueChanged 로 인한 재진입 없이)."""
        self._stagger_settle_timer.stop()
        self._stagger_show_value(0)
        self._stagger_show_value_offset(0.0)

    def _stagger_begin(self):
        """세션이 없으면 현재 리스트/구간으로 만든다. 실패하면 None."""
        if self._stagger_session is not None:
            return self._stagger_session

        objs = self.st_tsl.get_all_nodes()   # 리스트업된 항목만 (씬 선택 아님)
        if not objs:
            self.log("[Warning] Add objects to the Stagger List first.")
            return None

        rng = self._stagger_read_range()
        if rng is None:
            return None

        session, msg = StaggerOffsetSession.create(objs, rng[0], rng[1])
        self.log(msg)
        self._stagger_session = session
        return session

    def _stagger_drop_stale_session(self):
        """씬이 세션의 가정과 어긋났으면(주로 사용자가 Ctrl+Z) 세션을 조용히 버린다.

        이때 restore() 를 부르면 안 된다 — 세션은 이미 씬을 잘못 알고 있어서, 되돌리려는
        시도가 오히려 키를 엉뚱한 곳으로 민다. 씬은 undo 가 만든 상태 그대로 두고 세션만
        버린 뒤, 다음 조작에서 현재 상태를 기준으로 새 세션을 만든다.

        반환: 버렸으면 True.
        """
        session = self._stagger_session
        if session is None or session.scene_in_sync():
            return False

        self._stagger_session = None
        self._stagger_reset_spin()
        self.log("Stagger session dropped (scene changed outside the tool, e.g. undo).")
        return True

    def _stagger_invalidate(self, *args):
        """리스트/구간이 바뀌면 세션만 닫는다. **씬에 적용된 offset 은 건드리지 않는다.**

        예전에는 여기서 `restore()` 를 불러 키를 원위치로 되돌렸다. 그래서 슬라이더로
        offset 을 준 뒤 다른 오브젝트를 골라 **List Selected Objects** 를 누르면(리스트
        모델이 바뀌면서 이 훅이 돌아) **방금 준 offset 이 통째로 사라졌다**. 시간(Offset
        per Item)·값(Value per Item) 둘 다 같은 증상이었다 — `restore()` 가 둘을 함께
        0 으로 되돌리기 때문이다.

        슬라이더에서 손을 떼는 순간 값은 이미 undo 큐에 기록된 **확정된 결과**다.
        리스트가 바뀌었다는 이유로 조용히 되돌리는 것은 사용자가 한 작업을 지우는 셈이라
        더 이상 하지 않는다. 되돌리고 싶으면 **Reset** 이나 **Ctrl+Z** 를 쓰면 된다.

        세션을 닫는 것은 그대로다 — 세션은 시작 시점의 순서·구간을 고정하므로 바뀐 채로
        계속 쓰면 엉뚱한 구간을 민다. 다음 조작은 **지금 씬 상태를 기준**으로 새 세션을
        만들고, 슬라이더는 0 에서 다시 시작한다(그래서 두 번째 조작은 남아 있는 offset
        **위에 쌓인다**).
        """
        if self._stagger_session is None:
            return
        if self._stagger_drop_stale_session():
            return

        self._stagger_settle_timer.stop()

        # 아직 기록되지 않은 미리보기가 떠 있을 수 있다(디바운스 타이머가 돌기 전에
        # 리스트가 바뀐 경우). 세션을 닫기 전에 확정해 둬야 씬에 남는 결과가 undo 큐에도
        # 남는다 — 안 그러면 Ctrl+Z 로 되돌릴 수 없는 변경이 씬에 남는다.
        session = self._stagger_session
        _moved, msg = session.settle(self.sb_stagger.value(),
                                     self.sb_stagger_value.value())
        if msg:
            self.log(msg)

        kept_time, kept_value = session.settled, session.settled_value
        self._stagger_session = None
        self._stagger_reset_spin()

        if kept_time or abs(kept_value) > 1e-12:
            self.log("Stagger session closed (list or range changed). "
                     "The applied offset ({0:+d}f / {1:+g}) stays - the sliders "
                     "start from 0 again.".format(kept_time, kept_value))

    def on_stagger_slider_changed(self, *_args):
        """슬라이더 조작 -> 스핀박스를 맞추고 즉시 반영."""
        if self._stagger_updating:
            return
        value = self.sld_stagger.value()
        self._stagger_show_value(value)
        self._stagger_apply_live(value)

    def on_stagger_spin_changed(self, *_args):
        """스핀박스 조작 -> 슬라이더를 맞추고 즉시 반영."""
        if self._stagger_updating:
            return
        value = self.sb_stagger.value()
        self._stagger_show_value(value)
        self._stagger_apply_live(value)

    def on_stagger_value_slider_changed(self, *_args):
        """값 슬라이더 조작 -> 스핀박스를 맞추고 즉시 반영."""
        if self._stagger_updating:
            return
        value = self.sld_stagger_value.value() / float(STAGGER_VALUE_SLIDER_SCALE)
        self._stagger_show_value_offset(value)
        self._stagger_apply_live(self.sb_stagger.value())

    def on_stagger_value_spin_changed(self, *_args):
        """값 스핀박스 조작 -> 슬라이더를 맞추고 즉시 반영."""
        if self._stagger_updating:
            return
        self._stagger_show_value_offset(self.sb_stagger_value.value())
        self._stagger_apply_live(self.sb_stagger.value())

    def _stagger_apply_live(self, value):
        """실시간 반영. 값이 바뀔 때마다 '원래 위치 기준' 으로 다시 계산된다(비누적).

        기록(undo)은 여기서 하지 않는다. 조작이 멎으면 디바운스 타이머가 _stagger_settle 을
        불러 그때까지의 결과를 **한 항목으로** 기록한다.
        """
        self._stagger_drop_stale_session()

        session = self._stagger_begin()
        if session is None:
            self._stagger_reset_spin()
            return

        session.preview(value, self.sb_stagger_value.value())
        self._stagger_settle_timer.start()

    def _stagger_settle(self):
        """조작이 멎은 시점에 지금까지의 미리보기를 undo 큐에 한 항목으로 기록한다.

        이 덕분에 슬라이더를 아무리 흔들어도 **Ctrl+Z 한 번이면 조작 직전 상태**로 돌아간다
        (첫 조작이라면 곧 원위치 = Reset 과 같은 결과).
        """
        self._stagger_settle_timer.stop()

        session = self._stagger_session
        if session is None:
            return
        if self._stagger_drop_stale_session():
            return

        count, msg = session.settle(self.sb_stagger.value(),
                                    self.sb_stagger_value.value())
        if msg:
            self.log(msg)

    def on_stagger_reset(self):
        """키를 원위치(offset 0)로 되돌리고 세션 종료."""
        if self._stagger_session is None:
            self._stagger_reset_spin()
            self.log("No stagger offset to reset.")
            return
        if self._stagger_drop_stale_session():
            return

        self._stagger_settle_timer.stop()
        self._stagger_session.restore()
        self._stagger_session = None
        self._stagger_reset_spin()
        self.log("Stagger offset reset to 0.")

    def toggle_always_on_top(self, enabled):
        # WindowStaysOnTopHint 를 켜고/끄고, 플래그 변경 후 다시 show() (안 하면 창이 사라짐)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.pin_button.setText("Pinned" if enabled else "Pin")
        self.show()
        self.log("Always on Top: " + ("ON" if enabled else "OFF"))

    def show_about(self, *args):
        # jointTool 의 show_about(confirmDialog) 패턴을 Qt 로 옮김
        QMessageBox.information(
            self,
            "About",
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}",
        )

    # --------------------------------------------------
    # Hotkey
    # --------------------------------------------------

    # --------------------------------------------------
    # Handlers : Curve > Smooth / Intensity / Interp
    # --------------------------------------------------

    def on_cf_expand(self):
        """Curve Filters 를 별도 창으로 (공용 패널에 위임).

        패널이 창 생성·본문 이동·제자리 복귀·툴 창 닫힘 감시를 모두 처리한다.
        """
        self.cf_panel.toggle()

    def on_cf_collapse(self):
        """확장 창을 접는다(공용 패널에 위임)."""
        self.cf_panel.collapse()

    def _cf_settle_timer(self, kind):
        """조작이 멎으면 확정하는 타이머(종류별로 하나). 없으면 만든다."""
        timers = getattr(self, "_cf_timers", None)
        if timers is None:
            timers = {}
            self._cf_timers = timers
        timer = timers.get(kind)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(STAGGER_SETTLE_MS)
            timer.timeout.connect(lambda k=kind: self._cf_finish(k))
            timers[kind] = timer
        return timer

    def _cf_connect(self, kind, slider):
        slider.valueChanged.connect(lambda _v, k=kind: self._cf_changed(k))
        slider.sliderReleased.connect(lambda k=kind: self._cf_finish(k))

    def _cf_sliders(self, kind):
        if kind == "interpolate":
            return (self.cf_interp_slider_a, self.cf_interp_slider_b)
        return (getattr(self, "cf_%s_slider" % kind),)

    def _cf_params(self, kind, amount=None, shape=None):
        """지금 위젯 상태에서 필터 파라미터를 읽는다. (kind, params) 또는 (kind, None)."""
        if kind == "smooth":
            if amount is None:
                amount = self.cf_smooth_slider.value()
            return {"amount": amount,
                    "iterations": self.cf_smooth_iter.value(),
                    "strength": float(self.cf_smooth_strength.value())}
        if kind == "intensity":
            if amount is None:
                amount = self.cf_intensity_slider.value()
            return {"amount": amount}

        # interpolate : 두 슬라이더 중 **0 이 아닌 쪽**이 모양과 세기를 함께 정한다.
        # (가운데 = 변화 없음. 왼쪽으로 밀면 왼쪽 라벨의 이징, 오른쪽이면 오른쪽 라벨.)
        if amount is not None:
            return {"amount": abs(amount), "shape": shape or CF_LINEAR}
        a = self.cf_interp_slider_a.value()
        b = self.cf_interp_slider_b.value()
        value, pair = (a, (CF_EASE_IN, CF_EASE_OUT)) if abs(a) >= abs(b) \
            else (b, (CF_LINEAR, CF_EASE_IN_OUT))
        return {"amount": abs(value), "shape": pair[0] if value < 0 else pair[1]}

    def _cf_session(self, kind, create=True):
        """종류별 세션. create 면 없을 때 **지금 선택한 키**로 새로 만든다.

        대상은 리스트가 아니라 씬 상태다 — 그래프 에디터에서 고른 키가 1순위,
        없으면 타임 슬라이더 구간 + 씬 선택. 아무것도 고르지 않았으면 만들지 않는다.
        """
        sessions = getattr(self, "_cf_sessions", None)
        if sessions is None:
            sessions = {}
            self._cf_sessions = sessions

        session = sessions.get(kind)
        if session is not None or not create:
            return session

        session, message = CurveFilterSession.from_selection(
            quaternion=self.cf_quat.isChecked())
        if session is None:
            self.log("[Warning] " + message)
            return None

        sessions[kind] = session
        return session

    def _cf_changed(self, kind):
        """슬라이더가 움직이는 동안 — undo 기록 없이 미리보기."""
        if getattr(self, "_cf_updating", False):
            return
        params = self._cf_params(kind)
        session = self._cf_session(kind)
        if session is None:
            self._cf_reset_sliders(kind)
            return
        session.preview(kind, **params)
        self._cf_settle_timer(kind).start()

    def _cf_finish(self, kind):
        """조작이 끝났다 — 한 번의 undo 로 확정하고 슬라이더를 가운데로 되돌린다."""
        self._cf_settle_timer(kind).stop()
        session = self._cf_session(kind, create=False)
        if session is None:
            return
        params = self._cf_params(kind)
        if abs(params["amount"]) < 1e-9:
            session.restore()
        else:
            session.settle(kind, **params)
            self.log("{0}: {1}  {2}".format(
                kind.capitalize(), self._cf_describe(kind, params),
                session.summary()))
        self._cf_sessions[kind] = None
        self._cf_reset_sliders(kind)

    def _cf_apply_once(self, kind, amount, shape=None):
        """버튼 한 번 = 세션 생성 + 확정 + 정리 (undo 한 스텝)."""
        session = self._cf_session(kind)
        if session is None:
            return
        params = self._cf_params(kind, amount=amount, shape=shape)
        session.settle(kind, **params)
        self.log("{0}: {1}  {2}".format(
            kind.capitalize(), self._cf_describe(kind, params), session.summary()))
        self._cf_sessions[kind] = None
        self._cf_reset_sliders(kind)

    @staticmethod
    def _cf_describe(kind, params):
        if kind == "smooth":
            return "amount {0:+d}, {1} iteration(s), strength {2:g}%".format(
                int(params["amount"]), params["iterations"], params["strength"])
        if kind == "intensity":
            return "amount {0:+d}".format(int(params["amount"]))
        return "{0} {1:g}%".format(params["shape"], params["amount"])

    def _cf_reset_sliders(self, kind):
        self._cf_updating = True
        try:
            for slider in self._cf_sliders(kind):
                slider.blockSignals(True)
                slider.setValue(0)
                slider.blockSignals(False)
        finally:
            self._cf_updating = False

    def on_toggle_hotkey(self, checked):
        self._enable_hotkey(checked)

    def _enable_hotkey(self, on):
        """체크 상태에 따라 Shift+A 핫키를 설치/복원하고 상태 라벨을 갱신."""
        if on:
            ok, msg = self.hotkey_mgr.install()
            self.lbl_hotkey.setText("Shift+A : ON" if ok else "Shift+A : unavailable")
        else:
            self.hotkey_mgr.restore()
            msg = "Shift+A hotkey disabled."
            self.lbl_hotkey.setText("Shift+A : OFF")

        self.log(msg)

    # --------------------------------------------------
    # Graph Focus (선택 시 그래프 에디터 자동 프레이밍)
    # --------------------------------------------------

    def _graph_margin(self):
        """현재 margin 스핀박스 값(±프레임)."""
        return self.sb_graph_margin.value()

    def _graph_fit_value(self):
        """세로(값) 축도 맞출지 여부."""
        return self.cb_graph_fit_value.isChecked()

    def _graph_value_pad(self):
        """세로(값) 위/아래 여백 퍼센트."""
        return self.sb_graph_value_pad.value()

    def on_toggle_graph_focus(self, checked):
        """Auto-Focus 토글 ON/OFF. ON 이면 SelectionChanged 감시 시작 + 즉시 1회 적용."""
        self.btn_graph_focus.setText(
            "Auto-Focus on Selection : ON" if checked else "Auto-Focus on Selection : OFF")

        if checked:
            ok, msg = self.graph_focus_mgr.install(
                self._graph_margin, self._graph_fit_value, self._graph_value_pad)
            self.log(msg)
        else:
            self.graph_focus_mgr.uninstall()
            self.log("Graph focus: OFF")

    def on_graph_focus_now(self):
        """토글과 무관하게 지금 한 번만 현재 프레임 ± margin 으로 프레이밍."""
        count, msg = GraphViewManager.frame_around_current(
            self._graph_margin(), fit_value=self._graph_fit_value(),
            value_pad_pct=self._graph_value_pad())
        self.log(msg)

    def _graph_focus_reapply(self, *args):
        """margin / fit / 여백 값이 바뀌면 토글이 켜져 있을 때만 즉시 다시 프레이밍(로그 없음)."""
        if self.graph_focus_mgr.is_active():
            GraphViewManager.frame_around_current(
                self._graph_margin(), fit_value=self._graph_fit_value(),
                value_pad_pct=self._graph_value_pad())

    # --------------------------------------------------
    # Teardown
    # --------------------------------------------------

    def showEvent(self, event):
        # 최초 표시 직후 한 번, 현재 탭(섹션 접힘 상태)에 맞춰 창 크기를 맞춘다.
        # (표시 전에는 탭 페이지가 숨김 상태라 sizeHint 가 0 이므로 show 이후에 처리.)
        super().showEvent(event)
        if not getattr(self, "_initial_fit_done", False):
            self._initial_fit_done = True
            self._fit_window_later()

    def closeEvent(self, event):
        # 창이 닫힐 때 Shift+A 를 원래 바인딩으로 복원 + 그래프 포커스 scriptJob 정리
        try:
            if getattr(self, "hotkey_mgr", None):
                self.hotkey_mgr.restore()
            if getattr(self, "graph_focus_mgr", None):
                self.graph_focus_mgr.uninstall()
            # 아직 기록되지 않은 Stagger 미리보기가 남아 있으면 마지막으로 기록해 둔다.
            # (미리보기는 undo 큐에 없어서, 그냥 두면 Ctrl+Z 로도 못 되돌린다.)
            session = getattr(self, "_stagger_session", None)
            if session is not None:
                if getattr(self, "_stagger_settle_timer", None):
                    self._stagger_settle_timer.stop()
                if session.scene_in_sync():
                    # 시간과 **값** 을 함께 넘겨야 한다. 값을 빼먹으면 settle 이 그 인자를
                    # settled_value 로 채워, 아직 기록되지 않은 Value per Item 미리보기를
                    # 조용히 되돌려 버린다(시간만 남고 값은 사라진다).
                    session.settle(self.sb_stagger.value(),
                                   self.sb_stagger_value.value())
                self._stagger_session = None

            # 같은 이유로 Noise 미리보기도 마지막으로 확정한다.
            noise_sess = getattr(self, "_noise_sess", None)
            if noise_sess is not None:
                if getattr(self, "_noise_settle_timer", None):
                    self._noise_settle_timer.stop()
                if noise_sess.valid() and noise_sess.in_sync():
                    noise_sess.settle(**self._noise_widget_params())
                self._noise_sess = None
        finally:
            super().closeEvent(event)
