# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-10
# A00420_Wrapper core - Thin Plate Spline(TPS) 공간 워프. maya 비의존(numpy 만).
#
# 컨트롤 포인트 쌍 (src_i -> dst_i) 을 정확히 지나면서, 그 사이 공간은 "휘는 에너지가
# 최소"가 되도록 부드럽게 채우는 변형이다. Wrap3D 의 Wrapping 노드가 포인트 페어로
# 하는 일과 같은 역할을 한다(여기서는 그 페어가 커브에서 나온다).
#
#   f(x) = sum_i w_i * phi(|x - p_i|) + a0 + A * x       phi(r) = r  (3D 커널)
#
# 선형계:
#   [ K + lam*I   P ] [ W ]   [ Q ]
#   [ P^T         0 ] [ A ] = [ 0 ]
#   K_ij = phi(|p_i - p_j|),  P = [1, x, y, z]
#
# lam(Smoothness)을 올리면 컨트롤 포인트를 정확히 통과하지 않는 대신 결과가 부드러워진다
# (커브 샘플에 노이즈가 있거나 두 커브 모양이 많이 다를 때 쓴다).
#
# 주의: 컨트롤 포인트가 겹치면 K 가 특이해져 결과가 폭발한다. 호출 전에
# guide_sampler.merge_duplicates() 로 겹친 점을 합쳐 두는 것을 전제한다.

import numpy as np


def _pairwise_distance(a, b):
    """(n, 3) x (m, 3) -> (n, m) 유클리드 거리."""
    d = a[:, None, :] - b[None, :, :]
    return np.sqrt(np.einsum("ijk,ijk->ij", d, d))


class ThinPlateSpline(object):
    """컨트롤 포인트 쌍으로 만든 3D TPS 워프."""

    def __init__(self, src, dst, smoothness=0.0):

        src = np.asarray(src, dtype=np.float64)
        dst = np.asarray(dst, dtype=np.float64)

        if src.shape != dst.shape or src.ndim != 2 or src.shape[1] != 3:
            raise ValueError("src / dst must be matching (N, 3) arrays.")

        n = len(src)
        if n < 4:
            raise ValueError(
                "Need at least 4 control points (got {0}). "
                "Add more guide pairs or raise the sample count.".format(n))

        k = _pairwise_distance(src, src)

        # 정규화 항은 데이터 스케일에 맞춰 준다(메시 크기에 상관없이 같게 동작하도록).
        scale = float(k.mean()) or 1.0
        lam = float(smoothness) * scale + 1e-9 * scale

        k = k + np.eye(n) * lam

        p = np.hstack([np.ones((n, 1)), src])

        left = np.zeros((n + 4, n + 4), dtype=np.float64)
        left[:n, :n] = k
        left[:n, n:] = p
        left[n:, :n] = p.T

        right = np.zeros((n + 4, 3), dtype=np.float64)
        right[:n] = dst

        try:
            sol = np.linalg.solve(left, right)
        except np.linalg.LinAlgError:
            sol = np.linalg.lstsq(left, right, rcond=None)[0]

        self.src = src
        self.dst = dst
        self.weights = sol[:n]
        self.affine = sol[n:]
        self.control_count = n

    # ---- 적용 ------------------------------------------------------

    def apply(self, points, chunk=4096):
        """(N, 3) 점들을 워프한다. 메모리를 위해 chunk 행씩 나눠 계산한다."""
        points = np.asarray(points, dtype=np.float64)
        out = np.empty_like(points)

        for start in range(0, len(points), chunk):
            end = min(start + chunk, len(points))
            block = points[start:end]

            r = _pairwise_distance(block, self.src)
            homogeneous = np.hstack([np.ones((end - start, 1)), block])

            out[start:end] = r @ self.weights + homogeneous @ self.affine

        return out

    def residual(self):
        """컨트롤 포인트가 목표 위치에 얼마나 정확히 갔는지 (평균 오차, 최대 오차)."""
        err = np.linalg.norm(self.apply(self.src) - self.dst, axis=1)
        return float(err.mean()), float(err.max())
