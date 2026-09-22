# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-22
# A00275_skinTool_V01 - Weights > Smooth 탭 UI
"""
Weights > Smooth - 선택한 버텍스의 스킨 웨이트를 이웃과 평균해 매끄럽게 만드는 탭.

Kangaroo `SkinCluster > Smooth` 이식이고, 옵션 이름과 기본값을 **원본과 1:1** 로 맞췄다.
로직은 전부 `app/core/weight_smooth_manager.py` 에 있다 - 여기서는 위젯 값만 읽어 넘긴다.
main_window.py 가 길어서 Layer · By Weight 탭처럼 위젯 하나로 따로 둔다.

원본과 다르게 둔 것 둘:
  - 원본은 옵션을 SkinCluster 탭 전체가 공유하지만(다른 기능과 같은 칸을 쓴다), 이 탭은
    자기 옵션만 갖는다 - 이 저장소는 "하위 탭 = 기능 하나" 규칙이다.
  - `Use Soft Selection` 체크를 새로 뒀다. 원본은 소프트 셀렉션을 늘 반영하는데, 끄고 싶을
    때가 있다(소프트 셀렉션을 켠 채 다른 작업을 하다가 스무딩이 약하게 먹는 일).

모든 UI 문자열은 영어. (한국어는 주석/독스트링만)
"""

from Framework.qt.qt import *

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00275_skinTool_V01.app.core import weight_smooth_manager as sm_mgr


#: 실수 슬라이더 한 칸 (다른 탭과 같은 값)
FLOAT_SLIDER_STEPS = 1000

#: Iterations 슬라이더가 덮는 범위. 더 큰 값은 스핀박스로 직접 쳐 넣는다.
ITERATION_SLIDER_MAX = 20

_LOCK_ITEMS = (
    ("Ignore locks", sm_mgr.LOCKS_IGNORE,
     "Locked influences are treated like any other."),
    ("Keep locked weights", sm_mgr.LOCKS_KEEP,
     "A locked influence keeps its value on every vertex.\n"
     "The unlocked influences take up the rest."),
    ("Only add to locked", sm_mgr.LOCKS_ONLY_ADD,
     "A locked influence may grow but never shrink."),
    ("Only remove from locked", sm_mgr.LOCKS_ONLY_REMOVE,
     "A locked influence may shrink but never grow."),
)

_BORDER_ITEMS = (
    ("Everything", sm_mgr.BORDER_ALL,
     "Smooth the whole selection, borders included."),
    ("Ignore border edges", sm_mgr.BORDER_IGNORE,
     "Leave the open border of the mesh as it is, fading back in\n"
     "towards the inside (Border Mask Steps says how far)."),
    ("Only border edges", sm_mgr.BORDER_ONLY,
     "Smooth only the strip along the open border of the mesh."),
)


def _leaf(name):
    return name.split("|")[-1]


class SmoothTab(QWidget):
    """Weights > Smooth 탭. 로그는 툴 창의 것을 그대로 쓴다(log_callback)."""

    def __init__(self, log_callback=None, parent=None):
        super(SmoothTab, self).__init__(parent)

        self._log = log_callback or (lambda text: None)
        self._loop_curve = ""
        # 슬라이더 <-> 스핀박스 되먹임 차단 플래그 (_iterations_to_slider 주석 참고)
        self._syncing = False

        self._build_ui()
        self.refresh_selection()

    # ==============================================================
    # UI
    # ==============================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        desc = QLabel(
            "Average the skin weights of the selected vertices with their\n"
            "neighbours. Neighbours outside the selection are read but never\n"
            "changed, so the edge of the selection does not pop.")
        desc.setAlignment(Qt.AlignCenter)
        root.addWidget(desc)

        root.addWidget(self._build_target_group())
        root.addWidget(self._build_options_group())

        row = QHBoxLayout()
        row.addWidget(self._build_locks_group(), 1)
        row.addWidget(self._build_border_group(), 1)
        root.addLayout(row)

        root.addWidget(self._build_loop_group())

        buttons = QHBoxLayout()
        self.btn_smooth = QPushButton("Smooth")
        self.btn_smooth.setMinimumHeight(30)
        self.btn_smooth.setToolTip(
            "Smooth the selected vertices with the options above.\n"
            "One click = one undo step (Ctrl+Z brings the weights back).")
        self.btn_smooth.clicked.connect(self.on_smooth)
        buttons.addWidget(self.btn_smooth, 2)

        self.btn_reset = QPushButton("Reset Options")
        self.btn_reset.setToolTip("Put every option back to its default.")
        self.btn_reset.clicked.connect(self.reset_options)
        buttons.addWidget(self.btn_reset, 1)
        root.addLayout(buttons)

        root.addStretch(1)

    # ---------------- 대상 ----------------

    def _build_target_group(self):
        box = QGroupBox("Target")
        layout = QVBoxLayout(box)

        note = QLabel(
            "Works on the live scene selection - pick vertices (edges and faces\n"
            "work too), or a whole skinned mesh. Several meshes at once are fine.")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)

        row = QHBoxLayout()
        self.lbl_selection = QLabel()
        self.lbl_selection.setWordWrap(True)
        row.addWidget(self.lbl_selection, 1)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setToolTip(
            "Read the scene selection again and list the skinClusters on it.")
        self.btn_refresh.clicked.connect(lambda *_: self.refresh_selection())
        row.addWidget(self.btn_refresh)
        layout.addLayout(row)

        skin_row = QHBoxLayout()
        skin_row.addWidget(QLabel("SkinCluster"))
        self.cb_skin = QComboBox()
        self.cb_skin.setToolTip(
            "Which skinCluster to smooth when the mesh is driven by more than one.\n"
            "'Automatic' uses the first one in the history (what Maya's own tools use).")
        skin_row.addWidget(self.cb_skin, 1)
        layout.addLayout(skin_row)

        return box

    # ---------------- 옵션 ----------------

    def _build_options_group(self):
        box = QGroupBox("Smooth")
        layout = QVBoxLayout(box)

        # Iterations
        self.sb_iterations = QSpinBox()
        self.sb_iterations.setRange(0, 500)
        self.sb_iterations.setValue(4)
        self.sb_iterations.setKeyboardTracking(False)
        self.sl_iterations = QSlider(Qt.Horizontal)
        self.sl_iterations.setRange(0, ITERATION_SLIDER_MAX)
        self.sl_iterations.setValue(4)
        self.sb_iterations.valueChanged.connect(self._iterations_to_slider)
        self.sl_iterations.valueChanged.connect(self._iterations_from_slider)
        layout.addLayout(self._labeled_row(
            "Iterations", self.sl_iterations, self.sb_iterations,
            "How many times the averaging runs. Each pass spreads the weights\n"
            "one edge further, so 4 is a soft blur and 20 is nearly flat."))

        # Blend
        self.sb_blend, self.sl_blend = self._float_pair(1.0)
        layout.addLayout(self._labeled_row(
            "Blend", self.sl_blend, self.sb_blend,
            "How much of the smoothed result is used.\n"
            "1.0 = the smoothed weights, 0.5 = halfway, 0.0 = no change."))

        # Rigid
        self.sb_rigid, self.sl_rigid = self._float_pair(0.0)
        layout.addLayout(self._labeled_row(
            "Rigid", self.sl_rigid, self.sb_rigid,
            "Cuts back the weak neighbour shares (each share is raised to the\n"
            "power 1 + Rigid * 0.25, then re-normalised), so a weak influence\n"
            "bleeds in less and the area stays rigid. Where every share is\n"
            "already equal it changes nothing. 0.0 is a plain average."))

        checks = QHBoxLayout()
        self.cb_keep_one = QCheckBox("Keep Value One")
        self.cb_keep_one.setToolTip(
            "Vertices that are weighted 1.0 to a single influence are left\n"
            "untouched - useful to keep a rigid area (a belt buckle, a bone plate)\n"
            "while its surroundings are smoothed.")
        checks.addWidget(self.cb_keep_one)

        self.cb_soft = QCheckBox("Use Soft Selection")
        self.cb_soft.setChecked(True)
        self.cb_soft.setToolTip(
            "When Maya's soft selection is on, its falloff is used as the amount\n"
            "of smoothing per vertex (the same as Kangaroo does).")
        checks.addWidget(self.cb_soft)
        checks.addStretch(1)
        layout.addLayout(checks)

        return box

    def _build_locks_group(self):
        box = QGroupBox("Joint Locks")
        layout = QVBoxLayout(box)
        self.lock_buttons = QButtonGroup(self)
        for index, (label, value, tip) in enumerate(_LOCK_ITEMS):
            button = QRadioButton(label)
            button.setToolTip(tip)
            if value == sm_mgr.LOCKS_IGNORE:
                button.setChecked(True)
            self.lock_buttons.addButton(button, value)
            layout.addWidget(button)
        layout.addStretch(1)
        return box

    def _build_border_group(self):
        box = QGroupBox("Border Edges")
        layout = QVBoxLayout(box)
        self.border_buttons = QButtonGroup(self)
        for label, value, tip in _BORDER_ITEMS:
            button = QRadioButton(label)
            button.setToolTip(tip)
            if value == sm_mgr.BORDER_ALL:
                button.setChecked(True)
            self.border_buttons.addButton(button, value)
            layout.addWidget(button)

        self.sb_border_steps = QSpinBox()
        self.sb_border_steps.setRange(1, 10)
        self.sb_border_steps.setValue(2)
        self.sb_border_steps.setKeyboardTracking(False)
        self.sb_border_steps.setToolTip(
            "How far the border mask fades into the mesh, in edges.")
        steps = QHBoxLayout()
        steps.addWidget(QLabel("Border Mask Steps"))
        steps.addWidget(self.sb_border_steps)
        steps.addStretch(1)
        layout.addLayout(steps)

        # "Everything" 이면 마스크 칸은 할 일이 없다 (원본도 같은 규칙으로 끈다).
        self.border_buttons.buttonClicked.connect(lambda *_: self._sync_border_steps())
        self._sync_border_steps()

        layout.addStretch(1)
        return box

    def _build_loop_group(self):
        box = QGroupBox("Loop Curve (optional)")
        layout = QVBoxLayout(box)

        note = QLabel(
            "Keep the flow along a line. The vertices closest to the curve stop\n"
            "averaging ALONG the line and only average across it, so a lip or an\n"
            "eyelid loop keeps its corner-to-centre gradient while the rows\n"
            "around it relax.")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)

        row = QHBoxLayout()
        self.le_loop = QLineEdit()
        self.le_loop.setReadOnly(True)
        self.le_loop.setPlaceholderText("No loop curve - smooth every direction")
        row.addWidget(self.le_loop, 1)

        self.btn_loop_set = QPushButton("Set from Selection")
        self.btn_loop_set.setToolTip(
            "Use the selected NURBS curve as the loop. Its CVs pick the mesh\n"
            "vertices closest to them, and those vertices are the line.")
        self.btn_loop_set.clicked.connect(self.on_set_loop_curve)
        row.addWidget(self.btn_loop_set)

        self.btn_loop_clear = QPushButton("Clear")
        self.btn_loop_clear.setToolTip("Forget the curve and smooth every direction.")
        self.btn_loop_clear.clicked.connect(self.on_clear_loop_curve)
        row.addWidget(self.btn_loop_clear)
        layout.addLayout(row)

        return box

    # ---------------- 작은 UI 헬퍼 ----------------

    def _labeled_row(self, label, slider, spin, tooltip):
        row = QHBoxLayout()
        title = QLabel(label)
        title.setMinimumWidth(90)
        title.setToolTip(tooltip)
        slider.setToolTip(tooltip)
        spin.setToolTip(tooltip)
        row.addWidget(title)
        row.addWidget(slider, 1)
        row.addWidget(spin)
        return row

    def _float_pair(self, value):
        """0~1 실수 스핀박스 + 슬라이더 한 쌍 (서로 따라간다)."""
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 1.0)
        spin.setSingleStep(0.05)
        spin.setDecimals(3)
        spin.setValue(value)
        # 타이핑 한 글자마다 값이 튀지 않게 (엔터/포커스 이동에만 반영).
        spin.setKeyboardTracking(False)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, FLOAT_SLIDER_STEPS)
        slider.setValue(int(round(value * FLOAT_SLIDER_STEPS)))

        def to_spin(step):
            new = step / float(FLOAT_SLIDER_STEPS)
            if abs(new - spin.value()) > 1e-9:
                spin.setValue(new)

        def to_slider(new):
            step = int(round(new * FLOAT_SLIDER_STEPS))
            if step != slider.value():
                slider.setValue(step)

        slider.valueChanged.connect(to_spin)
        spin.valueChanged.connect(to_slider)
        return spin, slider

    def _iterations_to_slider(self, value):
        """슬라이더 범위를 넘는 값을 쳐 넣으면 슬라이더는 끝에 둔다.

        ★ 이때 슬라이더의 `valueChanged` 가 다시 스핀박스를 쓰면 **큰 값이 20 으로 되돌아간다**
        (40 을 넣으면 슬라이더가 20 으로 잘리고, 그 20 이 스핀박스로 돌아온다). 그래서 이쪽에서
        슬라이더를 움직이는 동안에는 되먹임을 막는다.
        """
        step = min(ITERATION_SLIDER_MAX, max(0, int(value)))
        if step == self.sl_iterations.value():
            return
        self._syncing = True
        try:
            self.sl_iterations.setValue(step)
        finally:
            self._syncing = False

    def _iterations_from_slider(self, step):
        """슬라이더를 끌었을 때만 스핀박스에 넣는다(위 주석의 되먹임 방지)."""
        if getattr(self, "_syncing", False):
            return
        self.sb_iterations.setValue(int(step))

    def _sync_border_steps(self):
        self.sb_border_steps.setEnabled(
            self.border_buttons.checkedId() != sm_mgr.BORDER_ALL)

    # ==============================================================
    # 값 읽기
    # ==============================================================

    def options(self):
        """지금 화면의 옵션을 코어 인자 dict 로."""
        return {
            "iterations": self.sb_iterations.value(),
            "blend": self.sb_blend.value(),
            "joint_locks": self.lock_buttons.checkedId(),
            "keep_value_one": self.cb_keep_one.isChecked(),
            "border_edges": self.border_buttons.checkedId(),
            "border_mask_steps": self.sb_border_steps.value(),
            "rigid": self.sb_rigid.value(),
            "loop_curve": self._loop_curve or None,
            "skin_cluster": self.skin_cluster(),
            "use_soft_selection": self.cb_soft.isChecked(),
        }

    def skin_cluster(self):
        """콤보에서 고른 skinCluster (Automatic 이면 None)."""
        value = self.cb_skin.currentData()
        return value or None

    def reset_options(self, *args):
        self.sb_iterations.setValue(4)
        self.sb_blend.setValue(1.0)
        self.sb_rigid.setValue(0.0)
        self.cb_keep_one.setChecked(False)
        self.cb_soft.setChecked(True)
        self.lock_buttons.button(sm_mgr.LOCKS_IGNORE).setChecked(True)
        self.border_buttons.button(sm_mgr.BORDER_ALL).setChecked(True)
        self.sb_border_steps.setValue(2)
        self.on_clear_loop_curve()
        self._sync_border_steps()
        self._log("[OK] Smooth options are back to their defaults.")

    # ==============================================================
    # 동작
    # ==============================================================

    def refresh_selection(self, *args):
        """선택 요약과 skinCluster 콤보를 다시 만든다."""
        try:
            targets = sm_mgr.parse_selection(
                use_soft_selection=self.cb_soft.isChecked()
                if hasattr(self, "cb_soft") else True)
        except Exception as exc:                           # noqa: BLE001
            targets = []
            self._log("[FAIL] Reading the selection failed : {0}".format(exc))

        if not targets:
            self.lbl_selection.setText("Selection : nothing skinnable selected.")
        else:
            parts = []
            for target in targets:
                ids = target.get("ids")
                count = "all" if ids is None else str(len(ids))
                soft = " + soft" if target.get("softs") else ""
                parts.append("{0} ({1} vtx{2})".format(
                    _leaf(target["mesh"]), count, soft))
            self.lbl_selection.setText("Selection : " + ", ".join(parts))

        previous = self.cb_skin.currentData()
        self.cb_skin.clear()
        self.cb_skin.addItem("Automatic (first in history)", "")
        for target in targets:
            for skin in sm_mgr.skin_clusters(target["mesh"]):
                if self.cb_skin.findData(skin) == -1:
                    self.cb_skin.addItem(_leaf(skin), skin)
        if previous:
            index = self.cb_skin.findData(previous)
            if index != -1:
                self.cb_skin.setCurrentIndex(index)

        return targets

    def on_set_loop_curve(self, *args):
        curves = cmds.ls(sl=True, l=True) or []
        picked = ""
        for node in curves:
            shapes = cmds.listRelatives(node, s=True, ni=True, f=True) or [node]
            if any(cmds.objExists(s) and cmds.objectType(s) == "nurbsCurve"
                   for s in shapes):
                picked = node
                break
        if not picked:
            self._log("[WARN] Select a NURBS curve to use as the loop curve.")
            return
        self._loop_curve = picked
        self.le_loop.setText(_leaf(picked))
        self._log("[OK] Loop curve : {0}".format(_leaf(picked)))

    def on_clear_loop_curve(self, *args):
        self._loop_curve = ""
        self.le_loop.setText("")

    def on_smooth(self, *args):
        options = self.options()
        if self._loop_curve and not cmds.objExists(self._loop_curve):
            self._log("[WARN] The loop curve {0} is gone from the scene - "
                      "cleared it.".format(_leaf(self._loop_curve)))
            self.on_clear_loop_curve()
            options["loop_curve"] = None

        try:
            with undo_chunk():
                done, messages = sm_mgr.smooth(**options)
        except Exception as exc:                           # noqa: BLE001
            self._log("[FAIL] Smooth failed : {0}".format(exc))
            return

        for message in messages:
            self._log(message)
        if done:
            # 씬 선택은 그대로 둔다(같은 선택에 여러 번 누르는 기능이다).
            self.refresh_selection()
