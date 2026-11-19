# -*- coding: utf-8 -*-
# A00275_skinTool_V01 v01.43 - Weights > Transfer > Target mode = Classic 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_transfer_classic_ui.py
# 예전 Weights > Classic 하위 탭을 없애고 Transfer 의 Target mode 로 옮겼다. 위젯 · 핸들러는 그대로인지,
# 모드 전환 때 보이는 것이 맞는지, Classic 의 두 버튼이 실제로 도는지 본다.
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
from tools.A00275_skinTool_V01.app.ui.main_window import MainWindow   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


logs = []
win = MainWindow()
win.log = logs.append
pages = [win.weights_tabs.tabText(i) for i in range(win.weights_tabs.count())]
check("no Classic sub tab, Transfer is first", "Classic" not in pages and pages[0] == "Transfer", pages)
win.show()
app.processEvents()


def visible(w):
    return w.isVisibleTo(win)


src_widgets = (win.lbl_transfer_desc, win.tsl_transfer_src, win.grp_transfer_opts,
               win.lbl_transfer_hint, win.btn_transfer_run)

check("default mode = Scene selection, Classic panel hidden",
      win.rb_transfer_sel.isChecked() and not visible(win.transfer_classic_panel)
      and all(visible(w) for w in src_widgets) and not visible(win.tsl_transfer_tgt))

win.rb_transfer_classic.click()
app.processEvents()
check("Classic mode : Classic panel shown, transfer widgets hidden",
      win.transfer_mode() == win.TRANSFER_MODE_CLASSIC and visible(win.transfer_classic_panel)
      and not any(visible(w) for w in src_widgets) and not visible(win.tsl_transfer_tgt))
check("Classic panel keeps the old widgets (engine, mode combo, From/To, two buttons)",
      all(visible(w) for w in (win.rb_classic_kangaroo, win.rb_classic_native, win.cmb_classic_mode,
                               win.tsl_classic_from, win.tsl_classic_to,
                               win.btn_joints_to_joints, win.btn_meshes_to_meshes)))

win.rb_transfer_pairs.click()
app.processEvents()
check("Target list mode : target list shown, Classic panel hidden",
      visible(win.tsl_transfer_tgt) and visible(win.tsl_transfer_src) and not visible(win.transfer_classic_panel))
win.rb_transfer_sel.click()
app.processEvents()
check("back to Scene selection", not visible(win.tsl_transfer_tgt) and not visible(win.transfer_classic_panel)
      and visible(win.btn_transfer_run))

# ---- 모드를 바꾸면 창 높이를 다시 맞춘다 (tab_fit.fit_later)
def settle():
    for _ in range(5):
        app.processEvents()


from PySide2.QtCore import QRect   # noqa: E402
win.tab_fit._available_geometry = lambda: QRect(0, 0, 2560, 1392)   # 오프스크린 화면 높이 제한을 풀어 둔다(tab_fit 시험과 같다)
win.rb_transfer_sel.click(); settle()
h_sel = win.height()
win.rb_transfer_classic.click(); settle()
h_classic = win.height()
win.rb_transfer_sel.click(); settle()
check("window height follows the mode (refit on switch)", h_classic != h_sel and win.height() == h_sel,
      (h_sel, h_classic, win.height()))

# ---- Classic 실제 동작 (Native 엔진)
cmds.file(new=True, force=True)
cmds.polyPlane(name="m", w=4, h=4, sx=4, sy=4)
cmds.select(clear=True)
cmds.joint(name="jA", position=(-2, 0, 0))
cmds.select(clear=True)
cmds.joint(name="jB", position=(2, 0, 0))
cmds.select(clear=True)
cmds.joint(name="jC", position=(0, 0, 2))
skin = cmds.skinCluster(["jA", "jB", "jC"], "m", toSelectedBones=True)[0]
cmds.skinPercent(skin, "m.vtx[*]", transformValue=[("jA", 0.6), ("jB", 0.4)])

win.rb_transfer_classic.click()
win.rb_classic_native.setChecked(True)
win.tsl_classic_from.set_items(["jA"])
win.tsl_classic_to.set_items(["jC"])
cmds.select("m")
logs[:] = []
win.btn_joints_to_joints.click()
wa = cmds.skinPercent(skin, "m.vtx[0]", q=True, transform="jA")
wc = cmds.skinPercent(skin, "m.vtx[0]", q=True, transform="jC")
check("Classic Joints to Joints (Native) moves jA -> jC", abs(wa) < 1e-6 and abs(wc - 0.6) < 1e-6, (wa, wc, logs))

cmds.polyPlane(name="m2", w=4, h=4, sx=4, sy=4)
cmds.select(clear=True)
skin2 = cmds.skinCluster(["jA", "jB", "jC"], "m2", toSelectedBones=True)[0]
cmds.skinPercent(skin2, "m2.vtx[*]", transformValue=[("jB", 1.0)])
win.tsl_classic_from.set_items(["m"])
win.tsl_classic_to.set_items(["m2"])
cmds.select(clear=True)
logs[:] = []
win.btn_meshes_to_meshes.click()
w2 = cmds.skinPercent(cmds.ls(cmds.listHistory("m2"), type="skinCluster")[0], "m2.vtx[0]", q=True, transform="jC")
check("Classic Meshes to Meshes (Native) copies m -> m2", abs(w2 - 0.6) < 1e-3, (w2, logs))

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
