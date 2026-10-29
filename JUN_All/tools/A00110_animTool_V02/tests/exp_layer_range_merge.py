# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# A00110_animTool_V02 - "Bake > Merge Layers" (구간 한정 애니메이션 레이어 병합) 계획서의 사전 실험 (mayapy 2024, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" exp_layer_range_merge.py     (약 3분, F8 성능 포함)
#
# 계획서 : docs/plans/A00110_animTool_V02_layer_range_merge_plan.md (§4 실측 표가 이 파일의 출력이다)
# 구현 뒤에는 test_layer_range_merge.py 가 이 역할을 이어받고 이 파일은 지운다.
#
# 판정 : ctl 의 worldMatrix 를 -3..1003 정수 프레임 전부 + 반 프레임에서 before / after 비교.
#        정수 프레임은 전부 같아야 하고, 구간 [s-1, e+1] 밖의 반 프레임도 같아야 한다.
#        구간 안의 반 프레임은 bake 보간이라 달라진다(마야 Merge Layers 도 같다 - F7).
#   F1 children 순서 방향 (override 를 첫/끝에 두고 어느 쪽이 덮는지)
#   F2 additive a+b=>b : scale identity 교정 + dest 에 새로 생긴 커브 경계 identity 키
#   F3 additive a+b=>new c
#   F4 override a + b => b : a 의 모든 멤버 plug 포함 + weight 게이트
#   F5 override a + b => new c (override, weight 게이트, a 의 위치)
#   F6 a + Base => Base : 임시 additive c 를 base 바로 위에 두고 합산해 접기
#   F7 마야 자체 animLayerMerge 의 정확도(참고)
#   F8 성능 : 50 컨트롤러 x 9축 x 3레이어, 구간 1000
import math, time
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds
import maya.mel as mel

R = []
def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))

S, E = 50, 300
ATTRS = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]


def new_scene(n=1):
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=0, max=1000, ast=0, aet=1000)
    ctls = []
    for k in range(n):
        ctl = cmds.polyCube(n="ctl%d" % k if n > 1 else "ctl")[0]
        for i, t in enumerate([0, 120, 260, 480, 700, 1000]):
            for j, a in enumerate(ATTRS):
                base = 1.0 if a.startswith("s") else 0.0
                cmds.setKeyframe(ctl, at=a, t=t, v=base + math.sin(0.7 * i + j + k) * (40 if a.startswith("r") else 4))
        ctls.append(ctl)
    return ctls if n > 1 else ctls[0]


def key_layer(ctls, layer, attrs, times, amp):
    if not isinstance(ctls, list):
        ctls = [ctls]
    for k, ctl in enumerate(ctls):
        for i, t in enumerate(times):
            for j, a in enumerate(attrs):
                base = 1.0 if a.startswith("s") else 0.0
                cmds.setKeyframe(ctl, at=a, t=t, v=base + math.cos(0.9 * i + 2 * j + k) * amp * (10 if a.startswith("r") else 1), animLayer=layer)


def curve_of(layer, plug):
    c = cmds.animLayer(layer, q=True, findCurveForPlug=plug) or []
    if not c and layer == cmds.animLayer(q=True, root=True):
        c = cmds.listConnections(plug, s=True, d=False, type="animCurve", skipConversionNodes=True) or []
    return c[0] if c else None


def layer_curves(layer, plugs):
    return {p: curve_of(layer, p) for p in plugs if curve_of(layer, p)}


def merge_plugs(layers):
    """additive 레이어 = 커브 있는 멤버만, override 레이어 = 모든 멤버(키 없는 멤버도 정적 값으로 덮는다)."""
    out = []
    for l in layers:
        ov = cmds.animLayer(l, q=True, override=True)
        for p in (cmds.animLayer(l, q=True, attribute=True) or []):
            if p in out:
                continue
            if ov or curve_of(l, p):
                out.append(p)
    return out


def snap(ctl, times):
    out = {}
    for t in times:
        cmds.currentTime(t, update=True)
        out[t] = cmds.getAttr(ctl + ".worldMatrix[0]")
    return out


def max_diff(a, b, times):
    m, worst = 0.0, None
    for t in times:
        d = max(abs(x - y) for x, y in zip(a[t], b[t]))
        if d > m:
            m, worst = d, t
    return m, worst


INT_T = list(range(-3, 1004))
HALF_OUT = [t + 0.5 for t in range(-3, 1003) if t + 0.5 < S - 1 or t + 0.5 > E + 1]
HALF_IN = [t + 0.5 for t in range(S - 1, E + 1)]


def snapshot(ctl):
    return (snap(ctl, INT_T), snap(ctl, HALF_OUT), snap(ctl, HALF_IN))


def report(tag, ctl, before):
    di, wi = max_diff(before[0], snap(ctl, INT_T), INT_T)
    do, wo = max_diff(before[1], snap(ctl, HALF_OUT), HALF_OUT)
    dn, wn = max_diff(before[2], snap(ctl, HALF_IN), HALF_IN)
    check(tag + " : integer frames identical", di < 1e-6, "max %.2e @ %s" % (di, wi))
    check(tag + " : half frames outside [s-1,e+1] identical", do < 1e-6, "max %.2e @ %s" % (do, wo))
    print("     (info) half frames inside : max %.3e @ %s" % (dn, wn))


def insert_boundary(curve, t):
    cmds.setKeyframe(curve, insert=True, time=(t, t))
    cmds.keyTangent(curve, e=True, time=(t, t), itt="fixed", ott="fixed")


def identity_for(plug, layer):
    # scaleAccumulationMode enum = Additive(0) : Multiply(1)
    if plug.split(".")[-1].startswith("scale") and cmds.getAttr(layer + ".scaleAccumulationMode") == 1:
        return 1.0
    return 0.0


def neutralize_additive(layer, plugs, s, e):
    for p, c in layer_curves(layer, plugs).items():
        insert_boundary(c, s - 1); insert_boundary(c, e + 1)
        cmds.cutKey(c, time=(s, e), clear=True)
        idv = identity_for(p, layer)
        cmds.setKeyframe(c, time=(s, s), value=idv, outTangentType="step")
        cmds.setKeyframe(c, time=(e, e), value=idv)


def gate_weight(layer, s, e, inside, outside=None):
    """weight 를 구간 안 inside, 밖 outside(기본 지금 값) 로 계단 키."""
    w = layer + ".weight"
    cur = cmds.getAttr(w) if outside is None else outside
    cmds.setKeyframe(w, time=(s - 1, s - 1), value=cur, outTangentType="step")
    cmds.setKeyframe(w, time=(s, s), value=inside, outTangentType="step")
    cmds.setKeyframe(w, time=(e, e), value=inside, outTangentType="step")
    cmds.setKeyframe(w, time=(e + 1, e + 1), value=cur)


def bake_into(dest, sources, plugs, s, e, mute_dest, **extra):
    """마야 animLayerMerge 와 같은 bakeResults 호출 + 구간/pok. dest 에 없던 커브는 경계 identity 키를 준다."""
    had = {p: bool(curve_of(dest, p)) for p in plugs}
    if mute_dest:
        cmds.animLayer(dest, e=True, mute=True)
    kw = dict(time=(s, e), sampleBy=1, simulation=False, disableImplicitControl=False,
              preserveOutsideKeys=True, destinationLayer=dest, resolveWithoutLayer=sources)
    kw.update(extra)
    try:
        cmds.bakeResults(plugs, **kw)
    finally:
        if mute_dest:
            cmds.animLayer(dest, e=True, mute=False)
    if not cmds.animLayer(dest, q=True, override=True):
        for p in plugs:
            if had[p]:
                continue
            c = curve_of(dest, p)
            if c:
                idv = identity_for(p, dest)
                cmds.setKeyframe(c, time=(s - 1, s - 1), value=idv)
                cmds.setKeyframe(c, time=(e + 1, e + 1), value=idv)


def prep_dest_existing(dest, plugs, s, e):
    for p, c in layer_curves(dest, plugs).items():
        insert_boundary(c, s - 1); insert_boundary(c, e + 1)


# ================================================================ F1 : children 순서 방향
ctl = new_scene(); cmds.select(ctl)
l1 = cmds.animLayer("L1", addSelectedObjects=True)
l2 = cmds.animLayer("L2", addSelectedObjects=True)
root = cmds.animLayer(q=True, root=True)
ov = cmds.animLayer("OV", override=True)
cmds.animLayer(ov, e=True, attribute=ctl + ".translateX", addRelatedKG=False)
cmds.setKeyframe(ctl + ".translateX", t=0, v=77.0, animLayer=ov)
cmds.setKeyframe(ctl + ".translateX", t=5, v=11.0, animLayer=l2)   # 위에서 더하는 레이어
cmds.animLayer(ov, e=True, parent=root)
first = cmds.animLayer(root, q=True, children=True)[0]
cmds.animLayer(ov, e=True, moveLayerBefore=first)
order = cmds.animLayer(root, q=True, children=True)
cmds.currentTime(5, update=True); v_first = cmds.getAttr(ctl + ".translateX")
cmds.animLayer(ov, e=True, moveLayerAfter=cmds.animLayer(root, q=True, children=True)[-1])
order2 = cmds.animLayer(root, q=True, children=True)
cmds.currentTime(5, update=True); v_last = cmds.getAttr(ctl + ".translateX")
print("F1 OV first -> order %s, tx@5 = %s ; OV last -> order %s, tx@5 = %s" % (order, v_first, order2, v_last))
first_is_bottom = abs(v_last - 77.0) < 1e-6 and abs(v_first - 77.0) > 1e-6
check("F1 children[0] is the BOTTOM layer (last child evaluated last / top of editor)", first_is_bottom, (v_first, v_last))

# ================================================================ F2 : additive a+b => b
def build_additive(weight_b=1.0, n=1):
    ctl = new_scene(n); cmds.select(ctl)
    b = cmds.animLayer("b", addSelectedObjects=True)
    a = cmds.animLayer("a", addSelectedObjects=True)
    top = cmds.animLayer("top", addSelectedObjects=True)
    key_layer(ctl, b, ["tx", "ty", "rz", "sx"], [30, 60, 180, 300, 900], 2.0)
    key_layer(ctl, a, ["tx", "ry", "tz", "sx"], [0, 100, 200, 400, 1000], 3.0)
    key_layer(ctl, top, ["tx", "rx"], [10, 500, 990], 1.5)
    cmds.setAttr(top + ".weight", 0.7)
    if weight_b != 1.0:
        cmds.setAttr(b + ".weight", weight_b)
    return ctl, a, b, top

ctl, a, b, top = build_additive()
before = snapshot(ctl)
plugs = merge_plugs([a, b])
t0 = time.time()
prep_dest_existing(b, plugs, S, E)
bake_into(b, [a, b], plugs, S, E, mute_dest=False)
neutralize_additive(a, plugs, S, E)
print("     F2 took %.3fs" % (time.time() - t0))
report("F2 additive a+b=>b", ctl, before)

# ================================================================ F3 : additive a+b => new c (a 자리, a 바로 위)
ctl, a, b, top = build_additive()
root = cmds.animLayer(q=True, root=True)
before = snapshot(ctl)
plugs = merge_plugs([a, b])
c = cmds.animLayer("Merged_Layer")
cmds.setAttr(c + ".scaleAccumulationMode", cmds.getAttr(a + ".scaleAccumulationMode"))
cmds.setAttr(c + ".rotationAccumulationMode", cmds.getAttr(a + ".rotationAccumulationMode"))
cmds.animLayer(c, e=True, parent=root)
cmds.animLayer(c, e=True, moveLayerAfter=a)
for p in plugs:
    cmds.animLayer(c, e=True, attribute=p, addRelatedKG=False)
bake_into(c, [a, b], plugs, S, E, mute_dest=True)
neutralize_additive(a, plugs, S, E)
neutralize_additive(b, plugs, S, E)
report("F3 additive a+b=>new c", ctl, before)
print("     F3 children :", cmds.animLayer(root, q=True, children=True))

# ================================================================ F4 : override a + b => b
def build_override(n=1):
    ctl = new_scene(n); cmds.select(ctl)
    b = cmds.animLayer("b", addSelectedObjects=True)
    a = cmds.animLayer("a", addSelectedObjects=True, override=True)
    top = cmds.animLayer("top", addSelectedObjects=True)
    key_layer(ctl, b, ["tx", "ty", "rz"], [30, 60, 180, 300, 900], 2.0)
    key_layer(ctl, a, ["tx", "ry", "tz"], [0, 100, 200, 400, 1000], 3.0)
    key_layer(ctl, top, ["tx", "rx"], [10, 500, 990], 1.5)
    return ctl, a, b, top

ctl, a, b, top = build_override()
before = snapshot(ctl)
plugs = merge_plugs([a, b])
print("     F4 plugs (override a => all members) :", len(plugs), plugs[:4], "...")
prep_dest_existing(b, plugs, S, E)
bake_into(b, [a, b], plugs, S, E, mute_dest=False)
gate_weight(a, S, E, inside=0.0)
report("F4 override a + b => b (a weight-gated)", ctl, before)

# ================================================================ F5 : override a + b => new c (override, a 바로 위, weight 게이트 밖 0 안 1)
ctl, a, b, top = build_override()
root = cmds.animLayer(q=True, root=True)
before = snapshot(ctl)
plugs = merge_plugs([a, b])
c = cmds.animLayer("Merged_Layer", override=True)
cmds.animLayer(c, e=True, parent=root)
cmds.animLayer(c, e=True, moveLayerAfter=a)
for p in plugs:
    cmds.animLayer(c, e=True, attribute=p, addRelatedKG=False)
# 멤버로 넣는 순간 정적 override 가 생긴다 -> bake 전까지 mute, bake 뒤 weight 게이트로 밖 0
bake_into(c, [a, b], plugs, S, E, mute_dest=True)
gate_weight(c, S, E, inside=1.0, outside=0.0)
gate_weight(a, S, E, inside=0.0)
neutralize_additive(b, plugs, S, E)
report("F5 override a + b => new override c", ctl, before)

# ================================================================ F6 : a + Base => Base (임시 additive c 접기)
ctl = new_scene(); cmds.select(ctl)
a = cmds.animLayer("a", addSelectedObjects=True)
top = cmds.animLayer("top", addSelectedObjects=True)
key_layer(ctl, a, ["tx", "ry", "tz", "sx"], [0, 100, 200, 400, 1000], 3.0)
key_layer(ctl, top, ["tx", "rx"], [10, 500, 990], 1.5)
cmds.setAttr(top + ".weight", 0.7)
root = cmds.animLayer(q=True, root=True)
before = snapshot(ctl)
plugs = merge_plugs([a])
t0 = time.time()
c = cmds.animLayer("tmpMerge")
cmds.setAttr(c + ".scaleAccumulationMode", 0)     # Additive -> 합이 성립
cmds.setAttr(c + ".rotationAccumulationMode", 0)  # By Component
cmds.animLayer(c, e=True, parent=root)
cmds.animLayer(c, e=True, moveLayerBefore=cmds.animLayer(root, q=True, children=True)[0])   # 맨 아래 = base 바로 위
for p in plugs:
    cmds.animLayer(c, e=True, attribute=p, addRelatedKG=False)
bake_into(c, [a], plugs, S, E, mute_dest=True)
for p in plugs:
    base_c = curve_of(root, p)
    cc = curve_of(c, p)
    if base_c is None:
        # base 에 커브가 없던 plug : 정적 값 + c -> base 에 새 커브
        static = cmds.getAttr(p)
        vals = [static + cmds.keyframe(cc, q=True, eval=True, time=(f, f))[0] for f in range(S, E + 1)]
        for f, v in zip(range(S, E + 1), vals):
            cmds.setKeyframe(p, time=(f, f), value=v)   # 레이어 멤버 plug 라 base 로 가나? -> 확인 대상
        base_c = curve_of(root, p)
        cmds.setKeyframe(base_c, time=(S - 1, S - 1), value=static); cmds.setKeyframe(base_c, time=(E + 1, E + 1), value=static)
        continue
    vals = [cmds.keyframe(base_c, q=True, eval=True, time=(f, f))[0] + cmds.keyframe(cc, q=True, eval=True, time=(f, f))[0]
            for f in range(S, E + 1)]
    insert_boundary(base_c, S - 1); insert_boundary(base_c, E + 1)
    cmds.cutKey(base_c, time=(S, E), clear=True)
    for f, v in zip(range(S, E + 1), vals):
        cmds.setKeyframe(base_c, time=(f, f), value=v)
cmds.delete(c)
neutralize_additive(a, plugs, S, E)
print("     F6 took %.3fs" % (time.time() - t0))
report("F6 a + Base => Base (fold temp additive c into base)", ctl, before)
print("     F6 layers left :", cmds.ls(type="animLayer"), " base tx keys :", cmds.keyframe(curve_of(root, ctl + ".translateX"), q=True, kc=True))

# ================================================================ F7 : 마야 자체 animLayerMerge 정확도 (참고, 전체 구간)
ctl, a, b, top = build_additive()
before = snapshot(ctl)
try:
    mel.eval('source "performAnimLayerMerge.mel";')
    mel.eval('optionVar -iv animLayerMergeSmartBake 0; optionVar -iv animLayerMergeDeleteLayers 1; optionVar -iv animLayerMergeUp 1; optionVar -fv animLayerMergeByTime 1.0;')
    mel.eval('animLayerMerge({"a","b"});')
    print("     F7 layers after Maya merge :", cmds.ls(type="animLayer"))
    di, wi = max_diff(before[0], snap(ctl, INT_T), INT_T)
    do, wo = max_diff(before[1], snap(ctl, HALF_OUT), HALF_OUT)
    print("     F7 Maya animLayerMerge : integer frames max diff %.3e @ %s ; half frames max diff %.3e @ %s" % (di, wi, do, wo))
    check("F7 (info) Maya's own merge exact at integer frames", di < 1e-6, di)
except Exception as ex:
    print("     F7 Maya merge failed headless :", ex)

# ================================================================ F8 : 성능 50 ctl x 3 layers, 구간 0..1000
ctls, a, b, top = build_additive(n=50)
plugs = merge_plugs([a, b])
t0 = time.time()
prep_dest_existing(b, plugs, 0, 1000)
bake_into(b, [a, b], plugs, 0, 1000, mute_dest=False)
neutralize_additive(a, plugs, 0, 1000)
dt = time.time() - t0
print("     F8 50 ctls, %d plugs, range 0..1000 : %.2fs" % (len(plugs), dt))
check("F8 (info) perf recorded", True)

print("\n%d / %d passed" % (sum(R), len(R)))
maya.standalone.uninitialize()
