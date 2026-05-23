import maya.cmds as cmds;
import maya.mel as mel
import copy, os
from functools import partial


def JUN_separate_crv(*args , **kwargs):
    tsl_main             = kwargs.get("tsl_jointTool_main")
    lst_crv = tsl_main.get_all_item()

    for crv_single in lst_crv:
        for shape in cmds.listRelatives(crv_single, c=1, type='shape', fullPath = True):
            newTrans = cmds.createNode('transform', n='hairCrv')
            cmds.parent(shape, newTrans, s=1)


def JUN_remove_crv_by_len(*args , **kwargs):
    tsl_main             = kwargs.get("tsl_jointTool_main")
    tfg_max_crv_len      = kwargs.get("tfg_max_crv_len")

    lst_crv = tsl_main.get_all_item()
    maxLen = float(tfg_max_crv_len.get_val())
    crv_short = []

    for crv in lst_crv:
        length = cmds.arclen(crv)
        if length <= maxLen:
            crv_short.append(crv)
    cmds.delete(crv_short)

def JUN_rebuild_crv(*args , **kwargs):
    tsl_main             = kwargs.get("tsl_jointTool_main")
    tfg_for_every_n_cm   = kwargs.get("tfg_for_every_n_cm")
    tfg_max_jnts         = kwargs.get("tfg_max_jnts")

    
    interval = float(tfg_for_every_n_cm.get_val())
    max_jnts = float(tfg_max_jnts.get_val())
    lst_crv = tsl_main.get_all_item()

    rebuild_curves_by_length(lst_crv, interval, max_jnts-1)

def rebuild_curves_by_length(curves, interval, max_spans = 4):

    for crv in curves:

        # curve length 측정
        length = cmds.arclen(crv)

        spans = max(1, int(length / interval))
        spans = min(spans, max_spans)

        # rebuild
        cmds.rebuildCurve(
            crv,
            ch=False,
            rpo=True,
            rt=0,
            end=1,
            kr=0,
            kcp=False,
            kep=True,
            kt=False,
            s=spans,
            d=3
        )

        print(f"{crv} | length={length:.2f} | spans={spans}")

def JUN_reverse_joint(*args , **kwargs):
    tsl_main             = kwargs.get("tsl_jointTool_main")
    cbg_remove_origin    = kwargs.get("cbg_remove_origin")

    remove_origin =  cbg_remove_origin.get_val()

    lst_joint_root = tsl_main.get_all_item()

    joints_new = []

    for jnt_root in lst_joint_root:
        joints_new = reverse_joint_chain(jnt_root)

        if remove_origin:
            cmds.delete(jnt_root)
            search_replace_names("_rev", "", joints_new)
    

def search_replace_names(search_str, replace_str, objs_main = None):
    # Get the current selection
    if objs_main is None:
        objs_main = cmds.ls(sl=True)
    
    # Iterate through each object in objs_main
    for obj in objs_main:
        if search_str in obj:
            # Generate the new name using Python's string replace
            new_name = obj.replace(search_str, replace_str)
            # Apply the rename
            cmds.rename(obj, new_name)

def reverse_joint_chain(root_joint):

    # =========================
    # joint chain 수집
    # =========================

    joints = cmds.listRelatives(
        root_joint,
        ad=True,
        type="joint"
    ) or []

    joints.append(root_joint)

    # root -> end 순서로 정렬
    joints.reverse()

    # 예:
    # [joint_01, joint_02, joint_03, joint_04]

    # =========================
    # 위치 저장
    # =========================

    joint_data = []

    for jnt in joints:

        pos = cmds.xform(
            jnt,
            q=True,
            ws=True,
            t=True
        )

        joint_data.append({
            "name": jnt,
            "pos": pos
        })

    # =========================
    # 역순 생성
    # =========================

    reversed_data = list(reversed(joint_data))

    new_joints = []

    cmds.select(clear=True)

    for data in reversed_data:

        new_name = f"{data['name']}_rev"

        jnt = cmds.joint(
            name=new_name,
            p=data["pos"]
        )

        new_joints.append(jnt)

    # =========================
    # orient 정리
    # =========================

    if len(new_joints) >= 2:

        cmds.joint(
            new_joints[0],
            e=True,
            oj="xyz",
            secondaryAxisOrient="zup",
            ch=True,
            zso=True
        )

    # 마지막 joint orient 제거
    cmds.setAttr(
        f"{new_joints[-1]}.jointOrientX",
        0
    )

    cmds.setAttr(
        f"{new_joints[-1]}.jointOrientY",
        0
    )

    cmds.setAttr(
        f"{new_joints[-1]}.jointOrientZ",
        0
    )

    print("Reverse chain created")

    return new_joints