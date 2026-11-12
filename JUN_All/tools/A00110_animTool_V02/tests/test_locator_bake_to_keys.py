# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.59 - Bake > Locator 의 Bake to Keys 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_locator_bake_to_keys.py
#
# 판정 : LOC + Anim + Constrain(LOC_Constraint 레이어, 구간 블렌드) 뒤 로케이터를 옮긴 움직임이,
#        Bake to Keys 뒤에는 컨스트레인트 · LOC_Constraint · 로케이터 없이 오브젝트 키만으로 똑같다(전 프레임 월드).
#        다른 레이어(additive · override)는 남는다. Bake 탭(BakeManager.bake)으로는 레이어를 지우면 사라진다(이유 재현).
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00110_animTool_V02.app.core.locator_bake_manager import LocatorBakeManager as LBM   # noqa: E402
from tools.A00110_animTool_V02.app.core.bake_manager import BakeManager   # noqa: E402

R = []
FRAMES = list(range(1, 41))
START, END = 10, 25
TOL = 1e-3


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build(big_rotation=False):
    """grp(키) > arm_ctl(Base 키 + Layer1 additive + Layer2 override 0.5) / plain_ctl(레이어 없음)."""
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=1, max=40, ast=1, aet=40)
    grp = cmds.group(empty=True, name="grp")
    for t, v in ((1, 0), (40, 30)):
        cmds.setKeyframe(grp, at="tx", t=t, v=v)
        cmds.setKeyframe(grp, at="ry", t=t, v=v * 2)
    ctl = cmds.circle(name="arm_ctl")[0]
    cmds.parent(ctl, grp)
    cmds.setAttr(ctl + ".rotateOrder", 2)
    base_y = 250 if big_rotation else 0
    for t, (x, y, z) in ((1, (0, 0, 0)), (20, (60, 40, -30)), (40, (120, 90, 80))):
        for a, v in (("rx", x), ("ry", y + base_y), ("rz", z), ("ty", t * 0.2)):
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
    return cmds.xform(node, q=True, ws=True, matrix=True)


def same(a, b):
    return all(abs(x - y) <= TOL for x, y in zip(a, b))


def snapshot(nodes):
    return dict(((n, f), world(n, f)) for n in nodes for f in FRAMES)


def constrained_motion(nodes, range_on=True, dy=50.0):
    """LOC + Anim + Constrain -> 로케이터를 옮겨 목표 움직임을 만든다. 반환 (로케이터, 목표 스냅샷)."""
    locs, msg = LBM.bake(nodes, START, END, constrain=["parent"], constrain_range=range_on)
    for loc in locs:
        cmds.keyframe(loc + ".ty", edit=True, relative=True, valueChange=dy)
        cmds.keyframe(loc + ".rz", edit=True, relative=True, valueChange=30)
    return locs, snapshot(nodes)


def loc_layers():
    return [l for l in cmds.ls(type="animLayer") if l.startswith(LBM.CONSTRAINT_LAYER)]


# ---------------------------------------------------------------- 0. 왜 Bake 탭으로는 안 되나 (재현)
ctl, plain = build()
locs, goal = constrained_motion([ctl])
BakeManager.bake([ctl], START, END)
cmds.delete(cmds.ls(type="parentConstraint"))
cmds.delete(loc_layers())
bad = [f for f in range(START, END + 1) if not same(world(ctl, f), goal[(ctl, f)])]
check("reason: Bake tab keys go into LOC_Constraint itself - deleting the layer loses them", len(bad) > 0, len(bad))

# ---------------------------------------------------------------- 1. 레이어 컨트롤러
ctl, plain = build()
orig = snapshot([ctl])
locs, goal = constrained_motion([ctl])
check("setup: the goal differs from the original inside the range",
      not same(goal[(ctl, START + 3)], orig[(ctl, START + 3)]))
done, msg = LBM.bake_to_keys([ctl])
print(msg)
# ★ undo 는 시간 이동보다 먼저 - mayapy 에선 currentTime 도 undo 대기열에 쌓인다
cmds.undo()
check("undo: constraint, layer, locator back",
      cmds.ls(type="parentConstraint") and loc_layers() and cmds.ls("arm_ctl_LOC"))
cmds.redo()
check("bake to keys: reports the object and the layer range", done and "[10-25]" in msg, msg)
check("bake to keys: constraint, LOC_Constraint, locator gone",
      not cmds.ls(type="parentConstraint") and not loc_layers() and not cmds.ls("arm_ctl_LOC*"))
check("bake to keys: the other layers stay", sorted(cmds.ls(type="animLayer")) == ["BaseAnimation", "Layer1", "Layer2"])
bad = [f for f in FRAMES if not same(world(ctl, f), goal[(ctl, f)])]
check("bake to keys: every frame = the constrained motion (keys only)", not bad, bad[:5])
check("bake to keys: outside the range = original motion",
      all(same(world(ctl, f), orig[(ctl, f)]) for f in FRAMES if f < START - 1 or f > END + 1))

# ---------------------------------------------------------------- 2. 레이어 없는 오브젝트 (구간 켬 = 레이어 경로)
ctl, plain = build()
orig = snapshot([plain])
locs, goal = constrained_motion([plain])
done, msg = LBM.bake_to_keys([plain])
check("plain object: layer path baked back to plain keys",
      not loc_layers() and not cmds.ls(type="parentConstraint")
      and all(same(world(plain, f), goal[(plain, f)]) for f in FRAMES), msg)

# ---------------------------------------------------------------- 3. 레이어 없는 오브젝트 + 구간 끔 (pairBlend 경로)
ctl, plain = build()
locs, goal = constrained_motion([plain], range_on=False)
done, msg = LBM.bake_to_keys([plain])
check("pairBlend path without Start / End: skipped with a reason", not done and "Start / End" in msg, msg)
done, msg = LBM.bake_to_keys([plain], start=START, end=END)
check("pairBlend path: baked with the Start / End fields, constraint gone",
      not cmds.ls(type="parentConstraint")
      and all(same(world(plain, f), goal[(plain, f)]) for f in range(START, END + 1)), msg)

# ---------------------------------------------------------------- 4. 큰 회전 (원래 커브가 180 넘음) - 경계에서 안 튄다
ctl, plain = build(big_rotation=True)
locs, goal = constrained_motion([ctl])
done, msg = LBM.bake_to_keys([ctl])
check("big rotation: every frame = the constrained motion",
      all(same(world(ctl, f), goal[(ctl, f)]) for f in FRAMES), msg)
cmds.currentTime(START - 1)
a = cmds.getAttr(ctl + ".ry")
cmds.currentTime(START)
b = cmds.getAttr(ctl + ".ry")
check("big rotation: no 360 jump at Start", abs(a - b) < 90, (a, b))

# ---------------------------------------------------------------- 5. 두 오브젝트 함께 · 로케이터 없는 오브젝트는 건너뜀
ctl, plain = build()
locs, goal = constrained_motion([ctl, plain])
other = cmds.circle(name="other_ctl")[0]
done, msg = LBM.bake_to_keys([ctl, plain, other])
check("two objects baked, one layer removed, unconstrained skipped",
      len(done) == 2 and not loc_layers() and "other_ctl (no locator constraint)" in msg, msg)
check("two objects: both keep the constrained motion",
      all(same(world(n, f), goal[(n, f)]) for n in (ctl, plain) for f in FRAMES))

# ---------------------------------------------------------------- 6. 레이어에 목록 밖 오브젝트도 있으면 레이어는 남는다
ctl, plain = build()
locs, goal = constrained_motion([ctl, plain])
done, msg = LBM.bake_to_keys([ctl])
check("layer kept while another object still uses it",
      loc_layers() and cmds.listRelatives(plain, children=True, type="parentConstraint"), msg)
check("the baked object left the layer", not LBM.constraint_layers(ctl))

# ---------------------------------------------------------------- 7. Keep locators
ctl, plain = build()
locs, goal = constrained_motion([ctl])
done, msg = LBM.bake_to_keys([ctl], delete_locators=False)
check("delete_locators=False keeps the locator", cmds.ls("arm_ctl_LOC") and not cmds.ls(type="parentConstraint"))

print("RESULT {0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
