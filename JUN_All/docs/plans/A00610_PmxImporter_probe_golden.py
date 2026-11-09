# -*- coding: utf-8 -*-
# A00610_PmxImporter 계획 실측용 (2026-11-09). 기준 mb(CATS->FBX) 와 PMX 를 대조 - 위치 · UV · 감기 · 노멀.
#   mayapy -I A00610_PmxImporter_probe_golden.py <base.mb> <model.pmx> <out.txt>
import sys, io, struct
out = io.open(sys.argv[3], "w", encoding="utf-8")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n"); out.flush()
b = open(sys.argv[2], "rb").read(); p = [0]
def r(fmt):
    v = struct.unpack_from("<"+fmt, b, p[0]); p[0] += struct.calcsize("<"+fmt); return v if len(v) > 1 else v[0]
p[0] = 4; r("f"); n = r("B"); g = [r("B") for _ in range(n)]
enc, addUV, vis, tis, mis, bis = g[:6]
def txt():
    L = r("i"); s = b[p[0]:p[0]+L]; p[0] += L; return s.decode("utf-16-le" if enc == 0 else "utf-8")
I = {1: "b", 2: "h", 4: "i"}; U = {1: "B", 2: "H", 4: "i"}
for _ in range(4): txt()
nv = r("i"); pos = []; nrm = []; uv = []; w = []
for _ in range(nv):
    pos.append(r("3f")); nrm.append(r("3f")); uv.append(r("2f")); [r("4f") for _ in range(addUV)]
    t = r("B")
    if t == 0: w.append([(r(I[bis]), 1.0)])
    elif t == 1: b0 = r(I[bis]); b1 = r(I[bis]); ww = r("f"); w.append([(b0, ww), (b1, 1-ww)])
    elif t in (2, 4): bb = [r(I[bis]) for _ in range(4)]; ww = r("4f"); w.append(list(zip(bb, ww)))
    elif t == 3: b0 = r(I[bis]); b1 = r(I[bis]); ww = r("f"); r("9f"); w.append([(b0, ww), (b1, 1-ww)])
    r("f")
nf = r("i"); faces = [r(U[vis]) for _ in range(nf)]
P("pmx verts", nv, "tris", nf//3)

import maya.standalone; maya.standalone.initialize()
import maya.cmds as cmds
import maya.api.OpenMaya as om
cmds.file(sys.argv[1], o=True, f=True, iv=True, lnr=True)
sc = "skinCluster1"
# 원본 형태: skin 입력 쪽 orig shape
orig = [s for s in cmds.listRelatives("Body", s=True, f=True) if cmds.getAttr(s+".intermediateObject")]
P("shapes", cmds.listRelatives("Body", s=True, f=True), "orig", orig)
sel = om.MSelectionList(); sel.add(orig[0]); fn = om.MFnMesh(sel.getDagPath(0))
M = om.MMatrix(cmds.xform("Body", q=True, ws=True, m=True))
mp = [om.MPoint(q) * M for q in fn.getPoints(om.MSpace.kObject)]
best = None
for name, f in [("x,y,-z", lambda v: (v[0], v[1], -v[2])), ("x,y,z", lambda v: v), ("-x,y,z", lambda v: (-v[0], v[1], v[2]))]:
    d = max(max(abs(mp[i][k] - f(pos[i])[k]*8.0) for k in range(3)) for i in range(nv))
    P("pos maxdiff", name, "x8", d)
# 메시 월드 변환
P("Body xform", cmds.xform("Body", q=True, ws=True, m=True))
us, vs = fn.getUVs("UVMap")
P("uv count", len(us))
# 버텍스 0..: face-vertex uv 비교 (u, 1-v)
it = om.MItMeshFaceVertex(sel.getDagPath(0)); dmax = 0; cnt = 0
while not it.isDone():
    vi = it.vertexId(); u, v = it.getUV("UVMap")
    dmax = max(dmax, abs(u-uv[vi][0]), abs(v-(1-uv[vi][1]))); cnt += 1; it.next()
P("uv maxdiff (u,1-v)", dmax, "fv", cnt)
# 와인딩: 첫 삼각형들 비교
tri0 = faces[0:3]; P("pmx tri0", tri0, "maya face0", list(fn.getPolygonVertices(0)), "maya face1", list(fn.getPolygonVertices(1)), "polys", fn.numPolygons)
# 노멀 비교 (x,y,-z)
nm = [om.MVector(q) * M for q in fn.getVertexNormals(False, om.MSpace.kObject)]
nm = [q.normal() for q in nm]
# 와인딩: pmx 순서 그대로 (x,y,-z) 로 만든 면 노멀 vs 마야 정점 노멀 평균 방향
def W(i): v = pos[i]; return om.MVector(v[0]*8, v[1]*8, -v[2]*8)
agree = 0; tot = 0
for t in range(0, nf//3, 5):
    a, b2, c = faces[3*t:3*t+3]
    fnm = (W(b2)-W(a)) ^ (W(c)-W(a))
    if fnm.length() < 1e-9: continue
    avg = nm[a] + nm[b2] + nm[c]
    agree += (fnm * avg) > 0; tot += 1
P("pmx order (x,y,-z) face normal agrees with maya normals:", agree, "/", tot)
dn = max(max(abs(nm[i][k] - (nrm[i][0], nrm[i][1], -nrm[i][2])[k]) for k in range(3)) for i in range(0, nv, 7))
P("normal maxdiff sample (x,y,-z)", dn, "locked normals", fn.isNormalLocked(0) if hasattr(fn, "isNormalLocked") else "?")
# 블렌드셰이프 타깃 0 델타 vs 첫 모프 수는 별도
P("bs weights", len(cmds.listAttr("Miyabi_ncl1_3.w", m=True)))
P("skin method", cmds.getAttr(sc+".skinningMethod"), "normalize", cmds.getAttr(sc+".normalizeWeights"))
