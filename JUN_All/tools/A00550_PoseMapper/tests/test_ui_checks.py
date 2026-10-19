# -*- coding: utf-8 -*-
# A00550_PoseMapper - Source 목록 다중 선택 · 체크 (Check Sel / Uncheck Sel / Check All 토글) 오프스크린 시험 (mayapy 2024, 합성 씬)
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, QItemSelectionModel
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


src = cmds.createNode("transform", n="JALI_IN")
for a in ("Jaw", "Lip", "AHH", "AAA", "Eh", "OHH", "MBP"):
    cmds.addAttr(src, ln=a, at="double", k=True)
tgt = cmds.createNode("transform", n="ARKIT")
cmds.addAttr(tgt, ln="jawOpen", at="double", k=True)

import tools.A00550_PoseMapper as tool   # noqa: E402
win = tool.run(False)
win.show()
tab = win.pose_tab
tab.le_source.setText(src)
tab.le_target.setText(tgt)
tab.on_nodes_changed()
lw = tab.lw_phonemes


def checked():
    return tab._phoneme_names()


def select(names):
    lw.clearSelection()
    for i in range(lw.count()):
        if lw.item(i).data(Qt.UserRole) in names:
            lw.selectionModel().select(lw.model().index(i, 0), QItemSelectionModel.Select)


check("default: Jaw/Lip unchecked", checked() == ["AHH", "AAA", "Eh", "OHH", "MBP"])
check("toggle label = Check All (not all checked)", tab.btn_check_all.text() == "Check All")
check("extended selection", lw.selectionMode() == lw.ExtendedSelection)

select(["AHH", "AAA", "Eh"])
tab._set_checks(tab._selected_items(), False)
check("Uncheck Sel (3)", checked() == ["OHH", "MBP"])
select(["Jaw", "AHH"])
tab._set_checks(tab._selected_items(), True)
check("Check Sel (2)", checked() == ["Jaw", "AHH", "OHH", "MBP"])
check("state remembered", tab._checked["Jaw"] is True and tab._checked["AAA"] is False)

tab.on_toggle_all()
check("toggle -> all checked, label Uncheck All", len(checked()) == 7 and tab.btn_check_all.text() == "Uncheck All")
tab.on_toggle_all()
check("toggle -> none checked, label Check All", checked() == [] and tab.btn_check_all.text() == "Check All")

# 실제 클릭: 3행을 고르고 그중 하나의 체크박스를 누르면 3행 전부 (공용 체크 동작)
select(["AAA", "Eh", "OHH"])
item = lw.item(3)                                    # AAA
rect = lw.visualItemRect(item)
pos = None
for x in range(rect.left(), rect.left() + 30):
    p = rect.center()
    p.setX(x)
    if tab.chk_phonemes.check_hit(p) is item:
        pos = p
        break
QTest.mouseClick(lw.viewport(), Qt.LeftButton, Qt.NoModifier, pos)
check("click checkbox of a selected row -> all 3 checked", checked() == ["AAA", "Eh", "OHH"] and tab._checked["OHH"] is True)

# Solo 중 체크가 바뀌어도 Solo 는 켜진 채 - 체크 해제된 음소만 원복 (v01.03)
lw.setCurrentRow(2)                                  # AHH
lw.item(2).setCheckState(Qt.Checked)
tab.cb_solo.setChecked(True)
check("solo on", tab.driver is not None and cmds.getAttr(src + ".AHH") == 10.0)
select(["AHH"])
tab._set_checks(tab._selected_items(), False)
check("check change keeps solo (v01.03), unchecked AHH restored", tab.cb_solo.isChecked() and tab.driver is not None and cmds.getAttr(src + ".AHH") == 0.0)

lw.clearSelection()
tab._set_checks(tab._selected_items(), True)
check("no selection -> WARN", "Select attributes in the Source list first" in win.log_view.toPlainText())
print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
