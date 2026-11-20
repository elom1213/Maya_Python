# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 매니퓰레이터 · 폴오프 계획서 G0 실측 (헤드리스 부분: G0-3 일부 · G0-4 · G0-5)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u bench_g0_manip_falloff.py
# GUI 부분(G0-1 점마다 색 · G0-2 b 키)은 g0_gui_probe.py 를 마야 GUI 에서.
#
# G0-5 : 기존 StrokeSession(모드 shape - 상태 = cache.times 의 월드 점) 에 **목표 경로를 그대로 넣고** end_stroke 하면
#        deform(폴오프 이동 · 회전)이 되는지 - 계획서 §3-3 의 "set_state 하나만 붙인다" 가 맞는지 잰다.
# G0-4 : 기즈모 고르기 · 끌기 수학 시제품 (가짜 원근 카메라, picking.project 와 같은 행 벡터 규약).
import time

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.api.OpenMayaRender as omr   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import arc_length as al   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_nodes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_cache as pc   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import picking as pk   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import speed_session as ss   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)
FR = np.arange(1, 121, dtype="float64")


# ====================================================================== 시제품 (G1 · G2 에서 app/core 로 옮긴다)
def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def weights(times, selected, radius):
    """경로를 따라 잰 프레임 거리 폴오프 (계획서 §3-2). 고른 점 = 1."""
    t = np.asarray(times, dtype="float64")
    s = np.asarray(sorted(selected), dtype="float64")
    d = np.abs(t[:, None] - s[None, :]).min(axis=1)
    if radius <= 0:
        return (d < 1e-9).astype("float64")
    return smooth01(1.0 - d / radius)


def rotate_weighted(P, pivot, axis, theta, w):
    """점마다 w·theta 만큼 axis 둘레 회전 (Rodrigues)."""
    k = np.asarray(axis, dtype="float64")
    k = k / np.linalg.norm(k)
    v = P - pivot
    a = (w * theta)[:, None]
    cos, sin = np.cos(a), np.sin(a)
    kv = np.cross(np.broadcast_to(k, v.shape), v)
    kd = (v @ k)[:, None]
    return pivot + v * cos + kv * sin + k[None, :] * kd * (1.0 - cos)


def track(node):
    return np.array([world_pivot(node, f) for f in FR])


def key_count(node):
    out = 0
    for at in ("translateX", "translateY", "translateZ"):
        out += cmds.keyframe(node, attribute=at, q=True, keyframeCount=True) or 0
    return out


def deform(cache, target, tol_rel=ss.TOL_REL):
    s = ss.StrokeSession(cache, mode=ss.MODE_SHAPE, tolerance_rel=tol_rel)
    s.begin_stroke()
    s.current = np.asarray(target, dtype="float64")          # = 계획서의 set_state
    t0 = time.perf_counter()
    wrote = s.end_stroke()
    return s, wrote, (time.perf_counter() - t0) * 1000.0


def report_case(label, node, cache, target, w):
    before = track(node)
    n0 = key_count(node)
    q0 = cmds.undoInfo(q=True, undoName=True)
    s, wrote, ms = deform(cache, target)
    after = track(node)
    size = al.size(before)
    err = np.linalg.norm(after - target, axis=1)
    outside = w <= 0
    moved_out = np.linalg.norm(after[outside] - before[outside], axis=1).max() if outside.any() else 0.0
    print("  [{0}] write {1:.1f} ms · keys {2} -> {3} · max err {4:.4f} ({5:.3f}% of size) · outside moved {6:.2e}".format(
        label, ms, n0, key_count(node), err.max(), 100.0 * err.max() / size, moved_out))
    for name, e, added, msg in s.report:
        print("      {0}: err {1:.4f} added {2} {3}".format(name, e, added, msg))
    check(label + ": wrote", wrote)
    check(label + ": result follows the target (< 0.3% of size)", err.max() < 0.003 * size, err.max())
    check(label + ": frames outside the falloff unchanged", moved_out < 1e-3 * size, moved_out)
    cmds.undo()
    back = np.abs(track(node) - before).max()
    check(label + ": one undo restores it", back < 1e-9, "{0:.2e} (undo name before: {1})".format(back, q0))
    return after


# ====================================================================== G0-5 deform 쓰기
print("\n== G0-5 deform through StrokeSession (shape state = target points)")
scenes.new(120)
plain = cmds.polyCube(name="sparse")[0]
scenes._key_translate(plain, (1, 30, 60, 90, 120), lambda f: (f * 0.1, np.sin(f * 0.1) * 3, 0.0))
cache = pc.PathCache(plain, 1, 120)
cache.rebake()
P0 = cache.points.copy()

# (a) 키 아닌 프레임 점 45 를 고르고 반경 15 fr 로 Y +2 이동
w = weights(cache.times, [45.0], 15.0)
report_case("move frame 45, R 15", plain, cache, P0 + w[:, None] * np.array([0.0, 2.0, 0.0]), w)
cache.refresh()

# (b) 같은 점 · 반경 15 로 피벗(45 의 점) 둘레 Y 축 40도 회전
pivot = P0[cache.row_of(45.0)]
w = weights(cache.times, [45.0], 15.0)
report_case("rotate 40 deg about frame 45, R 15", plain, cache, rotate_weighted(P0, pivot, (0, 1, 0), np.radians(40.0), w), w)
cache.refresh()

# (b2) 두 점(40, 50) 무게중심 둘레 회전 - 고른 점들 = 1 이라 그 사이 구간이 강체 회전
w = weights(cache.times, [40.0, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50.0], 12.0)
pivot = P0[[cache.row_of(40.0), cache.row_of(50.0)]].mean(axis=0)
report_case("rotate 30 deg segment 40-50, R 12", plain, cache, rotate_weighted(P0, pivot, (0, 0, 1), np.radians(30.0), w), w)
cache.refresh()

# (c) 폴오프 없이 프레임 점 하나 (키가 생기는가)
w = weights(cache.times, [45.0], 0.0)
report_case("single frame point 45, R 0", plain, cache, P0 + w[:, None] * np.array([0.0, 2.0, 0.0]), w)
cache.refresh()

# (d) 매 프레임 키 (모캡) - 키 수가 늘지 않아야
scenes.new(120)
mocap = cmds.polyCube(name="mocap")[0]
scenes._key_translate(mocap, range(1, 121), lambda f: (f * 0.1, np.sin(f * 0.13) * 3 + np.sin(f * 1.7) * 0.05, np.cos(f * 0.05)))
mc = pc.PathCache(mocap, 1, 120)
mc.rebake()
n0 = key_count(mocap)
w = weights(mc.times, [60.0], 20.0)
after = report_case("mocap move frame 60, R 20", mocap, mc, mc.points + w[:, None] * np.array([1.0, 1.5, -0.5]), w)
s, _wrote, ms = deform(mc, mc.points + w[:, None] * np.array([1.0, 1.5, -0.5]))
check("mocap: key count unchanged", key_count(mocap) == n0, "{0} -> {1}".format(n0, key_count(mocap)))
cmds.undo()

# (e) 애니메이션 레이어 (편집 레이어 addL 에만 쓰고 Base 는 그대로)
c, _other = scenes.layered(120)
base = {at: tuple(cmds.keyframe(c, attribute=at, q=True, valueChange=True) or ()) for at in ("translateX", "translateY", "translateZ")}
lc = pc.PathCache(c, 1, 120, layer="addL")
lc.rebake()
w = weights(lc.times, [40.0], 15.0)
before = track(c)
s, wrote, ms = deform(lc, lc.points + w[:, None] * np.array([0.0, 1.0, 0.0]))
after = track(c)
base_after = {at: tuple(cmds.keyframe(c, attribute=at, q=True, valueChange=True) or ()) for at in ("translateX", "translateY", "translateZ")}
target = before + w[:, None] * np.array([0.0, 1.0, 0.0])
err = np.linalg.norm(after - target, axis=1)
print("  [layer addL] write {0:.1f} ms · max err {1:.4f}".format(ms, err.max()))
check("layer: Base curves untouched", base == base_after)
# addL 가중치가 120 에서 0.4 로 줄고 override 0.5 가 X 를 반 가린다 → 레이어 값을 β 로 나눠 역산해 맞추는지
check("layer: combined motion follows the target (< 0.3%)", err.max() < 0.003 * al.size(before), err.max())
cmds.undo()
check("layer: one undo restores it", np.abs(track(c) - before).max() < 1e-9)

# (f) 미리보기 계산 속도 (끄는 동안 마우스 한 번 = 가중치 + 변환 + 그래프 속도)
scenes.new(1000)
big = cmds.polyCube(name="big")[0]
scenes._key_translate(big, range(1, 1001, 5), lambda f: (f * 0.1, np.sin(f * 0.05) * 3, 0.0))
bc = pc.PathCache(big, 1, 1000)
bc.rebake()
s = ss.StrokeSession(bc, mode=ss.MODE_SHAPE)
t0 = time.perf_counter()
for i in range(50):
    w = weights(bc.times, [500.0], 60.0)
    s.current = rotate_weighted(s.stack[-1], bc.points[499], (0, 1, 0), np.radians(i), w)
    sp = s.preview_speed(np.arange(1.0, 1000.0))
ms = (time.perf_counter() - t0) * 1000.0 / 50
print("  [preview 1,000 frames] {0:.2f} ms per mouse move".format(ms))
check("preview per mouse move < 5 ms (1,000 frames)", ms < 5.0, ms)


# ====================================================================== G0-4 기즈모 수학 (가짜 원근 카메라)
print("\n== G0-4 gizmo pick / drag math (fake perspective camera)")
W_, H_ = 800, 600
FOV = np.radians(54.43)
CAM = np.array([6.0, 5.0, 20.0])


def look_at(eye, target, up=(0.0, 1.0, 0.0)):
    f = target - eye
    f = f / np.linalg.norm(f)
    r = np.cross(f, up)
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    return r, u, f


R_, U_, F_ = look_at(CAM, np.zeros(3))
VIEW = np.eye(4)
VIEW[:3, 0], VIEW[:3, 1], VIEW[:3, 2] = R_, U_, -F_
VIEW[3, :3] = [-(CAM @ R_), -(CAM @ U_), (CAM @ F_)]
fy = 1.0 / np.tan(FOV / 2.0)
near, far = 0.1, 1000.0
PROJ = np.zeros((4, 4))
PROJ[0, 0], PROJ[1, 1] = fy / (W_ / float(H_)), fy
PROJ[2, 2], PROJ[2, 3] = (far + near) / (near - far), -1.0
PROJ[3, 2] = 2.0 * far * near / (near - far)
VP = VIEW @ PROJ


def ray(x, y):
    ndc_x, ndc_y = x / W_ * 2.0 - 1.0, y / H_ * 2.0 - 1.0
    d = F_ + R_ * ndc_x / PROJ[0, 0] + U_ * ndc_y / PROJ[1, 1]
    return CAM.copy(), d / np.linalg.norm(d)


def px_of(p):
    return pk.project(np.asarray(p).reshape(1, 3), VP, W_, H_)[0][0]


def world_per_px(pivot):
    """화면 크기 고정: pivot 깊이에서 1 px 의 월드 길이."""
    depth = float((pivot - CAM) @ F_)
    return depth * 2.0 * np.tan(FOV / 2.0) / H_


GIZMO_PX = 90.0
HIT_PX = 8.0
AX = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}


def gizmo_hit(pivot, mode, x, y):
    L = GIZMO_PX * world_per_px(pivot)
    best, part = HIT_PX, None
    if mode == "move":
        for name, a in AX.items():
            seg = pivot + np.outer(np.linspace(0.15, 1.0, 24), a * L)
            px, _f = pk.project(seg, VP, W_, H_)
            d = np.hypot(px[:, 0] - x, px[:, 1] - y).min()
            if d < best:
                best, part = d, name
    else:
        ang = np.linspace(0, 2 * np.pi, 97)
        for name, a in AX.items():
            b1 = np.cross(a, [0.3, 0.5, 0.7])
            b1 /= np.linalg.norm(b1)
            b2 = np.cross(a, b1)
            ring = pivot + L * (np.outer(np.cos(ang), b1) + np.outer(np.sin(ang), b2))
            px, _f = pk.project(ring, VP, W_, H_)
            d = np.hypot(px[:, 0] - x, px[:, 1] - y).min()
            if d < best:
                best, part = d, "r" + name
    return part


def ring_angle(pivot, axis, x0, y0, x1, y1):
    o0, d0 = ray(x0, y0)
    o1, d1 = ray(x1, y1)
    h0, h1 = pk.ray_plane(o0, d0, pivot, axis), pk.ray_plane(o1, d1, pivot, axis)
    v0, v1 = h0 - pivot, h1 - pivot
    return np.arctan2(float(np.cross(v0, v1) @ axis), float(v0 @ v1))


pivot = np.array([1.0, 0.5, -2.0])
L = GIZMO_PX * world_per_px(pivot)
tip = px_of(pivot + AX["x"] * L * 0.9)
check("gizmo: near the X arrow tip picks x", gizmo_hit(pivot, "move", tip[0] + 2, tip[1] - 2) == "x")
mid = px_of(pivot + AX["y"] * L * 0.5)
check("gizmo: middle of the Y arrow picks y", gizmo_hit(pivot, "move", *mid) == "y")
far_px = px_of(pivot) + np.array([200.0, 200.0])
check("gizmo: empty space picks nothing", gizmo_hit(pivot, "move", *far_px) is None)
# 화면 크기 고정: 피벗을 멀리 보내도 화살표 화면 길이가 같다
def arrow_px(pv):
    Lw = GIZMO_PX * world_per_px(pv)
    return np.linalg.norm(px_of(pv + AX["y"] * Lw) - px_of(pv))
near_len, far_len = arrow_px(pivot), arrow_px(pivot + F_ * 30.0)
check("gizmo: constant screen size (near vs far, Y arrow, within 15%)", abs(near_len - far_len) / near_len < 0.15,
      "{0:.1f} px vs {1:.1f} px".format(near_len, far_len))
# 축 이동: X 화살표를 끌면 X 로만
o0, d0 = ray(*tip)
o1, d1 = ray(tip[0] + 40, tip[1] + 25)
a0, a1 = pk.ray_axis(o0, d0, pivot, AX["x"]), pk.ray_axis(o1, d1, pivot, AX["x"])
check("gizmo: X drag moves along X only", np.allclose((a1 - a0)[1:], 0.0) and abs(a1[0] - a0[0]) > 1e-3, a1 - a0)
# 회전: Y 고리 위 0도 → 30도 지점의 화면 좌표로 끌면 30도
b1 = np.cross(AX["y"], [0.3, 0.5, 0.7])
b1 /= np.linalg.norm(b1)
b2 = np.cross(AX["y"], b1)
on = lambda deg: pivot + L * (np.cos(np.radians(deg)) * b1 + np.sin(np.radians(deg)) * b2)   # noqa: E731
p0, p1 = px_of(on(10.0)), px_of(on(40.0))
check("gizmo: a point on the Y ring picks ry", gizmo_hit(pivot, "rotate", *p0) == "ry")
ang = np.degrees(ring_angle(pivot, AX["y"], p0[0], p0[1], p1[0], p1[1]))
check("gizmo: Y ring drag 10 -> 40 deg = 30 deg (pixel rounding < 1 deg)", abs(ang - 30.0) < 1.0, "{0:.3f}".format(ang))


# ====================================================================== G0-1 · G0-3 헤드리스로 볼 수 있는 것
print("\n== G0-1 / G0-3 (API and hotkey, headless part)")
dm_doc = omr.MUIDrawManager.mesh.__doc__ or ""
print("  MUIDrawManager.mesh doc: " + dm_doc.strip().splitlines()[0] if dm_doc else "  (no doc)")
check("MUIDrawManager.mesh exists", hasattr(omr.MUIDrawManager, "mesh"))
check("primitive kPoints / kLineStrip exist", hasattr(omr.MUIDrawManager, "kPoints") and hasattr(omr.MUIDrawManager, "kLineStrip"))
check("beginDrawInXray exists", hasattr(omr.MUIDrawManager, "beginDrawInXray"))
for flag in ("name", "releaseName"):
    try:
        print("  hotkey b {0}: {1!r}".format(flag, cmds.hotkey("b", q=True, **{flag: True})))
    except Exception as exc:                               # noqa: BLE001
        print("  hotkey b {0}: (query failed in mayapy: {1})".format(flag, exc))
for cmd in ("softSelect",):
    try:
        print("  softSelect -q -ssd = {0}".format(cmds.softSelect(q=True, softSelectDistance=True)))
    except Exception as exc:                               # noqa: BLE001
        print("  softSelect query failed: {0}".format(exc))

_common.finish()
