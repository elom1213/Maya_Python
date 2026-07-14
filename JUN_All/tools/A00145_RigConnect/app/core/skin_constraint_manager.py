# -*- coding: utf-8 -*-
"""
skin_constraint_manager - "Skin Weight to Constraint" 기능 로직.

선택한 버텍스의 스킨 웨이트를 읽어, 영향(influence) joint 들을 그 웨이트만큼
가중치로 follower 오브젝트에 constraint 로 연결한다.

예) 버텍스의 웨이트가 hip:0.2 / spine_01:0.5 / spine_02:0.3 이면
    세 joint 를 그 비율의 weight 로 follower 에 constraint.

constraint 타입은 Parent / Scale / Point / Orient 중에서 고른다.

aggregation 두 가지:
  - average  : 선택한 모든 버텍스의 joint 별 웨이트를 평균/정규화 → 모든 follower 에 동일 적용.
  - per-vertex: vertices[i] 의 웨이트를 followers[i] 에 1:1 로 적용(개수 일치 필요).

UI 비의존: 위젯에서 읽은 list/int/bool 값만 받는다. (app/core ↔ app/ui 분리)
"""

import maya.cmds as cmds

from tools.A00145_RigConnect.app.core import constrain_manager as con_mgr

# weight 0 판정 임계값.
_EPS = 1e-6

# 스킨 웨이트 가중 방식으로 쓸 수 있는 constraint 타입만 노출한다.
# pointOnPoly 는 mesh 를 타겟으로 삼으므로 joint 가중 constraint 에 쓸 수 없어 제외.
_SKIN_KEYS = ("parent", "scale", "point", "orient")
SKIN_CONSTRAIN_TYPES = [t for t in con_mgr.CONSTRAIN_TYPES if t[0] in _SKIN_KEYS]


def get_skin_cluster(node):
    """node(메쉬/트랜스폼/버텍스 컴포넌트)에 연결된 skinCluster 노드명을 찾는다.

    Args:
        node: "pCube1" / "pCube1.vtx[5]" 등.

    Returns:
        skinCluster 노드명, 없으면 None.
    """
    mesh = node.split(".")[0]
    history = cmds.listHistory(mesh, pruneDagObjects=True) or []
    skins = cmds.ls(history, type="skinCluster")
    return skins[0] if skins else None


def get_vertex_weights(vtx):
    """버텍스 1개의 {influence: weight} (weight>0) 딕셔너리를 반환한다."""
    skin = get_skin_cluster(vtx)
    if not skin:
        raise ValueError("No skinCluster found for: {0}".format(vtx))
    infs = cmds.skinCluster(skin, q=True, inf=True) or []
    vals = cmds.skinPercent(skin, vtx, q=True, value=True) or []
    return {inf: v for inf, v in zip(infs, vals) if v > _EPS}


def _top_normalized(weights, max_influence):
    """weight dict 에서 상위 max_influence 개만 남기고 합=1 로 정규화한다.

    Args:
        weights: {influence: weight} dict.
        max_influence: 남길 최대 influence 개수. 0/None 이면 전부 사용.

    Returns:
        [(influence, normalized_weight), ...] (weight 내림차순).
    """
    items = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    if max_influence and max_influence > 0:
        items = items[:max_influence]
    total = sum(w for _, w in items)
    if total <= 0:
        raise ValueError("Total weight is zero.")
    return [(inf, w / total) for inf, w in items]


def _apply_weighted_constraint(influences_weights, follower, maintain_offset,
                               con_type="parent"):
    """[(joint, weight), ...] 로 follower 에 constraint 를 만들고 weight 를 설정한다.

    Args:
        influences_weights: [(joint, normalized_weight), ...].
        follower: 구속될 오브젝트.
        maintain_offset: constraint 의 maintain offset 옵션.
        con_type: SKIN_CONSTRAIN_TYPES 의 key ("parent"/"scale"/"point"/"orient").

    Returns:
        생성된 constraint 노드명.
    """
    con_func = con_mgr.get_constraint_func(con_type)

    joints = [inf for inf, _ in influences_weights]
    missing = [j for j in joints if not cmds.objExists(j)]
    if missing:
        raise ValueError(
            "Influences not found in scene: {0}".format(", ".join(missing)))
    if not cmds.objExists(follower):
        raise ValueError("Follower not found in scene: {0}".format(follower))

    con = con_func(*(joints + [follower]), mo=maintain_offset)[0]
    # 회전 보간을 Shortest 로 강제(0=No Flip, 1=Average, 2=Shortest).
    # 여러 joint 가 가중 평균될 때 No Flip/Average 는 짐벌 튐이 생길 수 있어 Shortest 로 고정.
    # interpType 은 회전을 다루는 parent/orient 에만 있다(point/scale 에는 없음).
    if cmds.attributeQuery("interpType", node=con, exists=True):
        cmds.setAttr("{0}.interpType".format(con), 2)
    # weightAliasList 는 target 추가 순서(=joints 순서)와 동일하다.
    aliases = con_func(con, q=True, weightAliasList=True) or []
    for alias, (_, w) in zip(aliases, influences_weights):
        cmds.setAttr("{0}.{1}".format(con, alias), w)
    return con


def skin_weight_to_constraint(vertices, followers, max_influence=0,
                              maintain_offset=True, per_vertex=False,
                              con_type="parent"):
    """선택 버텍스의 스킨 웨이트로 followers 에 constraint 를 생성한다.

    Args:
        vertices: 버텍스 컴포넌트 리스트("pMesh.vtx[i]").
        followers: 구속될(constraint 가 걸릴) 오브젝트 리스트.
        max_influence: 사용할 최대 joint 개수(정수). 0 이면 제한 없음.
        maintain_offset: constraint 의 maintain offset 옵션.
        per_vertex: True 면 vertices[i] -> followers[i] 1:1, False 면 평균을 전체에 적용.
        con_type: SKIN_CONSTRAIN_TYPES 의 key ("parent"/"scale"/"point"/"orient").

    Returns:
        생성된 constraint 노드명 리스트.
    """
    if not vertices:
        raise ValueError("No vertices. Add vertices to the Vertices list.")
    if not followers:
        raise ValueError("No followers. Add objects to the Followers list.")

    made = []

    if per_vertex:
        if len(vertices) != len(followers):
            raise ValueError(
                "Per-vertex mode needs equal counts: "
                "{0} vertices vs {1} followers.".format(
                    len(vertices), len(followers)))
        for vtx, flw in zip(vertices, followers):
            iw = _top_normalized(get_vertex_weights(vtx), max_influence)
            made.append(_apply_weighted_constraint(
                iw, flw, maintain_offset, con_type))
    else:
        # 모든 버텍스의 joint 별 웨이트를 합산 → 평균 → 정규화.
        accum = {}
        for vtx in vertices:
            for inf, w in get_vertex_weights(vtx).items():
                accum[inf] = accum.get(inf, 0.0) + w
        n = len(vertices)
        avg = {inf: w / n for inf, w in accum.items()}
        iw = _top_normalized(avg, max_influence)
        for flw in followers:
            made.append(_apply_weighted_constraint(
                iw, flw, maintain_offset, con_type))

    return made


# ----------------------------------------------------------------------
# Locator 자동 생성 + constraint (UI 의 "Locators" 버튼)
# ----------------------------------------------------------------------

def _vertex_world_pos(vtx):
    """버텍스의 월드 위치 (x, y, z)."""
    return cmds.pointPosition(vtx, world=True)


def _locator_name_from_vertex(vtx):
    """'pMesh.vtx[5]' -> 'pMesh_vtx5_loc' 형태의 로케이터 이름."""
    mesh, rest = vtx.split(".vtx[")
    index = rest[:-1]
    short = mesh.split("|")[-1].split(":")[-1]
    return "{0}_vtx{1}_loc".format(short, index)


def create_locators_and_constrain(vertices, max_influence=0,
                                  maintain_offset=True, per_vertex=False,
                                  con_type="parent"):
    """로케이터를 자동 생성해 스킨 웨이트 constraint 를 건다.

    빈 follower 를 만들 필요 없이, 선택 버텍스만으로 동작한다.

    - per_vertex=True : 버텍스마다 로케이터 1개를 그 버텍스 월드 위치에 생성하고,
                        각 버텍스 웨이트로 1:1 구속한다(스킨 표면을 따라가는 로케이터들).
    - per_vertex=False: 선택 버텍스 전체의 centroid 에 로케이터 1개를 생성하고,
                        평균 웨이트로 구속한다.

    생성한 로케이터들은 하나의 그룹("RigConnect_skinLoc_grp#")으로 묶는다.

    Args:
        vertices: 버텍스 컴포넌트 리스트("pMesh.vtx[i]").
        max_influence: 사용할 최대 joint 개수(정수). 0 이면 제한 없음.
        maintain_offset: constraint 의 maintain offset 옵션.
        per_vertex: True 면 버텍스당 로케이터 1개, False 면 centroid 에 1개.
        con_type: SKIN_CONSTRAIN_TYPES 의 key ("parent"/"scale"/"point"/"orient").

    Returns:
        (created_locators, made_constraints) 튜플.
    """
    if not vertices:
        raise ValueError(
            "No vertices. Select skinned vertices and add them to the "
            "Vertices list.")

    # 1) 위치/이름을 먼저 계산 (loc, pos) 목록을 만든다.
    if per_vertex:
        specs = [(_locator_name_from_vertex(v), _vertex_world_pos(v))
                 for v in vertices]
    else:
        pts = [_vertex_world_pos(v) for v in vertices]
        n = len(pts)
        centroid = (sum(p[0] for p in pts) / n,
                    sum(p[1] for p in pts) / n,
                    sum(p[2] for p in pts) / n)
        mesh = vertices[0].split(".")[0].split("|")[-1].split(":")[-1]
        specs = [("{0}_skinLoc".format(mesh), centroid)]

    # 2) 로케이터를 그룹 아래에 생성하고 월드 위치에 배치한다.
    #    (constrain 전에 그룹/배치를 끝내야 maintain offset 이 올바르게 계산된다)
    grp = cmds.group(empty=True, name="RigConnect_skinLoc_grp#")
    created = []
    for name, pos in specs:
        loc = cmds.spaceLocator(name=name)[0]
        loc = cmds.parent(loc, grp)[0]
        cmds.xform(loc, ws=True, translation=(pos[0], pos[1], pos[2]))
        created.append(loc)

    # 3) 생성한 로케이터를 follower 로 삼아 동일한 스킨 웨이트 constraint 적용.
    made = skin_weight_to_constraint(
        vertices, created, max_influence, maintain_offset, per_vertex, con_type)

    return created, made
