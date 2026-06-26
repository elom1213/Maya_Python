# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00210_FileManager - per-PC local preferences / profiles (UI/DCC 비의존)
#
# 절대 경로 / 사용자명 등 PC 마다 다른 설정을 로컬에 저장한다(데이터 리포 git 밖이라 push X).
# 집/회사처럼 환경별 세팅 묶음을 "프로파일"(JSON 1개 = 1프로파일)로 저장·전환한다.
#
#   %USERPROFILE%/.jun_filemanager/
#     ├── profiles/<name>.json   # 예: Default.json, Home.json, Work.json (= 세팅 dict)
#     ├── active.json            # {"active": "<현재 프로파일>"}
#     └── prefs.json             # (구버전 단일 파일) → 첫 실행 시 Default 로 1회 마이그레이션
#
# 프로파일 JSON 자료 구조 = 기존 prefs.json 과 동일한 세팅 dict
#   {"project_root": "", "store_dir": "", "scan_dir": "", "remote": "...", ...}

import os
import json

from ..config import data_repo

PREFS_DIR = os.path.join(
    os.path.expanduser("~"),
    ".jun_filemanager",
)

# 구버전 단일 설정 파일(있으면 Default 프로파일로 1회 마이그레이션).
PREFS_PATH = os.path.join(PREFS_DIR, "prefs.json")

PROFILES_DIR = os.path.join(PREFS_DIR, "profiles")
ACTIVE_PATH = os.path.join(PREFS_DIR, "active.json")

DEFAULT_PROFILE = "Default"

# 파일명으로 못 쓰는 문자(Windows 기준). 프로파일 이름 = 파일명이라 막아둔다.
_INVALID_CHARS = set('\\/:*?"<>|')

# 동기화 기본값은 번들된 data_repo 설정에서 가져온다(배포받은 사용자도 바로 동기화되도록).
DEFAULTS = {
    "project_root": "",
    # 데이터 소스 방식: "git" = 중앙 git 데이터 리포(Pull/Push), "local" = 공유/NAS 폴더 직접 사용.
    "source_mode": "git",
    "store_dir": data_repo.DEFAULT_STORE_DIR,
    # local 모드에서 records/thumbs 를 직접 읽고 쓸 공유 폴더(NAS 등). git 미사용.
    "local_dir": "",
    "scan_dir": "",
    "remote": data_repo.DATA_REPO_REMOTE,
    "branch": data_repo.DATA_REPO_BRANCH,
    "remote_url": data_repo.DATA_REPO_URL,
    "author": "",
    "recursive": False,
    "show_recorded_only": False,
}

# 비어 있으면 번들 기본값으로 보정할 동기화 키들(예전 파일에 없던 키 대비).
_SYNC_BACKFILL = {
    "store_dir": data_repo.DEFAULT_STORE_DIR,
    "remote": data_repo.DATA_REPO_REMOTE,
    "branch": data_repo.DATA_REPO_BRANCH,
    "remote_url": data_repo.DATA_REPO_URL,
}


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


def _apply_defaults(data):
    """세팅 dict 에 DEFAULTS + 동기화 키 백필을 적용해 완전한 dict 로 만든다."""
    prefs = dict(DEFAULTS)
    if isinstance(data, dict):
        prefs.update(data)

    # 구버전(remote_url 키 없던 시절) 마이그레이션: 당시 기본 브랜치 "main" 은 데이터
    # 리포(master)와 어긋나므로 번들 브랜치로 교정. store_dir·author 등은 건드리지 않는다.
    if "remote_url" not in (data or {}) and prefs.get("branch") in ("", "main"):
        prefs["branch"] = data_repo.DATA_REPO_BRANCH

    for key, default in _SYNC_BACKFILL.items():
        if not prefs.get(key):
            prefs[key] = default
    return prefs


# ----------------------------------------------------------------- profiles

def list_profiles():
    """profiles 폴더의 프로파일 이름 목록(대소문자 무시 정렬)."""
    if not os.path.isdir(PROFILES_DIR):
        return []
    names = [
        fn[:-5] for fn in os.listdir(PROFILES_DIR)
        if fn.lower().endswith(".json")
    ]
    return sorted(names, key=str.lower)


def load_profile(name):
    """프로파일 JSON 을 읽어 DEFAULTS 적용한 완전한 세팅 dict 반환."""
    return _apply_defaults(_read_json(_profile_path(name), {}))


def save_profile(name, data):
    """세팅 dict 를 프로파일 JSON 으로 저장하고 경로 반환."""
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
    # rename 후엔 get_active() 가 (옛 파일이 사라져) active 를 자가복구하므로,
    # 활성 여부는 rename 전에 raw 로 읽어둔다.
    was_active = (_read_active_raw() == old)
    os.replace(_profile_path(old), _profile_path(new))
    if was_active:
        set_active(new)


def _ensure_setup():
    """profiles 폴더 보장 + 구 prefs.json 마이그레이션 + 최소 1개 프로파일 보장."""
    os.makedirs(PROFILES_DIR, exist_ok=True)

    if list_profiles():
        return

    # 구버전 단일 prefs.json 이 있으면 Default 로 옮긴다(원본은 .bak 으로 보존).
    if os.path.isfile(PREFS_PATH):
        legacy = _read_json(PREFS_PATH, {})
        save_profile(DEFAULT_PROFILE, legacy if isinstance(legacy, dict) else {})
        set_active(DEFAULT_PROFILE)
        try:
            os.replace(PREFS_PATH, PREFS_PATH + ".bak")
        except OSError:
            pass
    else:
        save_profile(DEFAULT_PROFILE, dict(DEFAULTS))
        set_active(DEFAULT_PROFILE)


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


# --------------------------------------------------- back-compat single API

def load():
    """활성 프로파일의 세팅 dict 를 반환(구 단일 prefs.load() 호환).

    다른 호출부(예: A00211_RefLineage)가 그대로 동작하도록 시그니처/반환형을 유지한다.
    """
    return load_profile(get_active())


def save(prefs):
    """세팅 dict 를 활성 프로파일에 저장(구 단일 prefs.save() 호환). 경로 반환."""
    return save_profile(get_active(), prefs)
