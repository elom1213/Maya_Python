# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 툴 창 (계획서 §4-9)
"""
고른 오브젝트 · 조인트의 프레임별 월드 위치를 뷰포트에 경로로 그리고, 경로 위 키를 끌어 애니메이션을 고친다.
블렌더 애드온 Editable Motion Paths 의 아이디어를 **독자 구현**한 것(원본은 GPL-3.0 - 코드는 쓰지 않았다).
계획서 docs/plans/A00630_MotionPathEditor_plan.md.

모든 UI 문자열은 영어. (한국어는 주석/독스트링만)
"""

import maya.api.OpenMaya as om
import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt import JUN_mod_timeRange_qt
from Framework.qt.pin_style import apply_pin_style
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_progress_qt_v01 import JUN_mod_progress_qt_v01
from Framework.qt.MOD_sliderStyle_qt_v01 import JUN_mod_sliderStyle_qt_v01
from Framework.qt.MOD_tabFit_qt_v01 import JUN_mod_tabFit_qt_v01

from tools.A00630_MotionPathEditor.app.config.version import VERSION, LAST_UPDATE
from tools.A00630_MotionPathEditor.app.core import anim_channels as ch
from tools.A00630_MotionPathEditor.app.core import draw_nodes
from tools.A00630_MotionPathEditor.app.core import path_manager as pm
from tools.A00630_MotionPathEditor.app.core import picking
from tools.A00630_MotionPathEditor.app.core.watcher import Watcher
from tools.A00630_MotionPathEditor.app.ui.speed_graph import SpeedPanel

WINDOW_OBJECT_NAME = "JUN_A00630_MotionPathEditor_window"
OPTVAR = "JUN_A00630_"
#: 진행 팝업을 띄울 굽기 크기 (대상 수 x 프레임 수)
PROGRESS_THRESHOLD = 2000

_PLANE_ITEMS = (
    ("View", picking.PLANE_VIEW, "Move in the plane facing the camera (default)."),
    ("Ground", picking.PLANE_GROUND, "Move on the horizontal plane (world XZ) through the key."),
    ("X", picking.AXIS_X, "Move along world X only."),
    ("Y", picking.AXIS_Y, "Move along world Y only."),
    ("Z", picking.AXIS_Z, "Move along world Z only."),
)


class MainWindow(QWidget):

    def __init__(self):
        super().__init__(maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle("Motion Path Editor v{0}".format(VERSION))
        self.setWindowFlags(Qt.Window)
        self.resize(480, 760)

        draw_nodes.ensure_plugin()
        draw_nodes.delete_all()                 # 이전 세션이 남긴 그리기 노드
        self.manager = pm.PathManager(log=self.log)
        self._load_settings()
        self.watcher = Watcher(self.manager, on_scene_change=self._on_scene_change)
        self.context = None                     # 편집 컨텍스트 (Edit Path 를 처음 켤 때 만든다)
        self._syncing = False

        self.build_ui()
        self.manager.view_refresh = self._refresh_view
        self.watcher.start()
        # v01.01 - Q 를 누르거나 다른 마야 툴로 바꾸면 편집 모드가 꺼진다 → 버튼(빨강)도 따라 끈다
        self._tool_cb = om.MEventMessage.addEventCallback("ToolChanged", self._on_tool_changed)
        self.slider_style = JUN_mod_sliderStyle_qt_v01(self)
        if draw_nodes.replaced_plugin:              # v01.07 - 마야에 남아 있던 옛 플러그인을 새것으로 바꿨다
            self.log("[Info] Replaced the old Motion Path plugin (v{0}) loaded in this Maya session. "
                     "The undo queue was cleared once to do it.".format(draw_nodes.replaced_plugin))
            draw_nodes.replaced_plugin = None

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)

        self.menu_bar = JUN_mod_menuBar_qt_v01(tool_file=__file__)
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self.show_about)
        root.addWidget(self.menu_bar)

        desc = QLabel(
            "Draw the motion of objects / joints as a path, then drag the keys\n"
            "on the path to change the animation. Speed tab: see and smooth the timing.\n"
            "Ctrl+Z undoes a drag or a stroke in one step.")
        desc.setAlignment(Qt.AlignCenter)
        root.addWidget(desc)

        # ---- 경로 목록 (공용 TSL : Set / Add / Del 로 대상을 고르면 경로가 맞춰진다)
        self.tsl_paths = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Paths", select_label="Set Selected", show_order=False, show_sort=False,
            list_hint_height=120, log_callback=self.log)
        model = self.tsl_paths.list_widget.model()
        for sig in (model.rowsInserted, model.rowsRemoved, model.modelReset):
            sig.connect(self._on_paths_changed)
        root.addWidget(self.tsl_paths, 1)

        # v01.04 - 탭: Path (기존 설정 · 편집) / Speed (속도 그래프 · Smooth)
        self.tabs = QTabWidget()
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.addWidget(self._build_range_group())
        lay.addWidget(self._build_layer_group())
        lay.addWidget(self._build_display_group())
        lay.addWidget(self._build_edit_group())
        lay.addStretch(1)
        self.tabs.addTab(page, "Path")
        self.tabs.setTabToolTip(0, "Range, animation layer, display and Edit Path (drag the keys in the viewport).")
        self.speed_panel = SpeedPanel(self.manager, self.watcher, self.log, self._save)
        self.tabs.addTab(self.speed_panel, "Speed")
        self.tabs.setTabToolTip(1, "Speed graph: see the timing of a path and smooth it with a brush.")
        root.addWidget(self.tabs, 2)

        self.log_view = JUN_mod_log_qt_v01(window_title="Motion Path Editor - Log",
                                           object_name="JUN_A00630_MotionPathEditor_log_window")
        self.log_view.setMinimumHeight(90)
        root.addWidget(self.log_view, 1)
        self.tab_fit = JUN_mod_tabFit_qt_v01(self, self.tabs)

    def _build_range_group(self):
        box = QGroupBox("Range")
        outer = QVBoxLayout(box)
        lay = QHBoxLayout()
        self.range_buttons = QButtonGroup(self)
        for label, value, tip in (("Playback", pm.RANGE_PLAYBACK, "The playback range of the time slider."),
                                  ("Scene", pm.RANGE_SCENE, "The animation start / end of the scene."),
                                  ("Custom", pm.RANGE_CUSTOM, "The frames set below.")):
            rb = QRadioButton(label)
            rb.setToolTip(tip)
            rb.setProperty("rangeMode", value)
            rb.setChecked(self.manager.settings["range"] == value)
            self.range_buttons.addButton(rb)
            lay.addWidget(rb)
        lay.addStretch(1)
        outer.addLayout(lay)
        # v01.01 - Custom 시작 · 끝 = A00110 과 같은 공용 위젯 (Get Current 칸마다 + Get Sel Range 두 칸 함께)
        self.range_edit = JUN_mod_timeRange_qt.JUN_mod_timeRange_qt_v01(
            start_value=int(self.manager.settings["custom_start"]),
            end_value=int(self.manager.settings["custom_end"]), log_callback=self.log)
        self.range_edit.setToolTip("Custom range. Get Current: the current frame. "
                                   "Get Sel Range: the first and last selected keyframe.")
        self.range_edit.changed.connect(self._on_range_changed)
        outer.addWidget(self.range_edit)
        self.range_buttons.buttonClicked.connect(lambda *_: self._on_range_changed())
        self._sync_range_enabled()
        return box

    def _build_layer_group(self):
        """v01.03 - 편집할 애니메이션 레이어. 경로는 늘 모든 레이어를 합친 실제 움직임, 키 점 · 끌기는 고른 레이어만."""
        box = QGroupBox("Animation Layer")
        lay = QVBoxLayout(box)
        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.layer_list.setMaximumHeight(96)
        self.layer_list.setToolTip(
            "The layer whose keys are shown and dragged. Dragging changes only this layer's keys.\n"
            "The path always shows the motion of every layer combined (what really moves).\n"
            "A greyed path: the object is not in this layer, or the layer is locked / muted / weight 0.")
        self.layer_list.itemSelectionChanged.connect(self._on_layer_picked)
        lay.addWidget(self.layer_list)
        row = QHBoxLayout()
        self.lbl_layer = QLabel("")
        row.addWidget(self.lbl_layer, 1)
        btn = QPushButton("Reload Layers")
        btn.setToolTip("Read the animation layers of the scene again (after adding / deleting / renaming one).")
        btn.clicked.connect(self.reload_layers)
        row.addWidget(btn)
        lay.addLayout(row)
        self._layer_syncing = False
        self.reload_layers()
        return box

    def reload_layers(self, *args):
        """씬의 레이어로 목록을 다시 채우고, 편집 레이어를 고른다(없으면 Base)."""
        current = self.manager.edit_layer()
        self._layer_syncing = True
        try:
            self.layer_list.clear()
            for name in ch.scene_layers():
                item = QListWidgetItem(name)
                self.layer_list.addItem(item)
                if name == current:
                    item.setSelected(True)
            if not self.layer_list.selectedItems() and self.layer_list.count():
                self.layer_list.item(0).setSelected(True)
        finally:
            self._layer_syncing = False
        self._show_layer()

    def _show_layer(self):
        self.lbl_layer.setText("Editing: {0}".format(self.manager.edit_layer()))

    def _on_layer_picked(self):
        if self._layer_syncing:
            return
        items = self.layer_list.selectedItems()
        if not items:
            return
        name = items[0].text()
        if name == self.manager.edit_layer():
            return
        try:
            if self.context is not None:
                self.context._finalize()                # 끄는 중인 드래그가 있으면 취소
            self._with_progress(lambda prog: self.manager.set_edit_layer(name, progress=prog),
                                len(self.manager.caches))
            self._save("edit_layer")
            self.log("[OK] Editing the animation layer {0} - the path stays the combined motion.".format(
                self.manager.edit_layer()))
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Layer change failed : {0}".format(exc))
        self._show_layer()

    def _build_display_group(self):
        box = QGroupBox("Display")
        lay = QVBoxLayout(box)
        checks = QHBoxLayout()
        s = self.manager.settings
        self.cb_dots = QCheckBox("Frame dots")
        self.cb_dots.setToolTip("A dot on every frame - their spacing shows the speed.")
        self.cb_keys = QCheckBox("Keys")
        self.cb_keys.setToolTip("Big dots on the keys - drag them in Edit Path.")
        self.cb_numbers = QCheckBox("Frame numbers")
        self.cb_numbers.setToolTip("The frame number next to every key.")
        for cb, key in ((self.cb_dots, "show_dots"), (self.cb_keys, "show_keys"), (self.cb_numbers, "show_numbers")):
            cb.setChecked(bool(s[key]))
            cb.toggled.connect(lambda on, k=key: self._set(k, bool(on)))
            checks.addWidget(cb)
        checks.addStretch(1)
        lay.addLayout(checks)
        self.sl_line = self._slider_row(lay, "Line width", "line_width", 1, 8)
        self.sl_dot = self._slider_row(lay, "Dot size", "dot_size", 1, 12)
        self.sl_key = self._slider_row(lay, "Key size", "key_size", 4, 20)
        return box

    def _slider_row(self, layout, label, key, lo, hi):
        row = QHBoxLayout()
        title = QLabel(label)
        title.setMinimumWidth(80)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(int(round(self.manager.settings[key])))
        value = QLabel(str(slider.value()))
        value.setMinimumWidth(24)
        slider.valueChanged.connect(lambda v, k=key, lbl=value: (lbl.setText(str(v)), self._set(k, float(v))))
        row.addWidget(title)
        row.addWidget(slider, 1)
        row.addWidget(value)
        layout.addLayout(row)
        return slider

    def _build_edit_group(self):
        box = QGroupBox("Edit")
        lay = QVBoxLayout(box)
        row = QHBoxLayout()
        self.btn_edit = QPushButton("Edit Path")
        self.btn_edit.setCheckable(True)
        self.btn_edit.setMinimumHeight(34)
        self.btn_edit.setToolTip(
            "Turn the path edit tool on / off.\n"
            "Click a key: select it (Shift: add / remove, Ctrl: remove). Drag on empty space: box select.\n"
            "Drag a selected key: move it (and the other selected keys) - the animation follows.\n"
            "Right mouse while dragging: cancel. Alt + drag: Maya camera. Q: back to the select tool.")
        self.btn_edit.toggled.connect(self.set_edit_mode)
        # v01.01 - 켜져 있으면 연한 빨강 (공용 pin_style : 체크형 토글 = 켜짐 연한 빨강)
        apply_pin_style(self.btn_edit)
        row.addWidget(self.btn_edit, 2)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setMinimumHeight(34)
        self.btn_refresh.setToolTip(
            "Bake the paths again - needed after the animation of a parent / constraint / driver changed.\n"
            "(Edits of the path's own keys show at once without it.)")
        self.btn_refresh.clicked.connect(self.on_refresh)
        row.addWidget(self.btn_refresh, 1)
        lay.addLayout(row)

        plane = QHBoxLayout()
        plane.addWidget(QLabel("Drag in"))
        self.plane_buttons = QButtonGroup(self)
        for label, value, tip in _PLANE_ITEMS:
            rb = QRadioButton(label)
            rb.setToolTip(tip)
            rb.setProperty("plane", value)
            rb.setChecked(self.manager.settings["plane"] == value)
            self.plane_buttons.addButton(rb)
            plane.addWidget(rb)
        plane.addStretch(1)
        self.plane_buttons.buttonClicked.connect(
            lambda btn: self._set("plane", btn.property("plane"), redraw=False))
        lay.addLayout(plane)
        self.lbl_selection = QLabel("")
        lay.addWidget(self.lbl_selection)
        return box

    # ==================================================================
    # 설정
    # ==================================================================

    def _load_settings(self):
        s = self.manager.settings
        for key, default in pm.DEFAULT_SETTINGS.items():
            name = OPTVAR + key
            if not cmds.optionVar(exists=name):
                continue
            raw = cmds.optionVar(q=name)
            try:
                s[key] = type(default)(raw) if not isinstance(default, bool) else bool(int(raw))
            except (TypeError, ValueError):
                s[key] = default

    def _save(self, key):
        value = self.manager.settings[key]
        name = OPTVAR + key
        if isinstance(value, bool) or isinstance(value, int):
            cmds.optionVar(intValue=(name, int(value)))
        elif isinstance(value, float):
            cmds.optionVar(floatValue=(name, value))
        else:
            cmds.optionVar(stringValue=(name, str(value)))

    def _set(self, key, value, redraw=True):
        self.manager.settings[key] = value
        self._save(key)
        if redraw:
            self.manager.redraw()

    # ==================================================================
    # 동작
    # ==================================================================

    def log(self, text):
        try:
            self.log_view.appendPlainText(text)
        except Exception:                                  # noqa: BLE001
            print(text)

    def _refresh_view(self):
        try:
            cmds.refresh(currentView=True, force=True)
        except Exception:                                  # noqa: BLE001
            pass
        self._show_selection()

    def _show_selection(self):
        n = self.manager.selected_count()
        self.lbl_selection.setText("{0} key(s) selected".format(n) if n else "No key selected")

    def _with_progress(self, work, count):
        """굽기 - 크면 진행 팝업. work(progress) 를 부른다."""
        start, end = self.manager.frame_range()
        if count * (end - start + 1) < PROGRESS_THRESHOLD:
            return work(None)
        dlg = JUN_mod_progress_qt_v01(self, title="Motion Path Editor", message="Baking the paths...",
                                      phases=[("Baking", 100)])
        dlg.start()
        dlg.begin_phase()
        try:
            return work(dlg.callback())
        finally:
            dlg.finish()

    def _on_paths_changed(self, *args):
        if self._syncing:
            return
        self._syncing = True
        try:
            nodes = self.tsl_paths.get_all_nodes()
            new = [n for n in nodes if (cmds.ls(n, uuid=True) or [""])[0] not in self.manager.caches]
            added = self._with_progress(lambda prog: self.manager.set_targets(nodes, progress=prog), len(new))
            if added:
                self.log("[OK] Baked {0} path(s), frames {1}-{2}.".format(added, *self.manager.frame_range()))
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Could not make the paths : {0}".format(exc))
        finally:
            self._syncing = False

    def on_refresh(self, *args):
        if not self.manager.caches:
            self.log("[WARN] Add objects / joints to the Paths list first.")
            return
        try:
            self.reload_layers()                        # 레이어를 만들거나 지웠을 수 있다
            self._with_progress(lambda prog: self.manager.rebake_all(progress=prog), len(self.manager.caches))
            self.reload_layers()                        # 지워진 레이어였으면 Base 로 돌아왔다
            self.log("[OK] Re-baked {0} path(s), frames {1}-{2}.".format(len(self.manager.caches),
                                                                       *self.manager.frame_range()))
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Refresh failed : {0}".format(exc))

    def _sync_range_enabled(self):
        """시작 · 끝 칸과 Get Current · Get Sel Range 버튼은 Custom 일 때만."""
        self.range_edit.set_inputs_enabled(self.manager.settings["range"] == pm.RANGE_CUSTOM)

    def _on_range_changed(self, *args):
        """범위 모드 · 시작 · 끝이 바뀌면 저장하고, **실제 범위가 바뀌었을 때만** 다시 굽는다.

        공용 위젯은 칸에서 포커스만 빠져도 changed 를 보낸다 - 같은 범위로 다시 굽지 않게 비교한다.
        칸이 비었거나 숫자가 아니면 이전 값을 그대로 둔다.
        """
        before = self.manager.frame_range()
        btn = self.range_buttons.checkedButton()
        self.manager.settings["range"] = btn.property("rangeMode") if btn else pm.RANGE_PLAYBACK
        start, end = self.range_edit.start(), self.range_edit.end()
        if start is not None:
            self.manager.settings["custom_start"] = start
        if end is not None:
            self.manager.settings["custom_end"] = end
        for key in ("range", "custom_start", "custom_end"):
            self._save(key)
        self._sync_range_enabled()
        if self.manager.caches and self.manager.frame_range() != before:
            self.on_refresh()

    def set_edit_mode(self, on):
        """Edit Path 토글 - 편집 컨텍스트를 켜고 끈다 (GUI 전용)."""
        try:
            if self.context is None:
                from tools.A00630_MotionPathEditor.app.ui.edit_context import EditContext
                self.context = EditContext(self.manager, self.watcher, log=self.log)
            if on:
                if not self.manager.caches:
                    self.log("[WARN] Add objects / joints to the Paths list first.")
                self.context.activate()
                self.log("[Info] Edit Path on - click / drag the keys on the paths.")
            else:
                self.context.deactivate()
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Edit Path : {0}".format(exc))
            self.btn_edit.blockSignals(True)
            self.btn_edit.setChecked(False)
            self.btn_edit.blockSignals(False)

    def _on_tool_changed(self, *args):
        """마야 툴이 바뀌었다 - 버튼 맞추기는 **마야가 툴 전환을 끝낸 뒤(idle)** 에 한다.

        v01.02 - 알림을 받는 즉시 `currentCtx()` 를 물으면, Edit Path 를 켜는 그 순간에 아직 이전 툴 이름이 나와
        "편집 툴 아님" 으로 보고 방금 켠 버튼을 다시 껐다(편집은 되는데 버튼이 빨갛지 않던 증상, GUI 에서만).
        """
        if getattr(self, "_tool_sync_pending", False):
            return
        self._tool_sync_pending = True
        cmds.evalDeferred(self._sync_edit_button, lowestPriority=True)

    def _sync_edit_button(self):
        """Edit Path 버튼을 실제 상태(편집 컨텍스트가 지금 툴인가)에 맞춘다. 켜짐 = 연한 빨강."""
        self._tool_sync_pending = False
        try:
            active = self.context is not None and self.context.is_active()
        except Exception:                                  # noqa: BLE001
            active = False
        try:
            if self.btn_edit.isChecked() != active:
                if not active and self.context is not None:
                    self.context._finalize()                # 끄는 중인 드래그가 있으면 취소
                self.btn_edit.blockSignals(True)
                self.btn_edit.setChecked(active)
                self.btn_edit.blockSignals(False)
        except RuntimeError:
            pass                                            # 미뤄 둔 사이 창이 닫혔다 (버튼이 이미 없음)

    def _on_scene_change(self):
        """새 씬 · 열기 직전: 경로를 모두 정리한다."""
        if self.context is not None:
            self.context.deactivate()
        self.btn_edit.setChecked(False)
        self.manager.clear()
        self.manager.settings["edit_layer"] = ""
        self._syncing = True
        try:
            self.tsl_paths.set_items([])
        finally:
            self._syncing = False
        cmds.evalDeferred(self.reload_layers, lowestPriority=True)      # 새 씬이 열린 뒤 그 씬의 레이어로

    def closeEvent(self, event):
        try:
            self.speed_panel.shutdown()
            if self.context is not None:
                self.context.deactivate()
            if getattr(self, "_tool_cb", None) is not None:
                om.MMessage.removeCallback(self._tool_cb)
                self._tool_cb = None
            self.watcher.stop()
            self.manager.clear()
        finally:
            super().closeEvent(event)

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Motion Path Editor v{0}\nLast update : {1}\n\n"
            "Draws the motion of objects / joints as a path in the viewport and\n"
            "lets you drag the keys on it to change the animation.\n\n"
            "Fast: only the parent space is baked once; the object's own keys are\n"
            "read straight from its curves, so a drag never re-evaluates the scene.\n\n"
            "An independent implementation of the ideas of the Blender add-on\n"
            "Editable Motion Paths (no code taken from it).\n\n"
            "Written by Ji Hun Park.".format(VERSION, LAST_UPDATE))
