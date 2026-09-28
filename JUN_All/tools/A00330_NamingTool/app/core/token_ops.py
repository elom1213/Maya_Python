# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-28
# A00330_NamingTool - Rename > Token 탭의 토큰 규칙 (UI/DCC 비의존)
"""
token_ops - 토큰 목록으로 마야 노드 이름을 만든다.

v01.10 : 규칙 본체는 공용 **`Framework.core.token_naming`** 로 올렸다(A00480_FileTool 과 공유).
이 모듈은 이 툴의 규칙 묶음(`MAYA_NODE_RULES` = Custom / Numbering)과 레거시 기본값만 갖고,
예전 함수 이름을 그대로 노출한다.

  Custom    : 적은 글자를 그대로 쓴다.            {"rule": "custom", "text": "dyn"}
  Numbering : 시작 정수부터 올라가는 번호, pad 0 자리수로 0 을 채운다.
                                                   {"rule": "numbering", "start": 0, "pad": 2}

Numbering 1 개 = 이름을 바꾸는 노드 전부를 순서대로, 2 개 = 오브젝트(루트)마다 / 그 오브젝트 안의
노드마다, 3 개 이상 = 실행 안 함. 레거시 `dyn_asset_side_{index}_{index}` (pad 2) = DEFAULT_TOKENS.
"""

from Framework.core import token_naming
from Framework.core.token_naming import (   # noqa: F401 - 예전 이름 그대로
    RULE_CUSTOM,
    RULE_NUMBERING,
    MAX_PAD,
    pad_number,
)


#: 이 툴의 규칙 묶음 (마야 노드 이름)
RULESET = token_naming.MAYA_NODE_RULES

#: (key, UI 라벨) - 콤보 순서
RULES = tuple(RULESET.rule_items())

MAX_NUMBERING = RULESET.max_numbering

#: 레거시 Naming Dyn 탭의 기본값 그대로 - dyn_asset_side_{index}_{index}, pad 2
DEFAULT_TOKENS = [
    {"rule": RULE_CUSTOM, "text": "dyn"},
    {"rule": RULE_CUSTOM, "text": "asset"},
    {"rule": RULE_CUSTOM, "text": "side"},
    {"rule": RULE_NUMBERING, "start": 0, "pad": 2},
    {"rule": RULE_NUMBERING, "start": 0, "pad": 2},
]


def default_tokens():
    return [dict(token) for token in DEFAULT_TOKENS]


normalize_token = RULESET.normalize_token
normalize_tokens = RULESET.normalize_tokens
numbering_count = RULESET.numbering_count
validate = RULESET.validate
preview = RULESET.preview


def format_name(tokens, object_index, item_index, serial_index):
    """토큰으로 이름 하나를 만든다. 빈 Custom 은 건너뛰어 `__` 가 생기지 않는다."""
    return RULESET.format_name(tokens, object_index, item_index, serial_index)


def plan_names(group_sizes, tokens):
    """오브젝트(그룹)마다 노드 수를 받아 이름 목록을 만든다. 반환: [[name, ...], ...]"""
    return RULESET.plan_names(group_sizes, tokens)
