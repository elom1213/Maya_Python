# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.48 - Bake > Fix Sliding (FixSlidingManager) 시험 (mayapy headless)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_fix_sliding.py
# 계획서 docs/plans/a00110_fix_sliding_plan.md §6. 핵심 = 6 (손으로 selectKey + run_hold 한 결과와 1e-9 대조).
import os
import sys

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

from tools.A00110_animTool_V02.app.core import FixSlidingManager as FS   # noqa: E402
from tools.A00110_animTool_V02.app.core import HoldLayerManager as HLM   # noqa: E402
from tools.A00110_animTool_V02.app.core import HotkeyManager   # noqa: E402
from tools.A00110_animTool_V02.app.core import LayerKeyManager as LKM   # noqa: E402
from tools.A00110_animTool_V02.app.core import AnimLayerManager as ALM   # noqa: E402

R = []
PRE = "JUN_A00110_holdLayer_"
TR = ("translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ")
cmds.inViewMessage = lambda **kw: None      # headless


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def clear_optvars():
    for k in ("enabled", "offset", "layer", "axis_values", "use_current", "view_layer", "current_axes"):
        if cmds.optionVar(exists=PRE + k):
            cmds.optionVar(remove=PRE + k)


def keys(curve):
    if not curve:
        return {}
    t = cmds.keyframe(curve, q=True, timeChange=True) or []
    v = cmds.keyframe(curve, q=True, valueChange=True) or []
    return dict(zip([round(x, 6) for x in t], v))


def curves_of(obj, layer):
    return dict((a, keys(LKM.layer_curve("{0}.{1}".format(obj, a), layer))) for a in TR)


def same(c1, c2, tol=1e-9):
    if sorted(c1) != sorted(c2):
        return False
    return all(sorted(c1[a]) == sorted(c2[a]) and all(abs(c1[a][t] - c2[a][t]) < tol for t in c1[a]) for a in c1)


def make_scene(xs, start=1, member=True, rot=True, name="foot"):
    """xs[i] = 프레임 start+i 의 tx. 매 프레임 Base 키(tx, ty=0, tz, rx/ry/rz). AnimLayer1 에 T/R 멤버."""
    cmds.file(new=True, force=True)
    foot = cmds.spaceLocator(n=name)[0]
    for i, x in enumerate(xs):
        f = start + i
        cmds.setKeyframe(foot, at="tx", t=f, v=x)
        cmds.setKeyframe(foot, at="ty", t=f, v=0.0)
        cmds.setKeyframe(foot, at="tz", t=f, v=0.3 * x)
        if rot:
            cmds.setKeyframe(foot, at="rx", t=f, v=2.0 * x)
            cmds.setKeyframe(foot, at="ry", t=f, v=-x)
            cmds.setKeyframe(foot, at="rz", t=f, v=0.0)
    lay = cmds.animLayer("AnimLayer1")
    if member:
        cmds.select(foot)
        cmds.animLayer(lay, e=True, attribute=[foot + "." + a for a in TR])
    cmds.select(clear=True)
    cmds.currentTime(start)
    return foot, lay


def hotkey_settings(offset=5, enabled=True):
    HLM.update(enabled=enabled, layer="AnimLayer1", offset=offset, view_layer="",
               axis_values={"rx": 0.0, "rz": 0.0, "ty": 0.0}, current_axes=["ry", "tx", "tz"])


def walk_xs():
    """f1-10 이동 0->10, f11-30 정지(+-0.01 지터), f31-40 이동 10->20, f41-60 정지."""
    xs = []
    for f in range(1, 61):
        if f <= 10:
            x = float(f - 1) * 10.0 / 9.0
        elif f <= 30:
            x = 10.0 + 0.01 * (-1) ** f
        elif f <= 40:
            x = 10.0 + (f - 30) * 1.0
        else:
            x = 20.0 + 0.01 * (-1) ** f
        xs.append(x)
    return xs


clear_optvars()

# ================================================================ 순수 함수 1~4
pts = [(0, 0, 0), (1, 0, 0), (1, 2, 0), (1, 2, 0)]
check("P1 speeds: length kept, first = next diff", FS.speeds(pts) == [1.0, 1.0, 2.0, 0.0], FS.speeds(pts))
check("P1b speeds: Y off ignores vertical", FS.speeds(pts, (True, False, True)) == [1.0, 1.0, 0.0, 0.0])
check("P2 smooth: window 1 = same, 3 = centered mean, edges shrink",
      FS.smooth([0, 3, 6], 1) == [0, 3, 6] and FS.smooth([0, 3, 6], 3) == [1.5, 3.0, 4.5])
check("P2b smooth: even window 4 -> half 2 (window 5)", FS.smooth([0, 0, 5, 0, 0], 4) == [5 / 3.0, 1.25, 1.0, 1.25, 5 / 3.0],
      FS.smooth([0, 0, 5, 0, 0], 4))
check("P3 still_spans: strict <, spans touching both ends",
      FS.still_spans([0, 0, 1, 0.5, 0, 0], 10, 0.5) == [(10, 11), (14, 15)],
      FS.still_spans([0, 0, 1, 0.5, 0, 0], 10, 0.5))
ap, sh = FS.split_spans([(1, 3), (5, 8)], 3)
check("P4 split_spans: L == M short, L == M+1 apply", ap == [(5, 8)] and sh == [(1, 3)], (ap, sh))
m, ms = FS.merge_gaps([(0, 10), (12, 20), (25, 30), (36, 40)], 4)
check("P5 merge_gaps: gap 1 and gap 4 merge (chain), gap 5 stays",
      m == [(0, 30), (36, 40)] and len(ms) == 2, (m, ms))
check("P5b merge_gaps: G=0 never merges", FS.merge_gaps([(0, 10), (12, 20)], 0)[0] == [(0, 10), (12, 20)])
check("P6 blend_start: clamp to previous end, no clamp when off / earlier",
      FS.blend_start(16, 8, 10, True) == 10.0 and FS.blend_start(16, 8, 10, False) == 8.0
      and FS.blend_start(30, 5, 10, True) == 25.0)

# ================================================================ 5 Preview
foot, lay = make_scene(walk_xs())
hotkey_settings()
before = curves_of(foot, LKM.root_layer())
res, lines = FS.preview([foot], 1, 60, smooth=3, threshold_pct=5.0, merge_gap=0, min_span=5, debug=False)
r = res[foot]
exp = FS.still_spans(FS.smooth(FS.speeds([(x, 0.0, 0.3 * x) for x in walk_xs()]), 3), 1, r["threshold"])
check("5 Preview: spans = pure computation on the same data, two still spans ~[11,30] / [41,60]",
      r["spans"] == exp and len(r["apply"]) == 2 and abs(r["apply"][0][0] - 11) <= 2 and r["apply"][1][1] == 60,
      (r["spans"], r["apply"]))
check("5b Preview: no key changed", curves_of(foot, LKM.root_layer()) == before)
L1 = r["apply"][0][1] - r["apply"][0][0] + 1
_r2, _l = FS.preview([foot], 1, 60, smooth=3, threshold_pct=5.0, merge_gap=0, min_span=L1, debug=False)
check("5c Preview: M = span length -> that span is short", r["apply"][0] in _r2[foot]["short"], _r2[foot]["short"])

# ================================================================ 6 순수 Shift+A 대조 (G=0, Clamp/Lock 끔)
OPTS = dict(smooth=3, threshold_pct=5.0, min_span=5, merge_gap=0, clamp_blend=False, lock_end=False, debug=False)
foot, lay = make_scene(walk_xs())
hotkey_settings()
cnt, lines = FS.run([foot], 1, 60, **OPTS)
got_base, got_lay = curves_of(foot, LKM.root_layer()), curves_of(foot, lay)
# 손으로 : 같은 장면, 구간마다 selectKey (T/R Base 커브, [a,b]) + run_hold (보기 = Base)
foot2, lay2 = make_scene(walk_xs())
hotkey_settings()
pre = FS.analyze([foot2], 1, 60, smooth=3, threshold_pct=5.0, merge_gap=0, min_span=5)[foot2]
root = LKM.root_layer()
ALM.set_selected([root])
for a, b in pre["apply"]:
    cmds.select(foot2, r=True)
    crvs = [LKM.layer_curve(foot2 + "." + at, root) for at in TR]
    cmds.selectKey(clear=True)
    for c in crvs:
        cmds.selectKey(c, time=(a, b), add=True)
    HotkeyManager.run_hold()
cmds.selectKey(clear=True)
man_base, man_lay = curves_of(foot2, root), curves_of(foot2, lay2)
check("6 Run == manual selectKey + Shift+A per span (base + layer curves, 1e-9)",
      cnt == 2 and same(got_base, man_base) and same(got_lay, man_lay),
      (cnt, lines[-1]))

# ================================================================ 7 짧은 구간은 그대로
foot, lay = make_scene(walk_xs())
hotkey_settings()
b0 = curves_of(foot, LKM.root_layer())
cnt, lines = FS.run([foot], 1, 60, **dict(OPTS, min_span=100))
check("7 all spans <= M -> no key changed, reported as short",
      cnt == 0 and curves_of(foot, LKM.root_layer()) == b0 and "short span(s) skipped" in lines[-1], lines[-1])

# ================================================================ 8 레이어 멤버 아님
foot, lay = make_scene(walk_xs(), member=False)
hotkey_settings()
cnt, lines = FS.run([foot], 1, 60, **OPTS)
base_tx = keys(LKM.layer_curve(foot + ".translateX", LKM.root_layer()))
check("8 not a layer member: Hold done, Layer Blend 'Skipped' message",
      cnt == 2 and any("Skipped: foot (not in layer)" in l for l in lines) and len(base_tx) < 60, lines[-3:])

# ================================================================ 9 안 움직이는 오브젝트
foot, lay = make_scene([5.0] * 30)
hotkey_settings()
b0 = curves_of(foot, LKM.root_layer())
cnt, lines = FS.run([foot], 1, 30, **OPTS)
check("9 not moving: skipped with warning, no change",
      cnt == 0 and any("does not move" in l for l in lines) and curves_of(foot, LKM.root_layer()) == b0, lines[:2])

# ================================================================ 10 Layer Blend 끔 / 11 Translate 끔
foot, lay = make_scene(walk_xs())
hotkey_settings()
l0 = curves_of(foot, lay)
cnt, lines = FS.run([foot], 1, 60, **dict(OPTS, layer_blend=False))
check("10 layer_blend off: Hold only, layer curves untouched", cnt == 2 and curves_of(foot, lay) == l0)
foot, lay = make_scene(walk_xs())
hotkey_settings()
t0_ = keys(LKM.layer_curve(foot + ".translateX", LKM.root_layer()))
cnt, lines = FS.run([foot], 1, 60, **dict(OPTS, translate=False, layer_blend=False))
check("11 translate off: only rotate curves held",
      keys(LKM.layer_curve(foot + ".translateX", LKM.root_layer())) == t0_
      and len(keys(LKM.layer_curve(foot + ".rotateX", LKM.root_layer()))) < 60)

# ================================================================ 12 디버그 노드
foot, lay = make_scene(walk_xs())
hotkey_settings()
cmds.createNode("transform", name="_debug_speed")      # v02.48 단일 노드가 남아 있던 씬
cnt, lines = FS.run([foot], 1, 60, **dict(OPTS, debug=True))
DN = FS.debug_node_name(foot)
attrs = [a for a in (cmds.listAttr(DN, userDefined=True) or [])]
kc = cmds.keyframe(DN + ".speed", q=True, keyframeCount=True)
thr = set(round(v, 9) for v in cmds.keyframe(DN + ".threshold", q=True, valueChange=True))
spd = cmds.keyframe(DN + ".speed", q=True, valueChange=True)
resv = cmds.keyframe(DN + ".result", q=True, valueChange=True)
a, b = r["apply"][0]               # 5 Preview 에서 같은 데이터로 찾은 첫 적용 구간
inner = range(a, b)                # 구간 안쪽 프레임 a+1..b 의 인덱스 (인덱스 = f - 1)
check("12 debug node 'foot_debug_speed': speed / smooth / threshold / result + source / info, keys = frames",
      DN == "foot_debug_speed" and sorted(attrs) == sorted(["source", "info", "speed", "smooth", "threshold", "result"])
      and cmds.getAttr(DN + ".source") == foot and kc == 60 and len(thr) == 1, (DN, attrs, kc, thr))
colors = {}
for at in ("speed", "smooth", "threshold", "result"):
    crv = cmds.listConnections(DN + "." + at, type="animCurve")[0]
    colors[at] = (cmds.getAttr(crv + ".useCurveColor"), tuple(round(c, 2) for c in cmds.getAttr(crv + ".curveColor")[0]))
check("12e Graph Editor colors: white / light sky blue / red / green (v02.49)",
      colors == {"speed": (True, (1.0, 1.0, 1.0)), "smooth": (True, (0.53, 0.81, 0.98)),
                 "threshold": (True, (1.0, 0.0, 0.0)), "result": (True, (0.0, 1.0, 0.0))}, colors)
check("12f the old single '_debug_speed' node is removed", not cmds.objExists("_debug_speed"))
check("12b debug result (measured after the fix) lower than raw speed inside a fixed span",
      sum(resv[i] for i in inner) < sum(spd[i] for i in inner), (sum(resv[i] for i in inner), sum(spd[i] for i in inner)))
FS.run([foot], 1, 60, **dict(OPTS, debug=True, layer_blend=False))
check("12c second run keeps one debug node per object", cmds.ls("*_debug_speed*", type="transform") == [DN],
      cmds.ls("*_debug_speed*", type="transform"))
# 오브젝트 둘 -> 노드 둘 (TSL 에 든 개수만큼)
foot, lay = make_scene(walk_xs())
other = cmds.duplicate(foot, name="ns_other")[0]
hotkey_settings()
_r, lines = FS.preview([foot, other], 1, 60, smooth=3, threshold_pct=5.0, merge_gap=0, min_span=5, debug=True)
dn = sorted(cmds.ls("*_debug_speed", type="transform"))
check("12d two listed objects -> two debug nodes (one each)",
      dn == sorted([FS.debug_node_name(foot), FS.debug_node_name(other)]) and len(dn) == 2, dn)

# ================================================================ 13 undo 한 번 · 시간 복원
foot, lay = make_scene(walk_xs())
hotkey_settings()
cmds.currentTime(33)
cmds.undoInfo(state=True, infinity=True)
cmds.flushUndo()
b0, l0 = curves_of(foot, LKM.root_layer()), curves_of(foot, lay)
FS.run([foot], 1, 60, **dict(OPTS, debug=True, clamp_blend=True, lock_end=True, merge_gap=4))
changed = curves_of(foot, LKM.root_layer()) != b0
cmds.undo()
check("13 one undo reverts base + layer curves (debug node stays), time restored",
      changed and curves_of(foot, LKM.root_layer()) == b0 and curves_of(foot, lay) == l0
      and cmds.objExists(FS.debug_node_name(foot)) and cmds.currentTime(q=True) == 33.0)

# ================================================================ 14 force : Hot Key > Main 꺼짐 + 다른 레이어 보기
foot, lay = make_scene(walk_xs())
hotkey_settings(enabled=False)
ALM.set_selected([lay])
cnt, lines = FS.run([foot], 1, 60, **OPTS)
check("14 Hot Key Layer Blend off + viewing AnimLayer1: Fix Sliding still keys the layer (force)",
      cnt == 2 and len(keys(LKM.layer_curve(foot + ".translateX", lay))) >= 4, lines[-1])

# ================================================================ 14a 대안 B (사용자 예시 [0,10] · [12,20])
# f0-10 정지 x=0, f11 0.5, f12-20 정지 x=1 (틈 f11-12 의 속도 0.5), f21-30 이동 1/f, f31-40 정지
xs = [0.0] * 11 + [0.5] + [1.0] * 9 + [1.0 + i for i in range(1, 11)] + [11.0] * 10
foot, lay = make_scene(xs, start=0)
hotkey_settings(offset=5)
res = FS.analyze([foot], 0, 40, smooth=1, threshold_pct=5.0, merge_gap=4, min_span=3)[foot]
check("14a-1 merge: [0,10] + [13,20] -> [0,20] (gap 2 <= 4), [31,40] separate",
      res["apply"] == [(0, 20), (31, 40)] and len(res["merges"]) == 1, (res["spans"], res["apply"]))
cnt, lines = FS.run([foot], 0, 40, smooth=1, threshold_pct=5.0, min_span=3, merge_gap=4,
                    clamp_blend=True, lock_end=True, debug=False)
lt = sorted(keys(LKM.layer_curve(foot + ".translateX", lay)))
check("14a-2 layer keys only at -5, 0, 20 (first span) and 26, 31, 40 - no stray key like f7",
      lt == [-5.0, 0.0, 20.0, 26.0, 31.0, 40.0], lt)

# ================================================================ 14b 대안 A (gap 5 > G 4, N=8)
xs = [0.0] * 11 + [0.2 * i for i in range(1, 6)] + [1.0] * 10      # f0-10 정지, f11-15 이동, f16-25 정지
foot, lay = make_scene(xs, start=0)
hotkey_settings(offset=8)
res = FS.analyze([foot], 0, 25, smooth=1, threshold_pct=5.0, merge_gap=4, min_span=3)[foot]
cnt, lines = FS.run([foot], 0, 25, smooth=1, threshold_pct=5.0, min_span=3, merge_gap=4,
                    clamp_blend=True, lock_end=True, debug=False)
lt = sorted(keys(LKM.layer_curve(foot + ".translateX", lay)))
check("14b-1 spans [0,10] / [16,25] not merged (gap 5)", res["apply"] == [(0, 10), (16, 25)], res["apply"])
check("14b-2 second blend starts at f10 (clamped from f8), log says clamped",
      10.0 in lt and 8.0 not in lt and any("clamped from f8" in l for l in lines), (lt, [l for l in lines if "clamp" in l]))
foot, lay = make_scene(xs, start=0)
hotkey_settings(offset=8)
FS.run([foot], 0, 25, smooth=1, threshold_pct=5.0, min_span=3, merge_gap=4, clamp_blend=False, lock_end=False, debug=False)
check("14b-3 clamp off -> blend starts at f8", 8.0 in keys(LKM.layer_curve(foot + ".translateX", lay)))

# ================================================================ 14c 대안 D (구간 끝 잠금)
ok = True
info = []
foot2, lay2 = make_scene(walk_xs())
hotkey_settings()
ap = FS.analyze([foot2], 1, 60, smooth=3, threshold_pct=5.0, merge_gap=4, min_span=5)[foot2]["apply"]
cnt, lines = FS.run([foot2], 1, 60, **dict(OPTS, merge_gap=4, clamp_blend=True, lock_end=True))
for a_, b_ in ap:
    for at in TR:
        crv = LKM.layer_curve(foot2 + "." + at, lay2)
        vals = [cmds.keyframe(crv, q=True, eval=True, time=(t, t), valueChange=True)[0]
                for t in [a_ + 0.5 * i for i in range(int(2 * (b_ - a_)) + 1)]]
        flat = max(vals) - min(vals) < 1e-9
        tan_a = cmds.keyTangent(crv, q=True, time=(a_, a_), outTangentType=True)
        tan_b = cmds.keyTangent(crv, q=True, time=(b_, b_), inTangentType=True)
        if not (flat and tan_a == ["flat"] and tan_b == ["flat"]):
            ok = False
            info.append((at, a_, b_, max(vals) - min(vals), tan_a, tan_b))
check("14c lock: every layer T/R curve constant over [a, b] (int + half frames), a out / b in flat", ok, info[:3])

# 14d 재샘플 월드 속도 : 적용 구간 안쪽 < 1e-6
pos = FS.sample_positions([foot2], 1, 60)[foot2]
sp = FS.speeds(pos)
inner_max = max(sp[f - 1] for a_, b_ in ap for f in range(a_ + 1, b_ + 1))
check("14d B+A+D: world speed inside every fixed span < 1e-6", inner_max < 1e-6, inner_max)

# ================================================================ 15 탭에서 고른 레이어 · N (v02.49)
foot, lay = make_scene(walk_xs())
lay2 = cmds.animLayer("AnimLayer2")
cmds.select(foot)
cmds.animLayer(lay2, e=True, attribute=[foot + "." + a for a in TR])
cmds.select(clear=True)
hotkey_settings(offset=5)
HLM.update(layer="")                       # Hot Key > Main 에는 레이어가 없다
ok, _l, _n, msg = FS.layer_blend_status()
check("15a Hot Key layer empty -> status warns", not ok and "choose one" in msg, msg)
cnt, lines = FS.run([foot], 1, 60, **dict(OPTS, layer="AnimLayer2", offset=7))
k2 = sorted(keys(LKM.layer_curve(foot + ".translateX", lay2)))
k1 = keys(LKM.layer_curve(foot + ".translateX", lay))
check("15b run(layer=AnimLayer2, offset=7): keys on AnimLayer2 at a-7, nothing on AnimLayer1",
      cnt == 2 and k2 and (k2[0] == r["apply"][0][0] - 7) and not k1, (k2, k1, lines[-1]))
check("15c Hot Key > Main settings untouched", HLM.load_settings()["layer"] == "" and HLM.load_settings()["offset"] == 5)

clear_optvars()
print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
