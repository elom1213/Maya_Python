# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00120_FKIK - Setup 로직 (선택 -> targets / followers 해석)
#
# 레거시 JUN_cmd_FKIKTool_setup_btn 에서 UI 갱신(cmds.text/textScrollList)을 제거하고
# 순수 입출력으로 분리. 결과를 dict 로 반환하고 표시는 UI 가 담당.

from tools.A00120_FKIK.app.config import naming
from tools.A00120_FKIK.app.core.selection_utils import (
    make_hierarchy_list,
    filter_by_shape_types,
    filter_by_tokens,
    order_by_tokens,
)


class FKIKSetup:

    @staticmethod
    def resolve(selection):
        """
        선택(top node 들)으로부터 Targets(pos) / Followers(ctl) 목록을 해석.

        반환: {
            "ok": bool,
            "targets": [...],      # ordered pos objects
            "followers": [...],    # ordered ctl objects
            "message": str,        # 영어 상태 메시지
        }
        """

        if not selection:
            return FKIKSetup._fail("Failed : nothing selected")

        # 선택 계층 전체 (shape 제외)
        obj_children = make_hierarchy_list(selection, reverse=True, dedupe=True)

        # BlendFKIKPos_grp 탐색
        blend_grp = [
            obj for obj in obj_children
            if naming.BLEND_GRP_TOKEN in obj
        ]

        if not blend_grp:
            return FKIKSetup._fail(
                f"Failed : '{naming.BLEND_GRP_TOKEN}' not found"
            )

        blend_grp = blend_grp[:1]

        # position 오브젝트 (follicle / locator) 검증
        pos_objs = make_hierarchy_list(blend_grp, reverse=True, dedupe=True)
        pos_all = filter_by_shape_types(pos_objs, naming.POS_SHAPES)

        if len(pos_all) != naming.NUM_POS:
            return FKIKSetup._fail(
                f"Failed : position count mismatch ({len(pos_all)}/{naming.NUM_POS})"
            )

        # controller 오브젝트 (nurbsCurve) 검증
        ctls_all = filter_by_shape_types(obj_children, naming.CTL_SHAPE)
        ctls_matched = filter_by_tokens(ctls_all, naming.CTL_TOKENS)

        if len(ctls_matched) != naming.NUM_POS:
            return FKIKSetup._fail(
                f"Failed : controller count mismatch ({len(ctls_matched)}/{naming.NUM_POS})"
            )

        # 토큰 순서대로 정렬
        targets = order_by_tokens(pos_all, naming.TGT_POS_TOKENS)
        followers = order_by_tokens(ctls_matched, naming.CTL_TOKENS)

        return {
            "ok": True,
            "targets": targets,
            "followers": followers,
            "message": "Success",
        }

    @staticmethod
    def _fail(message):
        return {
            "ok": False,
            "targets": [],
            "followers": [],
            "message": message,
        }
