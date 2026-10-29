# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# A00110_animTool_V02 - "Bake > Counter Layer" (상위 레이어의 월드 변화를 되돌리는 보정 레이어) 계획서의 사전 실험
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" exp_counter_layer.py     (약 1분)
#
# 계획서 : docs/plans/A00110_animTool_V02_counter_layer_plan.md (§4 실측 표가 이 파일의 출력이다)
# 구현 뒤에는 test_counter_layer.py 가 이 역할을 이어받고 이 파일은 지운다.
#
# 씬 : global_ctl > foot_l_ctl, foot_r_ctl. 발은 Base + additive lyr_01, lyr_02 에 키.
#      lyr_glo 에 global_ctl 의 T/R 키 -> 발의 월드가 바뀐다.
# 목표 : lyr_glo 는 그대로 두고, 새 additive 레이어 하나로 발의 월드를 "lyr_glo 뮤트 상태" 와 같게 만든다.
# 판정 : 발의 worldMatrix 를 정수 프레임 전부에서 before(lyr_glo 뮤트) / after(보정 레이어 적용) 비교.
#   F1 기본 (transform, xyz, by-layer 회전 누적)       - xform -m + setKeyframe(animLayer, value) 역산
#   F2 회전 누적 by-component 레이어들
#   F3 조인트(jointOrient + 회전 순서 zxy) 가 보정 대상
#   F4 큰 회전(ry 0 -> 270) - 보정 커브의 연속성(프레임 사이 점프 < 180)
#   F5 발 자신도 lyr_glo 에 키가 있는 경우 (글로벌 레이어의 발 기여까지 되돌려야 "있기 전" 이다)
#   F6 레이어 가중치 (lyr_01 weight 0.5, lyr_glo weight 애니메이션)
#   F7 setAttr 만 하고 setKeyframe(animLayer) 에 value 를 안 주는 경로도 역산되나
#   F8 undo 한 번으로 보정 레이어가 통째로 사라지나
#   F9 다른 레이어 · Base 커브는 건드리지 않았나
#   F10 성능 : 발 2 x 201 프레임 (프레임당 비용 -> 50 ctl x 1000 f 추정)
#   F11 getAttr(time=) 로 스냅샷을 찍어도 currentTime 루프와 같은가 (스냅샷 가속 후보)
import math, time
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds
import maya.api.OpenMaya as om

R = []
def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))

S, E = 0, 200
TR = ["tx", "ty", "tz", "rx", "ry", "rz"]
ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
API_ORDER = [om.MEulerRotation.kXYZ, om.MEulerRotation.kYZX, om.MEulerRotation.kZXY,
             om.MEulerRotation.kXZY, om.MEulerRotation.kYXZ, om.MEulerRotation.kZYX]


def build_scene(rot_order="xyz", joint_feet=False, by_component=False):
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=S, max=E, ast=S, aet=E)
    glo = cmds.createNode("transform", n="global_ctl")
    feet = []
    for side, x in (("l", 5.0), ("r", -5.0)):
        if joint_feet:
            cmds.select(clear=True)
            f = cmds.joint(n="foot_%s_ctl" % side)
            cmds.parent(f, glo)
            cmds.setAttr(f + ".jointOrient", 10, 20, 30)
        else:
            f = cmds.createNode("transform", n="foot_%s_ctl" % side, p=glo)
        cmds.setAttr(f + ".rotateOrder", ORDERS.index(rot_order))
        feet.append(f)
    # Base 키 (걸음 흉내)
    for k, f in enumerate(feet):
        for i, t in enumerate(range(S, E + 1, 25)):
            for j, a in enumerate(TR):
                v = math.sin(0.5 * i + j + k) * (35 if a[0] == "r" else 6)
                if a == "tx":
                    v += 5.0 if k == 0 else -5.0
                cmds.setKeyframe(f, at=a, t=t, v=v)
    # additive 레이어 둘
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


def add_glo(glo, feet, feet_in_glo=False, big_turn=False, weight_anim=False):
    lyr = cmds.animLayer("lyr_glo")
    for a in TR:
        cmds.animLayer(lyr, e=True, at=glo + "." + a)
    for i, t in enumerate(range(S, E + 1, 50)):
        vals = {"tx": i * 7.0, "ty": math.sin(i) * 3, "tz": -i * 2.5,
                "rx": math.sin(i) * 15, "ry": (i * 67.5 if big_turn else math.cos(i) * 40),
                "rz": math.sin(1.3 * i) * 10}
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


def world_at_getattr(objs, times):
    """currentTime 을 바꾸지 않고 getAttr(time=) 로 찍는 스냅샷 (F11 후보)."""
    out = {}
    for t in times:
        for o in objs:
            out[(o, t)] = cmds.getAttr(o + ".worldMatrix[0]", time=t)
    return out


def max_diff(a, b):
    return max(max(abs(x - y) for x, y in zip(a[k], b[k])) for k in a)


def snapshot_without(layers, objs, times, fn=world_at):
    for l in layers:
        cmds.animLayer(l, e=True, mute=True)
    try:
        return fn(objs, times)
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


# ---------------------------------------------------------------- 보정 본체 (시제품)
def pick_rotation(obj, target_deg, ref_deg):
    """xform 이 돌려준 오일러(target) 와 같은 회전 중 ref 에 가장 가까운 것.
    alternateSolution + setToClosestCut 만 쓴다(closestSolution 은 짐벌 근처에서 다른 회전이 된다)."""
    order = API_ORDER[cmds.getAttr(obj + ".rotateOrder")]
    e = om.MEulerRotation(*[math.radians(v) for v in target_deg], order=order)
    ref = om.MEulerRotation(*[math.radians(v) for v in ref_deg], order=order)
    M = e.asMatrix()
    best = None
    for cand in (om.MEulerRotation(e), e.alternateSolution()):
        cand.setToClosestCut(ref)
        if not cand.asMatrix().isEquivalent(M, 1e-9):
            continue
        d = sum((cand[i] - ref[i]) ** 2 for i in range(3))
        if best is None or d < best[0]:
            best = (d, cand)
    c = best[1]
    return [math.degrees(c[0]), math.degrees(c[1]), math.degrees(c[2])]


def counter_layer(objs, target_world, times, name="lyr_glo_counter", use_value=True, by_component=False):
    """target_world[(obj, t)] 가 되도록 새 additive 레이어에 T/R 키를 찍는다. 반환 (레이어, 초/프레임)."""
    lyr = cmds.animLayer(name)
    if by_component:
        cmds.setAttr(lyr + ".rotationAccumulationMode", 1)
    for o in objs:
        for a in TR:
            cmds.animLayer(lyr, e=True, at=o + "." + a)
    t0 = time.time()
    for t in times:
        cmds.currentTime(t)
        for o in objs:
            ref_rot = cmds.getAttr(o + ".rotate")[0]            # 지금(글로벌 켜진) 로컬 회전 = 연속성 기준
            cmds.xform(o, ws=True, m=target_world[(o, t)])      # 일반 분해(jointOrient, 회전 순서, 피벗 포함)
            tr = cmds.xform(o, q=True, t=True)                   # 로컬 translate
            rot = pick_rotation(o, cmds.getAttr(o + ".rotate")[0], ref_rot)
            vals = dict(zip(TR, list(tr) + rot))
            if use_value:
                for a in TR:
                    cmds.setKeyframe(o, at=a, t=t, v=vals[a], animLayer=lyr)
            else:
                cmds.setAttr(o + ".rotate", *rot)
                for a in TR:
                    cmds.setKeyframe(o, at=a, t=t, animLayer=lyr)
    return lyr, (time.time() - t0) / max(1, len(times))


def max_jump(layer, objs):
    """보정 레이어 회전 커브의 프레임 사이 최대 점프(도)."""
    worst = 0.0
    for o in objs:
        for a in ("rx", "ry", "rz"):
            c = curve_of(layer, o + "." + a)
            vals = cmds.keyframe(c, q=True, vc=True) or []
            for x, y in zip(vals, vals[1:]):
                worst = max(worst, abs(x - y))
    return worst


TIMES = list(range(S, E + 1))
HALF = [t + 0.5 for t in range(S, E)]


def run_case(tag, rot_order="xyz", joint_feet=False, by_component=False, feet_in_glo=False,
             big_turn=False, weight_anim=False, use_value=True):
    glo, feet = build_scene(rot_order, joint_feet, by_component)
    lyr_glo = add_glo(glo, feet, feet_in_glo, big_turn, weight_anim)
    before = snapshot_without([lyr_glo], feet, TIMES)
    before_half = snapshot_without([lyr_glo], feet, HALF)
    moved = max_diff(before, world_at(feet, TIMES))           # 글로벌이 실제로 발을 움직였나
    layers = ["BaseAnimation", "lyr_01", "lyr_02", "lyr_glo"]
    plugs = [f + "." + a for f in feet for a in TR] + [glo + "." + a for a in TR]
    keep = all_curve_values(layers, plugs)
    cmds.undoInfo(openChunk=True)
    try:
        lyr_c, per_frame = counter_layer(feet, before, TIMES, use_value=use_value, by_component=by_component)
    finally:
        cmds.undoInfo(closeChunk=True)
    after = world_at(feet, TIMES)
    after_half = world_at(feet, HALF)
    err = max_diff(before, after)
    err_half = max_diff(before_half, after_half)
    glo_untouched = keep == all_curve_values(layers, plugs)
    top = (cmds.animLayer("BaseAnimation", q=True, children=True) or [])[-1] == lyr_c
    print("  [%s] moved=%.3f  err_int=%.2e  err_half=%.2e  jump=%.1f  %.2f ms/frame(2 obj)  top=%s"
          % (tag, moved, err, err_half, max_jump(lyr_c, feet), per_frame * 1000, top))
    return dict(moved=moved, err=err, err_half=err_half, untouched=glo_untouched, lyr=lyr_c,
                jump=max_jump(lyr_c, feet), per_frame=per_frame, top=top, feet=feet, before=before)


# F1 기본
r = run_case("F1 default")
check("F1 global layer really moved the feet", r["moved"] > 1.0, r["moved"])
check("F1 counter layer restores world at every integer frame (1e-6)", r["err"] < 1e-6, r["err"])
check("F1 other layers / base curves untouched", r["untouched"])
check("F1 new layer sits on top of the stack (children[-1])", r["top"])
print("     half-frame error (informational, interpolation): %.2e" % r["err_half"])

# F2 by-component
r = run_case("F2 by-component", by_component=True)
check("F2 by-component rotation accumulation: world restored (1e-6)", r["err"] < 1e-6, r["err"])

# F3 joint + zxy
r = run_case("F3 joint zxy", rot_order="zxy", joint_feet=True)
check("F3 joint with jointOrient + zxy: world restored (1e-6)", r["err"] < 1e-6, r["err"])

# F4 big turn continuity
r = run_case("F4 big turn", big_turn=True)
check("F4 big turn: world restored (1e-6)", r["err"] < 1e-6, r["err"])
check("F4 big turn: counter rotate curves continuous (max jump < 90 deg)", r["jump"] < 90.0, r["jump"])

# F5 feet keyed in lyr_glo too
r = run_case("F5 feet in glo", feet_in_glo=True)
check("F5 feet also keyed in lyr_glo: world restored to muted state (1e-6)", r["err"] < 1e-6, r["err"])

# F6 weights
glo, feet = build_scene()
cmds.setAttr("lyr_01.weight", 0.5)
lyr_glo = add_glo(glo, feet, weight_anim=True)
before = snapshot_without([lyr_glo], feet, TIMES)
lyr_c, _ = counter_layer(feet, before, TIMES)
check("F6 lyr_01 weight 0.5 + lyr_glo weight animated: world restored (1e-6)",
      max_diff(before, world_at(feet, TIMES)) < 1e-6, max_diff(before, world_at(feet, TIMES)))

# F7 setAttr + setKeyframe(animLayer) without value
r = run_case("F7 no value", use_value=False)
check("F7 setAttr then setKeyframe(animLayer) without value also back-solves (1e-6)", r["err"] < 1e-6, r["err"])

# F8 undo
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
before = snapshot_without([lyr_glo], feet, TIMES)
plugs = [f + "." + a for f in feet for a in TR]
keep = all_curve_values(["BaseAnimation", "lyr_01", "lyr_02"], plugs)
cmds.undoInfo(openChunk=True)
try:
    lyr_c, _ = counter_layer(feet, before, TIMES)
finally:
    cmds.undoInfo(closeChunk=True)
cmds.undo()
check("F8 one undo removes the counter layer", not cmds.objExists("lyr_glo_counter"))
check("F8 after undo other curves identical", keep == all_curve_values(["BaseAnimation", "lyr_01", "lyr_02"], plugs))

# F9 (F1 에서 untouched 로 확인) + F10 성능
r = run_case("F10 perf")
est = r["per_frame"] / 2.0 * 50 * 1000
check("F10 per-frame cost measured", True, "%.2f ms per obj-frame -> 50 ctl x 1000 f ~ %.0f s" % (r["per_frame"] / 2.0 * 1000, est))

# F11 getAttr(time=) snapshot equals currentTime snapshot
glo, feet = build_scene()
lyr_glo = add_glo(glo, feet)
a = snapshot_without([lyr_glo], feet, TIMES)
t0 = time.time(); b = snapshot_without([lyr_glo], feet, TIMES, fn=world_at_getattr); tb = time.time() - t0
t0 = time.time(); a2 = snapshot_without([lyr_glo], feet, TIMES); ta = time.time() - t0
check("F11 getAttr(time=) snapshot == currentTime snapshot (1e-9)", max_diff(a, b) < 1e-9,
      "diff=%.1e  getAttr %.0f ms vs currentTime %.0f ms" % (max_diff(a, b), tb * 1000, ta * 1000))

print("\n%d / %d passed" % (sum(R), len(R)))
maya.standalone.uninitialize()
