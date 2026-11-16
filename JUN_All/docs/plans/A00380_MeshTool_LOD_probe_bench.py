# -*- coding: utf-8 -*-
"""polyReduce vs numpy vertex-clustering(QEM 대표점) 속도 비교 프로토타입."""
import time
import numpy as np
import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds
import maya.api.OpenMaya as om


def make_mesh(div):
    t = cmds.polySphere(sx=div, sy=div, ch=False)[0]
    return t


def read_mesh(shape):
    sel = om.MSelectionList(); sel.add(shape)
    fn = om.MFnMesh(sel.getDagPath(0))
    P = np.array(fn.getPoints(om.MSpace.kObject), dtype=np.float64)[:, :3]
    counts, tri_v = fn.getTriangles()
    T = np.array(tri_v, dtype=np.int64).reshape(-1, 3)
    return P, T


def cluster_qem(P, T, target_tris):
    """그리드 클러스터링 + 셀마다 QEM 최소점. target 삼각형 수에 맞게 셀 크기를 이분 탐색."""
    v0, v1, v2 = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    n = np.cross(v1 - v0, v2 - v0)
    area2 = np.linalg.norm(n, axis=1)
    nn = n / np.maximum(area2, 1e-20)[:, None]
    d = -np.einsum('ij,ij->i', nn, v0)
    plane = np.concatenate([nn, d[:, None]], 1)              # (F,4)
    Kf = np.einsum('fi,fj->fij', plane, plane) * area2[:, None, None]  # 면적 가중
    bbmin, bbmax = P.min(0), P.max(0)
    ext = (bbmax - bbmin).max()

    def run(res):
        cell = ext / res
        g = np.floor((P - bbmin) / cell).astype(np.int64)
        key = (g[:, 0] * (res + 2) + g[:, 1]) * (res + 2) + g[:, 2]
        uniq, cid = np.unique(key, return_inverse=True)
        tc = cid[T]
        keep = (tc[:, 0] != tc[:, 1]) & (tc[:, 1] != tc[:, 2]) & (tc[:, 0] != tc[:, 2])
        return uniq.size, cid, tc[keep], keep

    lo, hi = 2, 2048
    best = None
    for _ in range(14):
        mid = (lo + hi) // 2
        nc, cid, tri, keep = run(mid)
        if len(tri) > target_tris:
            hi = mid
        else:
            lo = mid; best = (nc, cid, tri, keep)
        if hi - lo <= 1:
            break
    if best is None:
        best = run(lo)
    nc, cid, tri, keep = best
    # 버텍스 Q = 이웃 면 Q 합 → 셀 Q = 버텍스 Q 합
    Q = np.zeros((nc, 4, 4))
    for k in range(3):
        np.add.at(Q, cid[T[:, k]], Kf)
    A = Q[:, :3, :3] + np.eye(3) * 1e-9 * ext * ext
    b = -Q[:, :3, 3]
    mean = np.zeros((nc, 3)); cnt = np.zeros(nc)
    np.add.at(mean, cid, P); np.add.at(cnt, cid, 1)
    mean /= cnt[:, None]
    # 조건수 나쁜 셀(평면)은 평균점 + 정규화 항으로 안정
    A2 = A + np.eye(3) * (1e-3 * np.trace(A, axis1=1, axis2=2)[:, None, None] / 3)
    b2 = b + (1e-3 * np.trace(A, axis1=1, axis2=2) / 3)[:, None] * mean
    X = np.linalg.solve(A2, b2[..., None])[..., 0]
    # 중복 삼각형 제거
    s = np.sort(tri, 1)
    _, ui = np.unique(s, axis=0, return_index=True)
    tri = tri[np.sort(ui)]
    used = np.unique(tri)
    remap = -np.ones(nc, np.int64); remap[used] = np.arange(used.size)
    return X[used], remap[tri]


def build(V, F, name):
    pts = om.MPointArray([om.MPoint(*p) for p in V])  # 느림 주의 - 측정 분리
    fn = om.MFnMesh()
    obj = fn.create(pts, [3] * len(F), F.ravel().tolist())
    return obj


for div in (200, 400):
    src = make_mesh(div)
    shape = cmds.listRelatives(src, s=True)[0]
    nf = cmds.polyEvaluate(src, t=True)
    print('=== src tris', nf)
    for ratio in (0.5, 0.25, 0.125, 0.0625, 0.03):
        dup = cmds.duplicate(src)[0]
        t0 = time.perf_counter()
        cmds.polyReduce(dup, ver=1, trm=0, p=(1 - ratio) * 100, kqw=0, uwt=0, cwt=0, ch=False)
        t1 = time.perf_counter()
        r_tris = cmds.polyEvaluate(dup, t=True)
        cmds.delete(dup)

        t2 = time.perf_counter()
        P, T = read_mesh(shape)
        t3 = time.perf_counter()
        V, F = cluster_qem(P, T, int(nf * ratio))
        t4 = time.perf_counter()
        build(V, F, 'lod')
        t5 = time.perf_counter()
        print('ratio %.3f  polyReduce %.3fs (%d tris) | cluster read %.3f algo %.3f build %.3f = %.3fs (%d tris)' % (
            ratio, t1 - t0, r_tris, t3 - t2, t4 - t3, t5 - t4, t5 - t2, len(F)))
    cmds.file(new=True, force=True)

maya.standalone.uninitialize()
