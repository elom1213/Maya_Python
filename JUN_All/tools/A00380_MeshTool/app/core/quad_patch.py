# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00380_MeshTool - Quad Patch 코어 (v01.21)
#
# 구멍(짝수 개 보더 엣지)을 쿼드 그리드로 메운다. 블렌더 Grid Fill 과 같은 일을 하는 독자 구현이다.
# (참고한 외부 스크립트의 코드는 쓰지 않았다 - 아이디어만 같고 방식은 다르다.)
#
#   Edge Border  구멍 보더 엣지(일부만 골라도 그 보더 전체) -> 그리드로 채운다
#   Faces        고른 면들을 지우고 그 둘레를 그리드로 다시 채운다. 새 점은 원래 면 위로 투영하고
#                UV 도 원래 면에서 읽어 온다 (모양 · 텍스처 유지)
#   Extrude      보더의 일부 사슬(열린 엣지 줄)에서 구멍 안쪽으로 Rows 줄만큼 그리드를 뻗는다.
#                구멍은 작아진 채 남는다
#
# 방식
#   1. 보더 루프를 정렬하고(이웃 면의 감김과 반대 방향으로) 네 변 a, b, a, b 로 나눈다
#      (Rotation = 시작 위치, Proportion = a).
#   2. 네 변으로 Coons 패치(쌍선형 혼합 곡면)를 만들어 그리드 점의 초기 위치를 잡는다.
#      Inset 링이 있으면 링마다 파라미터 상자를 한 칸씩 줄여 같은 곡면에서 샘플한다.
#   3. 새 점만 라플라시안으로 Relax (Faces 는 매 반복 원래 면 위로 투영).
#   4. 미리보기 = API 로 만든 임시 와이어프레임 메시 (undo 큐에 남지 않는다).
#      확정 = polyAppendVertex 로 **원본 메시에 면을 직접 붙인다** - 트랜스폼 · 셰이프 · UUID 유지.
#      원래 히스토리가 없던 메시는 끝에 히스토리를 굽는다. 전부 Ctrl+Z 한 번.
#
# 슬롯(slot) 규약: 패치의 점 하나 = 슬롯 하나. 슬롯 0 ~ N-1 은 (회전 전) 보더 루프의 점,
# N 이상은 새로 만드는 점이다. 면은 슬롯 번호 튜플이다.

import math
import time

import numpy as np

import maya.cmds as cmds
import maya.api.OpenMaya as om


MODE_EDGE = "edge"
MODE_FACE = "face"
MODE_EXTRUDE = "extrude"

PREVIEW_NAME = "JUN_quadPatch_preview"
PREVIEW_COLOR = (0.35, 1.0, 0.55)

_EPS = 1e-4


class PatchError(Exception):
    """사용자에게 그대로 보여 줄 수 있는 실패 (영어 메시지)."""


# ======================================================================
# 메시 접근
# ======================================================================

def _dag(shape):
    sel = om.MSelectionList()
    sel.add(shape)
    return sel.getDagPath(0)


def _fn(shape):
    return om.MFnMesh(_dag(shape))


def _has_history(shape):
    return bool(cmds.listConnections(shape + ".inMesh", s=True, d=False))


def _selection(api_type):
    """활성 선택에서 (shape, transform, [ids]) - 메시 하나의 해당 컴포넌트만."""

    sel = om.MGlobal.getActiveSelectionList()
    found = {}
    for i in range(sel.length()):
        try:
            dag, comp = sel.getComponent(i)
        except Exception:
            continue
        if comp.isNull() or comp.apiType() != api_type:
            continue
        if dag.apiType() == om.MFn.kTransform:
            dag.extendToShape()
        ids = om.MFnSingleIndexedComponent(comp).getElements()
        found.setdefault(dag.fullPathName(), []).extend(ids)

    if not found:
        return None
    if len(found) > 1:
        raise PatchError("Components from more than one mesh are selected - pick one mesh.")
    shape, ids = list(found.items())[0]
    xform = cmds.listRelatives(shape, p=True, f=True)[0]
    return shape, xform, sorted(set(ids))


# ======================================================================
# 토폴로지 (필요한 곳만 API 로 읽는다 - 큰 메시도 전체 맵을 만들지 않는다)
# ======================================================================

class _Topo(object):

    def __init__(self, shape):
        self.shape = shape
        self.dag = _dag(shape)
        self.fn = om.MFnMesh(self.dag)
        self.eit = om.MItMeshEdge(self.dag)
        self.vit = om.MItMeshVertex(self.dag)

    def edge_verts(self, e):
        return tuple(self.fn.getEdgeVertices(e))

    def edge_faces(self, e):
        self.eit.setIndex(e)
        return list(self.eit.getConnectedFaces())

    def is_boundary(self, e):
        self.eit.setIndex(e)
        return self.eit.onBoundary()

    def vert_edges(self, v):
        self.vit.setIndex(v)
        return list(self.vit.getConnectedEdges())

    def vert_faces(self, v):
        self.vit.setIndex(v)
        return list(self.vit.getConnectedFaces())

    def face_verts(self, f):
        return list(self.fn.getPolygonVertices(f))

    def face_edges(self, f):
        it = om.MItMeshPolygon(self.dag)
        it.setIndex(f)
        return list(it.getEdges())

    def point(self, v):
        p = self.fn.getPoint(v, om.MSpace.kObject)
        return (p.x, p.y, p.z)

    def boundary_loop_of(self, e):
        """보더 엣지 e 가 속한 보더 루프 전체의 엣지 집합."""
        out = set([e])
        stack = [e]
        while stack:
            cur = stack.pop()
            for v in self.edge_verts(cur):
                for ne in self.vert_edges(v):
                    if ne not in out and self.is_boundary(ne):
                        out.add(ne)
                        stack.append(ne)
        return out


def _walk(topo, edges, closed):
    """엣지 집합을 정점 순서로 줄 세운다. closed=True 면 닫힌 루프, False 면 열린 사슬.

    돌려주는 것: 정점 id 리스트 (닫힌 루프는 처음 정점을 끝에 반복하지 않는다).
    """
    adj = {}
    for e in edges:
        a, b = topo.edge_verts(e)
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    for v, ns in adj.items():
        if len(ns) > 2:
            raise PatchError(
                "The edges branch at vertex {0} (a vertex shared by two holes) - "
                "pick a simple border.".format(v))

    if closed:
        if any(len(ns) != 2 for ns in adj.values()):
            raise PatchError("The edges do not form one closed loop.")
        start = min(adj)
    else:
        ends = [v for v, ns in adj.items() if len(ns) == 1]
        if len(ends) != 2:
            raise PatchError("The edges do not form one open chain.")
        start = min(ends)

    order = [start]
    prev = None
    cur = start
    while True:
        nxt = [n for n in adj[cur] if n != prev]
        if not nxt:
            break
        n = nxt[0]
        if closed and n == start:
            break
        order.append(n)
        prev, cur = cur, n
        if len(order) > len(adj):
            break

    if len(order) != len(adj):
        raise PatchError("The edges form more than one loop - pick one hole.")
    return order


def _winding_has(face_verts, a, b):
    """면의 정점 순서에 a -> b 가 (순환으로) 들어 있는가."""
    n = len(face_verts)
    for i in range(n):
        if face_verts[i] == a and face_verts[(i + 1) % n] == b:
            return True
    return False


def _orient(topo, loop, outside_face_of_edge):
    """패치 면이 loop[i] -> loop[i+1] 로 감기도록 방향을 맞춘다.

    바깥(남는) 면은 같은 엣지를 반대로 감아야 메시가 한 방향이 된다. 바깥 면이
    loop[0] -> loop[1] 로 감고 있으면 루프를 뒤집는다(시작 정점은 그대로).
    """
    a, b = loop[0], loop[1]
    f = outside_face_of_edge(a, b)
    if f is None:
        return loop
    if _winding_has(topo.face_verts(f), a, b):
        return [loop[0]] + loop[:0:-1]
    return loop


def _edge_between(topo, a, b):
    for e in topo.vert_edges(a):
        if b in topo.edge_verts(e):
            return e
    return None


# ======================================================================
# 패치 기하 (순수 numpy - 마야 없이도 돈다)
# ======================================================================

def _side_eval(pts, t):
    """점 열 pts(균등 인덱스 파라미터 0..1)의 t 위치를 선형 보간."""
    n = len(pts) - 1
    s = min(max(t, 0.0), 1.0) * n
    i = min(int(math.floor(s)), n - 1) if n > 0 else 0
    f = s - i
    if n == 0:
        return pts[0]
    return pts[i] * (1.0 - f) + pts[i + 1] * f


def _coons(bottom, top, left, right):
    """네 변(각각 균등 파라미터 점 열)으로 만든 Coons 곡면 함수 C(u, v).

    bottom(u) = C(u,0), top(u) = C(u,1), left(v) = C(0,v), right(v) = C(1,v).
    """
    p00, p10 = bottom[0], bottom[-1]
    p01, p11 = top[0], top[-1]

    def c(u, v):
        return ((1 - v) * _side_eval(bottom, u) + v * _side_eval(top, u)
                + (1 - u) * _side_eval(left, v) + u * _side_eval(right, v)
                - ((1 - u) * (1 - v) * p00 + u * (1 - v) * p10
                   + (1 - u) * v * p01 + u * v * p11))
    return c


def smooth_loop(pts, amount, iterations=3):
    """닫힌 보더 루프를 이웃 평균 쪽으로 amount(0..1) 만큼 당긴다."""
    p = np.array(pts, dtype=float)
    if amount <= 0.0:
        return p
    for _ in range(iterations):
        avg = 0.5 * (np.roll(p, 1, axis=0) + np.roll(p, -1, axis=0))
        p = p + amount * (avg - p)
    return p


def grid_patch(border_pts, a, rot, rings=0):
    """닫힌 루프(N 점)를 a x b 그리드로 채우는 패치.

    돌려주는 것: (positions (M,3), faces [슬롯 튜플], movable bool (M,))
    슬롯 0..N-1 = border_pts 그대로(고정).
    """
    pts = np.asarray(border_pts, dtype=float)
    n = len(pts)
    b = n // 2 - a
    if n % 2 or a < 1 or b < 1:
        raise PatchError("Bad grid split ({0} edges, side {1}).".format(n, a))

    # 회전된 루프 인덱스 k(0..N-1) -> 원래 슬롯
    def slot(k):
        return (k + rot) % n

    L = [pts[slot(k)] for k in range(n)]
    bottom = [L[i] for i in range(a + 1)]
    right = [L[a + j] for j in range(b + 1)]
    top = [L[(2 * a + b - i) % n] for i in range(a + 1)]
    left = [L[(n - j) % n] for j in range(b + 1)]
    C = _coons(bottom, top, left, right)

    def uv_of(k):
        if k <= a:
            return (k / float(a), 0.0)
        if k <= a + b:
            return (1.0, (k - a) / float(b))
        if k <= 2 * a + b:
            return (1.0 - (k - a - b) / float(a), 1.0)
        return (0.0, 1.0 - (k - 2 * a - b) / float(b))

    positions = [p for p in pts]
    movable = [False] * n
    faces = []

    du = 1.0 / (a + 2 * rings)
    dv = 1.0 / (b + 2 * rings)

    def shrink(u, v, lv):
        return (lv * du + u * (1 - 2 * lv * du), lv * dv + v * (1 - 2 * lv * dv))

    # 링: ring[l][k] = 회전 인덱스 k 의 슬롯
    ring = [[slot(k) for k in range(n)]]
    for lv in range(1, rings + 1):
        cur = []
        for k in range(n):
            u, v = shrink(*(uv_of(k) + (lv,)))
            positions.append(C(u, v))
            movable.append(True)
            cur.append(len(positions) - 1)
        ring.append(cur)
        prev = ring[lv - 1]
        for k in range(n):
            k1 = (k + 1) % n
            faces.append((prev[k], prev[k1], cur[k1], cur[k]))

    inner = ring[-1]

    # 그리드 G[i][j] - 경계는 안쪽 링, 안은 새 점
    G = [[None] * (b + 1) for _ in range(a + 1)]
    for i in range(a + 1):
        G[i][0] = inner[i]
        G[i][b] = inner[(2 * a + b - i) % n]
    for j in range(b + 1):
        G[a][j] = inner[a + j]
        G[0][j] = inner[(n - j) % n]
    for i in range(1, a):
        for j in range(1, b):
            u, v = shrink(i / float(a), j / float(b), rings)
            positions.append(C(u, v))
            movable.append(True)
            G[i][j] = len(positions) - 1
    for j in range(b):
        for i in range(a):
            faces.append((G[i][j], G[i + 1][j], G[i + 1][j + 1], G[i][j + 1]))

    return np.array(positions, dtype=float), faces, np.array(movable, dtype=bool)


def extrude_patch(loop_pts, a, rows):
    """열린 사슬(loop 인덱스 0..a)에서 rows 줄 뻗는 패치.

    loop_pts 는 사슬이 인덱스 0 에서 시작하도록 회전된 보더 루프 전체(N 점).
    왼쪽 변 = 0 에서 뒤로 rows 칸, 오른쪽 변 = a 에서 앞으로 rows 칸, 위 줄 = 새 점(고정).
    """
    pts = np.asarray(loop_pts, dtype=float)
    n = len(pts)
    k = rows
    if a < 1 or k < 1 or n - a - 2 * k < 1:
        raise PatchError("Too many rows for this hole ({0} edges, chain {1}, rows {2}).".format(
            n, a, k))

    bottom = [pts[i] for i in range(a + 1)]
    right = [pts[a + j] for j in range(k + 1)]
    left = [pts[(n - j) % n] for j in range(k + 1)]
    tl, tr = left[-1], right[-1]
    b0, b1 = bottom[0], bottom[-1]
    base = np.linalg.norm(b1 - b0)
    scale = (np.linalg.norm(tr - tl) / base) if base > 1e-9 else 1.0

    # 위 줄 = 두 위 모서리를 잇는 직선 + 사슬의 굽은 모양(폭 비율만큼)
    top = []
    for i in range(a + 1):
        u = i / float(a)
        dev = bottom[i] - (b0 * (1 - u) + b1 * u)
        top.append(tl * (1 - u) + tr * u + dev * scale)
    top[0], top[-1] = tl, tr
    C = _coons(bottom, top, left, right)

    positions = [p for p in pts]
    movable = [False] * n
    G = [[None] * (k + 1) for _ in range(a + 1)]
    for i in range(a + 1):
        G[i][0] = i
    for j in range(k + 1):
        G[a][j] = a + j
        G[0][j] = (n - j) % n
    for i in range(1, a):
        positions.append(top[i])
        movable.append(False)           # 새 구멍 경계 - 모양을 정한 대로 둔다
        G[i][k] = len(positions) - 1
    for i in range(1, a):
        for j in range(1, k):
            positions.append(C(i / float(a), j / float(k)))
            movable.append(True)
            G[i][j] = len(positions) - 1

    faces = []
    for j in range(k):
        for i in range(a):
            faces.append((G[i][j], G[i + 1][j], G[i + 1][j + 1], G[i][j + 1]))
    return np.array(positions, dtype=float), faces, np.array(movable, dtype=bool)


def relax(positions, faces, movable, iterations, project=None):
    """움직일 수 있는 점만 이웃 평균으로 (Jacobi). project(pos_array, mask) 로 매 반복 투영."""
    p = np.array(positions, dtype=float)
    if iterations <= 0 or not movable.any():
        if project is not None and movable.any():
            p = project(p, movable)
        return p

    src, dst = [], []
    seen = set()
    for f in faces:
        m = len(f)
        for i in range(m):
            x, y = f[i], f[(i + 1) % m]
            key = (min(x, y), max(x, y))
            if key in seen:
                continue
            seen.add(key)
            src += [x, y]
            dst += [y, x]
    src = np.array(src)
    dst = np.array(dst)
    count = np.bincount(dst, minlength=len(p)).astype(float)
    count[count == 0] = 1.0

    for _ in range(iterations):
        acc = np.zeros_like(p)
        np.add.at(acc, dst, p[src])
        avg = acc / count[:, None]
        p[movable] = avg[movable]
        if project is not None:
            p = project(p, movable)
    return p


def _corner_cos(pts, k):
    n = len(pts)
    p = pts[k]
    d0 = pts[(k - 1) % n] - p
    d1 = pts[(k + 1) % n] - p
    l0, l1 = np.linalg.norm(d0), np.linalg.norm(d1)
    if l0 < 1e-12 or l1 < 1e-12:
        return 1.0
    return abs(float(np.dot(d0, d1) / (l0 * l1)))


def _arc(pts, k0, count):
    n = len(pts)
    return sum(np.linalg.norm(pts[(k0 + i + 1) % n] - pts[(k0 + i) % n]) for i in range(count))


def corner_score(pts, a, rot):
    """낮을수록 좋다. 모서리가 직각에 가깝고, 마주 보는 변 길이가 같고, 칸이 정사각형에 가까울수록."""
    pts = np.asarray(pts, dtype=float)
    n = len(pts)
    b = n // 2 - a
    ks = [rot % n, (rot + a) % n, (rot + a + b) % n, (rot + 2 * a + b) % n]
    corner = sum(_corner_cos(pts, k) for k in ks)
    sa1, sb1 = _arc(pts, ks[0], a), _arc(pts, ks[1], b)
    sa2, sb2 = _arc(pts, ks[2], a), _arc(pts, ks[3], b)
    opp = (abs(sa1 - sa2) / max(sa1 + sa2, 1e-12) + abs(sb1 - sb2) / max(sb1 + sb2, 1e-12))
    ca = (sa1 + sa2) / (2.0 * a)
    cb = (sb1 + sb2) / (2.0 * b)
    aspect = abs(math.log(max(ca, 1e-12) / max(cb, 1e-12)))
    return corner + 0.5 * opp + 0.5 * aspect


def best_split(pts, a=None):
    """(rot, a) 중 corner_score 가 가장 낮은 것. a 를 주면 회전만 찾는다."""
    n = len(pts)
    sides = [a] if a else range(1, n // 2)
    best = None
    for aa in sides:
        for r in range(n):
            s = corner_score(pts, aa, r)
            if best is None or s < best[0] - 1e-9:
                best = (s, r, aa)
    return best[1], best[2]


# ======================================================================
# 세션
# ======================================================================

class QuadPatchSession(object):
    """선택에서 시작한 패치 한 건. 미리보기 · 확정 · 취소."""

    def __init__(self, mode, shape, xform, loop, chain_len=0, region=None):
        self.mode = mode
        self.shape = shape
        self.xform = xform
        self.uuid = cmds.ls(shape, uuid=True)[0]
        self.loop = list(loop)            # 정렬된 보더 정점 id (슬롯 0..N-1)
        self.chain_len = chain_len        # Extrude: 사슬 엣지 수 (loop[0..a])
        self.region = list(region or [])  # Faces: 지울 면 id
        topo = _Topo(shape)
        self.fn_points = np.array([topo.point(v) for v in self.loop], dtype=float)
        self.vertex_count = topo.fn.numVertices
        self.face_count = topo.fn.numPolygons
        self.history = _has_history(shape)
        self._preview = None              # (transform MObject, shape MObject)

        # 확정 때 새 면에 줄 셰이딩 그룹(남는 이웃 면 또는 지운 면의 다수결)
        self._sg = None
        # Faces: 원래 면(투영 · UV 샘플용) - 메모리 메시
        self._ref = None
        self._ref_fn = None
        self._ref_isect = None
        self._ref_uvset = None
        self._border_uv = {}
        if mode == MODE_FACE:
            self._build_ref(topo)
        self._sg = self._pick_sg(topo)

    # ---- 생성 ---------------------------------------------------------

    @classmethod
    def from_selection(cls, mode):
        if mode == MODE_FACE:
            return cls._start_face()
        if mode == MODE_EXTRUDE:
            return cls._start_extrude()
        return cls._start_edge()

    @classmethod
    def _start_edge(cls):
        got = _selection(om.MFn.kMeshEdgeComponent)
        if not got:
            raise PatchError("Select border edges of a hole (one edge is enough).")
        shape, xform, ids = got
        topo = _Topo(shape)
        if not all(topo.is_boundary(e) for e in ids):
            raise PatchError("Some selected edges are not border edges - "
                             "Edge Border needs the edges of a hole.")
        loop_edges = topo.boundary_loop_of(ids[0])
        if not set(ids) <= loop_edges:
            raise PatchError("The selected edges belong to more than one hole - pick one hole.")
        loop = _walk(topo, loop_edges, closed=True)
        _check_even(len(loop))
        loop = _orient(topo, loop, lambda a, b: _only_face(topo, a, b))
        return cls(MODE_EDGE, shape, xform, loop)

    @classmethod
    def _start_face(cls):
        got = _selection(om.MFn.kMeshPolygonComponent)
        if not got:
            raise PatchError("Select the faces to replace (one connected patch).")
        shape, xform, faces = got
        topo = _Topo(shape)
        region = set(faces)
        count = {}
        for f in faces:
            for e in topo.face_edges(f):
                count[e] = count.get(e, 0) + 1
        perimeter = set()
        for e in count:
            fs = topo.edge_faces(e)
            inside = [f for f in fs if f in region]
            if len(fs) == 1:
                raise PatchError("The faces touch the mesh border - Faces mode needs faces "
                                 "surrounded by other faces (use Edge Border after deleting).")
            if len(inside) == 1:
                perimeter.add(e)
        if not perimeter:
            raise PatchError("The selection has no outline (closed shell?).")
        _check_connected(topo, faces)
        loop = _walk(topo, perimeter, closed=True)
        _check_even(len(loop))

        def outside(a, b):
            e = _edge_between(topo, a, b)
            for f in topo.edge_faces(e):
                if f not in region:
                    return f
            return None
        loop = _orient(topo, loop, outside)
        return cls(MODE_FACE, shape, xform, loop, region=faces)

    @classmethod
    def _start_extrude(cls):
        got = _selection(om.MFn.kMeshEdgeComponent)
        if not got:
            raise PatchError("Select a run of border edges to extrude from.")
        shape, xform, ids = got
        topo = _Topo(shape)
        if not all(topo.is_boundary(e) for e in ids):
            raise PatchError("Some selected edges are not border edges.")
        loop_edges = topo.boundary_loop_of(ids[0])
        if not set(ids) <= loop_edges:
            raise PatchError("The selected edges belong to more than one hole.")
        if set(ids) == loop_edges:
            raise PatchError("The whole border is selected - Extrude needs part of it "
                             "(use Edge Border to fill the whole hole).")
        chain = _walk(topo, set(ids), closed=False)
        loop = _walk(topo, loop_edges, closed=True)
        n = len(loop)
        a = len(chain) - 1
        # 루프를 사슬 첫 점에서 시작하도록 돌리고, 사슬 방향과 맞춘다
        s = loop.index(chain[0])
        loop = loop[s:] + loop[:s]
        if loop[1] != chain[1]:
            loop = [loop[0]] + loop[:0:-1]
        if loop[a] != chain[-1]:
            raise PatchError("The selected edges are not one run along the border.")
        # 바깥 면 감김과 반대가 되도록 - 뒤집어야 하면 사슬의 반대쪽 끝에서 시작
        f = _only_face(topo, loop[0], loop[1])
        if f is not None and _winding_has(topo.face_verts(f), loop[0], loop[1]):
            loop = loop[a::-1] + loop[:a:-1]
        if n - a - 2 < 1:
            raise PatchError("The hole is too small to extrude into ({0} edges).".format(n))
        return cls(MODE_EXTRUDE, shape, xform, loop, chain_len=a)

    # ---- 정보 ---------------------------------------------------------

    @property
    def edge_count(self):
        return len(self.loop)

    def short_name(self):
        return self.xform.split("|")[-1]

    def max_rows(self):
        return max(1, (len(self.loop) - self.chain_len - 1) // 2)

    def auto_split(self, a=None):
        return best_split(self.fn_points, a)

    # ---- 패치 계산 ----------------------------------------------------

    def build(self, rot=0, side=1, rows=1, rings=0, relax_iter=10, smooth=0.0):
        """(positions, faces, movable, border_positions) - 오브젝트 공간."""
        border = self.fn_points
        if self.mode != MODE_EXTRUDE and smooth > 0.0:
            border = smooth_loop(border, smooth)

        if self.mode == MODE_EXTRUDE:
            pos, faces, mov = extrude_patch(border, self.chain_len, rows)
        else:
            pos, faces, mov = grid_patch(border, side, rot, rings)

        project = self._project if self.mode == MODE_FACE else None
        if project is not None:
            pos = project(pos, mov)
        pos = relax(pos, faces, mov, relax_iter, project)
        return pos, faces, mov, border

    # ---- Faces: 원래 면 -------------------------------------------------

    def _build_ref(self, topo):
        fn = topo.fn
        uvset = fn.currentUVSetName()
        vmap = {}
        pts = om.MPointArray()
        counts, conn = [], []
        us, vs, uvids = [], [], []
        has_uv = True
        for f in self.region:
            vs_f = fn.getPolygonVertices(f)
            counts.append(len(vs_f))
            for k, v in enumerate(vs_f):
                if v not in vmap:
                    vmap[v] = len(vmap)
                    pts.append(fn.getPoint(v, om.MSpace.kObject))
                conn.append(vmap[v])
                if has_uv:
                    try:
                        u, vv = fn.getPolygonUV(f, k, uvset)
                    except Exception:
                        has_uv = False
                        continue
                    uvids.append(len(us))
                    us.append(u)
                    vs.append(vv)
                    if v in self.loop and v not in self._border_uv:
                        self._border_uv[v] = (u, vv)

        data = om.MFnMeshData().create()
        mfn = om.MFnMesh()
        mfn.create(pts, counts, conn, parent=data)
        if has_uv and us:
            mfn.setUVs(us, vs)
            mfn.assignUVs(counts, uvids)
            self._ref_uvset = mfn.currentUVSetName()
        self._ref = data
        self._ref_fn = om.MFnMesh(data)
        self._ref_isect = om.MMeshIntersector()
        self._ref_isect.create(data, om.MMatrix())

    def _project(self, pos, mask):
        out = pos.copy()
        for i in np.nonzero(mask)[0]:
            hit = self._ref_isect.getClosestPoint(om.MPoint(*pos[i]))
            p = hit.point
            out[i] = (p.x, p.y, p.z)
        return out

    def _ref_uv(self, p):
        if self._ref_uvset is None:
            return None
        hit = self._ref_isect.getClosestPoint(om.MPoint(*p))
        q = om.MPoint(hit.point)
        try:
            u, v, _f = self._ref_fn.getUVAtPoint(q, om.MSpace.kObject, self._ref_uvset)
            return (u, v)
        except Exception:
            return None

    # ---- 셰이딩 ---------------------------------------------------------

    def _pick_sg(self, topo):
        """새 면에 줄 셰이딩 그룹 - 지울 면(Faces) 또는 보더 바깥 면들의 다수결."""
        try:
            shaders, idx = topo.fn.getConnectedShaders(0)
        except Exception:
            return None
        if len(shaders) == 0:
            return None
        if self.mode == MODE_FACE:
            faces = self.region
        else:
            faces = set()
            for v in self.loop:
                faces.update(topo.vert_faces(v))
        votes = {}
        for f in faces:
            s = idx[f]
            if s >= 0:
                votes[s] = votes.get(s, 0) + 1
        if not votes:
            return None
        best = max(votes, key=votes.get)
        return om.MFnDependencyNode(shaders[best]).name()

    # ---- 미리보기 -----------------------------------------------------

    def preview(self, **params):
        pos, faces, _mov, _border = self.build(**params)
        world = _dag(self.xform).inclusiveMatrix()
        pts = om.MPointArray([om.MPoint(*p) for p in pos])
        counts = [len(f) for f in faces]
        conn = [s for f in faces for s in f]

        if self._preview is not None and not _alive(self._preview[0]):
            self._preview = None
        if self._preview is None:
            self._preview = _make_preview(pts, counts, conn)
        else:
            om.MFnMesh(self._preview[1]).createInPlace(pts, counts, conn)
        om.MFnTransform(self._preview[0]).setTransformation(om.MTransformationMatrix(world))
        return len(faces), len(pos) - len(self.loop)

    def discard(self):
        if self._preview is not None and _alive(self._preview[0]):
            mod = om.MDagModifier()
            mod.deleteNode(self._preview[0])
            mod.doIt()
        self._preview = None

    # ---- 확정 ---------------------------------------------------------

    def _check_unchanged(self):
        if not cmds.objExists(self.shape) or cmds.ls(self.shape, uuid=True)[0] != self.uuid:
            raise PatchError("The mesh is gone or renamed - start again.")
        fn = _fn(self.shape)
        if fn.numVertices != self.vertex_count or fn.numPolygons != self.face_count:
            raise PatchError("The mesh changed since Start - start again.")
        for v, p in zip(self.loop, self.fn_points):
            q = fn.getPoint(v, om.MSpace.kObject)
            if abs(q.x - p[0]) + abs(q.y - p[1]) + abs(q.z - p[2]) > _EPS:
                raise PatchError("The border moved since Start - start again.")

    def commit(self, soft_edges=True, uvs=True, progress=None, **params):
        """원본 메시에 패치를 붙인다 (한 번의 undo). 결과 요약 dict."""
        self._check_unchanged()
        pos, faces, _mov, border = self.build(**params)
        self.discard()
        t0 = time.time()

        cmds.undoInfo(openChunk=True, chunkName="QuadPatch")
        touched = False
        ok = False
        try:
            touched = True
            ids = list(self.loop)

            # 1) Faces: 면을 지우고 보더 정점 id 를 새 번호로
            if self.mode == MODE_FACE:
                ids = self._delete_region()

            # 2) Smooth Border: 기존 보더 정점을 옮긴다
            if self.mode != MODE_EXTRUDE and params.get("smooth", 0.0) > 0.0:
                for vid, p in zip(ids, border):
                    cmds.xform("{0}.vtx[{1}]".format(self.shape, vid),
                               objectSpace=True, translation=tuple(p))

            # 3) 면 붙이기
            new_faces = self._append(ids, pos, faces, progress)

            # 4) 셰이딩 · 엣지 · UV
            comps = ["{0}.f[{1}:{2}]".format(self.shape, new_faces[0], new_faces[-1])]
            self._assign_sg(new_faces)
            if soft_edges:
                edges = cmds.polyListComponentConversion(comps, te=True)
                cmds.polySoftEdge(edges, angle=180, ch=True)
            if uvs:
                self._make_uvs(comps, ids, pos)

            if not self.history:
                cmds.delete(self.shape, ch=True)
            ok = True
        finally:
            cmds.undoInfo(closeChunk=True)
            if touched and not ok:
                try:
                    cmds.undo()
                except Exception:
                    pass

        return {
            "faces": len(faces),
            "new_vertices": len(pos) - len(self.loop),
            "seconds": time.time() - t0,
            "history_kept": self.history,
        }

    def _delete_region(self):
        topo = _Topo(self.shape)
        region = set(self.region)
        gone = set()
        for f in self.region:
            for v in topo.face_verts(f):
                if v in gone:
                    continue
                if all(ff in region for ff in topo.vert_faces(v)):
                    gone.add(v)
        cmds.delete(["{0}.f[{1}]".format(self.shape, f) for f in self.region])
        gone_sorted = sorted(gone)

        import bisect
        ids = [v - bisect.bisect_left(gone_sorted, v) for v in self.loop]
        fn = _fn(self.shape)
        for vid, p in zip(ids, self.fn_points):
            q = fn.getPoint(vid, om.MSpace.kObject)
            if abs(q.x - p[0]) + abs(q.y - p[1]) + abs(q.z - p[2]) > _EPS:
                raise PatchError("Lost track of the border after deleting the faces.")
        return ids

    def _append(self, border_ids, pos, faces, progress=None):
        """패치 면을 하나씩 polyAppendVertex. 새 점은 만들어진 뒤 위치로 id 를 찾는다."""
        n = len(self.loop)
        slot_vid = {k: border_ids[k] for k in range(n)}
        fn = _fn(self.shape)
        first_face = fn.numPolygons
        total = len(faces)

        for fi, face in enumerate(faces):
            args = []
            fresh = []
            for s in face:
                if s in slot_vid:
                    args.append(int(slot_vid[s]))
                else:
                    args.append(tuple(float(x) for x in pos[s]))
                    fresh.append(s)
            nv = _fn(self.shape).numVertices
            cmds.polyAppendVertex(self.shape, append=args, ch=True)
            if fresh:
                fn = _fn(self.shape)
                made = list(range(nv, fn.numVertices))
                if len(made) != len(fresh):
                    raise PatchError("polyAppendVertex made {0} points, expected {1}.".format(
                        len(made), len(fresh)))
                for s in fresh:
                    best, bd = None, None
                    for vid in made:
                        q = fn.getPoint(vid, om.MSpace.kObject)
                        d = (q.x - pos[s][0]) ** 2 + (q.y - pos[s][1]) ** 2 + (q.z - pos[s][2]) ** 2
                        if bd is None or d < bd:
                            best, bd = vid, d
                    slot_vid[s] = best
                    made.remove(best)
            if progress is not None:
                progress(fi + 1, total)

        last = _fn(self.shape).numPolygons - 1
        if last - first_face + 1 != total:
            raise PatchError("Expected {0} new faces, got {1}.".format(
                total, last - first_face + 1))
        self._slot_vid = slot_vid
        return list(range(first_face, last + 1))

    def _assign_sg(self, new_faces):
        if not self._sg or not cmds.objExists(self._sg):
            return
        fn = _fn(self.shape)
        try:
            _shaders, idx = fn.getConnectedShaders(0)
        except Exception:
            return
        missing = [f for f in new_faces if idx[f] < 0]
        if missing:
            cmds.sets(["{0}.f[{1}]".format(self.shape, f) for f in missing],
                      e=True, forceElement=self._sg)

    def _make_uvs(self, comps, border_ids, pos):
        """새 면에 UV. Faces 는 원래 면의 UV 를, 나머지는 최적 평면 투영."""
        cmds.polyProjection(comps, type="Planar", md="b", ch=True)
        if self.mode != MODE_FACE or self._ref_uvset is None:
            return

        fn = _fn(self.shape)
        uvset = fn.currentUVSetName()
        vid_slot = dict((v, s) for s, v in self._slot_vid.items())
        n = len(self.loop)
        f0 = int(comps[0].split("[")[1].split(":")[0])
        f1 = int(comps[0].split(":")[1].rstrip("]"))
        target = {}
        for f in range(f0, f1 + 1):
            for k, v in enumerate(fn.getPolygonVertices(f)):
                try:
                    uvid = fn.getPolygonUVid(f, k, uvset)
                except Exception:
                    continue
                s = vid_slot.get(v)
                if s is None:
                    continue
                if s < n:
                    uv = self._border_uv.get(self.loop[s])
                else:
                    uv = self._ref_uv(pos[s])
                if uv is not None:
                    target[uvid] = uv
        for uvid, (u, v) in target.items():
            cmds.polyEditUV("{0}.map[{1}]".format(self.shape, uvid), u=u, v=v, relative=False)
        # 보더 UV 를 바깥 면 UV 와 꿰맨다(같은 정점 + 같은 자리일 때만 합쳐진다)
        border_uvs = cmds.polyListComponentConversion(
            ["{0}.vtx[{1}]".format(self.shape, v) for v in border_ids], tuv=True)
        cmds.polyMergeUV(border_uvs, distance=1e-4, ch=True)


# ======================================================================
# 도우미
# ======================================================================

def _check_even(n):
    if n < 4:
        raise PatchError("The hole has {0} edges - needs at least 4.".format(n))
    if n % 2:
        raise PatchError("The hole has {0} edges (odd). Quads need an even count - "
                         "split or collapse one border edge first.".format(n))


def _check_connected(topo, faces):
    region = set(faces)
    seen = set([faces[0]])
    stack = [faces[0]]
    while stack:
        f = stack.pop()
        for e in topo.face_edges(f):
            for nf in topo.edge_faces(e):
                if nf in region and nf not in seen:
                    seen.add(nf)
                    stack.append(nf)
    if len(seen) != len(region):
        raise PatchError("The selected faces are not one connected patch.")


def _only_face(topo, a, b):
    e = _edge_between(topo, a, b)
    if e is None:
        return None
    fs = topo.edge_faces(e)
    return fs[0] if fs else None


def _alive(mobj):
    try:
        handle = om.MObjectHandle(mobj)
        return handle.isValid() and handle.isAlive()
    except Exception:
        return False


def _make_preview(pts, counts, conn):
    """API 로 만든 와이어프레임 미리보기 (undo 큐에 남지 않는다)."""
    for old in cmds.ls(PREVIEW_NAME, type="transform") or []:
        try:
            mod = om.MDagModifier()
            sel = om.MSelectionList()
            sel.add(old)
            mod.deleteNode(sel.getDependNode(0))
            mod.doIt()
        except Exception:
            pass

    mod = om.MDagModifier()
    xform = mod.createNode("transform")
    mod.renameNode(xform, PREVIEW_NAME)
    mod.doIt()
    shape = om.MFnMesh().create(pts, counts, conn, parent=xform)
    dep = om.MFnDependencyNode(shape)
    dep.setName(PREVIEW_NAME + "Shape")

    node = om.MFnDependencyNode(xform)
    node.findPlug("overrideEnabled", False).setBool(True)
    node.findPlug("overrideShading", False).setBool(False)
    node.findPlug("overrideRGBColors", False).setBool(True)
    rgb = node.findPlug("overrideColorRGB", False)
    for i, c in enumerate(PREVIEW_COLOR):
        rgb.child(i).setFloat(c)
    return xform, shape
