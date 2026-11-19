# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 경로 하나 (계획서 §4-2)
"""
PathCache = 대상 하나의 위치 경로.

    times  : 경로가 지나는 시간 (범위의 정수 프레임 + 범위 안의 키 시간)
    PM     : (N,4,4) 굽힌 부모 공간,  PMinv : 그 역행렬
    c      : (3,) 피벗 보정 = rotatePivot + rotatePivotTranslate (상수, 조인트 · 피벗 0 이면 0)
    T      : (N,3) translate (애님 커브에서 매번 다시 평가 - 굽지 않는다)
    points : (N,3) 월드 점 = (c + T) · PM  = 마야 `xform -q -ws -rp` (회전 피벗)

키를 움직여도 다시 굽지 않는다: `refresh()` 는 커브만 다시 평가하고 행렬 곱 한 번(1,000 프레임 약 2 ms, 0단계).
`rebake()` 는 부모 공간이 바뀌었을 때만(1단계는 Refresh 버튼).

solve(row, W) : 월드 점 W 에 피벗이 오게 하는 **편집 레이어 값** (정확한 역산)
    T* = W · PM⁻¹ − c  (필요한 최종 translate),   최종 T = α + β·v  (v = 편집 레이어 값, anim_channels 독스트링)
    → v_new = v_now + (T* − T_now) / β     (레이어가 없으면 β = 1 → v_new = T*)
    β 가 0 인 축(뮤트 · 가중치 0 · 위 override 가 가림)은 움직일 수 없다 → NaN (편집 세션이 건너뛴다)

애니메이션 레이어 (v01.03): 경로는 **모든 레이어를 합친** 실제 움직임이고, 키 점은 **편집 레이어**의 키다.
레이어 가중치는 부모 공간과 같은 시간 문맥 루프에서 굽는다(W). 편집 레이어를 바꿔도 다시 굽지 않는다(set_layer).
"""

import numpy as np

import maya.cmds as cmds

from . import anim_channels as ch
from . import parent_space

TIME_ROUND = ch.KEY_ROUND
BETA_EPS = 1e-6          # 편집 레이어 값이 최종 translate 에 이보다 적게 곱해지면 그 축은 움직일 수 없다고 본다


class PathKey(object):
    """경로 위 키 하나 (세 축 키 시간의 합집합 기준)."""

    __slots__ = ("t", "row", "partial")

    def __init__(self, t, row, partial):
        self.t = t
        self.row = row          # times 의 인덱스
        self.partial = partial  # 편집 가능한 축 중 키가 없는 축이 있다


class PathCache(object):

    def __init__(self, node, start, end, layer=None):
        self.node = ch.long_name(node) or node
        self.layer = layer                  # 편집 레이어 (None = Base)
        self.W = {}                         # {레이어: (wA (N,), wB (N,))}
        self.beta = None                    # (N,3) 편집 레이어 값 1 이 최종 translate 를 움직이는 양
        self.uuid = (cmds.ls(self.node, uuid=True) or [""])[0]
        self.start = int(start)
        self.end = int(end)
        self.times = []
        self.PM = None
        self.PMinv = None
        self.c = None
        self.T = None
        self.points = None
        self.keys = []
        self.channels = None
        self.lock_reason = ""
        self.dirty_bake = True

    # ---------------------------------------------------------------- 이름
    @property
    def key(self):
        """그리기 데이터 키 (UUID - 리네임 · 리페어런트 뒤에도 같다)."""
        return self.uuid or self.node

    def resolve(self):
        """UUID 로 지금 롱네임을 되찾는다. 씬에 없으면 None."""
        if self.uuid:
            found = cmds.ls(self.uuid, long=True) or []
            if found:
                self.node = found[0]
                return self.node
            return None
        return self.node if cmds.objExists(self.node) else None

    @property
    def label(self):
        return ch.short_name(self.node)

    @property
    def locked(self):
        return bool(self.lock_reason)

    # ---------------------------------------------------------------- 만들기
    def _frames(self):
        times = {round(float(f), TIME_ROUND): float(f) for f in range(self.start, self.end + 1)}
        for t in self.channels.key_times():
            if self.start - 1e-6 <= t <= self.end + 1e-6:
                times.setdefault(round(t, TIME_ROUND), t)
        return [times[k] for k in sorted(times)]

    def rebake(self, progress=None):
        """부모 공간 + 피벗 보정 굽기 (프레임마다 DG 문맥 평가)."""
        if self.resolve() is None:
            return False
        self._read_static()
        pms, weights = parent_space.bake([self.node], self.times, progress=progress,
                                         layers=self.channels.layers_used())
        self._take_bake(pms[self.node], weights)
        return True

    def _read_static(self):
        self.channels = ch.Channels(self.node, self.layer)
        self.lock_reason = self.channels.lock_reason()
        self.c = np.array(parent_space.pivot_offset(self.node), dtype="float64")
        self.times = self._frames()

    def _take_bake(self, pm, weights):
        self.PM = pm
        self.PMinv = np.linalg.inv(self.PM)
        self.W = dict(weights)
        self.dirty_bake = False
        self._evaluate()

    def _evaluate(self):
        """커브 → 최종 translate · β · 점 · 키 (굽기 없음)."""
        self.T = self.channels.values(self.times, self.W)
        self.beta = self.channels.coefficients(self.times, self.W)
        self._no_effect_lock()
        self._points()
        self._keys()

    def _no_effect_lock(self):
        """편집 레이어가 이 대상의 움직임에 전혀 영향을 주지 않으면(뮤트 · 가중치 0 · 위 override 가 다 가림) 잠근다."""
        if self.lock_reason or self.beta is None:
            return
        mask = self.channels.editable_mask()
        cols = [i for i, m in enumerate(mask) if m]
        if cols and np.all(np.abs(self.beta[:, cols]) < BETA_EPS):
            self.lock_reason = ("The animation layer {0} has no effect here (muted, weight 0, or covered by an "
                                "override layer above)".format(self.channels.layer))

    def set_layer(self, layer):
        """편집 레이어를 바꾼다. 가중치가 이미 구워져 있으면 굽지 않는다 - 다시 굽기가 필요하면 False."""
        self.layer = layer
        if self.resolve() is None:
            return False
        self.channels = ch.Channels(self.node, self.layer)
        self.lock_reason = self.channels.lock_reason()
        if self.PM is None or any(L not in self.W for L in self.channels.layers_used()) or                 self._frames() != self.times:
            self.dirty_bake = True
            return False
        self._evaluate()
        return True

    def refresh(self):
        """커브만 다시 평가 (굽기 없음). 범위 밖으로 키가 늘었거나 시간이 달라지면 False(다시 굽기 필요)."""
        if self.resolve() is None:
            return False
        self.channels = ch.Channels(self.node, self.layer)
        self.lock_reason = self.channels.lock_reason()
        self.c = np.array(parent_space.pivot_offset(self.node), dtype="float64")     # 피벗을 옮겼을 수도
        if self.dirty_bake or self.PM is None or self._frames() != self.times or                 any(L not in self.W for L in self.channels.layers_used()):
            return False
        self._evaluate()
        return True

    def _points(self):
        n = len(self.times)
        local = np.hstack([self.c + self.T, np.ones((n, 1))])
        self.points = np.einsum("ni,nij->nj", local, self.PM)[:, :3]

    def _keys(self):
        row_of = {round(t, TIME_ROUND): i for i, t in enumerate(self.times)}
        mask = self.channels.editable_mask()
        keys = []
        for t in self.channels.key_times():
            row = row_of.get(round(t, TIME_ROUND))
            if row is None:
                continue
            idx = self.channels.key_indices(t)
            partial = any(m and i < 0 for m, i in zip(mask, idx))
            keys.append(PathKey(t, row, partial))
        self.keys = keys

    # ---------------------------------------------------------------- 질의
    def key_points(self):
        if not self.keys:
            return np.zeros((0, 3))
        return self.points[[k.row for k in self.keys]]

    def row_of(self, t):
        rt = round(t, TIME_ROUND)
        for i, tt in enumerate(self.times):
            if round(tt, TIME_ROUND) == rt:
                return i
        return None

    def point_at(self, t):
        row = self.row_of(t)
        return None if row is None else self.points[row].copy()

    def solve(self, row, world):
        """월드 점 world 에 피벗이 오게 하는 **편집 레이어 값** (3,). 정확한 역산. 움직일 수 없는 축은 NaN."""
        local = np.append(np.asarray(world, dtype="float64"), 1.0) @ self.PMinv[row]
        wanted = local[:3] - self.c                                  # 필요한 최종 translate
        now = self.channels.layer_values([self.times[row]])[0]       # 편집 레이어의 지금 값
        beta = self.beta[row] if self.beta is not None else np.ones(3)
        out = np.full(3, np.nan)
        ok = np.abs(beta) >= BETA_EPS
        out[ok] = now[ok] + (wanted[ok] - self.T[row][ok]) / beta[ok]
        return out


def bake_many(caches, progress=None):
    """여러 경로를 한 번에 굽는다 (프레임 바깥 루프 - 같은 범위끼리 묶는다)."""
    groups = {}
    for c in caches:
        if c.resolve() is None:
            continue
        c._read_static()
        groups.setdefault(tuple(c.times), []).append(c)
    for times, members in groups.items():
        layers = []
        for c in members:
            for L in c.channels.layers_used():
                if L not in layers:
                    layers.append(L)
        pms, weights = parent_space.bake([c.node for c in members], list(times), progress=progress, layers=layers)
        for c in members:
            c._take_bake(pms[c.node], weights)
