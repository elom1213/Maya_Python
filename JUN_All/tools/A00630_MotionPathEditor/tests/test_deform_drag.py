# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - v01.10 프레임 점 · 폴오프 끌기 (deform) 시험 (매니퓰레이터 · 폴오프 계획서 G2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_deform_drag.py
#
# 가짜 뷰(정면 정사영, 25 px = 1 cm)로 편집 컨텍스트 흐름을 돌리고, 결과는 마야 `xform -ws -rp` 로 프레임마다 다시 잰다.
#   - 세션 deform 모드: set_state → end_stroke = 목표, undo 한 번
#   - 프레임 점 하나 끌기(폴오프 없음) · 폴오프 끌기 · 키 + 폴오프 · 키만(폴오프 끔) = 예전 키 끌기
#   - 끄는 동안 = 미리보기만(커브 그대로) · 오른쪽 버튼 취소 · 안 움직인 클릭 = 아무것도 안 씀
#   - 경로 두 개 = undo 한 번 · 애니메이션 레이어(편집 레이어만) · 축 고정
#   - 플러그인 screen_strips (선을 화면 2D 로 - 카메라 뒤에서 끊기)
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.mel as mel   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from _fake_view import FakeViewState, to_pixel, HALF, W   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import arc_length as al   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_bridge, draw_nodes, falloff, picking   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_manager as pm   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import speed_session as ss   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.watcher import Watcher   # noqa: E402
from tools.A00630_MotionPathEditor.app.plugin import jun_motion_path as plugin_source   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import edit_context as ec   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)
PX = 2.0 * HALF / W                     # 1 px 의 월드 길이 (cm)
FR = np.arange(1, 121, dtype="float64")


def track(node):
    return np.array([world_pivot(node, f) for f in FR])


def curves(node):
    return {at: tuple(cmds.keyframe(node, attribute=at, q=True, valueChange=True) or ())
            for at in ("translateX", "translateY", "translateZ")}


def key_count(node):
    return sum(cmds.keyframe(node, attribute=at, q=True, keyframeCount=True) or 0
               for at in ("translateX", "translateY", "translateZ"))


# ====================================================================== 0. 플러그인: 선을 화면 2D 로
VP = np.diag([0.1, 0.1, 0.1, 0.0])
VP[2, 3] = -1.0                          # w = -z : z < 0 이 카메라 앞
pts = np.array([[0, 0, -5], [1, 0, -5], [2, 0, 5], [3, 0, -5], [4, 0, -5], [5, 0, -5]], dtype="float64")
strips = plugin_source.screen_strips(pts, VP, 200, 100)
check("screen strips: break where the path goes behind the camera", [len(s) for s in strips] == [2, 3],
      [len(s) for s in strips])
check("screen strips: pixel = picking.project", np.allclose(strips[0], picking.project(pts[:2], VP, 200, 100)[0]))
check("screen strips: a lone point makes no line", plugin_source.screen_strips(pts[:1], VP, 200, 100) == [])
loaded = mel.eval('junMotionPathVersion')
loaded = loaded[0] if isinstance(loaded, (list, tuple)) else loaded
check("the loaded plugin is the current one", loaded == plugin_source.PLUGIN_VERSION, loaded)

# ====================================================================== 1. 세션 deform 모드
names = scenes.simple(120)
logs = []
mgr = pm.PathManager(log=logs.append)
watcher = Watcher(mgr)
mgr.set_targets([names["plain"]])
cache = mgr.cache_list()[0]
node = cache.node
before = track(node)
size = al.size(before)
s = ss.StrokeSession(cache, mode=ss.MODE_DEFORM)
w = falloff.weights(cache.times, [45.0], 10.0)
target = cache.points + w[:, None] * np.array([0.0, 2.0, 0.0])
s.begin_stroke()
s.set_state(target)
check("deform session: preview = the target, curves untouched before release",
      np.allclose(s.preview_points(), target) and np.abs(track(node) - before).max() < 1e-12)
s.end_stroke()
after = track(node)
check("deform session: release writes the target (< 0.3% of the path size)",
      np.linalg.norm(after - target, axis=1).max() < 0.003 * size, np.linalg.norm(after - target, axis=1).max())
cmds.undo()
check("deform session: one undo", np.abs(track(node) - before).max() < 1e-9)
mgr.refresh_all()

# ====================================================================== 2. 컨텍스트 흐름
ctx = ec.EditContext(mgr, watcher, log=logs.append)
picking.ViewState = FakeViewState
STATE = {}
ctx._query = lambda flag: STATE[flag]
ctx._ctrl_shift = lambda: False


def frame_pick(c, t):
    return [k for cc, k in mgr.pickable_frames() if cc is c and k.t == t][0]


def key_pick(c, t):
    return [k for k in c.keys if k.t == t][0]


def drag(c, t, dx, dy, release=True):
    x, y = to_pixel(c.points[c.row_of(t)])
    STATE.update({"anchorPoint": [x, y, 0.0], "dragPoint": [x, y, 0.0], "button": 1, "modifier": "none"})
    ctx._press()
    for k in (0.5, 1.0):
        STATE["dragPoint"] = [x + dx * k, y + dy * k, 0.0]
        ctx._drag()
    if release:
        ctx._release()


def expect(w, dx, dy):
    return before + w[:, None] * np.array([dx * PX, dy * PX, 0.0])


# (a) 프레임 점 하나, 폴오프 없음
mgr.settings.update({"falloff_on": False})
mgr.select([(cache, frame_pick(cache, 45.0))], "replace")
n0 = key_count(node)
del logs[:]
drag(cache, 45.0, 0.0, 50.0)
w = falloff.weights(cache.times, [45.0], 0.0)
after = track(node)
check("frame point drag (no falloff): that frame goes 2 cm up",
      np.linalg.norm(after[44] - expect(w, 0, 50)[44]) < 0.003 * size, after[44] - before[44])
check("frame point drag (no falloff): the rest of the path stays (< 0.1% of size)",
      np.abs(np.delete(after - before, 44, axis=0)).max() < 0.001 * size, np.abs(np.delete(after - before, 44, axis=0)).max())
check("frame point drag: keys were added around it, logged with one-step undo",
      key_count(node) > n0 and any(m.startswith("[OK] Moved 1 path point(s) on 1 path(s)") for m in logs), logs[-1:])
cmds.undo()
mgr.refresh_all()
check("frame point drag: one Ctrl+Z puts it back (keys too)", np.abs(track(node) - before).max() < 1e-9 and
      key_count(node) == n0)

# (b) 폴오프 10 fr
mgr.settings.update({"falloff_on": True, "falloff_radius": 10.0})
drag(cache, 45.0, 30.0, 40.0)
w = mgr.weights_for(cache)
after = track(node)
err = np.linalg.norm(after - expect(w, 30, 40), axis=1)
check("falloff drag: every frame moves by its weight (< 0.3% of size)", err.max() < 0.003 * size, err.max())
outside = w <= 0
check("falloff drag: frames outside the falloff stay (< 0.1%)",
      np.abs(after[outside] - before[outside]).max() < 0.001 * size, np.abs(after[outside] - before[outside]).max())
check("falloff drag: half way in the radius moves about half",
      0.3 < np.linalg.norm(after[49] - before[49]) / np.linalg.norm(after[44] - before[44]) < 0.7)
check("falloff drag: the log says the falloff", any("(falloff 10 fr)" in m for m in logs), logs[-1:])
cmds.undo()
mgr.refresh_all()
check("falloff drag: one undo", np.abs(track(node) - before).max() < 1e-9)

# (c) 키 + 폴오프 → deform (키 60, 이웃 프레임도 따라온다)
mgr.select([(cache, key_pick(cache, 60.0))], "replace")
drag(cache, 60.0, 0.0, -25.0, release=False)
check("key + falloff -> deform, not the old key drag", ctx.deform is not None and ctx.session is None)
ctx._release()
w = mgr.weights_for(cache)
after = track(node)
check("key + falloff: the key and its neighbours follow by weight",
      np.linalg.norm(after - expect(w, 0, -25), axis=1).max() < 0.003 * size)
cmds.undo()
mgr.refresh_all()

# (d) 키만 + 폴오프 끔 → 예전 키 끌기 (DragSession, 오브젝트가 끄는 동안 바로 따라옴)
mgr.settings["falloff_on"] = False
drag(cache, 60.0, 0.0, -25.0, release=False)
check("keys only, falloff off -> the old key drag (live)", ctx.session is not None and ctx.deform is None)
ctx._release()
cmds.undo()
mgr.refresh_all()
mgr.settings["falloff_on"] = True

# (e) 끄는 동안 = 미리보기만, 오른쪽 버튼 = 취소
mgr.select([(cache, frame_pick(cache, 45.0))], "replace")
crv0 = curves(node)
drag(cache, 45.0, 40.0, 40.0, release=False)
data = draw_bridge.DATA[cache.key]
check("while dragging: preview path + grey original, curves not written yet",
      cache.key in mgr.preview and len(data["ghost"]) > 1 and curves(node) == crv0 and
      np.abs(np.asarray(data["line"]) - before).max() > 0.5)
STATE["button"] = 3
ctx._press()
check("right mouse cancels: no change, preview gone, no undo entry added",
      ctx.deform is None and curves(node) == crv0 and cache.key not in mgr.preview and
      len(draw_bridge.DATA[cache.key]["ghost"]) == 0 and any(m == "[Info] Drag cancelled." for m in logs))

# (f) 안 움직인 클릭 = 아무것도 안 씀
cmds.flushUndo()
drag(cache, 45.0, 0.0, 0.0)
check("a click without moving writes nothing and adds no undo", curves(node) == crv0 and
      not cmds.undoInfo(q=True, undoName=True))

# (g) 축 고정 (Y 만)
mgr.settings["plane"] = picking.AXIS_Y
drag(cache, 45.0, 60.0, 30.0)
d = track(node) - before
check("Drag in Y: the falloff moves only along Y", np.abs(d[:, 0]).max() < 0.001 * size and
      np.abs(d[:, 2]).max() < 1e-6 and d[:, 1].max() > 0.5, (np.abs(d[:, 0]).max(), d[:, 1].max()))
cmds.undo()
mgr.refresh_all()
mgr.settings["plane"] = picking.PLANE_VIEW

# (h) 경로 두 개 = undo 한 번
mgr.set_targets([names["plain"], names["opm"]])
c2 = [c for c in mgr.cache_list() if c.node.endswith("opmCube")][0]
before2 = np.array([world_pivot(c2.node, f) for f in FR])
mgr.select([(cache, frame_pick(cache, 45.0)), (c2, frame_pick(c2, 45.0))], "replace")
drag(cache, 45.0, 0.0, 50.0)
moved1 = np.abs(track(node) - before).max()
moved2 = np.abs(np.array([world_pivot(c2.node, f) for f in FR]) - before2).max()
check("two paths move together", moved1 > 0.5 and moved2 > 0.5, (moved1, moved2))
cmds.undo()
check("two paths: one Ctrl+Z puts both back", np.abs(track(node) - before).max() < 1e-9 and
      np.abs(np.array([world_pivot(c2.node, f) for f in FR]) - before2).max() < 1e-9)
mgr.refresh_all()
check("no error logged", not any(m.startswith("[FAIL]") for m in logs), [m for m in logs if m.startswith("[FAIL]")])
mgr.clear()

# ====================================================================== 3. 애니메이션 레이어
c, _other = scenes.layered(120)
logs2 = []
mgr2 = pm.PathManager(log=logs2.append)
mgr2.settings["edit_layer"] = "addL"
mgr2.set_targets([c])
lc = mgr2.cache_list()[0]
ctx = ec.EditContext(mgr2, Watcher(mgr2), log=logs2.append)
ctx._query = lambda flag: STATE[flag]
ctx._ctrl_shift = lambda: False
mgr = mgr2
base0 = curves(c)
lb = np.array([world_pivot(c, f) for f in FR])
mgr2.settings.update({"falloff_on": True, "falloff_radius": 12.0})
mgr2.select([(lc, frame_pick(lc, 50.0))], "replace")
drag(lc, 50.0, 0.0, 25.0)
la = np.array([world_pivot(c, f) for f in FR])
w = mgr2.weights_for(lc)
lerr = np.linalg.norm(la - (lb + w[:, None] * np.array([0.0, 25 * PX, 0.0])), axis=1).max()
check("layer: the combined motion follows by weight (< 0.3%)", lerr < 0.003 * al.size(lb), lerr)
check("layer: Base curves untouched (only the edit layer is written)", curves(c) == base0)
cmds.undo()
check("layer: one undo", np.abs(np.array([world_pivot(c, f) for f in FR]) - lb).max() < 1e-9)
check("layer: no error logged", not any(m.startswith("[FAIL]") for m in logs2), logs2)
mgr2.clear()
_common.finish()
