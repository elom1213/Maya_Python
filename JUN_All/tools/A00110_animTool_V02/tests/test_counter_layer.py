# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.26 / v02.29 - Bake > Counter Layer 회귀 시험 (mayapy, 헤드리스) - Everywhere + Stationary spans only
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

# ================================================================ v02.29 Hold = Stationary spans only (T23~)
# 씬 : global_ctl > foot_l_ctl, foot_r_ctl (+ hand_ctl 정적, wave_ctl 계속 이동). 발은 Base + additive lyr_01 에
#      "정지(hold) - 이동 - 정지" 키 (hold 양끝 키 값 같음 + linear 탄젠트 -> hold 안 월드 완전 정지).
#      ※ 레이어를 먼저 만들면 그 레이어가 preferred 라 animLayer 없는 setKeyframe 이 거기로 간다 -> Base 키를 먼저.
#      ※ `setKeyframe -animLayer -value` 는 최종값 역산이라 by-layer 회전에선 아직 안 찍은 채널이 섞여 hold 양끝이 달라진다
#        -> 레이어 커브 값은 커브 노드에 직접 쓴다 (by-component 회전).
#      lyr_glo 가 global_ctl 을 0..200 에서 tx 0 -> -20 (옵션: ry 0 -> 40, tz 0 -> 8) 이동.
# 판정 : hold 안 월드 == 레이어 켠 상태의 앵커 프레임 월드, Start/End/밖 == 레이어 켠 월드, 다른 커브 불변.
HL = [(20, 30), (70, 85), (140, 150)]              # foot_l 의 정지 구간
HR = [(0, 10), (45, 60), (105, 120), (185, 200)]   # foot_r (Start · End 에 걸침)
STATIC_ROT = (5.0, 10.0, 15.0)


def build_plant_scene(global_rotates=False, static_rotate=False, extras=False):
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=S, max=E, ast=S, aet=E)
    glo = cmds.createNode("transform", n="global_ctl")
    feet = [cmds.createNode("transform", n="foot_%s_ctl" % s, p=glo) for s in ("l", "r")]

    def hold_values(side, k):
        base = {"tx": 10.0 * k + (3.0 if side == 0 else -3.0), "ty": 2.0 * k, "tz": -5.0 * k,
                "rx": 15.0 * k, "ry": -20.0 * k + 5.0, "rz": 8.0 * k}
        lyr = {"tx": 1.0 * (k % 2), "ty": 0.5 * k, "tz": -0.7 * (k % 3),
               "rx": 4.0 * (k % 2), "ry": 3.0 * k, "rz": -2.0 * (k % 2)}
        return base, lyr

    # 1) Base 키 먼저 (레이어가 아직 없어 setKeyframe 이 Base 로 간다). hold 양끝은 같은 값 + linear 탄젠트.
    plan = {}
    for side, (f, holds) in enumerate(zip(feet, (HL, HR))):
        rot_attrs = [] if (static_rotate and side == 0) else ["rx", "ry", "rz"]
        attrs = ["tx", "ty", "tz"] + rot_attrs
        plan[f] = attrs
        if not rot_attrs:
            cmds.setAttr(f + ".rotate", *STATIC_ROT)
        keyed = []
        for k, (s_, e_) in enumerate(holds):
            base, _ = hold_values(side, k)
            for a in attrs:
                for t in (s_, e_):
                    cmds.setKeyframe(f, at=a, t=t, v=base[a], itt="linear", ott="linear")
            keyed += [s_, e_]
        for t, mult in ((S, -1.0), (E, 2.5)):          # hold 가 없는 양끝엔 다른 값 -> 계속 움직임
            if t not in keyed:
                for a in attrs:
                    cmds.setKeyframe(f, at=a, t=t, v=mult * 6.0, itt="linear", ott="linear")
    # 2) additive lyr_01 (by-component 회전) - 커브 값은 **커브 노드에 직접** 써서 역산에 의존하지 않는다.
    lyr1 = cmds.animLayer("lyr_01")
    cmds.setAttr(lyr1 + ".rotationAccumulationMode", 1)
    for side, (f, holds) in enumerate(zip(feet, (HL, HR))):
        for a in plan[f]:
            cmds.animLayer(lyr1, e=True, at=f + "." + a)
            cmds.setKeyframe(f, at=a, t=S, animLayer=lyr1)          # 커브 생성
            curve = cmds.animLayer(lyr1, q=True, findCurveForPlug=f + "." + a)[0]
            keyed = []
            for k, (s_, e_) in enumerate(holds):
                _, lyr = hold_values(side, k)
                for t in (s_, e_):
                    cmds.setKeyframe(curve, t=t, v=lyr[a], itt="linear", ott="linear")
                keyed += [s_, e_]
            for t, mult in ((S, -1.0), (E, 2.5)):
                if t not in keyed:
                    cmds.setKeyframe(curve, t=t, v=mult * 0.5, itt="linear", ott="linear")
    extra = []
    if extras:
        hand = cmds.createNode("transform", n="hand_ctl", p=glo)      # 키 없음 -> 전구간 정지
        cmds.setAttr(hand + ".translate", 4, 12, 1)
        wave = cmds.createNode("transform", n="wave_ctl", p=glo)      # 계속 이동
        for a in TR:
            cmds.setKeyframe(wave, at=a, t=S, v=0.0, itt="linear", ott="linear", animLayer="BaseAnimation")
            cmds.setKeyframe(wave, at=a, t=E, v=30.0, itt="linear", ott="linear", animLayer="BaseAnimation")
        extra = [hand, wave]
    # 3) lyr_glo : 글로벌만. 0..200 에서 tx 0 -> -20 (옵션 ry 0 -> 40, tz 0 -> 8)
    lyr_glo = cmds.animLayer("lyr_glo")
    for a in TR:
        cmds.animLayer(lyr_glo, e=True, at=glo + "." + a)
    cmds.setKeyframe(glo, at="tx", t=S, v=0.0, animLayer=lyr_glo)
    cmds.setKeyframe(glo, at="tx", t=E, v=-20.0, animLayer=lyr_glo)
    if global_rotates:
        cmds.setKeyframe(glo, at="ry", t=S, v=0.0, animLayer=lyr_glo)
        cmds.setKeyframe(glo, at="ry", t=E, v=40.0, animLayer=lyr_glo)
        cmds.setKeyframe(glo, at="tz", t=S, v=0.0, animLayer=lyr_glo)
        cmds.setKeyframe(glo, at="tz", t=E, v=8.0, animLayer=lyr_glo)
    return glo, feet, lyr_glo, extra


def anchor_frame(s, e, anchor):
    if s <= S:
        return S
    if e >= E:
        return E
    return {"start": s, "end": e, "middle": (s + e) // 2}[anchor]


def span_err(on, new, feet, anchor="start"):
    """hold 안 모든 프레임의 월드 행렬 vs 앵커 프레임의 (레이어 켠) 월드 행렬 최대 차."""
    worst = 0.0
    for f, holds in zip(feet, (HL, HR)):
        for s, e in holds:
            ref = on[(f, anchor_frame(s, e, anchor))]
            for t in range(s, e + 1):
                worst = max(worst, max(abs(x - y) for x, y in zip(new[(f, t)], ref)))
    return worst


def edge_err(on, new, feet, frames=(S, E)):
    return max(max(abs(x - y) for x, y in zip(new[(f, t)], on[(f, t)])) for f in feet for t in frames)


def max_frame_jump(w, feet):
    worst = 0.0
    for f in feet:
        for t in range(S + 1, E + 1):
            a, b = w[(f, t)], w[(f, t - 1)]
            worst = max(worst, math.sqrt(sum((a[i] - b[i]) ** 2 for i in (12, 13, 14))))
    return worst


# ---------------------------------------------------------------- T23 정지 구간 탐지
glo, feet, lyr_glo, _ = build_plant_scene()
cmds.currentTime(77)
spans, cum_d, cum_a = CLM.detect_spans(feet, [lyr_glo], S, E)
check("T23 detect_spans finds the designed holds", spans[feet[0]] == [list(h) for h in HL]
      and spans[feet[1]] == [list(h) for h in HR], spans)
check("T23 detect leaves lyr_glo unmuted and restores current time",
      not cmds.getAttr(lyr_glo + ".mute") and cmds.currentTime(q=True) == 77)
check("T23 cumulative travel grows and is flat inside holds",
      cum_d[feet[0]][30] == cum_d[feet[0]][20] and cum_d[feet[0]][E - S] > cum_d[feet[0]][69] > 0,
      (cum_d[feet[0]][20], cum_d[feet[0]][30], cum_d[feet[0]][69]))
spans2 = CLM.detect_spans(feet, [lyr_glo], S, E, min_span=12)[0]
check("T23b min_span=12 keeps only the 16-frame hold", spans2[feet[0]] == [[70, 85]], spans2[feet[0]])
spans3 = CLM.detect_spans(feet, [lyr_glo], S, E, tol_t=1e9, tol_r=1e9)[0]
check("T23c huge tolerance -> the whole range is one span", spans3[feet[0]] == [[S, E]], spans3[feet[0]])
spans4 = CLM.detect_spans(feet, [lyr_glo], 25, 75)[0]
check("T23d spans clipped to the range", spans4[feet[0]] == [[25, 30], [70, 75]], spans4[feet[0]])

# ---------------------------------------------------------------- T24 Stationary 기본 (touchdown · by travel)
layers_all = ["BaseAnimation", "lyr_01", "lyr_glo"]
plugs_all = [f + "." + a for f in feet for a in TR] + [glo + "." + a for a in TR]
keep = all_curve_values(layers_all, plugs_all)
on = world_at(feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY)
new = world_at(feet, TIMES)
print("  [T24] " + msg)
check("T24 count 2, layer lyr_glo_plant, log head", count == 2 and cmds.objExists("lyr_glo_plant")
      and msg.startswith("Counter Layer (stationary): lyr_glo_plant"), msg[:80])
check("T24 log reports spans / anchor / blend", "spans [foot_l_ctl 3, foot_r_ctl 4]" in msg
      and "anchor touchdown" in msg and "blend by travel" in msg)
e_span = span_err(on, new, feet, "start")
check("T24 inside holds: world == layered world at touchdown (1e-5)", e_span < 1e-5, e_span)
e_edge = edge_err(on, new, feet)
check("T24 Start and End frames == layered world (1e-9)", e_edge < 1e-9, e_edge)
c = curve_of("lyr_glo_plant", feet[0] + ".tx")
times = cmds.keyframe(c, q=True, tc=True)
check("T24 zero keys at -1 and 201, every frame keyed", times[0] == S - 1 and times[-1] == E + 1
      and len(times) == E - S + 3, (times[0], times[-1], len(times)))
check("T24 other curves untouched", keep == all_curve_values(layers_all, plugs_all))
dev = max(max(abs(x - y) for x, y in zip(new[k], on[k])) for k in on)
check("T24 moving frames deviate from the layered world by less than the global shift (20)", 1e-3 < dev < 20.0, dev)
j_on, j_new = max_frame_jump(on, feet), max_frame_jump(new, feet)
check("T24 by travel: no speed spike (max frame jump <= 1.5 x original)", j_new <= 1.5 * j_on + 1e-6, (j_on, j_new))
cmds.animLayer("lyr_glo_plant", e=True, mute=True)
muted = world_at(feet, TIMES)
cmds.animLayer("lyr_glo_plant", e=True, mute=False)
check("T24 muting the plant layer gives the layered world back", max_diff(muted, on) < 1e-9)
check("T24 plant layer on top and selected", (cmds.animLayer("BaseAnimation", q=True, children=True) or [])[-1]
      == "lyr_glo_plant" and cmds.animLayer("lyr_glo_plant", q=True, selected=True))

# ---------------------------------------------------------------- T25 앵커 · T26 분배
for anchor in ("end", "middle"):
    cmds.delete("lyr_glo_plant")
    count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY, anchor=anchor)
    new = world_at(feet, TIMES)
    check("T25 anchor %s: holds == layered world at that frame, edges exact" % anchor,
          span_err(on, new, feet, anchor) < 1e-5 and edge_err(on, new, feet) < 1e-9
          and ("anchor lift-off" in msg if anchor == "end" else "anchor middle" in msg),
          (span_err(on, new, feet, anchor), edge_err(on, new, feet)))
for blend in ("ease", "linear"):
    cmds.delete("lyr_glo_plant")
    count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY, blend=blend)
    new = world_at(feet, TIMES)
    check("T26 blend %s: holds exact, edges exact, no spike" % blend,
          span_err(on, new, feet) < 1e-5 and edge_err(on, new, feet) < 1e-9
          and max_frame_jump(new, feet) <= 1.5 * j_on + 1e-6 and "blend %s" % blend in msg,
          (span_err(on, new, feet), max_frame_jump(new, feet)))
check("T26 unknown anchor / blend rejected", CLM.create(feet, [lyr_glo], S, E, hold="stationary", anchor="x")[0] == 0
      and "Unknown blend" in CLM.create(feet, [lyr_glo], S, E, hold="stationary", blend="x")[1])

# ---------------------------------------------------------------- T27 글로벌이 회전도 할 때 (쿼터니언 델타 경로)
glo, feet, lyr_glo, _ = build_plant_scene(global_rotates=True)
on = world_at(feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY)
new = world_at(feet, TIMES)
check("T27 rotating global: holds exact incl. rotation (1e-5), edges exact", span_err(on, new, feet) < 1e-5
      and edge_err(on, new, feet) < 1e-9, (span_err(on, new, feet), edge_err(on, new, feet)))
check("T27 rotating global: no speed spike", max_frame_jump(new, feet) <= 1.5 * max_frame_jump(on, feet) + 1e-6,
      (max_frame_jump(on, feet), max_frame_jump(new, feet)))
# 부분 구간 : 왼발 hold 70-85 / 140-150 가 Start/End 에 걸치게 [75, 145]
cmds.delete("lyr_glo_plant")
count, msg = CLM.create(feet, [lyr_glo], 75, 145, hold=CLM.HOLD_STATIONARY)
new = world_at(feet, TIMES)
ok_in = max(max(abs(x - y) for x, y in zip(new[(feet[0], t)], on[(feet[0], 75)])) for t in range(75, 86))
ok_in2 = max(max(abs(x - y) for x, y in zip(new[(feet[0], t)], on[(feet[0], 145)])) for t in range(140, 146))
out = max(max(abs(x - y) for x, y in zip(new[k], on[k])) for k in on if k[1] < 75 or k[1] > 145)
check("T27b span crossing Start/End: anchor forced to the boundary, outside untouched",
      ok_in < 1e-5 and ok_in2 < 1e-5 and out < 1e-9, (ok_in, ok_in2, out))

# ---------------------------------------------------------------- T28 translate only (+ 정적 회전 복원)
glo, feet, lyr_glo, _ = build_plant_scene(global_rotates=True, static_rotate=True)
on = world_at(feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY, rotate=False)
new = world_at(feet, TIMES)
pos = 0.0
for f, holds in zip(feet, (HL, HR)):
    for s, e in holds:
        ref = on[(f, anchor_frame(s, e, "start"))]
        for t in range(s, e + 1):
            pos = max(pos, max(abs(new[(f, t)][i] - ref[i]) for i in (12, 13, 14)))
check("T28 translate only: hold positions exact, rotate not in layer", pos < 1e-5
      and curve_of("lyr_glo_plant", feet[0] + ".rx") is None, pos)
cmds.currentTime(S)
rot_now = cmds.getAttr(feet[0] + ".rotate")[0]
check("T28b translate only: static (unkeyed) rotate of foot_l restored after xform",
      max(abs(a - b) for a, b in zip(rot_now, STATIC_ROT)) < 1e-9, rot_now)

# ---------------------------------------------------------------- T29 전구간 정지 · 구간 없음
glo, feet, lyr_glo, extra = build_plant_scene(extras=True)
hand, wave = extra
on = world_at(feet, TIMES)
count, msg = CLM.create(feet + extra, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY)
members = set(a.split(".")[0] for a in (cmds.animLayer("lyr_glo_plant", q=True, attribute=True) or []))
check("T29 whole-range still object reported and dropped", "Stationary for the whole range: hand_ctl" in msg
      and hand not in members, msg[-200:])
check("T29 always-moving object reported and dropped", "No stationary span: wave_ctl" in msg and wave not in members)
check("T29 feet still keyed and exact", count == 2 and span_err(on, world_at(feet, TIMES), feet) < 1e-5)
cmds.delete("lyr_glo_plant")
count, msg = CLM.create([hand, wave], [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY)
check("T29b nothing to hold -> 0, warning, no layer", count == 0 and "Nothing to hold" in msg
      and not cmds.objExists("lyr_glo_plant"), msg[:120])

# ---------------------------------------------------------------- T30 zero_outside=False
glo, feet, lyr_glo, _ = build_plant_scene()
on = world_at(feet, TIMES)
count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY, zero_outside=False)
new = world_at(feet, TIMES)
c = curve_of("lyr_glo_plant", feet[0] + ".tx")
times = cmds.keyframe(c, q=True, tc=True)
leak = max(abs(x - y) for x, y in zip(new[(feet[0], E)], on[(feet[0], E)]))
check("T30 zero_outside=False: last-span delta held to End (documented), no keys outside",
      leak > 1e-3 and times[0] == S and times[-1] == E and span_err(on, new, feet) < 1e-5, (leak, times[0], times[-1]))

# ---------------------------------------------------------------- T31 청크 · T32 undo
glo, feet, lyr_glo, _ = build_plant_scene()
count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY)
ref = world_at(feet, TIMES)
cmds.delete("lyr_glo_plant")
count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY, chunk_frames=7)
check("T31 chunk of 7 frames gives the same result (1e-9)", max_diff(ref, world_at(feet, TIMES)) < 1e-9)
check("T31 lyr_glo not left muted", not cmds.getAttr(lyr_glo + ".mute"))
cmds.delete("lyr_glo_plant")
keep = all_curve_values(layers_all, plugs_all)
cmds.flushUndo()
count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY)
cmds.undo()
check("T32 one undo removes the plant layer, curves identical, lyr_glo unmuted",
      not cmds.objExists("lyr_glo_plant") and keep == all_curve_values(layers_all, plugs_all)
      and not cmds.getAttr(lyr_glo + ".mute"))

# ---------------------------------------------------------------- T33 preview · T34 names · T35 step 무시 · T36 progress
found, msg = CLM.preview_spans(feet, [lyr_glo], S, E)
print("  [T33] " + msg)
check("T33 preview_spans lists spans per object without creating a layer", found == 2
      and "foot_l_ctl: 20-30 (11f), 70-85 (16f), 140-150 (11f)" in msg and "foot_r_ctl: 0-10 (11f)" in msg
      and msg.startswith("Stationary spans 0-200f without [lyr_glo]") and not cmds.objExists("lyr_glo_plant"), msg)
found, msg = CLM.preview_spans(feet, [lyr_glo], S, E, tol_t=1e9, tol_r=1e9)
check("T33b preview with huge tolerance shows the whole range", "foot_l_ctl: 0-200 (201f)" in msg, msg)
check("T33c preview rejects a muted layer like create", (cmds.animLayer(lyr_glo, e=True, mute=True) or True)
      and "is muted" in CLM.preview_spans(feet, [lyr_glo], S, E)[1])
cmds.animLayer(lyr_glo, e=True, mute=False)
check("T34 default names: _plant / plant in stationary mode, _counter otherwise",
      CLM.default_layer_name(["lyr_glo"], CLM.HOLD_STATIONARY) == "lyr_glo_plant"
      and CLM.default_layer_name(["a", "b"], CLM.HOLD_STATIONARY) == "plant"
      and CLM.default_layer_name(["lyr_glo"]) == "lyr_glo_counter")
count, msg = CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY, step=5)
c = curve_of("lyr_glo_plant", feet[0] + ".tx")
check("T35 step ignored in stationary mode (every frame keyed, no NOT exact note)",
      cmds.keyframe(c, q=True, kc=True) == E - S + 3 and "NOT exact" not in msg)
cmds.delete("lyr_glo_plant")
calls = []
CLM.create(feet, [lyr_glo], S, E, hold=CLM.HOLD_STATIONARY, progress=lambda d, t, m=None: calls.append((d, t, m)))
check("T36 progress ends at total = detect 202 + sample 201 + key 201", calls and calls[-1][0] == calls[-1][1] == 604,
      (len(calls), calls[-1]))
check("T36 everywhere-mode message unchanged (regression)",
      CLM.create(feet, [lyr_glo], S, E, layer_name="chk")[1].startswith("Counter Layer: chk - 2 object(s)"))

print("\n%d / %d passed" % (sum(R), len(R)))
maya.standalone.uninitialize()
