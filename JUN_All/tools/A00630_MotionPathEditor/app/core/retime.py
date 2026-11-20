# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 속도 Smooth · 속도 바꾸기 · 경로 모양 Smooth 의 수학 (속도 그래프 계획서 §4-3). 마야 비의존
"""
SpeedRetimer — 경로 **모양은 그대로**, 경로 위 어디에 언제 있는지(타이밍)만 바꾼다
------------------------------------------------------------------------------------
조밀 표본 u_j (균일 간격 h) 의 원래 위치 P_j, 구간 속도 v_j = |P_j+1 − P_j| / h.
상태 = 속도 배열 v (획마다 바뀐다). 새 호 길이 s'(t) = ∫v, 시간 왜곡 τ(t) = s₀⁻¹(s'(t)), 새 위치 = P(τ(t)).
→ 새 점은 늘 원래 경로 위에 있다(모양 유지). 키 프레임은 그대로, 키의 포즈가 경로를 따라 미끄러진다.

dab(중심 fc, 반경 r, 세기 k):
    w   = k · (1 − x²)²,  x = |mid − fc| / r      (부드러운 falloff, 반경 밖 0)
    v̄  = 정지 표본을 뺀 정규화 가우스 흐림 (σ = r/2, 3σ 까지 = 브러시보다 넓게 본다)
    v'  = (1 − w)·v + w·v̄,   정지 표본은 그대로
    보존: 브러시 지지 구간을 **정지 표본에서 끊은 조각마다** ∫v' = ∫v 가 되게 v' · (1 + λw) 로 맞춘다
          → 조각 양 끝의 호 길이가 원래와 같다 = 브러시 밖 움직임 불변, **정지는 같은 자리에서 정지**.
change(중심 fc, 양 a, 범위 reach): 잡은 곳은 a 만큼 빠르게(음수면 느리게), 범위 가장자리가 보상한다 (그래프 끌기, G4).

같은 원래 경로에서 매번 처음부터 계산하므로 여러 번 칠해도 흘러가지 않는다(오차 누적 없음).

ShapeSmoother — 경로 **모양**을 부드럽게 (G5)
---------------------------------------------
점들(시간 순서)에 Taubin 평활(λ = +w·0.5, μ = −w·0.53 한 쌍을 dab 마다 3 번): 울퉁불퉁한(짧은 파장) 것은 줄이고 큰 호(긴 파장)는
거의 줄이지 않는다 - 단순 평균은 호를 안쪽으로 오그라뜨린다. 반경 밖 · 경로 양 끝 점은 그대로.

AccelSmoother — **가속도**를 부드럽게 (v01.08)
----------------------------------------------
가속도 = 프레임 위치의 2차 차분 |P(f+1) − 2P(f) + P(f−1)| 이다. 그래서 점들을 **시간 축으로 가우스 평균**(σ = r/3)해 그 쪽으로 w 만큼 당긴다
(Taubin 처럼 되밀지 않는다 - 되밀면 2차 차분이 남는다). 모양 · 타이밍이 함께 바뀌어 튐 · 떨림 · 꺾인 곳이 둥글어진다.
브러시 지지 구간 양 끝 · 경로 양 끝은 그대로 → 브러시 밖 움직임 불변. Smooth Speed 는 꺾인 곳을 더 빨리 지나가게 해 가속도를 키울 수 있고
(실측 최대 0.057 → 0.195), Smooth Shape 는 큰 호를 지켜서 가속도가 10% 밖에 안 줄었다 → 가속도 그래프에는 이 브러시.
"""

import numpy as np

from . import arc_length as al

HOLD_REL = 1e-4             # 프레임당 이동이 경로 크기의 이 비율보다 작으면 정지
EPS_REL = 1e-9              # s₀ 를 엄격 증가로 만드는 아주 작은 속도 (정지 구간의 역함수가 한 값이 되게)
TAUBIN_MU = -0.53
TAUBIN_ITER = 3            # dab 한 번에 Taubin 반복 (한 번은 짧은 파장을 23% 밖에 못 줄인다)


def falloff(x):
    x = np.clip(np.asarray(x, dtype="float64"), 0.0, 1.0)
    return (1.0 - x * x) ** 2


def _gauss_blur(values, mask, sigma_samples):
    """mask 표본만 쓰는 정규화 가우스 흐림 (mask 밖은 원래 값)."""
    n = len(values)
    if n == 0 or sigma_samples <= 1e-9:
        return values.copy()
    half = int(np.ceil(3.0 * sigma_samples))
    k = np.exp(-0.5 * (np.arange(-half, half + 1) / sigma_samples) ** 2)
    m = mask.astype("float64")
    num = np.convolve(values * m, k, mode="same")
    den = np.convolve(m, k, mode="same")
    out = values.copy()
    ok = den > 1e-9
    out[ok] = num[ok] / den[ok]
    return out


def _runs(mask):
    """True 가 이어진 [시작, 끝) 조각들."""
    out = []
    i, n = 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


class SpeedRetimer(object):

    def __init__(self, u, points, hold_rel=HOLD_REL):
        self.u = np.asarray(u, dtype="float64")
        self.P = np.asarray(points, dtype="float64")
        if len(self.u) < 2:
            raise ValueError("A path needs at least two samples.")
        self.h = float(self.u[1] - self.u[0])
        self.mid = 0.5 * (self.u[:-1] + self.u[1:])
        self.size = al.size(self.P)
        self.eps = EPS_REL * self.size
        seg = np.linalg.norm(np.diff(self.P, axis=0), axis=1)
        self.v0 = seg / self.h
        self.hold = self.v0 < hold_rel * self.size
        self.s0 = self._arc(self.v0)

    # ---------------------------------------------------------------- 기본
    def _arc(self, v):
        return np.concatenate([[0.0], np.cumsum((v + self.eps) * self.h)])

    def tau(self, v, t):
        """시간 왜곡 τ(t): 새 타이밍의 시간 t 에 원래 경로의 어느 시간 위치에 있나."""
        s_new = np.interp(np.asarray(t, dtype="float64"), self.u, self._arc(v))
        return np.interp(s_new, self.s0, self.u)

    def points_at(self, v, t):
        """새 타이밍의 시간 t 위치들 (N,3) - 늘 원래 경로 위."""
        return al.positions(self.u, self.P, self.tau(v, t))

    def speed_at(self, v, frames):
        """새 타이밍의 프레임 속도 (그래프 미리보기)."""
        frames = np.asarray(frames, dtype="float64")
        s = self._arc(v) - self.eps * (self.u - self.u[0])
        lo = np.maximum(frames - 0.5, self.u[0])
        hi = np.minimum(frames + 0.5, self.u[-1])
        width = np.maximum(hi - lo, 1e-9)
        return (np.interp(hi, self.u, s) - np.interp(lo, self.u, s)) / width

    def _conserve(self, v_old, v_new, w):
        """브러시 지지 구간을 정지에서 끊은 조각마다 합을 원래대로 (v_new · (1 + λ·w))."""
        support = (w > 1e-12) & ~self.hold
        out = v_new.copy()
        for a, b in _runs(support):
            want = float(v_old[a:b].sum())
            seg = out[a:b]
            for _ in range(3):                      # 음수로 잘라낸 뒤 다시 맞추기
                have = float(seg.sum())
                if abs(have - want) <= 1e-12 * max(want, 1e-12):
                    break
                q = w[a:b] * seg
                denom = float(q.sum())
                if denom <= 1e-12 * max(want, 1e-12):
                    seg = v_old[a:b].copy()
                    break
                seg = np.maximum(seg + (want - have) / denom * q, 0.0)
            out[a:b] = seg
        return out

    # ---------------------------------------------------------------- 획
    def dab(self, v, fc, radius, strength):
        """속도 Smooth 한 번. 새 v (v 는 바꾸지 않는다)."""
        radius = max(float(radius), self.h)
        w = float(strength) * falloff(np.abs(self.mid - float(fc)) / radius)
        if not np.any(w > 1e-12):
            return v.copy()
        blurred = _gauss_blur(v, ~self.hold, max(radius / 2.0, self.h) / self.h)
        out = (1.0 - w) * v + w * blurred
        out[self.hold] = v[self.hold]
        return self._conserve(v, out, w)

    def change(self, v, fc, amount, reach):
        """fc 근처를 amount(경로 길이/프레임)만큼 빠르게(음수: 느리게), reach 가장자리가 보상. 새 v."""
        reach = max(float(reach), 2.0 * self.h)
        w = falloff(np.abs(self.mid - float(fc)) / reach)
        if not np.any(w > 1e-12):
            return v.copy()
        out = np.maximum(v + float(amount) * w, 0.0)
        out[self.hold] = v[self.hold]
        # 보상은 가운데가 아니라 가장자리에서 (잡은 곳은 amount 를 다 받는다)
        q_w = w * (1.0 - w)
        support = (w > 1e-12) & ~self.hold
        for a, b in _runs(support):
            want = float(v[a:b].sum())
            seg = out[a:b]
            q = q_w[a:b] * np.maximum(seg, 1e-12)
            denom = float(q.sum())
            if denom <= 1e-12:
                continue
            seg = np.maximum(seg + (want - float(seg.sum())) / denom * q, 0.0)
            have = float(seg.sum())
            if have > 1e-12:
                seg *= want / have                    # 잘라낸 만큼 비율로 마무리
            out[a:b] = seg
        return out


class ShapeSmoother(object):
    """경로 모양 Smooth - 점들 (times 시간 순서) 에 Taubin 평활."""

    def __init__(self, times, points):
        self.t = np.asarray(times, dtype="float64")
        self.P = np.asarray(points, dtype="float64")

    def _average(self, W, rows, sigma):
        out = W[rows].copy()
        for n, i in enumerate(rows):
            near = np.nonzero(np.abs(self.t - self.t[i]) <= 3.0 * sigma)[0]
            g = np.exp(-0.5 * ((self.t[near] - self.t[i]) / sigma) ** 2)
            out[n] = (W[near] * g[:, None]).sum(axis=0) / g.sum()
        return out

    def dab(self, W, fc, radius, strength):
        """모양 Smooth 한 번. 새 점들 (W 는 바꾸지 않는다)."""
        radius = max(float(radius), 1.0)
        w = float(strength) * falloff(np.abs(self.t - float(fc)) / radius)
        w[0] = w[-1] = 0.0
        rows = np.nonzero(w > 1e-12)[0]
        out = W.copy()
        if not len(rows):
            return out
        sigma = max(radius / 4.0, 0.75)
        for _ in range(TAUBIN_ITER):
            for factor in (0.5, TAUBIN_MU):
                avg = self._average(out, rows, sigma)
                out[rows] = out[rows] + (factor * w[rows])[:, None] * (avg - out[rows])
        return out


class AccelSmoother(ShapeSmoother):
    """가속도 Smooth (v01.08) - 시간 축 가우스 평균 쪽으로 당긴다(되밀지 않는다)."""

    ITER = 2

    def dab(self, W, fc, radius, strength):
        radius = max(float(radius), 1.0)
        w = float(strength) * falloff(np.abs(self.t - float(fc)) / radius)
        w[0] = w[-1] = 0.0
        rows = np.nonzero(w > 1e-12)[0]
        out = W.copy()
        if not len(rows):
            return out
        sigma = max(radius / 3.0, 1.0)
        for _ in range(self.ITER):
            avg = self._average(out, rows, sigma)
            out[rows] = out[rows] + (0.5 * w[rows])[:, None] * (avg - out[rows])
        return out
