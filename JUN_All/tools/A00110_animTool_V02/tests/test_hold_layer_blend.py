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

PRE = "JUN_A00110_holdLayer_"


def clear_optvars():
    for k in ("enabled", "offset", "layer", "axis_values", "use_current", "view_layer", "current_axes"):
        if cmds.optionVar(exists=PRE + k):
            cmds.optionVar(remove=PRE + k)


clear_optvars()


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


# current_axes=[] : Pose 값 경로를 보는 시험 (v02.45 기본 current 축 ry · tx · tz 를 끈다)
SETTINGS = {"enabled": True, "layer": "Layer_01", "offset": 10, "axis_values": {"rx": 0.0, "tx": 5.0}, "current_axes": []}

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
# v02.47 기준 프레임 = 고른 구간 [1, 100] 의 a=1 -> 레이어 키는 f1 (Pose) 와 f-9 (레이어 값), f100 에는 없다
check("RH2 run_hold: layer keys at range start a=1 and a-N=-9, none at f100 (v02.47)",
      1.0 in after_lay and -9.0 in after_lay and 100.0 not in after_lay and after_lay.get(90.0) == 2.0, after_lay)
cmds.undo()
check("RH3 one undo reverts both Hold and Layer Blend",
      keys(base_tx) == base0["translateX"] and keys(crv(cube, "translateX", layer)) == lay0,
      (keys(base_tx), keys(crv(cube, "translateX", layer))))
check("RH4 layer ry curve gone after undo", not keys(crv(cube, "rotateY", layer)))

# ---------------- v02.40 : 설정 원본 = optionVar ----------------
HLM.update(**SETTINGS)
check("OV1 update writes optionVars",
      cmds.optionVar(q=PRE + "enabled") == 1 and cmds.optionVar(q=PRE + "layer") == "Layer_01"
      and cmds.optionVar(q=PRE + "offset") == 10 and HLM.load_settings()["axis_values"] == {"rx": 0.0, "tx": 5.0},
      HLM.load_settings())
HLM.settings["enabled"] = False      # 클래스 변수만 꺼도 apply 는 optionVar 를 본다
cube, other, layer = scene(False)
cmds.select(cube)
n, msg = HLM.apply()
check("OV2 apply reads optionVar, not the class dict", n == 1, msg)
HLM.update(layer="")
n, msg = HLM.apply()
check("OV3 empty layer -> 'no layer chosen'", n == 0 and "no layer chosen" in msg, msg)

# ---------------- v02.40 : DEV 리로드 순서 회귀 ----------------
# v02.38 이 로드된 세션에서 업데이트하면 hotkey_manager 가 hold_layer_manager 보다 sys.modules 앞에 있다
# -> reload 때 hotkey_manager 가 옛 HoldLayerManager 를 잡았다(v02.39 버그: Shift+A 가 레이어 키를 조용히 건너뜀).
import importlib   # noqa: E402
import config   # noqa: E402
KEY = "tools.A00110_animTool_V02.app.core.hold_layer_manager"
mod = sys.modules.pop(KEY)
sys.modules[KEY] = mod
if config.DEV_MODE:
    from dev.reloader_v02 import reload_for_tool   # noqa: E402
    reload_for_tool("tools.A00110_animTool_V02")
else:
    importlib.reload(sys.modules["tools.A00110_animTool_V02.app.core.hotkey_manager"])
    importlib.reload(mod)
    importlib.reload(sys.modules["tools.A00110_animTool_V02.app.core"])
from tools.A00110_animTool_V02.app.core import HoldLayerManager as UI_HLM   # noqa: E402  (UI 가 잡는 클래스)
hk = sys.modules["tools.A00110_animTool_V02.app.core.hotkey_manager"]
clear_optvars()
cube, other, layer = scene(False)
UI_HLM.update(**SETTINGS)
cmds.select(cube)
cmds.inViewMessage = lambda **kw: None
hk.HotkeyManager.run_hold()
lay = keys(crv(cube, "translateX", layer))
check("RL1 after reload (old module order) run_hold still keys the layer",
      lay.get(90.0) == 2.0 and 100.0 in lay and 90.0 in keys(crv(cube, "rotateY", layer)), lay)
clear_optvars()

# ---------------- v02.41 : Use current values ----------------
from tools.A00110_animTool_V02.app.core import PoseKeyManager   # noqa: E402

cmds.file(new=True, force=True)
plain = cmds.polyCube(n="plain")[0]
cmds.setKeyframe(plain, at="tx", t=1, v=0.0)
cmds.setKeyframe(plain, at="tx", t=20, v=10.0)
cmds.currentTime(10)
cmds.setAttr(plain + ".tx", 7.25)          # 키 없이 바꾼 값
cmds.setAttr(plain + ".ry", 33.0)          # 키 없던 채널
n, msg = PoseKeyManager.set_pose_keys({"tx": 0.0, "ry": 0.0}, use_current=True)
k_tx = keys(cmds.listConnections(plain + ".tx", type="animCurve")[0])
k_ry = keys((cmds.listConnections(plain + ".ry", type="animCurve") or [None])[0])
check("UC1 Pose Key use_current=True (all axes): keys the current (unkeyed) values, not the typed 0",
      k_tx.get(10.0) == 7.25 and k_ry.get(10.0) == 33.0 and "tx=current" in msg, (k_tx, k_ry, msg))

# v02.44 축마다 : ry 만 current, tx 는 입력 값 1.5
cmds.currentTime(12)
cmds.setAttr(plain + ".tx", 8.0)
cmds.setAttr(plain + ".ry", 44.0)
n, msg = PoseKeyManager.set_pose_keys({"tx": 1.5, "ry": 0.0}, current_axes=["ry"])
k_tx = keys(cmds.listConnections(plain + ".tx", type="animCurve")[0])
k_ry = keys(cmds.listConnections(plain + ".ry", type="animCurve")[0])
check("UC1b per-axis: ry = current 44.0, tx = typed 1.5", k_tx.get(12.0) == 1.5 and k_ry.get(12.0) == 44.0,
      (k_tx, k_ry, msg))


def final_at(obj, attr, t):
    cmds.currentTime(t - 1)
    cmds.currentTime(t)
    return round(cmds.getAttr("{0}.{1}".format(obj, attr)), 6)


for override in (False, True):
    tag = "UC-OVR" if override else "UC-ADD"
    clear_optvars()
    cube, other, layer = scene(override)
    before = {a: final_at(cube, a, 100) for a in ("tx", "rx")}
    HLM.update(**dict(SETTINGS, current_axes=["rx", "tx"]))
    cmds.select(cube)
    n, msg = HLM.apply()
    after = {a: final_at(cube, a, 100) for a in ("tx", "rx")}
    lay = keys(crv(cube, "translateX", layer))
    check(tag + " 1 Layer Blend all axes current: f100 keyed, final value unchanged (not Pose 5.0 / 0.0)",
          n == 1 and 100.0 in lay and after == before and "current: rx, tx" in msg, (before, after, msg))
    check(tag + " 2 f90 still keeps layer value 2.0", lay.get(90.0) == 2.0, lay)

    # v02.44 축마다 : tx 만 current -> tx 는 지금 값 유지, rx 는 Pose 0.0
    clear_optvars()
    cube, other, layer = scene(override)
    before_tx = final_at(cube, "tx", 100)
    HLM.update(**dict(SETTINGS, current_axes=["tx"]))
    cmds.select(cube)
    n, msg = HLM.apply()
    check(tag + " 3 per-axis: tx current (unchanged), rx = Pose 0.0",
          final_at(cube, "tx", 100) == before_tx and final_at(cube, "rx", 100) == 0.0 and msg.count("current: tx") == 1,
          (before_tx, final_at(cube, "tx", 100), final_at(cube, "rx", 100), msg))

# Shift+A : Hold 가 base tx 를 평평하게 바꿔도, Hold **전** 값이 레이어 f100 키로 남는다
clear_optvars()
cube, other, layer = scene(False)
want = final_at(cube, "tx", 1)        # v02.47 Current 값 = 고른 구간 a=1 의 값
cmds.currentTime(100)
HLM.update(**dict(SETTINGS, current_axes=["rx", "tx"]))
cmds.select(cube)
cmds.selectKey(LKM.layer_curve("ctl.translateX", LKM.root_layer()), time=(1, 100), replace=True)
hk.HotkeyManager.run_hold()
# 시간 이동(final_at)도 undo 큐에 들어가므로 undo 확인을 먼저 하고 redo 뒤에 값을 잰다
cmds.undo()
check("UC4 one undo reverts (time moves for reading a are not in the undo queue)",
      keys(LKM.layer_curve("ctl.translateX", LKM.root_layer())).get(100.0) == 10.0
      and 1.0 not in keys(crv(cube, "translateX", layer)))
cmds.redo()
check("UC3 run_hold: Current = value at range start a=1 read before Hold (final f1 unchanged), base held",
      final_at(cube, "tx", 1) == want and keys(LKM.layer_curve("ctl.translateX", LKM.root_layer())).get(100.0) == 0.0,
      (want, final_at(cube, "tx", 1)))
# ---------------- v02.47 : 기준 프레임 = 고른 키 구간 [a, b] 의 a ----------------
clear_optvars()
cube, other, layer = scene(False)
base_tx = LKM.layer_curve("ctl.translateX", LKM.root_layer())
base_rx = LKM.layer_curve("ctl.rotateX", LKM.root_layer())
for c, v60, v90 in ((base_tx, 6.0, 9.0), (base_rx, 18.0, 27.0)):
    cmds.setKeyframe(c, time=60, value=v60)
    cmds.setKeyframe(c, time=90, value=v90)
HLM._key_raw(cube, "translateX", layer, 50, 1.5)
want_rx60 = final_at(cube, "rx", 60)
cmds.currentTime(100)
HLM.update(**dict(SETTINGS, current_axes=["rx"]))          # tx = Pose 5.0, rx = Current (f60 값)
cmds.select(cube)
cmds.selectKey(base_tx, time=(60, 90), replace=True)
cmds.selectKey(base_rx, time=(60, 90), add=True)
check("RA0 range_start() = 60", HLM.range_start() == 60.0, HLM.range_start())
msgs = []
cmds.inViewMessage = lambda **kw: msgs.append(kw.get("amg", ""))
cmds.flushUndo()
hk.HotkeyManager.run_hold()
lay_tx = keys(crv(cube, "translateX", layer))
check("RA1 layer keys at a=60 and a-N=50, none at f100 (current time 100), scene's own f80 / f90 untouched",
      60.0 in lay_tx and lay_tx.get(50.0) == 1.5 and 100.0 not in lay_tx
      and lay_tx.get(80.0) == 7.0 and lay_tx.get(90.0) == 2.0
      and "(f50 -> f60" in msgs[-1], (lay_tx, msgs[-1]))
check("RA2 current time restored to 100", cmds.currentTime(q=True) == 100.0)
check("RA3 Hold still ran on the selected range (base tx f90 = f60 value 6.0)", keys(base_tx).get(90.0) == 6.0, keys(base_tx))
cmds.undo()
check("RA4 one undo reverts Hold + Layer Blend", keys(base_tx).get(90.0) == 9.0 and 60.0 not in keys(crv(cube, "translateX", layer)))
cmds.redo()
check("RA5 final at a=60: tx = Pose 5.0, rx = its pre-Hold value (Current)",
      final_at(cube, "tx", 60) == 5.0 and final_at(cube, "rx", 60) == want_rx60,
      (final_at(cube, "tx", 60), final_at(cube, "rx", 60), want_rx60))
# 고른 키가 없으면 예전처럼 현재 프레임
clear_optvars()
cube, other, layer = scene(False)
cmds.currentTime(100)
HLM.update(**SETTINGS)
cmds.select(cube)
cmds.selectKey(clear=True)
check("RA6 no keys selected -> range_start() None", HLM.range_start() is None)
hk.HotkeyManager.run_hold()
check("RA7 no keys selected -> layer keys at current frame 100 and 90", 100.0 in keys(crv(cube, "translateX", layer)))
clear_optvars()
HLM.update(**SETTINGS)
cube, other, layer = scene(False)
cmds.select(cube)

HLM.update(current_axes=[])
check("UC5 no current axis -> capture_current() is None", HLM.capture_current() is None)
HLM.update(current_axes=["rz"])     # v02.46 체크된 축(rx, tx)에 없어도 current 축은 읽는다
cap = HLM.capture_current(["ctl"])
check("UC6 current axis not checked is still captured (v02.46)", cap is not None and ("ctl", "rz") in cap, cap)

# v02.46 사용자 보고 : 축 체크는 꺼져 있고 Current 만 켠 축(기본 ry tx tz)이 레이어에 안 찍혔다
clear_optvars()
cube, other, layer = scene(False)
cmds.currentTime(100)
before_ry = final_at(cube, "ry", 100)
HLM.update(**dict(SETTINGS, axis_values={"rx": 0.0}, current_axes=["ry", "tz"]))
cmds.select(cube)
n, msg = HLM.apply()
ry = keys(crv(cube, "rotateY", layer))
check("UC10 Layer Blend: Current-only axis ry (axis unchecked) keyed at f100 with its current value",
      n == 1 and 100.0 in ry and final_at(cube, "ry", 100) == before_ry and "current: ry" in msg
      and "Pose axes not in layer: tz" in msg, (ry, msg))
rx = keys(crv(cube, "rotateX", layer))
check("UC11 checked axis rx still keyed with the typed Pose value", final_at(cube, "rx", 100) == 0.0 and 100.0 in rx, rx)
cmds.file(new=True, force=True)
pk = cmds.polyCube(n="pk")[0]
cmds.currentTime(3)
cmds.setAttr(pk + ".ry", 21.0)
n, msg = PoseKeyManager.set_pose_keys({"tx": 1.0}, current_axes=["ry"])
k_ry = cmds.keyframe(pk + ".ry", q=True, valueChange=True, time=(3, 3)) or []
check("UC12 Pose Key: Current-only axis ry keyed (21.0) alongside checked tx", k_ry == [21.0]
      and (cmds.keyframe(pk + ".tx", q=True, valueChange=True, time=(3, 3)) or []) == [1.0], (k_ry, msg))

# v02.41 전역 use_current 를 쓰던 optionVar -> 체크된 축 전부 current 로 읽힌다
clear_optvars()
cmds.optionVar(intValue=(PRE + "use_current", 1))
cmds.optionVar(stringValue=(PRE + "axis_values", '{"rx": 0.0, "ty": 1.0}'))
check("UC7 old use_current=1 migrates to current_axes = checked axes",
      sorted(HLM.load_settings()["current_axes"]) == ["rx", "ty"], HLM.load_settings())
HLM.update(current_axes=["ty"])
check("UC8 writing current_axes removes the old flag",
      not cmds.optionVar(exists=PRE + "use_current") and HLM.load_settings()["current_axes"] == ["ty"])
clear_optvars()
check("UC9 no saved current_axes -> default ry, tx, tz (v02.45)",
      HLM.load_settings()["current_axes"] == ["ry", "tx", "tz"], HLM.load_settings())
clear_optvars()
for k in ("use_current",):
    if cmds.optionVar(exists=PRE + k):
        cmds.optionVar(remove=PRE + k)

# ---------------- v02.42 : 선택한 오브젝트에만 레이어 키 ----------------
# AnimLayer1 에 A · B · C 가 모두 들어 있어도 A 만 선택하면 A 에만 키. 선택에 레이어 · 세트 · 캐릭터 노드가 섞여도 마찬가지.


def layer_snap(objs, lay):
    out = {}
    for o in objs:
        for a in ("translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "visibility"):
            c = LKM.layer_curve(o + "." + a, lay)
            out[(o, a)] = tuple(zip(cmds.keyframe(c, q=True, timeChange=True) or [],
                                    cmds.keyframe(c, q=True, valueChange=True) or [])) if c else None
    return out


def three_scene():
    cmds.file(new=True, force=True)
    objs = [cmds.polyCube(n=n)[0] for n in ("A", "B", "C")]
    for o in objs:
        cmds.setKeyframe(o, at="tx", t=1, v=0)
        cmds.setKeyframe(o, at="tx", t=100, v=10)
    lay = cmds.animLayer("AnimLayer1")
    cmds.select(objs)
    cmds.animLayer(lay, e=True, addSelectedObjects=True)
    for o in objs:
        HLM._key_raw(o, "translateX", lay, 50, 1.0)
    cmds.currentTime(100)
    return objs, lay


for use_current in (False, True):
    for extra in ("none", "layer", "set", "character"):
        clear_optvars()
        objs, lay = three_scene()
        if extra == "set":
            cmds.sets(objs, n="ctlSet")
        if extra == "character":
            cmds.character(objs, n="charSet")
        HLM.update(enabled=True, layer=lay, offset=10, axis_values={"rx": 0.0, "tx": 5.0},
                   current_axes=["rx", "tx"] if use_current else [])
        before = layer_snap(objs, lay)
        cmds.select(["A"] + {"layer": [lay], "set": ["ctlSet"], "character": ["charSet"]}.get(extra, []), r=True, ne=True)
        hk.HotkeyManager.run_hold()
        after = layer_snap(objs, lay)
        changed = sorted({o for k, o in [(k, k[0]) for k in after] if after[k] != before[k]})
        check("SEL {0} +{1}: only the selected object A gets layer keys".format(
            "current" if use_current else "pose", extra), changed == ["A"], changed)

clear_optvars()
objs, lay = three_scene()
HLM.update(enabled=True, layer=lay, offset=10, axis_values={"tx": 5.0}, current_axes=[])
cmds.select(["A", lay, "B"], r=True, ne=True)
check("SEL selected_objects drops the layer node, keeps order", HLM.selected_objects() == ["A", "B"], HLM.selected_objects())
n, msg = HLM.apply()
check("SEL message names the keyed objects", n == 2 and msg.endswith(": A, B."), msg)
clear_optvars()

# ---------------- v02.43 : 보기 게이트 (Run only when viewing, 기본 BaseAnimation) ----------------
from tools.A00110_animTool_V02.app.core import AnimLayerManager as ALM   # noqa: E402

clear_optvars()
if cmds.optionVar(exists=PRE + "view_layer"):
    cmds.optionVar(remove=PRE + "view_layer")
check("VG0 default view_layer = '' (root)", HLM.load_settings()["view_layer"] == "")

objs, lay = three_scene()
root = LKM.root_layer()
HLM.update(enabled=True, layer=lay, offset=10, axis_values={"tx": 5.0}, current_axes=[])

# AnimLayer1 을 보면서 그 레이어 커브의 구간 키를 골라 Shift+A  ->  Hold 만, Layer Blend 는 건너뜀
HLM._key_raw("A", "translateX", lay, 80, 4.0)
ALM.set_selected([lay])
cmds.select("A", r=True)
a_curve = LKM.layer_curve("A.translateX", lay)
cmds.selectKey(a_curve, time=(50, 80), replace=True)
check("VG1 viewed_layers = [AnimLayer1]", HLM.viewed_layers() == [lay], HLM.viewed_layers())
msgs = []
cmds.inViewMessage = lambda **kw: msgs.append(kw.get("amg", ""))
hk.HotkeyManager.run_hold()
k = keys(a_curve)
check("VG2 viewing AnimLayer1: Hold ran on the layer curve (f80 = f50 value 1.0)", k.get(80.0) == 1.0, k)
check("VG3 viewing AnimLayer1: Layer Blend skipped (no f90/f100 keys) + reason in message",
      90.0 not in k and 100.0 not in k and "skipped - viewing 'AnimLayer1'" in msgs[-1], (k, msgs[-1]))

# BaseAnimation 을 보면 동작
ALM.set_selected([root])
cmds.select("A", r=True)
check("VG4 viewed_layers = [BaseAnimation]", HLM.viewed_layers() == [root], HLM.viewed_layers())
n, msg = HLM.apply()
check("VG5 viewing BaseAnimation: Layer Blend runs", n == 1 and 100.0 in keys(a_curve), msg)

# 둘 다 보고 있으면 건너뜀
ALM.set_selected([root, lay])
n, msg = HLM.apply(frame=60)
check("VG6 viewing two layers: skipped", n == 0 and "skipped - viewing" in msg and 60.0 not in keys(a_curve), msg)

# 게이트를 AnimLayer1 로 바꾸면 반대
HLM.update(view_layer=lay)
ALM.set_selected([root])
n, msg = HLM.apply(frame=60)
check("VG7 gate=AnimLayer1, viewing Base: skipped", n == 0 and "runs only when viewing 'AnimLayer1'" in msg, msg)
ALM.set_selected([lay])
n, msg = HLM.apply(frame=60)
check("VG8 gate=AnimLayer1, viewing AnimLayer1: runs", n == 1 and 60.0 in keys(a_curve), msg)

# 아무 레이어도 선택 안 됨 -> preferred, 그것도 없으면 루트
HLM.update(view_layer="")
for l in cmds.ls(type="animLayer"):
    cmds.animLayer(l, e=True, selected=False, preferred=False)
check("VG9 nothing selected/preferred -> viewing root", HLM.viewed_layers() == [root], HLM.viewed_layers())
cmds.animLayer(lay, e=True, preferred=True)
check("VG10 nothing selected, AnimLayer1 preferred -> viewing AnimLayer1", HLM.viewed_layers() == [lay], HLM.viewed_layers())
HLM.update(current_axes=["tx"])
check("VG11 gate closed -> capture_current() is None", HLM.capture_current(["A"]) is None)
clear_optvars()
if cmds.optionVar(exists=PRE + "view_layer"):
    cmds.optionVar(remove=PRE + "view_layer")

# ---------------- v02.52 : Shift+A 가 구간 끝 b 에도 레이어 키 (값 = a-N, a 를 찍은 뒤의 a 레이어 값) ----------------
cmds.file(new=True, force=True)
ctl = cmds.polyCube(n="ctl")[0]
for f in range(1, 101):
    cmds.setKeyframe(ctl, at="tx", t=f, v=f * 0.1)
    cmds.setKeyframe(ctl, at="rx", t=f, v=f * 0.5)
    cmds.setKeyframe(ctl, at="ry", t=f, v=-f * 0.2)
lay = cmds.animLayer("Layer_01")
cmds.select(ctl)
cmds.animLayer(lay, e=True, attribute=[ctl + "." + a for a in ("tx", "rx", "ry")])
cmds.currentTime(100)
HLM.update(**dict(SETTINGS, current_axes=["ry"]))           # tx = Pose 5.0, rx = Pose 0.0, ry = Current
root = LKM.root_layer()
base = dict((a, LKM.layer_curve(ctl + "." + a, root)) for a in ("translateX", "rotateX", "rotateY"))
cmds.select(ctl, r=True)
cmds.selectKey(base["translateX"], time=(60, 90), replace=True)
check("RB0 range_end() = 90", HLM.range_end() == 90.0, HLM.range_end())
cmds.flushUndo()
msgs = []
cmds.inViewMessage = lambda **kw: msgs.append(kw.get("amg", ""))
lay0 = dict((a, keys(crv(ctl, a, lay))) for a in ("translateX", "rotateX", "rotateY"))
hk.HotkeyManager.run_hold()
ok = True
info = []
for a in ("translateX", "rotateX", "rotateY"):
    c = crv(ctl, a, lay)
    k = keys(c)
    v60 = cmds.keyframe(c, q=True, eval=True, time=(60, 60), valueChange=True)[0]
    v90 = k.get(90.0)
    span = [cmds.keyframe(c, q=True, eval=True, time=(t, t), valueChange=True)[0] for t in [60 + 0.5 * i for i in range(61)]]
    flat = (cmds.keyTangent(c, q=True, time=(60, 60), outTangentType=True) == ["flat"]
            and cmds.keyTangent(c, q=True, time=(90, 90), inTangentType=True) == ["flat"])
    if not (50.0 in k and 60.0 in k and v90 is not None and abs(v90 - v60) < 1e-9
            and max(span) - min(span) < 1e-9 and flat):
        ok = False
        info.append((a, sorted(k), v60, v90, max(span) - min(span), flat))
check("RB1 Shift+A keys a-N=50, a=60 AND b=90 on every layer channel, b value = a value, constant on [a, b], flat",
      ok and "f50 -> f60 -> f90" in msgs[-1], (info, msgs[-1:]))
cmds.undo()
check("RB2 one undo removes the b key too",
      dict((a, keys(crv(ctl, a, lay))) for a in ("translateX", "rotateX", "rotateY")) == lay0)
# 고른 키가 없으면 b 없음 (현재 프레임 기준, 예전 그대로)
picked = cmds.keyframe(q=True, selected=True, name=True) or []
if picked:
    cmds.selectKey(picked, remove=True)
check("RB3 no keys selected -> range_end() None", HLM.range_end() is None)
hk.HotkeyManager.run_hold()
k = sorted(keys(crv(ctl, "translateX", lay)))
check("RB4 no selection -> keys only at current-N and current (no extra b key)", k == [90.0, 100.0], k)
clear_optvars()

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
