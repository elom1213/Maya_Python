# -*- coding: utf-8 -*-
"""관찰·재현 스크립트 (회귀 시험 아님) — `Bake > Counter Layer` Stationary spans only 모드 프로토타입.

계획서: docs/plans/A00110_animTool_V02_counter_layer_stationary_plan.md (§4 알고리즘 · §5 실측).
사용자 씬을 mayapy 로 열어 **저장 없이** 정지 구간 고정 보정 레이어를 만들고 수치를 `exp_plant_hold.txt` 에 쓴다.
아래 SCENE 경로를 바꿔서 실행:  "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe" exp_plant_hold_zihan.py
구현 때 test_counter_layer.py 로 흡수하고 삭제한다 (v02.26 exp_counter_layer.py 와 같은 절차).
"""
SCENE = "C:/JUN/JUN_MUE/00_04_02_ANI_00_PJ_010/scenes/5010_cleanup_BCM_ZIHAN/00010_cleanup_ZIHAN_00120_tmp.mb"
import math, time
from array import array
out = open("exp_plant_hold.txt", "w", encoding="utf-8")
def P(*a):
    out.write(" ".join(str(x) for x in a) + "\n"); out.flush()
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds
import maya.api.OpenMaya as om

path = SCENE
try:
    cmds.file(path, open=True, force=True, loadReferenceDepth="all", prompt=False)
except Exception as e:
    P("OPEN WARN:", repr(e)[:200])

L = "test:ZIHAN:Cage:CH_l_foot_xx_ctl"
R = "test:ZIHAN:Cage:CH_r_foot_xx_ctl"
GL = "global_lyr"
T_ATTRS = ["tx", "ty", "tz"]; R_ATTRS = ["rx", "ry", "rz"]
_L = dict(tx="translateX", ty="translateY", tz="translateZ", rx="rotateX", ry="rotateY", rz="rotateZ")
LONG = {}
_API_ORDER = [om.MEulerRotation.kXYZ, om.MEulerRotation.kYZX, om.MEulerRotation.kZXY,
              om.MEulerRotation.kXZY, om.MEulerRotation.kYXZ, om.MEulerRotation.kZYX]

def tq(m):
    tm = om.MTransformationMatrix(om.MMatrix(m))
    return tm.translation(om.MSpace.kWorld), tm.rotation(asQuaternion=True)

def qang(q1, q2):
    return math.degrees(2 * math.acos(min(1.0, abs((q1 * q2.inverse()).w))))

def pick_rotation(obj, target_deg, ref_deg):
    ro = _API_ORDER[cmds.getAttr(obj + ".rotateOrder")]
    tgt = om.MEulerRotation(*[math.radians(v) for v in target_deg]); tgt.order = ro
    ref = om.MEulerRotation(*[math.radians(v) for v in ref_deg]); ref.order = ro
    best, best_d = None, None
    for cand in (tgt, tgt.alternateSolution()):
        c = om.MEulerRotation(cand); c.setToClosestCut(ref)
        if not c.asMatrix().isEquivalent(tgt.asMatrix(), 1e-6):
            continue
        d = abs(c.x - ref.x) + abs(c.y - ref.y) + abs(c.z - ref.z)
        if best is None or d < best_d:
            best, best_d = c, d
    return [math.degrees(v) for v in (best.x, best.y, best.z)]

def smoothstep(u): return u * u * (3 - 2 * u)

def detect_spans(objs, start, end, layers, tol_t, tol_r_deg, min_span):
    """pass 1: layers 뮤트 -> 프레임마다 월드 T/Q 스트리밍 -> 정지 구간 + OFF 이동량."""
    for l in layers: cmds.animLayer(l, e=True, mute=True)
    still = dict((o, {}) for o in objs)
    travel = dict((o, {}) for o in objs)
    prev = {}
    try:
        for f in range(start - 1, end + 2):
            cmds.currentTime(f)
            for o in objs:
                t, q = tq(cmds.getAttr(o + ".worldMatrix[0]"))
                if o in prev:
                    pt, pq = prev[o]
                    dt = (t - pt).length()
                    ang = qang(q, pq)
                    still[o][f] = (dt < tol_t and ang < tol_r_deg)
                    travel[o][f] = (dt, ang)
                prev[o] = (t, q)
    finally:
        for l in layers: cmds.animLayer(l, e=True, mute=False)
    spans = {}
    for o in objs:
        runs, f = [], start
        while f <= end:
            if f + 1 <= end and still[o].get(f + 1):
                g = f
                while g + 1 <= end and still[o].get(g + 1): g += 1
                if g - f + 1 >= min_span: runs.append([f, g])
                f = g + 1
            else:
                f += 1
        spans[o] = runs
    return spans, travel

def layer_curve(lyr, plug):
    """plug 로 끝나는 레이어 커브 (blend 노드 inputB 커브)."""
    for c in cmds.animLayer(lyr, q=True, animCurves=True) or []:
        dst = cmds.listConnections(c + ".output", p=True, s=False, d=True) or []
        for d in dst:
            node = d.split(".")[0]
            # blend 노드 -> 출력 -> plug
            outs = cmds.listConnections(node, p=True, s=False, d=True) or []
            if plug in outs or LONG.get(plug) in outs:
                return c
    return None

def plant_hold(objs, layers, start, end, name, anchor="start", blend="travel",
               tol_t=0.01, tol_r=0.1, min_span=2, zero_outside=True, chunk=200):
    t0 = time.time()
    spans, travel = detect_spans(objs, start, end, layers, tol_t, tol_r, min_span)
    t_detect = time.time() - t0
    P("  spans:", dict((o.split(":")[-1], v) for o, v in spans.items()))
    anchors = {}
    skipped = []
    for o in objs:
        a = []
        for (s, e) in spans[o]:
            if s <= start and e >= end:
                skipped.append(o); a = None; break
            if s <= start: a.append(start)
            elif e >= end: a.append(end)
            elif anchor == "start": a.append(s)
            elif anchor == "end": a.append(e)
            else: a.append((s + e) // 2)
        anchors[o] = a
    objs = [o for o in objs if anchors[o] is not None and spans[o]]
    anchor_pose = dict((o, []) for o in objs)
    for o in objs:
        for (s, e), af in zip(spans[o], anchors[o]):
            cmds.currentTime(af)
            anchor_pose[o].append(tq(cmds.getAttr(o + ".worldMatrix[0]")))
    edge = dict((o, []) for o in objs)
    for o in objs:
        for (s, e), (ta, qa) in zip(spans[o], anchor_pose[o]):
            res = []
            for f in (s, e):
                cmds.currentTime(f)
                t, q = tq(cmds.getAttr(o + ".worldMatrix[0]"))
                res.append((ta - t, q.inverse() * qa))
            edge[o].append(res)
    def frac(o, g0, g1, f):
        if blend == "linear": return (f - g0) / float(g1 - g0)
        if blend == "ease": return smoothstep((f - g0) / float(g1 - g0))
        tot = sum(travel[o][k][0] for k in range(g0 + 1, g1 + 1))
        if tot < 1e-9:
            tot = sum(travel[o][k][1] for k in range(g0 + 1, g1 + 1))
            if tot < 1e-9: return (f - g0) / float(g1 - g0)
            return sum(travel[o][k][1] for k in range(g0 + 1, f + 1)) / tot
        return sum(travel[o][k][0] for k in range(g0 + 1, f + 1)) / tot
    zero = (om.MVector(0, 0, 0), om.MQuaternion())
    def delta_at(o, f):
        sp = spans[o]
        for i, (s, e) in enumerate(sp):
            if s <= f <= e:
                return None, i
        prev_i = max([i for i, (s, e) in enumerate(sp) if e < f] or [-1])
        next_i = min([i for i, (s, e) in enumerate(sp) if s > f] or [len(sp)])
        if prev_i >= 0: g0, (dT0, dQ0) = sp[prev_i][1], edge[o][prev_i][1]
        else:          g0, (dT0, dQ0) = start, zero
        if next_i < len(sp): g1, (dT1, dQ1) = sp[next_i][0], edge[o][next_i][0]
        else:
            if zero_outside: g1, (dT1, dQ1) = end, zero
            else: return (dT0, dQ0), None
        u = frac(o, g0, g1, f) if g1 > g0 else 1.0
        return (dT0 * (1 - u) + dT1 * u, om.MQuaternion.slerp(dQ0, dQ1, u)), None
    lyr = cmds.animLayer(name)
    for o in objs:
        for a in T_ATTRS + R_ATTRS:
            cmds.animLayer(lyr, e=True, attribute=o + "." + a)
    frames = list(range(start, end + 1))
    keyed = 0
    t1 = time.time()
    for c0 in range(0, len(frames), chunk):
        fl = frames[c0:c0 + chunk]
        cmds.animLayer(lyr, e=True, mute=True)
        on = dict((o, []) for o in objs)
        for f in fl:
            cmds.currentTime(f)
            for o in objs: on[o].append(array("d", cmds.getAttr(o + ".worldMatrix[0]")))
        cmds.animLayer(lyr, e=True, mute=False)
        for i, f in enumerate(fl):
            cmds.currentTime(f)
            for o in objs:
                d, span_i = delta_at(o, f)
                tm = om.MTransformationMatrix(om.MMatrix(on[o][i]))
                if span_i is not None:
                    ta, qa = anchor_pose[o][span_i]
                    tm.setTranslation(ta, om.MSpace.kWorld); tm.setRotation(qa)
                else:
                    t, q = tm.translation(om.MSpace.kWorld), tm.rotation(asQuaternion=True)
                    tm.setTranslation(t + d[0], om.MSpace.kWorld); tm.setRotation(q * d[1])
                target = list(tm.asMatrix())
                ref_rot = cmds.getAttr(o + ".rotate")[0]
                cmds.xform(o, ws=True, m=target)
                tr = cmds.xform(o, q=True, t=True)
                rot = pick_rotation(o, cmds.getAttr(o + ".rotate")[0], ref_rot)
                vals = dict(zip(T_ATTRS, tr)); vals.update(zip(R_ATTRS, rot))
                for a in T_ATTRS + R_ATTRS:
                    keyed += 1 if cmds.setKeyframe(o, at=a, t=f, v=vals[a], animLayer=lyr) else 0
        del on
    if zero_outside:
        for o in objs:
            for a in T_ATTRS + R_ATTRS:
                LONG[o + "." + a] = o + "." + _L[a]
                crv = layer_curve(lyr, o + "." + a)
                if crv:
                    for t in (start - 1, end + 1):
                        cmds.setKeyframe(crv, time=t, value=0.0)
    P("  keyed %d | detect %.1fs | write %.1fs | total %.1fs (%d obj x %d frames)" % (
        keyed, t_detect, time.time() - t1, time.time() - t0, len(objs), len(frames)))
    return lyr, spans, anchors, skipped

objs = [L, R]; start, end = 4270, 4313
def sample(frames, objs):
    d = {}
    for f in frames:
        cmds.currentTime(f)
        for o in objs: d[(o, f)] = tq(cmds.getAttr(o + ".worldMatrix[0]"))
    return d
def glo_state():
    return [(c, cmds.keyframe(c, q=True, tc=True), cmds.keyframe(c, q=True, vc=True)) for c in cmds.animLayer(GL, q=True, animCurves=True)]
glo_before = glo_state()
wide = list(range(start - 10, end + 11))
ON = sample(wide, objs)

def verify(tag, lyr, spans, anchors):
    NEW = sample(wide, objs)
    worst_span = 0.0; worst_out = 0.0; max_shift = 0.0; max_jump_new = 0.0; max_jump_on = 0.0
    for o in objs:
        for (s, e), af in zip(spans[o], anchors[o]):
            ta, qa = ON[(o, af)]
            for f in range(s, e + 1):
                t, q = NEW[(o, f)]
                worst_span = max(worst_span, (t - ta).length(), qang(q, qa))
        for f in wide:
            t, q = NEW[(o, f)]; t0, q0 = ON[(o, f)]
            sh = (t - t0).length()
            if f < start or f > end: worst_out = max(worst_out, sh)
            else: max_shift = max(max_shift, sh)
            if f > wide[0]:
                max_jump_new = max(max_jump_new, (t - NEW[(o, f - 1)][0]).length())
                max_jump_on = max(max_jump_on, (t0 - ON[(o, f - 1)][0]).length())
    top = (cmds.animLayer(cmds.animLayer(q=True, root=True), q=True, children=True) or [])[-1]
    P("  [%s] span hold err=%.2e | outside-range change=%.2e | max shift vs ON inside=%.3f | max frame jump NEW=%.3f ON=%.3f | global_lyr untouched=%s | top layer=%s"
      % (tag, worst_span, worst_out, max_shift, max_jump_new, max_jump_on, glo_state() == glo_before, top))
    return NEW

P("== run A: anchor=start blend=travel")
lyr, spans, anchors, sk = plant_hold(objs, [GL], start, end, "global_lyr_plant", "start", "travel")
P("  anchors:", dict((o.split(":")[-1], v) for o, v in anchors.items()), "skipped:", sk)
NEW = verify("A", lyr, spans, anchors)
P("  frame | L ON.x  L NEW.x  dX  | R ON.x  R NEW.x  dX   (world X; global only moves X)")
for f in range(start - 2, end + 4):
    P("  %d | %8.3f %8.3f %7.3f | %8.3f %8.3f %7.3f" % (f, ON[(L, f)][0].x, NEW[(L, f)][0].x, NEW[(L, f)][0].x - ON[(L, f)][0].x,
                                                      ON[(R, f)][0].x, NEW[(R, f)][0].x, NEW[(R, f)][0].x - ON[(R, f)][0].x))
cmds.animLayer(lyr, e=True, mute=True)
back = sample(wide, objs)
P("  mute new layer -> equals ON:", max((back[k][0] - ON[k][0]).length() for k in back) < 1e-9)
cmds.animLayer(lyr, e=True, mute=False)
crvs = cmds.animLayer(lyr, q=True, animCurves=True) or []
P("  curves:", len(crvs), "keys/curve:", cmds.keyframe(crvs[0], q=True, kc=True) if crvs else None,
  "first/last key:", (min(cmds.keyframe(crvs[0], q=True, tc=True)), max(cmds.keyframe(crvs[0], q=True, tc=True))) if crvs else None)
# 반 프레임 (보간) 오차 - 스팬 안
cmds.currentTime(4279.5); t_half = tq(cmds.getAttr(L + ".worldMatrix[0]"))[0]
P("  L half-frame 4279.5 vs anchor 4277 pos err: %.2e" % (t_half - ON[(L, 4277)][0]).length())
cmds.delete(lyr)
P("  delete layer -> equals ON:", max((sample(wide, objs)[k][0] - ON[k][0]).length() for k in ON) < 1e-9)

P("== run F: range 4280-4300 (L span 4277-4282 crosses range start -> anchor forced 4280; R span 4303-4305 outside)")
lyr, spans, anchors, sk = plant_hold(objs, [GL], 4280, 4300, "global_lyr_plant", "start", "travel")
P("  anchors:", dict((o.split(":")[-1], v) for o, v in anchors.items()))
NEW = sample(wide, objs)
P("  L 4279->4280 jump NEW=%.4f ON=%.4f | L 4280 shift=%.4f | L 4300 shift=%.4f | L 4301 shift=%.4f" % (
    (NEW[(L,4280)][0]-NEW[(L,4279)][0]).length(), (ON[(L,4280)][0]-ON[(L,4279)][0]).length(),
    (NEW[(L,4280)][0]-ON[(L,4280)][0]).length(), (NEW[(L,4300)][0]-ON[(L,4300)][0]).length(), (NEW[(L,4301)][0]-ON[(L,4301)][0]).length()))
cmds.delete(lyr)
P("== run H: 1000-frame range 3800-4800 both feet (timing + memory shape)")
import tracemalloc
tracemalloc.start()
lyr, spans, anchors, sk = plant_hold(objs, [GL], 3800, 4800, "global_lyr_plant", "start", "travel")
cur, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
P("  spans count:", dict((o.split(":")[-1], len(v)) for o, v in spans.items()), "py peak mem %.1f MB" % (peak / 1e6))
cmds.delete(lyr)
P("== tolerance sweep (detect only, 4270-4313): tol_t 0.01 / 0.3 / 0.5 / 1.0 units, tol_r 0.1 / 1 / 2 / 5 deg")
for tt, tr in [(0.01, 0.1), (0.3, 1.0), (0.5, 2.0), (1.0, 5.0)]:
    sp, _ = detect_spans(objs, start, end, [GL], tt, tr, 2)
    P("  tol_t=%.2f tol_r=%.1f ->" % (tt, tr), dict((o.split(":")[-1], v) for o, v in sp.items()))
P("== run I: 4270-4313 with ON-travel vs OFF-travel? (OFF used) ; also per-frame mute toggle cost")
t0 = time.time()
for f in range(4270, 4314):
    cmds.animLayer(GL, e=True, mute=True); cmds.currentTime(f); cmds.getAttr(L + ".worldMatrix[0]")
    cmds.animLayer(GL, e=True, mute=False); cmds.currentTime(f); cmds.getAttr(L + ".worldMatrix[0]")
P("  per-frame mute toggle x2 + 2 evals: %.1f ms/frame" % ((time.time() - t0) / 44 * 1000))
t0 = time.time()
for f in range(4270, 4314):
    cmds.currentTime(f); cmds.getAttr(L + ".worldMatrix[0]"); cmds.getAttr(R + ".worldMatrix[0]")
P("  plain currentTime + 2 getAttr: %.1f ms/frame" % ((time.time() - t0) / 44 * 1000))
maya.standalone.uninitialize()
out.close()
