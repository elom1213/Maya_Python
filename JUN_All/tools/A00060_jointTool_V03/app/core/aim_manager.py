# -*- coding: utf-8 -*-
# Aim 탭 로직 - Start~End 체인을 IK+pole 식으로 정렬한다(회전만 바꾸고 위치는 완전 보존).
#   v03.11 : Root 모드 - 루트 하나로 그 아래 모든 최하위 자식까지 (make_joint_aim_roots).
#   각 joint 의 X 를 자식의 원본 위치로 조준하고, 선택한 aim_axis 가 pole tgt 을 향하도록
#   X 둘레 트위스트를 결정해 jointOrient 에 기록한다. translate 는 **움직여 버린 자식만** 되돌린다(v03.11).
#
#   설계 원칙:
#   1) aimConstraint 미사용 : 부모가 자식을 타깃으로 aim 하면
#      joint.rotate -> child.worldMatrix -> constraint -> joint.rotate 평가 cycle 발생.
#   2) reparent(unparent) 미사용 : 레퍼런스 조인트는 부모 변경 편집이 제한된다. setAttr(jointOrient)만 씀.
#   3) 위치 완전 보존(IK 식) : 부모 X 를 자식의 원본 위치로 "정확히 조준"하면, 자식은 고정 local
#      거리(=뼈 길이)만큼 새 X 위에 놓여 원래 월드 위치에 그대로 떨어진다. 보조축(트위스트)은
#      X 둘레 회전이라 X 위의 자식을 움직이지 않는다.
#      단 이것은 **자식이 부모 X 축 위에 있을 때만** 성립한다(mayapy 실측). 분기점의 다른 가지,
#      X 로 정렬되지 않은 체인은 자식이 옮겨지므로 v03.11 부터 돌린 직후 그 자식만 원위치시킨다.
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


def _pole_for(pole_targets, i):
    """i 번째 줄의 pole tgt. 모자라면 마지막 것, 없으면 None."""
    if i < len(pole_targets):
        return pole_targets[i]
    return pole_targets[-1] if pole_targets else None


def _long(node):
    found = cmds.ls(node, long=True)
    return found[0] if found else node


def _joint_children(jnt):
    """jnt 의 자식 joint (전체 경로, 마야의 자식 순서 그대로)."""
    return cmds.listRelatives(jnt, children=True, type="joint", fullPath=True) or []


def _restore_children(jnt, wpos, warnings):
    """jnt 를 돌린 뒤, 움직여 버린 자식 joint 를 원래 월드 위치로 되돌린다 (v03.11).

    X 를 자식으로 조준해도 자식이 제자리에 남는 것은 **자식이 부모 X 축 위에 있을 때뿐**이다.
    - 분기점(Root 모드): 첫 자식만 X 위에 있고 다른 가지의 자식은 트위스트에 딸려 돈다.
    - X 로 정렬되지 않은 체인: 조준한 자식도 X 위에 있지 않아 옮겨진다.
    그래서 돌린 직후 **움직인 자식만** translate 를 고쳐 원위치시킨다. 이미 정렬된 체인은
    자식이 움직이지 않으므로 아무것도 쓰지 않는다(이전과 같은 결과).
    잠기거나 연결된 translate 는 xform 이 **조용히 건너뛰므로** 되읽어 확인하고 경고한다.
    """
    for child in _joint_children(jnt):
        target = wpos.get(child)
        if target is None:
            continue
        now = om.MVector(cmds.xform(child, q=True, ws=True, translation=True))
        if (now - target).length() < _EPS * 10:
            continue
        cmds.xform(child, ws=True, translation=(target.x, target.y, target.z))
        after = om.MVector(cmds.xform(child, q=True, ws=True, translation=True))
        if (after - target).length() > 1e-4:
            warnings.append("[WARN] {0} moved - its translate is locked or driven, "
                            "could not put it back".format(child.split("|")[-1]))


def _apply_tasks(task_by_joint, aim_axis):
    """정렬 작업 {joint: (child, pole)} 을 적용한다. `(정렬한 joint 수, 경고 목록)`.

    1) 어떤 joint 도 정렬하기 전에 대상 joint 와 **그 자식 joint 전부**의 원본 월드 위치를 스냅샷
    2) 조상부터(깊이 오름차순) 적용 : X 를 조준할 자식의 **원본** 위치로 향하게 하고,
       돌린 직후 움직인 자식을 원위치시킨다(_restore_children). 입력 순서와 무관.
    이름은 전체 경로로 통일한다 - Chain 모드 리스트는 짧은 이름, 자식 목록은 전체 경로라서.
    """
    tasks = {}
    for jnt, (child, pole) in task_by_joint.items():
        tasks.setdefault(_long(jnt), (_long(child), pole))

    joints_seen = set(tasks)
    for jnt, (child, _pole) in tasks.items():
        joints_seen.add(child)
        joints_seen.update(_joint_children(jnt))
    wpos = {j: om.MVector(cmds.xform(j, q=True, ws=True, translation=True))
            for j in joints_seen}

    done = 0
    warnings = []
    for j in sorted(tasks, key=_depth):
        child, pole = tasks[j]
        x = wpos[child] - wpos[j]  # 자식의 원본 위치 조준
        if x.length() < _EPS:
            continue  # 두 joint 가 겹침 -> 방향 정의 불가
        ppos = om.MVector(cmds.xform(pole, q=True, ws=True, translation=True)) if pole else None
        xb, yb, zb = _aim_basis(x, wpos[j], ppos, aim_axis)
        _apply_world_orient(j, xb, yb, zb)  # jointOrient
        _restore_children(j, wpos, warnings)
        done += 1
    return done, warnings


def make_joint_aim(starts, ends, pole_targets, aim_axis=2):
    """[Chain 모드] 각 (start,end) 체인 joint 의 X 를 자식의 원본 위치로 조준(=조준된 체인이면
    X 불변)하고, aim_axis 가 pole tgt 을 향하도록 X 둘레 트위스트를 jointOrient 에 기록한다.
    모든 joint 의 월드 위치가 보존된다(IK+pole 식) - 움직인 자식은 원위치시킨다(_restore_children).
    반환: `(정렬한 joint 수, 경고 목록)` (v03.11 - 전에는 None).

    start/end 가 체인을 여러 쌍으로 쪼개 줘도 정확하도록, 모든 대상 joint 를 정렬 전에 한 번에
    스냅샷하고 부모(조상)부터 적용한다.

    aim_axis : 1=X,2=Y,3=Z (pole 을 향할 보조축; X 는 트위스트 축이라 보통 Y/Z)
    """
    n = min(len(starts), len(ends))

    # 정렬 작업 수집 : joint -> (child, pole). 한 joint 은 한 번만(첫 등장 우선).
    task_by_joint = {}
    for i in range(n):
        chain = _chain_between(starts[i], ends[i])  # root -> leaf
        pole = _pole_for(pole_targets, i)
        for k in range(len(chain) - 1):  # leaf 제외
            if chain[k] not in task_by_joint:
                task_by_joint[chain[k]] = (chain[k + 1], pole)

    return _apply_tasks(task_by_joint, aim_axis)


# ----------------------------------------------------------------- Root 모드 (v03.11)

def root_tasks(root, pole):
    """root 부터 **모든 최하위 자식까지** 의 정렬 작업 {joint: (조준할 자식, pole)}.

    - 자식 joint 가 하나면 그 자식을 조준한다(Chain 모드와 같다).
    - **여럿이면(분기) 첫 번째 자식**을 조준한다 - 마야 `Orient Joint`(joint -e -oj -ch) 와 같은
      규칙이다. 나머지 가지도 각자 끝까지 내려가며 정렬된다.
    - 최하위(자식 없는) joint 는 조준할 곳이 없어 건드리지 않는다(Chain 모드의 End 와 같다).
    - 전체 경로로 다룬다 - 가지마다 같은 짧은 이름이 흔하다(예: 손가락 `_01`).
    """
    tasks = {}
    stack = [cmds.ls(root, long=True)[0]]
    while stack:
        jnt = stack.pop()
        children = _joint_children(jnt)
        if children:
            tasks[jnt] = (children[0], pole)
            stack.extend(children)
    return tasks


def make_joint_aim_roots(roots, pole_targets, aim_axis=2):
    """[Root 모드] roots[i] 아래 모든 joint 를 최하위 자식까지 정렬한다. `(정렬 수, 메시지)`.

    각 루트의 계층 전체가 **같은 줄의 pole tgt 하나**(모자라면 마지막 것)를 aim_axis 로 향한다.
    계산은 Chain 모드와 같다(_apply_tasks) - 위치는 그대로, jointOrient 만 바뀐다.
    루트가 겹치면(한 루트가 다른 루트 아래) 먼저 적힌 루트의 pole 이 이긴다.
    """
    messages = []
    task_by_joint = {}
    for i, root in enumerate(roots):
        if not cmds.objExists(root):
            messages.append("[WARN] Root not found: {0}".format(root))
            continue
        if cmds.nodeType(root) != "joint":
            messages.append("[WARN] Root is not a joint, skipped: {0}".format(root))
            continue
        tasks = root_tasks(root, _pole_for(pole_targets, i))
        if not tasks:
            messages.append("[WARN] {0} has no child joint - nothing to aim".format(root))
        for jnt, task in tasks.items():
            task_by_joint.setdefault(jnt, task)

    if not task_by_joint:
        return 0, messages
    done, warnings = _apply_tasks(task_by_joint, aim_axis)
    return done, messages + warnings
