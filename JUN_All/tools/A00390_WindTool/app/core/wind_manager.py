# -*- coding: utf-8 -*-
# A00390_WindTool core - 본 체인에 싸인 주기함수 키프레임을 찍어 '바람에 일렁이는'
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

# 키 시간의 부동소수 잡음을 없애기 위한 반올림 자리.
_TIME_ROUND = 5


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


def _resolve_targets(joints, mode):
    """(joint, offset_index) 쌍 목록과 missing(없는 노드) 목록을 만든다.

    chain: 리스트 순서가 offset 순번(index = 리스트 위치).
    root : 각 리스트 항목을 체인 루트로 보고 그 아래 모든 조인트를 depth 를 index 로.
           같은 조인트가 여러 루트에서 겹쳐 잡히면 처음 것만 쓴다(중복 키 방지).
    """
    missing = []

    if mode == MODE_ROOT:
        pairs = []
        seen = set()
        for root in joints:
            if not cmds.objExists(root):
                missing.append(root)
                continue
            for jnt, depth in _chain_from_root(root):
                if jnt in seen:
                    continue
                seen.add(jnt)
                pairs.append((jnt, depth))
        return pairs, missing

    # chain
    pairs = []
    for i, jnt in enumerate(joints):
        if not cmds.objExists(jnt):
            missing.append(jnt)
            continue
        pairs.append((jnt, i))
    return pairs, missing


def apply_wind(joints, attr, start, end, period, amplitude, offset,
               clear_range=True, tangent="spline", skip_zero_crossings=True,
               mode=MODE_CHAIN):
    """본 체인에 싸인 파형 키를 찍는다.

    joints     : 조인트 이름 목록.
    attr       : 키를 찍을 어트리뷰트('rotateX' 등, AXES 참고).
    start, end : 키를 만들 프레임 구간(실수 허용).
    period     : 한 주기의 프레임 수(실수 허용, > 0).
    amplitude  : 진폭(피크 값).
    offset     : 순번마다 더해지는 위상 지연(프레임, 실수 허용). 순번 i -> i*offset.
    clear_range: True 면 각 조인트의 attr 키를 [start, end] 에서 먼저 지운다(재적용 깔끔).
    tangent    : 키 탄젠트 타입(기본 'spline' -> 싸인 유사 보간).
    skip_zero_crossings: True(기본)면 구간 내부의 0 교차 키를 빼고 극값(±진폭)만 남긴다
                 (양끝은 앵커로 유지) -> 커브가 더 부드럽다.
    mode       : MODE_CHAIN(리스트 = 한 체인, 순번=리스트 순서) 또는
                 MODE_ROOT(리스트 각 항목 = 체인 루트, 순번=root 로부터의 depth).

    반환: (key_count, joint_count, message)
    """
    if not joints:
        return 0, 0, "[Warning] Joint list is empty. Add joints first."
    if attr not in AXES:
        return 0, 0, "[Warning] Unsupported axis: {0}".format(attr)
    if period <= 0:
        return 0, 0, "[Warning] Period must be greater than 0."
    if start > end:
        start, end = end, start

    pairs, missing = _resolve_targets(joints, mode)

    total_keys = 0
    keyed = set()

    for jnt, index in pairs:
        # 어트리뷰트가 존재하고 세팅 가능한지 확인.
        if not cmds.attributeQuery(attr, node=jnt, exists=True):
            missing.append("{0}.{1}".format(jnt, attr))
            continue

        if clear_range:
            # 기존 키를 구간에서 제거(없으면 조용히 넘어간다).
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
            total_keys, len(keyed), len(joints))
    else:
        head = "Wind keys (chain mode): {0} key(s) on {1} joint(s)".format(
            total_keys, len(keyed))
    msg = "{0} [{1}] {2}~{3} period={4} amp={5} offset={6}.".format(
        head, attr, start, end, period, amplitude, offset)
    if missing:
        msg += " Skipped: {0}".format(", ".join(missing))
    return total_keys, len(keyed), msg
