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


def joints_to_objs(objs, separate, fwd_axis, secd_axis, secd_ori):
    """MEL JUN_cmd_create_joints_toObj - 오브젝트마다 joint 생성, 축 옵션으로 orient.

    fwd_axis / secd_axis : 1-base (1=X, 2=Y, 3=Z)  (콤보 index + 1)
    secd_ori             : 1-base (1=+X,2=-X,3=+Y,4=-Y,5=+Z,6=-Z)
    separate             : True 면 각 joint 를 분리(루트), False 면 체인 연결
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
            cmds.select(clear=True)

    # 마지막 joint orient -> world
    if cmds.ls(selection=True):
        cmds.joint(edit=True, oj="none", ch=True, zso=True)
    cmds.select(clear=True)


def swap_rotate_orient(joints, attr_zero, attr_sum):
    """MEL JUN_cmd_joint_swap_rotate - attr_zero 를 0 으로, attr_sum 에 두 값을 합산.

    'joint orient -> rotate' : attr_zero="jointOrient", attr_sum="rotate"
    'rotate -> joint orient'  : attr_zero="rotate",      attr_sum="jointOrient"
    """
    for jnt in joints:
        zero_v = [cmds.getAttr("{0}.{1}{2}".format(jnt, attr_zero, ax)) for ax in "XYZ"]
        sum_v = [cmds.getAttr("{0}.{1}{2}".format(jnt, attr_sum, ax)) for ax in "XYZ"]

        for ax in "XYZ":
            cmds.setAttr("{0}.{1}{2}".format(jnt, attr_zero, ax), 0)

        for i, ax in enumerate("XYZ"):
            cmds.setAttr("{0}.{1}{2}".format(jnt, attr_sum, ax), zero_v[i] + sum_v[i])


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
