# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.58 - Bake > Locator 의 Constrain Objects : 애니메이션 레이어 오브젝트 · 구간 블렌드 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_locator_bake_layers.py
#
# 판정 : BaseAnimation + 다른 레이어에 키가 있는 컨트롤러에도 컨스트레인트가 걸린다(예전엔 0 개).
#        Blend only in Frame Range = 구간 안은 로케이터 월드, 밖은 원래 월드(베이크 전과 같다).
#        끄면 전 프레임 로케이터. 레이어 없는 오브젝트 + 구간 끔 = 예전 pairBlend 경로 그대로. undo 한 번.
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00110_animTool_V02.app.core.locator_bake_manager import LocatorBakeManager as LBM   # noqa: E402

R = []
FRAMES = list(range(1, 41))
START, END = 10, 25
TOL = 1e-3


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build():
    """grp(키) > ctl(BaseAnimation 키 + Layer1(additive) 키 + Layer2(override, weight 0.5) 키, scale 키) / plain(레이어 없음)."""
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=1, max=40, ast=1, aet=40)
    grp = cmds.group(empty=True, name="grp")
    for t, v in ((1, 0), (40, 30)):
        cmds.setKeyframe(grp, at="tx", t=t, v=v)
        cmds.setKeyframe(grp, at="ry", t=t, v=v * 2)
    ctl = cmds.circle(name="arm_ctl")[0]
    cmds.parent(ctl, grp)
    cmds.setAttr(ctl + ".rotateOrder", 2)
    for t, (x, y, z) in ((1, (0, 0, 0)), (20, (60, 40, -30)), (40, (120, 90, 80))):
        for a, v in (("rx", x), ("ry", y), ("rz", z), ("ty", t * 0.2), ("sx", 1 + t * 0.01)):
            cmds.setKeyframe(ctl, at=a, t=t, v=v)
    cmds.select(ctl)
    l1 = cmds.animLayer("Layer1", addSelectedObjects=True)
    l2 = cmds.animLayer("Layer2", addSelectedObjects=True, override=True)
    cmds.setAttr(l2 + ".weight", 0.5)
    for t, v in ((1, 0), (15, 4), (40, -2)):
        cmds.setKeyframe(ctl, at="tz", t=t, v=v, animLayer=l1)
        cmds.setKeyframe(ctl, at="rx", t=t, v=v * 10, animLayer=l1)
    for t, v in ((1, 1), (30, 6)):
        cmds.setKeyframe(ctl, at="tx", t=t, v=v, animLayer=l2)
    plain = cmds.circle(name="plain_ctl")[0]
    for t, v in ((1, 0), (40, 12)):
        cmds.setKeyframe(plain, at="tx", t=t, v=v)
        cmds.setKeyframe(plain, at="rz", t=t, v=v * 5)
    cmds.select(clear=True)
    return "|grp|arm_ctl", "|plain_ctl"


def world(node, f):
    cmds.currentTime(f)
    return (cmds.xform(node, q=True, ws=True, t=True) + cmds.xform(node, q=True, ws=True, ro=True))


def same(a, b):
    import math
    for x, y in zip(a, b):
        d = abs(x - y) % 360.0
        if min(d, 360.0 - d) > TOL and abs(x - y) > TOL:
            return False
    return True


def snapshot(node):
    return dict((f, world(node, f)) for f in FRAMES)


def shift_locator(loc, dy=50.0):
    """로케이터 커브를 옮겨 '로케이터를 따른다' 와 '원래 움직임' 을 구분한다."""
    cmds.keyframe(loc + ".ty", edit=True, relative=True, valueChange=dy)


# ---------------------------------------------------------------- 1. 옛 버그 재현 조건
ctl, plain = build()
check("scene: ctl is in anim layers", LBM.in_anim_layers(ctl) and not LBM.in_anim_layers(plain))
check("old check blocked every axis (the bug)", LBM._blocked_axes(ctl, "translate") == ["x", "y", "z"]
      and LBM._blocked_axes(ctl, "rotate") == ["x", "y", "z"])
check("layer check frees them", LBM._blocked_axes(ctl, "translate", True) == []
      and LBM._blocked_axes(ctl, "rotate", True) == [])

# ---------------------------------------------------------------- 2. 구간 블렌드 (기본)
orig = snapshot(ctl)
locs, msg = LBM.bake([ctl], 1, 40, constrain=["parent"], constrain_range=False)
cmds.undo()
locs, msg = LBM.bake([ctl], 1, 40, constrain=["parent"], constrain_range=True)
print(msg)
loc = locs[0]
cons = cmds.ls(type="parentConstraint")
check("layered ctl gets a parentConstraint", len(cons) == 1, msg)
layer = [l for l in cmds.ls(type="animLayer") if l.startswith(LBM.CONSTRAINT_LAYER)]
check("override layer LOC_Constraint created", len(layer) == 1 and cmds.animLayer(layer[0], q=True, override=True), layer)
check("message names the layer and the range", "LOC_Constraint" in msg and "1 - 40" in msg, msg)
# ★ undo 는 시간 이동보다 먼저 - mayapy 에선 currentTime 도 undo 대기열에 쌓여 undo 한 번이 그것만 되돌린다
cmds.undo()
check("undo removes locator, constraint, layer",
      not cmds.ls("arm_ctl_LOC*") and not cmds.ls(type="parentConstraint")
      and not [l for l in cmds.ls(type="animLayer") if l.startswith(LBM.CONSTRAINT_LAYER)])
cmds.redo()
check("no change right after constraining (locator = object)",
      all(same(world(ctl, f), orig[f]) for f in FRAMES))
ctl, plain = build()
orig = snapshot(ctl)
locs, msg = LBM.bake([ctl], 1, 40, constrain=["parent"], constrain_range=True)
cmds.undo()
check("undo removes locator, constraint, layer",
      not cmds.ls("arm_ctl_LOC*") and not cmds.ls(type="parentConstraint")
      and not [l for l in cmds.ls(type="animLayer") if l.startswith(LBM.CONSTRAINT_LAYER)])
check("undo keeps the original motion", all(same(world(ctl, f), orig[f]) for f in FRAMES))

locs, msg = LBM.bake([ctl], START, END, constrain=["parent"], constrain_range=True)
loc = locs[0]
shift_locator(loc)
bad_in = [f for f in range(START, END + 1) if not same(world(ctl, f), world(loc, f))]
bad_out = [f for f in FRAMES if (f < START or f > END) and not same(world(ctl, f), orig[f])]
check("range: inside Start-End the object matches the moved locator", not bad_in, bad_in[:5])
check("range: outside the object keeps its own motion", not bad_out, bad_out[:5])
lay = [l for l in cmds.ls(type="animLayer") if l.startswith(LBM.CONSTRAINT_LAYER)][0]
w = [(f, round(cmds.getAttr(lay + ".weight", time=f), 3)) for f in (START - 1, START, END, END + 1)]
check("range: layer weight 0 / 1 / 1 / 0 (stepped)", [v for _f, v in w] == [0, 1, 1, 0], w)
mid = (START + END) / 2.0 + 0.5
check("range: stepped - no ramp between keys (holds the previous key)",
      round(cmds.getAttr(lay + ".weight", time=START - 0.5), 3) == 0
      and round(cmds.getAttr(lay + ".weight", time=END + 0.5), 3) == 1
      and round(cmds.getAttr(lay + ".weight", time=mid), 3) == 1)

# ---------------------------------------------------------------- 3. 구간 끔 = 전 프레임
ctl, plain = build()
orig = snapshot(ctl)
locs, msg = LBM.bake([ctl], START, END, constrain=["parent"], constrain_range=False)
loc = locs[0]
check("range off: layered ctl still constrained (layer path)", len(cmds.ls(type="parentConstraint")) == 1, msg)
lay = [l for l in cmds.ls(type="animLayer") if l.startswith(LBM.CONSTRAINT_LAYER)]
check("range off: layer weight 1, no keys", lay and cmds.getAttr(lay[0] + ".weight") == 1
      and not cmds.listConnections(lay[0] + ".weight", s=True, d=False))
shift_locator(loc)
check("range off: every frame follows the locator",
      all(same(world(ctl, f), world(loc, f)) for f in FRAMES))

# ---------------------------------------------------------------- 4. 레이어 없는 오브젝트
ctl, plain = build()
orig_p = snapshot(plain)
locs, msg = LBM.bake([plain], START, END, constrain=["parent"], constrain_range=False)
check("plain + range off: old pairBlend path (no new layer)",
      len(cmds.ls(type="parentConstraint")) == 1
      and not [l for l in cmds.ls(type="animLayer") if l.startswith(LBM.CONSTRAINT_LAYER)]
      and cmds.ls(type="pairBlend"), msg)
cmds.undo()
locs, msg = LBM.bake([plain], START, END, constrain=["parent"], constrain_range=True)
loc = locs[0]
shift_locator(loc)
check("plain + range on: inside follows the locator",
      all(same(world(plain, f), world(loc, f)) for f in range(START, END + 1)))
check("plain + range on: outside keeps its own motion",
      all(same(world(plain, f), orig_p[f]) for f in FRAMES if f < START or f > END))

# ---------------------------------------------------------------- 5. 두 오브젝트 함께 · 레이어 하나 · 다른 종류
ctl, plain = build()
orig = snapshot(ctl)
locs, msg = LBM.bake([ctl, plain], START, END, scale=True, constrain=["point", "orient", "scale"],
                     constrain_range=True)
check("two objects share one LOC_Constraint layer",
      len([l for l in cmds.ls(type="animLayer") if l.startswith(LBM.CONSTRAINT_LAYER)]) == 1, msg)
check("point + orient + scale on the layered ctl (keyed scale too)",
      all(cmds.listRelatives(ctl, children=True, type=t)
          for t in ("pointConstraint", "orientConstraint", "scaleConstraint")), msg)
check("no warnings for the layered ctl", "arm_ctl:" not in msg, msg)
shift_locator(locs[0])
check("point / orient: inside follows, outside original",
      all(same(world(ctl, f), world(locs[0], f)) for f in range(START, END + 1))
      and all(same(world(ctl, f), orig[f]) for f in FRAMES if f < START or f > END))

# ---------------------------------------------------------------- 6. 잠긴 축은 레이어 경로에서도 skip
ctl, plain = build()
cmds.setAttr(ctl + ".tz", lock=True)
check("layer path: locked axis blocked", LBM._blocked_axes(ctl, "translate", True) == ["z"])
locs, msg = LBM.bake([ctl], START, END, constrain=["parent"], constrain_range=True)
check("layer path: constrained with the locked axis skipped",
      len(cmds.ls(type="parentConstraint")) == 1 and "T[z]" in msg, msg)

print("RESULT {0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
