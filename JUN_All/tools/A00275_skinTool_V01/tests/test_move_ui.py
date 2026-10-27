# -*- coding: utf-8 -*-
# A00275_skinTool_V01 v01.37 - Weights > Move 탭 UI 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_move_ui.py
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다 (메모리 qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication, QMessageBox   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00275_skinTool_V01.app.ui import move_tab as mt   # noqa: E402
from tools.A00275_skinTool_V01.app.ui.main_window import MainWindow   # noqa: E402
from tools.A00275_skinTool_V01.app.core import weight_move_manager as mv   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


logs = []
win = MainWindow()
pages = [win.weights_tabs.tabText(i) for i in range(win.weights_tabs.count())]
check("Weights sub tabs : Move is last, others unchanged",
      pages == ["Classic", "Transfer", "Migrate A -> B", "Copy Weights", "Layer", "Smooth", "Move"], pages)
check("main window keeps a MoveTab", isinstance(win.move_tab, mt.MoveTab))

tab = mt.MoveTab(log_callback=logs.append)
o = tab.options()
expect = dict(mt.DEFAULTS)
check("defaults = Kangaroo defaults (+ respect / soft on)", o == expect, o)
check("engine default Native", tab.rb_native.isChecked())
check("button disabled with empty lists", not tab.btn_move.isEnabled() and tab.btn_move.text() == "Move")
check("border mask steps disabled while Everything", not tab.sb_border_steps.isEnabled())
tab.border_buttons.button(mv.BORDER_IGNORE).click()
check("border mask steps enabled for Ignore", tab.sb_border_steps.isEnabled())
tab.cb_respect.setChecked(False)
check("soft selection follows Respect selection", not tab.cb_soft.isEnabled()
      and tab.options()["use_soft_selection"] is False)
tab.sb_smooth.setValue(40)
check("smooth steps above slider range kept", tab.sb_smooth.value() == 40 and tab.sl_smooth.value() == 20)
tab.reset_options()
check("Reset Options", tab.options() == expect, tab.options())

# 씬 + 실제 클릭
cmds.file(new=True, force=True)
cmds.polyPlane(name="m", w=10, h=2, sx=20, sy=4)
cmds.select(clear=True)
cmds.joint(name="fA", position=(-5, 0, 0))
cmds.joint(name="fB", position=(5, 0, 0))
cmds.select(clear=True)
cmds.joint(name="t1", position=(-5, 0.5, 0))
cmds.joint(name="t2", position=(0, 0.5, 0))
cmds.joint(name="t3", position=(5, 0.5, 0))
skin = cmds.skinCluster(["fA", "fB"], "m", toSelectedBones=True)[0]

tab.tsl_from.set_items(["fA", "fB"])
tab.tsl_to.set_items(["t1", "t2", "t3"])
app.processEvents()
check("button text follows the lists", tab.btn_move.isEnabled() and tab.btn_move.text() == "Move weights  2 -> 3",
      tab.btn_move.text())

before = [cmds.skinPercent(skin, "m.vtx[{0}]".format(v), q=True, v=True) for v in range(5)]
cmds.select("m")
del logs[:]
tab.btn_move.click()
infl = cmds.skinCluster(skin, q=True, influence=True)
row = dict(zip(infl, cmds.skinPercent(skin, "m.vtx[0]", q=True, v=True)))
check("click moves (To added as influences, From emptied)", set(infl) >= {"t1", "t2", "t3"}
      and row.get("fA", 0) < 1e-9 and abs(row.get("t1", 0) - 1.0) < 1e-6, row)
check("log has [OK] line", any(m.startswith("[OK]") for m in logs), logs[-2:])
cmds.undo()
after_undo = [cmds.skinPercent(skin, "m.vtx[{0}]".format(v), q=True, v=True)[:2] for v in range(5)]
check("one click = one undo step", all(abs(a[0] - b[0]) < 1e-9 for a, b in zip(after_undo, before)),
      (after_undo[0], before[0]))

# 섬 검사 -> 대화상자 (No)
mt.QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.No)
cmds.select(["m.vtx[0:1]", "m.vtx[100:101]"])
del logs[:]
tab.btn_move.click()
check("island check asks (No = skip)", any("island check" in m for m in logs), logs)

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
