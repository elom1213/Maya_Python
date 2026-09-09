# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-09
# Framework.core.falloff_curve - falloff 커브 모델 (**Maya / Qt 비의존 순수 파이썬**)
#
# 마야의 Soft Select / Paint 툴에 있는 "Falloff curve" 를 흉내낸다. 커브는
# **정규화 좌표**의 컨트롤 포인트 목록이다.
#
#   x = 0~1 로 정규화된 축 (툴마다 뜻이 다르다)
#   y = 그 자리에서의 값 (0~1)
#
#   A00275_skinTool  Expand Bind : x = 거리 / 반경,      y = 웨이트 비중
#   A00410_SecondaryMotion       : x = 체인 루트 -> 팁,  y = 파라미터 배수
#
# 커브 자체는 Qt 도, maya 도 모른다 — 위젯(Framework/qt/MOD_falloffCurve_qt_v01.py)이
# 그리기용으로, 툴의 계산 로직이 계산용으로 **같은 함수**를 쓴다. 그래야 화면에 보이는
# 모양과 실제 결과가 어긋나지 않는다.
#
# 2026-09-09 에 `A00275_skinTool_V01/app/core/falloff.py` 에서 승격했다.

# 보간 방식. 마야 gradient control 의 None / Linear / Smooth / Spline 과 같은 의미.
INTERP_NONE = "none"
INTERP_LINEAR = "linear"
INTERP_SMOOTH = "smooth"
INTERP_SPLINE = "spline"

INTERPOLATIONS = (INTERP_NONE, INTERP_LINEAR, INTERP_SMOOTH, INTERP_SPLINE)

# (이름, 포인트, 보간) — UI 의 프리셋 버튼 행이 이 목록을 그대로 쓴다.
PRESETS = (
    ("Linear", [(0.0, 1.0), (1.0, 0.0)], INTERP_LINEAR),
    ("Smooth", [(0.0, 1.0), (1.0, 0.0)], INTERP_SMOOTH),
    ("Ease In", [(0.0, 1.0), (0.5, 0.85), (1.0, 0.0)], INTERP_SPLINE),
    ("Ease Out", [(0.0, 1.0), (0.5, 0.15), (1.0, 0.0)], INTERP_SPLINE),
    ("Spike", [(0.0, 1.0), (0.25, 0.2), (1.0, 0.0)], INTERP_SPLINE),
    ("Solid", [(0.0, 1.0), (1.0, 1.0)], INTERP_LINEAR),
)

DEFAULT_POINTS = [(0.0, 1.0), (1.0, 0.0)]
DEFAULT_INTERP = INTERP_LINEAR

# 처음부터 끝까지 값이 1 인 커브. "커브를 쓰지 않는 상태" 를 표현할 때 쓴다
# (A00410 처럼 커브가 **배수**인 툴의 기본값 — 곱해도 아무것도 바뀌지 않는다).
FLAT_POINTS = [(0.0, 1.0), (1.0, 1.0)]
FLAT_INTERP = INTERP_LINEAR


def clamp01(value):
    return 0.0 if value < 0.0 else (1.0 if value > 1.0 else value)


def normalize_points(points):
    """포인트 목록을 x 오름차순 + 0~1 범위로 정리한다(빈 목록이면 기본값)."""
    cleaned = [(clamp01(float(x)), clamp01(float(y))) for x, y in (points or [])]
    if not cleaned:
        return list(DEFAULT_POINTS)
    return sorted(cleaned, key=lambda p: p[0])


def _smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def _catmull_rom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * ((2.0 * p1) +
                  (-p0 + p2) * t +
                  (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
                  (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3)


def evaluate(points, interp, t):
    """정규화 거리 t(0~1) 에서의 커브 값(0~1).

    포인트 사이에서만 보간하고, 양 끝 바깥은 끝 포인트 값으로 고정한다(마야와 같다).
    """
    pts = normalize_points(points)
    t = clamp01(float(t))

    if len(pts) == 1:
        return clamp01(pts[0][1])
    if t <= pts[0][0]:
        return clamp01(pts[0][1])
    if t >= pts[-1][0]:
        return clamp01(pts[-1][1])

    # t 를 감싸는 구간 찾기.
    i = 0
    for k in range(len(pts) - 1):
        if pts[k][0] <= t <= pts[k + 1][0]:
            i = k
            break

    x0, y0 = pts[i]
    x1, y1 = pts[i + 1]
    span = x1 - x0
    # 같은 x 에 포인트가 겹치면 나눗셈이 터진다 — 왼쪽 값을 쓴다.
    if span <= 1e-9:
        return clamp01(y0)
    local = (t - x0) / span

    if interp == INTERP_NONE:
        return clamp01(y0)
    if interp == INTERP_SMOOTH:
        return clamp01(y0 + (y1 - y0) * _smoothstep(local))
    if interp == INTERP_SPLINE:
        y_prev = pts[i - 1][1] if i > 0 else y0
        y_next = pts[i + 2][1] if i + 2 < len(pts) else y1
        return clamp01(_catmull_rom(y_prev, y0, y1, y_next, local))
    return clamp01(y0 + (y1 - y0) * local)


def sample(points, interp, count=64):
    """커브를 count 개로 균등 샘플링한 [(t, value), ...] (위젯 그리기용)."""
    count = max(2, int(count))
    step = 1.0 / (count - 1)
    return [(k * step, evaluate(points, interp, k * step)) for k in range(count)]


def is_flat(points, interp=None, value=1.0, tolerance=1e-6):
    """커브가 처음부터 끝까지 `value` 로 평평한가.

    커브가 배수인 툴에서 **지금 이 커브가 결과를 바꾸고 있는지**를 UI 가 표시하는 데 쓴다
    (예: 버튼에 표식 붙이기). 포인트 y 만 보면 되므로 보간 방식과 무관하다 —
    모든 포인트가 같은 값이면 어떤 보간이든 그 값으로 평평하다.
    """
    for _x, y in normalize_points(points):
        if abs(y - value) > tolerance:
            return False
    return True


def preset_points(name):
    """프리셋 이름 -> (포인트 사본, 보간). 없으면 기본값."""
    for label, points, interp in PRESETS:
        if label == name:
            return [tuple(p) for p in points], interp
    return list(DEFAULT_POINTS), DEFAULT_INTERP
