# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-10
# A00290_BSTool - Qt UI (레거시 JUN_PY_BSTool_V01_01 의 PySide 재작성)
#
# 탭 구성:
#   1) Shape Editor : blendShape 노드의 모든 타겟을 리스트업 → 타겟마다 Edit 토글
#                     (Maya 기본 Shape Editor 대체)
#   2) Edit BS      : blendShape 노드 리스트 → 모든 타겟 키 / 타겟 메시 추출
#   3) Base Shape   : blendShape 의 타겟을 리스트업 → 선택 타겟의 weight=value 모양을
#                     weight=1.0 기본 모양으로 재정의(델타 스케일)

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window

print("QT version  :  " + str(QT_VERSION))

import maya.cmds as cmds

from tools.A00290_BSTool.app.config.version import VERSION, LAST_UPDATE
from tools.A00290_BSTool.app.core import EditBSManager, BaseShapeManager, ShapeEditorManager
from tools.A00290_BSTool.app.core import blendshape_utils as bsu


# Edit 토글이 켜졌을 때의 버튼 색(Maya Shape Editor 의 활성 Edit 버튼과 같은 의미).
# 테마 qss 의 QPushButton:hover / :pressed 는 pseudo-state 규칙이라, 색만 바꾸면
# 마우스를 올리는 순간 테마 색으로 되돌아가 보인다. 그래서 hover/pressed 까지 함께 덮는다.
EDIT_ON_STYLE = (
    "QPushButton { background-color: #c85a28; color: #ffffff;"
    " border: 1px solid #f09050; font-weight: bold; }"
    "QPushButton:hover { background-color: #d96a34; }"
    "QPushButton:pressed { background-color: #a8441c; }"
)
EDIT_ON_TEXT = "Edit ON"
EDIT_OFF_TEXT = "Edit"

# WeightSlider 전용 스타일.
# 어떤 테마 qss 도 QSlider 를 스타일링하지 않아, 어두운 배경에선 Maya 네이티브 홈(groove)이
# 배경에 묻혀 핸들만 보인다("가로 막대가 안 보임"). 그래서 위젯이 자체적으로 홈을 그린다.
# 이 슬라이더는 중앙이 0 인 양방향이라, 한쪽에서 채워지는 sub-page fill 은 0 에서도 절반이
# 찬 것처럼 보여 오해를 준다. 그래서 홈을 좌우 균일한 한 줄로만 그리고, 0 위치는 기존 중앙
# 눈금(TicksBelow)이 표시한다. green_dark 테마 색(#6f9e80)에 맞췄다.
SLIDER_STYLE = (
    "QSlider:horizontal { min-height: 20px; }"
    # 홈: 좌우 균일한 트랙 + accent 테두리 (sub/add-page 를 같은 색으로 덮어 방향성 제거)
    "QSlider::groove:horizontal {"
    " height: 6px; margin: 0 4px;"
    " background: #353835; border: 1px solid #6f9e80; border-radius: 3px; }"
    "QSlider::sub-page:horizontal, QSlider::add-page:horizontal {"
    " background: #353835; border: 1px solid #6f9e80; border-radius: 3px; }"
    # 핸들: 홈 위로 튀어나오게
    "QSlider::handle:horizontal {"
    " width: 12px; margin: -6px 0;"
    " background: #cfe6d6; border: 1px solid #6f9e80; border-radius: 3px; }"
    "QSlider::handle:horizontal:hover { background: #ffffff; }"
    # 비활성(구동/잠긴 weight, 편집 중): 전체를 흐리게
    "QSlider::groove:horizontal:disabled,"
    " QSlider::sub-page:horizontal:disabled,"
    " QSlider::add-page:horizontal:disabled {"
    " background: #2f2f2f; border: 1px solid #454545; }"
    "QSlider::handle:horizontal:disabled {"
    " background: #5a5a5a; border: 1px solid #454545; }"
)


# Shape Editor 탭 인덱스 (weight 폴링을 이 탭이 보일 때만 돌리기 위해 필요)
SHAPE_EDITOR_TAB = 0

# 씬에서 weight 가 바뀌어도(채널박스, 어트리뷰트 에디터, 애니메이션 재생, 다른 스크립트 등)
# Maya 는 Qt 에 알려 주지 않는다. 그래서 주기적으로 다시 읽어 스핀박스에 반영한다.
SE_SYNC_INTERVAL_MS = 120

# 스핀박스가 보여 주는 마지막 자리(decimals=3)의 절반. 이보다 작은 차이는 화면상 같은 값이라
# 다시 써 봐야 소용이 없다.
SE_WEIGHT_EPS = 0.0005


# 리로드/재실행 시 기존 창을 찾아 닫기 위한 고유 objectName
WINDOW_OBJECT_NAME = "JUN_A00290_BSTool_window"
TARGETS_WINDOW_OBJECT_NAME = "JUN_A00290_BSTool_targets_window"


class TargetsWindow(QWidget):
    """Shape Editor 의 타겟 영역을 크게 보는 별도 창(Expand).

    타겟 행을 복제하지 않고 **스크롤 영역 자체를 옮겨 온다**. 그래서 Edit 토글 / 슬라이더 /
    실시간 폴링이 그대로 동작하고, 두 벌을 동기화할 일이 없다. 창을 닫으면 탭의 제자리로
    되돌아간다.
    """

    def __init__(self, owner):
        super().__init__(owner, Qt.Window)
        self._owner = owner
        self.setObjectName(TARGETS_WINDOW_OBJECT_NAME)
        self.setWindowTitle("BS Tool - Targets")
        self.resize(640, 900)

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Filter"))
        self.le_filter = QLineEdit()
        self.le_filter.setPlaceholderText("Type to filter target names")
        top.addWidget(self.le_filter, 1)
        self.lbl_number = QLabel("Number: 0")
        top.addWidget(self.lbl_number)
        layout.addLayout(top)

        # 탭에서 넘겨받은 스크롤 영역이 들어갈 자리
        self.body = QVBoxLayout()
        layout.addLayout(self.body, 1)

    def closeEvent(self, event):
        self._owner.on_se_collapse()
        super().closeEvent(event)


class WeightSlider(QSlider):
    """중앙이 0, 왼쪽 끝이 -1, 오른쪽 끝이 +1 인 가로 슬라이더.

    QSlider 는 정수만 다루므로 weight 를 SCALE 배 한 정수로 담는다(0.001 해상도).
    스핀박스(-10~10)보다 범위가 좁다. 범위를 벗어난 weight 는 슬라이더에서 끝에 붙고,
    실제 값은 옆의 스핀박스가 보여 준다.
    """

    SCALE = 1000
    MIN = -1.0
    MAX = 1.0

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(int(self.MIN * self.SCALE), int(self.MAX * self.SCALE))
        # 양 끝과 중앙(0)에 눈금을 찍어 0 위치를 눈으로 찾을 수 있게 한다.
        self.setTickPosition(QSlider.TicksBelow)
        self.setTickInterval(int(self.MAX * self.SCALE))
        self.setSingleStep(self.SCALE // 100)   # 방향키 0.01
        self.setPageStep(self.SCALE // 10)      # PageUp/Down 0.1
        self.setMinimumWidth(110)
        # 테마 qss 가 QSlider 를 스타일링하지 않아 홈이 배경에 묻히므로 직접 그린다.
        self.setStyleSheet(SLIDER_STYLE)

    def weight(self):
        return self.value() / float(self.SCALE)

    def _clamp(self, value):
        return max(self.MIN, min(self.MAX, value))

    def set_weight(self, value):
        self.setValue(int(round(self._clamp(value) * self.SCALE)))

    def shows(self, value, eps):
        """이 슬라이더가 이미 그 weight 를(범위 밖이면 클램프한 값을) 가리키고 있는가."""
        return abs(self.weight() - self._clamp(value)) < eps


# 선택된 타겟 행 배경(다중 편집 대상 표시). green_dark accent 계열.
ROW_SELECTED_STYLE = "QFrame#seTargetRow { background-color: #3f5c48; border-radius: 3px; }"


class TargetRow(QFrame):
    """Shape Editor 의 타겟 한 줄. 칸(빈 영역/이름)을 클릭하면 선택된다.

    슬라이더/스핀박스/Edit 버튼은 자기 클릭을 소비하므로 편집을 방해하지 않는다.
    QLabel 은 클릭을 무시(ignore)해 부모(이 행)로 전달되므로 이름 칸 클릭도 선택으로 잡힌다.
    """

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self._owner = owner
        self.row_info = None            # _add_se_target_row 에서 연결
        self.setObjectName("seTargetRow")

    def mousePressEvent(self, event):
        if self.row_info is not None:
            self._owner._on_se_row_clicked(self.row_info, event.modifiers())
        super().mousePressEvent(event)


class MainWindow(QWidget):

    def __init__(self):

        super().__init__(maya_main_window())

        self.setObjectName(WINDOW_OBJECT_NAME)

        # Shape Editor 탭의 타겟 행 정보:
        # [{node, index, name, row, btn, spin, slider, selected}, ...]
        self._se_rows = []
        self._se_rebuild_pending = False
        # 다중 편집 중 위젯 setValue 가 다시 on_se_weight_changed 를 부르는 재귀를 막는다.
        self._se_applying = False
        # Shift 범위 선택의 기준점(직전 단일/토글 선택 행). 재빌드 때 초기화한다.
        self._se_anchor = None
        # 슬라이더 드래그 전체를 하나의 undo 로 묶기 위한 상태.
        # 드래그는 매 틱 setAttr 을 내는데, 청크로 안 묶으면 Ctrl+Z 가 마지막 한 틱(한 타겟)만
        # 되돌린다. press~release 를 한 청크로 감싼다.
        self._se_dragging = False
        self._se_undo_open = False

        # Expand 로 띄운 별도 타겟 창 (없으면 None)
        self._se_window = None

        # 씬의 weight 를 스핀박스로 되비추는 폴링 타이머. Shape Editor 탭이 보일 때만 돈다.
        # (build_ui 가 tabs.currentChanged 를 붙이며 이 타이머를 건드리므로 먼저 만든다.)
        self._se_sync_timer = QTimer(self)
        self._se_sync_timer.setInterval(SE_SYNC_INTERVAL_MS)
        self._se_sync_timer.timeout.connect(self._sync_se_weights)

        # 타겟 행이 Edit + 이름 + 슬라이더 + 스핀박스라 460 이면 슬라이더가 눌린다.
        self.win_width = 580
        self.win_height = 720
        self.win_title = f"BS Tool v{VERSION}"

        self.resize(self.win_width, self.win_height)

        self.build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        main_layout = QVBoxLayout(self)

        # 메뉴 바 (Help > About)
        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self.show_about)
        main_layout.setMenuBar(self.menu_bar)

        # 탭
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_shape_editor_tab(), "Shape Editor")
        self.tabs.addTab(self._build_edit_bs_tab(), "Edit BS")
        self.tabs.addTab(self._build_base_shape_tab(), "Base Shape")
        self.tabs.currentChanged.connect(lambda *_a: self._update_se_timer())
        main_layout.addWidget(self.tabs)

        # 공용 로그
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMinimumHeight(80)
        self.te_log.setMaximumHeight(140)
        main_layout.addWidget(self.te_log)

        # 저작권
        self.lbl_copyright = QLabel("Copyright (c) Park Ji Hun. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_copyright)

    # ==================================================
    # Tab 1 : Shape Editor
    # ==================================================

    def _build_shape_editor_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # blendShape 노드 리스트 (씬 선택 연동). 노드가 추가/삭제되면 타겟을 다시 훑는다.
        self.tsl_se_nodes = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="BlendShape Nodes",
            select_label="Select BlendShape Nodes",
            list_min_height=70,
            log_callback=self.log)
        self.tsl_se_nodes.list_widget.model().rowsInserted.connect(
            self._on_se_nodes_changed)
        self.tsl_se_nodes.list_widget.model().rowsRemoved.connect(
            self._on_se_nodes_changed)
        layout.addWidget(self.tsl_se_nodes)

        # 필터 + 새로고침
        tool_row = QHBoxLayout()
        tool_row.addWidget(QLabel("Filter"))
        self.le_se_filter = QLineEdit()
        self.le_se_filter.setPlaceholderText("Type to filter target names")
        self.le_se_filter.textChanged.connect(self._apply_se_filter)
        tool_row.addWidget(self.le_se_filter)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setToolTip("Re-read targets and weights from the listed blendShape nodes.")
        btn_refresh.clicked.connect(self.on_se_refresh)
        tool_row.addWidget(btn_refresh)
        btn_expand = QPushButton("Expand")
        btn_expand.setToolTip("Show the target list in a separate, resizable window.")
        btn_expand.clicked.connect(self.on_se_expand)
        tool_row.addWidget(btn_expand)
        layout.addLayout(tool_row)

        # 타겟 헤더
        header = QHBoxLayout()
        lbl_t = QLabel("Targets")
        f = lbl_t.font()
        f.setBold(True)
        lbl_t.setFont(f)
        header.addWidget(lbl_t)

        # 다중 선택: 선택한 여러 타겟을 슬라이더/스핀박스 하나로 동시에 조절한다.
        # (행을 클릭하면 선택, Shift+클릭으로 여러 개 선택/해제.)
        btn_select_all = QPushButton("Select All")
        btn_select_all.setToolTip("Select all currently visible targets for multi-edit.")
        btn_select_all.clicked.connect(lambda: self._se_select_all(True))
        header.addWidget(btn_select_all)
        btn_clear_sel = QPushButton("Clear")
        btn_clear_sel.setToolTip("Clear the target selection.")
        btn_clear_sel.clicked.connect(lambda: self._se_select_all(False))
        header.addWidget(btn_clear_sel)

        header.addStretch(1)
        self.lbl_se_number = QLabel("Number: 0")
        header.addWidget(self.lbl_se_number)
        layout.addLayout(header)

        # 타겟 행 스크롤 영역 (blendShape 별 헤더 + 타겟마다 Edit 토글 / weight)
        self.se_scroll = QScrollArea()
        self.se_scroll.setWidgetResizable(True)
        self.se_scroll.setMinimumHeight(260)
        self.se_body = QWidget()
        self.se_body_layout = QVBoxLayout(self.se_body)
        self.se_body_layout.setContentsMargins(2, 2, 2, 2)
        self.se_body_layout.setSpacing(2)
        self.se_body_layout.addStretch(1)
        self.se_scroll.setWidget(self.se_body)
        layout.addWidget(self.se_scroll, 1)

        # Expand 로 스크롤 영역을 별도 창에 넘겨준 동안 탭에서 그 자리를 지킨다.
        # (숨긴 위젯은 레이아웃에서 자리를 차지하지 않으므로 평소엔 보이지 않는다.)
        self.lbl_se_expanded = QLabel("Targets are shown in the expanded window.")
        self.lbl_se_expanded.setAlignment(Qt.AlignCenter)
        self.lbl_se_expanded.setVisible(False)
        layout.addWidget(self.lbl_se_expanded, 1)

        # 스크롤 영역을 되돌릴 때 쓸 원래 자리
        self.se_tab_layout = layout
        self.se_scroll_index = layout.indexOf(self.se_scroll)

        # 설명
        info = QLabel(
            "Turn Edit on, sculpt the base mesh in the viewport, then turn Edit off\n"
            "to bake the change into that target - same as Maya's Shape Editor.\n"
            "Click a target row to select it; Shift+click selects the range in between,\n"
            "Ctrl+click toggles one. Then drag or type one value to change all selected.\n"
            "Keyed targets are editable: with Auto Key on the change is keyed, "
            "with it off it is a preview that reverts when you scrub time.")
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_exit = QPushButton("Exit Edit Mode (all blendShapes)")
        btn_exit.setToolTip("Turn off edit mode on every blendShape node in the scene.")
        btn_exit.clicked.connect(self.on_se_exit_all)
        layout.addWidget(btn_exit)

        return tab

    # --------------------------------------------------
    # Shape Editor : 행 구성
    # --------------------------------------------------

    def _clear_se_rows(self):
        # 드래그 청크가 열린 채 행이 재생성되면 청크가 누수된다. 안전하게 닫는다.
        if self._se_undo_open:
            cmds.undoInfo(closeChunk=True)
            self._se_undo_open = False
        self._se_dragging = False
        self._se_rows = []
        self._se_anchor = None
        # 마지막 stretch 를 제외한 모든 위젯 제거
        while self.se_body_layout.count() > 1:
            item = self.se_body_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _add_se_node_header(self, bs_node):
        lbl = QLabel(bs_node)
        f = lbl.font()
        f.setBold(True)
        lbl.setFont(f)
        lbl.setContentsMargins(2, 6, 2, 2)
        self.se_body_layout.insertWidget(self.se_body_layout.count() - 1, lbl)

    def _add_se_target_row(self, bs_node, target, editing_idx):
        idx = target["index"]
        is_editing = (idx == editing_idx)

        row = TargetRow(self)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(2, 0, 2, 0)

        btn = QPushButton(EDIT_OFF_TEXT)
        btn.setCheckable(True)
        # "Edit ON" 으로 바뀌어도 폭이 흔들리지 않도록 고정.
        btn.setFixedWidth(72)
        btn.setToolTip("Toggle sculpt mode on this target (blendShape sculptTargetIndex).")
        btn.setChecked(is_editing)
        self._style_edit_button(btn, is_editing)
        # clicked 는 clicked(bool checked=false) 라 인자 없이 발화될 수 있다.
        # 시그널 인자에 기대지 말고 버튼에서 직접 체크 상태를 읽는다.
        btn.clicked.connect(
            lambda *_a, n=bs_node, i=idx, b=btn: self.on_se_edit_toggled(n, i, b.isChecked()))
        row_layout.addWidget(btn)

        lbl = QLabel(target["name"])
        lbl.setToolTip("weight[{0}]".format(idx))
        row_layout.addWidget(lbl, 1)

        # 편집 가능(free/keyed) 하고 sculpt 편집 중이 아니면 조절 가능.
        enabled = target["editable"] and not is_editing

        slider = WeightSlider()
        slider.set_weight(target["weight"])
        slider.setEnabled(enabled)
        row_layout.addWidget(slider, 1)

        spin = QDoubleSpinBox()
        spin.setDecimals(3)
        spin.setRange(-10.0, 10.0)
        spin.setSingleStep(0.1)
        spin.setFixedWidth(72)
        spin.setValue(target["weight"])
        spin.setEnabled(enabled)
        row_layout.addWidget(spin)

        self._apply_se_row_tooltip(slider, spin, target["state"])

        self.se_body_layout.insertWidget(self.se_body_layout.count() - 1, row)
        row_info = {
            "node": bs_node, "index": idx, "name": target["name"],
            "row": row, "btn": btn, "spin": spin, "slider": slider,
            "selected": False,
        }
        row.row_info = row_info
        self._se_rows.append(row_info)

        # 슬라이더와 스핀박스는 같은 weight 를 가리키는 두 얼굴이다. 어느 쪽을 움직이든
        # 씬에 쓰고 반대쪽을 맞춘다.
        # valueChanged 는 바인딩/버전에 따라 double 또는 문자열을 넘긴다. 위젯에서 직접 읽는다.
        spin.valueChanged.connect(
            lambda *_a, r=row_info, s=spin: self.on_se_weight_changed(r, s.value()))
        slider.valueChanged.connect(
            lambda *_a, r=row_info, s=slider: self.on_se_weight_changed(r, s.weight()))
        # 드래그 전체를 한 undo 로 묶는다(press~release 한 청크).
        slider.sliderPressed.connect(self._se_slider_pressed)
        slider.sliderReleased.connect(self._se_slider_released)

    @staticmethod
    def _apply_se_row_tooltip(slider, spin, state):
        """weight 상태에 맞는 툴팁을 슬라이더/스핀박스에 건다."""
        base = "Drag to set the weight. Center is 0, right end +1, left end -1."
        if state == "keyed":
            tip = (base + "\nKeyed: with Auto Key on the change is keyframed at the "
                   "current time; with it off it is a preview that reverts when you "
                   "scrub time.")
        elif state == "driven":
            tip = "This weight is driven by another node and cannot be edited."
        elif state == "locked":
            tip = "This weight is locked and cannot be edited."
        else:
            tip = base
        slider.setToolTip(tip)
        spin.setToolTip(tip)

    def _style_edit_button(self, btn, on):
        """Edit 토글의 현재 상태(색 + 라벨)를 버튼에 반영한다."""
        btn.setStyleSheet(EDIT_ON_STYLE if on else "")
        btn.setText(EDIT_ON_TEXT if on else EDIT_OFF_TEXT)

    def _populate_shape_editor(self):
        """리스트의 blendShape 노드들을 훑어 타겟 행을 다시 만든다."""
        self._clear_se_rows()

        nodes = [n for n in self.tsl_se_nodes.get_all_items() if bsu.is_blendshape(n)]
        total = 0
        for bs_node in nodes:
            targets = ShapeEditorManager.list_targets(bs_node)
            editing_idx = ShapeEditorManager.get_edit_target(bs_node)
            if len(nodes) > 1 or not targets:
                self._add_se_node_header(bs_node)
            for target in targets:
                self._add_se_target_row(bs_node, target, editing_idx)
            total += len(targets)

        self.lbl_se_number.setText("Number: {0}".format(total))
        if self._se_window is not None:
            self._se_window.lbl_number.setText(self.lbl_se_number.text())
        self._apply_se_filter(self.le_se_filter.text())
        self._update_se_timer()
        return nodes, total

    def _apply_se_filter(self, text):
        needle = (text or "").strip().lower()
        for row in self._se_rows:
            row["row"].setVisible(needle in row["name"].lower())
        # 필터는 하나지만 입력 칸은 탭과 확장 창에 하나씩 있다. 서로 맞춰 준다.
        # (같을 때 쓰지 않으므로 textChanged 가 서로를 부르며 맴돌지 않는다.)
        if self._se_window is not None and self._se_window.le_filter.text() != (text or ""):
            self._se_window.le_filter.setText(text or "")

    def _sync_se_edit_states(self):
        """씬의 실제 sculptTargetIndex 를 읽어 Edit 버튼/스핀박스 상태를 맞춘다."""
        editing = {}
        for row in self._se_rows:
            node = row["node"]
            if node not in editing:
                editing[node] = ShapeEditorManager.get_edit_target(node)

            on = (editing[node] == row["index"])

            row["btn"].blockSignals(True)
            row["btn"].setChecked(on)
            row["btn"].blockSignals(False)
            self._style_edit_button(row["btn"], on)

            state = ShapeEditorManager.weight_state(node, row["index"])
            editable = state in ("free", "keyed")
            self._show_weight(row, ShapeEditorManager.get_weight(node, row["index"]))
            row["spin"].setEnabled(editable and not on)
            row["slider"].setEnabled(editable and not on)
            self._apply_se_row_tooltip(row["slider"], row["spin"], state)

    # --------------------------------------------------
    # Shape Editor : 씬 -> UI weight 실시간 반영
    # --------------------------------------------------

    @staticmethod
    def _show_weight(row, value):
        """행의 슬라이더/스핀박스에 값을 표시한다.

        setValue 는 valueChanged 를 발화해 on_se_weight_changed 로 되돌아온다. 그대로 두면
        방금 씬에서 읽은 값을 씬에 다시 쓰고(잠긴/구동되는 weight 는 매 틱 경고 로그까지 남는다),
        슬라이더 -> 스핀박스 -> 슬라이더 로 되울리기까지 한다. 그래서 시그널을 막고 쓴다.
        """
        for widget, setter in ((row["spin"], row["spin"].setValue),
                               (row["slider"], row["slider"].set_weight)):
            widget.blockSignals(True)
            setter(value)
            widget.blockSignals(False)

    @staticmethod
    def _user_is_dragging(row):
        """사용자가 그 행의 위젯을 직접 만지는 중이면 밑에서 값을 바꾸지 않는다.

        슬라이더는 '잡고 있는 동안'(isSliderDown)만 막는다. hasFocus 까지 막으면 한 번 클릭한
        행은 포커스를 옮길 때까지 씬 변화를 영영 못 따라온다.
        """
        return row["spin"].hasFocus() or row["slider"].isSliderDown()

    def _update_se_timer(self):
        """폴링은 타겟 행이 실제로 화면에 있을 때만 돌린다.

        확장 창이 떠 있으면 타겟은 그쪽에 있다. 이때는 본 창이 가려져 있거나 다른 탭이어도
        계속 갱신해야 한다.
        """
        expanded = self._se_window is not None and self._se_window.isVisible()
        active = bool(self._se_rows) and (
            expanded
            or (self.isVisible() and self.tabs.currentIndex() == SHAPE_EDITOR_TAB))
        if active and not self._se_sync_timer.isActive():
            self._se_sync_timer.start()
        elif not active and self._se_sync_timer.isActive():
            self._se_sync_timer.stop()

    def _sync_se_weights(self):
        """씬의 현재 weight 를 슬라이더/스핀박스에 반영한다(UI -> 씬 방향은 건드리지 않는다)."""
        for row in self._se_rows:
            node = row["node"]
            if not cmds.objExists(node):
                # 노드가 지워졌다. 행 자체는 Refresh(또는 노드 리스트 변경) 때 다시 만든다.
                continue

            if self._user_is_dragging(row):
                continue

            value = ShapeEditorManager.get_weight(node, row["index"])
            # 두 위젯을 다 봐야 한다. 씬에 못 쓴 조작(잠긴/구동되는 weight 를 민 경우)은 한쪽만
            # 어긋난 채 남으므로, 스핀박스만 보고 판단하면 그 행은 영영 되돌아오지 않는다.
            if (abs(value - row["spin"].value()) < SE_WEIGHT_EPS
                    and row["slider"].shows(value, SE_WEIGHT_EPS)):
                continue

            self._show_weight(row, value)

    # --------------------------------------------------
    # Handlers : Shape Editor
    # --------------------------------------------------

    def _on_se_nodes_changed(self, *args):
        # set_items 는 clear + add 로 rowsRemoved / rowsInserted 를 연달아 낸다.
        # 이벤트 루프로 한 번 미뤄 재빌드를 1회로 합친다.
        if self._se_rebuild_pending:
            return
        self._se_rebuild_pending = True
        QTimer.singleShot(0, self._rebuild_se_now)

    def _rebuild_se_now(self):
        self._se_rebuild_pending = False
        self._populate_shape_editor()

    def on_se_refresh(self):
        nodes, total = self._populate_shape_editor()
        if not nodes:
            self.log("[Warning] Add blendShape nodes to the list first.")
            return
        self.log("[Shape Editor] {0} node(s), {1} target(s).".format(len(nodes), total))

    def on_se_edit_toggled(self, bs_node, weight_idx, checked):
        if checked:
            _ok, msg = ShapeEditorManager.begin_edit(bs_node, weight_idx)
        else:
            _ok, msg = ShapeEditorManager.end_edit(bs_node)
        self.log(msg)
        # 노드당 한 타겟만 편집할 수 있으므로 다른 행의 상태도 다시 맞춘다.
        self._sync_se_edit_states()

    def _co_edit_rows(self, row):
        """이번 조작이 적용될 행들.

        조작한 행이 다중 선택의 일부면 선택된 행 전체, 아니면 그 행 하나.
        """
        selected = [r for r in self._se_rows if r["selected"]]
        if row in selected and len(selected) > 1:
            return selected
        return [row]

    # --------------------------------------------------
    # Shape Editor : 행 선택(칸 클릭 / Shift 다중)
    # --------------------------------------------------

    def _on_se_row_clicked(self, row, modifiers):
        """타겟 칸 클릭.

        - Shift+클릭 : 기준점(anchor)부터 이 행까지 **사이의 (보이는) 행 전체를 선택**(범위).
        - Ctrl+클릭  : 이 행만 선택 토글(비연속 다중 선택).
        - 그냥 클릭   : 이 행만 단일 선택. (Shift/Ctrl 이 아닐 때는 기준점을 이 행으로 갱신)
        """
        shift = bool(modifiers & Qt.ShiftModifier)
        ctrl = bool(modifiers & Qt.ControlModifier)

        anchor_alive = any(r is self._se_anchor for r in self._se_rows)
        if shift and anchor_alive:
            self._se_select_range(self._se_anchor, row)   # 기준점은 유지
        elif ctrl:
            row["selected"] = not row["selected"]
            self._se_anchor = row
        else:
            for r in self._se_rows:
                r["selected"] = (r is row)
            self._se_anchor = row

        self._refresh_se_selection_styles()

    def _se_select_range(self, anchor, row):
        """표시 순서로 anchor..row 구간을 선택하고 나머지는 해제한다.

        필터로 보이는 행만 대상으로 한다(화면상 A~B 사이). 기준점/끝점이 숨겨진 예외
        상황에서는 전체 순서로 폴백한다.
        """
        seq = [r for r in self._se_rows if r["row"].isVisible()]
        if anchor not in seq or row not in seq:
            seq = self._se_rows

        # 행 정보는 dict(unhashable)이므로 정체성(id)으로 구간을 판별한다.
        i = next(k for k, r in enumerate(seq) if r is anchor)
        j = next(k for k, r in enumerate(seq) if r is row)
        lo, hi = (i, j) if i <= j else (j, i)
        in_range = {id(r) for r in seq[lo:hi + 1]}

        for r in self._se_rows:
            r["selected"] = (id(r) in in_range)

    def _refresh_se_selection_styles(self):
        """각 행의 배경을 선택 상태에 맞게 칠한다."""
        for r in self._se_rows:
            r["row"].setStyleSheet(ROW_SELECTED_STYLE if r["selected"] else "")

    def _se_select_all(self, selected):
        """현재 보이는(필터 통과) 행들의 선택 상태를 일괄 설정한다."""
        for row in self._se_rows:
            if row["row"].isVisible():
                row["selected"] = selected
            elif selected is False:
                row["selected"] = False
        # 일괄 조작 뒤에는 기준점을 지워, 다음 Shift+클릭이 엉뚱한 구간을 잡지 않게 한다.
        self._se_anchor = None
        self._refresh_se_selection_styles()

    def _se_slider_pressed(self):
        """슬라이더를 잡았다. 놓을 때까지의 변경을 한 undo 로 묶기 시작한다."""
        self._se_dragging = True

    def _se_slider_released(self):
        """슬라이더를 놓았다. 드래그 청크를 닫는다."""
        self._se_dragging = False
        if self._se_undo_open:
            cmds.undoInfo(closeChunk=True)
            self._se_undo_open = False

    def on_se_weight_changed(self, row, value):
        """슬라이더나 스핀박스를 움직였다. 대상 행들에 값을 쓰고 위젯을 맞춘다.

        다중 선택이면 같은 value 를 선택된 모든 타겟에 동시에 적용한다.

        undo 는 **제스처 단위**로 묶는다:
          - 슬라이더 드래그: press~release 전체를 한 청크로(첫 변경 때 lazy open). 매 틱마다
            여러 타겟에 setAttr 을 내므로, 안 묶으면 Ctrl+Z 가 마지막 한 틱(한 타겟)만 되돌린다.
          - 스핀박스/개별 변경: 그 한 번의 변경(선택된 모든 타겟)을 한 청크로 감싼다.
        """
        if self._se_applying:
            return

        rows = self._co_edit_rows(row)
        # Auto Keyframe 상태는 이번 조작에서 한 번만 조회해 모든 행에 같은 기준을 쓴다.
        autokey = ShapeEditorManager.is_autokey_on()

        own_chunk = False
        if self._se_dragging:
            # 드래그: 첫 변경에서 청크를 열고 release 에서 닫는다.
            if not self._se_undo_open:
                cmds.undoInfo(openChunk=True)
                self._se_undo_open = True
        else:
            # 스핀박스 등 이산 변경: 이 한 번을 청크로 감싼다.
            cmds.undoInfo(openChunk=True)
            own_chunk = True

        self._se_applying = True
        try:
            for r in rows:
                ok, msg = ShapeEditorManager.set_weight(
                    r["node"], r["index"], value, autokey=autokey)
                if not ok:
                    # 다중 편집에서 잠긴/구동 타겟이 섞여 있을 수 있다. 매 틱 로그를 쏟지 않도록
                    # 조용히 건너뛴다(단일 편집이면 한 번 알린다).
                    if len(rows) == 1:
                        self.log(msg)
                    continue
                self._show_weight(r, value)
        finally:
            self._se_applying = False
            if own_chunk:
                cmds.undoInfo(closeChunk=True)

    def on_se_expand(self):
        """타겟 스크롤 영역을 별도 창으로 옮긴다(이미 떠 있으면 앞으로 가져온다)."""
        if self._se_window is not None:
            self._se_window.raise_()
            self._se_window.activateWindow()
            return

        win = TargetsWindow(self)
        win.lbl_number.setText(self.lbl_se_number.text())
        win.le_filter.setText(self.le_se_filter.text())
        win.le_filter.textChanged.connect(self.le_se_filter.setText)
        # addWidget 이 스크롤 영역을 탭 레이아웃에서 떼어 이 창으로 옮긴다.
        win.body.addWidget(self.se_scroll)
        self._se_window = win

        self.lbl_se_expanded.setVisible(True)
        win.show()
        self._update_se_timer()

    def on_se_collapse(self):
        """확장 창이 닫혔다. 스크롤 영역을 탭의 원래 자리로 되돌린다."""
        if self._se_window is None:
            return

        win, self._se_window = self._se_window, None
        self.lbl_se_expanded.setVisible(False)
        self.se_tab_layout.insertWidget(self.se_scroll_index, self.se_scroll, 1)
        win.deleteLater()
        self._update_se_timer()

    def on_se_exit_all(self):
        _n, msg = ShapeEditorManager.exit_all_edits()
        self.log(msg)
        self._sync_se_edit_states()

    # ==================================================
    # Tab 2 : Edit BS
    # ==================================================

    def _build_edit_bs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # blendShape 노드 리스트 (씬 선택 연동)
        self.tsl_bs_nodes = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="BlendShape Nodes",
            select_label="Select BlendShape Nodes",
            log_callback=self.log)
        layout.addWidget(self.tsl_bs_nodes)

        # 동작 버튼
        btn_key = QPushButton("Key every target")
        btn_key.setToolTip(
            "Keyframe each target so it shows one at a time: frame i = 1, i-1/i+1 = 0.")
        btn_key.clicked.connect(self.on_key_every_target)
        layout.addWidget(btn_key)

        btn_copy = QPushButton("Copy every target")
        btn_copy.setToolTip(
            "Key every target, then duplicate the base mesh at each frame to extract\n"
            "each target shape as a mesh (visibility off), grouped under <node>_targets.")
        btn_copy.clicked.connect(self.on_copy_every_target)
        layout.addWidget(btn_copy)

        # --- Copy every frame (구간 베이크) ---------------------------------
        # 정해진 [Start, End] 구간을 1프레임마다 베이스 메시를 복제(visibility off).
        # 구간 입력 UI 는 A00110 Follow 탭의 Start/End + Get Current 패턴을 따른다.
        validator = QIntValidator(-1000000, 1000000, self)
        t_min = int(cmds.playbackOptions(query=True, minTime=True))
        t_max = int(cmds.playbackOptions(query=True, maxTime=True))

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Start"))
        self.le_copy_start = QLineEdit(str(t_min))
        self.le_copy_start.setValidator(validator)
        range_row.addWidget(self.le_copy_start)
        btn_get_start = QPushButton("Get Current")
        btn_get_start.clicked.connect(lambda: self._set_current_frame(self.le_copy_start))
        range_row.addWidget(btn_get_start)
        range_row.addWidget(QLabel("End"))
        self.le_copy_end = QLineEdit(str(t_max))
        self.le_copy_end.setValidator(validator)
        range_row.addWidget(self.le_copy_end)
        btn_get_end = QPushButton("Get Current")
        btn_get_end.clicked.connect(lambda: self._set_current_frame(self.le_copy_end))
        range_row.addWidget(btn_get_end)
        layout.addLayout(range_row)

        btn_copy_frame = QPushButton("Copy every frame")
        btn_copy_frame.setToolTip(
            "Duplicate the SELECTED mesh(es) in the scene at every frame in\n"
            "[Start, End] (visibility off), grouped under <mesh>_frames.")
        btn_copy_frame.clicked.connect(self.on_copy_every_frame)
        layout.addWidget(btn_copy_frame)

        layout.addStretch(1)
        return tab

    # ==================================================
    # Tab 3 : Base Shape
    # ==================================================

    def _build_base_shape_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # blendShape 노드 지정 행
        node_row = QHBoxLayout()
        lbl = QLabel("BlendShape Node")
        lbl.setMinimumWidth(110)
        node_row.addWidget(lbl)
        self.le_bs_node = QLineEdit()
        self.le_bs_node.setPlaceholderText("Pick a blendShape node or a mesh, then <- Set")
        node_row.addWidget(self.le_bs_node)
        btn_set = QPushButton("<- Set")
        btn_set.setToolTip("Set the blendShape from the current selection (node or mesh).")
        btn_set.clicked.connect(self.on_set_bs_node)
        node_row.addWidget(btn_set)
        layout.addLayout(node_row)

        # List Targets 버튼
        btn_list = QPushButton("List Targets")
        btn_list.setToolTip("Populate the list below with this blendShape's targets.")
        btn_list.clicked.connect(self.on_list_targets)
        layout.addWidget(btn_list)

        # 타겟 리스트 (씬 오브젝트가 아니므로 일반 QListWidget)
        header = QHBoxLayout()
        lbl_t = QLabel("Targets")
        f = lbl_t.font()
        f.setBold(True)
        lbl_t.setFont(f)
        header.addWidget(lbl_t)
        header.addStretch(1)
        self.lbl_tgt_number = QLabel("Number: 0")
        header.addWidget(self.lbl_tgt_number)
        layout.addLayout(header)

        self.lw_targets = QListWidget()
        self.lw_targets.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_targets.setMinimumHeight(220)
        layout.addWidget(self.lw_targets)

        # 전체 선택 / 해제
        sel_row = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_all.clicked.connect(self.lw_targets.selectAll)
        btn_none = QPushButton("Clear Selection")
        btn_none.clicked.connect(self.lw_targets.clearSelection)
        sel_row.addWidget(btn_all)
        sel_row.addWidget(btn_none)
        layout.addLayout(sel_row)

        # 값 입력 행
        val_row = QHBoxLayout()
        lbl_v = QLabel("Value")
        lbl_v.setMinimumWidth(110)
        val_row.addWidget(lbl_v)
        self.dsb_value = QDoubleSpinBox()
        self.dsb_value.setDecimals(3)
        self.dsb_value.setRange(-10.0, 10.0)
        self.dsb_value.setSingleStep(0.1)
        self.dsb_value.setValue(0.5)
        self.dsb_value.setToolTip(
            "The shape currently seen at this weight value becomes the new weight=1.0 shape.\n"
            "Internally the target deltas are scaled by this factor (must be non-zero).")
        val_row.addWidget(self.dsb_value)
        val_row.addStretch(1)
        layout.addLayout(val_row)

        # 설명
        info = QLabel(
            "Make the shape at <Value> become the default (weight 1.0) shape\n"
            "for the selected targets. e.g. Value 0.5 halves the target; 1.3 exaggerates it.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Apply
        btn_apply = QPushButton("Apply  (Value -> 1.0)")
        btn_apply.setMinimumHeight(36)
        btn_apply.clicked.connect(self.on_apply_base_shape)
        layout.addWidget(btn_apply)

        layout.addStretch(1)
        return tab

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def log(self, text):
        self.te_log.append(text)

    def _update_target_number(self):
        self.lbl_tgt_number.setText("Number: {0}".format(self.lw_targets.count()))

    def _set_current_frame(self, line_edit):
        """Get Current 버튼: 현재 Maya 프레임으로 해당 Start/End LineEdit 을 갱신."""
        line_edit.setText(str(int(round(cmds.currentTime(query=True)))))

    # --------------------------------------------------
    # Handlers : Edit BS
    # --------------------------------------------------

    def on_key_every_target(self):
        nodes = self.tsl_bs_nodes.get_all_items()
        if not nodes:
            self.log("[Warning] Add blendShape nodes to the list first.")
            return
        _n, msg = EditBSManager.key_every_target(nodes)
        self.log(msg)

    def on_copy_every_target(self):
        nodes = self.tsl_bs_nodes.get_all_items()
        if not nodes:
            self.log("[Warning] Add blendShape nodes to the list first.")
            return
        _n, msg = EditBSManager.copy_every_target(nodes)
        self.log(msg)

    def on_copy_every_frame(self):
        meshes = cmds.ls(selection=True, long=False) or []
        if not meshes:
            self.log("[Warning] Select mesh(es) in the scene first.")
            return

        s_txt = self.le_copy_start.text().strip()
        e_txt = self.le_copy_end.text().strip()
        if s_txt == "" or e_txt == "":
            self.log("[Warning] Enter Start / End.")
            return

        start, end = int(s_txt), int(e_txt)
        if start > end:
            self.log("[Warning] Start ({0}) is greater than End ({1}).".format(start, end))
            return

        _n, msg = EditBSManager.copy_every_frame(meshes, start, end)
        self.log(msg)

    # --------------------------------------------------
    # Handlers : Base Shape
    # --------------------------------------------------

    def on_set_bs_node(self):
        found = bsu.find_blendshapes_from_selection()
        if not found:
            self.log("[Warning] Select a blendShape node or a mesh driven by one.")
            return
        self.le_bs_node.setText(found[0])
        if len(found) > 1:
            self.log("[Info] {0} blendShapes found; using '{1}'.".format(
                len(found), found[0]))
        # 지정과 동시에 타겟도 채워준다
        self.on_list_targets()

    def on_list_targets(self):
        bs_node = self.le_bs_node.text().strip()
        if not bsu.is_blendshape(bs_node):
            self.log("[Warning] '{0}' is not a valid blendShape node.".format(bs_node))
            return
        targets = BaseShapeManager.list_targets(bs_node)
        self.lw_targets.clear()
        self.lw_targets.addItems(targets)
        self._update_target_number()
        self.log("[List Targets] '{0}' : {1} target(s).".format(bs_node, len(targets)))

    def on_apply_base_shape(self):
        bs_node = self.le_bs_node.text().strip()
        if not bsu.is_blendshape(bs_node):
            self.log("[Warning] '{0}' is not a valid blendShape node.".format(bs_node))
            return

        target_names = [item.text() for item in self.lw_targets.selectedItems()]
        if not target_names:
            self.log("[Warning] Select target(s) in the list first.")
            return

        value = self.dsb_value.value()
        _done, msg = BaseShapeManager.apply_value_as_default(bs_node, target_names, value)
        self.log(msg)

    # --------------------------------------------------
    # Show / Hide / Close
    # --------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._update_se_timer()

    def hideEvent(self, event):
        # 본 창이 가려져도 확장 창이 떠 있으면 타겟은 보이므로 폴링을 이어 간다.
        super().hideEvent(event)
        self._update_se_timer()

    def closeEvent(self, event):
        # 확장 창을 먼저 닫아 스크롤 영역을 탭으로 되돌린다(고아 창이 남지 않게).
        if self._se_window is not None:
            self._se_window.close()
        self._se_sync_timer.stop()
        # 편집 모드를 켠 채 창을 닫으면 씬이 조용히 sculpt 상태로 남는다.
        # 닫을 때 해제해 편집 결과를 타겟에 확정시킨다(Maya 의 Edit off 와 동일).
        try:
            ShapeEditorManager.exit_all_edits()
        except Exception:
            pass
        super().closeEvent(event)

    # --------------------------------------------------
    # About
    # --------------------------------------------------

    def show_about(self, *args):
        QMessageBox.information(
            self,
            "About",
            f"BS Tool v{VERSION}\n"
            f"Written by Ji Hun Park.\nUpdate date: {LAST_UPDATE}",
        )
