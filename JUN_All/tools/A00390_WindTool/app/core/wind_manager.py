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


def apply_wind(joints, attr, start, end, period, amplitude, offset,
               clear_range=True, tangent="spline", skip_zero_crossings=True):
    """본 체인에 싸인 파형 키를 찍는다.

    joints     : 조인트 이름 목록(순서가 offset 의 순번을 정한다).
    attr       : 키를 찍을 어트리뷰트('rotateX' 등, AXES 참고).
    start, end : 키를 만들 프레임 구간(실수 허용).
    period     : 한 주기의 프레임 수(실수 허용, > 0).
    amplitude  : 진폭(피크 값).
    offset     : 조인트마다 더해지는 위상 지연(프레임, 실수 허용). 순번 i -> i*offset.
    clear_range: True 면 각 조인트의 attr 키를 [start, end] 에서 먼저 지운다(재적용 깔끔).
    tangent    : 키 탄젠트 타입(기본 'spline' -> 싸인 유사 보간).
    skip_zero_crossings: True(기본)면 구간 내부의 0 교차 키를 빼고 극값(±진폭)만 남긴다
                 (양끝은 앵커로 유지) -> 커브가 더 부드럽다.

    반환: (key_count, joint_count, message)
    """
    if not joints:
        return 0, 0, "[Warning] Joint list is empty. Add a bone chain first."
    if attr not in AXES:
        return 0, 0, "[Warning] Unsupported axis: {0}".format(attr)
    if period <= 0:
        return 0, 0, "[Warning] Period must be greater than 0."
    if start > end:
        start, end = end, start

    total_keys = 0
    done_joints = 0
    missing = []

    for index, jnt in enumerate(joints):
        if not cmds.objExists(jnt):
            missing.append(jnt)
            continue
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

        done_joints += 1

    msg = "Wind keys: {0} key(s) on {1} joint(s) [{2}] {3}~{4} " \
          "period={5} amp={6} offset={7}.".format(
              total_keys, done_joints, attr, start, end,
              period, amplitude, offset)
    if missing:
        msg += " Skipped: {0}".format(", ".join(missing))
    return total_keys, done_joints, msg
