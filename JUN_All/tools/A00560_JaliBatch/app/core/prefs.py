# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - PC 로컬 설정 (UI/DCC 비의존)
#
#   %USERPROFILE%/.jun_jalibatch/prefs.json  - mayapy 경로 · 컨트롤러 · 최근 폴더 · 옵션 (절대 경로라 PC 마다 다르다, git 밖)

import os
import json

PREFS_DIR = os.path.join(os.path.expanduser("~"), ".jun_jalibatch")
PREFS_PATH = os.path.join(PREFS_DIR, "prefs.json")

DEFAULTS = {
    "mayapy_path": "",          # 비어 있으면 자동 탐색 (Framework.core.mayapy_runner.find_mayapy)
    "controller": "",           # JALI 슬라이더 컨트롤러 .ma/.mb (A0030_jali_slider_ctl_direct_arkit.ma)
    "source_dir": "",           # 변환기 출력 폴더
    "output_dir": "",           # 클립 .mb 폴더 (비어 있으면 <source>/maya)
    "fps": "30",                # 콤보 글자 (사용자 수정 가능)
    "default_start": 1,
    "mapping": "jali_slider_dummy_in",
    "jali_mode": "data",        # data | fixed
    "jali_fixed": [0.6, 0.6],
    "overwrite": "skip",        # skip | overwrite | backup
    "copy_wav": True,
    "skip_edited": True,        # 재생성 때 edited 클립은 건너뛰기 (기본 체크)
    "validate_dir": "",         # Validate 탭 클립 폴더
    "repath_controller": "",
}


def load():
    data = dict(DEFAULTS)
    if os.path.isfile(PREFS_PATH):
        try:
            with open(PREFS_PATH, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
            if isinstance(saved, dict):
                data.update(saved)
        except (OSError, ValueError):
            pass
    return data


def save(data):
    try:
        if not os.path.isdir(PREFS_DIR):
            os.makedirs(PREFS_DIR)
        with open(PREFS_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=True)
        return True
    except OSError:
        return False
