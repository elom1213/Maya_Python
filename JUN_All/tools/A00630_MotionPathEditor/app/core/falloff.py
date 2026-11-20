# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 폴오프 (매니퓰레이터 · 폴오프 계획서 §3-2) - 마야 · Qt 비의존
"""
고른 점 둘레의 가중치 w(f) (0~1).

    d(f) = 고른 시간들 중 가장 가까운 것과의 |f − s|  (프레임 - **경로를 따라 잰 거리**)
    w(f) = curve(d / R)  (d < R),  0 (그 밖),  고른 점 = 1

- 월드 거리로 재지 않는다: 경로가 고리 · 왕복이면 시간이 먼 점이 끌려와 [a, b] 가 한 구간이 아니게 된다(계획서 Q2).
- curve 는 공용 `Framework/core/falloff_curve` (가로 0 = 고른 점, 1 = 반경 끝). 기본 = Smooth 프리셋.
  매번 커브를 평가하지 않고 표(LUT)를 만들어 보간한다(1,000 프레임도 즉시).
- 색표: 1 노랑 → 0.5 주황 → 0 빨강 → 어두운 빨강 (마야 소프트 셀렉션과 같은 기대). 뷰포트 · 그래프가 같은 함수를 쓴다.
"""

import json

import numpy as np

from Framework.core import falloff_curve as fc

DEFAULT_PRESET = "Smooth"
LUT_SIZE = 257
LEVELS = 16                 # 색 선을 나눠 그릴 색 단계 수 (G0-1: mesh 선은 x-ray 가 안 먹어 색마다 lineStrip)

_STOPS = ((0.0, (0.35, 0.05, 0.05)), (0.15, (0.85, 0.10, 0.05)), (0.5, (1.0, 0.50, 0.05)), (1.0, (1.0, 0.95, 0.20)))


# ---------------------------------------------------------------------- 커브
def default_curve():
    points, interp = fc.preset_points(DEFAULT_PRESET)
    return {"points": [list(p) for p in points], "interp": interp, "tangents": None}


def curve_from_text(text):
    """설정 문자열(json) → {"points", "interp", "tangents"}. 비었거나 깨졌으면 기본."""
    if not text:
        return default_curve()
    try:
        data = json.loads(text)
        pts = [(float(x), float(y)) for x, y in data["points"]]
        if len(pts) < 1:
            raise ValueError
        return {"points": pts, "interp": str(data.get("interp") or fc.DEFAULT_INTERP), "tangents": data.get("tangents")}
    except (ValueError, TypeError, KeyError):
        return default_curve()


def curve_to_text(points, interp, tangents=None):
    return json.dumps({"points": [[float(x), float(y)] for x, y in points], "interp": interp,
                       "tangents": tangents})


def lut(curve=None):
    """(LUT_SIZE,) - 가로 0~1 의 커브 값."""
    curve = curve or default_curve()
    xs = np.linspace(0.0, 1.0, LUT_SIZE)
    return np.array([fc.evaluate(curve["points"], curve["interp"], x, curve.get("tangents")) for x in xs])


# ---------------------------------------------------------------------- 가중치
def weights(times, selected, radius, table=None):
    """(N,) 가중치. selected = 고른 시간들, radius = 프레임(0 이면 고른 점만 1)."""
    t = np.asarray(times, dtype="float64").reshape(-1)
    out = np.zeros(len(t))
    sel = np.asarray(sorted(selected), dtype="float64").reshape(-1)
    if not len(t) or not len(sel):
        return out
    # 가장 가까운 고른 시간까지의 거리 (정렬 + searchsorted - N x M 행렬을 만들지 않는다)
    idx = np.clip(np.searchsorted(sel, t), 1, max(len(sel) - 1, 1))
    if len(sel) == 1:
        d = np.abs(t - sel[0])
    else:
        d = np.minimum(np.abs(t - sel[idx - 1]), np.abs(t - sel[idx]))
    picked = d < 1e-6
    radius = float(radius)
    if radius > 1e-9:
        table = lut() if table is None else table
        inside = d < radius
        x = d[inside] / radius
        out[inside] = np.interp(x, np.linspace(0.0, 1.0, len(table)), table)
    out[picked] = 1.0
    return np.clip(out, 0.0, 1.0)


def spans(times, w):
    """[(a, b)] - w > 0 인 연속 구간의 처음 · 끝 시간 (선택 덩어리마다)."""
    t = np.asarray(times, dtype="float64")
    on = np.asarray(w) > 1e-9
    out = []
    i, n = 0, len(t)
    while i < n:
        if not on[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and on[j + 1]:
            j += 1
        out.append((float(t[i]), float(t[j])))
        i = j + 1
    return out


# ---------------------------------------------------------------------- 색
def colors(w):
    """(N,3) RGB - 가중치 색표."""
    w = np.clip(np.asarray(w, dtype="float64").reshape(-1), 0.0, 1.0)
    xs = np.array([s[0] for s in _STOPS])
    rgb = np.array([s[1] for s in _STOPS])
    return np.stack([np.interp(w, xs, rgb[:, k]) for k in range(3)], axis=1)


def level_of(w):
    """색 단계 0..LEVELS (0 = 범위 밖)."""
    w = np.asarray(w, dtype="float64")
    return np.where(w > 1e-9, np.clip(np.ceil(w * LEVELS), 1, LEVELS), 0).astype(int)


def line_runs(w):
    """[(단계, [점 인덱스...])] - 색 선을 단계마다 나눠 그릴 조각. 선분 i-(i+1) 의 색 = 두 점 가중치 평균."""
    w = np.asarray(w, dtype="float64")
    if len(w) < 2:
        return []
    seg = level_of((w[:-1] + w[1:]) * 0.5)
    runs = []
    i, n = 0, len(seg)
    while i < n:
        if seg[i] == 0:
            i += 1
            continue
        j = i
        while j + 1 < n and seg[j + 1] == seg[i]:
            j += 1
        runs.append((int(seg[i]), list(range(i, j + 2))))
        i = j + 1
    return runs


def level_color(level):
    """단계 → RGB (그 단계 가운데 가중치의 색)."""
    return tuple(colors([(level - 0.5) / float(LEVELS)])[0])
