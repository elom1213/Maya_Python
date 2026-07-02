# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-02
# A00340_SelectionTool - selection-button config persistence (UI/DCC 비의존)
#
# 사용자가 만든 카테고리/선택 버튼을 "프로파일" 단위로 로컬에 저장한다.
# 프로파일이란 캐릭터/에셋처럼 서로 다른 묶음의 선택 버튼 세트로, JSON 파일 1개 = 1 프로파일.
# (구조/관리 방식은 A00240_PathTool.prefs 를 이식했다. 버튼이 경로 대신 오브젝트
#  이름 목록을 담는 점만 다르다.)
#
# 저장 위치는 툴 폴더 내부의 data/ 다.
#   <A00340_SelectionTool>/data/
#     ├── profiles/<profile>.json   # 예: BodyRig.json, FaceRig.json
#     └── active.json               # {"active": "<현재 프로파일>"}
#
# 프로파일 JSON 자료 구조:
#   {
#     "categories": [
#       {"name": "FK Controls",
#        "buttons": [{"name": "Arms", "objects": ["fk_arm_L", "fk_arm_R"]}]},
#       ...
#     ]
#   }

import os
import json


def _base_dir():
    """데이터 저장 기준 폴더(툴 루트). this file: <tool>/app/core/prefs.py."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PREFS_DIR = os.path.join(_base_dir(), "data")

PROFILES_DIR = os.path.join(PREFS_DIR, "profiles")
ACTIVE_PATH = os.path.join(PREFS_DIR, "active.json")

DEFAULT_PROFILE = "Default"

# 파일명으로 못 쓰는 문자(Windows 기준). 프로파일 이름 = 파일명이라 막아둔다.
_INVALID_CHARS = set('\\/:*?"<>|')


# ------------------------------------------------------------------ helpers

def sanitize_name(name):
    """프로파일 이름을 파일명으로 안전하게. 금지문자는 '_' 로 치환, 양끝 공백 제거."""
    cleaned = "".join("_" if c in _INVALID_CHARS else c for c in (name or ""))
    return cleaned.strip()


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
    """profiles 폴더 보장 + 최소 1개 프로파일 보장."""
    os.makedirs(PROFILES_DIR, exist_ok=True)

    if not list_profiles():
        save_profile(DEFAULT_PROFILE, {"categories": []})
        set_active(DEFAULT_PROFILE)


# ----------------------------------------------------------------- profiles

def list_profiles():
    """profiles 폴더의 프로파일 이름 목록(정렬)."""
    if not os.path.isdir(PROFILES_DIR):
        return []
    names = [
        fn[:-5] for fn in os.listdir(PROFILES_DIR)
        if fn.lower().endswith(".json")
    ]
    return sorted(names)


def load_profile(name):
    """프로파일 JSON 을 읽어 dict 반환. 없거나 깨지면 빈 구조."""
    data = {"categories": []}
    loaded = _read_json(_profile_path(name), None)
    if isinstance(loaded, dict):
        data.update(loaded)
    if not isinstance(data.get("categories"), list):
        data["categories"] = []
    return data


def save_profile(name, data):
    """dict 를 프로파일 JSON 으로 저장하고 경로 반환."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    path = _profile_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def delete_profile(name):
    """프로파일 JSON 삭제(없으면 무시)."""
    try:
        os.remove(_profile_path(name))
    except OSError:
        pass


def rename_profile(old, new):
    """프로파일 파일명을 바꾼다. 활성 프로파일이면 active 도 갱신."""
    # rename 후에는 get_active() 가 (옛 이름 파일이 사라져) 자가복구로 active 를
    # 바꿔버리므로, 활성 여부는 rename 전에 raw 로 읽어둔다.
    was_active = (_read_active_raw() == old)
    os.replace(_profile_path(old), _profile_path(new))
    if was_active:
        set_active(new)


# ------------------------------------------------------------ active profile

def _read_active_raw():
    """active.json 의 active 값을 보정 없이 그대로 읽는다(없으면 None)."""
    data = _read_json(ACTIVE_PATH, None)
    if isinstance(data, dict):
        return data.get("active")
    return None


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
    """활성 프로파일 이름을 저장."""
    os.makedirs(PREFS_DIR, exist_ok=True)
    with open(ACTIVE_PATH, "w", encoding="utf-8") as f:
        json.dump({"active": name}, f, ensure_ascii=False, indent=2)
