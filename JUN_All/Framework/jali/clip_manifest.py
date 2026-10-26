# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.jali.clip_manifest - 클립 폴더의 jali_clips.manifest.json 읽기 · 쓰기 (Maya 비의존, 순수 파이썬)
#
# A00560_JaliBatch 가 쓰고(app/core/manifest.py 는 재노출) A00570_JaliReview 가 읽는다 - 릴리즈본은 툴 간 import 금지라 공용에 둔다.
# 출력 폴더 하나 = 매니페스트 하나. 생성 설정 + 클립마다 상태. (평가서 §2-6, 계획 D10)
#   {"format": 1, "tool": "A00560_JaliBatch", "version": "01.00", "updated": "...",
#    "settings": {"controller", "mapping", "fps", "default_start", "jali", "viseme_scale", "copy_wav"},
#    "clips": {"<name>": {"name", "txt", "wav", "mb", "start", "end", "frames", "fps", "keys",
#                         "status": "generated" | "edited" | "failed" | "skipped", "generated_at", "edited_at", "error",
#                         "controller", "controller_mtime"}}}
# 쓰는 쪽: A00560 UI(Start 열 수정 · 설정) · A00560 워커(클립마다 상태) · A00570(edited_at · status edited).
# 읽는 쪽: A00560 Validate · A00570 클립 목록 (레퍼런스된 클립의 fileInfo 는 검수 씬에서 안 보이므로 start · end 는 여기서).

import json
import os
import time

FILE_NAME = "jali_clips.manifest.json"
FORMAT = 1
STATUS_GENERATED, STATUS_EDITED, STATUS_FAILED, STATUS_SKIPPED = "generated", "edited", "failed", "skipped"


def path_for(folder):
    return os.path.join(folder, FILE_NAME)


def empty(tool_version=""):
    return {"format": FORMAT, "tool": "A00560_JaliBatch", "version": tool_version,
            "updated": "", "settings": {}, "clips": {}}


def load(folder, tool_version=""):
    """매니페스트 dict. 없으면 빈 뼈대. 깨졌으면 ValueError."""
    path = path_for(folder)
    if not os.path.isfile(path):
        return empty(tool_version)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        raise ValueError("Cannot read {0}: {1}".format(path, e))
    if not isinstance(data, dict) or not isinstance(data.get("clips"), dict):
        raise ValueError("{0} is not a JALI clip manifest".format(path))
    data.setdefault("settings", {})
    data.setdefault("format", FORMAT)
    data.setdefault("tool", "A00560_JaliBatch")
    data.setdefault("version", tool_version)
    return data


def save(folder, data):
    data["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = path_for(folder)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)
    return path


def set_settings(data, settings):
    data["settings"] = dict(settings)


def clip(data, name):
    return data["clips"].get(name)


def update_clip(data, name, **fields):
    entry = data["clips"].setdefault(name, {"name": name})
    entry.update(fields)
    return entry


def start_of(data, name, default):
    """표의 Start 열 초기값 - 매니페스트에 그 클립의 start 가 있으면 그것, 없으면 default."""
    entry = data["clips"].get(name) or {}
    try:
        return int(entry.get("start", default))
    except (TypeError, ValueError):
        return int(default)


def status_of(data, name):
    entry = data["clips"].get(name) or {}
    return entry.get("status", "")


def edited_names(data, names):
    return [n for n in names if status_of(data, n) == STATUS_EDITED]


def ordered_clips(data):
    """클립 항목을 mb 이름 자연 순서로."""
    import re

    def key(item):
        return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", item.get("name", ""))]
    return sorted(data["clips"].values(), key=key)
