# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-06
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
# 델타를 X 배 하는 방법은 타겟이 어떻게 저장돼 있느냐에 따라 두 가지이고(baked / live),
# live 타겟은 델타 공간을 되돌려 메시를 옮겨야 한다. 그 저수준 처리는 전부
# delta_utils 에 있다(v01.17 에서 Mix Targets 탭과 공유하려고 분리) — 자세한 설명은
# delta_utils.py 의 헤더 주석 참고.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import blendshape_utils as bsu
from . import delta_utils as du


class BaseShapeManager:

    # ==================================================
    # 조회
    # ==================================================

    @staticmethod
    def list_targets(bs_node):
        """blendShape 타겟 이름 목록(weight 인덱스 순)."""
        return bsu.get_blendshape_targets(bs_node)

    # ==================================================
    # 델타 스케일 (그룹 단위)
    # ==================================================

    @staticmethod
    def _scale_live_item(bs_node, geo_idx, plug, shape, factor):
        """연결된 타겟 메시를 옮겨 델타를 factor 배로 만든다.

        반환: (처리한 포인트 수, 실패 사유 또는 None)
        """
        deltas = du.read_item_deltas(plug)
        if deltas is None:
            return 0, "component list did not match delta count"
        if not deltas:
            return 0, None

        offset = factor - 1.0
        offsets = {v: (d[0] * offset, d[1] * offset, d[2] * offset)
                   for v, d in deltas.items()}
        expected = {v: (d[0] * factor, d[1] * factor, d[2] * factor)
                    for v, d in deltas.items()}

        ok, problem = du.apply_live_offsets(
            bs_node, geo_idx, plug, shape, offsets, expected)
        return (len(deltas), None) if ok else (0, problem)

    @staticmethod
    def _scale_group_deltas(bs_node, geo_idx, grp_idx, factor):
        """inputTargetGroup 의 모든 inputTargetItem 델타를 factor 배.

        item 마다 live(타겟 메시 연결) / baked(델타만) 를 따로 판정한다. in-between
        타겟은 item 이 여러 개이고 각자 다른 메시에 연결돼 있을 수 있다.

        반환: (포인트 수, live item 수, 실패 사유 목록)
        """
        group = du.group_plug(bs_node, geo_idx, grp_idx)

        points_done = 0
        live_items = 0
        problems = []

        for it in du.item_indices(group):
            plug = du.item_plug(group, it)
            shape = du.live_target_shape(plug)

            if shape:
                pts, problem = BaseShapeManager._scale_live_item(
                    bs_node, geo_idx, plug, shape, factor)
                points_done += pts
                if pts:
                    live_items += 1
                if problem:
                    problems.append(problem)
            else:
                points_done += du.scale_baked_item(plug, factor)

        return points_done, live_items, problems

    @staticmethod
    def apply_value_as_default(bs_node, target_names, value):
        """선택 타겟들의 weight=value 모양을 weight=1.0 의 기본 모양으로 만든다.

        타겟이 baked 면 노드의 델타를, live(타겟 메시가 연결됨)면 **타겟 메시 자체**를
        고쳐서 그 순간 기본 모양이 바뀌게 한다. 어느 쪽이든 씬을 저장하거나 Shape Editor
        의 Edit 로 들어가도 되돌아오지 않는다.

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
        live_targets = 0
        skipped = []
        problems = []

        with undo_chunk():
            for name in target_names:
                grp_idx = name_to_idx.get(name)
                if grp_idx is None:
                    skipped.append(name)
                    continue

                touched_pts = 0
                touched_live = 0
                for geo_idx in geo_indices:
                    pts, live, probs = BaseShapeManager._scale_group_deltas(
                        bs_node, geo_idx, grp_idx, value)
                    touched_pts += pts
                    touched_live += live
                    problems.extend("{0}: {1}".format(name, p) for p in probs)

                if touched_pts == 0:
                    skipped.append(name)
                    continue

                done += 1
                if touched_live:
                    live_targets += 1

        msg = "[Base Shape] '{0}' : {1} target(s) rescaled by x{2} (value {2} -> 1.0).".format(
            bs_node, done, value)
        if live_targets:
            msg += (" {0} of them are live targets - their target mesh was moved"
                    " so the change sticks.".format(live_targets))
        if skipped:
            msg += " Skipped (no stored deltas / unknown): {0}".format(", ".join(skipped))
        if problems:
            msg += " Problems: {0}".format("; ".join(problems))

        return done, msg
