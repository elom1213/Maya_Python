# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.64 - Bake > Counter Layer 의 `Create Counter Layer` 진행 팝업 시험 (mayapy + 오프스크린 PySide2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_counter_layer_progress_ui.py
# 판정 : 작은 작업(예전 기준 오브젝트 x 프레임 <= 2000)에서도 팝업이 한 번 뜨고 닫힌다 · Everywhere / Stationary 둘 다 ·
#        게이지가 100% 까지 · 결과는 팝업 없이 core 로 만든 것과 같다 · 입력 오류면 팝업 없음.
# QApplication 은 maya.standalone.initialize() 보다 먼저 (qapplication-before-maya-standalone).
import math
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtCore import Qt   # noqa: E402
from PySide2.QtWidgets import QApplication   # noqa: E402

APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)

R = []
TR = ["tx", "ty", "tz", "rx", "ry", "rz"]
S, E = 1, 40


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build():
    """global_ctl > foot_l/r_ctl. 발은 Base 키, lyr_glo 가 global_ctl 을 움직인다 (발 2 x 40 프레임 = 80 단위)."""
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=S, max=E, ast=S, aet=E)
    glo = cmds.createNode("transform", n="global_ctl")
    feet = []
    for k, side in enumerate(("l", "r")):
        f = cmds.createNode("transform", n="foot_%s_ctl" % side, p=glo)
        for t, v in ((1, 0.0), (15, 4.0), (16, 4.0), (25, 4.0), (40, 9.0)):
            cmds.setKeyframe(f, at="tz", t=t, v=v + k)
        cmds.setKeyframe(f, at="tx", t=1, v=(5.0 if k == 0 else -5.0))
        feet.append(f)
    lyr = cmds.animLayer("lyr_glo")
    for a in TR:
        cmds.animLayer(lyr, e=True, at=glo + "." + a)
    for i, t in enumerate(range(S, E + 1, 13)):
        for j, a in enumerate(TR):
            cmds.setKeyframe(glo, at=a, t=t, v=math.sin(i + j) * (20 if a[0] == "r" else 3), animLayer=lyr)
    return feet


def worlds(objs):
    out = {}
    for t in range(S, E + 1):
        cmds.currentTime(t)
        for o in objs:
            out[(o, t)] = cmds.getAttr(o + ".worldMatrix[0]")
    return out


def diff(a, b):
    return max(max(abs(x - y) for x, y in zip(a[k], b[k])) for k in a)


from tools.A00110_animTool_V02.app.core.counter_layer_manager import CounterLayerManager as CLM   # noqa: E402

# ---------------------------------------------------------------- 기준: 팝업 없이 core 로 (Everywhere)
feet = build()
n, msg = CLM.create(feet, ["lyr_glo"], S, E)
check("core without progress still works", n == 2, msg)
REF = worlds(feet)

from Framework.qt import JUN_mod_progress_qt   # noqa: E402

REAL = JUN_mod_progress_qt.JUN_mod_progress_qt_v01
SEEN = {}


def reset():
    SEEN.clear()
    SEEN.update({"created": 0, "steps": 0, "finished": 0, "max": 0.0, "visible": False, "title": None})


class Spy(REAL):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        SEEN["created"] += 1
        SEEN["title"] = self.windowTitle()

    def step(self, done, total, message=None):
        SEEN["steps"] += 1
        SEEN["visible"] = SEEN["visible"] or self.isVisible()
        r = super().step(done, total, message)
        SEEN["max"] = max(SEEN["max"], self._fraction)
        return r

    def finish(self):
        SEEN["finished"] += 1
        return super().finish()


JUN_mod_progress_qt.JUN_mod_progress_qt_v01 = Spy

from tools.A00110_animTool_V02.app.ui.main_window import MainWindow   # noqa: E402

win = MainWindow()
win.show()
APP.processEvents()


def setup(hold_still):
    feet = build()
    win.cl_tsl.set_items(feet)
    win.on_cl_refresh_layers(quiet=True)
    for i in range(win.lw_cl_layers.count()):
        it = win.lw_cl_layers.item(i)
        it.setCheckState(Qt.Checked if it.text() == "lyr_glo" else Qt.Unchecked)
    win.rb_cl_timeline.setChecked(True)
    win.cb_cl_t.setChecked(True)
    win.cb_cl_r.setChecked(True)
    win.sb_cl_step.setValue(1)
    (win.rb_cl_hold_still if hold_still else win.rb_cl_hold_all).setChecked(True)
    win.le_cl_name.setText("")
    return feet


# ---------------------------------------------------------------- 1. Everywhere, 작은 작업 (2 x 40 = 80 < 2000)
feet = setup(False)
reset()
win.btn_cl_create.click()
APP.processEvents()
check("everywhere: popup shown once and closed (small job)",
      SEEN["created"] == 1 and SEEN["finished"] == 1 and SEEN["title"] == "Counter Layer", SEEN)
check("everywhere: popup visible while working", SEEN["visible"], SEEN)
check("everywhere: gauge stepped", SEEN["steps"] >= 3, SEEN["steps"])
check("everywhere: gauge reaches 100%", SEEN["max"] >= 0.999, SEEN["max"])
got = worlds(feet)
d = diff(REF, got)
check("everywhere: result identical to the core run without popup", d < 1e-9, d)
log = win.te_log.toPlainText()
import re   # noqa: E402
line = [x for x in log.splitlines() if x.startswith("Counter Layer:")]
check("log shows the result with elapsed time", line and re.search(r"\(\d+\.\ds\)$", line[-1]), line[-1:])

# ---------------------------------------------------------------- 2. Stationary spans only
feet = build()
n, msg = CLM.create(feet, ["lyr_glo"], S, E, hold=CLM.HOLD_STATIONARY)
REF2 = worlds(feet)
feet = setup(True)
reset()
win.btn_cl_create.click()
APP.processEvents()
check("stationary: popup shown once and closed",
      SEEN["created"] == 1 and SEEN["finished"] == 1, SEEN)
check("stationary: gauge reaches 100%", SEEN["max"] >= 0.999, SEEN["max"])
d2 = diff(REF2, worlds(feet))
check("stationary: result identical to the core run", d2 < 1e-9, (d2, msg))

# ---------------------------------------------------------------- 3. 입력 오류 -> 팝업 없음
win.cl_tsl.set_items([])
reset()
win.btn_cl_create.click()
check("empty list: no popup", SEEN["created"] == 0, SEEN)

win.close()
print("RESULT {0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
