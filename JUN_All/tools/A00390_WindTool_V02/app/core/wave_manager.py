# -*- coding: utf-8 -*-
# A00390_WindTool_V02 core - Chain Wave : 조인트 체인이 **회전만으로** 싸인 파형을 따라가게 한다.
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

import json
import math

import maya.cmds as cmds
from maya.api import OpenMaya as om

from .wind_manager import (
    DRIVER_SPEED, DRIVER_PHASE, DRIVER_PHASE_OFFSET, DRIVER_ENVELOPE,
    MODE_CHAIN, MODE_ROOT, OUTPUT_CURVE, OUTPUT_NODE,
    _make_phase_expression, _sine_lut, _leaf, _safe, follow_root_position,
)


# Chain Wave 드라이버 어트리뷰트(월드 단위).
WAVE_AMPLITUDE = "windAmplitude"      # CV 를 미는 양(월드 단위)
WAVE_WAVELENGTH = "windWavelength"    # 한 파장의 월드 길이
WAVE_PERIOD = "windPeriod"            # 한 주기의 프레임 수
WAVE_ROOT_RAMP = "windRootRamp"       # 0=루트부터 같은 진폭, 1=루트 0 -> 끝 1 로 커짐
# windEnvelope([0,1], wind_manager 의 DRIVER_ENVELOPE)은 **실효 진폭**에 곱해진다:
#     effAmplitude = windAmplitude * windEnvelope
# 0 이면 CV 가 rest 위치 그대로라 커브가 rest 체인을 그대로 지나가고(= 셋업이 없는 것과
# 같은 자세), 0.5 면 절반만 밀리고, 1 이면 완전히 적용된다. 진폭 하나에만 곱하면 되는
# 이유는 CV 변위가 진폭에 정비례하기 때문이다 — 드라이버당 multDoubleLinear 1개면 끝.

# 파동이 흔드는 월드 축.
UP_AXES = ("X", "Y", "Z")

# 생성물을 담는 세트 접미사(Remove 가 이걸로 찾는다).
WAVE_SET_SUFFIX = "_waveSET"

# 빌드 시점의 rest 회전을 적어 두는 세트 어트리뷰트(Remove 가 그 값으로 되돌린다).
WAVE_REST_ATTR = "waveRestRotate"


# --------------------------------------------------------------- 체인 해석

def is_joint(node):
    return cmds.objectType(node, isType="joint")


def _has_shape(node):
    """컨트롤러인가(셰이프가 달린 트랜스폼). 오프셋 그룹은 셰이프가 없다."""
    return bool(cmds.listRelatives(node, shapes=True, fullPath=True))


def _linear_chain(root, limit=200):
    """root 에서 **첫 자식만 따라 내려간** 체인 목록. (chain, branched)

    조인트면 자식 조인트를, **컨트롤러(셰이프 달린 트랜스폼)면 자손 중 셰이프가 있는
    트랜스폼**을 따라간다. FK 리그는 보통 `ctrl > offsetGrp > ctrl > ...` 처럼 중간에
    오프셋 그룹이 끼는데, 그룹은 건너뛰고 컨트롤러만 체인으로 잡는다.

    ikSpline(또는 프록시 조인트)은 갈래 없는 한 줄이어야 하므로, 갈래가 있으면 첫 자식
    쪽을 쓰고 branched=True 로 알려 호출측이 경고할 수 있게 한다.
    """
    joints_mode = is_joint(root)
    chain = [root]
    branched = False
    node = root
    for _ in range(limit):
        if joints_mode:
            found = cmds.listRelatives(node, children=True, type="joint",
                                       fullPath=True) or []
        else:
            # 셰이프가 달린 첫 자손 트랜스폼(오프셋 그룹은 건너뛴다)
            found = []
            frontier = cmds.listRelatives(node, children=True, type="transform",
                                          fullPath=True) or []
            while frontier:
                cur = frontier.pop(0)
                if _has_shape(cur):
                    found.append(cur)
                else:
                    frontier = (cmds.listRelatives(cur, children=True,
                                                   type="transform",
                                                   fullPath=True) or []) + frontier
        if not found:
            break
        if len(found) > 1:
            branched = True
        node = found[0]
        chain.append(node)
    return chain, branched


def resolve_chains(joints, mode):
    """(chains, missing, branched) — chains 는 [[노드...], ...] 각각이 한 줄 체인.

    조인트 체인과 **FK 컨트롤러 체인** 둘 다 받는다(무엇인지는 `_linear_chain` 이 판별).
    """
    missing, branched = [], []
    chains = []

    if mode == MODE_ROOT:
        for root in joints:
            if not cmds.objExists(root):
                missing.append(root)
                continue
            chain, is_branched = _linear_chain(root)
            if len(chain) < 2:
                missing.append(root + " (no child in the chain)")
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


# --------------------------------------------------------------- 컨트롤러(FK) 대응
#
# ikSpline 은 **조인트에만** 걸린다. FK 컨트롤러 체인은 그래서 이렇게 처리한다:
#
#   1. 컨트롤러 위치에 **프록시 조인트 체인**을 만들고(숨김),
#   2. 그 프록시에 지금까지의 파동 셋업(커브 + ikSpline + CV 노드망)을 그대로 걸고,
#   3. 프록시의 **월드 회전 변화량**을 컨트롤러의 rotate 로 옮긴다.
#
# 3번을 행렬로 쓰면:
#
#     ctrlWorld_desired = restCtrlWorld × restProxyWorld⁻¹ × proxyWorld
#     ctrlLocal         = ctrlWorld_desired × ctrl.parentInverseMatrix
#
# 앞 두 항은 빌드 시점에 고정이므로 상수 행렬 하나로 접어 넣는다. 곱의 3×3 블록은 각
# 3×3 블록의 곱이라 **이동 성분이 섞여 있어도 회전은 정확**하다. 그래서 decomposeMatrix 의
# outputRotate 만 쓰고 translate/scale 은 버린다 — 컨트롤러의 위치는 계층이 정한다.
#
# 사이클이 없다: ctrl.rotate 는 **조상**의 parentInverseMatrix 와 프록시에만 의존한다.

def _make_proxy_chain(controls, name, dummy_tip=True):
    """대상 위치에 숨긴 프록시 조인트 체인을 만든다. (joints, group, rest 행렬)

    `dummy_tip=True` 면 **마지막 뼈를 같은 방향·길이로 한 번 더 연장한 가상 조인트**를 끝에
    붙인다. ikSpline 은 **엔드 이펙터 조인트를 회전시키지 않으므로**, 가상 점이 없으면
    체인의 **마지막 노드가 영영 회전값 0** 으로 남는다(실측: 마지막 두 노드의 월드 회전이
    31.6°로 똑같았다 — 팁이 부모 방향을 그냥 물려받은 것). 가상 점을 붙이면 그것이 엔드
    이펙터가 되고 진짜 마지막 노드도 파형을 따라 회전한다.
    (`A00410_SecondaryMotion` 의 `Rotate last node` / KawaiiPhysics 의 dummy bone 과 같은 방식.)
    """
    grp = cmds.group(empty=True, name=name + "_waveProxyGrp#")
    cmds.setAttr(grp + ".visibility", 0)

    points = [cmds.xform(c, query=True, worldSpace=True, translation=True)
              for c in controls]
    if dummy_tip and len(points) >= 2:
        last, prev = points[-1], points[-2]
        points.append([last[k] + (last[k] - prev[k]) for k in range(3)])

    joints = []
    cmds.select(clear=True)
    for i, pos in enumerate(points):
        jnt = cmds.joint(name="{0}_waveProxyJnt{1:02d}#".format(name, i),
                         position=pos)
        joints.append(cmds.ls(jnt, long=True)[0])
    cmds.select(clear=True)

    # 각 조인트가 자식을 향하도록(마지막은 부모 방향을 물려받는다)
    cmds.joint(joints[0], edit=True, orientJoint="xyz", secondaryAxisOrient="yup",
               children=True, zeroScaleOrient=True)
    joints[0] = cmds.ls(cmds.parent(joints[0], grp)[0], long=True)[0]
    # 부모가 바뀌었으니 자손 경로를 다시 읽는다.
    chain, _ = _linear_chain(joints[0])

    # **rest 월드 행렬은 지금 읽어 둔다.** 파동 셋업(ikSpline + CV 노드망)을 건 뒤에 읽으면
    # 이미 휘어진 자세가 rest 로 잡혀 컨트롤러가 엉뚱한 각도로 간다(실측: 루트부터 어긋남).
    rest = [cmds.getAttr(j + ".worldMatrix[0]") for j in chain]
    return chain, grp, rest


def _connect_control(proxy, ctl, name, rest_ctl, rest_proxy_inv):
    """프록시의 월드 회전 변화량을 대상(컨트롤러/조인트) rotate 로 옮긴다. (만든 노드들)

    rest 행렬은 **파동을 걸기 전에** 캡처한 것을 받는다(호출측 책임).

    대상이 **조인트면 `jointOrient` 를 벗겨낸다.** 조인트의 로컬 행렬은 `R × JO` 라,
    구한 로컬 행렬을 그대로 rotate 에 넣으면 JO 가 두 번 먹는다.
    """
    const = _mat_mul(rest_ctl, rest_proxy_inv)     # restCtrlWorld × restProxyWorld⁻¹

    mmx = cmds.createNode("multMatrix", name=name + "_ctlMmx")
    cmds.setAttr(mmx + ".matrixIn[0]", const, type="matrix")
    cmds.connectAttr(proxy + ".worldMatrix[0]", mmx + ".matrixIn[1]")
    cmds.connectAttr(ctl + ".parentInverseMatrix[0]", mmx + ".matrixIn[2]")
    if is_joint(ctl):
        # jointOrient 는 빌드 시점에 고정이라 **상수 행렬**로 넣는다(노드를 더 만들 필요가 없다).
        cmds.setAttr(mmx + ".matrixIn[3]",
                     _mat_inverse(_joint_orient_matrix(ctl)), type="matrix")

    dcm = cmds.createNode("decomposeMatrix", name=name + "_ctlDcm")
    cmds.connectAttr(mmx + ".matrixSum", dcm + ".inputMatrix")
    # 컨트롤러의 회전 순서를 그대로 따른다(xyz 가 아닐 수 있다).
    cmds.connectAttr(ctl + ".rotateOrder", dcm + ".inputRotateOrder")

    for axis in "XYZ":
        plug = "{0}.rotate{1}".format(ctl, axis)
        for src in (cmds.listConnections(plug, source=True, destination=False,
                                         plugs=True) or []):
            cmds.disconnectAttr(src, plug)
    cmds.connectAttr(dcm + ".outputRotate", ctl + ".rotate", force=True)
    return [mmx, dcm]


def _joint_orient_matrix(jnt):
    """조인트의 jointOrient 를 4x4 행렬로. (오일러 순서는 XYZ 고정)"""
    orient = cmds.getAttr(jnt + ".jointOrient")[0]
    euler = om.MEulerRotation(
        *[om.MAngle(v, om.MAngle.kDegrees).asRadians() for v in orient])
    return list(euler.asMatrix())


def _mat_inverse(m):
    """4x4 일반 역행렬(가우스-조던). 스케일이 섞여 있어도 안전하다."""
    a = [list(m[r * 4:r * 4 + 4]) + [1.0 if c == r else 0.0 for c in range(4)]
         for r in range(4)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("Matrix is not invertible.")
        a[col], a[pivot] = a[pivot], a[col]
        div = a[col][col]
        a[col] = [v / div for v in a[col]]
        for r in range(4):
            if r == col:
                continue
            factor = a[r][col]
            if factor:
                a[r] = [v - factor * w for v, w in zip(a[r], a[col])]
    return [v for row in a for v in row[4:]]


def _mat_mul(a, b):
    """4x4 행렬 곱(마야와 같은 행벡터 규약)."""
    out = [0.0] * 16
    for r in range(4):
        for c in range(4):
            out[r * 4 + c] = sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4))
    return out

# --------------------------------------------------------------- 드라이버 / 노드망

def _make_wave_driver(name, amplitude, wavelength, period, speed, ramp,
                      phase_offset=0.0, envelope=1.0, place_at=None):
    """Chain Wave 드라이버 로케이터. 파라미터는 전부 **월드 단위 / 프레임**.

    place_at : 월드 좌표 (x, y, z). 주면 로케이터를 그 자리로 옷긴다(체인 최상단 위에 두기).
               None 이면 원점에 만든다(예전 동작).
    """
    drv = cmds.spaceLocator(name=name)[0]

    if place_at is not None:
        cmds.xform(drv, worldSpace=True, translation=place_at)
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

    # 영향력 [0, 1]. 0 = 파동 없음(rest), 0.5 = 절반, 1 = 완전 적용.
    cmds.addAttr(drv, longName=DRIVER_ENVELOPE, attributeType="double",
                 defaultValue=1.0, minValue=0.0, maxValue=1.0, keyable=True)
    cmds.setAttr(drv + "." + DRIVER_ENVELOPE, max(0.0, min(1.0, envelope)))

    # windPhaseTime = windSpeed 의 시간 적분 (Sine 탭과 같은 표현식 재사용)
    cmds.addAttr(drv, longName=DRIVER_PHASE, attributeType="double", keyable=True)
    _make_phase_expression(drv)
    return drv


def _wire_cv(drv, crv, index, arc, total, rest_value, axis, template_lut,
            amp_plug):
    """CV 하나를 흔든다. amp_plug 는 windAmplitude * windEnvelope 실효 진폭 플러그.

        value = rest + effAmplitude * ramp_k * sineLUT( arc/windWavelength - phase )
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
    cmds.connectAttr(amp_plug, amp + ".input2")

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
               phase_offset, envelope=1.0, driver_at_root=True,
               follow_root=True):
    """체인 하나에 커브 + ikSpline + 노드망을 만든다. (드라이버, 생성 노드들, rest 회전, 미추종)

    체인이 **조인트가 아니면**(FK 컨트롤러) 같은 자리에 숨긴 **프록시 조인트 체인**을 세워
    거기에 파동을 걸고, 프록시의 월드 회전 변화량을 컨트롤러 rotate 로 옮긴다.
    ikSpline 이 조인트에만 걸리기 때문이다.
    """
    # 조인트든 컨트롤러든 **프록시 체인**에 파동을 걸고 회전만 옮긴다.
    #   - ikSpline 은 조인트에만 걸린다(컨트롤러는 애초에 프록시가 필요하다).
    #   - 조인트도 프록시를 쓰면 사용자의 체인에 ikHandle·가상 조인트가 끼지 않는다.
    #   - 프록시 끝의 **가상 조인트(dummy tip)** 덕분에 **마지막 노드도 회전**한다.
    controls = list(chain)

    # 드라이버를 놓을 자리는 **아무것도 만들기 전**에 재 둔다(셀업이 체인을 건드리기 전 rest 위치).
    root_pos = (cmds.xform(controls[0], query=True, worldSpace=True, translation=True)
                if driver_at_root else None)

    rest_rotate = {}
    rest_ctl_world = {}
    for node in controls:
        rest_rotate[node] = list(cmds.getAttr(node + ".rotate")[0])
        rest_ctl_world[node] = cmds.getAttr(node + ".worldMatrix[0]")
    chain, proxy_grp, proxy_rest = _make_proxy_chain(
        controls, _safe(_leaf(controls[0])))

    # 노드 이름은 프록시가 아니라 **원본 체인 루트**(컨트롤러/조인트) 기준으로 짓는다.
    root_name = _safe(_leaf(controls[0] if controls else chain[0]))

    points = _chain_positions(chain)
    arcs = _arc_positions(points)
    total = arcs[-1]

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
                            period, speed, ramp, phase_offset, envelope,
                            place_at=root_pos)

    # 놓기만 하는 게 아니라 **따라다니게** 한다(위치만, constraint 없이 월드 행렬 직결).
    # 프록시가 아니라 **원본 체인 루트**를 따라간다 - 프록시는 숨은 내부 노드다.
    follow_made, follow_skip = ([], None)
    if follow_root:
        follow_made, follow_skip = follow_root_position(drv, controls[0])

    template = _sine_lut(drv + "_sineTemplate")

    # 실효 진폭 = windAmplitude * windEnvelope (커브의 모든 CV 가 공유, 노드 1개).
    amp_env = cmds.createNode("multDoubleLinear", name=drv + "_ampEnvelope")
    cmds.connectAttr(drv + "." + WAVE_AMPLITUDE, amp_env + ".input1")
    cmds.connectAttr(drv + "." + DRIVER_ENVELOPE, amp_env + ".input2")

    made = [crv, handle, effector, drv, amp_env] + follow_made
    n_cv = cmds.getAttr(crv + ".spans") + cmds.getAttr(crv + ".degree")
    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis.upper()]
    for k in range(n_cv):
        # CV 의 rest 좌표와 체인 위 거리. CV 는 조인트 위치에서 만들었으므로 그 순서를 쓴다.
        cv_rest = cmds.pointPosition("{0}.cv[{1}]".format(crv, k), world=True)
        arc = arcs[k] if k < len(arcs) else total
        made += _wire_cv(drv, crv, k, arc, total, cv_rest[axis_index], axis,
                         template, amp_env + ".output")
    cmds.delete(template)

    made.append(proxy_grp)
    for i, node in enumerate(controls):
        if i >= len(chain):
            break
        made += _connect_control(
            chain[i], node, "{0}_ctl{1:02d}".format(root_name, i),
            rest_ctl_world[node], _mat_inverse(proxy_rest[i]))
    return drv, made, rest_rotate, follow_skip


def build_wave(joints, mode=MODE_ROOT, axis="Y", amplitude=1.0, wavelength=10.0,
               period=24.0, speed=1.0, ramp=1.0, node_offset=0.0,
               output=OUTPUT_NODE, start=0.0, end=100.0, prefix=None,
               envelope=1.0, driver_at_root=True):
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
    envelope   : 드라이버 windEnvelope 초기값 [0, 1]. 0 = 파동이 전혀 적용되지 않음(rest),
                 0.5 = 절반, 1 = 완전 적용. 빌드 뒤에도 드라이버에서 라이브 조절/키잉.
    driver_at_root : True 면 드라이버 로케이터를 체인 최상단(루트) 월드 위치에 놓고,
                     node 출력이면 그 자리를 **계속 따라가게** 한다(위치만, constraint 없이
                     `multMatrix + decomposeMatrix` 직결). False 면 예전처럼 원점에 만든다.

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
    rest_all = {}
    no_follow = []
    # 루트 추종은 라이브 노드망일 때만 뜻이 있다 - curve 출력은 구운 뒤 셋업을 지운다.
    follow_root = driver_at_root and output != OUTPUT_CURVE
    for k, chain in enumerate(chains):
        drv, made, rest, follow_skip = _build_one(
            chain, axis, amplitude, wavelength, period,
            speed, ramp, k * node_offset, envelope,
            driver_at_root=driver_at_root, follow_root=follow_root)
        drivers.append(drv)
        made_all += made
        rest_all.update(rest)
        if follow_skip:
            no_follow.append("{0} ({1})".format(_leaf(chain[0]), follow_skip))

    set_name = (prefix or "chainWave") + WAVE_SET_SUFFIX
    node_set = cmds.sets(made_all, name=set_name)
    # Remove 가 회전을 **rest 값**으로 되돌릴 수 있도록 세트에 적어 둔다(0 이 아닐 수 있다).
    cmds.addAttr(node_set, longName=WAVE_REST_ATTR, dataType="string")
    cmds.setAttr(node_set + "." + WAVE_REST_ATTR, json.dumps(rest_all),
                 type="string")

    if output == OUTPUT_CURVE:
        joints_all = sorted(rest_all.keys())
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
        kind = "joint" if all(is_joint(c[0]) for c in chains) else "controller"
        msg = ("Chain Wave [{3}]: {0} chain(s), driver(s) {1} at {5}. Edit "
               "windAmplitude / windWavelength / windPeriod / windSpeed / "
               "windRootRamp live; windPhaseOffset shifts one chain's timing; "
               "windEnvelope [0-1] scales the whole effect (0 = off, 0.5 = half, "
               "now {4:g}). Remove with the '{2}' set.".format(
                   len(chains), ", ".join(_leaf(d) for d in drivers),
                   set_name, kind, envelope,
                   "the chain root (and follows it)" if follow_root
                   else ("the chain root" if driver_at_root else "the origin")))
        if no_follow:
            msg += " Root-follow skipped (would cycle): {0}.".format(
                ", ".join(no_follow[:5]))

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

    # 빌드할 때 적어 둔 rest 회전(컨트롤러는 0 이 아닐 수 있다).
    rest = {}
    if cmds.attributeQuery(WAVE_REST_ATTR, node=set_name, exists=True):
        try:
            rest = json.loads(cmds.getAttr(set_name + "." + WAVE_REST_ATTR) or "{}")
        except ValueError:
            rest = {}

    if members:
        cmds.delete(members)
    if cmds.objExists(set_name):
        cmds.delete(set_name)

    restored = 0
    for node, values in rest.items():
        if not cmds.objExists(node):
            continue
        for attr, value in zip(("rotateX", "rotateY", "rotateZ"), values):
            plug = "{0}.{1}".format(node, attr)
            if cmds.listConnections(plug, source=True, destination=False):
                continue
            try:
                cmds.setAttr(plug, value)
            except Exception:
                pass
        restored += 1
    joints = rest
    _nudge_eval()
    return len(members), ("Chain Wave removed: {0} node(s); {1} target(s) put back "
                          "to their rest rotation.".format(len(members), restored))
