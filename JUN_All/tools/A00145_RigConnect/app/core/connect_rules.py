# -*- coding: utf-8 -*-
"""
connect_rules - Connect 탭의 **규칙 연결** (v01.59).

정해진 어트리뷰트 묶음을 이름으로 잇는 작업(예: Apple ARKit 52 페이셜)은 코드에 박아 두지 않고
`app/rules/connect/<rule>.json` 로 둔다. 파일 하나가 규칙 하나다 — 새 규칙은 json 을 더하면 되고
코드는 손대지 않는다. UI 는 `load_rules()` 가 돌려준 목록을 콤보에 올리고 `connect_by_rule` 로 잇는다.

규칙 json
--------
    {
      "name": "Apple ARKit 52 Facial Target",      # 화면에 보이는 이름 (없으면 파일 이름)
      "description": "...",                        # 툴팁
      "attributes": ["browInnerUp", ...],          # 같은 이름끼리 Source.X -> Destination.X
      "pairs": [["srcAttr", "dstAttr"], ...]       # 이름이 다를 때 (선택)
    }

`attributes` 와 `pairs` 는 함께 써도 된다. 둘을 합쳐 (source_attr, destination_attr) 목록이 된다.

연결 규칙 (MEL JUN_cmd_connect_52Facial 그대로)
----------------------------------------------
오브젝트는 행 순서대로 1:1 (짧은 쪽 길이만큼). 쌍마다 모든 어트리뷰트 짝을 `connectAttr -force` 로
잇고, 어느 한쪽에 없는 어트리뷰트는 건너뛴다.

UI 비의존: maya.cmds 는 connect_by_rule 에서만 쓴다 (load_rules 는 standalone 에서도 돈다).
"""

import io
import json
import os

# app/rules/connect/ - 이 파일(app/core/connect_rules.py) 기준.
RULES_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "rules", "connect"))


class ConnectRule(object):
    """규칙 하나. pairs = [(source_attr, destination_attr), ...] (파일 순서)."""

    def __init__(self, name, pairs, description="", path=""):
        self.name = name
        self.pairs = list(pairs)
        self.description = description or ""
        self.path = path

    def __repr__(self):
        return "ConnectRule({0!r}, {1} pair(s))".format(self.name, len(self.pairs))


def _normalize(data, fallback_name, path):
    """json dict -> ConnectRule. 모양이 틀리면 ValueError."""
    if not isinstance(data, dict):
        raise ValueError("top level must be an object")

    name = str(data.get("name") or fallback_name).strip()
    pairs = []

    attrs = data.get("attributes") or []
    if not isinstance(attrs, list):
        raise ValueError("'attributes' must be a list")
    for attr in attrs:
        if not isinstance(attr, str) or not attr.strip():
            raise ValueError("'attributes' must hold attribute names")
        pairs.append((attr.strip(), attr.strip()))

    raw_pairs = data.get("pairs") or []
    if not isinstance(raw_pairs, list):
        raise ValueError("'pairs' must be a list")
    for pair in raw_pairs:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or not all(isinstance(p, str) and p.strip() for p in pair)):
            raise ValueError("each of 'pairs' must be [sourceAttr, destinationAttr]")
        pairs.append((pair[0].strip(), pair[1].strip()))

    if not pairs:
        raise ValueError("no attributes - give 'attributes' and / or 'pairs'")

    return ConnectRule(name, pairs, str(data.get("description") or ""), path)


def load_rules(rules_dir=None):
    """규칙 폴더의 모든 json 을 읽는다.

    Returns:
        (rules, errors)
        rules  : [ConnectRule...] 이름순.
        errors : [(file_name, message)...] 읽지 못한 파일 (깨진 json, 모양 틀림).
    """
    rules_dir = rules_dir or RULES_DIR
    rules = []
    errors = []
    if not os.path.isdir(rules_dir):
        return rules, errors

    for file_name in sorted(os.listdir(rules_dir)):
        if not file_name.lower().endswith(".json"):
            continue
        path = os.path.join(rules_dir, file_name)
        fallback = os.path.splitext(file_name)[0]
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            rules.append(_normalize(data, fallback, path))
        except Exception as e:
            errors.append((file_name, str(e)))

    rules.sort(key=lambda r: r.name.lower())
    return rules, errors


def find_rule(name, rules_dir=None):
    """이름으로 규칙 하나 (없으면 None)."""
    for rule in load_rules(rules_dir)[0]:
        if rule.name == name:
            return rule
    return None


def connect_by_rule(src_objs, dst_objs, rule):
    """규칙의 어트리뷰트 짝을 src -> dst 로 일괄 연결.

    오브젝트는 행 순서대로 1:1 (짧은 쪽 길이만큼). 어느 한쪽에 없는 어트리뷰트는 건너뛴다.

    Returns:
        (connected_count, skipped_count, object_pairs)
    """
    import maya.cmds as cmds

    if not src_objs or not dst_objs:
        raise ValueError("Source/Destination object list is empty.")
    if rule is None or not rule.pairs:
        raise ValueError("Rule has no attributes.")

    smaller = min(len(src_objs), len(dst_objs))
    connected = 0
    skipped = 0

    for i in range(smaller):
        src = src_objs[i]
        dst = dst_objs[i]
        for src_attr, dst_attr in rule.pairs:
            try:
                cmds.connectAttr(
                    "{0}.{1}".format(src, src_attr),
                    "{0}.{1}".format(dst, dst_attr),
                    force=True)
                connected += 1
            except Exception:
                # 소스/타겟에 해당 어트리뷰트가 없으면 스킵 (MEL catch 동작).
                skipped += 1

    return connected, skipped, smaller
