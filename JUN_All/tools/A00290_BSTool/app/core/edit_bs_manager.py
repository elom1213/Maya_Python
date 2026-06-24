# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00290_BSTool - Edit BS 탭 핵심 로직 (maya.cmds, UI 비의존)
#
# 레거시 JUN_PY_BSTool_V01_01 의 Edit BS 탭 기능 이식:
#   - key_every_target   : 각 타겟을 프레임 idx 에서 1, idx-1/idx+1 에서 0 으로 키 (타겟별 순차 노출)
#   - copy_every_target  : 위 키를 건 뒤, 프레임마다 베이스 메시를 복제해 타겟 모양을
#                          타겟 이름으로 추출(visibility off) → worldGroup 으로 묶음

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import blendshape_utils as bsu


class EditBSManager:

    # ==================================================
    # Key every target
    # ==================================================

    @staticmethod
    def _key_every_target_single(bs_node):
        weights = cmds.blendShape(bs_node, query=True, weight=True) or []
        for idx in range(len(weights)):
            plug = "{0}.weight[{1}]".format(bs_node, idx)
            cmds.setKeyframe(plug, t=idx, v=1)
            cmds.setKeyframe(plug, t=idx - 1, v=0)
            cmds.setKeyframe(plug, t=idx + 1, v=0)
        return len(weights)

    @staticmethod
    def key_every_target(bs_nodes):
        """각 blendShape 노드의 모든 타겟을 프레임순으로 1/0 키한다.

        반환: (처리한 노드 수, 메시지)
        """
        nodes = [n for n in (bs_nodes or []) if bsu.is_blendshape(n)]
        if not nodes:
            return 0, "[Warning] No valid blendShape node in the list."

        total = 0
        with undo_chunk():
            for node in nodes:
                total += EditBSManager._key_every_target_single(node)

        return len(nodes), "[Key every target] {0} node(s), {1} target(s) keyed.".format(
            len(nodes), total)

    # ==================================================
    # Copy every target
    # ==================================================

    @staticmethod
    def _copy_every_target_single(bs_node):
        target_names = bsu.get_blendshape_targets(bs_node)
        base_mesh = bsu.find_base_mesh(bs_node)

        if not base_mesh:
            cmds.warning("Base mesh not found for '{0}'.".format(bs_node))
            return []

        dup_list = []
        for idx, name in enumerate(target_names):
            cmds.currentTime(idx, edit=True)
            dup = cmds.duplicate(base_mesh)[0]
            cmds.setAttr(dup + ".visibility", False)
            dup = cmds.rename(dup, name)
            dup_list.append(dup)

        if dup_list:
            cmds.group(dup_list, world=True, name="{0}_targets".format(bs_node))

        return dup_list

    @staticmethod
    def copy_every_target(bs_nodes):
        """모든 타겟 모양을 메시로 복제 추출한다(먼저 key_every_target 수행).

        반환: (추출한 메시 수, 메시지)
        """
        nodes = [n for n in (bs_nodes or []) if bsu.is_blendshape(n)]
        if not nodes:
            return 0, "[Warning] No valid blendShape node in the list."

        total_dups = 0
        with undo_chunk():
            for node in nodes:
                EditBSManager._key_every_target_single(node)
            for node in nodes:
                total_dups += len(EditBSManager._copy_every_target_single(node))

        return total_dups, "[Copy every target] {0} mesh(es) extracted from {1} node(s).".format(
            total_dups, len(nodes))
