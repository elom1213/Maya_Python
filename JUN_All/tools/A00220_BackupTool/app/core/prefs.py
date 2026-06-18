# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00220_BackupTool - per-PC local preferences (UI/DCC 비의존)
#
# 대상 파일 목록 / 옵션 등 PC 마다 다른 설정을 로컬에 저장한다.
#   %USERPROFILE%/.jun_backuptool/prefs.json

import os
import json

PREFS_DIR = os.path.join(
    os.path.expanduser("~"),
    ".jun_backuptool",
)

PREFS_PATH = os.path.join(PREFS_DIR, "prefs.json")

DEFAULTS = {
    "files": [],
    "folder_name": "backup",
    "suffix": "BU",
    "versioned": False,
    "max_versions": 10,
    "minutes": 5,
    "seconds": 0,
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
