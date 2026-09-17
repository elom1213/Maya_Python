# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00330_NamingTool - Rename > Token 탭의 토큰 규칙 (UI/DCC 비의존)
"""
token_ops - 토큰 목록으로 이름을 만든다.

토큰은 `_` 로 이어 붙는 이름 조각이다. 조각마다 **규칙**을 고른다.

  Custom    : 적은 글자를 그대로 쓴다.            {"rule": "custom", "text": "dyn"}
  Numbering : 시작 정수부터 올라가는 번호, pad 0 자리수로 0 을 채운다.
                                                   {"rule": "numbering", "start": 0, "pad": 2}

Numbering 토큰이 **몇 개냐**에 따라 무엇을 세는지가 정해진다 (레거시 Naming Dyn 과 같은 규칙):

  1 개 : 이름을 바꾸는 노드 전부를 순서대로 센다 (오브젝트가 바뀌어도 이어진다).
  2 개 : 앞 = 리스트의 오브젝트(루트)마다 +1,
         뒤 = 그 오브젝트 안의 노드(루트 + transform 자손)마다 +1, 오브젝트가 바뀌면 시작값으로.
  3 개 이상 : 셀 대상이 없다 → 실행하지 않고 경고한다.

레거시 `dyn_asset_side_{index}_{index}` (pad 2) = DEFAULT_TOKENS.
"""

import re


RULE_CUSTOM = "custom"
RULE_NUMBERING = "numbering"

#: (key, UI 라벨) - 콤보 순서
RULES = (
    (RULE_CUSTOM, "Custom"),
    (RULE_NUMBERING, "Numbering"),
)

MAX_NUMBERING = 2
MAX_PAD = 10

#: 레거시 Naming Dyn 탭의 기본값 그대로 - dyn_asset_side_{index}_{index}, pad 2
DEFAULT_TOKENS = [
    {"rule": RULE_CUSTOM, "text": "dyn"},
    {"rule": RULE_CUSTOM, "text": "asset"},
    {"rule": RULE_CUSTOM, "text": "side"},
    {"rule": RULE_NUMBERING, "start": 0, "pad": 2},
    {"rule": RULE_NUMBERING, "start": 0, "pad": 2},
]

# 마야 이름에 쓸 수 있는 글자. 그 밖의 글자는 마야가 **조용히 `_` 로 바꾸고**,
# 숫자로 시작하는 이름은 **숫자를 지운다**(실측: '01_a' -> '_a'). 그래서 미리 막는다.
_CUSTOM_TEXT_RE = re.compile(r"^[A-Za-z0-9_]*$")


def default_tokens():
    return [dict(token) for token in DEFAULT_TOKENS]


def _as_int(value, fallback):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def normalize_token(raw):
    """UI/JSON 에서 온 dict 를 늘 같은 모양으로. 모르는 규칙은 Custom 으로 본다."""
    raw = raw if isinstance(raw, dict) else {}
    if raw.get("rule") == RULE_NUMBERING:
        pad = max(0, min(MAX_PAD, _as_int(raw.get("pad"), 0)))
        return {"rule": RULE_NUMBERING, "start": _as_int(raw.get("start"), 0), "pad": pad}
    text = raw.get("text")
    return {"rule": RULE_CUSTOM, "text": text.strip() if isinstance(text, str) else ""}


def normalize_tokens(raws):
    return [normalize_token(raw) for raw in (raws or [])]


def numbering_count(tokens):
    return sum(1 for token in tokens if token["rule"] == RULE_NUMBERING)


def pad_number(value, pad):
    """value 를 pad 자리수로 0 패딩 (7, pad 2 -> '07'). 자리수를 넘는 값은 그대로 (123 -> '123')."""
    return str(value).zfill(pad)


def validate(tokens):
    """실행 전에 막아야 할 문제 목록 (빈 리스트면 실행 가능)."""
    errors = []
    if not tokens:
        return ["Add at least one token."]

    for index, token in enumerate(tokens):
        if token["rule"] == RULE_CUSTOM and not _CUSTOM_TEXT_RE.match(token["text"]):
            errors.append(
                "Token {0} '{1}' has characters Maya does not allow in a name "
                "(use letters, digits and _).".format(index + 1, token["text"]))
        if token["rule"] == RULE_NUMBERING and token["start"] < 0:
            errors.append("Token {0} : Start must be 0 or more (a '-' is not allowed "
                          "in a name).".format(index + 1))

    count = numbering_count(tokens)
    if count > MAX_NUMBERING:
        errors.append(
            "{0} Numbering tokens - use at most {1} (1 = every node in order, "
            "2 = per object + per node inside it).".format(count, MAX_NUMBERING))

    if not errors:
        first = format_name(tokens, 0, 0, 0)
        if not first:
            errors.append("Every token is empty - the name would be empty.")
        elif first[0].isdigit():
            errors.append(
                "The name would start with a digit ('{0}'). Maya drops leading digits, "
                "so put a Custom token first.".format(first))
    return errors


def format_name(tokens, object_index, item_index, serial_index):
    """토큰으로 이름 하나를 만든다. 빈 Custom 은 건너뛰어 `__` 가 생기지 않는다.

    object_index : 리스트의 몇 번째 오브젝트인가 (0 부터)
    item_index   : 그 오브젝트 안에서 몇 번째 노드인가 (0 부터, 오브젝트마다 리셋)
    serial_index : 전체에서 몇 번째 노드인가 (0 부터)
    """
    count = numbering_count(tokens)
    parts = []
    seen = 0
    for token in tokens:
        if token["rule"] == RULE_CUSTOM:
            if token["text"]:
                parts.append(token["text"])
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


def plan_names(group_sizes, tokens):
    """오브젝트(그룹)마다 노드 수를 받아 이름 목록을 만든다. 반환: [[name, ...], ...]"""
    names = []
    serial = 0
    for object_index, size in enumerate(group_sizes):
        group = []
        for item_index in range(size):
            group.append(format_name(tokens, object_index, item_index, serial))
            serial += 1
        names.append(group)
    return names


def preview(tokens):
    """UI 미리보기 한 줄 - 첫 이름과, 다음 노드 · 다음 오브젝트의 이름."""
    errors = validate(tokens)
    if errors:
        return "[WARN] " + errors[0]
    first = format_name(tokens, 0, 0, 0)
    next_item = format_name(tokens, 0, 1, 1)
    count = numbering_count(tokens)
    if count == 2:
        next_object = format_name(tokens, 1, 0, 1)
        return "{0}  ->  next node {1}  |  next object {2}".format(first, next_item, next_object)
    if count == 1:
        return "{0}  ->  next node {1}".format(first, next_item)
    return "{0}  (no Numbering token - every node gets the same name)".format(first)
