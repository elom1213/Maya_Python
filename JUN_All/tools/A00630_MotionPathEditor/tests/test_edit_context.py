# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 편집 컨텍스트 흐름 시험 (누름 → 끌기 → 놓기, 박스 선택) - v01.01
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_edit_context.py
#
# draggerContext 와 3D 뷰는 헤드리스에 없다. 그래서
#   - 컨텍스트 질의(_query: anchorPoint / dragPoint / button / modifier)를 정해 둔 값으로 바꾸고
#   - 뷰(ViewState)를 "정면에서 내려다보는 정사영 카메라" 가짜로 바꾼다. 가짜 M3dView 의 viewToWorld 는
#     **마야 2024 와 같은 모양**(x, y, worldPt, worldVector 를 받아 OUT 인자를 채움)이라, v01.00 의
#     "function takes exactly 4 arguments (2 given)" 같은 호출 실수는 여기서 잡힌다.
# 그 밖의 코드(고르기 · 세션 · undo · 그리기 데이터)는 GUI 와 똑같이 돈다.
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.api.OpenMaya as om   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_bridge, draw_nodes, picking   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.path_manager import PathManager   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.watcher import Watcher   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import edit_context as ec   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)

from _fake_view import (CX, CY, FakeM3dView, FakeViewState, H, HALF, W,   # noqa: E402,F401
                         to_pixel, to_world_xy)


# ---- 장면 + 관리자 + 컨텍스트 (질의와 뷰만 가짜)
names = scenes.hierarchy(120)
logs = []
mgr = PathManager(log=logs.append)
watcher = Watcher(mgr)
mgr.set_targets([names["ctrl"]])
ctx = ec.EditContext(mgr, watcher, log=logs.append)
picking.ViewState = FakeViewState        # edit_context 는 picking.ViewState() 를 부른다
STATE = {}
ctx._query = lambda flag: STATE[flag]

cache = mgr.cache_list()[0]

# view_ray : 마야 2024 모양으로 불린다
o, d = picking.view_ray(FakeM3dView(), 500, 400, [0, 0, -1])
check("view_ray calls viewToWorld with OUT arguments and returns a unit ray",
      np.allclose(o, [0.0, 0.0, 100.0]) and np.allclose(d, [0.0, 0.0, -1.0]), (o, d))

# ---- 키 하나 클릭해서 끌기
key = cache.keys[2]
p0 = cache.points[key.row].copy()
x0, y0 = to_pixel(p0)
x1, y1 = x0 + 60.0, y0 - 25.0
STATE.update({"anchorPoint": [x0, y0, 0.0], "dragPoint": [x0, y0, 0.0], "button": 1, "modifier": "none"})
cmds.flushUndo()
ctx._press()
check("press on a key selects it and starts a drag", ctx.session is not None and
      mgr.selection.get(cache.key) == {key.t}, logs)
for step in (0.3, 0.7, 1.0):
    STATE["dragPoint"] = [x0 + (x1 - x0) * step, y0 + (y1 - y0) * step, 0.0]
    ctx._drag()
check("dragging raised no error", not any(m.startswith("[FAIL]") for m in logs), logs)
target = to_world_xy(x1, y1, p0[2])          # View 평면 = 키를 지나고 카메라(-Z)에 수직 → z 는 그대로
check("the key follows the mouse in the view plane", np.abs(cache.points[key.row] - target).max() < 1e-6,
      (cache.points[key.row], target))
ctx._release()
check("release commits and logs it", any(m.startswith("[OK] Moved 1 key(s)") for m in logs) and ctx.session is None,
      logs)
check("Maya's own pivot is at the dropped place", np.abs(np.array(world_pivot(cache.node, key.t)) - target).max() < 1e-6)
cmds.undo()
mgr.refresh_all()
check("one Ctrl+Z puts it back", np.abs(np.array(world_pivot(cache.node, key.t)) - p0).max() < 1e-6)

# ---- 축 고정 (Y 만)
mgr.settings["plane"] = picking.AXIS_Y
p0 = cache.points[key.row].copy()
x0, y0 = to_pixel(p0)
STATE.update({"anchorPoint": [x0, y0, 0.0], "dragPoint": [x0 + 80.0, y0 + 40.0, 0.0], "modifier": "none"})
ctx._press()
ctx._drag()
ctx._release()
moved = cache.points[key.row] - p0
check("Drag in Y moves only along Y", abs(moved[0]) < 1e-9 and abs(moved[2]) < 1e-9 and abs(moved[1]) > 0.1, moved)
cmds.undo()
mgr.refresh_all()
mgr.settings["plane"] = picking.PLANE_VIEW

# ---- 박스 선택 → 고른 키 하나를 끌면 모두 함께
# v01.09 - 박스는 프레임 점도 고른다. 여기서는 키만 끄는 기존 동작을 보므로 프레임 점 표시를 끈다(안 보이면 안 고른다)
mgr.settings["show_dots"] = False
pts = [cache.points[k.row] for k in cache.keys]
pix = [to_pixel(p) for p in pts]
xs = sorted(px for px, _py in pix)
ys = sorted(py for _px, py in pix)
STATE.update({"anchorPoint": [xs[0] - 5, ys[0] - 5, 0.0], "dragPoint": [xs[-1] + 5, ys[-1] + 5, 0.0],
              "modifier": "none"})
ctx._press()
check("press on empty space starts a box", ctx.box is not None and ctx.session is None)
ctx._drag()
check("the box is handed to the drawing (HUD)", "box" in draw_bridge.HUD)
ctx._release()
check("box selects every key inside", mgr.selected_count() == len(cache.keys), mgr.selected_count())
check("the box disappears after release", not draw_bridge.HUD)
starts = {k.t: cache.points[k.row].copy() for k in cache.keys}
k0 = cache.keys[0]
x0, y0 = to_pixel(starts[k0.t])
STATE.update({"anchorPoint": [x0, y0, 0.0], "dragPoint": [x0 + 30.0, y0 + 30.0, 0.0], "modifier": "none"})
ctx._press()
check("press on an already selected key keeps the whole selection", mgr.selected_count() == len(cache.keys))
ctx._drag()
ctx._release()
# 끄는 기준은 누른 자리에서 가장 가까운 키다(정면 정사영이라 이웃 키가 10 픽셀 안에 겹칠 수 있다) - 그래서
# "모든 키가 **같은 양**만큼, 화면 평면(z 그대로) 안에서 움직였다" 를 본다.
moves = [cache.points[k.row] - starts[k.t] for k in cache.keys]
same = max(np.abs(m - moves[0]).max() for m in moves)
check("all selected keys moved together by the same amount", same < 1e-6 and np.linalg.norm(moves[0]) > 0.5 and
      abs(moves[0][2]) < 1e-9, (same, moves[0]))
cmds.undo()
mgr.refresh_all()

mgr.settings["show_dots"] = True

# ---- Shift / Ctrl 클릭, 빈 곳 클릭 = 해제
k1, k3 = cache.keys[1], cache.keys[3]
mgr.select([], "replace")
for k, mod in ((k1, "none"), (k3, "shift")):
    x, y = to_pixel(cache.points[k.row])
    STATE.update({"anchorPoint": [x, y, 0.0], "dragPoint": [x, y, 0.0], "modifier": mod})
    ctx._press()
    ctx._release()
check("Shift + click adds a key", mgr.selection.get(cache.key) == {k1.t, k3.t}, mgr.selection)
x, y = to_pixel(cache.points[k1.row])
STATE.update({"anchorPoint": [x, y, 0.0], "dragPoint": [x, y, 0.0], "modifier": "ctrl"})
ctx._press()
ctx._release()
check("Ctrl + click removes it", mgr.selection.get(cache.key) == {k3.t}, mgr.selection)
STATE.update({"anchorPoint": [5.0, 5.0, 0.0], "dragPoint": [5.0, 5.0, 0.0], "modifier": "none"})
ctx._press()
ctx._release()
check("click on empty space clears the selection", mgr.selected_count() == 0)

# ---- 오른쪽 버튼 = 끄는 중 취소
p0 = cache.points[key.row].copy()
x0, y0 = to_pixel(p0)
STATE.update({"anchorPoint": [x0, y0, 0.0], "dragPoint": [x0 + 50.0, y0, 0.0], "button": 1, "modifier": "none"})
ctx._press()
ctx._drag()
STATE["button"] = 3
ctx._press()
check("right mouse during a drag cancels it", ctx.session is None and
      np.abs(np.array(world_pivot(cache.node, key.t)) - p0).max() < 1e-6)
check("no error logged in the whole run", not any(m.startswith("[FAIL]") for m in logs),
      [m for m in logs if m.startswith("[FAIL]")])

mgr.clear()
_common.finish()
