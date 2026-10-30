# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.31 - View > Layers (애니메이션 레이어 목록 · 선택 · Mute/Solo/Lock · Expand) 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_anim_layers.py
# 씬 : cube 키 + L1, L2, L3(L1 의 자식). 그래프 에디터는 mayapy 에 없어 필터는 (0, filter) 만 본다.
# QApplication 은 maya.standalone.initialize() 보다 먼저 (qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
from PySide2.QtCore import Qt   # noqa: E402
APP = QApplication.instance() or QApplication(sys.argv)

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

from tools.A00110_animTool_V02.app.core import AnimLayerManager as ALM   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def pump(n=3):
    for _ in range(n):
        APP.processEvents()


def sel():
    return [l for l in (cmds.ls(type="animLayer") or []) if cmds.animLayer(l, q=True, selected=True)]


def pref():
    return [l for l in (cmds.ls(type="animLayer") or []) if cmds.animLayer(l, q=True, preferred=True)]


# ---------------------------------------------------------------- core
cmds.file(new=True, force=True)
check("C0 no layers : tree / rows / snapshot empty", ALM.tree() == [] and ALM.rows() == [] and ALM.snapshot() == ())

cube = cmds.polyCube(n="ctl")[0]
cmds.setKeyframe(cube, at="tx", t=1, v=0)
L1 = cmds.animLayer("L1")
L2 = cmds.animLayer("L2")
L3 = cmds.animLayer("L3", parent=L1)
rows = ALM.rows()
check("C1 editor order : L2 (top), L1, L3 under L1, BaseAnimation last",
      [r["name"] for r in rows] == ["L2", "L1", "L3", "BaseAnimation"] and [r["depth"] for r in rows] == [0, 0, 1, 0],
      [(r["name"], r["depth"]) for r in rows])
tree = ALM.tree()
check("C2 tree : L1 node has child L3, base has none",
      [n["info"]["name"] for n in tree] == ["L2", "L1", "BaseAnimation"] and [c["info"]["name"] for c in tree[1]["children"]] == ["L3"])
check("C3 rows carry preferred + base flags", all("preferred" in r for r in rows) and rows[-1]["base"] is True and rows[0]["base"] is False)

chosen = ALM.set_selected(["L2"])
check("C4 set_selected one : selected + active", chosen == ["L2"] and sel() == ["L2"] and pref() == ["L2"], (sel(), pref()))
chosen = ALM.set_selected(["L1", "L3"])
check("C5 set_selected two : both selected, active unchanged", sorted(chosen) == ["L1", "L3"] and sorted(sel()) == ["L1", "L3"] and pref() == ["L2"], (sel(), pref()))
ALM.set_selected(["L1"])
check("C5b set_selected one again : active moves (only one preferred)", pref() == ["L1"], pref())
check("C6 set_selected ignores unknown names", ALM.set_selected(["nope", "L2"]) == ["L2"] and sel() == ["L2"])

check("C7 set_flag mute / solo / lock", ALM.set_flag("L1", "mute", True) and cmds.animLayer("L1", q=True, mute=True)
      and ALM.set_flag("L2", "solo", True) and cmds.animLayer("L2", q=True, solo=True)
      and ALM.set_flag("L3", "lock", True) and cmds.animLayer("L3", q=True, lock=True))
check("C8 set_flag off again", ALM.set_flag("L1", "mute", False) and not cmds.animLayer("L1", q=True, mute=True)
      and ALM.set_flag("L2", "solo", False) and ALM.set_flag("L3", "lock", False))
check("C9 BaseAnimation : mute / solo rejected, lock allowed",
      ALM.set_flag("BaseAnimation", "mute", True) is False and ALM.set_flag("BaseAnimation", "solo", True) is False
      and ALM.set_flag("BaseAnimation", "lock", True) and cmds.animLayer("BaseAnimation", q=True, lock=True)
      and ALM.set_flag("BaseAnimation", "lock", False))
check("C10 set_flag : unknown flag / layer -> False", ALM.set_flag("L1", "ghost", True) is False and ALM.set_flag("nope", "mute", True) is False)
snap = ALM.snapshot()
cmds.animLayer("L3", e=True, mute=True)
check("C11 snapshot changes when a flag changes", ALM.snapshot() != snap and len(snap) == 4)
cmds.animLayer("L3", e=True, mute=False)
check("C12 graph_editor_filter without a Graph Editor : (0, filter)", ALM.graph_editor_filter(True) == (0, "selected")
      and ALM.graph_editor_filter(False) == (0, "allAffecting"))

# ---------------------------------------------------------------- UI
from tools.A00110_animTool_V02.app.ui.main_window import MainWindow, LAYERS_WINDOW_OBJECT_NAME   # noqa: E402
ALM.set_selected(["L2"])
win = MainWindow()
win.show()
pump()
# View > Layers 탭을 보이게(폴링은 보이는 동안만 돈다)
win.tabs.setCurrentIndex([win.tabs.tabText(i) for i in range(win.tabs.count())].index("View"))
win.view_tabs.setCurrentIndex(1)
pump()
check("U0 Layers tab visible", win.tw_al_layers.isVisible())
labels = [win.view_tabs.tabText(i) for i in range(win.view_tabs.count())]
check("U1 View sub tabs : Graph Focus + Layers", labels == ["Graph Focus", "Layers"], labels)
tw = win.tw_al_layers
check("U2 tree filled : 3 top-level (L2, L1, Base), L3 under L1, expanded",
      tw.topLevelItemCount() == 3 and [tw.topLevelItem(i).text(0) for i in range(3)] == ["L2", "L1", "BaseAnimation"]
      and tw.topLevelItem(1).childCount() == 1 and tw.topLevelItem(1).child(0).text(0) == "L3" and tw.topLevelItem(1).isExpanded())
check("U3 header / buttons english", [tw.headerItem().text(i) for i in range(4)] == ["Layer", "Mute", "Solo", "Lock"]
      and win.btn_al_ge_selected.text() == "Graph Editor: Selected Only" and win.btn_al_ge_all.text() == "Graph Editor: All Layers")
check("U4 selected layer highlighted + active bold", [it.text(0) for it in tw.selectedItems()] == ["L2"] and tw.topLevelItem(0).font(0).bold()
      and not tw.topLevelItem(1).font(0).bold())
base_item = tw.topLevelItem(2)
check("U5 BaseAnimation row : no Mute / Solo checkbox, Lock checkbox present",
      base_item.data(1, Qt.CheckStateRole) is None and base_item.data(2, Qt.CheckStateRole) is None
      and base_item.data(3, Qt.CheckStateRole) is not None)

# 행 클릭 -> 마야 선택 + 활성
tw.clearSelection()
tw.topLevelItem(1).setSelected(True)        # L1
pump()
check("U6 selecting a row selects + activates the layer in Maya", sel() == ["L1"] and pref() == ["L1"] and tw.topLevelItem(1).font(0).bold()
      and not tw.topLevelItem(0).font(0).bold(), (sel(), pref()))
tw.topLevelItem(1).child(0).setSelected(True)   # + L3
pump()
check("U7 two rows -> two selected layers, active stays", sorted(sel()) == ["L1", "L3"] and pref() == ["L1"], (sel(), pref()))

# 체크 -> 플래그
l2_item = tw.topLevelItem(0)
l2_item.setCheckState(1, Qt.Checked)
pump()
check("U8 ticking Mute mutes the layer", cmds.animLayer("L2", q=True, mute=True))
l2_item.setCheckState(1, Qt.Unchecked)
pump()
check("U9 unticking Mute unmutes", not cmds.animLayer("L2", q=True, mute=True))
l2_item.setCheckState(2, Qt.Checked)
pump()
check("U10 Solo tick", cmds.animLayer("L2", q=True, solo=True))
l2_item.setCheckState(2, Qt.Unchecked)
l2_item.setCheckState(3, Qt.Checked)
pump()
check("U11 Lock tick", cmds.animLayer("L2", q=True, lock=True) and not cmds.animLayer("L2", q=True, solo=True))
l2_item.setCheckState(3, Qt.Unchecked)
pump()

# 마야 쪽 변화 -> 폴링이 따라간다
cmds.animLayer("L3", e=True, mute=True)
L4 = cmds.animLayer("L4")
win._al_poll()
pump()
check("U12 poll follows Maya : new layer on top, L3 mute ticked",
      tw.topLevelItem(0).text(0) == "L4" and win.al_item("L3").checkState(1) == Qt.Checked, [tw.topLevelItem(i).text(0) for i in range(tw.topLevelItemCount())])
win.cb_al_auto.setChecked(False)
cmds.delete(L4)
win._al_poll()
check("U13 auto refresh off : poll does nothing", tw.topLevelItem(0).text(0) == "L4")
win.cb_al_auto.setChecked(True)
win._al_poll()
check("U14 auto refresh on : deleted layer gone", tw.topLevelItem(0).text(0) == "L2")
cmds.animLayer("L3", e=True, mute=False)

# Graph Editor 필터 버튼 (mayapy 엔 그래프 에디터가 없다)
win.te_log.clear() if hasattr(win.te_log, "clear") else None
win.btn_al_ge_selected.click()
pump()
check("U15 Graph Editor button without an editor -> warning in log", "[WARN] No Graph Editor is open." in win.te_log.toPlainText())

# Expand : 본문이 별도 창으로 가고 돌아온다
body = win.al_panel.body.parentWidget() if hasattr(win.al_panel.body, "parentWidget") else None
win.al_panel.toggle()
pump()
expanded_windows = [w for w in QApplication.topLevelWidgets() if w.objectName() == LAYERS_WINDOW_OBJECT_NAME]
check("U16 Expand : separate window exists, tree lives in it", win.al_panel.is_expanded() and len(expanded_windows) == 1
      and tw.window() is expanded_windows[0], [w.objectName() for w in expanded_windows])
check("U17 Expand : tree still works there (select L2)", (tw.clearSelection(), tw.topLevelItem(0).setSelected(True), pump(), sel() == ["L2"])[-1], sel())
win.al_panel.collapse()
pump()
check("U18 Collapse : tree back in the tool window", not win.al_panel.is_expanded() and tw.window() is win)

# Pin(Always on Top) 이 Expand 창에도 걸린다 (v02.32)
def on_top(widget):
    return bool(widget.windowFlags() & Qt.WindowStaysOnTopHint)


check("P1 both expand panels are stay-on-top by construction (v02.33)", win.al_panel.stay_on_top() is True and win.cf_panel.stay_on_top() is True
      and not on_top(win))
win.al_panel.toggle()
pump()
lw = tw.window()
check("P2 expanded Layers window has WindowStaysOnTopHint from creation, pin off", win.al_panel.is_expanded() and lw is not win and on_top(lw)
      and lw.isVisible())
win.toggle_always_on_top(True)
pump()
check("P3 Pin on : tool on top, expanded window still on top + visible", on_top(win) and on_top(tw.window()) and tw.window().isVisible())
win.toggle_always_on_top(False)
pump()
check("P4 Pin off : tool normal, expanded window STAYS on top (independent of Pin)", not on_top(win) and on_top(tw.window()) and tw.window().isVisible())
win.al_panel.collapse()
pump()
win.cf_panel.toggle()
pump()
check("P5 Curve > Filters expand window is on top as well", on_top(win.cf_panel._window))
win.cf_panel.set_stay_on_top(False)
pump()
check("P6 set_stay_on_top(False) on a live window clears the flag and keeps it visible", not on_top(win.cf_panel._window) and win.cf_panel._window.isVisible())
win.cf_panel.collapse()
pump()

win.close()
pump()
print("\n%d / %d passed" % (sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if sum(R) == len(R) else 1)
