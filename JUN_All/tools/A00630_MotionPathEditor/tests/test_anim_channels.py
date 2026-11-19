# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - translate 채널 시험 (계획서 §7-2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_anim_channels.py
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

import _common   # noqa: E402
from _common import check   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import anim_channels as ch   # noqa: E402


def curve_values(node, frames):
    return [tuple(cmds.getAttr(node + ".translate", time=f)[0]) for f in frames]


FRAMES = [f * 0.5 for f in range(2, 241)]

# ---- 상태 판정
names = scenes.simple(120)
c = ch.Channels(names["plain"])
check("keyed axes are 'curve'", [a.state for a in c.axes] == ["curve", "curve", "curve"])
check("plain cube is editable", c.lock_reason() == "")
c = ch.Channels(names["partial"])
check("unkeyed Z is 'static'", [a.state for a in c.axes] == ["curve", "curve", "static"])
check("key union of partial X + Y", c.key_times() == [1.0, 25.0, 50.0, 120.0], c.key_times())
cmds.setAttr(names["opm"] + ".translateY", lock=True)
c = ch.Channels(names["opm"])
check("locked plug is 'locked', the rest still editable", c.axes[1].state == "locked" and c.lock_reason() == "")
cmds.setAttr(names["opm"] + ".translateX", lock=True)
cmds.setAttr(names["opm"] + ".translateZ", lock=True)
check("all three locked -> path locked", ch.Channels(names["opm"]).lock_reason() == "Translate is locked")

names = scenes.hierarchy(60)
c = ch.Channels(names["driven"])
check("constraint-driven -> 'driven' with the source named", c.axes[0].state == "driven" and "pointConstraint" in
      c.lock_reason(), c.lock_reason())

# 애니메이션 레이어
names = scenes.simple(60)
cmds.select(names["plain"])
layer = cmds.animLayer("layerA", addSelectedObjects=True)
cmds.setKeyframe(names["plain"], attribute="translateX", time=10, value=3.0, animLayer=layer)
reason = ch.Channels(names["plain"]).lock_reason()
check("animation layer -> locked with a 'not supported yet' reason", "not supported yet" in reason, reason)

# ---- 평가 = 마야 값 (내부 단위 cm, UI 단위 m 일 때도)
names = scenes.simple(120)
c = ch.Channels(names["plain"])
vals = c.values(FRAMES[::7])
maya_vals = curve_values(names["plain"], FRAMES[::7])
check("curve evaluation == getAttr -time (cm)", max(abs(a - b) for r, m in zip(vals, maya_vals)
                                                     for a, b in zip(r, m)) < 1e-9)
cmds.currentUnit(linear="m")
c = ch.Channels(names["plain"])
vals = c.values([30.0])[0]
ui = cmds.getAttr(names["plain"] + ".translate", time=30)[0]
check("internal units stay cm when the UI unit is m", abs(vals[0] - ui[0] * 100.0) < 1e-6, (vals[0], ui[0]))
cmds.currentUnit(linear="cm")

# ---- ensure_keys : 모양은 그대로
names = scenes.simple(120)
node = names["partial"]
before = curve_values(node, FRAMES)
c = ch.Channels(node)
changed = c.ensure_keys([50.0, 25.0])
after = curve_values(node, FRAMES)
worst = max(abs(a - b) for r, m in zip(before, after) for a, b in zip(r, m))
check("ensure_keys fills partial keys", changed and all(a.key_index(50.0) >= 0 and a.key_index(25.0) >= 0
                                                         for a in c.axes), [a.state for a in c.axes])
check("ensure_keys keeps the motion (every half frame)", worst < 1e-6, worst)
check("static Z got a curve keyed on the union times", c.axes[2].state == "curve" and
      sorted(c.axes[2].key_times()) == [1.0, 25.0, 50.0, 120.0], c.axes[2].key_times())
check("ensure_keys again changes nothing", c.ensure_keys([50.0]) is False)

# UI 단위 m 에서 static 축 커브 만들기 - 값이 그대로
names = scenes.simple(60)
cmds.setAttr(names["partial"] + ".translateZ", 2.5)       # cm
cmds.currentUnit(linear="m")
c = ch.Channels(names["partial"])
c.ensure_keys([1.0])
cmds.currentUnit(linear="cm")
z = cmds.getAttr(names["partial"] + ".translateZ", time=30)
check("static axis keyed in m UI units keeps its value", abs(z - 2.5) < 1e-6, z)

_common.finish()
