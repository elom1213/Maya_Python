# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00260_ConstraintConverter - 마야 씬의 컨스트레인트를 읽어 데이터로 변환

from dataclasses import dataclass, field

import maya.cmds as cmds


# 변환을 지원하는 마야 컨스트레인트 노드 타입.
# (UE Control Rig 의 Parent Constraint 노드 하나로 모두 매핑한다)
CONSTRAINT_TYPES = (
    "parentConstraint",
    "pointConstraint",
    "orientConstraint",
    "scaleConstraint",
)


@dataclass
class ConstraintData:
    """한 컨스트레인트의 변환에 필요한 최소 정보."""
    name    : str                       # 컨스트레인트 노드 이름
    ctype   : str                       # 마야 컨스트레인트 타입
    child   : str                       # 컨스트레인 대상(피구속) 본/오브젝트 짧은 이름
    targets : list = field(default_factory=list)   # [(bone_name, weight), ...]


def short_name(node):
    """DAG 경로/네임스페이스를 제거한 짧은 이름 반환 (UE 본 이름과 매칭)."""
    if node is None:
        return ""
    name = node.split("|")[-1]
    name = name.split(":")[-1]
    return name


def find_constraints_from_selection():
    """현재 선택에서 컨스트레인트 노드를 모은다.

    선택 항목이 컨스트레인트면 그대로, 트랜스폼이면 그 아래(또는 연결된)
    컨스트레인트를 찾아 반환한다. 중복은 제거하고 순서는 유지한다.
    """
    sel = cmds.ls(sl=True, long=False) or []
    found = []

    for node in sel:
        node_type = cmds.nodeType(node)

        if node_type in CONSTRAINT_TYPES:
            _append_unique(found, node)
            continue

        # 트랜스폼이면 자식 컨스트레인트를 수집
        children = cmds.listRelatives(node, type="constraint", fullPath=False) or []
        for c in children:
            if cmds.nodeType(c) in CONSTRAINT_TYPES:
                _append_unique(found, c)

    return found


def read_constraint(constraint_node):
    """컨스트레인트 노드 하나를 ConstraintData 로 읽는다. 실패 시 None."""
    if not cmds.objExists(constraint_node):
        return None

    ctype = cmds.nodeType(constraint_node)
    if ctype not in CONSTRAINT_TYPES:
        return None

    constraint_fn = getattr(cmds, ctype)

    target_list = constraint_fn(constraint_node, q=True, targetList=True) or []
    weight_aliases = constraint_fn(constraint_node, q=True, weightAliasList=True) or []

    targets = []
    for idx, tgt in enumerate(target_list):
        weight = 1.0
        if idx < len(weight_aliases):
            try:
                weight = cmds.getAttr(
                    "{0}.{1}".format(constraint_node, weight_aliases[idx])
                )
            except Exception:
                weight = 1.0
        targets.append((short_name(tgt), float(weight)))

    child = _driven_node(constraint_node)

    return ConstraintData(
        name    = constraint_node,
        ctype   = ctype,
        child   = short_name(child),
        targets = targets,
    )


def _driven_node(constraint_node):
    """컨스트레인 대상(피구속 트랜스폼) 반환. 컨스트레인트 노드의 부모."""
    parents = cmds.listRelatives(constraint_node, parent=True, fullPath=False) or []
    if parents:
        return parents[0]
    return constraint_node


def _append_unique(lst, item):
    if item not in lst:
        lst.append(item)
