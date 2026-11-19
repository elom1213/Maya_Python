# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 시험 씬 (계획서 §7-1). mayapy 에서 코드로 만든다.
#   simple()  : transform 하나(부분 키), 피벗이 원점 밖인 것, OPM 이 있는 것
#   hierarchy(): 애니메이션된 부모 3단 + parent/point 컨스트레인트 아래 컨트롤, 조인트 체인(jointOrient · SSC · 비균일 스케일 부모)
#   heavy()   : 조인트 200 + IK 4 + 컨스트레인트 50 + 스킨 메시(약 10만 버텍스) + 상관없는 무거운 캐릭터 한 벌
import math

import maya.cmds as cmds


def _key_translate(node, frames, fn):
    for f in frames:
        x, y, z = fn(f)
        cmds.setKeyframe(node, attribute="translateX", time=f, value=x)
        cmds.setKeyframe(node, attribute="translateY", time=f, value=y)
        cmds.setKeyframe(node, attribute="translateZ", time=f, value=z)


def _key_rotate(node, frames, fn):
    for f in frames:
        x, y, z = fn(f)
        cmds.setKeyframe(node, attribute="rotateX", time=f, value=x)
        cmds.setKeyframe(node, attribute="rotateY", time=f, value=y)
        cmds.setKeyframe(node, attribute="rotateZ", time=f, value=z)


def new(end=120):
    cmds.file(new=True, force=True)
    cmds.playbackOptions(minTime=1, maxTime=end, animationStartTime=1, animationEndTime=end)
    cmds.currentTime(1)


def simple(end=120):
    """단순 씬. 반환: {"plain", "pivot", "opm", "partial"}."""
    new(end)
    plain = cmds.polyCube(name="plain")[0]
    _key_translate(plain, (1, 30, 60, 90, end), lambda f: (f * 0.1, math.sin(f * 0.1) * 3, 0.0))
    pivot = cmds.polyCube(name="pivotCube")[0]
    cmds.xform(pivot, rotatePivot=(2, 1, 0), scalePivot=(1, 0, 0.5))
    _key_translate(pivot, (1, 40, end), lambda f: (0, f * 0.05, f * 0.02))
    _key_rotate(pivot, (1, end), lambda f: (0, f * 2.0, f * 0.5))
    cmds.setKeyframe(pivot, attribute="scaleX", time=1, value=1.0)
    cmds.setKeyframe(pivot, attribute="scaleX", time=end, value=2.0)
    opm = cmds.polyCube(name="opmCube")[0]
    cmds.setAttr(opm + ".offsetParentMatrix", [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 5, 2, -3, 1], type="matrix")
    _key_translate(opm, (1, end), lambda f: (f * 0.03, 0, 0))
    partial = cmds.polyCube(name="partialCube")[0]
    for f, v in ((1, 0.0), (50, 4.0), (end, 1.0)):
        cmds.setKeyframe(partial, attribute="translateX", time=f, value=v)
    cmds.setKeyframe(partial, attribute="translateY", time=25, value=2.0)   # Y 는 다른 프레임에 키 하나
    return {"plain": plain, "pivot": pivot, "opm": opm, "partial": partial}


def hierarchy(end=120):
    """계층 씬. 반환: {"ctrl", "joint", "driven"}."""
    new(end)
    top = cmds.group(empty=True, name="top")
    mid = cmds.group(empty=True, name="mid", parent=top)
    low = cmds.group(empty=True, name="low", parent=mid)
    _key_translate(top, (1, end), lambda f: (f * 0.05, 0, 0))
    _key_rotate(mid, (1, 60, end), lambda f: (0, f * 1.5, 0))
    cmds.setKeyframe(low, attribute="scaleX", time=1, value=1.0)
    cmds.setKeyframe(low, attribute="scaleX", time=end, value=1.5)
    # 컨스트레인트로 움직이는 그룹 아래 컨트롤
    driver = cmds.spaceLocator(name="driver")[0]
    _key_translate(driver, (1, 50, end), lambda f: (math.cos(f * 0.05) * 4, f * 0.02, math.sin(f * 0.05) * 4))
    follow = cmds.group(empty=True, name="follow", parent=low)
    cmds.parentConstraint(driver, follow, maintainOffset=False)
    ctrl = cmds.circle(name="ctrl")[0]
    cmds.parent(ctrl, follow)
    _key_translate(ctrl, (1, 30, 70, end), lambda f: (0, math.sin(f * 0.2), f * 0.01))
    # 조인트 체인 (jointOrient · segmentScaleCompensate · 비균일 스케일 부모)
    cmds.select(clear=True)
    holder = cmds.group(empty=True, name="holder")
    cmds.setAttr(holder + ".scale", 1.0, 2.0, 0.5)
    cmds.select(clear=True)
    j1 = cmds.joint(name="j1", position=(0, 0, 0))
    j2 = cmds.joint(name="j2", position=(2, 1, 0))
    j3 = cmds.joint(name="j3", position=(4, 0, 1))
    cmds.parent(j1, holder)
    cmds.setAttr(j2 + ".jointOrient", 10, 20, 30)
    cmds.setAttr(j3 + ".segmentScaleCompensate", 1)
    _key_rotate(j1, (1, end), lambda f: (0, 0, f * 0.5))
    cmds.setKeyframe(j2, attribute="scaleY", time=1, value=1.0)
    cmds.setKeyframe(j2, attribute="scaleY", time=end, value=1.3)
    _key_translate(j3, (1, 60, end), lambda f: (2 + math.sin(f * 0.1), 0.5, 1))
    # translate 가 컨스트레인트로 구동되는 것 (잠금 대상)
    driven = cmds.polyCube(name="driven")[0]
    cmds.pointConstraint(driver, driven)
    return {"ctrl": ctrl, "joint": "j3", "driven": driven, "top": top}


def heavy(end=120, joints=200, iks=4, constraints=50, mesh_div=(400, 250), extra_character=True):
    """무거운 리그. 반환: {"ctrl", "mesh", "joints"}."""
    new(end)
    root = cmds.group(empty=True, name="rig")
    chains = []
    per = joints // 4
    for c in range(4):
        cmds.select(clear=True)
        chain = []
        for i in range(per):
            chain.append(cmds.joint(name="c{0}_j{1}".format(c, i), position=(c * 3, i * 0.3, 0)))
        cmds.parent(chain[0], root)
        chains.append(chain)
        for i, j in enumerate(chain[:-1]):
            if i % 3 == 0:
                _key_rotate(j, (1, end // 2, end), lambda f, k=i: (math.sin(f * 0.05 + k) * 10, 0, math.cos(f * 0.04) * 8))
    # IK
    for c in range(iks):
        chain = chains[c % 4]
        ik = cmds.ikHandle(startJoint=chain[-12], endEffector=chain[-2], solver="ikRPsolver", name="ik{0}".format(c))[0]
        _key_translate(ik, (1, end), lambda f, c=c: (c * 3 + math.sin(f * 0.1), per * 0.3 - 1, math.cos(f * 0.1)))
    # 컨스트레인트
    locs = []
    for k in range(constraints):
        loc = cmds.spaceLocator(name="cn{0}".format(k))[0]
        src = chains[k % 4][(k * 7) % (per - 1)]
        cmds.parentConstraint(src, loc, maintainOffset=True)
        locs.append(loc)
    # 편집 대상: 컨스트레인트 로케이터 아래 컨트롤
    ctrl = cmds.circle(name="hand_ctrl")[0]
    cmds.parent(ctrl, locs[-1])
    _key_translate(ctrl, (1, 25, 50, 75, end), lambda f: (math.sin(f * 0.1), math.cos(f * 0.1), f * 0.01))
    # 스킨 메시
    mesh = cmds.polySphere(name="body", subdivisionsAxis=mesh_div[0], subdivisionsHeight=mesh_div[1], radius=8)[0]
    infl = [j for chain in chains for j in chain[::2]]
    cmds.skinCluster(infl, mesh, toSelectedBones=True, maximumInfluences=4)
    if extra_character:
        other = cmds.polySphere(name="other_body", subdivisionsAxis=mesh_div[0], subdivisionsHeight=mesh_div[1], radius=6)[0]
        cmds.select(clear=True)
        oj = [cmds.joint(name="o_j{0}".format(i), position=(10, i * 0.5, 0)) for i in range(40)]
        for i in range(0, 40, 4):
            _key_rotate(oj[i], (1, end), lambda f, k=i: (0, math.sin(f * 0.05 + k) * 15, 0))
        cmds.skinCluster(oj, other, toSelectedBones=True, maximumInfluences=4)
    return {"ctrl": ctrl, "mesh": mesh, "joints": joints}
