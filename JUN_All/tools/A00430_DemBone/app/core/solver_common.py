# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 솔버 공용 정의 (numpy 전용, Maya 비의존)
#
# ============================================================================
# 규약 (이 툴 전체에서 지킨다 - 여기서 틀리면 전부 틀린다)
# ============================================================================
#
# **행렬은 전부 Maya 규약(행벡터)**이다: 점은 행, 변환은 `p @ M`, translate 는 마지막 **행**.
# 원본 Dem Bones 는 Eigen 열벡터 규약(`M @ p`, translate 는 마지막 **열**)이라 전치 관계다.
# 마야에서 읽은 값을 그대로 쓰는 쪽이 버그가 적어서 이쪽으로 통일했다.
#
#   U : (nV, 3)        rest 포즈 버텍스 (월드)
#   V : (nF, nV, 3)    프레임별 목표 위치 (알렘빅 캐시 등, 월드)
#   M : (nF, nB, 4, 4) 본의 **상대(relative)** 변환. `u_h @ M[k,j]` = 본 j 만으로 변환한 위치
#   W : (nV, nB)       스키닝 웨이트 (행 합 = 1)
#
# M 의 정의는 원본과 같다 (ref/src/command/FbxReader.cpp:197):
#     M = (프레임 k 의 조인트 월드행렬) x (바인드 월드행렬)^-1
# 마야 skinCluster 로는 `bindPreMatrix[j] @ matrix[j]` — 행벡터 규약이라 이 순서다.
#
# LBS 모델:   V[k,i] ~= sum_j W[i,j] * (U_h[i] @ M[k,j])[:3]
#
# ============================================================================
# 출처
#   Dem Bones, Copyright (c) 2019 Electronic Arts. BSD 3-Clause (ref/LICENSE.md)
#   Le & Deng, "Smooth Skinning Decomposition with Rigid Bones", ACM TOG 31(6), 2012.
#   Le & Deng, "Robust and Accurate Skeletal Rigging from Mesh Sequences", ACM TOG 33(4), 2014.

import numpy as np


class SolveCancelled(Exception):
    """사용자가 진행 중인 솔브를 취소했다."""


class Progress(object):
    """진행률 콜백 래퍼.

    콜백은 `callback(fraction, message)` 로 불리며 **False 를 반환하면 취소**로 본다.
    콜백이 없으면 아무것도 하지 않는다.
    """

    def __init__(self, callback=None, base=0.0, span=1.0):
        self.callback = callback
        self.base = float(base)
        self.span = float(span)

    def sub(self, base, span):
        """전체 진행률의 [base, base+span] 구간을 담당하는 하위 진행률."""
        return Progress(self.callback,
                        self.base + self.span * base,
                        self.span * span)

    def tick(self, fraction, message=""):
        if self.callback is None:
            return
        value = self.base + self.span * max(0.0, min(1.0, float(fraction)))
        if self.callback(value, message) is False:
            raise SolveCancelled(message or "cancelled")


def homogeneous(U):
    """(nV, 3) -> (nV, 4) 동차좌표 (마지막 열 = 1)."""
    U = np.asarray(U, dtype=float)
    return np.concatenate([U, np.ones((U.shape[0], 1))], axis=1)


def model_size(U):
    """모델 크기 = 무게중심까지의 RMS 거리 (원본 DemBones.h:187 과 같은 정의).

    오차를 "모델 크기의 몇 %" 로 말하기 위한 스케일 기준이다.
    """
    U = np.asarray(U, dtype=float)
    return float(np.sqrt(((U - U.mean(axis=0)) ** 2).sum() / max(1, U.shape[0])))


def bone_errors(U, V, M, chunk=4000, progress=None):
    """E[i,j] = sum_k |u_h[i] @ M[k,j] - V[k,i]|^2  ->  (nV, nB).

    "버텍스 i 를 본 j 하나에만 강체로 붙였을 때 얼마나 틀리나".
    원본의 errorVtxBone (DemBones.h:426) 과 같다. 후보 본 선별과 초기 라벨링에 쓴다.

    비용이 O(nV * nB * nF) 라 전체에서 제일 무거운 단계다(실측: 20k/40/100 에서 6초).
    """
    V = np.asarray(V, dtype=float)
    n_f, n_v, _ = V.shape
    n_b = M.shape[1]
    Uh = homogeneous(U)
    M3 = M[:, :, :, :3]                                       # (nF, nB, 4, 3)

    E = np.empty((n_v, n_b))
    steps = max(1, int(np.ceil(n_v / float(chunk))))
    for s in range(steps):
        lo = s * chunk
        hi = min(n_v, lo + chunk)
        uh = Uh[lo:hi]                                        # (c, 4)
        vv = V[:, lo:hi, :]                                   # (nF, c, 3)
        for j in range(n_b):
            pred = np.einsum('ia,kab->kib', uh, M3[:, j], optimize=True)
            E[lo:hi, j] = ((pred - vv) ** 2).sum(axis=(0, 2))
        if progress is not None:
            progress.tick((s + 1) / float(steps), "bone errors")
    return E


def compute_mTm(M):
    """mTm[j,l] = sum_k M3[k,j] @ M3[k,l].T   ->  (nB, nB, 4, 4).

    프레임 루프를 여기서 한 번만 돌아 두면, 이후 버텍스별 정규방정식은
    프레임 수와 무관하게 4x4 이차형식 하나로 끝난다 (원본 DemBones.h:728).
    """
    M3 = np.asarray(M)[:, :, :, :3]                           # (nF, nB, 4, 3)
    return np.einsum('kjab,klcb->jlac', M3, M3, optimize=True)


def reconstruct(U, M, W, chunk=4000):
    """LBS 결과 (nF, nV, 3)."""
    Uh = homogeneous(U)
    M3 = np.asarray(M)[:, :, :, :3]
    n_f = M.shape[0]
    n_v = Uh.shape[0]
    out = np.zeros((n_f, n_v, 3))
    for lo in range(0, n_v, chunk):
        hi = min(n_v, lo + chunk)
        uh = Uh[lo:hi]
        w = W[lo:hi]
        for j in range(M.shape[1]):
            col = w[:, j]
            hit = np.nonzero(col)[0]
            if hit.size == 0:
                continue
            pred = np.einsum('ia,kab->kib', uh[hit], M3[:, j], optimize=True)
            out[:, lo + hit, :] += col[hit][None, :, None] * pred
    return out


def rmse(U, V, M, W, chunk=4000):
    """재구성 RMSE. 원본 DemBones::rmse (DemBones.h:356) 와 같은 정의."""
    V = np.asarray(V, dtype=float)
    n_f, n_v, _ = V.shape
    Uh = homogeneous(U)
    M3 = np.asarray(M)[:, :, :, :3]

    total = 0.0
    for lo in range(0, n_v, chunk):
        hi = min(n_v, lo + chunk)
        uh = Uh[lo:hi]
        acc = np.zeros((n_f, hi - lo, 3))
        w = W[lo:hi]
        for j in range(M.shape[1]):
            col = w[:, j]
            hit = np.nonzero(col)[0]
            if hit.size == 0:
                continue
            pred = np.einsum('ia,kab->kib', uh[hit], M3[:, j], optimize=True)
            acc[:, hit, :] += col[hit][None, :, None] * pred
        total += ((acc - V[:, lo:hi, :]) ** 2).sum()
    return float(np.sqrt(total / max(1, n_f) / max(1, n_v)))
