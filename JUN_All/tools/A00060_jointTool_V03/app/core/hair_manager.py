# -*- coding: utf-8 -*-
# Hair 탭 로직 - A00060_jointTool/utility.py 이식.
# 위젯(tsl/tfg/cbg) 의존을 제거하고 평범한 인자(list/float/bool)를 받는다.

import copy

import maya.cmds as cmds


# ==================================================================
# Sub Tool : Curve
# ==================================================================

def separate_curves(curves):
    """A00060 JUN_separate_crv - 각 커브 shape 를 개별 transform(hairCrv)으로 분리."""
    for crv in curves:
        for shape in cmds.listRelatives(crv, c=1, type='shape', fullPath=True) or []:
            new_trans = cmds.createNode('transform', n='hairCrv')
            cmds.parent(shape, new_trans, s=1)


def remove_curves_by_length(curves, max_len):
    """A00060 JUN_remove_crv_by_len - 길이가 max_len 이하인 커브 삭제."""
    short = [crv for crv in curves if cmds.arclen(crv) <= max_len]
    if short:
        cmds.delete(short)
    return short


def rebuild_curves_by_interval(curves, interval, max_jnts):
    """A00060 JUN_rebuild_crv - 길이/간격 기반으로 span 산정해 rebuild.
    max_jnts 는 최대 joint 수 -> 최대 span = max_jnts - 1."""
    _rebuild_curves_by_length(curves, interval, max_jnts - 1)


def _rebuild_curves_by_length(curves, interval, max_spans=4):
    """A00060 rebuild_curves_by_length."""
    for crv in curves:
        length = cmds.arclen(crv)
        spans = max(1, int(length / interval))
        spans = min(spans, int(max_spans))
        cmds.rebuildCurve(
            crv, ch=False, rpo=True, rt=0, end=1,
            kr=0, kcp=False, kep=True, kt=False, s=spans, d=3
        )
        print("{0} | length={1:.2f} | spans={2}".format(crv, length, spans))


# ==================================================================
# Tool : Edit
# ==================================================================

def reverse_joints(roots, remove_origin):
    """A00060 JUN_reverse_joint - root joint 체인들을 역순으로 재생성."""
    for root in roots:
        new_joints = reverse_joint_chain(root)
        if remove_origin:
            cmds.delete(root)
            _search_replace_names("_rev", "", new_joints)


def _search_replace_names(search_str, replace_str, objs):
    """A00060 search_replace_names."""
    for obj in objs:
        if search_str in obj:
            cmds.rename(obj, obj.replace(search_str, replace_str))


def reverse_joint_chain(root_joint):
    """A00060 reverse_joint_chain - 위치/radius 유지하며 역순 체인 생성."""
    parent_root_jnt = cmds.listRelatives(root_joint, parent=True, fullPath=True)
    joints = cmds.listRelatives(root_joint, ad=True, type="joint") or []
    joints.append(root_joint)
    joints.reverse()

    joint_data = []
    for jnt in joints:
        pos = cmds.xform(jnt, q=True, ws=True, t=True)
        rad = cmds.getAttr(jnt + '.radius')
        joint_data.append({"name": jnt, "pos": pos, "radius": float(rad)})

    reversed_data = copy.deepcopy(list(reversed(joint_data)))

    new_joints = []
    cmds.select(clear=True)

    for i in range(0, len(reversed_data)):
        reversed_data[i]["radius"] = joint_data[i]["radius"]
        reversed_data[i]["name"] = joint_data[i]["name"]

    for data in reversed_data:
        new_name = "{0}_rev".format(data['name'])
        jnt = cmds.joint(name=new_name, p=data["pos"])
        cmds.setAttr(jnt + ".radius", data["radius"])
        new_joints.append(jnt)

    if parent_root_jnt is not None:
        cmds.parent(new_joints[0], parent_root_jnt)

    if len(new_joints) >= 2:
        cmds.joint(new_joints[0], e=True, oj="xyz",
                   secondaryAxisOrient="zup", ch=True, zso=True)

    # 마지막 joint orient 제거
    cmds.setAttr("{0}.jointOrientX".format(new_joints[-1]), 0)
    cmds.setAttr("{0}.jointOrientY".format(new_joints[-1]), 0)
    cmds.setAttr("{0}.jointOrientZ".format(new_joints[-1]), 0)

    print("Reverse chain created")
    return new_joints


def unused_joints(joints):
    """A00060 get_unused_joints - skinCluster 에 쓰이지 않는 joint 목록 반환."""
    weighted = set()
    for skin in cmds.ls(type="skinCluster") or []:
        influences = cmds.skinCluster(skin, q=True, weightedInfluence=True) or []
        weighted.update(influences)
    return [jnt for jnt in joints if jnt not in weighted]
