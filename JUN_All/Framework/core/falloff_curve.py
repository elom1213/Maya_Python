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
#
# 탄젠트(베지어)
# -------------
# `INTERP_BEZIER` 에서는 포인트마다 **탄젠트 핸들**(in / out)이 붙어 구간이 3차 베지어로
# 그려진다. 나머지 보간(none/linear/smooth/spline)은 탄젠트를 보지 않으므로 **예전 커브는
# 그대로**다. 탄젠트 목록은 포인트 목록과 나란한 별도 인자라, 탄젠트를 모르는 옛 호출부
# (`evaluate(points, interp, t)`)도 그대로 동작한다.
#
#   tangents[i] = None                                   # 자동(이웃을 보고 매끄럽게)
#              또는 {"broken": bool,
#                    "in":  (dx, dy),                    # 왼쪽(들어오는) 핸들 벡터
#                    "out": (dx, dy)}                    # 오른쪽(나가는) 핸들 벡터
#
# 각도는 **양쪽 다 자기 핸들이 뻗는 방향**으로 잰다(in 은 -x 쪽). 그래서 **끊지 않은
# 탄젠트는 in 각도 == out 각도** 이고, 길이는 따로 논다(마야의 weighted tangent 와 같은 감각).
# `broken=True` 면 두 각도가 완전히 따로 논다.
#
# 커브가 **함수**로 남으려면 x 가 되돌아가면 안 된다 — 그래서 평가할 때 제어점 x 를
# `x0 <= cx0 <= cx1 <= x1` 로 가둔다(핸들을 아무리 길게 빼도 커브가 뒤로 접히지 않는다).

import math


# 보간 방식. 마야 gradient control 의 None / Linear / Smooth / Spline 과 같은 의미.
INTERP_NONE = "none"
INTERP_LINEAR = "linear"
INTERP_SMOOTH = "smooth"
INTERP_SPLINE = "spline"
# 포인트마다 탄젠트 핸들이 붙는 3차 베지어. 이 모드에서만 `tangents` 가 쓰인다.
INTERP_BEZIER = "bezier"

INTERPOLATIONS = (INTERP_NONE, INTERP_LINEAR, INTERP_SMOOTH, INTERP_SPLINE,
                  INTERP_BEZIER)

# 탄젠트 핸들의 방향(각도를 재는 기준이 다르다).
SIDE_IN = "in"
SIDE_OUT = "out"

# 자동 탄젠트 핸들의 길이 = 그쪽 이웃까지 x 거리의 이 비율.
AUTO_TANGENT_RATIO = 1.0 / 3.0

# 핸들 길이 상한(정규화 좌표). 화면 밖으로 나가면 잡을 수 없다.
MAX_TANGENT_LENGTH = 2.0

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


def normalize_curve(points, tangents=None):
    """(정렬된 포인트, 그 정렬을 따라간 탄젠트) 를 돌려준다.

    `normalize_points` 는 x 로 정렬하므로 탄젠트를 따로 정렬하면 **짝이 어긋난다**.
    포인트와 탄젠트를 같이 다루는 곳은 반드시 이 함수를 쓴다.
    """
    raw = list(points or [])
    if not raw:
        return list(DEFAULT_POINTS), [None] * len(DEFAULT_POINTS)

    tans = list(tangents or [])
    tans += [None] * (len(raw) - len(tans))

    paired = [((clamp01(float(x)), clamp01(float(y))), tans[i])
              for i, (x, y) in enumerate(raw)]
    paired.sort(key=lambda item: item[0][0])
    return [p for p, _t in paired], [t for _p, t in paired]


def make_tangent(in_vec=None, out_vec=None, broken=False):
    """탄젠트 항목 하나를 만든다(값은 전부 사본)."""
    return {"broken": bool(broken),
            "in": tuple(float(v) for v in in_vec) if in_vec else None,
            "out": tuple(float(v) for v in out_vec) if out_vec else None}


def auto_tangent_vectors(pts, index):
    """이웃을 보고 매끄럽게 이어지는 기본 탄젠트 (in_vec, out_vec).

    Catmull-Rom 과 같은 발상 — 앞뒤 포인트를 잇는 방향을 그 포인트의 접선으로 본다.
    끝 포인트는 한쪽 이웃만 있으므로 그 구간 방향을 쓴다.
    """
    n = len(pts)
    if n < 2:
        return ((-0.1, 0.0), (0.1, 0.0))

    i = max(0, min(n - 1, int(index)))
    prev_pt = pts[i - 1] if i > 0 else None
    next_pt = pts[i + 1] if i < n - 1 else None

    if prev_pt is None:
        dx, dy = next_pt[0] - pts[i][0], next_pt[1] - pts[i][1]
    elif next_pt is None:
        dx, dy = pts[i][0] - prev_pt[0], pts[i][1] - prev_pt[1]
    else:
        dx, dy = next_pt[0] - prev_pt[0], next_pt[1] - prev_pt[1]

    if abs(dx) < 1e-9:
        dx, dy = 1.0, 0.0
    slope = dy / dx

    left_gap = (pts[i][0] - prev_pt[0]) if prev_pt else (
        next_pt[0] - pts[i][0] if next_pt else 0.3)
    right_gap = (next_pt[0] - pts[i][0]) if next_pt else (
        pts[i][0] - prev_pt[0] if prev_pt else 0.3)

    lx = max(1e-4, left_gap * AUTO_TANGENT_RATIO)
    rx = max(1e-4, right_gap * AUTO_TANGENT_RATIO)
    return ((-lx, -lx * slope), (rx, rx * slope))


def resolve_tangents(points, tangents=None):
    """포인트마다 실제로 쓸 (in_vec, out_vec, broken) 목록.

    `None` 이거나 한쪽만 비어 있으면 그 자리를 자동 탄젠트로 채운다 — 그리기와 계산이
    **같은 값**을 보게 하려면 이 해석이 한 군데에만 있어야 한다.
    """
    pts, tans = normalize_curve(points, tangents)
    out = []
    for i in range(len(pts)):
        auto_in, auto_out = auto_tangent_vectors(pts, i)
        entry = tans[i] if isinstance(tans[i], dict) else None
        if entry is None:
            out.append((auto_in, auto_out, False))
            continue
        in_vec = entry.get("in") or auto_in
        out_vec = entry.get("out") or auto_out
        out.append((tuple(in_vec), tuple(out_vec), bool(entry.get("broken"))))
    return out


def tangent_polar(vec, side=SIDE_OUT):
    """핸들 벡터 -> (각도 deg, 길이).

    각도는 **핸들이 뻗는 방향**으로 잰다(in 은 -x 쪽). 그래서 끊지 않은 탄젠트는
    양쪽 각도가 같다.
    """
    dx, dy = float(vec[0]), float(vec[1])
    if side == SIDE_IN:
        dx, dy = -dx, -dy
    length = math.sqrt(dx * dx + dy * dy)
    angle = math.degrees(math.atan2(dy, dx)) if length > 1e-12 else 0.0
    return (angle, length)


def tangent_vector(angle_deg, length, side=SIDE_OUT):
    """(각도 deg, 길이) -> 핸들 벡터. `tangent_polar` 의 역."""
    length = max(0.0, min(MAX_TANGENT_LENGTH, float(length)))
    rad = math.radians(float(angle_deg))
    dx, dy = math.cos(rad) * length, math.sin(rad) * length
    if side == SIDE_IN:
        dx, dy = -dx, -dy
    return (dx, dy)


def set_tangent(points, tangents, index, side=SIDE_OUT, angle=None, length=None,
                broken=None):
    """탄젠트 하나를 각도/길이로 지정한 **새 탄젠트 목록**을 돌려준다.

    - `broken=False` 면 반대쪽 핸들의 **각도를 따라 돌린다**(길이는 각자 유지) —
      이것이 '일반 탄젠트'(양쪽이 한 직선) 다.
    - `broken=True` 면 그쪽만 바뀐다.
    값은 전부 사본이라 호출부의 목록을 건드리지 않는다.
    """
    pts, tans = normalize_curve(points, tangents)
    if not (0 <= index < len(pts)):
        return tans

    resolved = resolve_tangents(pts, tans)
    in_vec, out_vec, was_broken = resolved[index]
    is_broken = was_broken if broken is None else bool(broken)

    cur_angle, cur_length = tangent_polar(
        out_vec if side == SIDE_OUT else in_vec, side)
    new_angle = cur_angle if angle is None else float(angle)
    new_length = cur_length if length is None else float(length)
    new_vec = tangent_vector(new_angle, new_length, side)

    if side == SIDE_OUT:
        out_vec = new_vec
        if not is_broken:
            # 반대쪽은 각도만 맞추고 길이는 자기 것을 유지한다.
            _a, other_len = tangent_polar(in_vec, SIDE_IN)
            in_vec = tangent_vector(new_angle, other_len, SIDE_IN)
    else:
        in_vec = new_vec
        if not is_broken:
            _a, other_len = tangent_polar(out_vec, SIDE_OUT)
            out_vec = tangent_vector(new_angle, other_len, SIDE_OUT)

    new_tans = list(tans)
    new_tans[index] = make_tangent(in_vec, out_vec, is_broken)
    return new_tans


def break_tangent(points, tangents, index, broken=True):
    """그 포인트의 탄젠트를 끊거나(양쪽 독립) 다시 잇는다.

    다시 이을 때는 **out 각도를 기준**으로 양쪽을 한 직선에 맞춘다(길이는 유지).
    """
    pts, tans = normalize_curve(points, tangents)
    if not (0 <= index < len(pts)):
        return tans

    in_vec, out_vec, _was = resolve_tangents(pts, tans)[index]
    new_tans = list(tans)
    new_tans[index] = make_tangent(in_vec, out_vec, broken)
    if broken:
        return new_tans
    # 잇기 — out 각도로 in 을 정렬한다.
    angle, _len = tangent_polar(out_vec, SIDE_OUT)
    return set_tangent(pts, new_tans, index, SIDE_OUT, angle=angle, broken=False)


def reset_tangent(tangents, index):
    """그 포인트를 자동 탄젠트로 되돌린다(항목을 None 으로)."""
    tans = list(tangents or [])
    if 0 <= index < len(tans):
        tans[index] = None
    return tans


def _bezier_y(p0, c0, c1, p1, x):
    """x 에서의 3차 베지어 y. 제어점 x 를 구간 안에 가둬 **함수**로 유지한다."""
    x0, y0 = p0
    x1, y1 = p1
    span = x1 - x0
    if span <= 1e-9:
        return y0

    # x0 <= cx0 <= cx1 <= x1 이면 X(t) 가 단조라 이분법이 성립한다.
    cx0 = min(max(c0[0], x0), x1)
    cx1 = min(max(c1[0], cx0), x1)
    cy0, cy1 = c0[1], c1[1]

    target = min(max(x, x0), x1)
    lo, hi = 0.0, 1.0
    for _ in range(24):
        t = (lo + hi) * 0.5
        mt = 1.0 - t
        xt = (mt * mt * mt * x0 + 3.0 * mt * mt * t * cx0
              + 3.0 * mt * t * t * cx1 + t * t * t * x1)
        if xt < target:
            lo = t
        else:
            hi = t

    t = (lo + hi) * 0.5
    mt = 1.0 - t
    return (mt * mt * mt * y0 + 3.0 * mt * mt * t * cy0
            + 3.0 * mt * t * t * cy1 + t * t * t * y1)


def _smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def _catmull_rom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * ((2.0 * p1) +
                  (-p0 + p2) * t +
                  (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
                  (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3)


def evaluate(points, interp, t, tangents=None):
    """정규화 거리 t(0~1) 에서의 커브 값(0~1).

    포인트 사이에서만 보간하고, 양 끝 바깥은 끝 포인트 값으로 고정한다(마야와 같다).
    `interp == INTERP_BEZIER` 일 때만 `tangents` 를 본다(나머지는 무시 — 옛 호출 그대로).
    """
    pts, tans = normalize_curve(points, tangents)
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

    if interp == INTERP_BEZIER:
        res = resolve_tangents(pts, tans)
        out_vec = res[i][1]
        in_vec = res[i + 1][0]
        c0 = (x0 + out_vec[0], y0 + out_vec[1])
        c1 = (x1 + in_vec[0], y1 + in_vec[1])
        return clamp01(_bezier_y((x0, y0), c0, c1, (x1, y1), t))
    if interp == INTERP_NONE:
        return clamp01(y0)
    if interp == INTERP_SMOOTH:
        return clamp01(y0 + (y1 - y0) * _smoothstep(local))
    if interp == INTERP_SPLINE:
        y_prev = pts[i - 1][1] if i > 0 else y0
        y_next = pts[i + 2][1] if i + 2 < len(pts) else y1
        return clamp01(_catmull_rom(y_prev, y0, y1, y_next, local))
    return clamp01(y0 + (y1 - y0) * local)


def sample(points, interp, count=64, tangents=None):
    """커브를 count 개로 균등 샘플링한 [(t, value), ...] (위젯 그리기용)."""
    count = max(2, int(count))
    step = 1.0 / (count - 1)
    return [(k * step, evaluate(points, interp, k * step, tangents))
            for k in range(count)]


def is_flat(points, interp=None, value=1.0, tolerance=1e-6, tangents=None):
    """커브가 처음부터 끝까지 `value` 로 평평한가.

    커브가 배수인 툴에서 **지금 이 커브가 결과를 바꾸고 있는지**를 UI 가 표시하는 데 쓴다
    (예: 버튼에 표식 붙이기). 보통은 포인트 y 만 보면 된다 — 모든 포인트가 같은 값이면
    어떤 보간이든 그 값으로 평평하다.

    **베지어는 예외다.** 포인트가 전부 같은 값이어도 탄젠트를 위아래로 끊어 두면 그 사이가
    부풀 수 있다. 그래서 그때만 실제로 몇 점 찍어 본다.
    """
    for _x, y in normalize_points(points):
        if abs(y - value) > tolerance:
            return False

    if interp == INTERP_BEZIER and tangents:
        for _t, v in sample(points, interp, 33, tangents):
            if abs(v - value) > tolerance:
                return False
    return True


def preset_points(name):
    """프리셋 이름 -> (포인트 사본, 보간). 없으면 기본값."""
    for label, points, interp in PRESETS:
        if label == name:
            return [tuple(p) for p in points], interp
    return list(DEFAULT_POINTS), DEFAULT_INTERP
