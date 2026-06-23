# -*- coding: utf-8 -*-
"""
target_builder - 노드 타입에 따라 blendShape target 또는 attribute 를 생성하는 디스패처.

"Mesh / Node" 필드에 넣은 노드가
  - mesh(폴리곤 지오메트리)면  -> Rule mapping 이름으로 blendShape target 생성(+deformer).
  - 그 외(joint/transform/control 등)면 -> Rule mapping 이름으로 attribute 생성.

정책(어떤 매니저를 쓸지 결정)을 한 곳에 모아 두어 UI 와 각 매니저를 얇게 유지한다.
(app/core ↔ app/ui 분리)
"""

import maya.cmds as cmds

from .blendshape_manager import BlendShapeManager
from .attribute_manager import AttributeManager


class TargetBuilder:

    @staticmethod
    def is_mesh(node):
        """node(또는 그 shape)가 폴리곤 mesh 면 True."""
        if not cmds.objExists(node):
            return False
        if cmds.objectType(node) == "mesh":
            return True
        shapes = cmds.listRelatives(
            node, shapes=True, type="mesh", fullPath=True) or []
        return bool(shapes)

    @staticmethod
    def build(rule, node):
        """node 타입에 맞춰 target 또는 attribute 를 생성한다.

        Args:
            rule: ConnectionRule (mapping 이름 목록 보유).
            node: 대상 노드명.

        Returns:
            ("blendshape" | "attribute", result) 튜플.
            result 는 blendShape 노드명 또는 node 명.
        """
        if not cmds.objExists(node):
            raise RuntimeError(f"Node not found : {node}")

        if TargetBuilder.is_mesh(node):
            bs = BlendShapeManager.create_blendshape(rule, node)
            return ("blendshape", bs)

        AttributeManager.create(rule, node)
        return ("attribute", node)
