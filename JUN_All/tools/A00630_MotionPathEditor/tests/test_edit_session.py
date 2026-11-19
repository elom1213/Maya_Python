# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 편집 세션 시험 (계획서 §7-2) - 드래그를 세션 API 로 흉내
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_edit_session.py
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_nodes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_cache as pc   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.edit_session import DragSession   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)
FRAMES = list(range(1, 121))


def snapshot(node):
    return [tuple(cmds.getAttr(node + ".translate", time=f)[0]) for f in FRAMES]


def diff(a, b):
    return max(abs(x - y) for r, m in zip(a, b) for x, y in zip(r, m))


def drag(selection, deltas):
    s = DragSession(selection)
    s.begin()
    for d in deltas:
        s.update(d)
    return s


# ---- 계층 씬 컨트롤 키 하나 끌기
names = scenes.hierarchy(120)
node = names["ctrl"]
cache = pc.PathCache(node, 1, 120)
cache.rebake()
key = cache.keys[1]
p0 = cache.points[key.row].copy()
orig = snapshot(node)
cmds.flushUndo()
target_delta = np.array([0.8, -1.2, 2.0])
s = drag([(cache, [key.t])], [target_delta * 0.3, target_delta * 0.7, target_delta * 1.4, target_delta])
check("several moves then the last one: key lands exactly (no drift)",
      np.abs(np.array(world_pivot(node, key.t)) - (p0 + target_delta)).max() < 1e-6,
      np.abs(np.array(world_pivot(node, key.t)) - (p0 + target_delta)).max())
check("path follows during the drag", np.abs(cache.points[key.row] - (p0 + target_delta)).max() < 1e-6)
check("nothing in the undo queue while dragging", cmds.undoInfo(q=True, undoName=True) == "")
moved = s.commit()
check("commit reports a move", moved)
cmds.undo()
check("ONE undo restores the motion", diff(snapshot(node), orig) < 1e-9, diff(snapshot(node), orig))
cmds.redo()
check("redo puts the edit back", np.abs(np.array(world_pivot(node, key.t)) - (p0 + target_delta)).max() < 1e-6)
cmds.undo()

# ---- 여러 키 · 여러 경로를 함께
cache.refresh()
j = pc.PathCache("j3", 1, 120)
j.rebake()
sel = [(cache, [cache.keys[0].t, cache.keys[2].t]), (j, [j.keys[1].t])]
starts = [(c, t, c.point_at(t).copy()) for c, ts in sel for t in ts]
d = np.array([-0.5, 0.25, 0.75])
s = drag(sel, [d])
s.commit()
worst = max(np.abs(np.array(world_pivot(c.node, t)) - (p + d)).max() for c, t, p in starts)
check("several keys on two paths move together", worst < 1e-6, worst)
cmds.undo()

# ---- 부분 키 + 키 없는 축 : 처음 움직일 때 키를 맞추고, undo 한 번에 키까지 되돌린다
names = scenes.simple(120)
node = names["partial"]
cache = pc.PathCache(node, 1, 120)
cache.rebake()
orig = snapshot(node)
key_counts = [cmds.keyframe(node + "." + a, q=True, keyframeCount=True) or 0 for a in
              ("translateX", "translateY", "translateZ")]
k50 = [k for k in cache.keys if abs(k.t - 50.0) < 1e-6][0]
p0 = cache.points[k50.row].copy()
cmds.flushUndo()
s = drag([(cache, [50.0])], [np.array([0.0, 1.0, 1.0])])
check("partial key moves in Y and Z too (keys were added)",
      np.abs(np.array(world_pivot(node, 50.0)) - (p0 + [0.0, 1.0, 1.0])).max() < 1e-6)
s.commit()
check("the rest of the motion is unchanged away from the edited key",
      max(abs(a - b) for f, r, m in zip(FRAMES, snapshot(node), orig) if f < 25 or f > 120
          for a, b in zip(r, m)) < 1e-9)
cmds.undo()
check("one undo removes the move AND the added keys", diff(snapshot(node), orig) < 1e-9 and
      [cmds.keyframe(node + "." + a, q=True, keyframeCount=True) or 0 for a in
       ("translateX", "translateY", "translateZ")] == key_counts)

# ---- 잠긴 축은 그대로
names = scenes.simple(120)
node = names["plain"]
cmds.setAttr(node + ".translateY", lock=True)
cache = pc.PathCache(node, 1, 120)
cache.rebake()
k = cache.keys[2]
y_before = cmds.getAttr(node + ".translateY", time=k.t)
s = drag([(cache, [k.t])], [np.array([1.0, 5.0, 1.0])])
s.commit()
check("locked Y keeps its value", abs(cmds.getAttr(node + ".translateY", time=k.t) - y_before) < 1e-9)
check("X and Z still move", abs(cmds.getAttr(node + ".translateX", time=k.t) -
                                (cache.points[k.row][0])) < 1e-6)
cmds.undo()
cmds.setAttr(node + ".translateY", lock=False)

# ---- 취소 : 값 · 넣은 키 모두 원래대로, undo 큐에 남는 것 없음
names = scenes.simple(120)
node = names["partial"]
cache = pc.PathCache(node, 1, 120)
cache.rebake()
orig = snapshot(node)
cmds.flushUndo()
s = drag([(cache, [50.0])], [np.array([2.0, 2.0, 2.0])])
s.cancel()
check("cancel restores the motion", diff(snapshot(node), orig) < 1e-9)
check("cancel removes the added keys", (cmds.keyframe(node + ".translateZ", q=True, keyframeCount=True) or 0) == 0)
check("cancel leaves the path as it was", np.abs(cache.point_at(50.0) - np.array(world_pivot(node, 50.0))).max() < 1e-6)

# ---- 움직이지 않고 놓기 = 아무것도 안 바뀜
cmds.flushUndo()
s = drag([(cache, [50.0])], [np.zeros(3)])
check("no move -> commit returns False", s.commit() is False)
check("no move -> nothing changed, no keys added", diff(snapshot(node), orig) < 1e-12 and
      (cmds.keyframe(node + ".translateZ", q=True, keyframeCount=True) or 0) == 0)

# ---- 잠긴 경로는 세션에 들어가지 않는다
names = scenes.hierarchy(60)
locked = pc.PathCache(names["driven"], 1, 60)
locked.rebake()
s = DragSession([(locked, [1.0])])
check("locked path is left out of the session", s.empty)

# ---- 0-5 : auto 탄젠트 - 키 하나를 바꾸면 이웃 키의 auto 탄젠트도 다시 계산된다(그래프 에디터와 같은 마야 동작).
#      그래서 바뀌는 범위는 앞뒤 **두 번째 키**까지다. 그 밖은 그대로여야 한다.
names = scenes.simple(120)
node = names["plain"]
cmds.cutKey(node, attribute=("translateX", "translateY", "translateZ"))
for f in range(1, 121, 12):
    cmds.setKeyframe(node, attribute="translateX", time=f, value=f * 0.1)
    cmds.setKeyframe(node, attribute="translateY", time=f, value=(f % 24) * 0.2)
    cmds.setKeyframe(node, attribute="translateZ", time=f, value=0.0)
cmds.keyTangent(node, inTangentType="auto", outTangentType="auto")
cache = pc.PathCache(node, 1, 120)
cache.rebake()
orig = snapshot(node)
i = 5
mid = cache.keys[i]
s = drag([(cache, [mid.t])], [np.array([0.0, 3.0, 0.0])])
s.commit()
changed = [f for f, r, m in zip(FRAMES, snapshot(node), orig) if max(abs(a - b) for a, b in zip(r, m)) > 1e-9]
keys = [k.t for k in cache.keys]
print("INFO 0-5 auto tangents: moved key {0}, changed frames {1}..{2}, keys i-2 / i+2 = {3} / {4}".format(
    mid.t, changed[0], changed[-1], keys[i - 2], keys[i + 2]))
check("0-5: auto tangents - the change stays between the 2nd keys before / after",
      changed[0] > keys[i - 2] and changed[-1] < keys[i + 2], (changed[0], changed[-1]))
cmds.undo()
check("0-5: and one undo restores it", diff(snapshot(node), orig) < 1e-9)

# ---- 속도 (계획서 1단계 완료 기준) : 경로 1,000 프레임, 키 하나 드래그 - 마우스 한 번 갱신 < 16 ms
import time   # noqa: E402
names = scenes.hierarchy(1000)
cache = pc.PathCache(names["ctrl"], 1, 1000)
t0 = time.perf_counter()
cache.rebake()
bake_s = time.perf_counter() - t0
s = DragSession([(cache, [cache.keys[1].t])])
s.begin()
s.update(np.array([0.01, 0.0, 0.0]))          # 처음 움직임 (키 맞추기 포함)
samples = []
for i in range(30):
    t0 = time.perf_counter()
    s.update(np.array([0.01 * i, 0.02 * i, 0.0]))
    samples.append(time.perf_counter() - t0)
s.commit()
cmds.undo()
per_move = sorted(samples)[len(samples) // 2]
print("INFO speed: bake 1,000 frames {0:.3f}s, drag update median {1:.2f} ms".format(bake_s, per_move * 1000.0))
check("drag update of a 1,000-frame path < 16 ms", per_move < 0.016, "{0:.2f} ms".format(per_move * 1000.0))

_common.finish()
