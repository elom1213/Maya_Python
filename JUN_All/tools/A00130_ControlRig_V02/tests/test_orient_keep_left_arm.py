# -*- coding: utf-8 -*-
# A00130_ControlRig_V02 v02.32 / v02.33 - Orient & Place 시험 (mayapy)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_orient_keep_left_arm.py
#
# - v02.33 팔 A2 = -Z 가 폴 타깃을 향한다 (팔 폴 타깃은 늘 팔 뒤 = 월드 -Z, 사용자 전제). 다리는 +Z 그대로(무릎 폴은 앞).
# - v02.32 'Keep the left arm as it is' (v02.33 부터 기본 끔) - 켜면 왼팔 규칙을 건너뛴다.
#
# 기준 씬 = 사용자가 문제를 본 씬 (A00130_KEEP_SCENE, 없으면 SKIP):
#   왼팔은 사용자가 손으로 맞춘 상태(upperarm +Z -> 월드 +Z, -Z 가 뒤쪽 폴 타깃을 본다).
#   예전 규칙(+Z -> 폴)은 이 팔을 180 도 굴렸다(로그 'deviates 179.96 deg').
import io
import math
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds  # noqa: E402
import maya.api.OpenMaya as om  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, JUN_ALL)
from tools.A00130_ControlRig_V02.app.core import mapping_data  # noqa: E402
from tools.A00130_ControlRig_V02.app.core import orient_manager as OM  # noqa: E402
from tools.A00130_ControlRig_V02.app.core import scene_utils as su  # noqa: E402

SCENE = os.environ.get("A00130_KEEP_SCENE",
                       "C:/JUN/JUN_MUE/00_03_01_RIG_01_PJ/scenes/0402_IVI/.tmp/1010_IVI_ctl_AGF_0030_tmp.mb")
NS = "Cage"
OUT = io.open(sys.stdout.fileno(), "w", encoding="utf-8", closefd=False)
R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    OUT.write(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else "") + "\n")
    OUT.flush()


def wm(j):
    return om.MMatrix(cmds.xform(j, q=True, ws=True, m=True))


def local(j):
    return list(cmds.getAttr(j + ".r")[0]) + list(cmds.getAttr(j + ".jo")[0])


def axes_dev(m, m0):
    """두 월드 행렬의 축(X/Y/Z) 사이 최대 각도(도)."""
    worst = 0.0
    for i in range(3):
        a = om.MVector(m[4 * i], m[4 * i + 1], m[4 * i + 2]).normal()
        b = om.MVector(m0[4 * i], m0[4 * i + 1], m0[4 * i + 2]).normal()
        worst = max(worst, math.degrees(math.acos(max(-1.0, min(1.0, a * b)))))
    return worst


def logged_dev(msgs, chain):
    line = [m for m in msgs if m.startswith("[OK] {0} : aimed at the pole".format(chain))]
    if not line:
        return None, None
    return line[0], float(line[0].split("deviates ")[1].split(" deg")[0])


def run(doc, keep):
    cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
    pairs, _m = OM._pair_subtrees(NS + ":helper_clavicle_l", NS + ":helper_clavicle_r")
    before_local = dict((s, local(s)) for s, _d in pairs)
    before_world = dict((j, wm(j)) for j in cmds.ls(NS + ":helper_grp", dag=True, type="joint", long=True))
    rows, _ = OM.plan(doc, NS, keep=keep)
    _res, msgs = OM.apply(doc, NS, keep=keep)
    changed = [su.short_name(s) for s, _d in pairs
               if any(abs(a - b) > 1e-6 for a, b in zip(local(s), before_local[s]))]
    not_mirror = [su.short_name(d) for s, d in pairs
                  if not wm(d).isEquivalent(OM.mirror_behavior_matrix(wm(s), "YZ"), 1e-4)]
    after_world = dict((j, wm(j)) for j in before_world)
    return rows, msgs, changed, not_mirror, before_world, after_world


if not os.path.isfile(SCENE):
    OUT.write("SKIP (no scene {0})\n".format(SCENE))
    os._exit(0)

doc, _ = mapping_data.load_orient("v001")
arm = [c for c in doc["pole_chains"] if c["name"] == "arm_l"][0]
legs = [c for c in doc["pole_chains"] if c["name"].startswith("leg")]
check("json: arm_l aims -Z at the pole (arm pole behind), legs keep +Z (knee pole in front)",
      arm["up"] == "-Z" and arm["expect_up_world"] == "-Z"
      and len(legs) == 2 and all(c["up"] == "+Z" and c["expect_up_world"] == "+Z" for c in legs))
check("json: left arm rules tagged, keep default OFF (v02.33)",
      OM.keep_set(doc) == frozenset()
      and [g["name"] for g in doc["aim_groups"] if g.get("keep_option")] == ["clavicle_l"]
      and [c["name"] for c in doc["pole_chains"] if c.get("keep_option")] == ["arm_l"]
      and [s["name"] for s in doc["aim_subtrees"] if s.get("keep_option")] == ["fingers_l"])

# ---- 기본(Keep 끔): A2 arm_l(-Z -> 폴)이 손으로 맞춘 왼팔을 그대로 재현한다
rows, msgs, changed, not_mirror, w0, w_off = run(doc, None)
arm_joints = [j for j in w0 if any(j.endswith(":helper_" + n + "_l") for n in ("upperarm", "lowerarm", "hand"))]
devs = dict((su.short_name(j), round(axes_dev(w_off[j], w0[j]), 4)) for j in arm_joints)
check("keep off (default): A2 with -Z at the pole reproduces the hand-set left arm (< 0.05 deg)",
      len(devs) == 3 and all(v < 0.05 for v in devs.values()), devs)
line, dev = logged_dev(msgs, "arm_l")
check("keep off: arm_l -Z within 1 deg of world -Z (the old +Z rule logged 179.96)",
      dev is not None and dev < 1.0, line)
check("keep off: right arm = behavior mirror of the left (driven pole target excepted)",
      not_mirror == ["helper_polTgt_arm_r"], not_mirror)
ur = wm(NS + ":helper_upperarm_r")
down = (om.MVector(*cmds.xform(NS + ":helper_lowerarm_r", q=True, ws=True, t=True))
        - om.MVector(*cmds.xform(NS + ":helper_upperarm_r", q=True, ws=True, t=True))).normal()
check("keep off: upperarm_r forward -X, +Y -> world -Y, +Z -> world -Z (mirror of the left roll)",
      ur[4 + 1] < -0.99 and ur[8 + 2] < -0.99 and down * om.MVector(ur[0], ur[1], ur[2]) < -0.99)
for leg in ("leg_l", "leg_r"):
    line, dev = logged_dev(msgs, leg)
    check("legs unchanged: {0} +Z at the pole, within 1 deg of world +Z".format(leg),
          dev is not None and "+Z deviates" in line and dev < 1.0, line)

# ---- Keep 켬: 왼팔 로컬 값 그대로, 이 씬에서는 끔과 사실상 같은 결과
rows, msgs, changed, not_mirror, _w0, w_keep = run(doc, {"left_arm"})
pres = [r for r in rows if r["status"] == OM.ST_PRESERVED]
check("keep on: 23 left arm joints planned as preserved", len(pres) == 23, len(pres))
check("keep on: left arm rotation values untouched", not changed, changed)
check("keep on: right arm = behavior mirror of the left", not_mirror == ["helper_polTgt_arm_r"], not_mirror)
check("keep on: log says the left arm was kept", any("kept as it is" in m for m in msgs))
worst = max(axes_dev(w_keep[j], w_off[j]) for j in w_keep)
check("keep on / off agree on this scene (< 0.05 deg on every joint)", worst < 0.05, round(worst, 4))

OUT.write("\n{0}/{1} passed\n".format(sum(R), len(R)))
OUT.flush()
os._exit(0 if all(R) else 1)
