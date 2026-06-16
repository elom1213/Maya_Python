# -*- coding: utf-8 -*-
"""
settings_io - 리스트 세팅 JSON 저장/로드.

레거시 save_multiple_tsl_to_json / load_multiple_tsl_from_json / JUN_browse_json_save_path 이식.
레거시는 textScrollList 이름을 키로 썼지만, 여기서는 UI 가 정한 논리 슬롯 id(예: "src_fk_arm_l")를
키로 하는 dict[str, list[str]] 를 그대로 저장/로드한다(위젯 비의존).
"""

import json

import maya.cmds as cmds


def browse_path(save=True):
    """JSON 파일 경로를 고르는 다이얼로그. (구 JUN_browse_json_save_path)"""
    file_mode = 0 if save else 1   # 0=save, 1=open
    state = "Save" if save else "Load"
    result = cmds.fileDialog2(
        dialogStyle=2,
        fileMode=file_mode,
        caption="{0} Setting File".format(state),
        fileFilter="Setting Files (*.json)",
    )
    if result:
        return result[0]
    return None


def save_settings(data, path):
    """data(dict[str, list[str]]) 를 JSON 으로 저장. (구 save_multiple_tsl_to_json)"""
    if not path:
        return False
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("Saved settings to: {0}".format(path))
    return True


def load_settings(path):
    """JSON 에서 dict[str, list[str]] 를 읽어 반환. (구 load_multiple_tsl_from_json)"""
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Loaded settings from: {0}".format(path))
    return data
