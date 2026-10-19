# -*- coding: utf-8 -*-
# A00550_PoseMapper - Solo preview 유지 시험 (v01.03, mayapy 2024 오프스크린, 합성 씬)
# Solo 는 체크박스를 직접 누를 때(와 창을 닫을 때)만 꺼져야 한다.
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
from PySide2.QtTest import QTest
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def on():
    return tab.cb_solo.isChecked() and tab.driver is not None and tab.driver.active


src = cmds.createNode("transform", n="JALI_IN")
for a in ("Jaw", "AHH", "OHH", "MBP"):
    cmds.addAttr(src, ln=a, at="double", k=True)
cmds.setAttr(src + ".Jaw", 9)
cmds.setAttr(src + ".OHH", 3)                        # 원래 값 (원복 확인용)
src2 = cmds.createNode("transform", n="JALI_IN2")
for a in ("AHH", "OHH"):
    cmds.addAttr(src2, ln=a, at="double", k=True)
tgt = cmds.createNode("transform", n="ARKIT")
for a in ("jawOpen", "mouthFunnel"):
    cmds.addAttr(tgt, ln=a, at="double", k=True)

import tools.A00550_PoseMapper as tool   # noqa: E402
win = tool.run(False)
win.show()
tab = win.pose_tab
tab.le_source.setText(src)
tab.le_target.setText(tgt)
tab.on_nodes_changed()
tab.lw_phonemes.setCurrentRow(1)                     # AHH
tab.cb_solo.setChecked(True)
check("solo on: AHH 10, OHH 0, Jaw untouched", on() and cmds.getAttr(src + ".AHH") == 10 and cmds.getAttr(src + ".OHH") == 0
      and cmds.getAttr(src + ".Jaw") == 9)

# 요청한 경우: 타겟 값을 0 -> 올림 -> 0
spin = tab.table.cellWidget(0, 2)
for v in (0.1, 0.3, 0.0):
    spin.setValue(v)
check("target 0 -> 0.1 -> 0.3 -> 0 keeps solo", on() and cmds.getAttr(src + ".AHH") == 10)
tab.table.cellWidget(1, 2).setValue(0.5)
tab.table.cellWidget(1, 2).setValue(0.0)
check("second target too", on())

tab.lw_phonemes.setCurrentRow(2)                     # OHH
check("phoneme switch -> OHH 10, AHH 0, still on", on() and cmds.getAttr(src + ".OHH") == 10 and cmds.getAttr(src + ".AHH") == 0)

tab.le_source.editingFinished.emit()                 # 포커스만 빠짐 (글자 그대로)
check("focus-out without change keeps solo", on() and cmds.getAttr(src + ".OHH") == 10)

tab.ds_ref.setValue(6.5)
tab.on_ref_changed()
check("ref 6.5 -> OHH 6.5, still on", on() and cmds.getAttr(src + ".OHH") == 6.5)

tab.lw_phonemes.item(3).setCheckState(Qt.Unchecked)  # MBP 체크 해제 (사용자 클릭과 같은 itemChanged)
check("check change keeps solo, MBP restored", on() and "MBP" not in tab.driver.plugs and cmds.getAttr(src + ".OHH") == 6.5)

win.tabs.setCurrentIndex(1)
win.tabs.setCurrentIndex(0)
check("tab switch keeps solo", on() and cmds.getAttr(src + ".OHH") == 6.5)

tab.on_capture()
check("capture keeps solo (re-applied after)", on() and cmds.getAttr(src + ".OHH") == 6.5)

tab.on_build()
tab.on_remove()
check("build / remove network keeps solo", on())

tab.le_source.setText(src2)
tab.on_nodes_changed()
check("source change: old source restored (OHH 3), new source solo", on() and cmds.getAttr(src + ".OHH") == 3
      and tab.driver.source == src2)

# 체크박스를 직접 클릭 -> 꺼지고 원복 (click() = 사용자 클릭과 같은 toggled 경로. 오프스크린에선 QTest 마우스가 안 닿는다)
tab.cb_solo.click()
check("click checkbox -> off", not tab.cb_solo.isChecked() and tab.driver is None)
check("values restored", cmds.getAttr(src2 + ".OHH") == 0 and cmds.getAttr(src2 + ".AHH") == 0)

# 창 닫기 -> 원복
tab.le_source.setText(src)
tab.on_nodes_changed()
tab.lw_phonemes.setCurrentRow(1)
was_on = tab.cb_solo.isChecked()
tab.cb_solo.click()
check("click checkbox -> on (was off: " + str(not was_on) + ")", not was_on and on() and cmds.getAttr(src + ".AHH") == 6.5)
win.close()
check("close window restores", cmds.getAttr(src + ".AHH") == 0 and cmds.getAttr(src + ".OHH") == 3)
print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
