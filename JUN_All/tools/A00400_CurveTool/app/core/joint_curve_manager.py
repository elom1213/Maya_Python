# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-07
# A00400_CurveTool core - 커브 위에 조인트를 균일 배치 -> 커브를 바인드 -> 컨트롤러 스택
# (maya.cmds / maya.api.OpenMaya, UI 비의존)
#
# 흐름은 커브 하나마다 세 단계다.
#
#   1) 배치  : 커브의 시작~끝을 [0, 1] 로 보고 count 개를 균일하게 찍어 조인트를 만든다.
#              count=1 -> [0.5] 하나, count=3 -> [0.0, 0.5, 1.0].
#   2) 바인드: 그 조인트들로 **커브 자체를** skinCluster 한다. 조인트를 움직이면 커브의
#              CV 가 따라온다(= 조인트가 커브를 움직인다).
#   3) 컨트롤: 조인트마다 A00460_ControllerTool 과 같은 zro / con / ctl / tgt 스택을 세우고
#              스택 마지막 노드(보통 _tgt)로 조인트를 컨스트레인트한다. 애니메이터는 _ctl 만
#              잡으면 되고, 그 움직임이 조인트 -> 커브로 전달된다.
#
# -- 균일하다는 말의 두 가지 뜻 ----------------------------------------------
# 커브의 **파라미터**를 균등 분할하는 것과 **호 길이(arc length)**를 균등 분할하는 것은
# 다르다. polyToCurve 로 뜬 커브처럼 스팬 길이가 제각각이면 파라미터 균등은 눈에 띄게
# 치우친다(짧은 스팬에 조인트가 몰린다). 그래서 기본은 **호 길이 균등**
# (MFnNurbsCurve.findParamFromLength)이고, 파라미터 균등은 옵션으로 남겨 둔다.
#
# -- 닫힌 커브의 seam --------------------------------------------------------
# 엣지 루프에서 만든 커브는 닫혀 있는 경우가 많다. 닫힌 커브에서 u=0 과 u=1 은 **같은 점**
# 이라 그대로 두면 마지막 조인트가 첫 조인트 위에 겹친다. 닫힌/주기 커브는 마지막 자리를
# 빼고 count 등분해서(0, 1/n, 2/n ...) 겹침을 없앤다.
#
# -- A00460 의 스택을 여기 다시 둔 이유 --------------------------------------
# 노드 구성은 A00460_ControllerTool 의 fk_manager 와 같지만 그 모듈을 import 하지 않는다.
# dev/build_release.py 는 **툴 하나 + Framework** 만 릴리스 폴더로 복사하므로, 다른 툴의
# core 를 참조하면 릴리스에서 곧바로 깨진다. 툴 사이에서 정말 공유해야 해지면 그때
# Framework 로 올릴 자리다.

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om


# --------------------------------------------------------------- 상수

# 균일 배치 기준
SPACING_LENGTH = "length"      # 호 길이 균등 (기본)
SPACING_PARAM = "param"        # 커브 파라미터 균등

COUNT_MIN = 1
COUNT_DEFAULT = 3

SUFFIX_JNT = "_jnt"
SUFFIX_ZRO = "_zro"
SUFFIX_CON = "_con"
SUFFIX_CTL = "_ctl"
SUFFIX_TGT = "_tgt"

GRP_TOP = "_crvJnt_grp"
GRP_JNT = "_jnt_grp"
GRP_CTL = "_ctl_grp"

# 컨스트레인트 종류 (A00460 과 같은 이름을 쓴다)
CON_PARENT = "parent"
CON_POINT = "point"
CON_ORIENT = "orient"
CON_SCALE = "scale"
CONSTRAINT_TYPES = (CON_PARENT, CON_POINT, CON_ORIENT, CON_SCALE)
DEFAULT_CONSTRAINTS = (CON_PARENT,)

# 컨트롤러 커브 = 정육면체 테두리(degree 1). A00460_ControllerTool 과 같은 CV 데이터로,
# 한 붓 그리기로 12개 모서리를 모두 지난다. 좌표는 +-0.5(한 변 1) 단위 큐브.
_CUBE_POINTS = [
    (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
    (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5),
    (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5),
    (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
    (0.5, -0.5, 0.5),
]

# Control Size 는 **반변 길이**(반지름 감각). +-0.5 원본에 size*2 를 곱한다.
DEFAULT_SIZE = 1.0
DEFAULT_JOINT_RADIUS = 0.5

# 커브 바인드 기본값. 커브는 CV 가 한 줄로 늘어서 있어 영향 조인트를 많이 섞을 이유가 없다.
BIND_MAX_INFLUENCES = 3
BIND_DROPOFF = 4.0


# --------------------------------------------------------------- 헬퍼

def _short(node):
    """풀패스·네임스페이스를 뗀 짧은 이름."""
    return node.split("|")[-1].split(":")[-1]


def _curve_shape(node):
    """transform/shape 이름 -> nurbsCurve shape 롱네임. 커브가 아니면 None.

    noIntermediate=True 로 orig shape(`...Orig`)을 걸러 낸다 - 이미 디포머가 걸린
    커브를 다시 리스트업했을 때 원본 셰이프를 잡으면 엉뚱한 곳을 재는 셈이 된다.
    """
    if not node or not cmds.objExists(node):
        return None
    if cmds.objectType(node, isType="nurbsCurve"):
        found = cmds.ls(node, long=True) or []
        return found[0] if found else None
    shapes = cmds.listRelatives(node, shapes=True, type="nurbsCurve",
                                fullPath=True, noIntermediate=True) or []
    return shapes[0] if shapes else None


def _transform_of(shape):
    """셰이프의 부모 트랜스폼 롱네임."""
    parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
    return parents[0] if parents else shape


def _fn_curve(shape):
    """nurbsCurve shape 의 MFnNurbsCurve(월드 평가가 되는 DAG 경로로 연다)."""
    sel = om.MSelectionList()
    sel.add(shape)
    return om.MFnNurbsCurve(sel.getDagPath(0))


def _is_closed(shape):
    """커브가 닫혀 있는가. `.form` 0=open / 1=closed / 2=periodic."""
    try:
        return int(cmds.getAttr(shape + ".form")) != 0
    except Exception:                                       # noqa: BLE001
        return False


def uniform_us(count, closed=False):
    """[0, 1] 구간을 균일하게 나눈 위치 목록.

    count=1        -> [0.5]                    (구간 중앙 하나)
    count=3, 열림  -> [0.0, 0.5, 1.0]          (양 끝 포함)
    count=3, 닫힘  -> [0.0, 1/3, 2/3]          (u=1 은 u=0 과 같은 점이라 뺀다)
    """
    count = int(count)
    if count <= 1:
        return [0.5]
    division = count if closed else (count - 1)
    return [i / float(division) for i in range(count)]


def _padded(count, n):
    """count 자릿수만큼 0 을 채운 번호. count=5 -> '1'.., count=12 -> '01'.."""
    return str(n).zfill(len(str(int(count))))


def sample_curve(shape, count, spacing=SPACING_LENGTH):
    """커브 위 count 개 지점의 (월드 위치, 월드 접선) 목록.

    spacing=SPACING_LENGTH 면 호 길이로, SPACING_PARAM 이면 파라미터로 균등 분할한다.
    닫힌 커브는 seam 겹침을 피하려고 마지막 자리를 빼고 나눈다(uniform_us 참고).
    """
    fn = _fn_curve(shape)
    closed = _is_closed(shape)
    us = uniform_us(count, closed=closed)

    params = None
    if spacing == SPACING_LENGTH:
        total = fn.length()
        # 길이가 0 인(퇴화한) 커브는 findParamFromLength 가 의미를 잃는다 -> 파라미터로.
        if total > 1e-9:
            params = [fn.findParamFromLength(total * u) for u in us]

    if params is None:
        min_v = cmds.getAttr(shape + ".minValue")
        max_v = cmds.getAttr(shape + ".maxValue")
        params = [min_v + (max_v - min_v) * u for u in us]

    samples = []
    for param in params:
        point = fn.getPointAtParam(param, om.MSpace.kWorld)
        tangent = fn.tangent(param, om.MSpace.kWorld)
        samples.append(((point.x, point.y, point.z), tangent))
    return samples


def _aim_euler(tangent):
    """접선을 X 축으로 삼는 회전(도 단위 XYZ 오일러).

    up 은 월드 Y 를 쓰되, 접선이 Y 와 거의 나란하면 축이 무너지므로 월드 Z 로 갈아탄다.
    직교화 순서가 x -> z -> y 라 x(접선)는 정확히 보존되고 up 은 힌트로만 쓰인다.
    """
    x = om.MVector(tangent).normal()
    up = om.MVector(0.0, 1.0, 0.0)
    if abs(x * up) > 0.999:
        up = om.MVector(0.0, 0.0, 1.0)
    z = (x ^ up).normal()
    y = (z ^ x).normal()

    mat = om.MMatrix([x.x, x.y, x.z, 0.0,
                      y.x, y.y, y.z, 0.0,
                      z.x, z.y, z.z, 0.0,
                      0.0, 0.0, 0.0, 1.0])
    rot = om.MTransformationMatrix(mat).rotation()
    return [math.degrees(v) for v in (rot.x, rot.y, rot.z)]


def _cube_control(name, size):
    """컨트롤러 커브 하나(정육면체 테두리). 이름이 겹치면 마야가 번호를 붙인다."""
    scale = float(size) * 2.0          # +-0.5 원본 -> 반변 길이 = size
    points = [(x * scale, y * scale, z * scale) for x, y, z in _CUBE_POINTS]
    crv = cmds.curve(degree=1, point=points, knot=list(range(len(points))))
    return cmds.rename(crv, name)


def _reparent_local(node, parent):
    """parent 밑으로 **로컬 트랜스폼 0 을 유지한 채** 넣는다(월드 보존 안 함).

    원점에서 만든 노드는 로컬 0 을 그대로 유지하므로 결과적으로 부모 자리에 겹친다.
    """
    if not parent:
        return node
    result = cmds.parent(node, parent, relative=True)
    return result[0] if result else node


def _reparent_world(node, parent):
    """parent 밑으로 **월드 자리를 보존한 채** 넣는다(마야 parent 기본 동작)."""
    if not parent:
        return node
    result = cmds.parent(node, parent)
    return result[0] if result else node


def _stack_plan(use_zro, use_con, use_tgt):
    """만들 노드의 (종류, 접미사) 순서. _ctl 은 언제나 들어간다."""
    plan = []
    if use_zro:
        plan.append(("group", SUFFIX_ZRO))
    if use_con:
        plan.append(("group", SUFFIX_CON))
    plan.append(("curve", SUFFIX_CTL))
    if use_tgt:
        plan.append(("group", SUFFIX_TGT))
    return plan


def _create_stack(joint, plan, size, result):
    """조인트 하나에 대한 zro/con/ctl/tgt 스택. (최상단, 최하단, 컨트롤러) 반환.

    **최상단만** 조인트 자리(위치+회전)에 맞추고 나머지는 로컬 0 으로 그 밑에 넣는다.
    그래서 넷이 정확히 겹치고, 컨트롤러에 넣은 값이 곧 조인트 대비 오프셋이 된다.
    """
    base = _short(joint)
    cur_parent = None
    top = None
    ctl = None

    for i, (kind, suffix) in enumerate(plan):
        name = "{0}{1}".format(base, suffix)
        node = _cube_control(name, size) if kind == "curve" \
            else cmds.group(empty=True, name=name)

        # 이름이 이미 쓰이고 있으면 마야가 번호를 붙인다. 조용히 넘어가면 어떤 노드가
        # 어떤 조인트 것인지 나중에 헷갈리므로 알려 준다.
        if _short(node) != name:
            result["renamed"].append((name, _short(node)))

        node = _reparent_local(node, cur_parent)

        if i == 0:
            # 스케일은 건드리지 않는다(컨트롤러 크기는 Size 가 정한다).
            cmds.matchTransform(node, joint, position=True, rotation=True)
            top = node
        if suffix == SUFFIX_CTL:
            ctl = node
        cur_parent = node

    return top, cur_parent, ctl


def _apply_constraints(driver, driven, types, result):
    """driver 가 driven 을 끌게 컨스트레인트를 건다."""
    for con_type in types:
        try:
            if con_type == CON_PARENT:
                made = cmds.parentConstraint(driver, driven, maintainOffset=True)
            elif con_type == CON_POINT:
                made = cmds.pointConstraint(driver, driven, maintainOffset=True)
            elif con_type == CON_ORIENT:
                made = cmds.orientConstraint(driver, driven, maintainOffset=True)
            elif con_type == CON_SCALE:
                made = cmds.scaleConstraint(driver, driven, maintainOffset=True)
            else:
                continue
            result["constraints"].extend(made or [])
        except Exception as exc:                            # noqa: BLE001
            result["warnings"].append(
                "{0}Constraint failed on {1}: {2}".format(
                    con_type, _short(driven), exc))


def existing_skin(shape):
    """셰이프를 이미 구동하는 skinCluster 이름(없으면 None)."""
    history = cmds.listHistory(shape, pruneDagObjects=True) or []
    found = cmds.ls(history, type="skinCluster") or []
    return found[0] if found else None


# --------------------------------------------------------------- 빌드

def _build_one_curve(curve, count, spacing, aim, plan, types, size,
                     joint_radius, do_group, do_bind, result):
    """커브 하나: 조인트 배치 -> (선택) 바인드 -> 컨트롤러 스택."""
    shape = _curve_shape(curve)
    if shape is None:
        result["skipped"].append((_short(curve), "not a NURBS curve"))
        return

    base = _short(_transform_of(shape))

    try:
        samples = sample_curve(shape, count, spacing=spacing)
    except Exception as exc:                                # noqa: BLE001
        result["skipped"].append((base, "could not sample the curve: {0}".format(exc)))
        return

    # ---------------- 1) 조인트 배치 ----------------
    # 조인트는 **하나씩 따로** 만든다. cmds.joint 는 현재 선택의 자식으로 붙으므로 매번
    # 선택을 비워야 서로 부모-자식으로 엮이지 않는다. 커브를 구동하는 조인트들은 각자
    # 독립으로 움직여야 CV 가 제 몫만큼만 따라온다.
    joints = []
    for i, (point, tangent) in enumerate(samples):
        cmds.select(clear=True)
        name = "{0}_{1}{2}".format(base, _padded(len(samples), i + 1), SUFFIX_JNT)
        jnt = cmds.joint(position=point, name=name)
        if _short(jnt) != name:
            result["renamed"].append((name, _short(jnt)))
        cmds.setAttr(jnt + ".radius", float(joint_radius))
        if aim:
            # 조인트의 월드 회전은 rotate * jointOrient 인데 rotate 는 0 이고 부모가
            # 아직 월드(항등)라, jointOrient 에 그대로 쓰면 원하는 월드 방향이 된다.
            cmds.setAttr(jnt + ".jointOrient", *_aim_euler(tangent))
        joints.append(cmds.ls(jnt, long=True)[0])

    # ---------------- 그룹 ----------------
    jnt_grp = ctl_grp = None
    if do_group:
        top_grp = cmds.group(empty=True, name=base + GRP_TOP)
        jnt_grp = cmds.group(empty=True, name=base + GRP_JNT, parent=top_grp)
        ctl_grp = cmds.group(empty=True, name=base + GRP_CTL, parent=top_grp)
        result["groups"].extend([top_grp, jnt_grp, ctl_grp])
        # 조인트는 월드 자리를 지킨 채 옮긴다. 그룹은 원점·항등이라 값도 그대로 남는다.
        joints = [cmds.ls(_reparent_world(j, jnt_grp), long=True)[0] for j in joints]

    # 결과에는 **옮긴 뒤의** 경로를 담는다. 그룹에 넣기 전 롱네임을 담아 두면 호출부가
    # 받는 이름이 곧바로 죽는다(|testCrv_1_jnt 는 이미 없는 경로).
    result["joints"].extend(joints)

    # ---------------- 2) 커브 바인드 ----------------
    # 조인트를 옮긴 **뒤에** 바인드한다. bindPreMatrix 는 바인드 시점의 행렬을 잡으므로
    # 순서가 뒤집히면 그룹으로 옮기는 것만으로 커브가 튈 수 있다.
    if do_bind:
        already = existing_skin(shape)
        if already:
            result["warnings"].append(
                "{0} is already driven by '{1}' - the bind was skipped. Delete "
                "that skinCluster first if you want to rebind.".format(base, already))
        else:
            try:
                skin = cmds.skinCluster(
                    joints, _transform_of(shape), toSelectedBones=True,
                    bindMethod=0, skinMethod=0, normalizeWeights=1,
                    dropoffRate=BIND_DROPOFF,
                    maximumInfluences=min(BIND_MAX_INFLUENCES, len(joints)),
                    obeyMaxInfluences=True,
                    name="{0}_skinCluster".format(base))
                result["skins"].extend(skin or [])
            except Exception as exc:                        # noqa: BLE001
                result["warnings"].append(
                    "Bind failed on {0}: {1}".format(base, exc))

    # ---------------- 3) 컨트롤러 스택 ----------------
    for jnt in joints:
        top, last, ctl = _create_stack(jnt, plan, size, result)
        # 스택 최상단을 그룹에 넣으면 **그 아래 노드의 롱네임이 전부 바뀐다**. 리페어런트
        # 뒤에도 확실히 되찾을 수 있도록 UUID 를 먼저 잡아 둔다(이름은 죽는다).
        uuids = [cmds.ls(n, uuid=True)[0] for n in (top, last, ctl)]
        if ctl_grp:
            # 스택은 이미 조인트 자리에 맞춰져 있다 -> 월드를 지킨 채 담는다.
            _reparent_world(top, ctl_grp)
        top, last, ctl = [cmds.ls(u, long=True)[0] for u in uuids]

        result["roots"].append(top)
        result["controls"].append(ctl)
        _apply_constraints(last, jnt, types, result)

    result["curves"].append(base)


def build_joints_on_curves(curves, count=COUNT_DEFAULT,
                           spacing=SPACING_LENGTH, aim=True,
                           bind=True, group=True,
                           use_zro=True, use_con=True, use_tgt=True,
                           constraints=DEFAULT_CONSTRAINTS,
                           size=DEFAULT_SIZE,
                           joint_radius=DEFAULT_JOINT_RADIUS):
    """리스트업한 커브마다 조인트를 균일 배치하고, 커브를 바인드하고, 컨트롤러를 세운다.

    curves       : 커브 transform/shape 이름 목록.
    count        : 커브 하나당 조인트 개수(1 이상). 1 이면 중앙 하나, n 이면 [0,1] 균등.
    spacing      : SPACING_LENGTH(호 길이 균등, 기본) / SPACING_PARAM(파라미터 균등).
    aim          : True 면 각 조인트의 X 축을 커브 접선 방향으로 돌린다.
    bind         : True 면 만든 조인트로 그 커브를 skinCluster 한다.
    group        : True 면 커브마다 <curve>_crvJnt_grp 밑으로 정리한다.
    use_zro/con/tgt : 컨트롤러 스택에 넣을 널. _ctl 은 항상 만든다.
    constraints  : CON_* 목록. 조인트는 스택 마지막 노드(보통 _tgt)를 따라간다.
    size         : 컨트롤러 큐브의 반변 길이.
    joint_radius : 만든 조인트의 표시 반지름.

    반환 dict:
        curves      처리한 커브 이름
        joints      만든 조인트
        controls    만든 _ctl
        roots       컨트롤러 스택 최상단
        groups      만든 그룹
        skins       만든 skinCluster
        constraints 만든 컨스트레인트 노드
        missing     씬에 없던 입력
        skipped     (이름, 사유) - 커브가 아니거나 샘플링 실패
        renamed     이름이 겹쳐 마야가 번호를 붙인 (원한 이름, 실제 이름)
        warnings    경고 문자열
    """
    result = {
        "curves": [], "joints": [], "controls": [], "roots": [], "groups": [],
        "skins": [], "constraints": [], "missing": [], "skipped": [],
        "renamed": [], "warnings": [],
    }

    count = int(count)
    if count < COUNT_MIN:
        raise ValueError("Joint count must be {0} or more.".format(COUNT_MIN))

    types = [t for t in CONSTRAINT_TYPES if t in (constraints or ())]
    if not types:
        result["warnings"].append(
            "No constraint type is checked - controls are built but the joints "
            "will not follow them.")
    # parent 는 T+R 을 함께 잡는다. point/orient 를 같이 걸면 같은 채널을 두 컨스트레인트가
    # 다투게 된다. 막지는 않고 알려만 준다. (A00460 과 같은 판단)
    if CON_PARENT in types and (CON_POINT in types or CON_ORIENT in types):
        result["warnings"].append(
            "Parent is checked together with Point/Orient - they drive the same "
            "channels and will fight. Use Parent alone, or Point+Orient.")

    plan = _stack_plan(use_zro, use_con, use_tgt)

    valid = []
    for node in (curves or []):
        if not node or not cmds.objExists(node):
            result["missing"].append(node)
            continue
        valid.append(node)

    for curve in valid:
        _build_one_curve(curve, count, spacing, aim, plan, types, size,
                         joint_radius, group, bind, result)

    if result["controls"] or result["joints"]:
        cmds.select(result["controls"] or result["joints"], replace=True)
    return result
