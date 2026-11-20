# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 실제 씬에서 경로 하나를 6,000 프레임 그릴 때의 비용 (v01.10 기준)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u bench_scene_6000.py [씬 경로] [노드] [프레임 수]
# 사용자 요청 (2026-11-20): 00010_cleanup_CHOEUN_00130.mb 의 origin:CHOEUN:cage:CH_r_ArmIK_xx_ctl 같은 컨트롤러를 6,000 프레임.
# 재는 것: 굽기 · 커브 다시 읽기 · 그리기 데이터 · 그릴 때마다 플러그인 Python(점 + 화면 2D 선) · 폴오프 · 끌기 미리보기 · 놓기(refit 쓰기).
# GPU 그리기 시간은 헤드리스로 못 잰다.
import os
import sys
import time

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_bridge, draw_nodes, falloff   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_manager as pm   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import speed_session as ss   # noqa: E402
from tools.A00630_MotionPathEditor.app.plugin import jun_motion_path as jp   # noqa: E402

SCENE = sys.argv[1] if len(sys.argv) > 1 else (
    r"C:\Users\USER\Desktop\JP\0001_PJ\0023_MUE_original\00_04_02_ANI_00_PJ_010\scenes"
    r"\5050_cleanup_BCM_CHOEUN\.tmp\00010_cleanup_CHOEUN_00130.mb")
NODE = sys.argv[2] if len(sys.argv) > 2 else "origin:CHOEUN:cage:CH_r_ArmIK_xx_ctl"
COUNT = int(sys.argv[3]) if len(sys.argv) > 3 else 6000


def ms(t0):
    return (time.perf_counter() - t0) * 1000.0


class FakeDM(object):
    """MUIDrawManager 자리 - 호출만 받는다 (플러그인 Python 쪽 시간만 잰다)."""
    kNonSelectable = kPoints = kLineStrip = kLeft = kDashed = kSolid = kDefaultFontSize = 0

    def __getattr__(self, name):
        return lambda *a, **k: None


draw_nodes.ensure_plugin()
t0 = time.perf_counter()
cmds.file(SCENE, open=True, force=True)
print("open scene                : {0:9.0f} ms".format(ms(t0)))
if not cmds.objExists(NODE):
    print("node not found: " + NODE)
    _common.finish()
start = int(cmds.playbackOptions(q=True, animationStartTime=True))
end = start + COUNT - 1
print("scene anim range          : {0} - {1} (bench {2} - {3}, {4} frames)".format(
    start, int(cmds.playbackOptions(q=True, animationEndTime=True)), start, end, COUNT))

mgr = pm.PathManager(log=print)
mgr.settings.update({"range": pm.RANGE_CUSTOM, "custom_start": start, "custom_end": end})
t0 = time.perf_counter()
mgr.set_targets([NODE])
t_bake = ms(t0)
cache = mgr.cache_list()[0]
print("bake (first, + redraw)    : {0:9.0f} ms   path points {1}, keys {2}, locked: {3}".format(
    t_bake, len(cache.times), len(cache.keys), cache.lock_reason or "no"))
t0 = time.perf_counter()
for _ in range(5):
    cache.refresh()
print("refresh (curves only)     : {0:9.1f} ms   (after a key edit / undo)".format(ms(t0) / 5))
t0 = time.perf_counter()
for _ in range(5):
    mgr.redraw()
print("redraw (draw data)        : {0:9.1f} ms   (selection / display change)".format(ms(t0) / 5))

# 플러그인이 그릴 때마다 하는 Python (prepareForDraw 는 dict 하나 - 0 에 가깝다)
p = draw_bridge.DATA[cache.key]
P = np.asarray(p["line"])
lo, hi = P.min(axis=0), P.max(axis=0)
c = (lo + hi) / 2.0
eye = c + np.array([0.0, 0.0, 1.0]) * float(np.linalg.norm(hi - lo)) * 1.5
VP = np.eye(4)
VP[3, :3] = -eye                                      # 카메라를 앞에 (단순 원근: w = -z)
proj = np.diag([1.0, 1.0, 1.0, 0.0])
proj[2, 3] = -1.0
VP = VP @ proj
dm = FakeDM()
t0 = time.perf_counter()
for _ in range(10):
    jp.JunMotionPathDrawOverride._draw_path(dm, p)
t_pts = ms(t0) / 10
t0 = time.perf_counter()
for _ in range(10):
    jp.JunMotionPathDrawOverride._draw_lines(dm, p, VP, 1920, 1080)
t_lines = ms(t0) / 10
print("per viewport draw (Python): {0:9.1f} ms   = points {1:.1f} + screen 2D line {2:.1f}  (GPU time not included)".format(
    t_pts + t_lines, t_pts, t_lines))

# 폴오프: 프레임 점 하나 + 반경 30 fr
mid = cache.times[len(cache.times) // 2]
row = cache.row_of(mid)
mgr.selection = {cache.key: {mid}}
mgr.settings.update({"falloff_on": True, "falloff_radius": 30.0})
t0 = time.perf_counter()
for _ in range(10):
    w = mgr.weights_for(cache)
print("falloff weights           : {0:9.2f} ms   ({1} points inside)".format(ms(t0) / 10, int(np.count_nonzero(w))))
t0 = time.perf_counter()
for _ in range(5):
    mgr.redraw()
t_redraw_f = ms(t0) / 5
p = draw_bridge.DATA[cache.key]
t0 = time.perf_counter()
for _ in range(10):
    jp.JunMotionPathDrawOverride._draw_lines(dm, p, VP, 1920, 1080)
print("redraw with falloff       : {0:9.1f} ms   draw lines {1:.1f} ms".format(t_redraw_f, ms(t0) / 10))

# 끌기: 세션 만들기(누를 때) · 마우스 한 번(미리보기) · 놓기(refit 쓰기) · undo
t0 = time.perf_counter()
s = ss.StrokeSession(cache, mode=ss.MODE_DEFORM)
s.begin_stroke()
t_press = ms(t0)
delta = np.array([0.0, 2.0, 0.0])
t0 = time.perf_counter()
for i in range(10):
    Pn = s.stack[-1] + w[:, None] * delta * (i + 1) / 10.0
    s.set_state(Pn)
    mgr.preview[cache.key] = Pn
    mgr.redraw()
t_move = ms(t0) / 10
mgr.preview.pop(cache.key, None)
t0 = time.perf_counter()
s.end_stroke()
t_write = ms(t0)
added = sum(r[2] for r in s.report)
t0 = time.perf_counter()
cmds.undo()
t_undo = ms(t0)
print("drag: press (session)     : {0:9.1f} ms".format(t_press))
print("drag: one mouse move      : {0:9.1f} ms   (target + preview draw data)".format(t_move))
print("drag: release (refit+write): {0:8.1f} ms   keys added {1}".format(t_write, added))
print("undo                      : {0:9.1f} ms".format(t_undo))
mgr.clear()
sys.stdout.flush()
maya.standalone.uninitialize()
os._exit(0)
