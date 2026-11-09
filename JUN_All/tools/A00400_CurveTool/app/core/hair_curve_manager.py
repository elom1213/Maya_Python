# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00400_CurveTool core - Create > From Hair (v01.32)
#
# 헤어 메시 가닥(shell)마다 **가닥을 관통하는 중심선 커브**를 하나씩 만든다.
# Houdini `0010_hairShrink_LUN_01.hip` 의 foreach 루프(Labs straight_skeleton_3d, 149 가닥 71.5 초)를
# 대체한다. 설계 근거 · 실측은 docs/plans/A00400_CurveTool_hair_centerline_plan.md.
#
# -- 왜 스켈레톤(VDB 수축)이 아니라 링 중심점인가 ------------------------------
# 대상 헤어는 "뿌리 쪽이 열린 쿼드 튜브 + 끝이 삼각형 팬으로 닫힘" 이다(실측 149/149).
# 열린 끝(경계 루프)에서 엣지 홉 단위로 BFS 하면 한 단계 = 튜브의 단면 한 바퀴(링)이고,
# **링 중심을 이으면 중심선**, 첫 링이 뿌리이므로 **방향도 저절로** 정해진다(cv[0] = 뿌리).
# 위상이 고르지 않은 메시는 같은 자리에서 **측지 거리(Dijkstra)를 구간으로 나눠** 같은 일을 한다.
#
# -- 구성 ----------------------------------------------------------------
#   1) 순수 계산부 : 점 [(x,y,z)] + 면 [[v...]] 만 받는다. maya 를 import 하지 않는다
#                    (hython / 일반 파이썬으로도 시험 가능). numpy 도 쓰지 않는다.
#   2) 마야부      : 메시 수집 · om2 로 한 번에 읽기 · 커브 생성(undo 한 스텝).
#
# 길이 값(필터 · 다듬기 · 간격)은 **마야 내부 단위(cm)** 로 받는다. UI 단위 변환은 UI 가 한다.

import heapq
import math
import time


# =====================================================================
# 상수
# =====================================================================

METHOD_AUTO = "auto"
METHOD_RINGS = "rings"
METHOD_GEODESIC = "geodesic"

ROOT_OPEN_END = "open_end"
# (축 인덱스, 부호) - +1 = 그 축 값이 큰 끝이 뿌리
ROOT_AXES = {
    "+y": (1, 1), "-y": (1, -1),
    "+x": (0, 1), "-x": (0, -1),
    "+z": (2, 1), "-z": (2, -1),
}
ROOT_FALLBACK = "+y"

POINTS_COUNT = "count"
POINTS_SPACING = "spacing"
POINTS_PER_RING = "per_ring"

REASON_DEGENERATE = "degenerate"
REASON_SMALL = "small"
REASON_SHORT = "short"
REASON_TRIMMED = "trimmed_out"

REASON_LABELS = {
    REASON_DEGENERATE: "degenerate (too few points / rings)",
    REASON_SMALL: "mesh smaller than the minimum size",
    REASON_SHORT: "curve shorter than the minimum length",
    REASON_TRIMMED: "nothing left after Trim Root / Trim Tip",
}

QUAD_RATIO_AUTO = 0.8     # Auto: 4각형 면 비율이 이 이상이고 열린 끝이 1~2개면 Rings

NAME_DEFAULT = "{mesh}_crv"
GROUP_DEFAULT = "hairCurves_grp"
SOURCE_ATTR = "hairSourceMesh"

_EPS = 1e-9


class HairOptions(object):
    """From Hair 옵션 묶음. 길이 값은 내부 단위(cm)."""

    def __init__(self, method=METHOD_AUTO, slices=30, root=ROOT_OPEN_END,
                 smooth_iterations=10, smooth_strength=0.5,
                 trim_root=0.0, trim_tip=0.0,
                 points_mode=POINTS_COUNT, count=10, spacing=1.0, degree=1,
                 min_size_on=True, min_size=1.0,
                 min_length_on=True, min_length=1.0,
                 include_children=True, name=NAME_DEFAULT,
                 group_on=True, group_name=GROUP_DEFAULT, source_attr=True):
        self.method = method
        self.slices = max(2, int(slices))
        self.root = root
        self.smooth_iterations = max(0, int(smooth_iterations))
        self.smooth_strength = min(1.0, max(0.0, float(smooth_strength)))
        self.trim_root = max(0.0, float(trim_root))
        self.trim_tip = max(0.0, float(trim_tip))
        self.points_mode = points_mode
        self.count = max(2, int(count))
        self.spacing = max(1e-6, float(spacing))
        self.degree = 3 if int(degree) == 3 else 1
        self.min_size_on = bool(min_size_on)
        self.min_size = float(min_size)
        self.min_length_on = bool(min_length_on)
        self.min_length = float(min_length)
        self.include_children = bool(include_children)
        self.name = name or NAME_DEFAULT
        self.group_on = bool(group_on)
        self.group_name = group_name or GROUP_DEFAULT
        self.source_attr = bool(source_attr)


class ShellResult(object):
    """가닥(shell) 하나의 계산 결과. points 가 None 이면 건너뛴 것(reason)."""

    def __init__(self, points=None, reason=None, method=None, warnings=None,
                 length=0.0, diag=0.0, branched=False):
        self.points = points
        self.reason = reason
        self.method = method
        self.warnings = list(warnings or [])
        self.length = length
        self.diag = diag
        self.branched = branched
        # 마야부가 채운다
        self.mesh = None          # 메시 트랜스폼 long name
        self.shell_index = 0
        self.shell_count = 1
        self.curve = None         # 만든 커브 트랜스폼

    @property
    def skipped(self):
        return self.points is None


# =====================================================================
# 순수 계산부 - 위상
# =====================================================================

def split_shells(num_points, faces):
    """면 목록을 연결 성분(shell)으로 나눈다. 반환: [[face index, ...], ...] (첫 면 순서)."""
    parent = list(range(num_points))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for face in faces:
        if not face:
            continue
        r = find(face[0])
        for v in face[1:]:
            b = find(v)
            if b != r:
                parent[b] = r

    order = []
    groups = {}
    for fi, face in enumerate(faces):
        if not face:
            continue
        key = find(face[0])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(fi)
    return [groups[k] for k in order]


def edge_face_counts(faces):
    """엣지(작은 번호, 큰 번호) -> 그 엣지를 쓰는 면 수."""
    counts = {}
    for face in faces:
        n = len(face)
        for i in range(n):
            a, b = face[i], face[(i + 1) % n]
            key = (a, b) if a < b else (b, a)
            counts[key] = counts.get(key, 0) + 1
    return counts


def shell_topology(faces, face_ids, edge_counts=None):
    """가닥 하나의 위상.

    반환 (adj, boundary_loops, quad_ratio, face_adj)
        adj            : {정점: set(이웃 정점)} - 엣지 이웃. 링 BFS · 가지 판정용
        face_adj       : {정점: set(같은 면의 정점)} - 측지 거리용. 엣지만 따라 재면 쿼드 격자에서
                         대각선 방향이 길게 잡혀(둘레를 도는 경로가 과대평가) 끝 찾기가 틀린다
        boundary_loops : [[정점, ...], ...] 면 하나에만 쓰인 엣지들의 연결 성분(= 열린 끝)
        quad_ratio     : 4각형 면 비율
    """
    if edge_counts is None:
        edge_counts = edge_face_counts([faces[fi] for fi in face_ids])

    adj = {}
    face_adj = {}
    boundary = {}
    quads = 0
    for fi in face_ids:
        face = faces[fi]
        n = len(face)
        if n == 4:
            quads += 1
        for v in face:
            face_adj.setdefault(v, set()).update(face)
        for i in range(n):
            a, b = face[i], face[(i + 1) % n]
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
            key = (a, b) if a < b else (b, a)
            if edge_counts.get(key, 0) == 1:
                boundary.setdefault(a, set()).add(b)
                boundary.setdefault(b, set()).add(a)

    loops = []
    seen = set()
    for start in sorted(boundary):
        if start in seen:
            continue
        comp = []
        stack = [start]
        seen.add(start)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in boundary[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        loops.append(comp)

    for v, ns in face_adj.items():
        ns.discard(v)
    quad_ratio = float(quads) / len(face_ids) if face_ids else 0.0
    return adj, loops, quad_ratio, face_adj


def bbox_diagonal(points, verts):
    xs = [points[v][0] for v in verts]
    ys = [points[v][1] for v in verts]
    zs = [points[v][2] for v in verts]
    return math.sqrt((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2
                     + (max(zs) - min(zs)) ** 2)


def _centroid(points, verts):
    n = float(len(verts))
    sx = sy = sz = 0.0
    for v in verts:
        p = points[v]
        sx += p[0]
        sy += p[1]
        sz += p[2]
    return (sx / n, sy / n, sz / n)


def _bfs_hops(adj, seeds):
    """seeds 에서의 엣지 홉 수 {정점: 단계}."""
    level = dict((s, 0) for s in seeds)
    queue = list(seeds)
    i = 0
    while i < len(queue):
        x = queue[i]
        i += 1
        lx = level[x] + 1
        for y in adj[x]:
            if y not in level:
                level[y] = lx
                queue.append(y)
    return level


def _farthest(dist):
    """가장 먼 정점(동률이면 번호가 작은 것 - 결정적)."""
    best = max(dist.values())
    return min(v for v, d in dist.items() if d == best)


def _dijkstra(points, adj, seeds):
    """seeds 에서의 측지 거리(엣지 길이 가중) {정점: 거리}."""
    dist = dict((s, 0.0) for s in seeds)
    heap = [(0.0, s) for s in seeds]
    heapq.heapify(heap)
    while heap:
        d, x = heapq.heappop(heap)
        if d > dist[x]:
            continue
        px = points[x]
        for y in adj[x]:
            py = points[y]
            nd = d + math.sqrt((px[0] - py[0]) ** 2 + (px[1] - py[1]) ** 2 + (px[2] - py[2]) ** 2)
            if nd < dist.get(y, float("inf")):
                dist[y] = nd
                heapq.heappush(heap, (nd, y))
    return dist


def pick_seeds(points, adj, loops, root, metric_adj=None):
    """뿌리 정점 집합을 고른다. 반환 (seeds, warnings).

    root == ROOT_OPEN_END : 열린 끝이 정확히 하나면 그 루프. 아니면 ROOT_FALLBACK(+Y) 규칙으로 대체 + 경고.
    root == 축 규칙       : 열린 끝이 있으면 그중 그 축 끝의 루프, 없으면(닫힌 튜브) 측지 2단계 스윕 양끝 중 그 축 끝 정점.
    metric_adj            : 측지 거리용 이웃(shell_topology 의 face_adj). 없으면 adj.
    """
    warnings = []
    rule = root
    if root == ROOT_OPEN_END:
        if len(loops) == 1:
            return list(loops[0]), warnings
        if len(loops) == 0:
            warnings.append("Root fallback: no open end (closed mesh) -> Highest Y")
        else:
            warnings.append("Root fallback: {0} open ends -> Highest Y".format(len(loops)))
        rule = ROOT_FALLBACK
    elif len(loops) > 2:
        warnings.append("{0} open ends (holes?) - root picked by axis".format(len(loops)))

    axis, sign = ROOT_AXES.get(rule, ROOT_AXES[ROOT_FALLBACK])

    if loops:
        best = max(loops, key=lambda lp: sign * _centroid(points, lp)[axis])
        return list(best), warnings

    # 닫힌 메시 - 2단계 측지 거리 스윕으로 가장 먼 두 끝 A, B.
    # 엣지만 따라 재면(홉 수든 길이 가중이든) 튜브 끝 극점보다 맞은편 링 정점이 더 멀게 나온다 -
    # 쿼드 격자에 대각선이 없어 둘레를 도는 경로가 과대평가된다. 면 대각선을 넣은 이웃으로 잰다.
    madj = metric_adj or adj
    start = min(adj)
    a = _farthest(_dijkstra(points, madj, [start]))
    b = _farthest(_dijkstra(points, madj, [a]))
    chosen = a if sign * points[a][axis] >= sign * points[b][axis] else b
    return [chosen], warnings


# =====================================================================
# 순수 계산부 - 단면(레벨) 나누기
# =====================================================================

def levels_rings(adj, seeds):
    """엣지 홉 단계별 정점 목록 [[...], [...], ...]. 0 단계 = seeds."""
    level = _bfs_hops(adj, seeds)
    out = [[] for _ in range(max(level.values()) + 1)]
    for v, l in level.items():
        out[l].append(v)
    return out


def levels_geodesic(points, adj, seeds, slices, metric_adj=None):
    """seeds 에서의 측지 거리(엣지 길이 가중 Dijkstra)를 slices 구간으로 나눈 정점 목록.

    0 단계 = seeds 자신(뿌리가 열린 끝 그 자리에 오게), 나머지는 거리 (0, D] 를 1..slices 로.
    빈 구간은 버린다.
    """
    dist = _dijkstra(points, metric_adj or adj, seeds)
    seed_set = set(seeds)
    far = max(dist.values())
    bins = [[] for _ in range(slices + 1)]
    bins[0] = list(seeds)
    if far > _EPS:
        for v, d in dist.items():
            if v in seed_set:
                continue
            k = int(d / far * slices - 1e-12) + 1
            bins[min(max(k, 1), slices)].append(v)
    return [b for b in bins if b]


def _components(adj, verts):
    """verts 가 이루는 부분 그래프의 연결 성분."""
    vs = set(verts)
    comps = []
    seen = set()
    for s in verts:
        if s in seen:
            continue
        comp = []
        stack = [s]
        seen.add(s)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if y in vs and y not in seen:
                    seen.add(y)
                    stack.append(y)
        comps.append(comp)
    return comps


def branch_min_levels(level_count):
    """가지로 칠 최소 길이(레벨 수). 이보다 짧은 갈라짐은 끝 위상 잡음이다.

    실데이터(LUN 헤어) 한 가닥은 끝 단계에 **서로 이웃하지 않은 정점 2개**가 남는다(극점이 둘).
    그걸 가지로 세면 거짓 경고가 나므로 길이 기준을 둔다.
    """
    return max(3, int(level_count * 0.1))


def upper_set_splits(adj, levels):
    """레벨이 k 이상인 정점 집합이 **충분히 긴** 둘 이상의 덩어리로 갈라지는 k 가 있는가(= 가지).

    바깥 레벨부터 정점을 넣으며 union-find 로 덩어리를 합친다 - O(V).
    덩어리마다 가장 바깥 레벨을 들고 있어, k 에서의 길이 = (최대 레벨 - k + 1).
    두 번째로 긴 덩어리가 branch_min_levels 이상이면 가지다. 갈라지지 않은 튜브는 늘 덩어리 하나.
    """
    parent = {}
    top = {}          # 루트 -> 그 덩어리의 최대 레벨
    roots = set()
    need = branch_min_levels(len(levels))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for k in range(len(levels) - 1, -1, -1):
        for v in levels[k]:
            parent[v] = v
            top[v] = k
            roots.add(v)
        for v in levels[k]:
            for y in adj[v]:
                if y in parent:
                    a, b = find(v), find(y)
                    if a != b:
                        parent[a] = b
                        top[b] = max(top[a], top[b])
                        roots.discard(a)
        if len(roots) > 1:
            spans = sorted((top[r] - k + 1 for r in roots), reverse=True)
            if spans[1] >= need:
                return True
    return False


def keep_main_trunk(adj, levels):
    """가지가 있으면 **가장 멀리 가는 가지 하나**만 남긴 레벨 목록. 반환 (levels, branched).

    갈라진 가닥에서만 느린 경로(레벨마다 성분 계산)를 탄다 - 보통 가닥은 O(V) 판정 하나로 끝.
    """
    if not upper_set_splits(adj, levels):
        return levels, False

    level_of = {}
    for k, verts in enumerate(levels):
        for v in verts:
            level_of[v] = k

    allowed = set(level_of)
    out = []
    for k, verts in enumerate(levels):
        upper = [v for v in allowed if level_of[v] >= k]
        if not upper:
            break
        comps = _components(adj, upper)
        if len(comps) > 1:
            best = max(comps, key=lambda c: (max(level_of[v] for v in c), len(c)))
            allowed = set(best) | set(v for v in allowed if level_of[v] < k)
        keep = [v for v in verts if v in allowed]
        if keep:
            out.append(keep)
    return out, True


def level_centroids(points, levels):
    return [_centroid(points, verts) for verts in levels if verts]


# =====================================================================
# 순수 계산부 - 꺾은선
# =====================================================================

def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def polyline_length(pts):
    return sum(_dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def smooth_polyline(pts, iterations, strength):
    """끝점 고정 라플라시안 (Houdini smooth1 의 constrained boundary 와 같은 뜻).

    p[i] <- (1-s)*p[i] + s*(p[i-1]+p[i+1])/2  (동시 갱신)
    """
    if iterations <= 0 or strength <= 0.0 or len(pts) < 3:
        return list(pts)
    cur = list(pts)
    s = strength
    for _ in range(iterations):
        nxt = [cur[0]]
        for i in range(1, len(cur) - 1):
            a, p, b = cur[i - 1], cur[i], cur[i + 1]
            nxt.append(((1 - s) * p[0] + s * 0.5 * (a[0] + b[0]),
                        (1 - s) * p[1] + s * 0.5 * (a[1] + b[1]),
                        (1 - s) * p[2] + s * 0.5 * (a[2] + b[2])))
        nxt.append(cur[-1])
        cur = nxt
    return cur


def _cumulative(pts):
    cum = [0.0]
    for i in range(len(pts) - 1):
        cum.append(cum[-1] + _dist(pts[i], pts[i + 1]))
    return cum


def _point_at(pts, cum, s):
    """호 길이 s 의 점."""
    if s <= 0.0:
        return pts[0]
    if s >= cum[-1]:
        return pts[-1]
    lo, hi = 0, len(cum) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if cum[mid] <= s:
            lo = mid
        else:
            hi = mid
    seg = cum[hi] - cum[lo]
    t = (s - cum[lo]) / seg if seg > _EPS else 0.0
    return _lerp(pts[lo], pts[hi], t)


def trim_polyline(pts, root_len, tip_len):
    """뿌리 · 끝에서 호 길이만큼 잘라낸다. 남는 게 없으면 None."""
    if root_len <= 0.0 and tip_len <= 0.0:
        return list(pts)
    cum = _cumulative(pts)
    start, end = root_len, cum[-1] - tip_len
    if end - start <= _EPS:
        return None
    out = [_point_at(pts, cum, start)]
    for i in range(1, len(pts) - 1):
        if start < cum[i] < end:
            out.append(pts[i])
    out.append(_point_at(pts, cum, end))
    return out


def resample_polyline(pts, mode, count=10, spacing=1.0):
    """호 길이 균등 리샘플.

    POINTS_COUNT   : count 점(양끝 포함)
    POINTS_SPACING : 길이를 spacing 에 **가장 가까운 균등 간격**으로 나눈다(구간 수 = round(L / spacing), 최소 1)
    POINTS_PER_RING: 그대로
    """
    if mode == POINTS_PER_RING or len(pts) < 2:
        return list(pts)
    cum = _cumulative(pts)
    total = cum[-1]
    if mode == POINTS_SPACING:
        segs = max(1, int(round(total / spacing)))
    else:
        segs = max(1, int(count) - 1)
    return [_point_at(pts, cum, total * i / segs) for i in range(segs + 1)]


# =====================================================================
# 순수 계산부 - 가닥 하나
# =====================================================================

def resolve_method(method, quad_ratio, loop_count):
    if method != METHOD_AUTO:
        return method
    if quad_ratio >= QUAD_RATIO_AUTO and 1 <= loop_count <= 2:
        return METHOD_RINGS
    return METHOD_GEODESIC


def compute_shell(points, faces, face_ids, opts, edge_counts=None):
    """가닥 하나 -> ShellResult. 필터 · 엔진 선택 · 스무딩 · 다듬기 · 리샘플까지."""
    adj, loops, quad_ratio, face_adj = shell_topology(faces, face_ids, edge_counts)
    verts = list(adj)
    if len(verts) < 4:
        return ShellResult(reason=REASON_DEGENERATE)

    diag = bbox_diagonal(points, verts)
    if diag <= _EPS:
        return ShellResult(reason=REASON_DEGENERATE, diag=diag)
    if opts.min_size_on and diag < opts.min_size:
        return ShellResult(reason=REASON_SMALL, diag=diag)

    method = resolve_method(opts.method, quad_ratio, len(loops))
    seeds, warnings = pick_seeds(points, adj, loops, opts.root, face_adj)

    if method == METHOD_RINGS:
        levels = levels_rings(adj, seeds)
    else:
        levels = levels_geodesic(points, adj, seeds, opts.slices, face_adj)

    levels, branched = keep_main_trunk(adj, levels)
    if branched:
        warnings.append("Branched strand - only the longest branch was traced")

    pts = level_centroids(points, levels)
    if len(pts) < 2:
        return ShellResult(reason=REASON_DEGENERATE, diag=diag, method=method)

    pts = smooth_polyline(pts, opts.smooth_iterations, opts.smooth_strength)
    pts = trim_polyline(pts, opts.trim_root, opts.trim_tip)
    if pts is None:
        return ShellResult(reason=REASON_TRIMMED, diag=diag, method=method)

    length = polyline_length(pts)
    if length <= _EPS:
        return ShellResult(reason=REASON_DEGENERATE, diag=diag, method=method)
    if opts.min_length_on and length < opts.min_length:
        return ShellResult(reason=REASON_SHORT, diag=diag, length=length, method=method)

    pts = resample_polyline(pts, opts.points_mode, opts.count, opts.spacing)
    return ShellResult(points=pts, method=method, warnings=warnings, length=length,
                       diag=diag, branched=branched)


def compute_mesh(points, faces, opts):
    """메시 하나(여러 shell 가능) -> [ShellResult]. shell_index / shell_count 를 채운다."""
    edge_counts = edge_face_counts(faces)
    shells = split_shells(len(points), faces)
    results = []
    for i, face_ids in enumerate(shells):
        res = compute_shell(points, faces, face_ids, opts, edge_counts)
        res.shell_index = i
        res.shell_count = len(shells)
        results.append(res)
    return results


# =====================================================================
# 리포트
# =====================================================================

class HairReport(object):
    """Analyze / Create 결과."""

    def __init__(self):
        self.results = []         # [ShellResult]
        self.meshes = []          # 처리한 메시 트랜스폼
        self.missing = []         # 씬에 없거나 메시가 아닌 입력
        self.elapsed = 0.0
        self.created = False
        self.group = None

    @property
    def made(self):
        return [r for r in self.results if not r.skipped]

    @property
    def skipped(self):
        return [r for r in self.results if r.skipped]

    @property
    def curves(self):
        return [r.curve for r in self.results if r.curve]

    def skipped_meshes(self):
        out = []
        for r in self.skipped:
            if r.mesh and r.mesh not in out:
                out.append(r.mesh)
        return out

    def summary_lines(self, to_ui=None, limit=10):
        """(text, warn) 목록. to_ui = 내부 단위 -> UI 단위 변환 함수."""
        conv = to_ui or (lambda v: v)
        lines = []
        verb = "curves created" if self.created else "curves to create"
        lines.append(("[Hair] {0} shells from {1} meshes - {2} {3}, {4} skipped ({5:.2f}s)".format(
            len(self.results), len(self.meshes), len(self.made), verb, len(self.skipped),
            self.elapsed), False))

        for mesh in self.missing[:limit]:
            lines.append(("[Hair]   Not a mesh / not found: {0}".format(mesh), True))

        by_reason = {}
        for r in self.skipped:
            by_reason.setdefault(r.reason, []).append(r)
        for reason, items in sorted(by_reason.items()):
            names = [_label(r) for r in items]
            more = "" if len(names) <= limit else " ... and {0} more".format(len(names) - limit)
            lines.append(("[Hair]   Skipped - {0} ({1}): {2}{3}".format(
                REASON_LABELS.get(reason, reason), len(items), ", ".join(names[:limit]), more), True))

        if self.made:
            counts = {}
            for r in self.made:
                counts[r.method] = counts.get(r.method, 0) + 1
            lines.append(("[Hair]   Method: Rings {0}, Geodesic {1}".format(
                counts.get(METHOD_RINGS, 0), counts.get(METHOD_GEODESIC, 0)), False))
            lens = sorted(r.length for r in self.made)
            lines.append(("[Hair]   Length: min {0:.2f} / median {1:.2f} / max {2:.2f}".format(
                conv(lens[0]), conv(lens[len(lens) // 2]), conv(lens[-1])), False))

        warned = {}
        for r in self.results:
            for w in r.warnings:
                warned.setdefault(w, []).append(_label(r))
        for w, names in sorted(warned.items()):
            more = "" if len(names) <= limit else " ... and {0} more".format(len(names) - limit)
            lines.append(("[Hair] WARNING  {0} ({1}): {2}{3}".format(
                w, len(names), ", ".join(names[:limit]), more), True))
        return lines


def _short_name(node):
    """'|grp|ns:mesh' -> 'mesh' (경로 · 네임스페이스 제거)."""
    return (node or "").split("|")[-1].split(":")[-1]


def _label(result):
    name = _short_name(result.mesh) or "?"
    if result.shell_count > 1:
        name += " (shell {0})".format(result.shell_index + 1)
    return name


def curve_name(template, mesh, shell_index, shell_count):
    """출력 커브 이름. shell 이 여럿이면 _s01, _s02 …"""
    base = (template or NAME_DEFAULT).replace("{mesh}", _short_name(mesh))
    if shell_count > 1:
        base += "_s{0:02d}".format(shell_index + 1)
    return base


# =====================================================================
# 마야부
# =====================================================================

def _maya():
    import maya.cmds as cmds
    import maya.api.OpenMaya as om
    return cmds, om


def collect_meshes(nodes, include_children=True):
    """입력 노드 -> (메시 셰이프 long name 목록, 못 쓴 입력 목록). 중복 제거, 순서 유지."""
    cmds, _ = _maya()
    shapes = []
    seen = set()
    missing = []

    def add(shape):
        if shape not in seen and not cmds.getAttr(shape + ".intermediateObject"):
            seen.add(shape)
            shapes.append(shape)

    for node in nodes or []:
        found = cmds.ls(node, long=True) or []
        if not found:
            missing.append(node)
            continue
        node = found[0]
        before = len(shapes)
        if cmds.nodeType(node) == "mesh":
            add(node)
        else:
            direct = cmds.listRelatives(node, shapes=True, type="mesh", fullPath=True) or []
            for s in direct:
                add(s)
            if include_children:
                for s in cmds.listRelatives(node, allDescendents=True, type="mesh",
                                            fullPath=True) or []:
                    add(s)
                # allDescendents 는 깊은 것부터 준다 - 바깥 계층이 먼저 오게 경로 깊이 순으로
                tail = sorted(shapes[before:], key=lambda p: (p.count("|"), p))
                shapes[before:] = tail
        if len(shapes) == before:
            # 새 메시가 없다 - 앞선 입력(부모 그룹 등)이 이미 담은 것이 아니면 못 쓴 입력
            if not any(s == node or s.startswith(node + "|") for s in seen):
                missing.append(node)
    return shapes, missing


def read_mesh(shape):
    """om2 로 월드 점 + 면을 한 번에 읽는다. 반환 (points, faces)."""
    _, om = _maya()
    sel = om.MSelectionList()
    sel.add(shape)
    fn = om.MFnMesh(sel.getDagPath(0))
    # MPointArray 는 바로 파이썬 튜플로 옮긴다(배열 수명 함정 회피)
    points = [(p.x, p.y, p.z) for p in fn.getPoints(om.MSpace.kWorld)]
    counts, connects = fn.getVertices()
    counts = list(counts)
    connects = list(connects)
    faces = []
    i = 0
    for c in counts:
        faces.append(connects[i:i + c])
        i += c
    return points, faces


def _transform_of(shape):
    cmds, _ = _maya()
    parent = cmds.listRelatives(shape, parent=True, fullPath=True) or []
    return parent[0] if parent else shape


def analyze(nodes, opts, progress=None):
    """씬을 바꾸지 않고 계산만 한다 -> HairReport."""
    t0 = time.time()
    report = HairReport()
    shapes, report.missing = collect_meshes(nodes, opts.include_children)
    total = len(shapes)
    for i, shape in enumerate(shapes):
        mesh = _transform_of(shape)
        report.meshes.append(mesh)
        points, faces = read_mesh(shape)
        for res in compute_mesh(points, faces, opts):
            res.mesh = mesh
            report.results.append(res)
        if progress:
            progress(i + 1, total, _short_name(mesh))
    report.elapsed = time.time() - t0
    return report


def _ensure_group(name):
    cmds, _ = _maya()
    found = [n for n in (cmds.ls(name, long=True) or []) if cmds.nodeType(n) == "transform"]
    if found:
        return found[0]
    return cmds.ls(cmds.group(empty=True, name=name, world=True), long=True)[0]


def create_curves(nodes, opts, progress=None, create_progress=None):
    """analyze + 커브 생성. 호출자가 undo_chunk 로 감싼다(한 스텝).

    progress        : 계산 단계 진행 콜백
    create_progress : 생성 단계 진행 콜백
    """
    cmds, _ = _maya()
    report = analyze(nodes, opts, progress)
    t0 = time.time() - report.elapsed
    made = report.made
    report.created = True
    if not made:
        report.elapsed = time.time() - t0
        return report

    for i, res in enumerate(made):
        name = curve_name(opts.name, res.mesh, res.shell_index, res.shell_count)
        pts = res.points
        if opts.degree == 3 and len(pts) >= 3:
            crv = cmds.curve(degree=3, editPoint=pts, name=name)
        else:
            crv = cmds.curve(degree=1, point=pts, name=name)
        shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
        if shapes:
            cmds.rename(shapes[0], _short_name(crv) + "Shape")
        if opts.source_attr:
            cmds.addAttr(crv, longName=SOURCE_ATTR, dataType="string")
            cmds.setAttr(crv + "." + SOURCE_ATTR, res.mesh, type="string")
        res.curve = cmds.ls(crv, long=True)[0]
        if create_progress:
            create_progress(i + 1, len(made), _short_name(crv))

    if opts.group_on:
        grp = _ensure_group(opts.group_name)
        # parent 반환값은 짧은 이름이라 겹칠 수 있다 - UUID 로 새 경로를 되찾는다
        uuids = [cmds.ls(r.curve, uuid=True)[0] for r in made]
        cmds.parent([r.curve for r in made], grp)
        for r, uid in zip(made, uuids):
            r.curve = (cmds.ls(uid, long=True) or [r.curve])[0]
        report.group = grp

    cmds.select([r.curve for r in made], replace=True)
    report.elapsed = time.time() - t0
    return report
