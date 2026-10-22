# -*- coding: utf-8 -*-
# A00540_JaliLipSync - 실제 파일 시험 (T-E, mayapy 2024). 파일은 열기만 하고 저장하지 않는다.
#   mayapy test_end_to_end.py [A0020.ma] [angela_JALI.ma] [visemenet.txt]
import os
import sys

import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00540_JaliLipSync.app.core import mapping as mapping_mod, keyer, scene, lipsync_data   # noqa: E402

A0020 = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\USER\Desktop\JP\0035_maya_src_rig\02_Cage_JALI\A0020_jali_slider_ctl.ma"
ANGELA = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\USER\Desktop\JP\0001_PJ_portfolio\0040_JULI\scenes\angela_JALI.ma"
TXT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.dirname(JUN_ALL)), "JUN_JALI", "out", "visemenet_intro.txt")
TXT = os.path.normpath(TXT)

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def key_count(attr):
    return cmds.keyframe(attr, q=True, keyframeCount=True) or 0


def skip_all(reason):
    print("SKIP", reason)
    print("RESULT OK (skipped)")
    maya.standalone.uninitialize()
    sys.exit(0)


for path in (A0020, ANGELA, TXT):
    if not os.path.isfile(path):
        skip_all("missing file " + path)

data = lipsync_data.load(TXT)
new = mapping_mod.load_mapping("jali_slider_dummy_in")
angela = mapping_mod.load_mapping("angela_jali_visemenet")
idx = data.column_index()

# ---------------------------------------------------------------- E1 A0020 + Auto
cmds.file(A0020, open=True, force=True)
fps = keyer.scene_fps()
check("E1 find_rigs(DUMMY_IN_PHONEMES) == ['']", scene.find_rigs(scene.marker_of(new)) == [""])
check("E1 angela marker absent", scene.find_rigs(scene.marker_of(angela)) == [])
res = keyer.apply(data, new, "", start=1)
check("E1 auto apply 23 attrs, nothing skipped", res["attrs"] == 23 and res["skipped"] == [])
vals = cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, valueChange=True)
check("E1 AAA keyed, all values in 0-1", vals and min(vals) >= 0.0 and max(vals) <= 1.0 and max(vals) > 0.05)
times = cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, tc=True)
f_max = times[vals.index(max(vals))]
cmds.currentTime(f_max)
out_aaa = cmds.getAttr("DUMMY_OUT_PHONEMES.AAA")
check("E1 DUMMY_OUT_PHONEMES.AAA = key x 12 at its peak ({0:.3f})".format(out_aaa), abs(out_aaa - max(vals) * 12.0) < 1e-4)
jaw_key = cmds.keyframe("DUMMY_IN_JALI.Jaw", q=True, eval=True, t=(f_max, f_max))[0]
out_jaw = cmds.getAttr("DUMMY_OUT_JALI.Jaw")
check("E1 DUMMY_OUT_JALI.Jaw = key x 15 (controller rests at 0, nothing added) ({0:.3f})".format(out_jaw),
      abs(out_jaw - jaw_key * 15.0) < 1e-4 and cmds.getAttr("CNT_JaLi.tx") == 0)
row = data.rows[min(int(round((f_max - 1) / fps * data.fps)), len(data.rows) - 1)]   # 키는 start=1 부터
check("E1 key value equals the txt row (Aa, scale 1)", abs(max(vals) - min(max(row[idx["Aa"]], 0.0), 1.0)) < 1e-6)
check("E1 COARTIC keyed, YA_PEDAL not", key_count("DUMMY_IN_COARTIC.WA_PEDAL") > 0 and key_count("DUMMY_IN_COARTIC.YA_PEDAL") == 0)
warn = keyer.scale_warnings(keyer.resolve_targets(new, "")[0], new)
check("E1 no scale warnings with the mapping defaults", warn == [])

# ---------------------------------------------------------------- E2 A0020 + Manual phonemes 만
keyer.remove(new, "")
check("E2 removed", key_count("DUMMY_IN_PHONEMES.AAA") == 0 and key_count("DUMMY_IN_JALI.Jaw") == 0)
# 키를 지워도 어트리뷰트는 마지막 키 값에 머문다(마야 동작) - 새 씬처럼 기본값으로 되돌려 둔다
for a in ("Jaw", "Lip"):
    cmds.setAttr("DUMMY_IN_JALI." + a, 0.6)
res = keyer.apply(data, new, start=1, node_map={"phonemes": "DUMMY_IN_PHONEMES", "coartic": None, "jali": None})
check("E2 manual phonemes only -> skipped coartic, jali", res["skipped"] == ["coartic", "jali"] and res["attrs"] == 16)
check("E2 no keys on COARTIC / JALI", key_count("DUMMY_IN_COARTIC.WA_PEDAL") == 0 and key_count("DUMMY_IN_JALI.Jaw") == 0
      and key_count("DUMMY_IN_PHONEMES.AAA") > 0)
cmds.currentTime(f_max)
check("E2 JaLi output stays at default 9 (dummy default 0.6)", abs(cmds.getAttr("DUMMY_OUT_JALI.Jaw") - 9.0) < 1e-6)

# ---------------------------------------------------------------- E3 angela + angela 규칙 (v01.00 과 같은 값)
cmds.file(ANGELA, open=True, force=True, ignoreVersion=True)
fps = keyer.scene_fps()
check("E3 find_rigs(CNT_PHONEMES) == ['']", scene.find_rigs(scene.marker_of(angela)) == [""])
res = keyer.apply(data, angela, "", start=1)
check("E3 apply 23 attrs", res["attrs"] == 23 and res["skipped"] == [])
ok = True
for f in (1, 25, 60, res["end"]):
    r = data.rows[min(int(round((f - 1) / fps * data.fps)), len(data.rows) - 1)]
    exp_aaa = min(max(r[idx["Aa"]], 0.0), 1.0) * 10.0
    exp_ohh = max(min(max(r[idx["Oh"]], 0.0), 1.0), min(max(r[idx["Uh"]], 0.0), 1.0)) * 10.0
    exp_jaw = min(max(r[idx["Jaw"]], 0.0), 1.0) * 10.0
    got = [cmds.keyframe(a, q=True, eval=True, t=(f, f))[0] for a in ("CNT_PHONEMES.AAA", "CNT_PHONEMES.OHH", "CNT_JaLi.translateX")]
    if not (abs(got[0] - exp_aaa) < 1e-6 and abs(got[1] - exp_ohh) < 1e-6 and abs(got[2] - exp_jaw) < 1e-6):
        ok = False
        print("   frame", f, "got", got, "expected", exp_aaa, exp_ohh, exp_jaw)
check("E3 key values = v01.00 formula (x10, OHH = max(Oh, Uh), Jaw x10)", ok)
check("E3 COARTIC.LNTD keyed", key_count("CNT_COARTIC.LNTD") > 0)
res = keyer.apply(data, angela, "", start=1, jali_fixed=(9.0, 9.0))
check("E3 fixed 9/9 keyed at both ends", cmds.keyframe("CNT_JaLi.translateX", q=True, valueChange=True) == [9.0, 9.0])

print("RESULT", "OK" if all(R) else "%d FAILED" % R.count(False))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
