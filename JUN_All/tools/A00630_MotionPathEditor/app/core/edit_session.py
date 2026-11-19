# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 드래그 한 번 (계획서 §4-6 · §4-7)
"""
DragSession : 누름 → 움직임(여러 번) → 놓기 / 취소.

- 누를 때 선택 키들의 **원래 월드 점**을 기억한다. 움직일 때마다 원래 점 + 이동량으로 처음부터 다시 계산한다(오차 누적 없음).
- **처음 실제로 움직일 때 한 번** 채널 키를 맞춘다(`ensure_keys` - 부분 키 채우기 · 키 없는 축에 커브 만들기). 시작만 하고 놓으면 아무것도 안 바뀐다.
- 키 값은 `MFnAnimCurve.setValue(..., change)` 로 바꾸고 변경을 MAnimCurveChange 하나에 쌓는다 - 드래그 동안은 undo 큐에 들어가지 않는다.
- 놓을 때: `junMotionPathSetKeys` 명령이 그 기록을 undo 큐에 한 번 넣는다. ensure_keys 의 cmds 도 같은 undo 묶음(누를 때 연다) 안이라
  **Ctrl+Z 한 번**에 전부 되돌아간다.
- 취소: 쌓인 변경을 되돌리고(`change.undoIt()`), ensure_keys 가 키를 넣었으면 그 묶음도 undo 한다.

잠긴 축(lock · 편집 불가)은 원래 값을 그대로 둔다. 잠긴 경로(lock_reason)는 처음부터 세션에 넣지 않는다.
애니메이션 레이어 (v01.03): 키 값은 **편집 레이어의 커브**에만 쓴다(path_cache.solve 가 그 레이어 값을 돌려준다).
"""

import numpy as np

import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

from . import draw_bridge

COMMAND = "junMotionPathSetKeys"
DIRTY_COMMAND = "junMotionPathDirty"


class DragSession(object):

    def __init__(self, selection):
        """selection : [(PathCache, [키 시간, ...])] - 잠긴 경로 · 키 없는 경로는 빠진다."""
        self.items = [(c, sorted(ts)) for c, ts in selection if ts and not c.locked]
        self.start = {}                 # (cache.key, t) -> 원래 월드 점
        for cache, times in self.items:
            for t in times:
                p = cache.point_at(t)
                if p is not None:
                    self.start[(cache.key, t)] = p
        self.change = None
        self.moved = False
        self.inserted = False
        self.chunk_open = False
        self.finished = False

    @property
    def empty(self):
        return not self.start

    # ---------------------------------------------------------------- 수명
    def begin(self):
        """누를 때. undo 묶음을 연다(ensure_keys 의 cmds 와 놓을 때의 명령을 한 번으로)."""
        if self.empty:
            return
        cmds.undoInfo(openChunk=True, chunkName="MotionPathEdit")
        self.chunk_open = True

    def _dirty_nodes(self):
        out = []
        for cache, _times in self.items:
            for n in cache.channels.dirty_nodes():
                if n not in out:
                    out.append(n)
        return out

    def _prepare(self):
        """처음 실제로 움직일 때 한 번: 표시 명령 → 채널 키 맞추기 → 경로 다시 읽기.

        v01.03 - 표시 명령(junMotionPathDirty)을 묶음의 **맨 앞**에 넣는다: undo 때 가장 마지막에 되돌려지며
        대상 · 블렌드 노드를 다시 계산하게 한다(레이어에 새로 만든 커브가 undo 로 지워진 뒤 마야가 낡은 위치를 남겼다).
        """
        draw_bridge.stage_dirty(self._dirty_nodes())
        getattr(cmds, DIRTY_COMMAND)()
        for cache, times in self.items:
            if cache.channels.ensure_keys(times):
                self.inserted = True
                cache.refresh()
        self.change = oma.MAnimCurveChange()
        self.moved = True

    def update(self, delta):
        """선택 키 전부를 원래 점 + delta 로 (월드, (3,))."""
        if self.empty or self.finished:
            return
        delta = np.asarray(delta, dtype="float64")
        if not self.moved:
            if not np.any(np.abs(delta) > 1e-9):
                return
            self._prepare()
        for cache, times in self.items:
            mask = cache.channels.editable_mask()
            for t in times:
                p0 = self.start.get((cache.key, t))
                row = cache.row_of(t)
                if p0 is None or row is None:
                    continue
                T = cache.solve(row, p0 + delta)
                for axis, editable, value in zip(cache.channels.axes, mask, T):
                    # NaN = 그 축은 편집 레이어가 움직일 수 없다(β = 0 : 뮤트 · 가중치 0 · 위 override) - v01.03
                    if not editable or axis.fn is None or not np.isfinite(value):
                        continue
                    idx = axis.key_index(t)
                    if idx >= 0:
                        axis.fn.setValue(idx, float(value), self.change)
            cache.refresh()

    def commit(self):
        """놓을 때. 움직였으면 True."""
        if self.finished:
            return False
        self.finished = True
        try:
            if self.moved and self.change is not None:
                draw_bridge.stage(self.change, self._dirty_nodes())
                getattr(cmds, COMMAND)()
                return True
            return False
        finally:
            self._close_chunk()

    def cancel(self):
        """취소: 값을 되돌리고, 넣은 키도 되돌린다."""
        if self.finished:
            return
        self.finished = True
        if self.change is not None:
            self.change.undoIt()
        self._close_chunk()
        if self.moved:
            cmds.undo()             # 방금 닫은 묶음 = 표시 명령 + ensure_keys 로 넣은 키들 (값은 위에서 되돌렸다)
        for cache, _times in self.items:
            cache.refresh()

    def _close_chunk(self):
        if self.chunk_open:
            cmds.undoInfo(closeChunk=True)
            self.chunk_open = False

