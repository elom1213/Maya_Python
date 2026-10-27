# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
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


# ================================================================
# Mocap FBX Import (Exact Rotation) - v01.13
# ================================================================
#
# 본체는 Framework.core.maya_fbx_exact (A00210 일괄 처리가 요청되면 같은 코드를 쓴다).
# 마야 FBX 임포터가 비 XYZ 회전 순서 조인트의 회전 키를 뒤집는 문제를 파일 원본 키로 덮어 고친다
# (계획서 docs/plans/A00480_FileTool_fbx_exact_import_plan.md).

def scan_fbx_exact(path):
    """FBX 요약 (씬을 건드리지 않는다). 반환 (info | None, 로그 리스트)."""
    from Framework.core import maya_fbx_exact
    return maya_fbx_exact.scan(path)


def import_fbx_exact(path, skeletons=None, skeletons_only=True, unwrap=True, normalize=True, verify=True,
                     progress=None):
    """FBX 임포트 + 회전 커브를 파일 값으로. 반환 (ok, 로그 리스트)."""
    from Framework.core import maya_fbx_exact
    ok, logs, _report = maya_fbx_exact.import_exact(
        path, skeletons=skeletons, skeletons_only=skeletons_only, unwrap=unwrap, normalize=normalize,
        verify=verify, progress=progress)
    return ok, logs


def fix_scene_from_fbx(path, roots=None, unwrap=True, normalize=True, verify=True, progress=None):
    """이미 임포트한 씬의 회전 커브를 FBX 원본으로. roots 가 없으면 이름이 같은 최상위 노드. 반환 (ok, 로그 리스트)."""
    from Framework.core import maya_fbx_exact
    ok, logs, _report = maya_fbx_exact.fix_scene_from_fbx(
        path, roots=roots, unwrap=unwrap, normalize=normalize, verify=verify, progress=progress)
    return ok, logs
