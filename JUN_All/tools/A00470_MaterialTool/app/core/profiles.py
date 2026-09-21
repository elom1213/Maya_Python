# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00470_MaterialTool - 명명 규칙 프로파일(JSON) 입출력
#
# 규칙은 코드가 아니라 **데이터**다. `data/profiles/<이름>.json` 하나가 규칙 한 벌이고,
# UI 의 Profile 콤보가 이 폴더를 그대로 보여준다. 규칙이 바뀌면 파이썬이 아니라 JSON 을
# 고친다(팀마다 다른 규칙을 파일로 나눠 가질 수 있다).
#
# 이 모듈은 maya.cmds 를 쓰지 않는다 - 헤드리스로 그대로 테스트된다.

import os
import json


# app/core/profiles.py -> app/core -> app -> <툴 루트>
TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROFILE_DIR = os.path.join(TOOL_ROOT, "data", "profiles")

PROFILE_EXT = ".json"

# 콤보가 처음 열렸을 때 고를 프로파일. 폴더에 이 이름이 없으면 목록의 첫 번째를 쓴다.
DEFAULT_PROFILE = "Set_v001"


def default_profile(names=None):
    """기본 프로파일 이름. `DEFAULT_PROFILE` 이 목록에 있으면 그것, 없으면 첫 번째."""
    if names is None:
        names = list_profiles()

    if DEFAULT_PROFILE in names:
        return DEFAULT_PROFILE

    return names[0] if names else ""


def profiles_dir():
    """프로파일 JSON 이 모여 있는 폴더 경로."""
    return PROFILE_DIR


def profile_path(name):
    """프로파일 이름 -> 파일 경로."""
    return os.path.join(PROFILE_DIR, "{0}{1}".format(name, PROFILE_EXT))


def list_profiles():
    """폴더 안 프로파일 이름 목록(확장자 제외, 이름순). 폴더가 없으면 빈 목록."""
    if not os.path.isdir(PROFILE_DIR):
        return []

    names = []
    for entry in os.listdir(PROFILE_DIR):
        if entry.lower().endswith(PROFILE_EXT):
            names.append(entry[:-len(PROFILE_EXT)])

    return sorted(names)


def load_profile_data(name):
    """프로파일 JSON 을 dict 로 읽는다. 파일이 없으면 IOError, 깨졌으면 ValueError."""
    path = profile_path(name)

    if not os.path.isfile(path):
        raise IOError("Profile not found : {0}".format(path))

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Profile '{0}' must be a JSON object.".format(name))

    # 파일 이름을 프로파일 이름의 기준으로 삼는다(콤보가 파일 이름을 보여주므로).
    data.setdefault("name", name)

    return data


def save_profile_data(name, data):
    """프로파일 dict 를 JSON 으로 쓴다(폴더가 없으면 만든다)."""
    if not os.path.isdir(PROFILE_DIR):
        os.makedirs(PROFILE_DIR)

    with open(profile_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return profile_path(name)
