# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00570_JaliReview - 마야 optionVar 설정 (in-Maya)

import maya.cmds as cmds

KEYS = {"clip_dir": "JUN_A00570_clipDir", "avatar": "JUN_A00570_avatar", "blendshape": "JUN_A00570_blendShape",
        "rules": "JUN_A00570_rules"}


def get(name, default=""):
    key = KEYS[name]
    return cmds.optionVar(q=key) if cmds.optionVar(exists=key) else default


def set(name, value):   # noqa: A001 - optionVar 저장
    cmds.optionVar(sv=(KEYS[name], str(value or "")))
