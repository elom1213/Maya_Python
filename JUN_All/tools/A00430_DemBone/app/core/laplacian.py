# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 웨이트 스무딩용 라플라시안 (numpy 전용, Maya 비의존)
#
# ref/include/DemBones/DemBones.h 의 computeSmoothSolver()/compute_ws() 를 옮긴 것.
#
# 원본의 영리한 부분: 엣지 가중치가 **기하 거리가 아니라 "시퀀스 내내 이 엣지 길이가
# 얼마나 안 변했나"** 다 (DemBones.h:812).
#
#     val = 1 / ( rms_k( |v_i(k) - v_j(k)| - |u_i - u_j| ) + eps )
#
# 잘 늘어나는 엣지(= 서로 다른 본에 속할 법한 경계)는 약하게, 뻣뻣한 엣지(= 같이 움직이는
# 곳)는 강하게 묶인다. 그래서 스무딩이 본 경계를 뭉개지 않는다.
#
# **원본과 다른 점 (의도적)**: 원본은 (I + step*L) ws = w 를 Eigen SparseLU 로 직접 푼다.
# Maya 에 scipy 가 없어(2024 mayapy 확인) 같은 계를 **자코비 반복**으로 푼다.
# 행 정규화된 라플라시안은 L = I - P (P = 행 합이 1인 이웃 평균 행렬) 이므로
#
#     (I + step*(I - P)) ws = w   ->   ws <- (w + step * P @ ws) / (1 + step)
#
# 이 반복은 수렴 인자가 step/(1+step) < 1 이라 **항상 수렴한다**. 반복 20회면
# step=1 기준 오차가 2^-20 수준이라 실질적으로 직접 해와 같다.

import numpy as np


def build_edges(faces):
    """폴리곤 목록에서 중복 없는 엣지 배열 (nE, 2) 을 만든다.

    Args:
        faces: 폴리곤별 버텍스 인덱스 리스트의 리스트. (DemBones 의 fv)
    """
    pairs = []
    for verts in faces:
        n = len(verts)
        if n < 2:
            continue
        for g in range(n):
            i = verts[g]
            j = verts[(g + 1) % n]
            if i == j:
                continue
            pairs.append((i, j) if i < j else (j, i))
    if not pairs:
        return np.zeros((0, 2), dtype=np.int64)
    arr = np.asarray(pairs, dtype=np.int64)
    return np.unique(arr, axis=0)


def edge_weights(U, V, edges, eps_scale=1e-15):
    """시퀀스 기반 엣지 가중치 (nE,). 원본 DemBones.h:807~814 와 같은 식.

    Args:
        U: (nV, 3) rest 포즈.
        V: (nF, nV, 3) 애니메이션 시퀀스.
        edges: (nE, 2).
    """
    if edges.shape[0] == 0:
        return np.zeros(0)

    i = edges[:, 0]
    j = edges[:, 1]

    du = np.linalg.norm(U[i] - U[j], axis=1)                    # (nE,)
    dv = np.linalg.norm(V[:, i, :] - V[:, j, :], axis=2)        # (nF, nE)

    # eps 는 rest 엣지 길이 총합 기준(원본 :786) - 스케일 독립성을 준다.
    eps_dis = du.sum() * eps_scale
    val = np.sqrt(((dv - du[None, :]) ** 2).mean(axis=0))
    return 1.0 / (val + eps_dis + 1e-30)


class Neighborhood:
    """버텍스 인접 관계를 CSR 로 들고 있다가 `of(i)` 로 이웃을 준다.

    클러스터 초기화(`solver_init`)가 **메시 연결성을 따라 라벨을 퍼뜨리기** 때문에 필요하다.
    원본은 라플라시안 희소행렬의 열을 순회해 같은 일을 한다(DemBones.h:481, :589).
    """

    def __init__(self, n_v, edges):
        self.n_v = int(n_v)
        if edges.shape[0] == 0:
            self.indptr = np.zeros(self.n_v + 1, dtype=np.int64)
            self.indices = np.zeros(0, dtype=np.int64)
            return

        rows = np.concatenate([edges[:, 0], edges[:, 1]])
        cols = np.concatenate([edges[:, 1], edges[:, 0]])
        order = np.argsort(rows, kind="stable")
        rows = rows[order]
        self.indices = cols[order]

        counts = np.bincount(rows, minlength=self.n_v)
        self.indptr = np.zeros(self.n_v + 1, dtype=np.int64)
        np.cumsum(counts, out=self.indptr[1:])

    def of(self, i):
        return self.indices[self.indptr[i]:self.indptr[i + 1]]

    def __len__(self):
        return self.n_v


def neighborhood_from_faces(n_v, faces):
    """폴리곤 목록에서 바로 Neighborhood 를 만든다."""
    return Neighborhood(n_v, build_edges(faces))


class WeightSmoother:
    """행 정규화 이웃 평균 P 를 들고 있다가 웨이트를 스무딩한다.

    P 는 희소하지만 scipy 가 없으므로 (row, col, val) 배열 + bincount 로 곱한다.
    """

    def __init__(self, n_v, edges, weights):
        self.n_v = int(n_v)

        if edges.shape[0] == 0:
            self.rows = np.zeros(0, dtype=np.int64)
            self.cols = np.zeros(0, dtype=np.int64)
            self.vals = np.zeros(0)
            return

        # 양방향으로 펼친다.
        rows = np.concatenate([edges[:, 0], edges[:, 1]])
        cols = np.concatenate([edges[:, 1], edges[:, 0]])
        vals = np.concatenate([weights, weights])

        # 행 합으로 나눠 P 의 각 행 합을 1 로 만든다(= 가중 이웃 평균).
        deg = np.bincount(rows, weights=vals, minlength=self.n_v)
        deg[deg == 0.0] = 1.0
        self.rows = rows
        self.cols = cols
        self.vals = vals / deg[rows]

    def _neighbor_mean(self, W):
        """P @ W. W 는 (nV, nB)."""
        out = np.zeros_like(W)
        if self.rows.size == 0:
            return out
        for b in range(W.shape[1]):
            out[:, b] = np.bincount(
                self.rows,
                weights=self.vals * W[self.cols, b],
                minlength=self.n_v)
        return out

    def smooth(self, W, step=1.0, iters=20):
        """(I + step*(I-P)) ws = W 를 자코비 반복으로 푼다. W: (nV, nB)."""
        if self.rows.size == 0 or step <= 0.0 or iters <= 0:
            return W.copy()
        ws = W.copy()
        inv = 1.0 / (1.0 + step)
        for _ in range(int(iters)):
            ws = (W + step * self._neighbor_mean(ws)) * inv
        return ws

    def normalize(self, ws, n_b):
        """음수를 자르고 행 합을 1 로. 합이 너무 작으면 균등분배(원본 :855~857)."""
        ws = np.maximum(ws, 0.0)
        s = ws.sum(axis=1)
        bad = s < 0.1
        s[bad] = 1.0
        ws = ws / s[:, None]
        if bad.any():
            ws[bad] = 1.0 / float(n_b)
        return ws
