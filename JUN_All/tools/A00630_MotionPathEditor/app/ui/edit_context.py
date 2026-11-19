# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 편집 컨텍스트 (draggerContext, 계획서 §4-6) - GUI 전용
"""
Edit Path 를 켜면 이 컨텍스트가 마야 툴이 된다.

    클릭 키           : 그 키만 선택 (이미 선택된 키를 누르면 선택을 유지한 채 함께 끈다)
    Shift + 클릭      : 더하기 / 빼기 (toggle)
    Ctrl + 클릭       : 빼기
    빈 곳 드래그      : 박스 선택 (Shift = 더하기, Ctrl = 빼기) · 빈 곳 클릭 = 선택 해제
    선택 키 드래그    : 드래그 평면(View / Ground / X / Y / Z)에서 이동 → 놓으면 undo 한 번
    오른쪽 버튼       : 드래그 중이면 취소
    Alt + 드래그      : 마야 카메라 (컨텍스트로 오지 않는다)

화면 좌표는 space="screen" (M3dView 픽셀, 왼쪽 아래 원점) - picking 과 같다.
"""

import numpy as np

import maya.cmds as cmds

from tools.A00630_MotionPathEditor.app.core import draw_bridge
from tools.A00630_MotionPathEditor.app.core import picking
from tools.A00630_MotionPathEditor.app.core.edit_session import DragSession

CONTEXT_NAME = "junMotionPathEditCtx"
CLICK_PX = 3.0


class EditContext(object):

    def __init__(self, manager, watcher, log=None):
        self.manager = manager
        self.watcher = watcher
        self.log = log or (lambda text: None)
        self.session = None
        self.anchor = None
        self.view = None
        self.box = None
        self.previous_tool = None
        self.name = CONTEXT_NAME        # 마야가 실제로 붙인 컨텍스트 이름 (v01.02 - 이름으로 켜짐을 판단한다)

    # ---------------------------------------------------------------- 켜기 / 끄기
    def activate(self):
        kwargs = dict(pressCommand=self._press, dragCommand=self._drag, releaseCommand=self._release,
                      finalize=self._finalize, space="screen", cursor="crossHair", undoMode="sequence",
                      projection="viewPlane")
        if cmds.draggerContext(self.name, exists=True):
            cmds.draggerContext(self.name, edit=True, **kwargs)
        else:
            # 만들 때 마야가 돌려준 이름을 쓴다 - 같은 이름이 다른 종류로 있으면 마야가 다른 이름을 붙일 수 있다
            self.name = cmds.draggerContext(self.name, **kwargs) or self.name
        current = cmds.currentCtx()
        if current != self.name:
            self.previous_tool = current
        cmds.setToolTo(self.name)

    def deactivate(self):
        self._finalize()
        if cmds.currentCtx() == self.name:
            back = self.previous_tool if self.previous_tool and cmds.contextInfo(self.previous_tool, exists=True) \
                else "selectSuperContext"
            cmds.setToolTo(back)

    def is_active(self):
        return cmds.currentCtx() == self.name

    # ---------------------------------------------------------------- 입력
    def _query(self, flag):
        return cmds.draggerContext(self.name, query=True, **{flag: True})

    def _press(self):
        try:
            self.view = picking.ViewState()
            x, y = self._query("anchorPoint")[:2]
            button = self._query("button")
            modifier = self._query("modifier")
            if button == 3:
                if self.session is not None:
                    self._cancel()
                return
            picks = self.manager.pickable()
            hit = None
            if picks:
                pts = np.array([c.points[k.row] for c, k in picks])
                px, front = picking.project(pts, self.view.view_proj, self.view.width, self.view.height)
                hit = picking.nearest(px, front, x, y)
            if hit is None:
                self.box = (x, y, modifier)
                return
            cache, key = picks[hit]
            chosen = key.t in self.manager.selection.get(cache.key, set())
            if modifier == "shift":
                self.manager.select([(cache, key)], "toggle")
            elif modifier == "ctrl":
                self.manager.select([(cache, key)], "remove")
            elif not chosen:
                self.manager.select([(cache, key)], "replace")
            if key.t not in self.manager.selection.get(cache.key, set()):
                return                          # 방금 빼낸 키 - 끌지 않는다
            self.anchor = cache.points[key.row].copy()
            self.session = DragSession(self.manager.selected_items())
            if self.session.empty:
                self.session = None
                return
            self.watcher.busy = True
            self.session.begin()
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Press : {0}".format(exc))
            self._cancel()

    def _drag(self):
        try:
            x, y = self._query("dragPoint")[:2]
            if self.session is not None and self.anchor is not None:
                origin, direction = self.view.ray(x, y)
                target = picking.drag_target(self.manager.settings["plane"], origin, direction, self.anchor,
                                             self.view.view_dir)
                if target is None:
                    return
                self.session.update(target - self.anchor)
                self.manager.redraw()
            elif self.box is not None:
                x0, y0, _mod = self.box
                owner = self.manager.cache_list()[0].key if self.manager.cache_list() else ""
                draw_bridge.HUD.clear()
                draw_bridge.HUD.update({"box": (x0, y0, x, y), "owner": owner})
                self.manager.redraw()
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Drag : {0}".format(exc))
            self._cancel()

    def _release(self):
        try:
            if self.session is not None:
                session, self.session = self.session, None
                moved = session.commit()
                self.watcher.busy = False
                self.manager.refresh_all()
                if moved:
                    n = sum(len(ts) for _c, ts in session.items)
                    self.log("[OK] Moved {0} key(s). Ctrl+Z undoes it in one step.".format(n))
                return
            if self.box is not None:
                x0, y0, modifier = self.box
                self.box = None
                draw_bridge.HUD.clear()
                x, y = self._query("dragPoint")[:2]
                picks = self.manager.pickable()
                if abs(x - x0) < CLICK_PX and abs(y - y0) < CLICK_PX:
                    if modifier not in ("shift", "ctrl"):
                        self.manager.select([], "replace")      # 빈 곳 클릭 = 해제
                    else:
                        self.manager.redraw()
                    return
                inside = []
                if picks:
                    pts = np.array([c.points[k.row] for c, k in picks])
                    px, front = picking.project(pts, self.view.view_proj, self.view.width, self.view.height)
                    inside = [picks[i] for i in picking.inside_box(px, front, x0, y0, x, y)]
                mode = {"shift": "add", "ctrl": "remove"}.get(modifier, "replace")
                self.manager.select(inside, mode)
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Release : {0}".format(exc))
            self._cancel()

    def _cancel(self):
        if self.session is not None:
            session, self.session = self.session, None
            try:
                session.cancel()
            finally:
                self.watcher.busy = False
            self.log("[Info] Drag cancelled.")
        self.box = None
        draw_bridge.HUD.clear()
        self.manager.redraw()

    def _finalize(self):
        """컨텍스트에서 나갈 때 (다른 툴 · Q). 끄는 중인 드래그는 취소."""
        if self.session is not None or self.box is not None:
            self._cancel()
