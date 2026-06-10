# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00120_FKIK - 선택/리스트 유틸 (maya.cmds, UI 무관)
#
# 레거시 BF_* / JUN_get_* 함수를 현대화한 모듈.

import maya.cmds as cmds


# --------------------------------------------------
# 리스트 유틸
# --------------------------------------------------

def remove_duplicates(items):
    """순서를 유지하며 중복 제거. (레거시 BF_LIST_remove_repetitionArray)"""
    return list(dict.fromkeys(items))


# --------------------------------------------------
# 계층 수집
# --------------------------------------------------

def hierarchy_without_shapes(obj):
    """obj 와 그 모든 하위(shape 제외)를 리스트로. (레거시 _withoutShape)"""
    children = cmds.listRelatives(obj, allDescendents=True, path=True)

    if children is not None:
        result = list(children)
        result.append(obj)
    else:
        result = [obj]

    shapes = cmds.listRelatives(
        result, allDescendents=True, path=True, shapes=True
    )

    if shapes is not None:
        for shape in shapes:
            if shape in result:        # 버그 수정: 없는 항목 remove 시 ValueError 방지
                result.remove(shape)

    return result


def make_hierarchy_list(objs, reverse=False, dedupe=True):
    """여러 top obj 의 계층(shape 제외)을 하나로. (레거시 BF_SELECTION_makeList_hierarchy)"""
    result = []

    for obj in objs:
        children = hierarchy_without_shapes(obj)

        if reverse:
            children.reverse()

        result.extend(children)

    if dedupe:
        result = remove_duplicates(result)

    return result


# --------------------------------------------------
# 필터 / 정렬
# --------------------------------------------------

def filter_by_shape_types(objs, shape_types):
    """첫 하위 shape 의 objectType 이 shape_types 중 하나를 포함하는 obj 만. (레거시 JUN_get_list_by_shapes)"""
    result = set()

    for obj in objs:
        shapes = cmds.listRelatives(
            obj, allDescendents=True, path=True, shapes=True
        )

        if not shapes:
            continue

        obj_type = cmds.objectType(shapes[0])

        for shape_type in shape_types:
            if shape_type in obj_type:
                result.add(obj)
                break

    return result


def filter_by_tokens(objs, tokens):
    """이름에 tokens 중 하나라도 포함하는 obj 의 집합. (레거시 JUN_get_set_by_token)"""
    result = set()

    for obj in objs:
        for token in tokens:
            if token in obj:
                result.add(obj)
                break

    return result


def order_by_tokens(objs, tokens):
    """tokens 순서대로 매칭되는 obj 를 모아 정렬 리스트로. (레거시 JUN_get_list_ordered_by_token)

    버그 수정: 빈 문자열 비교 `is ""` -> falsy 체크.
    """
    result = []

    for token in tokens:
        if not token:                 # 빈 토큰 skip
            continue
        for obj in objs:
            if not obj:               # 빈 이름 skip
                continue
            if token in obj:
                result.append(obj)

    return result


# --------------------------------------------------
# 리스트 항목 이동 (0-based 인덱스, Qt QListWidget 용)
# --------------------------------------------------

def move_up(items, indices):
    """선택 인덱스(0-based)를 한 칸 위로. (new_items, new_indices) 반환."""
    items = list(items)
    new_indices = []

    for idx in sorted(indices):
        if idx > 0:
            items[idx - 1], items[idx] = items[idx], items[idx - 1]
            new_indices.append(idx - 1)
        else:
            new_indices.append(idx)

    return items, new_indices


def move_down(items, indices):
    """선택 인덱스(0-based)를 한 칸 아래로. (new_items, new_indices) 반환."""
    items = list(items)
    new_indices = []

    for idx in sorted(indices, reverse=True):
        if idx < len(items) - 1:
            items[idx + 1], items[idx] = items[idx], items[idx + 1]
            new_indices.append(idx + 1)
        else:
            new_indices.append(idx)

    return items, sorted(new_indices)
