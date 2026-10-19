# -*- coding: utf-8 -*-
# A00550_PoseMapper - Pose Map 탭 오프스크린 UI 시험 (mayapy 2024)
#   mayapy test_ui_pose_map.py <테스트 씬 .mb>   (씬은 열기만, 저장하지 않는다)
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
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


def near(a, b, tol=2e-3):
    return abs(a - b) < tol


def row_of(tab, name):
    for r in range(tab.table.rowCount()):
        if tab.table.item(r, 0).text() == name:
            return r
    return -1


def select_phoneme(tab, p):
    for i in range(tab.lw_phonemes.count()):
        if tab.lw_phonemes.item(i).data(Qt.UserRole) == p:
            tab.lw_phonemes.setCurrentRow(i)
            return


try:
    cmds.file(sys.argv[1], o=True, force=True, executeScriptNodes=False, ignoreVersion=True)
except RuntimeError:
    pass
import tools.A00550_PoseMapper as tool   # noqa: E402
from tools.A00550_PoseMapper.app.core import library, network   # noqa: E402
win = tool.run(False)
tab = win.pose_tab
SRC, BS = "JALI1:JALI_IN", "CHN_n_Face_xx_bs"
check("pose tab is real", hasattr(tab, "on_capture"))

tab.le_source.setText(SRC)
tab.le_target.setText(BS)
tab.on_nodes_changed()
check("phoneme list 20, Jaw/Lip unchecked", tab.lw_phonemes.count() == 20 and "Jaw" not in tab._phoneme_names()
      and len(tab._phoneme_names()) == 18)
check("target table 51 rows", tab.table.rowCount() == 51)

tab.on_capture()
check("capture -> AHH jawOpen 1.0", near(tab.lib.get("AHH", "jawOpen"), 1.0))
select_phoneme(tab, "AHH")
r = row_of(tab, "jawOpen")
check("table shows AHH jawOpen 1.0", near(tab.table.cellWidget(r, 2).value(), 1.0))
tab.cb_used.setChecked(True)
visible = [tab.table.item(i, 0).text() for i in range(tab.table.rowCount()) if not tab.table.isRowHidden(i)]
check("Used only -> 3 rows {0}".format(visible), sorted(visible) == ["jawOpen", "mouthLowerDownLeft", "mouthLowerDownRight"])
tab.cb_used.setChecked(False)

before = cmds.getAttr("JALI1:CNT_PHONEMES.AHH")
tab.cb_solo.setChecked(True)
check("solo AHH -> bs.jawOpen 1.0 (old network)", near(cmds.getAttr(BS + ".jawOpen"), 1.0))

tab.cmb_existing.setCurrentIndex(1)                     # Replace (테스트 씬은 51개 전부 이미 구동 중)
tab.on_build()
check("build with Replace -> network", tab.net and len(network.chains(tab.net)) > 10)
tab.table.cellWidget(r, 2).setValue(0.8)
check("slider edit -> bs.jawOpen 0.8 live", near(cmds.getAttr(BS + ".jawOpen"), 0.8))

tab.ds_ref.setValue(5.0)
tab.on_ref_changed()
check("ref 5.0 -> AHH solo at 5, jawOpen still 0.8", near(cmds.getAttr("JALI1:CNT_PHONEMES.AHH"), 5.0) and near(cmds.getAttr(BS + ".jawOpen"), 0.8))
tab.ds_ref.setValue(7.25)
tab.on_ref_changed()
check("ref 7.25 (any real) -> net pmRef", near(cmds.getAttr(tab.net + ".pmRef"), 7.25) and near(cmds.getAttr(BS + ".jawOpen"), 0.8))

select_phoneme(tab, "MBP")
check("switch phoneme while solo -> MBP on, AHH 0", near(cmds.getAttr("JALI1:CNT_PHONEMES.MBP"), 7.25) and cmds.getAttr("JALI1:CNT_PHONEMES.AHH") == 0)
tab.cb_solo.setChecked(False)
check("solo off -> restored", cmds.getAttr("JALI1:CNT_PHONEMES.AHH") == before)

path = os.path.join(tempfile.mkdtemp(), "ui_lib.json")
tab.lib.name = "ui_lib"
tab._write(path)
saved = library.load(path)
check("save -> json (ref 7.25, AHH jawOpen 0.8)", near(saved.ref_value, 7.25) and near(saved.get("AHH", "jawOpen"), 0.8))

# 다른 노드 쌍에 연결 (Connect 대화상자)
cmds.namespace(add="avatar")
s2 = cmds.createNode("transform", n="avatar:JALI_IN")
for a in ("AHH", "MBP", "OHH"):
    cmds.addAttr(s2, ln=a, at="double", k=True)
t2 = cmds.createNode("transform", n="avatar:ARKIT")
for a in ("jawOpen", "mouthClose"):
    cmds.addAttr(t2, ln=a, at="double", k=True)
from tools.A00550_PoseMapper.app.ui.connect_dialog import ConnectDialog   # noqa: E402
dlg = ConnectDialog(saved, tab._log, tab)
dlg.le_src.setText(s2)
dlg.le_tgt.setText(t2)
dlg.le_prefix.setText("avatar_")
dlg.ds_ref.setValue(10.0)
dlg.update_preview()
check("connect preview counts", "targets found" in dlg.lb_preview.text() and "missing" in dlg.lb_preview.text())
dlg.on_connect()
cmds.setAttr(s2 + ".AHH", 10)
check("connected to other pair (ref 10): jawOpen 0.8", dlg.result_net and near(cmds.getAttr(t2 + ".jawOpen"), 0.8))
check("log reports missing", "Targets not on avatar:ARKIT" in win.log_view.toPlainText())

n_bw = len(cmds.ls(type="blendWeighted"))
tab.on_remove()
check("remove network", tab.net is None and len(cmds.ls(type="blendWeighted")) < n_bw)

tab.cmb_lib.setCurrentText("jali_arkit_0040_default")
tab.on_load()
check("load default library", tab.lib.name == "jali_arkit_0040_default" and near(tab.lib.get("AHH", "jawOpen"), 1.0))
win.close()
print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
