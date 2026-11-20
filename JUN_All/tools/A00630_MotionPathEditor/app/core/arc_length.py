# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 호 길이 · 속도 · 가속도 (속도 그래프 계획서 §4-2). 마야 비의존 (numpy)
"""
경로 = 시간 순서 점들 (times (N,), points (N,3)). 점 사이는 직선(뷰포트에 그리는 선과 같다).

    s(t)        : 누적 호 길이 (첫 점 0)
    speed(f)    : 프레임 f 의 속도 = s(f + ½) − s(f − ½)   (경로 길이 / 프레임). 범위 끝은 반쪽을 두 배.
    accel(f)    : |P(f+1) − 2·P(f) + P(f−1)|              (경로 길이 / 프레임²) - 튐 · 떨림 찾기

그래프 표시 · Smooth 계산 · 미리보기가 모두 이 함수들을 쓴다.
"""

import numpy as np


def cumulative(points):
    """(N,) 누적 호 길이."""
    pts = np.asarray(points, dtype="float64")
    if len(pts) < 2:
        return np.zeros(len(pts))
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(seg)])


def arc_at(times, s, t):
    """시간들 t 의 누적 호 길이 (선형 보간, 범위 밖은 끝 값)."""
    return np.interp(np.asarray(t, dtype="float64"), np.asarray(times, dtype="float64"), s)


def speed(times, points, frames):
    """frames 마다 속도 (경로 길이 / 프레임)."""
    times = np.asarray(times, dtype="float64")
    frames = np.asarray(frames, dtype="float64")
    if len(times) < 2:
        return np.zeros(len(frames))
    s = cumulative(points)
    lo = np.maximum(frames - 0.5, times[0])
    hi = np.minimum(frames + 0.5, times[-1])
    width = np.maximum(hi - lo, 1e-9)
    return (arc_at(times, s, hi) - arc_at(times, s, lo)) / width


def accel(times, points, frames):
    """frames 마다 가속도 크기 (경로 길이 / 프레임²). 이웃 프레임이 없는 끝은 0."""
    times = np.asarray(times, dtype="float64")
    frames = np.asarray(frames, dtype="float64")
    pts = np.asarray(points, dtype="float64")
    if len(times) < 3:
        return np.zeros(len(frames))
    def at(t):
        return np.stack([np.interp(t, times, pts[:, k]) for k in range(3)], axis=1)
    out = np.linalg.norm(at(frames + 1.0) - 2.0 * at(frames) + at(frames - 1.0), axis=1)
    out[(frames - 1.0 < times[0] - 1e-9) | (frames + 1.0 > times[-1] + 1e-9)] = 0.0
    return out


def positions(times, points, frames):
    """frames 마다 위치 (N,3) - 선형 보간."""
    times = np.asarray(times, dtype="float64")
    pts = np.asarray(points, dtype="float64")
    frames = np.asarray(frames, dtype="float64")
    return np.stack([np.interp(frames, times, pts[:, k]) for k in range(3)], axis=1)


def size(points):
    """경로 크기 (경계 상자 대각선) - 정지 판정 · 허용 오차의 기준. 점이 다 같으면 1."""
    pts = np.asarray(points, dtype="float64")
    if len(pts) == 0:
        return 1.0
    d = float(np.linalg.norm(pts.max(axis=0) - pts.min(axis=0)))
    return d if d > 1e-9 else 1.0
