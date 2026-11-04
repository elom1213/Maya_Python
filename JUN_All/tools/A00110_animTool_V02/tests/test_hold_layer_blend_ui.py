# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.39 - Hot Key > Main `Layer Blend Key` UI 시험 (mayapy + 오프스크린 PySide2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_hold_layer_blend_ui.py
# 위젯 -> HoldLayerManager.settings push, Pose Key 행 변경 반영, optionVar 저장 / 다시 열 때 복원, (missing) 표시.
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


PRE = "JUN_A00110_holdLayer_"
for k in ("enabled", "offset", "layer", "axis_values", "use_current", "view_layer", "current_axes"):
    if cmds.optionVar(exists=PRE + k):
        cmds.optionVar(remove=PRE + k)

cmds.file(new=True, force=True)
cube = cmds.polyCube(n="ctl")[0]
cmds.setKeyframe(cube, at="tx", t=1, v=0)
cmds.animLayer("Layer_01")
cmds.animLayer("Layer_02")

from tools.A00110_animTool_V02.app.ui.main_window import MainWindow   # noqa: E402
from tools.A00110_animTool_V02.app.core import HoldLayerManager as HLM   # noqa: E402

win = MainWindow()
win.show()
APP.processEvents()

check("U20 View > Graph Focus Auto-Focus is ON when the tool opens (v02.46)",
      win.btn_graph_focus.isChecked() and win.btn_graph_focus.text().endswith(": ON")
      # mayapy(헤드리스)에서는 cmds.scriptJob 이 None 을 돌려줘 is_active() 가 False - 설치 호출 여부(게터)로 본다
      and win.graph_focus_mgr._margin_getter is not None, win.btn_graph_focus.text())
check("U21 Current-only axes (ry tx tz, axis unchecked) are pushed as key axes (v02.46)",
      all(a in HLM.load_settings()["axis_values"] for a in ("ry", "tx", "tz")), HLM.load_settings())

items = [win.cmb_hold_layer.itemText(i) for i in range(win.cmb_hold_layer.count())]
check("U1 combo lists layers without BaseAnimation", sorted(items) == ["Layer_01", "Layer_02"], items)
check("U2 default off, sub widgets disabled", not win.cb_hold_layer.isChecked() and not win.w_hold_layer.isEnabled())
check("U3 settings pushed on open (disabled)", HLM.settings["enabled"] is False)

win.cb_hold_layer.setChecked(True)
win.cmb_hold_layer.setCurrentIndex(win.cmb_hold_layer.findData("Layer_02"))
win.sp_hold_layer_offset.setValue(7)
check("U4 toggle enables widgets", win.w_hold_layer.isEnabled())
check("U5 settings = enabled, Layer_02, 7",
      HLM.settings["enabled"] and HLM.settings["layer"] == "Layer_02" and HLM.settings["offset"] == 7, HLM.settings)

# Pose 행 (기본 rx rz ty 체크, 0)
cb, le = win.pose_rows["tx"]
cb.setChecked(True)
le.setText("3.5")
cb_rz, le_rz = win.pose_rows["rz"]
le_rz.setText("")          # 빈 칸 -> 그 축만 빠진다
check("U6 pose rows pushed (tx 3.5, empty rz dropped)",
      HLM.settings["axis_values"].get("tx") == 3.5 and "rz" not in HLM.settings["axis_values"]
      and "rx" in HLM.settings["axis_values"], HLM.settings["axis_values"])

check("U7 optionVars saved",
      cmds.optionVar(q=PRE + "enabled") == 1 and cmds.optionVar(q=PRE + "offset") == 7
      and cmds.optionVar(q=PRE + "layer") == "Layer_02")

# v02.43 보기 게이트 콤보
vitems = [win.cmb_hold_view_layer.itemText(i) for i in range(win.cmb_hold_view_layer.count())]
check("U17 'Run only when viewing' defaults to BaseAnimation (data ''), lists other layers",
      win.cmb_hold_view_layer.currentText() == "BaseAnimation" and win.cmb_hold_view_layer.currentData() in ("", None)
      and vitems[0] == "BaseAnimation" and "Layer_01" in vitems, vitems)
win.cmb_hold_view_layer.setCurrentIndex(win.cmb_hold_view_layer.findData("Layer_01"))
check("U18 choosing Layer_01 pushes view_layer", HLM.load_settings()["view_layer"] == "Layer_01", HLM.load_settings())

# v02.44 축마다 `Current`
check("U13 every Pose Key row has its own 'Current', default on = ry, tx, tz (v02.45), their fields disabled",
      sorted(win.pose_current) == sorted(win.pose_rows)
      and all(c.text() == "Current" for c in win.pose_current.values())
      and sorted(a for a, c in win.pose_current.items() if c.isChecked()) == ["ry", "tx", "tz"]
      and [a for a, (_c, le) in win.pose_rows.items() if not le.isEnabled()] == ["ry", "tx", "tz"]
      and sorted(HLM.load_settings()["current_axes"]) == ["ry", "tx", "tz"] and not hasattr(win, "cb_pose_current"),
      HLM.load_settings())
for a in ("ry", "tx", "tz"):
    win.pose_current[a].setChecked(False)
win.pose_current["ty"].setChecked(True)
win.pose_current["rz"].setChecked(True)
check("U14 per-axis: only ty / rz fields disabled, current_axes pushed, empty rz still included",
      not win.pose_rows["ty"][1].isEnabled() and not win.pose_rows["rz"][1].isEnabled()
      and win.pose_rows["rx"][1].isEnabled() and win.pose_rows["tx"][1].isEnabled()
      and sorted(HLM.load_settings()["current_axes"]) == ["rz", "ty"] and "rz" in HLM.load_settings()["axis_values"],
      HLM.load_settings())
cmds.currentTime(5)
cmds.setAttr(cube + ".ty", 4.5)
cmds.setAttr(cube + ".tx", 9.0)
cmds.select(cube)
win.pose_rows["tx"][1].setText("3.5")
win.btn_set_pose.click()
k_ty = cmds.keyframe(cube + ".ty", q=True, valueChange=True, time=(5, 5)) or []
k_tx = cmds.keyframe(cube + ".tx", q=True, valueChange=True, time=(5, 5)) or []
check("U15 Set Pose Key: ty = current 4.5, tx = typed 3.5, empty rz field no warning stop",
      k_ty == [4.5] and k_tx == [3.5], (k_ty, k_tx))

win.close()
APP.processEvents()

# 다시 열기 : 복원 + 레이어가 사라지면 (missing)
cmds.delete("Layer_02")
HLM.settings.update(enabled=False, layer="", offset=10, axis_values={})
win2 = MainWindow()
win2.show()
APP.processEvents()
check("U8 reopen restores checkbox + offset", win2.cb_hold_layer.isChecked() and win2.sp_hold_layer_offset.value() == 7)
check("U9 missing layer shown as '(missing)' and kept",
      win2.cmb_hold_layer.currentText() == "Layer_02 (missing)" and HLM.settings["layer"] == "Layer_02",
      (win2.cmb_hold_layer.currentText(), HLM.settings["layer"]))
check("U10 settings re-pushed on reopen", HLM.settings["enabled"] and HLM.settings["offset"] == 7)
check("U19 reopen restores view layer Layer_01", win2.cmb_hold_view_layer.currentText() == "Layer_01",
      win2.cmb_hold_view_layer.currentText())
check("U16 reopen restores per-axis 'Current' (ty, rz) + their disabled fields",
      sorted(a for a, c in win2.pose_current.items() if c.isChecked()) == ["rz", "ty"]
      and not win2.pose_rows["ty"][1].isEnabled() and win2.pose_rows["rx"][1].isEnabled())

cmds.animLayer("Layer_03")
win2.cmb_hold_layer.showPopup()      # v02.40 : 펼치면 새 레이어가 바로 보인다
items = [win2.cmb_hold_layer.itemText(i) for i in range(win2.cmb_hold_layer.count())]
check("U12 popup refreshes the layer list", "Layer_03" in items, items)
win2.cmb_hold_layer.hidePopup()
cmds.animLayer("Layer_04")
win2.btn_hold_layer_refresh.click()
items = [win2.cmb_hold_layer.itemText(i) for i in range(win2.cmb_hold_layer.count())]
check("U11 Refresh picks up new layer, keeps missing selection",
      "Layer_04" in items and win2.cmb_hold_layer.currentText() == "Layer_02 (missing)", items)
win2.close()

for k in ("enabled", "offset", "layer", "axis_values", "use_current", "view_layer", "current_axes"):
    if cmds.optionVar(exists=PRE + k):
        cmds.optionVar(remove=PRE + k)

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
