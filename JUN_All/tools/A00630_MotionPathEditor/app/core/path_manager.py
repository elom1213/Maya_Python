# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 경로들 · 키 선택 · 그리기 (툴 창 · 편집 컨텍스트 · 감시가 함께 쓴다)
"""
PathManager 하나가 툴의 상태를 다 가진다:
    caches     : {경로 키(UUID): PathCache}
    nodes      : {경로 키: 그리기 노드 트랜스폼}
    selection  : {경로 키: {키 시간}}
    settings   : 범위 · 표시 · 드래그 평면

씬을 바꾸는 것은 키 값뿐이고(편집 세션), 그리기 노드는 undo 큐 밖에서 만든다(draw_nodes).
"""

import maya.cmds as cmds

from . import draw_bridge
from . import draw_nodes
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
                cache = pc.PathCache(node, start, end)
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
        draw_nodes.delete_node(self.nodes.pop(key, None))
        draw_bridge.drop(key)
        self.caches.pop(key, None)
        self.selection.pop(key, None)

    def clear(self):
        for key in list(self.caches):
            self._remove(key)
        self.order = []
        draw_nodes.delete_all()

    # ---------------------------------------------------------------- 갱신
    def rebake_all(self, progress=None):
        """범위를 다시 읽고 전부 다시 굽는다 (부모 애니메이션이 바뀌었을 때 - Refresh)."""
        start, end = self.frame_range()
        caches = self.cache_list()
        for c in caches:
            c.start, c.end = start, end
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
            have = {round(k.t, 3) for k in cache.keys}
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
            draw_bridge.put(cache.key, draw_nodes.payload(
                cache, color, self.selection.get(cache.key, ()), frame, show_dots=s["show_dots"],
                show_keys=s["show_keys"], show_numbers=s["show_numbers"], line_width=s["line_width"],
                dot_size=s["dot_size"], key_size=s["key_size"]))
        if self.view_refresh is not None:
            self.view_refresh()

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
