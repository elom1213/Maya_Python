# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.51 - Bake > Bake 를 구간만 구울 때 애니메이션 레이어 오브젝트의 구간 밖 키 보존 시험 (mayapy headless)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_bake_layers.py
# 사용자 보고: 컨스트레인트를 걸고 [10, 50] 만 구우면 그 밖의 기존 키가 지워진다 (오브젝트는 BaseAnimation + 다른 레이어에 키).
import os
import sys

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

from tools.A00110_animTool_V02.app.core import BakeManager   # noqa: E402
from tools.A00110_animTool_V02.app.core import LayerKeyManager as LKM   # noqa: E402

R = []
CH = ["tx", "ty", "tz", "rx", "ry", "rz"]
S, E = 10, 50
ALL = list(range(0, 101))


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def scene(mode="additive", member=True, make_layer=True, name="obj"):
    """obj : [0, 100] 매 프레임 Base 키 (tx, ty, ry), 레이어(tx, ry 멤버)에도 키. tgt : 움직이는 타깃."""
    cmds.file(new=True, force=True)
    obj = cmds.polyCube(n=name)[0]
    tgt = cmds.spaceLocator(n="tgt")[0]
    for f in ALL:
        cmds.setKeyframe(obj, at="tx", t=f, v=f * 0.1)
        cmds.setKeyframe(obj, at="ty", t=f, v=0.5)
        cmds.setKeyframe(obj, at="ry", t=f, v=f * 1.0)
        cmds.setKeyframe(tgt, at="tx", t=f, v=-3.0 + f * 0.02)
        cmds.setKeyframe(tgt, at="ty", t=f, v=5.0 + f * 0.05)
        cmds.setKeyframe(tgt, at="ry", t=f, v=10.0 + f * 0.5)
    lay = None
    if make_layer:
        lay = cmds.animLayer("AnimLayer1", override=(mode == "override"))
        if member:
            cmds.select(obj)
            cmds.animLayer(lay, e=True, attribute=[obj + ".tx", obj + ".ry"])
            for f in (0, 30, 70, 100):
                cmds.setKeyframe(obj, at="tx", t=f, v=f * 0.1 + 1.0, animLayer=lay)
                cmds.setKeyframe(obj, at="ry", t=f, v=f * 1.0 + 20.0, animLayer=lay)
    cmds.select(clear=True)
    return obj, tgt, lay


def finals(obj, frames):
    out = {}
    for f in frames:
        cmds.currentTime(f)
        out[f] = tuple(cmds.getAttr(obj + "." + c) for c in CH)
    return out


def diff_frames(a, b, frames, tol=1e-4):
    return [f for f in frames if any(abs(x - y) > tol for x, y in zip(a[f], b[f]))]


def curve_keys(obj, attr, layer):
    root = LKM.root_layer()
    plug = obj + "." + attr
    c = LKM.layer_curve(plug, layer, root) if layer else LKM.plain_curve(plug)
    if not c:
        return {}
    t = cmds.keyframe(c, q=True, timeChange=True) or []
    v = cmds.keyframe(c, q=True, valueChange=True) or []
    return dict(zip(t, v))


def outside(keys):
    return dict((t, v) for t, v in keys.items() if t < S or t > E)


def run_case(tag, obj, tgt, lay, **kw):
    before = finals(obj, ALL)
    base_before = dict((a, outside(curve_keys(obj, a, LKM.root_layer()))) for a in ("translateX", "rotateY", "translateY"))
    lay_before = dict((a, curve_keys(obj, a, lay)) for a in ("translateX", "rotateY")) if lay else {}
    con = cmds.parentConstraint(tgt, obj, mo=False)[0]
    want = finals(obj, range(S, E + 1))
    cmds.currentTime(77)
    n, msg = BakeManager.bake([obj], S, E, channels=CH, **kw)
    t_back = cmds.currentTime(q=True)
    cmds.delete(con)
    after = finals(obj, ALL)
    out_bad = diff_frames(before, after, [f for f in ALL if f < S or f > E])
    in_bad = diff_frames(want, after, range(S, E + 1))
    return dict(before=before, after=after, want=want, msg=msg, out_bad=out_bad, in_bad=in_bad, t_back=t_back,
                base_before=base_before, lay_before=lay_before)


# ---------------------------------------------------------------- B1 레이어 없음 (회귀 - bakeResults 그대로)
obj, tgt, lay = scene(make_layer=False)
r = run_case("B1", obj, tgt, lay)
check("B1 no layers: outside frames unchanged, inside = constraint (bakeResults path)",
      not r["out_bad"] and not r["in_bad"] and "in animation layers" not in r["msg"], (r["out_bad"][:5], r["in_bad"][:5]))

# ---------------------------------------------------------------- B2 레이어는 있지만 멤버 아님
obj, tgt, lay = scene(member=False)
r = run_case("B2", obj, tgt, lay)
check("B2 layer exists but object not a member: unchanged outside, inside = constraint",
      not r["out_bad"] and not r["in_bad"] and "in animation layers" not in r["msg"], (r["out_bad"][:5], r["in_bad"][:5]))

# ---------------------------------------------------------------- B3 additive 멤버 (사용자 상황)
obj, tgt, lay = scene("additive")
r = run_case("B3", obj, tgt, lay)
check("B3 additive layer member: every frame outside [10, 50] unchanged", not r["out_bad"], r["out_bad"][:5])
check("B3b inside [10, 50] = constraint result (layers not double counted)", not r["in_bad"],
      [(f, r["want"][f][0], r["after"][f][0]) for f in r["in_bad"][:3]])
check("B3c BaseAnimation keys outside the range kept (tx, ry, ty)",
      all(outside(curve_keys(obj, a, LKM.root_layer())) == r["base_before"][a] for a in r["base_before"]),
      dict((a, len(outside(curve_keys(obj, a, LKM.root_layer())))) for a in r["base_before"]))
check("B3d AnimLayer1 curves untouched", all(curve_keys(obj, a, lay) == r["lay_before"][a] for a in r["lay_before"]))
check("B3e message says layered objects were baked through the layers",
      "1 in animation layers" in r["msg"] and "kept" in r["msg"], r["msg"])
check("B3f current time restored", r["t_back"] == 77.0, r["t_back"])

# ---------------------------------------------------------------- B4 override 멤버 -> override 레이어에 키
obj, tgt, lay = scene("override")
r = run_case("B4", obj, tgt, lay)
base_tx_all_before = r["base_before"]["translateX"]
check("B4 override layer member: outside unchanged, inside = constraint",
      not r["out_bad"] and not r["in_bad"], (r["out_bad"][:5], r["in_bad"][:5]))
check("B4b keys went to the override layer for tx / ry (base tx outside kept), message names it",
      len([t for t in curve_keys(obj, "translateX", lay) if S <= t <= E]) == E - S + 1
      and outside(curve_keys(obj, "translateX", LKM.root_layer())) == base_tx_all_before
      and "AnimLayer1" in r["msg"], r["msg"])
check("B4c ty (not a layer member) keyed on BaseAnimation",
      len([t for t in curve_keys(obj, "translateY", LKM.root_layer()) if S <= t <= E]) == E - S + 1)

# ---------------------------------------------------------------- B5 뮤트된 override -> Base
obj, tgt, lay = scene("override")
cmds.animLayer(lay, e=True, mute=True)
r = run_case("B5", obj, tgt, lay)
check("B5 muted override layer is ignored: keys on BaseAnimation, layer curves untouched, result right",
      not r["out_bad"] and not r["in_bad"]
      and all(curve_keys(obj, a, lay) == r["lay_before"][a] for a in r["lay_before"]),
      (r["out_bad"][:5], r["in_bad"][:5]))

# ---------------------------------------------------------------- B6 잠긴 대상 레이어
obj, tgt, lay = scene("override")
cmds.animLayer(lay, e=True, lock=True)
r = run_case("B6", obj, tgt, lay)
check("B6 locked target layer: channel skipped with a warning, outside still unchanged",
      "is locked - skipped" in r["msg"] and not r["out_bad"], r["msg"])
cmds.animLayer(lay, e=True, lock=False)

# ---------------------------------------------------------------- B7 일반 + 레이어 오브젝트 섞기, smart 안내
obj, tgt, lay = scene("additive")
plain_obj = cmds.polyCube(n="plain")[0]
for f in ALL:
    cmds.setKeyframe(plain_obj, at="tx", t=f, v=f * 0.2)
b_plain = finals(plain_obj, ALL)
c2 = cmds.parentConstraint(tgt, plain_obj, mo=False)[0]
want_plain = finals(plain_obj, range(S, E + 1))
before = finals(obj, ALL)
con = cmds.parentConstraint(tgt, obj, mo=False)[0]
want = finals(obj, range(S, E + 1))
n, msg = BakeManager.bake([obj, plain_obj], S, E, channels=CH, smart=True)
cmds.delete(con, c2)
a_obj, a_plain = finals(obj, ALL), finals(plain_obj, ALL)
check("B7 mixed list + smart (tol 0.5): both unchanged outside, inside within the tolerance of the constraint",
      not diff_frames(before, a_obj, [f for f in ALL if f < S or f > E])
      and not diff_frames(want, a_obj, range(S, E + 1), tol=0.5 + 1e-6)
      # plain 은 tx 만 키가 있다 - 키가 없던 채널(ty ...)은 마야 기본대로 구간 밖에서 구운 끝값을 잇는다(원래 값은
      # 컨스트레인트를 거는 순간 pairBlend 입력이 0 이 되어 되살릴 수 없다)
      and all(abs(b_plain[f][0] - a_plain[f][0]) < 1e-4 for f in ALL if f < S or f > E)
      and not diff_frames(want_plain, a_plain, range(S, E + 1), tol=0.5 + 1e-6),
      msg)
check("B7d reduce_keys: straight line -> 2 keys, a bump above tolerance is kept",
      BakeManager.reduce_keys([0, 1, 2, 3, 4], [0, 1, 2, 3, 4], 0.01) == [0, 4]
      and 2 in BakeManager.reduce_keys([0, 1, 2, 3, 4], [0, 0, 1, 0, 0], 0.5))
in_keys = lambda obj_, layer_: len([t for t in curve_keys(obj_, "translateX", layer_) if S <= t <= E])
check("B7b smart = dense bake + simplify inside the range, for both objects (fewer than 41 keys inside)",
      "simplify inside the range" in msg and in_keys(obj, LKM.root_layer()) < E - S + 1
      and 0 < len([t for t in (cmds.keyframe(plain_obj + ".tx", q=True, timeChange=True) or []) if S <= t <= E]) < E - S + 1,
      (msg, in_keys(obj, LKM.root_layer())))
check("B7c smart keeps the plain object's keys outside (60 keys)",
      len([t for t in (cmds.keyframe(plain_obj + ".tx", q=True, timeChange=True) or []) if t < S or t > E]) == 60)

# ---------------------------------------------------------------- B9 레이어 없는 씬 + smart (예전: 구간 밖 60 f 값이 바뀌었다)
obj, tgt, lay = scene(make_layer=False)
r = run_case("B9", obj, tgt, lay, smart=True, smart_tolerance=0.01)
check("B9 no layers + smart: outside unchanged (was broken by bakeResults -smart), inside within tolerance",
      not r["out_bad"] and not diff_frames(r["want"], r["after"], range(S, E + 1), tol=0.05),
      (r["out_bad"][:3], r["msg"]))

# ---------------------------------------------------------------- B8 undo 한 번
obj, tgt, lay = scene("additive")
cmds.undoInfo(state=True, infinity=True)
cmds.flushUndo()
con = cmds.parentConstraint(tgt, obj, mo=False)[0]
base0 = curve_keys(obj, "translateX", LKM.root_layer())
lay0 = curve_keys(obj, "translateX", lay)
BakeManager.bake([obj], S, E, channels=CH)
changed = curve_keys(obj, "translateX", LKM.root_layer()) != base0
cmds.undo()
check("B8 one undo restores BaseAnimation and layer curves", changed and curve_keys(obj, "translateX", LKM.root_layer()) == base0
      and curve_keys(obj, "translateX", lay) == lay0)

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
