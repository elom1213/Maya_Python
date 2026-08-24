# -*- coding: utf-8 -*-
# A00390_WindTool_V03 core - 본 체인에 싸인 주기함수 키프레임을 찍어 '바람에 일렁이는'
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
#   windEnvelope : [0, 1] 의 **영향력**. 디포머의 envelope 과 같은 뜻이다.
#     0 = 노드가 전혀 영향을 주지 않는다, 0.5 = 절반, 1 = 완전히 적용(기본).
#     구현은 **진폭에 곱하는 것 하나**로 끝난다 — 파형 값이 진폭에 정비례하기 때문에
#     envelope 를 진폭에 한 번만 곱하면 아래 모든 조인트가 같은 비율로 줄어든다.
#     (드라이버당 multDoubleLinear 1개. 조인트마다 노드를 더 만들지 않는다.)
DRIVER_ENVELOPE = "windEnvelope"

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


def _long(node):
    """풀패스. 없는 노드면 None."""
    return (cmds.ls(node, long=True) or [None])[0]


def _is_ancestor(maybe_ancestor, node):
    """maybe_ancestor 가 node 의 조상이면 True (풀패스 접두 비교)."""
    a, n = _long(maybe_ancestor), _long(node)
    if not a or not n:
        return False
    return n.startswith(a + "|")


def follow_root_position(driver, root):
    """드라이버 로케이터가 root 의 **월드 위치**를 따라다니게 한다. (만든 노드들, 건너뛴 사유)

    **constraint 를 쓰지 않는다.** root 의 월드 행렬을 드라이버의 부모 공간으로 되돌려
    translate 에 그대로 넣는다:

        multMatrix(root.worldMatrix[0], driver.parentInverseMatrix[0])
            -> decomposeMatrix.outputTranslate -> driver.translate

    회전·스케일은 건드리지 않는다(요청대로 **위치만**). 그래서 드라이버는 리그를 씬에서
    옮기거나 루트 컨트롤러를 움직여도 늘 자기가 구동하는 뼈 위에 붙어 있다.

    ## 왜 사이클이 안 나는가

    `parentInverseMatrix` 는 **부모**의 월드 역행렬이라 드라이버 **자신의** translate 에
    의존하지 않는다(`worldInverseMatrix` 를 쓰면 자기 translate 를 읽어 진짜 사이클이 된다 —
    디버그 커브가 커브 자신이 아니라 CV 를 쓰기 때문에 거기서는 안전했던 것과 같은 이유다).

    드라이버의 wind* 어트리뷰트 -> ... -> root.rotate -> root.worldMatrix -> driver.translate
    는 driver.translate 로 되돌아오지 않으므로 경로가 닫히지 않는다.

    사이클이 되는 배치는 하나뿐이다 — **드라이버가 root 의 조상**인 경우(그러면
    root.worldMatrix 가 드라이버의 translate 에 의존한다). 그때는 연결하지 않고 사유를
    돌려준다.
    """
    if not (cmds.objExists(driver) and cmds.objExists(root)):
        return [], "node missing"

    if _is_ancestor(driver, root):
        return [], "driver is an ancestor of the root"

    tag = _safe(_leaf(driver)) + "_rootFollow"
    mmx = cmds.createNode("multMatrix", name=tag + "Mmx")
    cmds.connectAttr(root + ".worldMatrix[0]", mmx + ".matrixIn[0]")
    cmds.connectAttr(driver + ".parentInverseMatrix[0]", mmx + ".matrixIn[1]")

    dcm = cmds.createNode("decomposeMatrix", name=tag + "Dcm")
    cmds.connectAttr(mmx + ".matrixSum", dcm + ".inputMatrix")
    cmds.connectAttr(dcm + ".outputTranslate", driver + ".translate", force=True)
    return [mmx, dcm], None


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


def _make_driver(name, period, amplitude, offset, speed, phase_offset=0.0,
                 envelope=1.0, place_at=None):
    """windPeriod/Amplitude/Offset + windSpeed + windPhaseOffset + windEnvelope + windPhaseTime.

    place_at : 월드 좌표 (x, y, z). 주면 로케이터를 그 자리로 옮긴다(그룹 최상단 위에 두기).
               None 이면 원점에 만든다(예전 동작).
    """
    drv = cmds.spaceLocator(name=name)[0]

    if place_at is not None:
        cmds.xform(drv, worldSpace=True, translation=place_at)
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

    # 영향력 [0, 1]. minValue/maxValue 로 구간을 강제한다(그 밖의 값은 마야가 잘라 낸다).
    cmds.addAttr(drv, longName=DRIVER_ENVELOPE, attributeType="double",
                 defaultValue=1.0, minValue=0.0, maxValue=1.0, keyable=True)
    cmds.setAttr(drv + "." + DRIVER_ENVELOPE, max(0.0, min(1.0, envelope)))

    # 내부 위상 시계. 배선은 호출부가 wire_phase() 로 한다(상수 속도면 노드 3개,
    # windSpeed 에 키가 걸려 있으면 통합 표현식). V02 는 여기서 드라이버마다 표현식을
    # 하나씩 만들었고 그게 재생 비용의 99.8% 였다 - 위 '위상 시계 엔진' 주석 참고.
    cmds.addAttr(drv, longName=DRIVER_PHASE, attributeType="double", keyable=True)
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


# =====================================================================
# 위상 시계(windPhaseTime) 엔진  —  V03 에서 통째로 바뀐 부분
# =====================================================================
#
# ## V02 가 왜 느렸나 (실측)
#
# V02 는 드라이버마다 `expression` 노드를 하나 붙이고, 그 안에서 매 프레임
# **시작 프레임부터 현재 프레임까지 `getAttr -time` 을 반복 호출**해 windSpeed 를
# 사다리꼴 적분했다(`_make_phase_expression`, 아래에 참조용으로 남겨 둔다).
#
# `getAttr -time` 은 값 읽기가 아니라 **DG 를 그 시각으로 평가**하는 호출이다.
# 프레임 100 이면 드라이버 하나가 99번, 드라이버 30개면 한 프레임에 약 3,000번.
# 재생 비용의 **99.8%** 가 여기였다(30체인 58.72ms -> 표현식만 지우면 0.10ms).
# 비용이 **체인 개수 x 프레임 번호**라 재생할수록 느려졌다(30체인 기준 프레임
# 1-20 은 11ms, 180-200 은 114ms).
#
# ## V03 이 하는 것 — 속도에 따라 두 경로
#
#   windSpeed 가 **상수** (기본, 대부분)
#       -> 노드 3개.  상수의 적분은 곱셈 한 번이다:
#              phase = start + speed * (frame - start)
#          time1.outTime -> addDoubleLinear(-start) -> multDoubleLinear(xspeed)
#                        -> addDoubleLinear(+start) -> drv.windPhaseTime
#          **결과 회전값이 V02 와 완전히 같다**(실측 0.000e+00). 30체인 0.64ms.
#
#   windSpeed 에 **키가 걸림**
#       -> keyframe -q 로 **키 데이터를 직접 읽어** 구간 적분하는 표현식.
#          커브 조회는 DG 평가가 아니라서 싸고, 비용이 키 개수에만 붙어
#          **프레임 번호와 무관**하다. 키를 고치면 즉시 반영되는 **진짜 라이브**다.
#
# ## 표현식은 개수가 비용이다 — 그래서 씬에 하나만 둔다
#
# 실측(30체인 전부 키 걸린 최악):
#
#     V02 방식 (getAttr -time)              63.49 ms
#     키 데이터 적분, 표현식 30개            5.84 ms
#     키 데이터 적분, 표현식 1개로 통합      1.38 ms   <- V03
#     참고: 계산이 없는 빈 표현식 30개       0.65 ms
#
# 계산을 하지 않는 빈 표현식 30개만으로 0.65ms 다. **내용보다 개수가 중요하다.**
# 그래서 V03 은 씬에 `windPhaseEngine` 표현식을 **하나만** 두고, 키가 걸린 드라이버
# 전부를 그 안에서 계산한다.
#
# ## 알아 둘 것 — spline 탄젠트에서 V02 와 값이 다르다
#
# V02 는 **프레임 단위** 사다리꼴, V03 은 **키 구간** 선형 적분이라 키 사이의 곡률을
# 놓친다. `linear` 탄젠트면 값이 정확히 일치하고, 기본 `spline` 에서는 어긋난다
# (실측 최대값의 21%). 표현식 안에서 커브를 프레임 단위로 평가할 방법을 찾아봤지만
# **없다** — `keyframe -q -eval` 의 `-t` 는 TimeRange 리터럴이라 루프 변수를 받지
# 못하고(MEL/표현식 양쪽 문법 4종 전부 실패), 남는 것은 `getAttr -time` 뿐인데
# 그게 바로 V02 를 느리게 한 원인이다.
#
# V02 와 값을 정확히 맞춰야 하면 `bake_phase_time()` 으로 구우면 된다(값 동일, 라이브 X).

# 씬에 하나만 두는 통합 위상 표현식의 이름.
PHASE_ENGINE = "windPhaseEngine"

# 노드 경로가 만드는 노드의 이름 접미사(다시 배선할 때 찾아 지운다).
_PHASE_NODE_SUFFIXES = ("_phaseSub", "_phaseMul", "_phaseAdd")


def _speed_curve(drv):
    """windSpeed 를 구동하는 animCurve. 없으면 None(= 상수 속도)."""
    if not cmds.objExists(drv + "." + DRIVER_SPEED):
        return None
    curves = cmds.listConnections(drv + "." + DRIVER_SPEED, source=True,
                                  destination=False, type="animCurve") or []
    return curves[0] if curves else None


def _is_phase_node(node):
    return node.split("|")[-1].endswith(_PHASE_NODE_SUFFIXES)


def _clear_phase_input(drv):
    """windPhaseTime 에 물려 있던 것을 걷어낸다(노드 경로 / 구운 커브 / 표현식 출력).

    이름으로 찾지 않고 **연결을 따라간다** - 드라이버가 그룹 안으로 들어가 풀패스가
    되어도(`|grp|drv`) 안전하다.
    """
    plug = drv + "." + DRIVER_PHASE
    removed = []

    for src in (cmds.listConnections(plug, source=True, destination=False) or []):
        if _is_phase_node(src):
            # 이 phase 노드망 전체(상류 포함)를 지운다.
            hist = cmds.listHistory(src) or []
            targets = [h for h in hist if _is_phase_node(h) and cmds.objExists(h)]
            if targets:
                cmds.delete(targets)
                removed += targets
        elif cmds.nodeType(src).startswith("animCurve"):
            if cmds.objExists(src):
                cmds.delete(src)
                removed.append(src)

    # 남은 입력 연결(표현식 출력 등) 끊기
    for src in (cmds.listConnections(plug, source=True, destination=False,
                                     plugs=True) or []):
        try:
            cmds.disconnectAttr(src, plug)
        except RuntimeError:
            pass
    return removed


def _make_phase_time_nodes(drv, start):
    """상수 속도용 노드 경로. phase = start + windSpeed * (frame - start).

    `time1.outTime` 은 `addDoubleLinear` 에 연결할 때 unitConversion 이 끼지 않고
    **프레임 번호가 그대로** 들어온다(film/ntsc/pal/game 전부 확인). 표현식의 `frame`
    변수와 의미가 같다.
    """
    tag = _safe(_leaf(drv))

    sub = cmds.createNode("addDoubleLinear", name=tag + "_phaseSub")
    cmds.connectAttr("time1.outTime", sub + ".input1")
    cmds.setAttr(sub + ".input2", -float(start))

    mul = cmds.createNode("multDoubleLinear", name=tag + "_phaseMul")
    cmds.connectAttr(sub + ".output", mul + ".input1")
    cmds.connectAttr(drv + "." + DRIVER_SPEED, mul + ".input2")

    add = cmds.createNode("addDoubleLinear", name=tag + "_phaseAdd")
    cmds.connectAttr(mul + ".output", add + ".input1")
    cmds.setAttr(add + ".input2", float(start))
    cmds.connectAttr(add + ".output", drv + "." + DRIVER_PHASE, force=True)
    return [sub, mul, add]


def _integral_snippet(index, drv, start):
    """키 데이터를 읽어 구간 적분하는 MEL 조각. 통합 표현식에 이어 붙인다.

    MEL 은 블록 스코프가 없어 같은 변수명을 다시 선언하면 에러다. 그래서 드라이버마다
    변수 이름에 **번호를 붙인다**($t0, $t1 ...).

    첫 키 앞 구간은 커브 값이 첫 키 값으로 일정하므로(preInfinity constant) 그만큼을
    먼저 더한다 — 그래야 start 가 첫 키보다 앞이어도 V02 와 같은 뜻이 된다.

    커브 노드 이름이 아니라 **`drv.windSpeed` plug** 를 조회한다. 커브 이름을 박아 두면
    사용자가 키를 지우는 순간(`cutKey -clear`) 표현식이 없는 이름을 찾아 매 프레임 에러를
    쏟는다. plug 로 물으면 커브가 사라져도 **빈 배열**이 와서 `$n == 0` 가드에 걸리고,
    그동안 위상은 start 로 고정된다(다음 Rebuild Phase 에서 노드 경로로 복귀).
    """
    i = index
    return u"""
float $t{i}[] = `keyframe -q -timeChange {drv}.{speed}`;
float $v{i}[] = `keyframe -q -valueChange {drv}.{speed}`;
int $n{i} = size($t{i});
float $cf{i} = frame;
float $acc{i} = 0.0;
if ($n{i} > 0) {{
  float $head{i} = ($cf{i} < $t{i}[0]) ? $cf{i} : $t{i}[0];
  if ($head{i} > {start}) $acc{i} += $v{i}[0] * ($head{i} - {start});
  int $i{i};
  for ($i{i} = 0; $i{i} < $n{i} - 1; $i{i}++) {{
    float $a{i} = $t{i}[$i{i}];
    float $b{i} = $t{i}[$i{i} + 1];
    if ($cf{i} <= $a{i}) break;
    float $e{i} = ($cf{i} < $b{i}) ? $cf{i} : $b{i};
    float $w{i} = ($e{i} - $a{i}) / ($b{i} - $a{i});
    float $ve{i} = $v{i}[$i{i}] + ($v{i}[$i{i} + 1] - $v{i}[$i{i}]) * $w{i};
    $acc{i} += 0.5 * ($v{i}[$i{i}] + $ve{i}) * ($e{i} - $a{i});
  }}
  if ($cf{i} > $t{i}[$n{i} - 1])
    $acc{i} += $v{i}[$n{i} - 1] * ($cf{i} - $t{i}[$n{i} - 1]);
}}
{drv}.{phase} = {start} + $acc{i};
""".format(i=i, drv=drv, speed=DRIVER_SPEED, phase=DRIVER_PHASE,
           start=float(start))


def all_wind_drivers():
    """씬의 바람 드라이버 전부(windPhaseTime + windSpeed 를 가진 트랜스폼)."""
    out = []
    for node in (cmds.ls(type="transform", long=True) or []):
        if cmds.objExists(node + "." + DRIVER_PHASE) and \
                cmds.objExists(node + "." + DRIVER_SPEED):
            out.append(node)
    return out


def wire_phase(drivers, start=None):
    """드라이버들의 windPhaseTime 을 다시 배선한다. (만든 노드, 상수 수, 키 수)

    상수 속도는 노드 3개, 키가 걸린 것은 **씬에 하나뿐인 통합 표현식**이 맡는다.
    이미 물려 있던 것(노드/구운 커브/표현식)은 먼저 걷어낸다.
    """
    if start is None:
        start = int(round(cmds.playbackOptions(query=True, minTime=True)))

    drivers = [d for d in drivers if cmds.objExists(d)]

    # 통합 표현식은 씬에 하나뿐이다 - 항상 지우고 다시 만든다.
    if cmds.objExists(PHASE_ENGINE):
        cmds.delete(PHASE_ENGINE)

    per_driver, snippets, const_n = {}, [], 0
    for drv in drivers:
        _clear_phase_input(drv)
        curve = _speed_curve(drv)
        if curve is None:
            per_driver[drv] = _make_phase_time_nodes(drv, start)
            const_n += 1
        else:
            snippets.append(drv)

    made = [n for nodes in per_driver.values() for n in nodes]

    if snippets:
        body = "".join(_integral_snippet(k, drv, start)
                       for k, drv in enumerate(snippets))
        expr = cmds.expression(string=body, alwaysEvaluate=True,
                               unitConversion="all", name=PHASE_ENGINE)
        made.append(expr)
        # 통합 표현식은 씬에 하나뿐이라 특정 드라이버에 귀속시키지 않는다.
        # (Remove 로 드라이버가 사라지면 rewire_scene_phase 가 다시 만든다.)

    return made, const_n, len(snippets), per_driver


def _adopt_into_sets(per_driver):
    """새로 만든 phase 노드를 **그 드라이버가 속한** objectSet 에 넣는다.

    그래야 Remove 가 자기 빌드의 것만 지운다(여러 번 빌드한 씬에서 섞이지 않는다).
    """
    for drv, nodes in per_driver.items():
        sets = [st for st in (cmds.listSets(object=drv) or [])
                if cmds.nodeType(st) == "objectSet"]
        if not sets:
            continue
        for node in nodes:
            if cmds.objExists(node) and not cmds.listSets(object=node):
                try:
                    cmds.sets(node, addElement=sets[0])
                except RuntimeError:
                    pass


def rewire_scene_phase(start=None):
    """씬의 모든 바람 드라이버를 다시 배선한다(UI 의 Rebuild Phase). (개수, msg)"""
    drivers = all_wind_drivers()
    if not drivers:
        return 0, "[Warning] No wind driver found in the scene."

    made, const_n, keyed_n, per_driver = wire_phase(drivers, start)
    _adopt_into_sets(per_driver)

    msg = ("Phase rebuilt for {0} driver(s): {1} constant (node path), "
           "{2} keyed (live integral in one '{3}' expression).".format(
               len(drivers), const_n, keyed_n, PHASE_ENGINE))
    if keyed_n:
        msg += (" Keyed windSpeed is integrated from the curve data, so editing "
                "those keys updates the wave immediately - no rebuild needed.")
    return len(drivers), msg


def bake_phase_time(drv, start=None, end=None):
    """windPhaseTime 을 animCurve 로 굽는다 — **V02 와 값이 정확히 같은** 경로.

    V02 표현식과 같은 **프레임 단위 사다리꼴**로 적분하므로 spline 탄젠트에서도 값이
    일치한다(실측 diff 0.000e+00). 대신 라이브가 아니다 — windSpeed 키를 고치면 다시
    구워야 한다.
    """
    if start is None:
        start = int(round(cmds.playbackOptions(query=True, minTime=True)))
    if end is None:
        end = int(round(cmds.playbackOptions(query=True, maxTime=True)))
    start, end = int(round(min(start, end))), int(round(max(start, end)))

    plug = drv + "." + DRIVER_SPEED
    speeds = {f: cmds.getAttr(plug, time=f) for f in range(start, end + 1)}

    _clear_phase_input(drv)

    acc = 0.0
    cmds.setKeyframe(drv + "." + DRIVER_PHASE, time=start, value=float(start))
    for f in range(start + 1, end + 1):
        acc += 0.5 * (speeds[f - 1] + speeds[f])
        cmds.setKeyframe(drv + "." + DRIVER_PHASE, time=f, value=start + acc)
    cmds.keyTangent(drv + "." + DRIVER_PHASE, edit=True, itt="spline", ott="spline")
    return end - start + 1


def bake_scene_phase(start=None, end=None):
    """씬의 모든 드라이버 위상을 굽는다(값을 V02 와 정확히 맞춰야 할 때). (개수, msg)"""
    drivers = all_wind_drivers()
    if not drivers:
        return 0, "[Warning] No wind driver found in the scene."

    if cmds.objExists(PHASE_ENGINE):
        cmds.delete(PHASE_ENGINE)

    total = 0
    for drv in drivers:
        total += bake_phase_time(drv, start, end)
    return len(drivers), (
        "Phase baked to keys for {0} driver(s), {1} key(s). Values match the V02 "
        "expression exactly, but this is NOT live - press Rebuild Phase (or bake "
        "again) after editing windSpeed.".format(len(drivers), total))


# =====================================================================
# 체인 mute  —  원하는 체인만 남기고 나머지의 평가를 멈춘다 (V03 신규)
# =====================================================================
#
# ## windEnvelope 로는 안 되는 이유
#
# `windEnvelope = 0` 은 **스윙 각도에 0을 곱할 뿐** 노드망은 그대로 다 평가된다.
# 실측으로 30체인에서 envelope 1.0 이 62.97ms, 0.0 이 63.18ms 로 **차이가 없었다**.
# Maya DG 는 "값이 0이니 위쪽 계산을 건너뛰자" 를 하지 않는다 - 곱셈 노드가 결과를
# 내려면 두 입력이 다 필요하기 때문이다. **값을 0으로 만드는 것과 평가를 막는 것은
# 전혀 다른 일이다.**
#
# ## 그래서 nodeState 를 쓴다
#
#   0 Normal       정상 평가
#   1 HasNoEffect  계산을 건너뛰고 입력을 그대로 통과
#   2 Blocking     출력을 **마지막 값으로 고정**
#
# mute 는 이 순서로 한다:
#
#   1. windEnvelope 를 0 으로 두고 **한 번 평가**시킨다 -> 체인이 rest 자세가 된다.
#   2. 그 체인의 노드망을 전부 `nodeState = 2 (Blocking)` 으로 -> 출력이 **rest 를 만드는
#      값에 고정**된다.
#   3. windEnvelope 를 원래 값으로 되돌린다(Blocking 이라 반영되지 않고, 값만 보존된다).
#
# 그래서 mute 한 체인은 **흔들리다 멈춘 어정쩡한 포즈가 아니라 rest 자세**로 선다.
# unmute 는 nodeState 를 0 으로 되돌리기만 하면 된다.
#
# **`HasNoEffect(1)` 이 아니라 `Blocking(2)` 이어야 한다.** 둘 다 재 봤다:
#
#   자세 (envelope 0 으로 rest 를 만든 뒤 끄기)
#       HasNoEffect ->  0.000  -5.000   5.000  15.000 -15.000   (rest 가 아니다)
#       Blocking    ->  0.000  -0.000   0.000   0.000   0.000   (rest)
#   성능 (200체인 중 198개 mute)
#       HasNoEffect -> 2.51ms -> 2.33ms   (이득이 거의 없다)
#       Blocking    -> 4.63ms -> 2.01ms   (498 fps)
#
# HasNoEffect 는 "계산하지 않고 입력을 통과" 라 0 을 만들지 못한다.
#
# ## 무엇을 끄는가
#
# 드라이버의 **`wind*` 어트리뷰트가 구동하는 노드망 전부**다. 조인트/컨트롤러
# (transform)는 **건드리지 않는다** - 그것들은 이 툴의 소유가 아니고, 애니메이터가
# 다른 채널을 계속 써야 한다.
#
# `listHistory -future` 는 **쓸 수 없다.** 실측하면 드라이버 로케이터의 Shape 하나만
# 돌려준다(로케이터의 wind* 어트리뷰트 연결은 셰이프/디포머 히스토리가 아니기 때문).
# 그래서 `listAttr -userDefined` 의 destination 에서 시작해 **직접 너비 우선으로**
# 내려간다. 조인트/트랜스폼을 만나면 거기서 멈춘다.
#
# ## 성능은 부수 효과일 뿐이다
#
# 위상 엔진을 고친 뒤에는 노드망이 이미 싸서 mute 의 이득이 크지 않다(실측 200체인
# 4.28ms -> 198체인 mute 2.29ms, 2배 미만). mute 의 값어치는 성능이 아니라
# **"지금 보고 싶은 체인만 흔들리게 한다"** 는 작업 편의에 있다.

DRIVER_MUTE = "windMute"

# mute 대상에서 제외할 노드 타입. 조인트/컨트롤러와 드라이버 자신은 끄지 않는다.
_MUTE_SKIP_TYPES = ("joint", "transform", "objectSet", "expression",
                    "nurbsCurve", "mesh", "camera")


def ensure_mute_attr(drv):
    """드라이버에 windMute (bool) 를 보장한다."""
    if not cmds.objExists(drv + "." + DRIVER_MUTE):
        cmds.addAttr(drv, longName=DRIVER_MUTE, attributeType="bool",
                     defaultValue=False, keyable=False)
        cmds.setAttr(drv + "." + DRIVER_MUTE, channelBox=True)
    return drv + "." + DRIVER_MUTE


def _walk_downstream(drv):
    """드라이버의 wind* 어트리뷰트가 구동하는 것을 전부 모은다. (노드망, 트랜스폼)

    조인트/트랜스폼을 만나면 **거기서 멈춘다** - 그 너머(자식 조인트, 다른 리그)는
    이 드라이버의 것이 아니다.
    """
    seen, stack = set(), []
    for attr in (cmds.listAttr(drv, userDefined=True) or []):
        plug = drv + "." + attr
        if not cmds.objExists(plug):
            continue
        stack += (cmds.listConnections(plug, source=False, destination=True) or [])

    network, transforms = [], []
    while stack:
        node = stack.pop()
        if node in seen or not cmds.objExists(node):
            continue
        seen.add(node)

        if cmds.nodeType(node) in ("joint", "transform"):
            if node != drv and _leaf(node) != _leaf(drv):
                transforms.append(node)
            continue                       # 트랜스폼 너머로는 내려가지 않는다

        if cmds.nodeType(node) not in _MUTE_SKIP_TYPES \
                and not _is_phase_node(node) \
                and cmds.objExists(node + ".nodeState"):
            network.append(node)

        stack += (cmds.listConnections(node, source=False, destination=True) or [])

    return network, transforms


def _debug_curve_parts(driven):
    """이 체인을 따라 그리는 디버그 커브. (커브 트랜스폼, 그 커브를 먹이는 노드들)

    커브 CV 는 **조인트의 worldMatrix** 를 읽는다 - 드라이버가 아니라 조인트 하류다.
    `_walk_downstream` 은 트랜스폼에서 멈추므로 여기서 따로 따라간다.

    커브를 숨기는 것이 뷰포트에서 특히 크다(실측 200체인 mute 후 2.23ms -> 1.74ms).
    """
    curves, feeders, seen = [], [], set()
    for tr in driven:
        plug = tr + ".worldMatrix"
        if not cmds.objExists(plug):
            continue
        stack = list(cmds.listConnections(plug, source=False, destination=True) or [])
        while stack:
            node = stack.pop()
            if node in seen or not cmds.objExists(node):
                continue
            seen.add(node)
            if cmds.nodeType(node) == "nurbsCurve":
                for par in (cmds.listRelatives(node, parent=True, fullPath=True) or []):
                    if par not in curves:
                        curves.append(par)
                continue
            if cmds.objExists(node + ".nodeState"):
                feeders.append(node)
            stack += (cmds.listConnections(node, source=False,
                                           destination=True) or [])
    return curves, feeders


def _mutable_nodes(drv):
    """이 드라이버가 구동하는 노드 중 nodeState 를 건드려도 되는 것들."""
    return _walk_downstream(drv)[0]


def _driven_transforms(drv):
    """이 드라이버가 회전을 물려 준 트랜스폼(조인트/컨트롤러)."""
    return _walk_downstream(drv)[1]


def set_chain_mute(drv, mute):
    """드라이버 하나의 체인을 끄거나(rest 자세로 고정) 되돌린다. (바뀐 노드 수)"""
    ensure_mute_attr(drv)
    nodes, driven = _walk_downstream(drv)
    curves, feeders = _debug_curve_parts(driven)

    if mute:
        # 1) envelope 0 으로 rest 자세를 만든 뒤 2) 그 상태로 고정한다.
        env_plug = drv + "." + DRIVER_ENVELOPE
        had_env = cmds.objExists(env_plug)
        old_env = cmds.getAttr(env_plug) if had_env else None
        env_locked = bool(cmds.listConnections(env_plug, source=True,
                                               destination=False)) if had_env else False
        if had_env and not env_locked:
            cmds.setAttr(env_plug, 0.0)
            # rest 자세를 실제로 계산시킨다(읽어야 DG 가 돈다).
            for tr in driven:
                try:
                    cmds.getAttr(tr + ".rotate")
                except RuntimeError:
                    pass

        for node in nodes + feeders:
            try:
                cmds.setAttr(node + ".nodeState", 2)      # Blocking
            except RuntimeError:
                pass
        for crv in curves:
            try:
                cmds.setAttr(crv + ".visibility", 0)
            except RuntimeError:
                pass

        if had_env and not env_locked:
            cmds.setAttr(env_plug, old_env)               # 값만 복원(Blocking 이라 무해)
    else:
        for node in nodes + feeders:
            try:
                cmds.setAttr(node + ".nodeState", 0)      # Normal
            except RuntimeError:
                pass
        for crv in curves:
            try:
                cmds.setAttr(crv + ".visibility", 1)
            except RuntimeError:
                pass

    cmds.setAttr(drv + "." + DRIVER_MUTE, bool(mute))
    return len(nodes) + len(feeders)


def set_mute_all(mute, drivers=None):
    """씬(또는 주어진) 드라이버 전부를 끄거나 되돌린다. (드라이버 수, 노드 수, msg)"""
    drivers = [d for d in (drivers or all_wind_drivers()) if cmds.objExists(d)]
    if not drivers:
        return 0, 0, "[Warning] No wind driver found in the scene."

    total = sum(set_chain_mute(d, mute) for d in drivers)
    word = "muted" if mute else "unmuted"
    return len(drivers), total, "{0} {1} chain(s) ({2} node(s)).".format(
        word.capitalize(), len(drivers), total)


def solo_chains(keep, drivers=None):
    """keep 에 든 드라이버만 남기고 나머지를 끈다. (남긴 수, 끈 수, msg)"""
    drivers = [d for d in (drivers or all_wind_drivers()) if cmds.objExists(d)]
    if not drivers:
        return 0, 0, "[Warning] No wind driver found in the scene."

    keep_leaf = set(_leaf(k) for k in keep)
    kept, muted = 0, 0
    for drv in drivers:
        on = _leaf(drv) in keep_leaf
        set_chain_mute(drv, not on)
        kept += 1 if on else 0
        muted += 0 if on else 1

    if not kept:
        return 0, muted, ("[Warning] None of the selected nodes is a wind driver - "
                          "everything got muted. Select the driver locator(s).")
    return kept, muted, (
        "Solo: {0} chain(s) left playing, {1} muted (they hold their rest pose and "
        "stop evaluating).".format(kept, muted))


def muted_drivers():
    """지금 mute 상태인 드라이버 목록."""
    return [d for d in all_wind_drivers()
            if cmds.objExists(d + "." + DRIVER_MUTE)
            and cmds.getAttr(d + "." + DRIVER_MUTE)]


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
    windAmplitude 는 **windEnvelope 를 곱한 실효 진폭**으로 쓴다(0 이면 값이 전부 0 =
    노드가 아무 영향도 주지 않는 상태, 0.5 면 절반).
    """
    # 실효 진폭 = windAmplitude * windEnvelope (그룹 내 모든 조인트 공용, 노드 1개).
    amp_env = cmds.createNode("multDoubleLinear", name=drv + "_ampEnvelope")
    cmds.connectAttr(drv + ".windAmplitude", amp_env + ".input1")
    cmds.connectAttr(drv + "." + DRIVER_ENVELOPE, amp_env + ".input2")

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
        cmds.connectAttr(amp_env + ".output", mul_amp + ".input2")

        _clear_attr_input(jnt, attr)
        cmds.connectAttr(mul_amp + ".output", "{0}.{1}".format(jnt, attr))
        wired += 1

    return wired


def apply_wind(joints, attr, start, end, period, amplitude, offset,
               clear_range=True, tangent="spline", skip_zero_crossings=True,
               mode=MODE_CHAIN, output=OUTPUT_CURVE, speed=1.0, node_offset=0.0,
               envelope=1.0, driver_at_root=True):
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
    envelope   : (node) 드라이버 windEnvelope 초기값 [0, 1]. 0 = 영향 없음, 0.5 = 절반,
                 1 = 완전 적용. 만든 뒤에도 드라이버에서 라이브로 조절/키잉할 수 있다.
    driver_at_root: (node) True 면 드라이버 로케이터를 그 그룹 **최상단 노드의 위치**에
                 놓는다. False 면 예전처럼 원점에 만든다.

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
                            speed, mode, node_offset, envelope, driver_at_root)
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
                 node_offset=0.0, envelope=1.0, driver_at_root=True):
    """node 모드: 그룹마다 드라이버 null 1개 + 싸인 노드망을 만든다.

    드라이버 순번 k 마다 windPhaseOffset = k*node_offset 로 초기화해, Root 모드에서 루트들이
    서로 다른 타이밍으로 찰랑이게 한다(이후 각 드라이버의 windPhaseOffset 을 직접 조절 가능).

    driver_at_root=True 면 드라이버 로케이터를 그 그룹 최상단 노드의 월드 위치에 놓는다.
    """
    if not groups:
        msg = "[Warning] No valid joints for node driver."
        if missing:
            msg += " Skipped: {0}".format(", ".join(missing))
        return 0, 0, msg

    drivers = []
    wired = 0
    no_follow = []
    for k, grp in enumerate(groups):
        root_jnt = grp[0][0]
        place_at = (cmds.xform(root_jnt, query=True, worldSpace=True,
                               translation=True) if driver_at_root else None)
        drv = _make_driver(_leaf(root_jnt) + "_windDriver#",
                           period, amplitude, offset, speed,
                           phase_offset=k * node_offset, envelope=envelope,
                           place_at=place_at)
        template = _sine_lut(drv + "_sineTemplate")
        wired += _wire_group(drv, grp, attr, template)
        cmds.delete(template)   # 조인트마다 복제본을 썼으므로 템플릿은 버린다.

        # 놓기만 하는 게 아니라 **따라다니게** 한다 - 루트가 움직이면 드라이버도 같이 간다.
        if driver_at_root:
            _made, why = follow_root_position(drv, root_jnt)
            if why:
                no_follow.append("{0} ({1})".format(_leaf(root_jnt), why))

        drivers.append(drv)

    # ---- 위상 시계 배선 (V03). 위 '위상 시계(windPhaseTime) 엔진' 주석 참고.
    wire_phase(drivers)

    mode_label = "root" if mode == MODE_ROOT else "chain"
    head = "Wind node ({0} mode): {1} driver(s) on {2} joint(s)".format(
        mode_label, len(drivers), wired)
    msg = "{0} [{1}] period={2} amp={3} offset={4} speed={5} node_offset={6} " \
          "envelope={7}. Driver(s) placed at {8}. " \
          "Edit windPeriod/Amplitude/Offset/Speed live; " \
          "windPhaseOffset sets each driver's overall timing (per-root); " \
          "windEnvelope [0-1] scales the whole effect (0 = off, 0.5 = half)." \
          .format(head, attr, period, amplitude, offset, speed, node_offset,
                  envelope,
                  "the chain root (and follows it)" if driver_at_root
                  else "the origin")
    if no_follow:
        msg += " Root-follow skipped (would cycle): {0}.".format(
            ", ".join(no_follow[:5]))
    if missing:
        msg += " Skipped: {0}".format(", ".join(missing))
    return len(drivers), wired, msg
