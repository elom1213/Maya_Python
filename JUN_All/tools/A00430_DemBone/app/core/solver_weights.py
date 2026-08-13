# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 스키닝 웨이트 솔브 (numpy 전용, Maya 비의존)
#
# ref/include/DemBones/DemBones.h 의 computeWeights() (:276) 이식.
# 커맨드라인으로 치면 `DemBones --nTransIters=0` — **캐시 + 조인트 애님 -> 웨이트**.
#
# 아이디어: 버텍스 i 하나만 보면 문제가 아주 작아진다.
#
#     A x ~= b,   A 의 열 j = "본 j 만으로 변환한 궤적", b = 캐시 궤적
#     s.t. x >= 0, sum(x) = 1, 비영 성분 <= nnz
#
# 버텍스끼리 독립이므로 전부 따로 풀 수 있다. 관건은 A 를 만들지 않고 정규방정식만
# 값싸게 얻는 것이고, 원본이 쓰는 요령이 그대로 여기 있다:
#
#   mTm[j,l] = sum_k M3[k,j] @ M3[k,l].T     <- 프레임 루프는 여기서 딱 한 번
#   aTa[i]   = u_h[i] @ mTm[j,l] @ u_h[i].T  <- 버텍스별로는 4x4 이차형식 하나
#   aTb[i,j] = sum_k V[k,i] . (u_h[i] @ M3[k,j])
#
# 정규화 2종:
#   - weightsSmooth: 라플라시안으로 스무딩한 웨이트 ws 쪽으로 당긴다 (경계가 지저분해지는 것을 막음)
#   - lock_weights: 버텍스별 소프트 락. 1 이면 기존 웨이트를 그대로 유지한다
#
# 그리고 버텍스마다 **상위 nnz 개 본만** 남겨 실제로 푸는 계를 nnz x nnz 로 줄인다.
#
# 실측(mayapy, 합성 데이터): 20,000 버텍스 / 40 조인트 / 100 프레임 -> 약 12초.
#
# 출처: Dem Bones (c) 2019 Electronic Arts, BSD 3-Clause. 논문은 solver_common.py 헤더 참고.

import numpy as np

from . import convex_ls
from . import laplacian as lap_mod
from .solver_common import (Progress, bone_errors, compute_mTm, homogeneous,
                            model_size)

# 이보다 작은 값은 0 으로 본다(원본 weightEps).
WEIGHT_EPS = 1e-15


def build_smoother(U, V, faces):
    """메시 토폴로지 + 시퀀스로 웨이트 스무더를 만든다. faces 가 없으면 None."""
    if not faces:
        return None
    edges = lap_mod.build_edges(faces)
    if edges.shape[0] == 0:
        return None
    weights = lap_mod.edge_weights(U, V, edges)
    return lap_mod.WeightSmoother(U.shape[0], edges, weights)


def _candidates_from(score, n_keep):
    """행마다 값이 큰 순으로 n_keep 개 열 인덱스 -> (nV, n_keep)."""
    n_b = score.shape[1]
    keep = min(int(n_keep), n_b)
    if keep >= n_b:
        return np.tile(np.arange(n_b), (score.shape[0], 1))
    # argpartition 으로 상위 keep 개만 고른 뒤 그 안에서만 정렬한다(전체 정렬보다 싸다).
    part = np.argpartition(-score, keep - 1, axis=1)[:, :keep]
    rows = np.arange(score.shape[0])[:, None]
    order = np.argsort(-score[rows, part], axis=1)
    return part[rows, order]


def _normal_equations(Uh, V, M3, mTm, cand, lo, hi):
    """청크 [lo,hi) 의 aTa (c,K,K) 와 aTb (c,K) 를 만든다."""
    uh = Uh[lo:hi]                                            # (c, 4)
    idx = cand[lo:hi]                                         # (c, K)

    blocks = mTm[idx[:, :, None], idx[:, None, :]]            # (c, K, K, 4, 4)
    aTa = np.einsum('ia,ipqab,ib->ipq', uh, blocks, uh, optimize=True)
    del blocks

    vv = V[:, lo:hi, :]                                       # (nF, c, 3)
    aTb = np.empty(idx.shape)
    for p in range(idx.shape[1]):
        Mp = M3[:, idx[:, p], :, :]                           # (nF, c, 4, 3)
        pred = np.einsum('kiab,ia->kib', Mp, uh, optimize=True)
        aTb[:, p] = np.einsum('kib,kib->i', pred, vv, optimize=True)
        del Mp, pred
    return aTa, aTb


def solve_weights(U, V, M, faces=None, nnz=8, weights_smooth=1e-4,
                  smooth_step=1.0, smooth_iters=20, n_iters=3,
                  w_init=None, lock_weights=None, chunk=2000,
                  progress=None, smoother=None, errors=None):
    """LBS 웨이트를 푼다.

    Args:
        U: (nV, 3) rest 포즈 (월드).
        V: (nF, nV, 3) 목표 시퀀스 (월드).
        M: (nF, nB, 4, 4) 본 상대 변환 (Maya 행벡터 규약).
        faces: 폴리곤별 버텍스 인덱스. 주면 라플라시안 스무딩을 켠다.
        nnz: 버텍스당 최대 비영 웨이트 수.
        weights_smooth: 스무딩 정규화 강도.
        smooth_step / smooth_iters: 스무딩 세기 / 자코비 반복 횟수.
        n_iters: 웨이트 갱신 반복 횟수 (원본 nWeightsIters).
        w_init: (nV, nB) 시작 웨이트. 없으면 강체 오차로 초기화.
        lock_weights: (nV,) 0~1 소프트 락. w_init 이 있을 때만 의미가 있다.
        smoother / errors: 미리 만들어 둔 스무더 / 강체 오차 (Refine 에서 재사용).

    Returns:
        (nV, nB) 웨이트. 행 합 = 1, 비영 성분 <= nnz.
    """
    U = np.asarray(U, dtype=float)
    V = np.asarray(V, dtype=float)
    M = np.asarray(M, dtype=float)

    n_f, n_v = V.shape[0], V.shape[1]
    n_b = M.shape[1]
    keep = max(1, min(int(nnz), n_b))

    prog = progress if isinstance(progress, Progress) else Progress(progress)

    Uh = homogeneous(U)
    M3 = M[:, :, :, :3]

    if smoother is None:
        smoother = build_smoother(U, V, faces)

    # 스무딩 정규화를 스케일 독립으로 만드는 나눗셈 인자(원본 :295).
    reg_scale = max(1e-20, (model_size(U) ** 2) * n_f)

    W = None if w_init is None else np.array(w_init, dtype=float)
    lock = None
    if lock_weights is not None and W is not None:
        lock = np.clip(np.asarray(lock_weights, dtype=float), 0.0, 1.0)

    prog.tick(0.0, "preparing")
    mTm = compute_mTm(M)

    for it in range(max(1, int(n_iters))):
        span_lo = 0.05 + 0.95 * it / float(max(1, n_iters))
        span_hi = 0.05 + 0.95 * (it + 1) / float(max(1, n_iters))
        step_prog = prog.sub(span_lo, span_hi - span_lo)

        # ---- 후보 본 선별 + 스무딩 목표 ws ----
        if W is None:
            # 웨이트가 아직 없다: 강체 오차가 작은 본이 곧 후보 (원본 initWeights).
            if errors is None:
                errors = bone_errors(U, V, M, chunk=chunk,
                                     progress=step_prog.sub(0.0, 0.45))
            cand = _candidates_from(-errors, keep)
            ws = np.zeros((n_v, n_b))
            np.put_along_axis(ws, cand, 1.0 / keep, axis=1)
            base = 0.45
        else:
            if smoother is not None:
                ws = smoother.smooth(W, step=smooth_step, iters=smooth_iters)
                ws = smoother.normalize(ws, n_b)
            else:
                ws = W
            score = ws if lock is None else (1.0 - lock)[:, None] * ws + lock[:, None] * W
            cand = _candidates_from(score, keep)
            base = 0.05
        step_prog.tick(base, "normal equations")

        # ---- 버텍스별로 작은 제약 최소자승을 푼다 ----
        new_W = np.zeros((n_v, n_b))
        eye = np.eye(keep)
        n_chunks = max(1, int(np.ceil(n_v / float(chunk))))

        for c in range(n_chunks):
            lo = c * chunk
            hi = min(n_v, lo + chunk)
            aTa, aTb = _normal_equations(Uh, V, M3, mTm, cand, lo, hi)

            ws_c = np.take_along_axis(ws[lo:hi], cand[lo:hi], axis=1)
            if W is None:
                prev_c = None
                lock_c = None
            else:
                prev_c = np.take_along_axis(W[lo:hi], cand[lo:hi], axis=1)
                lock_c = None if lock is None else lock[lo:hi]

            for r in range(hi - lo):
                a = aTa[r] / reg_scale + weights_smooth * eye
                b = aTb[r] / reg_scale + weights_smooth * ws_c[r]

                if lock_c is not None and lock_c[r] > 0.0:
                    lk = lock_c[r]
                    a = (1.0 - lk) * a + lk * eye
                    b = (1.0 - lk) * b + lk * prev_c[r]

                x0 = ws_c[r] if prev_c is None else prev_c[r]
                s = x0.sum()
                x0 = x0 / s if s > 0.1 else np.full(keep, 1.0 / keep)

                x = convex_ls.solve(a, b, x0=x0, affine=True)
                x[x < WEIGHT_EPS] = 0.0
                s = x.sum()
                if s > 1e-12:
                    x = x / s
                else:
                    x = np.full(keep, 1.0 / keep)
                new_W[lo + r, cand[lo + r]] = x

            step_prog.tick(base + (1.0 - base) * (c + 1) / float(n_chunks),
                           "weights {0}/{1}".format(it + 1, n_iters))

        W = new_W

    prog.tick(1.0, "weights done")
    return W
