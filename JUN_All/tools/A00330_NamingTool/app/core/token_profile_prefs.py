# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-28
# A00330_NamingTool - Rename > Token 탭의 "프로파일" 저장 (UI/DCC 비의존)
#
# 프로파일 = **토큰 규칙 한 벌**. 예) Default = dyn_asset_side_{index}_{index}, pad 2.
# v01.10 : 저장 코드는 공용 `Framework.core.token_naming.TokenProfileStore` 로 올렸다.
# 저장 위치 · 파일 모양은 그대로다(툴 폴더 안 data/ - 예전 프로파일이 그대로 읽힌다).
#   <A00330_NamingTool>/data/
#     ├── token_profiles/<profile>.json   # {"tokens": [{"rule": ..., ...}, ...]}
#     └── token_profiles_active.json      # {"active": "<현재 프로파일>"}
#
# 프로파일이 하나도 없으면 레거시 기본 규칙으로 `Default` 를 만든다.

import os

from Framework.core.token_naming import TokenProfileStore, DEFAULT_PROFILE  # noqa: F401

from .token_ops import RULESET, default_tokens


def _base_dir():
    """툴 루트. this file: <tool>/app/core/token_profile_prefs.py"""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PREFS_DIR = os.path.join(_base_dir(), "data")

#: 이 툴의 프로파일 저장소 (Token 탭 위젯이 쓴다)
STORE = TokenProfileStore(PREFS_DIR, default_tokens(), RULESET)

PROFILES_DIR = STORE.profiles_dir
ACTIVE_PATH = STORE.active_path

# 예전 모듈 함수 이름 그대로
sanitize_name = STORE.sanitize_name
list_profiles = STORE.list_profiles
load_profile = STORE.load_profile
save_profile = STORE.save_profile
delete_profile = STORE.delete_profile
rename_profile = STORE.rename_profile
get_active = STORE.get_active
set_active = STORE.set_active
