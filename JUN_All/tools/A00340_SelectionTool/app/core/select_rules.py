# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-28
# A00340_SelectionTool - selection RULES persistence (UI/DCC 비의존)  (v01.11)
#
# "규칙(rule)" 은 어느 씬에서든 다시 선택할 오브젝트 **이름 목록** 하나다.
# 버튼 프로파일(prefs.py, 프로파일 하나 = json 하나에 버튼 여러 개)과 달리
# **규칙 하나 = json 파일 하나** 로 둔다 - 폴더만 봐도 어떤 규칙이 있는지 보이고,
# 다른 PC 와는 파일을 복사하는 것으로 공유가 끝난다.
#
#   <A00340_SelectionTool>/data/rules/<rule name>.json
#   {
#     "name": "rule_01",
#     "description": "left arm fk joints",
#     "objects": ["jnt_01", "jnt_02", "jnt_03"]
#   }
#
# - 화면에 보이는 이름은 json 안의 `name` 이 기준이다. 파일 이름은 그 이름을 따라가되
#   (Windows 금지 문자만 `_`), Rename 하면 파일 이름도 함께 바꾼다 (rename_rule).
# - 오브젝트는 캡처 당시의 **짧은 이름**(cmds.ls 기본값) 그대로 둔다 - 네임스페이스나
#   그룹이 달라진 씬에서도 맞게 하려는 것. 동명 노드는 선택 쪽(maya_select)이 경고한다.
# - 깨진 json 은 로드에서 errors 로 따로 돌려주고 건드리지 않는다 (A00145 connect_rules 와 같은 태도).
# - 지우기는 **규칙 폴더 안의 .json 만** 받는다.

import io
import os
import json

from . import prefs as prefs_mod


RULES_DIR = prefs_mod.LOCAL_RULES_DIR   # 로컬 규칙. 공유는 prefs_mod.rules_dir("shared") 를 rules_dir= 로 (v01.17)


class SelectRule(object):
    """규칙 하나. name(표시 이름) · objects(이름 목록) · description · path(json 절대 경로)."""

    def __init__(self, name, objects, description="", path=""):
        self.name = name
        self.objects = list(objects)
        self.description = description or ""
        self.path = path or ""

    @property
    def file_name(self):
        return os.path.basename(self.path) if self.path else ""

    def __repr__(self):
        return "SelectRule({0!r}, {1} objects)".format(self.name, len(self.objects))


# ------------------------------------------------------------------ paths

def rule_file_name(name):
    """규칙 이름 -> 파일 이름(확장자 없이). 금지 문자만 `_`, 대소문자는 그대로. 비면 'rule'."""
    cleaned = prefs_mod.sanitize_name(name)
    # 파일 이름 끝의 '.' 은 Windows 가 조용히 지우므로 미리 걷어낸다.
    cleaned = cleaned.rstrip(". ")
    return cleaned or "rule"


def rule_path(name, rules_dir=None):
    """규칙 이름 -> 규칙 폴더 안의 json 절대 경로."""
    return os.path.join(rules_dir or RULES_DIR, rule_file_name(name) + ".json")


def _is_rule_file(path, rules_dir=None):
    """path 가 규칙 폴더 **바로 안의** .json 인지. 지우기/이름 바꾸기 전에 확인한다."""
    folder = os.path.normcase(os.path.normpath(rules_dir or RULES_DIR))
    norm = os.path.normcase(os.path.normpath(path)) if path else ""
    return bool(norm) and os.path.dirname(norm) == folder and norm.endswith(".json")


# ------------------------------------------------------------------ load

def _normalize(data, fallback_name, path):
    """json dict -> SelectRule. 모양이 틀리면 ValueError."""
    if not isinstance(data, dict):
        raise ValueError("top level is not an object")
    objects = data.get("objects")
    if not isinstance(objects, list):
        raise ValueError("'objects' must be a list of names")
    names = []
    for item in objects:
        text = str(item or "").strip()
        if text and text not in names:
            names.append(text)
    name = str(data.get("name") or "").strip() or fallback_name
    return SelectRule(name, names, str(data.get("description") or ""), path)


def load_rules(rules_dir=None):
    """규칙 폴더의 *.json 을 모두 읽는다. (이름순 규칙 목록, errors[(file_name, message)...]) 반환.

    폴더가 없으면 빈 결과. 깨진 파일은 errors 로만 알리고 그대로 둔다.
    """
    folder = rules_dir or RULES_DIR
    rules, errors = [], []
    if not os.path.isdir(folder):
        return rules, errors
    for file_name in sorted(os.listdir(folder)):
        if not file_name.lower().endswith(".json"):
            continue
        path = os.path.join(folder, file_name)
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            rules.append(_normalize(data, file_name[:-5], path))
        except (OSError, ValueError) as e:
            errors.append((file_name, str(e)))
    rules.sort(key=lambda r: r.name.lower())
    return rules, errors


def find_rule(name, rules_dir=None):
    """이름으로 규칙 하나 (없으면 None). 이름 비교는 대소문자 구분."""
    for rule in load_rules(rules_dir)[0]:
        if rule.name == name:
            return rule
    return None


# ------------------------------------------------------------------ save

def _write(rule):
    folder = os.path.dirname(rule.path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    data = {"name": rule.name, "description": rule.description, "objects": list(rule.objects)}
    with io.open(rule.path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False))
        fh.write("\n")
    return rule.path


def save_rule(name, objects, description="", rules_dir=None, overwrite=False):
    """새 규칙 json 을 쓴다. 반환: SelectRule (path 포함).

    - name 이 비거나 objects 가 비면 ValueError.
    - 같은 파일이 이미 있으면 overwrite=False 일 때 ValueError (덮어쓰기는 호출 쪽이 확인한 뒤).
    - 이름이 같은 규칙이 다른 파일 이름으로 있는 경우도 ValueError - 콤보/목록에서 둘을 못 가른다.
    """
    name = str(name or "").strip()
    if not name:
        raise ValueError("rule name is empty")
    names = []
    for item in objects or []:
        text = str(item or "").strip()
        if text and text not in names:
            names.append(text)
    if not names:
        raise ValueError("rule has no object")

    path = rule_path(name, rules_dir)
    if os.path.exists(path) and not overwrite:
        raise ValueError("file already exists: {0}".format(os.path.basename(path)))
    other = find_rule(name, rules_dir)
    if other is not None and os.path.normcase(other.path) != os.path.normcase(path):
        raise ValueError("a rule named '{0}' already exists ({1})".format(name, other.file_name))

    rule = SelectRule(name, names, description, path)
    _write(rule)
    return rule


def update_rule(rule, objects=None, description=None):
    """있는 규칙의 objects / description 을 바꿔 같은 파일에 다시 쓴다. 반환: rule.

    objects 가 None 이면 그대로, 빈 목록이면 ValueError (빈 규칙은 만들지 않는다).
    """
    if objects is not None:
        names = []
        for item in objects:
            text = str(item or "").strip()
            if text and text not in names:
                names.append(text)
        if not names:
            raise ValueError("rule has no object")
        rule.objects = names
    if description is not None:
        rule.description = str(description)
    _write(rule)
    return rule


def rename_rule(rule, new_name, rules_dir=None):
    """규칙 이름을 바꾼다 - json 안의 name 과 **파일 이름** 둘 다. 반환: rule (path 갱신).

    - 새 이름이 비면 ValueError. 같은 이름이면 아무것도 안 한다.
    - 새 파일 이름이 다른 규칙 파일과 겹치면 ValueError (덮어쓰지 않는다).
    - 금지 문자만 다른 이름(예: 'a:b' -> 'a_b' 가 이미 있음)도 같은 이유로 막는다.
    """
    new_name = str(new_name or "").strip()
    if not new_name:
        raise ValueError("rule name is empty")
    if new_name == rule.name:
        return rule
    if not _is_rule_file(rule.path, rules_dir):
        raise ValueError("not a rule file in {0}".format(rules_dir or RULES_DIR))

    other = find_rule(new_name, rules_dir)
    if other is not None and os.path.normcase(other.path) != os.path.normcase(rule.path):
        raise ValueError("a rule named '{0}' already exists ({1})".format(new_name, other.file_name))

    new_path = rule_path(new_name, rules_dir)
    same_file = os.path.normcase(new_path) == os.path.normcase(rule.path)
    if not same_file and os.path.exists(new_path):
        raise ValueError("file already exists: {0}".format(os.path.basename(new_path)))

    old_path = rule.path
    rule.name = new_name
    rule.path = new_path
    _write(rule)
    if not same_file:
        try:
            os.remove(old_path)
        except OSError:
            pass
    return rule


def delete_rules(rules, rules_dir=None):
    """규칙 파일들을 지운다. **규칙 폴더 안의 .json 만**. (deleted_paths, failed[(path, reason)]) 반환.

    파일이 이미 없으면 지운 것으로 친다. 되돌릴 수 없다(os.remove) - 확인은 호출 쪽에서.
    """
    deleted, failed = [], []
    for rule in rules or []:
        path = rule.path if isinstance(rule, SelectRule) else str(rule or "")
        if not _is_rule_file(path, rules_dir):
            failed.append((path, "not a rule file in {0}".format(rules_dir or RULES_DIR)))
            continue
        try:
            if os.path.exists(path):
                os.remove(path)
            deleted.append(path)
        except OSError as e:
            failed.append((path, str(e)))
    return deleted, failed


def _transfer_rule(rule, target_dir, move):
    """규칙 파일을 target_dir 로 옮기거나(move) 복사한다. 대상에 같은 파일 · 같은 이름이 있으면 ValueError."""
    if not rule.path or not os.path.isfile(rule.path):
        raise ValueError("rule file not found: {0}".format(rule.path))
    target = rule_path(rule.name, target_dir)
    if os.path.normcase(os.path.normpath(os.path.dirname(target))) == \
            os.path.normcase(os.path.normpath(os.path.dirname(rule.path))):
        raise ValueError("the rule is already in {0}".format(target_dir))
    if os.path.exists(target):
        raise ValueError("file already exists: {0}".format(os.path.basename(target)))
    if find_rule(rule.name, target_dir) is not None:
        raise ValueError("a rule named '{0}' already exists there".format(rule.name))
    copied = SelectRule(rule.name, rule.objects, rule.description, target)
    _write(copied)
    if move:
        try:
            os.remove(rule.path)
        except OSError:
            pass
    return copied


def share_rule(rule, shared_dir):
    """로컬 규칙을 공유 폴더로 **옮긴다** (v01.17). 반환: 새 SelectRule."""
    return _transfer_rule(rule, shared_dir, move=True)


def copy_rule_to(rule, target_dir):
    """규칙을 다른 폴더로 **복사한다** (v01.17, 공유 -> 로컬 'Copy to Local'). 반환: 새 SelectRule."""
    return _transfer_rule(rule, target_dir, move=False)


def union_objects(rules):
    """여러 규칙의 오브젝트를 **첫 등장 순서**로 합친다(중복 제거). Select 가 여러 규칙을 고르면 쓴다."""
    seen = set()
    out = []
    for rule in rules or []:
        for name in rule.objects:
            if name not in seen:
                seen.add(name)
                out.append(name)
    return out
