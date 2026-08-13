# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 본 변환 솔브 (numpy 전용, Maya 비의존)
#
# ref/include/DemBones/DemBones.h 의 computeTranformations() (:237) + qpT2m() (:411) 이식.
# 커맨드라인으로 치면 `DemBones --nWeightsIters=0` — **캐시 + 웨이트 -> 본 애님**.
#
# 프레임 k, 본 j 의 최적 변환은 닫힌 형태로 나온다. 정규방정식을 세우면
#
#     sum_l  uuT[j,l] @ M3[k,l]  =  vuT[k,j]
#     uuT[j,l] = sum_i W[i,j] W[i,l] u_h[i]^T u_h[i]     (4x4)
#     vuT[k,j] = sum_i W[i,j] u_h[i]^T V[k,i]            (4x3)
#
# 이고, 본 j 만 남기면
#
#     uuT[j,j] @ M3[k,j] = vuT[k,j] - sum_{l!=j} uuT[j,l] @ M3[k,l]  =:  Q
#
# 여기서 M3 를 그냥 풀면 스케일·전단이 섞인다. 원본은 그러지 않고 Q 에서 **최적 강체**를
# 뽑는다(qpT2m) — 가중 Kabsch/Procrustes:
#
#     H = Q[:3] - outer(mass_u, centroid_y)     (3x3 교차공분산)
#     H = A S B^T (SVD)  ->  R = A diag(1,1,det(A B^T)) B^T
#     t = centroid_y - centroid_u @ R
#
# diag 의 det 항이 **반사(거울)를 막는다**. 그래서 결과가 항상 회전+이동 = rigid bones.
#
# 본끼리 웨이트를 공유하면 서로 영향을 주므로(uuT 의 비대각 항) 본을 순회하며
# 갱신을 반복한다(가우스-자이델, 원본과 동일하게 nTransIters 회).
#
# 출처: Dem Bones (c) 2019 Electronic Arts, BSD 3-Clause. 논문은 solver_common.py 헤더 참고.

import numpy as np

from .solver_common import Progress, homogeneous


def _outer_products(Uh):
    """(nV, 4, 4) = u_h^T u_h."""
    return np.einsum('ia,ib->iab', Uh, Uh, optimize=True)


def compute_uuT(W, Uh):
    """uuT[j,l] = sum_i W[i,j] W[i,l] u_h[i]^T u_h[i]  ->  (nB, nB, 4, 4).

    16개 성분마다 (nB,nV)x(nV,nB) 행렬곱 한 번으로 접는다 - 파이썬 루프 없이 BLAS 로 간다.
    """
    n_b = W.shape[1]
    outer = _outer_products(Uh)                               # (nV, 4, 4)
    uuT = np.empty((n_b, n_b, 4, 4))
    for a in range(4):
        for b in range(4):
            uuT[:, :, a, b] = W.T @ (W * outer[:, a, b][:, None])
    return uuT


def compute_vuT(W, Uh, V, trans_affine=0.0, trans_affine_norm=4.0):
    """vuT[k,j] = sum_i W[i,j] u_h[i]^T v_h[k,i]  ->  (nF, nB, 4, 4).

    **4x4 로 들고 있는 게 중요하다.** 마지막 열(동차 성분)이 이 본이 실제로 쥔 웨이트 질량
    `sum_i W[i,j]` 을 담고 있고, 무게중심을 그 질량으로 나눠 구하기 때문이다(원본 qpT2m 이
    `qpT(3,3)` 으로 나누는 것과 같다). 질량을 다른 행렬에서 가져오면 아래 affinity 처럼
    질량이 달라지는 경우에 무게중심이 어긋나 결과가 무너진다.

    trans_affine > 0 이면 **본 이동 친화(translations affinity)** 소프트 제약을 섞는다
    (원본 DemBones.h:656~660). 웨이트를 p 제곱해 가중한 공분산을 질량 비율로 맞춰 더하는
    것이라, 웨이트가 높은 **중심부**가 본의 변환을 더 강하게 결정하게 된다.
    """
    n_f = V.shape[0]
    n_b = W.shape[1]

    def _accumulate(weights):
        out = np.empty((n_f, n_b, 4, 4))
        for a in range(4):
            A = weights * Uh[:, a][:, None]                   # (nV, nB)
            # (nF, nV, 3) x (nV, nB) -> (nF, 3, nB)
            out[:, :, a, :3] = np.tensordot(V, A, axes=([1], [0])).transpose(0, 2, 1)
            # 동차 성분: v_h 의 마지막 원소가 1 이라 프레임과 무관하다.
            out[:, :, a, 3] = A.sum(axis=0)[None, :]
        return out

    vuT = _accumulate(W)
    if trans_affine and trans_affine > 0.0:
        Wp = np.power(np.maximum(W, 0.0), trans_affine_norm)
        vuTp = _accumulate(Wp)
        mass = W.sum(axis=0)                                  # (nB,)
        mass_p = Wp.sum(axis=0)
        scale = np.where(mass_p > 0.0, trans_affine * mass / np.maximum(mass_p, 1e-30), 0.0)
        vuT += scale[None, :, None, None] * vuTp
    return vuT


def rigid_from_normal(Q):
    """4x4 공분산 Q 에서 최적 강체 변환 M3 (4,3) 를 뽑는다.

    Q = sum_i w_i * u_h[i]^T v_h[i]  (커플링 항을 뺀 뒤) 형태이고, 마지막 행/열이
    무게중심을, (3,3) 이 질량을 담고 있다. 원본 qpT2m (DemBones.h:411) 과 같은 계산.
    못 구하면 None.
    """
    mass = Q[3, 3]
    if mass <= 1e-20:
        return None

    centroid_u = Q[:3, 3] / mass                              # (3,) u 쪽 무게중심
    centroid_y = Q[3, :3] / mass                              # (3,) 목표 쪽 무게중심

    H = Q[:3, :3] - np.outer(Q[:3, 3], centroid_y)            # (3,3) 교차공분산

    try:
        A, _, Bt = np.linalg.svd(H)
    except np.linalg.LinAlgError:
        return None

    R = A @ Bt
    if np.linalg.det(R) < 0.0:
        # 반사가 나왔다 - 마지막 특이방향을 뒤집어 회전으로 되돌린다.
        A = A.copy()
        A[:, 2] *= -1.0
        R = A @ Bt

    t = centroid_y - centroid_u @ R

    M3 = np.empty((4, 3))
    M3[:3, :] = R
    M3[3, :] = t
    return M3


def solve_transforms(U, V, W, M_init=None, n_iters=5, trans_affine=10.0,
                     trans_affine_norm=4.0, lock_bones=None, progress=None):
    """웨이트를 고정하고 본의 상대 변환 M 을 푼다.

    Args:
        U: (nV, 3) rest 포즈.
        V: (nF, nV, 3) 목표 시퀀스.
        W: (nV, nB) 스키닝 웨이트.
        M_init: (nF, nB, 4, 4) 시작값. 없으면 단위행렬.
        n_iters: 본 순회 반복 횟수 (원본 nTransIters).
        trans_affine / trans_affine_norm: 이동 친화 소프트 제약.
        lock_bones: (nB,) bool. True 인 본은 M_init 그대로 둔다 (원본 demLock).

    Returns:
        (nF, nB, 4, 4) 본 상대 변환.
    """
    U = np.asarray(U, dtype=float)
    V = np.asarray(V, dtype=float)
    W = np.asarray(W, dtype=float)

    n_f = V.shape[0]
    n_b = W.shape[1]

    prog = progress if isinstance(progress, Progress) else Progress(progress)

    Uh = homogeneous(U)

    if M_init is None:
        M = np.tile(np.eye(4), (n_f, n_b, 1, 1))
    else:
        M = np.array(M_init, dtype=float)

    locked = (np.zeros(n_b, dtype=bool) if lock_bones is None
              else np.asarray(lock_bones, dtype=bool))
    if locked.all():
        return M

    prog.tick(0.02, "covariance")
    uuT = compute_uuT(W, Uh)
    vuT = compute_vuT(W, Uh, V, trans_affine, trans_affine_norm)
    prog.tick(0.2, "solving bones")

    n_iters = max(1, int(n_iters))
    total = n_iters * n_f

    for it in range(n_iters):
        for k in range(n_f):
            Mk = M[k]                                         # (nB, 4, 4) 뷰
            for j in range(n_b):
                if locked[j]:
                    continue
                # 다른 본들이 이미 설명한 몫을 뺀다(가우스-자이델: 갱신된 값을 바로 쓴다).
                coupling = np.einsum('lab,lbc->ac', uuT[j], Mk, optimize=True)
                Q = vuT[k, j] - coupling + uuT[j, j] @ Mk[j]

                solved = rigid_from_normal(Q)
                if solved is None:
                    continue
                M[k, j, :, :3] = solved
                M[k, j, :, 3] = (0.0, 0.0, 0.0, 1.0)

            done = it * n_f + k + 1
            if (k % 8) == 0 or done == total:
                prog.tick(0.2 + 0.8 * done / float(total),
                          "transforms {0}/{1}".format(it + 1, n_iters))

    prog.tick(1.0, "transforms done")
    return M
