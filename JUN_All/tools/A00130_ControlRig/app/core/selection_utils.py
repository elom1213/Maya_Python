# -*- coding: utf-8 -*-
"""
selection_utils - 계층/리스트 유틸.

원본의 BF_* / JUN_get_* 전역 함수를 이식. 씬 조회는 MayaScene 어댑터를 통해서만 한다.
UI 비의존.
"""

from .maya_scene import MayaScene


def remove_duplicates(items):
    """리스트에서 중복을 제거(순서 유지). 원본 BF_LIST_remove_repetitionArray."""
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def make_hierarchy_without_shape(obj):
    """
    obj 와 그 하위 descendant 를 모은 뒤 shape 노드를 제거한 리스트 반환.
    원본 BF_SELECTION_makeList_hierarchy_withoutShape.
    """
    children = MayaScene.list_all_descendents(obj)

    result = []
    if children is not None:
        result = children
        result.append(obj)
    else:
        result.append(obj)

    shapes = MayaScene.list_all_descendents(result, shapes=True)
    if shapes is not None:
        for shape in shapes:
            result.remove(shape)

    return result


def make_hierarchy(objs, reverse=False, remove_repetition=False):
    """
    여러 top 오브젝트의 계층을 모은다. 원본 BF_SELECTION_makeList_hierarchy.
    """
    result = []
    for obj in objs:
        children = make_hierarchy_without_shape(obj)
        if reverse:
            children.reverse()
        for child in children:
            result.append(child)

    if remove_repetition:
        result = remove_duplicates(result)

    return result


def get_list_by_shapes(objs, target_shapes):
    """
    하위 shape 타입이 target_shapes 중 하나에 해당하는 오브젝트만 추린다.
    원본 JUN_get_list_by_shapes.
    """
    result = set()
    for obj in objs:
        obj_shapes = MayaScene.list_all_descendents(obj, shapes=True)
        if obj_shapes is not None:
            for target_shape in target_shapes:
                obj_type = MayaScene.object_type(obj_shapes[0])
                if target_shape in obj_type:
                    result.add(obj)
                    break
    return result


def get_set_by_token(objs, tokens):
    """이름에 token 을 포함하는 오브젝트 집합. 원본 JUN_get_set_by_token."""
    result = set()
    for obj in set(objs):
        for token in set(tokens):
            if token in obj:
                result.add(obj)
    return result


def get_list_ordered_by_token(objs, tokens):
    """
    token 순서대로 매칭되는 오브젝트를 정렬해 반환. 원본 JUN_get_list_ordered_by_token.
    (원본의 `is ""` 비교는 `== ""` 로 교정 — 동작 동일)
    """
    result = []
    for token in tokens:
        for obj in objs:
            if token == "":
                break
            if obj == "":
                break
            if token in obj:
                result.append(obj)
    return result


def add_suffix_to_children(parent_object, suffix="_new"):
    """
    parent 와 모든 자식 이름에 suffix 를 붙여 rename. 원본 JUN_add_suffix_to_children.
    """
    child_new = []
    if not MayaScene.exists(parent_object):
        MayaScene.warning(
            "Parent object '{0}' does not exist.".format(parent_object)
        )
        return

    children = MayaScene.list_all_descendents_full_path(parent_object)

    if not children:
        print("Object '{0}' has no children. Nothing to rename.".format(parent_object))
        return

    children = children + [parent_object]
    children.sort(reverse=True)

    for child in children:
        short_name = child.split("|")[-1]
        new_name = short_name + suffix
        renamed_child = MayaScene.rename(child, new_name)
        child_new.append(renamed_child)

    child_new.reverse()
    print("child new : '{0}'...".format(child_new))
    return child_new


# ---------------------------------------------------------------------
# list reorder (UI 리스트 Up/Down 용). 원본 BF_LIST_moveUp/Down_index.
# index 는 1-base (Maya textScrollList selectIndexedItem 규약 유지).
# ---------------------------------------------------------------------

def move_up_index(items, move_index_list):
    result_index_list = []
    for move_index in move_index_list:
        moved = items.pop(move_index - 1)
        items.insert(move_index - 1 - 1, moved)
        result_index_list.append(move_index - 1)
    return [items, result_index_list]


def move_down_index(items, move_index_list):
    move_index_list = list(move_index_list)
    move_index_list.reverse()

    result_index_list = []
    for move_index in move_index_list:
        moved = items.pop(move_index - 1)
        items.insert(move_index - 1 + 1, moved)
        result_index_list.append(move_index)

    result_index_list.reverse()
    return [items, result_index_list]
