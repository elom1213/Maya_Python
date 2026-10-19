# -*- coding: utf-8 -*-
# A00550_PoseMapper - blend_weights 코어 시험 (mayapy 2024)
#   mayapy test_blend_weights.py [테스트 씬 .mb]   (씬은 열기만, 저장하지 않는다)
import os
import sys

import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00550_PoseMapper.app.core import blend_weights as bwm   # noqa: E402

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


# --- 합성 씬
cmds.file(new=True, force=True)
src = cmds.createNode("transform", n="SRC")
for a in ("p0", "p1", "p2"):
    cmds.addAttr(src, ln=a, at="double", dv=0.5, k=True)
bw = cmds.createNode("blendWeighted", n="bw_test")
cmds.connectAttr(src + ".p0", bw + ".input[0]")
cmds.setAttr(bw + ".weight[0]", 0.2)
cmds.connectAttr(src + ".p1", bw + ".input[5]")          # weight 없이 연결 (Node Editor 와 같은 상태)

check("B1 missing weight detected", bwm.missing_weights(bw) == [5])
rows = bwm.rows(bw)
check("B1 rows show idx5 without weight", [(r[0], None if r[2] is None else round(r[2], 4), r[3]) for r in rows] == [(0, 0.2, True), (5, None, False)])
check("B1 check did not create the element", bwm.missing_weights(bw) == [5])
before = cmds.getAttr(bw + ".output")
check("B2 create missing -> [5]", bwm.create_missing(bw) == [5])
check("B2 output unchanged ({0:.3f})".format(before), abs(cmds.getAttr(bw + ".output") - before) < 1e-6 and not bwm.missing_weights(bw))
idx = bwm.add_input(bw, src + ".p2", 0.03)
check("B3 add -> next index 6 with weight", idx == 6 and abs(cmds.getAttr(bw + ".weight[6]") - 0.03) < 1e-6)
check("B3 add same source again -> same index", bwm.add_input(bw, src + ".p2", 0.05) == 6 and abs(cmds.getAttr(bw + ".weight[6]") - 0.05) < 1e-6)
bwm.remove(bw, [5])
check("B3 remove -> input and weight gone", 5 not in (cmds.getAttr(bw + ".input", mi=True) or []) and 5 not in (cmds.getAttr(bw + ".weight", mi=True) or []))
cmds.undo()
check("B3 undo remove -> back", 5 in cmds.getAttr(bw + ".input", mi=True))

# --- 테스트 씬 (레퍼런스 노드)
if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    try:
        cmds.file(sys.argv[1], o=True, force=True, executeScriptNodes=False, ignoreVersion=True)
    except RuntimeError:
        pass
    nodes = bwm.list_nodes()
    check("scene: 15 JALI1 bw nodes listed", len([n for n in nodes if n.startswith("JALI1:bw_")]) == 15)
    b = "JALI1:bw_mouthFunnel"
    r = bwm.rows(b)
    print("  scene rows:", [(x[0], x[1], None if x[2] is None else round(x[2], 4), x[3]) for x in r])
    print("  scene missing weights:", {n: bwm.missing_weights(n) for n in nodes if bwm.missing_weights(n)})
    check("scene: {0} first row UUU".format(b), r[0][1] == "JALI1:JALI_IN.UUU")
    i = bwm.add_input(b, "JALI1:JALI_IN.OHH", 0.03)
    check("scene: OHH -> idx {0}, weight element exists".format(i), i is not None and i in cmds.getAttr(b + ".weight", mi=True))
    cmds.setAttr("JALI1:CNT_PHONEMES.OHH", 10)
    check("scene: ARKIT_OUT.mouthFunnel moves ({0:.3f})".format(cmds.getAttr("JALI1:ARKIT_OUT.mouthFunnel")),
          cmds.getAttr("JALI1:ARKIT_OUT.mouthFunnel") > 0.25)

print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
