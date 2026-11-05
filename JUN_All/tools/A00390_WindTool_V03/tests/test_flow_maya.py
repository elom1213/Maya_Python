# -*- coding: utf-8 -*-
# A00390_WindTool_V03 - Flow 노드망 시험 (mayapy)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_flow_maya.py
#
# 1) 블렌더 Waves Gen 과 같은 리그(뼈 12, -Z 로 매달림)를 마야 조인트로 만들어 **블렌더 기준 데이터와 직접** 대조(12 경우)
# 2) 일반 마야 체인(X 진행 · jointOrient · rotateOrder · rest 회전 제각각, 두 체인 = 변주 · 지연)을 **순수 모델**과 대조
# 3) 위상 엔진: 키 걸린 speed / Mix / timeScale 적분 = 파이썬 Simpson, 역행 없음 · fps 30 · 제거
import os
import sys
import json
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, JUN_ALL)

import maya.standalone  # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds  # noqa: E402
from maya.api import OpenMaya as om  # noqa: E402

from tools.A00390_WindTool_V03.app.core import flow_manager as fmg  # noqa: E402
from tools.A00390_WindTool_V03.app.core import flow_model as fm  # noqa: E402
from tools.A00390_WindTool_V03.app.core import flow_presets as fp  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def world_rot_cols(node):
    """월드 회전을 열벡터 3x3 로 (열 = 로컬 축의 월드 방향)."""
    m = cmds.xform(node, q=True, ws=True, m=True)
    return [[m[0], m[4], m[8]], [m[1], m[5], m[9]], [m[2], m[6], m[10]]]


def world_pos(node):
    return cmds.xform(node, q=True, ws=True, t=True)


def ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, fm.dot(fm.norm(a), fm.norm(b))))))


def col(m, k):
    return [m[0][k], m[1][k], m[2][k]]


def make_joint(parent, world_rot_cols_, pos):
    """월드 회전(열벡터 3x3) · 위치로 조인트를 만들고 회전을 jointOrient 로 옮긴다."""
    cmds.select(clear=True)
    j = cmds.joint()
    if parent:
        j = cmds.parent(j, parent)[0]
    r = world_rot_cols_
    m = [r[0][0], r[1][0], r[2][0], 0, r[0][1], r[1][1], r[2][1], 0, r[0][2], r[1][2], r[2][2], 0,
         pos[0], pos[1], pos[2], 1]
    cmds.xform(j, ws=True, m=m)
    cmds.makeIdentity(j, apply=True, rotate=True)
    return cmds.ls(j, long=True)[0]


cmds.currentUnit(time="film")

# ================================================================ 1) 블렌더 기준 데이터 대조
G = json.load(open(os.path.join(HERE, "data", "wavesgen_golden.json")))
NB = G["bones"]
names = ["CF_%02d" % i for i in range(NB)]


def g_rot(m):
    return [row[:3] for row in m[:3]]


def g_pos(m):
    return [m[0][3], m[1][3], m[2][3]]


root_m = G["rest"]["CF_Root"]["matrix"]
grp = cmds.group(empty=True, name="wgRoot")
rr = g_rot(root_m)
cmds.xform(grp, ws=True, m=[rr[0][0], rr[1][0], rr[2][0], 0, rr[0][1], rr[1][1], rr[2][1], 0,
                            rr[0][2], rr[1][2], rr[2][2], 0] + g_pos(root_m) + [1])
joints = []
parent = grp
for nm in names:
    m = G["rest"][nm]["matrix"]
    parent = make_joint(parent, g_rot(m), g_pos(m))
    joints.append(parent)
end = make_joint(parent, g_rot(G["rest"][names[-1]]["matrix"]), G["rest"][names[-1]]["tail"])
joints.append(end)

n_chain, drv, msg = fmg.build_flow([joints[0]], mode=fmg.MODE_ROOT, preset="Breeze", chain_offset=0.0,
                                   variation=0.0, tip_follow=True, wind_axis="Auto")
print(msg)
check("golden rig: built 1 chain", n_chain == 1 and drv, msg[:160])
tip = [m for m in cmds.sets(cmds.ls("*" + fmg.FLOW_SET_SUFFIX)[0], q=True) if fmg.FLOW_TIP_SUFFIX in m][0]
check("tip at Blender CF_Tip head", math.dist(world_pos(tip), G["rest"]["CF_Tip"]["head"]) < 1e-5,
      (world_pos(tip), G["rest"]["CF_Tip"]["head"]))

chain_len = math.dist(G["rest"]["CF_00"]["head"], G["rest"]["CF_00"]["tail"]) * NB
frames_to_check = [1, 7, 13, 24, 33, 47, 60]
for case, data in G["cases"].items():
    v = data["values"]
    vals = {"lean": v["cf_wind"], "flutter": v["cf_flutter"], "cross": v["cf_cross"], "speed": v["cf_speed"],
            "wavelength": v["cf_length"], "stiffness": v["cf_stiff"], "random": v["cf_random"],
            "follow": min(v["cf_influence"], 0.99)}
    for p, x in vals.items():
        cmds.setAttr(drv + "." + fmg.a_attr(p), x)
        cmds.setAttr(drv + "." + fmg.b_attr(p), x)
    cmds.setAttr(drv + "." + fmg.FLOW_MIX, 0.0)
    cmds.setAttr(drv + "." + fmg.FLOW_DIR, math.degrees(v["cf_dir"]))
    wp, wa = 0.0, 0.0
    for f in frames_to_check:
        cmds.currentTime(f)
        gold = data["frames"][G["frames"].index(f)]
        for i, nm in enumerate(names):
            gm = gold[nm]["matrix"]
            wp = max(wp, math.dist(world_pos(joints[i]), g_pos(gm)))
            mr = world_rot_cols(joints[i])
            for k in range(3):
                wa = max(wa, ang(col(mr, k), col(g_rot(gm), k)))
    check("maya vs Blender {0}: head < 0.1% chain, axes < 0.2 deg".format(case),
          wp / chain_len < 1e-3 and wa < 0.2, "pos {0:.2e} ({1:.4%}) ang {2:.4f}".format(wp, wp / chain_len, wa))

check("flowPhase = speed * frame (constant, 24 fps)",
      abs(cmds.getAttr(drv + "." + fmg.FLOW_PHASE, time=40) - 40 * cmds.getAttr(drv + "." + fmg.a_attr("speed"))) < 1e-6)
cnt, rmsg = fmg.remove_flow()
cmds.currentTime(10)
check("remove restores rest + deletes engine", cnt == 1 and not cmds.objExists(fmg.FLOW_ENGINE)
      and all(max(abs(x) for x in cmds.getAttr(j + ".rotate")[0]) < 1e-9 for j in joints)
      and not cmds.ls("*" + fmg.FLOW_TIP_SUFFIX + "*"), rmsg)

# ================================================================ 2) 일반 마야 체인 vs 순수 모델
cmds.file(new=True, force=True)
cmds.currentUnit(time="film")
random.seed(7)
rig = cmds.group(empty=True, name="rig")
cmds.setAttr(rig + ".rotate", 10, 25, -5)
cmds.setAttr(rig + ".translate", 1, 2, 3)
roots = []
for c in range(2):
    cmds.select(clear=True)
    js = []
    for k in range(8):
        j = cmds.joint(p=(c * 2.0 + 0.3 * math.sin(k), 10 - k * 1.1, 0.4 * k * (1 if c else -1)))
        js.append(j)
    cmds.joint(js[0], e=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
    for k, j in enumerate(js):
        cmds.setAttr(j + ".rotateOrder", (k + c) % 6)
        cmds.setAttr(j + ".rotate", random.uniform(-15, 15), random.uniform(-15, 15), random.uniform(-15, 15))
    roots.append(cmds.parent(js[0], rig)[0])

params_a = dict(lean=17.0, flutter=12.5, cross=0.45, speed=3.1, wavelength=11.0, stiffness=0.7, random=0.6, follow=0.55)
params_b = dict(lean=30.0, flutter=7.0, cross=0.1, speed=1.4, wavelength=18.0, stiffness=1.6, random=0.2, follow=0.3)
n_chain, drv2, msg = fmg.build_flow(roots, mode=fmg.MODE_ROOT, opt_a=params_a, opt_b=params_b, mix=0.37,
                                    direction=63.0, envelope=0.8, chain_offset=9.0, variation=0.7,
                                    tip_follow=True, wind_axis="Z")
print(msg)
check("generic: 2 chains built", n_chain == 2, msg[:200])

eff = fp.mix(params_a, params_b, 0.37)
eff_p = dict(eff, direction=63.0, envelope=0.8)


def chain_nodes(root):
    out = [cmds.ls(root, long=True)[0]]
    while True:
        kids = cmds.listRelatives(out[-1], children=True, type="joint", fullPath=True)
        if not kids:
            return out
        out.append(kids[0])


# rest 를 순수 모델 좌표로: 모델 뼈 프레임 F = R_world · C,  C = [p1, aim, p2] (조인트 로컬)
cmds.currentTime(0)
saved = {}


def model_frames(chain, ref_w, tipw, p, phi, follow_on=True):
    bones = chain[:-1]
    frames, heads = [], []
    for i, nd in enumerate(bones):
        R = rest_world[nd]
        aim_w = [rest_pos[chain[i + 1]][k] - rest_pos[nd][k] for k in range(3)]
        Rt = fm.transpose(R)
        aim = fm.norm(fm.mat_vec(Rt, aim_w))
        p2 = fm.mat_vec(Rt, ref_w)
        d = fm.dot(p2, aim)
        p2 = fm.norm([p2[k] - aim[k] * d for k in range(3)])
        p1 = fm.norm(fm.cross(aim, p2))
        C = [[p1[r], aim[r], p2[r]] for r in range(3)]
        frames.append((fm.mat_mul(R, C), C))
        heads.append(rest_pos[nd])
    base_R = frames[0][0]
    rest = []
    prev_R, prev_p = parent_rest_rot[chain[0]], parent_rest_pos[chain[0]]
    for (F, C), h in zip(frames, heads):
        Pt = fm.transpose(prev_R)
        rest.append((fm.mat_mul(Pt, F), fm.mat_vec(Pt, [h[k] - prev_p[k] for k in range(3)])))
        prev_R, prev_p = F, h
    out = fm.evaluate_chain(parent_rest_rot[chain[0]], parent_rest_pos[chain[0]], rest, p, phi, tipw, follow_on)
    return [(fm.mat_mul(rot, fm.transpose(C)), head) for (rot, head), (F, C) in zip(out, frames)]


# rest 값은 셋업이 걸린 뒤라 envelope 0 으로 재서 얻는다
cmds.setAttr(drv2 + "." + "windEnvelope", 0.0)
for fl in ("follow",):
    pass
cmds.setAttr(drv2 + "." + fmg.a_attr("follow"), 0.0)
cmds.setAttr(drv2 + "." + fmg.b_attr("follow"), 0.0)
chains = [chain_nodes(r) for r in roots]
rest_world, rest_pos, parent_rest_rot, parent_rest_pos = {}, {}, {}, {}
for ch in chains:
    for nd in ch:
        rest_world[nd] = world_rot_cols(nd)
        rest_pos[nd] = world_pos(nd)
    par = cmds.listRelatives(ch[0], parent=True, fullPath=True)[0]
    parent_rest_rot[ch[0]] = world_rot_cols(par)
    parent_rest_pos[ch[0]] = world_pos(par)
envelope_zero_ok = all(math.dist(world_pos(nd), rest_pos[nd]) < 1e-9 for ch in chains for nd in ch)
cmds.setAttr(drv2 + ".windEnvelope", 0.8)
cmds.setAttr(drv2 + "." + fmg.a_attr("follow"), params_a["follow"])
cmds.setAttr(drv2 + "." + fmg.b_attr("follow"), params_b["follow"])
check("envelope 0 + follow 0 = rest pose", envelope_zero_ok)

tips = sorted([m for m in cmds.ls("*" + fmg.FLOW_TIP_SUFFIX + "*", type="transform", long=True)])
worst = 0.0
for f in (1, 5, 18, 37, 52):
    cmds.currentTime(f)
    for ci, ch in enumerate(chains):
        vs, vl, vf = fm.vary_factors(ci, 0.7)
        p = dict(eff_p, wavelength=eff["wavelength"] * vl, flutter=eff["flutter"] * vf)
        rate = eff["speed"]
        phi = (f * eff["speed"] + ci * 9.0 * rate) * vs
        tipw = world_pos([t for t in tips if fm is not None][ci])
        model = model_frames(ch, [0, 0, 1], tipw, p, phi)
        for i, nd in enumerate(ch[:-1]):
            mr = world_rot_cols(nd)
            orot, ohead = model[i]
            worst = max(worst, math.dist(world_pos(nd), ohead))
            for k in range(3):
                worst = max(worst, math.radians(ang(col(mr, k), col(orot, k))))
check("generic chain (2 chains, rotateOrder / JO / rest rot, mix 0.37, variation, offset) = pure model",
      worst < 1e-6, "worst {0:.2e}".format(worst))

# 라이브: 값을 바꾸면 바로
cmds.currentTime(18)
before = cmds.getAttr(chains[0][3] + ".rotate")[0]
cmds.setAttr(drv2 + "." + fmg.FLOW_MIX, 0.9)
after = cmds.getAttr(chains[0][3] + ".rotate")[0]
check("live: changing flowMix changes rotation at once", max(abs(a - b) for a, b in zip(before, after)) > 1e-3)
fmg.apply_preset([drv2], "Fast Flutter")
_pv = (cmds.getAttr(drv2 + "." + fmg.a_attr("speed")), cmds.getAttr(drv2 + "." + fmg.b_attr("cross")),
       cmds.getAttr(drv2 + "." + fmg.eff_attr("speed")), cmds.getAttr(drv2 + "." + fmg.FLOW_PRESET))
check("apply_preset writes option 1 / 2 into A / B (+ name)",
      abs(_pv[0] - 4.91) < 1e-9 and abs(_pv[1] - 0.0) < 1e-9
      and abs(_pv[2] - (4.91 + (4.41 - 4.91) * 0.9)) < 1e-6 and _pv[3] == "Fast Flutter", _pv)

# ================================================================ 3) 위상 엔진 (키)


def lin(keys, x):
    ts = sorted(keys)
    if x <= ts[0]:
        return keys[ts[0]]
    if x >= ts[-1]:
        return keys[ts[-1]]
    for a, b in zip(ts, ts[1:]):
        if x <= b:
            return keys[a] + (keys[b] - keys[a]) * (x - a) / (b - a)


def integ(f, lo, hi, steps=20000):
    h = (hi - lo) / steps
    return sum(f(lo + (k + 0.5) * h) for k in range(steps)) * h


SA = {1: 2.0, 30: 6.0, 60: 1.0}
MX = {10: 0.0, 50: 1.0}
W = {20: 1.0, 40: 0.25}
cmds.cutKey(drv2, clear=True, attribute=[fmg.a_attr("speed"), fmg.FLOW_MIX, fmg.FLOW_TIME_SCALE])
for t, v in SA.items():
    cmds.setKeyframe(drv2, attribute=fmg.a_attr("speed"), time=t, value=v, inTangentType="linear", outTangentType="linear")
for t, v in MX.items():
    cmds.setKeyframe(drv2, attribute=fmg.FLOW_MIX, time=t, value=v, inTangentType="linear", outTangentType="linear")
for t, v in W.items():
    cmds.setKeyframe(drv2, attribute=fmg.FLOW_TIME_SCALE, time=t, value=v, inTangentType="linear", outTangentType="linear")
SB = cmds.getAttr(drv2 + "." + fmg.b_attr("speed"))


def f_of(t):
    return lin(W, t) * (lin(SA, t) + (SB - lin(SA, t)) * lin(MX, t))


errs, prev, reverse = [], None, 0
for fr in list(range(0, 81, 3)) + [17.5, 33.25]:
    cmds.currentTime(fr)
    ph = cmds.getAttr(drv2 + "." + fmg.FLOW_PHASE)
    errs.append(abs(ph - integ(f_of, 0, fr)))
for fr in range(0, 81):
    cmds.currentTime(fr)
    ph = cmds.getAttr(drv2 + "." + fmg.FLOW_PHASE)
    if prev is not None and ph < prev - 1e-9:
        reverse += 1
    prev = ph
check("keyed speed A + Mix + timeScale: phase = exact integral", max(errs) < 1e-6, "max err {0:.2e}".format(max(errs)))
check("keyed: phase never goes backward", reverse == 0, reverse)
cmds.currentTime(25)
check("flowRate = f(frame)", abs(cmds.getAttr(drv2 + "." + fmg.FLOW_RATE) - f_of(25)) < 1e-9)
# 키 값을 고치면 Rebuild 없이 바로
cmds.keyframe(drv2, attribute=fmg.a_attr("speed"), time=(30, 30), valueChange=9.0)
SA[30] = 9.0
cmds.currentTime(45)
check("editing a key updates the phase live (no rebuild)",
      abs(cmds.getAttr(drv2 + "." + fmg.FLOW_PHASE) - integ(f_of, 0, 45)) < 1e-6)

# fps 30: 같은 초당 리듬 (flowFpsScale = 0.8)
cmds.file(new=True, force=True)
cmds.currentUnit(time="ntsc")
cmds.select(clear=True)
js = [cmds.joint(p=(0, 5 - k, 0)) for k in range(5)]
n_chain, drv3, msg = fmg.build_flow([js[0]], preset="Slow Flow", tip_follow=False)
cmds.currentTime(30)
check("30 fps: flowFpsScale 0.8, phase = 0.8 * speed * frame",
      abs(cmds.getAttr(drv3 + "." + fmg.FLOW_FPS_SCALE) - 0.8) < 1e-12
      and abs(cmds.getAttr(drv3 + "." + fmg.FLOW_PHASE) - 0.8 * 2.01 * 30) < 1e-6)
check("no tip follow: no tip locator", not cmds.ls("*" + fmg.FLOW_TIP_SUFFIX + "*"))
busy_root = js[0]
fmg.remove_flow()
cmds.setKeyframe(js[1], attribute="rotateZ", value=5)
n_chain, drv4, msg = fmg.build_flow([js[0]], preset="Breeze")
check("refuses a chain whose rotate is keyed", n_chain == 0 and "keyed" in msg, msg)

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
