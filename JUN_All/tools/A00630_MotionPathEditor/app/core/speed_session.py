# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 그래프 Smooth 세션 (속도 그래프 계획서 §4-5)
"""
StrokeSession = 경로 하나에 대한 획들. **획 하나 = 마야 undo 하나** (놓는 순간 등록).

    mode "speed" : 속도 Smooth / 속도 바꾸기 - 모양 유지, 타이밍만 (retime.SpeedRetimer)
    mode "shape" : 모양 Smooth (retime.ShapeSmoother)
    mode "deform": 목표 경로를 그대로 받는다 - set_state(P) (v01.10 Edit Path 의 프레임 점 · 폴오프 끌기, 매니퓰레이터 · 폴오프 계획서 §3-3)

흐름
----
    s = StrokeSession(cache)            # 시작 상태(원래 경로 · 부모 공간 · 커브)를 잡는다
    s.begin_stroke(); s.dab(...) ...    # 칠하는 동안: 상태만 바뀐다(커브 안 씀) → preview_points / preview_speed 로 미리보기
    s.end_stroke()                      # 놓을 때: 커브에 쓰고 junMotionPathSetKeys 로 undo 한 번 등록
    s.drop_stroke()                     # 놓기 전 취소 (Esc / 오른쪽 클릭)
    s.valid()                           # 바깥에서 커브가 바뀌었나(undo · 그래프 에디터) - 바뀌었으면 새 세션으로

획마다 undo 하나 (계획서 §4-5 에서 바꿈, 2026-11-20)
-----------------------------------------------------
계획서는 "여러 획 = 세션 끝에 undo 한 번" 이었지만, 마야에서 Ctrl+Z 는 보통 뷰포트로 가서 세션이 열린 채 누르면
**우리 획이 아니라 그 전의 다른 작업이** 되돌려진다(계획서 §4-5 위험). 그래서 획을 놓을 때마다 바로 등록한다.

**흘러가지 않게**: 목표는 늘 세션 시작 때의 **원래 경로**에서 계산하고(새 점 = 원래 경로 위), 커브에는
"직전 상태 → 새 상태" 의 **차이만** 더한다:  새 목표(f) = 지금 커브(f) + (L(새 상태, f) − L(직전 상태, f)).
브러시 밖은 차이가 정확히 0 → 그 프레임은 "안 바뀐 표본" 이라 원래대로 남고, refit 오차가 획마다 쌓여 번지지 않는다.

- 키 값은 **편집 레이어**에 쓴다: 목표 최종 translate → v = v₀ + (T* − T₀)/β (path_cache.solve 와 같은 식).
  β ≈ 0 인 프레임(부모 · 레이어 때문에 못 따라감)은 그 축을 원래 값으로 둔다(계획서 약속 8).
- 키 없는 축(그 레이어에 커브가 없음)은 건드리지 않는다. Whole Pose 는 같은 시간 왜곡을 rotate · scale 커브에도.
- 조밀 경로(정수 프레임 사이 0.25 프레임 간격): 자기 translate 는 커브를 그 시간에 정확히 평가하고,
  부모 공간 · 레이어 가중치는 구운 프레임 사이를 선형 보간한다(G0: 회전하는 부모에서도 경로 크기의 0.03% 차이 —
  exact=True 로 그 시간들을 다시 굽는 것보다 80배 빠르다).
"""

import numpy as np

import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

from . import anim_channels as ch
from . import arc_length as al
from . import draw_bridge
from . import parent_space
from . import refit
from . import retime

COMMAND = "junMotionPathSetKeys"
MODE_SPEED = "speed"
MODE_SHAPE = "shape"
MODE_ACCEL = "accel"          # v01.08 가속도 Smooth (retime.AccelSmoother)
MODE_DEFORM = "deform"        # v01.10 목표 경로를 직접 (set_state) - 상태 = cache.times 의 월드 점
ACCEL_TOL_FACTOR = 0.2         # 가속도 브러시는 refit 을 더 엄격히 - 위치 오차의 2차 차분이 그대로 가속도 잡음이 된다
POSE_ATTRS = ("rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ")
STEP = 0.25
BETA_EPS = 1e-6
TOL_REL = 0.001             # 위치 허용 오차 = 경로 크기의 0.1% (최소 refit.TOL_LINEAR) - 미터 씬에서 cm 고정값은 키를 너무 늘린다


def dense_points(cache, step=STEP, exact=False):
    """(u (M,), P (M,3)) - 경로 범위를 step 간격으로 (마지막 시간 포함)."""
    times = np.asarray(cache.times, dtype="float64")
    start, end = float(times[0]), float(times[-1])
    count = int(round((end - start) / step))
    u = start + step * np.arange(count + 1)
    u[-1] = end
    layers = cache.channels.layers_used()
    if exact:
        pms, weights = parent_space.bake([cache.node], list(u), layers=layers)
        PM = pms[cache.node]
    else:
        flat = cache.PM.reshape(len(times), 16)
        PM = np.stack([np.interp(u, times, flat[:, k]) for k in range(16)], axis=1).reshape(-1, 4, 4)
        weights = {L: (np.interp(u, times, wa), np.interp(u, times, wb)) for L, (wa, wb) in cache.W.items()}
    T = cache.channels.values(list(u), weights)
    local = np.hstack([cache.c + T, np.ones((len(u), 1))])
    return u, np.einsum("ni,nij->nj", local, PM)[:, :3]


def _signature(fn):
    """커브가 바깥에서 바뀌었는지 볼 서명 (키 수 · 시간 · 값 · 기울기)."""
    snap = refit.read_curve(fn)
    return (snap.count, tuple(np.round(snap.t, 6)), tuple(np.round(snap.y, 9)),
            tuple(np.round(snap.min, 9)), tuple(np.round(snap.mout, 9)))


class StrokeSession(object):

    def __init__(self, cache, mode=MODE_SPEED, step=STEP, whole_pose=False, tolerance_rel=TOL_REL, exact=False):
        if cache.locked:
            raise RuntimeError(cache.lock_reason)
        if cache.points is None or len(cache.times) < 3:
            raise RuntimeError("The path is too short.")
        self.cache = cache
        self.key = cache.key
        self.mode = mode
        self.whole_pose = bool(whole_pose) and mode == MODE_SPEED
        self.tolerance_rel = float(tolerance_rel)
        self.tolerance = max(refit.TOL_LINEAR, float(tolerance_rel) * al.size(cache.points))   # 위치 (내부 단위)
        if mode == MODE_ACCEL:
            self.tolerance = max(refit.TOL_LINEAR, self.tolerance * ACCEL_TOL_FACTOR)
        self.times = np.asarray(cache.times, dtype="float64")
        self.points0 = cache.points.copy()
        self.T0 = cache.T.copy()
        self.beta = cache.beta.copy() if cache.beta is not None else np.ones_like(self.T0)
        self.PMinv = cache.PMinv.copy()
        self.c = cache.c.copy()
        self.channels = ch.Channels(cache.node, cache.layer)
        self.L0 = self.channels.layer_values(list(self.times))
        if mode == MODE_SPEED:
            u, P = dense_points(cache, step, exact)
            self.retimer = retime.SpeedRetimer(u, P)
            state0 = self.retimer.v0.copy()
        elif mode == MODE_DEFORM:
            self.shaper = None
            state0 = self.points0.copy()
        else:
            smoother = retime.AccelSmoother if mode == MODE_ACCEL else retime.ShapeSmoother
            self.shaper = smoother(self.times, self.points0)
            state0 = self.points0.copy()
        self.stack = [state0]
        self.current = state0
        self.stroking = False
        # 커브: (이름, fn, 시작 스냅샷, translate 축 인덱스 또는 None)
        self.curves = []
        for k, axis in enumerate(self.channels.axes):
            if axis.state == "curve":
                self.curves.append((axis.attr, axis.fn, refit.read_curve(axis.fn), k))
        if self.whole_pose:
            for attr in POSE_ATTRS:
                try:
                    axis = ch.Axis(self.channels.obj, attr, self.channels.layer)
                except Exception:                          # noqa: BLE001
                    continue
                if axis.state == "curve":
                    self.curves.append((attr, axis.fn, refit.read_curve(axis.fn), None))
        self.signatures = self._signatures()
        self.report = []                    # 마지막 획: [(이름, 최대 오차, 넣은 키 수, 메시지)]

    # ---------------------------------------------------------------- 상태
    @property
    def strokes(self):
        return len(self.stack) - 1

    def _signatures(self):
        return [_signature(fn) for _n, fn, _s, _k in self.curves]

    def valid(self):
        """시작(또는 마지막 획) 뒤로 커브가 바깥에서 바뀌지 않았으면 True. 경로 노드가 없어져도 False."""
        try:
            layer = ch.root_layer() if ch.is_base(self.cache.layer) else self.cache.layer
            if self.cache.resolve() is None or layer != self.channels.layer:
                return False
            return self._signatures() == self.signatures
        except Exception:                                  # noqa: BLE001
            return False

    def begin_stroke(self):
        self.current = self.stack[-1]
        self.stroking = True

    def set_state(self, points):
        """deform 모드: 이번 획의 목표 경로 (N,3) - cache.times 의 새 월드 점. 놓을 때(end_stroke) 커브에 쓴다."""
        P = np.asarray(points, dtype="float64").reshape(self.points0.shape)
        self.current = P.copy()

    def dab(self, fc, radius, strength):
        if self.mode == MODE_DEFORM:
            return
        if self.mode == MODE_SPEED:
            self.current = self.retimer.dab(self.current, fc, radius, strength)
        else:
            self.current = self.shaper.dab(self.current, fc, radius, strength)

    def change_speed(self, fc, amount, reach):
        """그래프 끌기 (G4) - 획을 시작한 상태에서 fc 근처를 빠르게 / 느리게. amount 는 경로 길이 / 프레임."""
        if self.mode == MODE_SPEED:
            self.current = self.retimer.change(self.stack[-1], fc, amount, reach)

    def drop_stroke(self):
        """칠하던 획을 버린다 (놓기 전 취소)."""
        self.stroking = False
        self.current = self.stack[-1]

    # ---------------------------------------------------------------- 미리보기
    def preview_points(self, state=None):
        """(N,3) - cache.times 의 새 월드 점 (세션 시작 경로 기준)."""
        state = self.current if state is None else state
        if self.mode == MODE_SPEED:
            return self.retimer.points_at(state, self.times)
        return state

    def preview_speed(self, frames, state=None):
        state = self.current if state is None else state
        if self.mode == MODE_SPEED:
            return self.retimer.speed_at(state, frames)
        return al.speed(self.times, state, frames)

    def tau(self, t, state=None):
        state = self.current if state is None else state
        if self.mode == MODE_SPEED:
            return self.retimer.tau(state, t)
        return np.asarray(t, dtype="float64")

    # ---------------------------------------------------------------- 쓰기
    def _layer_targets(self, state):
        """그 상태의 새 월드 점 → 편집 레이어 값 (N,3). 못 따라가는 축 · 프레임은 원래 값."""
        W = self.preview_points(state)
        local = np.einsum("ni,nij->nj", np.hstack([W, np.ones((len(W), 1))]), self.PMinv)[:, :3]
        wanted = local - self.c
        out = self.L0.copy()
        ok = np.abs(self.beta) >= BETA_EPS
        out[ok] = self.L0[ok] + (wanted[ok] - self.T0[ok]) / self.beta[ok]
        return out

    def end_stroke(self):
        """획을 놓는다: 직전 상태 → 새 상태의 차이를 커브에 쓰고 undo 하나로 등록. 바뀐 것이 있으면 True."""
        self.stroking = False
        prev, new = self.stack[-1], self.current
        if new is prev:
            return False
        self.stack.append(new)
        self.report = []
        change = oma.MAnimCurveChange()
        wrote = False
        d_layer = self._layer_targets(new) - self._layer_targets(prev)
        for name, fn, start_snap, k in self.curves:
            now = refit.read_curve(fn)
            if k is not None:
                st = self.times
                sy = now.evaluate(st) + d_layer[:, k]
                tol = self.tolerance
            else:
                st = self._pose_samples(now)
                sy = now.evaluate(st) + (start_snap.evaluate(self.tau(st, new)) - start_snap.evaluate(self.tau(st, prev)))
                tol = refit.tolerance_for(fn)
            try:
                res = refit.fit(now, st, sy, tol)
            except ValueError as exc:
                self.report.append((name, 0.0, 0, str(exc)))
                continue
            if not res.changed:
                continue
            refit.write_fit(fn, res, change)
            wrote = True
            self.report.append((name, res.error, len(res.added) + len(res.anchors), ""))
        if wrote:
            draw_bridge.stage(change, self.channels.dirty_nodes())
            getattr(cmds, COMMAND)()
        self.signatures = self._signatures()
        self.cache.refresh()
        return wrote

    def _pose_samples(self, snap):
        """Whole Pose 커브의 표본 = 경로 범위의 정수 프레임 + 범위 안 그 커브의 키 시간."""
        start, end = self.times[0], self.times[-1]
        frames = set(np.arange(np.ceil(start), np.floor(end) + 1.0).tolist())
        frames |= {float(t) for t in snap.t if start - 1e-6 <= t <= end + 1e-6}
        return np.array(sorted(frames), dtype="float64")

