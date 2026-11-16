# -*- coding: utf-8 -*-
"""A00380 LOD 코어(lod_manager) 헤드리스 시험 - 계획서 9-1 의 A ~ I.

실행:
    "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe" A00380_MeshTool_LOD_probe_test.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))   # JUN_All

import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds
import numpy as np

from tools.A00380_MeshTool.app.core import lod_manager as lm

FAILS = []


def check(name, cond, info=""):
    print("{0} {1} {2}".format("PASS" if cond else "FAIL", name, info))
    if not cond:
        FAILS.append(name)


def bbox(node):
    shape = (cmds.listRelatives(node, s=True, ni=True, f=True) or [node])[0]
    return np.array(cmds.exactWorldBoundingBox(shape)).reshape(2, 3)


def opts(**kw):
    o = lm.LodOptions()
    for k, v in kw.items():
        setattr(o, k, v)
    return o


# ---------------------------------------------------------------- A / B
for div in (200, 400):
    cmds.file(new=True, force=True)
    sph = cmds.polySphere(sx=div, sy=div, ch=False, n="sph")[0]
    src = lm.mesh_tris(sph)
    o = opts(count=5)
    t0 = time.time()
    rep = lm.build_lods([sph], o)
    t_fast = time.time() - t0
    ok = True
    for lv, mesh, tris in rep.results[0].lods:
        tgt = lm.target_tris(src, o, lv)
        ok &= (tris <= tgt and tris >= 0.85 * tgt)
        print("   LOD{0}: {1} / target {2}".format(lv, tris, tgt))
    check("A tris within [85%,100%] of target (src {0})".format(src), ok)
    cmds.delete(rep.group)
    t0 = time.time()
    for lv in range(1, 6):
        d = cmds.duplicate(sph)[0]
        cmds.polyReduce(d, ver=1, trm=2, tct=lm.target_tris(src, o, lv), kqw=0, uwt=0, cwt=0, ch=False)
    t_q = time.time() - t0
    check("B fast faster than polyReduce (src {0})".format(src), t_fast < t_q,
          "fast {0:.2f}s vs polyReduce {1:.2f}s ({2:.1f}x)".format(t_fast, t_q, t_q / t_fast))

# ---------------------------------------------------------------- C 얇은 판 두 장
cmds.file(new=True, force=True)
a = cmds.polyPlane(w=10, h=10, sx=100, sy=100, ch=False)[0]
b = cmds.polyPlane(w=10, h=10, sx=100, sy=100, ch=False)[0]
cmds.move(0, 0.2, 0, b)
cmds.polyNormal(a, nm=0, ch=False)                 # 아래 판은 아래를 본다
plates = cmds.polyUnite(a, b, ch=False, n="plates")[0]
for keep in (True, False):
    rep = lm.build_lods([plates], opts(count=3, values=(50, 25, 3), keep_thin=keep))
    mesh = rep.results[0].lods[2][1]
    ys = np.array(cmds.xform(mesh + ".vtx[*]", q=True, ws=True, t=True)).reshape(-1, 3)[:, 1]
    mid = np.sum((ys > 0.05) & (ys < 0.15))
    if keep:
        check("C keep_thin: no vertex between the plates", mid == 0, "{0} in the gap".format(mid))
    else:
        print("   (keep_thin off: {0} vertices in the gap - expected to merge)".format(mid))
    cmds.delete(rep.group)

# ---------------------------------------------------------------- D UV
cmds.file(new=True, force=True)
s = cmds.polySphere(sx=60, sy=60, ch=False)[0]
rep = lm.build_lods([s], opts(count=2))
m = rep.results[0].lods[1][1]
uvs = cmds.polyEvaluate(m, uv=True)
nv = cmds.polyEvaluate(m, v=True)
uv = np.array(cmds.polyEditUV(m + ".map[*]", q=True)).reshape(-1, 2)
check("D UVs: one per vertex, in 0..1", uvs == nv and uv.min() >= 0 and uv.max() <= 1,
      "uv {0} / v {1}".format(uvs, nv))
check("D UV set name map1", cmds.polyUVSet(m, q=True, auv=True) == ["map1"])

# ---------------------------------------------------------------- E 재질
cmds.file(new=True, force=True)
s = cmds.polySphere(sx=80, sy=80, ch=False, n="matSph")[0]
sh = cmds.shadingNode("blinn", asShader=True)
sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, n="blinnSG")
cmds.connectAttr(sh + ".outColor", sg + ".surfaceShader")
nf = cmds.polyEvaluate(s, f=True)
cmds.sets("{0}.f[0:{1}]".format(s, nf // 2 - 1), e=True, forceElement=sg)
rep = lm.build_lods([s], opts(count=3))
m = rep.results[0].lods[2][1]
faces = cmds.ls(cmds.sets(sg, q=True), fl=True)
lod_faces = [f for f in faces if f.startswith(m.split("|")[-1])]
# 원본 blinn 면이 어느 반구인지(polySphere 면 0 은 아래쪽) 원본에서 재고, LOD blinn 면도 같은 쪽이어야 한다
src_y = np.array(cmds.xform("{0}.f[0:{1}]".format(s, nf // 2 - 1), q=True, ws=True, t=True)).reshape(-1, 3)[:, 1].mean()
side = 1.0 if src_y > 0 else -1.0
cy = []
for f in lod_faces:
    p = np.array(cmds.xform(f, q=True, ws=True, t=True)).reshape(-1, 3).mean(0)
    cy.append(p[1])
cy = np.array(cy)
ratio = np.mean(cy * side > -0.05) if len(cy) else 0
check("E materials follow original faces", len(lod_faces) > 0 and ratio > 0.95,
      "{0} faces, {1:.1%} on the right side".format(len(lod_faces), ratio))

# ---------------------------------------------------------------- F undo / redo
cmds.file(new=True, force=True)
s = cmds.polySphere(sx=50, sy=50, ch=False)[0]
cmds.undoInfo(state=True, infinity=True)
cmds.flushUndo()
n0 = len(cmds.ls())
rep = lm.build_lods([s], opts(count=3))
n1 = len(cmds.ls())
cmds.undo()
n2 = len(cmds.ls())
cmds.redo()
n3 = len(cmds.ls())
check("F undo removes everything", n2 == n0, "{0} -> {1} -> undo {2}".format(n0, n1, n2))
check("F redo restores", n3 == n1, "redo {0}".format(n3))

# ---------------------------------------------------------------- G 스킨 · 바인드 포즈
cmds.file(new=True, force=True)
cyl = cmds.polyCylinder(h=10, r=1, sx=40, sy=40, ch=False, n="arm")[0]
cmds.move(0, 5, 0, cyl)
cmds.select(cl=True)
j0 = cmds.joint(p=(0, 0, 0))
j1 = cmds.joint(p=(0, 5, 0))
j2 = cmds.joint(p=(0, 10, 0))
cmds.skinCluster([j0, j1, j2], cyl, tsb=True)
cmds.setAttr(j1 + ".rz", 90)
bind_bb = np.array([[-1, 0, -1], [1, 10, 1]], dtype=float)
rep = lm.build_lods([cyl], opts(count=2, source_pose="bind"))
bb = bbox(rep.results[0].lods[0][1])
check("G bind pose LOD matches bind bbox", np.abs(bb - bind_bb).max() < 0.15, str(bb.ravel().round(2)))
rep = lm.build_lods([cyl], opts(count=2, source_pose="current", overwrite=True))
bb2 = bbox(rep.results[0].lods[0][1])
# 트랜스폼 bbox 는 숨은 orig 셰이프(바인드 포즈)까지 포함한다 → 보이는 셰이프 점으로 잰다
vp = np.array(cmds.xform(cmds.listRelatives(cyl, s=True, ni=True, f=True)[0] + ".vtx[*]", q=True, ws=True, t=True)).reshape(-1, 3)
cur = np.array([vp.min(0), vp.max(0)])
check("G current pose LOD matches deformed bbox", np.abs(bb2 - cur).max() < 0.3,
      "{0} vs {1}".format(bb2.ravel().round(2), cur.ravel().round(2)))

# ---------------------------------------------------------------- H 트랜스폼
cmds.file(new=True, force=True)
s = cmds.polySphere(sx=40, sy=40, ch=False)[0]
cmds.xform(s, t=(3, 4, 5), ro=(30, 40, 50), s=(1, 2, 3))
cmds.setAttr(s + ".offsetParentMatrix",
             [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 2, 0, 0, 1], type="matrix")
rep = lm.build_lods([s], opts(count=1, values=(50,)))
c0 = bbox(s).mean(0)
c1 = bbox(rep.results[0].lods[0][1]).mean(0)
check("H world position kept", np.abs(c0 - c1).max() < 1e-2, str((c1 - c0).round(4)))

# ---------------------------------------------------------------- I 덮어쓰기 · 기록
grp = rep.group
rep2 = lm.build_lods([s], opts(count=1, values=(50,), overwrite=True))
check("I overwrite keeps one group", len(cmds.ls(lm.group_name([cmds.ls(s, l=True)[0]]))) == 1)
rep3 = lm.build_lods([s], opts(count=1, values=(50,), overwrite=False))
check("I no-overwrite makes a second group", rep3.group != rep2.group, rep3.group)
m = rep3.results[0].lods[0][1]
check("I junLodSource = source UUID",
      cmds.getAttr(m + ".junLodSource") == cmds.ls(s, uuid=True)[0])

# ---------------------------------------------------------------- Combine · Quality
cmds.file(new=True, force=True)
a = cmds.polySphere(sx=60, sy=60, ch=False)[0]
b = cmds.polyCube(sx=30, sy=30, sz=30, ch=False)[0]
cmds.move(4, 0, 0, b)
rep = lm.build_lods([a, b], opts(count=2, combine=True))
check("Combine: one mesh per LOD", len(rep.combined) == 2,
      str([(lv, t) for lv, _, t in rep.combined]))
bb = bbox(rep.combined[0][1])
check("Combine: world placement", bb[1][0] > 4.4 and bb[0][0] < -0.9, str(bb.ravel().round(2)))
rep = lm.build_lods([a, b], opts(count=2, method="quality", overwrite=True))
qt = [(r.source, [t for _, _, t in r.lods]) for r in rep.results]
check("Quality makes LODs", all(len(x[1]) == 2 for x in qt), str(qt))

print("\n{0} FAIL(S): {1}".format(len(FAILS), FAILS) if FAILS else "\nALL PASS")
maya.standalone.uninitialize()
