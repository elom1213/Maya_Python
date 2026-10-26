# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - 씬에서 규칙에 맞는 세트를 찾고 멤버를 펼친다 (maya.cmds, 워커 안)  (v01.41)
#
#   find_sets(rule)                       : 씬의 모든 objectSet 중 규칙에 맞는 것 (최상위든 다른 세트 안이든 - 세트는 DG 노드라 전부 나온다)
#   set_members_dag(set_name)             : 멤버 -> 트랜스폼/조인트 long name (하위 세트는 재귀, 컴포넌트는 그 오브젝트, 셰이프는 트랜스폼)
#   collect_targets(set_names, joints_only): 멤버마다 Framework.core.maya_fbx.collect_export_nodes (컨스트레인트는 늘 뺀다) 합집합
#   roots_of(nodes)                       : 조상이 목록에 없는 노드 (설계 D9b - 월드로 뺄 루트)
# 실측 2026-10-26: 레퍼런스 안에 정의된 세트는 `CHN:Bake` 로 보이고 멤버는 `|CHN:rig_grp|CHN:root` 처럼 long name 으로 온다.
#                  임포트 + 네임스페이스 제거 뒤에는 `Bake` / `|rig_grp|root`.

try:
    from . import set_rules
except ImportError:          # mayapy 워커가 평범한 모듈로 import 할 때
    import set_rules

from Framework.core import maya_fbx

# 마야 기본 세트 - 규칙이 "contains" 여도 걸리지 않게 뺀다
_BUILTIN_SETS = ("defaultLightSet", "defaultObjectSet", "initialParticleSE", "initialShadingGroup")


def _cmds():
    import maya.cmds as cmds
    return cmds


def all_sets():
    cmds = _cmds()
    out = []
    for s in cmds.ls(type="objectSet") or []:
        if s in _BUILTIN_SETS:
            continue
        try:
            if cmds.nodeType(s) != "objectSet":      # shadingEngine 등 파생 타입은 뺀다
                continue
        except RuntimeError:
            continue
        out.append(s)
    return out


def find_sets(rule):
    """규칙에 맞는 세트 이름들 (씬 순서)."""
    return [s for s in all_sets() if set_rules.name_matches(s, rule)]


def set_members_dag(set_name, _seen=None):
    """세트 멤버 -> DAG 트랜스폼 long name 목록(중복 없이, 순서 유지)."""
    cmds = _cmds()
    seen = set() if _seen is None else _seen
    if set_name in seen:
        return []
    seen.add(set_name)
    out = []
    for member in cmds.sets(set_name, q=True) or []:
        try:
            node_type = cmds.nodeType(member)
        except RuntimeError:
            continue
        if node_type == "objectSet":
            out.extend(set_members_dag(member, seen))
            continue
        for node in cmds.ls(member, objectsOnly=True, long=True) or []:
            if cmds.nodeType(node) != "transform" and "transform" not in (cmds.nodeType(node, inherited=True) or []):
                # 셰이프 -> 트랜스폼
                parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
                if not parents:
                    continue
                node = parents[0]
            if node not in out:
                out.append(node)
    return out


def collect_targets(set_names, joints_only=True):
    """(kept, pruned) - 멤버 + 자손. 컨스트레인트 노드는 늘 뺀다. 둘 다 long name, 중복 없이."""
    kept, pruned, seen = [], [], set()
    for set_name in set_names:
        for member in set_members_dag(set_name):
            k, p = maya_fbx.collect_export_nodes(member, [], joints_only=joints_only, prune_constraints=True)
            for node in k:
                if node not in seen:
                    seen.add(node)
                    kept.append(node)
            for node in p:
                if node not in seen:
                    seen.add(node)
                    pruned.append(node)
    # 한 멤버가 다른 멤버의 자손이면 kept 에 두 번 들어오지 않는다(seen). pruned 에 있던 것이 다른 멤버의 kept 로 오면 kept 가 이긴다.
    pruned = [p for p in pruned if p not in set(kept)]
    return kept, pruned


def roots_of(nodes):
    """조상이 nodes 에 없는 노드들 (long name 접두 비교)."""
    node_set = set(nodes)
    roots = []
    for node in nodes:
        parent = node.rsplit("|", 1)[0]
        has_ancestor = False
        while parent:
            if parent in node_set:
                has_ancestor = True
                break
            parent = parent.rsplit("|", 1)[0] if "|" in parent else ""
        if not has_ancestor:
            roots.append(node)
    return roots


def parent_of(node):
    cmds = _cmds()
    parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
    return parents[0] if parents else ""
