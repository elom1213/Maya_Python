# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.39 - Shift+A Layer Blend Key (HoldLayerManager.apply + run_hold) 시험 (mayapy headless)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_hold_layer_blend.py
# 계획서 docs/plans/a00110_hold_layer_blend_plan.md 5장.
import os
import sys

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

from tools.A00110_animTool_V02.app.core import HoldLayerManager as HLM   # noqa: E402
from tools.A00110_animTool_V02.app.core import HotkeyManager   # noqa: E402
from tools.A00110_animTool_V02.app.core import LayerKeyManager as LKM   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def crv(obj, attr, layer):
    return LKM.layer_curve("{0}.{1}".format(obj, attr), layer)


def keys(curve):
    if not curve:
        return {}
    t = cmds.keyframe(curve, q=True, timeChange=True) or []
    v = cmds.keyframe(curve, q=True, valueChange=True) or []
    return dict(zip([round(x, 4) for x in t], [round(x, 6) for x in v]))


def base_keys(obj):
    root = LKM.root_layer()
    return {a: keys(crv(obj, a, root)) for a in ("translateX", "rotateX")}


def scene(override=False):
    cmds.file(new=True, force=True)
    cube = cmds.polyCube(n="ctl")[0]
    other = cmds.polyCube(n="other")[0]
    for t, v in ((1, 0.0), (100, 10.0)):
        cmds.setKeyframe(cube, at="tx", t=t, v=v)
        cmds.setKeyframe(cube, at="rx", t=t, v=v * 3)
    layer = cmds.animLayer("Layer_01", override=override)
    cmds.select(cube)
    cmds.animLayer(layer, e=True, attribute=["ctl.tx", "ctl.rx", "ctl.ry"])
    # 레이어 값(raw) 키 : setKeyframe -animLayer -v 는 additive 에서 최종값 역산이라 커브에 직접 쓴다
    HLM._key_raw(cube, "translateX", layer, 90, 2.0)
    HLM._key_raw(cube, "translateX", layer, 80, 7.0)
    cmds.currentTime(100)
    return cube, other, layer


SETTINGS = {"enabled": True, "layer": "Layer_01", "offset": 10, "axis_values": {"rx": 0.0, "tx": 5.0}}

for override in (False, True):
    tag = "OVR" if override else "ADD"
    cube, other, layer = scene(override)
    base0 = base_keys(cube)
    HLM.update(**SETTINGS)
    cmds.select(cube)
    n, msg = HLM.apply()
    print("  msg:", msg)
    tx = keys(crv(cube, "translateX", layer))
    rx = keys(crv(cube, "rotateX", layer))
    ry = keys(crv(cube, "rotateY", layer))
    check(tag + " 1 apply returns 1 object", n == 1, msg)
    check(tag + " 2 layer tx: f90 keeps layer value 2.0 (overwrite), f80 untouched",
          tx.get(90.0) == 2.0 and tx.get(80.0) == 7.0 and 100.0 in tx, tx)
    # getAttr -time 은 레이어 blend 를 거치면 옛 값이 나올 때가 있다 -> 시간을 실제로 옮겨 잰다
    cmds.currentTime(1)
    cmds.currentTime(100)
    fin_tx = round(cmds.getAttr(cube + ".tx"), 6)
    fin_rx = round(cmds.getAttr(cube + ".rx"), 6)
    check(tag + " 2b f100 final value = Pose (tx 5.0, rx 0.0)", fin_tx == 5.0 and fin_rx == 0.0, (fin_tx, fin_rx))
    check(tag + " 3 layer rx: f90 + f100 keyed", 90.0 in rx and 100.0 in rx, rx)
    if not override:
        check(tag + " 3b additive rx f90 = 0 (no curve before)", rx.get(90.0) == 0.0, rx)
    check(tag + " 4 layer ry: f90 key, no f100 (not a pose axis)", 90.0 in ry and 100.0 not in ry, ry)
    check(tag + " 5 BaseAnimation curves unchanged", base_keys(cube) == base0, base_keys(cube))

    # 멤버 아닌 오브젝트
    cmds.select(other)
    n, msg = HLM.apply()
    check(tag + " 6 non-member: 0 keyed + Skipped", n == 0 and "Skipped: other" in msg
          and not cmds.keyframe(other, q=True), msg)

    # 없는 레이어
    HLM.update(layer="NoSuchLayer")
    cmds.select(cube)
    before = keys(crv(cube, "translateX", layer))
    n, msg = HLM.apply()
    check(tag + " 7 missing layer: warning, no keys", n == 0 and "not found" in msg
          and keys(crv(cube, "translateX", layer)) == before, msg)

    # 잠긴 레이어
    HLM.update(layer="Layer_01")
    cmds.animLayer(layer, e=True, lock=True)
    n, msg = HLM.apply(frame=50)
    check(tag + " 8 locked layer: warning", n == 0 and "locked" in msg, msg)
    cmds.animLayer(layer, e=True, lock=False)

    # 꺼짐 / 축 없음
    HLM.update(enabled=False)
    check(tag + " 9 disabled -> (0, '')", HLM.apply() == (0, ""))
    HLM.update(enabled=True, axis_values={})
    n, msg = HLM.apply()
    check(tag + " 10 no axis -> warning", n == 0 and "no Pose Key axis" in msg, msg)
    HLM.update(**SETTINGS)

    # mute 표시
    cmds.animLayer(layer, e=True, mute=True)
    n, msg = HLM.apply(frame=60)
    check(tag + " 11 muted layer: keyed + '(layer muted)'", n == 1 and "(layer muted)" in msg, msg)
    cmds.animLayer(layer, e=True, mute=False)

# ---------------- run_hold : Hold + Layer Blend 한 번의 undo ----------------
cube, other, layer = scene(False)
cmds.undoInfo(state=True, infinity=True)
cmds.flushUndo()
HLM.update(**SETTINGS)
cmds.select(cube)
base0 = base_keys(cube)
lay0 = keys(crv(cube, "translateX", layer))
root = LKM.root_layer()
base_tx = crv(cube, "translateX", root)
# Hold 대상: base tx 커브의 키 두 개 선택 (mayapy 에는 그래프 에디터가 없어 selectKey 로)
cmds.selectKey(base_tx, time=(1, 100), replace=True)
orig_inview = cmds.inViewMessage
cmds.inViewMessage = lambda **kw: None   # headless
try:
    HotkeyManager.run_hold()
finally:
    cmds.inViewMessage = orig_inview
after_lay = keys(crv(cube, "translateX", layer))
after_base = keys(base_tx)
check("RH1 run_hold: hold flattened base tx (f100 = f1 value 0)", after_base.get(100.0) == 0.0, after_base)
check("RH2 run_hold: layer tx f90 = 2.0 kept + f100 keyed", after_lay.get(90.0) == 2.0 and 100.0 in after_lay, after_lay)
cmds.undo()
check("RH3 one undo reverts both Hold and Layer Blend",
      keys(base_tx) == base0["translateX"] and keys(crv(cube, "translateX", layer)) == lay0,
      (keys(base_tx), keys(crv(cube, "translateX", layer))))
check("RH4 layer ry curve gone after undo", not keys(crv(cube, "rotateY", layer)))

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
