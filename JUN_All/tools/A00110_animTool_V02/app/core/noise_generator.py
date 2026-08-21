# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00110_animTool_V02 - Create > Noise : 결정론적 · 심리스 1D 노이즈 생성기 (DCC 비의존)
#
# 이 파일은 maya.cmds 를 import 하지 않는다. 순수 파이썬이라 마야 없이 단위 테스트가 된다.
# 마야 쪽(노드/커브)은 noise_node_manager.py 가 맡는다.
#
# 설계 요약 (계획서: docs/plans/A00110_animTool_V02_noise_tab_plan.md)
#
#   1) 옥타브 뱅크
#      옥타브 o 는 루프 안에 정확히 2^(o+1) 개의 셀을 갖는다. 셀 수가 정수라 **어느 옥타브든
#      루프 경계에서 저절로 이어진다** — 경계만 크로스페이드하는 흔한 편법이 필요 없다.
#      이게 seamless 의 첫 번째 겹이다(두 번째 겹은 커브의 cycle infinity, node manager 쪽).
#      최저음이 1셀이 아니라 **2셀**인 게 중요하다 — 1셀은 보간해도 양 끝이 같은 점이라
#      **상수**가 되고, Smoothness 를 크게 올리면 노이즈가 통째로 사라져 평평한 선만 남는다.
#
#   2) Smoothness = 스펙트럼 지수 β
#      최종값 = Σ w(o)·basis[o] / Σ w(o),  w(o) = (2^o)^(-β)
#      β>0 이면 저주파가 이겨 부드럽고, β<0 이면 고주파가 이겨 거칠다.
#      노이즈의 '색'(white β=0 / pink β=1 / brown β=2 / blue β=-1)과 같은 정의다.
#      **기저(노이즈 종류)와 스펙트럼(Smoothness)이 직교**해서, 종류를 추가할 때
#      Smoothness 코드를 건드릴 필요가 없다.
#
#   3) 결정론
#      random 모듈을 쓰지 않는다. 파이썬 구현에 따라 결과가 달라질 여지가 있기 때문이다.
#      대신 32bit 정수 해시(xorshift/mix)를 직접 돌린다. 같은 (종류, 시드, 길이) 는
#      어느 PC / 어느 파이썬에서도 **같은 파형**이다.
#
#   4) LUT 파일을 쓰지 않는 이유
#      옥타브 뱅크 생성이 5ms 짜리 1회성 작업이라, 디스크에서 86KB 를 읽어 파싱하는 것보다
#      빠르거나 비슷하다. 파일을 두면 배포·경로·버전 관리 부담만 생긴다.
#      대신 **세션 메모리에 (종류, 시드, 길이) 로 캐시**한다. 슬라이더를 흔드는 동안
#      바뀌는 건 β 가중치뿐이라 뱅크는 재생성되지 않는다.

import math


# ------------------------------------------------------------------ 노이즈 종류

VALUE = "Value (fBm)"
PERLIN = "Perlin"
SIMPLEX = "Simplex"
WORLEY = "Worley (Cellular)"
RIDGED = "Ridged"

# UI 콤보 순서 = 노드의 enum 순서. **순서를 바꾸면 기존 씬의 noiseType 값이 밀린다.**
# 새 종류는 반드시 **뒤에** 붙인다.
NOISE_TYPES = (VALUE, PERLIN, SIMPLEX, WORLEY, RIDGED)

# 노드 enum 에 쓸 짧은 이름. 마야 enum 이름에는 공백/괄호를 넣지 않는 게 안전하다.
# NOISE_TYPES 와 **같은 순서**여야 한다(인덱스로 서로 변환한다).
NOISE_TYPE_TOKENS = ("Value", "Perlin", "Simplex", "Worley", "Ridged")


def type_index(kind):
    """노이즈 종류 이름 -> enum 인덱스. 모르는 이름은 0(Value)."""
    try:
        return NOISE_TYPES.index(kind)
    except ValueError:
        return 0


def type_from_index(index):
    """enum 인덱스 -> 노이즈 종류 이름. 범위 밖이면 Value."""
    try:
        return NOISE_TYPES[int(index)]
    except (IndexError, ValueError, TypeError):
        return VALUE

# 루프 길이 선택지(프레임). 30fps 기준 6.7s / 16.7s / 33.3s / 66.7s.
LOOP_LENGTHS = (200, 500, 1000, 2000)

DEFAULT_LOOP_LENGTH = 1000
DEFAULT_SMOOTHNESS = 1.0
DEFAULT_MIN = -1.0
DEFAULT_MAX = 1.0


# ------------------------------------------------------------------ 결정론적 난수

_MASK = 0xFFFFFFFF


def hash32(x, seed):
    """32bit 정수 해시. 같은 (x, seed) 는 언제나 같은 정수.

    random 모듈 대신 이걸 쓰는 이유는 §결정론 참고 — 파이썬 버전이나 구현이 바뀌어도
    결과가 흔들리지 않아야 한다.
    """
    x = (int(x) * 0x9E3779B1 + int(seed) * 0x85EBCA6B) & _MASK
    x ^= (x >> 15)
    x = (x * 0x2545F491) & _MASK
    x ^= (x >> 13)
    x = (x * 0x27220A95) & _MASK
    x ^= (x >> 16)
    return x


def rand_unit(x, seed):
    """해시를 [-1, 1] 실수로."""
    return hash32(x, seed) / float(_MASK) * 2.0 - 1.0


def rand01(x, seed):
    """해시를 [0, 1) 실수로."""
    return hash32(x, seed) / float(_MASK + 1)


# ------------------------------------------------------------------ 옥타브 수

def cells_for_octave(octave):
    """옥타브 o 의 셀 수. o=0 이 **2셀**이다(1셀은 상수라 쓸모가 없다)."""
    return 2 ** (int(octave) + 1)


def octave_count(length):
    """루프 길이에 맞는 옥타브 수. 최고음 셀 수(2^n)가 length 에 가장 가깝게 잡힌다.

    프레임당 키 하나로 표현할 수 있는 한계(나이퀴스트)가 '셀 하나당 1프레임' 이다.
    그보다 잘게 쪼개면 **프레임 사이에 숨는 성분**만 만들어 에일리어싱이 된다.
    length=1000 -> 10 옥타브(셀 2 ~ 1024, 최고음 0.98 frame/cell).
    """
    length = max(2, int(length))
    return max(1, int(round(math.log(length, 2))))


# ------------------------------------------------------------------ 기저 파형 (옥타브 1개)
#
# 모든 기저는 길이 length 의 리스트를 돌려주고, 값은 대략 [-1, 1] 범위다.
# cells 는 2의 거듭제곱이라 인덱스를 cells 로 wrap 하는 것만으로 주기성이 보장된다.

def _quintic(f):
    """Perlin 의 quintic ease. 양 끝에서 1·2차 도함수가 0이라 셀 경계가 안 보인다."""
    return f * f * f * (f * (f * 6.0 - 15.0) + 10.0)


def _cell_pos(i, cells, length):
    """프레임 i 가 놓인 셀 좌표(실수). 정수부 = 셀 인덱스, 소수부 = 셀 안 위치."""
    return i * cells / float(length)


def _basis_value(cells, length, seed, octave):
    """Value noise — 셀마다 난수 '값' 을 두고 quintic 보간."""
    salt = octave * 7919
    g = [rand_unit(salt + i, seed) for i in range(cells)]

    out = []
    for i in range(length):
        x = _cell_pos(i, cells, length)
        i0 = int(math.floor(x))
        f = x - i0
        a = g[i0 % cells]
        b = g[(i0 + 1) % cells]
        s = _quintic(f)
        out.append(a * (1.0 - s) + b * s)
    return out


def _basis_perlin(cells, length, seed, octave):
    """Perlin(gradient) noise — 셀마다 '기울기' 를 두고 보간. 셀 경계에서 값이 0이라
    Value 보다 출렁임이 고르다."""
    salt = octave * 7919 + 104729
    g = [rand_unit(salt + i, seed) for i in range(cells)]

    out = []
    for i in range(length):
        x = _cell_pos(i, cells, length)
        i0 = int(math.floor(x))
        f = x - i0
        n0 = g[i0 % cells] * f
        n1 = g[(i0 + 1) % cells] * (f - 1.0)
        s = _quintic(f)
        # 1D gradient noise 는 최대 진폭이 대략 0.5 라 2배 해서 [-1,1] 로 맞춘다.
        out.append(2.0 * (n0 * (1.0 - s) + n1 * s))
    return out


def _basis_simplex(cells, length, seed, octave):
    """1D Simplex — Perlin 과 같은 기울기 기저에 **커널(radial falloff)** 로 합성한다.
    보간이 아니라 감쇠 합이라 격자 아티팩트가 덜하다. 0.395 는 Gustavson 의 1D 정규화 상수."""
    salt = octave * 7919 + 15485863
    g = [rand_unit(salt + i, seed) for i in range(cells)]

    out = []
    for i in range(length):
        x = _cell_pos(i, cells, length)
        i0 = int(math.floor(x))
        f = x - i0

        t0 = 1.0 - f * f
        n0 = (t0 ** 4) * g[i0 % cells] * f if t0 > 0.0 else 0.0

        f1 = f - 1.0
        t1 = 1.0 - f1 * f1
        n1 = (t1 ** 4) * g[(i0 + 1) % cells] * f1 if t1 > 0.0 else 0.0

        out.append(0.395 * (n0 + n1) * 2.0)
    return out


def _basis_worley(cells, length, seed, octave):
    """Worley(cellular) — 셀마다 특징점 하나를 두고 **가장 가까운 점까지의 거리**를 쓴다.
    1D 에서는 톱니/계곡 모양이라 툭툭 끊기는 맥동에 어울린다.

    특징점에 가까울수록 +1, 멀수록 -1 이 되도록 뒤집어 둔다(봉우리가 보이는 쪽이 직관적).
    """
    salt = octave * 7919 + 32452843
    # 셀 안에서의 지터. 0.5 를 중심으로 ±0.4 만 흔들어 인접 셀과 너무 붙지 않게 한다.
    fp = [c + 0.5 + 0.4 * rand_unit(salt + c, seed) for c in range(cells)]

    out = []
    for i in range(length):
        x = _cell_pos(i, cells, length)
        c = int(math.floor(x))

        best = None
        # 이웃 3셀만 보면 최근접점이 반드시 그 안에 있다(셀당 점 1개 + 지터 ±0.4).
        for k in (c - 1, c, c + 1):
            kk = k % cells
            # fp[kk] 는 [kk, kk+1) 구간의 좌표다. k 쪽 주기로 옮겨서 거리를 잰다.
            p = fp[kk] + (k - kk)
            d = abs(x - p)
            if best is None or d < best:
                best = d

        # 거리는 셀 단위로 대략 [0, 1]. 1 - 2d 로 [-1, 1] 에 태운다.
        v = 1.0 - 2.0 * best
        out.append(max(-1.0, min(1.0, v)))
    return out


def _basis_ridged(cells, length, seed, octave):
    """Ridged — Value 기저를 접어(|v|) 뾰족한 봉우리를 만든다.

    옥타브마다 접어야 ridged 특유의 능선이 나온다(최종 합에 한 번 접으면 그냥 절댓값이다).
    """
    base = _basis_value(cells, length, seed, octave)
    return [1.0 - 2.0 * abs(v) for v in base]


_BASIS = {
    VALUE: _basis_value,
    PERLIN: _basis_perlin,
    SIMPLEX: _basis_simplex,
    WORLEY: _basis_worley,
    RIDGED: _basis_ridged,
}


# ------------------------------------------------------------------ 옥타브 뱅크 + 캐시

# (종류, 시드, 길이) -> 옥타브 리스트. 슬라이더로 β 만 흔들 때 재생성을 막는다.
_BANK_CACHE = {}

# 캐시 상한. 노드마다 뱅크 하나(1000프레임 기준 약 86KB)라 넉넉히 잡아도 가볍다.
_BANK_CACHE_LIMIT = 32


def build_bank(kind, seed, length):
    """옥타브 기저파형들을 만든다. 반환: [[float] * length] * octave_count(length)"""
    fn = _BASIS.get(kind, _basis_value)
    length = max(2, int(length))
    n = octave_count(length)
    return [fn(cells_for_octave(o), length, int(seed), o) for o in range(n)]


def get_bank(kind, seed, length):
    """캐시된 옥타브 뱅크. 없으면 만들어 넣는다."""
    key = (kind, int(seed), int(length))
    bank = _BANK_CACHE.get(key)
    if bank is None:
        if len(_BANK_CACHE) >= _BANK_CACHE_LIMIT:
            _BANK_CACHE.clear()
        bank = build_bank(kind, seed, length)
        _BANK_CACHE[key] = bank
    return bank


def clear_cache():
    """뱅크 캐시를 비운다(테스트/리로드용)."""
    _BANK_CACHE.clear()


# ------------------------------------------------------------------ 합성

def mix_octaves(bank, smoothness):
    """옥타브들을 β 가중합한다. β = smoothness.

    가중치는 (2^o)^(-β) 인데, β 가 크면 곧장 overflow 로 inf 가 된다(요청상 β 에는
    최소/최대가 없다). 그래서 **로그 공간에서 최댓값을 빼고** exp 를 취한다 —
    수학적으로 같은 비율이면서 어떤 β 를 넣어도 inf/nan 이 나오지 않는다.
    """
    n = len(bank)
    if n == 0:
        return []

    ln2 = math.log(2.0)
    exps = [-float(smoothness) * o * ln2 for o in range(n)]
    top = max(exps)
    weights = [math.exp(e - top) for e in exps]

    total = sum(weights)
    if total <= 0.0:
        return list(bank[0])

    length = len(bank[0])
    out = []
    for i in range(length):
        s = 0.0
        for o in range(n):
            w = weights[o]
            if w:
                s += w * bank[o][i]
        out.append(s / total)
    return out


def apply_offset(values, offset):
    """노이즈 시작 위치를 offset 프레임만큼 민다. 값이 주기적이라 회전만으로 정확하다.

    양수 offset = 노이즈가 **앞당겨진다**(프레임 0에서 원래 offset 프레임의 값이 나온다).
    소수 offset 은 이웃 두 값의 선형 보간이다.
    """
    length = len(values)
    if not length:
        return []

    o = float(offset) % length          # 파이썬 % 는 음수 offset 도 [0, length) 로 접는다
    i0 = int(math.floor(o))
    frac = o - i0

    if frac <= 1e-12:
        return values[i0:] + values[:i0]

    out = []
    for i in range(length):
        a = values[(i + i0) % length]
        b = values[(i + i0 + 1) % length]
        out.append(a + (b - a) * frac)
    return out


def remap(values, out_min, out_max):
    """관측된 최소/최대 기준으로 정규화한 뒤 [out_min, out_max] 로 편다.

    이론상의 [-1,1] 이 아니라 **실제 값의 최소·최대**를 쓴다. 그래야 사용자가 지정한
    범위를 정확히 꽉 채운다(Max=5 라고 하면 어딘가에서 정확히 5를 찍는다).

    out_min > out_max 는 에러가 아니라 **뒤집힌 노이즈**로 해석한다.
    out_min == out_max 면 상수가 된다.
    """
    if not values:
        return []

    lo = min(values)
    hi = max(values)
    span = hi - lo

    if span <= 1e-12:
        mid = (float(out_min) + float(out_max)) * 0.5
        return [mid] * len(values)

    scale = (float(out_max) - float(out_min)) / span
    return [float(out_min) + (v - lo) * scale for v in values]


def generate(kind=VALUE, seed=0, length=DEFAULT_LOOP_LENGTH,
             smoothness=DEFAULT_SMOOTHNESS, offset=0.0,
             out_min=DEFAULT_MIN, out_max=DEFAULT_MAX):
    """설정 하나로부터 **커브에 그대로 꽂을 값 배열**을 만든다.

    반환 길이는 `length + 1` 이고 **마지막 값 == 첫 값**이다.
    이게 seamless 의 두 번째 겹이다 — 마야의 cycle 주기는 `마지막 키 − 첫 키` 라서,
    키를 length 개만 깔면 주기가 length-1 이 되어 **한 바퀴마다 1프레임씩 밀린다**.
    (계획서 §7-1 / T2. 눈에 잘 안 띄어서 더 나쁜 종류의 버그다.)
    """
    length = max(2, int(length))
    if kind not in _BASIS:
        kind = VALUE

    bank = get_bank(kind, seed, length)
    values = mix_octaves(bank, smoothness)
    values = apply_offset(values, offset)
    values = remap(values, out_min, out_max)

    # 루프를 닫는 여분 키 하나. 값은 첫 값과 **정확히 같아야** 한다.
    values.append(values[0])
    return values
