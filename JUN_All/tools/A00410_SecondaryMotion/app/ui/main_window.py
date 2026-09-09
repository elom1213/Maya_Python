# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-30
# A00410_SecondaryMotion - Qt UI
#
# FK 로 애니메이션된 컨트롤러/조인트 체인에 KawaiiPhysics 식 관성(2차 모션)을 얹어
# 키 애니메이션으로 굽는다. 파라미터를 만지면 구간 전체를 다시 풀어(≈13ms) 프리뷰
# override 레이어에 통째로 다시 기록하므로, 재생은 그냥 커브 재생이라 실시간이다.

from Framework.qt.qt import *
from Framework.qt.maya_window import maya_main_window
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_timeRange_qt
from Framework.qt import JUN_mod_progress_qt
from Framework.qt import JUN_mod_falloffCurve_qt
from Framework.core import falloff_curve

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00410_SecondaryMotion.app.config.version import VERSION, LAST_UPDATE
from tools.A00410_SecondaryMotion.app.core import bake_manager as bake_mgr
from tools.A00410_SecondaryMotion.app.core import chain_solver
from tools.A00410_SecondaryMotion.app.core import outputs
from tools.A00410_SecondaryMotion.app.core import scene_sampler


WINDOW_OBJECT_NAME = "JUN_A00410_SecondaryMotion_window"

_WARN_COLOR = "#ffb454"

# 프리뷰 재계산 디바운스(ms). 슬라이더를 드래그하는 동안 계산을 묶는다.
_DEBOUNCE_MS = 40

# 커브를 붙일 파라미터 — (키, 슬라이더 속성명, 팝업 제목, 설명).
# 키는 SolverParams 의 인자 이름과 맞춰 둔다(코드 두 군데가 어긋날 여지를 없앤다).
CURVE_PARAMS = (
    ("stiffness_curve", "sr_stiff", "Stiffness curve",
     "X = chain root -> tip.   Y multiplies Stiffness at that point.\n"
     "Example: left 1.0, right 0.1 - stiff at the root, loose towards the tip."),
    ("damping_curve", "sr_damp", "Damping curve",
     "X = chain root -> tip.   Y multiplies Damping at that point.\n"
     "Lower Y = that part of the chain keeps wobbling longer."),
    ("world_curve", "sr_world", "World Damp curve",
     "X = chain root -> tip.   Y multiplies World Damp at that point.\n"
     "Higher Y = that part is pulled back to the original pose more."),
)

# Apply 진행률 팝업의 단계 가중치(비율). 실측 비용에 맞춘 값이다 —
# 샘플링은 노드 x 프레임 만큼 `getAttr -time`, Bake Keys 는 노드 x 프레임 만큼
# `setKeyframe` 이라 기록이 압도적으로 무겁고, 레이어 승격은 사실상 즉시 끝난다.
_W_SAMPLE = 30
_W_SOLVE = 5
_W_WRITE_KEYS = 65        # Bake Keys — 노드 x 프레임 setKeyframe
_W_WRITE_LAYER = 40       # 레이어 커브 생성 + 값 기록
_W_WRITE_PROMOTE = 5      # 프리뷰 레이어 이름만 바꾸는 경로

# coral_dark 테마에서 홈이 배경에 묻히지 않도록 직접 그린다(A00290/A00380 과 같은 접근).
SLIDER_STYLE = """
QSlider::groove:horizontal {
    height: 4px; background: #2b2b2b; border: 1px solid #1e1e1e; border-radius: 2px;
}
QSlider::sub-page:horizontal {
    height: 4px; background: #d08778; border: 1px solid #1e1e1e; border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 12px; margin: -5px 0; border-radius: 3px;
    background: #cfcfcf; border: 1px solid #1e1e1e;
}
QSlider::handle:horizontal:hover { background: #ffffff; }
"""


class _SliderRow(QWidget):
    """라벨 + 슬라이더 + 스핀박스가 묶여 움직이는 실수 파라미터 한 줄.

    `graph=True` 면 오른쪽에 `Graph` 버튼이 붙는다 — 체인 위치별 **배수 커브** 팝업을
    여는 버튼이다(`graphClicked` 시그널). 커브가 평평하지 않으면 버튼에 `*` 를 붙여
    **지금 이 값에 커브가 걸려 있다**는 것을 한눈에 보이게 한다.
    """

    valueChanged = Signal(float)
    graphClicked = Signal()

    def __init__(self, label, minimum, maximum, value, decimals=3,
                 step=0.01, tooltip="", graph=False, parent=None):
        super(_SliderRow, self).__init__(parent)
        self._min = float(minimum)
        self._max = float(maximum)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label)
        lbl.setMinimumWidth(88)
        row.addWidget(lbl)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setStyleSheet(SLIDER_STYLE)
        row.addWidget(self.slider, 1)

        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(decimals)
        self.spin.setRange(self._min, self._max)
        self.spin.setSingleStep(step)
        self.spin.setMaximumWidth(78)
        row.addWidget(self.spin)

        self.btn_graph = None
        if graph:
            self.btn_graph = QPushButton("Graph")
            self.btn_graph.setMaximumWidth(62)
            self.btn_graph.setToolTip(
                "Shape this value along the chain with a curve.\n"
                "X = chain root -> tip, Y multiplies the value above.")
            self.btn_graph.clicked.connect(
                lambda _checked=False: self.graphClicked.emit())
            row.addWidget(self.btn_graph)

        if tooltip:
            self.setToolTip(tooltip)
            lbl.setToolTip(tooltip)

        self.spin.setValue(float(value))
        self._sync_slider(float(value))

        self.slider.valueChanged.connect(self._on_slider)
        self.spin.valueChanged.connect(self._on_spin)

    def _sync_slider(self, v):
        span = (self._max - self._min) or 1.0
        pos = int(round((v - self._min) / span * 1000.0))
        self.slider.blockSignals(True)
        self.slider.setValue(max(0, min(1000, pos)))
        self.slider.blockSignals(False)

    def _on_slider(self, pos):
        v = self._min + (self._max - self._min) * (pos / 1000.0)
        self.spin.blockSignals(True)
        self.spin.setValue(v)
        self.spin.blockSignals(False)
        self.valueChanged.emit(v)

    def _on_spin(self, v):
        self._sync_slider(v)
        self.valueChanged.emit(v)

    def value(self):
        return self.spin.value()

    def mark_graph(self, active):
        """커브가 걸려 있음을 버튼에 표시한다(평평한 1.0 이면 표시 없음)."""
        if self.btn_graph is None:
            return
        self.btn_graph.setText("Graph *" if active else "Graph")


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Secondary Motion v{0}".format(VERSION)
        self.resize(400, 780)

        self.session = bake_mgr.SecondaryMotionSession(log=self.log)
        self._dirty = True          # 캐시 무효 — 다음 프리뷰에서 다시 샘플링
        # Loop 를 켠 직후 프리뷰 한 번만 진단을 남기기 위한 일회성 플래그.
        self._loop_report_pending = False
        # 파라미터 커브 팝업(키 -> 다이얼로그). 처음 누를 때 만든다.
        self._curve_dialogs = {}

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._refresh_preview)

        self.build_ui()

    # ==============================================================
    # UI
    # ==============================================================

    def build_ui(self):
        self.setWindowTitle(self.win_title)
        self.setWindowFlags(Qt.Window)

        root = QVBoxLayout(self)

        self.menu_bar = QMenuBar()
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.setMenuBar(self.menu_bar)

        # ---- 체인 리스트. list 모드에서는 리스트 순서가 루트→팁 순서다.
        self.tsl = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Chain", select_label="Select Chain",
            list_min_height=130, log_callback=self.log)
        self.tsl.list_widget.model().rowsInserted.connect(self._invalidate)
        self.tsl.list_widget.model().rowsRemoved.connect(self._invalidate)
        root.addWidget(self.tsl, 1)

        # ---- 대상 해석 모드 / 대상 타입
        opt_row = QHBoxLayout()

        mode_box = QGroupBox("Mode")
        mode_lay = QVBoxLayout(mode_box)
        self.rb_chain = QRadioButton("Bone Chain")
        self.rb_chain.setChecked(True)
        self.rb_chain.setToolTip(
            "The listed nodes ARE one chain, in list order (root first).\n"
            "Tip: turn on the list's 'Order' checkbox to keep your pick order.")
        self.rb_root = QRadioButton("Bone Root")
        self.rb_root.setToolTip(
            "Each listed node is the TOP PARENT of its own chain: the chain is\n"
            "built by walking that node's descendants, so you can do many chains\n"
            "at once. Branches become separate chains.\n"
            "Controller target: offset/zero groups are walked THROUGH, not keyed -\n"
            "only shape-bearing nodes (the controls) become chain nodes.")
        mode_lay.addWidget(self.rb_chain)
        mode_lay.addWidget(self.rb_root)
        opt_row.addWidget(mode_box)

        tgt_box = QGroupBox("Target")
        tgt_lay = QVBoxLayout(tgt_box)
        self.rb_ctrl = QRadioButton("Controller")
        self.rb_ctrl.setChecked(True)
        self.rb_ctrl.setToolTip(
            "FK controllers (any transform). Hierarchy walk follows transforms.")
        self.rb_joint = QRadioButton("Joint (direct)")
        self.rb_joint.setToolTip(
            "Write straight onto joints. Hierarchy walk is limited to joints and\n"
            "jointOrient is taken out of the local rotation (local = R * JO).")
        tgt_lay.addWidget(self.rb_ctrl)
        tgt_lay.addWidget(self.rb_joint)
        opt_row.addWidget(tgt_box)

        root.addLayout(opt_row)

        for rb in (self.rb_chain, self.rb_root, self.rb_ctrl, self.rb_joint):
            rb.toggled.connect(self._invalidate)

        # ---- 구간
        t0 = int(cmds.playbackOptions(query=True, minTime=True))
        t1 = int(cmds.playbackOptions(query=True, maxTime=True))
        self.range = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=t0, end_value=t1, log_callback=self.log)
        self.range.changed.connect(self._invalidate)
        root.addWidget(self.range)

        # ---- 물리 파라미터
        phys = QGroupBox("Physics")
        pl = QVBoxLayout(phys)

        self.sr_stiff = _SliderRow(
            "Stiffness", 0.0, 1.0, 0.35, graph=True,
            tooltip="How strongly each node is pulled back to its original (FK) place.\n"
                    "Higher = follows the parent more closely.\n"
                    "'Graph' shapes this value along the chain (root -> tip).")
        self.sr_damp = _SliderRow(
            "Damping", 0.0, 1.0, 0.12, graph=True,
            tooltip="Velocity damping. Higher = settles faster, less wobble.\n"
                    "'Graph' shapes this value along the chain (root -> tip).")
        self.sr_falloff = _SliderRow(
            "Falloff", 0.0, 1.0, 0.5,
            tooltip="Root-to-tip stiffness falloff - THE inertia dial.\n"
                    "0 = every node equally stiff. 1 = the tip barely follows,\n"
                    "so nodes further from the parent lag behind more.")
        self.sr_world = _SliderRow(
            "World Damp", 0.0, 1.0, 0.0, graph=True,
            tooltip="Pulls the result back toward the original pose in world space.\n"
                    "'Graph' shapes this value along the chain (root -> tip).")
        self.sr_blend = _SliderRow(
            "Blend", 0.0, 1.0, 1.0,
            tooltip="Overall amount. 0 = identical to the original animation.")
        for w in (self.sr_stiff, self.sr_damp, self.sr_falloff,
                  self.sr_world, self.sr_blend):
            w.valueChanged.connect(self._schedule)
            pl.addWidget(w)

        # Graph 버튼 -> 파라미터별 커브 팝업(비모달, 한 번 만들면 값이 남는다).
        for key, attr, title, info in CURVE_PARAMS:
            row = getattr(self, attr)
            row.graphClicked.connect(
                lambda _checked=False, k=key: self._open_curve(k))

        form = QFormLayout()

        self.sb_limit = QDoubleSpinBox()
        self.sb_limit.setRange(0.0, 180.0)
        self.sb_limit.setValue(45.0)
        self.sb_limit.setToolTip(
            "Max angle (deg) a bone may swing away from its original direction.\n"
            "0 = no limit.")
        self.sb_limit.valueChanged.connect(self._schedule)
        form.addRow("Limit Angle", self.sb_limit)

        grav_row = QHBoxLayout()
        self.sb_grav = []
        for axis, default in (("X", 0.0), ("Y", 0.0), ("Z", 0.0)):
            sb = QDoubleSpinBox()
            sb.setDecimals(4)
            sb.setRange(-1000.0, 1000.0)
            sb.setSingleStep(0.01)
            sb.setValue(default)
            sb.setToolTip("Constant world force (units per frame^2).")
            sb.valueChanged.connect(self._schedule)
            grav_row.addWidget(QLabel(axis))
            grav_row.addWidget(sb)
            self.sb_grav.append(sb)
        form.addRow("Gravity", grav_row)

        self.sb_sub = QSpinBox()
        self.sb_sub.setRange(1, 16)
        self.sb_sub.setValue(1)
        self.sb_sub.setToolTip(
            "Sub-steps per frame. Raise it if fast motion makes the chain unstable.")
        self.sb_sub.valueChanged.connect(self._schedule)
        form.addRow("Substeps", self.sb_sub)

        pl.addLayout(form)

        # 팁도 회전시킬지 — 체인 끝에 가상 뼈를 하나 붙여 마지막 노드에도 키를 만든다.
        self.chk_tip = QCheckBox("Rotate last node (dummy bone)")
        self.chk_tip.setChecked(True)
        self.chk_tip.setToolTip(
            "The last node has no child, so it has no direction of its own.\n"
            "On (default): extend the last bone once more as a virtual point so the\n"
            "last controller/joint rotates and gets keys too, like KawaiiPhysics'\n"
            "dummy bone. Off: the last node keeps its original rotation.")
        self.chk_tip.toggled.connect(self._invalidate)
        pl.addWidget(self.chk_tip)

        # 구간을 사이클로 보고 푼다 — 샘플링은 그대로라 다시 풀기만 하면 된다.
        self.chk_loop = QCheckBox("Loop (cycle the range)")
        self.chk_loop.setToolTip(
            "Make the result loop: the pose at the END of the range continues\n"
            "seamlessly into its START.\n"
            "The range is solved as a cycle - it is pre-rolled a few times so the\n"
            "swing has settled into a steady state, and only the last pass is kept.\n"
            "Needs the source animation itself to cycle (first frame pose == last).\n"
            "The first frame no longer starts at rest, so its rotation will differ\n"
            "from the original - that is what makes it loop.")
        self.chk_loop.toggled.connect(self._on_loop_toggled)
        pl.addWidget(self.chk_loop)

        root.addWidget(phys)

        # ---- 프리뷰
        prev_row = QHBoxLayout()
        self.chk_preview = QCheckBox("Live Preview")
        self.chk_preview.setToolTip(
            "Solve the whole range and write it into a temporary override anim\n"
            "layer ('{0}'). Playback stays real-time because it is just curves.".format(
                bake_mgr.PREVIEW_LAYER))
        self.chk_preview.toggled.connect(self._on_preview_toggled)
        prev_row.addWidget(self.chk_preview)
        prev_row.addStretch(1)
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setToolTip("Remove the preview layer and go back to the original.")
        self.btn_reset.clicked.connect(self.on_reset)
        prev_row.addWidget(self.btn_reset)
        root.addLayout(prev_row)

        # ---- 출력. 라디오는 outputs 레지스트리에서 만든다 —
        #      나중에 A00390 처럼 라이브 노드 출력이 추가되면 여기 손대지 않아도 나타난다.
        out_box = QGroupBox("Output")
        out_lay = QHBoxLayout(out_box)
        self.out_group = QButtonGroup(self)
        self._out_buttons = {}
        for i, spec in enumerate(outputs.implemented_specs()):
            rb = QRadioButton(spec.label)
            if spec.tooltip:
                rb.setToolTip(spec.tooltip)
            rb.setChecked(i == 0)
            self.out_group.addButton(rb)
            out_lay.addWidget(rb)
            self._out_buttons[rb] = spec.id
        out_lay.addStretch(1)
        root.addWidget(out_box)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setMinimumHeight(38)
        self.btn_apply.clicked.connect(self.on_apply)
        root.addWidget(self.btn_apply)

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(110)
        root.addWidget(self.te_log)

        self.log("Secondary Motion v{0} ({1}) ready. List a chain (root first), "
                 "set the range, then turn on Live Preview.".format(VERSION, LAST_UPDATE))

    # ==============================================================
    # state
    # ==============================================================

    def _invalidate(self, *args):
        """체인/모드/구간이 바뀌면 샘플 캐시를 버린다(다음 프리뷰에서 다시 샘플링)."""
        self._dirty = True
        if self.chk_preview.isChecked():
            self._schedule()

    def _schedule(self, *args):
        """디바운스 — 조작이 멎으면 한 번만 다시 푼다."""
        if self.chk_preview.isChecked():
            self._timer.start(_DEBOUNCE_MS)

    def _open_curve(self, key):
        """파라미터 커브 팝업을 띄운다(없으면 만들고, 있으면 그 창을 앞으로)."""
        dlg = self._curve_dialogs.get(key)
        if dlg is None:
            title, info = "Curve", ""
            for k, _attr, t, i in CURVE_PARAMS:
                if k == key:
                    title, info = t, i
                    break
            dlg = JUN_mod_falloffCurve_qt.JUN_mod_falloffCurveDialog_qt_v01(
                self, title="Secondary Motion - {0}".format(title),
                # 기본은 **평평한 1.0** — 곱해도 아무것도 바뀌지 않는 상태에서 시작한다.
                points=falloff_curve.FLAT_POINTS, interp=falloff_curve.FLAT_INTERP,
                reset_points=falloff_curve.FLAT_POINTS,
                reset_interp=falloff_curve.FLAT_INTERP,
                info=info,
                tooltip="Drag a point to reshape, double-click to add, "
                        "right-click to remove.\n"
                        "The first and last points only move vertically.")
            dlg.changed.connect(lambda k=key: self._on_curve_changed(k))
            self._curve_dialogs[key] = dlg
        dlg.popup()

    def _on_curve_changed(self, key):
        for k, attr, _title, _info in CURVE_PARAMS:
            if k == key:
                dlg = self._curve_dialogs.get(key)
                getattr(self, attr).mark_graph(
                    dlg is not None and not dlg.is_flat())
                break
        self._schedule()

    def _curve_spec(self, key):
        """솔버에 넘길 `(points, interp, tangents)`. 팝업이 없거나 평평한 1.0 이면 None.

        평평하면 None 을 주는 것이 중요하다 — 커브 평가를 아예 건너뛰어 **예전 경로와
        완전히 같은 계산**이 되고, 로그/디버깅에서도 '커브 없음' 이 분명해진다.
        """
        dlg = self._curve_dialogs.get(key)
        if dlg is None or dlg.is_flat():
            return None
        return (dlg.points(), dlg.interpolation(), dlg.tangents())

    def _params(self):
        return chain_solver.SolverParams(
            stiffness=self.sr_stiff.value(),
            damping=self.sr_damp.value(),
            world_damping=self.sr_world.value(),
            falloff=self.sr_falloff.value(),
            gravity=tuple(sb.value() for sb in self.sb_grav),
            limit_angle=self.sb_limit.value(),
            blend=self.sr_blend.value(),
            substeps=self.sb_sub.value(),
            loop=self.chk_loop.isChecked(),
            stiffness_curve=self._curve_spec("stiffness_curve"),
            damping_curve=self._curve_spec("damping_curve"),
            world_curve=self._curve_spec("world_curve"))

    def _mode(self):
        return (scene_sampler.MODE_ROOT if self.rb_root.isChecked()
                else scene_sampler.MODE_CHAIN)

    def _output(self):
        """선택된 출력 id. 라디오는 outputs 레지스트리에서 생성된다."""
        for rb, oid in self._out_buttons.items():
            if rb.isChecked():
                return oid
        return outputs.default_id()

    def _target(self):
        return (scene_sampler.TARGET_JOINT if self.rb_joint.isChecked()
                else scene_sampler.TARGET_CTRL)

    def _ensure_cache(self, progress=None):
        """필요하면 씬을 다시 샘플링한다. 성공 여부 반환.

        progress 를 주면(Apply 의 진행률 팝업) 샘플링 진행이 그쪽으로 보고된다.
        프리뷰 경로는 그냥 None 으로 둔다.
        """
        if not self._dirty and self.session.has_cache():
            return True

        nodes = self.tsl.get_all_nodes()
        if not nodes:
            self.log("Chain list is empty. Select the chain and click "
                     "'Select Chain'.", warn=True)
            return False

        rng = self.range.values()
        if rng is None:
            self.log("Enter valid Start / End frames.", warn=True)
            return False

        try:
            chains, count, frames = self.session.prepare(
                nodes, self._mode(), self._target(), rng[0], rng[1],
                dummy_tip=self.chk_tip.isChecked(), progress=progress)
        except Exception as e:
            self.log("Prepare failed: {0}".format(e), warn=True)
            return False

        self._dirty = False
        if self.session.missing:
            self.log("Not in the scene: {0}".format(
                ", ".join(self.session.missing)), warn=True)
        if self.session.empty_roots:
            self.log("No chain under: {0} - a root needs at least one child "
                     "(check the Target type).".format(
                         ", ".join(self.session.empty_roots)), warn=True)
        if self.session.branched:
            self.log("Branching under: {0} - split into separate chains; the "
                     "longest one owns the shared nodes.".format(
                         ", ".join(self.session.branched)), warn=True)
        self.log("Sampled {0} chain(s), {1} nodes, {2} frames.".format(
            chains, count, frames))
        return True

    # ==============================================================
    # actions
    # ==============================================================

    def _on_preview_toggled(self, on):
        if on:
            self._refresh_preview()
        else:
            self.session.clear_preview()
            self.log("Preview off - back to the original animation.")

    def _on_loop_toggled(self, on):
        if on:
            rng = self.range.values()
            span = ("frame {0} and frame {1}".format(rng[0], rng[1]) if rng
                    else "the first and last frame")
            self.log("Loop on - the range is solved as a cycle. {0} must hold the "
                     "same pose in the source animation. The first frame no longer "
                     "starts at rest, so its rotation can differ from the "
                     "original.".format(span))
            self._loop_report_pending = True
        else:
            self.log("Loop off - the solve starts at rest on the first frame.")
        self._schedule()

    def _log_loop_report(self):
        """마지막 솔브의 루프 진단을 로그에 남긴다(Loop 가 꺼져 있으면 아무것도 안 한다)."""
        for msg, warn in self.session.loop_report():
            self.log(msg, warn=warn)

    def _refresh_preview(self):
        if not self.chk_preview.isChecked():
            return
        if not self._ensure_cache():
            self.chk_preview.blockSignals(True)
            self.chk_preview.setChecked(False)
            self.chk_preview.blockSignals(False)
            return
        try:
            self.session.update_preview(self._params())
        except Exception as e:
            self.log("Preview failed: {0}".format(e), warn=True)
            return
        # Loop 를 켠 직후 한 번만 — 슬라이더를 만질 때마다 찍으면 로그가 묻힌다.
        if self._loop_report_pending:
            self._loop_report_pending = False
            self._log_loop_report()

    def on_reset(self):
        self.chk_preview.blockSignals(True)
        self.chk_preview.setChecked(False)
        self.chk_preview.blockSignals(False)
        if self.session.clear_preview():
            self.log("Preview layer removed.")
        else:
            self.log("No preview layer to remove.")

    def on_apply(self):
        # 팝업을 띄우기 전에 값싼 검증부터 — 리스트/구간이 비었으면 로그만 남긴다.
        if not self.tsl.get_all_nodes():
            self.log("Chain list is empty. Select the chain and click "
                     "'Select Chain'.", warn=True)
            return
        if self.range.values() is None:
            self.log("Enter valid Start / End frames.", warn=True)
            return

        # 프리뷰가 켜져 있고 디바운스가 아직 안 터졌으면 먼저 반영한다 —
        # 안 그러면 마지막 조작 직후 Apply 를 눌렀을 때 한 단계 전 프리뷰가 승격된다.
        if self.chk_preview.isChecked() and self._timer.isActive():
            self._timer.stop()
            self._refresh_preview()

        output = self._output()
        params = self._params()

        need_sample = self._dirty or not self.session.has_cache()
        promote = (output == outputs.OUTPUT_LAYER and not need_sample
                   and self.session.has_preview())

        phases = []
        if need_sample:
            phases.append(("Sampling scene", _W_SAMPLE))
        phases.append(("Solving chains", _W_SOLVE))
        if output == outputs.OUTPUT_KEYS:
            phases.append(("Baking keys", _W_WRITE_KEYS))
        elif promote:
            phases.append(("Applying anim layer", _W_WRITE_PROMOTE))
        else:
            phases.append(("Writing anim layer", _W_WRITE_LAYER))

        dlg = JUN_mod_progress_qt.JUN_mod_progress_qt_v01(
            self, title="Secondary Motion - Apply",
            message="Starting...", phases=phases)
        dlg.start()
        elapsed = 0.0

        try:
            with undo_chunk():
                if need_sample:
                    dlg.begin_phase()
                    if not self._ensure_cache(progress=dlg.callback()):
                        return

                # 파라미터는 프리뷰 없이도 바뀔 수 있으므로 **항상 다시 푼다**
                # (예전에는 앞서 만든 _last_writes 를 그대로 써서 슬라이더를 만진
                #  뒤에도 옛 값이 구워질 수 있었다). 전 구간 솔브는 수십 ms 다.
                dlg.begin_phase()
                self.session.solve(params, progress=dlg.callback())

                dlg.begin_phase()
                count, msg = self.session.apply(
                    params, output, progress=dlg.callback())
        except Exception as e:
            self.log("Apply failed: {0}".format(e), warn=True)
            return
        finally:
            elapsed = dlg.elapsed()
            dlg.finish()

        self.chk_preview.blockSignals(True)
        self.chk_preview.setChecked(False)
        self.chk_preview.blockSignals(False)
        self._dirty = True
        self._log_loop_report()
        self.log("{0}  ({1:.1f}s)".format(msg, elapsed), warn=(count == 0))

    # ==============================================================
    # log / about
    # ==============================================================

    @staticmethod
    def _esc(text):
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def log(self, text, warn=False):
        if warn:
            self.te_log.append('<span style="color:{0};">{1}</span>'.format(
                _WARN_COLOR, self._esc(text)))
        else:
            self.te_log.append(text)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Secondary Motion\nv{0}  ({1})\n\n"
            "Adds KawaiiPhysics-style inertia (follow-through) to an FK chain\n"
            "and bakes it as keyframes.\n\n"
            "The whole range is re-solved on every parameter change and written\n"
            "into an override anim layer, so playback stays real-time.\n"
            "Falloff is the inertia dial: nodes further from the parent lag more.\n"
            "by Ji Hun Park".format(VERSION, LAST_UPDATE))

    def closeEvent(self, event):
        # 창을 닫으면 임시 프리뷰 레이어는 남기지 않는다.
        try:
            self.session.clear_preview()
        except Exception:
            pass
        # 커브 팝업은 자식 창이라 그대로 두면 툴을 닫아도 떠 있는다.
        for dlg in self._curve_dialogs.values():
            try:
                dlg.close()
            except Exception:
                pass
        super(MainWindow, self).closeEvent(event)
