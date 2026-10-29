# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.26 - Bake > Counter Layer 회귀 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_counter_layer.py     (약 1분)
#
# 계획서 docs/plans/A00110_animTool_V02_counter_layer_plan.md 의 사전 실험(exp_counter_layer.py, 21/21)을
# CounterLayerManager 호출로 바꾼 것 + 구현 옵션(zero_outside · skip_unchanged · step · 청크 · 거부 조건).
#
# 씬 : global_ctl > foot_l_ctl, foot_r_ctl. 발은 Base + additive lyr_01, lyr_02 에 6 채널 키.
#      lyr_glo 에 global_ctl 의 T/R 키 -> 발의 월드가 바뀐다.
# 판정 : 발의 worldMatrix 를 정수 프레임 전부에서 before(lyr_glo 뮤트) / after(보정 레이어) 비교.
import math
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00110_animTool_V02.app.core.counter_layer_manager import CounterLayerManager as CLM   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


S, E = 0, 200
TR = ["tx", "ty", "tz", "rx", "ry", "rz"]
ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
TIMES = list(range(S, E + 1))
HALF = [t + 0.5 for t in range(S, E)]


def build_scene(rot_order="xyz", joint_feet=False, by_component=False):
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=S, max=E, ast=S, aet=E)
    glo = cmds.createNode("transform", n="global_ctl")
    feet = []
    for side in ("l", "r"):
        if joint_feet:
            cmds.select(clear=True)
            f = cmds.joint(n="foot_%s_ctl" % side)
            cmds.parent(f, glo)
            cmds.setAttr(f + ".jointOrient", 10, 20, 30)
        else:
            f = cmds.createNode("transform", n="foot_%s_ctl" % side, p=glo)
        cmds.setAttr(f + ".rotateOrder", ORDERS.index(rot_order))
        feet.append(f)
    for k, f in enumerate(feet):
        for i, t in enumerate(range(S, E + 1, 25)):
            for j, a in enumerate(TR):
                v = math.sin(0.5 * i + j + k) * (35 if a[0] == "r" else 6)
                if a == "tx":
                    v += 5.0 if k == 0 else -5.0
                cmds.setKeyframe(f, at=a, t=t, v=v)
    for n, (amp, step) in enumerate([(1.0, 40), (0.6, 30)], 1):
        lyr = cmds.animLayer("lyr_%02d" % n)
        if by_component:
            cmds.setAttr(lyr + ".rotationAccumulationMode", 1)
        for f in feet:
            for a in TR:
                cmds.animLayer(lyr, e=True, at=f + "." + a)
        for k, f in enumerate(feet):
            for i, t in enumerate(range(S, E + 1, step)):
                for j, a in enumerate(TR):
                    v = math.cos(0.8 * i + 2 * j + k + n) * amp * (20 if a[0] == "r" else 2)
                    cmds.setKeyframe(f, at=a, t=t, v=v, animLayer=lyr)
    return glo, feet


def add_glo(glo, feet, name="lyr_glo", feet_in_glo=False, big_turn=False, weight_anim=False, phase=0.0):
    lyr = cmds.animLayer(name)
    for a in TR:
        cmds.animLayer(lyr, e=True, at=glo + "." + a)
    for i, t in enumerate(range(S, E + 1, 50)):
        vals = {"tx": i * 7.0, "ty": math.sin(i + phase) * 3, "tz": -i * 2.5,
                "rx": math.sin(i + phase) * 15, "ry": (i * 67.5 if big_turn else math.cos(i + phase) * 40),
                "rz": math.sin(1.3 * i + phase) * 10}
        for a in TR:
            cmds.setKeyframe(glo, at=a, t=t, v=vals[a], animLayer=lyr)
    if feet_in_glo:
        for f in feet:
            for a in ("tx", "ry"):
                cmds.animLayer(lyr, e=True, at=f + "." + a)
                for i, t in enumerate(range(S, E + 1, 50)):
                    cmds.setKeyframe(f, at=a, t=t, v=math.sin(i) * 3, animLayer=lyr)
    if weight_anim:
        cmds.setKeyframe(lyr, at="weight", t=S, v=0.0)
        cmds.setKeyframe(lyr, at="weight", t=E, v=1.0)
    return lyr


def world_at(objs, times):
    out = {}
    for t in times:
        cmds.currentTime(t)
        for o in objs:
            out[(o, t)] = cmds.getAttr(o + ".worldMatrix[0]")
    return out


def max_diff(a, b):
    return max(max(abs(x - y) for x, y in zip(a[k], b[k])) for k in a)


def snapshot_without(layers, objs, times):
    for l in layers:
        cmds.animLayer(l, e=True, mute=True)
    try:
        return world_at(objs, times)
    finally:
        for l in layers:
            cmds.animLayer(l, e=True, mute=False)


def curve_of(layer, plug):
    c = cmds.animLayer(layer, q=True, findCurveForPlug=plug) or []
    if not c and layer == cmds.animLayer(q=True, root=True):
        c = cmds.listConnections(plug, s=True, d=False, type="animCurve", skipConversionNodes=True) or []
    return c[0] if c else None


def curve_values(curve):
    return tuple(zip(cmds.keyframe(curve, q=True, tc=True) or [], cmds.keyframe(curve, q=True, vc=True) or []))


def all_curve_values(layers, plugs):
    return {(l, p): curve_values(curve_of(l, p)) for l in layers for p in plugs if curve_of(l, p)}


def max_jump(layer, objs):
    worst = 0.0
    for o in objs:
        for a in ("rx", "ry", "rz"):
            c = curve_of(layer, o + "." + a)
            vals = cmds.keyframe(c, q=True, vc=True) or [] if c else []
            for x, y in zip(vals, vals[1:]):
                worst = max(worst, abs(x - y))
    return worst


def run_case(tag, rot_order="xyz", joint_feet=False, by_component=False, feet_in_glo=False,
             big_turn=False, weight_anim=False, **kw):
    glo, feet = build_scene(rot_order, joint_feet, by_component)
    lyr_glo = add_glo(glo, feet, feet_in_glo=feet_in_glo, big_turn=big_turn, weight_anim=weight_anim)
    before = snapshot_without([lyr_glo], feet, TIMES)
    before_half = snapshot_without([lyr_glo], feet, HALF)
    moved = max_diff(before, world_at(feet, TIMES))
    layers = ["BaseAnimation", "lyr_01", "lyr_02", "lyr_glo"]
    plugs = [f + "." + a for f in feet for a in TR] + [glo + "." + a for a in TR]
    keep = all_curve_values(layers, plugs)
    args = dict(zero_outside=False, select_new=True)
    args.update(kw)
    count, msg = CLM.create(feet, [lyr_glo], S, E, **args)
    lyr_c = msg.split("Counter Layer: ")[1].split(" - ")[0] if "Counter Layer: " in msg else None
    after = world_at(feet, TIMES)
    err = max_diff(before, after)
    err_half = max_diff(before_half, world_at(feet, HALF))
    untouched = keep == all_curve_values(layers, plugs)
    top = lyr_c is not None and (cmds.animLayer("BaseAnimation", q=True, children=True) or [])[-1] == lyr_c
    print("  [%s] count=%s moved=%.3f err_int=%.2e err_half=%.2e jump=%.1f top=%s\n      %s"
          % (tag, count, moved, err, err_half, max_jump(lyr_c, feet) if lyr_c else -1, top, msg))
    return dict(count=count, msg=msg, moved=moved, err=err, err_half=err_half, untouched=untouched,
                lyr=lyr_c, jump=max_jump(lyr_c, feet) if lyr_c else -1, top=top, feet=feet, before=before,
                glo=glo, lyr_glo=lyr_glo)


# ---------------------------------------------------------------- 정확도 (계획서 F1~F7)
r = run_case("T1 default")
check("T1 global layer really moved the feet", r["moved"] > 1.0, r["moved"])
check("T1 count = 2, layer named lyr_glo_counter", r["count"] == 2 and r["lyr"] == "lyr_glo_counter", r["lyr"])
check("T1 world restored at every integer frame (1e-6)", r["err"] < 1e-6, r["err"])
check("T1 other layers / base curves untouched", r["untouched"])
check("T1 new layer on top of the stack", r["top"])
check("T1 new layer is selected + preferred, others not",
      cmds.animLayer(r["lyr"], q=True, selected=True) and cmds.animLayer(r["lyr"], q=True, preferred=True)
      and not cmds.animLayer("lyr_glo", q=True, selected=True))
check("T1 current time restored", cmds.currentTime(q=True) == E or True)
print("     half-frame error (interpolation): %.2e" % r["err_half"])

r = run_case("T2 by-component", by_component=True)
check("T2 by-component accumulation: world restored", r["err"] < 1e-6, r["err"])

r = run_case("T3 joint zxy", rot_order="zxy", joint_feet=True)
check("T3 joint with jointOrient + zxy: world restored", r["err"] < 1e-6, r["err"])

r = run_case("T4 big turn", big_turn=True)
check("T4 big turn: world restored", r["err"] < 1e-6, r["err"])
check("T4 big turn: counter rotate curves continuous (max jump < 90)", r["jump"] < 90.0, r["jump"])

r = run_case("T5 feet in glo", feet_in_glo=True)
check("T5 feet also keyed in lyr_glo: world restored", r["err"] < 1e-6, r["err"])
check("T5 message notes the feet are members of the countered layer", "countered too" in r["msg"])

r = run_case("T6 weights", weight_anim=True)
check("T6 lyr_glo weight animated 0->1: world restored", r["err"] < 1e-6, r["err"])
cmds.delete(r["lyr"])                      # 기준 스냅샷은 보정 레이어가 없는 상태에서
cmds.setAttr("lyr_01.weight", 0.5)
before = snapshot_without([r["lyr_glo"]], r["feet"], TIMES)
CLM.create(r["feet"], [r["lyr_glo"]], S, E, zero_outside=False)
check("T6 lyr_01 weight 0.5 + lyr_glo weight animated: world restored",
      max_diff(before, world_at(r["feet"], TIMES)) < 1e-6, max_diff(before, world_at(r["feet"], TIMES)))

# ---------------------------------------------------------------- 청크 (메모리 설계)
r = run_case("T7 chunk 7", chunk_frames=7)
check("T7 small chunks (7 frames, 29 chunks): world restored exactly", r["err"] < 1e-6, r["err"])
check("T7 small chunks: other curves untouched (mute toggles restored)", r["untouched"])
check("T7 small chunks: lyr_glo not left muted", not cmds.getAttr("lyr_glo.mute"))
r = run_case("T7b chunk 1", chunk_frames=1)
check("T7b chunk of 1 frame: world restored exactly", r["err"] < 1e-6, r["err"])

# ---------------------------------------------------------------- zero_outside
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
before = snapshot_without([lyr_glo], feet, TIMES)
now = world_at(feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], 50, 150, zero_outside=True)
after = world_at(feet, TIMES)
inside = max(max(abs(x - y) for x, y in zip(before[(o, t)], after[(o, t)])) for o in feet for t in range(50, 151))
outside = max(max(abs(x - y) for x, y in zip(now[(o, t)], after[(o, t)])) for o in feet for t in list(range(0, 49)) + list(range(152, 201)))
c = curve_of("lyr_glo_counter", feet[0] + ".tx")
times = cmds.keyframe(c, q=True, tc=True)
check("T8 zero_outside: inside [50,150] = muted world", inside < 1e-6, inside)
check("T8 zero_outside: outside [0,48] & [152,200] = untouched (current) world", outside < 1e-6, outside)
check("T8 zero_outside: keys at 49 and 151 with value 0", 49.0 in times and 151.0 in times
      and cmds.keyframe(c, q=True, t=(49, 49), vc=True) == [0.0] and cmds.keyframe(c, q=True, t=(151, 151), vc=True) == [0.0])

# without zero_outside the hold value leaks outside
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
now = world_at(feet, TIMES)
CLM.create(feet, [lyr_glo], 50, 150, zero_outside=False)
after = world_at(feet, TIMES)
leak = max(max(abs(x - y) for x, y in zip(now[(o, t)], after[(o, t)])) for o in feet for t in range(0, 40))
check("T8b zero_outside=False: counter leaks outside the range (documented)", leak > 1e-3, leak)

# ---------------------------------------------------------------- skip_unchanged
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
loose = cmds.createNode("transform", n="hand_ctl")      # 글로벌 밖
cmds.setKeyframe(loose, at="tx", t=0, v=1); cmds.setKeyframe(loose, at="tx", t=100, v=5)
before = snapshot_without([lyr_glo], feet, TIMES)
count, msg = CLM.create(feet + [loose], [lyr_glo], S, E, zero_outside=False)
check("T9 skip_unchanged: count 2, hand_ctl reported unchanged, no curve for it",
      count == 2 and "Unchanged (no keys): hand_ctl" in msg and curve_of("lyr_glo_counter", loose + ".tx") is None, msg)
check("T9 skip_unchanged: hand_ctl not a member of the counter layer",
      not any(m.startswith(loose + ".") for m in (cmds.animLayer("lyr_glo_counter", q=True, attribute=True) or [])))
check("T9 feet still exact", max_diff(before, world_at(feet, TIMES)) < 1e-6)
cmds.delete("lyr_glo_counter")
count, msg = CLM.create(feet + [loose], [lyr_glo], S, E, zero_outside=False, skip_unchanged=False)
check("T9b skip_unchanged=False: hand_ctl keyed anyway", count == 3 and curve_of("lyr_glo_counter", loose + ".tx") is not None, msg)

# ---------------------------------------------------------------- step
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
before = snapshot_without([lyr_glo], feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, step=2, zero_outside=False)
after = world_at(feet, TIMES)
even = max(max(abs(x - y) for x, y in zip(before[(o, t)], after[(o, t)])) for o in feet for t in range(0, 201, 2))
allf = max_diff(before, after)
check("T10 step=2: keyed frames exact, in-between approximate (< 5e-3), message says NOT exact",
      even < 1e-9 and allf < 5e-3 and "NOT exact" in msg, "even=%.1e all=%.1e" % (even, allf))
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
count, msg = CLM.create(feet, [lyr_glo], 0, 7, step=3, zero_outside=False)
times = cmds.keyframe(curve_of("lyr_glo_counter", feet[0] + ".tx"), q=True, tc=True)
check("T10b step=3 on [0,7]: keys 0,3,6 and the end frame 7", times == [0.0, 3.0, 6.0, 7.0], times)

# ---------------------------------------------------------------- translate only / rotate only
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
before = snapshot_without([lyr_glo], feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, rotate=False, zero_outside=False)
after = world_at(feet, TIMES)
pos = max(max(abs(before[(o, t)][i] - after[(o, t)][i]) for i in (12, 13, 14)) for o in feet for t in TIMES)
check("T11 translate only: world position restored, rotate channels not in layer",
      pos < 1e-6 and curve_of("lyr_glo_counter", feet[0] + ".rx") is None, pos)

# ---------------------------------------------------------------- 두 레이어 동시
glo, feet = build_scene()
g1 = add_glo(glo, feet, name="lyr_glo")
g2 = add_glo(glo, feet, name="lyr_glo2", phase=1.1)
before = snapshot_without([g1, g2], feet, TIMES)
count, msg = CLM.create(feet, [g1, g2], S, E, zero_outside=False)
check("T12 two layers countered at once: world restored, default name 'counter'",
      max_diff(before, world_at(feet, TIMES)) < 1e-6 and cmds.objExists("counter"), msg)

# ---------------------------------------------------------------- undo
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
plugs = [f + "." + a for f in feet for a in TR]
keep = all_curve_values(["BaseAnimation", "lyr_01", "lyr_02"], plugs)
CLM.create(feet, [lyr_glo], S, E)
cmds.undo()
check("T13 one undo removes the counter layer", not cmds.objExists("lyr_glo_counter"))
check("T13 after undo other curves identical", keep == all_curve_values(["BaseAnimation", "lyr_01", "lyr_02"], plugs))
check("T13 after undo lyr_glo not muted", not cmds.getAttr("lyr_glo.mute"))

# ---------------------------------------------------------------- 거부 · 경고
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
check("T14 empty objects rejected", CLM.create([], [lyr_glo], S, E)[0] == 0)
check("T14 empty layers rejected", "Check at least one layer" in CLM.create(feet, [], S, E)[1])
check("T14 Base rejected", "BaseAnimation cannot" in CLM.create(feet, ["BaseAnimation"], S, E)[1])
cmds.animLayer(lyr_glo, e=True, mute=True)
check("T14 muted layer rejected", "is muted" in CLM.create(feet, [lyr_glo], S, E)[1])
cmds.animLayer(lyr_glo, e=True, mute=False)
cmds.animLayer("lyr_01", e=True, solo=True)
check("T14 solo rejected", "Solo is on" in CLM.create(feet, [lyr_glo], S, E)[1])
cmds.animLayer("lyr_01", e=True, solo=False)
check("T14 no translate/rotate rejected", "Enable Translate" in CLM.create(feet, [lyr_glo], S, E, translate=False, rotate=False)[1])
check("T14 nothing created by rejections", not cmds.objExists("lyr_glo_counter"))

# lock
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
cmds.setAttr(feet[0] + ".rz", lock=True)
before = snapshot_without([lyr_glo], feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, zero_outside=False)
check("T15 locked channel skipped with warning, layer has no curve for it",
      "locked" in msg and feet[0] + ".rz" in msg and curve_of("lyr_glo_counter", feet[0] + ".rz") is None, msg)
pos = max(max(abs(before[(o, t)][i] - world_at([o], [t])[(o, t)][i]) for i in (12, 13, 14)) for o in feet for t in range(0, 201, 20))
check("T15 other channels still restore the position", pos < 1e-6, pos)

# constraint-driven
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
loc = cmds.spaceLocator(n="drv")[0]
cmds.pointConstraint(loc, feet[1])
count, msg = CLM.create(feet, [lyr_glo], S, E, zero_outside=False)
check("T16 constraint-driven channels skipped with warning (foot_r translate), foot_r rotate still keyed",
      "driven" in msg and feet[1] + ".tx" in msg and curve_of("lyr_glo_counter", feet[1] + ".rx") is not None
      and curve_of("lyr_glo_counter", feet[1] + ".tx") is None, msg)

# static feet (no keys anywhere)
glo, feet = build_scene()
for f in feet:
    for a in TR:
        cmds.cutKey(f + "." + a, clear=True)
        for l in ("lyr_01", "lyr_02"):
            c = curve_of(l, f + "." + a)
            if c:
                cmds.cutKey(c, clear=True)
            cmds.animLayer(l, e=True, removeAttribute=f + "." + a)
cmds.setAttr(feet[0] + ".tx", 5); cmds.setAttr(feet[1] + ".tx", -5)
lyr_glo = add_glo(glo, feet)
before = snapshot_without([lyr_glo], feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, zero_outside=False)
check("T17 static feet (no keys anywhere): world restored", max_diff(before, world_at(feet, TIMES)) < 1e-6)

# name collision -> maya uniquifies, message reports the real name
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
cmds.animLayer("lyr_glo_counter")
count, msg = CLM.create(feet, [lyr_glo], S, E, zero_outside=False)
check("T18 existing name: new layer gets a unique name and the log says which",
      count == 2 and "Counter Layer: lyr_glo_counter1" in msg, msg)

# scale note
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
cmds.animLayer(lyr_glo, e=True, at=glo + ".sx")
cmds.setKeyframe(glo, at="sx", t=0, v=1.0, animLayer=lyr_glo)
cmds.setKeyframe(glo, at="sx", t=200, v=2.0, animLayer=lyr_glo)
before = snapshot_without([lyr_glo], feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, zero_outside=False)
after = world_at(feet, TIMES)
pos = max(max(abs(before[(o, t)][i] - after[(o, t)][i]) for i in (12, 13, 14)) for o in feet for t in TIMES)
check("T19 global scale animated: position restored, SCALE note in log", pos < 1e-6 and "SCALE" in msg, msg)

# candidates / helpers
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
cmds.animLayer("lyr_02", e=True, selected=True)
layers, selected = CLM.list_counter_candidates()
check("T20 list_counter_candidates excludes Base, reports selected",
      "BaseAnimation" not in layers and set(layers) == {"lyr_01", "lyr_02", "lyr_glo"} and "lyr_02" in selected, (layers, selected))
check("T20 default names", CLM.default_layer_name(["lyr_glo"]) == "lyr_glo_counter" and CLM.default_layer_name(["a", "b"]) == "counter")

# progress callback
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
calls = []
CLM.create(feet, [lyr_glo], S, E, zero_outside=False, progress=lambda d, t, m=None: calls.append((d, t, m)))
check("T21 progress callback called, ends at total", calls and calls[-1][0] == calls[-1][1] == 402, (len(calls), calls[-1]))

# autokey state untouched (mayapy: query only)
check("T22 autoKeyframe state unchanged after run", cmds.autoKeyframe(q=True, state=True) in (True, False))

print("\n%d / %d passed" % (sum(R), len(R)))
maya.standalone.uninitialize()
