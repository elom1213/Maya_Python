# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 속도 그래프 G0 실측 (속도 그래프 계획서 §5 G0)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u bench_speed_graph.py
#   ① 조밀 경로: 부모 공간 보간(B) vs 서브프레임 굽기(A) 차이 · 시간
#   ② dab 시간 · apply(refit + 쓰기) 시간 - 키 몇 개 커브 / 매 프레임 키 커브
import time

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402,F401
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import arc_length as al   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_nodes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_cache as pc   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import speed_session as ss   # noqa: E402

draw_nodes.ensure_plugin()


def ms(t0):
    return (time.perf_counter() - t0) * 1000.0


def dense_compare(label, node, end):
    cache = pc.PathCache(node, 1, end)
    cache.rebake()
    t0 = time.perf_counter()
    u, Pb = ss.dense_points(cache, exact=False)
    tb = ms(t0)
    t0 = time.perf_counter()
    _u, Pa = ss.dense_points(cache, exact=True)
    ta = ms(t0)
    err = float(np.linalg.norm(Pa - Pb, axis=1).max())
    print("{0:28s} frames {1:5d}  B(interp) {2:7.1f} ms   A(bake) {3:8.1f} ms   max diff {4:.4f} cm = {5:.3f}% of path".format(
        label, end, tb, ta, err, 100.0 * err / al.size(Pa)))
    return cache


def bench_apply(label, cache):
    s = ss.StrokeSession(cache)
    a, b = cache.times[0], cache.times[-1]
    t0 = time.perf_counter()
    s.begin_stroke()
    centers = np.linspace(a + 0.3 * (b - a), a + 0.7 * (b - a), 20)
    for fc in centers:
        s.dab(fc, 12.0, 0.8)
    t_dab = ms(t0) / len(centers)
    t0 = time.perf_counter()
    s.end_stroke()
    t_apply = ms(t0)
    err = max((r[1] for r in s.report), default=0.0)
    added = sum(r[2] for r in s.report)
    print("{0:28s} dab {1:6.2f} ms   apply {2:7.1f} ms   fit err {3:.4f}   keys added {4}".format(
        label, t_dab, t_apply, err, added))
    s.cancel()


print("\n== dense path: interpolate the parent space (B) vs bake every 0.25 frame (A)")
names = scenes.simple(120)
dense_compare("simple / plain (static parent)", names["plain"], 120)
names = scenes.hierarchy(120)
c_ctrl = dense_compare("hierarchy / ctrl (rotating)", names["ctrl"], 120)
dense_compare("hierarchy / joint j3", names["joint"], 120)
names = scenes.hierarchy(1000)
c_long = dense_compare("hierarchy / ctrl", names["ctrl"], 1000)

print("\n== stroke: 20 dabs (radius 12, strength 0.8) then apply")
names = scenes.hierarchy(120)
cache = pc.PathCache(names["ctrl"], 1, 120)
cache.rebake()
bench_apply("ctrl 120 frames, 4 keys", cache)
names = scenes.hierarchy(1000)
cache = pc.PathCache(names["ctrl"], 1, 1000)
cache.rebake()
bench_apply("ctrl 1000 frames, 4 keys", cache)
# 매 프레임 키 (모캡 같은)
scenes.new(1000)
mocap = cmds.polyCube(name="mocap")[0]
rng = np.random.RandomState(3)
for f in range(1, 1001):
    cmds.setKeyframe(mocap, attribute="translateX", time=f, value=np.sin(f * 0.03) * 10 + rng.randn() * 0.05)
    cmds.setKeyframe(mocap, attribute="translateY", time=f, value=np.cos(f * 0.02) * 5 + rng.randn() * 0.05)
    cmds.setKeyframe(mocap, attribute="translateZ", time=f, value=f * 0.01)
cache = pc.PathCache(mocap, 1, 1000)
cache.rebake()
bench_apply("mocap 1000 frames, key/frame", cache)
maya.standalone.uninitialize()
