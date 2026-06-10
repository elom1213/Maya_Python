# -*- coding: utf-8 -*-
"""
pose_connector - pose object 셋업.

원본 get_connected_nodes / JUN_CR_setUp_pose_objects 이식.
pose object 의 Follow/Con attribute 에 연결된 노드를 찾아, Follow 노드로 transform 을
맞추고 Con 노드로 parentConstraint 를 건다.
"""

from .maya_scene import MayaScene


def get_connected_nodes(node, attrs):
    """node 의 각 attribute 에 연결된 노드 목록을 dict 로 반환."""
    result = {}
    for attr in attrs:
        result[attr] = MayaScene.list_connections(node, attr)
    return result


def setup_pose_objects(cage):
    pos_objs = cage.get_pos_objs()
    pos_attr = cage.get_pos_attr()

    for pos_obj in pos_objs:
        node_connected = get_connected_nodes(pos_obj, pos_attr)
        node_to_flw = node_connected[cage.get_pos_attr_flw()]
        node_to_con = node_connected[cage.get_pos_attr_con()]

        MayaScene.match_transforms(node_to_flw, pos_obj, 1, 1, 1, 1)
        MayaScene.parent_constraint(node_to_con, pos_obj, maintain_offset=True)
