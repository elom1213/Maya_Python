# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-26
# A00275_skinTool_V01 - Weights > Flood 탭 UI (v01.40, v01.48 Select in List, v01.49 Add Influence 후 리스트 선택)
"""
Weights > Flood - 고른 조인트(들)에 웨이트를 채운다. Kangaroo `SkinCluster > Flood` 이식.

로직은 전부 `app/core/weight_flood_manager.py` 에 있다 - 여기서는 위젯 값만 읽어 넘긴다.
옵션 이름과 기본값은 원본과 1:1 이다(Smooth Steps 4 · Joint Lines = All children · Border Mask Steps 1).

**리스트 선택 = Flood 대상** (v01.48) : 리스트에서 행을 고르면 그 조인트만, 안 고르면 리스트 전부를 Flood 한다.
`Select in List` 는 씬에서 고른 조인트를 리스트에서 골라 준다(바인드 조인트를 다 읽어 둔 뒤 일부만 Flood 할 때).

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
from Framework.core import maya_skin
from Framework.qt.MOD_sliderStyle_qt_v01 import JUN_mod_sliderStyle_qt_v01


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
        self._mesh_uuids = []          # v01.42 - Get Bound Joints 로 읽은 메시(UUID, 리네임 · 리페어런트 안전)
        self._build_ui()
        # v01.45 - 테마 qss 에 QSlider 규칙이 없어 어두운 배경에서 홈이 묻히고 손잡이만 보였다 -> 공용 위젯이 테마 색으로 칠한다.
        self.slider_style = JUN_mod_sliderStyle_qt_v01(self)
        self._sync_operation()
        self._update_button()
        self._sync_mesh_label()

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
            name_display=True, title="Joints", select_label="Select Joints", log_callback=self._log,
            show_up=False, show_down=False, show_sort=False)
        # v01.48 - 리스트는 늘 아웃라이너 계층 순서 + 들여쓰기 -> 순서를 손으로 바꾸는 Up/Down/Sort 는 뺐다
        # (Flood 결과는 리스트 순서와 무관하다). Select/Add 는 위젯 슬롯이 먼저 돈 뒤 여기서 정렬한다.
        self.tsl_joints.btn_select.clicked.connect(self._apply_hierarchy)
        self.tsl_joints.btn_add.clicked.connect(self._apply_hierarchy)
        # v01.41 - 메시를 고르고 누르면 그 메시에 바인드된 조인트로 리스트를 채운다.
        self.btn_bound = self.tsl_joints.add_button("Get Bound Joints", self.on_get_bound_joints, index=0)
        self.btn_bound.setToolTip(
            "Fill the list with the joints bound to the selected mesh(es).\n"
            "Mesh selected: every bound joint. Vertices / edges / faces selected:\n"
            "only the joints that have weight on them.\n"
            "The mesh(es) are remembered for Add Influence.")
        # v01.42 - 씬에서 고른 조인트를 기억한 메시의 skinCluster 에 인플루언스로 추가 (Skin > Add Influence 와 같다).
        self.btn_add_infl = self.tsl_joints.add_button("Add Influence", self.on_add_influence, index=1)
        self.btn_add_infl.setToolTip(
            "Add the joints selected in the scene to the skinCluster of the mesh(es)\n"
            "read by Get Bound Joints, with weight 0 (like Maya's Skin > Add Influence),\n"
            "and put them in the list. The mesh shape does not change.\n"
            "The joints are then selected in the list, so Flood works on them only.")
        # v01.48 - 씬에서 고른 조인트를 리스트에서 골라 준다 -> 이어서 Flood 하면 그 조인트만.
        self.btn_pick = self.tsl_joints.add_button("Select in List", self.on_select_in_list, index=2)
        self.btn_pick.setToolTip(
            "Select, in this list, the joints you selected in the scene\n"
            "(e.g. after Get Bound Joints, pick a few of them in the viewport or Outliner).\n"
            "Flood then works only on the joints selected in the list.\n"
            "Joints with the same name are told apart.")
        self.tsl_joints.list_widget.itemSelectionChanged.connect(self._update_button)
        model = self.tsl_joints.list_widget.model()
        model.rowsInserted.connect(self._update_button)
        model.rowsRemoved.connect(self._update_button)
        model.modelReset.connect(self._update_button)
        left = QVBoxLayout()
        self.lbl_mesh = QLabel()
        self.lbl_mesh.setToolTip("The skinned mesh(es) Add Influence works on (set by Get Bound Joints).")
        left.addWidget(self.lbl_mesh)
        left.addWidget(self.tsl_joints, 1)
        top.addLayout(left, 1)
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
        picked = len(self.tsl_joints.selected_items())
        if picked:
            text = "Flood  {0} selected joint(s)".format(picked)
        else:
            text = "Flood  {0} joint(s)".format(n) if n else "Flood"
        self.btn_flood.setText(text)
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
        """Flood 할 조인트를 **풀패스**로 (UUID 로 푼다 - 같은 이름 · 리네임 · 리페어런트 안전).

        v01.48 - 리스트에서 고른 행이 있으면 **그 행만**, 없으면 리스트 전부.
        씬에서 사라진 항목은 빠지고, 그 수를 로그에 남긴다.
        """
        if self.tsl_joints.selected_items():
            texts = self.tsl_joints.selected_items()
            nodes = self.tsl_joints.selected_nodes()
        else:
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

    def on_get_bound_joints(self, *args):
        """선택 메시의 바인드 조인트로 리스트를 **교체**한다.

        리스트에는 짧고 유일한 이름(`cmds.ls(풀패스)`)으로 담는다 - 같은 이름이면 `A|dup` 처럼 부분 경로가 되고,
        담을 때 UUID 가 붙으므로 Flood 는 그대로 풀패스로 돈다.
        """
        import maya.cmds as cmds
        try:
            targets = fl_mgr.parse_selection(use_soft_selection=False)
            joints, messages = fl_mgr.bound_joints(targets=targets) if targets else fl_mgr.bound_joints()
        except Exception as exc:                           # noqa: BLE001
            self._log("[FAIL] Get Bound Joints failed : {0}".format(exc))
            return
        meshes = fl_mgr.skinned_meshes(targets)
        if meshes:
            self._mesh_uuids = [u for m in meshes for u in (cmds.ls(m, uuid=True) or [])[:1]]
            self._sync_mesh_label()
        for message in messages:
            self._log(message)
        if not joints:
            if not any(m.startswith("[WARN]") for m in messages):
                self._log("[WARN] No bound joint found.")
            return
        names = [(cmds.ls(j) or [j])[0] for j in joints]
        self.tsl_joints.set_items(names)
        self._apply_hierarchy()
        self._log("[OK] Listed {0} bound joint(s).".format(len(names)))

    # ---------------- 계층 표시 (v01.48) ----------------

    def _apply_hierarchy(self, *args):
        """리스트를 아웃라이너 계층 순서로 다시 놓고, 리스트 안 조상 수만큼 들여 쓴다(글자는 그대로)."""
        tsl = self.tsl_joints
        if tsl.is_deferred() or not tsl.count():
            return
        nodes = [tsl.node_at(i) or tsl.list_widget.item(i).text() for i in range(tsl.list_widget.count())]
        order, depths = fl_mgr.hierarchy_order(nodes)
        tsl.arrange(order, depths)

    # ---------------- Select in List (v01.48) ----------------

    def on_select_in_list(self, *args):
        """씬에서 고른 조인트 중 리스트에 있는 것을 리스트에서 선택한다(씬 선택은 건드리지 않는다).

        비교는 풀패스(UUID) 기준이라 같은 이름 조인트도 정확히 그 행만 잡힌다.
        """
        import maya.cmds as cmds
        selected = cmds.ls(sl=True, type="joint", long=True) or []
        if not selected:
            self._log("[WARN] Select joints in the scene first.")
            return
        if self.tsl_joints.is_deferred():
            self.tsl_joints.show_all()
        rows = self.tsl_joints.select_by_nodes(selected)
        self._update_button()
        missing = len(selected) - len(rows)
        if not rows:
            self._log("[WARN] None of the {0} selected joint(s) are in the list.".format(len(selected)))
            return
        self._log("[OK] Selected {0} joint(s) in the list - Flood will use only these.".format(len(rows)))
        if missing > 0:
            self._log("[WARN] {0} selected joint(s) are not in the list - skipped.".format(missing))

    # ---------------- Add Influence (v01.42) ----------------

    def meshes(self):
        """Get Bound Joints 로 기억한 메시의 **지금** 풀패스 (씬에서 사라진 것은 빠진다)."""
        import maya.cmds as cmds
        out = []
        for uuid in self._mesh_uuids:
            found = cmds.ls(uuid, long=True) or []
            if found and found[0] not in out:
                out.append(found[0])
        return out

    def _sync_mesh_label(self):
        import maya.cmds as cmds
        meshes = self.meshes() if self._mesh_uuids else []
        if not meshes:
            self.lbl_mesh.setText("Mesh : (none - select a skinned mesh, Get Bound Joints)")
        else:
            names = [(cmds.ls(m) or [m])[0] for m in meshes]
            text = ", ".join(names[:3]) + (" +{0}".format(len(names) - 3) if len(names) > 3 else "")
            self.lbl_mesh.setText("Mesh : " + text)
        self.btn_add_infl.setEnabled(bool(meshes))

    def on_add_influence(self, *args):
        """씬에서 고른 조인트를 기억한 메시의 skinCluster 에 웨이트 0 으로 더하고 리스트에 붙인다(한 번 = undo 한 스텝)."""
        import maya.cmds as cmds
        selected = cmds.ls(sl=True, type="joint", long=True) or []
        meshes = self.meshes()
        try:
            with undo_chunk():
                added, messages = fl_mgr.add_influences(meshes, selected)
        except Exception as exc:                           # noqa: BLE001
            self._log("[FAIL] Add Influence failed : {0}".format(exc))
            return
        for message in messages:
            self._log(message)
        self._sync_mesh_label()
        if not meshes:
            return
        # 이미 바인드돼 있던 것도 리스트에는 붙인다(고른 조인트로 바로 Flood 할 수 있게).
        bound = set()
        for mesh in meshes:
            for skin in fl_mgr.skin_clusters(mesh)[:1]:
                bound.update(maya_skin.influence_paths(maya_skin.skin_fn(skin)))
        listed = [j for j in selected if j in bound]
        if listed:
            self.tsl_joints.append_unique([(cmds.ls(j) or [j])[0] for j in listed])
            self._apply_hierarchy()
            self._select_listed(listed)

    def _select_listed(self, nodes):
        """v01.49 - Add Influence 한 조인트를 리스트에서 골라 둔다 -> 이어서 Flood 하면 그 조인트만.

        이전 리스트 선택은 지운다(select_by_nodes). 요약 모드면 먼저 펼친다(Select in List 와 같다).
        select_by_nodes 는 시그널을 막으므로 Flood 버튼 글자는 여기서 갱신한다.
        """
        if self.tsl_joints.is_deferred():
            self.tsl_joints.show_all()
            self._apply_hierarchy()
        rows = self.tsl_joints.select_by_nodes(nodes)
        self._update_button()
        if rows:
            self._log("[OK] Selected {0} joint(s) in the list - Flood will use only these.".format(len(rows)))

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
