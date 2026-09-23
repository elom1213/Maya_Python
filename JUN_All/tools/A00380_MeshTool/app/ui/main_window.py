# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-23
# A00380_MeshTool - Qt UI
#
# Peak 탭: 선택한 메시/버텍스를 자기 노말 방향으로 팽창(+)·수축(-) 시킨다.
# 후디니 peak 노드와 같은 개념이고, 마야 기본(Move 툴 axis=normal)보다 훨씬 빠르다.
#
# Match 탭: 좌측 Source 메시의 같은 인덱스 버텍스 위치로, 우측 Target 메시들을 이동시킨다
# (v01.10~ 좌/우 리스트. 좌 1개 = 1 <= n, 여러 개 = n <= n). Kangaroo Geometry>Match 재현.
# v01.09~ 하위 탭 Default(위 기능) / By Weight(스킨 웨이트를 마스크로 타깃 쪽으로 이동).
#
# MeshDoctor 탭 (v01.14~): 옛 A00300_meshDoctor 를 그대로 옮겨 왔다. 메시를 **읽기만 해서**
# 진단하고(요약 표 + 상세 리포트 + 0020_out/ 에 JSON·TXT), 아래쪽 버튼으로 안전한 원클릭
# 수정을 한다. Peak/Match 가 메시를 "고치는" 쪽이라면 이 탭은 "무엇이 잘못됐는지 말해 주는" 쪽이다.
#
# UV Sets 탭 (v01.17~): A00050_uvTool_V02(v02.03) 를 탭으로 옮겼다 - UV 세트 규칙(`map1` 하나)
# 검사 · 삭제 · 이름 정리 + UV Sets 표. 탭 본체는 app/ui/uv_tab.py, 이 파일은 등록만 한다.
#
# 흐름: Load 로 스냅샷 → 슬라이더를 끌면 실시간 미리보기(API 직접 쓰기) → 손을 떼는 순간
#       그 상태를 그대로 확정(tweak 구간 setAttr, Ctrl+Z 한 번에 되돌아감). 별도 Apply 버튼 없음.

import os
import time

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_tsl_qt_v01 import JUN_mod_tsl_qt_v01
from Framework.qt.MOD_checkList_qt_v01 import JUN_mod_checkList_qt_v01
from Framework.qt.MOD_filter_qt_v01 import JUN_mod_filter_qt_v01
from Framework.qt.MOD_progress_qt_v01 import JUN_mod_progress_qt_v01
from Framework.qt import JUN_mod_collapsible_qt

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from tools.A00380_MeshTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00380_MeshTool.app.core import peak_manager as peak_mgr
from tools.A00380_MeshTool.app.core import match_manager as match_mgr
from tools.A00380_MeshTool.app.core import weight_match_manager as wm_mgr
from tools.A00380_MeshTool.app.core.mesh_scan import MeshScanner
from tools.A00380_MeshTool.app.core.mesh_fix import MeshFixer
from tools.A00380_MeshTool.app.core.report import ReportWriter
from tools.A00380_MeshTool.app.ui.uv_tab import UvSetsTab, RULE_TEXT as UV_RULE_TEXT


WINDOW_OBJECT_NAME = "JUN_A00380_MeshTool_window"

# 슬라이더는 정수만 다루므로 -SLIDER_TICKS ~ +SLIDER_TICKS 를 -range ~ +range 로 매핑한다.
SLIDER_TICKS = 1000

_WARN_COLOR = "#ffb454"
_OK_COLOR = "#7ddc7d"

# MeshDoctor 탭의 진단 등급 색. FAIL = 막힘, WARN = 문제일 가능성, INFO = 참고, PASS = 정상.
_SEV_COLOR = {
    "FAIL": "#ff6b6b",
    "WARN": "#ffd166",
    "INFO": "#8ab4f8",
    "PASS": "#6bcf8a",
}

# 미리보기 한 번이 이 시간을 넘으면 "무거운 메시"로 보고 드래그 중 갱신을 솎아낸다.
_HEAVY_SEC = 0.08

# 슬라이더 스타일. 어떤 테마 qss 도 QSlider 를 스타일링하지 않아, 어두운 배경(#2b2b2b)에선
# 네이티브 홈(groove)이 배경에 묻혀 구간이 안 보인다(핸들만 보임). A00290_BSTool 의 방식을
# 참고해 홈·핸들·비활성 상태를 직접 그린다. Peak 슬라이더는 중앙이 0 인 양방향이라, 한쪽에서
# 채워지는 fill 은 0 에서도 절반이 찬 것처럼 보여 오해를 준다 → 좌우 균일한 한 줄 홈으로만 그리고
# 0 위치는 눈금(TicksBelow)이 표시한다. 색은 coral_dark 테마 accent(#d08778)에 맞췄다.
SLIDER_STYLE = (
    "QSlider:horizontal { min-height: 20px; }"
    "QSlider::groove:horizontal {"
    " height: 6px; margin: 0 4px;"
    " background: #383534; border: 1px solid #d08778; border-radius: 3px; }"
    "QSlider::sub-page:horizontal, QSlider::add-page:horizontal {"
    " background: #383534; border: 1px solid #d08778; border-radius: 3px; }"
    "QSlider::handle:horizontal {"
    " width: 12px; margin: -6px 0;"
    " background: #efcabf; border: 1px solid #d08778; border-radius: 3px; }"
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
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Mesh Tool v{0}".format(VERSION)
        # 가로는 A00400_CurveTool 과 **같은 값(360)** 을 요청한다. 두 툴이 같은 규칙으로
        # 열리게 하는 것이 목적이다 - 실제 폭은 각자의 레이아웃 최소 폭까지만 벌어진다.
        #
        # 숫자를 크게 박지 않는 이유: 오프스크린(mayapy)에서 잰 최소 폭은 폰트가 달라
        # **마야에서 보이는 폭보다 크게 나온다**(A00400 은 오프스크린 1176, 마야에선 훨씬 좁다).
        # 그래서 실측값을 그대로 박으면 마야에서 필요 이상으로 넓은 창이 된다.
        # 세로만 이 툴 자신의 사정으로 넉넉히 둔다(MeshDoctor 탭의 표 + 리포트).
        self.resize(360, 860)

        self.session = None      # peak_mgr.PeakSession
        self._syncing = False    # 슬라이더 <-> 스핀박스 상호 갱신 재귀 방지
        self._script_job = None
        self._last_preview_sec = 0.0   # 직전 미리보기 소요 시간 (스로틀 판단용)
        self._last_preview_at = 0.0

        # 씬에 미확정 미리보기가 실제로 써져 있는지. 이게 False 면 되돌릴 게 없으므로
        # restore 를 건너뛴다. (auto-load 가 선택 변경마다 restore 를 부르면, 슬라이더를
        # 한 번도 안 건드렸어도 사용자가 손으로 옮긴 버텍스를 스냅샷으로 덮어써 버린다.)
        self._preview_dirty = False

        # Match 탭 상태 (Peak 과 독립된 세션/동기화 플래그)
        self.match_session = None      # match_mgr.MatchSession
        self._match_syncing = False
        self._match_preview_dirty = False

        # MeshDoctor 탭 상태. 진단은 씬을 읽기만 하므로 미리보기/세션이 없다.
        self.scanner = MeshScanner()
        self._doctor_results = []      # 마지막 진단 결과 (요약 표의 행과 1:1)
        self._last_out_dir = None      # 마지막으로 리포트를 쓴 폴더

        self.build_ui()
        self.update_state()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        help_menu.addAction("UV Sets Rule").triggered.connect(self.show_uv_rule)
        root.setMenuBar(self.menu_bar)

        self.tabs = QTabWidget()
        # MeshDoctor 가 맨 앞이다 — 무엇이 잘못됐는지 먼저 보고, 그다음에 고치는 순서.
        self.tabs.addTab(self.build_doctor_tab(), "MeshDoctor")
        # UV Sets (v01.17, A00050_uvTool_V02 이식) - MeshDoctor 오른쪽. 진단 다음, 모양을 고치기 전.
        # 로그는 이 창의 로그창을 쓴다. 로그창이 아래에서 만들어지므로 람다로 늦게 잡는다.
        self.uv_tab = UvSetsTab(log=lambda text: self.log(text),
                                log_html=lambda html: self.te_log.append(html))
        self.tabs.addTab(self.uv_tab, "UV Sets")
        self.tabs.addTab(self.build_peak_tab(), "Peak")
        self.tabs.addTab(self.build_match_tab(), "Match")
        self.tabs.currentChanged.connect(self.on_tab_changed)
        root.addWidget(self.tabs, 1)

        self.te_log = JUN_mod_log_qt_v01(
            window_title="Mesh Tool - Log",
            object_name="JUN_A00380_MeshTool_log_window")
        self.te_log.setMaximumHeight(110)
        root.addWidget(self.te_log)

        self.log("Mesh Tool v{0} ({1}) ready.  Peak / Match reshape meshes, "
                 "MeshDoctor diagnoses them, UV Sets checks the UV set rule.".format(
                     VERSION, LAST_UPDATE))

    def build_peak_tab(self):

        page = QWidget()
        lay = QVBoxLayout(page)

        # ---- 대상 -------------------------------------------------
        box_target = QGroupBox("Target")
        v = QVBoxLayout(box_target)

        self.lb_target = QLabel("Nothing loaded.")
        self.lb_target.setWordWrap(True)
        v.addWidget(self.lb_target)

        row = QHBoxLayout()
        self.btn_load = QPushButton("Load Selection")
        self.btn_load.setMinimumHeight(30)
        # clicked 는 checked(bool) 를 넘기므로 silent 인자로 새지 않게 감싼다.
        self.btn_load.clicked.connect(lambda: self.on_load())
        row.addWidget(self.btn_load, 2)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.on_clear)
        row.addWidget(self.btn_clear, 1)
        v.addLayout(row)

        self.chk_auto = QCheckBox("Auto load on selection change")
        self.chk_auto.setChecked(True)
        self.chk_auto.setToolTip(
            "Re-snapshot automatically whenever the scene selection changes.")
        self.chk_auto.toggled.connect(self.on_auto_toggled)
        v.addWidget(self.chk_auto)

        lay.addWidget(box_target)

        # ---- 옵션 -------------------------------------------------
        box_opt = QGroupBox("Options")
        vo = QVBoxLayout(box_opt)

        self.chk_angle = QCheckBox("Angle weighted normals")
        self.chk_angle.setChecked(True)
        self.chk_angle.setToolTip(
            "On: average face normals weighted by corner angle (smoother peak).\n"
            "Off: plain average.")
        vo.addWidget(self.chk_angle)

        self.chk_soft = QCheckBox("Respect soft selection")
        self.chk_soft.setChecked(True)
        self.chk_soft.setToolTip(
            "Use Maya's soft selection falloff as a per-vertex multiplier\n"
            "(only when soft select is enabled).")
        vo.addWidget(self.chk_soft)

        lay.addWidget(box_opt)

        # ---- 양(amount) -------------------------------------------
        box_amt = QGroupBox("Amount")
        va = QVBoxLayout(box_amt)

        row_r = QHBoxLayout()
        row_r.addWidget(QLabel("Range"))
        self.sp_range = QDoubleSpinBox()
        self.sp_range.setDecimals(3)
        self.sp_range.setRange(0.001, 10000.0)
        self.sp_range.setValue(1.0)
        self.sp_range.setToolTip(
            "Slider limit. Lower it for finer control (e.g. 0.05).")
        self.sp_range.valueChanged.connect(self.on_range_changed)
        row_r.addWidget(self.sp_range, 1)
        va.addLayout(row_r)

        self.sl_amount = QSlider(Qt.Horizontal)
        self.sl_amount.setRange(-SLIDER_TICKS, SLIDER_TICKS)
        self.sl_amount.setValue(0)
        # 테마 qss 가 QSlider 를 안 꾸며 홈이 배경에 묻히므로 직접 스타일. 양 끝·중앙(0)에
        # 눈금을 찍어 0 위치를 눈으로 찾는다.
        self.sl_amount.setStyleSheet(SLIDER_STYLE)
        self.sl_amount.setTickPosition(QSlider.TicksBelow)
        self.sl_amount.setTickInterval(SLIDER_TICKS)
        self.sl_amount.valueChanged.connect(self.on_slider_changed)
        # 손을 떼면 그 상태를 그대로 최종 결과로 확정한다(별도 Apply 버튼 없음).
        self.sl_amount.sliderReleased.connect(self.commit_stroke)
        va.addWidget(self.sl_amount)

        row_a = QHBoxLayout()
        row_a.addWidget(QLabel("Value"))
        self.sp_amount = QDoubleSpinBox()
        self.sp_amount.setDecimals(4)
        self.sp_amount.setRange(-10000.0, 10000.0)
        self.sp_amount.setSingleStep(0.01)
        self.sp_amount.setValue(0.0)
        self.sp_amount.valueChanged.connect(self.on_spin_changed)
        # 값 입력을 마치면(Enter/포커스 아웃) 그 상태를 확정한다.
        self.sp_amount.editingFinished.connect(self.commit_stroke)
        row_a.addWidget(self.sp_amount, 1)

        btn_zero = QPushButton("0")
        btn_zero.setMaximumWidth(30)
        btn_zero.setToolTip("Set amount back to zero.")
        btn_zero.clicked.connect(lambda: self.set_amount(0.0))
        row_a.addWidget(btn_zero)
        va.addLayout(row_a)

        # 미세 조정 nudge
        row_n = QHBoxLayout()
        row_n.addWidget(QLabel("Step"))
        self.sp_step = QDoubleSpinBox()
        self.sp_step.setDecimals(4)
        self.sp_step.setRange(0.0001, 1000.0)
        self.sp_step.setSingleStep(0.001)
        self.sp_step.setValue(0.01)
        self.sp_step.setToolTip("Amount added/removed by the - / + buttons.")
        row_n.addWidget(self.sp_step, 1)

        self.btn_minus = QPushButton("-")
        self.btn_minus.setMaximumWidth(34)
        self.btn_minus.setToolTip("Shrink by one step (applied immediately).")
        self.btn_minus.clicked.connect(lambda: self.nudge(-1))
        row_n.addWidget(self.btn_minus)

        self.btn_plus = QPushButton("+")
        self.btn_plus.setMaximumWidth(34)
        self.btn_plus.setToolTip("Inflate by one step (applied immediately).")
        self.btn_plus.clicked.connect(lambda: self.nudge(1))
        row_n.addWidget(self.btn_plus)
        va.addLayout(row_n)

        lay.addWidget(box_amt)

        # Apply 버튼은 없앴다. 슬라이더/스핀박스/±로 조절한 상태가 손을 떼는(확정) 순간
        # 그대로 최종 결과로 반영된다(각 조작이 Ctrl+Z 한 번 단위). '0' 으로 되돌리거나
        # Ctrl+Z 로 취소한다.
        hint = QLabel("Drag the slider (or use ± / Value) — the result is applied as\n"
                      "you go. Each change is one Ctrl+Z. '0' returns to no offset.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#9aa0a6;")
        lay.addWidget(hint)

        lay.addStretch(1)

        return page

    # --------------------------------------------------------------
    # Match 탭
    #   리스트업한 From 메시의 같은 인덱스 버텍스 위치로, 선택한 메시의 버텍스를
    #   이동시킨다(소프트 셀렉션 falloff 반영). Kangaroo Geometry>Match 를 재현.
    # --------------------------------------------------------------

    def build_match_tab(self):
        """Match 탭 = 하위 탭 두 개 (v01.09~).

        Default   : 예전 Match 탭 그대로 — From 메시의 같은 인덱스 버텍스로 선택을 스냅.
        By Weight : 스킨 웨이트를 마스크로 써서 M_j 들을 M_tgt 쪽으로 옮긴다.
        """
        self.match_tabs = QTabWidget()
        self.match_tabs.addTab(self.build_match_default_page(), "Default")
        self.match_tabs.setTabToolTip(
            0, "Reshape the right-hand meshes into the left-hand mesh(es),\n"
               "vertex index to vertex index (1 <= n, or pair by pair).")
        # By Weight 는 목록이 셋이라 키가 크다. 스크롤에 담아 창 최소 크기를 늘리지 않는다
        # (그대로 넣으면 창 최소가 435x615 -> 660x1002 로 커졌다, 테마 적용 실측).
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self.build_match_weight_page())
        self.match_tabs.addTab(scroll, "By Weight")
        self.match_tabs.setTabToolTip(
            1, "Move meshes toward a target by a skinned mesh's joint weights\n"
               "(like painting a blend shape target's weight map).")
        # Default 의 미확정 미리보기를 남긴 채 By Weight 로 가면 결과가 겹쳐 보인다.
        self.match_tabs.currentChanged.connect(
            lambda _i: self.discard_match_preview())
        return self.match_tabs

    def build_match_default_page(self):

        page = QWidget()
        lay = QVBoxLayout(page)

        # ---- 좌(Source) / 우(Targets) 리스트 (v01.10~) ----------------
        # 예전에는 From 한 칸 + 씬 선택이었다. 이제 좌측 메시 모양으로 **우측 메시들을** 바꾼다.
        #   좌 1개      -> 1 <= n : 우측 전부가 그 하나의 모양이 된다
        #   좌 여러 개  -> n <= n : 리스트 순서대로 k 번째끼리. 남는 쪽은 로그에 적는다
        box_lists = QGroupBox("Meshes  (vertex-index match)")
        hl = QHBoxLayout(box_lists)
        hl.setContentsMargins(4, 4, 4, 4)
        # Sort 를 켜 두는 이유(v01.13) : 짝은 **리스트 순서**로 맺어진다. 양쪽을
        # 이름순으로 정렬하면 `body_01 / body_02 …` 처럼 규칙적인 이름은 그것만으로
        # 짝이 맞는다 - Up / Down 을 수십 번 누르지 않아도 된다.
        self.tsl_from = JUN_mod_tsl_qt_v01(
            title="Source",
            show_sort=True, show_order=False, select_label="List Selected",
            list_min_height=80, log_callback=self.log)
        self.tsl_from.setToolTip(
            "The shape(s) to match TO.  One mesh here = every mesh on the right\n"
            "takes its shape.  Several = the k-th right mesh takes the k-th shape.")
        self.tsl_match_targets = JUN_mod_tsl_qt_v01(
            title="Targets", show_sort=True, show_order=False,
            select_label="List Selected",
            list_min_height=80, log_callback=self.log)
        self.tsl_match_targets.setToolTip(
            "The meshes that get modified.  Order matters when the left list has\n"
            "more than one mesh - use Sort or Up / Down to line the pairs up.")

        # Sort 는 순서를 바꾸는 버튼이라 무엇을 하는지 분명히 적는다.
        for tsl, side in ((self.tsl_from, "Source"),
                          (self.tsl_match_targets, "Target")):
            tsl.btn_sort.setToolTip(
                "Sort the {0} list by name.\n"
                "Pairs are made in list order, so sorting both lists is the quick\n"
                "way to line them up when the names run in the same "
                "order.".format(side))
        for tsl in (self.tsl_from, self.tsl_match_targets):
            model = tsl.list_widget.model()
            for sig in (model.rowsInserted, model.rowsRemoved, model.rowsMoved,
                        model.modelReset, model.layoutChanged):
                sig.connect(lambda *_a: self.update_match_pairs())
            hl.addWidget(tsl, 1)
        lay.addWidget(box_lists, 1)

        # ---- 짝 미리보기 --------------------------------------------
        self.lb_match_mode = QLabel()
        self.lb_match_mode.setWordWrap(True)
        lay.addWidget(self.lb_match_mode)
        self.tw_match_pairs = QTreeWidget()
        self.tw_match_pairs.setHeaderLabels(["Source", "Target (modified)"])
        self.tw_match_pairs.setRootIsDecorated(False)
        self.tw_match_pairs.setMinimumHeight(60)
        self.tw_match_pairs.setToolTip("What Apply will do. Grey rows have no partner "
                                       "and are skipped.")
        lay.addWidget(self.tw_match_pairs)

        # ---- 옵션 -------------------------------------------------
        box_opt = QGroupBox("Options")
        vo = QVBoxLayout(box_opt)

        self.chk_match_world = QCheckBox("World space")
        self.chk_match_world.setChecked(True)
        self.chk_match_world.setToolTip(
            "On: target vertices land on the From vertices' WORLD positions.\n"
            "Off: match the two meshes' local (object-space) coordinates.")
        vo.addWidget(self.chk_match_world)

        self.chk_match_soft = QCheckBox("Respect soft selection")
        self.chk_match_soft.setChecked(True)
        self.chk_match_soft.setToolTip(
            "When soft select is on and you have vertices of a Target mesh selected,\n"
            "only those move, by the falloff. Otherwise the whole Target mesh moves.")
        vo.addWidget(self.chk_match_soft)
        lay.addWidget(box_opt)

        # ---- Weight (0=원본, 1=완전 매칭) --------------------------
        box_w = QGroupBox("Weight")
        vw = QVBoxLayout(box_w)

        self.sl_match = QSlider(Qt.Horizontal)
        self.sl_match.setRange(0, SLIDER_TICKS)
        self.sl_match.setValue(SLIDER_TICKS)      # 기본 1.0 (완전 매칭)
        self.sl_match.setStyleSheet(SLIDER_STYLE)
        self.sl_match.setTickPosition(QSlider.TicksBelow)
        self.sl_match.setTickInterval(SLIDER_TICKS)
        # 슬라이더를 '잡는 순간' 현재 선택으로 세션을 만든다(백그라운드 scriptJob 없이).
        self.sl_match.sliderPressed.connect(self.on_match_slider_pressed)
        self.sl_match.valueChanged.connect(self.on_match_slider_changed)
        self.sl_match.sliderReleased.connect(self.match_preview)
        vw.addWidget(self.sl_match)

        row_w = QHBoxLayout()
        row_w.addWidget(QLabel("Value"))
        self.sp_match = QDoubleSpinBox()
        self.sp_match.setDecimals(3)
        self.sp_match.setRange(0.0, 1.0)
        self.sp_match.setSingleStep(0.05)
        self.sp_match.setValue(1.0)
        self.sp_match.valueChanged.connect(self.on_match_spin_changed)
        row_w.addWidget(self.sp_match, 1)
        vw.addLayout(row_w)
        lay.addWidget(box_w)

        # ---- 확정 -------------------------------------------------
        row_apply = QHBoxLayout()
        self.btn_match_apply = QPushButton("Apply Match")
        self.btn_match_apply.setMinimumHeight(38)
        self.btn_match_apply.setToolTip("Commit the match (undoable with one Ctrl+Z).")
        self.btn_match_apply.clicked.connect(self.on_match_apply)
        row_apply.addWidget(self.btn_match_apply, 2)

        self.btn_match_reset = QPushButton("Reset")
        self.btn_match_reset.setMinimumHeight(38)
        self.btn_match_reset.setToolTip("Back to the original (Weight 0), keep the target loaded.")
        self.btn_match_reset.clicked.connect(self.on_match_reset)
        row_apply.addWidget(self.btn_match_reset, 1)

        lay.addLayout(row_apply)

        self.update_match_pairs()
        return page

    # --------------------------------------------------------------
    # Match > By Weight
    # --------------------------------------------------------------

    def _mesh_pick_row(self, label, tip, on_load):
        """메시 **한 개**를 담는 줄: 이름 칸(읽기 전용) + Load 버튼."""
        row = QHBoxLayout()
        lb = QLabel(label)
        lb.setMinimumWidth(78)
        row.addWidget(lb)
        le = QLineEdit()
        le.setReadOnly(True)
        le.setPlaceholderText("select a mesh, then Load")
        le.setToolTip(tip)
        row.addWidget(le, 1)
        btn = QPushButton("Load")
        btn.setToolTip("Take the first selected mesh.")
        btn.clicked.connect(on_load)
        row.addWidget(btn)
        return row, le

    def build_match_weight_page(self):
        """스킨 웨이트를 마스크로 M_j 를 M_tgt 쪽으로 옮긴다 (블렌드셰이프 웨이트 맵과 같은 결과).

        M_w(스킨 메시)의 조인트를 체크 → 짝지은 M_j 마다
        `new = cur + weight(jnt, v) * Strength * (M_tgt - cur)` (오브젝트 공간, 버텍스 인덱스 대응).
        """
        page = QWidget()
        lay = QVBoxLayout(page)
        # 스크롤바 폭만큼 좁아지므로 좌우 여백을 뺀다(Meshes TSL 버튼 줄이 잘리지 않게).
        lay.setContentsMargins(0, 6, 0, 0)

        # ---- M_w + 조인트 -------------------------------------------
        box_w = QGroupBox("Weight Mesh (skinned)")
        vw = QVBoxLayout(box_w)
        row, self.le_wm_weight = self._mesh_pick_row(
            "Weight Mesh", "The skinned mesh whose joint weights are the mask.",
            self.on_wm_load_weight)
        vw.addLayout(row)

        head = QHBoxLayout()
        head.addWidget(QLabel("Joints"))
        head.addStretch(1)
        self.lb_wm_joints = QLabel("Number: 0")
        head.addWidget(self.lb_wm_joints)
        vw.addLayout(head)

        self.lw_wm_joints = QListWidget()
        self.lw_wm_joints.setMinimumHeight(120)
        self.lw_wm_joints.setToolTip(
            "Joints the weight mesh is bound to. Check the ones to use.\n"
            "Shift / Ctrl click selects several rows - clicking the check box of a\n"
            "selected row (or Space) checks or unchecks every selected row.\n"
            "Grey = bound but carries no weight.")
        self.chk_wm_joints = JUN_mod_checkList_qt_v01(self.lw_wm_joints)
        self.lw_wm_joints.itemChanged.connect(lambda _i: self.update_wm_pairs())
        self.chk_wm_joints.checksChanged.connect(lambda _l: self.update_wm_pairs())
        vw.addWidget(self.lw_wm_joints, 1)

        row_f = QHBoxLayout()
        self.flt_wm_joints = JUN_mod_filter_qt_v01(
            self.lw_wm_joints, placeholder="Type any part of a joint name",
            number_label=self.lb_wm_joints)
        row_f.addWidget(self.flt_wm_joints, 1)
        vw.addLayout(row_f)
        # 버튼은 필터와 한 줄에 두면 폭이 넓어져 따로 둔다.
        row_f = QHBoxLayout()
        btn_all = QPushButton("Check All")
        btn_all.setToolTip("Check every joint currently visible.")
        btn_all.clicked.connect(lambda: self._wm_set_all(True))
        row_f.addWidget(btn_all)
        btn_none = QPushButton("Clear")
        btn_none.setToolTip("Uncheck every joint.")
        btn_none.clicked.connect(lambda: self._wm_set_all(False))
        row_f.addWidget(btn_none)
        row_f.addStretch(1)
        vw.addLayout(row_f)
        lay.addWidget(box_w, 1)

        # ---- M_tgt ----------------------------------------------------
        row, self.le_wm_target = self._mesh_pick_row(
            "Target Mesh", "The shape to move toward (same mesh as the weight mesh).",
            self.on_wm_load_target)
        lay.addLayout(row)

        # ---- M_j ------------------------------------------------------
        box_m = QGroupBox("Meshes to Move")
        vm = QVBoxLayout(box_m)
        self.tsl_wm_meshes = JUN_mod_tsl_qt_v01(
            title="Meshes", select_label="List Selected",
            # Sort 는 뺀다 - 순서는 Up / Down 으로 조인트와 맞추는 것이고, 버튼 줄이 스크롤 폭을
            # 넘는다(테마 적용 401px > 395px, 실측).
            show_sort=False,
            list_min_height=90, log_callback=self.log)
        model = self.tsl_wm_meshes.list_widget.model()
        for sig in (model.rowsInserted, model.rowsRemoved, model.rowsMoved,
                    model.modelReset, model.layoutChanged):
            sig.connect(lambda *_a: self.update_wm_pairs())
        vm.addWidget(self.tsl_wm_meshes)
        lay.addWidget(box_m, 1)

        # ---- 짝짓기 ---------------------------------------------------
        box_p = QGroupBox("Pairing (joint weights -> mesh)")
        vp = QVBoxLayout(box_p)
        self.rb_wm_order = QRadioButton("Joint k -> Mesh k")
        self.rb_wm_order.setChecked(True)
        self.rb_wm_order.setToolTip(
            "The k-th checked joint (list order) masks the k-th mesh.\n"
            "e.g. jnt_01 -> M_01, jnt_02 -> M_02. Extra joints / meshes are skipped.")
        self.rb_wm_sum = QRadioButton("Sum -> every mesh")
        self.rb_wm_sum.setToolTip(
            "The checked joints' weights are added up (clamped to 1) and that one\n"
            "mask is used on every mesh in the list.")
        grp = QButtonGroup(self)
        grp.addButton(self.rb_wm_order)
        grp.addButton(self.rb_wm_sum)
        self.rb_wm_order.toggled.connect(lambda _c: self.update_wm_pairs())
        # 테마 qss 에서 라디오 하나가 245px 이라 한 줄에 두면 창 폭을 넘는다(실측) - 세로로.
        vp.addWidget(self.rb_wm_order)
        vp.addWidget(self.rb_wm_sum)

        self.tw_wm_pairs = QTreeWidget()
        self.tw_wm_pairs.setHeaderLabels(["Mesh", "Joint weights"])
        self.tw_wm_pairs.setRootIsDecorated(False)
        self.tw_wm_pairs.setMinimumHeight(70)
        self.tw_wm_pairs.setToolTip("What Apply will do. Grey rows are skipped.")
        vp.addWidget(self.tw_wm_pairs)
        lay.addWidget(box_p)

        # ---- 세기 + 적용 ---------------------------------------------
        row_s = QHBoxLayout()
        row_s.addWidget(QLabel("Strength"))
        self.sp_wm_strength = QDoubleSpinBox()
        self.sp_wm_strength.setDecimals(3)
        self.sp_wm_strength.setRange(0.0, 1.0)
        self.sp_wm_strength.setSingleStep(0.05)
        self.sp_wm_strength.setValue(1.0)
        self.sp_wm_strength.setToolTip(
            "Multiplies every mask. 1 = a vertex with weight 1 lands exactly on the\n"
            "target, weight 0.2 moves 20% of the way.")
        row_s.addWidget(self.sp_wm_strength, 1)
        lay.addLayout(row_s)

        self.btn_wm_apply = QPushButton("Apply By Weight")
        self.btn_wm_apply.setMinimumHeight(38)
        self.btn_wm_apply.setToolTip(
            "Move each mesh toward the target by its joint weights\n"
            "(object space, same vertex index). One Ctrl+Z undoes all.")
        self.btn_wm_apply.clicked.connect(self.on_wm_apply)
        lay.addWidget(self.btn_wm_apply)

        return page

    # ==============================================================
    # MeshDoctor 탭 (v01.14, 옛 A00300_meshDoctor 이식)
    # ==============================================================

    def build_doctor_tab(self):
        """진단(읽기 전용) + 안전한 원클릭 수정.

        A00300 은 대상 리스트를 직접 만들어 썼지만, 이 툴은 이미 공용 TSL 위젯을 쓰므로
        그쪽으로 맞췄다 — 행을 누르면 씬에서 선택되고, 항목은 UUID 로 보관되어
        리네임/리페어런트 뒤에도 같은 메시를 가리킨다.
        """

        page = QWidget()
        lay = QVBoxLayout(page)

        # ---- 대상 메시 --------------------------------------------
        self.tsl_doctor = JUN_mod_tsl_qt_v01(
            title="Target Meshes",
            show_sort=True, show_order=False, select_label="List Selected",
            list_min_height=90, log_callback=self.log)
        self.tsl_doctor.setToolTip(
            "Meshes to diagnose. Empty = diagnose whatever is selected in the scene.\n"
            "Clicking a row selects that mesh in the scene.")
        lay.addWidget(self.tsl_doctor)

        # ---- 진단 행 ----------------------------------------------
        diag_row = QHBoxLayout()
        self.btn_diagnose = QPushButton("Diagnose Listed")
        self.btn_diagnose.setMinimumHeight(38)
        self.btn_diagnose.setToolTip(
            "Diagnose every mesh in the list above, or the current scene selection\n"
            "when the list is empty. Reads the meshes only - nothing is changed.")
        self.btn_diagnose.clicked.connect(self.on_diagnose)
        diag_row.addWidget(self.btn_diagnose, 3)

        self.btn_open_reports = QPushButton("Open Report Folder")
        self.btn_open_reports.setMinimumHeight(38)
        self.btn_open_reports.setToolTip(
            "Open the 0020_out folder where the JSON / TXT reports are written.")
        self.btn_open_reports.clicked.connect(self.on_open_report_folder)
        diag_row.addWidget(self.btn_open_reports, 1)
        lay.addLayout(diag_row)

        # ---- 요약 표 (메시 한 줄, 행을 누르면 아래에 상세) ----------
        self.tbl_summary = QTableWidget(0, 3)
        self.tbl_summary.setHorizontalHeaderLabels(["Mesh", "Status", "Issues"])
        self.tbl_summary.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_summary.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_summary.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_summary.verticalHeader().setVisible(False)
        self.tbl_summary.setMinimumHeight(120)
        self.tbl_summary.setToolTip(
            "Click a row to read that mesh's full report below.\n"
            "The row is also selected in the scene.")
        hdr = self.tbl_summary.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_summary.itemSelectionChanged.connect(self._on_summary_row)
        lay.addWidget(self.tbl_summary, 1)

        # ---- 상세 리포트 -------------------------------------------
        # 공용 로그창은 이 툴 전체가 쓰는 한 줄짜리 상태 표시줄이라(높이 110), 수십 줄짜리
        # 진단 리포트를 거기 쏟으면 둘 다 못 읽는다. 리포트는 탭 안에 따로 둔다.
        self.te_report = QTextEdit()
        self.te_report.setReadOnly(True)
        self.te_report.setLineWrapMode(QTextEdit.NoWrap)
        self.te_report.setMinimumHeight(150)
        self.te_report.setToolTip("Full report of the mesh selected in the table above.")
        try:
            self.te_report.setFont(QFont("Consolas", 9))
        except Exception:
            pass
        lay.addWidget(self.te_report, 2)

        # ---- 안전한 원클릭 수정 -------------------------------------
        fixes = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            "Safe One-Click Fixes  (undoable)", expanded=False)
        for label, fn, tip in [
            ("Delete History (deformer-safe)", MeshFixer.delete_history,
             "Bake out leftover poly history, keep skinCluster / blendShape."),
            ("Merge Vertices", MeshFixer.merge_vertices,
             "Merge coincident / unmerged vertices (tolerance 1e-4)."),
            ("Conform Normals", MeshFixer.conform_normals,
             "Unlock + conform face normals (fixes flipped / locked normals)."),
            ("polyCleanup (fix corruption)", MeshFixer.poly_cleanup,
             "Fix non-manifold + lamina + zero-area faces + zero-length edges.\n"
             "May change topology - re-skin if needed."),
            ("Snap NaN / Stray Verts", MeshFixer.snap_stray_verts,
             "Move NaN / stray verts to the mesh centroid (nothing is deleted)\n"
             "-> deflates the bounding box, fixes selection in empty space."),
        ]:
            b = QPushButton(label)
            b.setMinimumHeight(30)
            b.setToolTip(tip)
            b.clicked.connect(self._doctor_fix(fn))
            fixes.add_widget(b)
        lay.addWidget(fixes)

        # ---- 문제 컴포넌트 선택 -------------------------------------
        picks = JUN_mod_collapsible_qt.JUN_mod_collapsible_qt_v01(
            "Select Problem Components", expanded=False)
        for label, fn, tip in [
            ("Select Non-Manifold", MeshFixer.select_non_manifold,
             "Select the non-manifold edges / vertices so you can look at them."),
            ("Select Zero-Area Faces", MeshFixer.select_zero_area_faces,
             "Select degenerate / sliver faces (not the small-but-fine ones)."),
            ("Select Stray / NaN Verts", MeshFixer.select_stray_verts,
             "Select vertices sitting far outside the mesh, or holding NaN."),
        ]:
            b = QPushButton(label)
            b.setMinimumHeight(28)
            b.setToolTip(tip)
            b.clicked.connect(self._doctor_fix(fn))
            picks.add_widget(b)
        lay.addWidget(picks)

        return page

    # ---- MeshDoctor 동작 -------------------------------------------

    def on_diagnose(self):
        """리스트(비어 있으면 씬 선택)를 진단해 요약 표를 채우고 리포트를 쓴다."""

        nodes = self.tsl_doctor.get_all_nodes()
        source = "listed"

        if not nodes:
            nodes = cmds.ls(selection=True, long=True) or []
            source = "selection"

        try:
            results = self.scanner.scan_nodes(nodes)
        except Exception as e:
            self.log("Diagnose failed: {0}".format(e), warn=True)
            return

        self._doctor_results = results
        self._fill_summary(results)
        self.te_report.clear()

        if not results:
            where = "in the list" if source == "listed" else "selected"
            self.log("No polygon mesh {0}. List meshes (or select some) and "
                     "try again.".format(where), warn=True)
            return

        worst = self._worst_of(results)
        self.log("Diagnosed {0} mesh(es) [{1}] - worst: {2}. Click a row for the "
                 "full report.".format(len(results), source, worst),
                 warn=worst in ("FAIL", "WARN"), ok=worst == "PASS")

        try:
            json_path, txt_path, out_dir = ReportWriter().write(results)
            self._last_out_dir = out_dir
            self.log("  report: {0}".format(json_path))
        except Exception as e:
            self.log("Failed to write the report file: {0}".format(e), warn=True)

        # 진단 직후에는 가장 심한 메시의 상세를 바로 펼쳐 준다(한 번 더 클릭하지 않게).
        worst_row = self._worst_row(results)
        if worst_row >= 0:
            self.tbl_summary.selectRow(worst_row)

    @staticmethod
    def _worst_of(results):
        for sev in ("FAIL", "WARN", "INFO"):
            if any(r["worst"] == sev for r in results):
                return sev
        return "PASS"

    @staticmethod
    def _worst_row(results):
        for sev in ("FAIL", "WARN", "INFO"):
            for i, r in enumerate(results):
                if r["worst"] == sev:
                    return i
        return 0 if results else -1

    @staticmethod
    def _issue_summary(r):
        """WARN / FAIL 인 검사만 'name(count)' 로 줄인다(FAIL 먼저). 없으면 'clean'."""
        parts = []
        for sev in ("FAIL", "WARN"):
            for chk in r["checks"]:
                if chk["severity"] != sev:
                    continue
                parts.append("{0}({1})".format(chk["check"], chk["count"])
                             if chk["count"] else chk["check"])
        return ", ".join(parts) if parts else "clean"

    def _fill_summary(self, results):

        self.tbl_summary.blockSignals(True)
        self.tbl_summary.setRowCount(0)

        for r in results:
            row = self.tbl_summary.rowCount()
            self.tbl_summary.insertRow(row)

            mesh_item = QTableWidgetItem(r["transform"])
            mesh_item.setToolTip(r.get("transform_full", r["transform"]))

            status_item = QTableWidgetItem("● " + r["worst"])
            color = _SEV_COLOR.get(r["worst"])
            if color:
                status_item.setForeground(QColor(color))

            issues_item = QTableWidgetItem(self._issue_summary(r))
            issues_item.setToolTip(issues_item.text())

            self.tbl_summary.setItem(row, 0, mesh_item)
            self.tbl_summary.setItem(row, 1, status_item)
            self.tbl_summary.setItem(row, 2, issues_item)

        self.tbl_summary.blockSignals(False)

    def _on_summary_row(self):
        """행을 고르면 그 메시의 상세 리포트를 띄우고 씬에서도 선택한다."""

        row = self.tbl_summary.currentRow()
        if row < 0 or row >= len(self._doctor_results):
            return

        result = self._doctor_results[row]
        self._print_result(result)

        # 표에서 고른 메시를 씬에서도 집어 준다. 전체 경로가 있으면 그쪽이 정확하다.
        node = result.get("transform_full") or result.get("transform")
        try:
            if node and cmds.objExists(node):
                cmds.select(node, replace=True)
        except Exception:
            pass

    def _print_result(self, r):
        """A00300 의 상세 리포트 형식 그대로 — 탭 안 리포트 뷰에 쓴다."""

        c = r.get("counts", {})
        self.te_report.clear()

        def put(text, severity=None):
            color = _SEV_COLOR.get(severity)
            if color:
                self.te_report.append(
                    '<span style="color:{0};">{1}</span>'.format(color, self._esc(text)))
            else:
                self.te_report.append(text)

        put("=" * 60)
        put("MESH: {0}  [{1}]  => {2}".format(r["transform"], r["shape"], r["worst"]),
            r["worst"])
        put("  verts={0} edges={1} faces={2} shells={3}".format(
            c.get("vertices", "?"), c.get("edges", "?"),
            c.get("faces", "?"), c.get("shells", "?")))

        for cause in r.get("suspected_root_causes", []):
            put("  >> " + cause, "WARN" if "Symptom" in cause else "PASS")

        put("-" * 60)

        clean = True
        for chk in r["checks"]:
            if chk["severity"] == "PASS":
                continue
            clean = False
            line = "  [{0}] {1}".format(chk["severity"], chk["check"])
            if chk["count"]:
                line += " (count={0})".format(chk["count"])
            put(line, chk["severity"])
            put("      " + chk["message"])

        if clean:
            put("  Nothing to report - every check passed.", "PASS")

        self.te_report.moveCursor(QTextCursor.Start)

    def _doctor_fix(self, fn):
        """수정 버튼 하나를 슬롯으로. clicked 가 넘기는 checked(bool) 는 버린다."""

        def _slot(*_args):
            try:
                msg = fn()
            except Exception as e:
                self.log("{0} failed: {1}".format(
                    getattr(fn, "__name__", "fix"), e), warn=True)
                return
            self.log("{0}  -> re-run Diagnose to confirm.".format(msg), ok=True)

        return _slot

    def on_open_report_folder(self):

        out_dir = self._last_out_dir

        if not out_dir:
            # 아직 한 번도 안 썼으면 기본 0020_out 경로라도 열어 준다.
            try:
                out_dir = str(ReportWriter().pm.path("write"))
            except Exception:
                out_dir = None

        if out_dir and os.path.isdir(out_dir):
            try:
                os.startfile(out_dir)
            except Exception as e:
                self.log("Could not open the folder: {0}".format(e), warn=True)
        else:
            self.log("No report folder yet. Run Diagnose first.", warn=True)

    # ==============================================================
    # 상태
    # ==============================================================

    def has_session(self):
        return self.session is not None

    def update_state(self):

        on = self.has_session()

        for w in (self.sl_amount, self.sp_amount, self.sp_step, self.sp_range,
                  self.btn_minus, self.btn_plus):
            w.setEnabled(on)

        if not on:
            self.lb_target.setText("Nothing loaded.")
            return

        names = self.session.mesh_names()
        head = names[0] if len(names) == 1 else "{0} meshes".format(len(names))

        text = "{0}  |  {1} vertice(s)".format(head, self.session.vertex_count)
        if self.session.is_soft:
            text += "  |  soft selection"

        self.lb_target.setText(text)

    def amount(self):
        return self.sp_amount.value()

    def set_amount(self, value):
        """슬라이더/스핀박스를 함께 맞추고 미리보기를 갱신한다."""

        rng = self.sp_range.value()
        value = max(-rng, min(rng, value))

        self._syncing = True
        self.sp_amount.setValue(value)
        self.sl_amount.setValue(int(round(value / rng * SLIDER_TICKS)))
        self._syncing = False

        self.apply_preview()

    def apply_preview(self, throttle=False):
        """미리보기 갱신.

        throttle=True 는 슬라이더를 잡고 끄는 중이라는 뜻이다. 아주 무거운 메시에서
        모든 슬라이더 눈금마다 갱신하면 UI 가 밀리므로, 직전 미리보기가 오래
        걸렸다면 그 시간만큼 지나기 전엔 건너뛴다. 손을 떼면 항상 마지막 값으로
        한 번 더 갱신하므로 결과가 어긋나지는 않는다.
        """

        if not self.has_session():
            return

        if throttle and self._last_preview_sec > _HEAVY_SEC:
            if (time.time() - self._last_preview_at) < self._last_preview_sec:
                return

        start = time.time()

        try:
            self.session.preview(self.amount())
        except Exception as e:
            self.log("Preview failed: {0}".format(e), warn=True)
            return

        self._last_preview_sec = time.time() - start
        self._last_preview_at = time.time()
        # amount 이 0 이면 preview 가 스냅샷 그대로를 쓴 것 → 되돌릴 게 없다.
        self._preview_dirty = abs(self.amount()) > 1e-9

    # ==============================================================
    # 이벤트
    # ==============================================================

    def on_slider_changed(self, tick):

        if self._syncing:
            return

        value = tick / float(SLIDER_TICKS) * self.sp_range.value()

        self._syncing = True
        self.sp_amount.setValue(value)
        self._syncing = False

        # 슬라이더를 잡고 있는 동안만 솎아낸다 (손을 떼면 sliderReleased 가 마무리).
        self.apply_preview(throttle=self.sl_amount.isSliderDown())

    def on_spin_changed(self, value):

        if self._syncing:
            return

        rng = self.sp_range.value()

        # 스핀박스로 슬라이더 범위를 넘겨 입력하면 범위를 늘려 준다.
        if abs(value) > rng:
            self._syncing = True
            self.sp_range.setValue(abs(value))
            self._syncing = False
            rng = abs(value)

        self._syncing = True
        self.sl_amount.setValue(int(round(value / rng * SLIDER_TICKS)))
        self._syncing = False

        self.apply_preview()

    def on_range_changed(self, rng):

        if self._syncing:
            return

        # 범위가 바뀌어도 현재 값은 유지되도록 슬라이더 위치만 다시 계산한다.
        self.set_amount(self.amount())

    def nudge(self, sign):
        # ± 한 번은 한 스텝을 곧바로 최종 결과로 확정한다(별도 Apply 없음).
        self.set_amount(self.amount() + sign * self.sp_step.value())
        self.commit_stroke()

    # ---- 로드 / 클리어 --------------------------------------------

    def on_load(self, silent=False):

        # 확정하지 않은 미리보기가 있으면 먼저 되돌린다.
        self.discard_preview()

        try:
            session = peak_mgr.PeakSession.from_selection(
                angle_weighted=self.chk_angle.isChecked(),
                soft_select=self.chk_soft.isChecked())
        except Exception as e:
            self.session = None
            self.update_state()
            self.log("Load failed: {0}".format(e), warn=True)
            return

        self.session = session
        self._preview_dirty = False   # 새 스냅샷 → 미리보기 없음

        self._syncing = True
        self.sp_amount.setValue(0.0)
        self.sl_amount.setValue(0)
        self._syncing = False

        self.update_state()

        if session is None:
            if not silent:
                self.log("Nothing to load. Select a mesh or its vertices.", warn=True)
            return

        msg = "Loaded {0} vertice(s) on {1}.".format(
            session.vertex_count, ", ".join(session.mesh_names()))
        if session.is_soft:
            msg += " (soft selection falloff active)"

        if not silent:
            self.log(msg)

    def on_clear(self):
        self.discard_preview()
        self.session = None
        self.update_state()
        self.log("Cleared.")

    def discard_preview(self):
        """미확정 미리보기가 있을 때만 스냅샷 상태로 되돌린다.

        미리보기를 쓴 적이 없으면(_preview_dirty=False) restore 를 부르지 않는다.
        안 그러면 auto-load 가 선택 변경마다 restore 를 불러, 슬라이더를 건드리지 않고
        사용자가 손으로 옮긴 버텍스까지 스냅샷으로 되돌려 버린다(= 편집이 원상복구되는 버그).
        """

        if not self.has_session() or not self._preview_dirty:
            return

        try:
            self.session.restore()
        except Exception:
            pass
        self._preview_dirty = False

    # ---- 확정(자동) ----------------------------------------------

    def commit_stroke(self):
        """현재 amount 를 그대로 최종 결과로 확정한다(undo 가능, 한 스텝).

        Apply 버튼을 대신한다. 슬라이더를 놓거나(sliderReleased), 스핀박스 입력을
        마치거나(editingFinished), ± 를 누르면 호출된다. 확정 후 amount 를 0 으로
        되돌리고 세션을 새 스냅샷으로 삼아(commit 이 갱신), 이어서 계속 조절할 수 있다.
        """

        if not self.has_session():
            return

        value = self.amount()
        if abs(value) < 1e-9:
            return   # 변화 없음 — 조용히 무시

        try:
            with undo_chunk():
                moved = self.session.commit(value)
        except Exception as e:
            self.log("Apply failed: {0}".format(e), warn=True)
            return

        self._preview_dirty = False   # 확정됨 → 씬이 곧 스냅샷(commit 이 갱신)

        self._syncing = True
        self.sp_amount.setValue(0.0)
        self.sl_amount.setValue(0)
        self._syncing = False

        verb = "Inflated" if value > 0 else "Shrunk"
        self.log("{0} {1} vertice(s) by {2:.4f}.".format(verb, moved, abs(value)),
                 ok=True)

    # ==============================================================
    # Match 탭 로직
    # ==============================================================

    def has_match_session(self):
        return self.match_session is not None

    def match_weight(self):
        return self.sp_match.value()

    def set_match_weight(self, value):
        """슬라이더/스핀박스를 함께 맞추고 (세션이 있으면) 미리보기를 갱신한다."""

        value = max(0.0, min(1.0, value))

        self._match_syncing = True
        self.sp_match.setValue(value)
        self.sl_match.setValue(int(round(value * SLIDER_TICKS)))
        self._match_syncing = False

        self.match_preview()

    @staticmethod
    def _short(node):
        return node.split("|")[-1]

    def _match_pairing(self):
        """좌/우 리스트로 짝을 짓는다 -> match_mgr.pair_meshes 의 결과 그대로."""
        return match_mgr.pair_meshes(self.tsl_from.get_all_nodes(),
                                     self.tsl_match_targets.get_all_nodes())

    def update_match_pairs(self):
        """짝 미리보기 표 + 모드 줄을 지금 리스트에 맞춘다."""
        if not hasattr(self, "tw_match_pairs"):
            return
        # 리스트가 바뀌면 미리보기 세션은 옛 짝의 것이다 - 되돌리고 버린다. 안 버리면
        # Apply 가 그 세션을 재사용해 **지금 리스트와 다른 짝**으로 확정한다(실측).
        self.discard_match_preview()
        self.match_session = None
        sources = self.tsl_from.get_all_nodes()
        targets = self.tsl_match_targets.get_all_nodes()
        mode, pairs, extra_src, extra_tgt = self._match_pairing()

        self.tw_match_pairs.clear()
        for src, tgt in pairs:
            self.tw_match_pairs.addTopLevelItem(
                QTreeWidgetItem([self._short(src), self._short(tgt)]))
        grey = QBrush(QColor("#808080"))
        for src in extra_src:
            item = QTreeWidgetItem([self._short(src), "(no target - skipped)"])
            for col in range(2):
                item.setForeground(col, grey)
            self.tw_match_pairs.addTopLevelItem(item)
        for tgt in extra_tgt:
            item = QTreeWidgetItem(["(no source - skipped)", self._short(tgt)])
            for col in range(2):
                item.setForeground(col, grey)
            self.tw_match_pairs.addTopLevelItem(item)

        if not sources or not targets:
            text = "List Source mesh(es) on the left and Target mesh(es) on the right."
        elif mode == match_mgr.MODE_ONE_TO_MANY:
            text = "1 <= {0} : every Target takes the Source's shape.".format(len(targets))
        else:
            text = "{0} <= {0} : k-th Target takes the k-th Source's shape.".format(len(pairs))
            if extra_src or extra_tgt:
                text += "  ({0} left unmatched)".format(len(extra_src) + len(extra_tgt))
        self.lb_match_mode.setText(text)

    def _match_build(self, progress=None):
        """좌/우 리스트의 짝으로 세션을 새로 만든다. 실패 시 None (v01.10~).

        좌 1개 = 1 <= n, 여러 개 = n <= n(작은 쪽 수만큼). 짝이 없어 남은 메시는 로그에 적는다.
        만들기 전에 이전 미리보기는 되돌린다(dirty 가드).
        """

        self.discard_match_preview()
        self.match_session = None

        sources = self.tsl_from.get_all_nodes()
        targets = self.tsl_match_targets.get_all_nodes()
        if not sources or not targets:
            self.log("List Source mesh(es) on the left and Target mesh(es) on the right "
                     "(select them, then 'List Selected').", warn=True)
            return None

        mode, pairs, extra_src, extra_tgt = self._match_pairing()
        if mode == match_mgr.MODE_PAIRWISE and (extra_src or extra_tgt):
            self.log("Source {0} / Target {1} - matching the first {2} pair(s) only."
                     .format(len(sources), len(targets), len(pairs)), warn=True)
            for src in extra_src:
                self.log("  Unmatched Source '{0}' (#{1}): no Target at that position - "
                         "skipped.".format(self._short(src), sources.index(src) + 1),
                         warn=True)
            for tgt in extra_tgt:
                self.log("  Unmatched Target '{0}' (#{1}): no Source at that position - "
                         "left unchanged.".format(self._short(tgt), targets.index(tgt) + 1),
                         warn=True)

        try:
            session, skipped = match_mgr.MatchSession.from_pairs(
                pairs,
                world=self.chk_match_world.isChecked(),
                soft_select=self.chk_match_soft.isChecked(),
                progress=progress)
        except Exception as e:
            self.log("Match build failed: {0}".format(e), warn=True)
            return None

        for src, tgt, why in skipped:
            self.log("  Skipped '{0}' <= '{1}': {2}.".format(
                self._short(tgt), self._short(src), why), warn=True)

        self.match_session = session
        self._match_preview_dirty = False
        if session is None:
            self.log("Nothing to match.", warn=True)
            return None

        for name, count, src_name, src_count in session.mismatch:
            self.log("Warning: '{0}' has {1}v but '{2}' has {3}v. Matching is "
                     "index-based; only overlapping indices move.".format(
                         name, count, src_name, src_count), warn=True)
        if session.skipped_count:
            self.log("{0} vertice(s) have no matching index on their Source "
                     "and were skipped.".format(session.skipped_count), warn=True)

        return session

    def match_preview(self, throttle=False):
        """Match 미리보기 갱신 (Peak 의 apply_preview 와 같은 스로틀 규칙)."""

        if not self.has_match_session():
            return

        if throttle and self._last_preview_sec > _HEAVY_SEC:
            if (time.time() - self._last_preview_at) < self._last_preview_sec:
                return

        start = time.time()
        try:
            self.match_session.preview(self.match_weight())
        except Exception as e:
            self.log("Match preview failed: {0}".format(e), warn=True)
            return
        self._last_preview_sec = time.time() - start
        self._last_preview_at = time.time()
        self._match_preview_dirty = self.match_weight() > 1e-9

    def on_match_slider_pressed(self):
        """슬라이더를 잡는 순간, 현재 선택으로 세션을 만들어 미리보기를 준비한다."""
        if self._match_build() is not None:
            self.match_preview()

    def on_match_slider_changed(self, tick):

        if self._match_syncing:
            return

        value = tick / float(SLIDER_TICKS)

        self._match_syncing = True
        self.sp_match.setValue(value)
        self._match_syncing = False

        # 슬라이더를 잡았을 때 만든 세션이 있으면 미리보기(없으면 조용히 무시).
        if self.has_match_session():
            self.match_preview(throttle=self.sl_match.isSliderDown())

    def on_match_spin_changed(self, value):

        if self._match_syncing:
            return

        self._match_syncing = True
        self.sl_match.setValue(int(round(value * SLIDER_TICKS)))
        self._match_syncing = False

        # 스핀박스로 값을 넣으면 현재 선택으로 세션을 만들어 미리보기한다.
        if not self.has_match_session():
            self._match_build()
        self.match_preview()

    def discard_match_preview(self):
        """미확정 Match 미리보기가 있을 때만 스냅샷 상태로 되돌린다.

        Peak 의 discard_preview 와 같은 이유로 dirty 일 때만 restore 한다(수동 편집 보존).
        """

        if not self.has_match_session() or not self._match_preview_dirty:
            return
        try:
            self.match_session.restore()
        except Exception:
            pass
        self._match_preview_dirty = False

    def on_match_apply(self):
        """우측 Target 메시들을 좌측 Source 모양으로 확정한다(Ctrl+Z 한 번).

        미리보기 중이면 그 세션을, 아니면 지금 리스트로 만든다.
        도는 동안 공용 진행률 팝업(`JUN_mod_progress_qt_v01`)이 뜬다(v01.11~).
        """

        weight = self.match_weight()
        if weight < 1e-9:
            self.log("Weight is 0 - nothing to apply.", warn=True)
            return

        # 미리보기 세션이 있으면 읽기 단계는 이미 끝났다 - 돌지 않는 단계는 목록에서 뺀다
        # (자리를 남겨 두면 게이지가 중간에서 시작하는 것처럼 보인다).
        session = self.match_session
        phases = [("Writing vertices", 70)]
        if session is None:
            phases.insert(0, ("Reading meshes", 30))

        dlg = JUN_mod_progress_qt_v01(self, title="Mesh Tool - Apply Match",
                                      phases=phases)
        dlg.start()
        moved = None
        try:
            if session is None:
                dlg.begin_phase()
                session = self._match_build(progress=dlg.callback())
            if session is not None:
                dlg.begin_phase()
                with undo_chunk():
                    moved = session.commit(weight, progress=dlg.callback())
        except Exception as e:
            self.log("Match apply failed: {0}".format(e), warn=True)
            return
        finally:
            elapsed = dlg.elapsed()
            dlg.finish()

        if moved is None:
            return

        self.log("Matched {0} mesh(es), {1} vertice(s) at weight {2:.3f} ({3:.1f}s).".format(
            session.mesh_count, moved, weight, elapsed), ok=True)
        for t in session.targets:
            self.log("  {0} <= {1}".format(t.target_name, t.from_name))

        # 확정 후에는 원본이 이미 이동했으므로 세션을 비운다(다음 Apply 는 새 선택으로).
        self._match_preview_dirty = False
        self.match_session = None

    def on_match_reset(self):
        """미리보기 중이면 원본(Weight 0)으로 되돌린다."""
        if not self.has_match_session():
            self.log("No match preview to reset.")
            return
        self.set_match_weight(0.0)
        self.log("Match reset to 0.")

    # ---- Match > By Weight -------------------------------------------

    def _first_selected_mesh(self):
        """선택 중 첫 메시의 트랜스폼(짧은 이름). 컴포넌트를 골랐어도 그 메시."""
        for node in cmds.ls(sl=True, objectsOnly=True) or []:
            try:
                shape = peak_mgr._shape_of(node)
            except Exception:
                shape = None
            if shape:
                parent = cmds.listRelatives(shape, parent=True, fullPath=True)
                return (cmds.ls(parent[0])[0] if parent else shape)
        return None

    def on_wm_load_weight(self):
        """M_w 를 담고 그 메시를 바인드한 조인트를 체크 목록에 채운다."""
        mesh = self._first_selected_mesh()
        if not mesh:
            self.log("Select a skinned mesh first.", warn=True)
            return
        try:
            sw = wm_mgr.SkinWeights(mesh)
        except Exception as e:
            self.log(str(e), warn=True)
            return

        keep = set(self._wm_checked_joints())
        used = set(sw.bound_joints())
        self.lw_wm_joints.blockSignals(True)
        self.lw_wm_joints.clear()
        # 이름순 — jnt_01, jnt_02 ... 가 그대로 Mesh 01, 02 ... 와 짝이 되도록.
        for joint in sorted(sw.joints):
            item = QListWidgetItem(joint)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if joint in keep else Qt.Unchecked)
            if joint not in used:
                item.setForeground(QBrush(QColor("#808080")))
                item.setToolTip("Bound, but carries no weight on this mesh.")
            self.lw_wm_joints.addItem(item)
        self.lw_wm_joints.blockSignals(False)

        self.le_wm_weight.setText(mesh)
        self.flt_wm_joints.refresh()
        self.update_wm_pairs()
        self.log("Weight mesh: {0} ({1}, {2} joint(s), {3} with weight, {4} vertices)."
                 .format(mesh, sw.skin, len(sw.joints), len(used), sw.vertex_count), ok=True)

    def on_wm_load_target(self):
        mesh = self._first_selected_mesh()
        if not mesh:
            self.log("Select the target mesh first.", warn=True)
            return
        self.le_wm_target.setText(mesh)
        self.update_wm_pairs()
        self.log("Target mesh: {0}".format(mesh), ok=True)

    def _wm_set_all(self, checked):
        """Check All 은 보이는 행만 켜고, Clear 는 가려진 것까지 전부 끈다."""
        self.lw_wm_joints.blockSignals(True)
        for i in range(self.lw_wm_joints.count()):
            item = self.lw_wm_joints.item(i)
            if checked and item.isHidden():
                continue
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self.lw_wm_joints.blockSignals(False)
        self.update_wm_pairs()

    def _wm_checked_joints(self):
        """체크한 조인트, 목록 순서대로."""
        return [self.lw_wm_joints.item(i).text()
                for i in range(self.lw_wm_joints.count())
                if self.lw_wm_joints.item(i).checkState() == Qt.Checked]

    def _wm_pairs(self):
        mode = wm_mgr.PAIR_ORDER if self.rb_wm_order.isChecked() else wm_mgr.PAIR_SUM
        meshes = self.tsl_wm_meshes.get_all_items()
        return wm_mgr.make_pairs(meshes, self._wm_checked_joints(), mode)

    def update_wm_pairs(self):
        """짝 미리보기 표를 다시 그린다."""
        if not hasattr(self, "tw_wm_pairs"):
            return
        pairs, left_meshes, left_joints = self._wm_pairs()
        self.tw_wm_pairs.clear()
        grey = QBrush(QColor("#808080"))
        for mesh, joints in pairs:
            self.tw_wm_pairs.addTopLevelItem(
                QTreeWidgetItem([mesh.split("|")[-1], " + ".join(joints)]))
        for mesh in left_meshes:
            item = QTreeWidgetItem([mesh.split("|")[-1], "(no joint - skipped)"])
            item.setForeground(0, grey)
            item.setForeground(1, grey)
            self.tw_wm_pairs.addTopLevelItem(item)
        for joint in left_joints:
            item = QTreeWidgetItem(["(no mesh - skipped)", joint])
            item.setForeground(0, grey)
            item.setForeground(1, grey)
            self.tw_wm_pairs.addTopLevelItem(item)
        self.tw_wm_pairs.resizeColumnToContents(0)

    def on_wm_apply(self):
        weight_mesh = self.le_wm_weight.text().strip()
        target = self.le_wm_target.text().strip()
        if not weight_mesh:
            self.log("Load a Weight Mesh first.", warn=True)
            return
        if not target:
            self.log("Load a Target Mesh first.", warn=True)
            return
        pairs, left_meshes, left_joints = self._wm_pairs()
        if not pairs:
            self.log("Nothing to apply - check joints and list meshes to move.", warn=True)
            return
        strength = self.sp_wm_strength.value()
        if strength < 1e-9:
            self.log("Strength is 0 - nothing to apply.", warn=True)
            return

        # Default 탭의 미확정 미리보기가 같은 메시의 pnts 에 남아 있으면 섞인다.
        self.discard_match_preview()
        try:
            with undo_chunk():
                done, skipped = wm_mgr.apply(weight_mesh, target, pairs, strength)
        except Exception as e:
            self.log("By Weight failed: {0}".format(e), warn=True)
            return

        for mesh, reason in skipped:
            self.log("{0}: skipped - {1}".format(mesh.split("|")[-1], reason), warn=True)
        for mesh in left_meshes:
            self.log("{0}: skipped - no joint paired".format(mesh.split("|")[-1]), warn=True)
        for joint in left_joints:
            self.log("{0}: not used - no mesh paired".format(joint), warn=True)
        for mesh, joints, moved, peak, sculpt in done:
            self.log("{0} <- {1}: {2} vertice(s) moved (max weight {3:.3f}){4}.".format(
                mesh.split("|")[-1], " + ".join(joints), moved, peak,
                " into sculpt target {0}".format(sculpt) if sculpt else ""), ok=True)
        if done:
            self.log("By Weight: {0} mesh(es) toward {1} at strength {2:.3f}.".format(
                len(done), target, strength), ok=True)

    def on_tab_changed(self, index):
        """탭을 옮기면, 떠나는 탭의 확정 안 한 미리보기를 되돌린다.

        두 탭 모두 shape.pnts 에 쓰므로, 한쪽 미리보기가 남은 채 다른 탭에서 작업하면
        결과가 겹쳐 보인다. 탭 전환 시 확정하지 않은 미리보기는 스냅샷으로 되돌린다.
        """
        self.discard_preview()
        self.discard_match_preview()

    # ---- 자동 로드 -------------------------------------------------

    def on_auto_toggled(self, on):
        if on:
            self.start_script_job()
        else:
            self.kill_script_job()

    def start_script_job(self):

        if self._script_job is not None:
            return

        try:
            self._script_job = cmds.scriptJob(
                event=["SelectionChanged", self.on_selection_changed],
                protected=False)
        except Exception as e:
            self.log("Auto load unavailable: {0}".format(e), warn=True)

    def kill_script_job(self):

        if self._script_job is None:
            return

        try:
            if cmds.scriptJob(exists=self._script_job):
                cmds.scriptJob(kill=self._script_job, force=True)
        except Exception:
            pass

        self._script_job = None

    def on_selection_changed(self):

        if not self.chk_auto.isChecked():
            return

        try:
            self.on_load(silent=True)
        except Exception:
            pass

    # ==============================================================
    # show / close
    # ==============================================================

    def showEvent(self, event):
        super(MainWindow, self).showEvent(event)
        if self.chk_auto.isChecked():
            self.start_script_job()

    def closeEvent(self, event):
        # 확정하지 않은 미리보기를 남긴 채 닫으면 씬이 어긋난 상태로 보인다.
        self.discard_preview()
        self.discard_match_preview()
        self.kill_script_job()
        super(MainWindow, self).closeEvent(event)

    # ==============================================================
    # log / about
    # ==============================================================

    @staticmethod
    def _esc(text):
        return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    def log(self, text, warn=False, ok=False):

        if warn:
            color = _WARN_COLOR
        elif ok:
            color = _OK_COLOR
        else:
            color = None

        if color:
            self.te_log.append(
                '<span style="color:{0};">{1}</span>'.format(color, self._esc(text)))
        else:
            self.te_log.append(text)

    def show_uv_rule(self):
        QMessageBox.information(self, "UV Sets Rule", UV_RULE_TEXT)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Mesh Tool\nv{0}  ({1})\n\n"
            "Peak: inflate / shrink a mesh along its vertex normals,\n"
            "like Houdini's peak node.\n\n"
            "Match: reshape the Target meshes (right list) into the Source\n"
            "mesh(es) (left list), same vertex index - one Source shapes every\n"
            "Target, several are paired in list order. A standalone take on\n"
            "Kangaroo's Geometry > Match.\n"
            "Match > By Weight: move meshes toward a target by a skinned\n"
            "mesh's joint weights (like a blend shape weight map).\n\n"
            "MeshDoctor: read-only diagnostics - list meshes, diagnose them,\n"
            "read the per-mesh report, and run the safe one-click fixes.\n"
            "Reports are written to the tool's 0020_out folder.\n\n"
            "UV Sets: one UV set per mesh (default 'map1') - catch the meshes\n"
            "that break it, delete the other sets, rename the first one.\n"
            "Ported from A00050_uvTool_V02. See Help > UV Sets Rule.\n\n"
            "Peak has no Apply button: dragging the slider applies the\n"
            "result as you go (each change is one Ctrl+Z).\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))
