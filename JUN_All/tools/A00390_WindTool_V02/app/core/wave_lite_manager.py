# -*- coding: utf-8 -*-
# A00390_WindTool_V02 core - Chain Wave **Lite** : 커브·ikHandle·프록시 없이
#                            **각도만으로** 체인이 싸인 파형을 따라가게 한다. (UI 비의존)
#
# ## 왜 따로 만들었나
#
# 기존 Chain Wave 는 체인마다 **커브 + ikSpline 핸들 + 프록시 조인트 체인**을 만든다.
# 옳은 방법이지만 개수가 붙는다(실측, 조인트 9개 기준):
#
#     체인당 141 노드 · 커브 1 · ikHandle 1 · 프록시 조인트 10
#     -> 루트 100 개면 약 14,100 노드 · 커브 100 · ikHandle 100
#
# 루트가 100 개를 넘는 상황(털·풀·촉수 다발)에서는 이것만으로 씬이 무거워진다.
# Lite 모드는 **같은 종류의 움직임**을 커브·IK·프록시 없이 만든다.
#
# ## 어떻게 하나 - 정의를 바꾼다
#
# 기존: "CV 를 A 만큼 밀어 만든 커브를 ikSpline 이 따라간다"  (진폭 = 미는 **거리**)
# Lite: **"뼈의 월드 방향각이 싸인파를 그린다"**              (진폭 = 흔들리는 **각도**)
#
#     theta_k    = swing * ramp_k * sin( 2pi * ( s_k/lambda - phase ) )   ... 뼈 k 의 월드 각도
#     localRot_k = theta_k - theta_(k-1)                                  ... 조인트 k 의 로컬 회전
#
# `theta_k - theta_(k-1)` 이 핵심이다. FK 는 로컬 회전이 자손에 **누적**되므로, 차분을 넣으면
# 누적 결과가 정확히 theta_k 가 된다 - 체인이 말리지 않고 파형을 따라간다.
# (기존 Sine 탭이 rotateZ 로 말려 들어갔던 이유가 이 차분을 안 했기 때문이다.)
#
# ## 기존 모드와 값이 같지는 않다 - 확인하고 바꾼 것
#
# "커브의 접선각을 그대로 쓰면 기존과 같아지지 않을까" 를 실제로 재 봤더니 **일관되게 과대**했다
# (조인트 9, 뼈 2.0, A 1.5, 파장 10 에서 ikSpline -25.5 도 vs 접선식 -39.7 도).
# NURBS 커브가 CV 를 통과하지 않고 안쪽으로 당겨지기 때문이고, 그 비율은 **파장에 따라 변한다**
# (실측 실제/접선 = 파장 6 -> 0.41, 10 -> 0.66, 20 -> 0.75). 상수 보정으로는 못 맞춘다.
#
# 그래서 Lite 는 기존 값을 재현하려 하지 않는다. 대신 **진폭의 뜻을 각도로 바꿔** 결과를
# 예측 가능하게 만들었다 - windSwingAngle 20 이면 끝 뼈가 월드 기준 +-20 도로 흔들린다.
# 기존 셋업에서 옮겨 올 때는 눈으로 맞추면 된다(같은 숫자가 같은 그림을 주지 않는다).
#
# ## 무엇을 만들지 않는가
#
#   커브 X · ikHandle X · ikEffector X · 프록시 조인트 X · 매트릭스 전달 노드 X
#
# 조인트든 FK 컨트롤러든 **같은 경로**로 처리한다. 기존 모드에서 컨트롤러 때문에 필요했던
# 프록시 체인이 통째로 사라진다.
#
# ## 디버그 커브 (선택, 기본 ON)
#
# 각도만 다루다 보니 "이 체인이 지금 어떤 파형을 그리고 있는지" 가 눈에 잘 안 들어온다.
# 그래서 **Chain Wave 탭이 만드는 커브와 같은 방식**(체인 노드 위치를 CV 로 하는 degree 3
# NURBS)으로 커브를 하나 만들어 흔들림을 보여 준다. 다른 것은 **방향뿐**이다:
#
#   Chain Wave : 커브가 ikSpline 으로 체인을 **구동**한다  (커브 -> 체인)
#   Lite       : 체인이 각도로 움직이고 커브가 **따라간다** (체인 -> 커브)
#
# CV k 는 `multMatrix(node_k.worldMatrix, curve.worldInverseMatrix) -> decomposeMatrix
# -> controlPoints[k]` 로 노드 k 의 월드 위치에 붙는다. 그래서 커브가 **늘 체인 위에 정확히**
# 놓이고(실측 일치), 커브나 그 부모를 옮겨도 CV 는 조인트를 따라간다. 사이클은 없다 —
# `worldInverseMatrix` 는 CV 에 의존하지 않는다.
#
# 굳이 "Chain Wave 가 만들었을 커브" 를 계산해 그리지 않는 이유: 두 모드는 **값이 같지 않다**
# (위 참고, 파장에 따라 비율이 0.41~0.75 로 변한다). 그런 커브를 그리면 실제 흔들림과 다른
# 그림을 보여 주게 되어 디버그용으로 오히려 해롭다. 지금 방식은 **실제 결과**를 그린다.
#
# ## 아웃라이너 - 로케이터 그룹 / 커브 그룹
#
# 빌드 하나가 그룹 **둘**을 만든다: `<prefix>_liteDriverGrp` (드라이버 로케이터) 와
# `<prefix>_liteCurveGrp` (디버그 커브). 예전에는 체인마다 (드라이버, 커브) 를 이어서
# 만들어 아웃라이너에 **번갈아** 쌓였다. 그룹은 원점·단위행렬이고 `parent -relative` 로
# 옮기므로 월드 위치가 변하지 않는다(드라이버는 이 시점에 translate 가 연결돼 있어
# 기본 parent 의 "월드 유지" setAttr 이 불가능하다는 실제 이유도 있다).
#
# ## 드라이버가 루트를 따라간다 (node 출력)
#
#   multMatrix(root.worldMatrix, driver.parentInverseMatrix)
#       -> decomposeMatrix.outputTranslate -> driver.translate
#
# constraint 없이 위치만 따라간다(회전은 그대로 둔다). `parentInverseMatrix` 는 **부모**의
# 월드 역행렬이라 드라이버 자신의 translate 에 의존하지 않아 사이클이 없다. 유일하게
# 사이클이 되는 배치(드라이버가 루트의 조상)는 연결하지 않고 로그에 사유를 남긴다.
# 자세한 근거는 `wind_manager.follow_root_position` 의 독스트링에 있다.
#
# ## 회전축을 정하는 두 가지 방법
#
# 1) **Sway Axis (월드)** — 기본. `world_axis = chain_dir x up` 으로 구한 **월드 축** 둘레로
#    돌린다. 체인이 어떻게 orient 돼 있든 결과가 월드 기준으로 같다. 대신 그 축이 노드의
#    로컬 기본축과 어긋나면 조인트마다 쿼터니언 노드 3개가 붙고, 세 rotate 채널이 전부 물린다.
#
# 2) **Rotate Axis (오브젝트)** — `local_axis="X"/"Y"/"Z"`. 각 노드의 **자기 rotate 채널 하나만**
#    쓴다(`rotateX` 등). 채널 직결이라 노드가 가장 적고, 다른 두 채널은 손대지 않아 애니메이터가
#    남은 축을 계속 쓸 수 있다. 이때 **Sway Axis 는 계산에 전혀 들어가지 않는다**(월드 축을
#    구하지 않으므로 "체인이 축과 평행" 실패도 없다).
#
#    주의: theta 차분(`theta_k - theta_(k-1)`)이 월드 각도로 정확히 누적되려면 체인의 각 노드가
#    **같은 방향으로 orient** 돼 있어야 한다. 보통의 FK 체인·조인트 체인은 그렇다. 축이 노드마다
#    제각각인 체인이라면 파형이 아니라 "각자 자기 축으로 흔들리는" 그림이 되므로 (1) 을 쓴다.

import json
import math

import maya.cmds as cmds
from maya.api import OpenMaya as om

from .wind_manager import (
    DRIVER_SPEED, DRIVER_PHASE, DRIVER_PHASE_OFFSET, DRIVER_ENVELOPE,
    MODE_CHAIN, MODE_ROOT, OUTPUT_CURVE, OUTPUT_NODE,
    _make_phase_expression, _sine_lut, _leaf, _safe, follow_root_position,
)
from .wave_manager import (
    WAVE_WAVELENGTH, WAVE_PERIOD, WAVE_ROOT_RAMP, UP_AXES,
    is_joint, resolve_chains, _chain_positions, _arc_positions,
)


# Lite 전용 드라이버 어트리뷰트. 진폭이 **각도(도)** 라는 점만 기존과 다르다.
LITE_SWING = "windSwingAngle"

# windEnvelope([0,1], wind_manager 의 DRIVER_ENVELOPE)은 **실효 스윙 각도**에 곱해진다:
#     effSwing = windSwingAngle * windEnvelope
# theta_k 가 스윙 각도에 정비례하고 로컬 회전이 theta 의 차분이므로, 스윙에 한 번만 곱하면
# 체인 전체가 같은 비율로 줄어든다. 0 이면 모든 theta 가 0 -> 로컬 회전 0 -> **rest 자세**,
# 0.5 면 절반, 1 이면 완전 적용. 체인당 multDoubleLinear 1개면 끝난다.

LITE_SET_SUFFIX = "_waveLiteSET"
# 디버그 커브 이름 접미사(제거 세트에 함께 담기므로 Remove 로 같이 지워진다).
LITE_DEBUG_SUFFIX = "_liteDebugCrv"
LITE_REST_ATTR = "waveRestRotate"

# 아웃라이너 정리용 그룹. 드라이버 로케이터와 디버그 커브가 **서로 섞이지 않게** 각각
# 자기 그룹으로 모인다(예전에는 체인 순서대로 로케이터/커브가 번갈아 쌓였다).
LITE_DRIVER_GRP_SUFFIX = "_liteDriverGrp"
LITE_CURVE_GRP_SUFFIX = "_liteCurveGrp"

# Rotate Axis (오브젝트 공간) 로 쓸 수 있는 축. 노드의 rotateX/Y/Z 채널에 그대로 대응한다.
LOCAL_AXES = ("X", "Y", "Z")

# 회전축이 로컬 기본축(+-X/Y/Z)과 이만큼 가까우면 rotate 채널에 바로 연결한다.
# 그러면 조인트당 쿼터니언 노드 3개를 아낀다.
_CARDINAL_TOL = 1e-4


def _ensure_quat_nodes():
    """쿼터니언 노드(quatNodes 플러그인)를 확실히 올린다. 이미 올라와 있으면 아무 일도 없다."""
    try:
        cmds.loadPlugin("quatNodes", quiet=True)
    except Exception:
        pass


# --------------------------------------------------------------- 회전축 계산

def _world_rotation(node):
    """노드 월드 행렬의 **회전 성분만** (MMatrix)."""
    matrix = om.MMatrix(cmds.getAttr(node + ".worldMatrix[0]"))
    return om.MTransformationMatrix(matrix).rotation(asQuaternion=True).asMatrix()


def _parent_rotation(node):
    parent = (cmds.listRelatives(node, parent=True, fullPath=True) or [None])[0]
    return _world_rotation(parent) if parent else om.MMatrix()


def _orient_matrix(node):
    """조인트면 jointOrient 행렬, 아니면 단위행렬.

    마야 조인트의 로컬 회전은 `rotate * jointOrient` 순서다. 그래서 rotate 채널에 넣을
    회전축은 jointOrient 까지 되돌린 공간에서 구해야 한다.
    """
    if not is_joint(node):
        return om.MMatrix()

    jo = cmds.getAttr(node + ".jointOrient")[0]
    euler = om.MEulerRotation([math.radians(v) for v in jo], om.MEulerRotation.kXYZ)
    return euler.asMatrix()


def _local_axis(node, world_axis):
    """월드 축을 그 노드의 **rotate 채널 공간**으로 옮긴 단위 벡터.

    world = rotate * jointOrient * parentWorld 이므로, rotate 에 넣을 축은
    world_axis * (jointOrient * parentWorld)^-1 이다.
    """
    space = _orient_matrix(node) * _parent_rotation(node)
    return (om.MVector(world_axis) * space.inverse()).normal()


def _cardinal(axis):
    """축이 +-X/Y/Z 에 충분히 가까우면 (채널 인덱스, 부호), 아니면 None."""
    for index in range(3):
        for sign in (1.0, -1.0):
            ideal = om.MVector(0.0, 0.0, 0.0)
            ideal[index] = sign
            if (axis - ideal).length() < _CARDINAL_TOL:
                return index, sign
    return None


def _rotate_order(node):
    return (om.MEulerRotation.kXYZ, om.MEulerRotation.kYZX, om.MEulerRotation.kZXY,
            om.MEulerRotation.kXZY, om.MEulerRotation.kYXZ,
            om.MEulerRotation.kZYX)[cmds.getAttr(node + ".rotateOrder")]


# --------------------------------------------------------------- 드라이버

def _make_lite_driver(name, swing, wavelength, period, speed, ramp, phase_offset=0.0,
                      envelope=1.0, place_at=None):
    """Lite 드라이버 로케이터. 진폭만 **각도(도)** 이고 나머지는 기존과 같다.

    place_at : 월드 좌표 (x, y, z). 주면 로케이터를 그 자리로 옮긴다(체인 최상단 위에 두기).
               None 이면 원점에 만든다(예전 동작).
    """
    drv = cmds.spaceLocator(name=name)[0]

    if place_at is not None:
        cmds.xform(drv, worldSpace=True, translation=place_at)

    for attr, val, minimum in ((LITE_SWING, swing, None),
                               (WAVE_WAVELENGTH, wavelength, 0.001),
                               (WAVE_PERIOD, period, 0.001),
                               (WAVE_ROOT_RAMP, ramp, 0.0)):
        kwargs = {"longName": attr, "attributeType": "double",
                  "defaultValue": val, "keyable": True}
        if minimum is not None:
            kwargs["minValue"] = minimum
        cmds.addAttr(drv, **kwargs)
        cmds.setAttr(drv + "." + attr, val)

    cmds.addAttr(drv, longName=DRIVER_SPEED, attributeType="double",
                 defaultValue=speed, keyable=True)
    cmds.setAttr(drv + "." + DRIVER_SPEED, speed)

    cmds.addAttr(drv, longName=DRIVER_PHASE_OFFSET, attributeType="double",
                 defaultValue=phase_offset, keyable=True)
    cmds.setAttr(drv + "." + DRIVER_PHASE_OFFSET, phase_offset)

    # 영향력 [0, 1]. 0 = 흔들리지 않음(rest 자세), 0.5 = 절반, 1 = 완전 적용.
    cmds.addAttr(drv, longName=DRIVER_ENVELOPE, attributeType="double",
                 defaultValue=1.0, minValue=0.0, maxValue=1.0, keyable=True)
    cmds.setAttr(drv + "." + DRIVER_ENVELOPE, max(0.0, min(1.0, envelope)))

    # windPhaseTime = windSpeed 의 시간 적분 (Sine 탭과 같은 표현식 재사용)
    cmds.addAttr(drv, longName=DRIVER_PHASE, attributeType="double", keyable=True)
    _make_phase_expression(drv)
    return drv


# --------------------------------------------------------------- 각도 적용

def _apply_angle(node, angle_plug, world_axis, rest, tag, local_index=None):
    """각도를 노드의 rotate 로 넣는다. 축이 기본축이면 채널 직결, 아니면 쿼터니언 경로.

    local_index : 0/1/2 를 주면 **오브젝트 공간** 축으로 보고 그 rotate 채널에 바로 넣는다
                  (world_axis 는 쓰지 않는다). None 이면 월드 축을 노드 공간으로 옮겨 쓴다.
    """
    if local_index is not None:
        axis, card = None, (local_index, 1.0)
    else:
        axis = _local_axis(node, world_axis)
        card = _cardinal(axis)

    if card is not None:
        index, sign = card
        channel = "{0}.rotate{1}".format(node, "XYZ"[index])

        scale = cmds.createNode("multDoubleLinear", name=tag + "_sign")
        cmds.connectAttr(angle_plug, scale + ".input1")
        cmds.setAttr(scale + ".input2", sign)

        if abs(rest[index]) > 1e-9:
            add = cmds.createNode("addDoubleLinear", name=tag + "_rest")
            cmds.connectAttr(scale + ".output", add + ".input1")
            cmds.setAttr(add + ".input2", rest[index])
            cmds.connectAttr(add + ".output", channel, force=True)
            return [scale, add]

        cmds.connectAttr(scale + ".output", channel, force=True)
        return [scale]

    # 임의 축 : rest 회전에 축-각 회전을 곱해 오일러로 되돌린다.
    # axisAngleToQuat / quatProd / quatToEuler 는 **quatNodes 플러그인** 소속이다. 로드돼 있지
    # 않으면 createNode 가 "No object matches name" 으로 죽으므로 먼저 확실히 올린다.
    _ensure_quat_nodes()

    a2q = cmds.createNode("axisAngleToQuat", name=tag + "_a2q")
    for i in range(3):
        cmds.setAttr(a2q + ".inputAxis" + "XYZ"[i], axis[i])
    cmds.connectAttr(angle_plug, a2q + ".inputAngle")

    rest_quat = om.MEulerRotation(
        [math.radians(v) for v in rest], _rotate_order(node)).asQuaternion()

    prod = cmds.createNode("quatProd", name=tag + "_qprod")
    for i, value in enumerate((rest_quat.x, rest_quat.y, rest_quat.z, rest_quat.w)):
        cmds.setAttr(prod + ".input1Quat" + "XYZW"[i], value)
    cmds.connectAttr(a2q + ".outputQuat", prod + ".input2Quat")

    q2e = cmds.createNode("quatToEuler", name=tag + "_q2e")
    cmds.setAttr(q2e + ".inputRotateOrder", cmds.getAttr(node + ".rotateOrder"))
    cmds.connectAttr(prod + ".outputQuat", q2e + ".inputQuat")
    cmds.connectAttr(q2e + ".outputRotate", node + ".rotate", force=True)

    return [a2q, prod, q2e]


# --------------------------------------------------------------- 디버그 커브

def _make_debug_curve(chain, points, name):
    """체인이 어떻게 흔들리는지 보여 주는 커브. (transform 또는 None, 만든 노드들)

    **Chain Wave 탭이 만드는 커브와 같은 방식**으로 만든다 — 체인 노드 위치를 CV 로 하는
    degree 3 NURBS(노드가 적으면 차수를 낮춘다). 그래서 CV k 가 체인 노드 k 와 1:1 이다.

    다만 구동 방향이 반대다. Chain Wave 는 커브가 체인을 끌지만, 여기서는 체인이 먼저
    움직이고 커브가 그 결과를 따라 그린다 — CV 를 노드의 월드 위치에 연결해 둔다.
    커브(또는 그 부모)를 옮겨도 CV 가 조인트에 그대로 붙어 있도록 `worldInverseMatrix` 로
    커브의 오브젝트 공간으로 되돌린다. `worldInverseMatrix` 는 CV 에 의존하지 않으므로
    사이클이 생기지 않는다(실측 확인).

    ※ Chain Wave 의 커브보다 **CV 가 정확히 하나 적다.** 그쪽은 커브를 프록시 체인에서
      만드는데 ikSpline 이 엔드 이펙터를 필요로 해 끝에 가상 조인트(dummy tip)를 하나 더
      붙이기 때문이다(조인트 9 -> CV 10). 디버그 커브는 실제 노드만 그리므로 그 하나가 없다.
    """
    if len(points) < 2:
        return None, []

    degree = min(3, len(points) - 1)
    crv = cmds.curve(name=name + "#", degree=degree, point=points)
    crv = cmds.ls(crv, long=True)[0]
    shape = (cmds.listRelatives(crv, shapes=True, fullPath=True) or [None])[0]
    if shape is None:
        return None, [crv]

    # 디버그 표시라 뷰포트 클릭에 걸리지 않게 reference 로 둔다(보이지만 선택되지 않음).
    cmds.setAttr(shape + ".overrideEnabled", 1)
    cmds.setAttr(shape + ".overrideDisplayType", 2)

    made = [crv]
    for k, node in enumerate(chain):
        tag = "{0}_cv{1:02d}".format(name, k)
        mmx = cmds.createNode("multMatrix", name=tag + "Mmx")
        cmds.connectAttr(node + ".worldMatrix[0]", mmx + ".matrixIn[0]")
        cmds.connectAttr(crv + ".worldInverseMatrix[0]", mmx + ".matrixIn[1]")

        dcm = cmds.createNode("decomposeMatrix", name=tag + "Dcm")
        cmds.connectAttr(mmx + ".matrixSum", dcm + ".inputMatrix")
        cmds.connectAttr(dcm + ".outputTranslate",
                         "{0}.controlPoints[{1}]".format(shape, k))
        made += [mmx, dcm]

    return crv, made


# --------------------------------------------------------------- 아웃라이너 정리

def _group_nodes(nodes, name):
    """nodes 를 새 그룹 하나에 모은다. (그룹 풀패스 or None, {옛 이름: 새 풀패스})

    `parent -relative` 로 옮긴다. 이유가 둘이다:

    1. 그룹을 **원점·단위행렬**로 만들므로 로컬을 그대로 둬도 월드 위치가 안 변한다.
    2. 드라이버는 이 시점에 이미 `translate` 가 **연결**돼 있다. 기본 parent 는 월드
       위치를 유지하려고 translate 를 setAttr 하는데, 연결된 채널에는 쓸 수 없다.
       `-relative` 는 로컬을 건드리지 않으므로 그 충돌이 없다.
    """
    nodes = [n for n in nodes if n and cmds.objExists(n)]
    if not nodes:
        return None, {}

    grp = cmds.ls(cmds.createNode("transform", name=name), long=True)[0]
    renamed = {}
    for node in nodes:
        moved = cmds.parent(node, grp, relative=True)[0]
        renamed[node] = cmds.ls(moved, long=True)[0]
    return grp, renamed


# --------------------------------------------------------------- 체인 하나

def _build_chain_lite(chain, axis, swing, wavelength, period, speed, ramp,
                      phase_offset, envelope=1.0, local_axis=None,
                      driver_at_root=True, debug_curve=True, follow_root=True,
                      auto_period=False):
    """체인 하나에 각도 노드망을 만든다. (드라이버, 만든 노드들, rest 회전, 정보, 커브)

    local_axis : "X"/"Y"/"Z" 를 주면 각 노드의 **오브젝트 공간** 축으로만 돌린다.
                 이때 `axis`(Sway Axis) 는 **전혀 쓰이지 않는다**.
    debug_curve: True 면 흔들림을 보여 주는 커브를 하나 만든다(`_make_debug_curve`).
    follow_root: True 면 드라이버가 체인 루트의 **월드 위치**를 계속 따라간다.
    auto_period: True 면 `wavelength` 인자를 무시하고 **이 체인의 길이**를 파장으로 쓴다
                 (아래 참고). 체인마다 값이 달라지므로 드라이버별로 정해진다.

    실패하면 (None, [], {}, 사유문자열, None) 을 돌려준다.
    성공하면 정보는 (직결 노드 수, 체인 노드 수, 루트추종 건너뛴 사유 or None, 쓴 파장) 이다.
    """
    name = _safe(_leaf(chain[0]))
    points = _chain_positions(chain)
    arcs = _arc_positions(points)
    total = arcs[-1] if arcs[-1] > 1e-9 else 1.0

    # ---- Auto Period : 파장을 **체인의 길이**로 잡는다.
    #
    # u_k = s_k/lambda - t 이고 LUT 가 sin(2pi*u) 이므로, lambda = (체인 전체 길이) 로 두면
    # s_k/lambda 가 루트에서 0, 끝에서 정확히 1 이 된다 - 체인 위에 파형이 **딱 한 주기**
    # 실린다(최댓값 한 번, 최솟값 한 번).
    #
    # 여기서 "체인의 길이" 는 루트와 끝의 **직선 거리가 아니라** 노드를 따라간 **경로 길이**
    # (`_arc_positions` 의 누적 거리)다. 파형의 위상도 같은 누적 거리 s_k 로 매기므로,
    # 체인이 굽어 있어도 굽은 길이 그대로 한 주기가 된다.
    if auto_period:
        wavelength = total

    chain_dir = om.MVector(*points[-1]) - om.MVector(*points[0])
    if chain_dir.length() < 1e-6:
        return None, [], {}, "chain length is 0", None

    if local_axis is not None:
        # 오브젝트 공간 축 : 노드마다 자기 rotate 채널 하나만 쓴다. 월드 축은 구하지 않는다.
        local_index = LOCAL_AXES.index(local_axis.upper())
        world_axis = None
    else:
        # 파동 평면 : 체인 방향 x 월드 진동축. 양의 각도가 진동축 쪽으로 뻗도록 이 순서다.
        local_index = None

        up = om.MVector(0.0, 0.0, 0.0)
        up[UP_AXES.index(axis.upper())] = 1.0

        world_axis = chain_dir.normal() ^ up
        if world_axis.length() < 1e-4:
            return None, [], {}, "chain is parallel to the wave axis", None
        world_axis = world_axis.normal()

    rest_rotate = {node: list(cmds.getAttr(node + ".rotate")[0]) for node in chain}

    drv = _make_lite_driver(name + "_liteDriver#", swing, wavelength, period,
                            speed, ramp, phase_offset, envelope,
                            place_at=(points[0] if driver_at_root else None))
    made = [drv]

    # 놓기만 하는 게 아니라 **따라다니게** 한다 - 루트 뼈/컨트롤러가 움직이면(리그 전체
    # 이동 포함) 드라이버도 같이 간다. 위치만이고 constraint 는 쓰지 않는다.
    follow_skip = None
    if follow_root:
        follow_made, follow_skip = follow_root_position(drv, chain[0])
        made += follow_made

    # 실효 스윙 = windSwingAngle * windEnvelope (체인 전체가 공유, 노드 1개).
    swing_env = cmds.createNode("multDoubleLinear", name=name + "_liteSwingEnv#")
    cmds.connectAttr(drv + "." + LITE_SWING, swing_env + ".input1")
    cmds.connectAttr(drv + "." + DRIVER_ENVELOPE, swing_env + ".input2")
    made.append(swing_env)

    # ---- 체인 전체가 공유하는 시간 위상 : (windPhaseTime - windPhaseOffset) / windPeriod
    phase_sub = cmds.createNode("plusMinusAverage", name=name + "_litePhase#")
    cmds.setAttr(phase_sub + ".operation", 2)
    cmds.connectAttr(drv + "." + DRIVER_PHASE, phase_sub + ".input1D[0]")
    cmds.connectAttr(drv + "." + DRIVER_PHASE_OFFSET, phase_sub + ".input1D[1]")

    time_u = cmds.createNode("multiplyDivide", name=name + "_liteTime#")
    cmds.setAttr(time_u + ".operation", 2)
    cmds.connectAttr(phase_sub + ".output1D", time_u + ".input1X")
    cmds.connectAttr(drv + "." + WAVE_PERIOD, time_u + ".input2X")
    made += [phase_sub, time_u]

    template = _sine_lut(name + "_liteSineTemplate")
    thetas = []
    cardinal_count = 0

    for k, node in enumerate(chain):
        tag = "{0}_lite{1:02d}".format(name, k)

        # u_k = s_k/lambda - timePhase
        space = cmds.createNode("multiplyDivide", name=tag + "_space")
        cmds.setAttr(space + ".operation", 2)
        cmds.setAttr(space + ".input1X", arcs[k])
        cmds.connectAttr(drv + "." + WAVE_WAVELENGTH, space + ".input2X")

        u = cmds.createNode("plusMinusAverage", name=tag + "_u")
        cmds.setAttr(u + ".operation", 2)
        cmds.connectAttr(space + ".outputX", u + ".input1D[0]")
        cmds.connectAttr(time_u + ".outputX", u + ".input1D[1]")

        lut = cmds.duplicate(template, name=tag + "_sine")[0]
        cmds.connectAttr(u + ".output1D", lut + ".input")

        # ramp_k = 1 + R * (s_k/total - 1)   (R=1 이면 루트 0 -> 끝 1)
        ramp_mul = cmds.createNode("multDoubleLinear", name=tag + "_rampMul")
        cmds.connectAttr(drv + "." + WAVE_ROOT_RAMP, ramp_mul + ".input1")
        cmds.setAttr(ramp_mul + ".input2", arcs[k] / total - 1.0)

        ramp_add = cmds.createNode("addDoubleLinear", name=tag + "_rampAdd")
        cmds.connectAttr(ramp_mul + ".output", ramp_add + ".input1")
        cmds.setAttr(ramp_add + ".input2", 1.0)

        # theta_k = effSwing * ramp_k * sin(u_k)   (effSwing = swing * envelope)
        swing_k = cmds.createNode("multDoubleLinear", name=tag + "_swing")
        cmds.connectAttr(swing_env + ".output", swing_k + ".input1")
        cmds.connectAttr(ramp_add + ".output", swing_k + ".input2")

        theta = cmds.createNode("multDoubleLinear", name=tag + "_theta")
        cmds.connectAttr(swing_k + ".output", theta + ".input1")
        cmds.connectAttr(lut + ".output", theta + ".input2")

        made += [space, u, lut, ramp_mul, ramp_add, swing_k, theta]

        # ---- 로컬 회전 = theta_k - theta_(k-1)  (FK 누적을 상쇄한다)
        if k == 0:
            local_plug = theta + ".output"
        else:
            diff = cmds.createNode("plusMinusAverage", name=tag + "_local")
            cmds.setAttr(diff + ".operation", 2)
            cmds.connectAttr(theta + ".output", diff + ".input1D[0]")
            cmds.connectAttr(thetas[-1] + ".output", diff + ".input1D[1]")
            made.append(diff)
            local_plug = diff + ".output1D"

        thetas.append(theta)

        if local_index is not None or _cardinal(_local_axis(node, world_axis)) is not None:
            cardinal_count += 1
        made += _apply_angle(node, local_plug, world_axis, rest_rotate[node], tag,
                             local_index=local_index)

    cmds.delete(template)

    # 디버그 커브는 각도 노드망을 다 건 뒤에 붙인다 — CV 가 노드의 월드 위치를 읽으므로
    # 순서가 결과를 바꾸지는 않지만, 커브가 만들어지지 않아도 파형은 그대로여야 한다.
    crv = None
    if debug_curve:
        crv, crv_made = _make_debug_curve(chain, points, name + LITE_DEBUG_SUFFIX)
        made += crv_made

    return (drv, made, rest_rotate,
            (cardinal_count, len(chain), follow_skip, wavelength), crv)


# --------------------------------------------------------------- 공개 API

def build_wave_lite(joints, mode=MODE_ROOT, axis="Y", swing=20.0, wavelength=10.0,
                    period=24.0, speed=1.0, ramp=1.0, node_offset=0.0,
                    output=OUTPUT_NODE, start=0.0, end=100.0, prefix=None,
                    envelope=1.0, local_axis=None, driver_at_root=True,
                    debug_curve=True, auto_period=True):
    """커브·ikHandle 없이 체인이 파형을 따라가게 한다.

    swing : **뼈가 흔들리는 각도(도)**. 기존 Chain Wave 의 windAmplitude(거리)와 뜻이 다르다.
    envelope : 드라이버 windEnvelope 초기값 [0, 1]. 0 = 전혀 흔들리지 않음(rest 자세),
               0.5 = 절반, 1 = 완전 적용. 빌드 뒤에도 드라이버에서 라이브 조절/키잉.
    local_axis : None 이면 `axis`(Sway Axis, 월드)로 회전축을 구한다(기본).
                 "X"/"Y"/"Z" 를 주면 각 노드의 **오브젝트 공간** 축 하나만 돌리고,
                 **`axis` 는 무시된다**.
    driver_at_root : True 면 드라이버 로케이터를 체인 최상단(루트) 월드 위치에 놓고,
                     node 출력이면 그 자리를 **계속 따라가게** 한다(위치만, constraint 없이
                     `multMatrix + decomposeMatrix` 직결). False 면 예전처럼 원점에 만든다.
    auto_period : True(기본)면 `wavelength` 를 무시하고 **체인마다 그 체인의 길이**를
                  파장으로 쓴다 - 루트에서 끝까지 파형이 딱 한 주기 실린다(진폭의 최댓값과
                  최솟값이 각각 한 번씩). 길이는 직선 거리가 아니라 노드를 따라간 **경로
                  길이**라 굽은 체인도 굽은 대로 한 주기다. 체인 길이가 제각각이어도
                  각각 자기 길이에 맞는 파장을 받는다. False 면 예전처럼 모든 체인이
                  `wavelength` 를 그대로 쓴다.
    debug_curve : True(기본)면 체인마다 **흔들림을 보여 주는 커브**를 하나 만든다.
                  Chain Wave 탭의 커브와 같은 방식(노드 위치 = CV, degree 3)이지만 구동
                  방향이 반대라 **실제 결과**를 그린다. Remove 로 함께 지워진다.
    나머지 인자는 기존 build_wave 와 같다.

    Returns: (체인 수, 드라이버 수, 메시지)
    """
    if local_axis is not None and local_axis.upper() not in LOCAL_AXES:
        return 0, 0, "[Warning] Rotate axis must be one of X / Y / Z."

    chains, missing, branched = resolve_chains(joints, mode)

    if not chains:
        msg = "[Warning] No usable chain."
        if missing:
            msg += " Skipped: {0}".format(", ".join(missing[:5]))
        return 0, 0, msg

    if period <= 0 or (not auto_period and wavelength <= 0):
        return 0, 0, "[Warning] Wavelength and Period must be greater than 0."

    drivers, curves, made_all, rest_all, failed = [], [], [], {}, []
    cardinal_total, node_total = 0, 0
    no_follow = []
    used_lengths = []       # Auto Period 로 체인마다 실제로 쓴 파장(= 체인 길이)
    # 루트 추종은 라이브 노드망일 때만 뜻이 있다 - curve 출력은 구운 뒤 셋업을 지운다.
    follow_root = driver_at_root and output != OUTPUT_CURVE

    for k, chain in enumerate(chains):
        drv, made, rest, info, crv = _build_chain_lite(
            chain, axis, swing, wavelength, period, speed, ramp, k * node_offset,
            envelope, local_axis=local_axis, driver_at_root=driver_at_root,
            debug_curve=debug_curve, follow_root=follow_root,
            auto_period=auto_period)

        if drv is None:
            failed.append("{0} ({1})".format(_leaf(chain[0]), info))
            continue

        drivers.append(drv)
        if crv:
            curves.append(crv)
        made_all += made
        rest_all.update(rest)
        cardinal_total += info[0]
        node_total += info[1]
        if info[2]:
            no_follow.append("{0} ({1})".format(_leaf(chain[0]), info[2]))
        used_lengths.append(info[3])

    if not drivers:
        return 0, 0, "[Warning] Nothing built. {0}".format("; ".join(failed))

    # ---- 아웃라이너 정리 : 로케이터는 로케이터끼리, 커브는 커브끼리.
    # 예전에는 체인마다 (드라이버, 커브) 를 이어서 만들어 둘이 **번갈아** 쌓였다.
    base = prefix or "chainWaveLite"
    groups = []
    for nodes, suffix in ((drivers, LITE_DRIVER_GRP_SUFFIX),
                          (curves, LITE_CURVE_GRP_SUFFIX)):
        grp, renamed = _group_nodes(nodes, base + suffix + "#")
        if grp is None:
            continue
        groups.append(grp)
        made_all = [renamed.get(n, n) for n in made_all]
        nodes[:] = [renamed.get(n, n) for n in nodes]
    made_all += groups

    if local_axis is not None:
        axis_note = ("Rotate axis: object {0} (rotate{0} only, Sway Axis "
                     "ignored)".format(local_axis.upper()))
    else:
        axis_note = "Sway axis: world {0}".format(axis.upper())

    # 파장을 어떻게 정했는지 알린다. Auto 면 체인마다 다르므로 범위로 보여 준다.
    if auto_period:
        span = sorted(used_lengths)
        span_txt = ("{0:g}".format(span[0]) if span[0] == span[-1]
                    else "{0:g}-{1:g}".format(span[0], span[-1]))
        length_note = ("Auto Period on: windWavelength = each chain's own path length "
                       "({0}), so exactly one cycle sits on every chain".format(span_txt))
    else:
        length_note = ("Auto Period off: every chain uses windWavelength "
                       "{0:g}".format(wavelength))

    set_name = (prefix or "chainWaveLite") + LITE_SET_SUFFIX
    node_set = cmds.sets(made_all, name=set_name)
    cmds.addAttr(node_set, longName=LITE_REST_ATTR, dataType="string")
    cmds.setAttr(node_set + "." + LITE_REST_ATTR, json.dumps(rest_all), type="string")

    if output == OUTPUT_CURVE:
        targets = sorted(rest_all.keys())
        cmds.bakeResults(targets, time=(min(start, end), max(start, end)),
                         simulation=True,
                         attribute=["rotateX", "rotateY", "rotateZ"],
                         sampleBy=1, disableImplicitControl=True,
                         preserveOutsideKeys=True)
        cmds.delete([n for n in made_all if cmds.objExists(n)])
        if cmds.objExists(node_set):
            cmds.delete(node_set)
        drivers = []
        msg = ("Chain Wave Lite baked: {0} chain(s), {1} node(s) over [{2:g}-{3:g}f]. "
               "{4}. Rotation keys only - the setup was removed.".format(
                   len(chains), len(targets), min(start, end), max(start, end),
                   axis_note))
    else:
        # 디버그 커브는 "이 탭은 커브를 만들지 않는다" 는 원래 문장과 어긋나므로, 켠 경우에는
        # 그 문장 대신 커브가 몇 개 생겼는지 알린다(끄면 예전 문장 그대로).
        shape_note = ("{0} debug curve(s) - display only, they follow the chain "
                      "and drive nothing".format(len(drivers)) if debug_curve
                      else "no curve / ikHandle / proxy")
        if follow_root:
            place_note = "the chain root and follows its world position"
        elif driver_at_root:
            place_note = "the chain root"
        else:
            place_note = "the origin"

        msg = ("Chain Wave Lite: {0} chain(s), {1} maya node(s), "
               "{8}. {6}. Direct-axis {2}/{3} node(s). "
               "Driver locator at {7}. Grouped as {9}. "
               "Edit windSwingAngle (degrees) / windWavelength / windPeriod / "
               "windSpeed / windRootRamp live; windEnvelope [0-1] scales the whole "
               "effect (0 = off, 0.5 = half, now {5:g}). "
               "Remove with the '{4}' set.".format(
                   len(drivers), len(made_all), cardinal_total, node_total, set_name,
                   envelope, axis_note, place_note, shape_note,
                   " + ".join(_leaf(g) for g in groups) or "no group"))
        if no_follow:
            msg += " Root-follow skipped (would cycle): {0}.".format(
                ", ".join(no_follow[:5]))

    msg += " {0}.".format(length_note)

    if failed:
        msg += " Failed: {0}.".format(", ".join(failed[:5]))
    if branched:
        msg += " Branching chain(s) followed the first child: {0}.".format(
            ", ".join(branched[:5]))
    if missing:
        msg += " Skipped: {0}.".format(", ".join(missing[:5]))

    return len(chains), len(drivers), msg


def remove_wave_lite(prefix=None):
    """Lite 셋업을 지우고 회전을 rest 로 되돌린다."""
    sets = [s for s in (cmds.ls(type="objectSet") or [])
            if s.endswith(LITE_SET_SUFFIX)
            and (prefix is None or s.startswith(prefix))]

    if not sets:
        return 0, "[Warning] No Chain Wave Lite set found."

    removed = 0

    for node_set in sets:
        rest = {}
        if cmds.objExists(node_set + "." + LITE_REST_ATTR):
            try:
                rest = json.loads(cmds.getAttr(node_set + "." + LITE_REST_ATTR) or "{}")
            except ValueError:
                rest = {}

        members = cmds.sets(node_set, q=True) or []
        cmds.delete([m for m in members if cmds.objExists(m)])
        if cmds.objExists(node_set):
            cmds.delete(node_set)

        # 연결이 사라진 뒤 rest 값으로 되돌린다.
        for node, value in rest.items():
            if not cmds.objExists(node):
                continue
            for i, channel in enumerate("XYZ"):
                plug = "{0}.rotate{1}".format(node, channel)
                if cmds.listConnections(plug, source=True, destination=False):
                    continue
                try:
                    cmds.setAttr(plug, value[i])
                except RuntimeError:
                    pass

        removed += 1

    return removed, "Chain Wave Lite removed: {0} setup(s).".format(removed)
