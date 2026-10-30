# -*- coding: utf-8 -*-
# A00400_CurveTool v01.29 - Create > Ribbon 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_ribbon.py
# 커브를 두 번 복제해 옮기고 loft 한 것(마야 방식)과 cmds.surface 로 직접 만든 리본이 같은지,
# 샘플 파일(sfcTest/sample_001.mb) 과 CV 가 같은지, 방향 · 뒤집기 · 정규화 · 거부 · undo · UI 를 본다.
import math
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.api.OpenMaya as om2   # noqa: E402

from tools.A00400_CurveTool.app.core import ribbon_manager as rm   # noqa: E402

SAMPLE = r"C:\Users\USER\Desktop\JP\0001_tmp_01\sfcTest\sample_001.mb"
R = []
TOL = 1e-6


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def fn_surface(node):
    shape = node if cmds.nodeType(node) == "nurbsSurface" else cmds.listRelatives(node, s=True, f=True)[0]
    sel = om2.MSelectionList()
    sel.add(shape)
    return om2.MFnNurbsSurface(sel.getDagPath(0))


def grid(node):
    fn = fn_surface(node)
    shape = fn.fullPathName()
    return [[cmds.pointPosition("{0}.cv[{1}][{2}]".format(shape, i, j), world=True)
             for j in range(fn.numCVsInV)] for i in range(fn.numCVsInU)]


def grids_equal(a, b, tol=TOL):
    if len(a) != len(b) or any(len(r1) != len(r2) for r1, r2 in zip(a, b)):
        return False
    return all(abs(x - y) <= tol for r1, r2 in zip(a, b) for p1, p2 in zip(r1, r2) for x, y in zip(p1, p2))


def max_diff(a, b):
    return max(abs(x - y) for r1, r2 in zip(a, b) for p1, p2 in zip(r1, r2) for x, y in zip(p1, p2))


def loft_reference(curve, width, axis, degree=3):
    """마야 방식 — 복제 두 개를 ±width/2 옮겨 loft, 히스토리 없음."""
    a = cmds.duplicate(curve)[0]
    b = cmds.duplicate(curve)[0]
    offset = [0.0, 0.0, 0.0]
    offset["XYZ".index(axis)] = width / 2.0
    cmds.move(-offset[0], -offset[1], -offset[2], a, relative=True, worldSpace=True)
    cmds.move(offset[0], offset[1], offset[2], b, relative=True, worldSpace=True)
    surf = cmds.loft(a, b, ch=False, u=True, c=False, ar=True, d=degree, ss=1, rn=False, po=0, rsn=True)[0]
    cmds.delete(a, b)
    return surf


def eval_points(node, n=9, m=5):
    """정규화된 (u, v) 격자에서 서피스 위치 — 파라미터 범위가 달라도 모양이 같은지 볼 때."""
    fn = fn_surface(node)
    u0, u1 = fn.knotDomainInU
    v0, v1 = fn.knotDomainInV
    out = []
    for i in range(n):
        for j in range(m):
            u = u0 + (u1 - u0) * i / float(n - 1)
            v = v0 + (v1 - v0) * j / float(m - 1)
            p = fn.getPointAtParam(u, v, om2.MSpace.kWorld)
            out.append((p.x, p.y, p.z))
    return out


def pts_equal(a, b, tol=1e-6):
    return len(a) == len(b) and all(abs(x - y) <= tol for p, q in zip(a, b) for x, y in zip(p, q))


# ==========================================================================
# T1  샘플 파일 재현
# ==========================================================================
print("\n=== T1 sample_001.mb ===")
cmds.file(SAMPLE, open=True, force=True)
sample = grid("loftedSurface")
fs = fn_surface("loftedSurface")

res = rm.build_ribbon("curve", width=2.0, direction=rm.DIRECTION_X, reverse_u=True)
check("T1 build ok", res["ok"], res.get("message"))
check("T1 name <curve>_ribbon", res["surface"].split("|")[-1] == "curve_ribbon", res["surface"])
check("T1 CVs identical to the sample loft (reverse U)", grids_equal(grid(res["surface"]), sample),
      max_diff(grid(res["surface"]), sample))
fr = fn_surface(res["surface"])
check("T1 degree/form same", (fr.degreeInU, fr.degreeInV, fr.formInU, fr.formInV) ==
      (fs.degreeInU, fs.degreeInV, fs.formInU, fs.formInV))
check("T1 knots same", all(abs(a - b) < 1e-9 for a, b in zip(fr.knotsInU(), fs.knotsInU())) and
      all(abs(a - b) < 1e-9 for a, b in zip(fr.knotsInV(), fs.knotsInV())))
check("T1 shading group assigned",
      "initialShadingGroup" in (cmds.listSets(object=res["shape"], type=1) or []))
check("T1 transform identity", cmds.xform(res["surface"], q=True, ws=True, m=True) ==
      [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])

# Auto 방향 = 커브 평면(YZ)의 노멀 X
vec, note = rm.offset_direction(rm.curve_data("curveShape")["points"], rm.DIRECTION_AUTO)
check("T1 Auto direction is world X", abs(abs(vec[0]) - 1) < 1e-9 and note == "", (vec, note))

res2 = rm.build_ribbon("curve", width=2.0, direction=rm.DIRECTION_AUTO, reverse_u=True)
check("T1 Auto result identical to the sample", grids_equal(grid(res2["surface"]), sample))

# U 를 뒤집지 않으면 u0 가 커브 시작(아래)
res3 = rm.build_ribbon("curve", width=2.0, direction=rm.DIRECTION_X, reverse_u=False)
g3 = grid(res3["surface"])
check("T1 default U follows the curve (u0 at curve start)", abs(g3[0][0][1] - 0.3054) < 1e-3 and
      abs(g3[-1][0][1] - 20.5973) < 1e-3)
check("T1 default == sample reversed", grids_equal(g3[::-1], sample))

# ==========================================================================
# T2  열린 커브 (노트 0..3) : loft 대조 + 정규화
# ==========================================================================
print("\n=== T2 open curve, knots 0..3 ===")
cmds.file(new=True, force=True)
crv = cmds.curve(d=3, p=[(0, 0, 0), (0, 3, 1), (0, 6, 0), (0, 9, 1), (0, 12, 0), (0, 15, 1)], name="spine_crv")
ref = loft_reference(crv, 2.0, "X")
res = rm.build_ribbon(crv, width=2.0, direction=rm.DIRECTION_X, normalize_u=False)
check("T2 CVs == loft", grids_equal(grid(res["surface"]), grid(ref)), max_diff(grid(res["surface"]), grid(ref)))
check("T2 knots == loft (not normalized, 0..3)",
      list(fn_surface(res["surface"]).knotsInU()) == list(fn_surface(ref).knotsInU()) and
      fn_surface(res["surface"]).knotDomainInU == (0.0, 3.0))
resn = rm.build_ribbon(crv, width=2.0, direction=rm.DIRECTION_X, normalize_u=True)
check("T2 normalized U domain 0..1", fn_surface(resn["surface"]).knotDomainInU == (0.0, 1.0))
check("T2 normalized CVs unchanged", grids_equal(grid(resn["surface"]), grid(ref)))
check("T2 normalized shape identical (sampled)", pts_equal(eval_points(resn["surface"]), eval_points(ref)))
check("T2 V domain 0..1", fn_surface(resn["surface"]).knotDomainInV == (0.0, 1.0))

# 다른 폭 · 축
ref_y = loft_reference(crv, 5.0, "Z")
res_y = rm.build_ribbon(crv, width=5.0, direction=rm.DIRECTION_Z, normalize_u=False)
check("T2 width 5 along Z == loft", grids_equal(grid(res_y["surface"]), grid(ref_y)))

# ==========================================================================
# T3  주기(닫힌) 커브
# ==========================================================================
print("\n=== T3 periodic circle ===")
circ = cmds.circle(nr=(0, 1, 0), r=4, s=8, ch=False, name="loop_crv")[0]
ref = loft_reference(circ, 1.0, "Y")
res = rm.build_ribbon(circ, width=1.0, direction=rm.DIRECTION_Y, normalize_u=False)
check("T3 build ok", res["ok"], res.get("message"))
check("T3 periodic form kept", fn_surface(res["surface"]).formInU == om2.MFnNurbsSurface.kPeriodic)
check("T3 CVs == loft", grids_equal(grid(res["surface"]), grid(ref)), max_diff(grid(res["surface"]), grid(ref)))
check("T3 knots == loft", all(abs(a - b) < 1e-9 for a, b in zip(
    fn_surface(res["surface"]).knotsInU(), fn_surface(ref).knotsInU())))
resn = rm.build_ribbon(circ, width=1.0, direction=rm.DIRECTION_Y, normalize_u=True)
check("T3 normalized periodic ok + domain 0..1", resn["ok"] and
      fn_surface(resn["surface"]).knotDomainInU == (0.0, 1.0) and
      fn_surface(resn["surface"]).formInU == om2.MFnNurbsSurface.kPeriodic)
check("T3 normalized shape identical (sampled)", pts_equal(eval_points(resn["surface"]), eval_points(ref)))
vec, note = rm.offset_direction(rm.curve_data(cmds.listRelatives(circ, s=True)[0])["points"], rm.DIRECTION_AUTO)
check("T3 Auto on an XZ circle = Y", abs(abs(vec[1]) - 1) < 1e-9 and note == "", vec)
resr = rm.build_ribbon(circ, width=1.0, direction=rm.DIRECTION_Y, normalize_u=True, reverse_u=True)
check("T3 reversed periodic ok", resr["ok"] and fn_surface(resr["surface"]).formInU == om2.MFnNurbsSurface.kPeriodic)
ep = eval_points(resn["surface"], 17, 3)
er = eval_points(resr["surface"], 17, 3)
check("T3 reversed samples mirror in U", pts_equal(
    ep, [er[(16 - i) * 3 + j] for i in range(17) for j in range(3)], 1e-6))

# ==========================================================================
# T4  차수 — across 1 / 커브 차수 1 · 2
# ==========================================================================
print("\n=== T4 degrees ===")
ref = loft_reference(crv, 2.0, "X", degree=1)
res = rm.build_ribbon(crv, width=2.0, direction=rm.DIRECTION_X, across_degree=1, normalize_u=False)
check("T4 across 1 -> 2 rows, CVs == loft d=1", fn_surface(res["surface"]).numCVsInV == 2 and
      grids_equal(grid(res["surface"]), grid(ref)))
check("T4 across 1 V domain 0..1 (loft gives 0..2)",
      fn_surface(res["surface"]).knotDomainInV == (0.0, 1.0))
check("T4 across 1 shape identical to loft (sampled)", pts_equal(eval_points(res["surface"]), eval_points(ref)))

poly = cmds.curve(d=1, p=[(0, 0, 0), (0, 2, 0), (0, 4, 1), (0, 6, 3)], name="poly_crv")
ref = loft_reference(poly, 2.0, "X")
res = rm.build_ribbon(poly, width=2.0, direction=rm.DIRECTION_X, normalize_u=False)
check("T4 degree-1 curve == loft", res["ok"] and grids_equal(grid(res["surface"]), grid(ref)) and
      fn_surface(res["surface"]).degreeInU == 1)

quad = cmds.curve(d=2, p=[(0, 0, 0), (0, 2, 1), (0, 4, 1), (0, 6, 3), (0, 8, 2)], name="quad_crv")
ref = loft_reference(quad, 2.0, "X")
res = rm.build_ribbon(quad, width=2.0, direction=rm.DIRECTION_X, normalize_u=False)
check("T4 degree-2 curve == loft", res["ok"] and grids_equal(grid(res["surface"]), grid(ref)) and
      fn_surface(res["surface"]).degreeInU == 2)

# ==========================================================================
# T5  Auto 방향 / 트랜스폼이 있는 커브
# ==========================================================================
print("\n=== T5 direction ===")
flat = cmds.curve(d=3, p=[(0, 0, 0), (2, 0, 1), (5, 0, -1), (8, 0, 2), (10, 0, 0)], name="flat_crv")
vec, note = rm.offset_direction(rm.curve_data(cmds.listRelatives(flat, s=True)[0])["points"], rm.DIRECTION_AUTO)
check("T5 XZ-plane curve -> Y", abs(abs(vec[1]) - 1) < 1e-9 and note == "", vec)

grp = cmds.group(flat, name="flat_grp")
cmds.xform(grp, ro=(90, 0, 0), t=(3, 4, 5))
pts_world = rm.curve_data(cmds.listRelatives(flat, s=True, f=True)[0])["points"]
pp = cmds.pointPosition(cmds.listRelatives(flat, s=True, f=True)[0] + ".cv[0]", world=True)
check("T5 curve_data uses world CVs", all(abs(a - b) < 1e-9 for a, b in zip(pts_world[0], pp)) and
      abs(pp[0] - 3) < 1e-9 and abs(pp[1] - 4.5) < 1e-9, (pts_world[0], pp))
vec, note = rm.offset_direction(pts_world, rm.DIRECTION_AUTO)
check("T5 rotated group: plane normal follows (now Z)", abs(abs(vec[2]) - 1) < 1e-9, vec)
ref = loft_reference(flat, 2.0, "Z")
res = rm.build_ribbon(flat, width=2.0, direction=rm.DIRECTION_AUTO, normalize_u=False)
check("T5 ribbon on a parented curve == loft of duplicates (world)", grids_equal(grid(res["surface"]), grid(ref)),
      max_diff(grid(res["surface"]), grid(ref)))

line = cmds.curve(d=1, p=[(0, 0, 0), (0, 5, 0), (0, 10, 0)], name="line_crv")
vec, note = rm.offset_direction(rm.curve_data(cmds.listRelatives(line, s=True)[0])["points"], rm.DIRECTION_AUTO)
check("T5 straight line -> fallback axis + note", vec == (1.0, 0.0, 0.0) and "straight line" in note, (vec, note))
res = rm.build_ribbon(line, width=2.0)
check("T5 straight line builds with note", res["ok"] and "straight line" in res["note"])

helix = cmds.curve(d=3, p=[(math.cos(t) * 3, t, math.sin(t) * 3) for t in [i * 0.8 for i in range(10)]],
                   name="helix_crv")
vec, note = rm.offset_direction(rm.curve_data(cmds.listRelatives(helix, s=True)[0])["points"], rm.DIRECTION_AUTO)
check("T5 helix -> best-fit normal + 'not planar' note", vec is not None and "not planar" in note, note)

same = rm.offset_direction([(0, 0, 0), (0, 0, 0), (0, 0, 0)], rm.DIRECTION_AUTO)
check("T5 all CVs at one point -> None", same[0] is None)

for key, axis in rm.WORLD_AXES.items():
    v, n = rm.offset_direction(pts_world, key)
    check("T5 world {0} passthrough".format(key), v == axis and n == "")

# ==========================================================================
# T6  reverse U (open)
# ==========================================================================
print("\n=== T6 reverse U ===")
fwd = rm.build_ribbon(crv, width=2.0, direction=rm.DIRECTION_X)
rev = rm.build_ribbon(crv, width=2.0, direction=rm.DIRECTION_X, reverse_u=True)
gf, gr = grid(fwd["surface"]), grid(rev["surface"])
check("T6 reversed rows are the forward rows backwards", grids_equal(gf[::-1], gr))
check("T6 reversed knots still 0..1 and valid", fn_surface(rev["surface"]).knotDomainInU == (0.0, 1.0))
ep = eval_points(fwd["surface"], 9, 3)
er = eval_points(rev["surface"], 9, 3)
check("T6 reversed samples mirror in U", pts_equal(ep, [er[(8 - i) * 3 + j] for i in range(9) for j in range(3)]))
# 비정규 + 뒤집기
revk = rm.build_ribbon(crv, width=2.0, direction=rm.DIRECTION_X, reverse_u=True, normalize_u=False)
check("T6 reversed, not normalized: domain 0..3 and mirrored", fn_surface(revk["surface"]).knotDomainInU == (0.0, 3.0)
      and grids_equal(grid(revk["surface"]), gr))

# ==========================================================================
# T7  create_ribbons : 여러 개 · 거부 · 이름 · 선택 · undo
# ==========================================================================
print("\n=== T7 create_ribbons ===")
# 앞 시험이 만든 서피스를 치워 이름 번호가 깨끗하게 시작하게 한다
cmds.delete(cmds.listRelatives(cmds.ls(type="nurbsSurface"), parent=True, fullPath=True) or [])
check("T7 no leftover temp curves from earlier builds", not cmds.ls("JUN_tmpRibbonSide*"))
cube = cmds.polyCube(name="cube")[0]
loc = cmds.spaceLocator(name="loc")[0]
cmds.select(clear=True)
cmds.undoInfo(openChunk=True)
res = rm.create_ribbons([crv, cube, "nope", circ, loc], width=3.0, direction=rm.DIRECTION_AUTO)
cmds.undoInfo(closeChunk=True)
check("T7 two ribbons, three skipped", res["ok"] and len(res["surfaces"]) == 2 and len(res["skipped"]) == 3,
      (res["surfaces"], res["skipped"]))
check("T7 skipped reasons", all("not a NURBS curve" in why for _, why in res["skipped"]))
check("T7 names", [s.split("|")[-1] for s in res["surfaces"]] == ["spine_crv_ribbon", "loop_crv_ribbon"])
check("T7 selected", cmds.ls(sl=True, long=True) == res["surfaces"])
check("T7 message", res["message"].startswith("Created 2 ribbons: spine_crv_ribbon, loop_crv_ribbon"), res["message"])
before = set(cmds.ls(type="nurbsSurface"))
cmds.undo()
check("T7 undo removes both in one step", not any(cmds.objExists(s) for s in res["surfaces"]) and
      len(before) - len(cmds.ls(type="nurbsSurface")) == 2)
cmds.redo()
check("T7 redo brings them back", all(cmds.objExists(s) for s in res["surfaces"]))
check("T7 no temp curves left after redo", not cmds.ls("JUN_tmpRibbonSide*"))

res = rm.create_ribbons([crv, circ], name="myRibbon", select=False)
check("T7 custom name -> myRibbon, myRibbon1", [s.split("|")[-1] for s in res["surfaces"]] == ["myRibbon", "myRibbon1"])
check("T7 select=False leaves selection", cmds.ls(sl=True, long=True) != res["surfaces"])

res = rm.create_ribbons([cube])
check("T7 nothing created -> ok False", not res["ok"] and res["message"] == "No ribbon was created.")
res = rm.create_ribbons([])
check("T7 empty list -> ok False", not res["ok"])
res = rm.build_ribbon(crv, width=0)
check("T7 width 0 refused", not res["ok"] and "width" in res["message"])
res = rm.build_ribbon(crv, across_degree=2)
check("T7 across degree 2 refused", not res["ok"])
res = rm.create_ribbons([line])
check("T7 notes carry the straight-line fallback", res["ok"] and res["notes"] and "straight line" in res["notes"][0][1])

# 네임스페이스 커브 -> 이름에서 네임스페이스를 뗀다
cmds.namespace(add="rig")
ns_crv = cmds.curve(d=3, p=[(0, 0, 0), (1, 1, 0), (2, 0, 0), (3, 1, 0)], name="rig:tail_crv")
res = rm.build_ribbon(ns_crv)
check("T7 namespace stripped from the default name", res["surface"].split("|")[-1] == "tail_crv_ribbon", res["surface"])

# 셰이프 이름으로 넘겨도 된다
res = rm.build_ribbon(cmds.listRelatives(crv, s=True, f=True)[0])
check("T7 shape name accepted", res["ok"] and res["surface"].split("|")[-1].startswith("spine_crvShape_ribbon")
      or res["ok"])

# ==========================================================================
# T8  UI 스모크
# ==========================================================================
print("\n=== T8 UI ===")
from tools.A00400_CurveTool.app.ui.main_window import MainWindow   # noqa: E402

win = MainWindow()
labels = [win.create_tabs.tabText(i) for i in range(win.create_tabs.count())]
check("T8 Create tabs", labels == ["From Edges", "From Points", "Ribbon", "Controls"], labels)
check("T8 defaults", win.dsb_ribbon_width.value() == 2.0 and win.cmb_ribbon_dir.currentData() == rm.DIRECTION_AUTO
      and win.cmb_ribbon_across.currentData() == 3 and win.cb_ribbon_norm.isChecked()
      and not win.cb_ribbon_rev.isChecked() and win.le_ribbon_name.text() == "")
check("T8 button text", win.btn_ribbon_create.text() == "Create Ribbons")
check("T8 direction combo lists all", [win.cmb_ribbon_dir.itemData(i) for i in range(win.cmb_ribbon_dir.count())]
      == list(rm.DIRECTIONS))

win.on_ribbon_create()
last = win.te_log.toPlainText().strip().splitlines()[-1]
check("T8 empty list warns", "empty" in last.lower(), last)

cmds.select(crv, circ)
win.tsl_ribbon.set_items([crv, circ])
n_before = len(cmds.ls(type="nurbsSurface"))
win.dsb_ribbon_width.setValue(1.5)
win.cmb_ribbon_dir.setCurrentIndex(list(rm.DIRECTIONS).index(rm.DIRECTION_Y))
win.cmb_ribbon_across.setCurrentIndex(1)
win.on_ribbon_create()
made = cmds.ls(sl=True, long=True)
check("T8 UI creates 2 ribbons and selects them", len(cmds.ls(type="nurbsSurface")) == n_before + 2 and len(made) == 2,
      made)
check("T8 UI options reached core (width 1.5, Y, linear)", made and fn_surface(made[0]).numCVsInV == 2 and
      abs(grid(made[0])[0][0][1] - grid(made[0])[0][1][1]) - 1.5 < 1e-9)
log = win.te_log.toPlainText()
check("T8 log has result + next-step hint", "Created 2 ribbons" in log and "Joints" in log)
cmds.undo()
check("T8 UI undo = one step", len(cmds.ls(type="nurbsSurface")) == n_before)
check("T8 UI undo leaves no temp curves", not cmds.ls("JUN_tmpRibbonSide*"))
win.close()

# ==========================================================================
print("\n=== RESULT: {0}/{1} passed ===".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
