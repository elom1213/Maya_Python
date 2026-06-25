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
from Framework.core.maya_refresh import suspend_refresh

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

    # ==================================================
    # Copy every frame
    # ==================================================

    @staticmethod
    def _copy_every_frame_single(mesh, frames, pad):
        # 그룹/이름 충돌 방지를 위해 메시의 짧은 이름(네임스페이스/경로 제거)을 쓴다.
        short = mesh.split("|")[-1].split(":")[-1]

        dup_list = []
        for f in frames:
            cmds.currentTime(f, edit=True)
            dup = cmds.duplicate(mesh)[0]
            cmds.setAttr(dup + ".visibility", False)
            # 프레임 번호를 0 패딩(구간 전체 동일 자릿수 -> 아웃라이너 정렬도 자연스럽다).
            dup = cmds.rename(dup, "{0}_f{1:0{2}d}".format(short, f, pad))
            dup_list.append(dup)

        if dup_list:
            cmds.group(dup_list, world=True, name="{0}_frames".format(short))

        return dup_list

    @staticmethod
    def copy_every_frame(meshes, start, end):
        """선택한 메시를 [start, end] 구간 매 프레임마다 복제(visibility off)해 추출한다.

        각 메시를 프레임마다 복제하고 <mesh>_f<frame> 으로 이름 붙여 <mesh>_frames 그룹에 묶는다.
        key 를 걸지 않고 현재 씬 애니메이션 상태를 그대로 캡처한다.
        반환: (추출한 메시 수, 메시지)
        """
        valid = [m for m in (meshes or []) if cmds.objExists(m) and bsu.is_mesh(m)]
        if not valid:
            return 0, "[Warning] Select mesh(es) in the scene first."
        if start > end:
            return 0, "[Warning] Start ({0}) is greater than End ({1}).".format(start, end)

        frames = list(range(int(start), int(end) + 1))
        # 0 패딩 폭: 구간 내 프레임 문자열 최대 길이(음수 부호 포함)에 맞춰 모두 동일 자릿수.
        pad = max(len(str(f)) for f in frames)
        cur = cmds.currentTime(query=True)

        total_dups = 0
        with undo_chunk():
            try:
                # suspend_refresh: 블록 종료 시 refresh 복원이 항상 먼저/무조건 실행된다.
                with suspend_refresh():
                    for mesh in valid:
                        total_dups += len(
                            EditBSManager._copy_every_frame_single(mesh, frames, pad))
            finally:
                # 예외가 나도 현재 프레임을 원복(refresh 는 위에서 복원됨).
                cmds.currentTime(cur, edit=True)

        return total_dups, (
            "[Copy every frame] {0} mesh(es) extracted over [{1}-{2}] from {3} selected mesh(es).".format(
                total_dups, int(start), int(end), len(valid)))
