# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 속도 그래프 엔진 수학 시험 (속도 그래프 계획서 §6: arc_length · retime · refit)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_speed_engine.py
import maya.standalone
maya.standalone.initialize(name="python")
import maya.api.OpenMaya as om   # noqa: E402
import maya.api.OpenMayaAnim as oma   # noqa: E402
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import arc_length as al   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import refit   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import retime   # noqa: E402

# ====================================================================== arc_length
t = np.arange(1.0, 101.0)
line = np.stack([t * 0.5, np.zeros_like(t), np.zeros_like(t)], axis=1)
sp = al.speed(t, line, t)
check("straight line at constant speed: speed = 0.5 everywhere", np.abs(sp - 0.5).max() < 1e-12, sp[:3])
ang = t * 0.05
circle = np.stack([np.cos(ang) * 10, np.sin(ang) * 10, np.zeros_like(t)], axis=1)
sp = al.speed(t, circle, t[5:-5])
check("circle at constant angular speed: speed constant (chord)", np.ptp(sp) < 1e-9, np.ptp(sp))
hold = line.copy()
hold[40:60] = hold[40]
sp = al.speed(t, hold, t)
check("hold frames have speed 0", np.abs(sp[41:59]).max() < 1e-12)
check("acceleration of a straight constant motion is 0", al.accel(t, line, t).max() < 1e-12)
check("acceleration shows a pop", al.accel(t, hold, t).max() > 0.2)

# ====================================================================== retime
u = np.arange(0.0, 100.0001, 0.25)
x = u + 3.0 * np.sin(u * 0.4)                       # 울퉁불퉁한 속도 (모양은 직선)
P = np.stack([x, np.zeros_like(u), np.zeros_like(u)], axis=1)
r = retime.SpeedRetimer(u, P)
v1 = r.dab(r.v0, 50.0, 10.0, 1.0)
s0 = r._arc(r.v0)
s1 = r._arc(v1)
check("dab: arc length at both ends of the brush unchanged (outside motion kept)",
      abs(np.interp(39.0, u, s1) - np.interp(39.0, u, s0)) < 1e-9 and abs(np.interp(61.0, u, s1) - np.interp(61.0, u, s0)) < 1e-9)
check("dab: speed inside the brush is smoother (less spread)",
      np.std(r.speed_at(v1, np.arange(45, 56))) < 0.4 * np.std(r.speed_at(r.v0, np.arange(45, 56))),
      (np.std(r.speed_at(v1, np.arange(45, 56))), np.std(r.speed_at(r.v0, np.arange(45, 56)))))
check("dab: strength 0 = no change", np.abs(r.dab(r.v0, 50.0, 10.0, 0.0) - r.v0).max() < 1e-15)
tau = r.tau(v1, np.arange(0, 101))
check("tau increases (no going back in time)", np.all(np.diff(tau) > 0))
check("tau = identity outside the brush", np.abs(tau[:39] - np.arange(0, 39)).max() < 1e-6 and
      np.abs(tau[62:] - np.arange(62, 101)).max() < 1e-6)
pts = r.points_at(v1, np.arange(0, 101))
check("new points lie on the original path (shape kept)", np.abs(pts[:, 1:]).max() < 1e-12)
again = r.dab(r.dab(r.v0, 50.0, 10.0, 1.0), 50.0, 10.0, 1.0)
check("same dab from the same start = same result (no drift)",
      np.abs(r.dab(r.v0, 50.0, 10.0, 1.0) - v1).max() == 0.0 and np.isfinite(again).all())
# 정지 유지 : 40 ~ 60 정지
xh = u.copy()
xh[(u >= 40) & (u <= 60)] = 40.0
xh[u > 60] = u[u > 60] - 20.0
Ph = np.stack([xh + np.sin(u * 0.7), np.zeros_like(u), np.zeros_like(u)], axis=1)
Ph[(u >= 40) & (u <= 60), 0] = 40.0 + np.sin(40 * 0.7)
rh = retime.SpeedRetimer(u, Ph)
vh = rh.dab(rh.v0, 45.0, 20.0, 1.0)
ph0 = rh.points_at(rh.v0, np.arange(40, 61))
ph1 = rh.points_at(vh, np.arange(40, 61))
check("a hold stays a hold, at the same place", np.abs(ph1 - ph0).max() < 1e-6, np.abs(ph1 - ph0).max())
check("but the motion before the hold was smoothed",
      np.abs(rh.points_at(vh, np.arange(28, 40)) - rh.points_at(rh.v0, np.arange(28, 40))).max() > 1e-3)
# 속도 바꾸기 (G4)
vc = r.change(r.v0, 50.0, 0.5, 15.0)
check("change: faster at the grabbed frame", r.speed_at(vc, [50])[0] > r.speed_at(r.v0, [50])[0] + 0.3)
sc = r._arc(vc)
check("change: reach edges make up for it (outside unchanged)",
      abs(np.interp(34.0, u, sc) - np.interp(34.0, u, s0)) < 1e-9 and abs(np.interp(66.0, u, sc) - np.interp(66.0, u, s0)) < 1e-9)
# 모양 Smooth (G5)
tt = np.arange(1.0, 121.0)
arc = np.stack([np.cos(tt * 0.03) * 20, np.sin(tt * 0.03) * 20, np.zeros_like(tt)], axis=1)
bumpy = arc + np.stack([np.zeros_like(tt), np.zeros_like(tt), 0.3 * np.sin(tt * 2.1)], axis=1)
sm = retime.ShapeSmoother(tt, bumpy)
W = bumpy
for _ in range(6):
    W = sm.dab(W, 60.0, 30.0, 1.0)
check("shape smooth: bumps reduced (z noise around the middle)", np.abs(W[50:70, 2]).max() < 0.5 * np.abs(bumpy[50:70, 2]).max(),
      (np.abs(W[50:70, 2]).max(), np.abs(bumpy[50:70, 2]).max()))
radius = np.linalg.norm(W[50:70, :2], axis=1)
check("shape smooth: the arc does not shrink much (Taubin)", np.abs(radius - 20.0).max() < 0.05, np.abs(radius - 20.0).max())
check("shape smooth: outside the brush unchanged", np.abs(W[:29] - bumpy[:29]).max() == 0 and np.abs(W[91:] - bumpy[91:]).max() == 0)

# ====================================================================== refit : 마야 커브 골든
def make_curve(weighted, fps_name="film", lin="cm"):
    cmds.file(new=True, force=True)
    cmds.currentUnit(time=fps_name, linear=lin)
    n = cmds.polyCube(name="k")[0]
    for f, v in ((1, 0), (10, 3), (25, -2), (40, 5), (41.5, 5.2), (60, 1)):
        cmds.setKeyframe(n, attribute="translateX", time=f, value=v)
    crv = cmds.listConnections(n + ".translateX")[0]
    if weighted:
        cmds.keyTangent(crv, edit=True, weightedTangents=True)
        cmds.keyTangent(crv, index=(1, 1), outWeight=3.0, inWeight=0.5, weightLock=False, lock=False)
    sel = om.MSelectionList()
    sel.add(crv)
    return n, crv, oma.MFnAnimCurve(sel.getDependNode(0))


def maya_eval(fn, ts):
    unit = om.MTime.uiUnit()
    return np.array([fn.evaluate(om.MTime(float(x), unit)) for x in ts])


for weighted in (False, True):
    for fps_name, lin in (("film", "cm"), ("ntsc", "m"), ("ntscf", "cm")):
        tag = "{0} {1} {2}".format("weighted" if weighted else "plain", fps_name, lin)
        n, crv, fn = make_curve(weighted, fps_name, lin)
        snap = refit.read_curve(fn)
        ts = np.linspace(0.0, 62.0, 311)
        check("golden: our evaluate = Maya ({0})".format(tag), np.abs(snap.evaluate(ts) - maya_eval(fn, ts)).max() < 1e-9,
              np.abs(snap.evaluate(ts) - maya_eval(fn, ts)).max())

n, crv, fn = make_curve(False)
snap = refit.read_curve(fn)
st = np.arange(1.0, 61.0)
res = refit.fit(snap, st, snap.evaluate(st), refit.TOL_LINEAR)
check("fit: target = the curve itself -> nothing to change", not res.changed)

# 목표 = 원래 커브 + 가운데 매끈한 혹 (키 사이에 걸침)
target = snap.evaluate(st) + 0.8 * np.exp(-0.5 * ((st - 30.0) / 4.0) ** 2) * (np.abs(st - 30.0) < 12)
target[np.abs(st - 30.0) >= 12] = snap.evaluate(st[np.abs(st - 30.0) >= 12])
res = refit.fit(snap, st, target, 0.01)
check("fit: within tolerance after adding keys", res.error <= 0.01, (res.error, res.added))
check("fit: keys added only where needed (<= 3 per segment)", 0 < len(res.added) <= 9, res.added)
for k in snap.t:
    if k not in res.snap.t:
        check("fit: original key frame kept {0}".format(k), False)
check("fit: every original key frame kept", all(np.any(np.abs(res.snap.t - k) < 1e-9) for k in snap.t))
outside = (st < 10) | (st > 41.5)
check("fit: curve outside the end keys unchanged", np.abs(res.snap.evaluate(st[outside]) - snap.evaluate(st[outside])).max() < 1e-12)
change = oma.MAnimCurveChange()
refit.write_fit(fn, res, change)
check("write: Maya now evaluates like the fitted curve", np.abs(maya_eval(fn, st) - res.snap.evaluate(st)).max() < 1e-5,
      np.abs(maya_eval(fn, st) - res.snap.evaluate(st)).max())
check("write: Maya matches the target within tolerance", np.abs(maya_eval(fn, st) - target).max() <= 0.0101)
check("write: keys outside unchanged", abs(fn.value(0) - snap.y[0]) < 1e-12 and abs(fn.value(fn.numKeys - 1) - snap.y[-1]) < 1e-12)
change.undoIt()
check("undo of the change: curve back exactly", fn.numKeys == snap.count and np.abs(maya_eval(fn, st) - snap.evaluate(st)).max() < 1e-12)

# 가중 커브에 쓰기
n, crv, fn = make_curve(True, "ntsc", "m")
snap = refit.read_curve(fn)
target = snap.evaluate(st) + np.where((st > 12) & (st < 38), 30.0 * np.sin((st - 12) / 26.0 * np.pi) ** 2, 0.0)
res = refit.fit(snap, st, target, 0.3)            # 30 cm 혹을 1% 로 (내부 cm, 미터 씬)
change = oma.MAnimCurveChange()
refit.write_fit(fn, res, change)
check("weighted curve: Maya = fitted (30fps, metres)", np.abs(maya_eval(fn, st) - res.snap.evaluate(st)).max() < 1e-4,
      np.abs(maya_eval(fn, st) - res.snap.evaluate(st)).max())
check("weighted curve: within tolerance with few keys", np.abs(maya_eval(fn, st) - target).max() <= 0.3 + 1e-4
      and len(res.added) + len(res.anchors) <= 6, (np.abs(maya_eval(fn, st) - target).max(), len(res.added), len(res.anchors)))
change.undoIt()

# 키가 매 프레임 (모캡) - 값만 바뀌고 키는 늘지 않는다
cmds.file(new=True, force=True)
cmds.currentUnit(time="film", linear="cm")
m = cmds.polyCube(name="mocap")[0]
for f in range(1, 61):
    cmds.setKeyframe(m, attribute="translateX", time=f, value=np.sin(f * 0.2) * 3)
sel = om.MSelectionList()
sel.add(cmds.listConnections(m + ".translateX")[0])
fn = oma.MFnAnimCurve(sel.getDependNode(0))
snap = refit.read_curve(fn)
target = snap.evaluate(st) + np.where((st > 20) & (st < 40), 0.5, 0.0)
res = refit.fit(snap, st, target, refit.TOL_LINEAR)
check("key per frame: exact at every frame, no key added", res.error < 1e-12 and not res.added and not res.anchors,
      (res.error, res.added))

# 첫 키 앞까지 바뀌면 앵커 키
cmds.file(new=True, force=True)
a = cmds.polyCube(name="a")[0]
for f, v in ((20, 1.0), (40, 3.0)):
    cmds.setKeyframe(a, attribute="translateX", time=f, value=v)
sel = om.MSelectionList()
sel.add(cmds.listConnections(a + ".translateX")[0])
fn = oma.MFnAnimCurve(sel.getDependNode(0))
snap = refit.read_curve(fn)
target = snap.evaluate(st) + np.where((st > 10) & (st < 30), np.sin((st - 10) / 20.0 * np.pi), 0.0)
res = refit.fit(snap, st, target, refit.TOL_LINEAR)
check("change before the first key: an anchor key at an unchanged frame", len(res.anchors) == 1 and res.anchors[0] == 10.0,
      res.anchors)
check("anchor fit within tolerance", res.error <= refit.TOL_LINEAR, res.error)
check("frames before the anchor unchanged", np.abs(res.snap.evaluate(st[st <= 10]) - snap.evaluate(st[st <= 10])).max() < 1e-12)

_common.finish()
