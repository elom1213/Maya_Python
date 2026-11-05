# -*- coding: utf-8 -*-
# A00390_WindTool_V03 - Flow 탭 UI 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_flow_ui.py
# QApplication 은 maya.standalone.initialize() 보다 먼저.
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
from tools.A00390_WindTool_V03.app.ui import main_window as mw  # noqa: E402
from tools.A00390_WindTool_V03.app.core import flow_manager as fmg  # noqa: E402
from tools.A00390_WindTool_V03.app.core import flow_presets as fp  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


cmds.currentUnit(time="film")
roots = []
for c in range(2):
    cmds.select(clear=True)
    js = [cmds.joint(p=(c, 8 - k, 0)) for k in range(9)]
    roots.append(js[0])

win = mw.MainWindow()
win.show()
APP.processEvents()
titles = [win.tabs.tabText(i) for i in range(win.tabs.count())]
check("Flow tab exists (before Playback)", "Flow" in titles and titles.index("Flow") == titles.index("Playback") - 1, titles)
ft = win.flow_tab
win.tabs.setCurrentIndex(titles.index("Flow"))
APP.processEvents()

check("default values = Breeze, button highlighted", ft.preset_buttons["Breeze"].isChecked()
      and abs(ft.sb_a["speed"].value() - 2.58) < 1e-9 and abs(ft.sb_b["speed"].value() - 2.01) < 1e-9)
ft.preset_buttons["Fast Flutter"].click()
APP.processEvents()
check("preset click (no driver) loads values + highlight moves",
      ft.preset_buttons["Fast Flutter"].isChecked() and not ft.preset_buttons["Breeze"].isChecked()
      and abs(ft.sb_a["cross"].value() - 0.33) < 1e-9)

ft.sb_a["lean"].setValue(40.0)
APP.processEvents()
check("editing a value un-highlights the preset", not any(b.isChecked() for b in ft.preset_buttons.values()))
ft.preset_buttons["Slow Flow"].click()

win.tsl.set_items(roots)
win.rb_root.setChecked(True)
ft.sb_mix.setValue(0.25)
ft.sb_offset.setValue(7.0)
ft.btn_build.click()
APP.processEvents()
drv = (fmg.flow_drivers() or [None])[0]
check("Build Flow: 1 driver, 2 chains", drv is not None and len(cmds.ls("*" + fmg.FLOW_TIP_SUFFIX + "*", type="transform")) == 2)
check("driver got UI values (Slow Flow A/B, mix 0.25, offset 7, preset name)",
      abs(cmds.getAttr(drv + "." + fmg.a_attr("speed")) - 2.01) < 1e-9
      and abs(cmds.getAttr(drv + "." + fmg.b_attr("speed")) - 1.17) < 1e-9
      and abs(cmds.getAttr(drv + "." + fmg.FLOW_MIX) - 0.25) < 1e-9
      and abs(cmds.getAttr(drv + "." + fmg.FLOW_CHAIN_OFFSET) - 7.0) < 1e-9
      and cmds.getAttr(drv + "." + fmg.FLOW_PRESET) == "Slow Flow")

# Live Edit: 선택이 드라이버
cmds.select(drv)
ft.sl_mix.setValue(80)
APP.processEvents()
check("Mix slider writes flowMix live", abs(cmds.getAttr(drv + "." + fmg.FLOW_MIX) - 0.8) < 1e-9
      and abs(ft.sb_mix.value() - 0.8) < 1e-9)
ft.preset_buttons["Breeze"].click()
APP.processEvents()
check("preset click with a driver -> A/B on the driver",
      abs(cmds.getAttr(drv + "." + fmg.a_attr("flutter")) - 15.218) < 1e-9
      and cmds.getAttr(drv + "." + fmg.FLOW_PRESET) == "Breeze")
ft.sb_dir.setValue(45.0)
check("Direction live", abs(cmds.getAttr(drv + "." + fmg.FLOW_DIR) - 45.0) < 1e-9)
# 선택이 체인 노드여도 드라이버를 찾는다
cmds.select(roots[1])
ft.sb_b["random"].setValue(0.5)
check("selection = chain joint -> its driver", abs(cmds.getAttr(drv + "." + fmg.b_attr("random")) - 0.5) < 1e-9
      and cmds.getAttr(drv + "." + fmg.FLOW_PRESET) == "")

# Key Mix
cmds.currentTime(10)
ft.sb_mix.setValue(0.0)
ft.on_key_mix()
cmds.currentTime(40)
ft.sb_mix.setValue(1.0)          # 키가 있으면 지금 시각에 키
ft.on_key_mix()
keys = cmds.keyframe(drv + "." + fmg.FLOW_MIX, q=True, timeChange=True)
check("Key Mix keys flowMix (10, 40)", keys == [10.0, 40.0], keys)
cmds.currentTime(25)
check("keyed Mix evaluates between", abs(cmds.getAttr(drv + "." + fmg.FLOW_MIX) - 0.5) < 1e-6)

# Load From Driver
ft.preset_buttons["Slow Flow"].click()       # 드라이버도 바뀐다(라이브)
ft.chk_live.setChecked(False)
ft.preset_buttons["Fast Flutter"].click()    # UI 만
cmds.select(drv)
ft.on_load()
check("Load From Driver brings the driver values (Slow Flow) back", ft.preset_buttons["Slow Flow"].isChecked()
      and abs(ft.sb_a["speed"].value() - 2.01) < 1e-9)

# Select Tips / Remove
ft._select(tips=True)
check("Select Tips", len(cmds.ls(selection=True)) == 2)
ft.btn_remove.click()
APP.processEvents()
check("Remove Flow", not fmg.flow_drivers() and not cmds.objExists(fmg.FLOW_ENGINE))

# 창 높이: Flow 탭에서 잘림 없음
check("Flow tab fits (tabFit)", win.tab_fit.content_height() > 0)
win.close()
print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
