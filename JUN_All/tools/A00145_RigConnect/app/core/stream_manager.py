# -*- coding: utf-8 -*-
"""
stream_manager - List Connected 탭 로직.

MEL ConnectionTool V04.02 의 노드 그래프 탐색 proc 포팅:
  - JUN_cmd_listStream        -> list_stream_types
  - JUN_cmd_update_streamNods -> nodes_by_types

hyperShade 의 -listUpstreamNodes / -listDownstreamNodes 로 연결된 노드를 모은다.
MEL 은 방향을 전역 변수($GLB_..._streamTyp)로 보관했지만, 여기서는 upstream(bool)
인자로 명시 전달한다(전역 제거 — UI 가 상태를 보관).
"""

import maya.cmds as cmds
import maya.mel as mel


def _stream_nodes(obj, upstream):
    """obj 의 up/down stream 노드 리스트. (hyperShade 그대로 mel.eval)"""
    flag = "-listUpstreamNodes" if upstream else "-listDownstreamNodes"
    nodes = mel.eval('hyperShade {0} {1}'.format(flag, obj))
    return nodes or []


def list_stream_types(objs, upstream):
    """objs 의 up/down stream 노드들의 노드 타입 목록(중복 제거, 순서 유지).

    Args:
        objs: 대상 오브젝트 리스트.
        upstream: True 면 upstream, False 면 downstream.

    Returns:
        노드 타입 문자열 리스트.
    """
    seen = []
    for obj in objs:
        for node in _stream_nodes(obj, upstream):
            node_type = cmds.nodeType(node)
            if node_type not in seen:
                seen.append(node_type)
    return seen


def nodes_by_types(objs, types, upstream):
    """objs 의 stream 노드 중 선택된 타입에 해당하는 노드 목록.

    Args:
        objs: 대상 오브젝트 리스트.
        types: 필터할 노드 타입 리스트.
        upstream: True 면 upstream, False 면 downstream (list_stream_types 와 동일 방향).

    Returns:
        노드 이름 문자열 리스트.
    """
    type_set = set(types)
    result = []
    for obj in objs:
        for node in _stream_nodes(obj, upstream):
            if cmds.nodeType(node) in type_set:
                result.append(node)
    return result
