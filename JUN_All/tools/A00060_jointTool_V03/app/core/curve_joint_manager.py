# -*- coding: utf-8 -*-
# Curve 탭 로직 - MEL JointTool V05.03 "joint to Crv" / "Clusters" 포팅.
#   JUN_make_jnt_toCurvePoint / make_jnts_toCurvePoint /
#   JUN_cmd_create_joints_toCrv / JUN_cmd_create_clusters_toCrv
#
# joint 는 항상 커브 포인트의 world-space 절대 위치에 생성한다(오브젝트/커브가 어떤
# 계층 아래에 있어도 정확히 배치). 예전의 "pointPosition + 커브 translation" 좌표 보정은
# 이중 가산 버그라 제거했다.

import maya.cmds as cmds


# point type enum (MEL JUN_get_pointType_from_vct 의 table_conType 과 동일)
POINT_TYPE_CV_OMIT = "controlPointsOmit"
POINT_TYPE_CV = "controlPoints"
POINT_TYPE_EP = "ep"


def cv_indices_of_curve(curve):
    """MEL get_list_numCVPoints_fromCurve: spans + 3 개의 인덱스 리스트."""
    num_cv = cmds.getAttr(curve + ".spans") + 3
    return list(range(num_cv))


def _joint_at_curve_point(curve, cp_num, point_type):
    """MEL JUN_make_jnt_toCurvePoint - 커브 포인트의 '월드' 위치에 joint 생성.

    pointPosition 은 이미 world-space 절대 좌표(부모 계층의 이동/회전/스케일까지 반영)를
    반환하므로 그대로 쓴다. (기존엔 여기에 커브의 world translation 을 한 번 더 더해서,
    커브가 원점이 아니거나 계층 아래에 있으면 위치가 두 배로 어긋났다.) 생성 직후
    xform(ws) 로 월드 위치를 확정해, joint 가 부모 체인 아래로 들어가도 정확히 배치한다."""
    pos = cmds.pointPosition("{0}.{1}[{2}]".format(curve, point_type, cp_num))
    jnt = cmds.joint(p=pos)
    cmds.xform(jnt, ws=True, translation=pos)
    cmds.joint(jnt, edit=True, zso=True, oj="xyz", sao="yup")
    return jnt


def joints_along_curve(curve, point_type, indices):
    """MEL make_jnts_toCurvePoint - 인덱스 순서대로 joint 체인 생성 후 끝 정렬."""
    prev = None
    for idx in indices:
        cur = _joint_at_curve_point(curve, idx, point_type)
        if prev is not None:
            cmds.joint(prev, edit=True, zso=True, oj="xyz", sao="yup")
        prev = cur
    # 마지막 joint orient -> world (선택된 joint 대상)
    if cmds.ls(selection=True):
        cmds.joint(edit=True, oj="none", ch=True, zso=True)
    cmds.select(clear=True)


def joints_to_curves(curves, point_type):
    """MEL JUN_cmd_create_joints_toCrv - 선택 nurbsCurve 들에 joint 생성."""
    cmds.select(clear=True)
    for obj in curves:
        shapes = cmds.listRelatives(obj) or []
        if not shapes or cmds.nodeType(shapes[0]) != "nurbsCurve":
            cmds.warning("{0} is not a nurbsCurve".format(obj))
            continue

        indices = cv_indices_of_curve(obj)
        last = len(indices) - 1

        pt = point_type
        if pt == POINT_TYPE_CV_OMIT:
            # CV 사용하되 [1], [-2] 인덱스 생략
            pt = POINT_TYPE_CV
            indices = [i for i in indices if i not in (1, last - 1)]
        elif pt == POINT_TYPE_EP:
            # edit point: cv 인덱스 리스트에서 끝 2개 제거 = ep 개수
            indices = [i for i in indices if i not in (last, last - 1)]

        joints_along_curve(obj, pt, indices)


def clusters_to_curves(curves):
    """MEL JUN_cmd_create_clusters_toCrv - 커브 CV 마다 cluster 생성."""
    for obj in curves:
        cp_size = cmds.getAttr(obj + ".spans") + 1
        # MEL: for(i; i <= cp_size + 1; i++)  -> 0 .. cp_size+1 (inclusive)
        for i in range(cp_size + 2):
            cmds.select("{0}.controlPoints[{1}]".format(obj, i))
            cmds.cluster()
            cmds.select(clear=True)
