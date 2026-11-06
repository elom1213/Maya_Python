# -*- coding: utf-8 -*-
# A00390_WindTool_V03 v03.06 - Chain Wave Lite 의 Tip Follow 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_lite_tip_follow.py
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication  # noqa: E402
APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone  # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
from tools.A00390_WindTool_V03.app.core import wave_lite_manager as lm  # noqa: E402
from tools.A00390_WindTool_V03.app.core import wind_manager as wm  # noqa: E402
from tools.A00390_WindTool_V03.app.core import flow_model as fm  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def chain(x, n=9, name="c", parent=None, joints=True):
    cmds.select(clear=True)
    if joints:
        js = [cmds.joint(p=(x, 10 - k * 1.2, 0.15 * k), name="{0}{1}".format(name, k)) for k in range(n)]
        cmds.joint(js[0], e=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
    else:
        js, prev = [], None
        for k in range(n):
            t = cmds.createNode("transform", name="{0}{1}".format(name, k), parent=prev)
            cmds.xform(t, ws=True, t=(x, 10 - k * 1.2, 0.15 * k))
            js.append(t)
            prev = t
    if parent:
        cmds.parent(js[0], parent)
    return [cmds.ls(cmds.ls("{0}0".format(name))[0] if k == 0 else "{0}{1}".format(name, k), long=True)[0]
            for k in range(n)]


def wpos(js):
    return [cmds.xform(j, q=True, ws=True, t=True) for j in js]


def maxdist(a, b):
    return max(sum((p - q) ** 2 for p, q in zip(pa, pb)) ** 0.5 for pa, pb in zip(a, b))


def driver(tag):
    return [d for d in wm.all_wind_drivers() if tag + "_liteDriver" in d][0]


def tip_of(tag):
    return [t for t in cmds.ls("*" + lm.LITE_TIP_SUFFIX + "*", type="transform", long=True) if tag + lm.LITE_TIP_SUFFIX in t][0]


cmds.currentUnit(time="film")
common = dict(mode=wm.MODE_ROOT, axis="Z", swing=18.0, period=20.0, speed=1.0, ramp=1.0, debug_curve=False,
              flutter=4.0, flutter_stiffness=0.3)
FRAMES = (1, 6, 13, 27, 40)

# ---------------------------------------------------------------- 1. follow 0 = 예전 Lite (월드 축 · 오브젝트 축)
for local in (None, "Z"):
    cmds.file(new=True, force=True)
    A = chain(0, name="a")
    B = chain(3, name="b")
    lm.build_wave_lite([A[0]], prefix="old", local_axis=local, **common)
    lm.build_wave_lite([B[0]], prefix="tip0", local_axis=local, tip_follow=0.0, **common)
    off = [3.0, 0.0, 0.0]
    worst = 0.0
    for f in FRAMES:
        cmds.currentTime(f)
        pa = wpos(A)
        pb = [[p[0] - off[0], p[1], p[2]] for p in wpos(B)]
        worst = max(worst, maxdist(pa, pb))
    check("1 windTipFollow 0 = Lite without Tip Follow ({0})".format(local or "world axis"), worst < 1e-6,
          "max pos diff {0:.2e}".format(worst))

# ---------------------------------------------------------------- 2. 어트리뷰트 · Tip 위치
drv_b = driver("b0")
check("2 windTipFollow keyable, range 0-0.99",
      cmds.getAttr(drv_b + "." + lm.LITE_TIP_FOLLOW, keyable=True)
      and cmds.attributeQuery(lm.LITE_TIP_FOLLOW, node=drv_b, maximum=True)[0] == 0.99)
drv_a = driver("a0")
check("2 Tip Follow off: no attr, no tip", not cmds.objExists(drv_a + "." + lm.LITE_TIP_FOLLOW)
      and not [t for t in cmds.ls("*" + lm.LITE_TIP_SUFFIX + "*") if "a0" in t])

# ---------------------------------------------------------------- 3. Tip 을 옮기면 체인이 쫓는다
cmds.file(new=True, force=True)
C = chain(0, name="c")
quiet = dict(common, swing=0.0, flutter=0.0)         # 바람 없이 따라가기만 본다
lm.build_wave_lite([C[0]], prefix="tip", tip_follow=0.6, **quiet)
tip = tip_of("c0")
cmds.currentTime(5)
rest = wpos(C)
check("3 Tip at rest -> chain stays at rest", maxdist(rest, [[0, 10 - k * 1.2, 0.15 * k] for k in range(9)]) < 1e-4,
      maxdist(rest, [[0, 10 - k * 1.2, 0.15 * k] for k in range(9)]))
cmds.move(6.0, 0, 0, tip, relative=True, worldSpace=True)
moved = wpos(C)
end_dx = moved[-1][0] - rest[-1][0]
check("3 move Tip +6 X -> chain end follows +X", end_dx > 1.0, round(end_dx, 3))
check("3 root node stays put (only rotations)", maxdist([moved[0]], [rest[0]]) < 1e-6)
check("3 the further down the chain, the more it moves",
      all(moved[k + 1][0] - rest[k + 1][0] >= moved[k][0] - rest[k][0] - 1e-9 for k in range(8)),
      [round(m[0] - r[0], 2) for m, r in zip(moved, rest)])
drv_c = driver("c0")
cmds.setAttr(drv_c + "." + lm.LITE_TIP_FOLLOW, 0.0)
check("3 windTipFollow live -> 0: chain back to rest", maxdist(wpos(C), rest) < 1e-6)
cmds.setAttr(drv_c + "." + lm.LITE_TIP_FOLLOW, 0.9)
end_strong = wpos(C)[-1][0] - rest[-1][0]
check("3 stronger follow -> closer to the Tip", end_strong > end_dx, (round(end_dx, 3), round(end_strong, 3)))
ws = [1.0 - (1.0 - min(fm.FOLLOW_CAP, 0.9 * (1.0 - fm.FOLLOW_TIP_DROP * k / 8.0))) ** (fm.REF_BONES / 9) for k in range(9)]
check("3 weight rule = Flow (root strongest)", ws[0] > ws[-1] > 0, [round(w, 3) for w in ws[::4]])

# ---------------------------------------------------------------- 4. 바람 + 따라가기, envelope 보정
cmds.file(new=True, force=True)
D = chain(0, name="d")
E = chain(3, name="e")
lm.build_wave_lite([D[0]], prefix="wind", **common)
lm.build_wave_lite([E[0]], prefix="windTip", tip_follow=0.5, **common)
drv_e = driver("e0")
gain_node = [n for n in cmds.ls("e0_liteTip_gain*") if cmds.nodeType(n) == "multiplyDivide"]
check("4 effective envelope = windEnvelope / (1 - 0.7 * follow)",
      gain_node and abs(cmds.getAttr(gain_node[0] + ".outputX") - 1.0 / (1.0 - fm.FOLLOW_GAIN * 0.5)) < 1e-6,
      (gain_node, gain_node and cmds.getAttr(gain_node[0] + ".outputX")))
moving = 0.0
for f in FRAMES:
    cmds.currentTime(f)
    moving = max(moving, maxdist(wpos(E), [[3, 10 - k * 1.2, 0.15 * k] for k in range(9)]))
check("4 the wind still waves with Tip Follow on", moving > 0.5, round(moving, 3))
cmds.setAttr(drv_e + ".windEnvelope", 0.0)
check("4 envelope 0 + Tip at rest -> rest pose", maxdist(wpos(E), [[3, 10 - k * 1.2, 0.15 * k] for k in range(9)]) < 1e-4)
cmds.setAttr(drv_e + ".windEnvelope", 1.0)
check("4 no cycle in the network", not (cmds.cycleCheck(E[-1] + ".rotate", list=True) or []))

# ---------------------------------------------------------------- 5. Tip 은 루트의 부모 아래 - 리그와 같이 움직인다
cmds.file(new=True, force=True)
grp = cmds.createNode("transform", name="rig")
F = chain(0, name="f", parent=grp)
lm.build_wave_lite([F[0]], prefix="rig", tip_follow=0.7, **quiet)
tip = tip_of("f0")
check("5 Tip parented under the root's parent", cmds.listRelatives(tip, parent=True, fullPath=True)[0] == "|rig")
cmds.currentTime(3)
before = wpos(F)
cmds.move(5, 2, -3, grp, relative=True)
after = wpos(F)
shift = max(abs(a[0] - b[0] - 5) + abs(a[1] - b[1] - 2) + abs(a[2] - b[2] + 3) for a, b in zip(after, before))
check("5 moving the rig moves chain + Tip together (shape unchanged)", shift < 1e-4, shift)

# ---------------------------------------------------------------- 6. 조인트가 아닌 체인(FK 컨트롤러 트랜스폼)
cmds.file(new=True, force=True)
G = chain(0, name="g", joints=False)
lm.build_wave_lite(G, prefix="fk", tip_follow=0.6, **dict(quiet, mode=wm.MODE_CHAIN))
rest = wpos(G)
cmds.move(0, 0, 5, tip_of("g0"), relative=True, worldSpace=True)
check("6 transform chain follows the Tip too", wpos(G)[-1][2] - rest[-1][2] > 1.0, round(wpos(G)[-1][2] - rest[-1][2], 3))

# ---------------------------------------------------------------- 7. 제거 · 굽기
cnt, msg = lm.remove_wave_lite()
check("7 remove deletes Tip + nodes, rotations back to rest",
      not cmds.ls("*" + lm.LITE_TIP_SUFFIX + "*") and not cmds.ls("*_tip_qBlend*")
      and maxdist(wpos(G), rest) < 1e-6)
cmds.file(new=True, force=True)
H = chain(0, name="h")
c, d, msg = lm.build_wave_lite([H[0]], prefix="bake", tip_follow=0.6, output=wm.OUTPUT_CURVE, start=1, end=30, **common)
keys = cmds.keyframe(H[4] + ".rotateZ", q=True, keyframeCount=True)
check("7 Curve output bakes with Tip Follow (keys, Tip removed)", keys and keys >= 30
      and not cmds.ls("*" + lm.LITE_TIP_SUFFIX + "*"), keys)

# ---------------------------------------------------------------- 8. UI
from tools.A00390_WindTool_V03.app.ui import main_window as mw  # noqa: E402
cmds.file(new=True, force=True)
J = chain(0, name="j")
win = mw.MainWindow()
win.show()
APP.processEvents()
check("8 UI: Tip Follow off by default, spin disabled", not win.chk_lite_tip.isChecked() and not win.sb_lite_tip.isEnabled())
win.tsl.set_items([J[0]])
win.rb_root.setChecked(True)
win.on_lite_apply()
check("8 UI off -> no Tip", not cmds.ls("*" + lm.LITE_TIP_SUFFIX + "*"))
win.on_lite_remove()
win.chk_lite_tip.setChecked(True)
win.sb_lite_tip.setValue(0.45)
win.on_lite_apply()
drv = driver("j0")
check("8 UI on -> windTipFollow passed + Tip built", abs(cmds.getAttr(drv + "." + lm.LITE_TIP_FOLLOW) - 0.45) < 1e-9
      and len(cmds.ls("*" + lm.LITE_TIP_SUFFIX + "*", type="transform")) == 1)
check("8 log mentions Tip Follow", "Tip Follow on" in win.te_log.toPlainText())
win.close()

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
