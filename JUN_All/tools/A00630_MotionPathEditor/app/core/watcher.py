# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 바뀌면 다시 그리기 (계획서 §4-8)
"""
| 바뀌는 것 | 감지 | 처리 |
| 애님 커브 (그래프 에디터 · 다른 툴) | MAnimMessage.addAnimCurveEditedCallback | idle 에 refresh_all 한 번 |
| undo / redo | MEventMessage "Undo" / "Redo" | idle 에 refresh_all 한 번 |
| 현재 시간 | MEventMessage "timeChanged" | 현재 프레임 점만 (redraw) |
| 저장 | MSceneMessage before / after save | 그리기 노드를 잠깐 지웠다 다시 (파일에 플러그인 requires 가 안 써지게) |
| 새 씬 · 열기 | MSceneMessage before new / open | 툴 상태 정리 (on_scene_change 콜백) |

콜백 안에서는 씬을 바꾸지 않고 "다시 할 일" 만 표시한다. 실제 계산은 `evalDeferred(lowestPriority)` 로 idle 에서 한 번
(여러 콜백이 몰려도 한 번). 편집 세션이 도는 동안(busy)은 무시한다 - 세션이 직접 갱신한다.
"""

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds


class Watcher(object):

    def __init__(self, manager, on_scene_change=None):
        self.manager = manager
        self.on_scene_change = on_scene_change
        self.ids = []
        self.busy = False
        self._pending = False

    def start(self):
        if self.ids:
            return
        self.ids.append(oma.MAnimMessage.addAnimCurveEditedCallback(self._curves_edited))
        for event in ("Undo", "Redo"):
            self.ids.append(om.MEventMessage.addEventCallback(event, self._schedule))
        self.ids.append(om.MEventMessage.addEventCallback("timeChanged", self._time_changed))
        self.ids.append(om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeSave, self._before_save))
        self.ids.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterSave, self._after_save))
        for msg in (om.MSceneMessage.kBeforeNew, om.MSceneMessage.kBeforeOpen):
            self.ids.append(om.MSceneMessage.addCallback(msg, self._scene_change))

    def stop(self):
        for cid in self.ids:
            try:
                om.MMessage.removeCallback(cid)
            except Exception:                              # noqa: BLE001
                pass
        self.ids = []

    # ---------------------------------------------------------------- 콜백
    def _curves_edited(self, curves, *args):
        if not self.busy:
            self._schedule()

    def _schedule(self, *args):
        if self.busy or self._pending:
            return
        self._pending = True
        cmds.evalDeferred(self.flush, lowestPriority=True)

    def flush(self):
        """미뤄 둔 갱신 (idle). 시험에서는 직접 부른다."""
        self._pending = False
        if self.busy:
            return
        try:
            self.manager.refresh_all()
        except Exception as exc:                           # noqa: BLE001
            self.manager.log("[WARN] Path refresh failed : {0}".format(exc))

    def _time_changed(self, *args):
        if not self.busy:
            self.manager.redraw()

    def _before_save(self, *args):
        self.manager.hide_for_save()

    def _after_save(self, *args):
        self.manager.show_after_save()

    def _scene_change(self, *args):
        if self.on_scene_change is not None:
            self.on_scene_change()
