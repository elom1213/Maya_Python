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

import json
import math

import maya.cmds as cmds
from maya.api import OpenMaya as om

from .wind_manager import (
    DRIVER_SPEED, DRIVER_PHASE, DRIVER_PHASE_OFFSET,
    MODE_CHAIN, MODE_ROOT, OUTPUT_CURVE, OUTPUT_NODE,
    _make_phase_expression, _sine_lut, _leaf, _safe,
)
from .wave_manager import (
    WAVE_WAVELENGTH, WAVE_PERIOD, WAVE_ROOT_RAMP, UP_AXES,
    is_joint, resolve_chains, _chain_positions, _arc_positions,
)


# Lite 전용 드라이버 어트리뷰트. 진폭이 **각도(도)** 라는 점만 기존과 다르다.
LITE_SWING = "windSwingAngle"

LITE_SET_SUFFIX = "_waveLiteSET"
LITE_REST_ATTR = "waveRestRotate"

# 회전축이 로컬 기본축(+-X/Y/Z)과 이만큼 가까우면 rotate 채널에 바로 연결한다.
# 그러면 조인트당 쿼터니언 노드 3개를 아낀다.
_CARDINAL_TOL = 1e-4


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

def _make_lite_driver(name, swing, wavelength, period, speed, ramp, phase_offset=0.0):
    """Lite 드라이버 로케이터. 진폭만 **각도(도)** 이고 나머지는 기존과 같다."""
    drv = cmds.spaceLocator(name=name)[0]

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

    # windPhaseTime = windSpeed 의 시간 적분 (Sine 탭과 같은 표현식 재사용)
    cmds.addAttr(drv, longName=DRIVER_PHASE, attributeType="double", keyable=True)
    _make_phase_expression(drv)
    return drv


# --------------------------------------------------------------- 각도 적용

def _apply_angle(node, angle_plug, world_axis, rest, tag):
    """각도를 노드의 rotate 로 넣는다. 축이 기본축이면 채널 직결, 아니면 쿼터니언 경로."""
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


# --------------------------------------------------------------- 체인 하나

def _build_chain_lite(chain, axis, swing, wavelength, period, speed, ramp,
                      phase_offset):
    """체인 하나에 각도 노드망을 만든다. (드라이버, 만든 노드들, rest 회전, 정보)"""
    name = _safe(_leaf(chain[0]))
    points = _chain_positions(chain)
    arcs = _arc_positions(points)
    total = arcs[-1] if arcs[-1] > 1e-9 else 1.0

    # 파동 평면 : 체인 방향 x 월드 진동축. 양의 각도가 진동축 쪽으로 뻗도록 이 순서다.
    chain_dir = om.MVector(*points[-1]) - om.MVector(*points[0])
    if chain_dir.length() < 1e-6:
        return None, [], {}, "chain length is 0"

    up = om.MVector(0.0, 0.0, 0.0)
    up[UP_AXES.index(axis.upper())] = 1.0

    world_axis = chain_dir.normal() ^ up
    if world_axis.length() < 1e-4:
        return None, [], {}, "chain is parallel to the wave axis"
    world_axis = world_axis.normal()

    rest_rotate = {node: list(cmds.getAttr(node + ".rotate")[0]) for node in chain}

    drv = _make_lite_driver(name + "_liteDriver#", swing, wavelength, period,
                            speed, ramp, phase_offset)
    made = [drv]

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

        # theta_k = swing * ramp_k * sin(u_k)
        swing_k = cmds.createNode("multDoubleLinear", name=tag + "_swing")
        cmds.connectAttr(drv + "." + LITE_SWING, swing_k + ".input1")
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

        if _cardinal(_local_axis(node, world_axis)) is not None:
            cardinal_count += 1
        made += _apply_angle(node, local_plug, world_axis, rest_rotate[node], tag)

    cmds.delete(template)

    return drv, made, rest_rotate, (cardinal_count, len(chain))


# --------------------------------------------------------------- 공개 API

def build_wave_lite(joints, mode=MODE_ROOT, axis="Y", swing=20.0, wavelength=10.0,
                    period=24.0, speed=1.0, ramp=1.0, node_offset=0.0,
                    output=OUTPUT_NODE, start=0.0, end=100.0, prefix=None):
    """커브·ikHandle 없이 체인이 파형을 따라가게 한다.

    swing : **뼈가 흔들리는 각도(도)**. 기존 Chain Wave 의 windAmplitude(거리)와 뜻이 다르다.
    나머지 인자는 기존 build_wave 와 같다.

    Returns: (체인 수, 드라이버 수, 메시지)
    """
    chains, missing, branched = resolve_chains(joints, mode)

    if not chains:
        msg = "[Warning] No usable chain."
        if missing:
            msg += " Skipped: {0}".format(", ".join(missing[:5]))
        return 0, 0, msg

    if wavelength <= 0 or period <= 0:
        return 0, 0, "[Warning] Wavelength and Period must be greater than 0."

    drivers, made_all, rest_all, failed = [], [], {}, []
    cardinal_total, node_total = 0, 0

    for k, chain in enumerate(chains):
        drv, made, rest, info = _build_chain_lite(
            chain, axis, swing, wavelength, period, speed, ramp, k * node_offset)

        if drv is None:
            failed.append("{0} ({1})".format(_leaf(chain[0]), info))
            continue

        drivers.append(drv)
        made_all += made
        rest_all.update(rest)
        cardinal_total += info[0]
        node_total += info[1]

    if not drivers:
        return 0, 0, "[Warning] Nothing built. {0}".format("; ".join(failed))

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
               "Rotation keys only - the setup was removed.".format(
                   len(chains), len(targets), min(start, end), max(start, end)))
    else:
        msg = ("Chain Wave Lite: {0} chain(s), {1} maya node(s), "
               "no curve / ikHandle / proxy. Direct-axis {2}/{3} node(s). "
               "Edit windSwingAngle (degrees) / windWavelength / windPeriod / "
               "windSpeed / windRootRamp live. Remove with the '{4}' set.".format(
                   len(drivers), len(made_all), cardinal_total, node_total, set_name))

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
