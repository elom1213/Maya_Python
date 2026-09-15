# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-15
# A00275_skinTool_V01 - Weights > Layer 탭 UI
"""
Weights > Layer - 메시 N 개의 웨이트를 레이어처럼 합성하는 탭.

main_window.py 가 이미 길어서 이 탭은 위젯 하나로 따로 둔다. 로직은 전부
`app/core/weight_layer_manager.py` 에 있고, 여기서는 목록 / lock / Blend 상태만 들고 있다.

조인트 lock 리스트는 A00290_BSTool Shape Editor 의 다중 편집을 따른다:
  - 행을 클릭 / Shift+클릭(범위) / Ctrl+클릭(토글)으로 **여러 개 고른다**(QTreeWidget 기본 선택).
  - **Lock 칸을 누르면**, 누른 행이 선택에 속해 있을 때 **선택된 행 전부**가 같은 상태로 바뀐다.
    선택은 그대로 둔다 - "여러 개 골라 두고 하나를 눌러 한꺼번에" 가 되게.
  - Space 도 같은 동작.

모든 UI 문자열은 영어. (한국어는 주석/독스트링만)
"""

from Framework.qt.qt import *
from Framework.qt import JUN_mod_filter_qt

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from tools.A00275_skinTool_V01.app.core import weight_layer_manager as lm


LOCK_COLUMN = 0
JOINT_COLUMN = 1
PATH_ROLE = Qt.UserRole

# 레이어 목록 열
L_INDEX, L_MESH, L_LOCKED, L_BLEND = range(4)

BLEND_SLIDER_STEPS = 1000


def _event_pos(event):
    """마우스 이벤트 위치 (PySide6 는 position(), PySide2 는 pos())."""
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()


class LockTree(QTreeWidget):
    """Lock 체크박스 열이 있는 조인트 목록.

    항목에 `ItemIsUserCheckable` 을 주지 않는다 - 주면 델리게이트가 **놓을 때** 체크를 또
    뒤집어서 한 번 누르면 두 번 바뀐다. 체크 전환은 전부 여기서 직접 한다.
    """

    lockToggled = Signal()

    def __init__(self, parent=None):
        super(LockTree, self).__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels(["Lock", "Joint"])
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.header().setStretchLastSection(True)
        self.setColumnWidth(LOCK_COLUMN, 48)

    def toggle_from(self, item):
        """item 의 반대 상태로. item 이 선택에 속하면 (보이는) 선택 행 전부."""
        state = Qt.Unchecked if item.checkState(LOCK_COLUMN) == Qt.Checked else Qt.Checked
        targets = self.selectedItems() if item.isSelected() else [item]
        for target in targets:
            if not target.isHidden():
                target.setCheckState(LOCK_COLUMN, state)
        self.lockToggled.emit()

    def _lock_hit(self, event):
        if event.button() != Qt.LeftButton:
            return None
        pos = _event_pos(event)
        item = self.itemAt(pos)
        if item is None or self.columnAt(pos.x()) != LOCK_COLUMN:
            return None
        return item

    def mousePressEvent(self, event):
        item = self._lock_hit(event)
        if item is not None:
            # 선택을 바꾸지 않도록 기본 처리로 넘기지 않는다.
            self.toggle_from(item)
            event.accept()
            return
        super(LockTree, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._lock_hit(event) is not None:
            event.accept()
            return
        super(LockTree, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        # 빠르게 두 번 누른 것도 두 번의 전환으로 본다.
        item = self._lock_hit(event)
        if item is not None:
            self.toggle_from(item)
            event.accept()
            return
        super(LockTree, self).mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            item = self.currentItem()
            if item is not None:
                self.toggle_from(item)
            event.accept()
            return
        super(LockTree, self).keyPressEvent(event)


class LayerTab(QWidget):
    """Weights > Layer 페이지."""

    def __init__(self, log_callback=None, parent=None):
        super(LayerTab, self).__init__(parent)
        self._log = log_callback or (lambda text: None)

        # 위 -> 아래 순서. 마지막이 베이스.
        # {"uuid", "influences": [롱네임], "locked": set(롱네임), "blend": float}
        self.layers = []
        # 위젯을 코드로 채우는 동안 시그널 처리를 막는 빗장.
        self._syncing = False

        self._build()
        self._show_layer(-1)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build(self):
        layout = QVBoxLayout(self)

        desc = QLabel(
            "Merge the skin weights of meshes with the SAME vertex order.\n"
            "Each mesh keeps the joints you lock, as much as Blend says. Where the "
            "locked\nweights add up past 1.0, the UPPER layers are cut first. The "
            "bottom mesh is the base:\nits geometry is used, and without locks its "
            "joints fill what is left.")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # ---------------- 레이어 목록
        layers_grp = QGroupBox("Layers  (bottom = base, upper layers are cut first)")
        layers_layout = QVBoxLayout(layers_grp)

        self.tw_layers = QTreeWidget()
        self.tw_layers.setColumnCount(4)
        self.tw_layers.setHeaderLabels(["#", "Mesh", "Locked", "Blend"])
        self.tw_layers.setRootIsDecorated(False)
        self.tw_layers.setUniformRowHeights(True)
        self.tw_layers.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tw_layers.setMinimumHeight(120)
        self.tw_layers.setColumnWidth(L_INDEX, 44)
        self.tw_layers.setColumnWidth(L_MESH, 220)
        self.tw_layers.setColumnWidth(L_LOCKED, 110)
        self.tw_layers.itemSelectionChanged.connect(self._on_layer_selected)
        layers_layout.addWidget(self.tw_layers)

        row = QHBoxLayout()
        for label, tip, slot in (
                ("Add Selected", "Add the selected skinned meshes to the bottom of the "
                 "list (in selection order).", self.on_add_selected),
                ("Remove", "Remove the highlighted layer.", self.on_remove),
                ("Up", "Move the highlighted layer up. Where the locks overflow, "
                 "upper layers are cut first.", lambda: self.on_move(-1)),
                ("Down", "Move the highlighted layer down. Lower layers keep their "
                 "locks first.", lambda: self.on_move(1)),
                ("Clear", "Remove every layer.", self.on_clear)):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _checked=False, s=slot: s())
            row.addWidget(btn)
        layers_layout.addLayout(row)

        row = QHBoxLayout()
        btn = QPushButton("Reload Joints")
        btn.setToolTip("Read the bound joints of every layer again (after changing a "
                       "skinCluster). Locks on joints that are still bound are kept.")
        btn.clicked.connect(self.on_reload)
        row.addWidget(btn)
        btn = QPushButton("Select Mesh")
        btn.setToolTip("Select the highlighted layer's mesh in the scene.")
        btn.clicked.connect(self.on_select_mesh)
        row.addWidget(btn)
        layers_layout.addLayout(row)

        layout.addWidget(layers_grp)

        # ---------------- 고른 레이어의 조인트 / lock / Blend
        self.gb_joints = QGroupBox("Joints")
        joints_layout = QVBoxLayout(self.gb_joints)

        self.tw_joints = LockTree()
        self.tw_joints.setMinimumHeight(200)
        self.tw_joints.lockToggled.connect(self._on_lock_toggled)

        filter_row = QHBoxLayout()
        self.lbl_joint_number = QLabel("")
        self.flt_joints = JUN_mod_filter_qt.JUN_mod_filter_qt_v01(
            tree_widget=self.tw_joints, tree_column=JOINT_COLUMN,
            placeholder="Type any part of a joint name",
            number_label=self.lbl_joint_number)
        filter_row.addWidget(self.flt_joints, 1)
        filter_row.addWidget(self.lbl_joint_number)
        joints_layout.addLayout(filter_row)

        joints_layout.addWidget(self.tw_joints)

        hint = QLabel(
            "Click / Shift+click / Ctrl+click rows to select several, then click one "
            "Lock box\n(or press Space) to lock or unlock all of them at once.")
        joints_layout.addWidget(hint)

        row = QHBoxLayout()
        for label, tip, slot in (
                ("Lock Selected", "Lock the selected rows.",
                 lambda: self.on_lock_rows(True, selected_only=True)),
                ("Unlock Selected", "Unlock the selected rows.",
                 lambda: self.on_lock_rows(False, selected_only=True)),
                ("Lock All", "Lock every visible row (the filter applies).",
                 lambda: self.on_lock_rows(True, selected_only=False)),
                ("Unlock All", "Unlock every visible row (the filter applies).",
                 lambda: self.on_lock_rows(False, selected_only=False))):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _checked=False, s=slot: s())
            row.addWidget(btn)
        joints_layout.addLayout(row)

        row = QHBoxLayout()
        btn = QPushButton("Select Joints")
        btn.setToolTip("Select the highlighted rows' joints in the scene (every "
                       "locked joint when no row is highlighted).")
        btn.clicked.connect(self.on_select_joints)
        row.addWidget(btn)
        row.addStretch(1)
        joints_layout.addLayout(row)

        blend_row = QHBoxLayout()
        blend_row.addWidget(QLabel("Blend"))
        self.sb_blend = QDoubleSpinBox()
        self.sb_blend.setDecimals(3)
        self.sb_blend.setRange(0.0, 1.0)
        self.sb_blend.setSingleStep(0.05)
        self.sb_blend.setValue(1.0)
        self.sb_blend.setKeyboardTracking(False)
        blend_tip = (
            "How much of this layer's locked weights goes into the result.\n\n"
            "  1.0 : the locked weights as they are (default).\n"
            "  0.5 : half of them - the rest is left for the other layers.\n"
            "  0.0 : this layer adds nothing.\n\n"
            "Locks are poured from the bottom layer up: where they add up past 1.0, "
            "an upper\nlayer is scaled down to what is left. A vertex that ends below "
            "1.0 is renormalized.")
        self.sb_blend.setToolTip(blend_tip)
        self.sb_blend.valueChanged.connect(self._on_blend_spin)
        blend_row.addWidget(self.sb_blend)
        self.sl_blend = QSlider(Qt.Horizontal)
        self.sl_blend.setRange(0, BLEND_SLIDER_STEPS)
        self.sl_blend.setValue(BLEND_SLIDER_STEPS)
        self.sl_blend.setToolTip(blend_tip)
        self.sl_blend.valueChanged.connect(self._on_blend_slider)
        blend_row.addWidget(self.sl_blend, 1)
        joints_layout.addLayout(blend_row)

        layout.addWidget(self.gb_joints)

        # ---------------- 출력
        out_grp = QGroupBox("Output")
        out_layout = QGridLayout(out_grp)

        self.rb_create = QRadioButton("Create new mesh")
        self.rb_create.setToolTip("Build a new mesh from the base mesh's rest shape and "
                                  "bind it with the merged weights.")
        self.rb_update = QRadioButton("Update existing mesh")
        self.rb_update.setToolTip(
            "Write the merged weights into a mesh that already exists (same vertex "
            "order).\nMissing joints are added to its skinCluster; joints it already "
            "has but the\nmerge does not use are kept with no weight. Ctrl+Z restores "
            "its old weights.")
        self.rb_create.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.rb_create)
        group.addButton(self.rb_update)
        self.rb_create.toggled.connect(self._on_output_mode)

        self.le_name = QLineEdit(lm.DEFAULT_NAME)
        self.le_name.setToolTip("Name of the new mesh. Maya adds a number if it is "
                                "taken.")
        self.le_target = QLineEdit()
        self.le_target.setPlaceholderText("Mesh to update")
        btn_target = QPushButton("<- Set")
        btn_target.setToolTip("Set from the first selected mesh.")
        btn_target.clicked.connect(self.on_set_target)
        self.btn_target = btn_target

        out_layout.addWidget(self.rb_create, 0, 0)
        out_layout.addWidget(QLabel("Name"), 0, 1)
        out_layout.addWidget(self.le_name, 0, 2, 1, 2)
        out_layout.addWidget(self.rb_update, 1, 0)
        out_layout.addWidget(QLabel("Target"), 1, 1)
        out_layout.addWidget(self.le_target, 1, 2)
        out_layout.addWidget(btn_target, 1, 3)
        layout.addWidget(out_grp)

        self.btn_merge = QPushButton("MERGE")
        self.btn_merge.setMinimumHeight(40)
        self.btn_merge.setToolTip("Merge the layers top to bottom (the log lists what "
                                  "was cut or renormalized).")
        self.btn_merge.clicked.connect(self.on_merge)
        layout.addWidget(self.btn_merge)

        layout.addStretch(1)
        self._on_output_mode()

    # --------------------------------------------------
    # 상태 헬퍼
    # --------------------------------------------------

    @staticmethod
    def _path(layer):
        found = cmds.ls(layer["uuid"], long=True) or []
        return found[0] if found else None

    def _current_index(self):
        items = self.tw_layers.selectedItems()
        if not items:
            return -1
        return self.tw_layers.indexOfTopLevelItem(items[0])

    def _locked_text(self, index):
        layer = self.layers[index]
        total = len(layer["influences"])
        count = len(layer["locked"])
        if index == len(self.layers) - 1 and count == 0:
            return "all (base)"
        return "{0} / {1}".format(count, total)

    def _refresh_layers(self, select=None):
        """레이어 목록을 다시 그린다. select 가 주어지면 그 줄을 고른다."""
        if select is None:
            select = self._current_index()
        self._syncing = True
        try:
            self.tw_layers.clear()
            last = len(self.layers) - 1
            for index, layer in enumerate(self.layers):
                path = self._path(layer)
                name = path.split("|")[-1] if path else "(missing)"
                item = QTreeWidgetItem([
                    "base" if index == last else str(index + 1),
                    name, self._locked_text(index), "{0:.3f}".format(layer["blend"])])
                item.setToolTip(L_MESH, path or "The mesh is gone from the scene.")
                self.tw_layers.addTopLevelItem(item)
        finally:
            self._syncing = False
        if 0 <= select < len(self.layers):
            # setSelected(True) 는 SingleSelection 이어도 다른 줄을 해제하지 않는다 -
            # 두 줄이 선택된 채 남아 엉뚱한 레이어가 '현재' 로 읽힌다. 클릭과 같은 경로로 고른다.
            self.tw_layers.setCurrentItem(self.tw_layers.topLevelItem(select))
        else:
            self._show_layer(-1)

    def _update_layer_row(self, index):
        item = self.tw_layers.topLevelItem(index)
        if item is None:
            return
        item.setText(L_LOCKED, self._locked_text(index))
        item.setText(L_BLEND, "{0:.3f}".format(self.layers[index]["blend"]))

    def _show_layer(self, index):
        """조인트 리스트와 Blend 를 index 레이어로 채운다. -1 이면 비운다."""
        self._syncing = True
        try:
            self.tw_joints.clear()
            valid = 0 <= index < len(self.layers)
            self.gb_joints.setEnabled(valid)
            if not valid:
                self.gb_joints.setTitle("Joints")
                self.sb_blend.setValue(1.0)
                self.sl_blend.setValue(BLEND_SLIDER_STEPS)
                return
            layer = self.layers[index]
            path = self._path(layer)
            base = "  (base)" if index == len(self.layers) - 1 else ""
            self.gb_joints.setTitle("Joints : {0}{1}".format(
                path.split("|")[-1] if path else "(missing)", base))
            for joint in layer["influences"]:
                item = QTreeWidgetItem(["", joint.split("|")[-1]])
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setData(JOINT_COLUMN, PATH_ROLE, joint)
                item.setToolTip(JOINT_COLUMN, joint)
                item.setCheckState(LOCK_COLUMN, Qt.Checked if joint in layer["locked"]
                                   else Qt.Unchecked)
                self.tw_joints.addTopLevelItem(item)
            self.sb_blend.setValue(layer["blend"])
            self.sl_blend.setValue(int(round(layer["blend"] * BLEND_SLIDER_STEPS)))
        finally:
            self._syncing = False
        self.flt_joints.refresh()

    def _joint_items(self, visible_only=False, selected_only=False):
        items = []
        for i in range(self.tw_joints.topLevelItemCount()):
            item = self.tw_joints.topLevelItem(i)
            if visible_only and item.isHidden():
                continue
            if selected_only and not item.isSelected():
                continue
            items.append(item)
        return items

    def specs(self):
        """코어에 넘길 레이어 목록(위 -> 아래)."""
        out = []
        for layer in self.layers:
            path = self._path(layer)
            out.append({"mesh": path or "",
                        "locked": sorted(layer["locked"]),
                        "blend": layer["blend"]})
        return out

    # --------------------------------------------------
    # 핸들러 : 레이어 목록
    # --------------------------------------------------

    def _on_layer_selected(self):
        if self._syncing:
            return
        self._show_layer(self._current_index())

    def on_add_selected(self):
        selection = cmds.ls(sl=True, long=True, objectsOnly=True) or []
        if not selection:
            self._log("[Warning] Layer : select the skinned meshes to add.")
            return
        known = {layer["uuid"] for layer in self.layers}
        added = 0
        first_new = len(self.layers)
        for node in selection:
            if cmds.objectType(node, isAType="shape"):
                parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
                node = parents[0] if parents else node
            uuid = (cmds.ls(node, uuid=True) or [None])[0]
            if not uuid or uuid in known:
                continue
            try:
                influences = lm.read_influences(node)
            except lm.LayerError as e:
                self._log("[Warning] Layer : {0}".format(e))
                continue
            known.add(uuid)
            self.layers.append({"uuid": uuid, "influences": influences,
                                "locked": set(), "blend": 1.0})
            added += 1
        if not added:
            self._log("[Warning] Layer : nothing was added (already listed, or not a "
                      "skinned mesh).")
            return
        self._refresh_layers(select=first_new)
        self._log("[OK] Layer : added {0} mesh(es). The bottom one is the base.".format(
            added))

    def on_remove(self):
        index = self._current_index()
        if index < 0:
            return
        del self.layers[index]
        self._refresh_layers(select=min(index, len(self.layers) - 1))

    def on_move(self, delta):
        index = self._current_index()
        new = index + delta
        if index < 0 or not 0 <= new < len(self.layers):
            return
        self.layers[index], self.layers[new] = self.layers[new], self.layers[index]
        self._refresh_layers(select=new)

    def on_clear(self):
        self.layers = []
        self._refresh_layers(select=-1)

    def on_reload(self):
        for layer in self.layers:
            path = self._path(layer)
            if not path:
                self._log("[Warning] Layer : a listed mesh is gone from the scene.")
                continue
            try:
                influences = lm.read_influences(path)
            except lm.LayerError as e:
                self._log("[Warning] Layer : {0}".format(e))
                continue
            dropped = [j for j in layer["locked"] if j not in influences]
            layer["influences"] = influences
            layer["locked"] = {j for j in layer["locked"] if j in influences}
            if dropped:
                self._log("[Warning] Layer : '{0}' - {1} locked joint(s) are no longer "
                          "bound and were unlocked.".format(path.split("|")[-1],
                                                            len(dropped)))
        self._refresh_layers()
        self._log("[OK] Layer : joints reloaded.")

    def on_select_mesh(self):
        index = self._current_index()
        if index < 0:
            return
        path = self._path(self.layers[index])
        if path:
            cmds.select(path, replace=True)

    # --------------------------------------------------
    # 핸들러 : 조인트 lock / Blend
    # --------------------------------------------------

    def _on_lock_toggled(self):
        index = self._current_index()
        if self._syncing or index < 0:
            return
        layer = self.layers[index]
        for item in self._joint_items():
            joint = item.data(JOINT_COLUMN, PATH_ROLE)
            if item.checkState(LOCK_COLUMN) == Qt.Checked:
                layer["locked"].add(joint)
            else:
                layer["locked"].discard(joint)
        self._update_layer_row(index)

    def on_lock_rows(self, lock, selected_only):
        items = self._joint_items(visible_only=True, selected_only=selected_only)
        if not items:
            return
        state = Qt.Checked if lock else Qt.Unchecked
        for item in items:
            item.setCheckState(LOCK_COLUMN, state)
        self._on_lock_toggled()

    def on_select_joints(self):
        index = self._current_index()
        if index < 0:
            return
        joints = [item.data(JOINT_COLUMN, PATH_ROLE)
                  for item in self._joint_items(selected_only=True)]
        if not joints:
            joints = sorted(self.layers[index]["locked"])
        joints = [j for j in joints if cmds.objExists(j)]
        if joints:
            cmds.select(joints, replace=True)

    def _set_blend(self, value):
        index = self._current_index()
        if index < 0:
            return
        self.layers[index]["blend"] = max(0.0, min(1.0, float(value)))
        self._update_layer_row(index)

    def _on_blend_spin(self, value):
        if self._syncing:
            return
        self._syncing = True
        try:
            self.sl_blend.setValue(int(round(value * BLEND_SLIDER_STEPS)))
        finally:
            self._syncing = False
        self._set_blend(value)

    def _on_blend_slider(self, step):
        if self._syncing:
            return
        value = float(step) / BLEND_SLIDER_STEPS
        self._syncing = True
        try:
            self.sb_blend.setValue(value)
        finally:
            self._syncing = False
        self._set_blend(value)

    # --------------------------------------------------
    # 핸들러 : 출력 / Merge
    # --------------------------------------------------

    def _on_output_mode(self, *_args):
        create = self.rb_create.isChecked()
        self.le_name.setEnabled(create)
        self.le_target.setEnabled(not create)
        self.btn_target.setEnabled(not create)

    def on_set_target(self):
        selection = cmds.ls(sl=True, objectsOnly=True) or []
        if not selection:
            self._log("[Warning] Layer : select the mesh to update first.")
            return
        node = selection[0]
        if cmds.objectType(node, isAType="shape"):
            parents = cmds.listRelatives(node, parent=True) or []
            node = parents[0] if parents else node
        self.le_target.setText(node)

    def on_merge(self):
        mode = lm.MODE_CREATE if self.rb_create.isChecked() else lm.MODE_UPDATE
        specs = self.specs()
        order = " > ".join((s["mesh"] or "(missing)").split("|")[-1] for s in specs)
        self._log("--- Layer merge ({0}: {1}) ---".format(mode, order or "no layers"))

        try:
            with undo_chunk():
                report = lm.merge(specs, mode=mode,
                                  name=self.le_name.text().strip() or lm.DEFAULT_NAME,
                                  target=self.le_target.text().strip() or None)
        except lm.LayerError as e:
            for line in str(e).splitlines():
                self._log("[Error] Layer : {0}".format(line))
            return
        except Exception as e:
            self._log("[Error] Layer : {0}".format(e))
            cmds.warning(str(e))
            return

        for line in report["warnings"]:
            self._log("[Warning] {0}".format(line))
        for line in report["infos"]:
            self._log("       {0}".format(line))
        mesh = report["mesh"].split("|")[-1]
        self._log("[OK] Layer : {0} '{1}' ({2}, {3} vertices, {4} influences{5}).".format(
            "created" if mode == lm.MODE_CREATE else "updated", mesh,
            report["skin_cluster"], report["vertices"], len(report["influences"]),
            ", {0} joint(s) added".format(len(report["added_influences"]))
            if report["added_influences"] else ""))
        if cmds.objExists(report["mesh"]):
            cmds.select(report["mesh"], replace=True)
