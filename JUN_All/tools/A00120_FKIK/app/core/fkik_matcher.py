# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00120_FKIK - 매칭 / 베이크 로직 (maya.cmds, UI 무관)
#
# 2026-06-15: bake() 를 Python 프레임 루프 -> native bakeResults 로 교체(대규모 구간 속도 개선).
# 2026-06-19: bake() 의 refresh suspend 누수 수정 — suspend_refresh() 컨텍스트 매니저로
#             감싸 복원이 항상 먼저/무조건 실행되도록 했다(임시 컨스트레인트 delete 가
#             실패해도 뷰포트가 프리즈되지 않음). bake_constraint() 도 delete 를 finally 로.
#
# 레거시 JUN_MATCH_twoObjects / JUN_matcher_FKIK / JUN_cmd_match_IK_and_FK /
#        JUN_cmd_bake_IK_FK / JUN_cmd_bake_IK_to_FK 를 현대화.

import maya.cmds as cmds

from Framework.core.maya_refresh import suspend_refresh
from tools.A00120_FKIK.app.config import naming
from tools.A00120_FKIK.app.core.selection_utils import order_by_tokens


# --------------------------------------------------
# 단일/리스트 트랜스폼 매칭
# --------------------------------------------------

def match_transforms(
    tgt_list,
    flw_list,
    rot_order=True,
    rot_axis=True,
    translate=True,
    rotate=True,
):
    """
    tgt_list[i] 의 월드 트랜스폼을 flw_list[i] 로 복사. (레거시 JUN_MATCH_twoObjects)

    follower 의 원래 rotateOrder 는 작업 후 복원한다.
    """

    count = min(len(tgt_list), len(flw_list))

    for i in range(count):
        tgt = tgt_list[i]
        flw = flw_list[i]

        tgt_rot_order = cmds.xform(tgt, q=True, rotateOrder=True)
        tgt_rot_axis  = cmds.xform(tgt, q=True, rotateAxis=True)
        tgt_trs       = cmds.xform(tgt, q=True, worldSpace=True, translation=True)
        tgt_rot       = cmds.xform(tgt, q=True, worldSpace=True, rotation=True)

        flw_rot_order_ori = cmds.xform(flw, q=True, rotateOrder=True)

        if rot_order:
            cmds.xform(flw, rotateOrder=tgt_rot_order)

        if rot_axis:
            cmds.xform(flw, rotateAxis=tgt_rot_axis)

        if translate:
            cmds.xform(flw, worldSpace=True, translation=tgt_trs)

        if rotate:
            cmds.xform(flw, worldSpace=True, rotation=tgt_rot)

        cmds.xform(flw, rotateOrder=flw_rot_order_ori)


# --------------------------------------------------
# Matcher
# --------------------------------------------------

class FKIKMatcher:

    @staticmethod
    def build_pairs(
        all_targets,
        all_followers,
        arm_l,
        arm_r,
        leg_l,
        leg_r,
        ik_to_fk,
    ):
        """
        활성 부위(arm/leg L/R)와 방향(ik_to_fk)에 맞는 (tgt_list, flw_list) 구성.
        두 리스트는 같은 index 끼리 대응한다.

        all_targets / all_followers 는 UI 리스트의 전체 항목(실제 오브젝트명).
        """

        flags = [
            ("arm_l", arm_l),
            ("arm_r", arm_r),
            ("leg_l", leg_l),
            ("leg_r", leg_r),
        ]

        tgt_tokens = []
        flw_tokens = []

        for key, enabled in flags:
            if enabled:
                group_tgt, group_flw = naming.LIMB_GROUPS[key]
                tgt_tokens.extend(group_tgt)
                flw_tokens.extend(group_flw)

        # 실제 오브젝트로 해석 (부위 토큰 순)
        tgt_objs = order_by_tokens(all_targets, tgt_tokens)
        flw_objs = order_by_tokens(all_followers, flw_tokens)

        # 방향별 정규 순서로 재정렬 -> tgt[i] <-> flw[i] 정렬 보장
        if ik_to_fk:
            tgt_objs = order_by_tokens(tgt_objs, naming.IK_TGT_TOKENS)
            flw_objs = order_by_tokens(flw_objs, naming.IK_FLW_TOKENS)
        else:
            tgt_objs = order_by_tokens(tgt_objs, naming.FK_TGT_TOKENS)
            flw_objs = order_by_tokens(flw_objs, naming.FK_FLW_TOKENS)

        return tgt_objs, flw_objs

    @staticmethod
    def match(tgt_list, flw_list):
        """현재 프레임에서 한 번 매칭. undo chunk 로 감쌈."""
        if not tgt_list or not flw_list:
            return 0

        cmds.undoInfo(openChunk=True)
        try:
            match_transforms(tgt_list, flw_list, 1, 1, 1, 1)
        finally:
            cmds.undoInfo(closeChunk=True)

        return min(len(tgt_list), len(flw_list))

    @staticmethod
    def bake(tgt_list, flw_list, start, end):
        """
        [start, end] 구간을 native bakeResults 로 베이크. (구 Python 프레임 루프 대체)

        각 (tgt, flw) 쌍에 임시 parentConstraint(mo=False) 를 건 뒤 bakeResults 로
        구간 전체를 일괄 샘플링하고, 베이크 후 컨스트레인트를 삭제한다.
        world 결과는 기존 match_transforms 베이크와 동치이며 (rotateAxis≠0 인 특수
        리그에서는 rotateAxis attr 자체는 복사하지 않음, 월드 포즈는 동일),
        currentTime/xform 프레임 루프를 제거해 대규모 구간에서 수십 배 빠르다.

        match_transforms 가 scale 을 건드리지 않으므로 translate/rotate 만 베이크한다.
        시그니처/반환값(end - start + 1)은 기존과 동일하여 호출부 무수정.

        Maya 2023(Python 3.9) 포함 동작 확인됨.
        """
        if not tgt_list or not flw_list:
            return 0

        count = min(len(tgt_list), len(flw_list))
        flw = flw_list[:count]
        attrs = ["tx", "ty", "tz", "rx", "ry", "rz"]   # match_transforms 는 scale 미사용

        cur = cmds.currentTime(q=True)

        cmds.undoInfo(openChunk=True)
        cons = []
        try:
            # suspend_refresh: 블록 종료 시 refresh 복원이 "항상 먼저/무조건" 실행된다.
            # 아래 finally 의 delete 가 실패해도 뷰포트가 프리즈되지 않는다(전역 누수 방지).
            with suspend_refresh():
                for i in range(count):
                    try:
                        cons += cmds.parentConstraint(
                            tgt_list[i], flw[i], maintainOffset=False
                        )
                    except Exception as e:
                        # 락/연결된 attr 등으로 컨스트레인트 실패 -> 해당 쌍 skip
                        cmds.warning(
                            "FKIK bake: skip pair %s -> %s (%s)"
                            % (tgt_list[i], flw[i], e)
                        )

                if cons:
                    cmds.bakeResults(
                        flw,
                        simulation=True,
                        time=(start, end),
                        sampleBy=1,
                        attribute=attrs,
                        disableImplicitControl=True,
                        preserveOutsideKeys=True,
                        sparseAnimCurveBake=False,
                    )
        finally:
            # 임시 컨스트레인트 정리는 독립적으로 감싼다(실패해도 이후 복원이 진행되도록).
            try:
                if cons:
                    cmds.delete([c for c in cons if cmds.objExists(c)])
            except Exception as e:
                cmds.warning("FKIK bake: constraint cleanup failed (%s)" % e)
            cmds.currentTime(cur, edit=True)
            cmds.undoInfo(closeChunk=True)

        return end - start + 1

    @staticmethod
    def bake_constraint(tgt_list, flw_list):
        """
        parentConstraint 로 묶어 bakeSimulation. (레거시 JUN_cmd_bake_IK_to_FK 복원)

        개선: range(0, 8) 하드코딩 -> 쌍 개수 기반, 베이크 후 임시 컨스트레인트 삭제.
        """
        if not tgt_list or not flw_list:
            return 0

        count = min(len(tgt_list), len(flw_list))

        sim_attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]

        time_start = cmds.playbackOptions(minTime=True, q=True)
        time_end = cmds.playbackOptions(maxTime=True, q=True)

        cmds.undoInfo(openChunk=True)
        constraints = []
        try:
            for i in range(count):
                con = cmds.parentConstraint(
                    tgt_list[i], flw_list[i], maintainOffset=True
                )
                constraints.extend(con)

            cmds.bakeSimulation(
                flw_list[:count],
                sb=1,
                t=(time_start, time_end),
                at=sim_attrs,
                hi="none",
            )
        finally:
            # 베이크 후 임시 컨스트레인트 정리 (레거시는 남겨뒀음 -> 개선).
            # finally 로 옮겨 bakeSimulation 이 실패해도 컨스트레인트가 남지 않게 한다.
            for con in constraints:
                if cmds.objExists(con):
                    cmds.delete(con)
            cmds.undoInfo(closeChunk=True)

        return count
