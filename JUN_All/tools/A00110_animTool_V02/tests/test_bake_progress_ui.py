# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.63 - Bake > Bake 의 `Bake List` 진행 팝업 시험 (mayapy + 오프스크린 PySide2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_bake_progress_ui.py
# 판정 : 팝업이 한 번 뜨고 닫힌다 · 단계는 실제로 도는 것만(레이어 없는 오브젝트 = Baking, 레이어 오브젝트 = Baking layered
#        objects, Smart = Simplifying) · 게이지가 프레임마다 움직여 100% 까지 · 굽는 결과는 팝업 없이 구운 것과 같다.
# QApplication 은 maya.standalone.initialize() 보다 먼저 (qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402

APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build():
    """drv(키) 를 따르는 plain_ctl(컨스트레인트, 레이어 없음) + 레이어 컨트롤러 lay_ctl(Base + Layer1)."""
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=1, max=60, ast=1, aet=60)
    drv = cmds.spaceLocator(name="drv")[0]
    for t, (x, r) in ((1, (0, 0)), (30, (10, 90)), (60, (-5, 200))):
        cmds.setKeyframe(drv, at="tx", t=t, v=x)
        cmds.setKeyframe(drv, at="ry", t=t, v=r)
    plain = cmds.circle(name="plain_ctl")[0]
    cmds.parentConstraint(drv, plain)
    lay = cmds.circle(name="lay_ctl")[0]
    for t, v in ((1, 0), (60, 30)):
        cmds.setKeyframe(lay, at="ty", t=t, v=v)
    cmds.select(lay)
    l1 = cmds.animLayer("Layer1", addSelectedObjects=True)
    for t, v in ((1, 0), (30, 4)):
        cmds.setKeyframe(lay, at="tz", t=t, v=v, animLayer=l1)
    cmds.select(clear=True)
    return plain, lay


def worlds(nodes, frames):
    out = {}
    for f in frames:
        cmds.currentTime(f)
        for n in nodes:
            out[(n, f)] = cmds.xform(n, q=True, ws=True, matrix=True)
    return out


FR = list(range(1, 61))

# ---------------------------------------------------------------- 기준: 팝업 없이 core 로 구운 결과
from tools.A00110_animTool_V02.app.core.bake_manager import BakeManager   # noqa: E402

plain, lay = build()
BakeManager.bake([plain, lay], 10, 40)
cmds.delete(cmds.ls(type="parentConstraint"))
REF = worlds([plain, lay], FR)

from Framework.qt import JUN_mod_progress_qt   # noqa: E402

REAL = JUN_mod_progress_qt.JUN_mod_progress_qt_v01
SEEN = {}


def reset():
    SEEN.clear()
    SEEN.update({"created": 0, "phases": [], "set": None, "steps": 0, "finished": 0, "max": 0.0, "visible": False})


class Spy(REAL):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        SEEN["created"] += 1
        SEEN["title"] = self.windowTitle()

    def set_phases(self, phases):
        SEEN["set"] = [p[0] for p in phases]
        return super().set_phases(phases)

    def begin_phase(self, label=None, index=None):
        SEEN["phases"].append(label)
        return super().begin_phase(label, index)

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
names = [win.tabs.tabText(i) for i in range(win.tabs.count())]
win.tabs.setCurrentIndex(names.index("Bake"))
sub = [win.bake_tabs.tabText(i) for i in range(win.bake_tabs.count())]
win.bake_tabs.setCurrentIndex(sub.index("Bake"))
APP.processEvents()

# ---------------------------------------------------------------- 빈 리스트 -> 팝업 없음
reset()
win.bake_tsl.set_items([])
win.btn_bake.click()
check("empty list: no popup", SEEN["created"] == 0, SEEN)


def list_up(nodes):
    win.bake_tsl.set_items(nodes)


def set_range(s, e):
    win.rb_bake_custom.setChecked(True)
    win.bake_range.set_range(s, e)


# ---------------------------------------------------------------- 1. plain + layered, smart 끔
plain, lay = build()
list_up([plain, lay])
check("list has 2 items", win.bake_tsl.get_all_items() == ["plain_ctl", "lay_ctl"], win.bake_tsl.get_all_items())
set_range(10, 40)
win.cb_bake_smart.setChecked(False)
reset()
win.btn_bake.click()
APP.processEvents()
check("popup shown once and closed", SEEN["created"] == 1 and SEEN["finished"] == 1 and SEEN["title"] == "Bake List", SEEN)
check("popup visible while baking", SEEN["visible"])
check("phases = only the ones that run",
      SEEN["set"] == ["Baking", "Baking layered objects"] and SEEN["phases"] == SEEN["set"], SEEN)
check("gauge stepped per frame (31 frames x 2 phases)", SEEN["steps"] >= 62, SEEN["steps"])
check("gauge reaches 100%", SEEN["max"] >= 0.999, SEEN["max"])
cmds.delete(cmds.ls(type="parentConstraint"))
got = worlds([plain, lay], FR)
bad = [k for k in REF if max(abs(x - y) for x, y in zip(REF[k], got[k])) > 1e-6]
check("result identical to the core bake without popup", not bad, bad[:5])
log = win.te_log.toPlainText()
check("log shows the result with elapsed time", "baked over [10-40]" in log and "s)" in log, log[-200:])

# ---------------------------------------------------------------- 2. plain 만 + smart
plain, lay = build()
list_up([plain])
items = win.bake_tsl.get_all_items()
win.cb_bake_smart.setChecked(True)
reset()
win.btn_bake.click()
APP.processEvents()
expect = ["Baking", "Simplifying"]
check("plain + smart: phases Baking -> Simplifying",
      items == ["plain_ctl"] and SEEN["set"] == expect and SEEN["phases"] == expect, (items, SEEN))
check("plain + smart: gauge reaches 100%", SEEN["max"] >= 0.999, SEEN["max"])
win.cb_bake_smart.setChecked(False)

# ---------------------------------------------------------------- 3. core: progress 없이도 그대로 (기존 호출)
plain, lay = build()
n, msg = BakeManager.bake([plain, lay], 10, 40)
check("core without progress still works", n == 2, msg)

win.close()
print("RESULT {0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
