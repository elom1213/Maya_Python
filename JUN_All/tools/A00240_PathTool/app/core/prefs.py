# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00240_PathTool - shortcut config persistence (UI/DCC 비의존)
#
# 사용자가 만든 카테고리/경로 버튼을 "프로파일" 단위로 로컬에 저장한다.
# 프로파일이란 집/회사처럼 서로 다른 환경의 경로 묶음으로, JSON 파일 1개 = 1 프로파일.
#
# 저장 위치는 툴 폴더 내부의 data/ 다(%USERPROFILE% 아님).
#   <A00240_PathTool>/data/
#     ├── profiles/<profile>.json   # 예: Home.json, Work.json
#     └── active.json               # {"active": "<현재 프로파일>"}
#
# 단, PyInstaller --onefile exe 로 실행하면 코드는 임시폴더(_MEIPASS)에 풀리므로
# 거기에 쓰면 종료 시 사라진다. 그래서 frozen 일 때는 __file__ 이 아니라 exe 가 있는
# 폴더 옆 data/ 에 저장한다(영속 + "툴 폴더 내부" 유지).
#
# 프로파일 JSON 자료 구조:
#   {
#     "categories": [
#       {"name": "Textures",
#        "buttons": [{"name": "char_tex", "path": "C:/.../tex"}]},
#       ...
#     ]
#   }

import os
import sys
import json


def _base_dir():
    """데이터 저장 기준 폴더. exe(frozen)면 exe 가 있는 폴더, 아니면 툴 루트."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # this file: <tool>/app/core/prefs.py → 3단계 위가 툴 루트
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PREFS_DIR = os.path.join(_base_dir(), "data")

PROFILES_DIR = os.path.join(PREFS_DIR, "profiles")
ACTIVE_PATH = os.path.join(PREFS_DIR, "active.json")

# 구버전 데이터 — 있으면 Default 프로파일로 1회 마이그레이션한다.
#   1) 같은 data/ 폴더의 단일 shortcuts.json
#   2) 더 옛 위치인 %USERPROFILE%/.jun_pathtool/shortcuts.json
LEGACY_PATHS = [
    os.path.join(PREFS_DIR, "shortcuts.json"),
    os.path.join(os.path.expanduser("~"), ".jun_pathtool", "shortcuts.json"),
]

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
    """profiles 폴더 보장 + 구버전 마이그레이션 + 최소 1개 프로파일 보장."""
    os.makedirs(PROFILES_DIR, exist_ok=True)

    if not list_profiles():
        # 구버전 shortcuts.json 이 있으면 Default 로 옮긴다(첫 번째로 발견된 것).
        legacy_src = next((p for p in LEGACY_PATHS if os.path.isfile(p)), None)
        if legacy_src:
            legacy = _read_json(legacy_src, {"categories": []})
            if not isinstance(legacy, dict):
                legacy = {"categories": []}
            save_profile(DEFAULT_PROFILE, legacy)
            set_active(DEFAULT_PROFILE)
            try:
                os.replace(legacy_src, legacy_src + ".bak")
            except OSError:
                pass
        else:
            save_profile(DEFAULT_PROFILE, {"categories": []})


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
