# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-12
# A00275_skinTool_V01 - Expand Bind (저장한 버텍스 집합을 저장한 조인트들에 바인드)
#
# Kangaroo 의 SkinCluster > ClosestExpand 를 대신하는 기능이다. 입술/눈처럼 **중심에서
# 원을 그리며 밖으로 퍼지는 엣지 루프** 위에 조인트를 죽 늘어놓고 바인드할 때, 조인트
# 사이의 웨이트가 "엣지 개수와 거리에 따라" 고르게 깔리도록 하는 것이 목적이다.
#
# ## Kangaroo ClosestExpand 가 고르지 않았던 이유
#
# Kangaroo 는 조인트들을 잇는 임시 커브의 최근접 버텍스를 찾아 시작점으로 삼고, 조인트
# 사이 경로를 **토폴로지 상의 등간격**(경로 인덱스 / 경로 길이)으로 섞은 뒤, 바깥으로는
# **루프 개수**(iExpandedFullWeightLoops / iExpandedFadeOutLoops)만큼 b-spline 으로
# 감쇠시킨다. 즉 실제 엣지 길이를 보지 않는다. 엣지 간격이 조금만 불규칙해도(대개
# 그렇다) 조인트 사이 웨이트가 한쪽으로 쏠린다.
#
# ## 이 모듈의 방식
#
# 1. 조인트마다 **저장된 버텍스 집합 안에서** 가장 가까운 버텍스를 시작점(seed)으로 잡는다.
# 2. seed 에서 각 버텍스까지의 거리를 낸다(Falloff mode):
#      surface  : 저장된 집합 안의 엣지를 따라가는 **측지 거리**(엣지 길이 누적, Dijkstra)
#      topology : 엣지 **개수**(BFS 홉 수) — 길이를 무시하고 루프 수로만 세고 싶을 때
#      volume   : 시작점에서의 **직선 거리**(토폴로지 무시 — 틈 건너로도 번진다)
# 3. 거리/반경 을 falloff 커브에 넣어 조인트별 원시 가중치를 얻고,
# 4. 버텍스마다 조인트들 사이에서 **정규화**한다(합 = 1).
#
# 4번이 핵심이다. 선형 커브라면 두 조인트 사이 버텍스의 웨이트는 정확히
# `d2/(d1+d2)` 가 되어, 엣지 간격이 불규칙해도 **거리에 비례해 고르게** 분배된다.
#
# ## Edge loop 를 함께 주면 (권장)
#
# 조인트가 앉아 있는 **엣지 루프**를 같이 저장하면 계산이 두 방향으로 분리된다.
#
#   루프 **따라**  : 조인트 사이 분배 (루프 호 길이로만 잰다)
#   루프 **바깥**  : 이 조인트 집합이 그 버텍스를 얼마나 가져가는지(amount)
#
# 루프 없이 영역 전체를 한 거리로 재면, 루프에서 멀어질수록 "바깥으로 나간 거리"가
# 반경을 잡아먹어 **먼 조인트의 falloff 가 먼저 0 이 된다.** 그러면 비율이 부드럽게
# 섞이지 않고 1.0 / 0.5 로 딱딱하게 갈라진다(격자 11x7 실측):
#
#   루프 줄      1.000  0.900  0.800  0.700  0.600  0.500   <- 원하는 모양
#   루프+3 줄    1.000  1.000  1.000  1.000  0.750  0.500   <- 루프 없이
#   루프+3 줄    1.000  0.900  0.800  0.700  0.600  0.500   <- 루프를 주면
#
# 루프를 주면 각 버텍스는 **가장 가까운 루프 버텍스(anchor)** 의 분배 비율을 그대로
# 물려받고, 루프에서 떨어진 거리는 `Across width` 로 amount 만 줄인다. 그래서 밴드
# 어디서나 루프와 같은 비율이 유지된다.
#
# ## Blend
#
# 저장된 버텍스가 **다른 조인트(대상 조인트 외)** 에 이미 바인드돼 있으면, 이번에 넣는
# 조인트들이 가져갈 총량을 `Blend * coverage` 로 제한한다(기존 인플루언스는 나머지를
# 비율대로 유지). coverage 는 `min(1, 조인트별 커브값의 합)` 이라 조인트 사이에서는 1
# 이고(=Blend 그대로) 바깥 끝으로 갈수록 떨어진다 — 그래서 최댓값은 정확히 Blend 다.
# 다른 인플루언스가 없는 버텍스는 남길 곳이 없으므로 Blend 와 무관하게 총량 1 이 된다
# (합이 1 이 아니면 마야가 어차피 다시 정규화한다).
#
# UI 비의존: 위젯에서 읽은 값만 받는다. (app/core <-> app/ui 분리)

import heapq

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from Framework.core import maya_shape
from tools.A00275_skinTool_V01.app.core import falloff


# Falloff mode — ref/ref_01.png 의 "Falloff mode" 콤보에 대응.
MODE_SURFACE = "surface"
MODE_TOPOLOGY = "topology"
MODE_VOLUME = "volume"

MODES = (MODE_SURFACE, MODE_TOPOLOGY, MODE_VOLUME)

# 반경이 0 이면 seed 만 남으므로 이보다 작은 값은 거부한다.
MIN_RADIUS = 1e-6


# =========================
# 이름/노드 헬퍼
# =========================

def _long(name):
    found = cmds.ls(name, l=True) or []
    return found[0] if found else None


def _leaf(name):
    return name.split("|")[-1].split(":")[-1]


def mesh_transform(node):
    """메시/셰이프/컴포넌트 이름 -> 트랜스폼 롱네임. 메시가 아니면 None."""
    if not node:
        return None
    node = node.split(".")[0]
    node = _long(node)
    if node is None:
        return None
    if cmds.objectType(node) == "mesh":
        parents = cmds.listRelatives(node, p=True, f=True) or []
        return parents[0] if parents else node
    shapes = cmds.listRelatives(node, s=True, type="mesh", f=True) or []
    return node if shapes else None


def skincluster_of(mesh):
    if not mesh or not cmds.objExists(mesh):
        return None
    skins = cmds.ls(cmds.listHistory(mesh, pdo=True) or [], type="skinCluster")
    return skins[0] if skins else None


def shape_of(node, skin=None):
    """대상의 **진짜 메시 셰이프** 롱네임.

    `MDagPath.extendToShape()` 를 쓰지 않는다. 그것은 "첫 번째 non-intermediate 셰이프"
    를 고르는데, 한 트랜스폼 아래에 셰이프가 여럿이면(blendShape 타겟 셰이프를 같은
    트랜스폼에 정리해 둔 리그, 머지/임포트 잔재 등) **스킨이 걸리지 않은 셰이프**를
    집는다. 그 경로로 `MFnSkinCluster.getWeights` 를 부르면
    `(kInvalidParameter): Object is incompatible with this method` 로 죽는다.

    그래서 skinCluster 가 있으면 **그 디포머가 실제로 변형하는 셰이프**를 고른다.
    구현은 공용 헬퍼(`Framework.core.maya_shape`)에 있다 — 같은 함정을 여러 툴이
    공유하므로 한 곳에서 처리한다.
    """
    if not node:
        return None
    return maya_shape.shape_path(node, deformer=skin or skincluster_of(node),
                                 type_="mesh")


def vertex_count(node):
    """메시의 버텍스 수. **셰이프 기준**으로 센다.

    셰이프가 여럿인 트랜스폼에 `polyEvaluate` 를 걸면 정수가 아니라 요약 문자열이
    돌아와 뒤에서 조용히 터진다.
    """
    return maya_shape.vertex_count(node, deformer=skincluster_of(node))


# =========================
# 선택 파싱 (저장 버튼이 쓰는 입력)
# =========================

def parse_selected_vertices():
    """현재 선택에서 (메시 롱네임, 정렬된 버텍스 id 리스트) 를 뽑는다.

    버텍스가 아니라 엣지/페이스를 골라도 버텍스로 변환한다. 메시를 통째로 고르면
    그 메시의 **모든** 버텍스를 담는다(그 경우가 실수라면 개수가 로그에 보인다).
    """
    sel = cmds.ls(sl=True, l=True, fl=False) or []
    if not sel:
        raise ValueError("Nothing selected. Select the vertices to bind.")

    comps = [s for s in sel if "." in s]
    wholes = [s for s in sel if "." not in s and mesh_transform(s)]

    if comps:
        meshes = {mesh_transform(c) for c in comps}
        meshes.discard(None)
        if len(meshes) > 1:
            raise ValueError(
                "Components from {0} meshes are selected. Pick one mesh at a "
                "time.".format(len(meshes)))
        mesh = meshes.pop()
        verts = cmds.ls(cmds.polyListComponentConversion(comps, tv=True),
                        fl=True) or []
        ids = sorted({int(v.split("[")[1].split("]")[0]) for v in verts})
        if not ids:
            raise ValueError("The selection has no vertices.")

        # 컴포넌트가 **셰이프 이름**으로 왔다면(한 트랜스폼에 셰이프가 여럿일 때 마야가
        # 그렇게 준다) 그 셰이프를 그대로 들고 간다 — 어느 셰이프의 버텍스인지가 곧
        # 어디에 바인드할지다. 트랜스폼 이름이면 예전처럼 트랜스폼을 돌려준다.
        owners = {c.split(".")[0] for c in comps}
        if len(owners) == 1:
            owner = _long(owners.pop())
            if owner and cmds.objectType(owner) == "mesh":
                return owner, ids
        return mesh, ids

    if wholes:
        if len(wholes) > 1:
            raise ValueError("Select one mesh (or its vertices), not {0}.".format(
                len(wholes)))
        mesh = mesh_transform(wholes[0])
        return mesh, list(range(vertex_count(mesh)))

    raise ValueError("No mesh in the selection. Select vertices of a mesh.")


def parse_selected_loop():
    """현재 선택에서 (메시, **순서대로 정렬된** 루프 버텍스 id, 닫힘 여부) 를 뽑는다.

    엣지 루프를 골라도 되고(권장) 버텍스를 골라도 된다 — 어느 쪽이든 버텍스로 바꾼 뒤
    그 안에서의 메시 인접만으로 줄을 세운다. 갈래가 지거나(3갈래 이상) 끊겨 있으면
    루프로 볼 수 없으므로 거절한다.
    """
    mesh, ids = parse_selected_vertices()
    order, closed = order_loop(mesh, ids)
    return mesh, order, closed


def order_loop(mesh, ids):
    """루프 버텍스 집합을 한 줄로 세운다. (정렬된 id, 닫힘 여부)"""
    ids = sorted({int(v) for v in (ids or [])})
    if len(ids) < 2:
        raise ValueError("An edge loop needs at least 2 vertices.")

    adj = adjacency(mesh, set(ids))
    ends = [v for v in ids if len(adj[v]) == 1]
    forks = [v for v in ids if len(adj[v]) > 2]
    loose = [v for v in ids if not adj[v]]

    if forks:
        raise ValueError(
            "That is not a single edge loop - {0} vertex(es) branch off (3+ "
            "neighbours).".format(len(forks)))
    if loose:
        raise ValueError(
            "That is not a single edge loop - {0} vertex(es) are not connected "
            "to it.".format(len(loose)))
    if len(ends) > 2:
        raise ValueError("That is not a single edge loop (too many open ends).")

    closed = not ends
    start = ids[0] if closed else min(ends)

    order = [start]
    previous = None
    current = start
    while True:
        nxt = [v for v in adj[current] if v != previous]
        if not nxt:
            break
        following = nxt[0]
        if following == start:
            break
        order.append(following)
        previous, current = current, following

    if len(order) != len(ids):
        raise ValueError(
            "That is not a single edge loop - it is made of more than one "
            "piece ({0} of {1} vertices are connected).".format(
                len(order), len(ids)))
    return order, closed


def parse_selected_joints():
    """현재 선택에서 조인트(또는 트랜스폼) 롱네임 목록을 뽑는다.

    바인드 인플루언스가 될 수 있는 것은 joint 만이 아니므로(트랜스폼도 가능) 타입을
    joint 로 강제하지 않는다. 셰이프/컴포넌트는 걸러 낸다.
    """
    sel = cmds.ls(sl=True, l=True) or []
    joints = []
    for node in sel:
        if "." in node:
            continue
        if not cmds.objectType(node, isAType="transform"):
            continue
        if mesh_transform(node) and cmds.nodeType(node) != "joint":
            # 메시 트랜스폼은 인플루언스로 쓰지 않는다.
            continue
        joints.append(node)
    if not joints:
        raise ValueError("No joints selected. Select the joints to bind to.")
    return joints


# =========================
# 메시 정보 (위치 / 인접)
# =========================

def _shape_dag(node):
    """셰이프 롱네임 -> MDagPath (extendToShape 로 추측하지 않는다 — shape_of 참고)."""
    shape = shape_of(node)
    if shape is None:
        raise ValueError("'{0}' has no polygon mesh shape.".format(_leaf(node or "")))
    sel = om.MSelectionList()
    sel.add(shape)
    return sel.getDagPath(0)


def _mesh_fn(mesh):
    dag = _shape_dag(mesh)
    return om.MFnMesh(dag), dag


def world_points(mesh):
    """메시 전체 버텍스의 월드 좌표(MPointArray)."""
    fn, _dag = _mesh_fn(mesh)
    return fn.getPoints(om.MSpace.kWorld)


def adjacency(mesh, allowed):
    """저장된 집합 **안에서만** 연결된 인접 리스트 {vid: [vid, ...]}.

    면 루프의 연속한 두 정점이 곧 엣지다. 집합 밖으로는 잇지 않으므로 falloff 가
    지정한 영역을 넘어 새지 않는다(입술 안쪽/바깥쪽이 붙어버리는 사고 방지).
    """
    fn, _dag = _mesh_fn(mesh)
    counts, indices = fn.getVertices()

    adj = {v: set() for v in allowed}
    start = 0
    for count in counts:
        face = indices[start:start + count]
        start += count
        for k in range(count):
            a = face[k]
            b = face[(k + 1) % count]
            if a in adj and b in adj:
                adj[a].add(b)
                adj[b].add(a)
    return adj


# =========================
# 거리 (Falloff mode)
# =========================

def _dijkstra(adj, points, seed, limit):
    """엣지 길이를 누적한 측지 거리. limit 를 넘으면 더 뻗지 않는다."""
    dist = {seed: 0.0}
    queue = [(0.0, seed)]
    while queue:
        d, v = heapq.heappop(queue)
        if d > dist.get(v, float("inf")):
            continue
        pv = points[v]
        for nb in adj.get(v, ()):
            pn = points[nb]
            step = ((pn.x - pv.x) ** 2 + (pn.y - pv.y) ** 2 +
                    (pn.z - pv.z) ** 2) ** 0.5
            nd = d + step
            if nd > limit:
                continue
            if nd < dist.get(nb, float("inf")):
                dist[nb] = nd
                heapq.heappush(queue, (nd, nb))
    return dist


def _bfs(adj, seed, limit):
    """엣지 개수(홉 수) 거리. limit 홉까지만."""
    dist = {seed: 0.0}
    frontier = [seed]
    step = 0
    while frontier and step < limit:
        step += 1
        nxt = []
        for v in frontier:
            for nb in adj.get(v, ()):
                if nb not in dist:
                    dist[nb] = float(step)
                    nxt.append(nb)
        frontier = nxt
    return dist


def _dijkstra_multi(mode, adj, points, seeds, limit):
    """여러 시작점에서 동시에 퍼지는 거리 + **어느 시작점에서 왔는지**(anchor).

    루프 전체를 시작점으로 주면 버텍스마다 "루프에서 얼마나 떨어졌나 / 가장 가까운
    루프 버텍스는 어디인가" 를 한 번에 얻는다. 루프 버텍스별로 따로 돌릴 필요가 없다.
    """
    dist = {}
    anchor = {}
    queue = []
    for seed in seeds:
        dist[seed] = 0.0
        anchor[seed] = seed
        queue.append((0.0, seed))
    heapq.heapify(queue)

    step_is_length = mode != MODE_TOPOLOGY

    while queue:
        d, v = heapq.heappop(queue)
        if d > dist.get(v, float("inf")):
            continue
        pv = points[v]
        for nb in adj.get(v, ()):
            if step_is_length:
                pn = points[nb]
                step = ((pn.x - pv.x) ** 2 + (pn.y - pv.y) ** 2 +
                        (pn.z - pv.z) ** 2) ** 0.5
            else:
                step = 1.0
            nd = d + step
            if nd > limit:
                continue
            if nd < dist.get(nb, float("inf")):
                dist[nb] = nd
                anchor[nb] = anchor[v]
                heapq.heappush(queue, (nd, nb))
    return dist, anchor


def _loop_arcs(mode, points, order, closed):
    """루프 버텍스의 호 위치 {vid: s} 와 전체 길이. topology 모드는 한 칸을 1 로 센다."""
    arcs = {}
    total = 0.0
    arcs[order[0]] = 0.0
    for i in range(1, len(order)):
        if mode == MODE_TOPOLOGY:
            step = 1.0
        else:
            a, b = points[order[i - 1]], points[order[i]]
            step = ((b.x - a.x) ** 2 + (b.y - a.y) ** 2 +
                    (b.z - a.z) ** 2) ** 0.5
        total += step
        arcs[order[i]] = total

    if closed:
        # 마지막 -> 처음 을 잇는 칸까지 더해야 둘레가 된다(감아 도는 거리 계산에 쓴다).
        if mode == MODE_TOPOLOGY:
            total += 1.0
        else:
            a, b = points[order[-1]], points[order[0]]
            total += ((b.x - a.x) ** 2 + (b.y - a.y) ** 2 +
                      (b.z - a.z) ** 2) ** 0.5
    return arcs, total


def _arc_distance(s1, s2, total, closed):
    """루프 위 두 지점 사이 거리. 닫힌 루프면 짧은 쪽으로 감아 돈다."""
    gap = abs(s1 - s2)
    if closed and total > 0.0:
        gap = min(gap, total - gap)
    return gap


def _volume(points, allowed, origin, limit):
    """시작 버텍스에서의 직선 거리(토폴로지 무시)."""
    dist = {}
    for v in allowed:
        p = points[v]
        d = ((p.x - origin.x) ** 2 + (p.y - origin.y) ** 2 +
             (p.z - origin.z) ** 2) ** 0.5
        if d <= limit:
            dist[v] = d
    return dist


def _closest_vertex(points, allowed, origin):
    """origin 에 가장 가까운, 집합 안의 버텍스 id."""
    best, best_d = None, float("inf")
    for v in allowed:
        p = points[v]
        d = ((p.x - origin.x) ** 2 + (p.y - origin.y) ** 2 +
             (p.z - origin.z) ** 2)
        if d < best_d:
            best, best_d = v, d
    return best


def _distances(mode, adj, points, allowed, seed, radius):
    """세 모드 모두 **시작 버텍스(seed)에서부터** 잰다.

    조인트 자체 위치가 아니라 seed 를 기준으로 두는 이유: 조인트가 표면에서 조금
    떨어져 있어도 그 조인트가 맡은 버텍스는 반드시 웨이트 1 로 시작해야 하기 때문이다
    (Soft Select 반경도 "가장 가까운 버텍스에서부터" 라는 뜻이 된다). 모드가 바뀌어도
    기준점이 같아서 결과를 비교하기 쉽다.
    """
    if mode == MODE_VOLUME:
        return _volume(points, allowed, points[seed], radius)
    if mode == MODE_TOPOLOGY:
        # 반경 무제한(Fit 측정)일 때는 홉 수를 정수로 못 바꾸므로 집합 크기로 막는다.
        steps = len(adj) if radius == float("inf") else int(round(radius))
        return _bfs(adj, seed, steps)
    return _dijkstra(adj, points, seed, radius)


def _joint_positions(joints):
    out = []
    for j in joints:
        pos = cmds.xform(j, q=True, ws=True, t=True)
        out.append(om.MPoint(pos[0], pos[1], pos[2]))
    return out


# =========================
# 반경 제안 (Fit to Joints)
# =========================

def suggest_radius(mesh, vtx_ids, joints, mode=MODE_SURFACE, loop_ids=None,
                   loop_closed=False):
    """조인트마다 '가장 가까운 다른 조인트'까지의 거리 중 **최댓값**.

    이 값을 반경으로 쓰면 각 조인트의 falloff 가 이웃 조인트에 꼭 닿아, 사이 구간이
    빈틈없이 채워진다. Falloff mode 와 같은 척도로 재므로 topology 모드에서는
    '엣지 개수' 가 나온다. 루프를 주면 **루프 위 간격**으로 잰다(밴드를 가로지르는
    지름길에 속지 않는다).
    """
    mesh, ids, joints = _validate(mesh, vtx_ids, joints)
    if len(joints) < 2:
        raise ValueError("Fit needs at least 2 joints.")

    allowed = set(ids)
    points = world_points(mesh)
    origins = _joint_positions(joints)

    if loop_ids:
        order = list(loop_ids)
        arcs, total = _loop_arcs(mode, points, order, loop_closed)
        seeds = [_closest_vertex(points, set(order), o) for o in origins]
        best = 0.0
        for i, seed in enumerate(seeds):
            nearest = min(
                (_arc_distance(arcs[seed], arcs[s], total, loop_closed)
                 for k, s in enumerate(seeds) if k != i), default=None)
            if nearest is not None and nearest > best:
                best = nearest
        if best <= 0.0:
            raise ValueError(
                "Could not measure the joint spacing on the loop - the joints "
                "may all snap to the same loop vertex.")
        return best

    seeds = [_closest_vertex(points, allowed, o) for o in origins]
    adj = adjacency(mesh, allowed) if mode != MODE_VOLUME else {}
    big = float("inf")

    best = 0.0
    for i, seed in enumerate(seeds):
        dist = _distances(mode, adj, points, allowed, seed, big)
        nearest = min((dist[s] for k, s in enumerate(seeds)
                       if k != i and s in dist), default=None)
        if nearest is not None and nearest > best:
            best = nearest
    if best <= 0.0:
        raise ValueError(
            "Could not measure the joint spacing - the joints may all share "
            "one vertex, or the stored vertices do not connect them.")
    return best


# =========================
# skinCluster 준비 / 웨이트 IO
# =========================

def _sc_fn(sc):
    sel = om.MSelectionList()
    sel.add(sc)
    return oma.MFnSkinCluster(sel.getDependNode(0))


def _dag_and_component(mesh, ids):
    """(셰이프 dagPath, 주어진 버텍스만 담은 component)."""
    dag = _shape_dag(mesh)
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(list(ids))
    return dag, comp


def _prepare_skin(mesh, joints):
    """skinCluster 를 보장하고 조인트들을 인플루언스로 넣는다. (skinCluster, 새로 만듦?)

    새로 만들 때는 트랜스폼이 아니라 **셰이프**에 건다. 셰이프가 여럿인 트랜스폼에
    이름만 넘기면 마야가 엉뚱한 셰이프에 바인드할 수 있다.
    """
    sc = skincluster_of(mesh)
    if not sc:
        shape = shape_of(mesh)
        sc = cmds.skinCluster(list(joints) + [shape], tsb=True,
                              n=_leaf(mesh) + "_skinCluster")[0]
        return sc, True

    have = {_long(n) for n in (cmds.skinCluster(sc, q=True, inf=True) or [])}
    for joint in joints:
        if _long(joint) not in have:
            cmds.skinCluster(sc, e=True, addInfluence=joint, weight=0.0)
    return sc, False


def _check_skin_drives(sc, mesh):
    """그 skinCluster 가 우리 셰이프를 실제로 변형하는지 확인(아니면 명확한 에러)."""
    shape, ok = maya_shape.drives_shape(sc, mesh)
    if not ok:
        driven = maya_shape.deformed_shapes(sc)
        raise ValueError(
            "'{0}' is not deformed by {1} (it drives {2}). Check the mesh's "
            "history - the shape that is bound may be a different one under "
            "the same transform.".format(
                _leaf(shape or mesh), sc,
                ", ".join(sorted(_leaf(d) for d in driven)) or "nothing"))
    return shape


def _influence_columns(sc, joints):
    """(모든 인플루언스의 논리 인덱스 MIntArray, 대상 조인트의 열 번호, 인플루언스 수)."""
    fn = _sc_fn(sc)
    dags = fn.influenceObjects()
    logical = om.MIntArray()
    paths = []
    for dag in dags:
        logical.append(int(fn.indexForInfluenceObject(dag)))
        paths.append(dag.fullPathName())

    wanted = [_long(j) for j in joints]
    columns = []
    for path in wanted:
        if path in paths:
            columns.append(paths.index(path))
        else:
            raise RuntimeError(
                "'{0}' is not an influence of {1}.".format(_leaf(path or ""), sc))
    return fn, logical, columns, len(paths)


# =========================
# 메인 동작
# =========================

def _validate(mesh, vtx_ids, joints):
    if not mesh or not cmds.objExists(mesh):
        raise ValueError("Stored mesh is gone. Store the vertices again.")
    ids = sorted({int(v) for v in (vtx_ids or [])})
    if not ids:
        raise ValueError("No vertices stored. Press 'Store Vertices' first.")
    count = vertex_count(mesh)
    if ids[-1] >= count:
        raise ValueError(
            "Stored vertices do not fit '{0}' any more (topology changed). "
            "Store them again.".format(_leaf(mesh)))

    live = []
    for joint in (joints or []):
        path = _long(joint)
        if path is None:
            raise ValueError("Stored joint '{0}' is gone.".format(joint))
        live.append(path)
    if not live:
        raise ValueError("No joints stored. Press 'Store Joints' first.")
    return mesh, ids, live


def _validate_loop(mesh, ids, loop_ids):
    """루프 입력 검사. (정렬된 루프 id, 저장 집합에 없어서 끼워 넣은 id 목록)

    루프는 저장한 버텍스 집합 **안에 있는** 엣지 루프라는 전제다. 그래도 사용자가
    루프만 따로 저장하고 집합에 안 넣은 경우가 있어, 빠진 루프 버텍스는 대상에 끼워
    넣고 몇 개였는지 보고한다(안 그러면 루프가 끊긴 채로 계산된다).
    """
    if not loop_ids:
        return [], []

    order = [int(v) for v in loop_ids]
    if max(order) >= vertex_count(mesh):
        raise ValueError(
            "The stored edge loop does not fit '{0}' any more (topology "
            "changed). Store it again.".format(_leaf(mesh)))
    if len(order) < 2:
        raise ValueError("The stored edge loop needs at least 2 vertices.")

    known = set(ids)
    extra = [v for v in order if v not in known]
    return order, extra


def _raw_from_region(mode, adj, points, allowed, seeds, radius,
                     points_curve, curve_interp):
    """루프 없이 — 조인트 seed 에서 영역 전체로 퍼진 거리로 원시 가중치를 낸다."""
    raw = [{} for _ in seeds]
    for i, seed in enumerate(seeds):
        dist = _distances(mode, adj, points, allowed, seed, radius)
        bucket = raw[i]
        for vid, d in dist.items():
            value = falloff.evaluate(points_curve, curve_interp, d / radius)
            if value > 0.0:
                bucket[vid] = value
    return raw, None


def _raw_from_loop(mode, adj, points, allowed, order, closed, origins, radius,
                   across_radius, points_curve, curve_interp):
    """루프를 줬을 때 — 루프 따라(분배) / 루프 바깥(amount) 을 분리해 낸다.

    1. 루프 전체를 시작점으로 한 번에 퍼뜨려(`_dijkstra_multi`) 버텍스마다
       "루프에서 떨어진 거리" 와 "가장 가까운 루프 버텍스(anchor)" 를 얻는다.
    2. 조인트 사이 비율은 **anchor 의 루프 위 호 거리**로만 낸다. 그래서 밴드
       어디서나 루프와 같은 비율이 유지된다(바깥 거리가 비율을 흔들지 않는다).
    3. 루프에서 떨어진 거리는 across 커브로 amount(coverage) 만 줄인다.
    """
    arcs, total = _loop_arcs(mode, points, order, closed)
    seeds = [_closest_vertex(points, set(order), o) for o in origins]

    limit = across_radius
    if mode == MODE_TOPOLOGY:
        limit = float(int(round(across_radius)))
    across_dist, anchor = _dijkstra_multi(mode, adj, points, order, limit)

    raw = [{} for _ in origins]
    across = {}
    for vid, d in across_dist.items():
        if vid not in allowed:
            continue
        value = falloff.evaluate(points_curve, curve_interp, d / across_radius)
        if value <= 0.0:
            continue
        across[vid] = value
        anchor_arc = arcs[anchor[vid]]
        for i, seed in enumerate(seeds):
            gap = _arc_distance(anchor_arc, arcs[seed], total, closed)
            share = falloff.evaluate(points_curve, curve_interp, gap / radius)
            if share > 0.0:
                raw[i][vid] = share
    return raw, across


def expand_bind(mesh, vtx_ids, joints, radius, blend=1.0, mode=MODE_SURFACE,
                curve_points=None, curve_interp=falloff.DEFAULT_INTERP,
                loop_ids=None, loop_closed=False, across_radius=0.0):
    """저장된 버텍스 집합을 저장된 조인트들에 바인드한다.

    Args:
        mesh: 대상 메시 트랜스폼.
        vtx_ids: 대상 버텍스 id 목록.
        joints: 인플루언스로 쓸 조인트(또는 트랜스폼) 목록.
        radius: Soft Select 반경. surface/volume 은 씬 단위, topology 는 엣지 개수.
            루프를 주면 **루프를 따라가는 방향**의 반경이다.
        blend: 기존 인플루언스가 있는 버텍스에서 이 조인트들이 가져갈 **최대** 총량
            (0~1). 실제로는 `blend * coverage` 만큼 가져가고 나머지는 기존
            인플루언스가 비율대로 유지한다. 기존 인플루언스가 없으면 항상 1.
        mode: MODE_SURFACE / MODE_TOPOLOGY / MODE_VOLUME.
        curve_points, curve_interp: falloff 커브(정규화 거리 -> 비중).
        loop_ids: 조인트가 앉아 있는 **엣지 루프**의 버텍스 id (order_loop 로 정렬된 것).
            주면 조인트 분배를 루프 위 거리로만 계산한다(권장).
        loop_closed: 그 루프가 닫혀 있는지.
        across_radius: 루프에서 **멀어지는 방향**의 반경. 0 이면 radius 와 같게 쓴다.

    Returns:
        report dict — mesh/joints/affected/skipped/created/max_weight 등.
    """
    mesh, ids, joints = _validate(mesh, vtx_ids, joints)
    radius = float(radius)
    if radius <= MIN_RADIUS:
        raise ValueError("Soft Select radius must be greater than 0.")
    blend = falloff.clamp01(float(blend))
    if mode not in MODES:
        mode = MODE_SURFACE
    points_curve = falloff.normalize_points(curve_points)

    across_radius = float(across_radius or 0.0)
    if across_radius <= MIN_RADIUS:
        across_radius = radius

    order, loop_added = _validate_loop(mesh, ids, loop_ids)
    if loop_added:
        ids = sorted(set(ids) | set(loop_added))
    allowed = set(ids)
    points = world_points(mesh)
    origins = _joint_positions(joints)

    # 루프 모드는 '루프에서 멀어지는' 탐색이 있어야 하므로 volume 이어도 인접이 필요하다.
    adj = ({} if (mode == MODE_VOLUME and not order)
           else adjacency(mesh, allowed))

    if order:
        raw, across = _raw_from_loop(
            mode, adj, points, allowed, order, loop_closed, origins, radius,
            across_radius, points_curve, curve_interp)
    else:
        seeds = [_closest_vertex(points, allowed, o) for o in origins]
        raw, across = _raw_from_region(
            mode, adj, points, allowed, seeds, radius, points_curve,
            curve_interp)

    # 버텍스별로 (a) 조인트들 사이의 비율, (b) 이 조인트 집합이 그 버텍스를 얼마나
    # 덮는지(coverage) 를 따로 낸다.
    #   비율     = 원시값 / 합            -> 조인트 사이 분배(요구사항의 '고른 분배')
    #   coverage = min(1, 합)             -> 커브가 바깥에서 서서히 빠지게 하는 몫
    # 두 조인트 사이는 합이 1 이라 coverage 가 1 이고(분배만 일어난다), 바깥쪽 끝에서는
    # 합이 줄어 coverage 가 떨어진다. coverage 없이 정규화만 하면 반경 끝에서 웨이트가
    # 1 -> 0 으로 뚝 끊긴다(커브 모양이 무의미해진다).
    shares = {}
    coverage = {}
    for i in range(len(joints)):
        for vid, value in raw[i].items():
            shares.setdefault(vid, {})[i] = value
    # 루프를 준 경우엔 '루프에서 멀어지며 빠지는 몫'(across)이 coverage 를 대신 이끈다.
    # 루프 위에서는 across = 1 이므로 조인트 사이 분배는 그대로 유지된다.
    for vid, per_joint in shares.items():
        total = sum(per_joint.values())
        if total <= 0.0:
            continue
        value = total if total < 1.0 else 1.0
        if across is not None:
            value *= across.get(vid, 0.0)
        coverage[vid] = value
        for i in per_joint:
            per_joint[i] /= total

    touched = sorted(v for v in shares if coverage.get(v, 0.0) > 0.0)
    if not touched:
        raise ValueError(
            "No vertex is within the Soft Select radius. Raise the radius, or "
            "check that the joints sit on the stored vertices.")

    sc, created = _prepare_skin(mesh, joints)
    # 웨이트를 읽고 쓰기 전에 '이 skinCluster 가 이 셰이프를 변형하는지' 를 확인한다.
    # 어긋난 채로 MFnSkinCluster.getWeights 를 부르면 마야가
    # "(kInvalidParameter): Object is incompatible with this method" 로 죽는다.
    shape = _check_skin_drives(sc, mesh)
    fn, logical, columns, n_inf = _influence_columns(sc, joints)
    dag, comp = _dag_and_component(shape, touched)

    weights = fn.getWeights(dag, comp)[0]
    new_weights = om.MDoubleArray(weights)

    target_cols = set(columns)
    max_weight = 0.0

    for row, vid in enumerate(touched):
        base = row * n_inf
        per_joint = shares[vid]

        # 대상 조인트 외 인플루언스가 이미 갖고 있는 양 -> Blend 적용 여부를 가른다.
        others = 0.0
        for col in range(n_inf):
            if col not in target_cols:
                others += weights[base + col]

        if others > 1e-6:
            # 남길 곳이 있으니 커브가 덜 덮은 만큼은 기존 인플루언스에 남긴다.
            amount = blend * coverage[vid]
            scale = (1.0 - amount) / others
        else:
            # 줄 곳이 여기밖에 없다 — 남기면 행의 합이 1 이 안 돼 마야가 어차피
            # 다시 정규화한다. 그래서 Blend / coverage 와 무관하게 전부 가져간다.
            amount = 1.0
            scale = 0.0

        for col in range(n_inf):
            if col in target_cols:
                continue
            new_weights[base + col] = weights[base + col] * scale

        for col in columns:
            new_weights[base + col] = 0.0
        for i, share in per_joint.items():
            value = share * amount
            new_weights[base + columns[i]] += value
            if value > max_weight:
                max_weight = value

    fn.setWeights(dag, comp, logical, new_weights, False)

    return {
        "mesh": mesh,
        "skin_cluster": sc,
        "created_skin": created,
        "joints": [_leaf(j) for j in joints],
        "stored": len(ids),
        "affected": len(touched),
        "skipped": len(ids) - len(touched),
        "radius": radius,
        "across_radius": across_radius if order else radius,
        "mode": mode,
        "blend": blend,
        "max_weight": max_weight,
        "loop": len(order),
        "loop_closed": bool(loop_closed) if order else False,
        "loop_added": len(loop_added),
    }
