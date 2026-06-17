# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - per-PC local preferences (UI/DCC 비의존)
#
# 절대 경로 / 사용자명 등 PC 마다 다른 설정을 로컬에 저장한다.
# 이 파일은 데이터 리포(git) 밖에 있으므로 push 대상이 아니다.
#   %USERPROFILE%/.jun_filemanager/prefs.json

import os
import json

PREFS_DIR = os.path.join(
    os.path.expanduser("~"),
    ".jun_filemanager",
)

PREFS_PATH = os.path.join(PREFS_DIR, "prefs.json")

DEFAULTS = {
    "project_root": "",
    "store_dir": "",
    "scan_dir": "",
    "remote": "origin",
    "branch": "main",
    "author": "",
    "recursive": False,
}


def load():
    """prefs.json 을 읽어 dict 반환. 없으면 DEFAULTS 사본."""
    prefs = dict(DEFAULTS)

    if os.path.isfile(PREFS_PATH):
        try:
            with open(PREFS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            prefs.update(data)
        except (OSError, ValueError):
            pass

    return prefs


def save(prefs):
    """dict 를 prefs.json 으로 저장."""
    os.makedirs(PREFS_DIR, exist_ok=True)

    with open(PREFS_PATH, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)

    return PREFS_PATH
