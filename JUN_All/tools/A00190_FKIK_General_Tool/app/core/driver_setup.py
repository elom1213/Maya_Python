# -*- coding: utf-8 -*-
"""
driver_setup - FK/IK 매칭용 드라이버(pose object) 생성.

레거시 pin_to_surface / JUN_cage_FKIK_Gen / JUN_cmd_FKIK_gen_setup_triangle_pos_objs /
JUN_create_loc_for_given_objs / JUN_cmd_FKIK_gen_create_pos_objs_FKIK_Gen 를 이식했다.

UI(textScrollList) 의존을 제거: 소스/컨트롤은 list[list[str]](limb 4개) 로 받고,
생성 결과는 list[list[str]] 로 돌려준다. UI 가 위젯에 채운다.

pin_to_surface 는 pymel 을 그대로 사용한다(Maya 2023 동봉 노드만 사용).
"""

import maya.cmds as cmds
import pymel.core as pm

from .matching import match_two_objects
from .selection_utils import world_position, average_position, ensure_parent


GRP_POS_OBJS = "JUN_posObjs_grp"

TRI_MESH_NAMES = [
    "CH_l_triArm_sfc",
    "CH_r_triArm_sfc",
    "CH_l_triLeg_sfc",
    "CH_r_triLeg_sfc",   # 레거시의 트레일링 콤마 오타("CH_r_triLeg_sfc,") 수정
]


# ----------------------------------------------------------------------
# NURBS surface pin (follicle 유사) — pymel
# ----------------------------------------------------------------------

def pin_to_surface(oNurbs, sourceObj=None, uPos=0.5, vPos=0.5):
    """NURBS 표면에 위치+방향이 따라붙는 locator 를 만든다. (구 pin_to_surface, pymel)"""

    if type(oNurbs) == str and pm.objExists(oNurbs):
        oNurbs = pm.PyNode(oNurbs)
    if type(oNurbs) == pm.nodetypes.Transform:
        pass
    elif type(oNurbs) == pm.nodetypes.NurbsSurface:
        oNurbs = oNurbs.getTransform()
    elif type(oNurbs) == list:
        pm.warning('Specify a NurbsSurface, not a list.')
        return False
    else:
        pm.warning('Invalid surface object specified.')
        return False

    pointOnSurface = pm.createNode('pointOnSurfaceInfo')
    oNurbs.getShape().worldSpace.connect(pointOnSurface.inputSurface)
    paramLengthU = oNurbs.getShape().minMaxRangeU.get()
    paramLengthV = oNurbs.getShape().minMaxRangeV.get()

    if sourceObj:
        if isinstance(sourceObj, str) and pm.objExists(sourceObj):
            sourceObj = pm.PyNode(sourceObj)
        if isinstance(sourceObj, pm.nodetypes.Transform):
            pass
        elif isinstance(sourceObj, pm.nodetypes.Shape):
            sourceObj = sourceObj.getTransform()
        elif type(sourceObj) == list:
            pm.warning('sourceObj should be a transform, not a list.')
            return False
        else:
            pm.warning('Invalid sourceObj specified.')
            return False
        oNode = pm.createNode('closestPointOnSurface', n='ZZZTEMP')
        oNurbs.worldSpace.connect(oNode.inputSurface, force=True)
        oNode.inPosition.set(sourceObj.getTranslation(space='world'))
        uPos = oNode.parameterU.get()
        vPos = oNode.parameterV.get()
        pm.delete(oNode)

    pName = '{}_foll#'.format(oNurbs.name())
    result = pm.spaceLocator(n=pName).getShape()
    result.addAttr('parameterU', at='double', keyable=True, dv=uPos)
    result.addAttr('parameterV', at='double', keyable=True, dv=vPos)
    result.parameterU.setMin(paramLengthU[0])
    result.parameterV.setMin(paramLengthV[0])
    result.parameterU.setMax(paramLengthU[1])
    result.parameterV.setMax(paramLengthV[1])
    result.parameterU.connect(pointOnSurface.parameterU)
    result.parameterV.connect(pointOnSurface.parameterV)

    mtx = pm.createNode('fourByFourMatrix')
    outMatrix = pm.createNode('decomposeMatrix')
    mtx.output.connect(outMatrix.inputMatrix)
    outMatrix.outputTranslate.connect(result.getTransform().translate)
    outMatrix.outputRotate.connect(result.getTransform().rotate)

    pointOnSurface.normalizedTangentUX.connect(mtx.in00)
    pointOnSurface.normalizedTangentUY.connect(mtx.in01)
    pointOnSurface.normalizedTangentUZ.connect(mtx.in02)
    mtx.in03.set(0)

    pointOnSurface.normalizedNormalX.connect(mtx.in10)
    pointOnSurface.normalizedNormalY.connect(mtx.in11)
    pointOnSurface.normalizedNormalZ.connect(mtx.in12)
    mtx.in13.set(0)

    pointOnSurface.normalizedTangentVX.connect(mtx.in20)
    pointOnSurface.normalizedTangentVY.connect(mtx.in21)
    pointOnSurface.normalizedTangentVZ.connect(mtx.in22)
    mtx.in23.set(0)

    pointOnSurface.positionX.connect(mtx.in30)
    pointOnSurface.positionY.connect(mtx.in31)
    pointOnSurface.positionZ.connect(mtx.in32)
    mtx.in33.set(1)

    return result


# ----------------------------------------------------------------------
# 드라이버 묶음(cage)
# ----------------------------------------------------------------------

class Cage:
    """베이크용 드라이버 보관. limb 별 [pole, wrist/ankle, (toe)]. (구 JUN_cage_FKIK_Gen)"""

    def __init__(self):
        self.arm_left = ["Empty", "Empty"]
        self.arm_right = ["Empty", "Empty"]
        self.leg_left = ["Empty", "Empty", "Empty"]
        self.leg_right = ["Empty", "Empty", "Empty"]
        self.lst_drv_all = [self.arm_left, self.arm_right, self.leg_left, self.leg_right]

    def set_drv_pole_arm_l(self, obj): self.arm_left[0] = obj
    def set_drv_pole_arm_r(self, obj): self.arm_right[0] = obj
    def set_drv_pole_leg_l(self, obj): self.leg_left[0] = obj
    def set_drv_pole_leg_r(self, obj): self.leg_right[0] = obj

    def set_drv_wrist_l(self, obj): self.arm_left[1] = obj
    def set_drv_wrist_r(self, obj): self.arm_right[1] = obj
    def set_drv_ankle_l(self, obj): self.leg_left[1] = obj
    def set_drv_ankle_r(self, obj): self.leg_right[1] = obj

    def set_drv_toe_l(self, obj): self.leg_left[2] = obj
    def set_drv_toe_r(self, obj): self.leg_right[2] = obj

    def print_lst_all(self):
        print("cage arm_left  : " + str(self.arm_left))
        print("cage arm_right : " + str(self.arm_right))
        print("cage leg_left  : " + str(self.leg_left))
        print("cage leg_right : " + str(self.leg_right))


# ----------------------------------------------------------------------
# locator 드라이버 생성
# ----------------------------------------------------------------------

def create_loc_for_objs(objs):
    """각 obj 위치/회전에 맞춘 spaceLocator 들을 만든다. (구 JUN_create_loc_for_given_objs)"""
    locs = []
    for obj in objs:
        loc = cmds.spaceLocator()
        match_two_objects([obj], loc, True, True, True, True)
        locs.append(loc[0])
    return locs


def _ensure_grp():
    if not cmds.objExists(GRP_POS_OBJS):
        cmds.group(em=True, name=GRP_POS_OBJS)
    return cmds.listRelatives(GRP_POS_OBJS, children=True, fullPath=False) or []


# ----------------------------------------------------------------------
# 삼각형 surface 드라이버 (pole 위치)
# ----------------------------------------------------------------------

def setup_triangle_drivers(fk_source_lists, cage):
    """limb 별 FK 소스 컨트롤 3개로 NURBS 삼각형을 만들고, 표면에 핀한 locator 를 pole 드라이버로 만든다.
    (구 JUN_cmd_FKIK_gen_setup_triangle_pos_objs)

    Args:
        fk_source_lists: limb 4개 [arm_l, arm_r, leg_l, leg_r] 각 FK 소스 컨트롤 list[str].
        cage: Cage — pole 드라이버가 채워진다.
    """
    grp_children = _ensure_grp()
    drivers = []

    for i in range(4):
        objs_ctls = fk_source_lists[i] if i < len(fk_source_lists) else None

        if not objs_ctls:
            print(TRI_MESH_NAMES[i] + " : Pass")
            continue

        if TRI_MESH_NAMES[i] in grp_children:
            print("Remove existing : " + TRI_MESH_NAMES[i])
            cmds.delete(TRI_MESH_NAMES[i])

        tri_nurbs = cmds.nurbsPlane(degree=1)
        cmds.DeleteHistory(tri_nurbs)
        tri_name = cmds.rename(tri_nurbs[0], TRI_MESH_NAMES[i])
        ensure_parent(tri_name, GRP_POS_OBJS)

        lst_pos_for_tri = []
        for j in range(3):
            decom = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(objs_ctls[j] + ".worldMatrix", decom + ".inputMatrix")
            cmds.connectAttr(decom + ".outputTranslate", tri_name + ".controlPoints[{0}]".format(j))
            if j == 2:
                cmds.connectAttr(decom + ".outputTranslate", tri_name + ".controlPoints[{0}]".format(j + 1))
            lst_pos_for_tri.append(world_position(objs_ctls[j]))

        pos_avg = average_position(lst_pos_for_tri)
        loc_avg = cmds.spaceLocator()
        cmds.xform(loc_avg, translation=pos_avg)

        pin_shape = str(pin_to_surface(pm.PyNode(tri_name), sourceObj=loc_avg[0]))
        pin_xform = cmds.listRelatives(pin_shape, parent=True, fullPath=False)

        ensure_parent(loc_avg, pin_xform[0])
        ensure_parent(pin_xform[0], GRP_POS_OBJS)
        loc_avg[0] = cmds.rename(loc_avg[0], pin_xform[0] + "_tgt")
        match_two_objects(pin_xform, [loc_avg[0]], True, True, True, True)

        drivers.append(loc_avg[0])

    funcs = [cage.set_drv_pole_arm_l, cage.set_drv_pole_arm_r,
             cage.set_drv_pole_leg_l, cage.set_drv_pole_leg_r]
    for i, func in enumerate(funcs):
        try:
            func(drivers[i])
        except Exception:
            continue

    cage.print_lst_all()


# ----------------------------------------------------------------------
# FK <-> IK 전환 드라이버
# ----------------------------------------------------------------------

def create_switch_drivers(ik_source_lists, fk_ctl_lists, ik_ctl_lists, cage):
    """FK<->IK 전환용 드라이버 locator 들을 생성한다. (구 JUN_cmd_FKIK_gen_create_pos_objs_FKIK_Gen)

    - IK->FK: 각 IK 소스 위치에 locator 생성, 회전을 FK 컨트롤에 맞추고 IK 소스에 parentConstraint.
    - FK->IK: wrist/ankle(FK idx2, IK idx1), toe(다리만, FK idx3, IK idx1) 드라이버 생성.

    Returns:
        (fk_pose_results, ik_pose_results): 각 limb 4개의 생성 결과 list[list[str]].
        fk_pose_results = IK->FK 드라이버, ik_pose_results = cage 의 pole/wrist/ankle/toe 드라이버.
    """
    grp_children = _ensure_grp()

    fk_pose_results = [[], [], [], []]

    # --- IK -> FK 드라이버 ---
    for i in range(4):
        ctl_fk = fk_ctl_lists[i] if i < len(fk_ctl_lists) else None
        source_ik = ik_source_lists[i] if i < len(ik_source_lists) else None

        if not source_ik:
            print("source IK empty, pass limb index " + str(i))
            continue

        locs = create_loc_for_objs(source_ik)

        if ctl_fk:
            # 회전만 FK 컨트롤(앞 3개)에 맞춘다.
            match_two_objects(ctl_fk[:3], locs, True, True, False, True)

        for j in range(len(locs)):
            name_drv = source_ik[j] + "_drv"
            if name_drv in grp_children:
                print("Remove existing : " + name_drv)
                cmds.delete(name_drv)
            locs[j] = cmds.rename(locs[j], name_drv)
            ensure_parent(locs[j], GRP_POS_OBJS)
            cmds.parentConstraint(source_ik[j], locs[j], mo=True)

        fk_pose_results[i] = locs

    # --- FK -> IK 드라이버 : wrist / ankle ---
    idx_fk_wrist_ankle = 2
    idx_ik_wrist_ankle = 1
    locs_wrist_ankle = []
    for i in range(4):
        ctl_fk_all = fk_ctl_lists[i] if i < len(fk_ctl_lists) else None
        ctl_ik_all = ik_ctl_lists[i] if i < len(ik_ctl_lists) else None

        if not ctl_fk_all:
            print("FK ctl empty, pass limb index " + str(i))
            continue

        name_drv = str(ctl_fk_all[idx_fk_wrist_ankle]) + "_drv"
        locs = create_loc_for_objs([ctl_fk_all[idx_fk_wrist_ankle]])

        if ctl_ik_all:
            match_two_objects([ctl_ik_all[idx_ik_wrist_ankle]], locs, True, True, False, True)

        if name_drv in grp_children:
            print("Remove existing : " + name_drv)
            cmds.delete(name_drv)
        locs[0] = cmds.rename(locs[0], name_drv)
        ensure_parent(locs[0], GRP_POS_OBJS)
        cmds.parentConstraint(ctl_fk_all[idx_fk_wrist_ankle], locs[0], mo=True)

        locs_wrist_ankle.append(locs[0])

    funcs = [cage.set_drv_wrist_l, cage.set_drv_wrist_r,
             cage.set_drv_ankle_l, cage.set_drv_ankle_r]
    for i, func in enumerate(funcs):
        try:
            func(locs_wrist_ankle[i])
        except Exception:
            continue

    # --- FK -> IK 드라이버 : toe (다리만) ---
    idx_fk_toe = 3
    idx_ik_toe = 1
    locs_toe = []
    for i in range(2, 4):
        ctl_fk_leg = fk_ctl_lists[i] if i < len(fk_ctl_lists) else None
        ctl_ik_leg = ik_ctl_lists[i] if i < len(ik_ctl_lists) else None

        if not ctl_fk_leg:
            print("FK ctl(leg) empty, pass limb index " + str(i))
            continue

        name_drv = str(ctl_fk_leg[idx_fk_toe]) + "_drv"
        locs = create_loc_for_objs([ctl_fk_leg[idx_fk_toe]])

        if ctl_ik_leg:
            match_two_objects([ctl_ik_leg[idx_ik_toe]], locs, True, True, False, True)

        if name_drv in grp_children:
            print("Remove existing : " + name_drv)
            cmds.delete(name_drv)
        locs[0] = cmds.rename(locs[0], name_drv)
        ensure_parent(locs[0], GRP_POS_OBJS)
        cmds.parentConstraint(ctl_fk_leg[idx_fk_toe], locs[0], mo=True)

        locs_toe.append(locs[0])

    funcs = [cage.set_drv_toe_l, cage.set_drv_toe_r]
    for i, func in enumerate(funcs):
        try:
            func(locs_toe[i])
        except Exception:
            continue

    cage.print_lst_all()

    ik_pose_results = [list(cage.lst_drv_all[i]) for i in range(4)]
    return fk_pose_results, ik_pose_results
