# -*- coding: utf-8 -*-
# A00590_SwingTwistNative - 골든 시험: 원본 SwingTwistEvaluatorNode vs Framework/core/maya_swing_twist.build()
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_swing_twist_golden.py [samples]
#
# 같은 start/end 조인트에 원본 노드와 노드망을 나란히 걸고, 각자 다른 출력 조인트를 구동시킨 뒤
# 무작위 입력 · 블렌드에서 출력 조인트 rotate(오일러 값, 도) 와 회전 행렬을 비교한다(계획서 §5-1).
# 원본 플러그인은 MetaHumanForMaya 모듈 안의 것을 마야 버전에 맞춰 찾는다. 없으면 골든 비교는 SKIP.
import glob
import os
import random
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.api.OpenMaya as om   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import maya_swing_twist as ST   # noqa: E402

SAMPLES = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
EULER_TOL = 1e-9      # 도
MATRIX_TOL = 1e-9

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def find_plugin():
    ver = cmds.about(version=True)[:4]
    pattern = os.path.expanduser(
        "~/Documents/maya/modules/MetaHumanForMaya/lib/SwingTwistEvaluatorPlugin/*/platform-windows/"
        "maya-{0}/lib/SwingTwistEvaluatorPlugin.mll".format(ver))
    found = sorted(glob.glob(pattern))
    return found[-1] if found else None


def joint(name):
    cmds.select(clear=True)
    return cmds.joint(name=name)


def matrix_of(node):
    r = [om.MAngle(v, om.MAngle.kDegrees).asRadians() for v in cmds.getAttr(node + ".rotate")[0]]
    return om.MEulerRotation(r[0], r[1], r[2], om.MEulerRotation.kXYZ).asMatrix()


def compare(pairs):
    """(원본 출력 조인트, 노드망 출력 조인트) 쌍들의 최대 오일러 · 행렬 오차."""
    e_err = m_err = 0.0
    for a, b in pairs:
        ea = cmds.getAttr(a + ".rotate")[0]
        eb = cmds.getAttr(b + ".rotate")[0]
        e_err = max(e_err, max(abs(x - y) for x, y in zip(ea, eb)))
        ma, mb = matrix_of(a), matrix_of(b)
        m_err = max(m_err, max(abs(ma.getElement(r, c) - mb.getElement(r, c)) for r in range(3) for c in range(3)))
    return e_err, m_err


def setup(tag, n_twist, use_swing, from_end, use_end):
    """원본 노드 + 노드망을 같은 입력에 건다."""
    start = joint(tag + "_start")
    end = joint(tag + "_end") if use_end else None
    o_sw = joint(tag + "_origSwing") if use_swing else None
    n_sw = joint(tag + "_netSwing") if use_swing else None
    o_tw = [joint("{0}_origTwist{1}".format(tag, i)) for i in range(n_twist)]
    n_tw = [joint("{0}_netTwist{1}".format(tag, i)) for i in range(n_twist)]

    orig = cmds.createNode(ST.ORIGINAL_TYPE, name=tag + "_SwingTwistEvalNode")
    cmds.setAttr(orig + ".fromEnd", bool(from_end))
    cmds.connectAttr(start + ".rotate", orig + ".startJoint")
    if end:
        cmds.connectAttr(end + ".rotate", orig + ".endJoint")
    if o_sw:
        cmds.connectAttr(orig + ".swing", o_sw + ".rotate")
    for i, j in enumerate(o_tw):
        cmds.setAttr("{0}.twistBlend[{1}].values".format(orig, i), 0.0)
        cmds.connectAttr("{0}.twists[{1}]".format(orig, i), j + ".rotate")

    holder = ST.build(tag, start, end, n_sw, 0.0, n_tw, [0.0] * n_twist, from_end)
    pairs = ([(o_sw, n_sw)] if use_swing else []) + list(zip(o_tw, n_tw))
    return start, end, orig, holder, pairs


def set_blends(orig, holder, n_twist, sb, tbs):
    cmds.setAttr(orig + ".swingBlend", sb)
    ST.set_swing_blend(holder, sb)
    for i in range(n_twist):
        cmds.setAttr("{0}.twistBlend[{1}].values".format(orig, i), tbs[i])
        ST.set_twist_blend(holder, i, tbs[i])


def blend_value(rng, k):
    mode = k % 4
    if mode == 0:
        return 0.0
    if mode == 1:
        return 1.0
    if mode == 2:
        return rng.random()
    return rng.uniform(-0.5, 1.5)        # 외삽


def run_case(label, n_twist, use_swing, from_end, use_end, rng):
    cmds.file(new=True, force=True)
    start, end, orig, holder, pairs = setup("c", n_twist, use_swing, from_end, use_end)
    e_max = m_max = 0.0
    for k in range(SAMPLES):
        span = 60.0 if k % 2 else 180.0
        cmds.setAttr(start + ".rotate", *[rng.uniform(-span, span) for _ in range(3)])
        if end:
            cmds.setAttr(end + ".rotate", *[rng.uniform(-span, span) for _ in range(3)])
        set_blends(orig, holder, n_twist, blend_value(rng, k), [blend_value(rng, k + i + 1) for i in range(n_twist)])
        e, m = compare(pairs)
        e_max, m_max = max(e_max, e), max(m_max, m)
    check("{0}: euler (deg) <= {1}".format(label, EULER_TOL), e_max <= EULER_TOL, "max {0:.3g}".format(e_max))
    check("{0}: matrix <= {1}".format(label, MATRIX_TOL), m_max <= MATRIX_TOL, "max {0:.3g}".format(m_max))
    return holder


SPECIAL = [
    (0, 180, 0), (0, 0, 180), (180, 0, 0), (0, 180, 180), (180, 180, 0), (360, 0, 0), (0, 360, 0),
    (1e-7, 0, 0), (0, 1e-7, 0), (179.9999, 0, 0), (0, 179.9999, 0), (-180, 0, 0), (0, -180, 0),
    (90, 90, 90), (0, 90, 0), (0, -90, 0), (90, 0, 90), (720, 0, 0), (45, 180, 0), (0, 180, 45),
    (180, 90, 180), (0, 0, 0),
]


def run_special(from_end, rng):
    cmds.file(new=True, force=True)
    start, end, orig, holder, pairs = setup("s", 2, True, from_end, True)
    e_max = m_max = 0.0
    for rot in SPECIAL:
        for end_rot in (SPECIAL[0], SPECIAL[2], (0, 0, 0)):
            for sb, tb in ((0.0, 0.0), (1.0, 1.0), (0.5, 0.25)):
                cmds.setAttr(start + ".rotate", *rot)
                cmds.setAttr(end + ".rotate", *end_rot)
                set_blends(orig, holder, 2, sb, [tb, 1.0 - tb])
                e, m = compare(pairs)
                e_max, m_max = max(e_max, e), max(m_max, m)
    label = "special inputs fromEnd={0}".format(int(from_end))
    check(label + ": euler", e_max <= EULER_TOL, "max {0:.3g}".format(e_max))
    check(label + ": matrix", m_max <= MATRIX_TOL, "max {0:.3g}".format(m_max))


# ---------------------------------------------------------------- 골든
plugin = find_plugin()
if not plugin:
    print("SKIP golden comparison - SwingTwistEvaluatorPlugin not found for Maya {0}".format(cmds.about(version=True)))
else:
    cmds.loadPlugin(plugin, quiet=True)
    print("original plugin:", plugin)
    rng = random.Random(590)
    run_case("fromEnd=0 swing+3 twists", 3, True, False, False, rng)
    run_case("fromEnd=1 swing+3 twists (end joint)", 3, True, True, True, rng)
    run_case("swing only", 0, True, False, False, rng)
    run_case("twist only fromEnd=0", 2, False, False, False, rng)
    run_case("twist only fromEnd=1 (end joint)", 2, False, True, True, rng)
    run_case("fromEnd=1 without end joint", 2, True, True, False, rng)
    run_special(False, rng)
    run_special(True, rng)

print("")
print("{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
