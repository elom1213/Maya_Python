# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - FBX 플러그인 로드 헬퍼 (Export · Import 공용)
"""
fbx_plugin - `fbxmaya` 가 올라와 있는지 보고, 없으면 올린다.

`FBXProperty` · `FBXExport*` 같은 명령과 `cmds.file(typ="FBX export")` 는 MEL 기본이 아니라
**`fbxmaya` 플러그인이 등록하는 것**이다. 플러그인이 없으면 `Cannot find procedure` 나
`Invalid file type` 으로 죽으므로, 부르기 전에 이 함수로 올리고 안 되면 **로그로 이유를 말한다.**

(A00030_quickTool_V02 의 `import_fbx_normal` 이 하던 로드 절차를 떼어 Export 도 같이 쓴다.)
"""

FBX_PLUGIN = "fbxmaya"


def _cmds():
    """maya.cmds 를 lazy import. Maya 밖이면 None."""
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


def ensure_fbx_plugin():
    """FBX 플러그인을 올린다. 반환: (성공 여부, 로그 리스트).

    이미 올라와 있으면 로그 없이 (True, []).
    """
    cmds = _cmds()
    if cmds is None:
        return False, ["[FAIL] Maya not available."]

    try:
        loaded = cmds.pluginInfo(FBX_PLUGIN, query=True, loaded=True)
    except RuntimeError:
        loaded = False

    if loaded:
        return True, []

    try:
        cmds.loadPlugin(FBX_PLUGIN, quiet=True)
    except RuntimeError:
        return False, ["[WARN] FBX plugin ('{0}') is not available.".format(FBX_PLUGIN)]

    return True, []
