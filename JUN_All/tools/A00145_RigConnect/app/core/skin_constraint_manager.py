# -*- coding: utf-8 -*-
"""
skin_constraint_manager - "Skin Weight to Constraint" 기능 로직.

선택한 버텍스의 스킨 웨이트를 읽어, 영향(influence) joint 들을 그 웨이트만큼
가중치로 follower 오브젝트에 parentConstraint 로 연결한다.

예) 버텍스의 웨이트가 hip:0.2 / spine_01:0.5 / spine_02:0.3 이면
    세 joint 를 그 비율의 weight 로 follower 에 parentConstraint.

aggregation 두 가지:
  - average  : 선택한 모든 버텍스의 joint 별 웨이트를 평균/정규화 → 모든 follower 에 동일 적용.
  - per-vertex: vertices[i] 의 웨이트를 followers[i] 에 1:1 로 적용(개수 일치 필요).

UI 비의존: 위젯에서 읽은 list/int/bool 값만 받는다. (app/core ↔ app/ui 분리)
"""

import maya.cmds as cmds

# weight 0 판정 임계값.
_EPS = 1e-6


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


def _apply_weighted_constraint(influences_weights, follower, maintain_offset):
    """[(joint, weight), ...] 로 follower 에 parentConstraint 를 만들고 weight 를 설정한다.

    Returns:
        생성된 constraint 노드명.
    """
    joints = [inf for inf, _ in influences_weights]
    missing = [j for j in joints if not cmds.objExists(j)]
    if missing:
        raise ValueError(
            "Influences not found in scene: {0}".format(", ".join(missing)))
    if not cmds.objExists(follower):
        raise ValueError("Follower not found in scene: {0}".format(follower))

    con = cmds.parentConstraint(*(joints + [follower]), mo=maintain_offset)[0]
    # weightAliasList 는 target 추가 순서(=joints 순서)와 동일하다.
    aliases = cmds.parentConstraint(con, q=True, weightAliasList=True) or []
    for alias, (_, w) in zip(aliases, influences_weights):
        cmds.setAttr("{0}.{1}".format(con, alias), w)
    return con


def skin_weight_to_constraint(vertices, followers, max_influence=0,
                              maintain_offset=True, per_vertex=False):
    """선택 버텍스의 스킨 웨이트로 followers 에 parentConstraint 를 생성한다.

    Args:
        vertices: 버텍스 컴포넌트 리스트("pMesh.vtx[i]").
        followers: 구속될(parentConstraint 가 걸릴) 오브젝트 리스트.
        max_influence: 사용할 최대 joint 개수(정수). 0 이면 제한 없음.
        maintain_offset: parentConstraint 의 maintain offset 옵션.
        per_vertex: True 면 vertices[i] -> followers[i] 1:1, False 면 평균을 전체에 적용.

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
            made.append(_apply_weighted_constraint(iw, flw, maintain_offset))
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
            made.append(_apply_weighted_constraint(iw, flw, maintain_offset))

    return made
