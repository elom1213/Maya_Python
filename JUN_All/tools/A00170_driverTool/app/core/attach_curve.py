# -*- coding: utf-8 -*-
"""
attach_curve - 주어진 커브에 오브젝트들을 '가장 가까운 지점'으로 라이브 어태치한다.

ref/ref_01.mel(attachDriverOnCurve, by Doosup Jung)의 '일정 간격으로 새 로케이터 어태치'
대신, 탭의 TSL 에 나열된 **기존 오브젝트들**을 각자 커브에서 가장 가까운 파라미터 지점에 붙인다.
빌드 후 커브가 변형되면 오브젝트도 그 지점을 따라간다.

각 오브젝트마다:
  - nearestPointOnCurve 로 빌드 시점의 최근접 파라미터를 구한다(임시 노드, 사용 후 삭제).
  - pointOnCurveInfo(parameter=그 값)로 커브 위 한 점을 라이브 추적한다.
  - fourByFourMatrix -> multMatrix(* parentInverseMatrix) -> decomposeMatrix 로
    오브젝트의 translate(옵션: rotate)를 구동한다.

orient 옵션이 켜지면 커브 접선(tangent)을 aim 축에 정렬한다. 업벡터는 월드 +Y 를 시드로
side = T x up, up' = side x T 로 직교 프레임을 만든다(ref 의 별도 normal 커브 없이 자족).
접선이 월드 업과 평행한(수직) 커브에서는 프레임이 무너질 수 있어 그런 경우 orient 를 끄는 게 좋다.
"""

import maya.cmds as cmds

# Aim Axis 옵션(오브젝트의 로컬 어느 축을 커브 접선에 맞출지). ref 의 +X / -X 와 동일.
AIM_AXES = ("+X", "-X")

# 직교 프레임의 업벡터 시드(월드 +Y).
_WORLD_UP = (0.0, 1.0, 0.0)


def _shape_of_curve(curve):
    """transform 이면 그 nurbsCurve shape 를, 이미 shape 면 자신을 반환. 없으면 None."""
    if cmds.objExists(curve) and cmds.objectType(curve, isType="nurbsCurve"):
        return curve
    shapes = cmds.listRelatives(curve, shapes=True, type="nurbsCurve",
                                fullPath=True) or []
    return shapes[0] if shapes else None


def _closest_parameter(curve_shape, world_pos):
    """nearestPointOnCurve 임시 노드로 world_pos 에 대한 최근접 파라미터를 구해 반환."""
    npoc = cmds.createNode("nearestPointOnCurve")
    try:
        cmds.connectAttr(curve_shape + ".worldSpace[0]",
                         npoc + ".inputCurve", force=True)
        cmds.setAttr(npoc + ".inPositionX", world_pos[0])
        cmds.setAttr(npoc + ".inPositionY", world_pos[1])
        cmds.setAttr(npoc + ".inPositionZ", world_pos[2])
        return cmds.getAttr(npoc + ".parameter")
    finally:
        cmds.delete(npoc)


def _orient_frame_outputs(poci, aim_axis):
    """커브 접선 기반 직교 프레임의 (X행, Y행, Z행) 소스 어트리뷰트 3쌍을 만들어 반환.

    각 원소는 (.x, .y, .z) 성분 어트리뷰트 튜플. fourByFourMatrix in0*/in1*/in2* 에 연결한다.
    +X: X=+T, Y=+up', Z=+side / -X: X=-T, Z=-side (handedness 유지).
    """
    # side = T x worldUp,  up' = side x T (둘 다 normalizeOutput).
    vp_side = cmds.createNode("vectorProduct")
    cmds.setAttr(vp_side + ".operation", 2)          # cross product
    cmds.setAttr(vp_side + ".normalizeOutput", 1)
    cmds.connectAttr(poci + ".normalizedTangent", vp_side + ".input1",
                     force=True)
    cmds.setAttr(vp_side + ".input2", *_WORLD_UP, type="double3")

    vp_up = cmds.createNode("vectorProduct")
    cmds.setAttr(vp_up + ".operation", 2)
    cmds.setAttr(vp_up + ".normalizeOutput", 1)
    cmds.connectAttr(vp_side + ".output", vp_up + ".input1", force=True)
    cmds.connectAttr(poci + ".normalizedTangent", vp_up + ".input2",
                     force=True)

    tan_attr = (poci + ".normalizedTangentX",
                poci + ".normalizedTangentY",
                poci + ".normalizedTangentZ")
    up_attr = (vp_up + ".outputX", vp_up + ".outputY", vp_up + ".outputZ")
    side_attr = (vp_side + ".outputX", vp_side + ".outputY",
                 vp_side + ".outputZ")

    if aim_axis == "-X":
        tan_attr = _negate_vector(poci, tan_attr, "negT")
        side_attr = _negate_vector(poci, side_attr, "negSide")

    return tan_attr, up_attr, side_attr


def _negate_vector(node_hint, src_attrs, name):
    """multiplyDivide(input2 = -1)로 벡터를 반전해 (.x,.y,.z) 출력 어트리뷰트를 반환."""
    neg = cmds.createNode("multiplyDivide", n="{0}_{1}".format(node_hint, name))
    cmds.setAttr(neg + ".input2", -1.0, -1.0, -1.0, type="double3")
    for comp, src in zip(("input1X", "input1Y", "input1Z"), src_attrs):
        cmds.connectAttr(src, "{0}.{1}".format(neg, comp), force=True)
    return neg + ".outputX", neg + ".outputY", neg + ".outputZ"


def _attach_one(curve_shape, obj, orient, aim_axis):
    """오브젝트 하나를 커브 최근접 지점에 라이브 어태치한다(노드 네트워크 구성)."""
    world_pos = cmds.xform(obj, query=True, worldSpace=True, rotatePivot=True)
    param = _closest_parameter(curve_shape, world_pos)

    poci = cmds.createNode("pointOnCurveInfo", n="{0}_atc_POCI".format(obj))
    cmds.connectAttr(curve_shape + ".worldSpace[0]", poci + ".inputCurve",
                     force=True)
    cmds.setAttr(poci + ".turnOnPercentage", 0)
    cmds.setAttr(poci + ".parameter", param)

    fbf = cmds.createNode("fourByFourMatrix", n="{0}_atc_FBF".format(obj))
    cmds.connectAttr(poci + ".positionX", fbf + ".in30", force=True)
    cmds.connectAttr(poci + ".positionY", fbf + ".in31", force=True)
    cmds.connectAttr(poci + ".positionZ", fbf + ".in32", force=True)

    if orient:
        x_row, y_row, z_row = _orient_frame_outputs(poci, aim_axis)
        for col, src in zip(("in00", "in01", "in02"), x_row):
            cmds.connectAttr(src, "{0}.{1}".format(fbf, col), force=True)
        for col, src in zip(("in10", "in11", "in12"), y_row):
            cmds.connectAttr(src, "{0}.{1}".format(fbf, col), force=True)
        for col, src in zip(("in20", "in21", "in22"), z_row):
            cmds.connectAttr(src, "{0}.{1}".format(fbf, col), force=True)

    mul = cmds.createNode("multMatrix", n="{0}_atc_MMX".format(obj))
    cmds.connectAttr(fbf + ".output", mul + ".matrixIn[0]", force=True)
    cmds.connectAttr(obj + ".parentInverseMatrix[0]", mul + ".matrixIn[1]",
                     force=True)

    dcp = cmds.createNode("decomposeMatrix", n="{0}_atc_DCM".format(obj))
    cmds.connectAttr(mul + ".matrixSum", dcp + ".inputMatrix", force=True)

    cmds.connectAttr(dcp + ".outputTranslate", obj + ".translate", force=True)
    if orient:
        cmds.connectAttr(dcp + ".outputRotate", obj + ".rotate", force=True)

    return param, poci


def build_attach_to_closest(curve, objects, orient=True, aim_axis="+X",
                            create_set=True):
    """objects 의 각 오브젝트를 curve 에서 가장 가까운 지점에 라이브 어태치한다.

    create_set 이 True 면 생성된 pointOnCurveInfo 노드들을 모두 담는 objectSet 을
    하나 만든다(이름 '<curve>_atcPOCI_SET', 이미 있으면 Maya 가 자동 넘버링).

    Returns (attached, failed, set_node):
      attached  = [(obj, parameter), ...]
      failed    = [(obj, reason), ...]
      set_node  = 생성한 세트 이름(미생성/멤버 없음이면 None)
    한 오브젝트가 실패해도 나머지는 계속 진행한다.
    """
    curve_shape = _shape_of_curve(curve)
    if curve_shape is None:
        raise ValueError("'{0}' is not a NURBS curve.".format(curve))
    if aim_axis not in AIM_AXES:
        aim_axis = "+X"

    attached = []
    failed = []
    pocis = []
    for obj in objects:
        if not cmds.objExists(obj):
            failed.append((obj, "not found in scene"))
            continue
        try:
            param, poci = _attach_one(curve_shape, obj, orient, aim_axis)
            attached.append((obj, param))
            pocis.append(poci)
        except Exception as exc:                       # noqa: BLE001
            failed.append((obj, str(exc)))

    set_node = None
    if create_set and pocis:
        # 세트 이름은 커브 transform 의 짧은 이름 기준(경로 구분자 제거).
        base = curve.split("|")[-1].split(":")[-1]
        set_node = cmds.sets(pocis, name="{0}_atcPOCI_SET".format(base))

    return attached, failed, set_node
