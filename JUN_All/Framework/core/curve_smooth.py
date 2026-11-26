# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-26
# Framework.core.curve_smooth - 키 값 목록을 부드럽게 (가우시안 Smooth, 순수 계산 · 마야 무관)
#
# 2026-11-26 A00110_animTool_V02/app/core/curve_filter_manager.py 의 Curve > Filters > Smooth 수식을 공용으로 올렸다.
# A00540_JaliLipSync 가 키를 걸기 전에 같은 Smooth 를 쓴다(릴리즈본은 툴 간 import 금지, Framework 는 모든 릴리즈에 동봉).
# A00110 은 여기서 import 해 쓰므로 두 툴의 결과가 숫자까지 같다. 수식을 바꾸면 두 툴이 함께 바뀐다.
#
# A00110 Filters 탭의 Smooth 기본값 = Iterations 3 · Strength 100 % · 슬라이더(amount) 0, 원클릭 버튼 -100 / -50 / 50 / 100.

EPS = 1e-6

#: A00110 Curve > Filters > Smooth 의 기본 세팅 (원클릭 "50" 버튼과 같다)
DEFAULT_AMOUNT = 50.0
DEFAULT_ITERATIONS = 3
DEFAULT_STRENGTH = 100.0


def gaussian_smooth(values, iterations=1):
    """[1 2 1]/4 커널을 `iterations` 번 돌린 값 목록. 양 끝 값은 고정한다.

    양 끝을 고정하는 이유: 구간 밖 애니메이션과 이어지는 지점이라 값이 움직이면
    경계에 이음매가 생긴다.
    """
    out = list(values)
    if len(out) < 3:
        return out
    for _ in range(max(0, int(iterations))):
        prev = list(out)
        for i in range(1, len(prev) - 1):
            out[i] = (prev[i - 1] + 2.0 * prev[i] + prev[i + 1]) * 0.25
    return out


def mix(original, target, t):
    """original 에서 target 쪽으로 t 만큼. t<0 이면 **반대로** 밀어낸다(요철 강조)."""
    return [o + (g - o) * t for o, g in zip(original, target)]


def smooth_values(values, amount, iterations=3, strength=100.0):
    """Smooth 결과.

    amount    : -100(Rough) ~ +100(Smooth). 0 이면 원본 그대로.
    iterations: 가우시안 패스 수(클수록 넓게 뭉갠다).
    strength  : 0~100. amount 에 곱해지는 전체 세기.
    """
    t = (amount / 100.0) * (strength / 100.0)
    if abs(t) < EPS or len(values) < 3:
        return list(values)
    return mix(values, gaussian_smooth(values, iterations), t)
