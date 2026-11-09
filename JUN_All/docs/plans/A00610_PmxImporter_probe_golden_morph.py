# -*- coding: utf-8 -*-
# A00610_PmxImporter 계획 실측용 (2026-11-09). 추가 UV · 모프 델타를 기준 mb(tgt_grp 타깃 메시)와 대조.
#   mayapy -I A00610_PmxImporter_probe_golden_morph.py <base.mb> <model.pmx> <out.txt>
import sys, io, struct, re
out = io.open(sys.argv[3], "w", encoding="utf-8")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n"); out.flush()
b = open(sys.argv[2], "rb").read(); p = [0]
def r(fmt):
    v = struct.unpack_from("<"+fmt, b, p[0]); p[0] += struct.calcsize("<"+fmt); return v if len(v) > 1 else v[0]
p[0] = 4; r("f"); n = r("B"); g = [r("B") for _ in range(n)]
enc, addUV, vis, tis, mis, bis, mois, ris = g
def txt():
    L = r("i"); s = b[p[0]:p[0]+L]; p[0] += L; return s.decode("utf-16-le")
I = {1: "b", 2: "h", 4: "i"}; U = {1: "B", 2: "H", 4: "i"}
for _ in range(4): txt()
nv = r("i"); auv = []
for _ in range(nv):
    r("8f"); auv.append([r("4f") for _ in range(addUV)])
    t = r("B")
    if t == 0: r(I[bis])
    elif t == 1: r(I[bis]); r(I[bis]); r("f")
    elif t in (2, 4): [r(I[bis]) for _ in range(4)]; r("4f")
    elif t == 3: r(I[bis]); r(I[bis]); r("f"); r("9f")
    r("f")
nf = r("i"); [r(U[vis]) for _ in range(nf)]
nt = r("i"); [txt() for _ in range(nt)]
nm = r("i")
for _ in range(nm):
    txt(); txt(); r("4f"); r("3f"); r("f"); r("3f"); r("B"); r("4f"); r("f"); r(I[tis]); r(I[tis]); r("B"); ts = r("B"); r("B") if ts else r(I[tis]); txt(); r("i")
nb = r("i")
for _ in range(nb):
    txt(); txt(); r("3f"); r(I[bis]); r("i"); fl = r("H")
    r(I[bis]) if fl & 1 else r("3f")
    if fl & 0x300: r(I[bis]); r("f")
    if fl & 0x400: r("3f")
    if fl & 0x800: r("6f")
    if fl & 0x2000: r("i")
    if fl & 0x20:
        r(I[bis]); r("i"); r("f"); c = r("i")
        for _ in range(c):
            r(I[bis]); h = r("B")
            if h: r("6f")
morphs = {}
for _ in range(r("i")):
    name = txt(); txt(); r("B"); t = r("B"); c = r("i"); d = {}
    for _ in range(c):
        vi = r(U[vis]); d[vi] = r("3f")
    morphs[name] = d
import maya.standalone; maya.standalone.initialize()
import maya.cmds as cmds, maya.api.OpenMaya as om
cmds.file(sys.argv[1], o=True, f=True, iv=True, lnr=True)
orig = [s for s in cmds.listRelatives("Body", s=True, f=True) if cmds.getAttr(s+".intermediateObject")][0]
sel = om.MSelectionList(); sel.add(orig); fn = om.MFnMesh(sel.getDagPath(0))
for k, setname in enumerate(["UV1", "UV2"]):
    it = om.MItMeshFaceVertex(sel.getDagPath(0)); dflip = dkeep = 0
    while not it.isDone():
        vi = it.vertexId(); u, v = it.getUV(setname); a = auv[vi][k]
        dflip = max(dflip, abs(u-a[0]), abs(v-(1-a[1]))); dkeep = max(dkeep, abs(u-a[0]), abs(v-a[1])); it.next()
    P(setname, "maxdiff flip", dflip, "keep", dkeep, "sample zw", auv[100][k][2:], "nonzero zw", sum(1 for x in auv if abs(x[k][2])+abs(x[k][3]) > 1e-6))
def dec(s):
    by = bytearray(); i = 0
    for m in re.finditer(r"FBXASC(\d{3})|(.)", s):
        if m.group(1): by.append(int(m.group(1)))
        else: by += m.group(2).encode()
    return by.decode("utf-8", "replace")
bs = "Miyabi_ncl1_3"
names = cmds.listAttr(bs + ".w", m=True)
P("bs origin", cmds.getAttr(bs + ".origin"), "decoded first", [dec(x) for x in names[:6]])
base = fn.getPoints()
M = om.MMatrix(cmds.xform("Body", q=True, ws=True, m=True))
for idx, al in enumerate(names):
    nm_ = dec(al)
    tgts = cmds.ls("tgt_grp|" + al)
    if not tgts: P("no tgt mesh for", nm_); continue
    s2 = om.MSelectionList(); s2.add(tgts[0]); tp = om.MFnMesh(s2.getDagPath(0)).getPoints(om.MSpace.kObject)
    bw = base
    d = morphs.get(nm_); mx = 0
    for vi in range(len(bw)):
        o = d.get(vi, (0, 0, 0)); exp = (o[0]*8, o[1]*8, -o[2]*8)
        got = (tp[vi] - bw[vi]) * M; mx = max(mx, abs(got.x-exp[0]), abs(got.y-exp[1]), abs(got.z-exp[2]))
    P("morph", nm_, "n", len(d) if d else None, "delta maxdiff (x,y,-z)*8", mx)
