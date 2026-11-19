# -*- coding: utf-8 -*-
# A00275_skinTool_V01 v01.40 - Weights > Flood 탭 UI 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_flood_ui.py
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다 (메모리 qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00275_skinTool_V01.app.ui import flood_tab as ft   # noqa: E402
from tools.A00275_skinTool_V01.app.ui.main_window import MainWindow   # noqa: E402
from tools.A00275_skinTool_V01.app.core import weight_flood_manager as fl   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


win = MainWindow()
pages = [win.weights_tabs.tabText(i) for i in range(win.weights_tabs.count())]
check("Weights sub tabs end with Move, Flood", pages[-2:] == ["Move", "Flood"], pages)
check("main window keeps a FloodTab", isinstance(win.flood_tab, ft.FloodTab))

logs = []
tab = ft.FloodTab(log_callback=logs.append)
check("defaults = Kangaroo Flood defaults (+ respect / soft on)", tab.options() == ft.DEFAULTS, tab.options())
check("button disabled with an empty list", not tab.btn_flood.isEnabled() and tab.btn_flood.text() == "Flood")

tab.op_buttons.button(fl.OP_SCALE_ALL).click()
tab.sb_value.setValue(3.0)
check("Scale All accepts Value > 1, slider stays at its end",
      abs(tab.sb_value.value() - 3.0) < 1e-9 and tab.sl_value.value() == ft.FLOAT_SLIDER_STEPS)
check("Scale All disables Smooth Steps", not tab.sb_smooth.isEnabled())
tab.op_buttons.button(fl.OP_REPLACE_CLOSEST).click()
check("back to Replace Closest clamps Value to 1, Smooth on",
      abs(tab.sb_value.value() - 1.0) < 1e-9 and tab.sb_smooth.isEnabled())
tab.op_buttons.button(fl.OP_DISTRIBUTE).click()
check("Distribute disables Value", not tab.sb_value.isEnabled() and tab.sb_smooth.isEnabled())
tab.border_buttons.button(fl.BORDER_ONLY).click()
check("border mask steps enabled for Only", tab.sb_border_steps.isEnabled())
tab.cb_respect.setChecked(False)
check("soft selection follows Respect selection", tab.options()["use_soft_selection"] is False)
tab.reset_options()
check("Reset Options", tab.options() == ft.DEFAULTS, tab.options())

# ---- 같은 이름 조인트 씬에서 실제 클릭
cmds.file(new=True, force=True)
cmds.polyPlane(name="m", w=10, h=2, sx=20, sy=4)
paths = []
for grp, x in (("A", -3.0), ("B", 3.0)):
    cmds.select(clear=True)
    cmds.group(empty=True, name=grp)
    cmds.select(clear=True)
    j = cmds.joint(name="dup", position=(x, 0.5, 0))
    cmds.parent(j, grp)
    paths.append(cmds.ls("{0}|dup".format(grp), long=True)[0])
cmds.select(clear=True)
cmds.joint(name="keep", position=(0, 0, 3))
skin = cmds.skinCluster(paths + ["keep"], "m", toSelectedBones=True)[0]
cmds.skinPercent(skin, "m.vtx[*]", transformValue=[("keep", 1.0)])

cmds.select(paths)                       # 리스트에는 ls(sl) 그대로 - 'A|dup', 'B|dup'
tab.tsl_joints.set_items(cmds.ls(sl=True))
check("button shows the joint count", tab.btn_flood.isEnabled() and "2 joint" in tab.btn_flood.text(),
      tab.btn_flood.text())
check("joints() gives full paths", sorted(tab.joints()) == sorted(paths), tab.joints())

cmds.rename(paths[0], "renamed")         # 리네임해도 UUID 로 따라간다
cmds.select("m")
logs[:] = []
tab.btn_flood.click()
check("Flood click logs OK", any(m.startswith("[OK]") for m in logs), logs)
w = cmds.skinPercent(skin, "m.vtx[0]", q=True, transform="|A|renamed")
w2 = cmds.skinPercent(skin, "m.vtx[20]", q=True, transform="|B|dup")
check("left corner -> A (renamed), right corner -> B|dup", w > 0.99 and w2 > 0.99, (w, w2))
cmds.undo()
check("one undo restores", cmds.skinPercent(skin, "m.vtx[0]", q=True, transform="keep") > 0.99)

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
