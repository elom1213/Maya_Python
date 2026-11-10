# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.56 - Bake > Locator `Fast` 경로 시험 (mayapy 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_locator_bake_fast.py
# 판정: 빠른 경로의 로케이터 월드 행렬 == 일반 경로(bakeResults) 의 로케이터 월드 행렬 (정수 프레임 전부).
import math
import os
import sys
import time

import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
from maya.api import OpenMaya as om   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)

from tools.A00110_animTool_V02.app.core.locator_bake_manager import LocatorBakeManager as LBM   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


S, E = 1, 60


def scene(animate_parent=False, constrained_parent=False, joint=False):
    """grp_01 > grp_02 > ctl_01 (+ 회전 · 스케일 · rotateAxis · rotateOrder · 피벗 · OPM 섞음)."""
    cmds.file(new=True, force=True)
    g1 = cmds.createNode("transform", name="grp_01")
    cmds.setAttr(g1 + ".translate", 10, 20, -5)
    cmds.setAttr(g1 + ".rotate", 30, -45, 10)
    cmds.setAttr(g1 + ".scale", 2, 2, 2)
    g2 = cmds.createNode("transform", name="grp_02", parent=g1)
    cmds.setAttr(g2 + ".translate", 3, 0, 1)
    cmds.setAttr(g2 + ".rotateAxis", 5, 15, -20)
    cmds.setAttr(g2 + ".rotatePivot", 1, 2, 0)
    m = om.MEulerRotation(0.2, 0.1, -0.3).asMatrix()
    cmds.setAttr(g2 + ".offsetParentMatrix", list(m), type="matrix")
    if animate_parent:
        for f, v in ((S, 0), (30, 80), (E, -20)):
            cmds.setKeyframe(g2, at="rotateY", t=f, v=v)
    if constrained_parent:
        drv = cmds.createNode("transform", name="driver")
        cmds.setAttr(drv + ".translate", 1, 2, 3)
        cmds.parentConstraint(drv, g1, maintainOffset=True)    # 연결은 있지만 움직이지 않는다
    if joint:
        cmds.select(clear=True)
        c = cmds.joint(name="ctl_01")
        c = cmds.parent(c, g2, relative=True)[0]
        cmds.setAttr(c + ".jointOrient", 20, -35, 50)
    else:
        c = cmds.circle(name="ctl_01", ch=False)[0]
        c = cmds.parent(c, g2, relative=True)[0]
    cmds.setAttr(c + ".rotateOrder", 2)
    cmds.setAttr(c + ".rotateAxis", 10, -20, 5)
    for f in range(S, E + 1, 3):
        cmds.setKeyframe(c, at="tx", t=f, v=math.sin(f * 0.2) * 5)
        cmds.setKeyframe(c, at="ty", t=f, v=f * 0.3)
        cmds.setKeyframe(c, at="rx", t=f, v=f * 7.0)          # 360 을 넘는 회전
        cmds.setKeyframe(c, at="ry", t=f, v=math.cos(f * 0.1) * 60)
        cmds.setKeyframe(c, at="sz", t=f, v=1 + 0.01 * f)
    return cmds.ls(c, long=True)[0]


def worlds(node):
    return [om.MMatrix(cmds.getAttr(node + ".worldMatrix[0]", time=f)) for f in range(S, E + 1)]


def max_diff(a, b):
    return max(abs(x[i] - y[i]) for x, y in zip(a, b) for i in range(16))


def bake(ctl, **kw):
    locs, msg = LBM.bake([ctl], S, E, translate=True, rotate=True, scale=True,
                         select_result=False, **kw)
    return locs[0], msg


try:
    cmds.undoInfo(state=True, infinity=True)

    # ---- 1. 정지 부모: Fast == 일반 == 원본 (원본에 rotateAxis 있음 - 일반 경로 v02.56 수정 확인)
    ctl = scene()
    ref = worlds(ctl)
    loc_n, _ = bake(ctl)
    loc_s, msg = bake(ctl, fast=True)
    check("normal bake matches the object (rotateAxis fix)", max_diff(worlds(loc_n), ref) < 1e-6,
          max_diff(worlds(loc_n), ref))
    check("fast == object", max_diff(worlds(loc_s), ref) < 1e-6, max_diff(worlds(loc_s), ref))
    check("normal path keeps its own scale = 1 when Scale is off",
          cmds.getAttr(LBM.bake([ctl], S, E, scale=False, select_result=False)[0][0] + ".scale")[0]
          == (1.0, 1.0, 1.0))
    check("message says fast", "Fast mode (parents treated as still" in msg, msg)
    check("a key on every frame", cmds.keyframe(loc_s + ".rx", q=True, kc=True) == E - S + 1)
    check("no temp curves left", not cmds.ls("LOC_fast_tmp*"))
    check("no constraint on fast locators", not cmds.listRelatives(loc_s, type="constraint"))
    rx = cmds.keyframe(loc_s + ".rx", q=True, valueChange=True)
    jump = max(abs(rx[i + 1] - rx[i]) for i in range(len(rx) - 1))
    check("rotate curve continuous (no 360 jumps)", jump < 90.0, jump)

    # ---- 2. 부모가 실제로 움직인다: 일반 경로는 맞고, Fast 는 (사용자 선택대로) 틀린다
    ctl = scene(animate_parent=True)
    ref = worlds(ctl)
    loc_n, _ = bake(ctl)
    loc_s, _ = bake(ctl, fast=True)
    check("moving parent: normal bake matches", max_diff(worlds(loc_n), ref) < 1e-6)
    check("moving parent: fast is wrong (user's call)", max_diff(worlds(loc_s), ref) > 1.0)
    check("moving parent: fast still right on the start frame",
          max_diff(worlds(loc_s)[:1], ref[:1]) < 1e-6)

    # ---- 3. 부모에 컨스트레인트가 연결돼 있지만 안 움직인다: Static 을 고르면 맞다
    ctl = scene(constrained_parent=True)
    ref = worlds(ctl)
    loc_s, _ = bake(ctl, fast=True)
    check("constrained but still parent: fast static matches", max_diff(worlds(loc_s), ref) < 1e-6)

    # ---- 4. 조인트(jointOrient) 원본
    ctl = scene(joint=True)
    ref = worlds(ctl)
    loc_s, _ = bake(ctl, fast=True)
    check("joint source: fast static matches", max_diff(worlds(loc_s), ref) < 1e-6)

    # ---- 5. 씬 단위 m
    ctl = scene()
    cmds.currentUnit(linear="m")
    ref = worlds(ctl)
    loc_s, _ = bake(ctl, fast=True)
    check("scene unit m: fast static matches", max_diff(worlds(loc_s), ref) < 1e-6)
    cmds.currentUnit(linear="cm")

    # ---- 6. undo / redo
    ctl = scene()
    before = set(cmds.ls(type="animCurve"))
    loc_s, _ = bake(ctl, fast=True)
    cmds.undo()
    check("undo removes locator and curves",
          not cmds.objExists(loc_s) and set(cmds.ls(type="animCurve")) == before)
    cmds.redo()
    check("redo brings the keys back", cmds.objExists(loc_s)
          and cmds.keyframe(loc_s + ".tx", q=True, kc=True) == E - S + 1
          and max_diff(worlds(loc_s), worlds(ctl)) < 1e-6)

    # ---- 7. 시간을 옮기지 않는다
    ctl = scene()
    cmds.currentTime(17)
    hits = []
    cb = om.MDGMessage.addTimeChangeCallback(lambda *a: hits.append(1))
    try:
        bake(ctl, fast=True)
    finally:
        om.MMessage.removeCallback(cb)
    check("fast path never changes the scene time", not hits and cmds.currentTime(q=True) == 17,
          len(hits))

    # ---- 8. 무거운 씬에서 속도 (기록만, 판정은 '빠르다')
    cmds.file(new=True, force=True)
    try:
        cmds.evaluationManager(mode="parallel")
    except Exception:
        pass
    # GUI 기본(병렬 평가)에서는 시간을 옮길 때마다 장면 전체가 평가된다 - 변형 메시 몇 개로 그 무게를 흉내 낸다.
    for k in range(4):
        heavy = cmds.polySphere(sx=300, sy=300, ch=False)[0]
        bend = cmds.nonLinear(heavy, type="bend")[0]
        cmds.setKeyframe(bend, at="curvature", t=S, v=0)
        cmds.setKeyframe(bend, at="curvature", t=300, v=90 + k)
    top = cmds.createNode("transform", name="rig")
    p = top
    for i in range(30):
        p = cmds.createNode("transform", name="g%d" % i, parent=p)
        cmds.setAttr(p + ".translate", 1, 0, 0)
    ctls = []
    for k in range(5):
        c = cmds.createNode("transform", name="ctl%d" % k, parent=p)
        for f in range(S, 301, 5):
            cmds.setKeyframe(c, at="ty", t=f, v=f * 0.1 + k)
            cmds.setKeyframe(c, at="rz", t=f, v=f + k)
        ctls.append(cmds.ls(c, long=True)[0])
    t0 = time.time()
    LBM.bake(ctls, S, 300, select_result=False)
    t_norm = time.time() - t0
    t0 = time.time()
    LBM.bake(ctls, S, 300, select_result=False, fast=True)
    t_static = time.time() - t0
    check("heavy scene: fast static faster than normal", t_static < t_norm,
          "normal %.2fs / fast %.2fs" % (t_norm, t_static))
finally:
    print("\n{0}/{1} passed".format(sum(R), len(R)))
    maya.standalone.uninitialize()
    os._exit(0 if all(R) else 1)
