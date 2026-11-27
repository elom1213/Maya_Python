# Python Script by Ji Hun Park
# last Update date : 2026-11-27
# A00210_FileManager - Path Structure library 의 PC 단위 설정 (UI/DCC 비의존)
#
# v01.60 : Path Structure 탭이 File Manager 프로파일과 무관하도록, 라이브러리 저장소 경로 · Recreate To 를
#   프로파일이 아니라 PC 하나에 하나인 파일에 둔다. git 밖(~/.jun_filemanager)이라 Push 되지 않는다.
#
#   ~/.jun_filemanager/structure_library.json
#     {"repo_dir", "remote", "branch", "remote_url", "recreate_to", "expanded"}
#
# 파일이 없으면(첫 실행) 활성 프로파일 값으로 한 번 채운다(seed) - 이후 프로파일을 바꿔도 이 값은 그대로.

import os
import json

from ..config import data_repo
from . import prefs as prefs_mod
from .paths import ui_path

SETTINGS_NAME = "structure_library.json"

# 시험에서 임시 경로로 바꿔 끼울 수 있게 모듈 속성으로 둔다. None 이면 **호출 시점의** prefs.PREFS_DIR 아래 -
# prefs.PREFS_DIR 를 임시 폴더로 바꿔 끼우는 기존 시험들이 실제 ~/.jun_filemanager 를 건드리지 않게.
SETTINGS_PATH = None

PATH_KEYS = ("repo_dir", "recreate_to")


def settings_path():
    return SETTINGS_PATH or os.path.join(prefs_mod.PREFS_DIR, SETTINGS_NAME)


def defaults():
    return {
        "repo_dir": "",
        "remote": data_repo.DATA_REPO_REMOTE,
        "branch": data_repo.DATA_REPO_BRANCH,
        "remote_url": data_repo.DATA_REPO_URL,
        "recreate_to": "",
        "expanded": None,          # 펼쳐 둔 카테고리 id 목록. None = 전부 펼침
    }


def _seed(seed_prefs):
    """첫 실행 값. git 모드 프로파일이면 그 Store Repo, 아니면 번들 기본 클론 경로."""
    data = defaults()
    seed = seed_prefs if isinstance(seed_prefs, dict) else {}
    store = (seed.get("store_dir") or "").strip()
    if seed.get("source_mode", "git") != "local" and store:
        data["repo_dir"] = store
    else:
        data["repo_dir"] = data_repo.DEFAULT_STORE_DIR
    data["recreate_to"] = seed.get("recreate_to", "") or ""
    return data


def _tidy(data):
    out = defaults()
    if isinstance(data, dict):
        out.update(data)
    for key in PATH_KEYS:
        if isinstance(out.get(key), str):
            out[key] = ui_path(out[key])
    for key in ("remote", "branch", "remote_url"):
        if not out.get(key):
            out[key] = defaults()[key]
    return out


def load(seed_prefs=None, path=None):
    """설정 dict. 파일이 없으면 seed_prefs(활성 프로파일 dict)로 채워 저장하고 반환."""
    path = path or settings_path()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return _tidy(json.load(f))
        except (OSError, ValueError):
            pass
    data = _tidy(_seed(seed_prefs))
    try:
        save(data, path=path)
    except OSError:
        pass
    return data


def save(data, path=None):
    path = path or settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_tidy(data), f, ensure_ascii=False, indent=2)
    return path
