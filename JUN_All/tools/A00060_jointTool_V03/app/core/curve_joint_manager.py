# -*- coding: utf-8 -*-
# Curve 탭 로직 - MEL JointTool V05.03 "joint to Crv" / "Clusters" 포팅.
#   JUN_make_jnt_toCurvePoint / make_jnts_toCurvePoint /
#   JUN_cmd_create_joints_toCrv / JUN_cmd_create_clusters_toCrv
#
# joint 는 항상 커브 포인트의 world-space 절대 위치에 생성한다(오브젝트/커브가 어떤
# 계층 아래에 있어도 정확히 배치). 예전의 "pointPosition + 커브 translation" 좌표 보정은
# 이중 가산 버그라 제거했다.

import maya.cmds as cmds


def _leaf(name):
    """로그에 쓸 짧은 이름."""
    return str(name).split("|")[-1]


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


# ==================================================================
# 개수로 만들기 (v03.12~) - POCI 의 parameter 0~1 을 등분한 자리
# ==================================================================
#
# "3 을 넣으면 POCI 의 입력값이 0 · 0.5 · 1.0 일 때와 같은 자리" 라는 요청 그대로다.
# `pointOnCurveInfo` 에 `turnOnPercentage = 1` 을 켜면 `parameter` 가 **파라미터 구간의
# 비율**(0~1)이 된다. 그 자리를 그대로 쓴다.
#
# ★ **길이(arc length) 등분이 아니다.** 파라미터 등분이므로 CV 간격이 불규칙한 커브에서는
#   조인트 간격도 불규칙해진다 - 이게 POCI 와 같은 자리라는 요청의 뜻이다. 길이로 고르게
#   놓는 것은 다른 규칙이다(`A00400_CurveTool` 의 Joints 탭이 그쪽이다).
#
# 위치는 `cmds.pointOnCurve(shape, pr=f, turnOnPercentage=True, p=True)` 로 얻는다.
# POCI 노드(`worldSpace` 입력) · 이 명령 · `MFnNurbsCurve.getPointAtParam(kWorld)` 세 가지가
# **같은 월드 좌표**를 주는 것을 확인했다(부모에 이동 · 회전 · 스케일이 걸린 커브,
# degree 1/3, 주기 커브 포함). 그래서 커브가 어느 계층 아래에 있어도 자리가 맞는다.

#: 개수 UI 의 최소값. 1 개면 "체인" 이 성립하지 않고 시작점 하나만 나온다.
MIN_JOINT_COUNT = 2


def _curve_shape(curve):
    """커브 트랜스폼/셰이프 이름 -> nurbsCurve 셰이프 이름. 커브가 아니면 None.

    셰이프를 직접 넘기는 이유: 트랜스폼 밑에 셰이프가 여럿이면 명령이 어느 것을 볼지
    모른다(공용 `Framework.core.maya_shape` 의 경고와 같은 함정).
    """
    if not curve or not cmds.objExists(curve):
        return None
    if cmds.nodeType(curve) == "nurbsCurve":
        return curve
    shapes = cmds.listRelatives(curve, s=True, ni=True, f=True) or []
    for shape in shapes:
        if cmds.nodeType(shape) == "nurbsCurve":
            return shape
    return None


def parameter_fractions(count):
    """`count` 개의 0~1 비율. count=3 -> [0.0, 0.5, 1.0] (요청 그대로)."""
    count = int(count)
    if count < MIN_JOINT_COUNT:
        raise ValueError("Joint count must be {0} or more (got {1}).".format(
            MIN_JOINT_COUNT, count))
    last = float(count - 1)
    return [i / last for i in range(count)]


def curve_count_positions(curve, count):
    """그 커브에서 `count` 개의 월드 위치. POCI(turnOnPercentage) 와 같은 자리."""
    shape = _curve_shape(curve)
    if shape is None:
        raise ValueError("{0} is not a NURBS curve.".format(curve))
    return [cmds.pointOnCurve(shape, pr=fraction, turnOnPercentage=True, p=True)
            for fraction in parameter_fractions(count)]


def _joint_at(position):
    """월드 위치에 joint 하나. 선택 중인 joint 가 있으면 그 자식으로 붙는다."""
    jnt = cmds.joint(p=position)
    # 생성 직후 월드 좌표를 확정한다 - 부모 체인이 있으면 `joint -p` 는 로컬로 해석된다.
    cmds.xform(jnt, ws=True, translation=position)
    return jnt


def joints_by_count(curves, count, chain=True):
    """커브마다 `count` 개의 조인트를 파라미터 등분 자리에 만든다.

    count   : 2 이상. 3 이면 POCI 입력 0 · 0.5 · 1.0 자리.
    chain   : True(기본) 면 **조인트 체인**(앞 조인트의 자식으로 이어 붙고 체인 orient),
              False 면 **자리마다 따로 떨어진 조인트**(각자 루트, orient 는 월드).

    반환: `(커브마다 만든 조인트 목록, 메시지 목록)`.
    씬을 바꾸므로 호출부가 `undo_chunk()` 안에서 부른다.
    """
    fractions = parameter_fractions(count)          # 여기서 count 검증도 함께 된다
    created = []
    messages = []

    cmds.select(clear=True)
    for curve in curves or []:
        shape = _curve_shape(curve)
        if shape is None:
            messages.append("[WARN] {0} is not a NURBS curve - skipped.".format(curve))
            continue

        positions = [cmds.pointOnCurve(shape, pr=f, turnOnPercentage=True, p=True)
                     for f in fractions]

        # 닫힌(주기) 커브는 parameter 0 과 1 이 같은 점이다 - 겹쳐 놓고 알린다
        # (자리를 임의로 옮기면 "POCI 와 같은 자리" 라는 규칙이 깨진다).
        if cmds.getAttr(shape + ".form") in (1, 2):
            messages.append(
                "[WARN] {0} is a closed curve - the last joint lands on the first "
                "(parameter 0 and 1 are the same point).".format(_leaf(curve)))

        joints = []
        prev = None
        cmds.select(clear=True)
        for position in positions:
            current = _joint_at(position)
            if chain and prev is not None:
                # 앞 조인트를 자식 쪽으로 조준시킨다(이 툴의 다른 생성 기능과 같은 규칙).
                cmds.joint(prev, edit=True, zso=True, oj="xyz", sao="yup")
            joints.append(current)
            prev = current
            if not chain:
                # 다음 조인트가 자식으로 붙지 않도록 선택을 비운다 -> 자리마다 루트 하나.
                cmds.select(clear=True)

        if chain and joints:
            # 마지막 조인트는 조준할 자식이 없다 - 월드 정렬로 둔다(체인 관례).
            cmds.select(joints[-1])
            cmds.joint(edit=True, oj="none", ch=True, zso=True)

        cmds.select(clear=True)
        created.append(joints)
        messages.append("[OK] {0} : {1} joint(s) as {2}.".format(
            _leaf(curve), len(joints), "a chain" if chain else "separate joints"))

    if not created:
        messages.append("[WARN] No NURBS curve in the list - nothing was created.")

    return created, messages
