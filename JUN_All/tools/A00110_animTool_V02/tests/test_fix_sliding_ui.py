# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.48 - Bake > Fix Sliding 탭 UI 시험 (mayapy + 오프스크린 PySide2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_fix_sliding_ui.py
# 계획서 docs/plans/a00110_fix_sliding_plan.md §6 의 16~19 + 실제 실행 한 번.
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


HL = "JUN_A00110_holdLayer_"
FSV = "JUN_A00110_fixSliding_"


def clear_optvars():
    for k in cmds.optionVar(list=True) or []:
        if k.startswith(HL) or k.startswith(FSV):
            cmds.optionVar(remove=k)


clear_optvars()
cmds.file(new=True, force=True)
foot = cmds.spaceLocator(n="foot")[0]
for f in range(1, 41):
    x = min(f, 10) * 1.0 if f <= 20 else 10.0 + min(f - 20, 10)
    cmds.setKeyframe(foot, at="tx", t=f, v=x)
lay = cmds.animLayer("AnimLayer1")
cmds.animLayer("AnimLayer2")
cmds.select(foot)
cmds.animLayer(lay, e=True, attribute=[foot + ".translateX"])
cmds.select(clear=True)

from tools.A00110_animTool_V02.app.ui import main_window as MWmod   # noqa: E402
from tools.A00110_animTool_V02.app.ui.main_window import MainWindow   # noqa: E402
from tools.A00110_animTool_V02.app.core import HoldLayerManager as HLM   # noqa: E402
from tools.A00110_animTool_V02.app.core import FixSlidingManager as FS   # noqa: E402
from tools.A00110_animTool_V02.app.core import LayerKeyManager as LKM   # noqa: E402

win = MainWindow()
win.show()
APP.processEvents()

# ---------------- 16 탭 · 기본값
names = [win.tabs.tabText(i) for i in range(win.tabs.count())]
win.tabs.setCurrentIndex(names.index("Bake"))
sub = [win.bake_tabs.tabText(i) for i in range(win.bake_tabs.count())]
check("16 Bake > Fix Sliding sub tab exists (after Counter Layer)",
      "Fix Sliding" in sub and sub.index("Fix Sliding") == sub.index("Counter Layer") + 1, sub)
win.bake_tabs.setCurrentIndex(sub.index("Fix Sliding"))
APP.processEvents()
check("16b defaults: smooth 5, 2 %, G 4, M 3, XYZ, T R, Layer Blend / Clamp / Lock / Debug on",
      win.sp_fs_smooth.value() == 5 and abs(win.sp_fs_threshold.value() - 2.0) < 1e-9
      and win.sp_fs_merge_gap.value() == 4 and win.sp_fs_min_span.value() == 3
      and all(c.isChecked() for c in (win.cb_fs_x, win.cb_fs_y, win.cb_fs_z, win.cb_fs_t, win.cb_fs_r,
                                       win.cb_fs_layer_blend, win.cb_fs_clamp, win.cb_fs_lock, win.cb_fs_debug)))
win.cb_fs_layer_blend.setChecked(False)
check("16c Layer Blend off disables Clamp / Lock", not win.cb_fs_clamp.isEnabled() and not win.cb_fs_lock.isEnabled())
win.cb_fs_layer_blend.setChecked(True)
check("16d Layer Blend on enables them again", win.cb_fs_clamp.isEnabled() and win.cb_fs_lock.isEnabled())

# ---------------- 19 레이어 · N 을 이 탭에서 고른다 (v02.49)
items = [win.cmb_fs_layer.itemText(i) for i in range(win.cmb_fs_layer.count())]
check("19 own Layer combo (no BaseAnimation) + Frames before N (default = Hot Key 10)",
      sorted(items) == ["AnimLayer1", "AnimLayer2"] and win.sp_fs_offset.value() == 10 and not hasattr(win, "lbl_fs_layer_blend"),
      (items, win.sp_fs_offset.value()))
win.cmb_fs_layer.setCurrentIndex(win.cmb_fs_layer.findData("AnimLayer2"))
win.sp_fs_offset.setValue(7)
check("19b choosing here does not change Hot Key > Main", HLM.load_settings()["layer"] != "AnimLayer2"
      and HLM.load_settings()["offset"] == 10, HLM.load_settings())
win.cb_fs_layer_blend.setChecked(False)
off = not win.w_fs_layer.isEnabled()
win.cb_fs_layer_blend.setChecked(True)
check("19c Layer Blend off disables the layer row", off and win.w_fs_layer.isEnabled())
cmds.animLayer("AnimLayer3")
win.cmb_fs_layer.showPopup()
items = [win.cmb_fs_layer.itemText(i) for i in range(win.cmb_fs_layer.count())]
win.cmb_fs_layer.hidePopup()
check("19d opening the combo picks up a new layer, keeps the choice",
      "AnimLayer3" in items and win.cmb_fs_layer.currentText() == "AnimLayer2", items)

# ---------------- 17 버튼 -> 코어 인자
win.fs_tsl.set_items([foot])
APP.processEvents()
check("17a TSL holds the object", win.fs_tsl.get_all_items() == [foot], win.fs_tsl.get_all_items())
win.fs_range.set_range(1, 40)
win.sp_fs_smooth.setValue(3)
win.sp_fs_threshold.setValue(5.0)
win.sp_fs_merge_gap.setValue(2)
win.sp_fs_min_span.setValue(4)
win.cb_fs_y.setChecked(False)
win.cb_fs_r.setChecked(False)
win.cb_fs_lock.setChecked(False)
seen = {}
real_run, real_preview = MWmod.FixSlidingManager.run, MWmod.FixSlidingManager.preview


def fake_run(objs, start, end, **kw):
    seen["run"] = (list(objs), start, end, kw)
    return 0, ["fake run"]


def fake_preview(objs, start, end, **kw):
    seen["preview"] = (list(objs), start, end, kw)
    return {}, ["fake preview"]


MWmod.FixSlidingManager.run = staticmethod(fake_run)
MWmod.FixSlidingManager.preview = staticmethod(fake_preview)
win.btn_fs_run.click()
win.btn_fs_preview.click()
MWmod.FixSlidingManager.run, MWmod.FixSlidingManager.preview = staticmethod(real_run), staticmethod(real_preview)
kw = seen.get("run", (None, None, None, {}))[3]
check("17b Fix Sliding passes the options",
      seen.get("run", [None])[0] == cmds.ls(foot, long=True) and seen["run"][1:3] == (1, 40)
      and kw.get("axes") == (True, False, True) and kw.get("smooth") == 3 and kw.get("threshold_pct") == 5.0
      and kw.get("merge_gap") == 2 and kw.get("min_span") == 4 and kw.get("translate") is True
      and kw.get("rotate") is False and kw.get("layer_blend") is True and kw.get("clamp_blend") is True
      and kw.get("lock_end") is False and kw.get("debug") is True and kw.get("progress") is not None
      and kw.get("layer") == "AnimLayer2" and kw.get("offset") == 7, kw)
check("17c Preview passes the options (no key options)",
      seen.get("preview", [None])[0] == cmds.ls(foot, long=True) and seen["preview"][3].get("min_span") == 4
      and "translate" not in seen["preview"][3], seen.get("preview"))

# 실제 실행 한 번 (진행 팝업 포함) - foot 은 AnimLayer1 멤버
win.cmb_fs_layer.setCurrentIndex(win.cmb_fs_layer.findData("AnimLayer1"))
win.cb_fs_r.setChecked(True)
win.cb_fs_lock.setChecked(True)
win.btn_fs_run.click()
APP.processEvents()
base_tx = LKM.layer_curve(foot + ".translateX", LKM.root_layer())
lay_tx = LKM.layer_curve(foot + ".translateX", lay)
check("17d real run: base tx held (fewer keys) + layer keys + debug node",
      cmds.keyframe(base_tx, q=True, keyframeCount=True) < 40 and lay_tx is not None
      and cmds.objExists(FS.debug_node_name(foot)), (cmds.keyframe(base_tx, q=True, keyframeCount=True), lay_tx))

# ---------------- 20 Expand : 별도 창으로 (v02.49)
win.fs_panel.expand()
APP.processEvents()
ext = [w for w in APP.topLevelWidgets() if w.objectName() == MWmod.FIX_SLIDING_WINDOW_OBJECT_NAME]
check("20 Expand moves the Fix Sliding body into its own window",
      win.fs_panel.is_expanded() and ext and ext[0].isVisible() and ext[0].isAncestorOf(win.fs_tsl)
      and ext[0].isAncestorOf(win.btn_fs_run), [w.objectName() for w in APP.topLevelWidgets()][:8])
win.fs_panel.collapse()
APP.processEvents()
check("20b collapse puts it back in the tab", not win.fs_panel.is_expanded() and win.fs_panel.isAncestorOf(win.fs_tsl))

# ---------------- 18 optionVar 저장 -> 다시 열면 복원
win.close()
APP.processEvents()
win2 = MainWindow()
win2.show()
APP.processEvents()
check("18 reopen restores Fix Sliding settings",
      win2.sp_fs_smooth.value() == 3 and abs(win2.sp_fs_threshold.value() - 5.0) < 1e-9
      and win2.sp_fs_merge_gap.value() == 2 and win2.sp_fs_min_span.value() == 4
      and not win2.cb_fs_y.isChecked() and win2.cb_fs_r.isChecked() and win2.cb_fs_lock.isChecked()
      and win2.cmb_fs_layer.currentText() == "AnimLayer1" and win2.sp_fs_offset.value() == 7,
      (win2.cmb_fs_layer.currentText(), win2.sp_fs_offset.value()))
win2.close()

clear_optvars()
print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
