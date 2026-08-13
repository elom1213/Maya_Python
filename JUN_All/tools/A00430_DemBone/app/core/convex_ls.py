# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 제약 최소자승 솔버 (numpy 전용, Maya 비의존)
#
# ref/include/DemBones/ConvexLS.h 의 Dem::ConvexLS 를 옮긴 것.
#
#     min |Ax - b|^2   subject to   x >= 0,  (옵션) sum(x) = 1
#
# 스키닝 웨이트가 정확히 이 형태다: 음수 웨이트 금지 + 버텍스당 합 1.
#
# 두 제약을 다루는 방법이 원본의 핵심이고 그대로 가져왔다:
#   - 비음 제약: **active set method**. 0 으로 눌린 변수(active)와 자유 변수(passive)를
#     나눠 자유 변수만 풀고, 음수가 나오면 그 방향으로 갈 수 있는 만큼만 가서 변수를
#     active 로 내린다. (Lawson-Hanson NNLS 계열)
#   - 합=1 제약: `ones` 벡터의 Householder QR 로 얻은 **널스페이스 기저 Q2** 에 gradient 를
#     투영한다. 그러면 이동해도 합이 변하지 않으므로 제약이 저절로 유지된다.
#     Q2 는 크기별로 한 번만 만들어 캐시한다(원본 ConvexLS::init 과 같은 이유).
#
# scipy 가 Maya 에 없어서(2024 mayapy 확인) 직접 구현해야 했던 두 조각 중 하나다.
#
# 참고 / 인용:
#   Dem Bones, Copyright (c) 2019 Electronic Arts. BSD 3-Clause (ref/LICENSE.md)
#   Le & Deng, "Smooth Skinning Decomposition with Rigid Bones",
#   ACM TOG 31(6), SIGGRAPH Asia 2012.

import numpy as np


# 크기별 널스페이스 기저 캐시. {n: (n, n-1) 행렬}
_Q2_CACHE = {}


def null_space_basis(n):
    """`sum(x) = c` 평면의 널스페이스 기저 (n, n-1).

    `ones(n)` 의 Householder QR 에서 첫 열(=ones 방향)을 뺀 나머지가 곧
    "합을 바꾸지 않는 방향들"이다.
    """
    if n < 2:
        return np.zeros((n, 0))
    basis = _Q2_CACHE.get(n)
    if basis is None:
        q, _ = np.linalg.qr(np.ones((n, 1)), mode="complete")
        basis = np.ascontiguousarray(q[:, 1:])
        _Q2_CACHE[n] = basis
    return basis


def _solve_sym(a, b):
    """대칭 계를 푼다. 특이(singular)하면 최소자승으로 물러선다."""
    try:
        return np.linalg.solve(a, b)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(a, b, rcond=None)[0]


def solve(aTa, aTb, x0=None, affine=True, max_iter=None):
    """min |Ax-b|^2  s.t.  x >= 0 (+ affine 이면 sum(x)=1).

    Args:
        aTa: (n, n) 정규방정식 좌변 A^T A.
        aTb: (n,)  정규방정식 우변 A^T b.
        x0: 초기 해(warm start). None 이면 균등분배.
        affine: True 면 합=1 제약을 건다.
        max_iter: active set 반복 상한. None 이면 n (원본과 동일).

    Returns:
        (n,) 해. 비음이며 affine 이면 합이 1.
    """
    n = int(aTa.shape[0])
    if n == 0:
        return np.zeros(0)
    if n == 1:
        return np.ones(1) if affine else np.array([max(0.0, aTb[0] / aTa[0, 0])])

    if x0 is None:
        x = np.full(n, 1.0 / n)
    else:
        x = np.asarray(x0, dtype=float).copy()

    # idx[:n_pass] = 자유(passive) 변수, 나머지 = 0 으로 눌린(active) 변수.
    idx = np.empty(n, dtype=int)
    n_pass = 0
    tail = n - 1
    for i in range(n):
        if x[i] > 0.0:
            idx[n_pass] = i
            n_pass += 1
        else:
            idx[tail] = i
            tail -= 1

    if n_pass == 0:
        # 전부 0 인 시작점은 진행이 안 된다 - 균등분배로 되돌린다.
        x = np.full(n, 1.0 / n)
        idx = np.arange(n)
        n_pass = n

    limit = n if max_iter is None else int(max_iter)

    for _ in range(limit):
        act = idx[:n_pass]

        # ---- 자유 변수 방향(p) 계산 ----
        p = np.zeros(n)
        if n_pass > 1:
            sub_a = aTa[np.ix_(act, act)]
            sub_b = aTb[act] - aTa[act, :] @ x
            if affine:
                # 합을 보존하는 부분공간으로 투영해서 푼다.
                q2 = null_space_basis(n_pass)
                z = q2 @ _solve_sym(q2.T @ sub_a @ q2, q2.T @ sub_b)
            else:
                z = _solve_sym(sub_a, sub_b)
            p[act] = z
        elif not affine:
            j = act[0]
            denom = aTa[j, j]
            if denom > 0.0:
                p[j] = (aTb[j] - aTa[j, :] @ x) / denom

        # ---- 그 방향으로 갈 수 있는가 ----
        if (x[act] + p[act]).min() >= -1e-12:
            x = x + p
            if n_pass == n:
                break
            # 눌러둔 변수 중 가장 이득이 큰 것을 자유 변수로 올린다.
            rest = idx[n_pass:]
            gain = aTb[rest] - aTa[rest, :] @ x
            i_max = int(np.argmax(gain))
            if gain[i_max] <= 0.0:
                break                       # 더 올릴 게 없다 = 최적
            idx[i_max + n_pass], idx[n_pass] = idx[n_pass], idx[i_max + n_pass]
            n_pass += 1
        else:
            # 음수가 되기 직전까지만 가고, 0 에 닿은 변수를 active 로 내린다.
            alpha = None
            i_min = -1
            for i in range(n_pass):
                j = idx[i]
                if p[j] < 0.0:
                    a = -x[j] / p[j]
                    if i_min == -1 or a < alpha:
                        alpha = a
                        i_min = i
            if i_min == -1:
                # 수치적으로는 결국 갈 수 있는 걸음이었다 - 받고 끝낸다.
                x = np.maximum(x + p, 0.0)
                break
            x = x + alpha * p
            eps = abs(x[idx[i_min]])
            x[idx[i_min]] = 0.0
            i = 0
            while i < n_pass:
                if x[idx[i]] <= eps:
                    n_pass -= 1
                    idx[i], idx[n_pass] = idx[n_pass], idx[i]
                else:
                    i += 1
            if n_pass == 0:
                break

        if affine:
            s = x.sum()
            if s > 1e-12:
                x = x / s

    x = np.maximum(x, 0.0)
    if affine:
        s = x.sum()
        x = x / s if s > 1e-12 else np.full(n, 1.0 / n)
    return x
