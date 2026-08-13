# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 교대 최적화 (numpy 전용, Maya 비의존)
#
# ref/include/DemBones/DemBones.h 의 compute() (:344) + ref/src/command/mainCmd.cpp 의
# 수렴 판정(cbIterEnd, :38) 이식.
#
#     반복:  트랜스폼 갱신(웨이트 고정)  ->  웨이트 갱신(트랜스폼 고정)  ->  RMSE 확인
#
# 전형적인 교대 최적화다. 한쪽을 고정하면 다른 쪽은 (거의) 닫힌 형태로 풀리기 때문에
# 매 반복이 싸고, 오차는 단조 감소한다.
#
# 수렴 판정은 원본 커맨드라인 툴과 같다: **오차가 tolerance 비율만큼도 안 줄어드는 일이
# patience 번 연속**이면 멈춘다. 한 번 삐끗한 것으로 멈추지 않게 하는 장치다.

import numpy as np

from . import solver_transforms as trans_mod
from . import solver_weights as weights_mod
from .solver_common import Progress, rmse


def refine(U, V, M, W, faces=None, n_iters=10, tolerance=1e-3, patience=3,
           n_trans_iters=5, n_weights_iters=3, nnz=8, weights_smooth=1e-4,
           smooth_step=1.0, smooth_iters=20, trans_affine=10.0,
           trans_affine_norm=4.0, lock_bones=None, lock_weights=None,
           chunk=2000, progress=None, log=None):
    """트랜스폼과 웨이트를 번갈아 최적화한다.

    Args:
        M: (nF, nB, 4, 4) 시작 본 변환. None 이면 웨이트만으로 시작(단위행렬).
        W: (nV, nB) 시작 웨이트. None 이면 첫 반복에서 만들어진다.
        n_iters: 전역 반복 상한 (원본 nIters).
        tolerance / patience: 수렴 판정.
        lock_bones: (nB,) bool - 이 본들의 변환은 건드리지 않는다.
        lock_weights: (nV,) 0~1 - 이 버텍스들의 웨이트를 유지한다.
        log: 반복마다 문자열을 받는 콜백(선택).

    Returns:
        (M, W, history) - history 는 반복별 RMSE 리스트.
    """
    prog = progress if isinstance(progress, Progress) else Progress(progress)

    n_iters = max(1, int(n_iters))
    history = []

    # 시퀀스 기반 라플라시안은 U/V 에만 의존하므로 한 번 만들어 계속 쓴다(무겁다).
    smoother = weights_mod.build_smoother(U, V, faces) if faces else None

    prev_err = None
    left = int(patience)

    for it in range(n_iters):
        lo = it / float(n_iters)
        span = 1.0 / float(n_iters)
        step = prog.sub(lo, span)

        # ---- 1) 트랜스폼 (웨이트가 있어야 의미가 있다) ----
        if W is not None and n_trans_iters > 0:
            M = trans_mod.solve_transforms(
                U, V, W, M_init=M, n_iters=n_trans_iters,
                trans_affine=trans_affine, trans_affine_norm=trans_affine_norm,
                lock_bones=lock_bones, progress=step.sub(0.0, 0.45))

        # ---- 2) 웨이트 ----
        if n_weights_iters > 0:
            W = weights_mod.solve_weights(
                U, V, M, faces=faces, nnz=nnz, weights_smooth=weights_smooth,
                smooth_step=smooth_step, smooth_iters=smooth_iters,
                n_iters=n_weights_iters, w_init=W, lock_weights=lock_weights,
                chunk=chunk, smoother=smoother,
                progress=step.sub(0.45, 0.5))

        err = rmse(U, V, M, W, chunk=chunk)
        history.append(err)
        if log is not None:
            log("iter {0}: RMSE = {1:.6f}".format(it + 1, err))
        step.tick(1.0, "iter {0}".format(it + 1))

        # ---- 3) 수렴 판정 (mainCmd.cpp:41 과 같은 규칙) ----
        if prev_err is not None:
            improved = prev_err - err
            if err < prev_err * (1.0 + 1e-15) and improved < tolerance * prev_err:
                left -= 1
                if left <= 0:
                    if log is not None:
                        log("converged (no meaningful gain in {0} iterations)".format(patience))
                    break
            else:
                left = int(patience)
        prev_err = err

    prog.tick(1.0, "refine done")
    return M, W, history
