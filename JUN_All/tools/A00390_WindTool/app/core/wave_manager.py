# -*- coding: utf-8 -*-
# A00390_WindTool core - Chain Wave : 조인트 체인이 **회전만으로** 싸인 파형을 따라가게 한다.
#                                     (maya.cmds, UI 비의존)
#
# ## 왜 따로 만들었나
#
# 기존 Sine 탭은 조인트마다 **어트리뷰트 하나**(rotateZ 등)에 위상만 밀린 같은 싸인을 넣는다.
# 그래서 다음 둘 중 하나를 얻는다(실측):
#
#   Axis=translateY : 월드 위치는 파도처럼 보이지만 **뼈 길이가 늘었다 줄고**(2.0 -> 2.12~2.22)
#                     조인트가 **자식을 향하지 않는다**(rotate 가 전부 0).
#   Axis=rotateZ    : 뼈 길이는 지켜지고 조인트가 자식을 향하지만, 각 조인트의 회전이
#                     자손에 **누적**되어 체인이 말려 들어간다 — 파형을 따라가지 않는다.
#
# 원하는 것은 "커브에 마야 기본 **Nonlinear > Sine** 디포머를 걸고 그 커브에 조인트를 붙인"
# 결과를, **회전값만 바꿔서** 재현하는 것이다.
#
# ## 어떻게 하나
#
# 마야에는 이 문제의 정답이 이미 있다 — **ikSplineSolver**. 커브를 따라 체인을 눕히되
# **회전만** 쓰고 뼈 길이를 그대로 유지한다. 그래서:
#
#   1. 조인트 rest 위치에 CV 를 둔 커브를 만들고,
#   2. 그 커브에 ikSpline 핸들을 물리고(createCurve=False),
#   3. 커브의 **CV 를 노드망으로 흔든다**:
#          CV_k 의 up 축 좌표 = rest + amplitude * ramp_k * sin( 2pi * (s_k/wavelength - phase) )
#      s_k 는 그 CV 의 체인 위 거리(월드 단위), phase 는 기존 Sine 탭과 같은
#      windPhaseTime(= windSpeed 의 적분) / windPeriod.
#
# 디포머를 쓰지 않고 CV 를 직접 구동하는 이유: 디포머의 amplitude/wavelength 는 핸들 스케일이
# 섞인 **디포머 로컬 단위**라 월드 단위로 예측하기 어렵다. CV 를 직접 흔들면 진폭·파장을
# **월드 단위 그대로** 준다.
#
# ## 실측 (조인트 9개, 뼈 2.0, 파장 10, 진폭 1.5)
#
#   - translate 는 **하나도 바뀌지 않는다**(회전만).      - 세그먼트 길이 2.0 정확히 유지.
#   - 루트는 제자리.                                      - 조인트-커브 거리 최대 0.067(체인 16의 0.4%).
#
# 진폭은 **CV 를 미는 양**이다. NURBS(3차)는 CV 를 통과하지 않고 안쪽으로 당겨지므로 실제
# 흔들림은 그보다 조금 작다(위 조건에서 약 0.85배). 파장 대비 진폭이 커지면 커브가 체인보다
# 길어져 체인이 커브 끝까지 못 간다 — 그때는 진폭을 줄이거나 파장을 늘린다.

import math

import maya.cmds as cmds

from .wind_manager import (
    DRIVER_SPEED, DRIVER_PHASE, DRIVER_PHASE_OFFSET,
    MODE_CHAIN, MODE_ROOT, OUTPUT_CURVE, OUTPUT_NODE,
    _make_phase_expression, _sine_lut, _leaf, _safe,
)


# Chain Wave 드라이버 어트리뷰트(월드 단위).
WAVE_AMPLITUDE = "windAmplitude"      # CV 를 미는 양(월드 단위)
WAVE_WAVELENGTH = "windWavelength"    # 한 파장의 월드 길이
WAVE_PERIOD = "windPeriod"            # 한 주기의 프레임 수
WAVE_ROOT_RAMP = "windRootRamp"       # 0=루트부터 같은 진폭, 1=루트 0 -> 끝 1 로 커짐

# 파동이 흔드는 월드 축.
UP_AXES = ("X", "Y", "Z")

# 생성물을 담는 세트 접미사(Remove 가 이걸로 찾는다).
WAVE_SET_SUFFIX = "_waveSET"


# --------------------------------------------------------------- 체인 해석

def _linear_chain(root, limit=200):
    """root 에서 **첫 자식만 따라 내려간** 조인트 목록. (chain, branched)

    ikSpline 은 갈래가 없는 한 줄 체인이어야 한다. 갈래가 있으면 첫 자식 쪽을 쓰고
    branched=True 로 알려 호출측이 경고할 수 있게 한다.
    """
    chain = [root]
    branched = False
    node = root
    for _ in range(limit):
        children = cmds.listRelatives(node, children=True, type="joint",
                                      fullPath=True) or []
        if not children:
            break
        if len(children) > 1:
            branched = True
        node = children[0]
        chain.append(node)
    return chain, branched


def resolve_chains(joints, mode):
    """(chains, missing, branched) — chains 는 [[관절...], ...] 각각이 한 줄 체인."""
    missing, branched = [], []
    chains = []

    if mode == MODE_ROOT:
        for root in joints:
            if not cmds.objExists(root):
                missing.append(root)
                continue
            chain, is_branched = _linear_chain(root)
            if len(chain) < 2:
                missing.append(root + " (no child joint)")
                continue
            if is_branched:
                branched.append(_leaf(root))
            chains.append(chain)
        return chains, missing, branched

    # chain 모드: 리스트 순서 그대로 한 체인
    chain = []
    for jnt in joints:
        if not cmds.objExists(jnt):
            missing.append(jnt)
            continue
        chain.append(cmds.ls(jnt, long=True)[0])
    if len(chain) >= 2:
        chains.append(chain)
    return chains, missing, branched


def _chain_positions(chain):
    return [cmds.xform(j, query=True, worldSpace=True, translation=True)
            for j in chain]


def _arc_positions(points):
    """각 점까지의 누적 거리."""
    out = [0.0]
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        out.append(out[-1] + math.sqrt(sum((a[k] - b[k]) ** 2 for k in range(3))))
    return out


# --------------------------------------------------------------- 드라이버 / 노드망

def _make_wave_driver(name, amplitude, wavelength, period, speed, ramp,
                      phase_offset=0.0):
    """Chain Wave 드라이버 로케이터. 파라미터는 전부 **월드 단위 / 프레임**."""
    drv = cmds.spaceLocator(name=name)[0]
    for attr, val, mn in ((WAVE_AMPLITUDE, amplitude, None),
                          (WAVE_WAVELENGTH, wavelength, 0.001),
                          (WAVE_PERIOD, period, 0.001),
                          (WAVE_ROOT_RAMP, ramp, 0.0)):
        kwargs = {"longName": attr, "attributeType": "double",
                  "defaultValue": val, "keyable": True}
        if mn is not None:
            kwargs["minValue"] = mn
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


def _wire_cv(drv, crv, index, arc, total, rest_value, axis, template_lut):
    """CV 하나를 흔든다.

        value = rest + windAmplitude * ramp_k * sineLUT( arc/windWavelength - phase )
        phase = (windPhaseTime - windPhaseOffset) / windPeriod
        ramp_k = 1 + windRootRamp * (arc/total - 1)      # ramp 0 -> 1, ramp 1 -> arc/total

    ramp 는 "루트는 가만히, 끝으로 갈수록 크게" 를 위한 것. windRootRamp 로 라이브 조절한다.
    """
    # ---- 공간 위상 : arc / wavelength  (arc 는 CV 마다 고정된 상수)
    space = cmds.createNode("multiplyDivide", name=_safe(_leaf(crv)) + "_cvSpace%d" % index)
    cmds.setAttr(space + ".operation", 2)              # divide
    cmds.setAttr(space + ".input1X", arc)
    cmds.connectAttr(drv + "." + WAVE_WAVELENGTH, space + ".input2X")

    # ---- 시간 위상 : (windPhaseTime - windPhaseOffset) / windPeriod
    base = cmds.createNode("plusMinusAverage", name=_safe(_leaf(crv)) + "_cvBase%d" % index)
    cmds.setAttr(base + ".operation", 2)               # subtract
    cmds.connectAttr(drv + "." + DRIVER_PHASE, base + ".input1D[0]")
    cmds.connectAttr(drv + "." + DRIVER_PHASE_OFFSET, base + ".input1D[1]")

    time_u = cmds.createNode("multiplyDivide", name=_safe(_leaf(crv)) + "_cvTime%d" % index)
    cmds.setAttr(time_u + ".operation", 2)
    cmds.connectAttr(base + ".output1D", time_u + ".input1X")
    cmds.connectAttr(drv + "." + WAVE_PERIOD, time_u + ".input2X")

    # ---- u = 공간 - 시간  (시간이 커지면 파형이 체인을 따라 진행한다)
    u = cmds.createNode("plusMinusAverage", name=_safe(_leaf(crv)) + "_cvU%d" % index)
    cmds.setAttr(u + ".operation", 2)
    cmds.connectAttr(space + ".outputX", u + ".input1D[0]")
    cmds.connectAttr(time_u + ".outputX", u + ".input1D[1]")

    # ---- s = sineLUT(u)
    lut = cmds.duplicate(template_lut, name=_safe(_leaf(crv)) + "_cvSine%d" % index)[0]
    cmds.connectAttr(u + ".output1D", lut + ".input")

    # ---- ramp_k = 1 + windRootRamp * (arc/total - 1)
    frac = (arc / total) if total > 1e-9 else 1.0
    ramp = cmds.createNode("multDoubleLinear", name=_safe(_leaf(crv)) + "_cvRamp%d" % index)
    cmds.connectAttr(drv + "." + WAVE_ROOT_RAMP, ramp + ".input1")
    cmds.setAttr(ramp + ".input2", frac - 1.0)
    ramp_add = cmds.createNode("addDoubleLinear", name=_safe(_leaf(crv)) + "_cvRampAdd%d" % index)
    cmds.connectAttr(ramp + ".output", ramp_add + ".input1")
    # 첫 CV 는 **항상 고정**한다(windRootRamp 와 무관). 커브 시작점이 루트에 붙어 있어야
    # 체인이 뿌리부터 자연스럽게 풀린다.
    cmds.setAttr(ramp_add + ".input2", 0.0 if index == 0 else 1.0)
    if index == 0:
        cmds.setAttr(ramp + ".input2", 0.0)

    # ---- value = rest + amp * ramp * s
    amp = cmds.createNode("multDoubleLinear", name=_safe(_leaf(crv)) + "_cvAmp%d" % index)
    cmds.connectAttr(lut + ".output", amp + ".input1")
    cmds.connectAttr(drv + "." + WAVE_AMPLITUDE, amp + ".input2")

    scaled = cmds.createNode("multDoubleLinear", name=_safe(_leaf(crv)) + "_cvVal%d" % index)
    cmds.connectAttr(amp + ".output", scaled + ".input1")
    cmds.connectAttr(ramp_add + ".output", scaled + ".input2")

    out = cmds.createNode("addDoubleLinear", name=_safe(_leaf(crv)) + "_cvOut%d" % index)
    cmds.connectAttr(scaled + ".output", out + ".input1")
    cmds.setAttr(out + ".input2", rest_value)

    cmds.connectAttr(out + ".output",
                     "{0}.controlPoints[{1}].{2}Value".format(
                         crv, index, axis.lower()))
    return [space, base, time_u, u, lut, ramp, ramp_add, amp, scaled, out]


def _nudge_eval():
    """IK 솔버를 한 번 다시 풀게 한다.

    ikSpline 은 커브/어트리뷰트가 바뀌어도 **평가가 돌아야** 자세가 갱신된다. 인터랙티브
    마야에서는 뷰포트 새로고침이 그 일을 하지만, 배치/스크립트에서는 아무 일도 일어나지
    않아 방금 만든 셋업이 rest 자세로 보인다. 현재 프레임을 다시 설정해 한 번 풀어 준다.
    """
    try:
        cmds.dgdirty(allPlugs=True)
        cmds.currentTime(cmds.currentTime(query=True), update=True)
    except Exception:
        pass


# --------------------------------------------------------------- 빌드 / 제거

def _build_one(chain, axis, amplitude, wavelength, period, speed, ramp,
               phase_offset):
    """체인 하나에 커브 + ikSpline + 노드망을 만든다. (드라이버, 생성 노드들)"""
    points = _chain_positions(chain)
    arcs = _arc_positions(points)
    total = arcs[-1]
    root_name = _safe(_leaf(chain[0]))

    # 조인트 rest 위치를 CV 로 하는 커브(3차. 조인트가 적으면 차수를 낮춘다).
    degree = min(3, len(points) - 1)
    crv = cmds.curve(name=root_name + "_waveCrv#", degree=degree, point=points)
    crv = cmds.ls(crv, long=True)[0]

    # rootOnCurve=False 가 **중요하다**. 기본값(True)이면 커브 시작점이 움직일 때 마야가
    # 루트 조인트의 translate 를 커브로 끌어당긴다 — "회전만 바꾼다" 는 이 탭의 약속이
    # 깨지고, 셋업을 지운 뒤에도 체인 전체가 통째로 밀린 채 남는다(실측: 전 조인트가
    # 똑같이 Y -1.448).
    handle, effector = cmds.ikHandle(
        name=root_name + "_waveIK#", startJoint=chain[0], endEffector=chain[-1],
        solver="ikSplineSolver", createCurve=False, curve=crv,
        parentCurve=False, rootOnCurve=False)[:2]

    drv = _make_wave_driver(root_name + "_waveDriver#", amplitude, wavelength,
                            period, speed, ramp, phase_offset)
    template = _sine_lut(drv + "_sineTemplate")

    made = [crv, handle, effector, drv]
    n_cv = cmds.getAttr(crv + ".spans") + cmds.getAttr(crv + ".degree")
    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis.upper()]
    for k in range(n_cv):
        # CV 의 rest 좌표와 체인 위 거리. CV 는 조인트 위치에서 만들었으므로 그 순서를 쓴다.
        cv_rest = cmds.pointPosition("{0}.cv[{1}]".format(crv, k), world=True)
        arc = arcs[k] if k < len(arcs) else total
        made += _wire_cv(drv, crv, k, arc, total, cv_rest[axis_index], axis,
                         template)
    cmds.delete(template)
    return drv, made


def build_wave(joints, mode=MODE_ROOT, axis="Y", amplitude=1.0, wavelength=10.0,
               period=24.0, speed=1.0, ramp=1.0, node_offset=0.0,
               output=OUTPUT_NODE, start=0.0, end=100.0, prefix=None):
    """조인트 체인이 **회전만으로** 싸인 파형을 따라가게 만든다.

    joints     : 체인(리스트 순서) 또는 체인 루트들.
    mode       : MODE_CHAIN(리스트가 한 체인) / MODE_ROOT(각 항목이 체인 루트).
    axis       : 파동이 흔드는 **월드 축** ("X"/"Y"/"Z").
    amplitude  : CV 를 미는 양(월드 단위). 실제 흔들림은 커브가 당겨져 조금 작다.
    wavelength : 한 파장의 월드 길이.
    period     : 한 주기의 프레임 수. speed 는 재생 속도(값 = 배속).
    ramp       : 0 = 루트부터 같은 진폭, 1 = 루트 0 에서 끝으로 갈수록 커짐.
    node_offset: 드라이버 k 의 windPhaseOffset = k * node_offset (루트마다 타이밍 차이).
    output     : OUTPUT_NODE(라이브 노드망) / OUTPUT_CURVE(회전 키로 굽고 셋업은 지운다).
    start, end : (curve 출력) 구울 구간.

    Returns: (chains, drivers, message)
    """
    chains, missing, branched = resolve_chains(joints, mode)
    if not chains:
        msg = "[Warning] No usable joint chain."
        if missing:
            msg += " Skipped: {0}".format(", ".join(missing[:5]))
        return 0, 0, msg

    if wavelength <= 0 or period <= 0:
        return 0, 0, "[Warning] Wavelength and Period must be greater than 0."

    drivers, made_all = [], []
    for k, chain in enumerate(chains):
        drv, made = _build_one(chain, axis, amplitude, wavelength, period,
                               speed, ramp, k * node_offset)
        drivers.append(drv)
        made_all += made

    set_name = (prefix or "chainWave") + WAVE_SET_SUFFIX
    node_set = cmds.sets(made_all, name=set_name)

    if output == OUTPUT_CURVE:
        joints_all = [j for chain in chains for j in chain]
        cmds.bakeResults(joints_all, time=(min(start, end), max(start, end)),
                         simulation=True, attribute=["rotateX", "rotateY", "rotateZ"],
                         sampleBy=1, disableImplicitControl=True,
                         preserveOutsideKeys=True)
        cmds.delete([n for n in made_all if cmds.objExists(n)])
        if cmds.objExists(node_set):
            cmds.delete(node_set)
        msg = ("Chain Wave baked: {0} chain(s), {1} joint(s) over [{2:g}-{3:g}f]. "
               "Rotation keys only - the rig setup was removed.".format(
                   len(chains), len(joints_all), min(start, end), max(start, end)))
        drivers = []
    else:
        _nudge_eval()
        msg = ("Chain Wave: {0} chain(s), driver(s) {1}. Edit windAmplitude / "
               "windWavelength / windPeriod / windSpeed / windRootRamp live; "
               "windPhaseOffset shifts one chain's timing. Remove with the "
               "'{2}' set.".format(len(chains), ", ".join(_leaf(d) for d in drivers),
                                   set_name))

    if branched:
        msg += " Branching chain(s) followed the first child: {0}.".format(
            ", ".join(branched[:5]))
    if missing:
        msg += " Skipped: {0}.".format(", ".join(missing[:5]))
    return len(chains), len(drivers), msg


def remove_wave(prefix=None):
    """build_wave 가 만든 셋업을 지운다(조인트 회전은 0 으로 되돌린다).

    Returns: (지운 노드 수, 메시지)
    """
    set_name = (prefix or "chainWave") + WAVE_SET_SUFFIX
    if not cmds.objExists(set_name):
        return 0, "[Warning] Nothing to remove ('{0}' not found).".format(set_name)

    members = [n for n in (cmds.sets(set_name, query=True) or [])
               if cmds.objExists(n)]
    # ikSpline 이 물려 있던 조인트는 회전이 남으므로 0 으로 되돌린다.
    joints = set()
    for node in members:
        if cmds.objectType(node, isAType="ikHandle"):
            start = cmds.ikHandle(node, query=True, startJoint=True)
            end = cmds.ikHandle(node, query=True, endEffector=True)
            chain, _ = _linear_chain(cmds.ls(start, long=True)[0])
            joints.update(chain)
    if members:
        cmds.delete(members)
    if cmds.objExists(set_name):
        cmds.delete(set_name)
    for jnt in joints:
        if not cmds.objExists(jnt):
            continue
        for attr in ("rotateX", "rotateY", "rotateZ"):
            plug = "{0}.{1}".format(jnt, attr)
            if not cmds.listConnections(plug, source=True, destination=False):
                try:
                    cmds.setAttr(plug, 0)
                except Exception:
                    pass
    _nudge_eval()
    return len(members), "Chain Wave removed: {0} node(s); {1} joint(s) reset.".format(
        len(members), len(joints))
