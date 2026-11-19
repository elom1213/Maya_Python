# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 애니메이션 레이어 시험 (v01.03)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_layers.py
# 경로 = 모든 레이어를 합친 실제 움직임, 끌면 고른 레이어의 키만 바뀐다.
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import anim_channels as ch   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_nodes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_cache as pc   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.edit_session import DragSession   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.path_manager import PathManager   # noqa: E402

draw_nodes.ensure_plugin()
cmds.undoInfo(state=True, infinity=True)
SAMPLE = (1, 7, 20, 33, 47, 60, 71, 88, 100, 111, 120)


def build():
    """부모 애니메이션 + Base 키 + 레이어 4종(additive 가중치 애니 · override 0.5 · 뮤트 · 잠김) + 레이어에 없는 오브젝트."""
    scenes.new(120)
    grp = cmds.group(empty=True, name="grp")
    for f, v in ((1, 0.0), (120, 30.0)):
        cmds.setKeyframe(grp, attribute="rotateY", time=f, value=v)
    c = cmds.polyCube(name="c")[0]
    cmds.parent(c, grp)
    for f in (1, 30, 60, 90, 120):
        cmds.setKeyframe(c, attribute="translateX", time=f, value=f * 0.05)
        cmds.setKeyframe(c, attribute="translateY", time=f, value=(f % 40) * 0.1)
        cmds.setKeyframe(c, attribute="translateZ", time=f, value=-f * 0.02)
    other = cmds.polyCube(name="other")[0]
    for f in (1, 120):
        cmds.setKeyframe(other, attribute="translateX", time=f, value=f * 0.1)
    cmds.select(c)
    add = cmds.animLayer("addL", addSelectedObjects=True)
    for f, (x, y) in ((1, (0.0, 0.0)), (40, (1.0, 0.5)), (80, (-0.5, 1.5)), (120, (0.0, 0.0))):
        cmds.setKeyframe(c, attribute="translateX", time=f, value=x, animLayer=add)
        cmds.setKeyframe(c, attribute="translateY", time=f, value=y, animLayer=add)
    cmds.setKeyframe(add, attribute="weight", time=1, value=1.0)          # 가중치 애니메이션
    cmds.setKeyframe(add, attribute="weight", time=120, value=0.4)
    ovr = cmds.animLayer("ovrL", addSelectedObjects=True, override=True)
    cmds.setKeyframe(c, attribute="translateX", time=20, value=3.0, animLayer=ovr)
    cmds.setKeyframe(c, attribute="translateX", time=100, value=6.0, animLayer=ovr)
    cmds.setAttr(ovr + ".weight", 0.5)
    mute = cmds.animLayer("muteL", addSelectedObjects=True)
    cmds.setKeyframe(c, attribute="translateZ", time=60, value=2.0, animLayer=mute)
    cmds.setAttr(mute + ".mute", True)
    locked = cmds.animLayer("lockL", addSelectedObjects=True)
    cmds.setKeyframe(c, attribute="translateZ", time=60, value=0.5, animLayer=locked)
    cmds.setAttr(locked + ".lock", True)
    cmds.select(clear=True)
    return c, other


def curve_keys(curve):
    return list(zip(cmds.keyframe(curve, q=True, timeChange=True) or [],
                    cmds.keyframe(curve, q=True, valueChange=True) or []))


def all_curves(node):
    out = {}
    for a in ch.AXES:
        axis = ch.Axis(ch.depend_node(node), a)
        for lv in axis.levels:
            if lv.curve_name:
                out[lv.curve_name] = curve_keys(lv.curve_name)
    return out


def path_error(cache):
    return max(np.abs(cache.point_at(f) - np.array(world_pivot(cache.node, f))).max() for f in SAMPLE)


c_node, other = build()
W0 = [np.array(world_pivot(c_node, f)) for f in SAMPLE]       # 처음 움직임 - undo 뒤 비교 기준
check("scene_layers lists Base first, then the layers in order",
      ch.scene_layers() == ["BaseAnimation", "addL", "ovrL", "muteL", "lockL"], ch.scene_layers())

# ---- 경로 = 레이어를 합친 실제 움직임 (어느 레이어를 고르든 같다)
for layer in ("BaseAnimation", "addL", "ovrL"):
    c = pc.PathCache(c_node, 1, 120, layer=layer)
    c.rebake()
    check("path with every layer combined == Maya ({0} picked)".format(layer), path_error(c) < 1e-6, path_error(c))

# ---- 키 점 = 고른 레이어의 키
c = pc.PathCache(c_node, 1, 120, layer="addL")
c.rebake()
check("keys shown are the picked layer's keys (addL)", [k.t for k in c.keys] == [1.0, 40.0, 80.0, 120.0],
      [k.t for k in c.keys])
check("switching the layer needs no re-bake", c.set_layer("ovrL") and [k.t for k in c.keys] == [20.0, 100.0],
      [k.t for k in c.keys])


def drag_layer_key(layer, t, delta):
    """layer 의 t 키를 delta 만큼 끌고 놓는다."""
    cache = pc.PathCache(c_node, 1, 120, layer=layer)
    cache.rebake()
    before = all_curves(c_node)
    p0 = cache.point_at(t).copy()
    s = DragSession([(cache, [t])])
    s.begin()
    s.update(np.asarray(delta) * 0.5)
    s.update(np.asarray(delta))
    s.commit()
    return p0, before


OTHER_TAGS = ("_addL_", "_ovrL_", "_muteL_", "_lockL_")
for layer, t in (("BaseAnimation", 60.0), ("addL", 40.0), ("ovrL", 20.0)):
    cmds.flushUndo()
    delta = np.array([0.7, -0.4, 0.3])
    p0, before = drag_layer_key(layer, t, delta)
    got = np.array(world_pivot(c_node, t))
    check("{0}: the dragged key lands exactly (all layers combined)".format(layer),
          np.abs(got - (p0 + delta)).max() < 1e-6, np.abs(got - (p0 + delta)).max())
    after = all_curves(c_node)
    changed = sorted(k for k in after if after[k] != before.get(k))
    if layer == "BaseAnimation":
        own = all(not any(tag in k for tag in OTHER_TAGS) for k in changed)
    else:
        own = all("_{0}_".format(layer) in k for k in changed)
    check("{0}: only that layer's curves changed".format(layer), bool(changed) and own, changed)
    cmds.undo()
    back = max(np.abs(np.array(world_pivot(c_node, f)) - w).max() for f, w in zip(SAMPLE, W0))
    check("{0}: one Ctrl+Z restores every curve AND the motion".format(layer), all_curves(c_node) == before and
          back < 1e-6, back)

# ---- override 레이어에서 그 레이어에 키가 없던 축(Y) : 처음 움직일 때 그 레이어에 커브를 만든다
cache = pc.PathCache(c_node, 1, 120, layer="ovrL")
cache.rebake()
orig = [world_pivot(c_node, f) for f in SAMPLE]
check("ovrL: Y has no curve on that layer yet (static)", cache.channels.axes[1].state == "static")
p0 = cache.point_at(100.0).copy()
s = DragSession([(cache, [100.0])])
s.begin()
s.update(np.array([0.0, 1.0, 0.0]))
s.commit()
check("ovrL: Y moves too (a layer curve was made)",
      np.abs(np.array(world_pivot(c_node, 100.0)) - (p0 + [0.0, 1.0, 0.0])).max() < 1e-6)
far = max(np.abs(np.array(world_pivot(c_node, f)) - np.array(o)).max() for f, o in zip(SAMPLE, orig) if f <= 20)
check("ovrL: frames up to the layer's first key are unchanged", far < 1e-6, far)
cmds.undo()
back = max(np.abs(np.array(world_pivot(c_node, f)) - np.array(o)).max() for f, o in zip(SAMPLE, orig))
check("ovrL: one Ctrl+Z removes the move and the new layer curve",
      back < 1e-6 and ch.Channels(c_node, "ovrL").axes[1].state == "static", back)

# ---- 잠금 이유
c = pc.PathCache(c_node, 1, 120, layer="muteL")
c.rebake()
check("muted layer -> locked: no effect", c.locked and "no effect" in c.lock_reason, c.lock_reason)
c = pc.PathCache(c_node, 1, 120, layer="lockL")
c.rebake()
check("locked layer -> locked with its name", c.locked and "lockL is locked" in c.lock_reason, c.lock_reason)
c = pc.PathCache(other, 1, 120, layer="addL")
c.rebake()
check("object not in the layer -> locked: not in the layer",
      c.locked and "Not in the animation layer addL" in c.lock_reason, c.lock_reason)
c = pc.PathCache(other, 1, 120, layer="BaseAnimation")
c.rebake()
check("the same object on Base is editable", not c.locked)

# ---- 관리자 : 편집 레이어 바꾸기
logs = []
mgr = PathManager(log=logs.append)
mgr.set_targets([c_node, other])
check("manager starts on Base", mgr.edit_layer() == "BaseAnimation" and not any(x.locked for x in mgr.cache_list()))
mgr.select([(mgr.cache_list()[0], mgr.cache_list()[0].keys[0])])
mgr.set_edit_layer("addL")
cc, oc = mgr.cache_list()
check("set_edit_layer: keys follow the layer, selection cleared, the other object locked and logged",
      [k.t for k in cc.keys] == [1.0, 40.0, 80.0, 120.0] and mgr.selected_count() == 0 and oc.locked and
      any("Not in the animation layer addL" in m for m in logs), logs)
check("set_edit_layer keeps the combined path", path_error(cc) < 1e-6, (path_error(cc), cc.node, cc.layer, sorted(cc.W)))
cmds.delete("addL")
mgr.rebake_all()
check("a deleted layer falls back to Base on Refresh", mgr.edit_layer() == "BaseAnimation" and
      [k.t for k in mgr.cache_list()[0].keys] == [1.0, 30.0, 60.0, 90.0, 120.0])
mgr.clear()

_common.finish()
