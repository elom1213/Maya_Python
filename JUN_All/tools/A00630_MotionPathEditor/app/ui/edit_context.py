# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 편집 컨텍스트 (draggerContext, 계획서 §4-6) - GUI 전용
"""
Edit Path 를 켜면 이 컨텍스트가 마야 툴이 된다.

    클릭 키 · 프레임 점 : 그 점만 선택 (이미 선택된 점을 누르면 선택을 유지한 채 함께 끈다)
                          같은 자리면 키가 먼저 (v01.09 - 프레임 점도 고른다, Frame dots 가 켜져 있을 때)
    Shift + 클릭      : 더하기 / 빼기 (toggle)
    Ctrl + 클릭       : 빼기
    빈 곳 드래그      : 박스 선택 (Shift = 더하기, Ctrl = 빼기) · 빈 곳 클릭 = 선택 해제
    선택 키 드래그    : 드래그 평면(View / Ground / X / Y / Z)에서 이동 → 놓으면 undo 한 번
                        프레임 점을 골랐거나 폴오프가 켜져 있으면 deform (v01.10): 고른 점 = 1, 둘레는 가중치만큼 함께.
                        끄는 동안은 미리보기(원래 경로 회색 점선 + 새 경로), 놓을 때 키에 쓴다(refit) - 경로 여럿이어도 undo 한 번
    b 톡              : 폴오프 켜기 / 끄기 (v01.09)
    b + 왼쪽 끌기     : 폴오프 반경 (좌우, v01.09) · Ctrl+Shift + 왼쪽 끌기 = 같은 일 (b 를 못 받을 때의 안전망)
    매니퓰레이터 (v01.11): 고른 점이 있으면 그 무게중심에 그린다. 화살표 · 평면 · 가운데 / 고리를 끌면 이동 / 회전
                        (고른 점 = 1, 폴오프 범위는 가중치만큼 - 회전은 각도가 가중치배). 점보다 먼저 잡힌다(Shift / Ctrl 클릭은 늘 점).
    w / e             : 매니퓰레이터 Move / Rotate (이 툴이 켜져 있을 때만 - 마야 툴 전환 핫키로 안 간다)
    호버 (v01.14)     : 버튼 없이 마우스가 기즈모 부분 위에 오면 그 부분이 굵어진다. draggerContext 는 버튼 없는 움직임을
                        알려 주지 않으므로 같은 앱 이벤트 필터가 MouseMove 를 보고(먹지 않는다) 활성 3D 뷰 픽셀로 바꿔 hover() 를 부른다.
    오른쪽 버튼       : 드래그 중이면 취소
    Alt + 드래그      : 마야 카메라 (컨텍스트로 오지 않는다)

화면 좌표는 space="screen" (M3dView 픽셀, 왼쪽 아래 원점) - picking 과 같다.

b 키 (v01.09, 매니퓰레이터 · 폴오프 계획서 §3-5 · G0-2 실측): draggerContext 는 키를 알려 주지 않고, b 는 마야 핫키
(artisanModifyUpperRadius - 소프트 셀렉션 반경)로 먼저 간다. 그래서 컨텍스트가 켜져 있는 동안 **앱 이벤트 필터**가
B 의 ShortcutOverride · KeyPress · KeyRelease 를 먹어 핫키로 안 보내고, 누름 상태를 기억한다(이 컨텍스트가 지금 툴일 때만).
"""

import numpy as np

import maya.cmds as cmds

from tools.A00630_MotionPathEditor.app.core import draw_bridge
from tools.A00630_MotionPathEditor.app.core import falloff
from tools.A00630_MotionPathEditor.app.core import gizmo as gz
from tools.A00630_MotionPathEditor.app.core import picking
from tools.A00630_MotionPathEditor.app.core import speed_session as ss
from tools.A00630_MotionPathEditor.app.core.edit_session import DragSession

CONTEXT_NAME = "junMotionPathEditCtx"
CLICK_PX = 3.0
RADIUS_PER_PX = 0.1          # 폴오프 반경: 가로 1 px = 0.1 프레임
RADIUS_MAX = 2000.0


class EditContext(object):

    def __init__(self, manager, watcher, log=None, on_setting=None):
        self.manager = manager
        self.watcher = watcher
        self.log = log or (lambda text: None)
        self.on_setting = on_setting or (lambda key: None)     # 설정을 바꿨다 (창이 저장 · 칸을 맞춘다) - v01.09
        self.session = None
        self.deform = None              # v01.10 [(cache, StrokeSession, 가중치)] - 프레임 점 · 폴오프 끌기
        self.deform_moved = False
        self.anchor = None
        self.anchor_point = None
        self.view = None
        self.box = None
        self.radius_drag = None         # (x0, 처음 반경) - b / Ctrl+Shift 끌기 중 (v01.09)
        self.gizmo_drag = None          # v01.11 {"part", "pivot", "axes", "vdir", "start", "ray0", "px0", "angle"}
        self.previous_tool = None
        self.name = CONTEXT_NAME        # 마야가 실제로 붙인 컨텍스트 이름 (v01.02 - 이름으로 켜짐을 판단한다)
        self.b_held = False             # v01.09 B 를 누르고 있다 (키 필터가 바꾼다)
        self.b_used = False             # B 를 누른 동안 마우스를 썼다 - 그러면 떼도 켜기/끄기 안 한다
        self.key_filter = None

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
        self._install_key_filter()
        cmds.setToolTo(self.name)
        self.manager.gizmo_on = True
        self.manager.redraw()

    def deactivate(self):
        self._finalize()
        self._remove_key_filter()
        self.manager.gizmo_on = False
        self.manager.gizmo_hover = None
        self.manager.redraw()
        if cmds.currentCtx() == self.name:
            back = self.previous_tool if self.previous_tool and cmds.contextInfo(self.previous_tool, exists=True) \
                else "selectSuperContext"
            cmds.setToolTo(back)

    def is_active(self):
        return cmds.currentCtx() == self.name

    # ---------------------------------------------------------------- b 키 (v01.09)
    def _install_key_filter(self):
        if self.key_filter is not None:
            return
        try:
            from Framework.qt.qt import QApplication
        except Exception:                                  # noqa: BLE001 - Qt 없는 환경
            return
        app = QApplication.instance()
        if app is None:
            return
        self.key_filter = _make_key_filter(self)
        app.installEventFilter(self.key_filter)

    def _remove_key_filter(self):
        if self.key_filter is None:
            return
        try:
            from Framework.qt.qt import QApplication
            app = QApplication.instance()
            if app is not None:
                app.removeEventFilter(self.key_filter)
        except Exception:                                  # noqa: BLE001
            pass
        self.key_filter = None
        self.b_held = False

    def b_pressed(self):
        self.b_held = True
        self.b_used = False

    def b_released(self):
        """B 를 뗐다. 그동안 마우스를 안 썼으면 = 톡 → 폴오프 켜기 / 끄기."""
        self.b_held = False
        if self.b_used:
            return
        s = self.manager.settings
        s["falloff_on"] = not s["falloff_on"]
        self.on_setting("falloff_on")
        self.manager.redraw()
        self.log("[Info] Falloff {0}{1}.".format(
            "on" if s["falloff_on"] else "off",
            " - radius {0:g} frame(s)".format(s["falloff_radius"]) if s["falloff_on"] else ""))

    def set_manip_mode(self, mode):
        """w / e (v01.11) - 매니퓰레이터 Move / Rotate."""
        if self.manager.settings.get("manip_mode") == mode:
            return
        self.manager.settings["manip_mode"] = mode
        self.on_setting("manip_mode")
        self.manager.redraw()

    def hover(self, x, y):
        """v01.14 - 화면 (x, y)(M3dView 픽셀, 왼쪽 아래 원점)에 있는 기즈모 부분을 굵게. 바뀔 때만 다시 그린다. 바뀌었으면 True."""
        part = None
        busy = self.gizmo_drag is not None or self.session is not None or self.deform is not None or \
            self.box is not None or self.radius_drag is not None
        if not busy and self.manager.gizmo_on:
            frame = self.manager.gizmo_frame()
            if frame is not None:
                v = picking.ViewState()
                part = gz.hit(frame[0], frame[1], self.manager.settings.get("manip_mode", gz.MODE_MOVE),
                              v.view_proj, v.width, v.height, x, y)
        if part == self.manager.gizmo_hover:
            return False
        self.manager.gizmo_hover = part
        self.manager.redraw()
        return True

    def hover_at_cursor(self):
        """마우스 커서 → 활성 3D 뷰 픽셀 → hover (GUI 전용). 뷰 밖이면 호버 없음."""
        try:
            import maya.api.OpenMayaUI as omui
            from Framework.qt.qt import QCursor, QWidget
            try:
                from shiboken2 import wrapInstance
            except ImportError:                            # pragma: no cover
                from shiboken6 import wrapInstance
            pos = QCursor.pos()
            here = (pos.x(), pos.y())
            if here == getattr(self, "_last_cursor", None):   # 한 움직임이 위젯마다 여러 번 온다 - 같은 자리는 한 번만
                return False
            self._last_cursor = here
            view = omui.M3dView.active3dView()
            widget = wrapInstance(int(view.widget()), QWidget)
            local = widget.mapFromGlobal(pos)
            if not widget.rect().contains(local):
                return self.hover(-1e6, -1e6)
            sx = view.portWidth() / float(max(widget.width(), 1))       # 고해상도 배율 (위젯 px → 뷰포트 px)
            sy = view.portHeight() / float(max(widget.height(), 1))
            return self.hover(local.x() * sx, (widget.height() - local.y()) * sy)
        except Exception:                                  # noqa: BLE001 - 호버는 보조 기능, 실패해도 조용히
            return False

    def _ctrl_shift(self):
        """Ctrl 과 Shift 를 함께 누르고 있나 (반경 끌기 안전망). draggerContext 의 modifier 는 하나만 알려 준다."""
        try:
            from Framework.qt.qt import QApplication, Qt
            mods = QApplication.queryKeyboardModifiers()
            return bool(mods & Qt.ControlModifier) and bool(mods & Qt.ShiftModifier)
        except Exception:                                  # noqa: BLE001
            return False

    # ---------------------------------------------------------------- 입력
    def _query(self, flag):
        return cmds.draggerContext(self.name, query=True, **{flag: True})

    def _hit(self, picks, x, y):
        if not picks:
            return None
        pts = np.array([c.points[k.row] for c, k in picks])
        px, front = picking.project(pts, self.view.view_proj, self.view.width, self.view.height)
        return picking.nearest(px, front, x, y)

    def _press(self):
        try:
            self.view = picking.ViewState()
            x, y = self._query("anchorPoint")[:2]
            button = self._query("button")
            modifier = self._query("modifier")
            if button == 3:
                if self.session is not None or self.deform is not None or self.gizmo_drag is not None:
                    self._cancel()
                return
            if button == 1 and (self.b_held or self._ctrl_shift()):
                self.b_used = True
                self.radius_drag = (x, float(self.manager.settings["falloff_radius"]))
                if not self.manager.settings["falloff_on"]:
                    self.manager.settings["falloff_on"] = True      # 반경을 만지면 켠다
                    self.on_setting("falloff_on")
                self._show_radius(x, y)
                return
            # v01.11 매니퓰레이터가 점보다 먼저 (Shift / Ctrl 클릭은 늘 점 선택)
            if button == 1 and modifier not in ("shift", "ctrl") and self._press_gizmo(x, y):
                return
            # 키가 먼저, 없으면 프레임 점 (v01.09)
            keys = self.manager.pickable()
            hit = self._hit(keys, x, y)
            picks = keys
            if hit is None:
                picks = self.manager.pickable_frames()
                hit = self._hit(picks, x, y)
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
                return                          # 방금 빼낸 점 - 끌지 않는다
            if self.manager.selection_has_frames() or self.manager.falloff_radius() > 0:
                self._start_deform(cache.points[key.row], x, y)
                return
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
            if self.gizmo_drag is not None:
                self._drag_gizmo(x, y)
            elif self.radius_drag is not None:
                x0, r0 = self.radius_drag
                r = min(RADIUS_MAX, max(0.0, r0 + (x - x0) * RADIUS_PER_PX))
                self.manager.settings["falloff_radius"] = round(r, 1)
                self._show_radius(x, y)
                self.manager.redraw()
            elif self.deform is not None and self.anchor is not None:
                origin, direction = self.view.ray(x, y)
                target = picking.drag_target(self.manager.settings["plane"], origin, direction, self.anchor_point,
                                             self.view.view_dir)
                if target is None:
                    return
                delta = target - self.anchor
                if np.any(np.abs(delta) > 1e-9):
                    self.deform_moved = True
                for cache, session, w in self.deform:
                    P = session.stack[-1] + w[:, None] * delta
                    session.set_state(P)
                    self.manager.preview[cache.key] = P
                self.manager.redraw()
            elif self.session is not None and self.anchor is not None:
                origin, direction = self.view.ray(x, y)
                target = picking.drag_target(self.manager.settings["plane"], origin, direction, self.anchor,
                                             self.view.view_dir)
                if target is None:
                    return
                self.session.update(target - self.anchor)
                self.manager.redraw()
            elif self.box is not None:
                x0, y0, _mod = self.box
                draw_bridge.HUD.clear()
                draw_bridge.HUD.update({"box": (x0, y0, x, y), "owner": self._hud_owner()})
                self.manager.redraw()
        except Exception as exc:                           # noqa: BLE001
            self.log("[FAIL] Drag : {0}".format(exc))
            self._cancel()

    def _release(self):
        try:
            if self.radius_drag is not None:
                self.radius_drag = None
                draw_bridge.HUD.clear()
                self.on_setting("falloff_radius")
                self.manager.redraw()
                self.log("[Info] Falloff radius {0:g} frame(s).".format(self.manager.settings["falloff_radius"]))
                return
            if self.gizmo_drag is not None:
                self._end_gizmo()
            if self.deform is not None:
                self._commit_deform()
                return
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
                if abs(x - x0) < CLICK_PX and abs(y - y0) < CLICK_PX:
                    if modifier not in ("shift", "ctrl"):
                        self.manager.select([], "replace")      # 빈 곳 클릭 = 해제
                    else:
                        self.manager.redraw()
                    return
                picks = self.manager.pickable() + self.manager.pickable_frames()
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

    # ---------------------------------------------------------------- deform (v01.10)
    def _start_deform(self, point, x, y):
        """고른 점이 있는 경로마다 deform 세션 (가중치 = 폴오프, 꺼져 있으면 고른 점만 1).

        끄는 기준(anchor)은 점 자체가 아니라 **누른 픽셀의 광선이 끌기 평면과 만나는 곳**이다 - 정수 픽셀 광선은 점을 정확히
        지나지 않아, 점을 기준으로 하면 움직이지 않은 클릭도 조금 튀어 키를 썼다(시험이 잡음). 그 평면은 점을 지난다.
        """
        point = np.asarray(point, dtype="float64")
        origin, direction = self.view.ray(x, y)
        hit = picking.drag_target(self.manager.settings["plane"], origin, direction, point, self.view.view_dir)
        anchor = point if hit is None else hit
        if not self._open_deform():
            return
        self.anchor = np.asarray(anchor, dtype="float64").copy()
        self.anchor_point = point.copy()            # 끌기 평면 · 축이 지나는 점

    def _open_deform(self):
        """고른 점이 있는 경로마다 deform 세션을 연다. 열었으면 True."""
        tol = float(self.manager.settings.get("fit_tolerance", 0.1)) / 100.0
        items = []
        for cache in self.manager.cache_list():
            times = self.manager.selection.get(cache.key)
            if not times or cache.locked or cache.points is None:
                continue
            w = self.manager.weights_for(cache)
            if w is None:
                w = falloff.weights(cache.times, times, 0.0)
            try:
                session = ss.StrokeSession(cache, mode=ss.MODE_DEFORM, tolerance_rel=tol)
            except RuntimeError as exc:
                self.log("[SKIP] {0} : {1}".format(cache.label, exc))
                continue
            session.begin_stroke()
            items.append((cache, session, w))
        if not items:
            return False
        self.deform = items
        self.deform_moved = False
        self.watcher.busy = True
        return True

    # ---------------------------------------------------------------- 매니퓰레이터 (v01.11)
    def _press_gizmo(self, x, y):
        """기즈모를 눌렀으면 끌기를 시작하고 True. 편집 툴이 켜져 있어 기즈모가 그려질 때만."""
        if not self.manager.gizmo_on:
            return False
        frame = self.manager.gizmo_frame()
        if frame is None:
            return False
        pivot, axes = frame
        v = self.view
        mode = self.manager.settings.get("manip_mode", gz.MODE_MOVE)
        part = gz.hit(pivot, axes, mode, v.view_proj, v.width, v.height, x, y)
        if part is None:
            return False
        vdir = gz.view_dir(v.view_proj)
        ray0 = v.ray(x, y)
        drag = {"part": part, "pivot": pivot, "axes": axes, "vdir": vdir, "ray0": ray0, "px0": (x, y), "angle": 0.0,
                "start": None}
        if mode == gz.MODE_MOVE:
            drag["start"] = self._gizmo_point(part, pivot, axes, ray0, vdir)
            if drag["start"] is None:
                return False
        keys_only = not self.manager.selection_has_frames() and self.manager.falloff_radius() <= 0
        if mode == gz.MODE_MOVE and keys_only:
            # 키만 + 폴오프 끔 = 예전 키 끌기 (끄는 동안 오브젝트가 바로 따라온다)
            self.session = DragSession(self.manager.selected_items())
            if self.session.empty:
                self.session = None
                return False
            self.watcher.busy = True
            self.session.begin()
        elif not self._open_deform():
            return False
        self.gizmo_drag = drag
        self.manager.gizmo_hover = None
        self.manager.gizmo_active = part
        self.manager.gizmo_axes = axes
        self.manager.redraw()
        return True

    def _drag_gizmo(self, x, y):
        g = self.gizmo_drag
        v = self.view
        ray = v.ray(x, y)
        if g["start"] is not None:                                  # 이동
            target = self._gizmo_point(g["part"], g["pivot"], g["axes"], ray, g["vdir"])
            if target is None:
                return
            delta = target - g["start"]
            if self.session is not None:
                self.session.update(delta)
            else:
                if np.any(np.abs(delta) > 1e-9):
                    self.deform_moved = True
                for cache, session, w in self.deform:
                    P = session.stack[-1] + w[:, None] * delta
                    session.set_state(P)
                    self.manager.preview[cache.key] = P
            self.manager.gizmo_pivot = g["pivot"] + delta
        else:                                                       # 회전
            angle = gz.rotate_angle(g["part"], g["pivot"], g["axes"], g["vdir"], g["ray0"], ray,
                                    v.view_proj, v.width, v.height, g["px0"], (x, y))
            axis = gz.rotate_axis(g["part"], g["axes"], g["vdir"])
            g["angle"] = angle
            if abs(angle) > 1e-9:
                self.deform_moved = True
            for cache, session, w in self.deform:
                P = gz.rotate_points(session.stack[-1], g["pivot"], axis, angle, w)
                session.set_state(P)
                self.manager.preview[cache.key] = P
            self.manager.gizmo_pivot = g["pivot"]
            draw_bridge.HUD.clear()
            draw_bridge.HUD.update({"text": (x, y, "{0:+.1f} deg".format(np.degrees(angle))), "owner": self._hud_owner()})
        self.manager.redraw()

    def _gizmo_point(self, part, pivot, axes, ray, vdir):
        """끌기 점. 가운데 사각형 = 고른 점을 그냥 끄는 것과 같다 → **Drag in** 평면 · 축을 따른다(View 가 기본).
        고른 점 위를 누르면 늘 가운데가 잡히므로, 이렇게 해야 Drag in 의 Y · Ground 같은 고정이 그대로 먹는다."""
        if part == "center":
            return picking.drag_target(self.manager.settings["plane"], ray[0], ray[1], pivot, self.view.view_dir)
        return gz.move_point(part, pivot, axes, ray[0], ray[1], vdir)

    def _end_gizmo(self):
        """기즈모 끌기 상태만 정리 (쓰기 · 취소는 deform / session 쪽이 한다)."""
        self.gizmo_drag = None
        self.manager.gizmo_active = None
        self.manager.gizmo_pivot = None
        self.manager.gizmo_axes = None
        draw_bridge.HUD.clear()

    def _clear_preview(self, items):
        for cache, _s, _w in items:
            self.manager.preview.pop(cache.key, None)

    def _commit_deform(self):
        """놓기: 경로마다 refit 해 쓰고, undo 묶음 하나로 (Ctrl+Z 한 번)."""
        items, self.deform = self.deform, None
        self._clear_preview(items)
        if not self.deform_moved:
            for _c, session, _w in items:
                session.drop_stroke()
            self.watcher.busy = False
            self.manager.redraw()
            return
        added, wrote, points = 0, 0, 0
        cmds.undoInfo(openChunk=True, chunkName="MotionPathDeform")
        try:
            for cache, session, w in items:
                if session.end_stroke():
                    wrote += 1
                added += sum(r[2] for r in session.report)
                points += int(np.count_nonzero(w > 1e-9))
                for name, _err, _n, msg in session.report:
                    if msg:
                        self.log("[WARN] {0}.{1} : {2}".format(cache.label, name, msg))
        finally:
            cmds.undoInfo(closeChunk=True)
            self.watcher.busy = False
        self.manager.refresh_all()
        if wrote:
            r = self.manager.falloff_radius()
            self.log("[OK] Moved {0} path point(s){1} on {2} path(s), {3} key(s) added. Ctrl+Z undoes it in one step.".format(
                points, " (falloff {0:g} fr)".format(r) if r > 0 else "", wrote, added))

    def _hud_owner(self):
        caches = self.manager.cache_list()
        return caches[0].key if caches else ""

    def _show_radius(self, x, y):
        draw_bridge.HUD.clear()
        draw_bridge.HUD.update({"text": (x, y, "Falloff {0:g} fr".format(self.manager.settings["falloff_radius"])),
                                "owner": self._hud_owner()})

    def _cancel(self):
        if self.gizmo_drag is not None:
            self._end_gizmo()
        if self.deform is not None:
            items, self.deform = self.deform, None
            for _c, session, _w in items:
                session.drop_stroke()
            self._clear_preview(items)
            self.watcher.busy = False
            self.log("[Info] Drag cancelled.")
        if self.session is not None:
            session, self.session = self.session, None
            try:
                session.cancel()
            finally:
                self.watcher.busy = False
            self.log("[Info] Drag cancelled.")
        self.box = None
        if self.radius_drag is not None:
            self.radius_drag = None
            self.on_setting("falloff_radius")
        draw_bridge.HUD.clear()
        self.manager.redraw()

    def _finalize(self):
        """컨텍스트에서 나갈 때 (다른 툴 · Q). 끄는 중인 드래그는 취소."""
        if self.session is not None or self.deform is not None or self.box is not None or self.radius_drag is not None \
                or self.gizmo_drag is not None:
            self._cancel()


def _make_key_filter(context):
    """B · W · E 를 먹는 앱 이벤트 필터 (G0-2 실측 방식). 이 컨텍스트가 지금 툴일 때만 먹는다 - 다른 툴이면 마야 그대로.
    W / E (v01.11) = 매니퓰레이터 Move / Rotate - 먹지 않으면 마야가 Move / Rotate 툴로 바꿔 편집 툴에서 나간다."""
    from Framework.qt.qt import QEvent, QObject, Qt

    watched = (QEvent.ShortcutOverride, QEvent.KeyPress, QEvent.KeyRelease)
    mouse_move = QEvent.MouseMove

    class _KeyFilter(QObject):
        def eventFilter(self, obj, event):
            et = event.type()
            if et == mouse_move:                           # v01.14 호버 - 버튼 없이 움직일 때만, 이벤트는 먹지 않는다
                try:
                    if event.buttons() == Qt.NoButton and context.is_active():
                        context.hover_at_cursor()
                except Exception:                          # noqa: BLE001
                    pass
                return False
            if et not in watched:
                return False
            try:
                key = event.key()
                if key not in (Qt.Key_B, Qt.Key_W, Qt.Key_E) or \
                        event.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier):
                    return False
                if not context.is_active():
                    return False
            except Exception:                              # noqa: BLE001
                return False
            if et == QEvent.ShortcutOverride:
                event.accept()                             # 단축키로 처리하지 말고 KeyPress 로
                return True
            if not event.isAutoRepeat():
                try:
                    if key == Qt.Key_W:
                        if et == QEvent.KeyPress:
                            context.set_manip_mode(gz.MODE_MOVE)
                    elif key == Qt.Key_E:
                        if et == QEvent.KeyPress:
                            context.set_manip_mode(gz.MODE_ROTATE)
                    elif et == QEvent.KeyPress:
                        context.b_pressed()
                    else:
                        context.b_released()
                except Exception as exc:                   # noqa: BLE001
                    context.log("[FAIL] b key : {0}".format(exc))
            return True

    return _KeyFilter()
