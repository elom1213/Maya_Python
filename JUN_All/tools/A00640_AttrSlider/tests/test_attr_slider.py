# -*- coding: utf-8 -*-
# A00640_AttrSlider v01.00 - 범위 규칙 · 나열 · 디코드 · 상태 · 쓰기 · UI 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_attr_slider.py
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00640_AttrSlider.app.core import ranges as RG   # noqa: E402
from tools.A00640_AttrSlider.app.core import attr_rows as AR   # noqa: E402
from tools.A00640_AttrSlider.app.ui import main_window as MW   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def close(a, b, eps=1e-6):
    return abs(float(a) - float(b)) < eps


# ---------------------------------------------------------------- 1. 범위 규칙 (마야 비의존)
check("1 user range wins", RG.resolve_range(5, 0, 1, user=(-3, 3))[:2] == (0.0, 1.0),
      "user range is clipped into hard limits")
check("1 user range (no hard)", RG.resolve_range(5, user=(-3, 30)) == (-3.0, 30.0, RG.SRC_USER))
check("1 hard both", RG.resolve_range(0.4, 0.0, 1.0) == (0.0, 1.0, RG.SRC_HARD))
check("1 soft before hard", RG.resolve_range(0.4, -10, 10, 0, 1)[2] == RG.SRC_SOFT)
check("1 soft both (blendShape weight)", RG.resolve_range(0.2, -10, 10, 0, 1) == (0.0, 1.0, RG.SRC_SOFT))
lo, hi, src = RG.resolve_range(15.0, hard_min=0.0)
check("1 min only (windSwingAngle 15, min 0) -> 0 ~ 30", (lo, hi, src) == (0.0, 30.0, RG.SRC_AUTO), (lo, hi))
lo, hi, _s = RG.resolve_range(0.5, hard_min=0.001)
check("1 min only small value -> span 10", close(lo, 0.001) and close(hi, 10.001), (lo, hi))
check("1 no range angle -> -180 ~ 180", RG.resolve_range(30, is_angle=True)[:2] == (-180.0, 180.0))
check("1 no range angle outside", RG.resolve_range(400, is_angle=True)[:2] == (-600.0, 600.0))
check("1 no range zero -> -10 ~ 10", RG.resolve_range(0.0)[:2] == (-10.0, 10.0))
check("1 no range 50 -> 0 ~ 100", RG.resolve_range(50.0)[:2] == (0.0, 100.0))
check("1 int rounds", RG.resolve_range(2.0, hard_min=0, is_int=True)[:2] == (0.0, 10.0)
      and RG.resolve_range(2.0, is_int=True, user=(0.4, 7.6))[:2] == (0.0, 8.0))
check("1 widen below", RG.widen(0, 10, -5) == (-6.0, 10))
check("1 widen respects hard min", RG.widen(0, 10, -5, hard_min=-2) == (-2.0, 10))
store = {"v": ""}
ur = RG.UserRanges(load=lambda: store["v"], save=lambda t: store.__setitem__("v", t))
ur.set("windSwingAngle", 0, 90)
ur2 = RG.UserRanges(load=lambda: store["v"])
check("1 user ranges persist", ur2.get("windSwingAngle") == (0.0, 90.0), store["v"])
try:
    ur.set("x", 5, 1)
    bad = False
except ValueError:
    bad = True
check("1 user range rejects max <= min", bad)
check("1 user range remove", ur.remove("windSwingAngle") and RG.UserRanges(load=lambda: store["v"]).get(
    "windSwingAngle") is None)


# ---------------------------------------------------------------- 2. 씬
def lite_driver(name):
    """A00390 V03 Chain Wave Lite 드라이버와 같은 모양(wave_lite_manager._make_lite_driver)."""
    drv = cmds.spaceLocator(name=name)[0]
    for attr, val, mn in (("windSwingAngle", 15.0, None), ("windWavelength", 10.0, 0.001),
                          ("windPeriod", 2.0, 0.001), ("windRootRamp", 0.0, 0.0)):
        kw = {"longName": attr, "attributeType": "double", "defaultValue": val, "keyable": True}
        if mn is not None:
            kw["minValue"] = mn
        cmds.addAttr(drv, **kw)
    cmds.addAttr(drv, longName="windSpeed", attributeType="double", defaultValue=1.0, keyable=True)
    cmds.addAttr(drv, longName="windEnvelope", attributeType="double", defaultValue=1.0, minValue=0, maxValue=1,
                 keyable=True)
    cmds.addAttr(drv, longName="windTipFollow", attributeType="double", defaultValue=0.5, minValue=0,
                 maxValue=0.99, keyable=True)
    cmds.addAttr(drv, longName="windPhaseTime", attributeType="double", keyable=True)
    t = cmds.createNode("multDoubleLinear")
    cmds.connectAttr(t + ".output", drv + ".windPhaseTime")
    return drv


cmds.file(new=True, force=True)
drv = lite_driver("a0_liteDriver1")
JP = u"まばたき"
ENC = "FBXASC227FBXASC129FBXASC190FBXASC227FBXASC129FBXASC176FBXASC227FBXASC129FBXASC159FBXASC227FBXASC129FBXASC141"
cmds.addAttr(drv, longName=ENC, attributeType="double", keyable=True)
cmds.addAttr(drv, longName="mode", attributeType="enum", enumName=ENC + ":B=5:C", keyable=True)
cmds.addAttr(drv, longName="flag", attributeType="bool", keyable=True)
cmds.addAttr(drv, longName="count", attributeType="long", defaultValue=3, minValue=0, keyable=True)
cmds.addAttr(drv, longName="cbOnly", attributeType="double", defaultValue=2)
cmds.setAttr(drv + ".cbOnly", channelBox=True)
cmds.addAttr(drv, longName="hiddenK", attributeType="double", keyable=True, hidden=True)
cmds.addAttr(drv, longName="note", dataType="string")
cmds.addAttr(drv, longName="vec", attributeType="double3", keyable=True)
for ax in "XYZ":
    cmds.addAttr(drv, longName="vec" + ax, attributeType="double", parent="vec", keyable=True)

secs, dropped = AR.build_sections([drv])
names = [r.raw_name for r in secs[0].rows]
check("2 one node section (locator shape has no channel box attrs except keyables?)",
      secs[0].kind == AR.SEC_NODE and secs[0].node.endswith(drv), [(s.kind, s.node) for s in secs])
check("2 liteDriver attrs listed", all(a in names for a in ("windSwingAngle", "windWavelength", "windEnvelope",
                                                             "windTipFollow", "windPhaseTime")), names)
check("2 transform channels listed", names[:10] == ["visibility", "translateX", "translateY", "translateZ",
                                                    "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"],
      names[:10])
check("2 channelBox (non-keyable) included", "cbOnly" in names)
check("2 hidden / string / compound parent excluded",
      not any(a in names for a in ("hiddenK", "note", "vec")) and "vecX" in names, names)
row = {r.raw_name: r for r in secs[0].rows}
check("2 kinds", (row["flag"].kind, row["mode"].kind, row["count"].kind, row["windSpeed"].kind)
      == (AR.KIND_BOOL, AR.KIND_ENUM, AR.KIND_INT, AR.KIND_FLOAT))
check("2 angle type", row["rotateX"].is_angle and not row["translateX"].is_angle)
check("2 hard range read", (row["windEnvelope"].hard_min, row["windEnvelope"].hard_max) == (0.0, 1.0)
      and row["windSwingAngle"].hard_min is None and row["windWavelength"].hard_min == 0.001)

# 디코드
check("3 FBXASC attr decoded (nice + long)", row[ENC].nice_name == JP and row[ENC].long_name == JP,
      (row[ENC].nice_name, row[ENC].long_name))
check("3 nice name for plain attr", row["windSwingAngle"].nice_name == "Wind Swing Angle"
      and row["windSwingAngle"].long_name == "windSwingAngle")
check("3 enum items decoded with Maya values", row["mode"].items == [(JP, 0), ("B", 5), ("C", 6)], row["mode"].items)
enc_node = cmds.rename(cmds.spaceLocator()[0], ENC + "_liteDriver")
secs_e, _d = AR.build_sections([enc_node])
check("3 node label decoded", secs_e[0].label == JP + "_liteDriver", secs_e[0].label)

# 블렌드셰이프
base = cmds.polyCube(name="face")[0]
tgt = cmds.polyCube(name=ENC)[0]
tgt2 = cmds.polyCube(name="smile")[0]
bs = cmds.blendShape(tgt, tgt2, base, name="faceBS")[0]
secs_b, _d = AR.build_sections([bs])
bs_names = [r.raw_name for r in secs_b[0].rows]
check("4 blendShape node -> envelope + targets", secs_b[0].kind == AR.SEC_BLENDSHAPE
      and bs_names == ["envelope", ENC, "smile"], bs_names)
trow = secs_b[0].rows[1]
check("4 target decoded + plug weight[i]", trow.nice_name == JP and trow.plug.endswith("faceBS.weight[0]"),
      (trow.nice_name, trow.plug))
check("4 target range = soft 0~1", RG.resolve_range(0, trow.hard_min, trow.hard_max, trow.soft_min,
                                                    trow.soft_max)[:2] == (0.0, 1.0),
      (trow.hard_min, trow.hard_max, trow.soft_min, trow.soft_max))
secs_m, _d = AR.build_sections([base])
check("4 mesh -> node + shape + blendShape sections",
      [s.kind for s in secs_m] == [AR.SEC_NODE, AR.SEC_SHAPE, AR.SEC_BLENDSHAPE] or
      [s.kind for s in secs_m] == [AR.SEC_NODE, AR.SEC_BLENDSHAPE], [(s.kind, s.raw_label) for s in secs_m])
secs_m2, _d = AR.build_sections([base], include_shapes=False, include_blendshapes=False)
check("4 options off -> node only", [s.kind for s in secs_m2] == [AR.SEC_NODE])
secs_d, _d = AR.build_sections([base, bs])
check("4 same blendShape once", sum(1 for s in secs_d if s.kind == AR.SEC_BLENDSHAPE) == 1)
many = [cmds.spaceLocator()[0] for _ in range(AR.MAX_NODES + 3)]
secs_x, dropped = AR.build_sections(many, include_shapes=False)
check("4 max nodes", len(secs_x) == AR.MAX_NODES and dropped == 3, (len(secs_x), dropped))

# 상태
cmds.setKeyframe(drv, attribute="windSpeed", time=1, value=1)
cmds.setKeyframe(drv, attribute="windSpeed", time=10, value=3)
ctl = cmds.spaceLocator(name="ctl")[0]
cmds.setDrivenKeyframe(drv + ".windPeriod", currentDriver=ctl + ".ty", driverValue=0, value=2)
cmds.setAttr(drv + ".windRootRamp", lock=True)
lay_obj = cmds.spaceLocator(name="layered")[0]
cmds.setKeyframe(lay_obj, attribute="tx", time=1, value=1)
lay = cmds.animLayer("L1")
cmds.animLayer(lay, edit=True, attribute=lay_obj + ".tx")
secs, _d = AR.build_sections([drv, lay_obj], include_shapes=False)
row = {r.plug.split("|")[-1]: r for s in secs for r in s.rows}
check("5 keyed", row["a0_liteDriver1.windSpeed"].state == AR.ST_KEYED)
check("5 layer = keyed", row["layered.translateX"].state == AR.ST_KEYED, row["layered.translateX"].source)
check("5 driven key = driven", row["a0_liteDriver1.windPeriod"].state == AR.ST_DRIVEN)
check("5 connection = driven", row["a0_liteDriver1.windPhaseTime"].state == AR.ST_DRIVEN)
check("5 locked", row["a0_liteDriver1.windRootRamp"].state == AR.ST_LOCKED)
check("5 free", row["a0_liteDriver1.windSwingAngle"].state == AR.ST_FREE)

# 쓰기
r = row["a0_liteDriver1.windWavelength"]
check("6 clamp to hard min", AR.set_value(r, -5) == 0.001 and close(cmds.getAttr(r.plug), 0.001))
r = row["a0_liteDriver1.windEnvelope"]
check("6 clamp to hard max", AR.set_value(r, 3) == 1.0)
r = [x for s in secs for x in s.rows if x.raw_name == "count"][0]
check("6 int rounds", AR.set_value(r, 4.6) == 5 and cmds.getAttr(r.plug) == 5)
try:
    AR.set_value(row["a0_liteDriver1.windPhaseTime"], 3)
    refused = False
except RuntimeError:
    refused = True
check("6 driven refused", refused)
r = row["a0_liteDriver1.windSwingAngle"]
AR.set_value(r, 22.0, key=True)
check("6 auto key makes it keyed", r.state == AR.ST_KEYED and cmds.keyframe(r.plug, q=True, kc=True) == 1)


# ---------------------------------------------------------------- 7. UI
cmds.file(new=True, force=True)
for k in (MW.OPTVAR_RANGES, MW.OPTVAR_AUTOKEY, MW.OPTVAR_NAMES, MW.OPTVAR_SHAPES, MW.OPTVAR_BLENDSHAPES):
    if cmds.optionVar(exists=k):
        cmds.optionVar(remove=k)
drv = lite_driver("b0_liteDriver1")
cmds.addAttr(drv, longName=ENC, attributeType="double", keyable=True)
base = cmds.polyCube(name="face")[0]
tgt = cmds.polyCube(name=ENC)[0]
bs = cmds.blendShape(tgt, base, name="faceBS")[0]
cmds.select(drv)
win = MW.MainWindow()
win.show()
APP.processEvents()


def rw(name, w=None):
    w = w or win
    for x in w.row_widgets():
        if x.row.raw_name == name:
            return x
    return None


check("7 selection -> driver section + its shape (Channel Box SHAPES)",
      [s.section.kind for s in win.sections] == [AR.SEC_NODE, AR.SEC_SHAPE], [s.section.node for s in win.sections])
sw = rw("windSwingAngle")
check("7 swing slider range 0~30", (sw.lo, sw.hi) == (0.0, 30.0), (sw.lo, sw.hi, sw.range_source))
check("7 FBXASC label decoded", rw(ENC).label.text() == JP)
from Framework.qt import MOD_sliderStyle_qt_v01 as SS   # noqa: E402
check("7 sliders themed (shared slider style)", bool(sw.slider.property(SS.STYLED_PROPERTY)))
sw.slider.setValue(500)          # 드래그가 아닌 값 변경 (클릭 = 페이지 스텝과 같은 경로)
check("7 slider -> scene", close(cmds.getAttr(drv + ".windSwingAngle"), 15.0), cmds.getAttr(drv + ".windSwingAngle"))
# 드래그 한 번 = undo 한 번
cmds.undoInfo(state=True)
cmds.flushUndo()
before = cmds.getAttr(drv + ".windSwingAngle")
win.begin_drag(sw)
for v in (600, 700, 800, 900):
    sw.slider.setSliderDown(True)
    sw.slider.setValue(v)
win.end_drag(sw)
sw.slider.setSliderDown(False)
after = cmds.getAttr(drv + ".windSwingAngle")
cmds.undo()
check("7 drag = one undo", close(after, 27.0) and close(cmds.getAttr(drv + ".windSwingAngle"), before),
      (before, after, cmds.getAttr(drv + ".windSwingAngle")))
# 숫자 칸 범위 밖 -> 범위 넓힘
sw.spin.setValue(50.0)
check("7 spin outside widens range", close(cmds.getAttr(drv + ".windSwingAngle"), 50.0) and sw.hi >= 50.0,
      (sw.lo, sw.hi))
env = rw("windEnvelope")
env.spin.setValue(0.25)
check("7 spin -> scene (hard range spin)", close(cmds.getAttr(drv + ".windEnvelope"), 0.25)
      and env.spin.maximum() == 1.0)
check("7 driven row disabled", not rw("windPhaseTime").slider.isEnabled())
# 사용자 범위 - 이름 기준, 다른 노드에도
check("7 set user range", win.set_user_range(sw, 0, 90) and (sw.lo, sw.hi) == (0.0, 90.0))
drv2 = lite_driver("c0_liteDriver1")
cmds.select(drv2)
win.rebuild_from_selection()
check("7 user range applies to another node", (rw("windSwingAngle").lo, rw("windSwingAngle").hi) == (0.0, 90.0))
win.clear_range(rw("windSwingAngle"))
check("7 reset range", (rw("windSwingAngle").lo, rw("windSwingAngle").hi) == (0.0, 30.0))
# 시간 변경 -> 값 다시 읽기
cmds.setKeyframe(drv2, attribute="windSpeed", time=1, value=1)
cmds.setKeyframe(drv2, attribute="windSpeed", time=11, value=5)
win.refresh_values()
check("7 keyed row color state", rw("windSpeed").row.state == AR.ST_KEYED)
cmds.currentTime(11)
win.refresh_values()
check("7 time change -> widget value", close(rw("windSpeed").spin.value(), 5.0), rw("windSpeed").spin.value())
# Auto Key
win.chk_autokey.setChecked(True)
rw("windWavelength").spin.setValue(4.0)
check("7 auto key on spin", cmds.keyframe(drv2 + ".windWavelength", q=True, kc=True) == 1
      and rw("windWavelength").row.state == AR.ST_KEYED)
win.chk_autokey.setChecked(False)
# 불리언 · enum 위젯
cmds.addAttr(drv2, longName="mode", attributeType="enum", enumName=ENC + ":B=5:C", keyable=True)
cmds.addAttr(drv2, longName="flag", attributeType="bool", keyable=True)
win.refresh_list()
m = rw("mode")
check("7 enum combo decoded", [m.combo.itemText(i) for i in range(m.combo.count())] == [JP, "B", "C"])
m.combo.setCurrentIndex(1)
m._on_combo(1)
check("7 enum -> scene value 5", cmds.getAttr(drv2 + ".mode") == 5)
rw("flag").check.setChecked(True)
check("7 bool -> scene", cmds.getAttr(drv2 + ".flag") is True)
# Filter
win.ed_filter.setText("wave")
APP.processEvents()
vis = [x.row.raw_name for x in win.row_widgets() if x.isVisibleTo(win)]
check("7 filter by nice/long name", vis == ["windWavelength"], vis)
win.ed_filter.setText(u"まば")
cmds.select(drv)
win.rebuild_from_selection()
vis = [x.row.raw_name for x in win.row_widgets() if x.isVisibleTo(win)]
check("7 filter by decoded text", vis == [ENC], vis)
win.ed_filter.setText("")
# Lock List
win.btn_lock.setChecked(True)
cmds.select(base)
win._on_selection()
APP.processEvents()
win.rebuild_from_selection()
check("7 lock list ignores selection", [s.section.node.split("|")[-1] for s in win.sections] == ["b0_liteDriver1", "b0_liteDriver1Shape"])
win.btn_lock.setChecked(False)
APP.processEvents()
check("7 unlock follows selection (mesh -> node/shape/blendShape)",
      AR.SEC_BLENDSHAPE in [s.section.kind for s in win.sections], [s.section.kind for s in win.sections])
t = [x for x in win.row_widgets() if x.row.target_index == 0][0]
check("7 target label decoded + gauge 0~1", t.label.text() == JP and (t.lo, t.hi) == (0.0, 1.0))
t.slider.setValue(1000)
check("7 target slider -> weight", close(cmds.getAttr(bs + ".weight[0]"), 1.0))
# 이름 모드
win.set_name_mode(AR.NAMES_LONG)
check("7 long names", rw("translateX").label.text() == "translateX")
win.set_name_mode(AR.NAMES_NICE)
check("7 nice names", rw("translateX").label.text() == "Translate X")
# 접기
win.sections[0].header.setChecked(False)
check("7 fold hides rows", not any(x.isVisibleTo(win) for x in win.sections[0].rows))
n_jobs = len(win._jobs)
win.close()
check("7 scriptJobs killed on close", n_jobs >= 4 and not any(cmds.scriptJob(exists=j) for j in win._jobs + [])
      and win._jobs == [], n_jobs)

print("\n{0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
