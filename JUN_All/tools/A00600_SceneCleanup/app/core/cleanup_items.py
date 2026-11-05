# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00600_SceneCleanup - 정리 항목 레지스트리.
#
# **새 항목 = CleanupItem 서브클래스 하나 + 아래 ITEMS 에 한 줄.** UI 는 ITEMS 를 읽어 체크 행을 만들고,
# runner 는 체크한 항목을 ITEMS 순서대로 돌린다. label / tooltip 은 UI 에 보이므로 영어.
# 실제 정리는 공용 Framework/core/maya_cleanup.py (다른 툴도 쓸 수 있게).

from Framework.core import maya_cleanup


class CleanupItem(object):
    """정리 항목 하나. run() 은 maya_cleanup.CleanupResult 를 돌려준다."""

    key = ""            # 고유 키 (테스트 · 로그용)
    label = ""          # 체크 행 글자
    tooltip = ""
    default = True      # 창을 열 때 체크 상태

    def run(self):
        raise NotImplementedError


class DisplayLayersItem(CleanupItem):
    key = "display_layers"
    label = "Delete all display layers"
    tooltip = ("Delete every display layer (defaultLayer is Maya's own and stays).\n"
               "The member objects stay in the scene. Referenced layers can not be deleted.")

    def run(self):
        return maya_cleanup.delete_display_layers()


class AnimLayersItem(CleanupItem):
    key = "anim_layers"
    label = "Delete all animation layers (incl. BaseAnimation)"
    tooltip = ("Delete every animation layer including BaseAnimation, so the Anim tab of the Layer Editor is empty.\n"
               "Only the BaseAnimation keys stay on the objects - keys on the other layers are removed.\n"
               "Merge the layers first if you need them. Referenced layers keep BaseAnimation alive.")

    def run(self):
        return maya_cleanup.delete_animation_layers()


class UnusedNodesItem(CleanupItem):
    key = "unused_nodes"
    label = "Delete unused nodes (Hypershade)"
    tooltip = ("Same as Hypershade > Edit > Delete Unused Nodes (MLdeleteUnused):\n"
               "empty shading groups, materials not used by any shading group,\n"
               "and texture / utility nodes whose output is not used.\n"
               "Default materials and referenced nodes are kept.")

    def run(self):
        return maya_cleanup.delete_unused_nodes()


# 실행 순서 = 이 순서. Unused nodes 는 앞 항목이 남긴 고아 노드까지 정리하도록 맨 뒤에 둔다.
ITEMS = [
    DisplayLayersItem(),
    AnimLayersItem(),
    UnusedNodesItem(),
]


def item_by_key(key):
    for item in ITEMS:
        if item.key == key:
            return item
    return None
