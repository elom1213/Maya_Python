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

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt
from Framework.qt.maya_window import maya_main_window
from Framework.qt.MOD_log_qt_v01 import JUN_mod_log_qt_v01
from Framework.qt.MOD_menuBar_qt_v01 import JUN_mod_menuBar_qt_v01
from Framework.qt.MOD_progress_qt_v01 import JUN_mod_progress_qt_v01
from Framework.qt.MOD_sliderStyle_qt_v01 import JUN_mod_sliderStyle_qt_v01

from tools.A00630_MotionPathEditor.app.config.version import VERSION, LAST_UPDATE
from tools.A00630_MotionPathEditor.app.core import draw_nodes
from tools.A00630_MotionPathEditor.app.core import path_manager as pm
from tools.A00630_MotionPathEditor.app.core import picking
from tools.A00630_MotionPathEditor.app.core.watcher import Watcher

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
        self.resize(460, 720)

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
        self.slider_style = JUN_mod_sliderStyle_qt_v01(self)

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
            "on the path to change the animation. Ctrl+Z undoes a drag in one step.")
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

        root.addWidget(self._build_range_group())
        root.addWidget(self._build_display_group())
        root.addWidget(self._build_edit_group())

        self.log_view = JUN_mod_log_qt_v01(window_title="Motion Path Editor - Log",
                                           object_name="JUN_A00630_MotionPathEditor_log_window")
        self.log_view.setMinimumHeight(90)
        root.addWidget(self.log_view, 1)

    def _build_range_group(self):
        box = QGroupBox("Range")
        lay = QHBoxLayout(box)
        self.range_buttons = QButtonGroup(self)
        for label, value, tip in (("Playback", pm.RANGE_PLAYBACK, "The playback range of the time slider."),
                                  ("Scene", pm.RANGE_SCENE, "The animation start / end of the scene."),
                                  ("Custom", pm.RANGE_CUSTOM, "The frames set on the right.")):
            rb = QRadioButton(label)
            rb.setToolTip(tip)
            rb.setProperty("rangeMode", value)
            rb.setChecked(self.manager.settings["range"] == value)
            self.range_buttons.addButton(rb)
            lay.addWidget(rb)
        self.sb_start = QSpinBox()
        self.sb_end = QSpinBox()
        for sb, key in ((self.sb_start, "custom_start"), (self.sb_end, "custom_end")):
            sb.setRange(-100000, 100000)
            sb.setValue(int(self.manager.settings[key]))
            sb.setKeyboardTracking(False)
            lay.addWidget(sb)
        self.range_buttons.buttonClicked.connect(lambda *_: self._on_range_changed())
        self.sb_start.valueChanged.connect(lambda *_: self._on_range_changed())
        self.sb_end.valueChanged.connect(lambda *_: self._on_range_changed())
        self._sync_range_enabled()
        return box

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
            self._with_progress(lambda prog: self.manager.rebake_all(progress=prog), len(self.manager.caches))
            self.log("[OK] Re-baked {0} path(s), frames {1}-{2}.".format(len(self.manager.caches),
                                                                       *self.manager.frame_range()))
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Refresh failed : {0}".format(exc))

    def _sync_range_enabled(self):
        custom = self.manager.settings["range"] == pm.RANGE_CUSTOM
        self.sb_start.setEnabled(custom)
        self.sb_end.setEnabled(custom)

    def _on_range_changed(self):
        btn = self.range_buttons.checkedButton()
        self.manager.settings["range"] = btn.property("rangeMode") if btn else pm.RANGE_PLAYBACK
        self.manager.settings["custom_start"] = self.sb_start.value()
        self.manager.settings["custom_end"] = self.sb_end.value()
        for key in ("range", "custom_start", "custom_end"):
            self._save(key)
        self._sync_range_enabled()
        if self.manager.caches:
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

    def _on_scene_change(self):
        """새 씬 · 열기 직전: 경로를 모두 정리한다."""
        if self.context is not None:
            self.context.deactivate()
        self.btn_edit.setChecked(False)
        self.manager.clear()
        self._syncing = True
        try:
            self.tsl_paths.set_items([])
        finally:
            self._syncing = False

    def closeEvent(self, event):
        try:
            if self.context is not None:
                self.context.deactivate()
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
