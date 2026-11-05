# -*- coding: utf-8 -*-
# A00390_WindTool_V03 v03.05 - Chain Wave Lite 의 Flutter 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_lite_flutter.py
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

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def chain(x, n=9, name="c"):
    cmds.select(clear=True)
    js = [cmds.joint(p=(x, 10 - k * 1.2, 0.15 * k), name="{0}{1}".format(name, k)) for k in range(n)]
    cmds.joint(js[0], e=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
    return [cmds.ls(j, long=True)[0] for j in js]


def rots(js):
    return [cmds.getAttr(j + ".rotate")[0] for j in js]


def maxdiff(a, b):
    return max(abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))


cmds.currentUnit(time="film")
A = chain(0, name="a")
B = chain(3, name="b")
C = chain(6, name="c")
common = dict(mode=wm.MODE_ROOT, axis="Z", swing=18.0, period=20.0, speed=1.0, ramp=1.0, debug_curve=False)
lm.build_wave_lite([A[0]], prefix="noFlut", **common)
lm.build_wave_lite([B[0]], prefix="flut0", flutter=0.0, flutter_stiffness=0.0, **common)
lm.build_wave_lite([C[0]], prefix="flut", flutter=0.0, flutter_stiffness=0.0, local_axis="Z", **common)
drv_a = [d for d in wm.all_wind_drivers() if "a0_liteDriver" in d][0]
drv_b = [d for d in wm.all_wind_drivers() if "b0_liteDriver" in d][0]
drv_c = [d for d in wm.all_wind_drivers() if "c0_liteDriver" in d][0]
check("Flutter off: driver has no windFlutter attr", not cmds.objExists(drv_a + "." + lm.LITE_FLUTTER))
check("Flutter on: windFlutter / windFlutterStiffness keyable", cmds.getAttr(drv_b + "." + lm.LITE_FLUTTER, keyable=True)
      and cmds.getAttr(drv_b + "." + lm.LITE_FLUTTER_STIFF, keyable=True))
worst = 0.0
for f in (1, 6, 13, 27, 40):
    cmds.currentTime(f)
    worst = max(worst, maxdiff(rots(A), rots(B)))
check("windFlutter 0 = exactly the old Lite rotations", worst < 1e-9, "max diff {0:.2e}".format(worst))

# ---- Flutter > 0 (Rotate Axis object Z: rotateZ = rest + local)  -> delta = 항
n = len(C)
pts = [cmds.xform(j, q=True, ws=True, t=True) for j in C]
arcs = [0.0]
for i in range(1, n):
    arcs.append(arcs[-1] + sum((pts[i][k] - pts[i - 1][k]) ** 2 for k in range(3)) ** 0.5)
total = arcs[-1]
F, P = 9.5, 0.8
worst, sum_flut, root_delta = 0.0, 0.0, 0.0
for f in (3, 11, 19, 33):
    cmds.currentTime(f)
    cmds.setAttr(drv_c + "." + lm.LITE_FLUTTER, 0.0)
    cmds.setAttr(drv_c + "." + lm.LITE_FLUTTER_STIFF, P)
    base = [r[2] for r in rots(C)]
    cmds.setAttr(drv_c + "." + lm.LITE_FLUTTER, F)
    now = [r[2] for r in rots(C)]
    for k, j in enumerate(C):
        lut = [x for x in cmds.ls("c0_lite{0:02d}_sine*".format(k)) if cmds.nodeType(x).startswith("animCurve")][0]
        expect = F * 1.0 * (12.0 / n) * (arcs[k] / total) ** P * cmds.getAttr(lut + ".output")
        worst = max(worst, abs((now[k] - base[k]) - expect))
        sum_flut += abs(expect)
    root_delta = max(root_delta, abs(now[0] - base[0]))
check("Flutter term = windFlutter * envelope * 12/n * (s/total)^stiffness * sin (same phase)", worst < 1e-5 and sum_flut > 1.0,
      "max err {0:.2e} (float precision of the node chain)".format(worst))
check("stiffness > 0: root node gets no flutter", root_delta < 1e-9, root_delta)

# 누적: 같은 Flutter 를 주면 끝으로 갈수록 월드 굽힘이 쌓인다 (Swing 0 으로 Flutter 만)
cmds.setAttr(drv_c + "." + lm.LITE_SWING, 0.0)
cmds.setAttr(drv_c + "." + lm.LITE_FLUTTER_STIFF, 0.0)
cmds.setAttr(drv_c + ".windWavelength", 1e6)          # 위상 같게 -> 모든 노드 같은 사인
cmds.currentTime(5)
lut0 = [x for x in cmds.ls("c0_lite00_sine*") if cmds.nodeType(x).startswith("animCurve")][0]
s0 = cmds.getAttr(lut0 + ".output")
locals_ = [r[2] for r in rots(C)]
check("Flutter piles up: every node turns by the same local angle (accumulates to the tip)",
      abs(s0) > 0.05 and max(abs(v - locals_[0]) for v in locals_) < 1e-6 and abs(locals_[0] - F * 12.0 / n * s0) < 1e-6,
      (round(locals_[0], 4), round(F * 12.0 / n * s0, 4)))

# 라이브 · envelope
cmds.setAttr(drv_c + ".windEnvelope", 0.0)
check("envelope 0 -> rest (flutter included)", max(abs(v) for v in [r[2] for r in rots(C)]) < 1e-9)
cmds.setAttr(drv_c + ".windEnvelope", 1.0)
cmds.setAttr(drv_c + "." + lm.LITE_FLUTTER, 0.0)
check("windFlutter live back to 0 -> rest (swing 0)", max(abs(v) for v in [r[2] for r in rots(C)]) < 1e-9)

# 제거: flutter 노드도 지운다
before = len(cmds.ls("*_flut*", type=["multDoubleLinear", "multiplyDivide", "plusMinusAverage"]))
cnt, msg = lm.remove_wave_lite()
after = len(cmds.ls("*_flut*", type=["multDoubleLinear", "multiplyDivide", "plusMinusAverage"]))
check("remove deletes flutter nodes + restores rest", before > 0 and after == 0
      and max(abs(x) for r in rots(C) for x in r) < 1e-9, (before, after))

# 굽기(Curve 출력)도 Flutter 포함
cmds.file(new=True, force=True)
cmds.currentUnit(time="film")
D = chain(0, name="d")
lm.build_wave_lite([D[0]], prefix="bake", flutter=12.0, output=wm.OUTPUT_CURVE, start=1, end=30, local_axis="Z", **common)
keys = cmds.keyframe(D[4] + ".rotateZ", q=True, keyframeCount=True)
check("Curve output bakes with Flutter (keys, setup removed)", keys and keys >= 30 and not cmds.ls("*_flut*"), keys)

# UI
from tools.A00390_WindTool_V03.app.ui import main_window as mw  # noqa: E402
cmds.file(new=True, force=True)
E = chain(0, name="e")
win = mw.MainWindow()
win.show()
APP.processEvents()
check("UI: Flutter checkbox (on) + spins (0)", win.chk_lite_flutter.isChecked() and win.sb_lite_flutter.value() == 0.0)
win.tsl.set_items([E[0]])
win.rb_root.setChecked(True)
win.sb_lite_flutter.setValue(7.5)
win.sb_lite_flutter_stiff.setValue(0.4)
win.on_lite_apply()
drv = [d for d in wm.all_wind_drivers() if "e0_liteDriver" in d][0]
check("UI build passes Flutter", abs(cmds.getAttr(drv + "." + lm.LITE_FLUTTER) - 7.5) < 1e-9
      and abs(cmds.getAttr(drv + "." + lm.LITE_FLUTTER_STIFF) - 0.4) < 1e-9)
win.on_lite_remove()
win.chk_lite_flutter.setChecked(False)
check("UI: unchecked disables spins", not win.sb_lite_flutter.isEnabled())
win.on_lite_apply()
drv = [d for d in wm.all_wind_drivers() if "e0_liteDriver" in d][0]
check("UI: Flutter off -> no attr", not cmds.objExists(drv + "." + lm.LITE_FLUTTER))
win.close()

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
