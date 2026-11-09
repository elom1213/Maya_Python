# -*- coding: utf-8 -*-
# A00130_ControlRig_V02 v02.32 - Orient & Place 'Keep the left arm as it is' 시험 (mayapy)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_orient_keep_left_arm.py
#
# 기준 씬 = 사용자가 문제를 본 씬 (A00130_KEEP_SCENE, 없으면 SKIP):
#   왼팔은 사용자가 롤을 맞춰 둔 상태(upperarm +Z -> 월드 +Z), 팔꿈치가 어깨-손목 선보다 0.15 cm 뒤라
#   A2(+Z -> 폴 타깃)가 왼팔 롤을 180 도 뒤집던 씬.
import io
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


def run(doc, keep):
    cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
    pairs, _m = OM._pair_subtrees(NS + ":helper_clavicle_l", NS + ":helper_clavicle_r")
    before = dict((s, local(s)) for s, _d in pairs)
    rows, _ = OM.plan(doc, NS, keep=keep)
    _res, msgs = OM.apply(doc, NS, keep=keep)
    changed = [su.short_name(s) for s, _d in pairs
               if any(abs(a - b) > 1e-6 for a, b in zip(local(s), before[s]))]
    not_mirror = [su.short_name(d) for s, d in pairs
                  if not wm(d).isEquivalent(OM.mirror_behavior_matrix(wm(s), "YZ"), 1e-4)]
    world = dict((j, wm(j)) for j in cmds.ls(NS + ":helper_grp", dag=True, type="joint", long=True))
    return rows, msgs, changed, not_mirror, world


if not os.path.isfile(SCENE):
    OUT.write("SKIP (no scene {0})\n".format(SCENE))
    os._exit(0)

doc, _ = mapping_data.load_orient("v001")
check("json: left arm rules tagged + default on",
      OM.keep_set(doc) == frozenset(["left_arm"])
      and [g["name"] for g in doc["aim_groups"] if g.get("keep_option")] == ["clavicle_l"]
      and [c["name"] for c in doc["pole_chains"] if c.get("keep_option")] == ["arm_l"]
      and [s["name"] for s in doc["aim_subtrees"] if s.get("keep_option")] == ["fingers_l"])

rows, msgs, changed, not_mirror, w_keep = run(doc, None)
pres = [r for r in rows if r["status"] == OM.ST_PRESERVED]
check("keep on: 23 left arm joints planned as preserved", len(pres) == 23, len(pres))
check("keep on: left arm rotation values untouched", not changed, changed)
check("keep on: right arm = behavior mirror of the left (driven pole target excepted)",
      not_mirror == ["helper_polTgt_arm_r"], not_mirror)
ur = wm(NS + ":helper_upperarm_r")
check("keep on: upperarm_r forward -X, +Y -> world -Y, +Z -> world -Z (mirror of the left roll)",
      ur[4 + 1] < -0.99 and ur[8 + 2] < -0.99
      and (om.MVector(*cmds.xform(NS + ":helper_lowerarm_r", q=True, ws=True, t=True))
           - om.MVector(*cmds.xform(NS + ":helper_upperarm_r", q=True, ws=True, t=True))).normal()
      * om.MVector(ur[0], ur[1], ur[2]) < -0.99)
check("keep on: log says the left arm was kept", any("kept as it is" in m for m in msgs))

rows, msgs, changed, not_mirror, w_old = run(doc, set())
check("keep off: old behaviour - A2 re-aims the left arm (roll flips on this scene)",
      "helper_upperarm_l" in changed and not [r for r in rows if r["status"] == OM.ST_PRESERVED], changed)
diff = sorted(su.short_name(j) for j in w_keep if not w_keep[j].isEquivalent(w_old[j], 1e-4))
check("keep on/off differ only on the arms' upperarm / lowerarm / hand",
      diff == ["helper_hand_l", "helper_hand_r", "helper_lowerarm_l", "helper_lowerarm_r",
               "helper_upperarm_l", "helper_upperarm_r"], diff)

OUT.write("\n{0}/{1} passed\n".format(sum(R), len(R)))
OUT.flush()
os._exit(0 if all(R) else 1)
