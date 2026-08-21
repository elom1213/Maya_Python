# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00145_RigConnect - Attribute > Create 탭의 "프로파일" 저장 (UI/DCC 비의존)
#
# 프로파일이란 **미리 적어 둔 어트리뷰트 정의 묶음**이다. 예를 들어 `UpperArm` 프로파일에
# World / Root / Shoulder 를 [0, 1] 실수로 저장해 두면, 팔 컨트롤러를 고르고 Create 만
# 누르면 세 개가 한 번에 만들어진다. 리그마다 늘 같은 어트리뷰트를 손으로 addAttr 하던
# 일을 없애는 것이 목적이다.
#
# 저장 위치·구조는 A00340_SelectionTool 의 prefs 를 그대로 따랐다(툴 폴더 안 data/).
#   <A00145_RigConnect>/data/
#     ├── attr_profiles/<profile>.json   # 예: UpperArm.json
#     └── attr_profiles_active.json      # {"active": "<현재 프로파일>"}
#
# 프로파일 JSON:
#   {"attributes": [
#      {"name": "World", "type": "float", "min": 0.0, "max": 1.0,
#       "default": 0.0, "keyable": true},
#      ...
#   ]}
#
# `min` / `max` 는 **None 이면 제한 없음**이다. bool 은 범위를 쓰지 않는다.

import os
import json
import re


# UI 에 보여 주는 타입 이름 -> maya addAttr 의 attributeType.
# 세 가지만 둔다(실수 / 정수 / 불리언) - 요청 범위이고, 그 이상은 Copy 탭이 원본에서
# 그대로 복제하는 쪽이 정확하다.
TYPE_TO_MAYA = {
    "float": "double",
    "int": "long",
    "bool": "bool",
}

ATTR_TYPES = ("float", "int", "bool")

# 범위를 쓰는 타입(불리언은 0/1 고정이라 제외).
RANGED_TYPES = ("float", "int")

DEFAULT_PROFILE = "Default"

# 파일명으로 못 쓰는 문자(Windows 기준). 프로파일 이름 = 파일명이라 막아둔다.
_INVALID_CHARS = set('\\/:*?"<>|')

# 마야 어트리뷰트 이름 규칙: 영문자/밑줄로 시작하고 그 뒤는 영숫자/밑줄.
_ATTR_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# ------------------------------------------------------------------ 경로

def _base_dir():
    """데이터 저장 기준 폴더(툴 루트). this file: <tool>/app/core/attr_profile_prefs.py."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PREFS_DIR = os.path.join(_base_dir(), "data")
PROFILES_DIR = os.path.join(PREFS_DIR, "attr_profiles")
ACTIVE_PATH = os.path.join(PREFS_DIR, "attr_profiles_active.json")


# ------------------------------------------------------------------ 이름

def sanitize_name(name):
    """프로파일 이름을 파일명으로 안전하게. 금지문자는 '_' 로 치환, 양끝 공백 제거."""
    cleaned = "".join("_" if c in _INVALID_CHARS else c for c in (name or ""))
    return cleaned.strip()


def is_valid_attr_name(name):
    """마야 어트리뷰트로 쓸 수 있는 이름인지."""
    return bool(_ATTR_NAME_RE.match(name or ""))


# ------------------------------------------------------------------ 스펙

def normalize_spec(spec):
    """UI/JSON 에서 온 dict 를 항상 같은 모양으로 정리한다.

    - 알 수 없는 타입은 "float" 로 본다.
    - bool 은 범위를 지우고 default 를 0/1 로 맞춘다.
    - int 는 범위/기본값을 정수로 맞춘다.
    - min > max 면 서로 바꾼다(사용자가 거꾸로 넣는 일이 흔하다).
    - **default 는 범위 안으로 자른다.** addAttr 은 범위 밖 defaultValue 를 에러가
      아니라 **경고 후 무시**해 버리므로(실측), 잘라 두지 않으면 사용자가 적은 기본값이
      조용히 사라진다.

    Raises:
        ValueError: 이름이 비었거나 마야 어트리뷰트 이름 규칙에 어긋날 때.
    """
    name = (spec.get("name") or "").strip()
    if not name:
        raise ValueError("Attribute name is empty.")
    if not is_valid_attr_name(name):
        raise ValueError(
            "'{0}' is not a valid attribute name. Use letters, digits and "
            "underscore, starting with a letter or underscore.".format(name))

    attr_type = spec.get("type")
    if attr_type not in ATTR_TYPES:
        attr_type = "float"

    keyable = bool(spec.get("keyable", True))

    if attr_type == "bool":
        default = 1 if _as_float(spec.get("default"), 0.0) else 0
        return {"name": name, "type": "bool", "min": None, "max": None,
                "default": default, "keyable": keyable}

    minimum = _as_optional_float(spec.get("min"))
    maximum = _as_optional_float(spec.get("max"))
    if minimum is not None and maximum is not None and minimum > maximum:
        minimum, maximum = maximum, minimum

    default = _as_float(spec.get("default"), 0.0)
    if minimum is not None:
        default = max(default, minimum)
    if maximum is not None:
        default = min(default, maximum)

    if attr_type == "int":
        minimum = None if minimum is None else int(round(minimum))
        maximum = None if maximum is None else int(round(maximum))
        default = int(round(default))
        # 반올림 때문에 다시 범위를 벗어날 수 있다(예: min 0.6 -> 1, default 0.4 -> 0).
        if minimum is not None:
            default = max(default, minimum)
        if maximum is not None:
            default = min(default, maximum)

    return {"name": name, "type": attr_type, "min": minimum, "max": maximum,
            "default": default, "keyable": keyable}


def _as_float(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _as_optional_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def describe_spec(spec):
    """리스트에 보여 줄 한 줄 설명. 예: 'World   float [0, 1]  default 0'."""
    parts = [spec["type"]]
    if spec["type"] in RANGED_TYPES:
        low = "-inf" if spec["min"] is None else _g(spec["min"])
        high = "inf" if spec["max"] is None else _g(spec["max"])
        parts.append("[{0}, {1}]".format(low, high))
    parts.append("default {0}".format(_g(spec["default"])))
    if not spec["keyable"]:
        parts.append("non-keyable")
    return "   ".join(parts)


def _g(value):
    if isinstance(value, bool):
        return "on" if value else "off"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return "{0:g}".format(value) if isinstance(value, float) else str(value)


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
    """profiles 폴더 보장 + 최소 1개 프로파일 보장."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    if not list_profiles():
        save_profile(DEFAULT_PROFILE, {"attributes": []})
        set_active(DEFAULT_PROFILE)


# ----------------------------------------------------------------- profiles

def list_profiles():
    """attr_profiles 폴더의 프로파일 이름 목록(정렬)."""
    if not os.path.isdir(PROFILES_DIR):
        return []
    names = [fn[:-5] for fn in os.listdir(PROFILES_DIR)
             if fn.lower().endswith(".json")]
    return sorted(names)


def load_profile(name):
    """프로파일 JSON 을 읽어 dict 반환. 깨진 항목은 조용히 건너뛴다."""
    loaded = _read_json(_profile_path(name), None)
    attrs = []
    if isinstance(loaded, dict) and isinstance(loaded.get("attributes"), list):
        for raw in loaded["attributes"]:
            if not isinstance(raw, dict):
                continue
            try:
                attrs.append(normalize_spec(raw))
            except ValueError:
                continue
    return {"attributes": attrs}


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
    # 바꿔 버리므로, 활성 여부는 rename 전에 raw 로 읽어둔다.
    was_active = (_read_active_raw() == old)
    os.replace(_profile_path(old), _profile_path(new))
    if was_active:
        set_active(new)


# ------------------------------------------------------------ active profile

def _read_active_raw():
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
