# -*- coding: utf-8 -*-
"""Physics Asset 모드 - 마야 씬 시험 (mayapy 헤드리스).

    "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe" tests/test_physics_maya.py

핵심 판정은 V2: **자식 노드에 회전 키가 있든 없든 결과가 같다**(원래 회전값을 지키지 않는다).
시험 씬은 오프셋 그룹 · rotateAxis · rotateOrder · jointOrient 를 0 아닌 값으로 섞는다.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, JUN_ALL)

import maya.standalone  # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds  # noqa: E402
from maya.api import OpenMaya as om  # noqa: E402

from tools.A00410_SecondaryMotion.app.core import bake_manager as bm  # noqa: E402
from tools.A00410_SecondaryMotion.app.core import chain_solver  # noqa: E402
from tools.A00410_SecondaryMotion.app.core import physics_solver as ps  # noqa: E402
from tools.A00410_SecondaryMotion.app.core import scene_sampler as ss  # noqa: E402

passed = 0
failed = 0


def check(label, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print("PASS", label, extra)
    else:
        failed += 1
        print("FAIL", label, extra)


N = 5
START, END = 1, 120


def build_ctrl_chain(prefix):
    """grp > ctl0 > off1 > ctl1 > off2 > ctl2 ... (오프셋 그룹 회전 + RA + RO 섞음)."""
    top = cmds.createNode("transform", name=prefix + "_grp")
    cmds.setAttr(top + ".translate", 0, 100, 0)
    cmds.setAttr(top + ".rotate", 0, 15, 0)
    parent = top
    ctls = []
    for i in range(N):
        if i > 0:
            off = cmds.createNode("transform", name="{0}_off{1}".format(prefix, i), parent=parent)
            cmds.setAttr(off + ".translate", 6, 0, 0)
            cmds.setAttr(off + ".rotate", 5 * i, -7, 3)
            parent = off
        ctl = cmds.circle(name="{0}_ctl{1}".format(prefix, i), ch=False)[0]
        ctl = cmds.parent(ctl, parent, relative=True)[0]
        cmds.setAttr(ctl + ".rotateOrder", i % 6)
        cmds.setAttr(ctl + ".rotateAxis", 10, -20 + i, 5)
        ctls.append(cmds.ls(ctl, long=True)[0])
        parent = ctl
    return top, ctls


def build_joint_chain(prefix):
    cmds.select(clear=True)
    js = []
    for i in range(N):
        j = cmds.joint(name="{0}_j{1}".format(prefix, i), p=(6 * i, 100, 30))
        js.append(j)
    for i, j in enumerate(js):
        cmds.setAttr(j + ".jointOrient", 10 + i, -5 * i, 20 - 3 * i)
        cmds.setAttr(j + ".rotateOrder", (i + 2) % 6)
        cmds.setAttr(j + ".rotateAxis", 3, 4 * i, -6)
    return [cmds.ls(j, long=True)[0] for j in js]


def key_parent_motion(node):
    """체인 위(그룹)가 흔들리는 애니메이션 = 체인을 끄는 드라이버."""
    for f, v in ((1, 0), (20, 60), (40, -40), (60, 30), (80, 0), (120, 0)):
        cmds.setKeyframe(node, at="rotateZ", t=f, v=v)


def key_child_curl(ctls):
    """자식 노드에만 회전 키(꼬리 말기)."""
    for c in ctls[1:]:
        for f, v in ((1, 0), (30, 35), (60, -20), (90, 40), (120, 10)):
            cmds.setKeyframe(c, at="rotateY", t=f, v=v)


def world_pos(node, t):
    m = cmds.getAttr(node + ".worldMatrix[0]", time=t)
    return (m[12], m[13], m[14])


def world_q(node, t):
    m = om.MMatrix(cmds.getAttr(node + ".worldMatrix[0]", time=t))
    return om.MTransformationMatrix(m).rotation(asQuaternion=True)


def q_angle(a, b):
    d = abs(a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w)
    return math.degrees(2.0 * math.acos(min(1.0, d)))


def solve(nodes, params, target=ss.TARGET_CTRL):
    s = bm.SecondaryMotionSession()
    s.prepare(nodes, ss.MODE_CHAIN, target, START, END)
    return s, s.solve(params)


def max_write_diff(a, b):
    worst = 0.0
    for node in a:
        for va, vb in zip(a[node], b[node]):
            worst = max(worst, max(abs(va[k] - vb[k]) for k in range(3)))
    return worst


try:
    cmds.file(new=True, force=True)
    cmds.playbackOptions(minTime=START, maxTime=END)
    top, ctls = build_ctrl_chain("A")
    key_parent_motion(top)

    phys = ps.PhysicsParams(swing1=40.0, swing2=40.0)
    kawaii = chain_solver.SolverParams()

    # ---------------- V2 핵심: 자식 회전 키와 무관
    _, w_plain = solve(ctls, phys)
    _, k_plain = solve(ctls, kawaii)
    key_child_curl(ctls)
    sess, w_curl = solve(ctls, phys)
    _, k_curl = solve(ctls, kawaii)
    d_phys = max_write_diff(w_plain, w_curl)
    d_kaw = max_write_diff(k_plain, k_curl)
    check("V2 physics result ignores child rotation keys", d_phys < 1e-9, "%.2e deg" % d_phys)
    check("V2 control: kawaii keeps child keys", d_kaw > 5.0, "%.2f deg" % d_kaw)

    # 결과 = 키를 굽고 씬에서 읽은 실제 월드 위치
    chain, anim_world = ss.physics_input(sess.samples[0], 0, phys.kinematic_root)
    pp0 = phys.copy()
    pp0.fps = sess.fps
    pts, W = ps.solve_physics(chain, pp0, anim_world)
    bm.outputs.get(bm.OUTPUT_KEYS).apply(sess, phys, w_curl)

    # ---------------- V5 왕복: 구운 회전으로 계산된 실제 위치/회전 == 솔버
    worst_p = worst_q = 0.0
    for fi, f in enumerate(sess.frames):
        for i, node in enumerate(ctls):
            p = world_pos(node, f)
            worst_p = max(worst_p, max(abs(p[k] - pts[fi][i][k]) for k in range(3)))
            if i < len(W[fi]):
                x, y, z, w = W[fi][i]
                worst_q = max(worst_q, q_angle(world_q(node, f), om.MQuaternion(x, y, z, w)))
    check("V5 baked world positions == solver", worst_p < 1e-6, "%.2e" % worst_p)
    check("V5 baked world rotations == solver", worst_q < 1e-4, "%.2e deg" % worst_q)

    # ---------------- V7 루트 위치는 애니메이션 그대로
    src = sess.samples[0].positions
    worst = max(max(abs(world_pos(ctls[0], f)[k] - src[fi][0][k]) for k in range(3))
                for fi, f in enumerate(sess.frames))
    check("V7 root position unchanged", worst < 1e-9, "%.2e" % worst)

    # ---------------- V1 정지 + Free: 매달린다 / Kawaii 는 그대로
    cmds.file(new=True, force=True)
    cmds.playbackOptions(minTime=START, maxTime=END)
    top, ctls = build_ctrl_chain("B")
    for c in ctls:
        cmds.setKeyframe(c, at="rotateX", t=START)
    free = ps.PhysicsParams(swing1_mode=ps.LIMIT_FREE, swing2_mode=ps.LIMIT_FREE,
                            kinematic_root=False, start=ps.START_SETTLED)
    s1, w1 = solve(ctls, free)
    bm.outputs.get(bm.OUTPUT_KEYS).apply(s1, free, w1)
    worst = 0.0
    for i in range(N - 1):
        a, b = world_pos(ctls[i], END), world_pos(ctls[i + 1], END)
        d = om.MVector(b[0] - a[0], b[1] - a[1], b[2] - a[2]).normal()
        worst = max(worst, math.degrees(d.angle(om.MVector(0, -1, 0))))
    check("V1 static chain hangs along gravity (scene)", worst < 5.0, "%.3f deg" % worst)
    rest_change = max(abs(w1[ctls[i]][0][k] - s1.samples[0].rest_local[i][k])
                      for i in range(N - 1) for k in range(3))
    check("V1 rotations differ from the original", rest_change > 30.0, "%.1f deg" % rest_change)
    cmds.file(new=True, force=True)
    cmds.playbackOptions(minTime=START, maxTime=END)
    top, ctls = build_ctrl_chain("B")
    for c in ctls:
        cmds.setKeyframe(c, at="rotateX", t=START)
    s1k, k1 = solve(ctls, chain_solver.SolverParams())
    worst = max(abs(k1[n][f][k] - s1k.samples[0].rest_local[i][k])
                for i, n in enumerate(ctls[:-1]) for f in range(len(k1[n])) for k in range(3))
    check("V1 control: kawaii keeps the static pose", worst < 1e-6, "%.2e" % worst)

    # ---------------- 조인트 체인 (JO · RA · RO) 왕복
    js = build_joint_chain("J")
    for f, v in ((1, 0), (30, 50), (60, -30), (120, 0)):
        cmds.setKeyframe(js[0], at="translateY", t=f, v=100 + v * 0.3)
        cmds.setKeyframe(js[1], at="rotateZ", t=f, v=v)      # 자식 키 - 무시돼야 한다
    pj = ps.PhysicsParams(swing1=35.0, swing2=20.0)
    sj, wj = solve(js, pj, ss.TARGET_JOINT)
    cmds.cutKey(js[1], at="rotateZ", clear=True)
    _, wj2 = solve(js, pj, ss.TARGET_JOINT)
    check("joint chain: child keys ignored", max_write_diff(wj, wj2) < 1e-9)
    chj, awj = ss.physics_input(sj.samples[0], 0, pj.kinematic_root)
    pp = pj.copy()
    pp.fps = sj.fps
    ptsj, Wj = ps.solve_physics(chj, pp, awj)
    bm.outputs.get(bm.OUTPUT_KEYS).apply(sj, pj, wj)
    worst = max(max(abs(world_pos(j, f)[k] - ptsj[fi][i][k]) for k in range(3))
                for fi, f in enumerate(sj.frames) for i, j in enumerate(js))
    check("joint chain round trip (JO/RA/RO)", worst < 1e-6, "%.2e" % worst)

    # ---------------- Override Layer 출력 + Rotate Axis + Blend 0 = 원본
    cmds.file(new=True, force=True)
    cmds.playbackOptions(minTime=START, maxTime=END)
    top, ctls = build_ctrl_chain("C")
    key_parent_motion(top)
    key_child_curl(ctls)
    s0 = bm.SecondaryMotionSession()
    s0.prepare(ctls, ss.MODE_CHAIN, ss.TARGET_CTRL, START, END)
    b0 = ps.PhysicsParams(blend=0.0)
    w0 = s0.solve(b0)
    worst = max(abs(w0[n][fi][k] - cmds.getAttr(n + ".rotate", time=f)[0][k])
                for n in w0 for fi, f in enumerate(s0.frames) for k in range(3))
    check("Physics Blend 0 = original animation", worst < 1e-6, "%.2e" % worst)
    s0.set_axes(("rotateY",))
    n, msg = s0.apply(ps.PhysicsParams(), bm.OUTPUT_LAYER)
    layers = cmds.ls(type="animLayer")
    check("override layer written", n == N and any(l.startswith("SM_") for l in layers), msg)

    # ---------------- 씬 단위 / 업 축 헬퍼
    check("unit helper cm", abs(ss.cm_per_scene_unit() - 1.0) < 1e-12)
    cmds.currentUnit(linear="m")
    check("unit helper m", abs(ss.cm_per_scene_unit() - 100.0) < 1e-12)
    cmds.currentUnit(linear="cm")
    check("up axis helper", ss.up_axis_index() == 1)

finally:
    print("\n{0}/{1} passed".format(passed, passed + failed))
    maya.standalone.uninitialize()
    os._exit(1 if failed else 0)
