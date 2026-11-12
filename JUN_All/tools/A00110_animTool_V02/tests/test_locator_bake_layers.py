# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.61 - Bake > Locator 의 Constrain Objects : 애니메이션 레이어 컨트롤러 · 구간 블렌드(blendParent) ·
# Bake 탭으로 굽기 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_locator_bake_layers.py
#
# 판정 : BaseAnimation + 다른 레이어에 키가 있는 컨트롤러에도 컨스트레인트가 걸린다(v02.57 까지 0 개). 새 레이어는 안 생긴다.
#        Blend only in Frame Range = pairBlend 웨이트(blendParent1 ...) step 키 -> 구간 안은 로케이터, 밖은 원래 월드.
#        그 상태로 Bake 탭(BakeManager.bake) -> 로케이터 · 컨스트레인트를 지워도 전 프레임 같은 움직임(키만으로).
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
    """grp(키) > arm_ctl(Base 키 + Layer1 additive + Layer2 override 0.5) / plain_ctl(레이어 없음) / bare_ctl(키 없음)."""
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
        for a, v in (("rx", x), ("ry", y + base_y), ("rz", z), ("ty", t * 0.2), ("sx", 1 + t * 0.01)):
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
    for t, v in ((1, 0), (20, 7), (40, 12)):
        cmds.setKeyframe(plain, at="ty", t=t, v=v)
        cmds.setKeyframe(plain, at="rz", t=t, v=v * 5)
    bare = cmds.circle(name="bare_ctl")[0]
    cmds.setAttr(bare + ".t", 3, 4, 5)
    cmds.setAttr(bare + ".r", 10, 20, 30)
    cmds.select(clear=True)
    return "|grp|arm_ctl", "|plain_ctl", "|bare_ctl"


def world(node, f):
    cmds.currentTime(f)
    return cmds.xform(node, q=True, ws=True, matrix=True)


def same(a, b):
    return all(abs(x - y) <= TOL for x, y in zip(a, b))


def same_tr(a, b):
    """이동 · 회전만 비교 (축 길이 = 스케일은 뺀다 - 로케이터 scale 은 1, 오브젝트는 scale 키가 있다)."""
    import math

    def unit(m):
        out = []
        for r in range(3):
            row = m[r * 4:r * 4 + 3]
            n = math.sqrt(sum(v * v for v in row)) or 1.0
            out += [v / n for v in row]
        return out + list(m[12:15])
    return same(unit(a), unit(b))


def snapshot(nodes):
    return dict(((n, f), world(n, f)) for n in nodes for f in FRAMES)


def move_locators(locs):
    """로케이터 커브를 옮겨 '로케이터를 따른다' 와 '원래 움직임' 을 구분한다."""
    for loc in locs:
        cmds.keyframe(loc + ".ty", edit=True, relative=True, valueChange=50)
        cmds.keyframe(loc + ".rz", edit=True, relative=True, valueChange=30)


def layers():
    return sorted(cmds.ls(type="animLayer") or [])


def bad_frames(node, expect, frames=FRAMES):
    return [f for f in frames if not same(world(node, f), expect[(node, f)])]


# ---------------------------------------------------------------- 1. 레이어 채널 판정
ctl, plain, bare = build()
check("layered channels are free now (v02.57 blocked them all)",
      LBM._blocked_axes(ctl, "translate") == [] and LBM._blocked_axes(ctl, "rotate") == [])
check("keyed / layered scale is still blocked (no pairBlend for scale)",
      LBM._blocked_axes(ctl, "scale") == ["x", "y", "z"])

# ---------------------------------------------------------------- 2. 구간 블렌드 - 레이어 컨트롤러
orig = snapshot([ctl])
before_layers = layers()
locs, msg = LBM.bake([ctl], START, END, constrain=["parent"], constrain_range=True)
print(msg)
# ★ undo 는 시간 이동보다 먼저 - mayapy 에선 currentTime 도 undo 대기열에 쌓인다
cmds.undo()
check("undo: locator and constraint gone, no blend keys left",
      not cmds.ls("arm_ctl_LOC*") and not cmds.ls(type="parentConstraint")
      and not cmds.keyframe(ctl + ".blendParent1", q=True) if cmds.attributeQuery("blendParent1", node=ctl, exists=True)
      else not cmds.ls("arm_ctl_LOC*") and not cmds.ls(type="parentConstraint"))
cmds.redo()
check("layered ctl gets a parentConstraint", len(cmds.ls(type="parentConstraint")) == 1, msg)
check("no new animation layer", layers() == before_layers, layers())
check("message names the blend range", "Blend 1 only in 10 - 25" in msg, msg)
w = [(f, round(cmds.getAttr(ctl + ".blendParent1", time=f), 3)) for f in (START - 1, START, END, END + 1)]
check("blendParent1 keyed 0 / 1 / 1 / 0", [v for _f, v in w] == [0, 1, 1, 0], w)
check("stepped: holds between keys", round(cmds.getAttr(ctl + ".blendParent1", time=START - 0.5), 3) == 0
      and round(cmds.getAttr(ctl + ".blendParent1", time=END + 0.5), 3) == 1)
check("right after: object unchanged (locator = object)", not bad_frames(ctl, orig))
loc = locs[0]
move_locators(locs)
inside = [f for f in range(START, END + 1) if not same_tr(world(ctl, f), world(loc, f))]
outside = [f for f in FRAMES if (f < START or f > END) and not same(world(ctl, f), orig[(ctl, f)])]
check("inside Start-End: object matches the moved locator", not inside, inside[:5])
check("outside: object keeps its own motion", not outside, outside[:5])

# ---------------------------------------------------------------- 3. 그 상태로 Bake 탭 -> 로케이터 삭제 = 키만으로 같은 움직임
goal = snapshot([ctl])
n, bmsg = BakeManager.bake([ctl], START, END)
print(bmsg)
check("Bake tab: routed as a range blend object", "range blend" in bmsg, bmsg)
check("Bake tab: nothing changes while the constraint is still there", not bad_frames(ctl, goal))
cmds.delete(loc)
check("deleting the locator removes the constraint", not cmds.ls(type="parentConstraint"))
bad = bad_frames(ctl, goal)
check("after deleting the locator: every frame = the constrained motion (keys only)", not bad, bad[:6])
check("the animation layers are as before", layers() == before_layers, layers())

# ---------------------------------------------------------------- 4. 레이어 없는 오브젝트 · 키 없는 오브젝트
ctl, plain, bare = build()
locs, msg = LBM.bake([plain, bare], START, END, constrain=["parent"], constrain_range=True)
check("bare object got blendParent1 (static key first)", cmds.attributeQuery("blendParent1", node=bare, exists=True)
      and cmds.keyframe(bare + ".blendParent1", q=True), msg)
move_locators(locs)
goal = snapshot([plain, bare])
BakeManager.bake([plain, bare], START, END)
cmds.delete(locs)
for node in (plain, bare):
    bad = bad_frames(node, goal)
    check("plain / bare {0}: keys only = the constrained motion".format(node), not bad, bad[:6])

# ---------------------------------------------------------------- 5. 구간 끔 - 전 프레임 컨스트레인트, 블렌드 키 없음
ctl, plain, bare = build()
locs, msg = LBM.bake([ctl], START, END, constrain=["parent"], constrain_range=False)
move_locators(locs)
check("range off: no blend keys", not cmds.keyframe(ctl + ".blendParent1", q=True))
check("range off: every frame follows the locator",
      all(same_tr(world(ctl, f), world(locs[0], f)) for f in FRAMES))

# ---------------------------------------------------------------- 6. Point + Orient + Scale
ctl, plain, bare = build()
orig = snapshot([ctl])
locs, msg = LBM.bake([ctl], START, END, scale=True, constrain=["point", "orient", "scale"], constrain_range=True)
check("point + orient: blendPoint1 / blendOrient1 keyed",
      all(cmds.keyframe(ctl + "." + a, q=True) for a in ("blendPoint1", "blendOrient1")), msg)
check("scale on a keyed / layered object: skipped with a warning", "scale skipped" in msg, msg)
move_locators(locs)
check("point / orient: inside follows, outside original",
      all(same(world(ctl, f), world(locs[0], f)) for f in range(START, END + 1))
      and all(same(world(ctl, f), orig[(ctl, f)]) for f in FRAMES if f < START or f > END))
ctl2, plain2, bare2 = build()
locs, msg = LBM.bake([bare2], START, END, scale=True, constrain=["parent", "scale"], constrain_range=True)
check("scale on an unkeyed object: constrained every frame with a warning",
      cmds.ls(type="scaleConstraint") and "scale constraint drives every frame" in msg, msg)

# ---------------------------------------------------------------- 7. 큰 회전 - Bake 탭 뒤 경계에서 360 안 튐
ctl, plain, bare = build(big_rotation=True)
locs, msg = LBM.bake([ctl], START, END, constrain=["parent"], constrain_range=True)
move_locators(locs)
goal = snapshot([ctl])
BakeManager.bake([ctl], START, END)
cmds.delete(locs)
check("big rotation: keys only = the constrained motion", not bad_frames(ctl, goal))
cmds.currentTime(START - 1)
a = cmds.getAttr(ctl + ".ry")
cmds.currentTime(START)
b = cmds.getAttr(ctl + ".ry")
check("big rotation: no 360 jump at Start", abs(a - b) < 90, (a, b))

# ---------------------------------------------------------------- 8. 잠긴 축
ctl, plain, bare = build()
cmds.setAttr(ctl + ".tz", lock=True)
locs, msg = LBM.bake([ctl], START, END, constrain=["parent"], constrain_range=True)
check("locked axis skipped, rest constrained", len(cmds.ls(type="parentConstraint")) == 1 and "T[z]" in msg, msg)

print("RESULT {0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
