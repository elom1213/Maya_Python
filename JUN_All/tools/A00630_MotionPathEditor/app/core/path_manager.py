# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 경로들 · 키 선택 · 그리기 (툴 창 · 편집 컨텍스트 · 감시가 함께 쓴다)
"""
PathManager 하나가 툴의 상태를 다 가진다:
    caches     : {경로 키(UUID): PathCache}
    nodes      : {경로 키: 그리기 노드 트랜스폼}
    selection  : {경로 키: {시간}} - 키 시간 또는 프레임 점 시간 (v01.09 - 프레임 점도 고른다)
    settings   : 범위 · 표시 · 드래그 평면
    preview    : {경로 키: (N,3)} 그래프 Smooth 를 칠하는 동안 보여 줄 새 점 (원래 선은 회색으로 함께) - v01.04
    listeners  : redraw 끝에 부르는 함수들 (속도 그래프가 따라 그린다) - v01.04

씬을 바꾸는 것은 키 값뿐이고(편집 세션), 그리기 노드는 undo 큐 밖에서 만든다(draw_nodes).
"""

import numpy as np

import maya.cmds as cmds

from . import anim_channels as ch
from . import draw_bridge
from . import draw_nodes
from . import falloff
from . import gizmo
from . import path_cache as pc

RANGE_PLAYBACK = "playback"
RANGE_SCENE = "scene"
RANGE_CUSTOM = "custom"

DEFAULT_SETTINGS = {
    "range": RANGE_PLAYBACK,
    "custom_start": 1,
    "custom_end": 120,
    "show_dots": True,
    "show_keys": True,
    "show_numbers": False,
    "line_width": 2.0,
    "dot_size": 4.0,
    "key_size": 9.0,
    "plane": "view",
    "edit_layer": "",              # v01.03 편집할 애니메이션 레이어 ("" = Base)
    # v01.04 속도 그래프 (Speed 탭)
    "graph_mode": "speed",         # speed / position / accel
    "graph_range": "path",         # path / selected / around / custom (v01.06)
    "graph_start": 1,              # v01.06 그래프 Custom 범위 (프레임)
    "graph_end": 120,
    "graph_per_second": False,
    "brush_mode": "speed",         # speed (타이밍만) / shape (모양)
    "brush_radius": 8.0,           # 프레임
    "brush_strength": 0.5,
    "whole_pose": False,           # 속도 획이 rotate · scale 도 같은 시간 왜곡으로 (원본: 끔)
    "fit_tolerance": 0.1,          # % (경로 크기 대비) - refit 허용 오차
    # v01.09 폴오프 (매니퓰레이터 · 폴오프 계획서 §3-2)
    "falloff_on": False,
    "falloff_radius": 8.0,         # 프레임 (경로를 따라 잰 거리)
    "falloff_curve": "",           # json (falloff.curve_to_text), "" = Smooth 프리셋
    # v01.11 매니퓰레이터 (계획서 §3-4)
    "manip_mode": "move",          # move / rotate
    "manip_axes": "world",         # world / path (고른 점 자리의 접선 · 위 · 옆)
}


class PathManager(object):

    def __init__(self, log=None):
        self.caches = {}
        self.nodes = {}
        self.order = []
        self.selection = {}
        self.settings = dict(DEFAULT_SETTINGS)
        self.log = log or (lambda text: None)
        self.view_refresh = None        # GUI 에서 뷰를 다시 그리는 함수 (헤드리스는 None)
        self.saving = False
        self.preview = {}
        self.listeners = []
        self._lut_key = None
        self._lut = None
        self.gizmo_on = False           # v01.11 편집 컨텍스트가 켜져 있으면 고른 점에 매니퓰레이터를 그린다
        self.gizmo_active = None        # 끄는 중인 부분 (노랑)
        self.gizmo_pivot = None         # 끄는 중 피벗 (이동하면 따라간다) - None 이면 고른 점의 무게중심
        self.gizmo_axes = None          # 끄는 중 축 고정 (Path 축이 끄는 동안 돌지 않게)

    # ---------------------------------------------------------------- 범위
    def frame_range(self):
        mode = self.settings["range"]
        if mode == RANGE_SCENE:
            return int(cmds.playbackOptions(q=True, animationStartTime=True)), \
                int(cmds.playbackOptions(q=True, animationEndTime=True))
        if mode == RANGE_CUSTOM:
            s, e = int(self.settings["custom_start"]), int(self.settings["custom_end"])
            return min(s, e), max(s, e)
        return int(cmds.playbackOptions(q=True, minTime=True)), int(cmds.playbackOptions(q=True, maxTime=True))

    # ---------------------------------------------------------------- 대상
    def cache_list(self):
        return [self.caches[k] for k in self.order if k in self.caches]

    def set_targets(self, nodes, progress=None):
        """대상 목록을 nodes 로 맞춘다 (새로 들어온 것만 굽는다). 굽힌 수를 돌려준다."""
        start, end = self.frame_range()
        wanted = []
        for node in nodes:
            uuid = (cmds.ls(node, uuid=True) or [""])[0]
            if not uuid or cmds.objectType(node) not in ("transform", "joint") and \
                    not cmds.objectType(node, isAType="transform"):
                self.log("[SKIP] {0} : not a transform or joint.".format(node))
                continue
            if uuid not in wanted:
                wanted.append(uuid)
        for key in list(self.caches):
            if key not in wanted:
                self._remove(key)
        fresh = []
        for uuid in wanted:
            if uuid not in self.caches:
                node = (cmds.ls(uuid, long=True) or [None])[0]
                cache = pc.PathCache(node, start, end, layer=self.edit_layer())
                self.caches[uuid] = cache
                fresh.append(cache)
        self.order = wanted
        if fresh:
            pc.bake_many(fresh, progress=progress)
            for c in fresh:
                if c.locked:
                    self.log("[Info] {0} : {1}.".format(c.label, c.lock_reason))
        self.redraw()
        return len(fresh)

    def _remove(self, key):
        self.preview.pop(key, None)
        draw_nodes.delete_node(self.nodes.pop(key, None))
        draw_bridge.drop(key)
        self.caches.pop(key, None)
        self.selection.pop(key, None)

    def clear(self):
        self.preview = {}
        for key in list(self.caches):
            self._remove(key)
        self.order = []
        draw_bridge.GIZMO.clear()
        draw_nodes.delete_all()

    # ---------------------------------------------------------------- 애니메이션 레이어 (v01.03)
    def edit_layer(self):
        """편집할 레이어 이름. 비었거나 씬에 없으면 Base."""
        name = self.settings.get("edit_layer") or ""
        if not name or ch.is_base(name) or not cmds.objExists(name):
            return ch.root_layer()
        return name

    def set_edit_layer(self, layer, progress=None):
        """편집 레이어를 바꾼다 - 경로(합친 움직임)는 그대로, 키 점 · 잠금 · 끌 때 쓰는 커브만 바뀐다. 키 선택은 비운다."""
        self.settings["edit_layer"] = "" if ch.is_base(layer) else layer
        need = []
        for c in self.cache_list():
            if not c.set_layer(self.edit_layer()):
                need.append(c)
        if need:
            pc.bake_many(need, progress=progress)
        self.selection = {}
        for c in self.cache_list():
            if c.locked:
                self.log("[Info] {0} : {1}.".format(c.label, c.lock_reason))
        self.redraw()

    # ---------------------------------------------------------------- 갱신
    def rebake_all(self, progress=None):
        """범위를 다시 읽고 전부 다시 굽는다 (부모 애니메이션이 바뀌었을 때 - Refresh)."""
        start, end = self.frame_range()
        caches = self.cache_list()
        for c in caches:
            c.start, c.end = start, end
            c.layer = self.edit_layer()
            c.dirty_bake = True
        pc.bake_many(caches, progress=progress)
        self._prune_selection()
        self.redraw()

    def refresh_all(self):
        """커브만 다시 읽는다 (그래프 에디터 편집 · undo 뒤). 다시 굽기가 필요한 경로는 굽는다."""
        need = []
        for c in self.cache_list():
            if c.resolve() is None:
                continue
            if not c.refresh():
                need.append(c)
        if need:
            pc.bake_many(need)
        self._prune_selection()
        self.redraw()

    def _prune_selection(self):
        for key, times in list(self.selection.items()):
            cache = self.caches.get(key)
            if cache is None:
                self.selection.pop(key)
                continue
            have = {round(t, 3) for t in cache.times}          # v01.09 - 키든 프레임 점이든 경로 위에 있으면 남긴다
            self.selection[key] = {t for t in times if round(t, 3) in have}

    # ---------------------------------------------------------------- 그리기
    def redraw(self):
        if self.saving:
            return
        frame = cmds.currentTime(q=True)
        s = self.settings
        for i, cache in enumerate(self.cache_list()):
            if cache.points is None:
                continue
            if cache.key not in self.nodes or not cmds.objExists(self.nodes[cache.key]):
                self.nodes[cache.key] = draw_nodes.create_node(cache.key, cache.label)[0]
            color = draw_nodes.PALETTE[i % len(draw_nodes.PALETTE)]
            preview = self.preview.get(cache.key)
            draw_bridge.put(cache.key, draw_nodes.payload(
                cache, color, self.selection.get(cache.key, ()), frame, show_dots=s["show_dots"],
                show_keys=s["show_keys"], show_numbers=s["show_numbers"], line_width=s["line_width"],
                dot_size=s["dot_size"], key_size=s["key_size"], points=preview,
                ghost=cache.points if preview is not None else None, weights=self.weights_for(cache)))
        self._update_gizmo()
        if self.view_refresh is not None:
            self.view_refresh()
        for fn in list(self.listeners):
            try:
                fn()
            except Exception:                              # noqa: BLE001 - 그래프가 실패해도 뷰는 그린다
                pass

    def hide_for_save(self):
        """저장 직전: 그리기 노드를 지운다 - 노드가 있으면 파일에 `requires` 플러그인 줄이 써진다."""
        self.saving = True
        for key in list(self.nodes):
            draw_nodes.delete_node(self.nodes.pop(key))

    def show_after_save(self):
        self.saving = False
        self.redraw()

    # ---------------------------------------------------------------- 선택
    def pickable(self):
        """[(cache, key)] - 그려진 키 전부 (잠긴 경로 제외)."""
        out = []
        for c in self.cache_list():
            if c.locked or c.points is None:
                continue
            for k in c.keys:
                out.append((c, k))
        return out

    def pickable_frames(self):
        """[(cache, PathKey(partial=None))] - 키가 아닌 프레임 점 (v01.09). Frame dots 를 끄면 고르지 않는다(안 보이는 것)."""
        out = []
        if not self.settings["show_dots"]:
            return out
        for c in self.cache_list():
            if c.locked or c.points is None:
                continue
            keyed = {k.row for k in c.keys}
            for row, t in enumerate(c.times):
                if row not in keyed:
                    out.append((c, pc.PathKey(t, row, None)))
        return out

    def select(self, picks, mode="replace"):
        """picks : [(cache, key)]. mode = replace / add / toggle / remove."""
        if mode == "replace":
            self.selection = {}
        for cache, key in picks:
            cur = self.selection.setdefault(cache.key, set())
            t = key.t
            if mode == "remove" or (mode == "toggle" and t in cur):
                cur.discard(t)
            else:
                cur.add(t)
        self.redraw()

    def selected_items(self):
        """[(cache, [키 시간])] - 편집 세션에 넘길 것."""
        out = []
        for c in self.cache_list():
            times = self.selection.get(c.key)
            if times:
                out.append((c, sorted(times)))
        return out

    def selected_count(self):
        return sum(len(v) for v in self.selection.values())

    def selection_has_frames(self):
        """고른 것 중 키가 아닌 프레임 점이 있나."""
        for c in self.cache_list():
            times = self.selection.get(c.key)
            if times:
                keyed = {round(k.t, 3) for k in c.keys}
                if any(round(t, 3) not in keyed for t in times):
                    return True
        return False

    # ---------------------------------------------------------------- 매니퓰레이터 (v01.11)
    def gizmo_frame(self):
        """(피벗 (3,), 축 (3,3)) - 고른 점들의 무게중심 · World 또는 Path 축. 고른 것이 없으면 None.
        미리보기 중이면 미리보기 점으로 (끄는 동안 기즈모가 점을 따라간다)."""
        pts, first = [], None
        for c in self.cache_list():
            times = self.selection.get(c.key)
            if not times or c.points is None or c.locked:
                continue
            P = self.preview.get(c.key)
            P = c.points if P is None else P
            rows = [r for r in (c.row_of(t) for t in sorted(times)) if r is not None]
            if not rows:
                continue
            pts.append(P[rows])
            if first is None:
                first = (P, rows[len(rows) // 2])
        if not pts:
            return None
        pivot = np.vstack(pts).mean(axis=0)
        if self.settings.get("manip_axes") == gizmo.AXES_PATH and first is not None:
            axes = gizmo.path_frame(first[0], first[1])
        else:
            axes = np.eye(3)
        return pivot, axes

    def _update_gizmo(self):
        draw_bridge.GIZMO.clear()
        if not self.gizmo_on:
            return
        frame = self.gizmo_frame()
        caches = self.cache_list()
        if frame is None or not caches:
            return
        pivot, axes = frame
        if self.gizmo_pivot is not None:
            pivot = self.gizmo_pivot
        if self.gizmo_axes is not None:
            axes = self.gizmo_axes
        draw_bridge.GIZMO.update({"owner": caches[0].key, "pivot": np.asarray(pivot, dtype="float64"),
                                  "axes": np.asarray(axes, dtype="float64"),
                                  "mode": self.settings.get("manip_mode", gizmo.MODE_MOVE), "active": self.gizmo_active})

    # ---------------------------------------------------------------- 폴오프 (v01.09)
    def falloff_radius(self):
        """지금 쓰는 반경 (프레임). 꺼져 있으면 0."""
        return float(self.settings["falloff_radius"]) if self.settings["falloff_on"] else 0.0

    def falloff_table(self):
        text = self.settings.get("falloff_curve") or ""
        if self._lut is None or self._lut_key != text:
            self._lut = falloff.lut(falloff.curve_from_text(text))
            self._lut_key = text
        return self._lut

    def weights_for(self, cache):
        """(N,) 그 경로의 폴오프 가중치 - 고른 것이 없거나 폴오프가 꺼져 있으면 None."""
        times = self.selection.get(cache.key)
        if not times or cache.points is None or self.falloff_radius() <= 0:
            return None
        return falloff.weights(cache.times, times, self.falloff_radius(), self.falloff_table())

    def falloff_spans(self):
        """[(cache, [(a, b)])] - 폴오프 범위 (폴오프가 꺼져 있으면 고른 점 자체의 구간)."""
        out = []
        for c in self.cache_list():
            times = self.selection.get(c.key)
            if not times or c.points is None:
                continue
            w = falloff.weights(c.times, times, self.falloff_radius(), self.falloff_table())
            out.append((c, falloff.spans(c.times, w)))
        return out
