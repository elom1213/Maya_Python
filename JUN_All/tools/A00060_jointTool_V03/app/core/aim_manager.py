# -*- coding: utf-8 -*-
# Aim 탭 로직 - Start~End 체인을 IK+pole 식으로 정렬한다(회전만 바꾸고 위치는 완전 보존).
#   각 joint 의 X 를 자식의 원본 위치로 조준하고, 선택한 aim_axis 가 pole tgt 을 향하도록
#   X 둘레 트위스트를 결정해 jointOrient 에 기록한다. translate 는 건드리지 않는다.
#
#   설계 원칙:
#   1) aimConstraint 미사용 : 부모가 자식을 타깃으로 aim 하면
#      joint.rotate -> child.worldMatrix -> constraint -> joint.rotate 평가 cycle 발생.
#   2) reparent(unparent) 미사용 : 레퍼런스 조인트는 부모 변경 편집이 제한된다. setAttr(jointOrient)만 씀.
#   3) 위치 완전 보존(IK 식) : 부모 X 를 자식의 원본 위치로 "정확히 조준"하면, 자식은 고정 local
#      거리(=뼈 길이)만큼 새 X 위에 놓여 원래 월드 위치에 그대로 떨어진다. translate 수정 불필요.
#      보조축(트위스트)은 X 둘레 회전이라 X 위의 자식을 움직이지 않는다.
#   4) swing 보존 : 조준된 체인(X 가 이미 자식을 향함)에서는 자식 방향 = 현재 X 라서 X 방향이
#      그대로 유지되고, 결과적으로 트위스트만 바뀐다.
#
#   전역 스냅샷 + 부모우선 적용 : start/end 가 체인을 여러 쌍으로 쪼개 줘도(예: start=[j01,j02],
#   end=[j02,j03]) 정확하도록, "어떤 joint 도 정렬하기 전"에 모든 대상 joint 의 원본 월드 위치를
#   한 번에 스냅샷하고, 정렬 작업을 계층 깊이(조상 먼저)로 정렬해 적용한다. 부모를 정렬하면 자식이
#   잠시 흔들리지만, 자식을 "원본" 손자 위치로 다시 조준하면 손자가 원위치로 복원된다.

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

_EPS = 1e-6


def _chain_between(start, end):
    """start..end 부모 체인을 root->leaf 순으로 반환. 직접 조상 아니면 [start, end]."""
    chain, cur, guard = [end], end, 0
    while cur != start and guard < 10000:
        parent = cmds.listRelatives(cur, parent=True, type="joint")
        if not parent:
            break
        cur = parent[0]
        chain.append(cur)
        guard += 1
    chain.reverse()
    return chain if chain[0] == start else [start, end]


def _aim_basis(x, p_jnt, p_pole, aim_axis):
    """주어진 X(자식 방향) 기준으로 aim_axis 축이 pole 을 향하는 직교 정규기저 (x,y,z) 반환.

    aim_axis : 1=X(=X 와 충돌 -> 임의 up), 2=Y, 3=Z.
    p_pole 가 None 이거나 X 와 평행하면 임의 up 으로 폴백한다(트위스트 미정).
    """
    x = x.normal()

    up = (p_pole - p_jnt) if p_pole is not None else None
    if up is None or up.length() < _EPS or abs((up.normal()) * x) > 0.9999:
        # pole 이 없거나 aim 과 평행 -> world Y(또는 Z)로 폴백
        up = om.MVector(0, 1, 0)
        if abs(up * x) > 0.9999:
            up = om.MVector(0, 0, 1)

    if aim_axis == 3:           # Z 가 pole 을 향함
        y = (up ^ x).normal()
        z = (x ^ y).normal()
    else:                       # 2(Y, 기본) / 1(X 충돌 폴백) : Y 를 pole 쪽으로
        z = (x ^ up).normal()
        y = (z ^ x).normal()
    return x, y, z


def _apply_world_orient(jnt, x, y, z):
    """기저 (x,y,z) 를 jnt 의 world 회전으로 적용. rotate/rotateAxis=0, jointOrient 에 기록."""
    world_rot = om.MMatrix([
        x.x, x.y, x.z, 0.0,
        y.x, y.y, y.z, 0.0,
        z.x, z.y, z.z, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ])
    parent = cmds.listRelatives(jnt, parent=True, fullPath=True)
    if parent:
        p_world = om.MMatrix(cmds.getAttr(parent[0] + ".worldMatrix[0]"))
        local = world_rot * p_world.inverse()
    else:
        local = world_rot

    euler = om.MTransformationMatrix(local).rotation(asQuaternion=False)  # rad, XYZ
    for ax in ("X", "Y", "Z"):
        cmds.setAttr("{0}.rotateAxis{1}".format(jnt, ax), 0)
        cmds.setAttr("{0}.rotate{1}".format(jnt, ax), 0)
    cmds.setAttr(jnt + ".jointOrientX", math.degrees(euler.x))
    cmds.setAttr(jnt + ".jointOrientY", math.degrees(euler.y))
    cmds.setAttr(jnt + ".jointOrientZ", math.degrees(euler.z))


def _depth(node):
    """node 의 DAG 깊이(full path 의 '|' 분절 수). 조상일수록 작다."""
    full = cmds.ls(node, long=True)
    return full[0].count("|") if full else 0


def make_joint_aim(starts, ends, pole_targets, aim_axis=2):
    """각 (start,end) 체인 joint 의 X 를 자식의 원본 위치로 조준(=조준된 체인이면 X 불변)하고,
    aim_axis 가 pole tgt 을 향하도록 X 둘레 트위스트를 jointOrient 에 기록한다. 회전만 바꾸므로
    (translate 미변경) 체인의 모든 joint 월드 위치가 보존된다(IK+pole 식).

    start/end 가 체인을 여러 쌍으로 쪼개 줘도 정확하도록, 모든 대상 joint 를 정렬 전에 한 번에
    스냅샷하고 부모(조상)부터 적용한다.

    aim_axis : 1=X,2=Y,3=Z (pole 을 향할 보조축; X 는 트위스트 축이라 보통 Y/Z)
    """
    n = min(len(starts), len(ends))

    # 1) 정렬 작업 수집 : joint -> (child, pole). 한 joint 은 한 번만(첫 등장 우선).
    task_by_joint = {}
    joints_seen = set()
    for i in range(n):
        chain = _chain_between(starts[i], ends[i])  # root -> leaf
        pole = (pole_targets[i] if i < len(pole_targets)
                else (pole_targets[-1] if pole_targets else None))
        for k in range(len(chain) - 1):  # leaf 제외
            j = chain[k]
            joints_seen.add(j)
            joints_seen.add(chain[k + 1])
            if j not in task_by_joint:
                task_by_joint[j] = (chain[k + 1], pole)

    # 2) 정렬 전에 모든 대상 joint 의 원본 월드 위치를 한 번에 스냅샷
    wpos = {j: om.MVector(cmds.xform(j, q=True, ws=True, translation=True))
            for j in joints_seen}

    # 3) 조상부터(깊이 오름차순) 적용 : 부모 정렬이 자식을 흔들어도, 자식을 "원본" 손자 위치로
    #    다시 조준하면 손자가 원위치로 복원된다. 입력 리스트 순서와 무관.
    for j in sorted(task_by_joint, key=_depth):
        child, pole = task_by_joint[j]
        x = wpos[child] - wpos[j]  # 자식의 원본 위치 조준 -> 자식이 원위치에 자동 복원
        if x.length() < _EPS:
            continue  # 두 joint 가 겹침 -> 방향 정의 불가
        ppos = om.MVector(cmds.xform(pole, q=True, ws=True, translation=True)) if pole else None
        xb, yb, zb = _aim_basis(x, wpos[j], ppos, aim_axis)
        _apply_world_orient(j, xb, yb, zb)  # jointOrient 만 (translate 미변경)
