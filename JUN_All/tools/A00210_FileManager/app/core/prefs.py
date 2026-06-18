# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - per-PC local preferences (UI/DCC 비의존)
#
# 절대 경로 / 사용자명 등 PC 마다 다른 설정을 로컬에 저장한다.
# 이 파일은 데이터 리포(git) 밖에 있으므로 push 대상이 아니다.
#   %USERPROFILE%/.jun_filemanager/prefs.json

import os
import json

from ..config import data_repo

PREFS_DIR = os.path.join(
    os.path.expanduser("~"),
    ".jun_filemanager",
)

PREFS_PATH = os.path.join(PREFS_DIR, "prefs.json")

# 동기화 기본값은 번들된 data_repo 설정에서 가져온다(배포받은 사용자도 바로 동기화되도록).
DEFAULTS = {
    "project_root": "",
    "store_dir": data_repo.DEFAULT_STORE_DIR,
    "scan_dir": "",
    "remote": data_repo.DATA_REPO_REMOTE,
    "branch": data_repo.DATA_REPO_BRANCH,
    "remote_url": data_repo.DATA_REPO_URL,
    "author": "",
    "recursive": False,
}

# 비어 있으면 번들 기본값으로 보정할 동기화 키들(예전 prefs.json 에 없던 키 대비).
_SYNC_BACKFILL = {
    "store_dir": data_repo.DEFAULT_STORE_DIR,
    "remote": data_repo.DATA_REPO_REMOTE,
    "branch": data_repo.DATA_REPO_BRANCH,
    "remote_url": data_repo.DATA_REPO_URL,
}


def load():
    """prefs.json 을 읽어 dict 반환. 없으면 DEFAULTS 사본."""
    prefs = dict(DEFAULTS)
    data = {}

    if os.path.isfile(PREFS_PATH):
        try:
            with open(PREFS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            prefs.update(data)
        except (OSError, ValueError):
            data = {}

    # 구버전 prefs.json(= remote_url 키가 없던 시절) 마이그레이션: 동기화 대상이 번들
    # 데이터 리포에 맞도록 보정한다. 당시 기본 브랜치였던 "main" 은 데이터 리포(master)와
    # 어긋나므로 번들 브랜치로 교정. store_dir(개인 clone 위치)·author 등은 건드리지 않는다.
    if "remote_url" not in data and prefs.get("branch") in ("", "main"):
        prefs["branch"] = data_repo.DATA_REPO_BRANCH

    # 비어 있는 동기화 키는 번들 기본값으로 보정(remote_url 누락 등).
    for key, default in _SYNC_BACKFILL.items():
        if not prefs.get(key):
            prefs[key] = default

    return prefs


def save(prefs):
    """dict 를 prefs.json 으로 저장."""
    os.makedirs(PREFS_DIR, exist_ok=True)

    with open(PREFS_PATH, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)

    return PREFS_PATH
