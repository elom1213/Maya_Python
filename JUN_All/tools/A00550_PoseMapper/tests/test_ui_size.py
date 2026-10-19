# -*- coding: utf-8 -*-
# A00550_PoseMapper - 창 크기 시험 (v01.04, mayapy 오프스크린, 합성 씬)
# 창은 언제든 자유롭게 줄이고 늘릴 수 있어야 하고, Save / Build / Capture / 탭 이동이 크기를 바꾸면 안 된다.
import os, sys, tempfile
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone; maya.standalone.initialize()
import maya.cmds as cmds
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
src = cmds.createNode("transform", n="JALI_IN")
for a in ("AHH", "OHH"): cmds.addAttr(src, ln=a, at="double", k=True)
tgt = cmds.createNode("transform", n="ARKIT")
for a in ("jawOpen", "mouthFunnel"): cmds.addAttr(tgt, ln=a, at="double", k=True)
import tools.A00550_PoseMapper as tool
win = tool.run(False); app.processEvents(); app.processEvents()
tab = win.pose_tab
R = []
def check(n, c): R.append(c); print(("PASS " if c else "FAIL ") + n)
def sz(): app.processEvents(); return (win.width(), win.height())
opened = sz()
print("opened at", opened, "content min", win.tabs.minimumSizeHint().width(), "window minSizeHint", win.minimumSizeHint().width(), win.minimumSizeHint().height())
avail = win.screen().availableGeometry()
want_w = min(win.tabs.minimumSizeHint().width() + win.minimumSizeHint().width() - win.tabs_scroll.minimumSizeHint().width(), avail.width())
print("screen", avail.width(), avail.height())
check("opens fitted to content (clipped to screen %dx%d)" % (avail.width(), avail.height()), abs(opened[0] - want_w) < 30 and opened[1] <= avail.height())
win.resize(420, 420)
check("shrink freely to 420x420 -> %s" % (sz(),), sz() == (420, 420))
win.resize(1500, 1000)
check("grow freely 1500x1000", sz() == (1500, 1000))
win.resize(500, 600); before = sz()
tab.le_source.setText(src); tab.le_target.setText(tgt); tab.on_nodes_changed()
deep = os.path.join(tempfile.mkdtemp(), "a_very_long_folder_name_for_testing_the_status_label_width", "and_another_long_one")
os.makedirs(deep)
tab.lib.name = "jali_arkit_0040_default_Test_01_with_a_really_long_library_name"
tab._write(os.path.join(deep, tab.lib.name + ".json"))
check("Save keeps size %s" % (sz(),), sz() == before)
tab.on_build(); tab.on_capture(); tab.on_build()
check("Build / Capture keep size %s" % (sz(),), sz() == before)
check("status label shows the long path in tooltip", deep in tab.lb_status.toolTip())
win.tabs.setCurrentIndex(1); win.bw_tab.refresh_nodes()
check("Blend Weights tab keeps size", sz() == before)
win.resize(380, 380)
check("still shrinks after all commands -> %s" % (sz(),), sz() == (380, 380))
print("RESULT", "OK" if all(R) else "%d FAILED" % R.count(False))
maya.standalone.uninitialize()
