# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 0단계 실측 (계획서 §5 0단계 0-1 · 0-2 · 0-3 · 0-8)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" bench_motion_path.py [frames] [--light]
# 표를 출력한다. 결과는 계획서 §10 에 옮겨 적는다.
import os
import sys
import time

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.api.OpenMaya as om   # noqa: E402
import maya.api.OpenMayaAnim as oma   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenes   # noqa: E402

FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 120
LIGHT = "--light" in sys.argv


def plug_of(node, attr):
    sel = om.MSelectionList()
    sel.add(node + "." + attr)
    return sel.getPlug(0)


def matrix_at(plug, ctx):
    prev = ctx.makeCurrent()
    try:
        return om.MFnMatrixData(plug.asMObject()).matrix()
    finally:
        prev.makeCurrent()


def bake_a(node, f0, f1):
    """A : parentMatrix plug 만 시간 문맥으로."""
    plug = plug_of(node, "parentMatrix[0]")
    unit = om.MTime.uiUnit()
    out = []
    for f in range(f0, f1 + 1):
        out.append(matrix_at(plug, om.MDGContext(om.MTime(f, unit))))
    return out


def bake_b(node, f0, f1):
    """B : cmds.getAttr -time."""
    return [cmds.getAttr(node + ".parentMatrix[0]", time=f) for f in range(f0, f1 + 1)]


def bake_c(node, f0, f1):
    """C : currentTime(update=False) + plug 읽기 (끝나고 시간을 되돌린다)."""
    plug = plug_of(node, "parentMatrix[0]")
    keep = cmds.currentTime(q=True)
    out = []
    try:
        for f in range(f0, f1 + 1):
            cmds.currentTime(f, update=False)
            out.append(om.MFnMatrixData(plug.asMObject()).matrix())
    finally:
        cmds.currentTime(keep, update=False)
    return out


def bake_d(node, f0, f1):
    """D : 마야 Editable Motion Trail (만들기 + 점 계산)."""
    trail = cmds.snapshot(node, motionTrail=True, increment=1, startTime=f0, endTime=f1)
    shape = cmds.listRelatives(trail[0], shapes=True) or trail
    for s in shape:
        if cmds.attributeQuery("points", node=s, exists=True):
            cmds.getAttr(s + ".points")
    for t in trail:
        if cmds.objExists(t):
            cmds.delete(t)


def own_curves(node):
    out = []
    for a in ("translateX", "translateY", "translateZ"):
        src = cmds.listConnections(node + "." + a, source=True, destination=False, type="animCurve") or []
        if src:
            sel = om.MSelectionList()
            sel.add(src[0])
            out.append(oma.MFnAnimCurve(sel.getDependNode(0)))
    return out


def eval_curves(curves, f0, f1):
    unit = om.MTime.uiUnit()
    return [[c.evaluate(om.MTime(f, unit)) for c in curves] for f in range(f0, f1 + 1)]


def timed(fn, *args, repeat=1):
    best = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn(*args)
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    return best


def check_values(node, f0, f1, step):
    """0-2 · 0-8 : A 로 구운 parentMatrix 로 만든 피벗 점 = worldMatrix -time 의 피벗 점."""
    pm = bake_a(node, f0, f1)
    worst = 0.0
    is_joint = cmds.objectType(node) == "joint"
    for i, f in enumerate(range(f0, f1 + 1, step)):
        k = f - f0
        wm = om.MMatrix(cmds.getAttr(node + ".worldMatrix[0]", time=f))
        rp = om.MPoint(cmds.getAttr(node + ".rotatePivot", time=f)[0]) if not is_joint else om.MPoint(0, 0, 0)
        world = rp * wm
        # c + T 를 그 프레임 local 로: P = (c + T) * PM
        local = world * pm[k].inverse()
        T = cmds.getAttr(node + ".translate", time=f)[0]
        c = (local.x - T[0], local.y - T[1], local.z - T[2])
        # c 를 0 으로 보면 되는가(조인트 · 피벗 0) 는 따로 보고, 여기서는 P 를 다시 만든 값 비교
        again = om.MPoint(c[0] + T[0], c[1] + T[1], c[2] + T[2]) * pm[k]
        worst = max(worst, (again - world).length())
    return worst


def c_size(node, f0, f1):
    """c(f) 의 최대 크기 - 조인트 · 피벗 0 이면 0 이어야 한다."""
    pm = bake_a(node, f0, f1)
    is_joint = cmds.objectType(node) == "joint"
    biggest = 0.0
    for k, f in enumerate(range(f0, f1 + 1, max(1, (f1 - f0) // 10))):
        k = f - f0
        wm = om.MMatrix(cmds.getAttr(node + ".worldMatrix[0]", time=f))
        rp = om.MPoint(0, 0, 0) if is_joint else om.MPoint(cmds.getAttr(node + ".rotatePivot", time=f)[0])
        local = (rp * wm) * pm[k].inverse()
        T = cmds.getAttr(node + ".translate", time=f)[0]
        biggest = max(biggest, abs(local.x - T[0]), abs(local.y - T[1]), abs(local.z - T[2]))
    return biggest


print("=" * 72)
print("A00630 bench - frames 1..{0}".format(FRAMES))

# ---- 0-2 / 0-8 : 값 확인 (단순 · 계층)
names = scenes.simple(FRAMES)
for key in ("plain", "pivot", "opm", "partial"):
    print("[0-2] simple {0:8s} : rebuild error {1:.2e}   |c| max {2:.4f}".format(
        key, check_values(names[key], 1, FRAMES, 7), c_size(names[key], 1, FRAMES)))
names = scenes.hierarchy(FRAMES)
for key in ("ctrl", "joint"):
    print("[0-2] hierarchy {0:6s} : rebuild error {1:.2e}   |c| max {2:.4f}".format(
        key, check_values(names[key], 1, FRAMES, 7), c_size(names[key], 1, FRAMES)))

# ---- 0-1 : 굽기 시간
rows = []
for label, builder in (("simple", lambda: scenes.simple(FRAMES)["plain"]),
                       ("hierarchy", lambda: scenes.hierarchy(FRAMES)["ctrl"]),
                       ("heavy", lambda: scenes.heavy(FRAMES, mesh_div=(120, 80) if LIGHT else (400, 250))["ctrl"])):
    t0 = time.perf_counter()
    node = builder()
    build = time.perf_counter() - t0
    a = timed(bake_a, node, 1, FRAMES)
    b = timed(bake_b, node, 1, FRAMES)
    c = timed(bake_c, node, 1, FRAMES)
    try:
        d = timed(bake_d, node, 1, FRAMES)
    except Exception as exc:                      # noqa: BLE001
        d = None
        print("  motionTrail failed:", exc)
    curves = own_curves(node)
    e = timed(eval_curves, curves, 1, FRAMES, repeat=3)
    # C 값 = A 값 인가
    va, vc = bake_a(node, 1, FRAMES), bake_c(node, 1, FRAMES)
    diff = max(max(abs(x - y) for x, y in zip(list(ma), list(mc))) for ma, mc in zip(va, vc))
    # 키 하나 바꾼 뒤 다시 계산 : D(트레일 점 다시 읽기) 대 우리(커브만 다시 평가)
    trail = cmds.snapshot(node, motionTrail=True, increment=1, startTime=1, endTime=FRAMES)
    shapes = [s for s in (cmds.listRelatives(trail[0], shapes=True) or []) + trail
              if cmds.attributeQuery("points", node=s, exists=True)]
    cmds.getAttr(shapes[0] + ".points")
    cmds.keyframe(node + ".translateY", index=(1, 1), relative=True, valueChange=0.5)
    t0 = time.perf_counter()
    cmds.getAttr(shapes[0] + ".points")
    d_edit = time.perf_counter() - t0
    for t in trail:
        if cmds.objExists(t):
            cmds.delete(t)
    rows.append((label, build, a, b, c, d, e, diff, d_edit))

print("-" * 72)
print("{0:10s} {1:>8s} {2:>9s} {3:>9s} {4:>9s} {5:>9s} {6:>9s} {7:>10s} {8:>9s}".format(
    "scene", "build s", "A ctx", "B getAttr", "C time", "D trail", "curves", "C-A diff", "D edit"))
for label, build, a, b, c, d, e, diff, d_edit in rows:
    print("{0:10s} {1:8.2f} {2:9.4f} {3:9.4f} {4:9.4f} {5:>9s} {6:9.4f} {7:10.1e} {8:9.4f}".format(
        label, build, a, b, c, "{0:.4f}".format(d) if d is not None else "n/a", e, diff, d_edit))
print("(seconds, best of 1; curves = 3 translate curves evaluated, best of 3)")

maya.standalone.uninitialize()
os._exit(0)
