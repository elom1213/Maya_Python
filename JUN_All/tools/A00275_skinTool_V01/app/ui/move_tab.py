# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# A00275_skinTool_V01 - Weights > Move 탭 UI (v01.37)
"""
Weights > Move - 조인트 **n 개(From) -> k 개(To)** 웨이트 이동. Kangaroo `SkinCluster > Move` 이식.

로직은 전부 `app/core/weight_move_manager.py` 에 있다 - 여기서는 위젯 값만 읽어 넘긴다.
옵션 이름과 기본값은 원본과 1:1 이고, 이 툴이 더한 것은 `Respect selection` · `Use soft selection` 두 체크다.
Classic 탭의 `Joints to Joints` 는 From[i] -> To[i] 1:1 이라 뜻이 다르다 - 그래서 하위 탭을 따로 뒀다(계획서 Q1).

모든 UI 문자열은 영어. (한국어는 주석/독스트링만)
"""

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from Framework.core.maya_undo import undo_chunk
from tools.A00275_skinTool_V01.app.core import weight_move_manager as mv_mgr


FLOAT_SLIDER_STEPS = 1000
SMOOTH_SLIDER_MAX = 20

DEFAULTS = {
    "smooth_steps": 5,
    "blend": 1.0,
    "joint_lines": mv_mgr.JOINT_LINES_YES,
    "joint_locks": mv_mgr.LOCKS_IGNORE,
    "border_edges": mv_mgr.BORDER_ALL,
    "border_mask_steps": 2,
    "respect_selection": True,
    "use_soft_selection": True,
    "project_squash": True,
    "island_check": True,
}

_LINE_ITEMS = (
    ("Children in To list", mv_mgr.JOINT_LINES_YES,
     "Distance to the bone from each To joint to its child joints - only children\n"
     "that are in the To list. (Kangaroo default)"),
    ("All children", mv_mgr.JOINT_LINES_ALL_CHILDREN,
     "Distance to the bone from each To joint to any of its child joints,\n"
     "even children that are not in the To list."),
    ("Points only", mv_mgr.JOINT_LINES_NO,
     "Distance to the joint position itself (no bones)."),
)

_LOCK_ITEMS = (
    ("Ignore locks", mv_mgr.LOCKS_IGNORE, "Locked influences are treated like any other."),
    ("Keep locked weights", mv_mgr.LOCKS_KEEP,
     "A locked influence keeps its value on every vertex.\nThe unlocked influences take up the rest."),
    ("Only add to locked", mv_mgr.LOCKS_ONLY_ADD, "A locked influence may grow but never shrink."),
    ("Only remove from locked", mv_mgr.LOCKS_ONLY_REMOVE, "A locked influence may shrink but never grow."),
)

_BORDER_ITEMS = (
    ("Everything", mv_mgr.BORDER_ALL, "Move on the whole selection, borders included."),
    ("Ignore border edges", mv_mgr.BORDER_IGNORE,
     "Leave the open border of the mesh as it is, fading back in\n"
     "towards the inside (Border Mask Steps says how far)."),
    ("Only border edges", mv_mgr.BORDER_ONLY, "Move only on the strip along the open border of the mesh."),
)


class MoveTab(QWidget):
    """Weights > Move 탭. 로그는 툴 창의 것을 그대로 쓴다(log_callback)."""

    def __init__(self, log_callback=None, parent=None):
        super(MoveTab, self).__init__(parent)
        self._log = log_callback or (lambda text: None)
        self._syncing = False
        self._build_ui()
        self._update_button()

    # ==============================================================
    # UI
    # ==============================================================

    def _build_ui(self):
        root = QVBoxLayout(self)

        desc = QLabel(
            "Move the skin weights of n joints (From) to k joints (To).\n"
            "Each vertex goes to its closest To joint (by bone), and the seams between\n"
            "To joints are smoothed. Only where the From joints have weight changes.\n"
            "(Kangaroo SkinCluster > Move, no plugin needed)")
        desc.setAlignment(Qt.AlignCenter)
        root.addWidget(desc)

        eng = QGroupBox("Engine")
        eng_row = QHBoxLayout(eng)
        self.engine_buttons = QButtonGroup(self)
        self.rb_native = QRadioButton("Native")
        self.rb_native.setChecked(True)
        self.rb_native.setToolTip("No plugin. One click = one undo step.")
        self.rb_kangaroo = QRadioButton("Kangaroo")
        self.rb_kangaroo.setToolTip("Kangaroo Builder's moveSkinClusterWeights (the plugin must be loaded).")
        self.engine_buttons.addButton(self.rb_native)
        self.engine_buttons.addButton(self.rb_kangaroo)
        eng_row.addWidget(self.rb_native)
        eng_row.addWidget(self.rb_kangaroo)
        eng_row.addStretch(1)
        root.addWidget(eng)

        lists = QHBoxLayout()
        self.tsl_from = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="From (n)", select_label="Select From", log_callback=self._log)
        self.tsl_to = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="To (k)", select_label="Select To", log_callback=self._log)
        for tsl in (self.tsl_from, self.tsl_to):
            model = tsl.list_widget.model()
            model.rowsInserted.connect(self._update_button)
            model.rowsRemoved.connect(self._update_button)
            model.modelReset.connect(self._update_button)
            lists.addWidget(tsl)
        root.addLayout(lists)

        root.addWidget(self._build_options_group())
        row = QHBoxLayout()
        row.addWidget(self._build_radio_group("Joint Lines", _LINE_ITEMS, "line_buttons",
                                              DEFAULTS["joint_lines"]), 1)
        row.addWidget(self._build_radio_group("Joint Locks", _LOCK_ITEMS, "lock_buttons",
                                              DEFAULTS["joint_locks"]), 1)
        row.addWidget(self._build_border_group(), 1)
        root.addLayout(row)

        buttons = QHBoxLayout()
        self.btn_move = QPushButton("Move")
        self.btn_move.setMinimumHeight(32)
        self.btn_move.setToolTip(
            "Move the From weights to the To joints on the selected mesh(es) - or only on the\n"
            "selected vertices when Respect selection is on. One click = one undo step (Native).")
        self.btn_move.clicked.connect(self.on_move)
        buttons.addWidget(self.btn_move, 2)
        self.btn_reset = QPushButton("Reset Options")
        self.btn_reset.setToolTip("Put every option back to its default.")
        self.btn_reset.clicked.connect(self.reset_options)
        buttons.addWidget(self.btn_reset, 1)
        root.addLayout(buttons)
        root.addStretch(1)

    def _build_options_group(self):
        box = QGroupBox("Options")
        layout = QVBoxLayout(box)

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
            "How many times the seams between the To joints are averaged with their neighbours\n"
            "(only neighbours inside the selection). 0 = hard seams. Ignored when k = 1."))

        self.sb_blend, self.sl_blend = self._float_pair(DEFAULTS["blend"])
        layout.addLayout(self._labeled_row(
            "Blend", self.sl_blend, self.sb_blend,
            "How much of the moved result is used. 1.0 = all of it, 0.5 = halfway."))

        checks = QGridLayout()
        self.cb_respect = QCheckBox("Respect selection")
        self.cb_respect.setToolTip(
            "On: when vertices (edges / faces) are selected, only those vertices change.\n"
            "Off: the whole mesh is used even if components are selected.")
        self.cb_soft = QCheckBox("Use soft selection")
        self.cb_soft.setToolTip("When Maya's soft selection is on, its falloff is the amount moved per vertex.")
        self.cb_squash = QCheckBox("Project squash joints (skinParent)")
        self.cb_squash.setToolTip(
            "A To joint with a 'skinParent' string attribute is measured from the joint it names\n"
            "(Kangaroo rigs). No effect when the attribute is not there.")
        self.cb_island = QCheckBox("Island check")
        self.cb_island.setToolTip("Ask before moving when the selected vertices are split into several islands.")
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

    # ---------------- 작은 UI 헬퍼 (Smooth 탭과 같은 모양) ----------------

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
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 1.0)
        spin.setSingleStep(0.05)
        spin.setDecimals(3)
        spin.setValue(value)
        spin.setKeyboardTracking(False)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, FLOAT_SLIDER_STEPS)
        slider.setValue(int(round(value * FLOAT_SLIDER_STEPS)))
        slider.valueChanged.connect(
            lambda step: spin.setValue(step / float(FLOAT_SLIDER_STEPS))
            if abs(step / float(FLOAT_SLIDER_STEPS) - spin.value()) > 1e-9 else None)
        spin.valueChanged.connect(
            lambda new: slider.setValue(int(round(new * FLOAT_SLIDER_STEPS)))
            if int(round(new * FLOAT_SLIDER_STEPS)) != slider.value() else None)
        return spin, slider

    def _smooth_to_slider(self, value):
        """슬라이더 범위를 넘는 값은 슬라이더만 끝에 둔다 - 되먹임으로 값이 잘리지 않게(Smooth 탭과 같은 방어)."""
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
        self.sb_border_steps.setEnabled(self.border_buttons.checkedId() != mv_mgr.BORDER_ALL)

    def _set_checks_default(self):
        self.cb_respect.setChecked(DEFAULTS["respect_selection"])
        self.cb_soft.setChecked(DEFAULTS["use_soft_selection"])
        self.cb_squash.setChecked(DEFAULTS["project_squash"])
        self.cb_island.setChecked(DEFAULTS["island_check"])
        self.cb_soft.setEnabled(self.cb_respect.isChecked())

    def _update_button(self, *args):
        n = len(self.tsl_from.get_all_items())
        k = len(self.tsl_to.get_all_items())
        self.btn_move.setText("Move weights  {0} -> {1}".format(n, k) if n and k else "Move")
        self.btn_move.setEnabled(bool(n and k))

    # ==============================================================
    # 값 읽기
    # ==============================================================

    def options(self):
        return {
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

    def reset_options(self, *args):
        self.sb_smooth.setValue(DEFAULTS["smooth_steps"])
        self.sb_blend.setValue(DEFAULTS["blend"])
        self.line_buttons.button(DEFAULTS["joint_lines"]).setChecked(True)
        self.lock_buttons.button(DEFAULTS["joint_locks"]).setChecked(True)
        self.border_buttons.button(DEFAULTS["border_edges"]).setChecked(True)
        self.sb_border_steps.setValue(DEFAULTS["border_mask_steps"])
        self._set_checks_default()
        self._sync_border_steps()
        self._log("[OK] Move options are back to their defaults.")

    # ==============================================================
    # 동작
    # ==============================================================

    def _confirm(self, question):
        answer = QMessageBox.question(self, "Move weights", question, QMessageBox.Yes | QMessageBox.No)
        return answer == QMessageBox.Yes

    def on_move(self, *args):
        joints_from = self.tsl_from.get_all_items()
        joints_to = self.tsl_to.get_all_items()
        options = self.options()
        try:
            if self.rb_kangaroo.isChecked():
                with undo_chunk():
                    _ok, messages = mv_mgr.move_weights_kangaroo(joints_from, joints_to, **options)
            else:
                with undo_chunk():
                    _done, messages = mv_mgr.move_weights(joints_from, joints_to, confirm=self._confirm, **options)
        except Exception as exc:                           # noqa: BLE001
            self._log("[FAIL] Move failed : {0}".format(exc))
            return
        for message in messages:
            self._log(message)
