# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00480_FileTool / Maya 탭 - 현재 씬 보호 (maya.cmds, 함수 안 lazy import)
#
# 스캔(.mb) · 임포트는 다른 파일을 **열어서** 작업하므로 현재 씬이 닫힌다. 작업 전에 현재 씬의
# 상태를 적어 두고(경로 · 수정 여부), 끝나면 다시 연다. "저장할까?" 를 묻는 다이얼로그는 UI 몫이다 -
# 여기는 사실(수정됐는가)과 동작(저장 · 복원)만 준다.
#
# 사용 형태(2026-10-12 결정): 이 작업을 위해 마야를 띄우는 경우가 대부분이라 작업 중인 씬이 열려 있는
# 일은 드물다. 그래도 untitled 수정 씬은 저장할 수 없으므로 `Don't Save` 또는 취소만 가능하다.


def _cmds():
    import maya.cmds as cmds
    return cmds


def current_scene():
    """{"path": 절대경로 또는 "", "modified": bool, "untitled": bool}"""
    cmds = _cmds()
    path = cmds.file(q=True, sceneName=True) or ""
    modified = bool(cmds.file(q=True, modified=True))
    return {"path": path, "modified": modified, "untitled": not path}


def save_current():
    """현재 씬을 제자리에 저장한다(untitled 면 False)."""
    cmds = _cmds()
    if not (cmds.file(q=True, sceneName=True) or ""):
        return False
    cmds.file(save=True, force=True)
    return True


def restore(info):
    """적어 둔 씬으로 돌아간다 - 경로가 있으면 다시 열고, untitled 였으면 새 씬."""
    cmds = _cmds()
    path = (info or {}).get("path") or ""
    if path:
        cmds.file(path, open=True, force=True, prompt=False, ignoreVersion=True)
    else:
        cmds.file(new=True, force=True)
    return path


def new_scene():
    _cmds().file(new=True, force=True)
