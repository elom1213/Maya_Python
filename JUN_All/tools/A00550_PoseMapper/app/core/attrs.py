# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - 노드의 음소 / 타겟 어트리뷰트 목록 (maya.cmds, UI 비의존)
#
# Source(음소) = 숫자형 사용자 어트리뷰트. Target = blendShape 면 타겟 별칭(aliasAttr), 아니면 숫자형 사용자 어트리뷰트.

import maya.cmds as cmds


NUMERIC_TYPES = ("double", "float", "long", "short", "byte", "doubleLinear", "doubleAngle", "floatLinear",
                 "floatAngle", "bool")


def numeric_user_attrs(node):
    """숫자형 · 단일 값 사용자 어트리뷰트 (정의 순서)."""
    out = []
    for a in cmds.listAttr(node, userDefined=True) or []:
        plug = "{0}.{1}".format(node, a)
        try:
            if cmds.attributeQuery(a, node=node, multi=True) or cmds.attributeQuery(a, node=node, listChildren=True):
                continue
            if cmds.getAttr(plug, type=True) in NUMERIC_TYPES:
                out.append(a)
        except (RuntimeError, ValueError):
            continue
    return out


def is_blendshape(node):
    return bool(node) and cmds.objExists(node) and cmds.nodeType(node) == "blendShape"


def blendshape_targets(bs):
    """타겟 별칭을 weight 인덱스 순으로. 별칭이 없는 weight 는 건너뛴다."""
    pairs = cmds.aliasAttr(bs, q=True) or []
    items = []
    for alias, plug in zip(pairs[0::2], pairs[1::2]):
        if plug.startswith("weight["):
            items.append((int(plug[7:-1]), alias))
    return [alias for _i, alias in sorted(items)]


def target_attrs(node):
    return blendshape_targets(node) if is_blendshape(node) else numeric_user_attrs(node)


def plug(node, attr):
    return "{0}.{1}".format(node, attr)


def incoming(plug_name):
    """plug 에 들어오는 연결의 소스 plug (없으면 None). 변환 노드는 건너뛴다."""
    src = cmds.listConnections(plug_name, source=True, destination=False, plugs=True, skipConversionNodes=True)
    return src[0] if src else None
