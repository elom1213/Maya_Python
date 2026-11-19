# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 감시 · 관리자 시험 (계획서 §7-2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_watcher.py
# 헤드리스에는 idle 이 없어 evalDeferred 가 돌지 않는다 - 콜백이 "할 일" 을 표시했는지 보고 flush() 를 직접 부른다.
import os

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_bridge   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_nodes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.path_manager import PathManager   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.watcher import Watcher   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)
logs = []
scene_changes = []

names = scenes.hierarchy(120)
mgr = PathManager(log=logs.append)
w = Watcher(mgr, on_scene_change=lambda: scene_changes.append(1))
w.start()

# ---- 대상 추가 → 굽기 · 그리기 노드 · 그리기 데이터
added = mgr.set_targets([names["ctrl"], "j3", names["driven"]])
check("three targets baked", added == 3 and len(mgr.cache_list()) == 3)
check("one draw node per path", len(cmds.ls(type="junMotionPath")) == 3)
check("draw data for every path", all(c.key in draw_bridge.DATA for c in mgr.cache_list()))
check("locked path is logged with its reason", any("driven by" in m for m in logs), logs)
ctrl = [c for c in mgr.cache_list() if c.node.endswith("|ctrl")][0]
check("draw data has the line and the keys", len(draw_bridge.DATA[ctrl.key]["line"]) == 120 and
      len(draw_bridge.DATA[ctrl.key]["keys"]) == len(ctrl.keys))

# ---- 그래프 에디터처럼 다른 곳에서 키를 바꾸면
cmds.keyframe(names["ctrl"] + ".translateY", index=(1, 1), relative=True, valueChange=2.0)
# MAnimMessage 의 커브 편집 알림은 마야가 idle 에 모아 보낸다 - mayapy 에는 idle 이 없어 오지 않는다(GUI 확인 목록).
print("INFO anim-curve-edited callback delivered headless:", w._pending, "(expected False: Maya sends it on idle)")
w.flush()
k = ctrl.keys[1]
check("the path follows the edit", np.abs(ctrl.points[k.row] - np.array(world_pivot(ctrl.node, k.t))).max() < 1e-6)

# ---- undo 도
cmds.undo()
w.flush()
check("the path follows undo", np.abs(ctrl.points[k.row] - np.array(world_pivot(ctrl.node, k.t))).max() < 1e-6)

# ---- 편집 세션이 도는 동안(busy)은 무시
w.busy = True
w._pending = False
cmds.keyframe(names["ctrl"] + ".translateY", index=(1, 1), relative=True, valueChange=1.0)
check("busy watcher does not schedule", not w._pending)
w.busy = False
w.flush()

# ---- 소수 프레임 키를 새로 넣으면(경로 시간이 바뀜) 다시 굽는다
cmds.setKeyframe(names["ctrl"], attribute="translateX", time=44.5, value=3.0)
w.flush()
check("a new fractional key triggers a re-bake and lands on the path",
      ctrl.row_of(44.5) is not None and
      np.abs(ctrl.point_at(44.5) - np.array(world_pivot(ctrl.node, 44.5))).max() < 1e-6)

# ---- 선택 : 고르기 · 토글 · 빼기 · 사라진 키는 빠진다
picks = [(ctrl, ctrl.keys[0]), (ctrl, ctrl.keys[2])]
mgr.select(picks, "replace")
check("select two keys", mgr.selected_count() == 2)
mgr.select([(ctrl, ctrl.keys[0])], "toggle")
check("toggle removes one", mgr.selected_count() == 1)
t_sel = ctrl.keys[2].t
cmds.cutKey(names["ctrl"], attribute=("translateX", "translateY", "translateZ"), time=(t_sel, t_sel))
w.flush()
check("a deleted key drops out of the selection", mgr.selected_count() == 0)
check("selected keys are drawn in their own array", len(draw_bridge.DATA[ctrl.key]["selected"]) == 0)

# ---- 저장 : 그리기 노드가 파일에 없고 플러그인 requires 도 없다, 저장 뒤 다시 보인다
path = os.path.join(os.environ.get("TEMP", "."), "a630_watch_save.ma")
cmds.file(rename=path)
cmds.file(save=True, type="mayaAscii", force=True)
text = open(path, encoding="utf-8", errors="ignore").read()
check("saved file has no draw node and does not require the plugin",
      "junMotionPath" not in text and "jun_motion_path" not in text)
check("draw nodes come back after the save", len(cmds.ls(type="junMotionPath")) == 3)

# ---- 대상 빼기 · 시간 바뀜
mgr.set_targets([names["ctrl"]])
check("removing targets deletes their draw nodes", len(cmds.ls(type="junMotionPath")) == 1 and
      len(draw_bridge.DATA) == 1)
cmds.currentTime(77)
check("time change moves the current-frame dot", np.abs(
    np.array(list(draw_bridge.DATA[ctrl.key]["current"][0])[:3]) - ctrl.point_at(77)).max() < 1e-6)

# ---- 그리기 노드는 undo 큐에 들어가지 않는다
cmds.flushUndo()
mgr.set_targets([names["ctrl"], "j3"])
check("creating draw nodes leaves the undo queue empty", cmds.undoInfo(q=True, undoName=True) == "")

# ---- 새 씬 → 정리 콜백
cmds.file(new=True, force=True)
check("new scene calls the cleanup hook", len(scene_changes) >= 1)
mgr.clear()
w.stop()
check("clear leaves no draw nodes", not cmds.ls(type="junMotionPath") and not draw_bridge.DATA)

_common.finish()
