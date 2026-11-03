# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.36 - Bake > Locator (LOC + Anim) 회귀 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_locator_bake.py
#
# 판정 : 로케이터의 worldMatrix == 원본의 worldMatrix (구간 안 정수 프레임 전부). 진행 콜백 · 단계 순서 · 실패 정리 · undo.
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00110_animTool_V02.app.core.locator_bake_manager import LocatorBakeManager as LBM   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def max_world_diff(a, b, frames):
    worst = 0.0
    for t in frames:
        ma = cmds.getAttr(a + ".worldMatrix", time=t)
        mb = cmds.getAttr(b + ".worldMatrix", time=t)
        worst = max(worst, max(abs(x - y) for x, y in zip(ma, mb)))
    return worst


def build():
    """ns:grp(키) > ns:arm_ctl(zxy, 키 + 큰 회전) / 조인트 체인(jointOrient) / IK 없는 단순 리그."""
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=1, max=60, ast=1, aet=60)
    cmds.namespace(add="ns")
    grp = cmds.group(empty=True, name="ns:grp")
    for t, v in ((1, 0), (60, 30)):
        cmds.setKeyframe(grp, at="ry", t=t, v=v * 3)
        cmds.setKeyframe(grp, at="tx", t=t, v=v)
    ctl = cmds.circle(name="ns:arm_ctl")[0]
    cmds.parent(ctl, grp)
    cmds.setAttr(grp + ".s", 2, 2, 2)   # parent 뒤에 - 앞에 주면 parent 가 ctl 에 0.5 를 넣어 월드 스케일이 1 이 된다
    cmds.setAttr(ctl + ".rotateOrder", 2)
    for t, (x, y, z) in ((1, (0, 0, 0)), (30, (170, 40, -60)), (60, (350, 90, 200))):
        cmds.setKeyframe(ctl, at="rx", t=t, v=x)
        cmds.setKeyframe(ctl, at="ry", t=t, v=y)
        cmds.setKeyframe(ctl, at="rz", t=t, v=z)
        cmds.setKeyframe(ctl, at="ty", t=t, v=t * 0.1)
    cmds.select(clear=True)
    j1 = cmds.joint(name="j1", p=(0, 0, 0))
    j2 = cmds.joint(name="j2", p=(0, 5, 2))
    cmds.joint(j1, e=True, oj="xyz", sao="yup", ch=True, zso=True)
    for t, v in ((1, 0), (60, 120)):
        cmds.setKeyframe(j1, at="rz", t=t, v=v)
        cmds.setKeyframe(j2, at="ry", t=t, v=-v)
    return grp, ctl, j1, j2


grp, ctl, j1, j2 = build()
calls = {"phases": [], "steps": 0, "last": None}


def progress(done, total, message=None):
    calls["steps"] += 1
    calls["last"] = (done, total)


progress.phase = lambda name: calls["phases"].append(name)

cmds.currentTime(17)
locs, msg = LBM.bake([ctl, j2, "j2Shape_missing", ctl], 5, 50, progress=progress)
print(msg)
check("two locators (duplicate + missing skipped)", len(locs) == 2, locs)
check("name drops namespace", locs[0] == "arm_ctl_LOC", locs)
check("joint locator name", locs[1] == "j2_LOC", locs)
check("missing reported", "j2Shape_missing" in msg, msg)
check("phases in order", calls["phases"] == [LBM.PHASE_CREATE, LBM.PHASE_BAKE, LBM.PHASE_CLEANUP], calls["phases"])
check("progress called per frame", calls["steps"] >= 46, calls["steps"])
check("current time restored", cmds.currentTime(q=True) == 17)
check("locators selected", sorted(cmds.ls(sl=True)) == sorted(locs))
check("no constraints left", not cmds.ls(type=["parentConstraint", "scaleConstraint"]))
check("rotate order copied", cmds.getAttr(locs[0] + ".rotateOrder") == 2)
check("locators at world root", all(not cmds.listRelatives(l, parent=True) for l in locs))
frames = list(range(5, 51))
check("scale off: locator keeps scale 1 (parent scale 2 not followed)",
      max_world_diff(ctl, locs[0], frames) > 0.5, (max_world_diff(ctl, locs[0], frames), cmds.getAttr(locs[0] + ".s"), cmds.getAttr(ctl + ".worldMatrix", time=10)[:3]))   # 부모 스케일 2 는 S 끄면 안 따라간다
# 위치 · 회전만 비교 (스케일 제외): 정규화한 축 + 위치
import maya.api.OpenMaya as om   # noqa: E402


def tr_diff(a, b, frames):
    worst = 0.0
    for t in frames:
        ma = om.MTransformationMatrix(om.MMatrix(cmds.getAttr(a + ".worldMatrix", time=t)))
        mb = om.MTransformationMatrix(om.MMatrix(cmds.getAttr(b + ".worldMatrix", time=t)))
        pa, pb = ma.translation(om.MSpace.kWorld), mb.translation(om.MSpace.kWorld)
        qa, qb = ma.rotation(asQuaternion=True), mb.rotation(asQuaternion=True)
        dq = min(sum((x - y) ** 2 for x, y in zip(qa, qb)), sum((x + y) ** 2 for x, y in zip(qa, qb))) ** 0.5
        worst = max(worst, (pa - pb).length(), dq)
    return worst


check("ctl world T/R matches 1e-4", tr_diff(ctl, locs[0], frames) < 1e-4, tr_diff(ctl, locs[0], frames))
check("joint world T/R matches 1e-4", tr_diff(j2, locs[1], frames) < 1e-4, tr_diff(j2, locs[1], frames))
check("keys only in range", cmds.keyframe(locs[0] + ".tx", q=True, tc=True)[0] == 5
      and cmds.keyframe(locs[0] + ".tx", q=True, tc=True)[-1] == 50)
ry = cmds.keyframe(locs[0] + ".rx", q=True, vc=True)
check("euler filtered (no jump > 90 between frames)", max(abs(a - b) for a, b in zip(ry, ry[1:])) < 90)

# undo 한 번에 전부 사라진다
cmds.undo()
check("undo removes locators", not cmds.ls("arm_ctl_LOC", "j2_LOC"))

# Scale 포함 -> 월드 행렬 전체가 같다
locs2, msg2 = LBM.bake([ctl], 1, 60, scale=True)
check("scale on: full world matrix matches", max_world_diff(ctl, locs2[0], range(1, 61)) < 1e-4,
      max_world_diff(ctl, locs2[0], range(1, 61)))

# 이름 충돌 -> 마야가 숫자를 붙인다
locs3, _ = LBM.bake([ctl], 1, 10)
check("second run gets unique name", locs3 and locs3[0] != locs2[0], locs3)

# 거부 조건
check("start > end rejected", LBM.bake([ctl], 10, 5)[0] == [])
check("no channel rejected", LBM.bake([ctl], 1, 5, translate=False, rotate=False)[0] == [])
check("empty list rejected", LBM.bake([], 1, 5)[0] == [])
check("shape resolves to transform", LBM.resolve_targets([cmds.listRelatives(ctl, shapes=True, fullPath=True)[0]])[0]
      == cmds.ls(ctl, long=True))

# 실패 정리: bakeResults 가 죽으면 만든 것이 남지 않는다
before = set(cmds.ls(type="transform"))
orig = cmds.bakeResults
cmds.bakeResults = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
try:
    locs4, msg4 = LBM.bake([ctl, j2], 1, 10)
finally:
    cmds.bakeResults = orig
check("failure returns error", locs4 == [] and msg4.startswith("[Error]"), msg4)
check("failure leaves nothing", set(cmds.ls(type="transform")) == before
      and not cmds.ls(type="parentConstraint"))

print("RESULT {0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
