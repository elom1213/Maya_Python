# -*- coding: utf-8 -*-
# A00600_SceneCleanup v01.00 - 정리 항목 · runner · UI 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_scene_cleanup.py
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.mel as mel   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import maya_cleanup as MC   # noqa: E402
from Framework.qt.qt import Qt   # noqa: E402
from tools.A00600_SceneCleanup.app.core import cleanup_items as CI   # noqa: E402
from tools.A00600_SceneCleanup.app.core import cleanup_runner as CR   # noqa: E402
from tools.A00600_SceneCleanup.app.ui import main_window as MW   # noqa: E402

R = []
TMP = tempfile.mkdtemp(prefix="a00600_")


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build():
    """레이어 2 · 애니메이션 레이어(Base + AL1) · 쓰는/안 쓰는 셰이딩 네트워크."""
    cmds.file(new=True, force=True)
    cube = cmds.polyCube(name="box")[0]
    sph = cmds.polySphere(name="ball")[0]
    cmds.setKeyframe(cube, attribute="tx", time=1, value=0)
    cmds.setKeyframe(cube, attribute="tx", time=10, value=5)
    cmds.select(cube)
    cmds.createDisplayLayer(name="L_geo", noRecurse=True)
    cmds.select(sph)
    cmds.createDisplayLayer(name="L_ball", noRecurse=True)
    cmds.select(cube)
    cmds.animLayer("AL1", addSelectedObjects=True)
    cmds.setKeyframe(cube, attribute="tx", time=5, value=3, animLayer="AL1")
    used = cmds.shadingNode("lambert", asShader=True, name="usedM")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="usedSG")
    cmds.connectAttr(used + ".outColor", sg + ".surfaceShader")
    cmds.sets(cube, edit=True, forceElement=sg)
    unused = cmds.shadingNode("blinn", asShader=True, name="unusedM")
    tex = cmds.shadingNode("file", asTexture=True, name="unusedFile")
    cmds.connectAttr(tex + ".outColor", unused + ".color")
    usg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="emptySG")
    cmds.shadingNode("multiplyDivide", asUtility=True, name="loneMD")
    cmds.select(clear=True)
    return cube, usg


def layers():
    return sorted(cmds.ls(type="displayLayer") or []), sorted(cmds.ls(type="animLayer") or [])


# ---------------------------------------------------------------- 1. 레지스트리
check("1 registry order", [i.key for i in CI.ITEMS] == ["display_layers", "anim_layers", "unused_nodes"])
check("1 every item default checked", all(i.default for i in CI.ITEMS))
check("1 labels are English ascii", all(i.label.isascii() and i.tooltip.isascii() for i in CI.ITEMS))

# ---------------------------------------------------------------- 2. 전부 실행
cube, _ = build()
before_nodes = set(cmds.ls())
logs = []
out = CR.run_items(list(CI.ITEMS), log=logs.append)
disp, anim = layers()
check("2 display layers -> defaultLayer only", disp == ["defaultLayer"], disp)
check("2 animation layers all gone (BaseAnimation too)", anim == [], anim)
check("2 unused nodes removed", not any(cmds.objExists(n) for n in ("unusedM", "unusedFile", "loneMD", "emptySG")))
check("2 used material + SG kept", cmds.objExists("usedM") and cmds.objExists("usedSG"))
check("2 default material kept", cmds.objExists("lambert1"))
check("2 objects kept", cmds.objExists("box") and cmds.objExists("ball"))
tx = cmds.getAttr("box.tx", time=10)
check("2 Base keys kept on tx (AL1 key gone)", abs(tx - 5.0) < 1e-6 and cmds.keyframe("box.tx", q=True, keyframeCount=True) == 2,
      (tx, cmds.keyframe("box.tx", q=True, timeChange=True)))
check("2 three outcomes, no error", len(out) == 3 and all(e is None for _, _, e in out))
check("2 log has Done line", any(l.startswith("Done : ") for l in logs), logs[-1:])
cmds.undo()
check("2 one undo restores every node", set(cmds.ls()) == before_nodes, sorted(before_nodes ^ set(cmds.ls()))[:8])
disp, anim = layers()
check("2 undo restores layers", disp == ["L_ball", "L_geo", "defaultLayer"] and anim == ["AL1", "BaseAnimation"], (disp, anim))

# ---------------------------------------------------------------- 3. 체크 안 한 항목은 안 돈다
build()
CR.run_items([CI.item_by_key("unused_nodes")], log=None)
disp, anim = layers()
check("3 only unused nodes ran", len(disp) == 3 and len(anim) == 2 and not cmds.objExists("unusedM"), (disp, anim))
logs = []
check("3 nothing checked -> no-op", CR.run_items([], log=logs.append) == [] and "Nothing checked" in logs[0])

# ---------------------------------------------------------------- 4. BaseAnimation 만 남은 씬
build()
cmds.delete("AL1")
check("4 setup: BaseAnimation alone", layers()[1] == ["BaseAnimation"])
res = MC.delete_animation_layers()
check("4 BaseAnimation alone is deleted", layers()[1] == [] and res.removed == ["BaseAnimation"], res)

# ---------------------------------------------------------------- 5. 중첩 · 잠긴 레이어
build()
cmds.select("box")
cmds.animLayer("AL2", addSelectedObjects=True, parent="AL1")
cmds.animLayer("AL1", edit=True, lock=True)
cmds.lockNode("AL2", lock=True)
res = MC.delete_animation_layers()
check("5 nested + locked layers gone", layers()[1] == [] and len(res.removed) == 3, res)

# ---------------------------------------------------------------- 6. Hypershade Delete Unused Nodes 와 같은 결과
build()
path = os.path.join(TMP, "hs_compare.ma")
cmds.file(rename=path)
cmds.file(save=True, type="mayaAscii", force=True)
tool_removed = sorted(MC.delete_unused_nodes().removed)
cmds.file(path, open=True, force=True)
b = set(cmds.ls())
mel.eval("MLdeleteUnused")
maya_removed = sorted(b - set(cmds.ls()))
check("6 same nodes as MLdeleteUnused", tool_removed == maya_removed and tool_removed, (tool_removed, maya_removed))

# ---------------------------------------------------------------- 7. 레퍼런스 레이어
build()
ref_path = os.path.join(TMP, "ref_layers.ma")
cmds.file(rename=ref_path)
cmds.file(save=True, type="mayaAscii", force=True)
cmds.file(new=True, force=True)
cmds.file(ref_path, reference=True, namespace="REF")
local = cmds.polyCube(name="localBox")[0]
cmds.select(local)
cmds.createDisplayLayer(name="L_local", noRecurse=True)
ref_anim_before = [l for l in cmds.ls(type="animLayer") if cmds.referenceQuery(l, isNodeReferenced=True)]
cmds.select(local)
local_layer = cmds.animLayer("ALlocal", addSelectedObjects=True)
res_a = MC.delete_animation_layers()
res_d = MC.delete_display_layers()
check("7 local anim layer removed", not cmds.objExists(local_layer), res_a)
check("7 referenced anim layers kept + warning", ref_anim_before and all(cmds.objExists(l) for l in ref_anim_before)
      and any("stays visible" in w for w in res_a.warnings), res_a.warnings)
check("7 local display layer removed, referenced kept + warning",
      not cmds.objExists("L_local") and cmds.objExists("REF:L_geo") and any("referenced display" in w for w in res_d.warnings),
      res_d)

# ---------------------------------------------------------------- 8. 한 항목 예외 -> 나머지는 돈다
class _Boom(CI.CleanupItem):
    key = "boom"
    label = "Boom"

    def run(self):
        raise RuntimeError("boom")


build()
logs = []
out = CR.run_items([_Boom(), CI.item_by_key("display_layers")], log=logs.append)
check("8 error logged, next item still ran", out[0][2] == "boom" and layers()[0] == ["defaultLayer"]
      and any(l.startswith("[ERROR] Boom") for l in logs), logs)

# ---------------------------------------------------------------- 9. UI
build()
w = MW.MainWindow()
w.confirm_before_run = False
lw = w.lw_items
check("9 rows = ITEMS order", [lw.item(i).text() for i in range(lw.count())] == [i.label for i in CI.ITEMS])
check("9 all checked on open", all(lw.item(i).checkState() == Qt.Checked for i in range(lw.count())))
w.set_all_checked(False)
check("9 Uncheck All", w.checked_items() == [])
w.run_cleanup()
check("9 run with nothing checked does nothing", layers()[1] == ["AL1", "BaseAnimation"])
w.set_all_checked(True)
check("9 Check All", [i.key for i in w.checked_items()] == [i.key for i in CI.ITEMS])
lw.item(1).setCheckState(Qt.Unchecked)
check("9 checked_items skips unchecked", [i.key for i in w.checked_items()] == ["display_layers", "unused_nodes"])
w.run_cleanup()
disp, anim = layers()
check("9 run: anim layers untouched, others cleaned", disp == ["defaultLayer"] and anim == ["AL1", "BaseAnimation"]
      and not cmds.objExists("unusedM"), (disp, anim))
check("9 log shows Done", "Done : " in w.log_view.toPlainText())
w2 = MW.MainWindow()
check("9 reopened window is all checked again", all(w2.lw_items.item(i).checkState() == Qt.Checked
                                                     for i in range(w2.lw_items.count())))

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
