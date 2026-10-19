# -*- coding: utf-8 -*-
# A00550_PoseMapper - JaLi UI 시험 (v01.05, mayapy 2024 오프스크린)  계획서 §11.6 J7
#   mayapy test_ui_jali.py <테스트 씬 .mb>   (씬은 열기만, 저장하지 않는다)
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def near(a, b, tol=2e-3):
    return abs(a - b) < tol


try:
    cmds.file(sys.argv[1], o=True, force=True, executeScriptNodes=False, ignoreVersion=True)
except RuntimeError:
    pass
import scene_fixture   # noqa: E402
scene_fixture.reset_to_original_wiring()
import tools.A00550_PoseMapper as tool   # noqa: E402
from tools.A00550_PoseMapper.app.core import library, network   # noqa: E402
from tools.A00550_PoseMapper.app.ui.pose_map_tab import COL_AXIS, COL_STRENGTH   # noqa: E402

BS, SRC, JALI = "CHN_n_Face_xx_bs", "JALI1:CNT_PHONEMES", "JALI1:CNT_JaLi"
cmds.setAttr(JALI + ".tx", 9)
cmds.setAttr(JALI + ".ty", 9)
win = tool.run(False)
tab = win.pose_tab
tab.le_source.setText(SRC)
tab.le_target.setText(BS)
tab.on_nodes_changed()
check("source without Jaw/Lip -> JaLi node empty", tab.le_jali.text() == "")
cmds.select(JALI)
tab.on_pick_jali()
check("pick CNT_JaLi -> Jaw translateX, Lip translateY", tab.jali_node() == JALI and tab.cmb_jaw.currentText() == "translateX"
      and tab.cmb_lip.currentText() == "translateY")

tab.on_capture()
tab.on_jali_defaults()
check("JALI Defaults: jawOpen jaw, mouthFunnel lip", tab.lib.axis("jawOpen") == "jaw" and tab.lib.axis("mouthFunnel") == "lip")


def row(name):
    for r in range(tab.table.rowCount()):
        if tab.table.item(r, 0).text() == name:
            return r


r = row("jawOpen")
check("table shows Axis Jaw / Strength 1", tab.table.cellWidget(r, COL_AXIS).currentText() == "Jaw"
      and tab.table.cellWidget(r, COL_STRENGTH).value() == 1.0)

tab.cmb_existing.setCurrentIndex(1)       # Replace
tab.on_build()
check("build: JaLi wired to CNT_JaLi", tab.net and network.net_jali(tab.net)[0] == JALI and network.jali_ready(tab.net))
for p in ("AHH",):
    for i in range(tab.lw_phonemes.count()):
        if tab.lw_phonemes.item(i).data(Qt.UserRole) == p:
            tab.lw_phonemes.setCurrentRow(i)
tab.cb_solo.setChecked(True)
cmds.setAttr(JALI + ".tx", 2)
check("Jaw 2 -> jawOpen 0.222 (like the original JALI network)", near(cmds.getAttr(BS + ".jawOpen"), 0.222))

tab.table.cellWidget(r, COL_AXIS).setCurrentIndex(0)                 # -
check("Axis '-' -> JaLi ignored, jawOpen 1.0", near(cmds.getAttr(BS + ".jawOpen"), 1.0)
      and not tab.table.cellWidget(r, COL_STRENGTH).isEnabled())
tab.table.cellWidget(r, COL_AXIS).setCurrentIndex(1)                 # Jaw
tab.table.cellWidget(r, COL_STRENGTH).setValue(0.5)
check("Strength 0.5, Jaw 2 -> 1 + 0.5 x (2/9 - 1) = 0.611", near(cmds.getAttr(BS + ".jawOpen"), 0.6111))

tab.ds_neutral.setValue(4.0)
tab.on_jali_changed()
check("Neutral 4 -> 1 + 0.5 x (2/4 - 1) = 0.75", near(cmds.getAttr(BS + ".jawOpen"), 0.75))
tab.ds_neutral.setValue(9.0)
tab.on_jali_changed()
tab.cb_solo.setChecked(False)

path = os.path.join(tempfile.mkdtemp(), "jali_ui.json")
tab.lib.name = "jali_ui"
tab._write(path)
saved = library.load(path)
check("saved json has jali (translateX / translateY, jawOpen jaw 0.5)", saved.jaw_attr == "translateX"
      and saved.axis("jawOpen") == "jaw" and near(saved.strength("jawOpen"), 0.5, 1e-6))

# 다른 노드 쌍에 Connect - JaLi 칸 비움 = Source 에 Jaw / Lip 이 있으면 Source
cmds.namespace(add="avatar")
s2 = cmds.createNode("transform", n="avatar:JALI_IN")
for a in ("AHH", "Jaw", "Lip"):
    cmds.addAttr(s2, ln=a, at="double", k=True)
cmds.setAttr(s2 + ".Jaw", 4.5)
cmds.setAttr(s2 + ".Lip", 9)
t2 = cmds.createNode("transform", n="avatar:ARKIT")
cmds.addAttr(t2, ln="jawOpen", at="double", k=True)
saved.jaw_attr, saved.lip_attr = "Jaw", "Lip"
from tools.A00550_PoseMapper.app.ui.connect_dialog import ConnectDialog   # noqa: E402
dlg = ConnectDialog(saved, tab._log, tab, jali_node="")
dlg.le_src.setText(s2)
dlg.le_tgt.setText(t2)
dlg.le_prefix.setText("avatar_")
dlg.update_preview()
check("connect preview mentions JaLi", "JaLi: avatar:JALI_IN.Jaw" in dlg.lb_preview.text())
dlg.on_connect()
cmds.setAttr(s2 + ".AHH", 10)
want = saved.get("AHH", "jawOpen") * (1 + 0.5 * (4.5 / 9.0 - 1))
check("connected pair follows its own Jaw 4.5: {0:.3f} = {1:.3f}".format(cmds.getAttr(t2 + ".jawOpen"), want),
      near(cmds.getAttr(t2 + ".jawOpen"), want))

# 다시 고르면 노드망에서 JaLi 칸이 채워진다
tab.le_source.setText("")
tab.on_nodes_changed()
tab.le_source.setText(SRC)
tab.on_nodes_changed()
check("re-pick source -> JaLi node from network", tab.le_jali.text() == JALI and tab.lib.axis("jawOpen") == "jaw")

# Capture 를 JaLi 가 neutral 이 아닐 때 하면 경고
cmds.setAttr(JALI + ".tx", 3)
tab.on_capture()
check("capture with JaLi off-neutral warns", "JaLi is not at Neutral while capturing" in win.log_view.toPlainText()
      and tab.lib.axis("jawOpen") == "jaw")
win.close()
print("RESULT", "OK" if all(R) else "{0} FAILED".format(R.count(False)))
maya.standalone.uninitialize()
