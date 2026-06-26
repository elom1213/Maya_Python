# -*- coding: utf-8 -*-
"""
search / select 핵심 로직 (maya.cmds, UI 비의존).

레거시 JUN_PY_SelectionTool_V02_01 + JUN_PY_SearchTool_V01_02 의 선택/검색 동작을
이식했다. 모든 함수는 '대상 오브젝트 리스트'(보통 Objects TSL 의 전체 항목)를 받아
조건에 맞는 오브젝트를 골라 씬에서 선택하고, 그 리스트를 반환한다.
"""

import maya.cmds as cmds

from .maya_scene import MayaScene


# 'Constraint' 버튼이 매칭할 컨스트레인트 노드 타입들(레거시 GLB_JUN_set_constraint).
CONSTRAINT_TYPES = frozenset({
    "aimConstraint", "orientConstraint", "pointConstraint",
    "scaleConstraint", "parentConstraint",
})


def collect_from_selection(hierarchy):
    """현재 선택을 가져온다. hierarchy 면 각 항목의 계층(자손 transform)까지 펼친다."""
    selection = MayaScene.selection()
    if hierarchy:
        return MayaScene.expand_hierarchy(selection)
    return selection


def collect_types(objects):
    """objects 각 항목의 노드 타입을 모아 정렬된 유니크 리스트로 반환."""
    types = {MayaScene.node_type(obj) for obj in objects}
    return sorted(types)


def select_by_types(objects, type_names, invert=False):
    """objects 중 노드 타입이 type_names 에 속하는 것을 선택한다.

    type_names 는 문자열 1개이거나 문자열 컬렉션(set/list/tuple) 모두 허용.
    invert 면 매칭되지 않은 것(여집합)을 선택한다. 선택된 리스트를 반환.
    """
    if isinstance(type_names, str):
        wanted = {type_names}
    else:
        wanted = set(type_names)

    matched = {obj for obj in objects if MayaScene.node_type(obj) in wanted}

    result = set(objects) - matched if invert else matched
    cmds.select(list(result))
    return list(result)


def select_by_token(objects, token, invert=False):
    """objects 중 이름에 token 문자열을 포함하는 것을 선택한다(invert 면 여집합)."""
    matched = {obj for obj in objects if token in obj}

    result = set(objects) - matched if invert else matched
    cmds.select(list(result))
    return list(result)
