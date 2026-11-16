# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-16
# A00380_MeshTool - LOD 메시 생성 (v01.20)
#
# 재생용 저폴리 프록시(LOD) 메시를 빠르게 만든다. 바인딩은 하지 않는다.
# 계획서: JUN_All/docs/plans/A00380_MeshTool_LOD_plan.md
#
#   * Fast    : numpy 로 짠 "그리드 클러스터링 + 셀마다 QEM 대표점"(Lindstrom 2000).
#               통째로 계산하는 벡터 연산이라 polyReduce 보다 5~18배 빠르다(계획서 2장).
#               얇은 부위가 붙지 않게 버텍스 노멀 방향(6 버킷)을 셀 키에 넣는다.
#               UV 는 버텍스당 하나(대표 버텍스의 UV) - 이음매에서 늘어나 보여도 된다(요구사항).
#   * Quality : 원본(바인드 포즈)을 그대로 복사한 뒤 마야 polyReduce. 느리지만 깨끗하다.
#
# 스킨 · 블렌드셰이프가 있는 메시는 기본으로 **orig 셰이프(바인드 포즈)** 를 읽는다 →
# A00275 로 다시 바인딩할 때 자세가 맞는다.
#
# 계산(numpy, `_simplify_*`)과 씬 쓰기(`_create_*`)를 나눴다. 계산부는 마야 없이도 시험할 수 있다.

import time
from dataclasses import dataclass, field

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core import maya_shape
from Framework.core.maya_undo import undo_chunk

try:
    import numpy as np
except Exception:          # numpy 없는 마야 - Fast 를 막고 Quality 만 허용한다
    np = None


DEFAULT_VALUES = (50.0, 25.0, 12.5, 6.25, 3.125)
MAX_LODS = 5

# 기록 어트리뷰트 (재바인딩 · 다시 만들기용 - 파일 이름에 의존하지 않는다)
ATTR_SOURCE = "junLodSource"     # 원본 메시 UUID (Combine 이면 쉼표로 이은 목록)
ATTR_LEVEL = "junLodLevel"
ATTR_TARGET = "junLodTarget"
ATTR_METHOD = "junLodMethod"

UV_SET = "map1"                  # 이 툴의 UV 세트 규칙(UV Sets 탭)과 같은 이름


def has_numpy():
    return np is not None


# ======================================================================
# 옵션 · 결과
# ======================================================================

@dataclass
class LodOptions:
    count: int = 3
    mode: str = "ratio"                    # "ratio"(%) | "triangles"
    values: tuple = DEFAULT_VALUES         # LOD1..5 의 비율(%) 또는 삼각형 수
    method: str = "fast"                   # "fast" | "quality"
    source_pose: str = "bind"              # "bind"(orig 셰이프) | "current"(현재 변형 결과)
    approx_uvs: bool = True
    copy_materials: bool = True
    keep_thin: bool = True
    combine: bool = False
    overwrite: bool = True
    min_tris: int = 100


@dataclass
class LodResult:
    source: str                            # 원본 트랜스폼 (짧은 이름)
    src_tris: int = 0
    lods: list = field(default_factory=list)       # [(level, mesh, tris)]
    seconds: float = 0.0
    warnings: list = field(default_factory=list)


@dataclass
class BuildReport:
    group: str = ""
    results: list = field(default_factory=list)    # [LodResult]
    combined: list = field(default_factory=list)   # Combine 일 때 [(level, mesh, tris)]
    seconds: float = 0.0


# ======================================================================
# 입력
# ======================================================================

def _short(name):
    return name.split("|")[-1].split(":")[-1]


def _is_mesh_transform(node):
    return bool(cmds.listRelatives(node, s=True, ni=True, type="mesh", f=True))


def collect_meshes(nodes):
    """선택 · 리스트 항목을 메시 트랜스폼 롱네임 목록으로. 그룹은 아래를 펼친다(순서 유지, 중복 제거)."""
    out, seen = [], set()
    for node in nodes or []:
        node = node.split(".")[0]
        longs = cmds.ls(node, l=True) or []
        if not longs:
            continue
        node = longs[0]
        if cmds.objectType(node, isAType="shape"):
            node = cmds.listRelatives(node, p=True, f=True)[0]
        cands = [node] if _is_mesh_transform(node) else []
        for shape in cmds.listRelatives(node, ad=True, type="mesh", ni=True, f=True) or []:
            cands.append(cmds.listRelatives(shape, p=True, f=True)[0])
        for c in cands:
            if c not in seen and _is_mesh_transform(c):
                seen.add(c)
                out.append(c)
    return out


def find_orig_shape(shape):
    """디포머 체인 맨 위의 orig 셰이프(바인드 포즈). 디포머가 없거나 못 찾으면 None.

    조건: intermediateObject 인 mesh, inMesh 입력 없음, 버텍스 수가 같음.
    같은 트랜스폼 아래의 것을 먼저 고른다(블렌드셰이프 타깃 메시는 다른 트랜스폼이다).
    """
    if not cmds.listConnections(shape + ".inMesh", s=True, d=False):
        return None                        # 디포머 없음 - 셰이프 자체가 원본
    nv = cmds.polyEvaluate(shape, v=True)
    parent = cmds.listRelatives(shape, p=True, f=True)[0]
    cands = []
    for m in cmds.ls(cmds.listHistory(shape) or [], type="mesh", l=True) or []:
        if m == shape or not cmds.getAttr(m + ".intermediateObject"):
            continue
        if cmds.listConnections(m + ".inMesh", s=True, d=False):
            continue
        if cmds.polyEvaluate(m, v=True) != nv:
            continue
        same = cmds.listRelatives(m, p=True, f=True)[0] == parent
        cands.append((0 if same else 1, m))
    cands.sort()
    return cands[0][1] if cands else None


def _fn(node):
    sel = om.MSelectionList()
    sel.add(node)
    return om.MFnMesh(sel.getDagPath(0)), sel.getDagPath(0)


class MeshData(object):
    """한 메시의 읽기 + 사전 계산 결과. 모든 LOD 가 공유한다(계획서 4-1)."""

    def __init__(self, transform, source_pose="bind", want_uv=True, want_sg=True):
        self.transform = transform
        self.name = _short(transform)
        self.uuid = cmds.ls(transform, uuid=True)[0]
        self.matrix = cmds.xform(transform, q=True, ws=True, m=True)
        self.warnings = []

        shape = maya_shape.shape_path(transform, type_="mesh")
        read = shape
        if source_pose == "bind":
            orig = find_orig_shape(shape)
            if orig:
                read = orig
            elif cmds.listConnections(shape + ".inMesh", s=True, d=False):
                self.warnings.append("no bind-pose (orig) shape found - used the current pose")
        self.shape = shape
        self.read_shape = read

        fn, _ = _fn(read)
        self.P = np.array(fn.getPoints(om.MSpace.kObject), dtype=np.float64)[:, :3]
        counts, verts = fn.getVertices()
        self.counts = np.array(counts, dtype=np.int64)
        self.verts = np.array(verts, dtype=np.int64)
        tri_counts, tri_verts = fn.getTriangles()
        self.T = np.array(tri_verts, dtype=np.int64).reshape(-1, 3)
        self.tri_poly = np.repeat(np.arange(len(self.counts)), np.array(tri_counts, dtype=np.int64))

        # UV - 현재 UV 세트. 원본 그대로(Quality 용)와 버텍스당 하나(Fast 용) 둘 다 만든다.
        self.uv = None          # (u, v, uvCounts, uvIds) - 원본 그대로
        self.vert_uv = None     # (N,2)
        if want_uv:
            self._read_uv(fn)

        # 재질 - 폴리곤마다 셰이딩 그룹. orig 셰이프엔 연결이 없으므로 **보이는 셰이프**에서 읽는다.
        self.poly_sg = None
        self.sg_names = []
        if want_sg:
            self._read_sg(shape)

        self._quadrics()

    def _read_uv(self, fn):
        try:
            u, v = fn.getUVs()
            uv_counts, uv_ids = fn.getAssignedUVs()
        except Exception:
            return
        if len(u) == 0 or len(uv_ids) == 0:
            return
        u = np.array(u, dtype=np.float64)
        v = np.array(v, dtype=np.float64)
        uv_counts = np.array(uv_counts, dtype=np.int64)
        uv_ids = np.array(uv_ids, dtype=np.int64)
        self.uv = (u, v, uv_counts, uv_ids)
        # 버텍스당 첫 face-vertex 의 UV. UV 없는 면의 face-vertex 는 건너뛴다.
        mask = np.repeat(uv_counts > 0, self.counts)
        fv_verts = self.verts[mask]
        vert_uv = np.zeros((len(self.P), 2))
        # 팬시 대입은 마지막 값이 이긴다 → 거꾸로 넣어 **첫 등장**이 남게 한다
        vert_uv[fv_verts[::-1], 0] = u[uv_ids[::-1]]
        vert_uv[fv_verts[::-1], 1] = v[uv_ids[::-1]]
        self.vert_uv = vert_uv

    def _read_sg(self, shape):
        fn, dag = _fn(shape)
        try:
            sgs, idx = fn.getConnectedShaders(dag.instanceNumber())
        except Exception:
            return
        names = [om.MFnDependencyNode(o).name() for o in sgs]
        if not names:
            return
        idx = np.array(idx, dtype=np.int64)
        idx[idx < 0] = 0                    # 할당 없는 면은 첫 그룹으로
        if len(idx) != len(self.counts):
            return
        self.poly_sg = idx
        self.sg_names = names

    def _quadrics(self):
        P, T = self.P, self.T
        v0 = P[T[:, 0]]
        n = np.cross(P[T[:, 1]] - v0, P[T[:, 2]] - v0)          # 길이 = 면적 x 2
        area2 = np.linalg.norm(n, axis=1)
        nn = n / np.maximum(area2, 1e-30)[:, None]
        plane = np.concatenate([nn, -np.einsum("ij,ij->i", nn, v0)[:, None]], 1)
        kf = np.einsum("fi,fj->fij", plane, plane) * area2[:, None, None]
        kv = np.zeros((len(P), 4, 4))
        vn = np.zeros((len(P), 3))
        for k in range(3):
            np.add.at(kv, T[:, k], kf)
            np.add.at(vn, T[:, k], n)
        self.Kv = kv
        # 노멀 버킷 0..5 = 지배 축 x 2 + (음수면 1) - 계획서 4-4
        axis = np.argmax(np.abs(vn), axis=1)
        neg = vn[np.arange(len(vn)), axis] < 0
        self.bucket = axis * 2 + neg.astype(np.int64)
        self.bbmin = P.min(0) if len(P) else np.zeros(3)
        self.ext = float((P.max(0) - P.min(0)).max()) if len(P) else 1.0
        self.ext = max(self.ext, 1e-9)
        self._res_cache = {}

    @property
    def src_tris(self):
        return len(self.T)


# ======================================================================
# 계산 - 조각(Piece) 하나 = 만들 메시 하나의 배열
# ======================================================================

class Piece(object):
    """create 할 메시의 배열 묶음. face_sg 는 sg_names 의 인덱스."""

    def __init__(self, P, counts, connects, uv=None, face_sg=None, sg_names=None):
        self.P = P
        self.counts = counts
        self.connects = connects
        self.uv = uv                       # (u, v, uvCounts, uvIds) 또는 None
        self.face_sg = face_sg
        self.sg_names = sg_names or []

    @property
    def tris(self):
        return int(np.sum(self.counts - 2)) if len(self.counts) else 0


def _cluster(md, res, keep_thin):
    """해상도 res(가장 긴 축의 셀 수)로 클러스터링. (cid, g, 남는 삼각형 mask)"""
    cell = md.ext / res
    g = np.floor((md.P - md.bbmin) / cell).astype(np.int64)
    g = np.clip(g, 0, res)
    key = (g[:, 0] * (res + 2) + g[:, 1]) * (res + 2) + g[:, 2]
    if keep_thin:
        key = key * 6 + md.bucket
    _, cid = np.unique(key, return_inverse=True)
    cid = cid.reshape(-1)
    tc = cid[md.T]
    keep = (tc[:, 0] != tc[:, 1]) & (tc[:, 1] != tc[:, 2]) & (tc[:, 0] != tc[:, 2])
    # 중복 삼각형(앞뒤로 겹친 면 포함 - 양면 헤어 카드는 절반이 여기서 사라진다) 제거.
    # 정렬한 세 셀 번호를 정수 키 하나로 → 1차원 unique (axis=0 unique 보다 훨씬 빠르다)
    idx = np.flatnonzero(keep)
    s = np.sort(tc[idx], 1)
    nc = int(cid.max()) + 1
    tkey = (s[:, 0] * nc + s[:, 1]) * nc + s[:, 2]
    _, first = np.unique(tkey, return_index=True)
    keep = np.zeros(len(md.T), dtype=bool)
    keep[idx[first]] = True
    return cid, g, keep


def _count(md, res, keep_thin):
    """res 에서 남는(중복 제거 후) 삼각형 수. 이분 탐색용 - 메시마다 캐시."""
    k = (res, keep_thin)
    if k not in md._res_cache:
        md._res_cache[k] = int(_cluster(md, res, keep_thin)[2].sum())
    return md._res_cache[k]


def _find_res(md, target, keep_thin):
    """남는 삼각형 <= target 인 가장 큰 res. 추정값에서 출발해 구간을 잡고 이분 탐색."""
    probe = 64
    n = _count(md, probe, keep_thin)
    if n <= 0:
        est = probe * 4
    else:
        est = max(1, int(probe * (target / float(n)) ** 0.5))
    lo, hi = None, None
    r = est
    for _ in range(20):                     # 구간 잡기
        if _count(md, r, keep_thin) <= target:
            lo = r
            if hi is not None:
                break
            r = int(r * 1.5) + 1
            if r > 1 << 16:
                return lo
        else:
            hi = r
            if lo is not None:
                break
            if r <= 1:
                return 1
            r = max(1, int(r / 1.5))
    if lo is None:
        return 1
    if hi is None:
        return lo
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _count(md, mid, keep_thin) <= target:
            lo = mid
        else:
            hi = mid
    return lo


def simplify_fast(md, target, keep_thin=True, approx_uvs=True, copy_materials=True):
    """클러스터-QEM 으로 target 삼각형 이하의 Piece. 계획서 4-2."""
    res = _find_res(md, target, keep_thin)
    cid, g, keep = _cluster(md, res, keep_thin)
    nc = int(cid.max()) + 1
    cell = md.ext / res

    q = np.zeros((nc, 4, 4))
    np.add.at(q, cid, md.Kv)
    cnt = np.bincount(cid, minlength=nc).astype(np.float64)
    mean = np.zeros((nc, 3))
    for k in range(3):
        mean[:, k] = np.bincount(cid, weights=md.P[:, k], minlength=nc)
    mean /= cnt[:, None]
    a = q[:, :3, :3]
    b = -q[:, :3, 3]
    lam = 1e-3 * np.trace(a, axis1=1, axis2=2) / 3.0 + 1e-12 * md.ext * md.ext
    a = a + np.eye(3)[None] * lam[:, None, None]
    b = b + lam[:, None] * mean
    x = np.linalg.solve(a, b[..., None])[..., 0]

    # 셀 대표(첫 멤버)의 셀 상자로 자른다 - 조건 나쁜 셀에서 점이 튀는 것을 막는다
    order = np.lexsort((np.einsum("ij,ij->i", md.P - mean[cid], md.P - mean[cid]), cid))
    first = order[np.r_[0, np.flatnonzero(np.diff(cid[order])) + 1]]
    lo = md.bbmin + g[first] * cell
    x = np.clip(x, lo, lo + cell)
    x = np.where(np.isfinite(x), x, mean)

    tri = cid[md.T][keep]              # 중복은 _cluster 에서 이미 뺐다(원래 순서 유지)
    tri_poly = md.tri_poly[keep]

    used = np.unique(tri)
    remap = -np.ones(nc, np.int64)
    remap[used] = np.arange(len(used))
    tri = remap[tri]
    V = x[used]

    uv = None
    if approx_uvs and md.vert_uv is not None:
        # 셀마다 대표점에 가장 가까운 원본 버텍스의 UV (계획서 4-5)
        d = np.einsum("ij,ij->i", md.P - x[cid], md.P - x[cid])
        order = np.lexsort((d, cid))
        rep = order[np.r_[0, np.flatnonzero(np.diff(cid[order])) + 1]]
        cuv = md.vert_uv[rep[used]]
        uv = (cuv[:, 0], cuv[:, 1], np.full(len(tri), 3, np.int64), tri.ravel())

    face_sg, names = None, []
    if copy_materials and md.poly_sg is not None:
        face_sg = md.poly_sg[tri_poly]
        names = list(md.sg_names)

    return Piece(V, np.full(len(tri), 3, np.int64), tri.ravel(), uv, face_sg, names), res


def full_piece(md, copy_materials=True):
    """원본 그대로(폴리곤 · UV) - Quality 모드와 min_tris 이하 메시에 쓴다."""
    face_sg, names = None, []
    if copy_materials and md.poly_sg is not None:
        face_sg, names = md.poly_sg.copy(), list(md.sg_names)
    return Piece(md.P.copy(), md.counts.copy(), md.verts.copy(), md.uv, face_sg, names)


def _to_world(P, matrix):
    m = np.array(matrix, dtype=np.float64).reshape(4, 4)
    return P @ m[:3, :3] + m[3, :3]


def concat_pieces(pieces, matrices):
    """Combine - 월드 공간으로 옮겨 하나의 Piece 로. 재질은 이름으로 합친다."""
    Ps, counts, conns, us, vs, uvc, uvi, fsg = [], [], [], [], [], [], [], []
    names = []
    voff = uoff = 0
    has_uv = all(p.uv is not None for p in pieces)
    has_sg = all(p.face_sg is not None for p in pieces)
    for p, mtx in zip(pieces, matrices):
        Ps.append(_to_world(p.P, mtx))
        counts.append(p.counts)
        conns.append(p.connects + voff)
        if has_uv:
            u, v, c, i = p.uv
            us.append(u)
            vs.append(v)
            uvc.append(c)
            uvi.append(i + uoff)
            uoff += len(u)
        if has_sg:
            lut = []
            for n in p.sg_names:
                if n not in names:
                    names.append(n)
                lut.append(names.index(n))
            fsg.append(np.array(lut, np.int64)[p.face_sg])
        voff += len(p.P)
    uv = (np.concatenate(us), np.concatenate(vs), np.concatenate(uvc),
          np.concatenate(uvi)) if has_uv else None
    return Piece(np.concatenate(Ps), np.concatenate(counts), np.concatenate(conns), uv,
                 np.concatenate(fsg) if has_sg else None, names)


def _sorted_by_sg(piece):
    """면을 셰이딩 그룹 순서로 재배열 → 그룹마다 면 번호가 연속(할당을 그룹당 한 번에)."""
    if piece.face_sg is None or len(piece.sg_names) < 2:
        return piece, None
    order = np.argsort(piece.face_sg, kind="stable")
    counts = piece.counts
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
    new_counts = counts[order]
    total = int(new_counts.sum())
    # 가변 길이 면 재배열: 각 면의 시작 위치 + 0..len-1
    seg_start = np.concatenate([[0], np.cumsum(new_counts)[:-1]])
    idx = np.repeat(starts[order] - seg_start, new_counts) + np.arange(total)
    uv = None
    if piece.uv is not None:
        u, v, uvc, uvi = piece.uv
        if np.all(uvc == counts):
            uv = (u, v, uvc[order], uvi[idx])
        else:
            # UV 없는 면이 섞여 있으면 face-vertex 대응이 어긋난다 → 재배열 대신 UV 를 버리지 않고
            # 면 순서를 그대로 둔다
            return piece, None
    sg = piece.face_sg[order]
    p = Piece(piece.P, new_counts, piece.connects[idx], uv, sg, piece.sg_names)
    return p, sg


# ======================================================================
# 씬 쓰기
# ======================================================================

def _mobject(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDependNode(0)


def create_mesh(name, parent, piece, matrix=None):
    """트랜스폼은 cmds, 셰이프는 MFnMesh.create(parent=) - 둘이 같은 undo 청크로 사라진다."""
    piece, sorted_sg = _sorted_by_sg(piece)
    tr = cmds.createNode("transform", name=name, parent=parent)
    tr = cmds.ls(tr, l=True)[0]
    nv = len(piece.P)
    pts = om.MPointArray()
    pts.setLength(nv)
    for i, p in enumerate(piece.P.tolist()):
        pts[i] = om.MPoint(p[0], p[1], p[2])
    fn = om.MFnMesh()
    fn.create(pts, om.MIntArray(piece.counts.tolist()),
              om.MIntArray(piece.connects.tolist()), parent=_mobject(tr))
    shape = cmds.listRelatives(tr, s=True, f=True)[0]
    shape = cmds.rename(shape, _short(tr) + "Shape")
    shape = cmds.listRelatives(tr, s=True, f=True)[0]
    fn = om.MFnMesh(_fn(shape)[1])
    if piece.uv is not None:
        u, v, uvc, uvi = piece.uv
        fn.setUVs(om.MFloatArray(u.tolist()), om.MFloatArray(v.tolist()), UV_SET)
        fn.assignUVs(om.MIntArray(uvc.tolist()), om.MIntArray(uvi.tolist()), UV_SET)
    # 새 메시 에지는 하드로 생긴다 → 전부 부드럽게
    cmds.polySoftEdge(shape, a=180, ch=False)
    if matrix is not None:
        cmds.xform(tr, ws=True, m=matrix)
    _assign_materials(tr, shape, piece, sorted_sg)
    return tr


def _assign_materials(tr, shape, piece, sorted_sg):
    names = [n for n in piece.sg_names if cmds.objExists(n)]
    if piece.face_sg is None or not names:
        cmds.sets(shape, e=True, forceElement="initialShadingGroup")
        return
    if len(piece.sg_names) == 1 or sorted_sg is None:
        if len(set(piece.face_sg.tolist())) <= 1:
            sg = piece.sg_names[int(piece.face_sg[0])] if len(piece.face_sg) else names[0]
            cmds.sets(shape, e=True, forceElement=sg if cmds.objExists(sg) else "initialShadingGroup")
            return
        sorted_sg = piece.face_sg
    # 정렬돼 있으면 그룹마다 연속 구간 하나
    change = np.flatnonzero(np.diff(sorted_sg)) + 1
    starts = np.r_[0, change]
    ends = np.r_[change, len(sorted_sg)] - 1
    for s, e in zip(starts.tolist(), ends.tolist()):
        sg = piece.sg_names[int(sorted_sg[s])]
        if not cmds.objExists(sg):
            sg = "initialShadingGroup"
        cmds.sets("{0}.f[{1}:{2}]".format(shape, s, e), e=True, forceElement=sg)


def _tag(tr, uuids, level, target, method):
    for attr, kind, value in ((ATTR_SOURCE, "string", ",".join(uuids)),
                              (ATTR_LEVEL, "long", level),
                              (ATTR_TARGET, "long", target),
                              (ATTR_METHOD, "string", method)):
        if kind == "string":
            cmds.addAttr(tr, ln=attr, dt="string")
            cmds.setAttr("{0}.{1}".format(tr, attr), value, type="string")
        else:
            cmds.addAttr(tr, ln=attr, at="long")
            cmds.setAttr("{0}.{1}".format(tr, attr), value)


def _quality_reduce(tr, target):
    """polyReduce - 삼각형 수 지정. 이미 목표 이하면 그대로."""
    shape = cmds.listRelatives(tr, s=True, f=True)[0]
    if cmds.polyEvaluate(shape, t=True) <= target:
        return
    cmds.polyReduce(tr, ver=1, trm=2, tct=int(target), kqw=0, ch=False)


def mesh_tris(tr):
    shape = cmds.listRelatives(tr, s=True, f=True, ni=True)[0]
    return int(cmds.polyEvaluate(shape, t=True))


# ======================================================================
# 전체
# ======================================================================

def target_tris(src_tris, opts, level):
    """level(1부터)의 목표 삼각형 수. min_tris 를 바닥으로 쓰고 원본을 넘지 않는다."""
    v = opts.values[level - 1]
    t = int(round(src_tris * v / 100.0)) if opts.mode == "ratio" else int(v)
    return max(1, min(src_tris, max(t, opts.min_tris)))


def root_name(transforms):
    top = transforms[0].split("|")
    return _short(top[1] if len(top) > 1 else top[0])


def group_name(transforms):
    return "{0}_LOD_grp".format(root_name(transforms))


def build_lods(nodes, opts, progress=None, log=None):
    """nodes(트랜스폼 · 그룹)의 메시마다 LOD 1..count 를 만든다. 전체가 Ctrl+Z 한 번.

    Returns:
        BuildReport
    """
    t_all = time.time()
    if opts.method == "fast" and np is None:
        raise RuntimeError("numpy is not available - use Method = Quality.")
    if np is None:
        raise RuntimeError("numpy is required to read meshes.")
    transforms = collect_meshes(nodes)
    if not transforms:
        raise RuntimeError("No polygon meshes in the list.")
    count = max(1, min(MAX_LODS, int(opts.count)))
    total_steps = len(transforms) * (count + 1)
    step = [0]

    def tick(msg):
        step[0] += 1
        if progress:
            progress(step[0], total_steps, msg)

    report = BuildReport(group=group_name(transforms))
    with undo_chunk():
        top = "|" + report.group
        if cmds.objExists(top) and opts.overwrite:
            cmds.delete(top)
        report.group = cmds.ls(cmds.createNode("transform", name=report.group), l=True)[0]
        lod_grps = []
        for lv in range(1, count + 1):
            g = cmds.createNode("transform", name="{0}_LOD{1}_grp".format(
                root_name(transforms), lv), parent=report.group)
            lod_grps.append(cmds.ls(g, l=True)[0])

        combine_buf = {lv: [] for lv in range(1, count + 1)}   # lv -> [(piece, matrix, target, md)]
        for tr in transforms:
            t0 = time.time()
            res = LodResult(source=_short(tr))
            try:
                md = MeshData(tr, opts.source_pose, want_uv=opts.approx_uvs or opts.method == "quality",
                              want_sg=opts.copy_materials)
            except Exception as e:
                res.warnings.append("read failed: {0}".format(e))
                report.results.append(res)
                step[0] += count
                tick(res.source)
                continue
            res.src_tris = md.src_tris
            res.warnings.extend(md.warnings)
            tick("{0}: read".format(md.name))
            for lv in range(1, count + 1):
                target = target_tris(md.src_tris, opts, lv)
                try:
                    if opts.method == "quality" or md.src_tris <= opts.min_tris or target >= md.src_tris:
                        piece = full_piece(md, opts.copy_materials)
                        if not opts.approx_uvs and opts.method == "fast":
                            piece.uv = None
                    else:
                        piece, _ = simplify_fast(md, target, opts.keep_thin,
                                                 opts.approx_uvs, opts.copy_materials)
                    if opts.combine:
                        combine_buf[lv].append((piece, md.matrix, target, md))
                    else:
                        mesh = create_mesh("{0}_LOD{1}".format(md.name, lv), lod_grps[lv - 1],
                                           piece, md.matrix)
                        if opts.method == "quality":
                            _quality_reduce(mesh, target)
                        _tag(mesh, [md.uuid], lv, target, opts.method)
                        res.lods.append((lv, mesh, mesh_tris(mesh)))
                except Exception as e:
                    res.warnings.append("LOD{0} failed: {1}".format(lv, e))
                tick("{0}: LOD{1}".format(md.name, lv))
            res.seconds = time.time() - t0
            report.results.append(res)

        if opts.combine:
            for lv in range(1, count + 1):
                buf = combine_buf[lv]
                if not buf:
                    continue
                piece = concat_pieces([b[0] for b in buf], [b[1] for b in buf])
                target = sum(b[2] for b in buf)
                mesh = create_mesh("{0}_LOD{1}".format(root_name(transforms), lv),
                                   lod_grps[lv - 1], piece, None)
                if opts.method == "quality":
                    _quality_reduce(mesh, target)
                _tag(mesh, [b[3].uuid for b in buf], lv, target, opts.method)
                report.combined.append((lv, mesh, mesh_tris(mesh)))
    report.seconds = time.time() - t_all
    return report


def lod_meshes(group, level=None):
    """그룹 아래 LOD 메시(기록 어트리뷰트가 있는 트랜스폼). level 을 주면 그 단계만."""
    if not group or not cmds.objExists(group):
        return []
    out = []
    for tr in cmds.listRelatives(group, ad=True, type="transform", f=True) or []:
        if not cmds.attributeQuery(ATTR_LEVEL, node=tr, exists=True):
            continue
        if level is None or cmds.getAttr(tr + "." + ATTR_LEVEL) == level:
            out.append(tr)
    return out


def delete_group(group):
    if group and cmds.objExists(group):
        with undo_chunk():
            cmds.delete(group)
        return True
    return False
