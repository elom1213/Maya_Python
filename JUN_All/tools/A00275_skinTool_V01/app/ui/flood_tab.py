# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00275_skinTool_V01 - Weights > Flood 탭 UI (v01.40)
"""
Weights > Flood - 고른 조인트(들)에 웨이트를 채운다. Kangaroo `SkinCluster > Flood` 이식.

로직은 전부 `app/core/weight_flood_manager.py` 에 있다 - 여기서는 위젯 값만 읽어 넘긴다.
옵션 이름과 기본값은 원본과 1:1 이다(Smooth Steps 4 · Joint Lines = All children · Border Mask Steps 1).

**같은 이름 조인트** : 조인트 리스트는 담을 때 UUID 를 붙이고, 실행할 때 `get_all_nodes()` 로 **풀패스**를 넘긴다.
원본은 짧은 이름을 넘겨서 씬에 같은 이름 조인트가 있으면 죽는다(이 이식의 핵심 개선, 코어 독스트링 참고).

Engine 선택은 두지 않는다 - Kangaroo 엔진은 바로 그 같은 이름 문제가 있기 때문이다.

모든 UI 문자열은 영어. (한국어는 주석/독스트링만)
"""

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from Framework.core.maya_undo import undo_chunk
from tools.A00275_skinTool_V01.app.core import weight_flood_manager as fl_mgr
from tools.A00275_skinTool_V01.app.ui.move_tab import _LOCK_ITEMS


FLOAT_SLIDER_STEPS = 1000
SMOOTH_SLIDER_MAX = 20
VALUE_MAX_SCALE = 10.0      # Scale All 은 1 보다 큰 배율도 받는다

DEFAULTS = {
    "value": 1.0,
    "operation": fl_mgr.OP_REPLACE_CLOSEST,
    "smooth_steps": 4,
    "blend": 1.0,
    "joint_lines": fl_mgr.JOINT_LINES_ALL_CHILDREN,
    "joint_locks": fl_mgr.LOCKS_IGNORE,
    "border_edges": fl_mgr.BORDER_ALL,
    "border_mask_steps": 1,
    "respect_selection": True,
    "use_soft_selection": True,
    "project_squash": True,
    "island_check": True,
}

_OP_ITEMS = (
    ("Replace Closest", fl_mgr.OP_REPLACE_CLOSEST,
     "Each vertex gets Value on its closest joint (by bone).\nWith one joint, every vertex gets Value on it."),
    ("Add Closest", fl_mgr.OP_ADD_CLOSEST,
     "Like Replace Closest, but Value is added on top of what the joints\nalready have (scaled by what is left)."),
    ("Replace All", fl_mgr.OP_REPLACE_ALL,
     "Every listed joint gets Value / joint count on every vertex."),
    ("Add All", fl_mgr.OP_ADD_ALL,
     "Like Replace All, but added on top of what the joints already have."),
    ("Scale All", fl_mgr.OP_SCALE_ALL,
     "Multiply the weight of every listed joint by Value.\nThe other influences take up the rest."),
    ("Distribute", fl_mgr.OP_DISTRIBUTE,
     "Share the weights of the listed joints among themselves by closest bone\n"
     "(= Move with the same joints in From and To). Value is not used."),
)

_LINE_ITEMS = (
    ("All children", fl_mgr.JOINT_LINES_ALL_CHILDREN,
     "Distance to the bone from each joint to any of its child joints,\n"
     "even children that are not in the list. (Kangaroo Flood default)"),
    ("Children in list", fl_mgr.JOINT_LINES_YES,
     "Distance to the bone from each joint to its child joints - only children\nthat are in the list."),
    ("Points only", fl_mgr.JOINT_LINES_NO,
     "Distance to the joint position itself (no bones)."),
)

_BORDER_ITEMS = (
    ("Everything", fl_mgr.BORDER_ALL, "Flood the whole selection, borders included."),
    ("Ignore border edges", fl_mgr.BORDER_IGNORE,
     "Leave the open border of the mesh as it is, fading back in\n"
     "towards the inside (Border Mask Steps says how far)."),
    ("Only border edges", fl_mgr.BORDER_ONLY, "Flood only the strip along the open border of the mesh."),
)


class FloodTab(QWidget):
    """Weights > Flood 탭. 로그는 툴 창의 것을 그대로 쓴다(log_callback)."""

    def __init__(self, log_callback=None, parent=None):
        super(FloodTab, self).__init__(parent)
        self._log = log_callback or (lambda text: None)
        self._syncing = False
        self._build_ui()
        self._sync_operation()
        self._update_button()

    # ==============================================================
    # UI
    # ==============================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        desc = QLabel(
            "Flood the selected mesh(es) or vertices with the listed joint(s).\n"
            "Like Maya's Flood, but soft selection counts and several joints can be\n"
            "flooded at once (each vertex goes to its closest joint by bone).\n"
            "Joints with the same name are fine. (Kangaroo SkinCluster > Flood, no plugin)")
        desc.setAlignment(Qt.AlignCenter)
        root.addWidget(desc)

        top = QHBoxLayout()
        self.tsl_joints = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Joints", select_label="Select Joints", log_callback=self._log)
        model = self.tsl_joints.list_widget.model()
        model.rowsInserted.connect(self._update_button)
        model.rowsRemoved.connect(self._update_button)
        model.modelReset.connect(self._update_button)
        top.addWidget(self.tsl_joints, 1)
        top.addWidget(self._build_operation_group(), 1)
        root.addLayout(top)

        root.addWidget(self._build_options_group())
        row = QHBoxLayout()
        row.addWidget(self._build_radio_group("Joint Lines", _LINE_ITEMS, "line_buttons",
                                              DEFAULTS["joint_lines"]), 1)
        row.addWidget(self._build_radio_group("Joint Locks", _LOCK_ITEMS, "lock_buttons",
                                              DEFAULTS["joint_locks"]), 1)
        row.addWidget(self._build_border_group(), 1)
        root.addLayout(row)

        buttons = QHBoxLayout()
        self.btn_flood = QPushButton("Flood")
        self.btn_flood.setMinimumHeight(32)
        self.btn_flood.setToolTip(
            "Flood the listed joints on the selected mesh(es) - or only on the selected\n"
            "vertices when Respect selection is on. One click = one undo step.")
        self.btn_flood.clicked.connect(self.on_flood)
        buttons.addWidget(self.btn_flood, 2)
        self.btn_reset = QPushButton("Reset Options")
        self.btn_reset.setToolTip("Put every option back to its default.")
        self.btn_reset.clicked.connect(self.reset_options)
        buttons.addWidget(self.btn_reset, 1)
        root.addLayout(buttons)
        root.addStretch(1)

    def _build_operation_group(self):
        box = QGroupBox("Operation")
        layout = QGridLayout(box)
        self.op_buttons = QButtonGroup(self)
        for index, (label, value, tip) in enumerate(_OP_ITEMS):
            button = QRadioButton(label)
            button.setToolTip(tip)
            button.setChecked(value == DEFAULTS["operation"])
            self.op_buttons.addButton(button, value)
            layout.addWidget(button, index // 2, index % 2)
        layout.setRowStretch(len(_OP_ITEMS) // 2 + 1, 1)
        self.op_buttons.buttonClicked.connect(lambda *_: self._sync_operation())
        return box

    def _build_options_group(self):
        box = QGroupBox("Options")
        layout = QVBoxLayout(box)

        self.sb_value, self.sl_value = self._float_pair(DEFAULTS["value"])
        layout.addLayout(self._labeled_row(
            "Value", self.sl_value, self.sb_value,
            "The weight to flood. 1.0 = the listed joints take everything.\n"
            "For Scale All it is the factor (up to {0:g}).".format(VALUE_MAX_SCALE)))

        self.sb_smooth = QSpinBox()
        self.sb_smooth.setRange(0, 200)
        self.sb_smooth.setValue(DEFAULTS["smooth_steps"])
        self.sb_smooth.setKeyboardTracking(False)
        self.sl_smooth = QSlider(Qt.Horizontal)
        self.sl_smooth.setRange(0, SMOOTH_SLIDER_MAX)
        self.sl_smooth.setValue(DEFAULTS["smooth_steps"])
        self.sb_smooth.valueChanged.connect(self._smooth_to_slider)
        self.sl_smooth.valueChanged.connect(self._smooth_from_slider)
        layout.addLayout(self._labeled_row(
            "Smooth Steps", self.sl_smooth, self.sb_smooth,
            "How many times the seams between the joints are averaged with their neighbours\n"
            "(only neighbours inside the selection). Needs two joints or more.\n"
            "Used by Replace Closest, Add Closest and Distribute."))

        self.sb_blend, self.sl_blend = self._float_pair(DEFAULTS["blend"])
        layout.addLayout(self._labeled_row(
            "Blend", self.sl_blend, self.sb_blend,
            "How much of the flooded result is used. 1.0 = all of it, 0.5 = halfway.\n"
            "(Kangaroo ignores Blend here except for Distribute - this tool uses it everywhere.)"))

        checks = QGridLayout()
        self.cb_respect = QCheckBox("Respect selection")
        self.cb_respect.setToolTip(
            "On: when vertices (edges / faces) are selected, only those vertices change.\n"
            "Off: the whole mesh is used even if components are selected.")
        self.cb_soft = QCheckBox("Use soft selection")
        self.cb_soft.setToolTip("When Maya's soft selection is on, its falloff is the amount flooded per vertex.")
        self.cb_squash = QCheckBox("Project squash joints (skinParent)")
        self.cb_squash.setToolTip(
            "A joint with a 'skinParent' string attribute is measured from the joint it names\n"
            "(Kangaroo rigs). No effect when the attribute is not there.")
        self.cb_island = QCheckBox("Island check")
        self.cb_island.setToolTip("Ask before flooding when the selected vertices are split into several islands.")
        self.cb_respect.toggled.connect(lambda on: self.cb_soft.setEnabled(on))
        checks.addWidget(self.cb_respect, 0, 0)
        checks.addWidget(self.cb_soft, 0, 1)
        checks.addWidget(self.cb_squash, 1, 0)
        checks.addWidget(self.cb_island, 1, 1)
        layout.addLayout(checks)
        self._set_checks_default()
        return box

    def _build_radio_group(self, title, items, attr, default):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        group = QButtonGroup(self)
        for label, value, tip in items:
            button = QRadioButton(label)
            button.setToolTip(tip)
            button.setChecked(value == default)
            group.addButton(button, value)
            layout.addWidget(button)
        layout.addStretch(1)
        setattr(self, attr, group)
        return box

    def _build_border_group(self):
        box = self._build_radio_group("Border Edges", _BORDER_ITEMS, "border_buttons", DEFAULTS["border_edges"])
        self.sb_border_steps = QSpinBox()
        self.sb_border_steps.setRange(0, 10)
        self.sb_border_steps.setValue(DEFAULTS["border_mask_steps"])
        self.sb_border_steps.setKeyboardTracking(False)
        self.sb_border_steps.setToolTip("How far the border mask fades into the mesh, in edges.")
        steps = QHBoxLayout()
        steps.addWidget(QLabel("Border Mask Steps"))
        steps.addWidget(self.sb_border_steps)
        steps.addStretch(1)
        box.layout().insertLayout(box.layout().count() - 1, steps)
        self.border_buttons.buttonClicked.connect(lambda *_: self._sync_border_steps())
        self._sync_border_steps()
        return box

    # ---------------- 작은 UI 헬퍼 (Move 탭과 같은 모양) ----------------

    def _labeled_row(self, label, slider, spin, tooltip):
        row = QHBoxLayout()
        title = QLabel(label)
        title.setMinimumWidth(90)
        for widget in (title, slider, spin):
            widget.setToolTip(tooltip)
        row.addWidget(title)
        row.addWidget(slider, 1)
        row.addWidget(spin)
        return row

    def _float_pair(self, value):
        """슬라이더는 0~1, 스핀은 그 이상도(Scale) - 슬라이더 범위 밖 값은 슬라이더만 끝에 둔다."""
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 1.0)
        spin.setSingleStep(0.05)
        spin.setDecimals(3)
        spin.setValue(value)
        spin.setKeyboardTracking(False)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, FLOAT_SLIDER_STEPS)
        slider.setValue(int(round(min(1.0, value) * FLOAT_SLIDER_STEPS)))
        slider.valueChanged.connect(
            lambda step: spin.setValue(step / float(FLOAT_SLIDER_STEPS))
            if abs(min(1.0, spin.value()) - step / float(FLOAT_SLIDER_STEPS)) > 1e-9 else None)
        spin.valueChanged.connect(
            lambda new: slider.setValue(int(round(min(1.0, new) * FLOAT_SLIDER_STEPS)))
            if int(round(min(1.0, new) * FLOAT_SLIDER_STEPS)) != slider.value() else None)
        return spin, slider

    def _smooth_to_slider(self, value):
        step = min(SMOOTH_SLIDER_MAX, max(0, int(value)))
        if step == self.sl_smooth.value():
            return
        self._syncing = True
        try:
            self.sl_smooth.setValue(step)
        finally:
            self._syncing = False

    def _smooth_from_slider(self, step):
        if not self._syncing:
            self.sb_smooth.setValue(int(step))

    def _sync_border_steps(self):
        self.sb_border_steps.setEnabled(self.border_buttons.checkedId() != fl_mgr.BORDER_ALL)

    def _sync_operation(self):
        """연산에 따라 Value 범위 · Smooth Steps 활성 (원본 UI 의 setControlEnabled 와 같다)."""
        op = self.op_buttons.checkedId()
        self.sb_value.setMaximum(VALUE_MAX_SCALE if op == fl_mgr.OP_SCALE_ALL else 1.0)
        value_on = op != fl_mgr.OP_DISTRIBUTE
        self.sb_value.setEnabled(value_on)
        self.sl_value.setEnabled(value_on)
        smooth_on = op in fl_mgr.SMOOTH_OPS
        self.sb_smooth.setEnabled(smooth_on)
        self.sl_smooth.setEnabled(smooth_on)
        self._update_button()

    def _set_checks_default(self):
        self.cb_respect.setChecked(DEFAULTS["respect_selection"])
        self.cb_soft.setChecked(DEFAULTS["use_soft_selection"])
        self.cb_squash.setChecked(DEFAULTS["project_squash"])
        self.cb_island.setChecked(DEFAULTS["island_check"])
        self.cb_soft.setEnabled(self.cb_respect.isChecked())

    def _update_button(self, *args):
        if not hasattr(self, "btn_flood"):
            return
        n = len(self.tsl_joints.get_all_items())
        self.btn_flood.setText("Flood  {0} joint(s)".format(n) if n else "Flood")
        self.btn_flood.setEnabled(bool(n))

    # ==============================================================
    # 값 읽기
    # ==============================================================

    def options(self):
        return {
            "value": self.sb_value.value(),
            "operation": self.op_buttons.checkedId(),
            "smooth_steps": self.sb_smooth.value(),
            "blend": self.sb_blend.value(),
            "joint_lines": self.line_buttons.checkedId(),
            "joint_locks": self.lock_buttons.checkedId(),
            "border_edges": self.border_buttons.checkedId(),
            "border_mask_steps": self.sb_border_steps.value(),
            "respect_selection": self.cb_respect.isChecked(),
            "use_soft_selection": self.cb_soft.isChecked() and self.cb_respect.isChecked(),
            "project_squash": self.cb_squash.isChecked(),
            "island_check": self.cb_island.isChecked(),
        }

    def joints(self):
        """리스트의 조인트를 **풀패스**로 (UUID 로 푼다 - 같은 이름 · 리네임 · 리페어런트 안전).

        씬에서 사라진 항목은 빠지고, 그 수를 로그에 남긴다.
        """
        texts = self.tsl_joints.get_all_items()
        nodes = self.tsl_joints.get_all_nodes()
        if len(nodes) < len(texts):
            self._log("[WARN] {0} listed joint(s) are no longer in the scene - skipped.".format(
                len(texts) - len(nodes)))
        return nodes

    def reset_options(self, *args):
        self.op_buttons.button(DEFAULTS["operation"]).setChecked(True)
        self._sync_operation()
        self.sb_value.setValue(DEFAULTS["value"])
        self.sb_smooth.setValue(DEFAULTS["smooth_steps"])
        self.sb_blend.setValue(DEFAULTS["blend"])
        self.line_buttons.button(DEFAULTS["joint_lines"]).setChecked(True)
        self.lock_buttons.button(DEFAULTS["joint_locks"]).setChecked(True)
        self.border_buttons.button(DEFAULTS["border_edges"]).setChecked(True)
        self.sb_border_steps.setValue(DEFAULTS["border_mask_steps"])
        self._set_checks_default()
        self._sync_border_steps()
        self._log("[OK] Flood options are back to their defaults.")

    # ==============================================================
    # 동작
    # ==============================================================

    def _confirm(self, question):
        answer = QMessageBox.question(self, "Flood weights", question, QMessageBox.Yes | QMessageBox.No)
        return answer == QMessageBox.Yes

    def on_flood(self, *args):
        joints = self.joints()
        if not joints:
            self._log("[WARN] Add the joints to flood to the list first.")
            return
        options = self.options()
        try:
            with undo_chunk():
                _done, messages = fl_mgr.flood_weights(joints, confirm=self._confirm, **options)
        except Exception as exc:                           # noqa: BLE001
            self._log("[FAIL] Flood failed : {0}".format(exc))
            return
        for message in messages:
            self._log(message)
