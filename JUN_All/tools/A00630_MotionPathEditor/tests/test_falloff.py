# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - v01.09 프레임 점 고르기 · 폴오프 시험 (매니퓰레이터 · 폴오프 계획서 G1)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_falloff.py
#
# 1. falloff 계산 (마야 비의존) : 가중치 · 구간 · 색 · 색 선 조각 · 커브 저장
# 2. 관리자 : 프레임 점 고르기 · 선택 정리 · 가중치 · 그리기 데이터 · 플러그인 버전
# 3. 편집 컨텍스트 (가짜 뷰, test_edit_context 와 같은 방식) : 프레임 점 클릭 · 키 우선 · 박스 · b 톡 · b 끌기 반경 · Ctrl+Shift 끌기
# 4. b 키 필터 (진짜 Qt 키 이벤트) : 먹는다 · 누름/뗌 · 키 반복 무시 · Ctrl+B 는 통과 · 다른 툴이면 통과
# 5. 창 (오프스크린) : Falloff 줄 · 컨텍스트가 바꾼 설정이 칸에 · 선택 표시 · 저장
# QApplication 은 maya.standalone 보다 먼저 (메모 qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtCore import QEvent, Qt   # noqa: E402
from PySide2.QtGui import QKeyEvent   # noqa: E402
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.mel as mel   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check   # noqa: E402
import scenes   # noqa: E402
from _fake_view import FakeViewState, to_pixel, W, H   # noqa: E402
from Framework.core import falloff_curve as fcurve   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_bridge, draw_nodes, falloff, picking   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_manager as pm   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.watcher import Watcher   # noqa: E402
from tools.A00630_MotionPathEditor.app.plugin import jun_motion_path as plugin_source   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import edit_context as ec   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)

# ====================================================================== 1. 계산
T = np.arange(1.0, 101.0)
lin = falloff.lut({"points": [(0.0, 1.0), (1.0, 0.0)], "interp": fcurve.INTERP_LINEAR, "tangents": None})
w = falloff.weights(T, [50.0], 10.0, lin)
check("weights: the selected point = 1", w[49] == 1.0)
check("weights: linear curve, half the radius = 0.5", abs(w[54] - 0.5) < 1e-6 and abs(w[44] - 0.5) < 1e-6,
      (w[44], w[54]))
check("weights: at and beyond the radius = 0", w[59] == 0.0 and w[39] == 0.0 and w[:39].max() == 0.0)
check("weights: symmetric around the point", np.allclose(w[39:49], w[50:60][::-1]))
w = falloff.weights(T, [50.0], 10.0)          # 기본 = Smooth 프리셋
check("weights: default curve is Smooth (0.5 at half, smoother than linear near the point)",
      abs(w[54] - 0.5) < 1e-3 and w[50] > 0.9, (w[50], w[54]))
w2 = falloff.weights(T, [30.0, 34.0], 10.0, lin)
check("weights: two points - the nearer one decides, never more than 1", w2.max() <= 1.0 and
      w2[29] == 1.0 and w2[33] == 1.0 and abs(w2[31] - 0.8) < 1e-6, w2[29:34])
w0 = falloff.weights(T, [20.0, 70.0], 0.0)
check("weights: radius 0 = only the selected points", set(np.nonzero(w0)[0]) == {19, 69})
check("weights: fractional radius 2.5 reaches 2 frames", np.count_nonzero(falloff.weights(T, [50.0], 2.5, lin)) == 5)
check("weights: nothing selected = all 0", not falloff.weights(T, [], 10.0).any())
sub = np.array([1.0, 1.5, 2.0, 2.5, 3.0])                # 소수 시간(소수 프레임 키)도 같은 식
check("weights: fractional times", np.allclose(falloff.weights(sub, [2.0], 1.0, lin), [0, 0.5, 1, 0.5, 0]))
check("spans: one run per cluster", falloff.spans(T, w2) == [(21.0, 43.0)] and
      falloff.spans(T, falloff.weights(T, [20.0, 70.0], 5.0, lin)) == [(16.0, 24.0), (66.0, 74.0)],
      falloff.spans(T, w2))
c = falloff.colors([1.0, 0.5, 0.0])
check("colors: 1 = yellow, 0.5 = orange, 0 = dark red", c[0][0] > 0.9 and c[0][1] > 0.9 and c[0][2] < 0.3 and
      abs(c[1][1] - 0.5) < 1e-6 and c[2][0] < 0.5 and c[2][1] < 0.1, c)
runs = falloff.line_runs(falloff.weights(T, [50.0], 10.0, lin))
segs = sum(len(r) - 1 for _l, r in runs)
check("line runs: cover every segment inside the falloff once, consecutive points",
      segs == 20 and all(np.all(np.diff(r) == 1) for _l, r in runs) and runs[0][1][0] == 39 and runs[-1][1][-1] == 59,
      (segs, runs[0][1][:3], runs[-1][1][-3:]))
check("line runs: levels go up to the point and down after it",
      [l for l, _r in runs] == sorted([l for l, _r in runs])[:len(runs) // 2] + sorted([l for l, _r in runs], reverse=True)[len(runs) // 2:]
      or max(l for l, _r in runs) == falloff.LEVELS, [l for l, _r in runs])
text = falloff.curve_to_text([(0, 1), (0.5, 0.2), (1, 0)], fcurve.INTERP_SPLINE)
back = falloff.curve_from_text(text)
check("curve text round trip", back["interp"] == fcurve.INTERP_SPLINE and back["points"][1] == (0.5, 0.2))
check("broken curve text -> Smooth preset", falloff.curve_from_text("{nope")["interp"] == fcurve.INTERP_SMOOTH and
      falloff.curve_from_text("")["interp"] == fcurve.INTERP_SMOOTH)

# ====================================================================== 2. 관리자
names = scenes.simple(120)
logs = []
mgr = pm.PathManager(log=logs.append)
watcher = Watcher(mgr)
mgr.set_targets([names["plain"]])
cache = mgr.cache_list()[0]
key_rows = {k.row for k in cache.keys}
frames = mgr.pickable_frames()
check("pickable frames = every path point that is not a key", len(frames) == len(cache.times) - len(cache.keys) and
      not any(k.row in key_rows for _c, k in frames))
mgr.settings["show_dots"] = False
check("frame dots off -> frame points are not pickable", mgr.pickable_frames() == [])
mgr.settings["show_dots"] = True
f45 = [k for _c, k in frames if k.t == 45.0][0]
mgr.select([(cache, f45)], "replace")
check("a frame point can be selected", mgr.selection[cache.key] == {45.0} and mgr.selection_has_frames())
mgr.refresh_all()
check("refresh keeps a selected frame point (it is still on the path)", mgr.selection[cache.key] == {45.0})
check("falloff off -> no weights", mgr.weights_for(cache) is None and mgr.falloff_radius() == 0.0)
mgr.settings.update({"falloff_on": True, "falloff_radius": 10.0})
wts = mgr.weights_for(cache)
check("falloff on -> weights around the selected point", wts is not None and wts[cache.row_of(45.0)] == 1.0 and
      np.count_nonzero(wts) == 19, np.count_nonzero(wts))
check("falloff spans", mgr.falloff_spans()[0][1] == [(36.0, 54.0)], mgr.falloff_spans())
mgr.redraw()
data = draw_bridge.DATA[cache.key]
check("drawing: selected frame dot", len(data["selected_dots"]) == 1 and len(data["selected"]) == 0)
check("drawing: falloff dots + one color each", len(data["fall_dots"]) == 19 and len(data["fall_colors"]) == 19)
check("drawing: falloff line pieces (color levels)", len(data["fall_lines"]) >= 2 and
      sum(len(strip) - 1 for _c, strip in data["fall_lines"]) == 20)
mgr.settings["falloff_on"] = False
mgr.redraw()
check("falloff off -> no falloff drawing", len(draw_bridge.DATA[cache.key]["fall_dots"]) == 0 and
      not draw_bridge.DATA[cache.key]["fall_lines"])
loaded = mel.eval('junMotionPathVersion')
loaded = loaded[0] if isinstance(loaded, (list, tuple)) else loaded
check("the loaded plugin is the current one", loaded == plugin_source.PLUGIN_VERSION, loaded)
# 박스 선택 · 드래그가 키와 프레임 점을 섞어 받는다
key30 = [k for k in cache.keys if k.t == 30.0][0]
mgr.select([(cache, key30), (cache, f45)], "replace")
check("keys and frame points mix in one selection", mgr.selection[cache.key] == {30.0, 45.0})

# ====================================================================== 3. 편집 컨텍스트
settings_seen = []
ctx = ec.EditContext(mgr, watcher, log=logs.append, on_setting=settings_seen.append)
picking.ViewState = FakeViewState
STATE = {}
ctx._query = lambda flag: STATE[flag]
ctx._ctrl_shift = lambda: False


def click(p, modifier="none", button=1):
    x, y = to_pixel(p)
    STATE.update({"anchorPoint": [x, y, 0.0], "dragPoint": [x, y, 0.0], "button": button, "modifier": modifier})
    ctx._press()
    ctx._release()


mgr.select([], "replace")
click(cache.points[cache.row_of(45.0)])
check("click on a frame dot selects that frame", mgr.selection.get(cache.key) == {45.0}, mgr.selection)
click(cache.points[cache.row_of(30.0)])
check("click where a key and frame dots overlap picks the key", mgr.selection.get(cache.key) == {30.0}, mgr.selection)
click(cache.points[cache.row_of(46.0)], modifier="shift")
check("Shift + click adds a frame dot", mgr.selection.get(cache.key) == {30.0, 46.0})
# 박스: 40~50 프레임 근처를 감싸면 키(없음)와 프레임 점이 들어온다
px = [to_pixel(cache.points[cache.row_of(t)]) for t in (40.0, 50.0)]
xs, ys = sorted(p[0] for p in px), [to_pixel(cache.points[cache.row_of(t)])[1] for t in np.arange(40.0, 51.0)]
STATE.update({"anchorPoint": [xs[0] - 1, min(ys) - 2, 0.0], "dragPoint": [xs[1] + 1, max(ys) + 2, 0.0],
              "button": 1, "modifier": "none"})
ctx._press()
ctx._drag()
ctx._release()
got = mgr.selection.get(cache.key, set())
check("box selects frame dots too", set(np.arange(40.0, 51.0)) <= got, sorted(got))
mgr.select([(cache, f45)], "replace")
# (프레임 점 끌기 = deform 은 test_deform_drag.py)

# b 톡 = 켜기 / 끄기
mgr.settings.update({"falloff_on": False, "falloff_radius": 10.0})
del settings_seen[:]
ctx.b_pressed()
ctx.b_released()
check("tap b turns the falloff on", mgr.settings["falloff_on"] and settings_seen == ["falloff_on"] and
      any(m.startswith("[Info] Falloff on - radius 10") for m in logs), settings_seen)
ctx.b_pressed()
ctx.b_released()
check("tap b again turns it off", not mgr.settings["falloff_on"])
# b + 끌기 = 반경 (켜기도 한다), 가로만
del settings_seen[:]
ctx.b_pressed()
STATE.update({"anchorPoint": [300.0, 300.0, 0.0], "dragPoint": [300.0, 300.0, 0.0], "button": 1, "modifier": "none"})
ctx._press()
check("b + press starts a radius drag (no selection change)", ctx.radius_drag is not None and
      mgr.selection.get(cache.key) == {45.0} and mgr.settings["falloff_on"])
STATE["dragPoint"] = [350.0, 380.0, 0.0]
ctx._drag()
check("dragging right by 50 px grows the radius by 5 frames (vertical ignored)",
      abs(mgr.settings["falloff_radius"] - 15.0) < 1e-9, mgr.settings["falloff_radius"])
check("the radius shows next to the cursor", draw_bridge.HUD.get("text", (0, 0, ""))[2] == "Falloff 15 fr", draw_bridge.HUD)
check("the falloff colors follow the new radius while dragging",
      len(draw_bridge.DATA[cache.key]["fall_dots"]) == 29, len(draw_bridge.DATA[cache.key]["fall_dots"]))
STATE["dragPoint"] = [-400.0, 300.0, 0.0]
ctx._drag()
check("the radius never goes below 0", mgr.settings["falloff_radius"] == 0.0)
STATE["dragPoint"] = [320.0, 300.0, 0.0]
ctx._drag()
ctx._release()
ctx.b_released()
check("release keeps the radius, saves it, clears the text; releasing b after a drag does not toggle",
      abs(mgr.settings["falloff_radius"] - 12.0) < 1e-9 and "falloff_radius" in settings_seen and
      mgr.settings["falloff_on"] and "text" not in draw_bridge.HUD, (mgr.settings["falloff_radius"], settings_seen))
# Ctrl+Shift + 끌기 = 같은 일 (b 를 못 받는 경우의 안전망)
ctx._ctrl_shift = lambda: True
STATE.update({"anchorPoint": [300.0, 300.0, 0.0], "dragPoint": [280.0, 300.0, 0.0]})
ctx._press()
ctx._drag()
ctx._release()
ctx._ctrl_shift = lambda: False
check("Ctrl+Shift + drag sets the radius too", abs(mgr.settings["falloff_radius"] - 10.0) < 1e-9 and
      mgr.selection.get(cache.key) == {45.0}, mgr.settings["falloff_radius"])
# 반경 끌기 중에 툴을 나가면 (finalize) 정리
ctx.b_pressed()
STATE.update({"anchorPoint": [300.0, 300.0, 0.0], "dragPoint": [330.0, 300.0, 0.0]})
ctx._press()
ctx._drag()
ctx._finalize()
ctx.b_released()
check("leaving the tool during a radius drag cleans up", ctx.radius_drag is None and not draw_bridge.HUD)
check("no error logged in the context run", not any(m.startswith("[FAIL]") for m in logs),
      [m for m in logs if m.startswith("[FAIL]")])

# ====================================================================== 4. b 키 필터
flt = ec._make_key_filter(ctx)
ctx.is_active = lambda: True
mgr.settings["falloff_on"] = False


def key_event(kind, key=Qt.Key_B, mods=Qt.NoModifier, repeat=False):
    types = {"press": QEvent.KeyPress, "release": QEvent.KeyRelease, "override": QEvent.ShortcutOverride}
    return QKeyEvent(types[kind], key, mods, "", repeat)


ev = key_event("override")
check("filter eats ShortcutOverride B (Maya's b hotkey never runs) and accepts it",
      flt.eventFilter(None, ev) is True and ev.isAccepted())
check("filter eats KeyPress B and marks b held", flt.eventFilter(None, key_event("press")) is True and ctx.b_held)
check("auto-repeat press is eaten but ignored", flt.eventFilter(None, key_event("press", repeat=True)) is True and
      ctx.b_held and not ctx.b_used)
check("filter eats KeyRelease B -> tap = falloff on", flt.eventFilter(None, key_event("release")) is True and
      not ctx.b_held and mgr.settings["falloff_on"])
check("other keys pass", flt.eventFilter(None, key_event("press", key=Qt.Key_W)) is False)
check("Ctrl+B passes (left to Maya)", flt.eventFilter(None, key_event("press", mods=Qt.ControlModifier)) is False)
ctx.is_active = lambda: False
check("B passes when another Maya tool is current", flt.eventFilter(None, key_event("press")) is False and
      not ctx.b_held)
check("mouse / other events pass", flt.eventFilter(None, QEvent(QEvent.MouseMove)) is False)

# ====================================================================== 5. 창
from tools.A00630_MotionPathEditor.app.ui import main_window as mw   # noqa: E402
saved = {k: cmds.optionVar(q=mw.OPTVAR + k) for k in pm.DEFAULT_SETTINGS if cmds.optionVar(exists=mw.OPTVAR + k)}
for k in pm.DEFAULT_SETTINGS:
    cmds.optionVar(remove=mw.OPTVAR + k)
try:
    win = mw.MainWindow()
    win.show()
    app.processEvents()
    check("window: Falloff row starts off, radius 8 fr", not win.cb_falloff.isChecked() and
          win.sp_falloff.value() == 8.0)
    win.tsl_paths.set_items([names["plain"]])
    app.processEvents()
    wc = win.manager.cache_list()[0]
    win.manager.select([(wc, [k for _c, k in win.manager.pickable_frames() if k.t == 62.0][0])], "replace")
    win.cb_falloff.setChecked(True)
    check("window: checking Falloff turns it on, saves it and shows the span",
          win.manager.settings["falloff_on"] and cmds.optionVar(q=mw.OPTVAR + "falloff_on") == 1 and
          "falloff [55, 69]" in win.lbl_selection.text(), win.lbl_selection.text())
    win.sp_falloff.setValue(4.0)
    check("window: radius box -> setting -> span", "falloff [59, 65]" in win.lbl_selection.text() and
          cmds.optionVar(q=mw.OPTVAR + "falloff_radius") == 4.0, win.lbl_selection.text())
    win.manager.settings.update({"falloff_on": False, "falloff_radius": 20.0})
    win._on_context_setting("falloff_radius")
    check("window: settings changed by the viewport (b) show in the boxes and are saved",
          not win.cb_falloff.isChecked() and win.sp_falloff.value() == 20.0 and
          cmds.optionVar(q=mw.OPTVAR + "falloff_radius") == 20.0)
    win.show_falloff_curve()
    app.processEvents()
    dlg = win.curve_dialog
    pts, interp = fcurve.preset_points("Linear")
    dlg.panel.set_curve(pts, interp)
    app.processEvents()
    check("window: the curve popup saves the curve", falloff.curve_from_text(
        win.manager.settings["falloff_curve"])["interp"] == fcurve.INTERP_LINEAR and
        cmds.optionVar(exists=mw.OPTVAR + "falloff_curve"))
    win.close()
    app.processEvents()
    check("window: closing removes the popup and the paths", not draw_bridge.DATA and not dlg.isVisible())
finally:
    for k in pm.DEFAULT_SETTINGS:
        cmds.optionVar(remove=mw.OPTVAR + k)
    for k, v in saved.items():
        if isinstance(v, int):
            cmds.optionVar(intValue=(mw.OPTVAR + k, v))
        elif isinstance(v, float):
            cmds.optionVar(floatValue=(mw.OPTVAR + k, v))
        else:
            cmds.optionVar(stringValue=(mw.OPTVAR + k, v))

mgr.clear()
_common.finish()
