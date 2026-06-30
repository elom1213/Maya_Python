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

orient 옵션이 켜지면 커브 접선(tangent)을 aim 축에 정렬한다. 업벡터는 두 방식 중 하나로 정한다.

  - use_normal_curve=True (기본, ref_01.mel 원본대로):
    attachCrv 밑에 별도의 직선 'norCrv'(2점 커브)를 만들어 부모로 두고, 각 오브젝트의
    up(Y)/side(Z) 축을 norCrv 의 tangent/normal 에서 가져온다. 리거가 norCrv 를 회전/조정해
    체인 전체의 up/트위스트를 제어할 수 있다(원본 attachDriverOnCurve 의 노드 구성 그대로).
  - use_normal_curve=False:
    norCrv 없이 월드 +Y 를 시드로 side = T x up, up' = side x T 직교 프레임을 만든다(자족).
    접선이 월드 업과 평행한(수직) 커브에서는 프레임이 무너질 수 있어 그런 경우 orient 를 끈다.
"""

import maya.cmds as cmds

# Aim Axis 옵션(오브젝트의 로컬 어느 축을 커브 접선에 맞출지). ref 의 +X / -X 와 동일.
AIM_AXES = ("+X", "-X")

# Distribute 모드에서 생성할 드라이버 종류(ref 의 Locator / Null).
DRIVER_TYPES = ("locator", "null")

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


def _transform_of_curve(curve):
    """shape 가 주어지면 그 부모 transform 을, transform 이면 자신을 반환."""
    if cmds.objectType(curve, isType="nurbsCurve"):
        parents = cmds.listRelatives(curve, parent=True, fullPath=True) or []
        return parents[0] if parents else curve
    return curve


def _create_normal_curve(curve_transform, aim_axis, length, base_name):
    """ref 의 norCrv 를 만든다 : 원점→(0,±length,0) 2점 직선 커브.

    attachCrv 의 월드 transform(위치+회전)에 맞춘 뒤 그 자식으로 parent 한다(ref 동일).
    리거가 이 커브를 회전/조정하면 어태치된 오브젝트들의 up/트위스트가 따라간다.
    Returns (norcrv_transform, norcrv_shape).
    """
    sign = 1.0 if aim_axis == "+X" else -1.0          # ref: +X -> +len, -X -> -len
    crv = cmds.curve(degree=1,
                     point=[(0.0, 0.0, 0.0), (0.0, sign * length, 0.0)],
                     knot=[0, 1])
    crv = cmds.rename(crv, "{0}_norCrv".format(base_name))
    cmds.matchTransform(crv, curve_transform, position=True, rotation=True)
    crv = cmds.parent(crv, curve_transform)[0]
    shape = cmds.listRelatives(crv, shapes=True, type="nurbsCurve",
                               fullPath=True)[0]
    return crv, shape


def _orient_rows_from_normal_curve(attach_poci, norcrv_poci, aim_axis):
    """ref 원본 방식 : fourByFourMatrix 의 (X,Y,Z) 행 소스 어트리뷰트를 반환.

    X = attachCrv 접선, Y = norCrv 접선, Z = norCrv 노멀. -X 면 세 행을 모두 반전.
    """
    x_row = (attach_poci + ".normalizedTangentX",
             attach_poci + ".normalizedTangentY",
             attach_poci + ".normalizedTangentZ")
    y_row = (norcrv_poci + ".normalizedTangentX",
             norcrv_poci + ".normalizedTangentY",
             norcrv_poci + ".normalizedTangentZ")
    z_row = (norcrv_poci + ".normalizedNormalX",
             norcrv_poci + ".normalizedNormalY",
             norcrv_poci + ".normalizedNormalZ")

    if aim_axis == "-X":
        x_row = _negate_vector(attach_poci, x_row, "negT")
        y_row = _negate_vector(norcrv_poci, y_row, "negNorT")
        z_row = _negate_vector(norcrv_poci, z_row, "negNorN")

    return x_row, y_row, z_row


def _attach_one(curve_shape, obj, orient, aim_axis, norcrv_shape=None, param=None):
    """오브젝트 하나를 커브 위 한 지점에 라이브 어태치한다(노드 네트워크 구성).

    param 이 None 이면 오브젝트의 월드 위치에서 최근접 파라미터를 구해 쓰고(closest 모드),
    값이 주어지면 그 파라미터 지점에 그대로 붙인다(distribute 모드).
    norcrv_shape 가 주어지면(use_normal_curve) up/side 를 그 norCrv 에서 가져오고(ref 원본),
    없으면 커브 접선 기반 자족 직교 프레임을 쓴다.
    """
    if param is None:
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
        if norcrv_shape:
            # ref 원본 : norCrv 에 같은 곡선 shape 를 물린 별도 POCI 를 만들어 up/side 를 뽑는다.
            nor_poci = cmds.createNode("pointOnCurveInfo",
                                       n="{0}_nor_POCI".format(obj))
            cmds.connectAttr(norcrv_shape + ".worldSpace[0]",
                             nor_poci + ".inputCurve", force=True)
            cmds.setAttr(nor_poci + ".turnOnPercentage", 0)
            x_row, y_row, z_row = _orient_rows_from_normal_curve(
                poci, nor_poci, aim_axis)
        else:
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
                            use_normal_curve=True, normal_curve_length=1.0,
                            create_set=True):
    """objects 의 각 오브젝트를 curve 에서 가장 가까운 지점에 라이브 어태치한다.

    orient 가 True 이고 use_normal_curve 가 True 면(기본, ref 원본) attachCrv 밑에
    별도 'norCrv' 직선 커브 하나를 만들어 up/side 의 기준으로 쓴다. False 면 norCrv 없이
    커브 접선 기반 자족 프레임을 쓴다. normal_curve_length 는 생성할 norCrv 의 길이.

    create_set 이 True 면 생성된 pointOnCurveInfo 노드들을 모두 담는 objectSet 을
    하나 만든다(이름 '<curve>_atcPOCI_SET', 이미 있으면 Maya 가 자동 넘버링).

    Returns (attached, failed, set_node, norcrv):
      attached  = [(obj, parameter), ...]
      failed    = [(obj, reason), ...]
      set_node  = 생성한 세트 이름(미생성/멤버 없음이면 None)
      norcrv    = 생성한 norCrv transform 이름(미생성이면 None)
    한 오브젝트가 실패해도 나머지는 계속 진행한다.
    """
    curve_shape = _shape_of_curve(curve)
    if curve_shape is None:
        raise ValueError("'{0}' is not a NURBS curve.".format(curve))
    if aim_axis not in AIM_AXES:
        aim_axis = "+X"

    # 세트/노멀커브 이름 기준 : 커브 transform 의 짧은 이름(경로/네임스페이스 제거).
    base = _transform_of_curve(curve).split("|")[-1].split(":")[-1]

    # ref 원본 : orient + use_normal_curve 면 norCrv 를 한 개 만들어 공유한다.
    norcrv = None
    norcrv_shape = None
    if orient and use_normal_curve:
        norcrv, norcrv_shape = _create_normal_curve(
            _transform_of_curve(curve), aim_axis, normal_curve_length, base)

    attached = []
    failed = []
    pocis = []
    for obj in objects:
        if not cmds.objExists(obj):
            failed.append((obj, "not found in scene"))
            continue
        try:
            param, poci = _attach_one(curve_shape, obj, orient, aim_axis,
                                      norcrv_shape)
            attached.append((obj, param))
            pocis.append(poci)
        except Exception as exc:                       # noqa: BLE001
            failed.append((obj, str(exc)))

    set_node = None
    if create_set and pocis:
        set_node = cmds.sets(pocis, name="{0}_atcPOCI_SET".format(base))

    return attached, failed, set_node, norcrv


# ----------------------------------------------------------------------------
# Distribute 모드 : 커브에 새 드라이버 N 개를 균일 파라미터 간격으로 어태치한다.
# (ref_01.mel attachDriverOnCurve 의 원래 동작 — comd_M_b_create / makeParameterValueList)
# ----------------------------------------------------------------------------

def _curve_param_range(curve_shape):
    """커브 shape 의 (minValue, maxValue) 파라미터 범위를 반환."""
    return (cmds.getAttr(curve_shape + ".minValue"),
            cmds.getAttr(curve_shape + ".maxValue"))


def _uniform_parameters(count, start, end, full_range):
    """ref 의 makeParameterValueList : start..end 사이에 count 개의 파라미터를 균일 분배.

    full_range=True 면 division=count-1 이라 마지막 드라이버가 정확히 end 에 놓인다
    (열린 커브용, 양 끝 포함). full_range=False 면 division=count 라 마지막이 end 직전에서
    멈춘다(주기적 커브의 seam 중복 방지). count==1 이면 구간 중앙(start + (end-start)/2)에 둔다.
    """
    diff = end - start
    if count == 1:
        return [start + diff / 2.0]
    division = (count - 1) if full_range else count
    return [start + (diff / division) * i for i in range(count)]


def _padded_number(count, n):
    """ref 의 MF_increaseNumberListWithZero : count 자릿수만큼 0 패딩한 번호 문자열.

    count=5 -> '1'..'5', count=12 -> '01'..'12'.
    """
    return str(n).zfill(len(str(count)))


def _create_driver(driver_type):
    """driver_type 에 맞는 새 드라이버 노드(transform 이름)를 만들어 반환."""
    if driver_type == "null":
        return cmds.group(empty=True)
    return cmds.spaceLocator()[0]


def build_attach_uniform(curve, count, driver_type="locator", name_prefix=None,
                         start=None, end=None, full_range=True,
                         orient=True, aim_axis="+X",
                         use_normal_curve=True, normal_curve_length=1.0,
                         create_set=True):
    """커브 위에 새 드라이버 count 개를 균일한 파라미터 간격으로 생성·라이브 어태치한다.

    ref_01.mel attachDriverOnCurve 의 원래 동작 이식 : Locator/Null 드라이버를 만들어
    makeParameterValueList 로 구한 파라미터 지점마다 pointOnCurveInfo -> matrix 네트워크로
    붙인다. closest 모드(build_attach_to_closest)와 같은 orient/norCrv/set 옵션을 공유한다.

    start/end 가 None 이면 커브의 minValue/maxValue 를 쓴다(전 구간). full_range 는
    _uniform_parameters 참고. name_prefix 가 None 이면 커브 이름을 접두사로 쓴다.

    Returns (created, set_node, norcrv):
      created   = [(driver, parameter), ...]  (생성 순서)
      set_node  = 생성한 pointOnCurveInfo 세트 이름(미생성이면 None)
      norcrv    = 생성한 norCrv transform 이름(미생성이면 None)
    """
    curve_shape = _shape_of_curve(curve)
    if curve_shape is None:
        raise ValueError("'{0}' is not a NURBS curve.".format(curve))
    if count < 1:
        raise ValueError("count must be a positive integer.")
    if driver_type not in DRIVER_TYPES:
        driver_type = "locator"
    if aim_axis not in AIM_AXES:
        aim_axis = "+X"

    min_v, max_v = _curve_param_range(curve_shape)
    if start is None:
        start = min_v
    if end is None:
        end = max_v

    base = _transform_of_curve(curve).split("|")[-1].split(":")[-1]
    prefix = (name_prefix or base).split("|")[-1].split(":")[-1]

    # ref 원본 : orient + use_normal_curve 면 norCrv 를 한 개 만들어 공유한다.
    norcrv = None
    norcrv_shape = None
    if orient and use_normal_curve:
        norcrv, norcrv_shape = _create_normal_curve(
            _transform_of_curve(curve), aim_axis, normal_curve_length, base)

    params = _uniform_parameters(count, start, end, full_range)

    created = []
    pocis = []
    for i, param in enumerate(params):
        drv = _create_driver(driver_type)
        drv = cmds.rename(
            drv, "{0}_{1}_drv".format(prefix, _padded_number(count, i + 1)))
        _, poci = _attach_one(curve_shape, drv, orient, aim_axis,
                              norcrv_shape, param=param)
        created.append((drv, param))
        pocis.append(poci)

    set_node = None
    if create_set and pocis:
        set_node = cmds.sets(pocis, name="{0}_atcPOCI_SET".format(base))

    return created, set_node, norcrv
