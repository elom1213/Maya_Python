# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-08
# A00370_ToolLauncher - shortcut-button config persistence (UI/DCC 비의존)
#
# 사용자가 만든 카테고리/툴 버튼을 "프로파일" 단위로 로컬에 저장한다.
# 프로파일이란 상황(리깅/페이셜/UE 익스포트 등)별로 서로 다른 툴 숏컷 세트로,
# JSON 파일 1개 = 1 프로파일이다.
# (구조/관리 방식은 A00340_SelectionTool.prefs 를 이식했다. 버튼이 오브젝트 이름
#  목록 대신 '실행할 툴 폴더 경로' 를 담는 점만 다르다.)
#
# 저장 위치는 툴 폴더 내부의 data/ 다.
#   <A00370_ToolLauncher>/data/
#     ├── profiles/<profile>.json   # 예: Default.json, Facial.json   (git 추적 — PC 간 공유)
#     ├── active.json               # {"active": "<현재 프로파일>"}     (gitignore — PC별)
#     └── local_env.json            # {"root_override": "..."}         (gitignore — PC별)
#
# 프로파일 JSON 자료 구조 (버튼 경로는 **JUN_All 루트 기준 상대경로**로 저장한다):
#   {
#     "categories": [
#       {"name": "Maya to Unreal",
#        "buttons": [{"name": "KWI Creator", "path": "tools/A00080_KWI_creator_V03"}]},
#       ...
#     ]
#   }
#
# PC 간 동기화(중요): 예전엔 버튼이 PC 마다 다른 '절대경로' 를 담아, 다른 PC 에서 Refresh Paths 를
# 누를 때마다 프로파일 JSON 이 통째로 바뀌어 git 병합 충돌이 났다. 이제 버튼은 'tools/…' 상대경로만
# 저장하므로 프로파일은 모든 PC 에서 동일하다(= 추적/공유해도 흔들리지 않음). 실제 절대경로는 실행
# 시점에 이 PC 의 JUN_All 루트(effective_root)로 resolve 한다. PC별로 다른 루트/활성프로파일은
# gitignore 된 local_env.json / active.json 에만 둔다.

import os
import json

from . import tool_launcher


def _base_dir():
    """데이터 저장 기준 폴더(툴 루트). this file: <tool>/app/core/prefs.py."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


PREFS_DIR = os.path.join(_base_dir(), "data")

PROFILES_DIR = os.path.join(PREFS_DIR, "profiles")
ACTIVE_PATH = os.path.join(PREFS_DIR, "active.json")
# PC별 로컬 설정(루트 오버라이드). gitignore 대상.
LOCAL_ENV_PATH = os.path.join(PREFS_DIR, "local_env.json")

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


# --------------------------------------------------- local env (root override)

def get_root_override():
    """PC별 JUN_All 루트 오버라이드(없거나 비어있으면 '')."""
    data = _read_json(LOCAL_ENV_PATH, None)
    if isinstance(data, dict):
        return (data.get("root_override") or "").strip()
    return ""


def set_root_override(root):
    """루트 오버라이드를 로컬 파일에 저장(gitignore 대상)."""
    os.makedirs(PREFS_DIR, exist_ok=True)
    with open(LOCAL_ENV_PATH, "w", encoding="utf-8") as f:
        json.dump({"root_override": root or ""}, f, ensure_ascii=False, indent=2)


def clear_root_override():
    """루트 오버라이드를 지운다(다시 자동 감지 사용)."""
    try:
        os.remove(LOCAL_ENV_PATH)
    except OSError:
        pass


def effective_root():
    """버튼 경로를 resolve 할 이 PC 의 JUN_All 루트.

    유효한 오버라이드가 있으면 그것을, 없으면 런처 실행 위치에서 자동 감지한 루트를 쓴다.
    """
    override = get_root_override()
    if override and os.path.isdir(override):
        return tool_launcher.normalize_path(override)
    return tool_launcher.jun_all_root()


# ------------------------------------------------------- make paths portable

def make_all_portable():
    """모든 프로파일의 버튼 경로를 이식 가능(상대) 형태로 바꿔 저장한다.

    예전 버전(또는 다른 PC)에서 만든 '절대경로' 버튼을 `tools/A000XX/...` 상대경로로
    한 번에 정규화하는 마이그레이션. 결과가 이미 상대경로면 그대로라 파일이 안 바뀐다
    (= 어느 PC 에서 눌러도 같은 결과 → git churn 없음). 'tools' 앵커가 없는 외부 절대경로는
    바꿀 수 없어 건너뛴다.

    통계 dict: changed / unchanged / skipped / total / profiles.
    """
    changed = unchanged = skipped = total = files = 0

    for name in list_profiles():
        data = load_profile(name)
        dirty = False

        for cat in data.get("categories", []):
            for btn in cat.get("buttons", []):
                total += 1
                old = btn.get("path", "")
                new = tool_launcher.to_portable(old)
                if tool_launcher._tools_tail(old) is None:
                    skipped += 1          # 외부 절대경로 — 상대화 불가
                elif new != old:
                    btn["path"] = new
                    changed += 1
                    dirty = True
                else:
                    unchanged += 1

        if dirty:
            save_profile(name, data)
            files += 1

    return {
        "changed": changed,
        "unchanged": unchanged,
        "skipped": skipped,
        "total": total,
        "profiles": files,
    }
