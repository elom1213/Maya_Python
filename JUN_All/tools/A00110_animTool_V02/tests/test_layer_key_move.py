# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.28 - Transfer > Layer `Cut Keys to Layer (Move)` 최종값 보존 회귀 시험 (mayapy, 헤드리스)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_layer_key_move.py     (약 30초)
#
# 관찰(2026-10-29): ctl 이 Base 에만 키가 있을 때 Base -> a 로 Move 하면 월드 위치·회전이 달라진다.
# 원인: 커브를 다 지우면 blend 노드 입력(inputA / inputB)에 마지막 값이 정적으로 남는다 + 대상의 정적값이 덮인다.
# 판정: ctl 의 worldMatrix 를 반 프레임 간격으로 Move 전후 비교(keep_result=True 기본). keep_result=False 는 예전 동작(어긋남).
import math
import os
import sys

# QApplication 은 maya.standalone.initialize() 보다 먼저 (qapplication-before-maya-standalone). UI 스모크용.
os.environ["QT_QPA_PLATFORM"] = "offscreen"
try:
    from PySide2.QtWidgets import QApplication
    APP = QApplication.instance() or QApplication(sys.argv)
except Exception:
    APP = None

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00110_animTool_V02.app.core.layer_key_manager import LayerKeyManager as LKM   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


TR = ["tx", "ty", "tz", "rx", "ry", "rz"]
ALL9 = TR + ["sx", "sy", "sz"]
FLAGS = {k: True for k in ALL9}
HALF = [t * 0.5 for t in range(0, 41)]
INT = list(range(0, 21))
TOL = 1e-6


def world(obj, times=HALF):
    out = []
    for t in times:
        cmds.currentTime(t)
        out.append(cmds.xform(obj, q=True, ws=True, m=True))
    return out


def maxdiff(a, b):
    return max(abs(x - y) for ma, mb in zip(a, b) for x, y in zip(ma, mb))


def values(plug, times=HALF):
    return [cmds.getAttr(plug, t=t) for t in times]


def build(base_keys=True, layers=("a", "b"), override=(), rot_mode=0, scale_mode=1, scale=False,
          key_layer=None, base_static=None, joint=False, custom=False, skip_member=()):
    """grp(1,2,3 / 10,20,30) > ctl. Base 키 0..20 step 5(base_keys) 또는 정적값(base_static). 레이어 a, b 멤버
    (skip_member 에 든 레이어는 멤버로 넣지 않는다 - 키 없는 override 멤버는 정적값으로 아래를 전부 덮으므로)."""
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=0, max=20)
    grp = cmds.createNode("transform", n="grp")
    cmds.setAttr(grp + ".t", 1, 2, 3)
    cmds.setAttr(grp + ".r", 10, 20, 30)
    if joint:
        cmds.select(clear=True)
        ctl = cmds.joint(n="ctl")
        cmds.parent(ctl, grp)
        cmds.setAttr(ctl + ".jointOrient", 15, -25, 40)
        cmds.setAttr(ctl + ".rotateOrder", 3)
    else:
        ctl = cmds.createNode("transform", n="ctl", p=grp)
    attrs = list(ALL9 if scale else TR)
    if custom:
        cmds.addAttr(ctl, ln="ikBlend", at="double", k=True, min=0, max=10)
        attrs.append("ikBlend")
    if base_keys:
        for i, t in enumerate(range(0, 21, 5)):
            for j, a in enumerate(attrs):
                v = math.sin(i + j) * (40 if a[0] == "r" else 5)
                if a[0] == "s":
                    v = 1.0 + 0.3 * math.sin(i + j)
                if a == "ikBlend":
                    v = 5 + 4 * math.sin(i)
                cmds.setKeyframe(ctl, at=a, t=t, v=v)
    if base_static:
        for a, v in zip(attrs, base_static):
            cmds.setAttr(ctl + "." + a, v)
    lyrs = []
    for n in layers:
        l = cmds.animLayer(n)
        cmds.setAttr(l + ".rotationAccumulationMode", rot_mode)
        cmds.setAttr(l + ".scaleAccumulationMode", scale_mode)
        if n in override:
            cmds.setAttr(l + ".override", 1)
        if n not in skip_member:
            for a in attrs:
                cmds.animLayer(l, e=True, at=ctl + "." + a)
        lyrs.append(l)
    if key_layer:
        for i, t in enumerate(range(0, 21, 4)):
            for j, a in enumerate(attrs):
                v = math.cos(i + j) * (20 if a[0] == "r" else 2)
                if a[0] == "s":
                    v = 1.0 + 0.2 * math.cos(i + j)
                if a == "ikBlend":
                    v = 1 + math.cos(i)
                cmds.setKeyframe(ctl, at=a, t=t, v=v, animLayer=key_layer)
    cmds.currentTime(7)
    return ctl, lyrs


def chain_tx(ctl):
    return LKM._blend_chain(ctl + ".tx")


# ==================================================
# 1. 사용자 관찰 : Base 에만 키 -> a / b 로 Move
# ==================================================
print("\n--- 1. base-only ctl, Move Base -> a / b ---")
for dst_name in ("a", "b"):
    ctl, lyrs = build()
    before = world(ctl)
    n, msg = LKM.transfer_keys([ctl], "BaseAnimation", dst_name, FLAGS, cut=True, keep_result=False)
    raw = maxdiff(before, world(ctl))
    check("Base -> %s raw move drifts (observation is real)" % dst_name, raw > 0.5, raw)

    ctl, lyrs = build()
    before = world(ctl)
    n, msg = LKM.transfer_keys([ctl], "BaseAnimation", dst_name, FLAGS, cut=True)
    check("Base -> %s keep_result world exact" % dst_name, maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))
    check("Base -> %s log says kept 6" % dst_name, "Result kept on 6 channel(s)" in msg and "Not exact" not in msg, msg)
    check("Base -> %s base input is identity" % dst_name,
          abs(cmds.getAttr(chain_tx(ctl)[-1][0] + ".inputA")) < 1e-12)
    check("Base -> %s base curve gone" % dst_name, LKM.layer_curve(ctl + ".tx", "BaseAnimation") is None)

# ==================================================
# 2. a -> b / a -> Base (base 정적값 0 아님)
# ==================================================
print("\n--- 2. a keyed + base static, Move a -> b / a -> Base ---")
ctl, (a, b) = build(base_keys=False, key_layer="a", base_static=[1, 2, 3, 10, 20, 30])
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, b, FLAGS, cut=True, keep_result=False)
check("a -> b raw move drifts", maxdiff(before, world(ctl)) > 0.5)

ctl, (a, b) = build(base_keys=False, key_layer="a", base_static=[1, 2, 3, 10, 20, 30])
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, b, FLAGS, cut=True)
check("a -> b keep_result world exact", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))
check("a -> b: a still a member", any(nd in LKM._layer_nodes(a) for nd, _ in chain_tx(ctl)))

ctl, (a, b) = build(base_keys=False, key_layer="a", base_static=[1, 2, 3, 10, 20, 30])
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, "BaseAnimation", FLAGS, cut=True)
check("a -> Base keep_result world exact (by-component, static folded in)", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))
check("a -> Base base curve exists", LKM.layer_curve(ctl + ".tx", "BaseAnimation") is not None)

# base + a 둘 다 키, a -> b
ctl, (a, b) = build(base_keys=True, key_layer="a")
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, b, FLAGS, cut=True)
check("base keyed + a keyed, a -> b exact", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))

# ==================================================
# 3. by-layer 회전 · multiply / additive 스케일
# ==================================================
print("\n--- 3. by-layer rotation, scale modes ---")
for smode in (0, 1):
    ctl, (a, b) = build(rot_mode=1, scale_mode=smode, scale=True)
    before = world(ctl)
    n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True)
    check("by-layer rot + scale mode %d, Base -> a exact (9 ch)" % smode, maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))
    check("scale mode %d log clean" % smode, "Result kept on 9" in msg and "Not exact" not in msg, msg)
    sx_in = [nd for nd, _ in LKM._blend_chain(ctl + ".sx")][-1] + ".inputA"
    check("scale mode %d base identity = %s" % (smode, 1.0 if smode else 0.0),
          abs(cmds.getAttr(sx_in) - (1.0 if smode else 0.0)) < 1e-12, cmds.getAttr(sx_in))

    ctl, (a, b) = build(base_keys=False, key_layer="a", scale=True, scale_mode=smode,
                        base_static=[1, 2, 3, 0, 0, 0, 1.5, 0.8, 1.2])
    before = world(ctl)
    n, msg = LKM.transfer_keys([ctl], a, "BaseAnimation", FLAGS, cut=True)
    check("scale mode %d, a -> Base with static scale folded (mul/add)" % smode, maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))

ctl, (a, b) = build(base_keys=False, key_layer="a", rot_mode=1, base_static=[1, 2, 3, 10, 20, 30])
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, "BaseAnimation", FLAGS, cut=True)
check("by-layer rot + non-zero base rot, a -> Base: warned", "rotation not exact" in msg, msg)
check("by-layer rot + non-zero base rot, a -> Base: translate still exact",
      max(abs(x - y) for ma, mb in zip(before, world(ctl)) for x, y in zip(ma[12:15], mb[12:15])) < 0.5)

# ==================================================
# 4. override 레이어
# ==================================================
print("\n--- 4. override layers ---")
ctl, (a, b) = build(base_keys=False, key_layer="a", override=("a",), base_static=[1, 2, 3, 10, 20, 30])
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, b, FLAGS, cut=True)
check("override a -> additive b exact (below folded out)", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))
check("override a -> b: plug removed from a", not any(nd in LKM._layer_nodes(a) for nd, _ in chain_tx(ctl)))

# override 대상은 **아직 멤버가 아닌** 채널만 뜻이 있다 (키 없는 override 멤버는 정적값으로 아래를 전부 덮는다)
ctl, (a, b) = build(override=("a",), skip_member=("a",))
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True)
check("Base -> override a (new member) exact", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))

ctl, (a, b) = build(base_keys=False, key_layer="a", override=("b",), base_static=[1, 2, 3, 10, 20, 30], skip_member=("b",))
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, b, FLAGS, cut=True)
check("additive a -> override b (new member) exact (static below folded in)", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))

ctl, (a, b) = build(base_keys=False, key_layer="a", override=("a", "b"), base_static=[1, 2, 3, 10, 20, 30], skip_member=("b",))
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, b, FLAGS, cut=True)
check("override a -> override b (new member) exact", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))

# 키 없는 override 멤버로 옮기면 "이동 전" 이 그 정적값 상수였다 -> 경고
ctl, (a, b) = build(override=("a",))
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True)
check("Base -> override a (static member): warned", "already overrides" in msg, msg)

# ==================================================
# 5. 구간 이동 (Limit to Time Range)
# ==================================================
print("\n--- 5. ranged move ---")


def ranged_checks(label, ctl, before, s, e):
    after = world(ctl)
    ints = [i for i, t in enumerate(HALF) if t == int(t)]
    outside = [i for i, t in enumerate(HALF) if t <= s - 1 or t >= e + 1]
    inside = [i for i, t in enumerate(HALF) if s <= t <= e]
    d_int = maxdiff([before[i] for i in ints], [after[i] for i in ints])
    d_out = maxdiff([before[i] for i in outside], [after[i] for i in outside])
    d_in = maxdiff([before[i] for i in inside], [after[i] for i in inside])
    check(label + ": integer frames exact", d_int < TOL, d_int)
    check(label + ": outside range exact at half frames", d_out < TOL, d_out)
    check(label + ": inside range exact at half frames", d_in < TOL, d_in)


ctl, (a, b) = build()
cmds.keyTangent(ctl, e=True, itt="auto", ott="auto")
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True, start=5, end=15, keep_result=False)
check("ranged raw drifts", maxdiff(before, world(ctl)) > 0.5)

ctl, (a, b) = build()
cmds.keyTangent(ctl, e=True, itt="auto", ott="auto")
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True, start=5, end=15)
ranged_checks("Base -> a 5..15", ctl, before, 5, 15)
bc = LKM.layer_curve(ctl + ".tx", "BaseAnimation")
ac = LKM.layer_curve(ctl + ".tx", a)
check("ranged: base keys = 0,4,5,15,16,20", sorted(cmds.keyframe(bc, q=True, tc=True)) == [0.0, 4.0, 5.0, 15.0, 16.0, 20.0], cmds.keyframe(bc, q=True, tc=True))
check("ranged: a keys = 4,5,10,15,16", sorted(cmds.keyframe(ac, q=True, tc=True)) == [4.0, 5.0, 10.0, 15.0, 16.0], cmds.keyframe(ac, q=True, tc=True))
check("ranged: base identity in range", all(abs(v) < 1e-12 for v in cmds.keyframe(bc, q=True, time=(5, 15), vc=True)))
check("ranged: log", "Result kept on 6" in msg and "Not exact" not in msg, msg)

# 구간이 앞쪽 끝을 포함 (앞에 키 없음)
ctl, (a, b) = build()
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True, start=0, end=10)
ranged_checks("Base -> a 0..10 (no key before)", ctl, before, 0, 10)

# a -> b 구간, a 는 밖에 키 남음, base 정적
ctl, (a, b) = build(base_keys=False, key_layer="a", base_static=[1, 2, 3, 10, 20, 30])
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, b, FLAGS, cut=True, start=4, end=12)
ranged_checks("a -> b 4..12", ctl, before, 4, 12)

# a -> Base 구간 (base 정적값이 밖에서도 유지돼야 한다)
ctl, (a, b) = build(base_keys=False, key_layer="a", base_static=[1, 2, 3, 10, 20, 30])
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], a, "BaseAnimation", FLAGS, cut=True, start=8, end=16)
ranged_checks("a -> Base 8..16", ctl, before, 8, 16)

# 구간이 모든 키를 덮으면 커브가 사라지고 정적 identity 경로
ctl, (a, b) = build()
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True, start=0, end=20)
check("ranged covering all keys exact", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))
check("ranged covering all keys: base curve gone", LKM.layer_curve(ctl + ".tx", "BaseAnimation") is None)

# override 소스 구간 -> 거부(경고), 값은 raw
ctl, (a, b) = build(base_keys=False, key_layer="a", override=("a",), base_static=[1, 2, 3, 10, 20, 30])
n, msg = LKM.transfer_keys([ctl], a, b, FLAGS, cut=True, start=4, end=12)
check("override source ranged: warned", "override layer with keys outside the range" in msg, msg)

# ==================================================
# 6. 기타 : 비멤버 · 커스텀 채널 · 조인트 · 다중 오브젝트 · undo · Copy 불변 · 경고들
# ==================================================
print("\n--- 6. misc ---")
cmds.file(new=True, force=True)
ctl = cmds.createNode("transform", n="ctl")
for i, t in enumerate(range(0, 21, 5)):
    for j, at in enumerate(TR):
        cmds.setKeyframe(ctl, at=at, t=t, v=math.sin(i + j) * (30 if at[0] == "r" else 5))
a = cmds.animLayer("a")
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True)
check("non-member plug Base -> a exact (membership added)", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))

ctl, (a, b) = build(custom=True)
before_v = values(ctl + ".ikBlend")
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, custom_attrs=["ikBlend"], cut=True)
check("custom attr Base -> a exact", max(abs(x - y) for x, y in zip(before_v, values(ctl + ".ikBlend"))) < TOL)
check("custom attr + TR, log kept 7", "Result kept on 7" in msg, msg)

ctl, (a, b) = build(joint=True, rot_mode=1)
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True)
check("joint (jointOrient, rotateOrder xzy) Base -> a exact", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))

# 부모-자식 두 오브젝트를 한 번에 (둘 다 Base 키) - 자식의 월드는 부모 이동 결과까지 포함
ctl, (a, b) = build()
child = cmds.createNode("transform", n="child", p=ctl)
for i, t in enumerate(range(0, 21, 5)):
    for j, at in enumerate(TR):
        cmds.setKeyframe(child, at=at, t=t, v=math.cos(i + j) * (30 if at[0] == "r" else 3))
for at in TR:
    cmds.animLayer(a, e=True, at=child + "." + at)
before = world(child)
n, msg = LKM.transfer_keys([ctl, child], "BaseAnimation", a, FLAGS, cut=True)
check("parent + child both moved, child world exact", maxdiff(before, world(child)) < TOL, maxdiff(before, world(child)))
check("two objects, 12 channels kept", "Result kept on 12" in msg, msg)

# undo 한 번에 복귀
ctl, (a, b) = build()
before = world(ctl)
cmds.undoInfo(state=True, infinity=True)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True)
cmds.undo()
check("undo restores base curve", LKM.layer_curve(ctl + ".tx", "BaseAnimation") is not None)
check("undo restores world", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))

# Copy 는 그대로 (값 그대로 복사 = Base -> a 는 두 배)
ctl, (a, b) = build()
before = world(ctl)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=False)
check("Copy unchanged: no keep in log", "Result kept" not in msg, msg)
check("Copy unchanged: doubles (raw)", maxdiff(before, world(ctl)) > 0.5)

# 대상에 이미 키 -> 경고
ctl, (a, b) = build(base_keys=True, key_layer="a")
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True)
check("destination already keyed: warned", "destination already has keys" in msg, msg)

# weight != 1 -> 경고
ctl, (a, b) = build()
cmds.setAttr(a + ".weight", 0.5)
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, cut=True)
check("weight 0.5: warned", "weight is 0.5" in msg, msg)

# visibility (boolean blend) -> 경고, 에러 없음
ctl, (a, b) = build()
for t, v in ((0, 1), (10, 0), (20, 1)):
    cmds.setKeyframe(ctl, at="visibility", t=t, v=v)
cmds.animLayer(a, e=True, at=ctl + ".visibility")
n, msg = LKM.transfer_keys([ctl], "BaseAnimation", a, FLAGS, custom_attrs=["visibility"], cut=True)
check("visibility: non-numeric warned, TR kept", "non-numeric" in msg and "Result kept on 6" in msg, msg)

# ==================================================
# 7. UI 스모크 (offscreen) : Keep Result 체크박스 기본 ON, on_lk_transfer 가 keep_result 를 넘긴다
# ==================================================
print("\n--- 7. UI smoke ---")
try:
    from tools.A00110_animTool_V02.app.ui.main_window import MainWindow
    ctl, (a, b) = build()
    before = world(ctl)
    win = MainWindow()
    check("UI: Keep Result checkbox default ON", win.cb_lk_keep.isChecked() and win.cb_lk_keep.text() == "Keep Result")
    win.on_lk_refresh_layers(quiet=True)
    win.cmb_lk_src.setCurrentText("BaseAnimation")
    win.cmb_lk_dst.setCurrentText("a")
    win.layer_tsl.set_items([ctl])
    win.on_lk_transfer(cut=True)
    check("UI: Move via on_lk_transfer keeps world", maxdiff(before, world(ctl)) < TOL, maxdiff(before, world(ctl)))
    win.cb_lk_keep.setChecked(False)
    ctl, (a, b) = build()
    before = world(ctl)
    win.layer_tsl.set_items([ctl])
    win.on_lk_transfer(cut=True)
    check("UI: Keep Result off = raw move (drifts)", maxdiff(before, world(ctl)) > 0.5)
    win.close()
except Exception as ex:
    check("UI smoke", False, repr(ex))

print("\n==== %d / %d passed ====" % (sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
