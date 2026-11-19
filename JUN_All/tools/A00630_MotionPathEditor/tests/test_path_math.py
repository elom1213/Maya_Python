# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 경로 수식 시험 (계획서 §7-2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_path_math.py
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_cache as pc   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import parent_space   # noqa: E402


def max_error(cache, frames):
    return max(np.abs(cache.point_at(f) - np.array(world_pivot(cache.node, f))).max() for f in frames)


SAMPLE = (1, 13, 30, 47, 60, 89, 120)

# ---- 단순 씬 : 일반 · 피벗 · OPM · 부분 키
names = scenes.simple(120)
for key in ("plain", "pivot", "opm", "partial"):
    c = pc.PathCache(names[key], 1, 120)
    c.rebake()
    check("simple {0}: path == Maya world pivot".format(key), max_error(c, SAMPLE) < 1e-6, max_error(c, SAMPLE))
c_pivot = pc.PathCache(names["pivot"], 1, 120)
c_pivot.rebake()
check("pivot cube has a pivot term c = rp + rpt", np.abs(c_pivot.c).max() > 0.1, c_pivot.c)
c_plain = pc.PathCache(names["plain"], 1, 120)
c_plain.rebake()
check("plain cube: c is zero", np.abs(c_plain.c).max() == 0.0)

# ---- 계층 씬 : 컨스트레인트 아래 컨트롤 · 조인트 (jointOrient · SSC · 비균일 부모 스케일)
names = scenes.hierarchy(120)
for key in ("ctrl", "joint"):
    c = pc.PathCache(names[key], 1, 120)
    c.rebake()
    check("hierarchy {0}: path == Maya world pivot".format(key), max_error(c, SAMPLE) < 1e-6, max_error(c, SAMPLE))
c_joint = pc.PathCache("j3", 1, 120)
c_joint.rebake()
check("joint: c is zero", np.abs(c_joint.c).max() < 1e-9, c_joint.c)

# ---- solve : 월드 점 → translate, 그 translate 로 다시 만든 점 = 그 월드 점
c = pc.PathCache(names["ctrl"], 1, 120)
c.rebake()
worst = 0.0
for k in c.keys:
    target = c.points[k.row] + np.array([1.5, -0.7, 2.25])
    T = c.solve(k.row, target)
    again = (np.append(c.c + T, 1.0) @ c.PM[k.row])[:3]
    worst = max(worst, np.abs(again - target).max())
check("solve is an exact inverse", worst < 1e-9, worst)

# ---- 굽기는 사용자 시간 · 선택 · 포즈를 바꾸지 않는다
cmds.currentTime(57)
cmds.select("driver")
before_pose = cmds.getAttr(names["ctrl"] + ".translate")[0]
c = pc.PathCache(names["ctrl"], 1, 120)
c.rebake()
check("bake keeps the current time", cmds.currentTime(q=True) == 57)
check("bake keeps the selection", cmds.ls(sl=True) == ["driver"])
check("bake keeps the pose", cmds.getAttr(names["ctrl"] + ".translate")[0] == before_pose)

# ---- 잠금 판정
c = pc.PathCache(names["driven"], 1, 120)
c.rebake()
check("constraint-driven translate is locked with a reason", c.locked and "driven by" in c.lock_reason, c.lock_reason)

# ---- 소수 프레임 키도 경로에 들어간다
names = scenes.simple(60)
cmds.setKeyframe(names["plain"], attribute="translateX", time=10.5, value=9.0)
c = pc.PathCache(names["plain"], 1, 60)
c.rebake()
check("fractional key time is on the path", c.row_of(10.5) is not None and any(abs(k.t - 10.5) < 1e-6 for k in c.keys))
check("fractional key point == Maya", np.abs(c.point_at(10.5) - np.array(world_pivot(c.node, 10.5))).max() < 1e-6)

# ---- 여러 경로 한 번에 굽기 = 하나씩 굽기
names = scenes.hierarchy(120)
a = pc.PathCache(names["ctrl"], 1, 120)
b = pc.PathCache("j3", 1, 120)
pc.bake_many([a, b])
one = pc.PathCache(names["ctrl"], 1, 120)
one.rebake()
check("bake_many == single bake", np.abs(a.points - one.points).max() < 1e-12 and
      np.abs(b.points - c_joint.points).max() < 1e-6)

# ---- 피벗 노드 : 자기 회전 · 스케일을 바꿔도 다시 굽지 않고 맞다 (c 는 상수)
names = scenes.simple(120)
pv = pc.PathCache(names["pivot"], 1, 120)
pv.rebake()
cmds.keyframe(names["pivot"] + ".rotateY", edit=True, relative=True, valueChange=40.0)
cmds.keyframe(names["pivot"] + ".scaleX", edit=True, relative=True, valueChange=1.5)
pv.refresh()
check("pivot node: rotate / scale edits need no re-bake", max_error(pv, SAMPLE) < 1e-6, max_error(pv, SAMPLE))
cmds.select(clear=True)
_j = cmds.joint(position=(1, 2, 3))
check("pivot_offset of a joint is zero", parent_space.pivot_offset(_j) == (0.0, 0.0, 0.0))

_common.finish()
