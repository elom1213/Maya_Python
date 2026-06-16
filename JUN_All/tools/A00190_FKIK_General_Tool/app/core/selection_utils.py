# -*- coding: utf-8 -*-
"""
selection_utils - 선택/리스트/위치 유틸 (씬 조회 헬퍼).

레거시 BF_* / JUN_get_* / JUN_average_* / JUN_parent 함수를 이식했다.
모든 함수는 컨트롤 이름 문자열 리스트(list[str])를 받고 돌려준다(UI/위젯 비의존).
"""

import maya.cmds as cmds


def remove_duplicates(items):
    """순서를 보존하며 중복을 제거한다. (구 BF_LIST_remove_repetitionArray)"""
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def make_hierarchy_without_shape(obj):
    """obj 하위 전체 트랜스폼 계층을 리턴(shape 노드 제외).
    (구 BF_SELECTION_makeList_hierarchy_withoutShape)
    """
    children = cmds.listRelatives(obj, allDescendents=True, path=True)

    if children is None:
        result = [obj]
    else:
        result = list(children)
        result.append(obj)

    shapes = cmds.listRelatives(result, allDescendents=True, path=True, shapes=True)
    if shapes is not None:
        for shape in shapes:
            if shape in result:
                result.remove(shape)

    return result


def make_hierarchy_list(objs, reverse=True, dedup=True):
    """여러 obj 의 계층을 펼쳐 하나의 리스트로. (구 BF_SELECTION_makeList_hierarchy)"""
    result = []
    for obj in objs:
        children = make_hierarchy_without_shape(obj)
        if reverse:
            children.reverse()
        result.extend(children)

    if dedup:
        result = remove_duplicates(result)

    return result


def list_by_shapes(objs, shape_types):
    """shape 타입이 shape_types 중 하나인 obj 만 골라 set 으로. (구 JUN_get_list_by_shapes)"""
    result = set()
    for obj in objs:
        shapes = cmds.listRelatives(obj, allDescendents=True, path=True, shapes=True)
        if shapes is None:
            continue
        obj_type = cmds.objectType(shapes[0])
        for shape_type in shape_types:
            if shape_type in obj_type:
                result.add(obj)
                break
    return result


def set_by_token(objs, tokens):
    """obj 이름에 token 중 하나라도 포함되면 set 에 추가. (구 JUN_get_set_by_token)"""
    result = set()
    for obj in set(objs):
        for token in set(tokens):
            if token in obj:
                result.add(obj)
    return result


def order_by_token(objs, tokens):
    """token 순서대로, token 을 포함하는 obj 들을 모아 정렬된 리스트로.
    (구 JUN_get_list_ordered_by_token — 'is' 문자열 비교 버그를 정상 비교로 수정)
    """
    result = []
    for token in tokens:
        if not token:
            continue
        for obj in objs:
            if not obj:
                continue
            if token in obj:
                result.append(obj)
    return result


def search_by_token(items, token, invert=False):
    """items 중 token 을 포함하는 항목 set. invert=True 면 나머지. (구 JUN_cmd_Search_By_Token 의 순수 로직)"""
    matched = set(obj for obj in items if token in obj)
    if invert:
        return set(items) - matched
    return matched


def world_position(obj):
    """obj 의 월드 좌표 [x, y, z]. (구 JUN_get_world_positions)"""
    return cmds.xform(obj, q=True, ws=True, t=True)


def average_position(points):
    """[[x,y,z], ...] 의 평균 좌표 [x, y, z]. (구 JUN_average_position)"""
    if not points:
        return None
    count = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_z = sum(p[2] for p in points)
    return [sum_x / count, sum_y / count, sum_z / count]


def ensure_parent(child, parent_name):
    """parent_name 그룹이 없으면 만들고 child 를 그 아래로 옮긴다. (구 JUN_parent)"""
    parent = parent_name
    if not cmds.objExists(parent_name):
        parent = cmds.group(em=True, name=parent_name)
    try:
        cmds.parent(child, parent)
    except Exception:
        print("parent fail : {0}  ->  {1}".format(child, parent))
