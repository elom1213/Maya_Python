# -*- coding: utf-8 -*-
# A00470_MaterialTool v01.13 - Copy Material 탭 왼쪽 · 오른쪽 리스트 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_copy_material_pairs.py
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication, QPlainTextEdit   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00470_MaterialTool.app.core import material_copy as MC   # noqa: E402
from tools.A00470_MaterialTool.app.ui import copy_material_tab as CT   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def engine(name):
    mat = cmds.shadingNode("lambert", asShader=True, name=name)
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "SG")
    cmds.connectAttr(mat + ".outColor", sg + ".surfaceShader")
    return sg


def cube(name):
    return cmds.polyCube(name=name, constructionHistory=False)[0]


def faces_of(node):
    return MC.per_face_engines(MC.mesh_shapes(node)[0])


def build():
    cmds.file(new=True, force=True)
    sgs = {n: engine(n) for n in ("red", "green", "blue")}
    # 소스 3 개 - 서로 다른 면별 배정
    s1, s2, s3 = cube("srcA"), cube("srcB"), cube("srcC")
    cmds.sets(s1, edit=True, forceElement=sgs["red"])
    cmds.sets(s1 + ".f[0:1]", edit=True, forceElement=sgs["blue"])
    cmds.sets(s2, edit=True, forceElement=sgs["green"])
    cmds.sets(s2 + ".f[5]", edit=True, forceElement=sgs["red"])
    cmds.sets(s3, edit=True, forceElement=sgs["blue"])
    targets = [cube(n) for n in ("tgtA", "tgtB", "tgtC")]
    for t in targets:
        cmds.sets(t, edit=True, forceElement="initialShadingGroup")
    return [s1, s2, s3], targets


def make_tab():
    log = QPlainTextEdit()
    tab = CT.CopyMaterialTab(log_view=log)
    return tab, log


# ---------------------------------------------------------------- 1) 1 -> n (예전 동작)
srcs, tgts = build()
tab, log = make_tab()
check("empty lists : mode none, button off", tab.mode()[0] == CT.MODE_NONE and not tab.btn_copy.isEnabled())
tab.tsl_source.append_unique([srcs[0]])
tab.tsl_target.append_unique(tgts)
app.processEvents()
check("1 -> n : mode label", tab.mode()[0] == CT.MODE_ONE_TO_N and "1 -> 3" in tab.lbl_mode.text()
      and tab.btn_copy.isEnabled(), tab.lbl_mode.text())
tab.on_copy_material()
want = faces_of(srcs[0])
check("1 -> n : every target matches the source", all(faces_of(t) == want for t in tgts),
      [faces_of(t) for t in tgts])
check("1 -> n : log message", "srcA -> 3 mesh(es)" in log.toPlainText(), log.toPlainText()[-200:])
cmds.undo()
check("1 -> n : one undo step reverts all", all(set(faces_of(t)) == {"initialShadingGroup"} for t in tgts))

# ---------------------------------------------------------------- 2) n 쌍
srcs, tgts = build()
tab, log = make_tab()
tab.tsl_source.append_unique(srcs)
tab.tsl_target.append_unique(tgts)
app.processEvents()
check("pairs : mode label", tab.mode()[0] == CT.MODE_PAIRS and "3 pairs" in tab.lbl_mode.text(), tab.lbl_mode.text())
tab.on_copy_material()
check("pairs : row i -> row i", all(faces_of(t) == faces_of(s) for s, t in zip(srcs, tgts)),
      [faces_of(t) for t in tgts])
check("pairs : the three results differ (really pairwise)", len({tuple(faces_of(t)) for t in tgts}) == 3)
check("pairs : log", "3 pair(s) copied, 3 material(s)" in log.toPlainText() and "srcB -> tgtB" in log.toPlainText(),
      log.toPlainText()[-300:])
cmds.undo()
check("pairs : one undo step reverts all", all(set(faces_of(t)) == {"initialShadingGroup"} for t in tgts))

# ---------------------------------------------------------------- 3) 개수 다름 -> 거절
srcs, tgts = build()
tab, log = make_tab()
tab.tsl_source.append_unique(srcs[:2])
tab.tsl_target.append_unique(tgts)
app.processEvents()
check("mismatch : mode, button off, red label", tab.mode()[0] == CT.MODE_MISMATCH and not tab.btn_copy.isEnabled()
      and "ff6b6b" in tab.lbl_mode.styleSheet(), tab.lbl_mode.text())
tab.on_copy_material()
check("mismatch : nothing changed + warning", all(set(faces_of(t)) == {"initialShadingGroup"} for t in tgts)
      and "[warning] 2 sources and 3 targets" in log.toPlainText())
tab.tsl_target.clear()
app.processEvents()
check("clear updates the mode", tab.mode()[0] == CT.MODE_NONE)

# ---------------------------------------------------------------- 4) 사라진 행은 그 쌍만 + 이름 바꿔도 UUID
srcs, tgts = build()
tab, log = make_tab()
tab.tsl_source.append_unique(srcs)
tab.tsl_target.append_unique(tgts)
cmds.delete(srcs[1])                                    # 가운데 소스 삭제
renamed = cmds.rename(tgts[2], "tgtC_renamed")          # 마지막 대상 이름 바꾸기
grp = cmds.group(empty=True, name="grp")
cmds.parent(renamed, grp)                               # 부모도 옮기기
tab.on_copy_material()
check("missing row : only its pair skipped, no shift",
      faces_of(tgts[0]) == faces_of(srcs[0]) and set(faces_of(tgts[1])) == {"initialShadingGroup"}
      and faces_of("grp|tgtC_renamed") == faces_of(srcs[2]))
check("missing row : logged with the list name", "[skipped] srcB -> tgtB : not in the scene anymore" in log.toPlainText(),
      log.toPlainText())

# ---------------------------------------------------------------- 5) 면 개수 다름 -> 그 쌍만 건너뜀
srcs, tgts = build()
odd = cmds.polySphere(name="odd", constructionHistory=False)[0]
tab, log = make_tab()
tab.tsl_source.append_unique(srcs[:2])
tab.tsl_target.append_unique([odd, tgts[1]])
tab.on_copy_material()
check("face count mismatch : skipped, other pair copied",
      faces_of(tgts[1]) == faces_of(srcs[1]) and "[skipped] srcA -> odd" in log.toPlainText()
      and "1 pair(s) copied, 2 material(s)" in log.toPlainText(), log.toPlainText())

# ---------------------------------------------------------------- 6) 1 -> n 에서 소스 삭제
srcs, tgts = build()
tab, log = make_tab()
tab.tsl_source.append_unique([srcs[0]])
tab.tsl_target.append_unique(tgts)
cmds.delete(srcs[0])
tab.on_copy_material()
check("1 -> n : deleted source warns", "is not in the scene anymore" in log.toPlainText())

# ---------------------------------------------------------------- 7) core 직접 - copy_material(uuid) 회귀
srcs, tgts = build()
res = MC.copy_material(MC.uuid_of(srcs[0]), tgts[:1])
check("core : copy_material(uuid) still works", res["ok"] and faces_of(tgts[0]) == faces_of(srcs[0]))
res = MC.copy_material_pairs([(None, tgts[1]), (srcs[2], tgts[2])])
check("core : pairs with None skip that row", res["ok"] and len(res["copied"]) == 1 and len(res["skipped"]) == 1)

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
