# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# Framework - 씬 정리(cleanup) 공용 함수. A00600_SceneCleanup 이 쓰고, 다른 툴도 그대로 쓸 수 있다.
#
#   delete_display_layers()   디스플레이 레이어 전부 (defaultLayer · 레퍼런스 레이어 제외)
#   delete_animation_layers() 애니메이션 레이어 전부 - **루트(BaseAnimation)까지** 지워 Layer Editor 에 안 보이게
#   delete_unused_nodes()     Hypershade > Edit > Delete Unused Nodes 와 같은 것 = MEL MLdeleteUnused 그대로
#   refresh_layer_editors()   GUI 의 Layer Editor Anim 탭 다시 그리기 (없으면 아무것도 안 함)
#
# 모두 CleanupResult(removed, warnings) 를 돌려준다. 메시지(warnings)는 UI 로그에 붙으므로 영어.
# 실측 근거는 docs/plans/A00600_SceneCleanup_plan.md §2 (mayapy 2024).

import maya.cmds as cmds
import maya.mel as mel


class CleanupResult(object):
    """정리 한 번의 결과. removed = 지운 노드 이름, warnings = 사용자에게 보일 경고(영어)."""

    def __init__(self, removed=None, warnings=None):
        self.removed = list(removed or [])
        self.warnings = list(warnings or [])

    def __repr__(self):
        return "CleanupResult(removed={0!r}, warnings={1!r})".format(self.removed, self.warnings)


def _is_referenced(node):
    try:
        return bool(cmds.referenceQuery(node, isNodeReferenced=True))
    except (RuntimeError, ValueError):
        return False


def _unlock(node):
    try:
        if cmds.lockNode(node, q=True, lock=True)[0]:
            cmds.lockNode(node, lock=False)
    except (RuntimeError, ValueError, IndexError):
        pass


# ------------------------------------------------------------------ display layers

def delete_display_layers():
    """디스플레이 레이어를 전부 지운다. 멤버 노드는 그대로(레이어 소속만 풀린다).

    `defaultLayer` 는 마야 내부 노드라 남긴다. 레퍼런스 레이어는 지울 수 없어 건너뛰고 경고한다.
    (A00210 ref_importer.delete_display_layers 와 같은 규칙)
    """
    result = CleanupResult()
    skipped = []
    for layer in cmds.ls(type="displayLayer") or []:
        if layer.split(":")[-1] == "defaultLayer":
            continue
        if _is_referenced(layer):
            skipped.append(layer)
            continue
        try:
            _unlock(layer)
            cmds.delete(layer)
            result.removed.append(layer)
        except (RuntimeError, ValueError) as exc:
            result.warnings.append("Could not delete display layer {0} : {1}".format(layer, str(exc).strip()))
    if skipped:
        result.warnings.append("Kept {0} referenced display layer(s) : {1}".format(len(skipped), ", ".join(skipped)))
    return result


# ------------------------------------------------------------------ animation layers

def delete_animation_layers():
    """애니메이션 레이어를 **루트(BaseAnimation)까지** 전부 지운다 → Layer Editor 의 Anim 탭이 빈다.

    루트를 지우면 마야가 자식 레이어 · blend 노드 · 레이어 커브를 함께 지우고 Base 커브를 어트리뷰트에 다시 꽂는다
    → **Base 레이어 애니메이션만 남고 다른 레이어 키는 사라진다**(MEL `delete BaseAnimation;` 과 같다).
    자식을 하나씩 지우면 `BaseAnimation` 이 홀로 남으므로 반드시 루트를 지운다. 이름을 박지 않고 루트를 질의한다.

    레퍼런스 레이어가 있으면 루트를 지울 수 없다 → 로컬 레이어만 하나씩 지우고 루트가 남는다고 경고한다(마야 한계).
    """
    result = CleanupResult()
    layers = cmds.ls(type="animLayer") or []
    if not layers:
        return result
    try:
        root = cmds.animLayer(q=True, root=True) or ""
    except RuntimeError:
        root = ""
    referenced = [layer for layer in layers if _is_referenced(layer)]

    if root and not referenced:
        try:
            for layer in layers:
                _unlock(layer)
            cmds.delete(root)
        except (RuntimeError, ValueError) as exc:
            result.warnings.append("Could not delete {0} : {1} - deleting layer by layer".format(
                root, str(exc).strip()))
        else:
            result.removed = [layer for layer in layers if not cmds.objExists(layer)]
            leftover = cmds.ls(type="animLayer") or []
            if leftover:
                result.warnings.append("Animation layers still in the scene : {0}".format(", ".join(leftover)))
            return result

    # 하나씩 - 레퍼런스 레이어와 루트는 남긴다. 자식이 먼저 지워지도록 깊은 것부터.
    def depth(layer):
        d = 0
        parent = layer
        while True:
            try:
                parent = cmds.animLayer(parent, q=True, parent=True)
            except RuntimeError:
                parent = None
            if not parent:
                return d
            d += 1

    for layer in sorted(layers, key=depth, reverse=True):
        if layer == root or layer in referenced or not cmds.objExists(layer):
            continue
        try:
            _unlock(layer)
            cmds.delete(layer)
            result.removed.append(layer)
        except (RuntimeError, ValueError) as exc:
            result.warnings.append("Could not delete animation layer {0} : {1}".format(layer, str(exc).strip()))
    if referenced:
        result.warnings.append(
            "{0} stays visible : {1} referenced animation layer(s) can not be deleted ({2})".format(
                root or "BaseAnimation", len(referenced), ", ".join(referenced)))
    return result


# ------------------------------------------------------------------ unused shading nodes

def _ensure_mldeleteunused():
    """GUI 마야는 스크립트 경로에서 자동으로 찾지만 mayapy 는 source 가 먼저 필요했다(실측)."""
    if not mel.eval('exists "MLdeleteUnused"'):
        mel.eval('source "MLdeleteUnused.mel"')


def delete_unused_nodes():
    """Hypershade > Edit > **Delete Unused Nodes** 와 같은 것 - 마야 MEL `MLdeleteUnused` 를 그대로 부른다.

    빈 셰이딩 그룹 → 그룹에 안 물린 머티리얼 → 출력이 안 쓰이는 텍스처 · 유틸리티(반복). 기본 머티리얼과
    레퍼런스 노드는 마야가 지우지 않는다. 지운 이름은 실행 전후 노드 목록 차이로 얻는다.
    """
    result = CleanupResult()
    _ensure_mldeleteunused()
    before = cmds.ls(long=True) or []
    mel.eval("MLdeleteUnused")
    after = set(cmds.ls(long=True) or [])
    result.removed = [node.split("|")[-1] for node in before if node not in after]
    return result


# ------------------------------------------------------------------ UI refresh

def refresh_layer_editors():
    """GUI 의 Layer Editor Anim 탭을 다시 그린다. 배치(mayapy) · 에디터가 없으면 아무것도 안 한다."""
    if cmds.about(batch=True):
        return
    try:
        if cmds.treeView("AnimLayerTabanimLayerEditor", exists=True) and mel.eval('exists "updateAnimLayerEditor"'):
            mel.eval('updateAnimLayerEditor("AnimLayerTab")')
    except RuntimeError:
        pass
