# -*- coding: utf-8 -*-
"""
snap_core - 최근접 정점/표면 스냅 + 기하학적 대칭화(토폴로지 무관) 순수 수학.

Houdini point wrangle 의 nearpoint() 스냅을 옮긴 모듈.
  - 0번 입력(비대칭, 수정 대상) 의 각 정점 P 를
  - 1번 입력(대칭 레퍼런스) 의 가장 가까운 정점 위치로 옮긴다.

abSymMesh 의 sym_core 와 달리 **정점 인덱스 대응(대칭 토폴로지)을 요구하지 않는다.**
공간 격자(uniform grid) 해시로 최근접 정점을 O(1) 근처로 찾는다(scipy 비의존).

cmds/OpenMaya 비의존(순수 좌표 리스트 연산). 씬 접근은 mesh_io 가 담당한다.
표면 최근접점(closest-surface) 모드는 MFnMesh.getClosestPoint 가 필요해 mesh_io 에 둔다.
"""

import math


_EPS = 1e-12


def _finite(p):
    """세 좌표가 모두 유한(NaN/inf 아님)이면 True. 깨진 정점 방어용."""
    return math.isfinite(p[0]) and math.isfinite(p[1]) and math.isfinite(p[2])


def count_invalid(points):
    """NaN/inf 좌표를 가진(깨진) 정점 수를 센다."""
    return sum(1 for p in points if not _finite(p))


# ----------------------------------------------------------------------
# 미러(reflect) — sym_core 와 동일 규칙(axis 0/1/2 = X/Y/Z 성분을 mid 기준 반전)
# ----------------------------------------------------------------------

def reflect(p, axis, mid):
    """평면(축 성분 = mid) 기준으로 p 의 해당 축 성분만 반전한다."""
    q = [p[0], p[1], p[2]]
    q[axis] = 2.0 * mid - q[axis]
    return (q[0], q[1], q[2])


# ----------------------------------------------------------------------
# 공간 격자(uniform grid) 최근접 정점 탐색
# ----------------------------------------------------------------------

def build_grid(points, target_per_cell=4):
    """points 를 균일 격자에 버킷팅한 인덱스 구조를 만든다.

    cell 크기는 bounding box 부피와 정점 수로 대략적인 평균 간격에 맞춘다.
    Returns:
        {"grid": {(ix,iy,iz): [idx,...]}, "cell": float, "points": points}
    """
    empty = {"grid": {}, "cell": 1.0, "points": points,
             "imin": (0, 0, 0), "imax": (0, 0, 0)}
    if not points:
        return empty

    # NaN/inf 정점은 격자 계산/버킷팅에서 제외(인덱스는 보존되어 후보에서만 빠진다).
    fin = [p for p in points if _finite(p)]
    if not fin:
        return empty

    xs = [p[0] for p in fin]
    ys = [p[1] for p in fin]
    zs = [p[2] for p in fin]
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)

    # cell 은 '가장 긴 변' 기준으로 잡는다. (부피 기준은 평면/박판 메시에서 한 축이
    # 0 이 되어 cell 이 미세해지고 셸 탐색이 폭발하므로 쓰지 않는다.)
    extent = max(dx, dy, dz)
    n = len(fin)
    if extent <= _EPS:
        # 모든 점이 거의 일치 -> 단일 셀.
        cell = 1.0
    else:
        # 가장 긴 축을 대략 n^(1/3) 칸으로 나눠 셀당 점 수가 과하지 않게 한다.
        divisions = max(1.0, round((n / max(1.0, target_per_cell)) ** (1.0 / 3.0)))
        cell = extent / divisions
    if not (cell > _EPS):  # NaN/inf 방어
        cell = 1.0

    inv = 1.0 / cell
    grid = {}
    for i, p in enumerate(points):
        if not _finite(p):
            continue  # 깨진 정점은 후보에서 제외.
        key = (
            int(math.floor(p[0] * inv)),
            int(math.floor(p[1] * inv)),
            int(math.floor(p[2] * inv)),
        )
        grid.setdefault(key, []).append(i)

    if not grid:
        return empty

    # 점유 셀 인덱스 범위(셸 탐색 상한 계산용).
    keys = list(grid.keys())
    imin = (min(k[0] for k in keys), min(k[1] for k in keys), min(k[2] for k in keys))
    imax = (max(k[0] for k in keys), max(k[1] for k in keys), max(k[2] for k in keys))

    return {"grid": grid, "cell": cell, "points": points,
            "imin": imin, "imax": imax}


def _shell_keys(center, r):
    """center 셀에서 체비셰프 거리 == r 인 셀 키들을 생성한다."""
    cx, cy, cz = center
    if r == 0:
        yield (cx, cy, cz)
        return
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            for dz in range(-r, r + 1):
                # 표면(껍질)만: 한 성분이라도 |·| == r 이어야 한다.
                if max(abs(dx), abs(dy), abs(dz)) != r:
                    continue
                yield (cx + dx, cy + dy, cz + dz)


def nearest_index(g, q):
    """질의점 q 에 가장 가까운 정점의 인덱스를 반환한다(없으면 -1).

    셀 껍질을 r=0 부터 넓혀가며 탐색하고, 다음 껍질의 최소 가능 거리(r*cell)가
    현재 최단거리보다 멀어지면 종료한다(정확한 최근접 보장).
    """
    grid = g["grid"]
    cell = g["cell"]
    pts = g["points"]
    if not grid:
        return -1
    if not _finite(q):
        return -1   # 질의점이 깨졌으면 매칭 불가.

    inv = 1.0 / cell
    center = (
        int(math.floor(q[0] * inv)),
        int(math.floor(q[1] * inv)),
        int(math.floor(q[2] * inv)),
    )

    best = -1
    best_d2 = float("inf")
    r = 0
    # 셸 반경 상한: 질의 셀에서 점유 범위(imin..imax) 양 끝까지의 최대 체비셰프 거리.
    # 이 반경이면 모든 점유 셀을 덮으므로 best 가 반드시 채워지고 종료 조건이 성립한다.
    imin = g["imin"]
    imax = g["imax"]
    max_r = max(
        max(abs(center[a] - imin[a]), abs(center[a] - imax[a]))
        for a in range(3)
    ) + 1
    while r <= max_r:
        for key in _shell_keys(center, r):
            bucket = grid.get(key)
            if not bucket:
                continue
            for i in bucket:
                p = pts[i]
                ddx = p[0] - q[0]
                ddy = p[1] - q[1]
                ddz = p[2] - q[2]
                d2 = ddx * ddx + ddy * ddy + ddz * ddz
                if d2 < best_d2:
                    best_d2 = d2
                    best = i
        if best >= 0:
            # 다음 껍질(r+1)의 최소 가능 거리는 r*cell. 그보다 가까우면 확정.
            reach = r * cell
            if best_d2 <= reach * reach:
                break
        r += 1

    return best


# ----------------------------------------------------------------------
# 스냅 / 대칭화
# ----------------------------------------------------------------------

def _tick_step(total):
    """진행 콜백 호출 간격(전체를 약 200등분, 최소 1)."""
    return max(1, total // 200)


def snap_to_nearest_vertex(src_points, ref_points, indices=None, progress=None):
    """src 의 각 정점을 ref 의 최근접 '정점' 위치로 옮긴 새 좌표 리스트를 반환한다.

    Houdini: @P = point(1, "P", nearpoint(1, @P)) 와 동일.

    Args:
        src_points: 수정 대상 좌표 리스트.
        ref_points: 대칭 레퍼런스 좌표 리스트.
        indices: 옮길 정점 인덱스(None 이면 전체).

    Returns:
        (new_points, moved_count)
    """
    out = [tuple(p) for p in src_points]
    if not ref_points:
        return out, 0

    g = build_grid(ref_points)
    targets = list(range(len(out))) if indices is None else list(indices)
    total = len(targets)
    step = _tick_step(total)

    moved = 0
    for k, i in enumerate(targets):
        j = nearest_index(g, out[i])
        if j >= 0:
            out[i] = tuple(ref_points[j])
            moved += 1
        if progress is not None and k % step == 0:
            progress(k, total)
    if progress is not None:
        progress(total, total)
    return out, moved


def mirror_one_side_points(points, axis, mid, positive_source, tol=1e-6,
                           progress=None):
    """한쪽 면을 반대쪽에 그대로 미러해 완전 대칭으로 만든다(토폴로지 무관).

    소스 면(유지)을 반대 면(덮어씀)으로 반사 복사한다. Maya Symmetrize/Mirror 처럼
    한쪽 모양이 양쪽에 동일하게 들어가 변화가 확실히 보인다.

    Args:
        points: 대상 좌표 리스트.
        axis: 미러 축 인덱스(0/1/2 = X/Y/Z).
        mid: 대칭 평면의 축 성분값(중심).
        positive_source: True 면 +side(축 성분 > mid)를 소스로, -side 를 덮어씀.
                         False 면 그 반대.
        tol: 평면 위(중앙) 정점 판정 허용 오차.

    Returns:
        대칭화된 좌표 리스트.
    """
    out = [tuple(p) for p in points]
    if not points:
        return out

    # 소스 면 정점만 모아 격자를 만든다.
    src_pts = []
    for p in points:
        d = p[axis] - mid
        if (d > tol) if positive_source else (d < -tol):
            src_pts.append((p[0], p[1], p[2]))

    if not src_pts:
        # 소스 면에 정점이 없다(원점이 메시 바깥). 변경 없이 반환.
        return out

    g = build_grid(src_pts)

    total = len(points)
    step = _tick_step(total)
    for i, p in enumerate(points):
        if progress is not None and i % step == 0:
            progress(i, total)
        if not _finite(p):
            continue  # 깨진 정점은 그대로 둔다.
        d = p[axis] - mid
        if abs(d) <= tol:
            # 평면 위 정점은 평면으로 스냅.
            q = [p[0], p[1], p[2]]
            q[axis] = mid
            out[i] = (q[0], q[1], q[2])
            continue
        is_src = (d > tol) if positive_source else (d < -tol)
        if is_src:
            continue  # 소스 면은 유지.
        # 대상 면: 반사점의 최근접 소스 정점을 다시 반사해 대입.
        rp = reflect(p, axis, mid)
        j = nearest_index(g, rp)
        if j >= 0:
            out[i] = reflect(src_pts[j], axis, mid)

    if progress is not None:
        progress(total, total)
    return out


def mirror_deformation(base_points, deformed_points, axis, mid,
                       onto_deformed=False, progress=None):
    """변형(deformed - base)을 미러 평면 건너편으로 반사해 적용한다.

    Houdini Attribute Wrangle(nearpoint 기반) 이식:
      각 정점 i 에 대해 base 에서 i 의 '미러 위치'에 가장 가까운 정점 m 을 찾고,
      m 의 변형 오프셋(deformed[m] - base[m])을 축 기준으로 반사해 적용한다.
      대칭 토폴로지가 아니어도 nearpoint 로 미러 짝을 찾는다.

    base 와 deformed 는 **같은 토폴로지(같은 정점 수/순서)** 여야 한다
    (오프셋을 인덱스로 읽으므로).

    Args:
        base_points: 입력0(원본) 좌표.
        deformed_points: 입력1(변형) 좌표. base 와 길이 동일.
        axis: 미러 축(0/1/2 = X/Y/Z).
        mid: 대칭 평면의 축 성분값.
        onto_deformed: False 면 base 에 적용(반사만 = VEX 그대로, 원래 변형 쪽은 base 로 복귀),
                       True  면 deformed 에 적용(원래 변형 유지 + 반대쪽에 반사 = 대칭화).

    Returns:
        결과 좌표 리스트.
    """
    if len(base_points) != len(deformed_points):
        raise ValueError(
            "Base and Deformed must share topology "
            "({0} vs {1} verts).".format(
                len(base_points), len(deformed_points)))

    g = build_grid(base_points)
    out = []
    total = len(base_points)
    step = _tick_step(total)
    for i, bp in enumerate(base_points):
        if progress is not None and i % step == 0:
            progress(i, total)
        anchor = deformed_points[i] if onto_deformed else bp
        mp = reflect(bp, axis, mid)
        m = nearest_index(g, mp)
        if m < 0:
            out.append(tuple(anchor))
            continue
        b = base_points[m]
        d = deformed_points[m]
        if not (_finite(b) and _finite(d) and _finite(anchor)):
            out.append(tuple(anchor))
            continue
        # 오프셋은 '방향'이라 위치 반사(2*mid-..)가 아니라 축 성분 부호만 반전.
        off = [d[0] - b[0], d[1] - b[1], d[2] - b[2]]
        off[axis] = -off[axis]
        out.append((anchor[0] + off[0], anchor[1] + off[1], anchor[2] + off[2]))
    if progress is not None:
        progress(total, total)
    return out


def apply_mirrored_offsets(base_points, deformed_points, offsets, axis,
                           onto_deformed=False):
    """이미 구한 per-vertex 미러 오프셋을 축 반사해 적용한다.

    Closest Surface 경로용 공통 적용기. offsets[i] = 정점 i 의 미러 위치에서
    구한(표면 보간된) 변형 오프셋. 오프셋의 축 성분만 부호 반전 후 적용한다.

    Args:
        base_points / deformed_points: 동일 토폴로지 좌표.
        offsets: 정점별 미러 오프셋 [(dx,dy,dz), ...].
        axis: 미러 축(0/1/2).
        onto_deformed: False 면 base, True 면 deformed 에 적용.

    Returns:
        결과 좌표 리스트.
    """
    out = []
    for i, b in enumerate(base_points):
        anchor = deformed_points[i] if onto_deformed else b
        o = offsets[i]
        if not (_finite(o) and _finite(anchor)):
            out.append(tuple(anchor))
            continue
        oo = [o[0], o[1], o[2]]
        oo[axis] = -oo[axis]
        out.append((anchor[0] + oo[0], anchor[1] + oo[1], anchor[2] + oo[2]))
    return out


def make_symmetric_points(points, axis, mid, progress=None):
    """토폴로지 무관 기하학적 대칭화.

    각 정점 p 를 p 와 (미러 집합에서 p 에 가장 가까운 점)의 평균으로 옮긴다.
    원본 토폴로지를 유지한 채 거의 대칭인 좌표를 만든다.

    Args:
        points: 대상 좌표 리스트.
        axis: 미러 축 인덱스(0/1/2 = X/Y/Z).
        mid: 대칭 평면의 축 성분값(중심).

    Returns:
        대칭화된 좌표 리스트.
    """
    if not points:
        return []

    mirrored = [reflect(p, axis, mid) for p in points]
    g = build_grid(mirrored)

    out = []
    total = len(points)
    step = _tick_step(total)
    for i, p in enumerate(points):
        if progress is not None and i % step == 0:
            progress(i, total)
        if not _finite(p):
            out.append(tuple(p))   # 깨진 정점은 그대로 둔다.
            continue
        j = nearest_index(g, p)
        m = mirrored[j] if j >= 0 else reflect(p, axis, mid)
        out.append((
            (p[0] + m[0]) * 0.5,
            (p[1] + m[1]) * 0.5,
            (p[2] + m[2]) * 0.5,
        ))
    if progress is not None:
        progress(total, total)
    return out
