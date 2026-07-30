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
    """라벨 + 슬라이더 + 스핀박스가 묶여 움직이는 실수 파라미터 한 줄."""

    valueChanged = Signal(float)

    def __init__(self, label, minimum, maximum, value, decimals=3,
                 step=0.01, tooltip="", parent=None):
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


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)

        self.win_title = "Secondary Motion v{0}".format(VERSION)
        self.resize(400, 780)

        self.session = bake_mgr.SecondaryMotionSession(log=self.log)
        self._dirty = True          # 캐시 무효 — 다음 프리뷰에서 다시 샘플링

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
            "Stiffness", 0.0, 1.0, 0.35,
            tooltip="How strongly each node is pulled back to its original (FK) place.\n"
                    "Higher = follows the parent more closely.")
        self.sr_damp = _SliderRow(
            "Damping", 0.0, 1.0, 0.12,
            tooltip="Velocity damping. Higher = settles faster, less wobble.")
        self.sr_falloff = _SliderRow(
            "Falloff", 0.0, 1.0, 0.5,
            tooltip="Root-to-tip stiffness falloff - THE inertia dial.\n"
                    "0 = every node equally stiff. 1 = the tip barely follows,\n"
                    "so nodes further from the parent lag behind more.")
        self.sr_world = _SliderRow(
            "World Damp", 0.0, 1.0, 0.0,
            tooltip="Pulls the result back toward the original pose in world space.")
        self.sr_blend = _SliderRow(
            "Blend", 0.0, 1.0, 1.0,
            tooltip="Overall amount. 0 = identical to the original animation.")
        for w in (self.sr_stiff, self.sr_damp, self.sr_falloff,
                  self.sr_world, self.sr_blend):
            w.valueChanged.connect(self._schedule)
            pl.addWidget(w)

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

    def _params(self):
        return chain_solver.SolverParams(
            stiffness=self.sr_stiff.value(),
            damping=self.sr_damp.value(),
            world_damping=self.sr_world.value(),
            falloff=self.sr_falloff.value(),
            gravity=tuple(sb.value() for sb in self.sb_grav),
            limit_angle=self.sb_limit.value(),
            blend=self.sr_blend.value(),
            substeps=self.sb_sub.value())

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

    def _ensure_cache(self):
        """필요하면 씬을 다시 샘플링한다. 성공 여부 반환."""
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
                dummy_tip=self.chk_tip.isChecked())
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

    def on_reset(self):
        self.chk_preview.blockSignals(True)
        self.chk_preview.setChecked(False)
        self.chk_preview.blockSignals(False)
        if self.session.clear_preview():
            self.log("Preview layer removed.")
        else:
            self.log("No preview layer to remove.")

    def on_apply(self):
        if not self._ensure_cache():
            return

        output = self._output()
        params = self._params()

        try:
            with undo_chunk():
                if not self.session._last_writes:
                    self.session.solve(params)
                count, msg = self.session.apply(params, output)
        except Exception as e:
            self.log("Apply failed: {0}".format(e), warn=True)
            return

        self.chk_preview.blockSignals(True)
        self.chk_preview.setChecked(False)
        self.chk_preview.blockSignals(False)
        self._dirty = True
        self.log(msg, warn=(count == 0))

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
        super(MainWindow, self).closeEvent(event)
