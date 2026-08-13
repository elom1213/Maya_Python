# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 풀어낸 클러스터로 조인트를 만든다 (maya.cmds 의존)
#
# 원본 DemBonesExt 의 `computeCentroids()` / `computeBind()` / `computeRoot()` 에 해당한다.
#
# **조인트를 어디에 놓을 것인가**가 전부다. 원본은 웨이트를 p(기본 4) 제곱해 가중한 무게중심에
# 놓는다. 그냥 평균이 아니라 제곱을 높게 주는 이유는, 경계에 걸쳐 웨이트가 얕게 묻은 버텍스가
# 위치를 끌고 가지 못하게 해서 **그 본이 확실히 지배하는 영역의 중심**으로 보내기 위해서다.
# 회전은 단위행렬(축 정렬)로 둔다.
#
# 상대 변환 M 은 조인트 위치와 **무관하게** 정의되므로(rest 월드 -> 포즈 월드), 조인트를 어디에
# 놓든 `joint.worldMatrix(k) = bind_world @ M[k]` 로 애니메이션이 정확히 재현된다.
# 위치는 "리거가 손대기 좋은 자리인가"의 문제이지 정확도의 문제가 아니다.

import numpy as np

import maya.api.OpenMaya as om
import maya.cmds as cmds


def bind_positions(U, W, p_norm=4.0):
    """(nB, 3) 본별 바인드 위치 = 웨이트 p 제곱 가중 무게중심."""
    U = np.asarray(U, dtype=float)
    Wp = np.power(np.maximum(np.asarray(W, dtype=float), 0.0), float(p_norm))

    mass = Wp.sum(axis=0)                                    # (nB,)
    positions = (Wp.T @ U)                                   # (nB, 3)

    good = mass > 1e-20
    positions[good] /= mass[good][:, None]
    if not good.all():
        # 웨이트를 하나도 못 가진 본은 모델 중심에 둔다(보통 곧 지워질 본).
        positions[~good] = U.mean(axis=0)
    return positions


def pick_root(E):
    """루트로 삼을 본 인덱스 = 혼자서 메시 전체를 가장 잘 설명하는 본.

    원본 computeRoot (DemBonesExt.h:225) 와 같은 기준이며, 오차표의 **열 합이 최소인 열**이다.
    보통 몸통처럼 가장 덜 움직이는 부위가 뽑힌다.
    """
    return int(np.argmin(np.asarray(E).sum(axis=0)))


def _world_matrix(node):
    sel = om.MSelectionList()
    sel.add(node)
    return np.asarray(sel.getDagPath(0).inclusiveMatrix()).reshape(4, 4)


def create_joints(positions, root=None, prefix="demBone", radius=1.0):
    """바인드 위치에 조인트를 만든다.

    Args:
        positions: (nB, 3) 월드 위치.
        root: None 이면 전부 형제로(플랫), 인덱스를 주면 그 본을 루트로 나머지를 그 밑에.
        prefix: 이름 접두사. `<prefix>_00` 형식.
        radius: 조인트 표시 반경.

    Returns:
        (조인트 이름 목록, (nB, 4, 4) 바인드 월드행렬)

    바인드 행렬은 **만들고 나서 실제 노드에서 읽는다**. 계층/jointOrient 때문에 값이 우리가
    의도한 것과 달라질 수 있는데, 읽어 오면 어떤 경우에도 M 과 짝이 맞는다.
    """
    positions = np.asarray(positions, dtype=float)
    n_b = positions.shape[0]

    names = [None] * n_b
    order = list(range(n_b))
    if root is not None:
        root = int(root)
        order = [root] + [j for j in range(n_b) if j != root]

    for j in order:
        if root is not None and j != root:
            cmds.select(names[root], replace=True)
        else:
            cmds.select(clear=True)
        names[j] = cmds.joint(
            position=[float(v) for v in positions[j]],
            name="{0}_{1:02d}".format(prefix, j),
            radius=float(radius))

    names = [(cmds.ls(n, l=True) or [n])[0] for n in names]
    bind_world = np.asarray([_world_matrix(n) for n in names])
    return names, bind_world


def suggest_radius(U, n_b):
    """모델 크기와 본 개수에 맞춘 보기 좋은 조인트 반경."""
    U = np.asarray(U, dtype=float)
    size = float(np.sqrt(((U - U.mean(axis=0)) ** 2).sum() / max(1, U.shape[0])))
    return max(1e-4, size / max(2.0, float(n_b)) * 1.5)
