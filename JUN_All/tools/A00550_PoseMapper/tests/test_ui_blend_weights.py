# -*- coding: utf-8 -*-
# A00550_PoseMapper - Blend Weights 탭 오프스크린 UI 시험 (mayapy 2024)
#   mayapy test_ui_blend_weights.py <테스트 씬 .mb>   (씬은 열기만, 저장하지 않는다)
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication
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


try:
    cmds.file(sys.argv[1], o=True, force=True, executeScriptNodes=False, ignoreVersion=True)
except RuntimeError:
    pass
import tools.A00550_PoseMapper as tool   # noqa: E402
win = tool.run(False)
tab = win.bw_tab
win.tabs.setCurrentWidget(tab)
check("window + 2 tabs", win.tabs.count() == 2 and win.tabs.tabText(1) == "Blend Weights")

tab.cb_missing_only.setChecked(True)
check("missing-only filter lists bw_mouthFunnel", [tab.cmb_node.itemText(i) for i in range(tab.cmb_node.count())] == ["JALI1:bw_mouthFunnel"])
tab.cb_missing_only.setChecked(False)
tab.cmb_node.setCurrentText("JALI1:bw_mouthFunnel")
check("table 6 rows", tab.table.rowCount() == 6)
check("row 5 flagged", "no weight element" in tab.table.item(5, 4).text())
out_before = cmds.getAttr("JALI1:bw_mouthFunnel.output")
tab.on_create_missing()
check("create missing -> state OK, output same", tab.table.item(5, 4).text() == "OK" and
      abs(cmds.getAttr("JALI1:bw_mouthFunnel.output") - out_before) < 1e-6)
tab.table.cellWidget(5, 2).setValue(0.03)
check("edit weight cell -> weight[5] = 0.03", abs(cmds.getAttr("JALI1:bw_mouthFunnel.weight[5]") - 0.03) < 1e-6)
tab.le_source.setText("JALI1:JALI_IN.AHH")
tab.ds_weight.setValue(0.02)
tab.on_add()
check("add AHH -> row 7 with weight", tab.table.rowCount() == 7 and abs(cmds.getAttr("JALI1:bw_mouthFunnel.weight[6]") - 0.02) < 1e-6)
tab.table.selectRow(6)
tab.on_remove()
check("remove row -> 6 rows", tab.table.rowCount() == 6 and 6 not in cmds.getAttr("JALI1:bw_mouthFunnel.input", mi=True))
tab.table.selectRow(0)
tab.on_select_source()
check("select source", cmds.ls(sl=True) == ["JALI1:JALI_IN"])
tab.le_source.setText("JALI1:JALI_IN.NOPE")
tab.on_add()
check("bad source -> ERROR", "[ERROR] Source not found" in win.log_view.toPlainText())
print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
