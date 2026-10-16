# -*- coding: utf-8 -*-
# Curve 탭 로직 - MEL JointTool V05.03 "joint to obj" / orient & rotate / Set Orient 포팅.
#   JUN_make_jnt_toObj / JUN_cmd_create_joints_toObj /
#   JUN_cmd_joint_swap_rotate / JUN_cmd_set_jntOri

import math

import maya.cmds as cmds


_LIST_AXIS = ["x", "y", "z"]
_LIST_UPDWN = ["down", "up"]


def _joint_at_obj(obj):
    """MEL JUN_make_jnt_toObj - 오브젝트의 '월드' 위치에 joint 생성.

    오브젝트가 어떤 계층 아래에 있든 world-space 절대 위치(xform -q -ws -translation)로
    생성한다. joint -p 는 생성 시점에 선택된 부모 joint 아래로 들어갈 수 있어(체인 모드),
    생성 직후 xform(ws) 로 월드 위치를 다시 확정한다(부모/계층 무관 정확 배치)."""
    pos = cmds.xform(obj, q=True, ws=True, translation=True)
    jnt = cmds.joint(p=pos)
    cmds.xform(jnt, ws=True, translation=pos)
    cmds.joint(jnt, edit=True, zso=True, oj="xyz", sao="yup")
    return jnt


def _match_world_rotation(jnt, obj):
    """v03.14 - 분리 조인트에 obj 의 월드 회전을 준다 (jointOrient 로, rotate 는 0).

    버텍스 등 컴포넌트는 회전이 없으니 그대로 둔다. xform 으로 월드 회전을 rotate 에 넣고
    makeIdentity(rotate) 로 jointOrient 에 굳힌다 - 루트 조인트이므로 월드 오일러가 그대로 들어간다.
    """
    if "." in obj:
        return False
    try:
        rot = cmds.xform(obj, q=True, ws=True, rotation=True)
    except Exception:
        return False
    cmds.xform(jnt, ws=True, rotation=rot)
    cmds.makeIdentity(jnt, apply=True, rotate=True, translate=False, scale=False)
    return True


def joints_to_objs(objs, separate, fwd_axis, secd_axis, secd_ori, match_rotation=False):
    """MEL JUN_cmd_create_joints_toObj - 오브젝트마다 joint 생성, 축 옵션으로 orient.

    fwd_axis / secd_axis : 1-base (1=X, 2=Y, 3=Z)  (콤보 index + 1)
    secd_ori             : 1-base (1=+X,2=-X,3=+Y,4=-Y,5=+Z,6=-Z)
    separate             : True 면 각 joint 를 분리(루트), False 면 체인 연결
    match_rotation       : (v03.14) separate 일 때만 - 조인트의 회전을 오브젝트의 월드 회전과
                           맞춘다(jointOrient). 체인(connect)에서는 무시한다.
    """
    # MEL 의 축 인덱스 계산을 그대로 이식
    last_axis = 3 - (fwd_axis + secd_axis - 2)  # 0-base 세 번째 축
    flag_ori = (_LIST_AXIS[fwd_axis - 1]
                + _LIST_AXIS[secd_axis - 1]
                + _LIST_AXIS[last_axis])
    flag_secd_ori = (_LIST_AXIS[int(math.ceil(secd_ori / 2.0) - 1)]
                     + _LIST_UPDWN[secd_ori % 2])

    cmds.select(clear=True)
    prev = None
    for obj in objs:
        cur = _joint_at_obj(obj)
        if prev is not None:
            cmds.joint(prev, edit=True, zso=True, oj=flag_ori, sao=flag_secd_ori)
        prev = cur

        if separate:
            if match_rotation:
                _match_world_rotation(cur, obj)
            cmds.select(clear=True)

    # 마지막 joint orient -> world
    if cmds.ls(selection=True):
        cmds.joint(edit=True, oj="none", ch=True, zso=True)
    cmds.select(clear=True)


def _blocked_channels(jnt, attr):
    """attr(rotate / jointOrient) 중 잠기거나 입력 연결이 있는 채널 이름 목록"""
    blocked = []
    for name in [attr] + [attr + ax for ax in "XYZ"]:
        plug = "{0}.{1}".format(jnt, name)
        if cmds.getAttr(plug, lock=True) or cmds.listConnections(plug, s=True, d=False):
            blocked.append(name)
    return blocked


def _closest_equivalent(euler, target, mat):
    """euler 와 같은 회전인 해 중 target 에 가장 가까운 것.

    옛 축별 합(target)에 맞춰, 한쪽만 값이 있던 경우 숫자가 예전과 같게 나온다
    (예: 190 이 -170 으로 바뀌지 않음). MEulerRotation.setToClosestSolution 은 짐벌 근처에서
    다른 회전을 돌려주므로(0,90,0 x 45,0,0 -> 22.5,45,22.5) 쓰지 않는다 - 두 등가 해에
    360 도 배수만 맞추는 setToClosestCut 을 걸고, 행렬이 같은 것만 고른다.
    """
    best = euler
    best_d = None
    for cand in (euler, euler.alternateSolution()):
        cand = cand.setToClosestCut(target)
        if not cand.asMatrix().isEquivalent(mat, 1e-9):
            continue
        dist = sum(abs(a - b) for a, b in zip((cand.x, cand.y, cand.z),
                                              (target.x, target.y, target.z)))
        if best_d is None or dist < best_d:
            best, best_d = cand, dist
    return best


def swap_rotate_orient(joints, attr_zero, attr_sum):
    """MEL JUN_cmd_joint_swap_rotate - attr_zero 를 0 으로, attr_sum 에 두 값을 합친다.

    'joint orient -> rotate' : attr_zero="jointOrient", attr_sum="rotate"
    'rotate -> joint orient'  : attr_zero="rotate",      attr_sum="jointOrient"

    v03.15 - 축별 덧셈(옛 MEL 방식)은 rotate 와 jointOrient 가 둘 다 값이 있으면 회전이
    바뀐다(오일러는 더해지지 않는다). 조인트 로컬 회전은 [rotateAxis][rotate][jointOrient]
    (행 벡터) 이므로 R x JO 행렬을 만들어 남는 쪽의 회전 순서로 분해한다.
      rotate -> jointOrient : JO' = R x JO   (jointOrient 는 항상 XYZ)
      jointOrient -> rotate : R'  = R x JO   (조인트의 rotateOrder 로)
    rotateAxis 는 앞에 곱해지므로 그대로 둔다. 분해 결과는 _closest_equivalent 참고.

    반환 : 메시지 목록 (잠김 · 연결로 건너뛴 조인트)
    """
    from maya.api import OpenMaya as om

    messages = []
    to_jo = attr_sum == "jointOrient"
    for jnt in joints:
        if cmds.nodeType(jnt) != "joint":
            messages.append("[Warning] {0}: not a joint - skipped.".format(jnt))
            continue
        blocked = _blocked_channels(jnt, "rotate") + _blocked_channels(jnt, "jointOrient")
        if blocked:
            messages.append("[Warning] {0}: {1} locked or connected - skipped.".format(
                jnt, ", ".join(blocked)))
            continue

        rot = cmds.getAttr(jnt + ".rotate")[0]
        jo = cmds.getAttr(jnt + ".jointOrient")[0]
        rot_order = cmds.getAttr(jnt + ".rotateOrder")

        r_mat = om.MEulerRotation([math.radians(v) for v in rot], rot_order).asMatrix()
        jo_mat = om.MEulerRotation([math.radians(v) for v in jo],
                                   om.MEulerRotation.kXYZ).asMatrix()
        out_order = om.MEulerRotation.kXYZ if to_jo else rot_order
        mat = r_mat * jo_mat
        naive = om.MEulerRotation([math.radians(a + b) for a, b in zip(rot, jo)], out_order)
        euler = _closest_equivalent(om.MEulerRotation.decompose(mat, out_order), naive, mat)

        cmds.setAttr(jnt + "." + attr_zero, 0, 0, 0)
        cmds.setAttr(jnt + "." + attr_sum, *[math.degrees(v) for v in (euler.x, euler.y, euler.z)])
    return messages


def set_joint_orient(joints, axis_idx, degree):
    """MEL JUN_cmd_set_jntOri - 체인을 역순 unparent -> jointOrient 설정 -> 정순 reparent.

    axis_idx : 1-base (1=X, 2=Y, 3=Z)
    joints   : 리스트 순서가 root -> ... -> end 인 체인이어야 함.
    """
    axis = ["X", "Y", "Z"][axis_idx - 1]
    n = len(joints)

    # 끝에서부터 unparent 후 orient 설정
    for i in range(n):
        j = joints[n - i - 1]
        try:
            cmds.parent(j, world=True)
        except Exception:
            pass
        cmds.setAttr("{0}.jointOrient{1}".format(j, axis), degree)

    # 다시 정순으로 reparent
    for i in range(n - 1):
        try:
            cmds.parent(joints[i + 1], joints[i])
        except Exception:
            pass
