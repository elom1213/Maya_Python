# Python Script by Ji Hun Park
# last Update date : 2026-10-01
# A00490_KeyboardTool - preset save / load (UI/DCC 비의존)
#
# 프리셋 = 키 시퀀스 + 루프 + 전송 방식 설정. 대상 창은 저장하지 않는다
# (창 핸들은 실행할 때마다 바뀐다).
#   <tool>/data/presets/<name>.json
# exe(frozen) 로 실행하면 exe 옆 data/ 에 저장한다 (A00240 prefs 와 같은 이유 - _MEIPASS 는 휘발).

import os
import sys
import json


def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


PRESETS_DIR = os.path.join(_base_dir(), "data", "presets")
_INVALID_CHARS = set('\\/:*?"<>|')


def sanitize_name(name):
    return "".join("_" if c in _INVALID_CHARS else c for c in (name or "")).strip()


def _path(name):
    return os.path.join(PRESETS_DIR, name + ".json")


def list_presets():
    if not os.path.isdir(PRESETS_DIR):
        return []
    return sorted(fn[:-5] for fn in os.listdir(PRESETS_DIR) if fn.lower().endswith(".json"))


def load_preset(name):
    try:
        with open(_path(name), "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def save_preset(name, data):
    os.makedirs(PRESETS_DIR, exist_ok=True)
    path = _path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def delete_preset(name):
    try:
        os.remove(_path(name))
        return True
    except OSError:
        return False
