# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00290_BSTool - Base Shape 탭 핵심 로직 (maya.cmds, UI 비의존)
#
# 목적: 선택한 blendShape 타겟의 "기본(weight=1.0) 모양"을 다시 정의한다.
#
# 아이디어:
#   blendShape 결과 = base + weight * delta  (delta = 타겟의 포인트 오프셋)
#   weight = X (예: 0.5 또는 1.3) 에서 보이던 모양을 weight = 1.0 의 모양으로 만들려면
#   delta 를 X 배 하면 된다.
#       new_delta = delta * X
#       => weight 1.0 일 때: base + 1.0 * (delta*X) = base + X*delta = 예전 weight X 모양
#
#   따라서 "값 X 의 모양을 1.0 의 기본 모양으로" == 타겟 포인트 델타를 X 배 스케일.
#
# 델타는 blendShape 노드의 다음 plug 에 pointArray 로 저장된다:
#   inputTarget[g].inputTargetGroup[w].inputTargetItem[i].inputPointsTarget
#     g = 출력 지오메트리 인덱스, w = weight(타겟) 인덱스, i = 6000(=weight 1.0) 등
#   in-between 타겟이 있으면 inputTargetItem 인덱스가 여러 개일 수 있어 모두 스케일한다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import blendshape_utils as bsu


class BaseShapeManager:

    # ==================================================
    # 조회
    # ==================================================

    @staticmethod
    def list_targets(bs_node):
        """blendShape 타겟 이름 목록(weight 인덱스 순)."""
        return bsu.get_blendshape_targets(bs_node)

    # ==================================================
    # 델타 스케일
    # ==================================================

    @staticmethod
    def _scale_group_deltas(bs_node, geo_idx, grp_idx, factor):
        """inputTargetGroup[grp_idx] 의 모든 inputTargetItem 포인트 델타를 factor 배.

        반환: (스케일된 item 수, 영향받은 포인트 수)
        """
        group_plug = "{0}.inputTarget[{1}].inputTargetGroup[{2}]".format(
            bs_node, geo_idx, grp_idx)

        item_indices = cmds.getAttr(group_plug + ".inputTargetItem",
                                    multiIndices=True) or []
        items_done = 0
        points_done = 0

        for it in item_indices:
            plug = "{0}.inputTargetItem[{1}].inputPointsTarget".format(group_plug, it)
            pts = cmds.getAttr(plug) or []
            if not pts:
                continue

            new_pts = []
            for p in pts:
                w = p[3] if len(p) > 3 else 1.0
                new_pts.append((p[0] * factor, p[1] * factor, p[2] * factor, w))

            cmds.setAttr(plug, len(new_pts), *new_pts, type="pointArray")
            items_done += 1
            points_done += len(new_pts)

        return items_done, points_done

    @staticmethod
    def apply_value_as_default(bs_node, target_names, value):
        """선택 타겟들의 weight=value 모양을 weight=1.0 의 기본 모양으로 만든다.

        내부적으로 각 타겟의 포인트 델타를 value 배 스케일한다.

        Args:
            bs_node      : blendShape 노드 이름
            target_names : 대상 타겟 이름 리스트
            value        : 기준 값 X (0 이 아니어야 함)

        반환: (처리한 타겟 수, 메시지)
        """
        if not bsu.is_blendshape(bs_node):
            return 0, "[Warning] '{0}' is not a valid blendShape node.".format(bs_node)

        if not target_names:
            return 0, "[Warning] No target selected."

        if value is None or abs(value) < 1e-6:
            return 0, "[Warning] Value must be non-zero."

        name_to_idx = bsu.target_index_map(bs_node)
        geo_indices = cmds.getAttr(bs_node + ".inputTarget", multiIndices=True) or [0]

        done = 0
        skipped = []
        with undo_chunk():
            for name in target_names:
                grp_idx = name_to_idx.get(name)
                if grp_idx is None:
                    skipped.append(name)
                    continue

                touched_pts = 0
                for geo_idx in geo_indices:
                    _items, pts = BaseShapeManager._scale_group_deltas(
                        bs_node, geo_idx, grp_idx, value)
                    touched_pts += pts

                if touched_pts == 0:
                    # 저장된 포인트 델타가 없는 타겟(예: 라이브 지오 입력으로 연결됨)
                    skipped.append(name)
                    continue

                done += 1

        msg = "[Base Shape] '{0}' : {1} target(s) rescaled by x{2} (value {2} -> 1.0).".format(
            bs_node, done, value)
        if skipped:
            msg += " Skipped (no stored deltas / unknown): {0}".format(", ".join(skipped))

        return done, msg
