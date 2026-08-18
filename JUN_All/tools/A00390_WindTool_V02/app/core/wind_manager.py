# -*- coding: utf-8 -*-
# A00390_WindTool_V02 core - 본 체인에 싸인 주기함수 키프레임을 찍어 '바람에 일렁이는'
# 애니메이션을 만드는 로직 (maya.cmds, UI 비의존).
#
# 원리
# ----
# 리스트업한 조인트마다 회전(또는 이동) 어트리뷰트에
#     value(t) = amplitude * sin( 2*pi * (t - shift) / period )
# 모양의 커브가 생기도록 키를 찍는다. shift 는 조인트 순번 * offset (계단식 위상 지연).
#
# 대상 해석 모드(mode):
#   chain : 리스트업한 조인트들이 '하나의 체인' — 리스트 순서가 순번(index).
#   root  : 리스트업한 각 조인트를 '체인의 루트' 로 보고, 그 조인트 + 모든 자손 조인트에
#           root 로부터의 깊이(depth)를 순번으로 삼아 같은 파형을 반복 적용.
#
# 키는 **주기의 1/4 지점마다**(0, +A, 0, -A, 0 ...) 계산하되, 기본적으로 **구간 내부의
# 0 교차 키는 빼고 극값(±A)만** 남긴다. spline 탄젠트는 극값만 있을 때 깔끔한 싸인으로
# 보간되지만, 극값 사이 0 교차마다 키가 있으면 그 지점이 평평/각지게 되어 커브가 부드럽지
# 않기 때문이다. 대신 구간 **양끝(start/end)** 에는 그 지점의 실제 싸인 값으로 앵커 키를 둔다.
# 1/4 지점은 quarter = period/4 이므로 period 가 정수가 아니어도(예: 10 -> 2.5, 7.5)
# 소수 프레임에 키가 찍힌다.
#
# 예) rotateX, start=0, end=100, period=12, amplitude=40, offset=10
#   jnt_01(순번 0, shift 0)  : t=0->0, 3->40, 6->0, 9->-40, 12->0, ... (매 12프레임 반복)
#   jnt_02(순번 1, shift 10) : 같은 파형이 +10프레임 밀려서(t=13->40 ...)
#   jnt_03(순번 2, shift 20) : +20프레임 밀려서

import math

import maya.cmds as cmds


# 1/4 주기 격자의 순번(n) 에 따른 sin(n*pi/2) 값: 0, 1, 0, -1 (반복).
# 파이썬 n % 4 는 음수 n 에도 0..3 을 주므로 음의 격자에도 그대로 맞는다.
_SIN_QUARTER = (0.0, 1.0, 0.0, -1.0)

# 지원 축(어트리뷰트). UI 콤보와 공유.
AXES = ["rotateX", "rotateY", "rotateZ", "translateX", "translateY", "translateZ"]

# 대상 해석 모드.
#   chain : 리스트업한 조인트들이 '하나의 체인' — 리스트 순서가 offset 순번.
#   root  : 리스트업한 각 조인트를 '체인의 루트' 로 보고, 그 조인트 + 모든 자손 조인트에
#           대해 root 로부터의 깊이(depth)를 offset 순번으로 파형을 반복 적용.
MODE_CHAIN = "chain"
MODE_ROOT = "root"

# 출력 모드.
#   curve : 조인트에 직접 키를 굽는다(씬 재생으로 애니메이션). 기존 동작.
#   node  : Period/Amplitude/Offset/Speed 어트리뷰트를 가진 null(로케이터) 드라이버 +
#           노드망으로 같은 파형을 '실시간' 재현. 어트리뷰트로 파형을, windSpeed 로
#           재생 속도를 프레임마다 조절할 수 있다. Chain=드라이버 1개, Root=루트 수만큼.
OUTPUT_CURVE = "curve"
OUTPUT_NODE = "node"

# node 모드 드라이버 어트리뷰트.
#   windPeriod/Amplitude/Offset : 파형 파라미터(정적, 실시간 편집).
#   windSpeed : **값 = 재생 속도**(1=보통, 상수로 둬도 계속 재생, 키로 프레임마다 속도 변경).
#   windPhaseTime : 내부 위상 시계. 노드망이 읽는다. **표현식으로 windSpeed 를 시간 적분**한다:
#       windPhaseTime(f) = startFrame + ∫_startFrame^f windSpeed dt   (프레임 사다리꼴)
#     속도는 시간의 적분이므로(단순 time*speed 곱셈이 아니라), windSpeed 를 값으로 바꾸든
#     키로 애니메이션하든 **버튼 없이 즉시 반영**되고, 속도가 변해도 **위상이 역행하지 않는다**
#     (찰랑임이 뒤집히지 않음). windSpeed=1 상수면 windPhaseTime=frame 이라 curve 모드와 같은 위상.
DRIVER_PARAMS = ("windPeriod", "windAmplitude", "windOffset")
DRIVER_SPEED = "windSpeed"
DRIVER_PHASE = "windPhaseTime"
#   windPhaseOffset : 이 드라이버(노드) **전체**의 위상 타이밍 offset(프레임). 드라이버마다
#     다른 값을 주면(특히 Bone Root 모드) 루트들이 서로 다른 타이밍으로 찰랑인다.
DRIVER_PHASE_OFFSET = "windPhaseOffset"

# 키 시간의 부동소수 잡음을 없애기 위한 반올림 자리.
_TIME_ROUND = 5

# node 모드 싸인 LUT 샘플 수(한 주기당). 많을수록 곡선이 매끈.
_LUT_SAMPLES = 16


def _key_times_values(index, start, end, period, amplitude, offset,
                      skip_zero_crossings=True):
    """조인트 순번 index 의 (시간, 값) 목록. 1/4 주기 격자를 [start, end] 로 자른다.

    skip_zero_crossings=True(기본)면 **구간 내부의 0 교차 키를 빼고 극값(±진폭)만** 남긴다.
    spline 탄젠트는 극값만 있을 때 깔끔한 싸인으로 보간되지만, 극값 사이 0 교차마다 키가
    박혀 있으면 그 지점이 평평/각지게 되어 커브가 부드럽지 않다. 대신 구간 **양끝(start,
    end)** 에는 그 지점의 실제 싸인 값으로 앵커 키를 둬, 0 교차를 지워도 커브가 구간 밖으로
    흘러가지 않고 양끝에 고정되게 한다.
    """
    quarter = period / 4.0
    shift = index * offset

    # shift + n*quarter 가 [start, end] 에 들도록 n 범위를 구한다.
    n_min = int(math.ceil((start - shift) / quarter - 1e-9))
    n_max = int(math.floor((end - shift) / quarter + 1e-9))

    keys = {}
    for n in range(n_min, n_max + 1):
        t = round(shift + n * quarter, _TIME_ROUND)
        unit = _SIN_QUARTER[n % 4]
        if skip_zero_crossings and unit == 0.0:
            continue   # 내부 0 교차 키는 건너뛴다(양끝 앵커는 아래에서 처리).
        keys[t] = amplitude * unit

    if skip_zero_crossings:
        for bt in (round(start, _TIME_ROUND), round(end, _TIME_ROUND)):
            if bt not in keys:
                keys[bt] = amplitude * math.sin(2.0 * math.pi * (bt - shift) / period)

    return sorted(keys.items())


def _chain_from_root(root):
    """root 조인트와 그 아래 모든 조인트를 (joint_fullpath, depth) 로 반환(BFS).

    depth 는 root 로부터의 거리(root=0, 자식=1, ...). 이 depth 를 offset 순번으로 써서,
    바람이 체인을 따라 내려가며 아래 조인트일수록 위상이 더 밀린 것처럼 보이게 한다.
    분기(자식이 여럿)면 같은 깊이의 형제는 같은 depth(같은 offset)를 갖는다.
    """
    out = [(root, 0)]
    frontier = [(root, 0)]
    while frontier:
        node, d = frontier.pop(0)
        children = cmds.listRelatives(
            node, children=True, type="joint", fullPath=True) or []
        for c in children:
            out.append((c, d + 1))
            frontier.append((c, d + 1))
    return out


def _resolve_groups(joints, mode):
    """드라이버 단위의 그룹 목록과 missing(없는 노드) 목록을 만든다.

    각 그룹은 [(joint, offset_index), ...] 이고, node 모드에서 **그룹 하나당 드라이버 1개**가
    생긴다(curve 모드는 그룹을 평탄화해 그냥 전부 키를 굽는다).

    chain: 그룹 1개 — 리스트 순서가 offset 순번.
    root : 그룹은 루트마다 1개 — 각 루트의 자손을 depth 를 순번으로. 같은 조인트가 여러
           루트에서 겹쳐 잡히면 처음 것만 쓴다(중복 방지).
    """
    missing = []

    if mode == MODE_ROOT:
        groups = []
        seen = set()
        for root in joints:
            if not cmds.objExists(root):
                missing.append(root)
                continue
            grp = []
            for jnt, depth in _chain_from_root(root):
                if jnt in seen:
                    continue
                seen.add(jnt)
                grp.append((jnt, depth))
            if grp:
                groups.append(grp)
        return groups, missing

    # chain: 그룹 1개
    grp = []
    for i, jnt in enumerate(joints):
        if not cmds.objExists(jnt):
            missing.append(jnt)
            continue
        grp.append((jnt, i))
    return ([grp] if grp else []), missing


# --------------------------------------------------------------- node 모드 헬퍼

def _leaf(name):
    """풀패스/네임스페이스 제거한 짧은 이름."""
    return name.split("|")[-1].split(":")[-1]


def _safe(name):
    """노드 이름에 쓰기 위해 '|' ':' 를 '_' 로."""
    return name.replace("|", "_").replace(":", "_").strip("_")


def _sine_lut(name):
    """정규화 싸인 LUT animCurveUU: input u(주기 1) -> sin(2*pi*u), 무한 반복(cycle).

    Maya 2023 에는 네이티브 sin 노드가 없으므로 한 주기 싸인을 담은 driven 커브를 LUT 로
    쓴다. animCurveUU 는 setInfinity 가 안 먹으므로 preInfinity/postInfinity enum 을 직접
    3(cycle)으로 준다(양끝 값이 모두 0 이라 offset 누적 없이 매끈히 반복).
    """
    crv = cmds.createNode("animCurveUU", name=name)
    for k in range(_LUT_SAMPLES + 1):
        u = k / float(_LUT_SAMPLES)
        cmds.setKeyframe(crv, float=u, value=math.sin(2.0 * math.pi * u))
    cmds.keyTangent(crv, edit=True, itt="spline", ott="spline")
    cmds.setAttr(crv + ".preInfinity", 3)
    cmds.setAttr(crv + ".postInfinity", 3)
    return crv


def _make_driver(name, period, amplitude, offset, speed, phase_offset=0.0):
    """windPeriod/Amplitude/Offset + windSpeed + windPhaseOffset + windPhaseTime(내부 시계)."""
    drv = cmds.spaceLocator(name=name)[0]
    for attr, val in zip(DRIVER_PARAMS, (period, amplitude, offset)):
        cmds.addAttr(drv, longName=attr, attributeType="double",
                     defaultValue=val, keyable=True)
        cmds.setAttr(drv + "." + attr, val)

    # 값 = 속도(1=보통). 키로 프레임마다 속도 조절.
    cmds.addAttr(drv, longName=DRIVER_SPEED, attributeType="double",
                 defaultValue=speed, keyable=True)
    cmds.setAttr(drv + "." + DRIVER_SPEED, speed)

    # 이 드라이버 전체의 위상 타이밍 offset(프레임). 드라이버마다 다르게 주면 서로 다른 타이밍.
    cmds.addAttr(drv, longName=DRIVER_PHASE_OFFSET, attributeType="double",
                 defaultValue=phase_offset, keyable=True)
    cmds.setAttr(drv + "." + DRIVER_PHASE_OFFSET, phase_offset)

    # 내부 위상 시계 = windSpeed 의 시간 적분(표현식). 값/키 무엇을 바꿔도 라이브 반영.
    cmds.addAttr(drv, longName=DRIVER_PHASE, attributeType="double", keyable=True)
    _make_phase_expression(drv)
    return drv


def _make_phase_expression(drv):
    """windPhaseTime = startFrame + ∫ windSpeed dt 를 표현식으로 라이브 계산한다.

    매 프레임 windSpeed 를 startFrame..frame 에서 사다리꼴 적분한다. 상수 속도는 곱셈과
    같고, 가변 속도(키 애니메이션)에서도 위상이 단조 전진해 역행이 없다. windSpeed 를 값으로
    바꾸든 키를 편집하든 **버튼 없이 즉시** 반영된다(표현식이 매 프레임 재평가).
    """
    start = int(round(cmds.playbackOptions(query=True, minTime=True)))
    expr = (
        "float $cf = frame;\n"
        "int $start = {start};\n"
        "int $fend = (int)floor($cf);\n"
        "float $acc = 0.0;\n"
        "float $prev = `getAttr -time $start {drv}.{spd}`;\n"
        "int $f;\n"
        "for ($f = $start + 1; $f <= $fend; $f++) {{\n"
        "  float $s = `getAttr -time $f {drv}.{spd}`;\n"
        "  $acc += 0.5 * ($prev + $s);\n"
        "  $prev = $s;\n"
        "}}\n"
        "float $frac = $cf - $fend;\n"    # 현재 프레임의 소수 잔여 구간
        "if ($frac > 0.0) {{\n"
        "  float $sf = `getAttr -time $cf {drv}.{spd}`;\n"
        "  $acc += 0.5 * ($prev + $sf) * $frac;\n"
        "}}\n"
        "{drv}.{phase} = $start + $acc;\n"
    ).format(start=start, drv=drv, spd=DRIVER_SPEED, phase=DRIVER_PHASE)
    return cmds.expression(string=expr, alwaysEvaluate=True,
                           unitConversion="all", name=drv + "_windInteg")


def _clear_attr_input(jnt, attr):
    """attr 의 기존 키/입력 연결을 끊는다(node 드라이버를 새로 연결하기 전에)."""
    plug = "{0}.{1}".format(jnt, attr)
    try:
        cmds.cutKey(jnt, attribute=attr, clear=True)
    except Exception:
        pass
    for src in (cmds.listConnections(plug, source=True, destination=False,
                                     plugs=True) or []):
        try:
            cmds.disconnectAttr(src, plug)
        except Exception:
            pass


def _wire_group(drv, pairs, attr, template_lut):
    """드라이버 drv 에서 그룹의 각 조인트로 싸인 노드망을 연결한다.

    조인트 j(순번 i) 에 대해:
        value = windAmplitude * sineLUT( (base - i*windOffset) / windPeriod )
        base  = windPhaseTime - windPhaseOffset   (드라이버 전체 타이밍 offset)
    windPhaseTime 은 windSpeed 의 적분(재생 속도가 값에 반영됨, 위상 역행 없음).
    """
    # 드라이버 전체 위상 시계에서 전역 offset 을 뺀 base (그룹 내 모든 조인트 공용).
    base_pma = cmds.createNode("plusMinusAverage", name=drv + "_phaseBase")
    cmds.setAttr(base_pma + ".operation", 2)   # subtract
    cmds.connectAttr(drv + "." + DRIVER_PHASE, base_pma + ".input1D[0]")
    cmds.connectAttr(drv + "." + DRIVER_PHASE_OFFSET, base_pma + ".input1D[1]")
    base = base_pma + ".output1D"

    wired = 0
    for jnt, index in pairs:
        if not cmds.attributeQuery(attr, node=jnt, exists=True):
            continue

        # shift = base - offset*index
        if index != 0:
            mdl_off = cmds.createNode("multDoubleLinear")
            cmds.connectAttr(drv + ".windOffset", mdl_off + ".input1")
            cmds.setAttr(mdl_off + ".input2", index)
            pma = cmds.createNode("plusMinusAverage")
            cmds.setAttr(pma + ".operation", 2)   # subtract
            cmds.connectAttr(base, pma + ".input1D[0]")
            cmds.connectAttr(mdl_off + ".output", pma + ".input1D[1]")
            shift = pma + ".output1D"
        else:
            shift = base

        # u = shift / period
        div = cmds.createNode("multiplyDivide")
        cmds.setAttr(div + ".operation", 2)       # divide
        cmds.connectAttr(shift, div + ".input1X")
        cmds.connectAttr(drv + ".windPeriod", div + ".input2X")

        # s = sineLUT(u)  (템플릿 복제 — 조인트마다 입력이 달라 개별 커브 필요)
        lut = cmds.duplicate(template_lut, name=drv + "_sine_" + _safe(jnt))[0]
        cmds.connectAttr(div + ".outputX", lut + ".input")

        # val = s * amplitude
        mul_amp = cmds.createNode("multDoubleLinear")
        cmds.connectAttr(lut + ".output", mul_amp + ".input1")
        cmds.connectAttr(drv + ".windAmplitude", mul_amp + ".input2")

        _clear_attr_input(jnt, attr)
        cmds.connectAttr(mul_amp + ".output", "{0}.{1}".format(jnt, attr))
        wired += 1

    return wired


def apply_wind(joints, attr, start, end, period, amplitude, offset,
               clear_range=True, tangent="spline", skip_zero_crossings=True,
               mode=MODE_CHAIN, output=OUTPUT_CURVE, speed=1.0, node_offset=0.0):
    """본 체인에 싸인 파형(바람 일렁임)을 적용한다.

    joints     : 조인트 이름 목록.
    attr       : 대상 어트리뷰트('rotateX' 등, AXES 참고).
    start, end : (curve 모드) 키를 만들 프레임 구간(실수 허용).
    period     : 한 주기의 프레임 수(실수 허용, > 0).
    amplitude  : 진폭(피크 값).
    offset     : 순번마다 더해지는 위상 지연(프레임, 실수 허용). 순번 i -> i*offset.
    clear_range: (curve) True 면 각 조인트의 attr 키를 [start, end] 에서 먼저 지운다.
    tangent    : (curve) 키 탄젠트 타입(기본 'spline').
    skip_zero_crossings: (curve) True 면 구간 내부의 0 교차 키를 빼고 극값만 남긴다.
    mode       : MODE_CHAIN(리스트=한 체인) 또는 MODE_ROOT(각 항목=체인 루트).
    output     : OUTPUT_CURVE(조인트에 키 굽기) 또는 OUTPUT_NODE(드라이버 노드망 실시간).
    speed      : (node) 드라이버 windSpeed 초기값(재생 속도 배수).
    node_offset: (node) 드라이버(노드)마다 순번 k 만큼 더해지는 전체 위상 offset 초기값
                 (windPhaseOffset = k*node_offset). Root 모드에서 루트마다 다른 타이밍.

    반환: (count, joint_count, message)  -- curve 면 count=키 수, node 면 count=드라이버 수.
    """
    if not joints:
        return 0, 0, "[Warning] Joint list is empty. Add joints first."
    if attr not in AXES:
        return 0, 0, "[Warning] Unsupported axis: {0}".format(attr)
    if period <= 0:
        return 0, 0, "[Warning] Period must be greater than 0."
    if start > end:
        start, end = end, start

    groups, missing = _resolve_groups(joints, mode)

    if output == OUTPUT_NODE:
        return _apply_nodes(groups, missing, attr, period, amplitude, offset,
                            speed, mode, node_offset)
    return _apply_curve(groups, missing, attr, start, end, period, amplitude, offset,
                        clear_range, tangent, skip_zero_crossings, mode)


def _apply_curve(groups, missing, attr, start, end, period, amplitude, offset,
                 clear_range, tangent, skip_zero_crossings, mode):
    """curve 모드: 그룹을 평탄화해 각 조인트에 키를 굽는다(기존 동작)."""
    total_keys = 0
    keyed = set()

    for jnt, index in [p for grp in groups for p in grp]:
        if not cmds.attributeQuery(attr, node=jnt, exists=True):
            missing.append("{0}.{1}".format(jnt, attr))
            continue

        if clear_range:
            try:
                cmds.cutKey(jnt, attribute=attr, time=(start, end), clear=True)
            except Exception:
                pass

        for t, val in _key_times_values(index, start, end, period, amplitude, offset,
                                        skip_zero_crossings=skip_zero_crossings):
            cmds.setKeyframe(jnt, attribute=attr, time=t, value=val,
                             inTangentType=tangent, outTangentType=tangent)
            total_keys += 1

        keyed.add(jnt)

    if mode == MODE_ROOT:
        head = "Wind keys (root mode): {0} key(s) on {1} joint(s) from {2} root(s)".format(
            total_keys, len(keyed), len(groups))
    else:
        head = "Wind keys (chain mode): {0} key(s) on {1} joint(s)".format(
            total_keys, len(keyed))
    msg = "{0} [{1}] {2}~{3} period={4} amp={5} offset={6}.".format(
        head, attr, start, end, period, amplitude, offset)
    if missing:
        msg += " Skipped: {0}".format(", ".join(missing))
    return total_keys, len(keyed), msg


def _apply_nodes(groups, missing, attr, period, amplitude, offset, speed, mode,
                 node_offset=0.0):
    """node 모드: 그룹마다 드라이버 null 1개 + 싸인 노드망을 만든다.

    드라이버 순번 k 마다 windPhaseOffset = k*node_offset 로 초기화해, Root 모드에서 루트들이
    서로 다른 타이밍으로 찰랑이게 한다(이후 각 드라이버의 windPhaseOffset 을 직접 조절 가능).
    """
    if not groups:
        msg = "[Warning] No valid joints for node driver."
        if missing:
            msg += " Skipped: {0}".format(", ".join(missing))
        return 0, 0, msg

    drivers = []
    wired = 0
    for k, grp in enumerate(groups):
        root_jnt = grp[0][0]
        drv = _make_driver(_leaf(root_jnt) + "_windDriver#",
                           period, amplitude, offset, speed,
                           phase_offset=k * node_offset)
        template = _sine_lut(drv + "_sineTemplate")
        wired += _wire_group(drv, grp, attr, template)
        cmds.delete(template)   # 조인트마다 복제본을 썼으므로 템플릿은 버린다.
        drivers.append(drv)

    mode_label = "root" if mode == MODE_ROOT else "chain"
    head = "Wind node ({0} mode): {1} driver(s) on {2} joint(s)".format(
        mode_label, len(drivers), wired)
    msg = "{0} [{1}] period={2} amp={3} offset={4} speed={5} node_offset={6}. " \
          "Edit windPeriod/Amplitude/Offset/Speed live; windPhaseOffset sets each " \
          "driver's overall timing (per-root).".format(
              head, attr, period, amplitude, offset, speed, node_offset)
    if missing:
        msg += " Skipped: {0}".format(", ".join(missing))
    return len(drivers), wired, msg
