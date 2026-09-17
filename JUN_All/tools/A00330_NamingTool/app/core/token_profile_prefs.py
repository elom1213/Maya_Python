# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00330_NamingTool - Rename > Token 탭의 "프로파일" 저장 (UI/DCC 비의존)
#
# 프로파일 = **토큰 규칙 한 벌**. 예) Default = dyn_asset_side_{index}_{index}, pad 2.
# 저장 위치·구조는 A00145_RigConnect `attr_profile_prefs` 를 그대로 따랐다(툴 폴더 안 data/).
#   <A00330_NamingTool>/data/
#     ├── token_profiles/<profile>.json   # {"tokens": [{"rule": ..., ...}, ...]}
#     └── token_profiles_active.json      # {"active": "<현재 프로파일>"}
#
# 프로파일이 하나도 없으면 레거시 기본 규칙으로 `Default` 를 만든다.

import os
import json

from .token_ops import normalize_tokens, default_tokens


DEFAULT_PROFILE = "Default"

# 파일명으로 못 쓰는 문자(Windows 기준). 프로파일 이름 = 파일명이라 막아둔다.
_INVALID_CHARS = set('\\/:*?"<>|')


# ------------------------------------------------------------------ 경로

def _base_dir():
    """툴 루트. this file: <tool>/app/core/token_profile_prefs.py"""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PREFS_DIR = os.path.join(_base_dir(), "data")
PROFILES_DIR = os.path.join(PREFS_DIR, "token_profiles")
ACTIVE_PATH = os.path.join(PREFS_DIR, "token_profiles_active.json")


def sanitize_name(name):
    """프로파일 이름을 파일명으로 안전하게. 금지문자는 '_' 로, 양끝 공백 제거."""
    cleaned = "".join("_" if c in _INVALID_CHARS else c for c in (name or ""))
    return cleaned.strip()


# ------------------------------------------------------------------ 파일 IO

def _profile_path(name):
    return os.path.join(PROFILES_DIR, name + ".json")


def _read_json(path, fallback):
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    return fallback


def _ensure_setup():
    """profiles 폴더 + 최소 1개 프로파일(Default = 레거시 규칙) 보장."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    if not list_profiles():
        save_profile(DEFAULT_PROFILE, default_tokens())
        set_active(DEFAULT_PROFILE)


def list_profiles():
    if not os.path.isdir(PROFILES_DIR):
        return []
    return sorted(fn[:-5] for fn in os.listdir(PROFILES_DIR)
                  if fn.lower().endswith(".json"))


def load_profile(name):
    """프로파일의 토큰 목록. 파일이 없거나 깨졌거나 비었으면 레거시 기본 규칙."""
    loaded = _read_json(_profile_path(name), None)
    tokens = []
    if isinstance(loaded, dict) and isinstance(loaded.get("tokens"), list):
        tokens = normalize_tokens(t for t in loaded["tokens"] if isinstance(t, dict))
    return tokens or default_tokens()


def save_profile(name, tokens):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    path = _profile_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"tokens": normalize_tokens(tokens)}, f, ensure_ascii=False, indent=2)
    return path


def delete_profile(name):
    try:
        os.remove(_profile_path(name))
    except OSError:
        pass


def rename_profile(old, new):
    """파일명을 바꾼다. 활성 프로파일이면 active 도 갱신."""
    was_active = (_read_active_raw() == old)
    os.replace(_profile_path(old), _profile_path(new))
    if was_active:
        set_active(new)


# ------------------------------------------------------------ active profile

def _read_active_raw():
    data = _read_json(ACTIVE_PATH, None)
    return data.get("active") if isinstance(data, dict) else None


def get_active():
    """현재 활성 프로파일 이름(항상 존재하는 것으로 보정)."""
    _ensure_setup()
    active = _read_active_raw()
    profiles = list_profiles()
    if active not in profiles:
        active = profiles[0] if profiles else DEFAULT_PROFILE
        set_active(active)
    return active


def set_active(name):
    os.makedirs(PREFS_DIR, exist_ok=True)
    with open(ACTIVE_PATH, "w", encoding="utf-8") as f:
        json.dump({"active": name}, f, ensure_ascii=False, indent=2)
