# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00310_SearchTool - Search > Rules 의 규칙 엔진
"""
select_rules - "규칙에 맞는 오브젝트만 고른다" 의 규칙 레지스트리 (maya.cmds, UI 비의존).

규칙은 계속 늘어난다. 그래서 **규칙 하나를 추가하는 일이 함수 하나 + `register()` 한 줄**로
끝나도록 짰다. UI 는 `all_rules()` 가 돌려주는 목록을 그대로 그리므로 **규칙을 더해도 UI 코드는
건드리지 않는다.**

새 규칙 추가하는 법
-------------------
    def _rule_my_thing(obj):
        if 조건에 맞지 않으면:
            return False, "왜 안 맞는지"        # 이유는 로그에 그대로 찍힌다
        return True, ""

    register(SelectRule("my_thing", "My Thing", "한 줄 설명.", _rule_my_thing))

판정 함수는 `(맞는가, 안 맞는 이유)` 를 돌려준다. **이유를 함께 돌려주는 것이 핵심**이다 -
"12개 중 3개만 맞았다" 보다 "나머지 9개는 각각 이래서 빠졌다" 가 훨씬 쓸모 있다.
"""

from collections import OrderedDict

import maya.cmds as cmds


# ==================================================================
# ★ 씬에 기본으로 딸려 오는 연결 - "엮였다" 로 보지 않는다
# ==================================================================
# 실측(mayapy)으로 고른 목록이다. 이걸 빼지 않으면 **아무 메시도 규칙을 통과하지 못한다** -
# 히스토리 없이 만든 폴리큐브에도 `initialShadingGroup` 이 붙어 있기 때문이다.
# 디스플레이 레이어 멤버십과 평범한 셋 멤버십도 마찬가지로 "리깅으로 엮인 것" 이 아니다.
#
# ※ `shadingEngine` 은 `objectSet` 의 **하위 타입**이라 상속으로 판정하면 둘이 같이 걸린다.
#    그래서 여기 이름들은 전부 `objectType()` 이 돌려주는 **정확한 타입 이름**으로 본다.
IGNORED_TYPES = frozenset({
    "shadingEngine",            # 머티리얼 배정
    "materialInfo",
    "displayLayer", "displayLayerManager", "layerManager",
    "objectSet",                # 평범한 셋 멤버십
    "groupId",                  # 면 단위 머티리얼 배정에 딸려 온다
    "nodeGraphEditorInfo", "hyperLayout", "hyperGraphInfo", "hyperView",
})


# ==================================================================
# 규칙
# ==================================================================

class SelectRule(object):
    """규칙 하나. `test(obj) -> (맞는가, 이유)` 를 감싼다.

    key         : 코드에서 부르는 이름(고유).
    label       : UI 리스트에 보이는 이름.
    description : UI 툴팁 / 설명줄에 보이는 한 줄.
    """

    def __init__(self, key, label, description, test):
        self.key = key
        self.label = label
        self.description = description
        self._test = test

    def check(self, obj):
        """(맞는가, 안 맞는 이유). 씬에서 사라진 노드는 조용히 탈락시킨다."""
        if not cmds.objExists(obj):
            return False, "does not exist any more"
        return self._test(obj)

    def matches(self, obj):
        return self.check(obj)[0]


_REGISTRY = OrderedDict()


def register(rule):
    """규칙을 등록한다. 같은 key 면 덮어쓴다(리로드 대비)."""
    _REGISTRY[rule.key] = rule
    return rule


def all_rules():
    """등록된 순서 그대로의 규칙 목록. UI 는 이걸 그려 준다."""
    return list(_REGISTRY.values())


def get_rule(key):
    return _REGISTRY.get(key)


# ==================================================================
# 규칙 적용
# ==================================================================

def filter_objects(objects, keys):
    """objects 중 keys 의 규칙을 **전부** 만족하는 것을 고른다.

    규칙을 여러 개 고르면 AND 다 - 하나라도 어긋나면 빠진다.
    반환: (맞은 것 목록, [(오브젝트, 이유), ...] 탈락 목록)
    """
    rules = [_REGISTRY[key] for key in keys if key in _REGISTRY]
    if not rules:
        return [], []

    matched = []
    rejected = []
    for obj in objects:
        reason = ""
        for rule in rules:
            ok, why = rule.check(obj)
            if not ok:
                reason = why
                break
        if reason:
            rejected.append((obj, reason))
        else:
            matched.append(obj)
    return matched, rejected


def select_by_rules(objects, keys, invert=False):
    """규칙에 맞는 것(invert 면 그 여집합)을 씬에서 선택한다.

    반환: (선택한 목록, 탈락 목록[(오브젝트, 이유)])
    """
    matched, rejected = filter_objects(objects, keys)

    if invert:
        chosen = [obj for obj in objects if obj not in set(matched)]
    else:
        chosen = matched

    if chosen:
        cmds.select(chosen, replace=True)
    else:
        cmds.select(clear=True)
    return chosen, rejected


# ==================================================================
# 노드 검사 헬퍼
# ==================================================================

def _long(node):
    """롱네임 하나. 못 찾으면 받은 이름 그대로.

    ★ 이름 형식을 반드시 맞춰야 한다 - `listHistory` 는 **짧은 이름**을 돌려주는데
    `listRelatives(fullPath=True)` 는 롱네임을 준다. 그대로 비교하면 **자기 셰이프조차
    걸러지지 않아** 히스토리 없는 메시가 "히스토리 있음" 으로 판정된다(실측으로 밟은 함정).
    """
    found = cmds.ls(node, long=True) or []
    return found[0] if found else node


def _self_nodes(obj):
    """자기 자신 + 자기 셰이프(인터미디어트 포함)의 롱네임 집합."""
    nodes = {_long(obj)}
    for shape in cmds.listRelatives(obj, shapes=True, fullPath=True) or []:
        nodes.add(_long(shape))
    return nodes


def _inherits(node, base):
    """node 의 상속 타입 목록에 base 가 있는가(`skinCluster` -> `geometryFilter` 등)."""
    return base in (cmds.nodeType(node, inherited=True) or [])


def _describe(node):
    return "{0} ({1})".format(node.split("|")[-1], cmds.objectType(node))


def _foreign_history(obj, own):
    """자기 자신·셰이프·무시 타입을 뺀 히스토리 노드 목록."""
    found = []
    for node in cmds.listHistory(obj, pruneDagObjects=False) or []:
        path = _long(node)
        if path in own or cmds.objectType(node) in IGNORED_TYPES:
            continue
        found.append(path)
    return found


def _foreign_connections(own):
    """자기 자신·셰이프·무시 타입을 뺀, 들어오고 나가는 모든 연결 상대."""
    found = []
    seen = set()
    for node in own:
        for other in cmds.listConnections(node, source=True, destination=True) or []:
            path = _long(other)
            if path in own or path in seen:
                continue
            if cmds.objectType(other) in IGNORED_TYPES:
                continue
            seen.add(path)
            found.append(path)
    return found


# ==================================================================
# 규칙 1 - Standalone
# ==================================================================

def _rule_standalone(obj):
    """어디에도 엮이지 않은 노드인가.

    컨스트레인트 · 스킨/디포머 · 히스토리 · 어트리뷰트 연결이 **하나도 없어야** 한다.
    부모-자식(DAG)은 DG 연결이 아니므로 **부모가 있어도 통과한다** - 그룹 밑에 있다고
    해서 그 노드가 무언가에 구동되는 것은 아니다(실측 확인).
    """
    own = _self_nodes(obj)

    # 왜 빠졌는지를 구체적으로 말해 주려고 히스토리를 먼저 종류별로 본다.
    history = _foreign_history(obj, own)
    for node in history:
        if _inherits(node, "constraint"):
            return False, "driven by a constraint - " + _describe(node)
    for node in history:
        if _inherits(node, "geometryFilter"):
            return False, "has a deformer - " + _describe(node)
    if history:
        return False, "has history - " + _describe(history[0])

    connections = _foreign_connections(own)
    for node in connections:
        if _inherits(node, "constraint"):
            return False, "driven by a constraint - " + _describe(node)
    if connections:
        return False, "connected to " + _describe(connections[0])

    return True, ""


register(SelectRule(
    "standalone",
    "Standalone",
    "No connections and no history - nothing drives it and it drives nothing. "
    "Constraints, skin/deformers, history nodes and attribute connections all "
    "disqualify. Being parented under a group does not.",
    _rule_standalone))
