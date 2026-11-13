# -*- coding: utf-8 -*-
# A00590_SwingTwistNative v01.01 - Convert · Restore · Container 시험 (mayapy, 원본 플러그인 필요)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_swing_twist_convert.py
# 계획서 §9 (5-2 변환 · 5-3 undo · 5-4 restore 왕복) · §10 (container).
import os
import random
import sys
import tempfile

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import maya_swing_twist as ST   # noqa: E402

R = []
TMP = tempfile.mkdtemp(prefix="a00590c_")
TOL = 1e-9


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def joint(name):
    cmds.select(clear=True)
    return cmds.joint(name=name)


def mh_create(name, start, end, swing, swing_blend, twists, blends, from_end=False):
    """MetaHuman mh_pose_editor/model/swing_twist.py create_swing_twist_evaluator 그대로."""
    node = cmds.createNode(ST.ORIGINAL_TYPE, name=name + ST.ORIGINAL_SUFFIX)
    if from_end:
        cmds.setAttr(node + ".fromEnd", True)
    if swing:
        cmds.setAttr(node + ".swingBlend", swing_blend)
        cmds.connectAttr(node + ".swing", swing + ".rotate")
    cmds.connectAttr(start + ".rotate", node + ".startJoint")
    if end:
        cmds.connectAttr(end + ".rotate", node + ".endJoint")
    for i in range(len(twists)):
        cmds.setAttr("{0}.twists[{1}]".format(node, i), 0, 0, 0)
        cmds.setAttr("{0}.twistBlend[{1}]".format(node, i), blends[i])
        cmds.connectAttr("{0}.twists[{1}]".format(node, i), twists[i] + ".rotate")
    return node


def rig(tag, from_end):
    s, e, sw = joint(tag + "_start"), joint(tag + "_end"), joint(tag + "_swing")
    tws = [joint("{0}_tw{1}".format(tag, i)) for i in range(3)]
    node = mh_create(tag, s, e, sw, 0.2, tws, [0.25, 0.5, 0.75], from_end)
    return node, s, e, [sw] + tws


POSES = [tuple(random.Random(7).uniform(-170, 170) for _ in range(6))]
_rng = random.Random(11)
POSES += [tuple(_rng.uniform(-170, 170) for _ in range(6)) for _ in range(40)]


def sample(start, end, outs):
    """포즈를 돌며 출력값을 읽는다. undo 큐를 건드리지 않게 그동안 기록을 끈다."""
    vals = []
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        for p in POSES:
            cmds.setAttr(start + ".rotate", *p[:3])
            cmds.setAttr(end + ".rotate", *p[3:])
            vals.append([cmds.getAttr(o + ".rotate")[0] for o in outs])
        cmds.setAttr(start + ".rotate", 0, 0, 0)
        cmds.setAttr(end + ".rotate", 0, 0, 0)
    finally:
        cmds.undoInfo(stateWithoutFlush=True)
    return vals


def max_diff(a, b):
    return max(abs(x - y) for pa, pb in zip(a, b) for ra, rb in zip(pa, pb) for x, y in zip(ra, rb))


plugin_ok = ST.load_original_plugin()
check("0 original plugin loads", plugin_ok)
if not plugin_ok:
    print("SKIP - SwingTwistEvaluatorPlugin not available")
    sys.exit(1)

# ---------------------------------------------------------------- 1. read_original
cmds.file(new=True, force=True)
node, s, e, outs = rig("arm", True)
loc = cmds.spaceLocator(name="blendCtl")[0]
cmds.addAttr(loc, longName="tb1", attributeType="double", defaultValue=0.5, keyable=True)
cmds.connectAttr(loc + ".tb1", node + ".twistBlend[1].values")
cmds.setKeyframe(node, attribute="swingBlend", time=1, value=0.2)
spec = ST.read_original(node)
check("1 joints", (spec["start_joint"], spec["end_joint"], spec["swing_joint"]) == (s, e, outs[0]), spec)
check("1 twists", spec["twist_joints"] == outs[1:], spec["twist_joints"])
check("1 blends + fromEnd", spec["twist_blends"] == [0.25, 0.5, 0.75] and spec["from_end"] and abs(spec["swing_blend"] - 0.2) < 1e-12)
check("1 blend sources", spec["twist_blend_srcs"] == {1: loc + ".tb1"} and spec["swing_blend_src"]
      and spec["swing_blend_src"].endswith(".output"), (spec["twist_blend_srcs"], spec["swing_blend_src"]))
check("1 name prefix", spec["name"] == "arm")

# ---------------------------------------------------------------- 2. convert
before = sample(s, e, outs)
cmds.undoInfo(state=True, infinity=True)
cmds.flushUndo()
logs = []
holder = ST.convert(node, verify_samples=20, log=logs.append)
check("2 holder", holder == "arm_SwingTwist", holder)
check("2 original gone", not cmds.objExists(node) and ST.list_original_nodes() == [])
check("2 no orphan unitConversion", not cmds.ls(type="unitConversion"), cmds.ls(type="unitConversion"))
after = sample(s, e, outs)
check("2 outputs same at 41 poses", max_diff(before, after) <= TOL, "{0:.3g}".format(max_diff(before, after)))
check("2 log has verify result", any("max diff" in m and "21 pose" in m for m in logs), logs[-1:])
check("2 blend source moved", cmds.listConnections(holder + ".twistBlend[1]", s=True, d=False, plugs=True) == [loc + ".tb1"])
check("2 keyed swingBlend moved", cmds.nodeType(cmds.listConnections(holder + ".swingBlend", s=True, d=False)[0]).startswith("animCurve"))
check("2 source recorded", ST.read_holder(holder)["source_name"] == node)

cmds.undo()
check("3 one undo restores original", cmds.objExists(node) and ST.list_holders() == []
      and cmds.listConnections(outs[0] + ".rotate", s=True, d=False, skipConversionNodes=True) == [node])
check("3 undo restores original outputs", max_diff(before, sample(s, e, outs)) <= TOL)
cmds.redo()
check("3 redo converts again", ST.list_holders() == ["arm_SwingTwist"] and not cmds.objExists(node))
cmds.setAttr(loc + ".tb1", 0.9)
check("2 blend driver still drives", abs(cmds.getAttr("arm_SwingTwist" + ".twistBlend[1]") - 0.9) < 1e-12)
cmds.setAttr(loc + ".tb1", 0.5)

# ---------------------------------------------------------------- 4. restore 왕복
holder = "arm_SwingTwist"
restored = ST.restore(holder)
check("4 restore name", restored == node, restored)
check("4 network gone", ST.list_holders() == [] and not cmds.ls(type="quatSlerp"))
spec2 = ST.read_original(restored)
same = {k: spec2[k] == spec[k] for k in spec if k != "swing_blend_src"}
check("4 settings round-trip", all(same.values()), [k for k, v in same.items() if not v])
check("4 keyed swingBlend back on original", cmds.nodeType(spec2["swing_blend_src"].split(".")[0]).startswith("animCurve"))
check("4 outputs same after restore", max_diff(before, sample(s, e, outs)) <= TOL)

# ---------------------------------------------------------------- 5. fromEnd=0, 빈 인덱스, wrap
cmds.file(new=True, force=True)
node, s, e, outs = rig("leg", False)
# twists[1] 출력만 떼어 빈 인덱스를 만든다. 사이의 unitConversion 을 그냥 delete 하면 마야가 연결을 유지한 채
# 새 unitConversion 을 다시 만든다(실측) → 연결을 먼저 끊고 지운다.
_uc = cmds.listConnections(node + ".twists[1]", s=False, d=True)[0]
cmds.disconnectAttr(node + ".twists[1]", _uc + ".input")
cmds.delete(_uc)
spec = ST.read_original(node)
check("5 empty twist index kept", spec["twist_joints"] == ["leg_tw0", None, "leg_tw2"], spec["twist_joints"])
outs5 = [o for o in outs if o != "leg_tw1"]
before = sample(s, e, outs5)
holder = ST.convert(node, wrap=True)
ctn = ST.container_of(holder)
check("5 convert wrap -> container", ctn == holder + ST.CONTAINER_SUFFIX, ctn)
check("5 outputs same (fromEnd=0)", max_diff(before, sample(s, e, outs5)) <= TOL)
check("5 untouched joint stays free", not cmds.listConnections("leg_tw1.rotate", s=True, d=False))

# ---------------------------------------------------------------- 6. container
pub = cmds.container(ctn, query=True, publishName=True) or []
want = {"swingBlend", "twistBlend0", "twistBlend1", "twistBlend2", "startJoint", "swing", "twists0", "twists2"}
check("6 published names", want <= set(pub), sorted(pub))
check("6 endJoint not published (fromEnd off)", "endJoint" not in pub)
check("6 black box on", cmds.getAttr(ctn + ".blackBox"))
check("6 holder + all members inside", set(cmds.container(ctn, q=True, nodeList=True)) == set(ST.members(holder) + [holder]))
check("6 joints not inside", not set(cmds.container(ctn, q=True, nodeList=True)) & set(outs + [s, e]))
cmds.setAttr(ctn + ".swingBlend", 0.9)
check("6 container.swingBlend drives holder", abs(cmds.getAttr(holder + ".swingBlend") - 0.9) < 1e-12)
check("6 container blend keyable", "swingBlend" in (cmds.listAttr(ctn, keyable=True) or []))
check("6 holder still listed", ST.list_holders() == [holder])
cmds.setAttr(ctn + ".swingBlend", 0.2)

cmds.flushUndo()
check("6 unwrap", ST.unwrap_container(holder) and ST.container_of(holder) is None and not cmds.objExists(ctn))
check("6 network intact after unwrap", len(ST.members(holder)) == 4 + 2 * 2 + 4 and max_diff(before, sample(s, e, outs5)) <= TOL,
      len(ST.members(holder)))
cmds.undo()
check("6 undo unwrap", ST.container_of(holder) == ctn)
check("6 black box toggle", ST.set_black_box(holder, False) and not cmds.getAttr(ctn + ".blackBox"))

# 저장 · 다시 열기 (원본 노드 0 → 플러그인 내리기)
check("7 unload original plugin", ST.unload_original_plugin() and not ST.original_type_known())
path = os.path.join(TMP, "converted.ma").replace("\\", "/")
cmds.file(rename=path)
cmds.file(save=True, type="mayaAscii")
with open(path) as fh:
    text = fh.read()
req = [l for l in text.splitlines() if l.startswith("requires") or l.startswith("		") and '"' in l][:10]
check("7 file has no SwingTwist plugin requirement", "SwingTwistEvaluatorPlugin" not in text
      and "requires -nodeType \"SwingTwistEvaluatorNode\"" not in text, req)
cmds.file(path, open=True, force=True)
check("7 container + holder survive reopen", ST.list_holders() == [holder] and ST.container_of(holder) == ctn)
check("7 outputs same after reopen", max_diff(before, sample(s, e, outs5)) <= TOL)
n = ST.delete_rig(holder)
check("7 delete wrapped rig removes container + all", n == 12 and not cmds.objExists(ctn) and ST.list_holders() == []
      and not cmds.ls(type="quatProd"), n)

# ---------------------------------------------------------------- 8. build(wrap) + restore from container
ST.load_original_plugin()
cmds.file(new=True, force=True)
s, sw, t0 = joint("s"), joint("sw"), joint("t0")
holder = ST.build("w", s, None, sw, 0.3, [t0], [0.4], wrap=True)
check("8 build wrap", ST.container_of(holder) == holder + ST.CONTAINER_SUFFIX)
cmds.setAttr(s + ".rotate", 20, 60, -30)
v = [cmds.getAttr(j + ".rotate")[0] for j in (sw, t0)]
node = ST.restore(holder)
check("8 restore from container", cmds.nodeType(node) == ST.ORIGINAL_TYPE and not cmds.ls(type="container"), node)
v2 = [cmds.getAttr(j + ".rotate")[0] for j in (sw, t0)]
check("8 same values from restored original", max_diff([v], [v2]) <= TOL)

# ---------------------------------------------------------------- 9. 거절
cmds.file(new=True, force=True)
s, sw = joint("s"), joint("sw")
node = cmds.createNode(ST.ORIGINAL_TYPE, name="bad" + ST.ORIGINAL_SUFFIX)
cmds.connectAttr(s + ".rotate", node + ".startJoint")
cmds.connectAttr(node + ".swing", sw + ".translate")
try:
    ST.convert(node)
    msg = None
except ST.SwingTwistError as exc:
    msg = str(exc)
check("9 non-rotate output refused", msg and "not a rotate" in msg and cmds.objExists(node) and not ST.list_holders(), msg)
node2 = cmds.createNode(ST.ORIGINAL_TYPE, name="loose" + ST.ORIGINAL_SUFFIX)
try:
    ST.convert(node2)
    msg = None
except ST.SwingTwistError as exc:
    msg = str(exc)
check("9 no start joint refused", msg and "no start joint" in msg, msg)

# 레퍼런스 안의 원본은 건너뛴다
cmds.file(new=True, force=True)
rig("ref", False)
rpath = os.path.join(TMP, "orig.ma").replace("\\", "/")
cmds.file(rename=rpath)
cmds.file(save=True, type="mayaAscii")
cmds.file(new=True, force=True)
cmds.file(rpath, reference=True, namespace="R")
rnode = ST.list_original_nodes()[0]
try:
    ST.convert(rnode)
    msg = None
except ST.SwingTwistError as exc:
    msg = str(exc)
check("9 referenced node refused", msg and "reference" in msg, msg)

print("")
print("{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
