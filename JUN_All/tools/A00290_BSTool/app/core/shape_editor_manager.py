# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-10
# A00290_BSTool - Shape Editor 탭 핵심 로직 (maya.cmds, UI 비의존)
#
# 목적: Maya 기본 Shape Editor 의 "Edit" 토글을 대체한다.
#   Shape Editor 는 가끔 원하는 타겟을 노출하지 않아 Edit 버튼조차 없는 경우가 있다.
#   이 매니저는 blendShape 노드의 별칭(alias)에서 타겟을 직접 읽어오므로 항상 전부 보인다.
#
# 원리:
#   cmds.sculptTarget(bs, e=True, target=weightIndex)  → Edit ON
#   cmds.sculptTarget(bs, e=True, target=-1)           → Edit OFF (편집이 타겟 모양으로 확정)
#   ON 인 동안 베이스 메시에 가한 버텍스 편집은 그 타겟의 델타
#   (inputTargetItem[6000].inputPointsTarget) 로 기록된다.
#
#   주의: 같은 값을 담는 inputTarget[g].sculptTargetIndex 어트리뷰트를 setAttr 로 직접 써도
#   "편집 모드처럼" 보이지만 실제로는 동작하지 않는다. 디포머가 버텍스 편집을 가로채도록
#   설정하는 일은 sculptTarget 커맨드가 하고, setAttr 은 값만 바꾸므로 편집이 그대로
#   베이스 shape 의 tweak(.pnts) 로 들어간다(= 원본 메시가 수정됨).
#   따라서 읽기는 어트리뷰트로, 쓰기는 반드시 커맨드로 한다.
#   (Maya 의 setSculptTargetIndex.mel 은 이미 sculpt 세팅이 끝난 상태에서 인덱스만 옮기는 용도)
#
# 편집 중에는 그 타겟이 눈에 보여야 하므로 weight 를 1.0 으로 올리고,
# 편집을 끄면 원래 weight 로 되돌린다(진입 시 값을 _weight_backup 에 저장).

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import blendshape_utils as bsu


# 기본 타겟(in-between 아님)을 가리키는 sculptInbetweenWeight 값
FULL_WEIGHT = 1.0


class ShapeEditorManager:

    # Edit 진입 직전의 weight 값을 기억해 두었다가 Edit 해제 시 복원한다.
    #   {(bs_node, weight_index): 이전 weight}
    _weight_backup = {}

    # ==================================================
    # 저수준 조회
    # ==================================================

    @staticmethod
    def _geo_indices(bs_node):
        """blendShape 가 디포밍하는 지오메트리(inputTarget) 인덱스 목록."""
        return cmds.getAttr(bs_node + ".inputTarget", multiIndices=True) or []

    @staticmethod
    def _sculpt_plug(bs_node, geo_idx):
        return "{0}.inputTarget[{1}].sculptTargetIndex".format(bs_node, geo_idx)

    @staticmethod
    def weight_plug(bs_node, weight_idx):
        # 별칭(alias)에는 특수문자가 섞일 수 있어 항상 weight[i] 인덱스 plug 로 접근한다.
        return "{0}.weight[{1}]".format(bs_node, weight_idx)

    @staticmethod
    def get_edit_target(bs_node):
        """현재 Edit 모드인 타겟의 weight 인덱스. 편집 중이 아니면 -1."""
        if not bsu.is_blendshape(bs_node):
            return -1
        for geo_idx in ShapeEditorManager._geo_indices(bs_node):
            plug = ShapeEditorManager._sculpt_plug(bs_node, geo_idx)
            if not cmds.objExists(plug):
                continue
            idx = cmds.getAttr(plug)
            if idx is not None and idx != -1:
                return idx
        return -1

    @staticmethod
    def get_weight(bs_node, weight_idx):
        try:
            return cmds.getAttr(ShapeEditorManager.weight_plug(bs_node, weight_idx))
        except Exception:
            return 0.0

    @staticmethod
    def is_weight_settable(bs_node, weight_idx):
        """weight 가 잠기거나 다른 노드에 의해 구동되면 값을 바꿀 수 없다."""
        plug = ShapeEditorManager.weight_plug(bs_node, weight_idx)
        if cmds.getAttr(plug, lock=True):
            return False
        return not cmds.connectionInfo(plug, isDestination=True)

    # ==================================================
    # 타겟 목록
    # ==================================================

    @staticmethod
    def list_targets(bs_node):
        """타겟 정보를 weight 인덱스 순으로 반환.

        반환: [{"name", "index", "weight", "settable"}, ...]
        """
        if not bsu.is_blendshape(bs_node):
            return []

        result = []
        for name, idx in sorted(bsu.target_index_map(bs_node).items(),
                                key=lambda kv: kv[1]):
            result.append({
                "name": name,
                "index": idx,
                "weight": ShapeEditorManager.get_weight(bs_node, idx),
                "settable": ShapeEditorManager.is_weight_settable(bs_node, idx),
            })
        return result

    @staticmethod
    def editing_nodes():
        """씬에서 현재 Edit 모드인 blendShape 노드 목록."""
        nodes = cmds.ls(type="blendShape") or []
        return [n for n in nodes if ShapeEditorManager.get_edit_target(n) != -1]

    # ==================================================
    # weight
    # ==================================================

    @staticmethod
    def set_weight(bs_node, weight_idx, value):
        """타겟 weight 설정. 구동/잠금된 어트리뷰트면 (False, 사유) 반환."""
        if not ShapeEditorManager.is_weight_settable(bs_node, weight_idx):
            return False, "[Warning] weight[{0}] of '{1}' is locked or driven.".format(
                weight_idx, bs_node)
        cmds.setAttr(ShapeEditorManager.weight_plug(bs_node, weight_idx), value)
        return True, ""

    # ==================================================
    # Edit 토글
    # ==================================================

    @staticmethod
    def _set_sculpt_index(bs_node, weight_idx, inbetween=FULL_WEIGHT):
        """편집 대상 타겟을 지정한다(-1 이면 편집 모드 해제).

        반드시 sculptTarget 커맨드를 쓴다. 이 커맨드만이 디포머가 버텍스 편집을
        가로채도록 설정하며, sculptTargetIndex 어트리뷰트도 함께 갱신해 준다.
        """
        if weight_idx == -1:
            cmds.sculptTarget(bs_node, edit=True, target=-1)
        else:
            cmds.sculptTarget(bs_node, edit=True, target=weight_idx,
                              inbetweenWeight=inbetween)

    @staticmethod
    def _refresh_hud():
        """Maya 기본 Shape Editor 와 동일한 뷰포트 HUD 표시를 갱신한다."""
        try:
            import maya.mel as mel
            mel.eval("updateBlendShapeEditHUD")
        except Exception:
            pass

    @staticmethod
    def begin_edit(bs_node, weight_idx, select_base=True):
        """해당 타겟의 Edit 모드를 켠다(Maya Shape Editor 의 Edit 버튼 ON).

        - 같은 blendShape 에서 편집 중이던 다른 타겟은 자동으로 해제된다
          (sculptTargetIndex 는 노드당 하나만 가질 수 있다).
        - 타겟이 보이도록 weight 를 1.0 으로 올리고, 이전 값은 저장해 둔다.

        반환: (성공 여부, 메시지)
        """
        if not bsu.is_blendshape(bs_node):
            return False, "[Warning] '{0}' is not a valid blendShape node.".format(bs_node)

        targets = bsu.target_index_map(bs_node)
        if weight_idx not in targets.values():
            return False, "[Warning] weight[{0}] does not exist on '{1}'.".format(
                weight_idx, bs_node)

        msgs = []
        with undo_chunk():
            # 이전에 편집 중이던 타겟이 있으면 그 weight 부터 되돌린다.
            prev_idx = ShapeEditorManager.get_edit_target(bs_node)
            if prev_idx != -1 and prev_idx != weight_idx:
                ShapeEditorManager._restore_weight(bs_node, prev_idx)

            # envelope 가 1 이 아니면 편집한 모양이 그대로 보이지 않는다.
            if cmds.getAttr(bs_node + ".envelope") != 1.0:
                try:
                    cmds.setAttr(bs_node + ".envelope", 1.0)
                    msgs.append("envelope set to 1.0")
                except Exception:
                    msgs.append("envelope is not 1.0 and could not be changed")

            if (bs_node, weight_idx) not in ShapeEditorManager._weight_backup:
                ShapeEditorManager._weight_backup[(bs_node, weight_idx)] = \
                    ShapeEditorManager.get_weight(bs_node, weight_idx)

            ok, warn = ShapeEditorManager.set_weight(bs_node, weight_idx, 1.0)
            if not ok:
                # weight 가 구동/잠금이면 값을 못 올린다. 편집 자체는 가능하지만
                # 현재 weight 에서의 모양이 보이므로 사용자에게 알린다.
                ShapeEditorManager._weight_backup.pop((bs_node, weight_idx), None)
                msgs.append("weight is locked/driven, could not set it to 1.0")

            ShapeEditorManager._set_sculpt_index(bs_node, weight_idx)

            if select_base:
                base = bsu.find_base_mesh(bs_node)
                if base:
                    cmds.select(base, replace=True)

        ShapeEditorManager._refresh_hud()

        name = ShapeEditorManager._name_of(bs_node, weight_idx)
        msg = "[Edit ON] '{0}.{1}' - sculpt the mesh, then turn Edit off.".format(
            bs_node, name)
        if msgs:
            msg += " ({0})".format("; ".join(msgs))
        return True, msg

    @staticmethod
    def _restore_weight(bs_node, weight_idx):
        prev = ShapeEditorManager._weight_backup.pop((bs_node, weight_idx), None)
        if prev is None:
            return
        if ShapeEditorManager.is_weight_settable(bs_node, weight_idx):
            cmds.setAttr(ShapeEditorManager.weight_plug(bs_node, weight_idx), prev)

    @staticmethod
    def end_edit(bs_node):
        """Edit 모드를 끈다(편집 결과가 타겟 모양으로 확정된다).

        반환: (성공 여부, 메시지)
        """
        if not bsu.is_blendshape(bs_node):
            return False, "[Warning] '{0}' is not a valid blendShape node.".format(bs_node)

        weight_idx = ShapeEditorManager.get_edit_target(bs_node)
        if weight_idx == -1:
            return False, "[Info] '{0}' is not in edit mode.".format(bs_node)

        with undo_chunk():
            ShapeEditorManager._set_sculpt_index(bs_node, -1)
            ShapeEditorManager._restore_weight(bs_node, weight_idx)

        ShapeEditorManager._refresh_hud()

        name = ShapeEditorManager._name_of(bs_node, weight_idx)
        return True, "[Edit OFF] '{0}.{1}' - target shape updated.".format(bs_node, name)

    @staticmethod
    def exit_all_edits():
        """씬의 모든 blendShape 편집 모드를 해제한다.

        반환: (해제한 노드 수, 메시지)
        """
        nodes = ShapeEditorManager.editing_nodes()
        if not nodes:
            return 0, "[Info] No blendShape node is in edit mode."

        for node in nodes:
            ShapeEditorManager.end_edit(node)

        return len(nodes), "[Exit Edit] {0} node(s) left edit mode: {1}".format(
            len(nodes), ", ".join(nodes))

    # ==================================================
    # 기타
    # ==================================================

    @staticmethod
    def _name_of(bs_node, weight_idx):
        for name, idx in bsu.target_index_map(bs_node).items():
            if idx == weight_idx:
                return name
        return "weight[{0}]".format(weight_idx)
