# -*- coding: utf-8 -*-
"""
sym_core - 대칭 테이블/미러/플립/리버트 수학 (씬 비의존, 순수 좌표 계산).

origin.mel 의 두 병목을 알고리즘으로 제거한다.
  - 대칭 매칭 O(N^2) -> 공간 해시로 O(N)        (build_symmetry)
  - abGetSymVtx 선형 탐색 O(N) -> dict 조회 O(1) (sym_pair)

좌표는 [(x, y, z), ...] 리스트로 주고받는다. 실제 get/setPoints 는 mesh_io 가 담당.
모든 함수는 인덱스 기준으로 동작하며 base 메시와 대상 메시는 동일 토폴로지(같은 정점
순서)를 가진다고 가정한다(원본과 동일 전제).
"""

import math


# ----------------------------------------------------------------------
# 공간 해시 헬퍼
# ----------------------------------------------------------------------

def _bucket(p, inv_tol):
    return (
        int(math.floor(p[0] * inv_tol)),
        int(math.floor(p[1] * inv_tol)),
        int(math.floor(p[2] * inv_tol)),
    )


_NEIGHBORS = [(dx, dy, dz)
              for dx in (-1, 0, 1)
              for dy in (-1, 0, 1)
              for dz in (-1, 0, 1)]


def _reflect(p, axis, mid):
    """축 mid 평면에 대한 반사 좌표(나머지 축은 그대로)."""
    q = [p[0], p[1], p[2]]
    q[axis] = 2.0 * mid - p[axis]
    return (q[0], q[1], q[2])


def _within_tol(a, b, tol):
    return (abs(a[0] - b[0]) < tol and
            abs(a[1] - b[1]) < tol and
            abs(a[2] - b[2]) < tol)


# ----------------------------------------------------------------------
# 대칭 계산 (Select Base / Check Symmetry 공용)
# ----------------------------------------------------------------------

def compute_symmetry(points, axis, tol, mid):
    """공간 해시로 대칭 짝을 찾는다. O(N).

    반환 dict:
        pair         : {i: j, j: i}  대칭 정점 인덱스 양방향 매핑
        zero         : set(idx)       대칭 평면 위(중앙) 정점
        asym         : [idx, ...]     짝을 못 찾은 비대칭 정점
        symmetrical  : bool           전부 매칭됐는지
    """
    n = len(points)
    if tol <= 0:
        tol = 1e-6
    inv_tol = 1.0 / tol

    # mid 가 NaN/inf 면(예: NaN 정점이 섞인 메시의 bbox) 대칭 측정이 불가능하다.
    if not math.isfinite(mid):
        return {
            "pair": {},
            "zero": set(),
            "asym": list(range(n)),
            "symmetrical": False,
            "invalid": n,
            "bad_mid": True,
        }

    zero = set()
    pos_list = []                 # (idx, point)
    neg_buckets = {}              # bucket -> [(idx, point), ...]
    invalid = 0                   # NaN/inf 좌표 정점 수(매칭 제외)

    for i in range(n):
        p = points[i]
        # 좌표가 NaN/inf 이면 매칭에서 제외(원본 MEL 처럼 비대칭으로 남긴다).
        # int(floor(NaN)) 가 ValueError 를 내므로 반드시 먼저 걸러야 한다.
        if not (math.isfinite(p[0]) and math.isfinite(p[1]) and math.isfinite(p[2])):
            invalid += 1
            continue
        offset = p[axis] - mid
        if abs(offset) < tol:
            zero.add(i)
        elif offset > 0.0:
            pos_list.append((i, p))
        else:
            neg_buckets.setdefault(_bucket(p, inv_tol), []).append((i, p))

    pair = {}
    matched = set(zero)

    for (i, p) in pos_list:
        target = _reflect(p, axis, mid)        # p 의 거울 위치(neg 쪽에 있어야 함)
        b = _bucket(target, inv_tol)
        found = None
        for (dx, dy, dz) in _NEIGHBORS:
            cell = neg_buckets.get((b[0] + dx, b[1] + dy, b[2] + dz))
            if not cell:
                continue
            for (j, q) in cell:
                if j in matched:
                    continue
                if _within_tol(target, q, tol):
                    found = j
                    break
            if found is not None:
                break
        if found is not None:
            pair[i] = found
            pair[found] = i
            matched.add(i)
            matched.add(found)

    asym = [i for i in range(n) if i not in matched]
    return {
        "pair": pair,
        "zero": zero,
        "asym": asym,
        "symmetrical": (len(matched) == n),
        "invalid": invalid,
        "bad_mid": False,
    }


# ----------------------------------------------------------------------
# Mirror / Flip (abMirrorSel)
# ----------------------------------------------------------------------

def mirror_points(obj_points, base_points, sym_pair, sel_indices,
                  axis, mid, base_mid, neg_to_pos, flip, tol):
    """선택 정점을 미러(또는 플립)한 전체 좌표 배열(월드)을 반환한다.

    - 선택 정점의 pos/neg/zero 분류는 base 메시 위치(base_mid 기준)로 한다.
    - 실제 반사는 대상 메시의 대칭 평면 mid 기준으로 한다(원본과 동일하게 분리).
    - neg_to_pos 면 neg 쪽 선택을 소스로 사용.
    """
    pts = [(*p,) for p in obj_points]   # 가변 복사(튜플 리스트)

    pos_src = []
    neg_src = []
    zero_sel = []
    for idx in sel_indices:
        offset = base_points[idx][axis] - base_mid
        if abs(offset) < tol:
            zero_sel.append(idx)
        elif offset > 0.0:
            pos_src.append(idx)
        else:
            neg_src.append(idx)

    src = neg_src if neg_to_pos else pos_src

    for i in src:
        j = sym_pair.get(i)
        if j is None:
            continue
        if not flip:
            pts[j] = _reflect(pts[i], axis, mid)
        else:
            mi = _reflect(pts[i], axis, mid)
            mj = _reflect(pts[j], axis, mid)
            pts[j] = mi
            pts[i] = mj

    for i in zero_sel:
        if flip:
            pts[i] = _reflect(pts[i], axis, mid)
        else:
            q = list(pts[i])
            q[axis] = mid
            pts[i] = (q[0], q[1], q[2])

    return pts


# ----------------------------------------------------------------------
# Selection Mirror (abSelMirror)
# ----------------------------------------------------------------------

def selection_mirror(sym_pair, sel_indices):
    """선택 정점의 대칭 정점 인덱스를 반환(짝 없으면 자기 자신)."""
    return [sym_pair.get(i, i) for i in sel_indices]


# ----------------------------------------------------------------------
# Select Moved Verts (abSelMovedVerts)
# ----------------------------------------------------------------------

def moved_vertices(obj_points, base_points, tol):
    """base 대비 위치가 바뀐 정점 인덱스(오브젝트 공간 비교)."""
    thresh_sq = 3.0 * tol * tol      # 원본의 magnitude(diff) > magnitude(vTol) 와 동치
    res = []
    n = min(len(obj_points), len(base_points))
    for i in range(n):
        o = obj_points[i]
        b = base_points[i]
        dx = o[0] - b[0]
        dy = o[1] - b[1]
        dz = o[2] - b[2]
        if (dx * dx + dy * dy + dz * dz) > thresh_sq:
            res.append(i)
    return res


# ----------------------------------------------------------------------
# Revert Selected (abRevertSel)
# ----------------------------------------------------------------------

def revert_points(obj_points, base_points, sel_indices, bias_input):
    """선택 정점을 base 로 bias 만큼 되돌린 전체 좌표 배열(오브젝트 공간) 반환.

    bias_input 1.0 = 완전히 base, 0.0 = 변화 없음(원본과 동일 의미).
    """
    b = bias_input
    if b > 1.0:
        b = 1.0
    elif b < 0.0:
        b = 0.0
    b = 1.0 - b
    if b < 0.01:
        b = 0.0

    pts = [(*p,) for p in obj_points]
    for i in sel_indices:
        o = obj_points[i]
        base = base_points[i]
        pts[i] = (
            base[0] + (o[0] - base[0]) * b,
            base[1] + (o[1] - base[1]) * b,
            base[2] + (o[2] - base[2]) * b,
        )
    return pts


def revert_interactive_points(full_points, vert_indices, pos_table, base_table, bias):
    """슬라이더 드래그용: 캐시된 (현재pos, basepos) 로 bias 보간한 전체 배열 반환.

    full_points : 현재 전체 좌표(오브젝트 공간) 복사 기준
    vert_indices: 캐시된 정점 인덱스
    pos_table   : 각 정점의 드래그 시작 시점 좌표
    base_table  : 각 정점의 base 좌표
    bias        : 슬라이더 값(0=base, 1=원위치)
    """
    pts = [(*p,) for p in full_points]
    for k, i in enumerate(vert_indices):
        o = pos_table[k]
        base = base_table[k]
        pts[i] = (
            base[0] + (o[0] - base[0]) * bias,
            base[1] + (o[1] - base[1]) * bias,
            base[2] + (o[2] - base[2]) * bias,
        )
    return pts


# ----------------------------------------------------------------------
# Side selection (abSelSideVerts)
# ----------------------------------------------------------------------

def side_indices(base_points, axis, base_mid, sel_neg, tol):
    """한쪽 면(또는 전체) 정점 인덱스. sel_neg: True=neg, False=pos, 2=all."""
    n = len(base_points)
    if sel_neg == 2:
        return list(range(n))

    res = []
    for i in range(n):
        offset = base_points[i][axis] - base_mid
        if abs(offset) < tol:
            res.append(i)               # 중앙 정점은 항상 포함
        elif offset > 0.0 and not sel_neg:
            res.append(i)
        elif offset < 0.0 and sel_neg:
            res.append(i)
    return res


# ----------------------------------------------------------------------
# Copy / Add / Subtract (abSMAddSubtractCopyMesh)
# ----------------------------------------------------------------------

def add_sub_copy_points(base_points, source_points, target_points, operation):
    """operation: 0=subtract, 1=add, 2=copy. target 의 새 좌표 배열(오브젝트 공간)."""
    n = len(base_points)
    out = [(*p,) for p in target_points]
    for i in range(n):
        b = base_points[i]
        s = source_points[i]
        t = target_points[i]
        if operation == 2:
            out[i] = (s[0], s[1], s[2])
        else:
            ox = s[0] - b[0]
            oy = s[1] - b[1]
            oz = s[2] - b[2]
            if operation == 0:
                out[i] = (t[0] - ox, t[1] - oy, t[2] - oz)
            else:
                out[i] = (t[0] + ox, t[1] + oy, t[2] + oz)
    return out
