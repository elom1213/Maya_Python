# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.25 - Graph Focus 레이어 필터 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_graph_focus_layers.py
#
# 씬 : ctl.ty 베이스 [-400, 400], Layer1 [-200, 200], Layer2 [-100, 100] (+ ctl.tx 베이스만 ±100, other.ty 베이스만 ±800)
# 그래프 에디터(cmds UI)는 mayapy 에서 못 만든다 - 값 범위 · 레이어 판정 · 커브 고르기만 본다.
# GE 아웃라이너 필터(outlinerEditor -animLayerFilterOptions)가 실제로 커브를 가리는 것은 마야 GUI 에서 확인한다.
import os
import sys

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00110_animTool_V02.app.core import graph_view_manager as gvm   # noqa: E402
GVM = gvm.GraphViewManager

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def rng(layers, start=0, end=100):
    return GVM._value_range_in_window(start, end, layers)


# ---------------------------------------------------------------- 레이어 없는 씬
cube = cmds.polyCube(n="ctl")[0]
other = cmds.polyCube(n="other")[0]
for t, v in [(0, -400), (50, 400), (100, -400)]:
    cmds.setKeyframe(cube, at="ty", t=t, v=v)
    cmds.setKeyframe(cube, at="tx", t=t, v=v / 4.0)
    cmds.setKeyframe(other, at="ty", t=t, v=v * 2)
cmds.select(cube)
check("no layers : anim_layers() empty", GVM.anim_layers() == [])
check("no layers : resolve selected -> allAffecting, None", GVM.resolve_layer_filter("selected") == ("allAffecting", None, ""))
check("no layers : curves_for_layers(None) = base ty, tx", sorted(GVM.curves_for_layers([cube], None)) == ["ctl_translateX", "ctl_translateY"], GVM.curves_for_layers([cube], None))
check("no layers : range = [-400, 400]", rng(None) == (-400.0, 400.0), rng(None))

# ---------------------------------------------------------------- 레이어 둘
l1 = cmds.animLayer("Layer1", addSelectedObjects=True)
l2 = cmds.animLayer("Layer2", addSelectedObjects=True)
# setKeyframe(animLayer=L, value=V) 는 최종 평가값이 V 가 되도록 역산한다 - 레이어를 번갈아 키하면
# 서로의 외삽값이 섞여 커브 값이 엉킨다. 레이어마다 따로 세 키를 다 찍어 L1 커브 = ±200, L2 커브 = ±100 이 되게 한다.
for t, v in [(0, -200), (50, 200), (100, -200)]:
    cmds.setKeyframe(cube, at="ty", t=t, v=v, animLayer=l1)          # L1 = target - base = (200, -200, 200)
for t, v in [(0, -100), (50, 100), (100, -100)]:
    cmds.setKeyframe(cube, at="ty", t=t, v=v, animLayer=l2)          # L2 = target - (base + L1) = (100, -100, 100)
assert cmds.keyframe("ctl_translateY_Layer1_inputB", q=True, valueChange=True) == [200.0, -200.0, 200.0]
assert cmds.keyframe("ctl_translateY_Layer2_inputB", q=True, valueChange=True) == [100.0, -100.0, 100.0]
cmds.select(cube)
root = cmds.animLayer(q=True, root=True)
check("anim_layers = [Layer1, Layer2]", GVM.anim_layers() == [l1, l2], GVM.anim_layers())

all_curves = GVM.curves_for_layers([cube], None)
check("all curves = base ty, tx + L1 ty + L2 ty (4)", len(all_curves) == 4, all_curves)
check("curves of Layer1 only", GVM.curves_for_layers([cube], [l1]) == ["ctl_translateY_Layer1_inputB"], GVM.curves_for_layers([cube], [l1]))
check("curves of Base only = ty, tx base", sorted(GVM.curves_for_layers([cube], [root])) == ["ctl_translateX", "ctl_translateY"], GVM.curves_for_layers([cube], [root]))
check("curves of Base + Layer2", sorted(GVM.curves_for_layers([cube], [root, l2])) == ["ctl_translateX", "ctl_translateY", "ctl_translateY_Layer2_inputB"])
check("other object : layers filter Layer1 -> nothing", GVM.curves_for_layers([other], [l1]) == [])
check("other object : Base -> its base curve", GVM.curves_for_layers([other], [root]) == ["other_translateY"])

# 값 범위 - 레이어별
check("range Base = [-400, 400]", rng([root]) == (-400.0, 400.0), rng([root]))
check("range Layer1 = [-200, 200]", rng([l1]) == (-200.0, 200.0), rng([l1]))
check("range Layer2 = [-100, 100]", rng([l2]) == (-100.0, 100.0), rng([l2]))
check("range all = [-400, 400]", rng(None) == (-400.0, 400.0), rng(None))
check("range Layer1 in [60, 90] window (no keys inside) still valid", rng([l1], 60, 90) is not None and -200 <= rng([l1], 60, 90)[0] < rng([l1], 60, 90)[1] <= 200, rng([l1], 60, 90))

# ★ 예전 방식(keyframe -name)은 활성 레이어만 돌려준다 - 증상의 원인 재현
for l in cmds.ls(type="animLayer"):
    cmds.animLayer(l, e=True, selected=False, preferred=False)
cmds.animLayer(l1, e=True, selected=True, preferred=True)
old_way = cmds.keyframe(cube, q=True, name=True)
check("old keyframe -name with Layer1 active = Layer1 curve only (cause of the bug)", old_way == ["ctl_translateY_Layer1_inputB"], old_way)

# resolve : 선택 / 활성 / 둘 다 / 전부 / fallback
check("resolve selected -> Layer1", GVM.resolve_layer_filter("selected") == ("selected", [l1], ""), GVM.resolve_layer_filter("selected"))
check("resolve active -> Layer1", GVM.resolve_layer_filter("active") == ("active", [l1], ""))
check("resolve allAffecting -> None", GVM.resolve_layer_filter("allAffecting") == ("allAffecting", None, ""))
cmds.animLayer(l2, e=True, selected=True)       # L1 활성+선택, L2 선택
r = GVM.resolve_layer_filter("selected"); check("resolve selected -> L1 + L2 (order of ls)", r[0] == "selected" and sorted(r[1]) == [l1, l2], r)
r = GVM.resolve_layer_filter("activeAndSelected"); check("resolve activeAndSelected -> L1, L2", r[0] == "activeAndSelected" and sorted(r[1]) == [l1, l2], r)
cmds.animLayer(l1, e=True, selected=False); cmds.animLayer(l2, e=True, selected=False)
r = GVM.resolve_layer_filter("selected"); check("resolve selected, none selected -> active (Layer1) with note", r == ("active", [l1], "no layer selected"), r)
cmds.animLayer(l1, e=True, preferred=False)
r = GVM.resolve_layer_filter("selected"); check("resolve selected, none selected/active -> allAffecting with note", r[0] == "allAffecting" and r[1] is None and "no" in r[2], r)
r = GVM.resolve_layer_filter("active"); check("resolve active, none active -> allAffecting", r[0] == "allAffecting" and r[1] is None, r)
cmds.animLayer(root, e=True, selected=True, preferred=True)
r = GVM.resolve_layer_filter("selected"); check("resolve selected -> BaseAnimation", r == ("selected", [root], ""), r)
check("range for selected Base = [-400, 400]", rng(r[1]) == (-400.0, 400.0))
cmds.animLayer(root, e=True, selected=False); cmds.animLayer(l1, e=True, selected=True, preferred=True)
r = GVM.resolve_layer_filter("selected"); check("range for selected Layer1 = [-200, 200] (the requested behaviour)", rng(r[1]) == (-200.0, 200.0), rng(r[1]))

# keep 모드 : GE 가 없으니 allAffecting 로 (outliner None)
check("keep without outliner -> allAffecting", GVM.resolve_layer_filter("keep", None)[0] == "allAffecting")
check("editor_layer_filter on missing control -> allAffecting", GVM.editor_layer_filter("noSuchOutlineEd") == "allAffecting")

# frame_around_current : GE 없음 -> (0, msg), 예외 없음 (모든 모드)
for mode in gvm.LAYER_FILTER_MODES:
    n, msg = GVM.frame_around_current(10, True, 10.0, layer_filter=mode)
    check("frame_around_current(%s) without GE -> 0, 'not open'" % mode, n == 0 and "not open" in msg, msg)

# GraphFocusManager 가 layer_getter 를 넘기는지 (frame 호출을 가로채서 확인)
from tools.A00110_animTool_V02.app.core.graph_focus_manager import GraphFocusManager   # noqa: E402
seen = {}
orig = GVM.frame_around_current
def spy(margin, fit_value=True, value_pad_pct=10.0, layer_filter="selected"):
    seen["layer_filter"] = layer_filter
    return (1, "spy")
GVM.frame_around_current = staticmethod(spy)
mgr = GraphFocusManager()
mgr._margin_getter = lambda: 80
mgr._layer_getter = lambda: "activeAndSelected"
mgr.apply_now()
check("GraphFocusManager passes layer_getter mode", seen.get("layer_filter") == "activeAndSelected", seen)
mgr._layer_getter = None
mgr.apply_now()
check("GraphFocusManager default mode = selected", seen.get("layer_filter") == "selected", seen)
GVM.frame_around_current = staticmethod(orig)

print("\n%d / %d passed" % (sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
