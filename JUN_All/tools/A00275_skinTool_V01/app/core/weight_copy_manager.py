# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-07
# A00275_skinTool_V01 - Copy Weights (한 메시 안에서 버텍스 -> 버텍스로 웨이트 복사)
#
# 같은 메시 M 의 버텍스 집합을 저장해 두고(Copy), 나중에 M 의 **다른 버텍스들을 골라**
# 붙여넣으면(Paste) 저장한 쪽의 웨이트가 그대로 실린다.
#
# ## "그대로" 가 무슨 뜻인가
#
# 목표 버텍스마다 **가장 가까운 소스 버텍스 하나**를 골라 그 버텍스의 **웨이트 행 전체**를
# 그대로 베낀다. 값을 섞거나 보간하지 않는다 — 그래서 인플루언스 구성이 무엇이든,
# 행의 합이 얼마든 소스와 **완전히 같은 값**이 나온다.
#
# 인플루언스를 새로 넣지 않는다. 소스와 목표가 **같은 skinCluster** 라 열 구성이 이미
# 같기 때문이다(그래서 이 기능은 한 메시 안에서만 동작한다. 메시 사이 전이는
# `weight_transfer_manager` / `skin_migrate_manager` 쪽이다).
#
# ## 무엇을 "가깝다" 고 볼지 — Expand Bind 의 Falloff mode 와 같은 세 가지
#
#   surface  : 메시의 엣지를 따라가는 **측지 거리**(엣지 길이 누적). 기본.
#   topology : 엣지 **개수**(홉 수) — 엣지 길이가 들쭉날쭉해도 "몇 칸 떨어졌나" 로만 센다.
#   volume   : **직선 거리**(토폴로지 무시 — 틈 건너편에서도 가져온다).
#
# surface / topology 는 `expand_bind_manager.dijkstra_multi` 를 그대로 쓴다. 소스 집합
# 전체를 시작점으로 한 번 퍼뜨리면 버텍스마다 "가장 가까운 소스가 누구인지"(anchor)가
# 한 번에 나오므로, 소스마다 따로 돌릴 필요가 없다.
#
# **탐색 범위는 메시 전체다.** Expand Bind 는 저장한 집합 **안으로** 인접을 가두지만
# (falloff 가 영역 밖으로 새면 안 되니까), 여기서는 소스와 목표가 **떨어져 있는 것이 정상**
# 이라 가둬 두면 아무 데도 못 간다.
#
# ## volume 은 전수 비교를 하면 안 된다
#
# 목표마다 소스를 전부 재면 `목표 x 소스` 다 — 20,000 x 5,000 = **1억 번**이라 순수
# 파이썬에서는 분 단위가 된다. 그래서 소스를 **균일 격자**에 담고 목표 주변 셀만 본다.
# 셀을 한 겹씩 넓히다가 "다음 겹의 가장 가까운 지점보다 이미 찾은 것이 더 가깝다" 가
# 되면 멈춘다 — 근사가 아니라 전수 비교와 **같은 답**이다.
#
# UI 비의존: 위젯에서 읽은 값만 받는다. (app/core <-> app/ui 분리)

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core import maya_shape
from Framework.core import maya_skin
from tools.A00275_skinTool_V01.app.core import expand_bind_manager as eb


# Falloff mode 와 같은 값을 쓴다 — 콤보 표시도 같아야 사용자가 두 탭을 같은 것으로 읽는다.
MODE_SURFACE = eb.MODE_SURFACE
MODE_TOPOLOGY = eb.MODE_TOPOLOGY
MODE_VOLUME = eb.MODE_VOLUME

MODES = eb.MODES

# 소스가 이보다 적으면 격자를 만드는 비용이 전수 비교보다 크다.
GRID_MIN_SOURCES = 64


def _leaf(name):
    return name.split("|")[-1].split(":")[-1]


# =========================
# 선택 파싱 (Copy / Paste 버튼이 쓰는 입력)
# =========================

def parse_selected_vertices():
    """현재 선택에서 (메시 롱네임, 정렬된 버텍스 id 리스트).

    Expand Bind 와 같은 파서다 — 엣지/페이스를 골라도 버텍스로 바꾸고, 셰이프가 여럿인
    트랜스폼에서 어느 셰이프의 컴포넌트인지도 같은 규칙으로 가린다.
    """
    return eb.parse_selected_vertices()


# =========================
# volume — 균일 격자로 최근접 소스
# =========================

def _brute_nearest(points, sources, targets):
    out = {}
    for t in targets:
        p = points[t]
        best, best_d2 = None, float("inf")
        for s in sources:
            q = points[s]
            d2 = ((q.x - p.x) ** 2 + (q.y - p.y) ** 2 + (q.z - p.z) ** 2)
            if d2 < best_d2:
                best, best_d2 = s, d2
        out[t] = best
    return out


def _grid_nearest(points, sources, targets):
    """소스를 균일 격자에 담고 목표 주변 셀만 훑어 최근접 소스를 찾는다.

    전수 비교와 **같은 답**이다. 한 겹(ring) 을 다 본 뒤 "지금까지 찾은 최단거리" 가
    `겹수 x 셀크기` 보다 작거나 같으면, 아직 안 본 셀에는 더 가까운 점이 있을 수 없으므로
    멈춘다.
    """
    xs = [points[s].x for s in sources]
    ys = [points[s].y for s in sources]
    zs = [points[s].z for s in sources]
    lo = (min(xs), min(ys), min(zs))
    hi = (max(xs), max(ys), max(zs))
    diag = ((hi[0] - lo[0]) ** 2 + (hi[1] - lo[1]) ** 2 +
            (hi[2] - lo[2]) ** 2) ** 0.5
    if diag <= 1e-9:
        # 소스가 사실상 한 점 — 격자로 나눌 것이 없다.
        return _brute_nearest(points, sources, targets)

    # 셀 하나에 소스가 평균 한 개쯤 들어가게.
    side = max(1, int(round(len(sources) ** (1.0 / 3.0))))
    cell = diag / float(side)

    def key(p):
        return (int((p.x - lo[0]) // cell), int((p.y - lo[1]) // cell),
                int((p.z - lo[2]) // cell))

    buckets = {}
    for s in sources:
        buckets.setdefault(key(points[s]), []).append(s)

    span = [max(1, int((hi[i] - lo[i]) // cell) + 1) for i in range(3)]

    out = {}
    for t in targets:
        p = points[t]
        ci, cj, ck = key(p)
        # 격자를 다 덮는 데 필요한 최대 겹수(목표가 bbox 밖에 있어도 끝난다).
        max_ring = max(abs(ci) + 1, abs(ci - span[0]) + 1,
                       abs(cj) + 1, abs(cj - span[1]) + 1,
                       abs(ck) + 1, abs(ck - span[2]) + 1)
        best, best_d2 = None, float("inf")
        ring = 0
        while True:
            for i in range(ci - ring, ci + ring + 1):
                for j in range(cj - ring, cj + ring + 1):
                    for k in range(ck - ring, ck + ring + 1):
                        # 겹의 **껍질**만 본다(안쪽은 이전 겹에서 이미 봤다).
                        if (ring and abs(i - ci) != ring and
                                abs(j - cj) != ring and abs(k - ck) != ring):
                            continue
                        for s in buckets.get((i, j, k), ()):
                            q = points[s]
                            d2 = ((q.x - p.x) ** 2 + (q.y - p.y) ** 2 +
                                  (q.z - p.z) ** 2)
                            if d2 < best_d2:
                                best, best_d2 = s, d2
            if best is not None and (ring * cell) ** 2 >= best_d2:
                break
            ring += 1
            if ring > max_ring:
                break
        out[t] = best
    return out


def _nearest_volume(points, sources, targets):
    if len(sources) < GRID_MIN_SOURCES:
        return _brute_nearest(points, sources, targets)
    return _grid_nearest(points, sources, targets)


# =========================
# 최근접 소스 (세 모드 공통 진입점)
# =========================

def nearest_sources(mesh, source_ids, target_ids, mode=MODE_SURFACE):
    """목표 버텍스마다 가장 가까운 소스 버텍스. {target_vid: source_vid}

    닿지 못한 목표는 **아예 넣지 않는다**(surface/topology 에서 소스와 이어져 있지 않은
    조각). 부르는 쪽이 그 개수를 사용자에게 알린다 — 조용히 다른 모드로 넘어가지 않는다.
    """
    points = eb.world_points(mesh)
    sources = sorted(set(int(v) for v in source_ids))
    targets = sorted(set(int(v) for v in target_ids))

    if mode == MODE_VOLUME:
        return _nearest_volume(points, sources, targets)

    # 인접은 **메시 전체**로 만든다. 소스와 목표가 떨어져 있는 것이 정상이므로
    # Expand Bind 처럼 집합 안으로 가두면 아무 데도 못 간다.
    everything = set(range(eb.vertex_count(mesh)))
    adj = eb.adjacency(mesh, everything)
    _dist, anchor = eb.dijkstra_multi(mode, adj, points, sources,
                                      float("inf"))
    return {t: anchor[t] for t in targets if t in anchor}


# =========================
# 메인 동작
# =========================

def _validate(mesh, source_ids, target_ids):
    if not mesh or not cmds.objExists(mesh):
        raise ValueError("Stored mesh is gone. Copy the vertices again.")

    src = sorted(set(int(v) for v in (source_ids or [])))
    if not src:
        raise ValueError("No vertices copied yet. Select the vertices to copy "
                         "from and press 'Copy'.")
    tgt = sorted(set(int(v) for v in (target_ids or [])))
    if not tgt:
        raise ValueError("No vertices selected to paste onto.")

    count = eb.vertex_count(mesh)
    if src[-1] >= count:
        raise ValueError(
            "The copied vertices do not fit '{0}' any more (topology "
            "changed). Copy them again.".format(_leaf(mesh)))
    if tgt[-1] >= count:
        raise ValueError(
            "The selected vertices are out of range for '{0}'.".format(
                _leaf(mesh)))
    return src, tgt


def copy_weights(mesh, source_ids, target_ids, mode=MODE_SURFACE):
    """저장한 버텍스의 웨이트를 고른 버텍스에 그대로 붙여넣는다.

    Args:
        mesh: 대상 메시(소스와 목표가 **같은 메시**여야 한다).
        source_ids: 복사해 둔 버텍스 id.
        target_ids: 붙여넣을 버텍스 id (현재 선택).
        mode: MODE_SURFACE / MODE_TOPOLOGY / MODE_VOLUME — 무엇을 "가깝다" 고 볼지.

    Returns:
        report dict — mesh/skin_cluster/sources/targets/pasted/unreached/mode 등.
    """
    src, tgt = _validate(mesh, source_ids, target_ids)
    if mode not in MODES:
        mode = MODE_SURFACE

    sc = eb.skincluster_of(mesh)
    if not sc:
        raise ValueError(
            "'{0}' has no skinCluster - there are no weights to copy.".format(
                _leaf(mesh)))
    # 이 skinCluster 가 우리 셰이프를 실제로 변형하는지 먼저 본다. 어긋난 채로
    # getWeights 를 부르면 마야가 kInvalidParameter 로 죽는다(원인이 안 보이는 에러다).
    shape, drives = maya_shape.drives_shape(sc, mesh)
    if not drives:
        driven = maya_shape.deformed_shapes(sc)
        raise ValueError(
            "'{0}' is not deformed by {1} (it drives {2}). Check the mesh "
            "history - the shape that is bound may be a different one under "
            "the same transform.".format(
                _leaf(shape or mesh), sc,
                ", ".join(sorted(_leaf(d) for d in driven)) or "nothing"))

    pairs = nearest_sources(mesh, src, tgt, mode)
    unreached = [t for t in tgt if t not in pairs]
    touched = sorted(pairs)
    if not touched:
        raise ValueError(
            "No selected vertex could reach the copied vertices along the "
            "mesh. Try the 'Volume (straight line)' mode, or copy vertices on "
            "the same shell.")

    fn = maya_skin.skin_fn(sc)
    n_inf = len(maya_skin.influence_paths(fn))
    inf_indices = maya_skin.weight_indices(n_inf)

    dag = maya_shape.shape_dag(shape, deformer=sc, type_="mesh")

    # 소스는 **실제로 쓰이는 것만** 읽는다(고른 소스가 1000개여도 목표가 10개면 10행).
    used = sorted(set(pairs.values()))
    src_weights = fn.getWeights(dag, _component(used))[0]
    src_row = {vid: i for i, vid in enumerate(used)}

    tgt_comp = _component(touched)
    new_weights = om.MDoubleArray()
    new_weights.setLength(len(touched) * n_inf)
    for row, vid in enumerate(touched):
        base = row * n_inf
        origin = src_row[pairs[vid]] * n_inf
        for col in range(n_inf):
            new_weights[base + col] = src_weights[origin + col]

    # normalize=False — 소스 행을 **그대로** 옮기는 것이 이 기능의 정의다. 마야가 다시
    # 정규화하면 소스와 값이 달라진다(정규화가 필요한 씬은 소스도 이미 정규화돼 있다).
    fn.setWeights(dag, tgt_comp, inf_indices, new_weights, False)

    return {
        "mesh": mesh,
        "skin_cluster": sc,
        "sources": len(src),
        "targets": len(tgt),
        "pasted": len(touched),
        "unreached": len(unreached),
        "used_sources": len(used),
        "influences": n_inf,
        "mode": mode,
    }


def _component(ids):
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(list(ids))
    return comp
