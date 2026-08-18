# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00440_SetTool - Maya 세트 입출력
#
# 집합 연산의 전제는 **같은 원소가 항상 같은 문자열이어야 한다**는 것이다.
# 마야는 같은 컴포넌트를 여러 형태로 부른다.
#     pCube1.vtx[0:2]      (세트가 돌려주는 축약형)
#     pCube1Shape.vtx[1]   (셰이프로 선택했을 때)
#     |grp1|pCube1.vtx[1]  (풀 패스)
# 그래서 읽어들이는 모든 경로에서 `cmds.ls(..., flatten=True, long=True)` 로 한 형태로
# 통일한다. mayapy 로 확인한 사실:
#   - 축약 범위(`vtx[0:2]`)가 flatten 으로 펼쳐진다
#   - **셰이프로 선택해도 트랜스폼 롱네임으로 정규화된다** → 선택과 세트 멤버를 직접 비교해도 된다
#   - 동명 노드가 있으면 `cmds.sets(q=True)` 가 알아서 구분되는 부분 경로를 준다
#     (`grp1|pCube1.vtx[0:2]`) → 모호하게 뭉개지지 않는다
#   - 빈 세트는 `None` 을 돌려준다 → 반드시 `or []` 로 받는다
#   - `cmds.sets()` 에 **모호한 짧은 이름을 넘기면 에러**가 난다 → 항상 정규화된 이름으로 넘긴다

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


def canonicalize(items):
    """멤버 문자열들을 비교 가능한 한 형태로 통일한다(펼침 + 롱네임)."""
    if not items:
        return []

    return cmds.ls(items, flatten=True, long=True) or []


def is_object_set(node):
    """objectSet 노드인가. (셰이딩 그룹도 objectSet 이지만 여기서는 구분하지 않는다)"""
    if not node or not cmds.objExists(node):
        return False

    return cmds.nodeType(node) == "objectSet"


def set_members(set_node):
    """세트의 멤버를 정규화해서 돌려준다. 빈 세트면 빈 리스트."""
    return canonicalize(cmds.sets(set_node, q=True) or [])


def nested_sets(set_node):
    """멤버 중 그 자체가 세트인 것들. (집합 연산에서는 원소 하나로 취급된다)"""
    return [m for m in (cmds.sets(set_node, q=True) or []) if is_object_set(m)]


def current_selection():
    """씬에서 지금 선택된 것들을 정규화해서 돌려준다."""
    return canonicalize(cmds.ls(selection=True, flatten=True, long=True) or [])


def create_set(members, name):
    """멤버로 새 세트를 만들고 **실제로 붙은 이름**을 돌려준다.

    이름이 겹치면 마야가 뒤에 번호를 붙이므로 요청한 이름과 다를 수 있다.
    """
    if members:
        return cmds.sets(list(members), name=name)

    return cmds.sets(name=name, empty=True)


def remove_from_set(set_node, members):
    """세트에서 멤버를 뺀다. 들어 있지 않은 것을 빼도 에러가 아니다(무시)."""
    if members:
        cmds.sets(list(members), remove=set_node)


def add_to_set(set_node, members):
    """세트에 멤버를 더한다. 이미 있는 것은 중복되지 않는다."""
    if members:
        cmds.sets(list(members), add=set_node)


def select(members):
    """결과를 씬에서 선택한다. 비어 있으면 선택을 비운다."""
    if members:
        cmds.select(list(members), replace=True)
    else:
        cmds.select(clear=True)


__all__ = [
    "canonicalize",
    "is_object_set",
    "set_members",
    "nested_sets",
    "current_selection",
    "create_set",
    "remove_from_set",
    "add_to_set",
    "select",
    "undo_chunk",
]
