# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.27 - Bake > Merge Layers (구간 한정 레이어 병합) 회귀 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_layer_range_merge.py     (약 4분, 성능 항목 포함)
#
# 계획서 docs/plans/A00110_animTool_V02_layer_range_merge_plan.md 의 사전 실험(exp_layer_range_merge.py, 13/13)을
# LayerMergeManager.merge_range 호출로 바꾼 것 + 구현 옵션 · 거부 조건 · undo · 성능 · UI 스모크.
#
# 씬 : ctl 큐브, base 9축 키(0 120 260 480 700 1000), 레이어 b(tx ty rz sx · 30 60 180 300 900), a(tx ry tz sx · 0 100 200 400 1000),
#      그 위 비병합 레이어 top(tx rx · weight 0.7). 구간 [50, 300].
# 판정 : ctl 의 worldMatrix 를 -3..1003 정수 프레임 전부 + 반 프레임에서 before / after 비교.
#        정수 프레임은 전부 같아야 하고, 구간 [s-1, e+1] 밖의 반 프레임도 같아야 한다(구간 안 반 프레임은 bake 보간).
import math
import os
import sys
import time

# QApplication 은 maya.standalone.initialize() 보다 먼저 (qapplication-before-maya-standalone). UI 스모크용.
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    from PySide2.QtWidgets import QApplication
    from PySide2.QtCore import Qt
    APP = QApplication.instance() or QApplication(sys.argv)
except Exception:
    APP = None

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.mel as mel     # noqa: E402

from tools.A00110_animTool_V02.app.core.layer_merge_manager import LayerMergeManager as LMM   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


S, E = 50, 300
ATTRS = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
LONG = {"tx": "translateX", "ty": "translateY", "tz": "translateZ", "rx": "rotateX", "ry": "rotateY", "rz": "rotateZ",
        "sx": "scaleX", "sy": "scaleY", "sz": "scaleZ"}


def long_plugs(node):
    return [node + "." + LONG[x] for x in ATTRS]
INT_T = list(range(-3, 1004))
HALF_OUT = [t + 0.5 for t in range(-3, 1003) if t + 0.5 < S - 1 or t + 0.5 > E + 1]


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
                cmds.setKeyframe(ctl, at=a, t=t, v=base + math.cos(0.9 * i + 2 * j + k) * amp * (10 if a.startswith("r") else 1),
                                 animLayer=layer)


def root():
    return cmds.animLayer(q=True, root=True)


def curve_of(layer, plug):
    c = cmds.animLayer(layer, q=True, findCurveForPlug=plug) or []
    if not c and layer == root():
        c = cmds.listConnections(plug, s=True, d=False, type="animCurve", skipConversionNodes=True) or []
    return c[0] if c else None


def ev(curve, t):
    return cmds.keyframe(curve, q=True, eval=True, time=(t, t))[0]


def curve_values(curve):
    return tuple(zip(cmds.keyframe(curve, q=True, tc=True) or [], cmds.keyframe(curve, q=True, vc=True) or []))


def all_curve_values(layers, plugs):
    return {(l, p): curve_values(curve_of(l, p)) for l in layers for p in plugs if curve_of(l, p)}


def snap(ctls, times):
    if not isinstance(ctls, list):
        ctls = [ctls]
    out = {}
    for t in times:
        cmds.currentTime(t, update=True)
        for c in ctls:
            out[(c, t)] = cmds.getAttr(c + ".worldMatrix[0]")
    return out


def max_diff(a, b):
    m, worst = 0.0, None
    for k in a:
        d = max(abs(x - y) for x, y in zip(a[k], b[k]))
        if d > m:
            m, worst = d, k
    return m, worst


def snapshot(ctls, s=S, e=E):
    half_out = [t + 0.5 for t in range(-3, 1003) if t + 0.5 < s - 1 or t + 0.5 > e + 1]
    return (snap(ctls, INT_T), snap(ctls, half_out), half_out)


def report(tag, ctls, before, tol=1e-6):
    di, wi = max_diff(before[0], snap(ctls, INT_T))
    do, wo = max_diff(before[1], snap(ctls, before[2]))
    check(tag + " : integer frames identical", di < tol, "max %.2e @ %s" % (di, wi))
    check(tag + " : half frames outside [s-1,e+1] identical", do < tol, "max %.2e @ %s" % (do, wo))
    return di


def build_additive(n=1, weight_b=1.0):
    ctl = new_scene(n); cmds.select(ctl)
    b = cmds.animLayer("b", addSelectedObjects=True)
    a = cmds.animLayer("a", addSelectedObjects=True)
    top = cmds.animLayer("lyrTop", addSelectedObjects=True)
    key_layer(ctl, b, ["tx", "ty", "rz", "sx"], [30, 60, 180, 300, 900], 2.0)
    key_layer(ctl, a, ["tx", "ry", "tz", "sx"], [0, 100, 200, 400, 1000], 3.0)
    key_layer(ctl, top, ["tx", "rx"], [10, 500, 990], 1.5)
    cmds.setAttr(top + ".weight", 0.7)
    if weight_b != 1.0:
        cmds.setAttr(b + ".weight", weight_b)
    return ctl, a, b, top


def build_override(n=1):
    ctl = new_scene(n); cmds.select(ctl)
    b = cmds.animLayer("b", addSelectedObjects=True)
    a = cmds.animLayer("a", addSelectedObjects=True, override=True)
    top = cmds.animLayer("lyrTop", addSelectedObjects=True)
    key_layer(ctl, b, ["tx", "ty", "rz"], [30, 60, 180, 300, 900], 2.0)
    key_layer(ctl, a, ["tx", "ry", "tz"], [0, 100, 200, 400, 1000], 3.0)
    key_layer(ctl, top, ["tx", "rx"], [10, 500, 990], 1.5)
    return ctl, a, b, top


# ================================================================ T1 additive a + b => b
ctl, a, b, top = build_additive()
plugs9 = long_plugs(ctl)
before = snapshot(ctl)
keep = all_curve_values(["BaseAnimation", "lyrTop"], plugs9)
b_out = {t: ev(curve_of(b, ctl + ".translateX"), t) for t in (0, 30, 40, 400, 900, 1000)}
count, msg = LMM.merge_range([a, b], b, S, E)
print("  T1:", msg)
check("T1 count = 4 (a's keyed channels tx ry tz sx)", count == 4, count)
report("T1 additive a+b=>b", ctl, before)
check("T1 base + top curves untouched", keep == all_curve_values(["BaseAnimation", "lyrTop"], plugs9))
check("T1 b keys outside range preserved", all(abs(ev(curve_of(b, ctl + ".translateX"), t) - v) < 1e-9 for t, v in b_out.items()))
ca, cs = curve_of(a, ctl + ".translateX"), curve_of(a, ctl + ".scaleX")
check("T1 a neutralised inside: tx = 0, sx = 1 (Multiply) at f100 / f250", abs(ev(ca, 100)) < 1e-12 and abs(ev(ca, 250)) < 1e-12 and abs(ev(cs, 100) - 1.0) < 1e-12)
check("T1 a still keyed outside (f1000 key kept)", 1000.0 in (cmds.keyframe(ca, q=True, tc=True) or []))
check("T1 message verified, no warning", "Verified: max deviation" in msg and "[Warning]" not in msg and "Skipped" not in msg)
check("T1 b selected + preferred", cmds.animLayer(b, q=True, selected=True) and cmds.animLayer(b, q=True, preferred=True) and not cmds.animLayer(a, q=True, selected=True))

# ================================================================ T2 additive a + b => new
ctl, a, b, top = build_additive()
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], None, S, E)
print("  T2:", msg)
check("T2 count = 6 (union tx ty rz sx ry tz)", count == 6, count)
report("T2 additive a+b=>new", ctl, before)
children = cmds.animLayer("BaseAnimation", q=True, children=True)
check("T2 new layer 'Merged_Layer' additive, placed just above a (below top)", children == ["b", "a", "Merged_Layer", "lyrTop"] and not cmds.animLayer("Merged_Layer", q=True, override=True), children)
cm = curve_of("Merged_Layer", ctl + ".translateX")
times = cmds.keyframe(cm, q=True, tc=True)
check("T2 new layer curve: identity keys at 49 / 301, dense inside", 49.0 in times and 301.0 in times and abs(ev(cm, 49)) < 1e-12 and abs(ev(cm, 301)) < 1e-12 and len(times) == 253, len(times))
check("T2 new layer selected", cmds.animLayer("Merged_Layer", q=True, selected=True) and not cmds.animLayer(b, q=True, selected=True))
check("T2 message names placement", "Placed just above 'a'" in msg)

# ================================================================ T3 override a + b => b
ctl, a, b, top = build_override()
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], b, S, E)
print("  T3:", msg)
check("T3 count = 10 (all members of override a incl. keyless + visibility)", count == 10, count)
report("T3 override a + additive b => b", ctl, before)
w = a + ".weight"
check("T3 a.weight gated: 1 at f20, 0 at f50/f100/f300, 1 at f301/f500",
      all(abs(ev(curve_of(a, w) or cmds.listConnections(w, s=True, d=False)[0], t) - v) < 1e-12
          for t, v in ((20, 1), (50, 0), (100, 0), (300, 0), (301, 1), (500, 1))))
check("T3 message notes static override members", "member channel(s) without keys baked as static" in msg)

# ================================================================ T4 override a + b => new (override)
ctl, a, b, top = build_override()
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], None, S, E, new_name="mergeAB")
print("  T4:", msg)
report("T4 override a + b => new override layer", ctl, before)
check("T4 new layer is override, above a", cmds.animLayer("mergeAB", q=True, override=True) and cmds.animLayer("BaseAnimation", q=True, children=True) == ["b", "a", "mergeAB", "lyrTop"])
wc = cmds.listConnections("mergeAB.weight", s=True, d=False)[0]
check("T4 new layer weight: 0 outside, 1 inside", all(abs(ev(wc, t) - v) < 1e-12 for t, v in ((20, 0), (49, 0), (50, 1), (300, 1), (301, 0), (500, 0))))

# ================================================================ T5 a + Base => Base (정적 base plug 포함)
ctl = new_scene(); cmds.select(ctl)
cmds.cutKey(ctl + ".tz", clear=True); cmds.setAttr(ctl + ".tz", 2.5)          # base tz 는 정적
a = cmds.animLayer("a", addSelectedObjects=True)
top = cmds.animLayer("lyrTop", addSelectedObjects=True)
key_layer(ctl, a, ["tx", "ry", "tz", "sx"], [0, 100, 200, 400, 1000], 3.0)
key_layer(ctl, top, ["tx", "rx"], [10, 500, 990], 1.5)
cmds.setAttr(top + ".weight", 0.7)
before = snapshot(ctl)
count, msg = LMM.merge_range([a, "BaseAnimation"], "BaseAnimation", S, E)
print("  T5:", msg)
check("T5 count = 4", count == 4, count)
report("T5 a + Base => Base", ctl, before)
check("T5 temp layer gone, a still there", not cmds.objExists(LMM.TEMP_BASE_NAME) and cmds.objExists(a) and set(cmds.ls(type="animLayer")) == {"BaseAnimation", "a", "lyrTop"})
bz = curve_of("BaseAnimation", ctl + ".translateZ")
check("T5 static base tz got a curve: 2.5 at 49 / 301, dense inside", bz is not None and abs(ev(bz, 49) - 2.5) < 1e-12 and abs(ev(bz, 301) - 2.5) < 1e-12 and 150.0 in cmds.keyframe(bz, q=True, tc=True))
check("T5 a tz neutralised inside (0 at f150)", abs(ev(curve_of(a, ctl + ".translateZ"), 150)) < 1e-12)

# ================================================================ T6 by-layer(quaternion) rotation + additive scale
for tgt in ("b", None):
    ctl, a, b, top = build_additive()
    for l in (a, b):
        cmds.setAttr(l + ".rotationAccumulationMode", 1)   # By Layer
        cmds.setAttr(l + ".scaleAccumulationMode", 0)      # Additive
    before = snapshot(ctl)
    count, msg = LMM.merge_range([a, b], tgt, S, E)
    print("  T6 ->", tgt, ":", msg)
    report("T6 by-layer rotation + additive scale => %s" % (tgt or "new"), ctl, before)
    check("T6 a sx identity is 0 (Additive scale) at f150", abs(ev(curve_of(a, ctl + ".scaleX"), 150)) < 1e-12)
    if tgt is None:
        check("T6 new layer inherits by-layer / additive-scale (majority)", cmds.getAttr("Merged_Layer.rotationAccumulationMode") == 1 and cmds.getAttr("Merged_Layer.scaleAccumulationMode") == 0)

# ================================================================ T7 source weights (static 0.7 · animated) additive / override
ctl, a, b, top = build_additive()
cmds.setAttr(a + ".weight", 0.7)
cmds.setKeyframe(a + ".weight", t=0, v=0.7); cmds.setKeyframe(a + ".weight", t=1000, v=0.2)
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], b, S, E)
report("T7 additive a with animated weight => b", ctl, before)
ctl, a, b, top = build_override()
cmds.setKeyframe(a + ".weight", t=0, v=0.9); cmds.setKeyframe(a + ".weight", t=1000, v=0.3)
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], b, S, E)
report("T7 override a with animated weight => b (weight curve gated)", ctl, before)
wcurve = cmds.listConnections(a + ".weight", s=True, d=False)[0]
check("T7 animated weight: 0 inside, original curve outside (f1000 = 0.3)", abs(ev(wcurve, 150)) < 1e-12 and abs(ev(wcurve, 1000) - 0.3) < 1e-9)
check("T7 override a + b => new with animated weight", LMM.merge_range([a, b], None, S, E)[0] > 0)

# ================================================================ T9 ranges at the edges · no keys inside · non-integer key
for (s, e, tag) in ((-10, 20, "range before the first keys"), (900, 1100, "range past the last keys"), (150, 160, "a has no key inside")):
    ctl, a, b, top = build_additive()
    before = snapshot(ctl, s, e)
    count, msg = LMM.merge_range([a, b], b, s, e)
    report("T9 [%d, %d] %s" % (s, e, tag), ctl, before)
ctl, a, b, top = build_additive()
cmds.setKeyframe(ctl, at="tx", t=120.5, v=7.0, animLayer=a)
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], b, S, E)
report("T9 non-integer source key (120.5) inside", ctl, before)
check("T9 non-integer key removed from a", 120.5 not in (cmds.keyframe(curve_of(a, ctl + ".translateX"), q=True, tc=True) or []))

# ================================================================ T10 three sources
for tgt in ("b", None):
    ctl, a, b, top = build_additive()
    c3 = cmds.animLayer("c3", addSelectedObjects=True)
    cmds.animLayer(c3, e=True, moveLayerBefore=top)
    key_layer(ctl, c3, ["ty", "rz", "sy"], [5, 77, 333, 800], 1.2)
    before = snapshot(ctl)
    count, msg = LMM.merge_range([a, b, c3], tgt, S, E)
    print("  T10 ->", tgt, ":", msg)
    report("T10 a + b + c3 => %s" % (tgt or "new"), ctl, before)
    if tgt is None:
        check("T10 new layer above c3 (topmost source)", cmds.animLayer("BaseAnimation", q=True, children=True) == ["b", "a", "c3", "Merged_Layer", "lyrTop"])

# ================================================================ T11 refusals (scene unchanged)
ctl, a, b, top = build_additive()
plugs_all = long_plugs(ctl)
keep = all_curve_values(["BaseAnimation", a, b, top], plugs_all)
n_layers = len(cmds.ls(type="animLayer"))


def refused(tag, args, kw=None, needle="Skipped"):
    count, msg = LMM.merge_range(*args, **(kw or {}))
    check("T11 refused: " + tag, count == 0 and needle in msg, msg[:140])


refused("no layers", ([], None, S, E))
refused("only the target checked", ([b], b, S, E), needle="nothing to merge")
refused("start > end", ([a, b], b, 300, 50), needle="greater than")
refused("sample_by 0", ([a, b], b, S, E), dict(sample_by=0), needle="Sample by")
refused("missing layer", (["ghost", b], b, S, E), needle="not an animation layer")
refused("Base source -> other target", (["BaseAnimation", a], a, S, E), needle="BaseAnimation can only")
refused("Base source -> new layer", (["BaseAnimation", a], None, S, E), needle="BaseAnimation can only")
cmds.setAttr(b + ".weight", 0.6)
refused("target weight 0.6", ([a, b], b, S, E), needle="weight is 0.6")
cmds.setAttr(b + ".weight", 1.0)
cmds.setKeyframe(b + ".weight", t=0, v=1.0)
refused("target weight animated", ([a, b], b, S, E), needle="weight is animated")
cmds.cutKey(b + ".weight", clear=True); cmds.setAttr(b + ".weight", 1.0)
cmds.animLayer(a, e=True, mute=True)
refused("muted source", ([a, b], b, S, E), needle="is muted")
cmds.animLayer(a, e=True, mute=False)
cmds.animLayer(a, e=True, lock=True)
refused("locked source", ([a, b], b, S, E), needle="is locked")
cmds.animLayer(a, e=True, lock=False)
cmds.animLayer(top, e=True, solo=True)
refused("solo somewhere", ([a, b], b, S, E), needle="Solo is on")
cmds.animLayer(top, e=True, solo=False)
child = cmds.animLayer("child", parent=a)
refused("source has child layer", ([a, b], b, S, E), needle="has child layers")
refused("child layer as source", ([child, b], b, S, E), needle="is a child layer")
cmds.delete(child)
check("T11 nothing changed by the refusals", keep == all_curve_values(["BaseAnimation", a, b, top], plugs_all) and len(cmds.ls(type="animLayer")) == n_layers)
ctl, a, b, top = build_override()
refused("selected objects only + override source", ([a, b], b, S, E), dict(objects=[ctl]), needle="override source")

# ================================================================ T12 smart bake = approximate + warning
ctl, a, b, top = build_additive()
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], None, S, E, smart=True, smart_tolerance=0.5)
print("  T12:", msg)
di, wi = max_diff(before[0], snap(ctl, INT_T))
nkeys = cmds.keyframe(curve_of("Merged_Layer", ctl + ".translateX"), q=True, kc=True)
check("T12 smart bake: fewer keys, deviates on integer frames, log says Smart bake + [Warning]", nkeys < 253 and di > 1e-3 and "Smart bake is on" in msg and "[Warning] Verified" in msg, "keys %d dev %.3g" % (nkeys, di))

# ================================================================ T13 two consecutive merges sharing a boundary
ctl, a, b, top = build_additive()
before = snapshot(ctl, 50, 600)
count, msg = LMM.merge_range([a, b], b, 50, 300)
count2, msg2 = LMM.merge_range([a, b], b, 300, 600)
print("  T13:", msg2)
report("T13 [50,300] then [300,600] into b", ctl, before)
check("T13 second merge verified clean", "Verified" in msg2 and "[Warning]" not in msg2)

# ================================================================ T14 whole key range (= Maya's full merge) + source_key_range
ctl, a, b, top = build_additive()
check("T14 source_key_range(a, b) = (0, 1000)", LMM.source_key_range([a, b]) == (0, 1000), LMM.source_key_range([a, b]))
before = snapshot(ctl, 0, 1000)
count, msg = LMM.merge_range([a, b], None, 0, 1000)
di = report("T14 full range into new layer", ctl, before)
ca = curve_of(a, ctl + ".translateX")
check("T14 sources left with identity keys only inside", abs(ev(ca, 500)) < 1e-12)
ctl, a, b, top = build_additive()
before = snapshot(ctl, 0, 1000)
try:
    mel.eval('source "performAnimLayerMerge.mel";')
    mel.eval('optionVar -iv animLayerMergeSmartBake 0; optionVar -iv animLayerMergeDeleteLayers 1; optionVar -iv animLayerMergeUp 1; optionVar -fv animLayerMergeByTime 1.0;')
    mel.eval('animLayerMerge({"a","b"});')
    dm, wm = max_diff(before[0], snap(ctl, INT_T))
    print("  T14 (info) Maya's own animLayerMerge : integer frames max diff %.2e ; ours %.2e" % (dm, di))
    check("T14 (info) ours is at least as exact as Maya's merge on integer frames", di <= max(dm, 1e-12))
except Exception as ex:
    print("  T14 Maya merge failed headless :", ex)

# ================================================================ T15 performance 50 ctl (single call vs chunked)
ctls, a, b, top = build_additive(n=50)
t0 = time.time()
count, msg = LMM.merge_range([a, b], b, S, E, verify=False, progress=None)
dt_chunk = time.time() - t0
ctls, a, b, top = build_additive(n=50)
saved = LMM.BAKE_CHUNK_PLUGS
LMM.BAKE_CHUNK_PLUGS = 10 ** 6
t0 = time.time()
count1, msg1 = LMM.merge_range([a, b], b, S, E, verify=False)
dt_single = time.time() - t0
LMM.BAKE_CHUNK_PLUGS = saved
ctls, a, b, top = build_additive(n=50)
t0 = time.time()
LMM.merge_range([a, b], b, S, E, verify=True)
dt_verify = time.time() - t0
print("  T15 (info) 50 ctl x %d plugs x 251 f : chunked %.1fs, single call %.1fs, chunked + verify %.1fs" % (count, dt_chunk, dt_single, dt_verify))
check("T15 (info) chunked bake not slower than single call by more than 30%%", dt_chunk <= dt_single * 1.3 + 0.5, "%.1f vs %.1f" % (dt_chunk, dt_single))

# ================================================================ T16 undo = one step
ctl, a, b, top = build_additive()
keep = all_curve_values(["BaseAnimation", a, b, top], plugs_all)
LMM.merge_range([a, b], None, S, E)
cmds.undo()
check("T16 one undo removes the new layer and restores every curve", not cmds.objExists("Merged_Layer") and keep == all_curve_values(["BaseAnimation", a, b, top], plugs_all))
LMM.merge_range([a, b], b, S, E)
cmds.undo()
check("T16 one undo restores an in-place merge", keep == all_curve_values(["BaseAnimation", a, b, top], plugs_all))
ctl = new_scene(); cmds.select(ctl)
a = cmds.animLayer("a", addSelectedObjects=True)
key_layer(ctl, a, ["tx", "ry"], [0, 100, 200, 400, 1000], 3.0)
keep = all_curve_values(["BaseAnimation", a], plugs_all)
LMM.merge_range([a], "BaseAnimation", S, E)
cmds.undo()
check("T16 one undo restores a Base merge (temp layer gone too)", keep == all_curve_values(["BaseAnimation", a], plugs_all) and not cmds.objExists(LMM.TEMP_BASE_NAME))

# ================================================================ T17 override EXISTING target with a keyless member
ctl = new_scene(); cmds.select(ctl)
b = cmds.animLayer("b", override=True)
for at in ["tx", "ty", "rz", "rx"]:
    cmds.animLayer(b, e=True, attribute=ctl + "." + at)
key_layer(ctl, b, ["tx", "ty", "rz"], [30, 60, 180, 300, 900], 2.0)     # rx 는 멤버지만 키 없음(정적 override)
a = cmds.animLayer("a")
cmds.animLayer(a, e=True, attribute=ctl + ".tx")
key_layer(ctl, a, ["tx"], [0, 100, 200, 400, 1000], 3.0)
top = cmds.animLayer("lyrTop", addSelectedObjects=True)
key_layer(ctl, top, ["tx", "rx"], [10, 500, 990], 1.5)
cmds.setAttr(top + ".weight", 0.7)
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], b, S, E)
print("  T17:", msg)
report("T17 additive a => existing OVERRIDE b (tx shared member)", ctl, before)
check("T17 keyless override member rx untouched (no curve created)", curve_of(b, ctl + ".rotateX") is None)
a2 = cmds.animLayer("a2")
cmds.animLayer(a2, e=True, attribute=ctl + ".ry")
key_layer(ctl, a2, ["ry"], [0, 100, 200, 400, 1000], 3.0)
refused("override target lacking the sources' channels (b has no ry)", ([a2, b], b, S, E), needle="override layer and the sources key channels")

# ================================================================ T23 additive source with a static (keyless) member value
ctl, a, b, top = build_additive()
ib = LMM._blend_input_plug(a, ctl + ".rotateX")
check("T23 blend input plug found for a keyless additive member", ib is not None and cmds.objExists(ib), ib)
cmds.setAttr(ib, 12.0)
check("T23 static value read back", abs((LMM._blend_input_value(a, ctl + ".rotateX") or 0) - 12.0) < 1e-9)
before = snapshot(ctl)
count, msg = LMM.merge_range([a, b], b, S, E)
print("  T23:", msg)
report("T23 additive a with static rx = 12 (no key) => b", ctl, before)
crx = curve_of(a, ctl + ".rotateX")
check("T23 static member counted and keyed on a: 12 outside, 0 inside", count == 5 and crx is not None and abs(ev(crx, 10) - 12) < 1e-9
      and abs(ev(crx, 150)) < 1e-12 and abs(ev(crx, 900) - 12) < 1e-9 and "hold a non-zero value" in msg, (count, crx))
check("T23 b received rx", curve_of(b, ctl + ".rotateX") is not None)

# ================================================================ T18 selected objects only
ctls, a, b, top = build_additive(n=2)
before = snapshot(ctls)
keep1 = all_curve_values([a, b], long_plugs(ctls[1]))
count, msg = LMM.merge_range([a, b], b, S, E, objects=[ctls[0]])
print("  T18:", msg)
check("T18 count = 4 (ctl0 only)", count == 4, count)
report("T18 objects filter : both objects' world unchanged", ctls, before)
check("T18 ctl1 curves untouched on a and b", keep1 == all_curve_values([a, b], long_plugs(ctls[1])))
check("T18 ctl0 merged on b (tz now keyed on b)", curve_of(b, ctls[0] + ".translateZ") is not None and curve_of(b, ctls[1] + ".translateZ") is None)

# ================================================================ T19 progress callback
ctl, a, b, top = build_additive()
calls = []
LMM.merge_range([a, b], None, S, E, progress=lambda d, t, m=None: calls.append((d, t, m)))
check("T19 progress called, ends at total", calls and calls[-1][0] == calls[-1][1], (len(calls), calls[-1] if calls else None))

# ================================================================ T20 override above masks the result -> warning
ctl, a, b, top = build_additive()
mask = cmds.animLayer("mask", override=True)
cmds.animLayer(mask, e=True, attribute=ctl + ".tx")
count, msg = LMM.merge_range([a, b], b, S, E)
check("T20 non-merged override above warns", "override layer 'mask' above the result masks" in msg, msg[-200:])

# ================================================================ T21 list / labels for the UI
ctl, a, b, top = build_override()
cmds.animLayer(a, e=True, selected=True)
rows, selected = LMM.list_layers_stack()
check("T21 list_layers_stack top first + Base last, selected reported", [r["name"] for r in rows] == ["lyrTop", "a", "b", "BaseAnimation"] and selected == ["a"], ([r["name"] for r in rows], selected))
check("T21 row labels", LMM.row_label(rows[1]).startswith("a    override  w 1.00") and LMM.row_label(rows[3]) == "BaseAnimation    base", [LMM.row_label(r) for r in rows])
check("T21 auto_result: override wins, ties -> 1", LMM.auto_result([a, b]) == (True, 1, 0) and LMM.auto_result([b]) == (False, 1, 0))

# ================================================================ T22 UI smoke (offscreen) : 탭 존재 · 기본값 · 영어
try:
    from tools.A00110_animTool_V02.app.ui.main_window import MainWindow
    win = MainWindow()
    labels = [win.bake_tabs.tabText(i) for i in range(win.bake_tabs.count())]
    check("T22 Bake sub tabs include 'Merge Layers'", "Merge Layers" in labels, labels)
    win.on_ml_refresh_layers(quiet=True)
    names = [win.lw_ml_layers.item(i).data(Qt.UserRole) for i in range(win.lw_ml_layers.count())]
    check("T22 layer list filled top first + Base", names == ["lyrTop", "a", "b", "BaseAnimation"], names)
    check("T22 defaults: existing radio, verify on, smart off, sample 1.0", win.rb_ml_existing.isChecked() and win.cb_ml_verify.isChecked()
          and not win.cb_ml_smart.isChecked() and abs(win.sb_ml_sample.value() - 1.0) < 1e-9)
    check("T22 button text english", win.btn_ml_merge.text() == "Merge Range")
    win.close()
except Exception as ex:
    check("T22 UI smoke", False, repr(ex))

print("\n%d / %d passed" % (sum(R), len(R)))
maya.standalone.uninitialize()
