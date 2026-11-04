# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.37 - Bake > Locator 의 Constrain Objects (로케이터 -> 오브젝트) 회귀 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_locator_bake_constrain.py
#
# 판정 : 컨스트레인트를 건 뒤 오브젝트의 월드 행렬 == 베이크 전 자기 애니메이션(구간 안 전 프레임).
#        로케이터를 움직이면 오브젝트가 따라온다. 잠김 · 다른 구동 축은 skip, 종류 조합 · 거부 · undo.
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.api.OpenMaya as om   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00110_animTool_V02.app.core.locator_bake_manager import LocatorBakeManager as LBM   # noqa: E402

R = []
FRAMES = list(range(1, 41))


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build():
    """ns:grp(키 · 스케일 2) > ns:arm_ctl(zxy, 키) / 조인트 체인(jointOrient, 키)."""
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=1, max=40, ast=1, aet=40)
    if not cmds.namespace(exists="ns"):
        cmds.namespace(add="ns")
    grp = cmds.group(empty=True, name="ns:grp")
    for t, v in ((1, 0), (40, 30)):
        cmds.setKeyframe(grp, at="ry", t=t, v=v * 3)
        cmds.setKeyframe(grp, at="tx", t=t, v=v)
    ctl = cmds.circle(name="ns:arm_ctl")[0]
    cmds.parent(ctl, grp)
    cmds.setAttr(grp + ".s", 2, 2, 2)
    cmds.setAttr(ctl + ".rotateOrder", 2)
    for t, (x, y, z) in ((1, (0, 0, 0)), (20, (170, 40, -60)), (40, (350, 90, 200))):
        for a, v in (("rx", x), ("ry", y), ("rz", z), ("ty", t * 0.1), ("sx", 1 + t * 0.01)):
            cmds.setKeyframe(ctl, at=a, t=t, v=v)
    cmds.select(clear=True)
    j1 = cmds.joint(name="j1", p=(0, 0, 0))
    j2 = cmds.joint(name="j2", p=(0, 5, 2))
    cmds.joint(j1, e=True, oj="xyz", sao="yup", ch=True, zso=True)
    for t, v in ((1, 0), (40, 120)):
        cmds.setKeyframe(j1, at="rz", t=t, v=v)
        cmds.setKeyframe(j2, at="ry", t=t, v=-v)
    return grp, ctl, j1, j2


def snapshot(node):
    return [om.MMatrix(cmds.getAttr(node + ".worldMatrix", time=t)) for t in FRAMES]


def tr_diff(node, snaps):
    """월드 위치 · 회전(스케일 제외) 최대 차이."""
    worst = 0.0
    for t, mb in zip(FRAMES, snaps):
        ma = om.MTransformationMatrix(om.MMatrix(cmds.getAttr(node + ".worldMatrix", time=t)))
        mb = om.MTransformationMatrix(mb)
        pa, pb = ma.translation(om.MSpace.kWorld), mb.translation(om.MSpace.kWorld)
        qa, qb = ma.rotation(asQuaternion=True), mb.rotation(asQuaternion=True)
        dq = min(sum((x - y) ** 2 for x, y in zip(qa, qb)), sum((x + y) ** 2 for x, y in zip(qa, qb))) ** 0.5
        worst = max(worst, (pa - pb).length(), dq)
    return worst


def full_diff(node, snaps):
    worst = 0.0
    for t, mb in zip(FRAMES, snaps):
        ma = cmds.getAttr(node + ".worldMatrix", time=t)
        worst = max(worst, max(abs(x - y) for x, y in zip(ma, list(mb))))
    return worst


def constraints_on(node, ctype):
    """node 에 걸린 ctype 컨스트레인트 (키가 있으면 pairBlend 를 거치므로 연결 대신 자식으로 찾는다)."""
    return cmds.listRelatives(node, children=True, type=ctype) or []


# ---- 1. 기본 Parent: 오브젝트가 베이크 전 애니메이션 그대로, 로케이터가 구동 ----
grp, ctl, j1, j2 = build()
snap_ctl, snap_j2 = snapshot(ctl), snapshot(j2)
calls = {"phases": []}


def progress(done, total, message=None):
    pass


progress.phase = lambda name: calls["phases"].append(name)
cmds.currentTime(7)
locs, msg = LBM.bake([ctl, j2], 1, 40, constrain=["parent"], progress=progress)
print(msg)
check("parent: two locators", len(locs) == 2, locs)
check("parent: phases include Constraining last", calls["phases"][-1] == LBM.PHASE_CONSTRAIN, calls["phases"])
check("parent: ctl has parentConstraint", len(constraints_on(ctl, "parentConstraint")) == 1)
check("parent: j2 has parentConstraint", len(constraints_on(j2, "parentConstraint")) == 1)
check("parent: ctl driven by its own locator",
      locs[0] in (cmds.parentConstraint(constraints_on(ctl, "parentConstraint")[0], q=True, targetList=True) or []))
check("parent: ctl world T/R unchanged 1e-4", tr_diff(ctl, snap_ctl) < 1e-4, tr_diff(ctl, snap_ctl))
check("parent: joint world T/R unchanged 1e-4", tr_diff(j2, snap_j2) < 1e-4, tr_diff(j2, snap_j2))
check("parent: keyed channels go through pairBlend", bool(cmds.listConnections(ctl + ".rx", type="pairBlend")))
check("parent: message reports constraints", "Constrained objects (Parent): 2" in msg, msg)
check("parent: current time restored", cmds.currentTime(q=True) == 7)
cmds.undo()
check("undo removes locators and constraints",
      not cmds.ls("arm_ctl_LOC", "j2_LOC") and not cmds.ls(type="parentConstraint"))
check("undo restores object animation", tr_diff(ctl, snap_ctl) < 1e-6, tr_diff(ctl, snap_ctl))
# 로케이터를 움직이면 오브젝트가 따라온다 (새 씬)
grp, ctl, j1, j2 = build()
locs, msg = LBM.bake([ctl], 1, 40, constrain=["parent"])
cmds.currentTime(10)
cmds.cutKey(locs[0], attribute="tx", clear=True)
cmds.setAttr(locs[0] + ".tx", 123.0)
check("parent: moving locator moves object",
      abs(cmds.xform(ctl, q=True, ws=True, t=True)[0] - 123.0) < 1e-4, cmds.xform(ctl, q=True, ws=True, t=True))

# ---- 2. Parent + Scale (스케일 부모 2 아래, 스케일 키) -> 월드 행렬 전체 ----
grp, ctl, j1, j2 = build()
locs, msg = LBM.bake([ctl], 1, 40, scale=True, constrain=["parent", "scale"])
print(msg)
check("parent+scale: both constraints", constraints_on(ctl, "parentConstraint") and constraints_on(ctl, "scaleConstraint"))
check("parent+scale: keyed sx skipped (scale has no pairBlend), sy/sz constrained",
      not cmds.listConnections(ctl + ".sx", source=True, destination=False, type="scaleConstraint")
      and cmds.listConnections(ctl + ".sy", source=True, destination=False, type="scaleConstraint")
      and "scale skipped axes [x] (locked / driven / keyed)" in msg, msg)
check("parent+scale: full world matrix unchanged 1e-4", full_diff(ctl, snap_ctl) < 1e-4, full_diff(ctl, snap_ctl))
cmds.undo()

# ---- 3. Point + Orient (Parent 대신) ----
grp, ctl, j1, j2 = build()
locs, msg = LBM.bake([ctl, j2], 1, 40, constrain=["point", "orient"])
print(msg)
check("point+orient: ctl has point and orient",
      constraints_on(ctl, "pointConstraint") and constraints_on(ctl, "orientConstraint")
      and not constraints_on(ctl, "parentConstraint"))
check("point+orient: ctl world T/R unchanged 1e-4", tr_diff(ctl, snap_ctl) < 1e-4, tr_diff(ctl, snap_ctl))
check("point+orient: joint (jointOrient) world T/R unchanged 1e-4", tr_diff(j2, snap_j2) < 1e-4, tr_diff(j2, snap_j2))
cmds.undo()

# ---- 4. 잠긴 축 · 다른 노드가 구동하는 축은 그 축만 skip ----
grp, ctl, j1, j2 = build()
cmds.setAttr(ctl + ".tz", lock=True)
md = cmds.createNode("multiplyDivide", name="driver_md")
cmds.connectAttr(md + ".outputX", ctl + ".rotateY", force=True)
locs, msg = LBM.bake([ctl], 1, 40, constrain=["parent"])
print(msg)
pc = constraints_on(ctl, "parentConstraint")
check("blocked axes: constraint still made", len(pc) == 1)
check("blocked axes: tz not connected (locked)", not cmds.listConnections(ctl + ".tz", source=True, destination=False))
check("blocked axes: ry still driven by multiplyDivide",
      cmds.listConnections(ctl + ".ry", source=True, destination=False, skipConversionNodes=True) == [md])
check("blocked axes: tx connected by constraint",
      bool(cmds.listConnections(ctl + ".tx", source=True, destination=False, type="pairBlend")
           or cmds.listConnections(ctl + ".tx", source=True, destination=False, type="parentConstraint")))
check("blocked axes: warning names the axes", "T[z]" in msg and "R[y]" in msg, msg)
cmds.undo()
cmds.delete(md)
cmds.setAttr(ctl + ".tz", lock=False)

# ---- 5. 거부 · 건너뛰기 ----
grp, ctl, j1, j2 = build()
check("parent + point rejected", LBM.bake([ctl], 1, 10, constrain=["parent", "point"])[0] == [])
check("parent + orient rejected", LBM.bake([ctl], 1, 10, constrain=["parent", "orient"])[0] == [])
locs, msg = LBM.bake([ctl], 1, 10, constrain=["scale"])   # Scale 안 구움
check("scale constraint without scale bake skipped with warning",
      locs and not constraints_on(ctl, "scaleConstraint") and "Scale not baked" in msg, msg)
cmds.undo()
locs, msg = LBM.bake([ctl], 1, 10, translate=False, constrain=["point"])
check("point without translate bake skipped", locs and not constraints_on(ctl, "pointConstraint"), msg)
cmds.undo()
locs, msg = LBM.bake([ctl], 1, 10, translate=False, constrain=["parent"])
pc = constraints_on(ctl, "parentConstraint")
check("parent with rotate only: translate untouched",
      pc and not cmds.listConnections(ctl + ".tx", source=True, destination=False, type="pairBlend")
      and not cmds.listConnections(ctl + ".tx", source=True, destination=False, type="parentConstraint"), msg)
cmds.undo()

# ---- 6. 컨스트레인트 없음 (기존 동작 그대로) ----
grp, ctl, j1, j2 = build()
locs, msg = LBM.bake([ctl], 1, 10)
check("no constrain: object untouched", not constraints_on(ctl, "parentConstraint") and "Constrained" not in msg, msg)
cmds.undo()

# ---- 7. 한 종류가 실패해도 경고만 - 로케이터 · 다른 종류는 남는다 ----
grp, ctl, j1, j2 = build()
orig = cmds.orientConstraint
cmds.orientConstraint = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
try:
    locs, msg = LBM.bake([ctl, j2], 1, 10, constrain=["point", "orient"])
finally:
    cmds.orientConstraint = orig
print(msg)
check("orient failure: locators kept", len(locs) == 2, locs)
check("orient failure: point still made on both",
      constraints_on(ctl, "pointConstraint") and constraints_on(j2, "pointConstraint"))
check("orient failure: reported per object", msg.count("orient failed - boom") == 2, msg)
cmds.undo()
check("undo after partial failure leaves nothing",
      not cmds.ls("arm_ctl_LOC*", "j2_LOC*") and not cmds.ls(type=["pointConstraint", "parentConstraint"]))

print("RESULT {0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
