# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 본을 처음부터 만들어내는 초기화 (numpy 전용, Maya 비의존)
#
# 원본 Dem Bones 의 `init()` "웨이트도 트랜스폼도 없음" 분기(DemBones.h:190~213) 이식.
# 커맨드라인으로 치면 `DemBones -b 20` — **캐시만 주면 본 개수만큼 클러스터를 만들어 낸다.**
#
# LBG-VQ (Linde-Buzo-Gray Vector Quantization):
#
#     본 1개에서 시작
#     repeat:
#         split()                     쪼갤 만한 클러스터를 골라 새 라벨을 심고
#         repeat n_init_iters:
#             transforms from label   라벨별 최적 강체를 구하고
#             compute_label()         메시 연결성을 따라 라벨을 다시 퍼뜨리고
#             prune_bones()           너무 작은 클러스터는 없앤다
#     until 목표 개수 도달
#
# **핵심은 compute_label 이 "오차 최소 본"을 그냥 고르지 않는다는 것**이다. 클러스터마다
# 오차가 가장 작은 버텍스를 시드로 삼아 **메시 이웃을 따라 우선순위 큐로 퍼뜨린다**.
# 그래서 클러스터가 조각나지 않는다(= 본이 몸 반대편까지 튀지 않는다).
#
# 원본과 다른 점: 원본은 이웃마다 `errorVtxBone(i2, j)` 를 그때그때 다시 계산한다.
# 우리는 `bone_errors()` 로 (nV x nB) 오차표를 **벡터화해서 통째로** 갖고 있으므로 O(1) 조회다.
# 대신 그 표를 만드는 비용이 O(nV*nB*nF) 라, 초기화 단계는 **프레임을 솎아서** 쓴다(§manager).
#
# 출처: Dem Bones (c) 2019 Electronic Arts, BSD 3-Clause. 논문은 solver_common.py 헤더 참고.
# (원본 소스를 읽거나 import 하지 않는다 - 알고리즘만 파이썬으로 새로 작성했다.)

import heapq

import numpy as np

from . import laplacian as lap_mod
from .solver_common import Progress, bone_errors, homogeneous
from .solver_transforms import rigid_from_normal


def compute_trans_from_label(U, V, label, n_b):
    """라벨이 같은 버텍스들로 프레임마다 최적 강체를 구한다 -> (nF, nB, 4, 4).

    원본 computeTransFromLabel (DemBones.h:507). 공분산은 반드시 **4x4** 로 쌓는다 -
    (3,3) 성분이 질량이고, 무게중심을 그 질량으로 나눠야 한다.
    """
    Uh = homogeneous(U)
    n_f = V.shape[0]

    M = np.tile(np.eye(4), (n_f, n_b, 1, 1))
    valid = label >= 0
    if not valid.any():
        return M

    lab = label[valid]
    uh = Uh[valid]

    for k in range(n_f):
        vk = V[k][valid]
        Q = np.zeros((n_b, 4, 4))
        for a in range(4):
            wa = uh[:, a]
            for b in range(3):
                Q[:, a, b] = np.bincount(lab, weights=wa * vk[:, b], minlength=n_b)
            # v 의 동차 성분은 항상 1
            Q[:, a, 3] = np.bincount(lab, weights=wa, minlength=n_b)

        for j in range(n_b):
            solved = rigid_from_normal(Q[j])
            if solved is not None:
                M[k, j, :, :3] = solved
    return M


def label_to_weights(label, n_b):
    """라벨 -> 0/1 웨이트 (nV, nB). 원본 labelToWeights (DemBones.h:520)."""
    W = np.zeros((label.shape[0], n_b))
    valid = np.flatnonzero(label >= 0)
    W[valid, label[valid]] = 1.0
    return W


def compute_label(label, E, n_b, neighbors):
    """메시 연결성을 따라 라벨을 다시 퍼뜨린다. 원본 computeLabel (DemBones.h:447).

    Args:
        label: (nV,) 현재 라벨. 도달하지 못한 버텍스는 이 값을 유지한다(원본과 같음).
        E: (nV, nB) 버텍스-본 강체 오차표.
        neighbors: `laplacian.Neighborhood`.

    Returns:
        (nV,) 새 라벨. 어디에도 안 닿은 버텍스는 오차 최소 본으로 채운다.
    """
    n_v = label.shape[0]
    out = label.copy()

    # 우선순위는 **절대 오차가 아니라 "최선의 본 대비 얼마나 나쁜가"** 로 잡는다.
    #
    # 원본은 E 를 그대로 우선순위로 쓴다(DemBones.h:485). 힙이 하나뿐이라 그러면 오차가
    # 작은 본이 먼저 전부 훑고 지나가고, 뒤늦게 차례가 온 본은 **이웃이 이미 다 점령돼
    # 확장할 곳이 없어** 시드 한 개만 쥔 채 굶는다 -> pruneBones 에 지워진다. 실측:
    # 4개로 쪼갠 클러스터가 매 라운드 [1, 1, 431, 359] 로 무너져 목표 개수에 도달하지 못했다.
    #
    # 차이값을 쓰면 "그 버텍스의 주인" 은 0 에 가까운 값으로 즉시 자기 자리를 잡고,
    # 남의 영역으로 넘어가려는 본은 값이 튀어 그 자리에서 멈춘다. 연결성을 따라 자란다는
    # 성질(클러스터가 조각나지 않는다)은 그대로다.
    advantage = E - E.min(axis=1, keepdims=True)

    # 클러스터마다 "이 본이 가장 확실히 주인인 버텍스" 를 시드로.
    seeds = []
    for j in range(n_b):
        members = np.flatnonzero(label == j)
        if members.size == 0:
            continue
        best = members[int(np.argmin(advantage[members, j]))]
        seeds.append((float(advantage[best, j]), j, int(best)))

    if not seeds:
        return np.argmin(E, axis=1)

    dirty = np.ones(n_v, dtype=bool)

    # 시드는 **먼저 확정**한다. 힙이 하나뿐이라, 오차가 낮은 본이 먼저 퍼지면서 다른 본의
    # 시드까지 집어삼키면 그 본은 힙에 남은 항목이 없어 **한 버텍스도 못 가지고 굶어 죽는다**
    # (그리고 곧 pruneBones 에 지워진다). 실측: 그래서 4개로 쪼갠 클러스터가 매번 다시 2개로
    # 돌아가 목표 개수에 영영 도달하지 못했다. 시드를 미리 박아 두면 모든 본이 최소 1개를
    # 쥔 채 자기 자리에서 자라기 시작한다(= 다중 소스 다익스트라의 소스 확정).
    for _err, j, i in seeds:
        out[i] = j
        dirty[i] = False

    heap = []
    for _err, j, i in seeds:
        for i2 in neighbors.of(i):
            if dirty[i2]:
                heapq.heappush(heap, (float(advantage[i2, j]), j, int(i2)))

    while heap:
        _err, j, i = heapq.heappop(heap)
        if not dirty[i]:
            continue
        out[i] = j
        dirty[i] = False
        for i2 in neighbors.of(i):
            if dirty[i2]:
                heapq.heappush(heap, (float(advantage[i2, j]), j, int(i2)))

    missing = np.flatnonzero(out < 0)
    if missing.size:
        out[missing] = np.argmin(E[missing], axis=1)
    return out


def grow_patch(neighbors, seed, member_mask, min_size, max_size):
    """seed 에서 클러스터 안쪽으로만 BFS 로 퍼져 나가며 링 단위로 패치를 키운다.

    **왜 필요한가**: 원본은 새 클러스터의 씨앗으로 시드의 1링(4~5 버텍스)만 심는다
    (DemBones.h:589). 그런데 그 몇 개로 맞춘 강체는 자유도에 비해 표본이 적어 오차가 크고,
    바로 다음 `compute_label` 에서 옆의 큰 클러스터에 **자기 씨앗까지 빼앗긴 뒤 pruneBones 로
    사라진다**. 실측: 20,100 버텍스 원통에서 목표 20개를 줘도 2개에서 멈췄다.
    씨앗을 클러스터 크기에 비례해 키우면 새 본이 경쟁할 수 있게 되어 정상적으로 갈라진다.

    Args:
        member_mask: (nV,) bool - 이 클러스터에 속한 버텍스만 True (다른 클러스터를 침범하지
            않도록 BFS 를 여기로 가둔다).
    """
    picked = [int(seed)]
    taken = np.zeros(member_mask.shape[0], dtype=bool)
    taken[seed] = True

    frontier = [int(seed)]
    while frontier and len(picked) < min_size:
        nxt = []
        for i in frontier:
            for i2 in neighbors.of(i):
                i2 = int(i2)
                if taken[i2] or not member_mask[i2]:
                    continue
                taken[i2] = True
                picked.append(i2)
                nxt.append(i2)
                if len(picked) >= max_size:
                    return np.asarray(picked, dtype=np.int64)
        frontier = nxt

    return np.asarray(picked, dtype=np.int64)


def split(U, label, n_b, E, neighbors, max_b, threshold=3):
    """쪼갤 만한 클러스터에 새 라벨을 심는다. 원본 split (DemBones.h:532).

    시드 고르는 기준이 특이하다 - **오차도 크고 중심에서도 먼** 지점
    `|(e - minE) * (d - minD)|` 이 최대인 버텍스. 둘 중 하나만 커서는 쪼갤 가치가 없다는 판단이다.

    Returns:
        (새 label, 새 n_b)
    """
    label = label.copy()
    valid = label >= 0
    if not valid.any() or n_b >= max_b:
        return label, n_b

    counts = np.bincount(label[valid], minlength=n_b).astype(float)

    # 클러스터 중심까지의 거리 d, 강체 피팅 오차 e
    centroid = np.zeros((n_b, 3))
    for axis in range(3):
        centroid[:, axis] = np.bincount(label[valid], weights=U[valid, axis],
                                        minlength=n_b)
    safe = np.maximum(counts, 1.0)
    centroid /= safe[:, None]

    d = np.zeros(label.shape[0])
    e = np.zeros(label.shape[0])
    d[valid] = np.linalg.norm(U[valid] - centroid[label[valid]], axis=1)
    e[valid] = np.sqrt(np.maximum(E[valid, label[valid]], 0.0))

    min_d = np.full(n_b, np.inf)
    min_e = np.full(n_b, np.inf)
    np.minimum.at(min_d, label[valid], d[valid])
    np.minimum.at(min_e, label[valid], e[valid])
    cluster_err = np.bincount(label[valid], weights=e[valid], minlength=n_b)

    avg_err = cluster_err.sum() / float(n_b)
    count_id = n_b

    for j in range(n_b):
        if count_id >= max_b:
            break
        if counts[j] <= threshold * 2 or cluster_err[j] <= avg_err / 100.0:
            continue

        members = np.flatnonzero(label == j)
        if members.size == 0:
            continue
        score = np.abs((e[members] - min_e[j]) * (d[members] - min_d[j]))
        seed = int(members[int(np.argmax(score))])

        # 시드 주변을 새 라벨로 떼어 낸다. 크기는 클러스터에 비례시킨다 - 1링만 심으면
        # 새 본이 다음 라벨 확산에서 살아남지 못한다(grow_patch 독스트링 참고).
        mask = label == j
        want = int(min(max(8, members.size // 8), max(1, members.size // 2)))
        fresh = grow_patch(neighbors, seed, mask, want, members.size // 2)
        label[fresh] = count_id
        count_id += 1

    return label, count_id


def prune_bones(label, n_b, E, neighbors, threshold=3):
    """버텍스가 너무 적은 본을 없애고 번호를 다시 매긴다. 원본 pruneBones (DemBones.h:597).

    Returns:
        (label, n_b, E, 바뀌었는지)
    """
    valid = label >= 0
    counts = np.bincount(label[valid], minlength=n_b)
    keep = np.flatnonzero(counts >= threshold)

    if keep.size == n_b:
        return label, n_b, E, False
    if keep.size == 0:
        return label, n_b, E, False

    new_id = np.full(n_b, -1, dtype=int)
    new_id[keep] = np.arange(keep.size)

    new_label = np.where(valid, new_id[np.maximum(label, 0)], -1)
    new_E = E[:, keep]
    new_nb = int(keep.size)

    # 라벨을 잃은 버텍스는 라벨 확산으로 다시 채운다(원본도 여기서 computeLabel 을 부른다).
    new_label = compute_label(new_label, new_E, new_nb, neighbors)
    return new_label, new_nb, new_E, True


def initialize(U, V, faces, target_bones, n_init_iters=5, threshold=3,
               neighbors=None, progress=None, log=None):
    """캐시만으로 본 클러스터를 만들어 낸다.

    Args:
        U: (nV, 3) rest 포즈.
        V: (nF, nV, 3) 목표 시퀀스. **초기화용으로 프레임을 솎아 넣는 것을 권장**한다
            (오차표 비용이 O(nV*nB*nF) 라 여기가 제일 무겁다).
        faces: 폴리곤별 버텍스 인덱스. 연결성이 없으면 클러스터가 조각난다.
        target_bones: 목표 본 개수. **정확히 이 개수가 나오지는 않는다** - 분할/솎아내기
            결과로 달라질 수 있다(원본도 같다, DemBones.h:182 주석).

    Returns:
        (W, label, n_b) - W 는 (nV, n_b) 0/1 웨이트.
    """
    U = np.asarray(U, dtype=float)
    V = np.asarray(V, dtype=float)

    prog = progress if isinstance(progress, Progress) else Progress(progress)
    say = log or (lambda *_a: None)

    n_v = U.shape[0]
    target_bones = max(1, int(target_bones))

    if neighbors is None:
        neighbors = lap_mod.neighborhood_from_faces(n_v, faces or [])

    label = np.zeros(n_v, dtype=int)
    n_b = 1

    # 진행률은 "본 개수가 목표에 얼마나 다가갔나" 로 잡는다(반복 횟수를 미리 모른다).
    def _report(message):
        frac = min(0.99, np.log2(max(1, n_b)) / max(1.0, np.log2(target_bones)))
        prog.tick(frac, message)

    _report("initializing bones")

    guard = 0
    while True:
        guard += 1
        if guard > 64:                       # 폭주 방지 - 정상적으로는 log2(target) 회
            break

        previous = n_b
        M = compute_trans_from_label(U, V, label, n_b)
        E = bone_errors(U, V, M)
        label, n_b = split(U, label, n_b, E, neighbors, target_bones, threshold)
        if n_b > previous:
            # 새로 생긴 본의 오차 열이 아직 없다 - 다시 만든다.
            M = compute_trans_from_label(U, V, label, n_b)
            E = bone_errors(U, V, M)

        for _rep in range(max(1, int(n_init_iters))):
            M = compute_trans_from_label(U, V, label, n_b)
            E = bone_errors(U, V, M)
            label = compute_label(label, E, n_b, neighbors)
            label, n_b, E, changed = prune_bones(label, n_b, E, neighbors, threshold)
            _report("clustering ({0} bones)".format(n_b))

        say("split -> {0} bones".format(n_b))

        if n_b >= target_bones or n_b <= previous:
            break

    prog.tick(1.0, "{0} bones".format(n_b))
    return label_to_weights(label, n_b), label, n_b
