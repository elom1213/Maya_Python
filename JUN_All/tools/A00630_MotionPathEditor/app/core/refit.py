# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 목표 값 → 마야 애님 커브 키 다시 맞추기 (속도 그래프 계획서 §4-4)
"""
refit = "프레임마다 이 값이 나와야 한다" 는 목표를 **키 프레임은 그대로 둔 채** 키 값 · 탄젠트로 맞춘다.
속도 Smooth · 경로 모양 Smooth · Whole Pose 가 모두 이 한 경로를 쓴다.

마야 애님 커브 한 구간 (G0 골든 실측, 24/30/60 fps · cm/m · 가중/비가중 전부 오차 < 1e-11)
-------------------------------------------------------------------------------------
    탄젠트 XY (`MFnAnimCurve.getTangentXY`) 는 **x = 초, y = 내부 단위 값** 이다.
    키 i → i+1 사이는 3차 Bezier:
        P0 = (t_i, y_i)
        P1 = (t_i + Lout_i,  y_i + mout_i · Lout_i)
        P2 = (t_i+1 − Lin_i+1,  y_i+1 − min_i+1 · Lin_i+1)
        P3 = (t_i+1, y_i+1)
    기울기(프레임당)  m = y / x / fps
    핸들 시간 길이 L  : 비가중 = 구간 길이 / 3 (x 크기는 무시된다 → 결과가 3차 Hermite),
                       가중   = x · fps / 3
그래서 **핸들 시간 길이를 고정하면** 각 시간 t 의 Bezier 매개변수 u 가 고정되고, 값은 기울기 m 에 **선형**이다
→ 구간 안 모든 표본의 오차 제곱합을 최소로 하는 기울기를 numpy 최소제곱 한 번으로 푼다.

맞추는 방법
-----------
1. 바뀐 표본을 덮는 키 구간 [kl, kr] 을 찾는다. 양 끝 키(kl, kr)는 **값 · 탄젠트 고정**(바깥 커브가 그대로).
   바뀐 곳이 첫 키 앞 / 마지막 키 뒤까지 가면 바뀌지 않은 바로 앞 · 뒤 표본에 **고정 앵커 키**를 넣는다(지금 값 · 지금 기울기).
2. 안쪽 키의 값 = 그 시간의 목표 값. 기울기는 최소제곱(탄젠트가 묶인 키는 in = out 하나, 풀린 키는 둘).
   **안 바뀐 구간 쪽 기울기는 원래대로**(그 키의 묶음을 푼다 - 정지 경계의 flat 이 남는다), 안 바뀐 표본은 오차를 10 배로 친다.
   표본이 없는 구간(키가 매 프레임)은 새 값의 Catmull-Rom 기울기로 끌리게 약한 정규화 항을 둔다.
3. 표본 오차가 Tolerance 를 넘으면 가장 큰 곳에 키를 넣고 2 로 (상한 max_added, 상한이면 가장 좋았던 결과).
   그래도 못 맞추면 바뀐 범위 바로 바깥에 **경계 키**(원래 모양 그대로 나눈 키)를 넣고 다시 맞춰 나은 쪽을 고른다.
   키 넣기는 가중 커브도 de Casteljau 로 정확히 나눈다(원래 모양 그대로).
4. 쓰기 = `MFnAnimCurve` 로, 한 `MAnimCurveChange` 에. 바뀐 키 + 양 끝 키는 탄젠트 타입을 **fixed** 로(auto · spline 은 값이
   바뀌면 마야가 다시 계산해 이웃까지 움직인다).

수학 부분(CurveSnap · fit)은 마야 없이 돈다 - 마야는 read_curve / write_fit 만.
"""

import numpy as np

try:
    import maya.api.OpenMaya as om
    import maya.api.OpenMayaAnim as oma
except Exception:                                          # noqa: BLE001 - 수학 시험은 마야 없이
    om = None
    oma = None

TIME_EPS = 1e-6
VALUE_EPS = 1e-9            # 이보다 적게 바뀐 표본은 "안 바뀜"
REG = 1e-3                  # 기울기 정규화 세기 (표본이 많으면 무시될 만큼 작게)
UNCHANGED_WEIGHT = 10.0     # 안 바뀐 표본은 오차를 10 배로 친다 = tol/10 안에 (브러시 밖 · 정지)

# 커브 종류별 기본 허용 오차 (내부 단위) - 거리 cm · 각도 rad · 그 밖
TOL_LINEAR = 0.01
TOL_ANGULAR = np.radians(0.05)
TOL_UNITLESS = 0.001


class CurveSnap(object):
    """애님 커브 한 개의 키들 (시간은 UI 프레임, 값은 내부 단위). 바꾸지 않는 사본."""

    def __init__(self, times, values, lin, lout, min_, mout, weighted, locked, fps):
        self.t = np.asarray(times, dtype="float64")
        self.y = np.asarray(values, dtype="float64")
        self.lin = np.asarray(lin, dtype="float64")         # 가중일 때만 뜻: in 핸들 시간 길이 (프레임)
        self.lout = np.asarray(lout, dtype="float64")
        self.min = np.asarray(min_, dtype="float64")        # in 기울기 (값 / 프레임)
        self.mout = np.asarray(mout, dtype="float64")
        self.weighted = bool(weighted)
        self.locked = np.asarray(locked, dtype=bool)
        self.fps = float(fps)

    @property
    def count(self):
        return len(self.t)

    def copy(self):
        return CurveSnap(self.t.copy(), self.y.copy(), self.lin.copy(), self.lout.copy(), self.min.copy(),
                         self.mout.copy(), self.weighted, self.locked.copy(), self.fps)

    # ---------------------------------------------------------------- 구간 핸들
    def handles(self, i):
        """구간 i → i+1 의 (Lout_i, Lin_i+1) 프레임."""
        if not self.weighted:
            third = (self.t[i + 1] - self.t[i]) / 3.0
            return third, third
        return self.lout[i], self.lin[i + 1]

    def segment_u(self, i, ts):
        """구간 i 안의 시간들 → Bezier 매개변수 u (가중이면 x(u) = t 를 풀고, 아니면 선형)."""
        t0, t1 = self.t[i], self.t[i + 1]
        s = (np.asarray(ts, dtype="float64") - t0) / (t1 - t0)
        if not self.weighted:
            return np.clip(s, 0.0, 1.0)
        a, b = self.handles(i)
        x1 = t0 + a
        x2 = t1 - b
        ts = np.asarray(ts, dtype="float64")
        lo = np.zeros_like(ts)
        hi = np.ones_like(ts)
        for _ in range(60):                     # 이분법 (x(u) 는 핸들이 구간 안이면 단조)
            u = 0.5 * (lo + hi)
            x = (1 - u) ** 3 * t0 + 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u ** 2 * x2 + u ** 3 * t1
            below = x < ts
            lo = np.where(below, u, lo)
            hi = np.where(below, hi, u)
        return 0.5 * (lo + hi)

    # ---------------------------------------------------------------- 평가
    def evaluate(self, ts):
        """시간들 → 값 (키 범위 밖은 상수 - 마야 기본 pre/post infinity)."""
        ts = np.atleast_1d(np.asarray(ts, dtype="float64"))
        out = np.empty_like(ts)
        if self.count == 0:
            out[:] = 0.0
            return out
        out[ts <= self.t[0]] = self.y[0]
        out[ts >= self.t[-1]] = self.y[-1]
        if self.count == 1:
            return out
        inside = (ts > self.t[0]) & (ts < self.t[-1])
        if not np.any(inside):
            return out
        # v01.11 - 모든 표본을 한 번에 (구간마다 루프를 돌면 매 프레임 키 6,000 개 커브 평가 한 번이 0.1 초였다)
        tt = ts[inside]
        i = np.clip(np.searchsorted(self.t, tt, side="right") - 1, 0, self.count - 2)
        t0, t1 = self.t[i], self.t[i + 1]
        if self.weighted:
            a, b = self.lout[i], self.lin[i + 1]
            x1, x2 = t0 + a, t1 - b
            lo = np.zeros_like(tt)
            hi = np.ones_like(tt)
            for _ in range(60):                 # 이분법 (segment_u 와 같은 식, 표본마다 핸들이 다르다)
                u = 0.5 * (lo + hi)
                x = (1 - u) ** 3 * t0 + 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u ** 2 * x2 + u ** 3 * t1
                below = x < tt
                lo = np.where(below, u, lo)
                hi = np.where(below, hi, u)
            u = 0.5 * (lo + hi)
        else:
            a = b = (t1 - t0) / 3.0
            u = np.clip((tt - t0) / (t1 - t0), 0.0, 1.0)
        y0, y1 = self.y[i], self.y[i + 1]
        p1 = y0 + self.mout[i] * a
        p2 = y1 - self.min[i + 1] * b
        out[inside] = (1 - u) ** 3 * y0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u ** 2 * p2 + u ** 3 * y1
        return out

    def slope_at(self, t, h=1e-4):
        """그 시간의 기울기 (값 / 프레임, 수치). 키 범위 밖은 0."""
        if self.count < 2 or t <= self.t[0] or t >= self.t[-1]:
            return 0.0
        a, b = self.evaluate([t - h, t + h])
        return float((b - a) / (2 * h))

    def find(self, t):
        hit = np.nonzero(np.abs(self.t - t) < TIME_EPS)[0]
        return int(hit[0]) if len(hit) else -1

    # ---------------------------------------------------------------- 키 넣기 (사본 안에서)
    def insert(self, t, value, slope, locked=True):
        """키를 넣고 인덱스를 돌려준다.

        가중 커브는 그 구간 Bezier 를 **de Casteljau 로 정확히 둘로 나눈** 핸들 길이를 쓴다 - 이웃 키의 핸들은 방향(기울기)
        그대로 길이만 u / (1 − u) 배, 새 키는 나눈 점의 안 · 밖 핸들. (시간 비율로 줄이면 원래 모양이 깨져 G0 에서 키 옆
        오차가 0.19 cm 남았다.) 비가중은 핸들 = 구간 1/3 규칙이라 Hermite 분할이 그대로 정확하다.
        """
        i = int(np.searchsorted(self.t, t))
        if self.weighted and 0 < i < self.count:
            seg = i - 1
            u = float(self.segment_u(seg, [t])[0])
            a, b = self.handles(seg)
            t0, t1 = self.t[seg], self.t[i]
            x0, x1, x2, x3 = t0, t0 + a, t1 - b, t1
            ax, bx, cx = x0 + u * (x1 - x0), x1 + u * (x2 - x1), x2 + u * (x3 - x2)
            dx, ex = ax + u * (bx - ax), bx + u * (cx - bx)
            self.lout[seg] = a * u
            self.lin[i] = b * (1.0 - u)
            lin_new = t - dx
            lout_new = ex - t
            y0, y3 = self.y[seg], self.y[i]
            y1, y2 = y0 + self.mout[seg] * a, y3 - self.min[i] * b
            ay, by, cy = y0 + u * (y1 - y0), y1 + u * (y2 - y1), y2 + u * (y3 - y2)
            dy, ey = ay + u * (by - ay), by + u * (cy - by)
            if ex - dx > 1e-12:
                slope = (ey - dy) / (ex - dx)
        else:
            span = (self.t[1] - self.t[0]) if self.count > 1 else 3.0
            lin_new = lout_new = span / 3.0
        self.t = np.insert(self.t, i, t)
        self.y = np.insert(self.y, i, value)
        self.lin = np.insert(self.lin, i, lin_new)
        self.lout = np.insert(self.lout, i, lout_new)
        self.min = np.insert(self.min, i, slope)
        self.mout = np.insert(self.mout, i, slope)
        self.locked = np.insert(self.locked, i, locked)
        return i


# ---------------------------------------------------------------------- 맞추기
class FitResult(object):
    __slots__ = ("snap", "first", "last", "added", "anchors", "error", "changed")

    def __init__(self, snap, first, last, added, anchors, error, changed):
        self.snap = snap            # 맞춘 뒤 커브 (사본)
        self.first = first          # 바뀐 범위의 첫 키 인덱스(고정 끝, 결과 커브 기준)
        self.last = last
        self.added = added          # 오차 때문에 넣은 키 시간들
        self.anchors = anchors      # 앵커로 넣은 키 시간들
        self.error = error          # 표본 최대 오차 (내부 단위)
        self.changed = changed      # 바꿀 것이 있었나


def _catmull(t, y):
    """새 값의 Catmull-Rom 기울기 (정규화 기준)."""
    n = len(t)
    m = np.zeros(n)
    if n < 2:
        return m
    m[1:-1] = (y[2:] - y[:-2]) / (t[2:] - t[:-2])
    m[0] = (y[1] - y[0]) / (t[1] - t[0])
    m[-1] = (y[-1] - y[-2]) / (t[-1] - t[-2])
    return m


def _seg_changed(snap, kl, kr, rt, changed_rt, key_changed):
    """구간 j(kl ≤ j < kr) 가 바뀌나 - 안쪽 표본이 바뀌었거나 양 끝 키 값이 바뀌었으면."""
    out = {}
    for j in range(kl, kr):
        t0, t1 = snap.t[j], snap.t[j + 1]
        sel = (rt > t0 + TIME_EPS) & (rt < t1 - TIME_EPS)
        out[j] = bool(np.any(changed_rt[sel])) or key_changed.get(j, False) or key_changed.get(j + 1, False)
    return out


def _solve_slopes(snap, kl, kr, st, sy, ref, seg_changed, weights):
    """안쪽 키(kl < i < kr) 의 **바뀌는 구간 쪽** 기울기를 최소제곱으로 snap 에 써 넣는다. 키 값은 이미 들어 있어야 한다.

    - 양쪽 구간이 다 바뀌고 탄젠트가 묶인 키 : in = out 하나
    - 한쪽 구간만 바뀌는 키 : 그쪽만 풀고 다른 쪽은 원래 기울기 그대로 → 묶여 있었으면 푼다(정지 경계의 flat 이 남는다)
    - weights : 표본마다 무게 (안 바뀐 표본은 크게 - 원래대로 남게)
    """
    cols = {}               # (키, "in"/"out") -> 열 번호
    n = 0
    for i in range(kl + 1, kr):
        fin, fout = seg_changed.get(i - 1, False), seg_changed.get(i, False)
        if fin and fout and snap.locked[i]:
            cols[(i, "in")] = cols[(i, "out")] = n
            n += 1
            continue
        if fin:
            cols[(i, "in")] = n
            n += 1
        if fout:
            cols[(i, "out")] = n
            n += 1
        if fin != fout and snap.locked[i]:
            snap.locked[i] = False
    if n == 0:
        return
    rows_a, rows_b = [], []
    for i in range(kl, kr):
        t0, t1 = snap.t[i], snap.t[i + 1]
        sel = (st > t0 + TIME_EPS) & (st < t1 - TIME_EPS)
        if not np.any(sel):
            continue
        u = snap.segment_u(i, st[sel])
        a, b = snap.handles(i)
        b0, b1, b2, b3 = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3
        y0, y1 = snap.y[i], snap.y[i + 1]
        const = (b0 + b1) * y0 + (b2 + b3) * y1
        rhs = sy[sel] - const
        A = np.zeros((len(u), n))
        # out 기울기 of i : b1 · a,  in 기울기 of i+1 : − b2 · b
        if (i, "out") in cols:
            A[:, cols[(i, "out")]] += b1 * a
        else:
            rhs = rhs - b1 * a * snap.mout[i]
        if (i + 1, "in") in cols:
            A[:, cols[(i + 1, "in")]] += -b2 * b
        else:
            rhs = rhs + b2 * b * snap.min[i + 1]
        w = weights[sel]
        rows_a.append(A * w[:, None])
        rows_b.append(rhs * w)
    # 정규화: 기울기 · 이웃 구간 평균 길이 ≈ Catmull-Rom 기울기 · 같은 길이 (값 단위로 맞춰 무게를 준다)
    seen = set()
    for (i, side), c in cols.items():
        if c in seen:
            continue
        seen.add(c)
        span = 0.5 * ((snap.t[min(i + 1, snap.count - 1)] - snap.t[max(i - 1, 0)]))
        w = np.sqrt(REG) * span
        row = np.zeros((1, n))
        row[0, c] = w
        rows_a.append(row)
        rows_b.append(np.array([w * ref[i]]))
    A = np.vstack(rows_a)
    B = np.concatenate(rows_b)
    sol, *_ = np.linalg.lstsq(A, B, rcond=None)
    for (i, side), c in cols.items():
        if side == "in":
            snap.min[i] = sol[c]
        else:
            snap.mout[i] = sol[c]


def fit(snap, st, sy, tol, max_added=None):
    """snap(원래 커브)을 목표 표본(st 시간, sy 값)에 맞춘 결과. snap 은 바꾸지 않는다.

    st 는 정렬된 시간들(정수 프레임 + 키 시간 등). **영향 구간 안 키 시간은 st 에 들어 있어야** 한다(값을 바로 넣는다).
    안 바뀐 표본은 tol / UNCHANGED_WEIGHT 안에 들어야 한다(브러시 밖 · 정지가 원래대로 남게).
    max_added 기본 = 구간마다 3 + 바뀐 프레임 6 개마다 1 (키가 듬성한 커브를 크게 리타임할 때 - Whole Pose 회전 등).

    먼저 기존 키만으로(필요한 곳에 키를 더해) 맞춰 보고, 허용치를 못 넘으면 **바뀐 범위 바로 바깥 표본에 경계 키**
    (원래 모양을 정확히 나눈 키)를 넣고 다시 맞춰 더 나은 쪽을 고른다 - 키가 듬성한 커브(양 끝 키 둘뿐인 회전)는
    바뀐 곳과 안 바뀐 곳이 한 구간에 섞여 키를 넣어도 수렴이 느렸다(G2: Whole Pose 0.7°).
    """
    st = np.asarray(st, dtype="float64")
    sy = np.asarray(sy, dtype="float64")
    cur = snap.evaluate(st)
    changed = np.abs(sy - cur) > VALUE_EPS
    if not np.any(changed) or snap.count == 0:
        return FitResult(snap.copy(), -1, -1, [], [], 0.0, False)
    first = _fit_once(snap, st, sy, changed, tol, max_added, False)
    if first.error <= tol:
        return first
    second = _fit_once(snap, st, sy, changed, tol, max_added, True)
    if second.error < first.error:
        return second
    return first


def _fit_once(snap, st, sy, changed, tol, max_added, boundary):
    out = snap.copy()
    ia = int(np.nonzero(changed)[0][0])
    ib = int(np.nonzero(changed)[0][-1])
    ta, tb = st[ia], st[ib]
    anchors = []
    if boundary:
        # 바뀐 범위 바로 바깥의 안 바뀐 표본에 모양 그대로의 키 (이미 키가 있거나 표본이 없으면 그대로)
        for j in (ia - 1, ib + 1):
            if 0 <= j < len(st) and out.find(st[j]) < 0 and out.t[0] < st[j] < out.t[-1]:
                out.insert(float(st[j]), float(snap.evaluate([st[j]])[0]), snap.slope_at(float(st[j])))
                anchors.append(float(st[j]))
    # ---- 왼쪽 끝 키 : ta 보다 앞의 마지막 키, 없으면 바뀌지 않은 앞 표본에 앵커
    left = np.nonzero(out.t < ta - TIME_EPS)[0]
    if len(left):
        kl_t = out.t[left[-1]]
    else:
        if ia == 0:
            raise ValueError("the change starts at the first sample - no unchanged sample before it")
        kl_t = st[ia - 1]
        out.insert(kl_t, float(snap.evaluate([kl_t])[0]), snap.slope_at(kl_t))
        anchors.append(kl_t)
    right = np.nonzero(out.t > tb + TIME_EPS)[0]
    if len(right):
        kr_t = out.t[right[0]]
    else:
        if ib == len(st) - 1:
            raise ValueError("the change reaches the last sample - no unchanged sample after it")
        kr_t = st[ib + 1]
        out.insert(kr_t, float(snap.evaluate([kr_t])[0]), snap.slope_at(kr_t))
        anchors.append(kr_t)
    in_region = (st > kl_t + TIME_EPS) & (st < kr_t - TIME_EPS)
    rt, ry, rc = st[in_region], sy[in_region], changed[in_region]
    weights = np.where(rc, 1.0, UNCHANGED_WEIGHT)
    kl = out.find(kl_t)
    kr = out.find(kr_t)
    if max_added is None:
        max_added = 3 * max(kr - kl, 1) + int(tb - ta) // 6
    added = []
    best = None
    while True:
        kl = out.find(kl_t)
        kr = out.find(kr_t)
        # 안쪽 키 값 = 목표, 키 값이 바뀌는지
        key_changed = {}
        for i in range(kl + 1, kr):
            hit = np.nonzero(np.abs(rt - out.t[i]) < TIME_EPS)[0]
            if len(hit):
                out.y[i] = ry[hit[0]]
                key_changed[i] = bool(rc[hit[0]])
            else:                                   # 표본에 없는 키 시간 - 목표를 선형 보간
                out.y[i] = float(np.interp(out.t[i], rt, ry))
                key_changed[i] = True
        seg_changed = _seg_changed(out, kl, kr, rt, rc, key_changed)
        idx = np.arange(kl, kr + 1)
        ref = np.zeros(out.count)
        ref[idx] = _catmull(out.t[idx], out.y[idx])
        _solve_slopes(out, kl, kr, rt, ry, ref, seg_changed, weights)
        on_key = np.zeros(len(rt), dtype=bool)
        for i in range(kl, kr + 1):
            on_key |= np.abs(rt - out.t[i]) < TIME_EPS
        res = np.abs(out.evaluate(rt) - ry) * weights
        res[on_key] = 0.0
        error = float(res.max()) if len(res) else 0.0
        if best is None or error < best[0] - 1e-12:
            best = (error, out.copy(), list(added))
        if error <= tol or len(added) >= max_added:
            break
        j = int(np.argmax(res))
        t_new = float(rt[j])
        out.insert(t_new, float(ry[j]), out.slope_at(t_new))
        added.append(t_new)
    # 키를 더 넣었는데 오차가 오히려 커지는 일이 있다(가중 핸들 길이 고정) - 상한에 걸리면 가장 좋았던 결과로
    error, out, added = best
    return FitResult(out, out.find(kl_t), out.find(kr_t), added, anchors, error, True)


# ---------------------------------------------------------------------- 마야 읽기 · 쓰기
def fps():
    return om.MTime(1.0, om.MTime.kSeconds).asUnits(om.MTime.uiUnit())


def read_curve(fn):
    """MFnAnimCurve → CurveSnap."""
    unit = om.MTime.uiUnit()
    f = fps()
    n = fn.numKeys
    times, values, lin, lout, mi, mo, locked = [], [], [], [], [], [], []
    for i in range(n):
        times.append(fn.input(i).asUnits(unit))
        values.append(fn.value(i))
        ix, iy = fn.getTangentXY(i, True)
        ox, oy = fn.getTangentXY(i, False)
        lin.append(ix * f / 3.0)
        lout.append(ox * f / 3.0)
        mi.append(iy / ix / f if abs(ix) > 1e-12 else 0.0)
        mo.append(oy / ox / f if abs(ox) > 1e-12 else 0.0)
        locked.append(fn.tangentsLocked(i))
    return CurveSnap(times, values, lin, lout, mi, mo, fn.isWeighted, locked, f)


def tolerance_for(fn):
    """커브 종류별 기본 허용 오차 (내부 단위)."""
    t = fn.animCurveType
    if t in (oma.MFnAnimCurve.kAnimCurveTL, oma.MFnAnimCurve.kAnimCurveUL):
        return TOL_LINEAR
    if t in (oma.MFnAnimCurve.kAnimCurveTA, oma.MFnAnimCurve.kAnimCurveUA):
        return TOL_ANGULAR
    return TOL_UNITLESS


def _tangent_xy(slope, length, weighted, f):
    """기울기(값/프레임) · 핸들 길이(프레임) → setTangent 의 (x 초, y 값)."""
    if weighted:
        x = length * 3.0 / f
        return x, slope * length * 3.0
    return 1.0 / f, slope            # 비가중: x 크기는 무시된다 - 기울기 y/x/fps = slope


def write_fit(fn, result, change):
    """FitResult 를 커브에 쓴다 (한 change 에). 결과 커브의 [first, last] 키만 건드린다."""
    snap = result.snap
    unit = om.MTime.uiUnit()
    f = snap.fps
    fixed = oma.MFnAnimCurve.kTangentFixed
    # 1) 새 키 (앵커 · 오차 키) - 넣은 뒤 인덱스는 시간으로 다시 찾는다
    for t in list(result.anchors) + list(result.added):
        if fn.find(om.MTime(t, unit)) is None:
            fn.addKey(om.MTime(t, unit), float(snap.y[snap.find(t)]), fixed, fixed, change)
    # 2) 범위의 키를 fixed 로 (값을 바꿔도 마야가 탄젠트를 다시 계산하지 않게)
    idx = []
    for i in range(result.first, result.last + 1):
        k = fn.find(om.MTime(snap.t[i], unit))
        if k is not None:
            idx.append((i, k))
    fn.setTangentTypes([k for _i, k in idx], fixed, fixed, change)
    # 3) 잠금을 잠깐 푼다 - tangent lock · weight lock 이 걸려 있으면 한쪽을 쓸 때 마야가 반대쪽 각도 · 길이까지 바꾼다
    #    (G0 실측: 가중 커브에서 오차 9 cm). 다 쓴 뒤 원래(새 키는 snap 의 묶음) 상태로 다시 건다.
    new = set(round(t, 6) for t in list(result.anchors) + list(result.added))
    locks = {}
    for i, k in idx:
        tl = bool(snap.locked[i])           # 결과의 묶음 (한쪽만 푼 키 · 새 키 포함, 나머지는 원래와 같다)
        wl = fn.weightsLocked(k) if snap.weighted else None
        locks[k] = (tl, wl)
        fn.setTangentsLocked(k, False, change)
        if snap.weighted:
            fn.setWeightsLocked(k, False, change)
    # 4) 값 · 탄젠트 (끝 키는 값 · 바깥쪽 탄젠트가 원래 그대로 - 안쪽 탄젠트도 원래 값이라 다시 써도 같다)
    for i, k in idx:
        fn.setValue(k, float(snap.y[i]), change)
    for i, k in idx:
        lin = snap.lin[i] if snap.weighted else 1.0
        lout = snap.lout[i] if snap.weighted else 1.0
        xi, yi = _tangent_xy(snap.min[i], lin, snap.weighted, f)
        xo, yo = _tangent_xy(snap.mout[i], lout, snap.weighted, f)
        fn.setTangent(k, xi, yi, True, change, False)
        fn.setTangent(k, xo, yo, False, change, False)
    for k, (tl, wl) in locks.items():
        fn.setTangentsLocked(k, tl, change)
        if wl is not None:
            fn.setWeightsLocked(k, wl, change)
