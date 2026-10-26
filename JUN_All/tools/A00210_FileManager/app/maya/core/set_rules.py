# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - 세트 규칙 json (UI/DCC 비의존, 순수 파이썬)  (v01.41)
#
# "규칙" = 마야 파일 안에서 **어떤 이름의 objectSet 을 찾을지**. A00340 select_rules 와 같은 태도 -
# **규칙 하나 = json 파일 하나**, 폴더를 복사하면 다른 PC 와 공유가 끝난다. 기본 폴더는 A00210 prefs 옆
# (~/.jun_filemanager/export_rules), prefs `export_rules_dir` 로 바꿀 수 있다(NAS 등 공유 폴더).
#
#   <rules_dir>/<name>.json
#   {"name": "Bake", "description": "...", "set_name": "Bake", "match": "exact", "ignore_namespace": true}
#
#   match            : exact(잎 이름 ==) · contains(부분 문자열) · regex(re.fullmatch). 대소문자 구분.
#   ignore_namespace : true 면 `CHN:rig:Bake` 를 `Bake` 로 비교한다. 세트의 **부모 세트는 보지 않는다** - 최상위든
#                      다른 세트 안이든 씬의 모든 objectSet 을 잎 이름으로 맞춘다(설계 D6).
# - 화면 이름은 json 의 `name`. 파일 이름은 그 이름(금지 문자만 `_`). Rename 은 둘 다 바꾼다.
# - 깨진 json 은 errors 로 돌려주고 건드리지 않는다. Delete 는 규칙 폴더 **바로 안**의 .json 만.
# - 폴더가 비어 있으면 기본 규칙 `Bake` 하나를 만든다.
#
# 매칭 자체(name_matches)는 여기 둔다 - Maya 가 필요 없어 테스트가 쉽고, 워커(set_match.py)가 가져다 쓴다.

import io
import os
import re
import json

MATCH_EXACT, MATCH_CONTAINS, MATCH_REGEX = "exact", "contains", "regex"
MATCHES = (MATCH_EXACT, MATCH_CONTAINS, MATCH_REGEX)
MATCH_LABELS = {MATCH_EXACT: "Exact", MATCH_CONTAINS: "Contains", MATCH_REGEX: "Regex"}

DEFAULT_RULES_DIR = os.path.join(os.path.expanduser("~"), ".jun_filemanager", "export_rules")
DEFAULT_RULE = {"name": "Bake", "description": "set that holds the avatar root bone(s) to bake and export",
                "set_name": "Bake", "match": MATCH_EXACT, "ignore_namespace": True}

_INVALID_CHARS = set('\\/:*?"<>|')


class SetRule(object):
    """규칙 하나."""

    def __init__(self, name, set_name, match=MATCH_EXACT, ignore_namespace=True, description="", path=""):
        self.name = name
        self.set_name = set_name
        self.match = match
        self.ignore_namespace = bool(ignore_namespace)
        self.description = description or ""
        self.path = path or ""

    def to_json(self):
        return {"name": self.name, "description": self.description, "set_name": self.set_name,
                "match": self.match, "ignore_namespace": self.ignore_namespace}

    def to_job(self):
        """워커 job 의 rule 항목."""
        return {"set_name": self.set_name, "match": self.match, "ignore_namespace": self.ignore_namespace}

    def summary(self):
        """UI 한 줄: set "Bake" · exact · ignore namespace"""
        parts = ['set "{0}"'.format(self.set_name), MATCH_LABELS.get(self.match, self.match).lower()]
        parts.append("ignore namespace" if self.ignore_namespace else "namespace matters")
        return " · ".join(parts)

    def __repr__(self):
        return "SetRule({0!r}, set={1!r}, {2})".format(self.name, self.set_name, self.match)


# ------------------------------------------------------------------ validation · matching

def validate(name, set_name, match, description=""):
    """틀린 점 목록(영어, UI 에 그대로). 비면 OK."""
    errors = []
    if not (name or "").strip():
        errors.append("Name is empty.")
    if not (set_name or "").strip():
        errors.append("Set name is empty.")
    if match not in MATCHES:
        errors.append("Unknown match type {0!r}.".format(match))
    if match == MATCH_REGEX and set_name:
        try:
            re.compile(set_name)
        except re.error as exc:
            errors.append("Regex error : {0}".format(exc))
    return errors


def leaf_name(node_name):
    """'CHN:rig:Bake' -> 'Bake' (세트는 DAG 경로가 없지만 '|' 도 뗀다)."""
    return (node_name or "").split("|")[-1].split(":")[-1]


def name_matches(node_name, rule):
    """rule 은 SetRule 또는 {"set_name", "match", "ignore_namespace"} dict."""
    if isinstance(rule, SetRule):
        set_name, match, ignore_ns = rule.set_name, rule.match, rule.ignore_namespace
    else:
        set_name, match = rule.get("set_name", ""), rule.get("match", MATCH_EXACT)
        ignore_ns = bool(rule.get("ignore_namespace", True))
    target = leaf_name(node_name) if ignore_ns else (node_name or "")
    if match == MATCH_CONTAINS:
        return bool(set_name) and set_name in target
    if match == MATCH_REGEX:
        try:
            return re.fullmatch(set_name, target) is not None
        except re.error:
            return False
    return target == set_name


# ------------------------------------------------------------------ paths

def rules_dir(pref_value=""):
    """prefs 값이 비면 기본 폴더. 폴더를 만든다."""
    folder = (pref_value or "").strip() or DEFAULT_RULES_DIR
    folder = os.path.normpath(os.path.expanduser(folder))
    if not os.path.isdir(folder):
        os.makedirs(folder)
    return folder


def sanitize_name(name):
    cleaned = "".join("_" if c in _INVALID_CHARS else c for c in (name or ""))
    return cleaned.strip().rstrip(". ")


def rule_file_name(name):
    return sanitize_name(name) or "rule"


def rule_path(name, folder):
    return os.path.join(folder, rule_file_name(name) + ".json")


def _is_rule_file(path, folder):
    norm_folder = os.path.normcase(os.path.normpath(folder))
    norm = os.path.normcase(os.path.normpath(path)) if path else ""
    return bool(norm) and os.path.dirname(norm) == norm_folder and norm.lower().endswith(".json")


# ------------------------------------------------------------------ load · save

def _read(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("not a json object")
    name = str(data.get("name") or os.path.splitext(os.path.basename(path))[0])
    set_name = str(data.get("set_name") or "")
    match = str(data.get("match") or MATCH_EXACT)
    errors = validate(name, set_name, match)
    if errors:
        raise ValueError(" ".join(errors))
    return SetRule(name, set_name, match, data.get("ignore_namespace", True), str(data.get("description") or ""), path)


def load_rules(folder, create_default=True):
    """(rules 이름순, errors [(path, message)]). 비어 있으면 기본 규칙 Bake 를 만든다(create_default)."""
    rules, errors = [], []
    if not os.path.isdir(folder):
        os.makedirs(folder)
    for fn in sorted(os.listdir(folder), key=str.lower):
        if not fn.lower().endswith(".json"):
            continue
        path = os.path.join(folder, fn)
        try:
            rules.append(_read(path))
        except (OSError, ValueError) as exc:
            errors.append((path, str(exc)))
    if not rules and not errors and create_default:
        rule = SetRule(DEFAULT_RULE["name"], DEFAULT_RULE["set_name"], DEFAULT_RULE["match"],
                       DEFAULT_RULE["ignore_namespace"], DEFAULT_RULE["description"])
        save_rule(rule, folder)
        rules.append(rule)
    rules.sort(key=lambda r: r.name.lower())
    return rules, errors


def save_rule(rule, folder):
    """json 으로 저장. 유효성 틀리면 ValueError. 반환 경로(rule.path 도 갱신)."""
    errors = validate(rule.name, rule.set_name, rule.match)
    if errors:
        raise ValueError(" ".join(errors))
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = rule.path if (rule.path and _is_rule_file(rule.path, folder)) else rule_path(rule.name, folder)
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(rule.to_json(), fh, ensure_ascii=False, indent=2)
    rule.path = path
    return path


def rename_rule(rule, new_name, folder):
    """json 의 name 과 파일 이름을 함께 바꾼다. 같은 이름 파일이 있으면 ValueError."""
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("Name is empty.")
    new_path = rule_path(new_name, folder)
    if os.path.normcase(new_path) != os.path.normcase(rule.path or "") and os.path.exists(new_path):
        raise ValueError("A rule file named {0!r} already exists.".format(os.path.basename(new_path)))
    old_path = rule.path
    rule.name = new_name
    if old_path and os.path.isfile(old_path) and os.path.normcase(old_path) != os.path.normcase(new_path):
        os.replace(old_path, new_path)
    rule.path = new_path
    save_rule(rule, folder)
    return rule


def delete_rule(rule, folder):
    """규칙 폴더 바로 안의 .json 만 지운다. 아니면 ValueError."""
    if not _is_rule_file(rule.path, folder):
        raise ValueError("Not a rule file inside the rules folder : {0!r}".format(rule.path))
    if os.path.isfile(rule.path):
        os.remove(rule.path)
    return True


def find_rule(rules, name):
    for rule in rules:
        if rule.name == name:
            return rule
    return None
