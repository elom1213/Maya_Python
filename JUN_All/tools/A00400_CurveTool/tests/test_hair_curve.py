# -*- coding: utf-8 -*-
# A00400_CurveTool v01.32 - Create > From Hair 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_hair_curve.py
#
# 합성 튜브 메시(한쪽 열림 + 끝 극점 - 실제 헤어 가닥과 같은 위상)로 엔진 · 필터 · 출력 · undo · UI 를 보고,
# 실데이터(LUN hair_01.fbx + Houdini 결과 hair_02.abc)가 있으면 골든 대조를 한다(없으면 SKIP).
# 계획서: docs/plans/A00400_CurveTool_hair_centerline_plan.md §8
import math
import os
import sys
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import maya.api.OpenMaya as om   # noqa: E402

from tools.A00400_CurveTool.app.core import hair_curve_manager as hm   # noqa: E402
from tools.A00400_CurveTool.app.core import joint_curve_manager as jm   # noqa: E402

DATA = (r"C:\Users\USER\Desktop\JP\0001_PJ\JP__02.Art\JP__Asset\JP__CH\JP__LUN\JP__Rig"
        r"\JP__Revision_01020_HDN\JP_0030_hairshrink")
SRC_FBX = os.path.join(DATA, "0010_src", "hair_01.fbx")
HOU_ABC = os.path.join(DATA, "0020_out", "hair_02.abc")

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def cvs(crv):
    p = cmds.xform(crv + ".cv[*]", q=True, ws=True, t=True)
    return [tuple(p[i:i + 3]) for i in range(0, len(p), 3)]


# --------------------------------------------------------------------------
# 합성 튜브: centers(t) 를 따라 링 n 개짜리 쿼드 튜브. 뿌리 = 열림(또는 극점), 끝 = 극점(또는 열림).
# --------------------------------------------------------------------------
def make_tube(name, centers, radius=0.5, around=12, root="open", tip="pole", normal_hint=(0, 0, 1)):
    pts = []
    rings = []
    for i, c in enumerate(centers):
        a = centers[min(i + 1, len(centers) - 1)]
        b = centers[max(i - 1, 0)]
        t = om.MVector(a[0] - b[0], a[1] - b[1], a[2] - b[2]).normal()
        u = (t ^ om.MVector(*normal_hint))
        if u.length() < 1e-6:
            u = t ^ om.MVector(1, 0, 0)
        u = u.normal()
        v = (t ^ u).normal()
        ring = []
        for k in range(around):
            ang = 2.0 * math.pi * k / around
            off = u * (radius * math.cos(ang)) + v * (radius * math.sin(ang))
            ring.append(len(pts))
            pts.append((c[0] + off.x, c[1] + off.y, c[2] + off.z))
        rings.append(ring)
    faces = []
    for r in range(len(rings) - 1):
        r0, r1 = rings[r], rings[r + 1]
        for k in range(around):
            faces.append([r0[k], r0[(k + 1) % around], r1[(k + 1) % around], r1[k]])

    def pole(ring, at, outward):
        idx = len(pts)
        pts.append(at)
        for k in range(around):
            a, b = ring[k], ring[(k + 1) % around]
            faces.append([a, b, idx] if outward else [b, a, idx])
    first, last = centers[0], centers[-1]
    if tip == "pole":
        d = om.MVector(*[last[i] - centers[-2][i] for i in range(3)]).normal() * radius
        pole(rings[-1], (last[0] + d.x, last[1] + d.y, last[2] + d.z), True)
    if root == "pole":
        d = om.MVector(*[first[i] - centers[1][i] for i in range(3)]).normal() * radius
        pole(rings[0], (first[0] + d.x, first[1] + d.y, first[2] + d.z), False)

    mpts = om.MPointArray([om.MPoint(*p) for p in pts])
    counts = [len(f) for f in faces]
    connects = [v for f in faces for v in f]
    tr = om.MFnTransform().create()
    om.MFnMesh().create(mpts, counts, connects, parent=tr)
    path = om.MDagPath.getAPathTo(tr).fullPathName()
    node = cmds.rename(path, name)
    shape = cmds.listRelatives(node, shapes=True, fullPath=True)[0]
    cmds.sets(shape, edit=True, forceElement="initialShadingGroup")
    return cmds.ls(node, long=True)[0]


def line_centers(n=21, length=10.0, axis=1, start=(0.0, 0.0, 0.0), down=True):
    out = []
    for i in range(n):
        p = list(start)
        p[axis] += (-1 if down else 1) * length * i / (n - 1)
        out.append(tuple(p))
    return out


def opts(**kw):
    return hm.HairOptions(**kw)


# ==========================================================================
print("\n=== T1 straight tube (open root up, pole tip down) ===")
cmds.file(new=True, force=True)
tube = make_tube("strandA", line_centers(start=(0, 20, 0)))
rep = hm.analyze([tube], opts(points_mode=hm.POINTS_PER_RING, smooth_iterations=0))
r = rep.results[0]
check("T1 one shell, made", len(rep.results) == 1 and not r.skipped, r.reason)
check("T1 method auto -> rings", r.method == hm.METHOD_RINGS, r.method)
check("T1 root = open-end centre", dist(r.points[0], (0, 20, 0)) < 1e-6, r.points[0])
check("T1 tip = pole", dist(r.points[-1], (0, 20 - 10 - 0.5, 0)) < 1e-6, r.points[-1])
check("T1 all on axis", max(math.hypot(p[0], p[2]) for p in r.points) < 1e-6)
check("T1 one point per ring + pole", len(r.points) == 22, len(r.points))
check("T1 no warnings", not r.warnings, r.warnings)

# ==========================================================================
print("\n=== T2 bent tube (arc) - ring centres exactly ===")
arc = [(10 * math.cos(a), 10 * math.sin(a), 0.0)
       for a in [math.pi / 2 - (math.pi / 2) * i / 20 for i in range(21)]]
bent = make_tube("strandBent", arc, normal_hint=(0, 0, 1))
r = hm.analyze([bent], opts(points_mode=hm.POINTS_PER_RING, smooth_iterations=0)).results[0]
check("T2 ring centres on the arc", max(dist(r.points[i], arc[i]) for i in range(21)) < 1e-6)
check("T2 root at arc start", dist(r.points[0], arc[0]) < 1e-6)

# ==========================================================================
print("\n=== T3 tube open at both ends -> fallback Highest Y ===")
both = make_tube("strandBoth", line_centers(start=(5, 0, 0), down=False), tip="none")
r = hm.analyze([both], opts(points_mode=hm.POINTS_PER_RING, smooth_iterations=0)).results[0]
check("T3 made", not r.skipped, r.reason)
check("T3 fallback warning", any("Root fallback" in w for w in r.warnings), r.warnings)
check("T3 cv0 is the higher end", r.points[0][1] > r.points[-1][1], (r.points[0], r.points[-1]))
r = hm.analyze([both], opts(root="-y", points_mode=hm.POINTS_PER_RING, smooth_iterations=0)).results[0]
check("T3 Lowest Y flips it", r.points[0][1] < r.points[-1][1] and not r.warnings)

# ==========================================================================
print("\n=== T4 closed tube (pole both ends) ===")
closed = make_tube("strandClosed", line_centers(start=(-5, 20, 0)), root="pole")
r = hm.analyze([closed], opts(points_mode=hm.POINTS_PER_RING, smooth_iterations=0)).results[0]
check("T4 made, one curve", not r.skipped, r.reason)
check("T4 root = upper pole (fallback Highest Y)", r.points[0][1] > r.points[-1][1] and
      any("no open end" in w for w in r.warnings), (r.points[0], r.warnings))
check("T4 auto -> geodesic (no open end)", r.method == hm.METHOD_GEODESIC, r.method)
check("T4 on axis", max(math.hypot(p[0] + 5, p[2]) for p in r.points) < 1e-6)
check("T4 spans both poles", abs(r.points[0][1] - 20.5) < 1e-6 and abs(r.points[-1][1] - 9.5) < 1e-6,
      (r.points[0], r.points[-1]))

# ==========================================================================
print("\n=== T5 two strands in one mesh ===")
a = make_tube("pa", line_centers(start=(20, 20, 0)))
b = make_tube("pb", line_centers(start=(25, 20, 0)))
comb = cmds.polyUnite(a, b, name="combo", constructionHistory=False)[0]
cmds.undoInfo(state=True, infinity=True)
cmds.undoInfo(openChunk=True)
rep = hm.create_curves([comb], opts(group_on=False))
cmds.undoInfo(closeChunk=True)
names = sorted(c.split("|")[-1] for c in rep.curves)
check("T5 two curves, _s01/_s02", names == ["combo_crv_s01", "combo_crv_s02"], names)
check("T5 shape names", all(cmds.listRelatives(c, shapes=True)[0] == c.split("|")[-1] + "Shape"
                            for c in rep.curves))
check("T5 source attribute", cmds.getAttr(rep.curves[0] + "." + hm.SOURCE_ATTR).endswith("combo"))
cmds.undo()
check("T5 undo removes both", not any(cmds.objExists(c) for c in ["combo_crv_s01", "combo_crv_s02"]))

# ==========================================================================
print("\n=== T6 / T7 filters ===")
cmds.file(new=True, force=True)
small = make_tube("tiny", line_centers(n=6, length=0.3, start=(0, 5, 0)), radius=0.05)
big = make_tube("big", line_centers(start=(3, 20, 0)))
rep = hm.analyze([small, big], opts())
check("T6 small mesh skipped (size)", rep.results[0].reason == hm.REASON_SMALL and not rep.results[1].skipped,
      [x.reason for x in rep.results])
check("T6 skipped_meshes", rep.skipped_meshes() == [small])
rep = hm.analyze([small, big], opts(min_size_on=False))
check("T7 then caught by length", rep.results[0].reason == hm.REASON_SHORT, rep.results[0].reason)
rep = hm.analyze([small, big], opts(min_size_on=False, min_length_on=False))
check("T7 both off -> both made", not rep.skipped)
rep = hm.analyze([big], opts(trim_root=6.0, trim_tip=6.0))
check("T7 trimmed out", rep.results[0].reason == hm.REASON_TRIMMED)
r = hm.analyze([big], opts(trim_root=1.0, trim_tip=2.0, smooth_iterations=0,
                           points_mode=hm.POINTS_PER_RING)).results[0]
check("T7 trim lengths", abs(r.points[0][1] - 19.0) < 1e-6 and abs(r.points[-1][1] - (9.5 + 2.0)) < 1e-6,
      (r.points[0], r.points[-1]))

# ==========================================================================
print("\n=== T8 / T9 / T10 output points ===")
r = hm.analyze([big], opts(count=10)).results[0]
segs = [dist(r.points[i], r.points[i + 1]) for i in range(len(r.points) - 1)]
mean = sum(segs) / len(segs)
sd = math.sqrt(sum((s - mean) ** 2 for s in segs) / len(segs))
check("T8 count 10, even", len(r.points) == 10 and sd / mean < 1e-3, (len(r.points), sd / mean))
r = hm.analyze([big], opts(points_mode=hm.POINTS_SPACING, spacing=1.0)).results[0]
segs = [dist(r.points[i], r.points[i + 1]) for i in range(len(r.points) - 1)]
check("T9 spacing ~1.0", all(abs(s - 1.0) < 0.06 for s in segs), (len(segs), segs[:3]))
rep = hm.create_curves([big], opts(degree=3, count=8, group_on=False))
crv = rep.curves[0]
fn = om.MFnNurbsCurve(om.MSelectionList().add(crv).getDagPath(0))
gap = max(fn.distanceToPoint(om.MPoint(*p), om.MSpace.kWorld) for p in rep.results[0].points)
check("T10 cubic passes through points", cmds.getAttr(crv + ".degree") == 3 and gap < 1e-3, gap)
cmds.delete(crv)

# ==========================================================================
print("\n=== T11 group + child meshes ===")
grp = cmds.group(empty=True, name="hair_grp")
p1 = make_tube("h1", line_centers(start=(0, 30, 5)))
p2 = make_tube("h2", line_centers(start=(2, 30, 5)))
p1 = cmds.ls(cmds.parent(p1, grp)[0], long=True)[0]
p2 = cmds.ls(cmds.parent(p2, p1)[0], long=True)[0]   # 메시 아래 메시
shapes, missing = hm.collect_meshes([grp, p1])
check("T11 group + child collected once", len(shapes) == 2 and not missing, shapes)
shapes, _ = hm.collect_meshes([grp], include_children=False)
check("T11 children off -> nothing under a bare group", shapes == [])
_, missing = hm.collect_meshes(["nope", grp])
check("T11 missing input reported", missing == ["nope"], missing)

# ==========================================================================
print("\n=== T12 parent transform ===")
cmds.xform(grp, t=(3, -2, 1), ro=(10, 20, 30), s=(2, 2, 2))
r = hm.analyze([p1], opts(include_children=False, points_mode=hm.POINTS_PER_RING,
                          smooth_iterations=0)).results[0]
m = om.MMatrix(cmds.xform(grp, q=True, ws=True, m=True))
want = om.MPoint(0, 30, 5) * m
check("T12 world space", dist(r.points[0], (want.x, want.y, want.z)) < 1e-5, (r.points[0], want))
cmds.xform(grp, t=(0, 0, 0), ro=(0, 0, 0), s=(1, 1, 1))

# ==========================================================================
print("\n=== T13 triangulated tube -> Geodesic ===")
tri = make_tube("tri", line_centers(start=(-10, 20, 0), n=31), radius=0.5)
cmds.polyTriangulate(tri, constructionHistory=False)
r = hm.analyze([tri], opts(points_mode=hm.POINTS_PER_RING)).results[0]
off = max(math.hypot(p[0] + 10, p[2]) for p in r.points)
check("T13 auto -> geodesic", r.method == hm.METHOD_GEODESIC, r.method)
check("T13 near axis (< 10% radius)", off < 0.05, off)
check("T13 root at top", r.points[0][1] > r.points[-1][1])

# ==========================================================================
print("\n=== T14 branch detection (graph) ===")


def chain(adj, a, b):
    adj.setdefault(a, set()).add(b)
    adj.setdefault(b, set()).add(a)


adj = {}
for i in range(9):
    chain(adj, i, i + 1)              # 줄기 0..9
chain(adj, 9, 10)
for i in range(10, 19):
    chain(adj, i, i + 1)              # 긴 가지 10..19
chain(adj, 9, 20)
for i in range(20, 24):
    chain(adj, i, i + 1)              # 짧은 가지 20..24
levels = hm.levels_rings(adj, [0])
kept, branched = hm.keep_main_trunk(adj, levels)
flat = [v for lv in kept for v in lv]
check("T14 branched", branched)
check("T14 longest branch kept", 19 in flat and not any(v in flat for v in range(20, 25)), flat)
adj2 = {}
for i in range(19):
    chain(adj2, i, i + 1)
chain(adj2, 18, 30)                    # 끝에서 한 칸짜리 곁가지 = 잡음
_, br2 = hm.keep_main_trunk(adj2, hm.levels_rings(adj2, [0]))
check("T14 one-level spur is not a branch", not br2)

# ==========================================================================
print("\n=== T15 undo / redo (group) ===")
cmds.file(new=True, force=True)
t1 = make_tube("u1", line_centers(start=(0, 20, 0)))
t2 = make_tube("u2", line_centers(start=(3, 20, 0)))
cmds.undoInfo(openChunk=True)
rep = hm.create_curves([t1, t2], opts())
cmds.undoInfo(closeChunk=True)
check("T15 under group", all(c.startswith("|" + hm.GROUP_DEFAULT + "|") for c in rep.curves), rep.curves)
check("T15 selected", sorted(cmds.ls(sl=True, long=True)) == sorted(rep.curves))
cmds.undo()
check("T15 one undo removes curves and group", not cmds.objExists(hm.GROUP_DEFAULT) and
      not cmds.ls("u1_crv", "u2_crv"))
cmds.redo()
check("T15 redo restores", cmds.objExists(hm.GROUP_DEFAULT) and len(cmds.ls("u1_crv", "u2_crv")) == 2)

# ==========================================================================
print("\n=== T16 joints land on CVs (By parameter) ===")
crv = cmds.ls("u1_crv", long=True)[0]
res = jm.build_joints_on_curves([crv], count=10, spacing=jm.SPACING_PARAM, bind=False,
                                group=False, use_zro=False, use_con=False, use_tgt=False, constraints=[])
jpos = [tuple(cmds.xform(j, q=True, ws=True, t=True)) for j in res["joints"]]
cvp = cvs(crv)
err = max(dist(a, b) for a, b in zip(jpos, cvp))
check("T16 joint i == cv[i]", len(jpos) == 10 == len(cvp) and err < 1e-4, err)

# ==========================================================================
print("\n=== T17 / T18 UI ===")
from tools.A00400_CurveTool.app.ui.main_window import MainWindow   # noqa: E402

cmds.file(new=True, force=True)
w1 = make_tube("ui1", line_centers(start=(0, 20, 0)))
w2 = make_tube("ui2", line_centers(start=(3, 20, 0)))
w3 = make_tube("uiTiny", line_centers(n=4, length=0.2, start=(6, 20, 0)), radius=0.05)
win = MainWindow()
labels = [win.create_tabs.tabText(i) for i in range(win.create_tabs.count())]
check("T17 From Hair tab", "From Hair" in labels, labels)
ht = win.hair_tab
check("T17 defaults", ht.cb_method.currentData() == hm.METHOD_AUTO and ht.sb_count.value() == 10
      and ht.rb_linear.isChecked() and ht.chk_min_size.isChecked() and ht.chk_min_len.isChecked()
      and ht.chk_children.isChecked())
check("T17 enable rules", not ht.sb_spacing.isEnabled() and ht.sb_count.isEnabled()
      and not ht.btn_send.isEnabled() and not ht.btn_select_skipped.isEnabled())
ht.cb_points.setCurrentIndex(1)
check("T17 spacing mode enables Spacing", ht.sb_spacing.isEnabled() and not ht.sb_count.isEnabled())
ht.cb_points.setCurrentIndex(0)
ht.on_analyze()
last = win.te_log.toPlainText().strip().splitlines()[-1]
check("T17 empty list warns", "empty" in last.lower(), last)

ht.tsl.set_items([w1, w2, w3])
ht.on_analyze()
log = win.te_log.toPlainText()
check("T17 analyze summary", "3 shells from 3 meshes - 2 curves to create, 1 skipped" in log, log[-300:])
check("T17 analyze changes nothing", not cmds.ls(type="nurbsCurve"))
ht.on_create()
check("T17 create makes 2", len(cmds.ls(type="nurbsCurve")) == 2)
cmds.undo()
check("T17 UI create = one undo step", not cmds.ls(type="nurbsCurve"))
cmds.redo()
check("T17 redo", len(cmds.ls(type="nurbsCurve")) == 2)
cmds.rename(w3, "uiTinyRenamed")
cmds.select(clear=True)
sel = ht.on_select_skipped()
check("T18 select skipped after rename (UUID)", [s.split("|")[-1] for s in sel] == ["uiTinyRenamed"], sel)
check("T17 send enabled", ht.btn_send.isEnabled())
ht.on_send_to_joints()
check("T17 send -> joints list + count + By parameter",
      len(win.tsl_joints.get_all_items()) == 2 and win.sb_jnt_count.value() == 10
      and win.rb_jnt_param.isChecked() and win.edit_tabs.tabText(win.edit_tabs.currentIndex()) == "Joints"
      and win.tabs.tabText(win.tabs.currentIndex()) == "Edit")
win.close()

# ==========================================================================
print("\n=== G  golden: LUN hair_01.fbx vs Houdini hair_02.abc ===")
if not (os.path.exists(SRC_FBX) and os.path.exists(HOU_ABC)):
    print("SKIP golden (data not found)")
else:
    cmds.file(new=True, force=True)
    cmds.loadPlugin("fbxmaya", quiet=True)
    cmds.loadPlugin("AbcImport", quiet=True)
    cmds.file(SRC_FBX, i=True, type="FBX", ignoreVersion=True)
    hair_top = [n for n in cmds.ls(assemblies=True, long=True)
                if n not in ("|persp", "|top", "|front", "|side")]
    t0 = time.perf_counter()
    rep_a = hm.analyze(hair_top, opts())
    t_an = time.perf_counter() - t0
    t0 = time.perf_counter()
    cmds.undoInfo(openChunk=True)
    rep = hm.create_curves(hair_top, opts(points_mode=hm.POINTS_SPACING, spacing=0.1))
    cmds.undoInfo(closeChunk=True)
    t_cr = time.perf_counter() - t0
    print("  analyze {0:.2f}s  create {1:.2f}s".format(t_an, t_cr))
    for line, _ in rep.summary_lines():
        print("  " + line)
    check("G curve count 148", len(rep.made) == 148, len(rep.made))
    check("G one skipped (degenerate/small)", len(rep.skipped) == 1 and
          rep.skipped[0].reason in (hm.REASON_DEGENERATE, hm.REASON_SMALL), [r.reason for r in rep.skipped])
    check("G no branch warnings", not any(r.branched for r in rep.results))
    check("G analyze + create < 3s", t_an + t_cr < 3.0, round(t_an + t_cr, 2))
    down = sum(1 for r in rep.made if r.points[0][1] > r.points[-1][1])
    check("G root above tip on >= 146", down >= 146, down)

    before = set(cmds.ls(type="transform", long=True))
    cmds.AbcImport(HOU_ABC, mode="import")
    hou_curves = [c for c in cmds.ls(type="nurbsCurve", long=True)
                  if not c.startswith("|" + hm.GROUP_DEFAULT)]
    hou = []
    for c in hou_curves:
        p = cmds.xform(c + ".cv[*]", q=True, ws=True, t=True)
        if len(p) // 3 > 3:
            hou.append([tuple(p[i:i + 3]) for i in range(0, len(p), 3)])
    print("  houdini curves", len(hou))

    def mean_min_dist(a_pts, b_pts):
        return sum(min(dist(p, q) for q in b_pts) for p in a_pts) / len(a_pts)

    def bbox_c(pts):
        return tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))

    hou_c = [bbox_c(h) for h in hou]
    devs = []
    for r in rep.made:
        mine = r.points[::4] or r.points
        c = bbox_c(r.points)
        # 중심이 가까운 후보 5개 중 가장 잘 맞는 Houdini 커브
        cand = sorted(range(len(hou)), key=lambda i: dist(hou_c[i], c))[:5]
        devs.append(min(mean_min_dist(hou[i][::2], mine) for i in cand))
    devs.sort()
    med, p95 = devs[len(devs) // 2], devs[int(len(devs) * 0.95)]
    check("G deviation median <= 0.3 cm", med <= 0.3, round(med, 4))
    check("G deviation p95 <= 0.5 cm", p95 <= 0.5, round(p95, 4))

# ==========================================================================
print("\n=== RESULT: {0}/{1} passed ===".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
