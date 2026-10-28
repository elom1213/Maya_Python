# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-28
# A00340_SelectionTool - selection-button config persistence (UI/DCC 비의존)
#
# 사용자가 만든 카테고리/선택 버튼을 "프로파일" 단위로 저장한다.
# 프로파일이란 캐릭터/에셋처럼 서로 다른 묶음의 선택 버튼 세트로, JSON 파일 1개 = 1 프로파일.
# (구조/관리 방식은 A00240_PathTool.prefs 를 이식했다. 버튼이 경로 대신 오브젝트
#  이름 목록을 담는 점만 다르다.)
#
# 저장 위치 (v01.17 부터 두 곳 - 계획서 docs/plans/A00340_SelectionTool_shared_profiles_plan.md)
#   <A00340_SelectionTool>/data/            # git 제외 (.gitignore **/A00340_SelectionTool/data/)
#     ├── profiles/<profile>.json           # 로컬 프로파일
#     ├── rules/<rule>.json                 # 로컬 규칙 (select_rules)
#     └── active.json                       # {"active": "<이름>", "active_scope": "local"|"shared",
#                                           #  "shared_dir": "<PC 별 공유 루트>", "show_controls": true, ...}
#   <A00340_SelectionTool>/shared/          # git 추적 - 공유하고 싶은 것만 여기로 (Share)
#     ├── profiles/<profile>.json
#     └── rules/<rule>.json
#   공유 루트는 PC 별로 바꿀 수 있다(active.json 의 shared_dir - NAS · 별도 데이터 저장소).
#   git 은 무시된 폴더 안을 `!` 로 다시 포함시키지 못하므로 공유 폴더는 data/ **밖**이다.
#
# 프로파일의 정체는 (scope, 이름) - 같은 이름이 로컬과 공유에 함께 있어도 따로 다룬다.
# 함수들은 scope 인자의 기본값이 "local" 이라 v01.16 이하의 호출은 그대로 동작한다.
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
import shutil


def _base_dir():
    """데이터 저장 기준 폴더(툴 루트). this file: <tool>/app/core/prefs.py."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PREFS_DIR = os.path.join(_base_dir(), "data")

PROFILES_DIR = os.path.join(PREFS_DIR, "profiles")
LOCAL_RULES_DIR = os.path.join(PREFS_DIR, "rules")
ACTIVE_PATH = os.path.join(PREFS_DIR, "active.json")

DEFAULT_PROFILE = "Default"

SCOPE_LOCAL = "local"
SCOPE_SHARED = "shared"
SCOPES = (SCOPE_LOCAL, SCOPE_SHARED)

#: 공유 루트 기본값 - 툴 폴더 안 shared/ (git 추적)
DEFAULT_SHARED_ROOT = os.path.join(_base_dir(), "shared")
#: active.json 에 PC 별 공유 루트를 저장하는 키
SHARED_DIR_KEY = "shared_dir"
ACTIVE_SCOPE_KEY = "active_scope"

# 파일명으로 못 쓰는 문자(Windows 기준). 프로파일 이름 = 파일명이라 막아둔다.
_INVALID_CHARS = set('\\/:*?"<>|')


# ------------------------------------------------------------------ helpers

def sanitize_name(name):
    """프로파일 이름을 파일명으로 안전하게. 금지문자는 '_' 로 치환, 양끝 공백 제거."""
    cleaned = "".join("_" if c in _INVALID_CHARS else c for c in (name or ""))
    return cleaned.strip()


def _check_scope(scope):
    if scope not in SCOPES:
        raise ValueError("unknown scope: {0!r}".format(scope))
    return scope


def _read_json(path, fallback):
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    return fallback


# ------------------------------------------------------------- shared root

def configured_shared_root():
    """active.json 에 적힌 공유 루트 (없으면 "")."""
    value = get_setting(SHARED_DIR_KEY, "")
    return value if isinstance(value, str) else ""


def shared_root():
    """지금 쓰는 공유 루트. 설정된 경로가 있는 폴더면 그것, 아니면 DEFAULT_SHARED_ROOT."""
    configured = configured_shared_root()
    if configured and os.path.isdir(configured):
        return configured
    return DEFAULT_SHARED_ROOT


def shared_root_missing():
    """설정은 돼 있는데 그 폴더가 없으면 그 경로 (다른 PC 의 경로 등). 아니면 ""."""
    configured = configured_shared_root()
    return configured if configured and not os.path.isdir(configured) else ""


def set_shared_root(path):
    """공유 루트를 바꾼다. "" 이면 기본(툴 안 shared/)으로 되돌린다."""
    set_setting(SHARED_DIR_KEY, os.path.normpath(path) if path else "")


def profiles_dir(scope=SCOPE_LOCAL):
    _check_scope(scope)
    return PROFILES_DIR if scope == SCOPE_LOCAL else os.path.join(shared_root(), "profiles")


def rules_dir(scope=SCOPE_LOCAL):
    _check_scope(scope)
    return LOCAL_RULES_DIR if scope == SCOPE_LOCAL else os.path.join(shared_root(), "rules")


# ----------------------------------------------------------------- profiles

def _profile_path(name, scope=SCOPE_LOCAL):
    return os.path.join(profiles_dir(scope), name + ".json")


def profile_path(name, scope=SCOPE_LOCAL):
    """프로파일 JSON 의 절대 경로 (v01.10, View > Show Profile 이 탐색기로 연다)."""
    return _profile_path(name, scope)


def _ensure_setup():
    """로컬 profiles 폴더 보장 + 로컬 · 공유를 합쳐 최소 1개 프로파일 보장."""
    os.makedirs(PROFILES_DIR, exist_ok=True)

    if not list_all_profiles():
        save_profile(DEFAULT_PROFILE, {"categories": []})
        set_active(DEFAULT_PROFILE, SCOPE_LOCAL)


def list_profiles(scope=SCOPE_LOCAL):
    """그 scope 폴더의 프로파일 이름 목록(정렬)."""
    folder = profiles_dir(scope)
    if not os.path.isdir(folder):
        return []
    names = [
        fn[:-5] for fn in os.listdir(folder)
        if fn.lower().endswith(".json")
    ]
    return sorted(names)


def list_all_profiles():
    """[(scope, name)] - 로컬 먼저(이름순), 그다음 공유(이름순)."""
    return ([(SCOPE_LOCAL, n) for n in list_profiles(SCOPE_LOCAL)]
            + [(SCOPE_SHARED, n) for n in list_profiles(SCOPE_SHARED)])


def load_profile(name, scope=SCOPE_LOCAL):
    """프로파일 JSON 을 읽어 dict 반환. 없거나 깨지면 빈 구조."""
    data = {"categories": []}
    loaded = _read_json(_profile_path(name, scope), None)
    if isinstance(loaded, dict):
        data.update(loaded)
    if not isinstance(data.get("categories"), list):
        data["categories"] = []
    return data


def save_profile(name, data, scope=SCOPE_LOCAL):
    """dict 를 프로파일 JSON 으로 저장하고 경로 반환."""
    os.makedirs(profiles_dir(scope), exist_ok=True)
    path = _profile_path(name, scope)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def delete_profile(name, scope=SCOPE_LOCAL):
    """프로파일 JSON 삭제(없으면 무시). 그 프로파일의 네임스페이스 매핑도 지운다(v01.18)."""
    try:
        os.remove(_profile_path(name, scope))
    except OSError:
        pass
    _move_namespace_map((scope, name), None)


def rename_profile(old, new, scope=SCOPE_LOCAL):
    """프로파일 파일명을 바꾼다(같은 scope 안). 활성 프로파일이면 active 도 갱신."""
    # rename 후에는 get_active() 가 (옛 이름 파일이 사라져) 자가복구로 active 를
    # 바꿔버리므로, 활성 여부는 rename 전에 raw 로 읽어둔다.
    was_active = (_read_active_raw() == (scope, old))
    os.replace(_profile_path(old, scope), _profile_path(new, scope))
    _move_namespace_map((scope, old), (scope, new))
    if was_active:
        set_active(new, scope)


def share_profile(name):
    """로컬 프로파일을 공유 폴더로 **옮긴다**. 공유에 같은 이름이 있으면 ValueError. 반환: 새 경로."""
    src = _profile_path(name, SCOPE_LOCAL)
    dst = _profile_path(name, SCOPE_SHARED)
    if not os.path.isfile(src):
        raise ValueError("local profile '{0}' not found".format(name))
    if os.path.exists(dst):
        raise ValueError("a shared profile named '{0}' already exists".format(name))
    was_active = (_read_active_raw() == (SCOPE_LOCAL, name))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    _move_namespace_map((SCOPE_LOCAL, name), (SCOPE_SHARED, name))
    if was_active:
        set_active(name, SCOPE_SHARED)
    return dst


def copy_profile_to_local(name):
    """공유 프로파일을 로컬로 **복사한다**. 로컬에 같은 이름이 있으면 ValueError. 반환: 새 경로."""
    src = _profile_path(name, SCOPE_SHARED)
    dst = _profile_path(name, SCOPE_LOCAL)
    if not os.path.isfile(src):
        raise ValueError("shared profile '{0}' not found".format(name))
    if os.path.exists(dst):
        raise ValueError("a local profile named '{0}' already exists".format(name))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst


# ------------------------------------------------------------ active profile

def _read_active_raw():
    """active.json 의 (scope, name) 을 보정 없이 읽는다. scope 가 없으면 local (v01.16 이하 호환). 없으면 None."""
    data = _read_json(ACTIVE_PATH, None)
    if isinstance(data, dict) and data.get("active"):
        scope = data.get(ACTIVE_SCOPE_KEY) or SCOPE_LOCAL
        return (scope if scope in SCOPES else SCOPE_LOCAL, data.get("active"))
    return None


def get_active_ref():
    """현재 활성 프로파일 (scope, name) - 항상 존재하는 것으로 보정한다."""
    _ensure_setup()

    active = _read_active_raw()
    profiles = list_all_profiles()
    if active not in profiles:
        active = profiles[0] if profiles else (SCOPE_LOCAL, DEFAULT_PROFILE)
        set_active(active[1], active[0])
    return active


def get_active():
    """현재 활성 프로파일 이름 (호환용 - scope 가 필요하면 get_active_ref)."""
    return get_active_ref()[1]


def set_active(name, scope=SCOPE_LOCAL):
    """활성 프로파일을 저장. 같은 파일의 다른 설정(show_controls 등)은 보존한다."""
    data = _read_active_dict()
    data["active"] = name
    data[ACTIVE_SCOPE_KEY] = _check_scope(scope)
    _write_active_dict(data)


# ------------------------------------------------------------- window settings
# 프로파일과 무관한 창 설정(Controls 표시 여부 등)도 active.json 에 함께 둔다.
# 파일 하나 = dict 하나. 키를 하나 바꿀 때 나머지 키는 그대로 다시 쓴다.

def _read_active_dict():
    data = _read_json(ACTIVE_PATH, None)
    return dict(data) if isinstance(data, dict) else {}


def _write_active_dict(data):
    os.makedirs(PREFS_DIR, exist_ok=True)
    with open(ACTIVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_setting(key, default=None):
    """active.json 의 설정값 하나. 없으면 default."""
    return _read_active_dict().get(key, default)


def set_setting(key, value):
    """active.json 의 설정값 하나를 쓴다(다른 키는 보존)."""
    data = _read_active_dict()
    data[key] = value
    _write_active_dict(data)


# ------------------------------------------------------------ namespace maps (v01.18)
# 선택할 때 바꿔 끼울 {원래 ns: 대상 ns} 를 프로파일마다 · PC 마다 기억한다 (active.json - git 제외).
#   "namespace_maps": {"shared:MUE_BCM": {"test:ZIHAN:Cage": "test:IVI:Cage"}, ...}

NAMESPACE_MAPS_KEY = "namespace_maps"


def _map_key(scope, name):
    return "{0}:{1}".format(scope, name)


def get_namespace_map(scope, name):
    """그 프로파일에 저장된 매핑 {원래: 대상} (없으면 {})."""
    maps = get_setting(NAMESPACE_MAPS_KEY, {})
    value = maps.get(_map_key(scope, name)) if isinstance(maps, dict) else None
    return dict(value) if isinstance(value, dict) else {}


def set_namespace_map(scope, name, mapping):
    """매핑을 저장한다. 원래 == 대상 인 쌍은 빼고, 비면 키를 지운다."""
    data = _read_active_dict()
    maps = data.get(NAMESPACE_MAPS_KEY)
    maps = dict(maps) if isinstance(maps, dict) else {}
    clean = dict((s, d) for s, d in (mapping or {}).items() if s != d)
    key = _map_key(scope, name)
    if clean:
        maps[key] = clean
    else:
        maps.pop(key, None)
    data[NAMESPACE_MAPS_KEY] = maps
    _write_active_dict(data)


def _move_namespace_map(old_ref, new_ref):
    """프로파일 이름 바꾸기 · Share 때 매핑 키를 옮긴다. new_ref 가 None 이면 지운다(Delete)."""
    data = _read_active_dict()
    maps = data.get(NAMESPACE_MAPS_KEY)
    if not isinstance(maps, dict):
        return
    value = maps.pop(_map_key(*old_ref), None)
    if value is None:
        return
    if new_ref is not None:
        maps[_map_key(*new_ref)] = value
    data[NAMESPACE_MAPS_KEY] = maps
    _write_active_dict(data)
