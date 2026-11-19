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

solve(row, W) : 월드 점 W 에 피벗이 오게 하는 translate — T = W · PM⁻¹ − c  (정확한 역산)
"""

import numpy as np

import maya.cmds as cmds

from . import anim_channels as ch
from . import parent_space

TIME_ROUND = ch.KEY_ROUND


class PathKey(object):
    """경로 위 키 하나 (세 축 키 시간의 합집합 기준)."""

    __slots__ = ("t", "row", "partial")

    def __init__(self, t, row, partial):
        self.t = t
        self.row = row          # times 의 인덱스
        self.partial = partial  # 편집 가능한 축 중 키가 없는 축이 있다


class PathCache(object):

    def __init__(self, node, start, end):
        self.node = ch.long_name(node) or node
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
        baked = parent_space.bake([self.node], self.times, progress=progress)[self.node]
        self._take_bake(baked)
        return True

    def _read_static(self):
        self.channels = ch.Channels(self.node)
        self.lock_reason = self.channels.lock_reason()
        self.c = np.array(parent_space.pivot_offset(self.node), dtype="float64")
        self.times = self._frames()

    def _take_bake(self, pm):
        self.PM = pm
        self.PMinv = np.linalg.inv(self.PM)
        self.T = self.channels.values(self.times)
        self.dirty_bake = False
        self._points()
        self._keys()

    def refresh(self):
        """커브만 다시 평가 (굽기 없음). 범위 밖으로 키가 늘었거나 시간이 달라지면 False(다시 굽기 필요)."""
        if self.resolve() is None:
            return False
        self.channels = ch.Channels(self.node)
        self.lock_reason = self.channels.lock_reason()
        self.c = np.array(parent_space.pivot_offset(self.node), dtype="float64")     # 피벗을 옮겼을 수도
        if self.dirty_bake or self.PM is None or self._frames() != self.times:
            return False
        self.T = self.channels.values(self.times)
        self._points()
        self._keys()
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
        """월드 점 world 에 피벗이 오게 하는 translate (3,). 정확한 역산."""
        local = np.append(np.asarray(world, dtype="float64"), 1.0) @ self.PMinv[row]
        return local[:3] - self.c


def bake_many(caches, progress=None):
    """여러 경로를 한 번에 굽는다 (프레임 바깥 루프 - 같은 범위끼리 묶는다)."""
    groups = {}
    for c in caches:
        if c.resolve() is None:
            continue
        c._read_static()
        groups.setdefault(tuple(c.times), []).append(c)
    for times, members in groups.items():
        baked = parent_space.bake([c.node for c in members], list(times), progress=progress)
        for c in members:
            c._take_bake(baked[c.node])
