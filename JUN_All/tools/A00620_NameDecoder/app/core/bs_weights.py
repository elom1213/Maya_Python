# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00620_NameDecoder - Blend Shapes 탭: 타겟을 풀린 이름으로 보고 웨이트를 바꾼다 (maya.cmds)
#
# Shape Editor · 채널 박스는 FBXASC 이름 그대로라 읽을 수 없다. 여기서는 웨이트 setAttr 만 한다(키는 찍지 않는다).
# 웨이트에 연결이 들어와 있거나 잠겨 있으면 바꾸지 않는다(source 로 알려 준다).

import maya.cmds as cmds

from Framework.core import fbx_name
from Framework.core import maya_fbx_names
from Framework.core.maya_undo import undo_chunk


class TargetRow(object):
    __slots__ = ("index", "alias", "decoded", "plug", "source", "locked")

    def __init__(self, bs, index, alias):
        self.index = index
        self.alias = alias
        self.decoded = fbx_name.decode(alias)
        self.plug = "{0}.weight[{1}]".format(bs, index)
        self.source = (cmds.listConnections(self.plug, source=True, destination=False, plugs=True) or [None])[0]
        self.locked = bool(cmds.getAttr(self.plug, lock=True))

    @property
    def editable(self):
        return self.source is None and not self.locked


def blendshape_nodes():
    return sorted(cmds.ls(type="blendShape") or [])


def blendshapes_of_selection():
    """고른 메시(또는 blendShape 자신)의 blendShape."""
    nodes = maya_fbx_names.scope_nodes(maya_fbx_names.SCOPE_SELECTED)
    return [n for n in nodes if cmds.nodeType(n) == "blendShape"]


def targets(bs):
    return [TargetRow(bs, index, alias) for index, alias in maya_fbx_names.blendshape_targets(bs)]


def get_weight(plug):
    return cmds.getAttr(plug)


def set_weight(plug, value):
    cmds.setAttr(plug, float(value))


def reset_all(bs):
    """바꿀 수 있는 웨이트를 전부 0. (바꾼 수, 건너뛴 수) - undo 한 번."""
    changed = skipped = 0
    with undo_chunk():
        for row in targets(bs):
            if not row.editable:
                skipped += 1
                continue
            if abs(cmds.getAttr(row.plug)) > 1e-9:
                cmds.setAttr(row.plug, 0.0)
                changed += 1
    return changed, skipped
