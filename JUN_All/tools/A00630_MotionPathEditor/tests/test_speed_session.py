# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 그래프 Smooth 세션 시험 (속도 그래프 계획서 §6)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_speed_session.py
# 마야로 다시 재서(xform -ws -rp) 확인: 모양 유지 · 키 프레임 유지 · 브러시 밖 불변 · 정지 유지 · undo 한 번 · 레이어 · Whole Pose
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import arc_length as al   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_nodes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_cache as pc   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import speed_session as ss   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)


def track(node, frames):
    return np.array([world_pivot(node, f) for f in frames])


def dist_to_path(points, path):
    """점마다 폴리라인 path 까지 최단 거리."""
    a = path[:-1]
    d = path[1:] - a
    dd = np.maximum((d * d).sum(axis=1), 1e-18)
    out = []
    for p in points:
        t = np.clip(((p - a) * d).sum(axis=1) / dd, 0.0, 1.0)
        out.append(np.linalg.norm(a + d * t[:, None] - p, axis=1).min())
    return np.array(out)


def curves_state(node, attrs=("translateX", "translateY", "translateZ")):
    out = {}
    for at in attrs:
        crv = cmds.listConnections("{0}.{1}".format(node, at), source=True, destination=False, type="animCurve") or []
        if crv:
            out[at] = (tuple(cmds.keyframe(crv[0], q=True, timeChange=True) or ()),
                       tuple(cmds.keyframe(crv[0], q=True, valueChange=True) or ()),
                       tuple(cmds.keyTangent(crv[0], q=True, outAngle=True) or ()))
    return out


def same_state(a, b, tol=1e-9):
    if set(a) != set(b):
        return False
    for k in a:
        for x, y in zip(a[k], b[k]):
            if len(x) != len(y) or any(abs(p - q) > tol for p, q in zip(x, y)):
                return False
    return True


def stroke(s, centers, radius, strength):
    s.begin_stroke()
    for fc in centers:
        s.dab(fc, radius, strength)
    s.end_stroke()


FR = np.arange(1, 121, dtype="float64")

# ====================================================================== 1. 단순 (고정 부모) - 울퉁불퉁한 속도
scenes.new(120)
node = cmds.polyCube(name="bumpy")[0]
for f in (1, 20, 35, 45, 60, 70, 90, 120):
    x = f * 0.2 + (1.5 if f in (35, 60) else 0.0)          # 속도가 들쭉날쭉한 키
    cmds.setKeyframe(node, attribute="translateX", time=f, value=x)
    cmds.setKeyframe(node, attribute="translateY", time=f, value=np.sin(f * 0.05) * 4)
    cmds.setKeyframe(node, attribute="translateZ", time=f, value=0.0)
cache = pc.PathCache(node, 1, 120)
cache.rebake()
orig_track = track(node, FR)
orig_state = curves_state(node)
orig_keys = set(orig_state["translateX"][0])
cmds.flushUndo()
s = ss.StrokeSession(cache)
dense = s.retimer.P.copy()
s.begin_stroke()
for fc in np.linspace(40, 65, 12):
    s.dab(fc, 15.0, 1.0)
check("while painting: curves untouched", same_state(curves_state(node), orig_state))
check("while painting: preview points are on the path", dist_to_path(s.preview_points(), dense).max() < 1e-9)
check("while painting: nothing in the undo queue", cmds.undoInfo(q=True, undoName=True) == "")
check("release writes the stroke", s.end_stroke() and s.report, s.report)
new_track = track(node, FR)
size = al.size(orig_track)
d = dist_to_path(new_track, dense)
check("every frame is still on the original path (shape kept, < 0.2% of size)", d.max() < 0.002 * size, d.max() / size)
moved = np.linalg.norm(new_track - orig_track, axis=1)
check("the frames in the brush moved along the path", moved[45:60].max() > 0.05, moved[45:60].max())
outside = (FR < 23) | (FR > 85)
check("frames outside the brush unchanged (within tolerance / 10)", moved[outside].max() < s.tolerance / 10 + 1e-9,
      (moved[outside].max(), s.tolerance))
now_keys = set(curves_state(node)["translateX"][0])
check("every original key frame kept", orig_keys <= now_keys, sorted(now_keys - orig_keys))
sp0 = al.speed(FR, orig_track, np.arange(45, 61))
sp1 = al.speed(FR, new_track, np.arange(45, 61))
check("speed in the brush is smoother", np.std(sp1) < 0.6 * np.std(sp0), (np.std(sp1), np.std(sp0)))
check("path cache follows (refresh)", np.abs(cache.points[cache.row_of(50)] - new_track[49]).max() < 1e-6)
check("session still valid after its own stroke", s.valid())
first_state = curves_state(node)
first_track = new_track
stroke(s, [27.0], 8.0, 1.0)                     # 지지 19 ~ 35 (첫 획 25 ~ 80 과 앞쪽만 겹친다)
second_track = track(node, FR)
check("second stroke: frames it does not reach stay (no drift, < tol/10)",
      np.linalg.norm(second_track[39:] - first_track[39:], axis=1).max() < s.tolerance / 10 + 1e-9,
      np.linalg.norm(second_track[39:] - first_track[39:], axis=1).max())
check("second stroke changed its own frames", np.linalg.norm(second_track[19:35] - first_track[19:35], axis=1).max() > 1e-3,
      np.linalg.norm(second_track[19:35] - first_track[19:35], axis=1).max())
for _ in range(5):
    stroke(s, [52.0], 12.0, 0.5)
many = track(node, FR)
check("many strokes: still on the original path (no drift, < 0.2%)", dist_to_path(many, dense).max() < 0.002 * size,
      dist_to_path(many, dense).max() / size)
for _ in range(5):
    cmds.undo()
check("each stroke is one undo (5 undos = back before them)", np.abs(track(node, FR) - second_track).max() < 1e-9)
cmds.undo()
check("one more undo = after the first stroke", same_state(curves_state(node), first_state, 1e-9))
cmds.undo()
check("one more undo = the original curves", same_state(curves_state(node), orig_state))
check("and the original motion", np.abs(track(node, FR) - orig_track).max() < 1e-9)
check("after an outside undo the session knows it is stale", not s.valid())
cmds.redo()
check("redo puts the first stroke back", same_state(curves_state(node), first_state, 1e-9))
cmds.undo()

# 놓기 전 취소 · 빈 획
cache.refresh()
s = ss.StrokeSession(cache)
s.begin_stroke()
s.dab(50.0, 20.0, 1.0)
s.drop_stroke()
check("dropped stroke: nothing written", not s.end_stroke() and same_state(curves_state(node), orig_state))
s.begin_stroke()
check("empty stroke: nothing written", not s.end_stroke())

# 키 시간 끌기 (G4) - 포즈 전체, 이웃 키 사이로
cmds.setKeyframe(node, attribute="rotateY", time=45, value=30.0)
cmds.setKeyframe(node, attribute="rotateY", time=1, value=0.0)
cache.refresh()
moved_to = ss.move_key_time(cache, 45.0, 50.0)
keys_x = cmds.keyframe(node + ".translateX", q=True, timeChange=True)
keys_r = cmds.keyframe(node + ".rotateY", q=True, timeChange=True)
check("move key time: translate and rotate keys move together", moved_to == 50.0 and 50.0 in keys_x and 50.0 in keys_r
      and 45.0 not in keys_x, (moved_to, keys_x, keys_r))
clamped = ss.move_key_time(cache, 50.0, 80.0)
check("move key time: stops before the next key (60)", clamped is not None and 59.0 < clamped < 60.0, clamped)
cmds.undo()
cmds.undo()
check("move key time: one undo each", 45.0 in cmds.keyframe(node + ".translateX", q=True, timeChange=True))

# ====================================================================== 2. 정지 유지
scenes.new(120)
hn = cmds.polyCube(name="holder")[0]
for f, v in ((1, 0.0), (25, 6.0), (40, 10.0), (60, 10.0), (80, 18.0), (120, 30.0)):
    cmds.setKeyframe(hn, attribute="translateX", time=f, value=v)
    cmds.setKeyframe(hn, attribute="translateY", time=f, value=v * 0.3)
cmds.keyTangent(hn, attribute=("translateX", "translateY"), time=(40, 60), inTangentType="flat", outTangentType="flat")
cache = pc.PathCache(hn, 1, 120)
cache.rebake()
h0 = track(hn, FR)
s = ss.StrokeSession(cache)
stroke(s, np.linspace(25, 75, 15), 18.0, 1.0)
h1 = track(hn, FR)
check("hold frames 40-60 stay exactly where they were", np.abs(h1[39:60] - h0[39:60]).max() < 2e-3,
      np.abs(h1[39:60] - h0[39:60]).max())
check("motion around the hold changed", np.abs(h1[26:38] - h0[26:38]).max() > 0.01)

# ====================================================================== 3. 회전하는 부모 · 컨스트레인트 계층
names = scenes.hierarchy(120)
node = names["ctrl"]
cache = pc.PathCache(node, 1, 120)
cache.rebake()
t0 = track(node, FR)
orig = curves_state(node)
cmds.flushUndo()
s = ss.StrokeSession(cache)
dense = s.retimer.P.copy()
stroke(s, np.linspace(30, 80, 20), 12.0, 1.0)
t1 = track(node, FR)
size = al.size(t0)
check("hierarchy: on the original path (< 0.5% of size)", dist_to_path(t1, dense).max() < 0.005 * size,
      dist_to_path(t1, dense).max() / size)
check("hierarchy: changed", np.abs(t1 - t0).max() > 1e-3)
cmds.undo()
check("hierarchy: one undo", same_state(curves_state(node), orig))

# ====================================================================== 4. 애니메이션 레이어 - 편집 레이어 커브만
c, _other = scenes.layered(120)
base_before = curves_state(c)
cache = pc.PathCache(c, 1, 120, layer="addL")
cache.rebake()
check("layer: editable", not cache.locked, cache.lock_reason)
l0 = track(c, FR)
s = ss.StrokeSession(cache)
dense = s.retimer.P.copy()
stroke(s, np.linspace(30, 90, 20), 15.0, 1.0)
l1 = track(c, FR)
check("layer: Base curves untouched", same_state(curves_state(c), base_before))
size = al.size(l0)
check("layer: combined motion stays on the path (< 0.5%)", dist_to_path(l1, dense).max() < 0.005 * size,
      dist_to_path(l1, dense).max() / size)
check("layer: changed", np.abs(l1 - l0).max() > 1e-3)
cmds.undo()
check("layer: undo restores the motion", np.abs(track(c, FR) - l0).max() < 1e-9)

# ====================================================================== 5. Whole Pose - 회전도 같은 시간 왜곡
names = scenes.simple(120)
node = names["pivot"]
for f, v in ((1, 0.0), (30, 9.0), (50, 10.0), (90, 25.0), (120, 30.0)):
    cmds.setKeyframe(node, attribute="translateX", time=f, value=v)
cmds.keyTangent(node, attribute="rotateY", inTangentType="linear", outTangentType="linear")
cache = pc.PathCache(node, 1, 120)
cache.rebake()
ry0 = np.array([cmds.getAttr(node + ".rotateY", time=f) for f in FR])
s = ss.StrokeSession(cache, whole_pose=True)
stroke(s, np.linspace(30, 70, 12), 15.0, 1.0)
tau = s.retimer.tau(s.stack[-1], FR)
ry1 = np.array([cmds.getAttr(node + ".rotateY", time=f) for f in FR])
want = np.interp(tau, FR, ry0)
check("Whole Pose: rotateY(f) = old rotateY(tau(f)) (< 0.1 deg)", np.abs(ry1 - want).max() < 0.1, np.abs(ry1 - want).max())
check("Whole Pose: rotation really retimed", np.abs(ry1 - ry0).max() > 0.2, np.abs(ry1 - ry0).max())
cmds.undo()
cache.refresh()
s = ss.StrokeSession(cache, whole_pose=False)
stroke(s, np.linspace(30, 70, 12), 15.0, 1.0)
ry2 = np.array([cmds.getAttr(node + ".rotateY", time=f) for f in FR])
check("without Whole Pose: rotation untouched", np.abs(ry2 - ry0).max() < 1e-9)
cmds.undo()
cache.refresh()

# ====================================================================== 6. 모양 Smooth (G5) · 속도 바꾸기 (G4)
scenes.new(120)
node = cmds.polyCube(name="shaky")[0]
for f in range(1, 121, 3):
    cmds.setKeyframe(node, attribute="translateX", time=f, value=np.cos(f * 0.03) * 20)
    cmds.setKeyframe(node, attribute="translateY", time=f, value=np.sin(f * 0.03) * 20)
    cmds.setKeyframe(node, attribute="translateZ", time=f, value=0.6 * np.sin(f * 1.7))
cache = pc.PathCache(node, 1, 120)
cache.rebake()
k0 = set(curves_state(node)["translateX"][0])
a0 = track(node, FR)
s = ss.StrokeSession(cache, mode=ss.MODE_SHAPE)
for _ in range(4):
    stroke(s, [60.0], 30.0, 1.0)
a1 = track(node, FR)
check("shape: bumps reduced (z wobble in the middle)", np.abs(a1[52:68, 2]).max() < 0.5 * np.abs(a0[52:68, 2]).max(),
      (np.abs(a1[52:68, 2]).max(), np.abs(a0[52:68, 2]).max()))
check("shape: acceleration in the middle lower", al.accel(FR, a1, FR[45:75]).max() < al.accel(FR, a0, FR[45:75]).max())
check("shape: outside the brush unchanged", np.abs(a1[:28] - a0[:28]).max() < 1e-6 and np.abs(a1[93:] - a0[93:]).max() < 1e-6)
check("shape: key frames kept", k0 <= set(curves_state(node)["translateX"][0]))
for _ in range(4):
    cmds.undo()
cache.refresh()
check("shape: 4 undos = back", np.abs(track(node, FR) - a0).max() < 1e-9)
s = ss.StrokeSession(cache)
v_before = al.speed(FR, a0, [60.0])[0]
s.begin_stroke()
s.change_speed(60.0, 0.4 * v_before, 15.0)
s.end_stroke()
a2 = track(node, FR)
check("change speed: faster at 60", al.speed(FR, a2, [60.0])[0] > 1.2 * v_before, (al.speed(FR, a2, [60.0])[0], v_before))
check("change speed: outside the reach unchanged (< tol/10)",
      np.abs(a2[:40] - a0[:40]).max() < s.tolerance / 10 and np.abs(a2[80:] - a0[80:]).max() < s.tolerance / 10)
cmds.undo()

# ====================================================================== 7. 잠긴 경로
names = scenes.hierarchy(120)
cache = pc.PathCache(names["driven"], 1, 120)
cache.rebake()
try:
    ss.StrokeSession(cache)
    check("locked path refuses a session", False)
except RuntimeError as exc:
    check("locked path refuses a session (reason)", "driven" in str(exc), exc)

_common.finish()
