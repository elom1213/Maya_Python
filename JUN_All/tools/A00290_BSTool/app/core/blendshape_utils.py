# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00290_BSTool - blendShape 공용 유틸 (UI 비의존, maya.cmds)
#
# 두 탭(Edit BS / Base Shape)이 공유하는 blendShape 조회 헬퍼.
#   - get_blendshape_targets : 별칭(타겟 이름)을 weight 인덱스 순으로 반환
#   - target_index_map       : 타겟 이름 -> weight(inputTargetGroup) 인덱스 dict
#   - find_base_mesh         : blendShape 가 출력하는 베이스 메시 transform
#   - find_blendshapes_from_selection : 선택(노드/메시)에서 blendShape 노드 수집

import re

import maya.cmds as cmds


def get_weight_index(attr):
    """'weight[3]' 같은 문자열에서 정수 인덱스(3)를 뽑는다. 못 찾으면 -1."""
    match = re.search(r"\[(\d+)\]", attr)
    return int(match.group(1)) if match else -1


def is_blendshape(node):
    return cmds.objExists(node) and cmds.nodeType(node) == "blendShape"


def _aliased_pairs(blendshape_node):
    """[(alias, realAttr), ...] 를 weight 인덱스 오름차순으로 반환."""
    aliases = cmds.aliasAttr(blendshape_node, query=True) or []
    # aliasAttr 은 [alias1, attr1, alias2, attr2, ...] 평면 리스트로 준다.
    pairs = [(aliases[i], aliases[i + 1]) for i in range(0, len(aliases), 2)]
    # weight[...] 별칭만 (다른 별칭이 섞일 수 있어 필터)
    pairs = [p for p in pairs if p[1].startswith("weight")]
    pairs.sort(key=lambda x: get_weight_index(x[1]))
    return pairs


def get_blendshape_targets(blendshape_node):
    """blendShape 타겟(별칭) 이름을 weight 인덱스 순으로 반환."""
    if not is_blendshape(blendshape_node):
        cmds.warning("'{0}' is not a valid blendShape node.".format(blendshape_node))
        return []
    return [alias for alias, _attr in _aliased_pairs(blendshape_node)]


def target_index_map(blendshape_node):
    """{타겟이름: weight 인덱스} dict 반환."""
    if not is_blendshape(blendshape_node):
        return {}
    return {alias: get_weight_index(attr)
            for alias, attr in _aliased_pairs(blendshape_node)}


def is_mesh(obj_name):
    if not cmds.objExists(obj_name):
        return False
    shapes = cmds.listRelatives(obj_name, shapes=True, fullPath=True) or []
    for shape in shapes:
        if cmds.objectType(shape) == "mesh":
            return True
    return cmds.objectType(obj_name) == "mesh"


def find_base_mesh(blendshape_node):
    """blendShape 가 디포밍하는 베이스 메시 transform 을 반환(없으면 None)."""
    history = cmds.listHistory(blendshape_node, future=True) or []
    for member in history:
        if is_mesh(member):
            # shape 면 transform 으로 올린다
            if cmds.objectType(member) == "mesh":
                parents = cmds.listRelatives(member, parent=True) or []
                return parents[0] if parents else member
            return member
    return None


def find_blendshapes_from_selection():
    """현재 선택에서 blendShape 노드를 수집.

    - 선택이 blendShape 노드면 그대로 사용.
    - 선택이 메시/transform 이면 그 히스토리에서 blendShape 를 찾는다.
    중복 없이 순서를 보존해 반환.
    """
    sel = cmds.ls(sl=True, long=False) or []
    result = []
    for node in sel:
        if is_blendshape(node):
            if node not in result:
                result.append(node)
            continue
        history = cmds.listHistory(node) or []
        for h in history:
            if cmds.nodeType(h) == "blendShape" and h not in result:
                result.append(h)
    return result
