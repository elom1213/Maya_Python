# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-28
# Framework - 토큰 이름 규칙 + 토큰 프로파일(json) 저장소 (공용, UI/DCC 비의존)
"""
token_naming - 토큰 목록으로 이름을 만든다. A00330_NamingTool(Rename > Token) 에서 올려 왔다.

토큰은 `_` 로 이어 붙는 이름 조각이다. 조각마다 **규칙**을 고른다.

  Custom     : 적은 글자를 그대로 쓴다.            {"rule": "custom", "text": "dyn"}
  Numbering  : 시작 정수부터 올라가는 번호, pad 0 자리수로 0 을 채운다.
                                                    {"rule": "numbering", "start": 0, "pad": 2}
  Set's Name : 이름을 지을 대상마다 주어지는 글자(세트 이름 등)를 그대로 쓴다.
                                                    {"rule": "setname"}

툴마다 쓸 수 있는 규칙 · 이름 종류가 다르므로 **`TokenRuleSet`** 에 묶어 넘긴다.

  MAYA_NODE_RULES  : 마야 노드 이름 (Custom / Numbering)            - A00330 Token 탭
  FILE_NAME_RULES  : 파일 이름     (Custom / Numbering / Set's Name) - A00480 Export Naming

Numbering 토큰이 **몇 개냐**에 따라 무엇을 세는지가 정해진다 (레거시 Naming Dyn 과 같은 규칙):

  1 개 : 이름을 짓는 대상 전부를 순서대로 센다 (오브젝트가 바뀌어도 이어진다).
  2 개 : 앞 = 리스트의 오브젝트(루트)마다 +1,
         뒤 = 그 오브젝트 안의 노드마다 +1, 오브젝트가 바뀌면 시작값으로.
  max_numbering 를 넘으면 셀 대상이 없다 → 실행하지 않고 경고한다.

프로파일(토큰 규칙 한 벌)은 **`TokenProfileStore(data_dir, ...)`** 가 툴 폴더 안에 json 으로 둔다.
  <data_dir>/
    ├── token_profiles/<profile>.json   # {"tokens": [{"rule": ..., ...}, ...]}
    └── token_profiles_active.json      # {"active": "<현재 프로파일>"}
"""

import os
import re
import json


RULE_CUSTOM = "custom"
RULE_NUMBERING = "numbering"
RULE_SETNAME = "setname"

#: 규칙 key -> UI 라벨
RULE_LABELS = {
    RULE_CUSTOM: "Custom",
    RULE_NUMBERING: "Numbering",
    RULE_SETNAME: "Set's Name",
}

#: 규칙 key -> 콤보 툴팁 한 줄
RULE_TIPS = {
    RULE_CUSTOM: "Custom     : the text as typed",
    RULE_NUMBERING: "Numbering  : a number counting up from Start, zero-padded to Pad 0 digits",
    RULE_SETNAME: "Set's Name : the name of each set (namespace and path removed)",
}

NAME_MAYA = "maya"   # 마야 노드 이름 - [A-Za-z0-9_], 숫자로 시작 금지
NAME_FILE = "file"   # 파일 이름     - Windows 금지 문자만 막는다

MAX_PAD = 10

# 마야 이름에 쓸 수 있는 글자. 그 밖의 글자는 마야가 **조용히 `_` 로 바꾸고**,
# 숫자로 시작하는 이름은 **숫자를 지운다**(실측: '01_a' -> '_a'). 그래서 미리 막는다.
_MAYA_TEXT_RE = re.compile(r"^[A-Za-z0-9_]*$")
# 파일명으로 못 쓰는 문자(Windows 기준).
_INVALID_FILE_CHARS = set('\\/:*?"<>|')


def _as_int(value, fallback):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def pad_number(value, pad):
    """value 를 pad 자리수로 0 패딩 (7, pad 2 -> '07'). 자리수를 넘는 값은 그대로 (123 -> '123')."""
    return str(value).zfill(pad)


def short_name(name):
    """DAG 경로/네임스페이스를 떼고 leaf 이름만. 'a|b:c' -> 'c'."""
    return (name or "").split("|")[-1].split(":")[-1]


class TokenRuleSet(object):
    """툴 하나가 쓰는 토큰 규칙 묶음.

    rules          : 콤보에 보일 규칙 key 순서 (RULE_*)
    max_numbering  : Numbering 토큰 최대 개수 (1 = 전체 순번만, 2 = 오브젝트 / 오브젝트 안 노드)
    name_kind      : NAME_MAYA | NAME_FILE - 글자 검사 방식
    serial_label   : 미리보기의 '다음 ...' 이름 (Numbering 1 개일 때 세는 대상)
    object_label   : 미리보기의 '다음 ...' 이름 (Numbering 2 개일 때 앞 번호가 세는 대상)
    sample_context : 미리보기 · 검사에서 Set's Name 자리에 넣을 보기 글자
    """

    def __init__(self, rules=(RULE_CUSTOM, RULE_NUMBERING), max_numbering=2,
                 name_kind=NAME_MAYA, serial_label="node", object_label="object",
                 sample_context="<Set>"):
        self.rules = tuple(rules)
        self.max_numbering = max_numbering
        self.name_kind = name_kind
        self.serial_label = serial_label
        self.object_label = object_label
        self.sample_context = sample_context

    # ------------------------------------------------------------ 모양 맞추기

    def rule_items(self):
        """[(key, UI 라벨), ...] - 콤보 순서."""
        return [(key, RULE_LABELS[key]) for key in self.rules]

    def rule_tooltip(self):
        return "\n".join(RULE_TIPS[key] for key in self.rules)

    def normalize_token(self, raw):
        """UI/JSON 에서 온 dict 를 늘 같은 모양으로. 모르는(또는 이 툴에 없는) 규칙은 Custom 으로 본다."""
        raw = raw if isinstance(raw, dict) else {}
        rule = raw.get("rule")
        if rule == RULE_NUMBERING and rule in self.rules:
            pad = max(0, min(MAX_PAD, _as_int(raw.get("pad"), 0)))
            return {"rule": RULE_NUMBERING, "start": _as_int(raw.get("start"), 0), "pad": pad}
        if rule == RULE_SETNAME and rule in self.rules:
            return {"rule": RULE_SETNAME}
        text = raw.get("text")
        return {"rule": RULE_CUSTOM, "text": text.strip() if isinstance(text, str) else ""}

    def normalize_tokens(self, raws):
        return [self.normalize_token(raw) for raw in (raws or [])]

    @staticmethod
    def numbering_count(tokens):
        return sum(1 for token in tokens if token["rule"] == RULE_NUMBERING)

    # ------------------------------------------------------------ 검사

    def _bad_text(self, text):
        if self.name_kind == NAME_MAYA:
            return not _MAYA_TEXT_RE.match(text)
        return any(c in _INVALID_FILE_CHARS for c in text)

    def _bad_text_message(self, index, text):
        if self.name_kind == NAME_MAYA:
            return ("Token {0} '{1}' has characters Maya does not allow in a name "
                    "(use letters, digits and _).".format(index + 1, text))
        return ("Token {0} '{1}' has characters a file name cannot have "
                "(\\ / : * ? \" < > |).".format(index + 1, text))

    def _numbering_help(self):
        if self.max_numbering >= 2:
            return "1 = every {0} in order, 2 = per {1} + per {0} inside it".format(
                self.serial_label, self.object_label)
        return "it counts every {0} in order".format(self.serial_label)

    def validate(self, tokens):
        """실행 전에 막아야 할 문제 목록 (빈 리스트면 실행 가능)."""
        errors = []
        if not tokens:
            return ["Add at least one token."]

        for index, token in enumerate(tokens):
            if token["rule"] == RULE_CUSTOM and self._bad_text(token["text"]):
                errors.append(self._bad_text_message(index, token["text"]))
            if token["rule"] == RULE_NUMBERING and token["start"] < 0:
                errors.append("Token {0} : Start must be 0 or more (a '-' is not allowed "
                              "in a name).".format(index + 1))

        count = self.numbering_count(tokens)
        if count > self.max_numbering:
            errors.append("{0} Numbering tokens - use at most {1} ({2}).".format(
                count, self.max_numbering, self._numbering_help()))

        if not errors:
            first = self.format_name(tokens, 0, 0, 0, self.sample_context)
            if not first:
                errors.append("Every token is empty - the name would be empty.")
            elif self.name_kind == NAME_MAYA and first[0].isdigit():
                errors.append(
                    "The name would start with a digit ('{0}'). Maya drops leading digits, "
                    "so put a Custom token first.".format(first))
        return errors

    # ------------------------------------------------------------ 이름 만들기

    def format_name(self, tokens, object_index, item_index, serial_index, context_name=""):
        """토큰으로 이름 하나를 만든다. 빈 토큰은 건너뛰어 `__` 가 생기지 않는다.

        object_index : 리스트의 몇 번째 오브젝트인가 (0 부터)
        item_index   : 그 오브젝트 안에서 몇 번째 노드인가 (0 부터, 오브젝트마다 리셋)
        serial_index : 전체에서 몇 번째인가 (0 부터)
        context_name : Set's Name 토큰 자리에 들어갈 글자 (세트 이름 등)
        """
        count = self.numbering_count(tokens)
        parts = []
        seen = 0
        for token in tokens:
            rule = token["rule"]
            if rule == RULE_CUSTOM:
                if token["text"]:
                    parts.append(token["text"])
                continue
            if rule == RULE_SETNAME:
                value = short_name(context_name)
                if value:
                    parts.append(value)
                continue
            if count == 1:
                counter = serial_index
            elif seen == 0:
                counter = object_index
            else:
                counter = item_index
            seen += 1
            parts.append(pad_number(token["start"] + counter, token["pad"]))
        return "_".join(parts)

    def plan_names(self, group_sizes, tokens, context_names=None):
        """오브젝트(그룹)마다 노드 수를 받아 이름 목록을 만든다. 반환: [[name, ...], ...]

        context_names : 그룹마다 Set's Name 자리에 들어갈 글자 (없으면 빈 글자)
        """
        names = []
        serial = 0
        for object_index, size in enumerate(group_sizes):
            context = ""
            if context_names and object_index < len(context_names):
                context = context_names[object_index]
            group = []
            for item_index in range(size):
                group.append(self.format_name(tokens, object_index, item_index, serial, context))
                serial += 1
            names.append(group)
        return names

    def names_for(self, context_names, tokens):
        """이름을 지을 대상(세트 등)마다 하나씩 - Numbering 은 목록 순번. 반환: [name, ...]"""
        groups = self.plan_names([1] * len(context_names), tokens, context_names)
        return [group[0] for group in groups]

    def preview(self, tokens):
        """UI 미리보기 한 줄 - 첫 이름과, 번호가 어떻게 넘어가는지."""
        errors = self.validate(tokens)
        if errors:
            return "[WARN] " + errors[0]
        sample = self.sample_context
        first = self.format_name(tokens, 0, 0, 0, sample)
        count = self.numbering_count(tokens)
        if count == 2:
            next_item = self.format_name(tokens, 0, 1, 1, sample)
            next_object = self.format_name(tokens, 1, 0, 1, sample)
            return "{0}  ->  next {1} {2}  |  next {3} {4}".format(
                first, self.serial_label, next_item, self.object_label, next_object)
        if count == 1:
            next_serial = self.format_name(tokens, 1, 1, 1, sample)
            return "{0}  ->  next {1} {2}".format(first, self.serial_label, next_serial)
        if any(t["rule"] == RULE_SETNAME for t in tokens):
            return "{0}  ({1} = each set's name)".format(first, sample)
        return "{0}  (no Numbering token - every {1} gets the same name)".format(
            first, self.serial_label)


#: 마야 노드 이름 (A00330 Rename > Token)
MAYA_NODE_RULES = TokenRuleSet(
    rules=(RULE_CUSTOM, RULE_NUMBERING), max_numbering=2, name_kind=NAME_MAYA,
    serial_label="node", object_label="object")

#: 세트마다 파일 이름 하나 (A00480 Export > Naming). Numbering 은 세트 순번 하나만.
FILE_NAME_RULES = TokenRuleSet(
    rules=(RULE_CUSTOM, RULE_NUMBERING, RULE_SETNAME), max_numbering=1, name_kind=NAME_FILE,
    serial_label="set", object_label="set")


# ======================================================================
# 프로파일 저장소
# ======================================================================

DEFAULT_PROFILE = "Default"

# 파일명으로 못 쓰는 문자(Windows 기준). 프로파일 이름 = 파일명이라 막아둔다.
_INVALID_NAME_CHARS = _INVALID_FILE_CHARS


def sanitize_profile_name(name):
    """프로파일 이름을 파일명으로 안전하게. 금지문자는 '_' 로, 양끝 공백 제거."""
    cleaned = "".join("_" if c in _INVALID_NAME_CHARS else c for c in (name or ""))
    return cleaned.strip()


def _read_json(path, fallback):
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    return fallback


class TokenProfileStore(object):
    """토큰 프로파일(json) 저장소 - 툴마다 하나 (A00145 `attr_profile_prefs` 와 같은 구성).

    data_dir       : 툴 폴더의 data/ (PC 별 - .gitignore 대상)
    default_tokens : 프로파일이 하나도 없을 때 `default_profile` 로 만들 토큰
    ruleset        : 읽고 쓸 때 모양을 맞출 TokenRuleSet
    """

    def __init__(self, data_dir, default_tokens, ruleset=MAYA_NODE_RULES,
                 default_profile=DEFAULT_PROFILE):
        self.data_dir = data_dir
        self.profiles_dir = os.path.join(data_dir, "token_profiles")
        self.active_path = os.path.join(data_dir, "token_profiles_active.json")
        self.ruleset = ruleset
        self.default_profile = default_profile
        self._default_tokens = [dict(t) for t in default_tokens]

    sanitize_name = staticmethod(sanitize_profile_name)

    def default_tokens(self):
        return self.ruleset.normalize_tokens(self._default_tokens)

    def _profile_path(self, name):
        return os.path.join(self.profiles_dir, name + ".json")

    def _ensure_setup(self):
        """profiles 폴더 + 최소 1개 프로파일(기본 토큰) 보장."""
        os.makedirs(self.profiles_dir, exist_ok=True)
        if not self.list_profiles():
            self.save_profile(self.default_profile, self.default_tokens())
            self.set_active(self.default_profile)

    def list_profiles(self):
        if not os.path.isdir(self.profiles_dir):
            return []
        return sorted(fn[:-5] for fn in os.listdir(self.profiles_dir)
                      if fn.lower().endswith(".json"))

    def load_profile(self, name):
        """프로파일의 토큰 목록. 파일이 없거나 깨졌거나 비었으면 기본 토큰."""
        loaded = _read_json(self._profile_path(name), None)
        tokens = []
        if isinstance(loaded, dict) and isinstance(loaded.get("tokens"), list):
            tokens = self.ruleset.normalize_tokens(
                t for t in loaded["tokens"] if isinstance(t, dict))
        return tokens or self.default_tokens()

    def save_profile(self, name, tokens):
        os.makedirs(self.profiles_dir, exist_ok=True)
        path = self._profile_path(name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"tokens": self.ruleset.normalize_tokens(tokens)}, f,
                      ensure_ascii=False, indent=2)
        return path

    def delete_profile(self, name):
        try:
            os.remove(self._profile_path(name))
        except OSError:
            pass

    def rename_profile(self, old, new):
        """파일명을 바꾼다. 활성 프로파일이면 active 도 갱신."""
        was_active = (self._read_active_raw() == old)
        os.replace(self._profile_path(old), self._profile_path(new))
        if was_active:
            self.set_active(new)

    def _read_active_raw(self):
        data = _read_json(self.active_path, None)
        return data.get("active") if isinstance(data, dict) else None

    def get_active(self):
        """현재 활성 프로파일 이름(항상 존재하는 것으로 보정)."""
        self._ensure_setup()
        active = self._read_active_raw()
        profiles = self.list_profiles()
        if active not in profiles:
            active = profiles[0] if profiles else self.default_profile
            self.set_active(active)
        return active

    def set_active(self, name):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.active_path, "w", encoding="utf-8") as f:
            json.dump({"active": name}, f, ensure_ascii=False, indent=2)
