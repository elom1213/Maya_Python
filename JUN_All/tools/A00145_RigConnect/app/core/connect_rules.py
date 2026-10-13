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

규칙 만들기 (v01.60)
-------------------
Connect > Transfer Connection 의 `Save as Rule...` 가 체크한 연결(어트리뷰트 x 노드)을 `save_rule` 로
같은 모양의 json 으로 쓴다 — 같은 이름 짝은 `attributes`, 다른 이름 짝은 `pairs`. 파일 이름은
`rule_file_name(name)` (영문자·숫자 외는 `_`). 저장 뒤 Connect 페이지의 콤보가 다시 읽는다.

UI 비의존: maya.cmds 는 connect_by_rule 에서만 쓴다 (load_rules / save_rule 은 standalone 에서도 돈다).
"""

import io
import json
import os
import re

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


# ----------------------------------------------------------------------
# 규칙 저장 (v01.60 - Transfer Connection > Save as Rule)
# ----------------------------------------------------------------------

def rule_file_name(name):
    """규칙 이름 -> 파일 이름 (확장자 없이). 영문자·숫자 외는 `_` 로, 소문자.

    'Apple ARKit 52 Facial Target' -> 'apple_arkit_52_facial_target'. 비면 'rule'.
    """
    out = re.sub(r"[^0-9A-Za-z]+", "_", str(name or "")).strip("_").lower()
    return out or "rule"


def rule_path(file_name, rules_dir=None):
    """파일 이름 (확장자 있어도 됨) -> 규칙 폴더 안의 절대 경로."""
    file_name = str(file_name or "").strip()
    if not file_name.lower().endswith(".json"):
        file_name += ".json"
    return os.path.join(rules_dir or RULES_DIR, file_name)


def save_rule(name, pairs, description="", file_name=None, rules_dir=None, overwrite=False):
    """규칙 json 을 쓴다. 반환: 쓴 파일의 절대 경로.

    같은 이름의 짝 (a, a) 은 `attributes` 로, 이름이 다른 짝은 `pairs` 로 나눠 적는다 (읽을 때와 같은 모양).
    같은 짝이 두 번 오면 한 번만 적는다 (첫 등장 순서).

    Args:
        name: 규칙 이름 (화면에 보이는 이름). 비면 ValueError.
        pairs: [(source_attr, destination_attr), ...]. 비면 ValueError.
        description: 툴팁 설명.
        file_name: 파일 이름 (없으면 rule_file_name(name)).
        overwrite: False 면 파일이 이미 있을 때 ValueError.
    """
    name = str(name or "").strip()
    if not name:
        raise ValueError("rule name is empty")

    seen = set()
    attributes = []
    others = []
    for pair in pairs or []:
        src, dst = (str(pair[0]).strip(), str(pair[1]).strip())
        if not src or not dst or (src, dst) in seen:
            continue
        seen.add((src, dst))
        if src == dst:
            attributes.append(src)
        else:
            others.append([src, dst])
    if not attributes and not others:
        raise ValueError("rule has no attribute pair")

    path = rule_path(file_name or rule_file_name(name), rules_dir)
    if os.path.exists(path) and not overwrite:
        raise ValueError("file already exists: {0}".format(path))

    data = {"name": name, "description": str(description or "")}
    if attributes:
        data["attributes"] = attributes
    if others:
        data["pairs"] = others

    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False))
        fh.write("\n")
    return path


def delete_rules(rules, rules_dir=None):
    """규칙 파일들을 지운다 (v01.61 - Connect by Rule > Manage...).

    **규칙 폴더 안의 .json 만** 지운다 - 그 밖의 경로(규칙 폴더 밖, 확장자 다름)는 건드리지 않고
    failed 로 돌려준다. 파일이 이미 없으면 지운 것으로 친다.

    Args:
        rules: ConnectRule 목록이거나 파일 경로 문자열 목록.

    Returns:
        (deleted_paths, failed) - failed = [(path, reason)...]
    """
    folder = os.path.normcase(os.path.normpath(rules_dir or RULES_DIR))
    deleted = []
    failed = []
    for rule in rules or []:
        path = rule.path if isinstance(rule, ConnectRule) else str(rule or "")
        norm = os.path.normcase(os.path.normpath(path)) if path else ""
        if not norm or os.path.dirname(norm) != folder or not norm.endswith(".json"):
            failed.append((path, "not a rule file in {0}".format(rules_dir or RULES_DIR)))
            continue
        try:
            if os.path.exists(path):
                os.remove(path)
            deleted.append(path)
        except OSError as e:
            failed.append((path, str(e)))
    return deleted, failed


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
