# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - v01.11 매니퓰레이터 시험 (매니퓰레이터 · 폴오프 계획서 G3)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_gizmo.py
#
# 1. gizmo 수학 (가짜 원근 카메라): 고르기 · 화면 크기 고정 · 축 / 평면 이동 · 고리 각도 · 가중 회전 · Path 축 · 시선 방향
# 2. 편집 컨텍스트 흐름 (가짜 정사영 뷰, 25 px = 1 cm): 화살표 끌기 · 키만 = 예전 끌기 · 폴오프 회전 · Shift 클릭은 점 ·
#    끄는 동안 기즈모가 따라감 · 각도 글자 · 취소 · undo 한 번 · 켜고 끌 때 그리기 데이터
# 3. w / e 키 필터 · 창 라디오 · 플러그인 그리기(가짜 DM) · 플러그인 버전
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
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from _fake_view import FakeViewState, to_pixel, HALF, W   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import arc_length as al   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_bridge, draw_nodes, picking   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import gizmo as gz   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_manager as pm   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.watcher import Watcher   # noqa: E402
from tools.A00630_MotionPathEditor.app.plugin import jun_motion_path as jp   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import edit_context as ec   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)

# ====================================================================== 1. 수학 (가짜 원근 카메라)
WP, HP = 800, 600
FOV = np.radians(54.43)
CAM = np.array([6.0, 5.0, 20.0])
f = -CAM / np.linalg.norm(CAM)
r = np.cross(f, [0.0, 1.0, 0.0])
r /= np.linalg.norm(r)
u = np.cross(r, f)
VIEW = np.eye(4)
VIEW[:3, 0], VIEW[:3, 1], VIEW[:3, 2] = r, u, -f
VIEW[3, :3] = [-(CAM @ r), -(CAM @ u), (CAM @ f)]
fy = 1.0 / np.tan(FOV / 2.0)
PROJ = np.zeros((4, 4))
PROJ[0, 0], PROJ[1, 1] = fy / (WP / float(HP)), fy
PROJ[2, 2], PROJ[2, 3], PROJ[3, 2] = (1000.1) / (0.1 - 1000.0), -1.0, 2.0 * 1000.0 * 0.1 / (0.1 - 1000.0)
VP = VIEW @ PROJ


def ray(x, y):
    d = f + r * (x / WP * 2.0 - 1.0) / PROJ[0, 0] + u * (y / HP * 2.0 - 1.0) / PROJ[1, 1]
    return CAM.copy(), d / np.linalg.norm(d)


def px_of(p):
    return gz.project([p], VP, WP, HP)[0][0]


check("view_dir from view_proj = the camera direction", np.allclose(gz.view_dir(VP), f, atol=1e-6), gz.view_dir(VP))
pivot = np.array([1.0, 0.5, -2.0])
I = np.eye(3)
L = gz.SIZE_PX * gz.world_per_px(pivot, VP, WP, HP)
tip = px_of(pivot + I[0] * L * 0.9)
check("hit: near the X arrow -> x", gz.hit(pivot, I, gz.MODE_MOVE, VP, WP, HP, tip[0] + 2, tip[1] - 2) == "x")
mid = px_of(pivot + I[1] * L * 0.6)
check("hit: Y arrow -> y", gz.hit(pivot, I, gz.MODE_MOVE, VP, WP, HP, *mid) == "y")
c = px_of(pivot)
check("hit: the centre -> center (screen plane)", gz.hit(pivot, I, gz.MODE_MOVE, VP, WP, HP, *c) == "center")
q = px_of(pivot + (I[0] + I[1]) * L * 0.35)
check("hit: inside the XY square -> xy", gz.hit(pivot, I, gz.MODE_MOVE, VP, WP, HP, *q) == "xy")
check("hit: empty space -> None", gz.hit(pivot, I, gz.MODE_MOVE, VP, WP, HP, c[0] + 200, c[1] + 200) is None)
far = pivot + f * 30.0
lens = [np.linalg.norm(px_of(p + I[1] * gz.SIZE_PX * gz.world_per_px(p, VP, WP, HP)) - px_of(p)) for p in (pivot, far)]
check("size: about SIZE_PX on screen, near and far", all(abs(x - gz.SIZE_PX) / gz.SIZE_PX < 0.15 for x in lens), lens)
o0, d0 = ray(*tip)
o1, d1 = ray(tip[0] + 40, tip[1] + 25)
a0 = gz.move_point("x", pivot, I, o0, d0, gz.view_dir(VP))
a1 = gz.move_point("x", pivot, I, o1, d1, gz.view_dir(VP))
check("move x: only along X", np.allclose((a1 - a0)[1:], 0.0) and abs(a1[0] - a0[0]) > 1e-3, a1 - a0)
p0 = gz.move_point("xy", pivot, I, *ray(*q), gz.view_dir(VP))
p1 = gz.move_point("xy", pivot, I, *ray(q[0] + 30, q[1] - 10), gz.view_dir(VP))
check("move xy: stays in the XY plane (z fixed)", abs(p1[2] - pivot[2]) < 1e-9 and abs(p0[2] - pivot[2]) < 1e-9)
geo = dict(gz.geometry(pivot, I, gz.MODE_ROTATE, L, gz.view_dir(VP)))
for name, axis in (("rx", 0), ("ry", 1), ("rz", 2)):
    ring = geo[name]
    i0, i1 = 5, 5 + 16                       # 64 조각 중 16 = 90도
    on0, on1 = ring[i0], ring[i1]
    sp0, sp1 = px_of(on0), px_of(on1)
    hit_part = gz.hit(pivot, I, gz.MODE_ROTATE, VP, WP, HP, *sp0)
    ang = np.degrees(gz.rotate_angle(name, pivot, I, gz.view_dir(VP), ray(*sp0), ray(*sp1), VP, WP, HP, sp0, sp1))
    want = np.degrees(np.arctan2(np.cross(on0 - pivot, on1 - pivot) @ I[axis], (on0 - pivot) @ (on1 - pivot)))
    check("rotate {0}: picked, drag along the ring = the ring angle ({1:.1f} deg)".format(name, want),
          hit_part == name and abs(ang - want) < 1.0, (hit_part, ang))
P = np.array([[2.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
R = gz.rotate_points(P, np.zeros(3), [0, 0, 1], np.radians(90.0), np.array([1.0, 0.5]))
check("rotate points: weight 1 = full angle, 0.5 = half", np.allclose(R[0], [0, 2, 0]) and
      np.allclose(R[1], [3 * np.cos(np.pi / 4), 3 * np.sin(np.pi / 4), 0]), R)
path = np.array([[0, 0, 0], [1, 0, 0], [2, 0.5, 0], [3, 1.5, 0]], dtype="float64")
F = gz.path_frame(path, 2)
check("path frame: orthonormal, X along the path, Y up-ish", np.allclose(F @ F.T, np.eye(3), atol=1e-9) and
      F[0] @ np.array([1.0, 0.75, 0]) / 1.25 > 0.99 and F[1][1] > 0.5, F)
check("path frame: a stopped path falls back to world", np.allclose(gz.path_frame(np.zeros((3, 3)), 1), np.eye(3)))

# ====================================================================== 2. 컨텍스트 흐름 (정사영 25 px = 1 cm)
PX = 2.0 * HALF / W
names = scenes.simple(120)
logs = []
mgr = pm.PathManager(log=logs.append)
watcher = Watcher(mgr)
mgr.set_targets([names["plain"]])
cache = mgr.cache_list()[0]
node = cache.node
ctx = ec.EditContext(mgr, watcher, log=logs.append)
picking.ViewState = FakeViewState
STATE = {}
ctx._query = lambda flag: STATE[flag]
ctx._ctrl_shift = lambda: False
mgr.gizmo_on = True
FR = np.arange(1, 121, dtype="float64")
VPF = FakeViewState().view_proj


def track():
    return np.array([world_pivot(node, fr) for fr in FR])


def frame_pick(t):
    return [k for _c, k in mgr.pickable_frames() if k.t == t][0]


def gizmo_px(part):
    frame = mgr.gizmo_frame()
    pv, ax = frame
    length = gz.SIZE_PX * gz.world_per_px(pv, VPF, W, 800)
    geo = dict(gz.geometry(pv, ax, mgr.settings["manip_mode"], length, gz.view_dir(VPF)))
    return geo, length


def drag(x, y, dx, dy, release=True, steps=(0.5, 1.0), modifier="none"):
    x, y = float(int(x)), float(int(y))         # 가짜 뷰 광선은 정수 픽셀 - 시작을 정수로 두면 이동량이 정확히 dx
    STATE.update({"anchorPoint": [x, y, 0.0], "dragPoint": [x, y, 0.0], "button": 1, "modifier": modifier})
    ctx._press()
    for k in steps:
        STATE["dragPoint"] = [x + dx * k, y + dy * k, 0.0]
        ctx._drag()
    if release:
        ctx._release()


before = track()
size = al.size(before)
mgr.settings.update({"falloff_on": False, "manip_mode": "move", "manip_axes": "world"})
mgr.select([(cache, frame_pick(45.0))], "replace")
mgr.redraw()
check("gizmo drawn at the selected point while the tool is on",
      draw_bridge.GIZMO.get("owner") == cache.key and np.allclose(draw_bridge.GIZMO["pivot"], cache.points[44]))
geo, length = gizmo_px("x")
sx, sy = gz.project([geo["x"][-1] - (geo["x"][-1] - geo["x"][0]) * 0.2], VPF, W, 800)[0][0]
drag(sx, sy, 50.0, 30.0, release=False)
check("press on the X arrow starts a gizmo drag (not a box, selection kept)",
      ctx.gizmo_drag is not None and ctx.box is None and mgr.selection[cache.key] == {45.0} and
      draw_bridge.GIZMO.get("active") == "x")
check("while dragging the gizmo follows the point", abs(draw_bridge.GIZMO["pivot"][0] - (cache.points[44][0] + 50 * PX)) < 1e-6)
ctx._release()
after = track()
check("X arrow: the frame moves 2 cm along X only (vertical mouse ignored)",
      abs(after[44][0] - before[44][0] - 50 * PX) < 0.003 * size and abs(after[44][1] - before[44][1]) < 0.003 * size,
      after[44] - before[44])
check("gizmo drag state cleared after release", ctx.gizmo_drag is None and draw_bridge.GIZMO.get("active") is None)
cmds.undo()
mgr.refresh_all()
check("one undo", np.abs(track() - before).max() < 1e-9)

# 키만 + 폴오프 끔 → 예전 키 끌기 (Y 화살표)
mgr.select([(cache, [k for k in cache.keys if k.t == 60.0][0])], "replace")
mgr.redraw()
geo, length = gizmo_px("y")
sx, sy = gz.project([geo["y"][0] + (geo["y"][-1] - geo["y"][0]) * 0.6], VPF, W, 800)[0][0]
drag(sx, sy, 20.0, 25.0, release=False)
check("keys only + falloff off: the gizmo uses the live key drag", ctx.session is not None and ctx.deform is None)
ctx._release()
after = track()
check("Y arrow on a key: the key moves 1 cm up only", abs(after[59][1] - before[59][1] - 25 * PX) < 1e-6 and
      abs(after[59][0] - before[59][0]) < 1e-6, after[59] - before[59])
cmds.undo()
mgr.refresh_all()

# 폴오프 회전 (Z 고리 - 정면에서 보이는 고리): 고른 두 점(40, 50)의 가운데 둘레로
mgr.settings.update({"falloff_on": True, "falloff_radius": 10.0, "manip_mode": "rotate"})
mgr.select([(cache, frame_pick(40.0)), (cache, frame_pick(50.0))], "replace")
mgr.redraw()
geo, length = gizmo_px("rz")
pv = mgr.gizmo_frame()[0]
ring = geo["rz"]
sp0 = gz.project([ring[3]], VPF, W, 800)[0][0]
sp1 = gz.project([ring[3 + 4]], VPF, W, 800)[0][0]       # 4/64 바퀴 = 22.5도
want = np.arctan2(np.cross(ring[3] - pv, ring[7] - pv)[2], (ring[3] - pv) @ (ring[7] - pv))
drag(sp0[0], sp0[1], sp1[0] - sp0[0], sp1[1] - sp0[1], release=False, steps=(1.0,))
ang = ctx.gizmo_drag["angle"]
check("rotate: dragging along the Z ring = the ring angle (pixel rounding < 1 deg)",
      abs(np.degrees(ang - want)) < 1.0, (np.degrees(ang), np.degrees(want)))
check("rotate: the angle shows next to the cursor", draw_bridge.HUD.get("text", (0, 0, ""))[2] ==
      "{0:+.1f} deg".format(np.degrees(ang)), draw_bridge.HUD.get("text"))
check("rotate: preview only while dragging", cache.key in mgr.preview and np.abs(track() - before).max() < 1e-12)
ctx._release()
w = mgr.weights_for(cache)
target = gz.rotate_points(before, pv, [0, 0, 1], ang, w)
after = track()
err = np.linalg.norm(after - target, axis=1).max()
check("rotate: every frame turns by weight x angle around the centre (< 0.3%)", err < 0.003 * size, err)
check("rotate: frames outside the falloff stay", np.abs((after - before)[w <= 0]).max() < 0.001 * size)
cmds.undo()
mgr.refresh_all()
check("rotate: one undo", np.abs(track() - before).max() < 1e-9)

# 오른쪽 버튼 = 취소, Shift 클릭은 기즈모가 아니라 점
drag(sp0[0], sp0[1], sp1[0] - sp0[0], sp1[1] - sp0[1], release=False, steps=(1.0,))
STATE["button"] = 3
ctx._press()
check("right mouse cancels a gizmo drag", ctx.gizmo_drag is None and ctx.deform is None and
      cache.key not in mgr.preview and "text" not in draw_bridge.HUD and np.abs(track() - before).max() < 1e-12)
mgr.settings["manip_mode"] = "move"
mgr.redraw()
geo, length = gizmo_px("x")
cx, cy = gz.project([mgr.gizmo_frame()[0]], VPF, W, 800)[0][0]
x45, y45 = to_pixel(cache.points[44])
STATE.update({"anchorPoint": [x45, y45, 0.0], "dragPoint": [x45, y45, 0.0], "button": 1, "modifier": "shift"})
ctx._press()
ctx._release()
check("Shift + click on the gizmo still picks points", ctx.gizmo_drag is None and 45.0 in mgr.selection[cache.key])
# 가운데 사각형 = 고른 점을 그냥 끄는 것 → Drag in 을 따른다 (고른 점 위를 누르면 늘 가운데가 잡힌다)
mgr.settings.update({"plane": picking.AXIS_Y, "falloff_on": False})
mgr.select([(cache, frame_pick(45.0))], "replace")
mgr.redraw()
x45, y45 = to_pixel(cache.points[44])
drag(x45, y45, 60.0, 40.0, release=False)
check("press on the selected point = the gizmo centre", ctx.gizmo_drag is not None and ctx.gizmo_drag["part"] == "center")
ctx._release()
d = track() - before
check("centre drag follows Drag in = Y: the point moves along Y only", abs(d[44][0]) < 0.003 * size and
      abs(d[44][1] - 40 * PX) < 0.003 * size, d[44])
cmds.undo()
mgr.refresh_all()
mgr.settings["plane"] = picking.PLANE_VIEW
# Path 축
mgr.settings["manip_axes"] = "path"
mgr.select([(cache, frame_pick(45.0))], "replace")
mgr.redraw()
ax = draw_bridge.GIZMO["axes"]
tangent = cache.points[45] - cache.points[43]
check("Path axes: X follows the path", ax[0] @ (tangent / np.linalg.norm(tangent)) > 0.999, ax[0])
mgr.settings["manip_axes"] = "world"
# 툴을 끄면 기즈모도 사라진다
mgr.gizmo_on = False
mgr.redraw()
check("tool off -> no gizmo", not draw_bridge.GIZMO)
mgr.gizmo_on = True
mgr.redraw()
check("no error logged", not any(m.startswith("[FAIL]") for m in logs), [m for m in logs if m.startswith("[FAIL]")])

# ====================================================================== 3. 키 필터 · 플러그인 · 창
flt = ec._make_key_filter(ctx)
ctx.is_active = lambda: True
seen = []
ctx.on_setting = seen.append


def key_event(kind, key, mods=Qt.NoModifier):
    types = {"press": QEvent.KeyPress, "release": QEvent.KeyRelease, "override": QEvent.ShortcutOverride}
    return QKeyEvent(types[kind], key, mods, "", False)


check("e is eaten (Maya's Rotate tool hotkey never runs) and switches to Rotate",
      flt.eventFilter(None, key_event("override", Qt.Key_E)) is True and
      flt.eventFilter(None, key_event("press", Qt.Key_E)) is True and mgr.settings["manip_mode"] == "rotate" and
      seen == ["manip_mode"])
check("w switches back to Move", flt.eventFilter(None, key_event("press", Qt.Key_W)) is True and
      mgr.settings["manip_mode"] == "move")
check("releases are eaten too", flt.eventFilter(None, key_event("release", Qt.Key_W)) is True)
check("Shift+W passes (left to Maya)", flt.eventFilter(None, key_event("press", Qt.Key_W, Qt.ShiftModifier)) is False)
ctx.is_active = lambda: False
check("w passes when another tool is current", flt.eventFilter(None, key_event("press", Qt.Key_W)) is False)


class FakeDM(object):
    kNonSelectable = kPoints = kLineStrip = kLeft = kDashed = kSolid = kDefaultFontSize = 0

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def call(*a, **k):
            self.calls.append(name)
        return call


dm = FakeDM()
jp.JunMotionPathDrawOverride._draw_gizmo(dm, dict(draw_bridge.GIZMO), VPF, W, 800)
# 정면 정사영이라 Z 화살표는 화면 길이 0 - 머리는 X · Y 둘(선 4개)만
check("plugin draws the gizmo (2D lines + arrow heads, none for an arrow pointing at the camera)",
      dm.calls.count("mesh2d") >= 7 and dm.calls.count("line2d") == 4,
      (dm.calls.count("mesh2d"), dm.calls.count("line2d")))
loaded = mel.eval("junMotionPathVersion")
loaded = loaded[0] if isinstance(loaded, (list, tuple)) else loaded
check("the loaded plugin is the current one", loaded == jp.PLUGIN_VERSION, loaded)
mgr.clear()

from tools.A00630_MotionPathEditor.app.ui import main_window as mw   # noqa: E402
saved = {k: cmds.optionVar(q=mw.OPTVAR + k) for k in pm.DEFAULT_SETTINGS if cmds.optionVar(exists=mw.OPTVAR + k)}
for k in pm.DEFAULT_SETTINGS:
    cmds.optionVar(remove=mw.OPTVAR + k)
try:
    win = mw.MainWindow()
    win.show()
    app.processEvents()
    checked = [b.property("manip") for b in win.manip_buttons.buttons() if b.isChecked()]
    check("window: Manipulator starts on Move, World axes", checked == ["move"] and
          [b.property("axes") for b in win.axes_buttons.buttons() if b.isChecked()] == ["world"])
    [b for b in win.axes_buttons.buttons() if b.property("axes") == "path"][0].click()
    check("window: Axes Path saved", win.manager.settings["manip_axes"] == "path" and
          cmds.optionVar(q=mw.OPTVAR + "manip_axes") == "path")
    win.manager.settings["manip_mode"] = "rotate"
    win._on_context_setting("manip_mode")
    check("window: e in the viewport shows as Rotate and is saved",
          [b.property("manip") for b in win.manip_buttons.buttons() if b.isChecked()] == ["rotate"] and
          cmds.optionVar(q=mw.OPTVAR + "manip_mode") == "rotate")
    win.close()
    app.processEvents()
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
_common.finish()
