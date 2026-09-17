# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - Import 탭 로직 (maya.mel, UI 비의존)
"""
import_ops - 임포트 설정.

A00030_quickTool_V02 `quick_ops.import_fbx_normal` 을 옮겼다. 동작은 같고,
플러그인 로드는 공용 `fbx_plugin.ensure_fbx_plugin` 이 한다.
결과는 **로그 문자열 리스트**로 돌려준다(UI 가 로그창에 쌓는다).
"""

from .fbx_plugin import FBX_PLUGIN, ensure_fbx_plugin


def _mel():
    try:
        import maya.mel as mel
        return mel
    except Exception:
        return None


def import_fbx_normal():
    """FBX 임포트 때 **노멀을 파일 것 그대로** 쓰게 한다(OverrideNormalsLock).

    다음 임포트부터 적용되는 **전역 FBX 설정**이다 - 지금 씬을 바꾸지 않는다.
    """
    ok, logs = ensure_fbx_plugin()
    if not ok:
        return logs + ["[WARN] Cannot set the import option."]

    mel = _mel()
    try:
        mel.eval('FBXProperty "Import|IncludeGrp|Geometry|OverrideNormalsLock" -v 1')
    except (RuntimeError, AttributeError):
        return ["[WARN] FBX plugin ('{0}') did not provide FBXProperty - "
                "cannot set the import option.".format(FBX_PLUGIN)]

    return ["FBX import : OverrideNormalsLock ON (applies to the next import)."]
