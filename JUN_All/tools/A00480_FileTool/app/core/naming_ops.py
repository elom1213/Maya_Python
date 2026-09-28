# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-28
# A00480_FileTool - Export > Naming 의 토큰 규칙 · 프로파일 (UI/DCC 비의존)
#
# v01.06 : A00330_NamingTool Rename > Token 과 같은 토큰 방식으로 바꿨다. 규칙 · 저장은 공용
# `Framework.core.token_naming`, 화면은 공용 `Framework.qt.MOD_tokenName_qt_v01`.
#
# 이 툴의 규칙 묶음 = FILE_NAME_RULES
#   Custom     : 적은 글자 그대로
#   Numbering  : 세트 순번 (Set's Name 목록 순서, 하나만)
#   Set's Name : 세트마다 그 세트 이름(네임스페이스 · 경로 없이)
#
# 기본 프로파일 `Default` = 옛 6칸 그대로 SK_MANU_CH_Name_Basic_Version (전부 Custom).
# 프로파일은 툴 폴더 안 data/ 에 저장된다(PC 별, .gitignore).
#   <A00480_FileTool>/data/
#     ├── token_profiles/<profile>.json
#     └── token_profiles_active.json

import os

from Framework.core import token_naming
from Framework.core.token_naming import RULE_CUSTOM


#: 이 툴의 규칙 묶음 (파일 이름, 세트마다 하나)
RULESET = token_naming.FILE_NAME_RULES

#: 옛 Naming 6칸의 Custom 글자 그대로
DEFAULT_TOKENS = [
    {"rule": RULE_CUSTOM, "text": "SK"},
    {"rule": RULE_CUSTOM, "text": "MANU"},
    {"rule": RULE_CUSTOM, "text": "CH"},
    {"rule": RULE_CUSTOM, "text": "Name"},
    {"rule": RULE_CUSTOM, "text": "Basic"},
    {"rule": RULE_CUSTOM, "text": "Version"},
]


def _base_dir():
    """툴 루트. this file: <tool>/app/core/naming_ops.py"""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PREFS_DIR = os.path.join(_base_dir(), "data")

#: 이 툴의 토큰 프로파일 저장소 (Export 탭 Naming 위젯이 쓴다)
TOKEN_STORE = token_naming.TokenProfileStore(PREFS_DIR, DEFAULT_TOKENS, RULESET)


def build_file_names(set_names, tokens):
    """세트마다 토큰을 조합해 파일명을 만든다.

    tokens : 토큰 dict 목록 (Custom / Numbering / Set's Name).
             Numbering = 세트 순번(목록 순서), Set's Name = 그 세트의 leaf 이름.
    빈 토큰은 건너뛰어 '__' 가 생기지 않게 한다.
    반환: (file_names, errors) - errors 가 있으면 file_names 는 빈 리스트.
    """
    tokens = RULESET.normalize_tokens(tokens)
    errors = RULESET.validate(tokens)
    if errors:
        return [], errors
    return RULESET.names_for(list(set_names), tokens), []
