# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00640_AttrSlider core - 슬라이더 끝(범위)을 정하는 규칙 + 사용자 범위 저장소
#
# **마야 비의존** 계산(resolve_range) 과, 저장소(UserRanges - 읽기/쓰기 함수를 주입받는다)로 나눴다.
# 계획서 docs/plans/A00640_AttrSlider_plan.md §2.
#
# 우선순위
#   1. 사용자 범위(어트리뷰트 이름 기준 - 노드가 달라도 같은 범위)
#   2. 양쪽 소프트 범위          (blendShape weight 0~1 - 하드 -10~10 도 있지만 소프트가 '슬라이더 범위' 라는 뜻이다)
#   3. 양쪽 하드 범위            (liteDriver windEnvelope 0~1)
#   4. 하드 최소만               [min, max(min + 기본폭, 값 * 2)]
#   5. 하드 최대만               [min(max - 기본폭, ...), max]
#   6. 없음                     각도 = -180~180, 그 밖 = 값 ± max(기본폭, |값|)

import json

DEFAULT_SPAN = 10.0
ANGLE_RANGE = (-180.0, 180.0)

SRC_USER = "user"
SRC_HARD = "hard"
SRC_SOFT = "soft"
SRC_AUTO = "auto"


def _num(v):
    return None if v is None else float(v)


def resolve_range(value, hard_min=None, hard_max=None, soft_min=None, soft_max=None,
                  is_angle=False, is_int=False, user=None):
    """슬라이더 범위 (lo, hi, source).

    value     : 지금 값(자동 범위의 기준)
    user      : (lo, hi) 사용자 범위 또는 None
    반환 범위는 항상 lo < hi 이고, 하드 범위 안으로 잘린다(하드 범위 밖은 setAttr 가 거부한다).
    """
    value = float(value or 0.0)
    hard_min, hard_max = _num(hard_min), _num(hard_max)
    soft_min, soft_max = _num(soft_min), _num(soft_max)

    if user is not None:
        lo, hi, src = float(user[0]), float(user[1]), SRC_USER
    elif soft_min is not None and soft_max is not None:
        lo, hi, src = soft_min, soft_max, SRC_SOFT
    elif hard_min is not None and hard_max is not None:
        lo, hi, src = hard_min, hard_max, SRC_HARD
    elif hard_min is not None:
        lo = hard_min
        hi = max(hard_min + DEFAULT_SPAN, value * 2.0, value + DEFAULT_SPAN * 0.5)
        src = SRC_AUTO
    elif hard_max is not None:
        hi = hard_max
        lo = min(hard_max - DEFAULT_SPAN, value * 2.0 if value < 0 else value - DEFAULT_SPAN)
        src = SRC_AUTO
    elif is_angle:
        lo, hi, src = ANGLE_RANGE[0], ANGLE_RANGE[1], SRC_AUTO
        if not lo <= value <= hi:
            span = abs(value) * 1.5
            lo, hi = -span, span
    else:
        span = max(DEFAULT_SPAN, abs(value))
        lo, hi, src = value - span, value + span, SRC_AUTO
        # 0 근처 값은 0~ 대칭이 읽기 쉽다
        if abs(value) < 1e-9:
            lo, hi = -DEFAULT_SPAN, DEFAULT_SPAN

    # 하드 범위 밖으로는 못 넣는다 - 사용자 · 소프트 범위도 그 안으로
    if hard_min is not None:
        lo = max(lo, hard_min)
    if hard_max is not None:
        hi = min(hi, hard_max)

    if is_int:
        lo, hi = float(int(round(lo))), float(int(round(hi)))
    if hi <= lo:
        hi = lo + (1.0 if is_int else 1e-3)
    return lo, hi, src


def widen(lo, hi, value, hard_min=None, hard_max=None):
    """값이 범위 밖이면 그 값을 담도록 넓힌 (lo, hi). 넓힐 때 10% 여유를 둔다(끝에 붙지 않게)."""
    value = float(value)
    if lo <= value <= hi:
        return lo, hi
    pad = (hi - lo) * 0.1
    if value < lo:
        lo = value - pad
    else:
        hi = value + pad
    if hard_min is not None:
        lo = max(lo, float(hard_min))
    if hard_max is not None:
        hi = min(hi, float(hard_max))
    return lo, hi


class UserRanges(object):
    """어트리뷰트 이름 -> (lo, hi). 저장은 문자열 하나(json) - 읽기/쓰기 함수를 주입받는다.

    마야에서는 optionVar 를 쓴다(launch 가 주입). 시험은 dict 를 넘긴다.
    """

    def __init__(self, load=None, save=None):
        self._load = load
        self._save = save
        self.data = {}
        self.reload()

    def reload(self):
        self.data = {}
        if not self._load:
            return
        try:
            raw = self._load()
            loaded = json.loads(raw) if raw else {}
        except (ValueError, TypeError):
            loaded = {}
        for key, pair in loaded.items():
            try:
                lo, hi = float(pair[0]), float(pair[1])
            except (TypeError, ValueError, IndexError):
                continue
            if hi > lo:
                self.data[key] = (lo, hi)

    def get(self, attr):
        return self.data.get(attr)

    def set(self, attr, lo, hi):
        lo, hi = float(lo), float(hi)
        if hi <= lo:
            raise ValueError("Max must be greater than Min.")
        self.data[attr] = (lo, hi)
        self._write()

    def remove(self, attr):
        if self.data.pop(attr, None) is not None:
            self._write()
            return True
        return False

    def _write(self):
        if self._save:
            self._save(json.dumps(self.data, sort_keys=True))
