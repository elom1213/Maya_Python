# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - Speed 탭 오프스크린 시험 (속도 그래프 계획서 §6)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_speed_graph_ui.py
# QApplication 은 maya.standalone 보다 먼저 (메모 qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtCore import QEvent, QPoint, QPointF, Qt   # noqa: E402
from PySide2.QtGui import QMouseEvent, QWheelEvent   # noqa: E402
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
from Framework.themes.theme_manager import ThemeManager   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_bridge   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_manager as pm   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import main_window as mw   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import speed_graph as sg   # noqa: E402

cmds.undoInfo(state=True, infinity=True)
saved_vars = {k: cmds.optionVar(q=mw.OPTVAR + k) for k in pm.DEFAULT_SETTINGS if cmds.optionVar(exists=mw.OPTVAR + k)}
for k in pm.DEFAULT_SETTINGS:
    cmds.optionVar(remove=mw.OPTVAR + k)


def mouse(widget, kind, x, y, button=Qt.NoButton, buttons=Qt.NoButton, mods=Qt.NoModifier):
    types = {"press": QEvent.MouseButtonPress, "move": QEvent.MouseMove, "release": QEvent.MouseButtonRelease}
    ev = QMouseEvent(types[kind], QPointF(x, y), button, buttons, mods)
    QApplication.sendEvent(widget, ev)
    app.processEvents()


def wheel(widget, x, y, steps, mods=Qt.NoModifier):
    ev = QWheelEvent(QPointF(x, y), QPointF(widget.mapToGlobal(QPoint(int(x), int(y)))), QPoint(0, 0),
                     QPoint(0, int(120 * steps)), Qt.NoButton, mods, Qt.NoScrollPhase, False)
    QApplication.sendEvent(widget, ev)
    app.processEvents()


def track(node, frames):
    return np.array([world_pivot(node, f) for f in frames])


# ---- 씬: 속도가 들쭉날쭉한 경로 하나 + 조용한 경로 하나
cmds.file(new=True, force=True)
cmds.playbackOptions(minTime=1, maxTime=120, animationStartTime=1, animationEndTime=120)
node = cmds.polyCube(name="bumpy")[0]
for f in (1, 20, 35, 45, 60, 70, 90, 120):
    cmds.setKeyframe(node, attribute="translateX", time=f, value=f * 0.2 + (1.5 if f in (35, 60) else 0.0))
    cmds.setKeyframe(node, attribute="translateY", time=f, value=np.sin(f * 0.05) * 4)
    cmds.setKeyframe(node, attribute="translateZ", time=f, value=0.0)
other = cmds.polyCube(name="calm")[0]
for f in (1, 120):
    cmds.setKeyframe(other, attribute="translateZ", time=f, value=f * 0.1)
cmds.currentTime(1)

win = mw.MainWindow()
ThemeManager.load_theme_to_widget(win, "blue_dark")
logs = []
win.log = lambda text: logs.append(text)
win.manager.log = win.log
win.speed_panel.log = win.log
win.resize(700, 900)
win.show()
app.processEvents()

panel = win.speed_panel
graph = panel.graph
check("tabs: Path and Speed", [win.tabs.tabText(i) for i in range(win.tabs.count())] == ["Path", "Speed"])
check("empty graph says what to do", "Add paths" in graph.data.get("empty", ""))
win.tsl_paths.set_items([node, other])
app.processEvents()
check("path combo lists both paths", panel.cmb_path.count() == 2, [panel.cmb_path.itemText(i) for i in range(2)])
win.tabs.setCurrentIndex(1)
app.processEvents()
check("Speed tab shows the graph", graph.isVisible() and graph.height() >= 150, graph.height())
d = graph.data
check("speed mode: one series per path, active first-drawn last", len(d["series"]) == 2 and d["series"][-1]["active"])
check("keys of the active path drawn as lines", [t for t, _s in d["keys"]] == [1.0, 20.0, 35.0, 45.0, 60.0, 70.0, 90.0, 120.0])
check("range = whole path", (d["x0"], d["x1"]) == (1.0, 120.0))
cache = panel.active_cache()
want = np.linalg.norm(cache.points[1:] - cache.points[:-1], axis=1)
check("speed values = distance per frame (matches the path)",
      abs(d["series"][-1]["ys"][50] - np.interp(51, cache.times, np.r_[want[0], 0.5 * (want[:-1] + want[1:]), want[-1]])) < 0.05)
check("title names the unit", d["title"].startswith("Speed (cm/frame)"), d["title"])

# ---- 모드 · 단위
[b for b in panel.mode_buttons.buttons() if b.property("value") == sg.MODE_POSITION][0].click()
check("Position mode: X / Y / Z of the active path only", len(graph.data["series"]) == 3)
check("Position mode: no curve dragging", not graph.edit_curve)
[b for b in panel.mode_buttons.buttons() if b.property("value") == sg.MODE_ACCEL][0].click()
check("Acceleration mode draws", len(graph.data["series"]) == 2 and "Acceleration" in graph.data["title"])
[b for b in panel.mode_buttons.buttons() if b.property("value") == sg.MODE_SPEED][0].click()
panel.cmb_units.setCurrentIndex(1)
check("per second = 24 x per frame", abs(graph.data["series"][-1]["ys"][10] / d["series"][-1]["ys"][10] - 24.0) < 1e-6)
check("units setting remembered", cmds.optionVar(q=mw.OPTVAR + "graph_per_second") == 1)
panel.cmb_units.setCurrentIndex(0)

# ---- 범위 모드
cmds.currentTime(50)
[b for b in panel.range_buttons.buttons() if b.property("value") == sg.RANGE_AROUND][0].click()
check("Around Current = keys around frame 50 (45 - 60)", (graph.data["x0"], graph.data["x1"]) == (45.0, 60.0),
      (graph.data["x0"], graph.data["x1"]))
win.manager.selection = {cache.key: {35.0}}
[b for b in panel.range_buttons.buttons() if b.property("value") == sg.RANGE_SELECTED][0].click()
check("Selected Keys with one key = its two segments (20 - 45)", (graph.data["x0"], graph.data["x1"]) == (20.0, 45.0))
win.manager.selection = {}

# v01.06 Custom = [Start, End] 만 (공용 Start / End / Get Sel Range)
check("Custom off: Start / End inputs disabled", not panel.range_edit.start_edit.isEnabled())
[b for b in panel.range_buttons.buttons() if b.property("value") == sg.RANGE_CUSTOM][0].click()
check("Custom on: Start / End inputs enabled", panel.range_edit.start_edit.isEnabled())
panel.range_edit.set_range(30, 80)
check("Custom 30 - 80: the graph shows only those frames", (graph.data["x0"], graph.data["x1"]) == (30.0, 80.0) and
      graph.data["series"][-1]["xs"][0] == 30.0 and graph.data["series"][-1]["xs"][-1] == 80.0,
      (graph.data.get("x0"), graph.data.get("x1")))
check("Custom range remembered", cmds.optionVar(q=mw.OPTVAR + "graph_start") == 30 and
      cmds.optionVar(q=mw.OPTVAR + "graph_end") == 80 and cmds.optionVar(q=mw.OPTVAR + "graph_range") == "custom")
panel.range_edit.set_range(90, 200)
check("Custom past the path end is clipped to the path (90 - 120)", (graph.data["x0"], graph.data["x1"]) == (90.0, 120.0))
panel.range_edit.set_range(300, 400)
check("Custom outside the path: says so instead of drawing", not graph.data.get("series") and
      "outside the path" in graph.data.get("empty", ""), graph.data.get("empty"))
cmds.selectKey(clear=True)
cmds.selectKey(node + ".translateX", time=(20, 20), add=True)
cmds.selectKey(node + ".translateX", time=(60, 60), add=True)
panel.range_edit.get_selected_range()
check("Get Sel Range: first - last selected key (20 - 60)", (graph.data["x0"], graph.data["x1"]) == (20.0, 60.0),
      (graph.data.get("x0"), graph.data.get("x1")))
cmds.selectKey(clear=True)
[b for b in panel.range_buttons.buttons() if b.property("value") == sg.RANGE_PATH][0].click()
check("back to Whole Path: inputs disabled, whole range", not panel.range_edit.start_edit.isEnabled() and
      (graph.data["x0"], graph.data["x1"]) == (1.0, 120.0))

# ---- 휠: 반경 · 세기
r0 = graph.radius
cx, cy = graph.width() / 2, graph.height() / 2
wheel(graph, cx, cy, 2)
check("wheel grows the radius (spin box follows)", graph.radius > r0 and abs(panel.sp_radius.value() - graph.radius) < 0.06)
wheel(graph, cx, cy, -2)
s0 = graph.strength
wheel(graph, cx, cy, 2, Qt.ShiftModifier)
check("Shift+wheel raises the strength (slider follows)", graph.strength > s0 and panel.sl_strength.value() == int(round(graph.strength * 100)))
check("brush settings remembered", abs(cmds.optionVar(q=mw.OPTVAR + "brush_strength") - graph.strength) < 1e-6)

# ---- 왼쪽 빈 곳 = 스크럽
ytop = graph.MARGIN_T + 4
x80 = float(graph.frame_to_x(80.3))
mouse(graph, "press", x80, ytop + 60 if not graph.on_curve(x80, ytop + 60) else ytop + 2, Qt.LeftButton, Qt.LeftButton)
mouse(graph, "release", x80, ytop + 60, Qt.LeftButton, Qt.NoButton)
check("left-click on empty graph = current frame (rounded)", cmds.currentTime(q=True) == 80.0, cmds.currentTime(q=True))

# ---- 오른쪽 드래그 = 속도 Smooth 획 (놓을 때 undo 하나)
FR = np.arange(1, 121, dtype="float64")
before = track(node, FR)
cmds.flushUndo()
graph.radius = 12.0
graph.strength = 1.0
ybot = graph.height() - graph.MARGIN_B - 10
mouse(graph, "press", float(graph.frame_to_x(42)), ybot, Qt.RightButton, Qt.RightButton)
for f in np.linspace(42, 62, 8):
    mouse(graph, "move", float(graph.frame_to_x(f)), ybot, Qt.NoButton, Qt.RightButton)
check("while painting: preview in the viewport (ghost line + new dots)",
      len(draw_bridge.DATA[cache.key]["ghost"]) > 1 and cache.key in win.manager.preview)
check("while painting: the graph shows the original curve grey", graph.data.get("ghost") is not None)
check("while painting: animation untouched", np.abs(track(node, FR) - before).max() < 1e-12)
mouse(graph, "release", float(graph.frame_to_x(62)), ybot, Qt.RightButton, Qt.NoButton)
after = track(node, FR)
check("release: the stroke is written", np.abs(after - before).max() > 0.05)
check("release: preview gone", cache.key not in win.manager.preview and len(draw_bridge.DATA[cache.key]["ghost"]) == 0)
check("release: logged with the fit error", any(m.startswith("[OK] bumpy : stroke applied") for m in logs), logs[-2:])
sp0 = np.std(np.linalg.norm(np.diff(before[44:60], axis=0), axis=1))
sp1 = np.std(np.linalg.norm(np.diff(after[44:60], axis=0), axis=1))
check("the speed in the stroke is more even", sp1 < sp0, (sp1, sp0))
cmds.undo()
check("Ctrl+Z (one undo) = the stroke is gone", np.abs(track(node, FR) - before).max() < 1e-9)
win.manager.refresh_all()

# ---- v01.05 획 → 그래프 스크럽 → Ctrl+Z 한 번 = 획이 사라지고 그래프도 원래대로
#      (v01.04 는 스크럽이 cmds.currentTime 을 마우스 이동마다 불러 undo 큐에 시간 변경이 쌓였다 - Ctrl+Z 가 시간만 되돌림)
cmds.flushUndo()
g_before = np.array(graph.data["series"][-1]["ys"]).copy()
mouse(graph, "press", float(graph.frame_to_x(42)), ybot, Qt.RightButton, Qt.RightButton)
for f in np.linspace(42, 62, 8):
    mouse(graph, "move", float(graph.frame_to_x(f)), ybot, Qt.NoButton, Qt.RightButton)
mouse(graph, "release", float(graph.frame_to_x(62)), ybot, Qt.RightButton, Qt.NoButton)
g_stroke = np.array(graph.data["series"][-1]["ys"]).copy()
check("v01.05: the graph shows the stroke", np.abs(g_stroke - g_before).max() > 1e-3)
# 빈 곳 = 곡선 밖 (곡선 위면 속도 끌기가 된다)
f_scrub = 5
x_s = float(graph.frame_to_x(f_scrub))
ys_scrub = [y for y in range(int(ytop), int(ybot)) if not graph.on_curve(x_s, y)][0]
mouse(graph, "press", x_s, ys_scrub, Qt.LeftButton, Qt.LeftButton)
for f in range(f_scrub + 1, f_scrub + 11):
    mouse(graph, "move", float(graph.frame_to_x(f)), ys_scrub, Qt.NoButton, Qt.LeftButton)
mouse(graph, "release", float(graph.frame_to_x(f_scrub + 10)), ys_scrub, Qt.LeftButton, Qt.NoButton)
check("v01.05: scrubbing moves the time", cmds.currentTime(q=True) == f_scrub + 10.0, (f_scrub, cmds.currentTime(q=True)))
cmds.undo()
check("v01.05: after scrubbing, ONE undo still removes the stroke", np.abs(track(node, FR) - before).max() < 1e-9)
check("v01.05: scrubbing put nothing in the undo queue (time stays)", cmds.currentTime(q=True) == f_scrub + 10.0,
      cmds.currentTime(q=True))
win.watcher.flush()                     # 마야는 Undo 알림 뒤 idle 에 부른다
check("v01.05: after undo the graph shows the original curve",
      np.abs(np.array(graph.data["series"][-1]["ys"]) - g_before).max() < 1e-9)
cmds.redo()
win.watcher.flush()
check("v01.05: redo brings the stroke back in the graph",
      np.abs(np.array(graph.data["series"][-1]["ys"]) - g_stroke).max() < 1e-9)
cmds.undo()
win.watcher.flush()

# 끄는 중 Esc = 취소
mouse(graph, "press", float(graph.frame_to_x(42)), ybot, Qt.RightButton, Qt.RightButton)
mouse(graph, "move", float(graph.frame_to_x(55)), ybot, Qt.NoButton, Qt.RightButton)
from PySide2.QtGui import QKeyEvent   # noqa: E402
QApplication.sendEvent(graph, QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
mouse(graph, "release", float(graph.frame_to_x(55)), ybot, Qt.RightButton, Qt.NoButton)
check("Esc while painting: nothing written, preview gone",
      np.abs(track(node, FR) - before).max() < 1e-12 and cache.key not in win.manager.preview)

# ---- Smooth Range 버튼
panel.sp_radius.setValue(10.0)
panel.btn_smooth.click()
check("Smooth Range: one stroke over the whole graph", np.abs(track(node, FR) - before).max() > 0.05)
cmds.undo()
win.manager.refresh_all()

# ---- 곡선 끌기 = 그곳을 빠르게
app.processEvents()
ys = graph.data["series"][-1]["ys"]
x100 = float(graph.frame_to_x(100))
y100 = float(graph.value_to_y(np.interp(100, graph.data["series"][-1]["xs"], ys)))
check("the curve is hit at frame 100", graph.on_curve(x100, y100))
mouse(graph, "press", x100, y100, Qt.LeftButton, Qt.LeftButton)
mouse(graph, "move", x100, y100 - 40, Qt.NoButton, Qt.LeftButton)
mouse(graph, "release", x100, y100 - 40, Qt.LeftButton, Qt.NoButton)
fast = track(node, FR)
v_before = np.linalg.norm(before[100] - before[98]) / 2
v_after = np.linalg.norm(fast[100] - fast[98]) / 2
check("drag the curve up = faster there", v_after > v_before * 1.1, (v_after, v_before))
cmds.undo()
win.manager.refresh_all()

# ---- 키 선 위 왼쪽 드래그 = 스크럽 (v01.05: 키 시간 끌기는 없앴다 - 키는 그대로)
app.processEvents()
x70 = float(graph.frame_to_x(70))
yk = [y for y in range(int(ytop), int(ybot)) if not graph.on_curve(x70, y)][0]
mouse(graph, "press", x70, yk, Qt.LeftButton, Qt.LeftButton)
mouse(graph, "move", float(graph.frame_to_x(74)), yk, Qt.NoButton, Qt.LeftButton)
mouse(graph, "release", float(graph.frame_to_x(74)), yk, Qt.LeftButton, Qt.NoButton)
kx = cmds.keyframe(node + ".translateX", q=True, timeChange=True)
check("left-drag on a key line scrubs and does not move the key", 70.0 in kx and 74.0 not in kx and
      cmds.currentTime(q=True) == 74.0, (kx, cmds.currentTime(q=True)))
check("no key-time drag left", not hasattr(sg.SpeedGraphWidget, "key_drag_finished") and
      not hasattr(sg.SpeedPanel, "_on_key_moved"))

# ---- 모양 브러시
panel.cmb_brush.setCurrentIndex(1)
check("brush mode remembered", cmds.optionVar(q=mw.OPTVAR + "brush_mode") == "shape")
mouse(graph, "press", float(graph.frame_to_x(50)), ybot, Qt.RightButton, Qt.RightButton)
mouse(graph, "move", float(graph.frame_to_x(52)), ybot, Qt.NoButton, Qt.RightButton)
mouse(graph, "release", float(graph.frame_to_x(52)), ybot, Qt.RightButton, Qt.NoButton)
check("Smooth Shape stroke writes", np.abs(track(node, FR) - before).max() > 1e-4)
cmds.undo()
panel.cmb_brush.setCurrentIndex(0)

# ---- 잠긴 경로 / Pop Out
panel.cmb_path.setCurrentIndex(1)
check("switching the active path", panel.active_cache().label == "calm")
panel.btn_pop.click()
app.processEvents()
check("Pop Out moves the graph to its own window", panel._float is not None and graph.window() is panel._float)
panel.btn_pop.click()
app.processEvents()
check("Dock puts it back", panel._float is None and graph.parent() is panel.graph_holder)

win.close()
app.processEvents()
check("closing removes the graph listener", panel.refresh_graph not in win.manager.listeners)

for k in pm.DEFAULT_SETTINGS:
    cmds.optionVar(remove=mw.OPTVAR + k)
for k, v in saved_vars.items():
    if isinstance(v, int):
        cmds.optionVar(intValue=(mw.OPTVAR + k, v))
    elif isinstance(v, float):
        cmds.optionVar(floatValue=(mw.OPTVAR + k, v))
    else:
        cmds.optionVar(stringValue=(mw.OPTVAR + k, v))
_common.finish()
