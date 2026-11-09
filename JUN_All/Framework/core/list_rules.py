# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
"""
list_rules - 정해진 규칙대로 오브젝트 목록을 만든다 (공용, TSL `Rules` 버튼이 쓴다).

규칙 하나 = json 파일 하나. 지금 규칙은 **세트(objectSet)가 간직한 오브젝트**를 꺼내는 것이다.
"A01_FingersMC_O_tgt_L 규칙을 고르면 씬의 그 세트 멤버가 리스트에 올라온다."

규칙 폴더
---------
    Framework/rules/list_rules/<Category>/<rule>.json
하위 폴더 이름이 **카테고리**(메뉴의 하위 메뉴)다 — 리그 · 프로젝트마다 묶어 둔다(예: `Cage_v02`).
폴더 바로 아래 json 은 카테고리 없이 메뉴 맨 위에 놓인다. 새 규칙은 파일만 더하면 된다(코드 변경 없음).
Framework 폴더라 릴리즈 빌드에도 함께 들어간다.

json 모양
---------
    {
      "name": "A01_FingersMC_O_tgt_L",          # 메뉴에 보이는 이름
      "description": "...",                     # 툴팁 (선택)
      "sets": ["A01_FingersMC_O_tgt_L"],        # 멤버를 모을 세트 이름들(네임스페이스 없이). 여럿이면 합집합
      "order": "set",                           # "set"(기본, 세트 안 원본 순서) | "name"
      "expand_nested": true                     # 멤버 중 세트는 펼쳐 그 멤버를 담는다(기본 true)
    }

네임스페이스
-----------
세트 이름은 네임스페이스 없이 적는다. 씬에서는 **어느 네임스페이스에 있든**(`ns:A01_...`, `a:b:A01_...`) 찾는다
(`cmds.ls(name, recursive=True)`). 같은 세트가 **여러 네임스페이스**에 있으면(같은 리그를 두 번 레퍼런스)
어느 쪽인지 자동으로 고를 수 없으므로 `resolve_rule` 이 `ambiguous` 로 돌려주고, 호출부(TSL)가 사용자에게 묻는다.

순서 (`order`)
-------------
기본 `"set"` = **세트 안 원본 순서** — 세트의 `dagSetMembers[0], [1], …`(DAG 멤버) 다음 `dnSetMembers[…]`(DG 멤버)
**배열 인덱스 순서**다. 세트를 만들 때 · 멤버를 더할 때의 순서가 여기 남는다(파일에 저장되는 순서).
**`cmds.sets -q` 의 순서는 이것이 아니다** — 넣은 순서도 이름 순서도 아니고 **같은 파일을 열 때마다 달라진다**
(Cage_v002_0130 실측: `B03_leg_drv_L` 배열 = leg, knee, ankle, foot, toe / `sets -q` = leg, ankle, foot, knee, toe,
다른 실행에선 또 다름). 그래서 멤버 이름은 `sets -q` 로 받되 **자리는 배열 인덱스로** 정한다(`set_members`).
`"name"` = 네임스페이스를 뺀 이름순.
"""

import io
import json
import os
import re


RULES_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules", "list_rules"))

ORDER_NAME = "name"
ORDER_SET = "set"
ORDERS = (ORDER_NAME, ORDER_SET)

_BAD_FILE_CHARS = re.compile(r'[^0-9A-Za-z_.\-]+')


# =====================================================================
# 규칙 (DCC 비의존)
# =====================================================================

class ListRule(object):
    """규칙 하나."""

    def __init__(self, name, sets, description="", order=ORDER_SET,
                 expand_nested=True, category="", path=None):
        self.name = name
        self.sets = list(sets)
        self.description = description or ""
        self.order = order if order in ORDERS else ORDER_SET
        self.expand_nested = bool(expand_nested)
        self.category = category or ""
        self.path = path

    def to_dict(self):
        return {"name": self.name, "description": self.description, "sets": list(self.sets),
                "order": self.order, "expand_nested": self.expand_nested}

    def tooltip(self):
        lines = []
        if self.description:
            lines.append(self.description)
        lines.append("Sets: " + ", ".join(self.sets))
        lines.append("Order: " + ("by name" if self.order == ORDER_NAME else "as stored in the set (original order)"))
        if self.path:
            lines.append(self.path)
        return "\n".join(lines)

    def __repr__(self):
        return "ListRule({0!r}, {1!r})".format(self.name, self.sets)


def _rule_from_dict(data, category, path):
    if not isinstance(data, dict):
        raise ValueError("not a json object")
    name = data.get("name") or os.path.splitext(os.path.basename(path))[0]
    sets = data.get("sets")
    if isinstance(sets, str):
        sets = [sets]
    if not sets or not all(isinstance(s, str) and s.strip() for s in sets):
        raise ValueError("'sets' must be a non-empty list of set names")
    return ListRule(name=name, sets=[s.strip() for s in sets],
                    description=data.get("description", ""),
                    order=data.get("order", ORDER_SET),
                    expand_nested=data.get("expand_nested", True),
                    category=category, path=path)


def load_rules(rules_dir=None):
    """규칙 폴더를 읽는다. 반환 (rules, errors).

    rules  : 카테고리('' 가 먼저) → 이름 순으로 정렬한 ListRule 목록
    errors : [(path, 사유)] - 깨진 json · 형식 오류. 나머지 규칙은 그대로 쓴다.
    하위 폴더는 한 단계만 본다(폴더 이름 = 카테고리).
    """
    root = rules_dir or RULES_DIR
    rules, errors = [], []
    if not os.path.isdir(root):
        return rules, errors

    def read(path, category):
        try:
            with io.open(path, encoding="utf-8") as f:
                rules.append(_rule_from_dict(json.load(f), category, path))
        except Exception as exc:          # 깨진 파일 하나가 메뉴 전체를 막지 않게
            errors.append((path, str(exc)))

    for entry in sorted(os.listdir(root)):
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            for fname in sorted(os.listdir(full)):
                if fname.lower().endswith(".json"):
                    read(os.path.join(full, fname), entry)
        elif entry.lower().endswith(".json"):
            read(full, "")

    rules.sort(key=lambda r: (r.category != "", r.category.lower(), r.name.lower()))
    return rules, errors


def categories(rules):
    """[(category, [rules])] - 규칙 순서 유지."""
    out = []
    for rule in rules:
        if not out or out[-1][0] != rule.category:
            out.append((rule.category, []))
        out[-1][1].append(rule)
    return out


def safe_folder_name(name):
    """카테고리 이름 -> 폴더 이름(금지 문자는 `_`, 빈 값은 '')."""
    return _BAD_FILE_CHARS.sub("_", (name or "").strip()).strip("._")


def rule_file_name(name):
    """규칙 이름 -> 파일 이름(금지 문자는 `_`)."""
    base = _BAD_FILE_CHARS.sub("_", name.strip()).strip("._") or "rule"
    return base + ".json"


def save_rule(rule, rules_dir=None, overwrite=False):
    """규칙을 <rules_dir>/<category>/<name>.json 에 쓴다. 반환 경로.

    이미 있으면 overwrite=False 일 때 FileExistsError.
    """
    root = rules_dir or RULES_DIR
    folder = os.path.join(root, rule.category) if rule.category else root
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = os.path.join(folder, rule_file_name(rule.name))
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(path)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rule.to_dict(), indent=2, ensure_ascii=False) + "\n")
    rule.path = path
    return path


def strip_namespace(name):
    """'|a:grp|ns:obj.vtx[0]' -> 'obj.vtx[0]' (경로 · 네임스페이스 제거)."""
    leaf = name.split("|")[-1]
    node, dot, comp = leaf.partition(".")
    return node.split(":")[-1] + dot + comp


def namespace_of(node):
    """'ns:sub:set' -> 'ns:sub', 루트는 ''."""
    leaf = node.split("|")[-1]
    return leaf.rpartition(":")[0]


def sort_items(items, order):
    if order == ORDER_SET:
        return list(items)
    return sorted(items, key=lambda n: (strip_namespace(n).lower(), n))


# =====================================================================
# 마야 - 세트 해석
# =====================================================================

class RuleResult(object):
    """resolve_rule 결과."""

    def __init__(self):
        self.items = []          # 리스트에 올릴 이름(순서 적용)
        self.used_sets = []      # 실제로 읽은 세트 노드
        self.missing = []        # 씬에서 못 찾은 세트 이름
        self.ambiguous = {}      # 세트 이름 -> 여러 네임스페이스의 후보 (namespace 를 정해 다시 부를 것)
        self.empty_sets = []     # 찾았지만 멤버가 없던 세트

    @property
    def ok(self):
        return not self.ambiguous


def _cmds():
    import maya.cmds as cmds
    return cmds


def find_sets(set_name):
    """어느 네임스페이스든 그 이름의 objectSet 노드들."""
    cmds = _cmds()
    found = cmds.ls(set_name, recursive=True, type="objectSet") or []
    # recursive 는 짧은 이름이 같은 다른 네임스페이스도 잡는다 - 잎 이름이 정확히 같은 것만
    return [n for n in found if strip_namespace(n) == set_name]


def rule_namespaces(rule):
    """규칙의 세트들이 있는 네임스페이스 목록(정렬, 루트는 '')."""
    spaces = set()
    for name in rule.sets:
        for node in find_sets(name):
            spaces.add(namespace_of(node))
    return sorted(spaces)


def _member_array(set_node):
    """세트 멤버 배열의 원본 순서 = [연결된 노드 long name] (dagSetMembers 인덱스 순 -> dnSetMembers 인덱스 순).

    컴포넌트 멤버는 셰이프의 objectGroups 가 연결되므로 셰이프가 나온다.
    """
    cmds = _cmds()
    out = []
    for attr in ("dagSetMembers", "dnSetMembers"):
        if not cmds.attributeQuery(attr, node=set_node, exists=True):
            continue
        for i in cmds.getAttr("{0}.{1}".format(set_node, attr), multiIndices=True) or []:
            src = cmds.listConnections("{0}.{1}[{2}]".format(set_node, attr, i),
                                       source=True, destination=False, shapes=True) or []
            for node in src:
                long = cmds.ls(node, long=True) or [node]
                out.append(long[0])
    return out


def ordered_members(set_node):
    """세트의 직속 멤버를 **원본 순서**(멤버 배열 인덱스)로.

    이름 · 컴포넌트 표기는 `cmds.sets -q` 그대로 쓰고, 자리만 배열에서 찾는다. 배열에서 못 찾은 멤버는
    (있을 일은 드물다) `sets -q` 순서대로 뒤에 붙인다.
    """
    cmds = _cmds()
    members = cmds.sets(set_node, q=True) or []
    rank = {}
    for pos, node in enumerate(_member_array(set_node)):
        rank.setdefault(node, pos)
        # 컴포넌트는 셰이프가 연결되지만 sets -q 는 트랜스폼 이름으로 적는다
        if cmds.objectType(node, isAType="shape"):
            parent = cmds.listRelatives(node, parent=True, fullPath=True) or []
            if parent:
                rank.setdefault(parent[0], pos)

    def key(item):
        node = item.split(".")[0]
        long = cmds.ls(node, long=True) or [node]
        return rank.get(long[0], len(rank) + members.index(item))

    return sorted(members, key=key)


def set_members(set_node, expand_nested=True, _seen=None):
    """세트 멤버(이름, 원본 순서). expand_nested 면 멤버 세트를 **그 자리에서** 펼친다(순환 안전)."""
    cmds = _cmds()
    seen = _seen if _seen is not None else set()
    if set_node in seen:
        return []
    seen.add(set_node)
    out = []
    for member in ordered_members(set_node):
        if expand_nested and "." not in member and cmds.objExists(member) \
                and cmds.nodeType(member) == "objectSet":
            out.extend(set_members(member, True, seen))
        else:
            out.append(member)
    return out


def resolve_rule(rule, namespace=None):
    """규칙 -> RuleResult.

    namespace=None : 세트가 한 군데에서만 찾히면 그것. 여러 네임스페이스면 ambiguous 에 담고 items 는 비운다.
    namespace='ns' : 그 네임스페이스의 세트만('' = 루트).
    """
    result = RuleResult()
    picked = []
    for name in rule.sets:
        found = find_sets(name)
        if namespace is not None:
            found = [n for n in found if namespace_of(n) == namespace]
        if not found:
            result.missing.append(name)
        elif len(found) > 1:
            result.ambiguous[name] = found
        else:
            picked.append(found[0])
    if result.ambiguous:
        return result

    seen = set()
    items = []
    for node in picked:
        result.used_sets.append(node)
        members = set_members(node, rule.expand_nested)
        if not members:
            result.empty_sets.append(node)
        for m in members:
            if m not in seen:
                seen.add(m)
                items.append(m)
    result.items = sort_items(items, rule.order)
    return result


def selected_sets():
    """현재 선택 중 objectSet 노드(아웃라이너에서 세트를 고른 경우)."""
    cmds = _cmds()
    return cmds.ls(selection=True, type="objectSet") or []


def rules_from_sets(set_nodes, category="", order=ORDER_SET):
    """세트 노드들 -> 규칙(세트 하나 = 규칙 하나, 이름 = 네임스페이스를 뺀 세트 이름)."""
    out = []
    for node in set_nodes:
        name = strip_namespace(node)
        out.append(ListRule(name=name, sets=[name], order=order, category=category))
    return out
