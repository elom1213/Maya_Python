# -*- coding: utf-8 -*-
"""
blendshape_utils - blendShape 타겟 조회 헬퍼 (UI 비의존).

blendShape 의 타겟 이름은 별도 어트리뷰트가 아니라 `weight[i]` 멀티에 걸린 **별칭(alias)** 이다.
그래서 `listAttr(bs, userDefined=True)` 로는 `attributeAliasList` 밖에 안 나오고,
`weight` 멀티를 펼쳐도 인덱스 0 하나만 잡힌다. 타겟 이름은 `aliasAttr` 에서 직접 읽어야 한다.

Attribute 탭과 Connect 탭이 함께 쓴다.
(같은 로직이 A00290_BSTool/app/core/blendshape_utils.py 에도 있지만, 툴 간 import 는 하지 않는다.)
"""

import re

import maya.cmds as cmds


def is_blendshape(node):
    """node 가 blendShape 노드인가."""
    return bool(node) and cmds.objExists(node) and \
        cmds.nodeType(node) == "blendShape"


def _weight_index(attr):
    """'weight[3]' -> 3. 못 찾으면 -1."""
    match = re.search(r"\[(\d+)\]", attr)
    return int(match.group(1)) if match else -1


def get_blendshape_targets(node):
    """blendShape 타겟(별칭) 이름을 weight 인덱스 순으로 반환한다.

    blendShape 가 아니면 빈 리스트.
    """
    if not is_blendshape(node):
        return []

    # aliasAttr 은 [alias1, attr1, alias2, attr2, ...] 평면 리스트로 준다.
    aliases = cmds.aliasAttr(node, query=True) or []
    pairs = [(aliases[i], aliases[i + 1]) for i in range(0, len(aliases) - 1, 2)]
    # weight[...] 별칭만 남긴다(다른 별칭이 섞일 수 있다).
    pairs = [p for p in pairs if p[1].startswith("weight")]
    pairs.sort(key=lambda p: _weight_index(p[1]))
    return [alias for alias, _attr in pairs]
