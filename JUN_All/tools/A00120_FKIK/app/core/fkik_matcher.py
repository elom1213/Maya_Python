# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00120_FKIK - 매칭 / 베이크 로직 (maya.cmds, UI 무관)
#
# 2026-06-15: bake() 를 Python 프레임 루프 -> native bakeResults 로 교체(대규모 구간 속도 개선).
# 2026-06-19: bake() 의 refresh suspend 누수 수정 — suspend_refresh() 컨텍스트 매니저로
#             감싸 복원이 항상 먼저/무조건 실행되도록 했다(임시 컨스트레인트 delete 가
#             실패해도 뷰포트가 프리즈되지 않음). bake_constraint() 도 delete 를 finally 로.
# 2026-06-22: 구간 베이크 시 베이크 구간 밖의 기존 키가 사라지던 버그 수정. 임시
#             parentConstraint 를 거는 순간 기존 animCurve 가 플러그에서 분리(pairBlend)
#             되어 bakeResults 의 preserveOutsideKeys 가 바깥 키를 보존하지 못한다.
#             -> 컨스트레인트를 걸기 전에 [start, end] 밖의 키(값/탄젠트)를 스냅샷하고
#             베이크 후 복원하도록 했다(_snapshot_outside_keys / _restore_outside_keys).
# 2026-06-29: bake() 의 parentConstraint+bakeResults 방식을 완전히 폐기. 컨트롤러가 여러
#             애니메이션 레이어에 키를 가지면 컨스트레인트가 만드는 pairBlend 머지가 베이크
#             구간 "밖"의 포즈까지 바꿔버렸고(스냅샷 우회도 레이어를 인식 못함), 원본
#             JUN_PY_FKIK_Tool_V02_01 에는 없던 현상이었다. -> 레거시처럼 컨스트레인트 없이
#             프레임마다 matchTransform 매칭 후 키를 찍는 방식으로 되돌림. match_transforms 도
#             xform rotateOrder 스왑 대신 cmds.matchTransform 으로 교체(A00145 Match 탭 방식).
#             _snapshot/_restore 는 bake_constraint() 전용으로만 남는다.
#
# 레거시 JUN_MATCH_twoObjects / JUN_matcher_FKIK / JUN_cmd_match_IK_and_FK /
#        JUN_cmd_bake_IK_FK / JUN_cmd_bake_IK_to_FK 를 현대화.

import maya.cmds as cmds

from Framework.core.maya_refresh import suspend_refresh
from Framework.core.maya_undo import undo_chunk
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
    tgt_list[i] 의 월드 트랜스폼을 flw_list[i] 로 복사. (레거시 JUN_MATCH_twoObjects 대체)

    구현: `cmds.matchTransform`(position/rotation) 을 쓴다. A00145_RigConnect Match 탭과
    동일한 방식으로 **컨스트레인트를 전혀 쓰지 않고**, follower 와 target 의 rotateOrder 가
    서로 달라도 월드 포즈가 정확히 일치한다(matchTransform 이 rotateOrder 를 알아서 처리).

    rot_order / rot_axis 인자는 레거시 시그니처 호환을 위해 남겨두며 무시한다 —
    matchTransform 은 월드 트랜스폼을 맞추므로 rotateOrder/rotateAxis 를 건드릴 필요가 없다.
    scale 은 건드리지 않는다.
    """

    count = min(len(tgt_list), len(flw_list))

    for i in range(count):
        cmds.matchTransform(
            flw_list[i], tgt_list[i],
            position=translate, rotation=rotate,
        )


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

        with undo_chunk():
            match_transforms(tgt_list, flw_list, 1, 1, 1, 1)

        return min(len(tgt_list), len(flw_list))

    # --------------------------------------------------
    # 구간 밖 키 보존 (preserveOutsideKeys 보강)
    # --------------------------------------------------
    # 임시 parentConstraint 를 거는 순간 기존 animCurve 가 플러그에서 분리(pairBlend)
    # 되므로, bakeResults 의 preserveOutsideKeys=True 만으로는 베이크 구간 밖의 원본 키가
    # 보존되지 않는다. 컨스트레인트를 걸기 "전에" 바깥 키를 직접 스냅샷해 두었다가 베이크
    # 후 다시 찍어 복원한다.

    @staticmethod
    def _snapshot_outside_keys(nodes, attrs, start, end):
        """[start, end] 밖에 있는 키들을 (값 + 탄젠트) 단위로 스냅샷한다.

        반드시 임시 컨스트레인트를 걸기 전에 호출해야 한다 (그 후에는 animCurve 가
        플러그에서 분리되어 cmds.keyframe 로 조회되지 않는다).
        반환: { (node, attr): {"weighted": bool, "keys": [ {...}, ... ]} }
        """
        snap = {}
        for node in nodes:
            for attr in attrs:
                plug = "%s.%s" % (node, attr)
                if not cmds.objExists(plug):
                    continue
                times = cmds.keyframe(plug, q=True, timeChange=True) or []
                if not times:
                    continue
                values = cmds.keyframe(plug, q=True, valueChange=True) or []
                in_types = cmds.keyTangent(plug, q=True, inTangentType=True) or []
                out_types = cmds.keyTangent(plug, q=True, outTangentType=True) or []
                in_ang = cmds.keyTangent(plug, q=True, inAngle=True) or []
                out_ang = cmds.keyTangent(plug, q=True, outAngle=True) or []
                in_wt = cmds.keyTangent(plug, q=True, inWeight=True) or []
                out_wt = cmds.keyTangent(plug, q=True, outWeight=True) or []
                wt_q = cmds.keyTangent(plug, q=True, weightedTangents=True)
                weighted = bool(wt_q[0]) if wt_q else False

                keys = []
                for i, t in enumerate(times):
                    if start <= t <= end:
                        continue  # 베이크가 덮어쓸 구간은 보존하지 않는다.
                    keys.append({
                        "t": t,
                        "v": values[i] if i < len(values) else 0.0,
                        "it": in_types[i] if i < len(in_types) else "auto",
                        "ot": out_types[i] if i < len(out_types) else "auto",
                        "ia": in_ang[i] if i < len(in_ang) else None,
                        "oa": out_ang[i] if i < len(out_ang) else None,
                        "iw": in_wt[i] if i < len(in_wt) else None,
                        "ow": out_wt[i] if i < len(out_wt) else None,
                    })
                if keys:
                    snap[(node, attr)] = {"weighted": weighted, "keys": keys}
        return snap

    @staticmethod
    def _restore_outside_keys(snap):
        """_snapshot_outside_keys 로 떠 둔 구간 밖 키들을 다시 찍어 복원한다.

        베이크가 만든 [start, end] 커브에 바깥 키를 더해 원래 애니메이션을 되살린다.
        탄젠트 타입은 그대로, fixed 인 경우에만 각도/가중치까지 복원한다.
        키가 많을 수 있으므로 suspend_refresh 로 감싸 프레임마다 리드로우하지 않는다.
        """
        with suspend_refresh():
            for (node, attr), data in snap.items():
                plug = "%s.%s" % (node, attr)
                if not cmds.objExists(plug):
                    continue
                for k in data["keys"]:
                    cmds.setKeyframe(plug, time=k["t"], value=k["v"])
                if data["weighted"]:
                    try:
                        cmds.keyTangent(plug, edit=True, weightedTangents=True)
                    except Exception:
                        pass
                for k in data["keys"]:
                    t = k["t"]
                    try:
                        cmds.keyTangent(
                            plug, time=(t, t), edit=True,
                            inTangentType=k["it"], outTangentType=k["ot"],
                        )
                    except Exception:
                        pass
                    # fixed 탄젠트는 타입만으로 모양이 결정되지 않으므로 각도/가중치까지 복원.
                    if k["it"] == "fixed" and k["ia"] is not None:
                        try:
                            cmds.keyTangent(plug, time=(t, t), edit=True,
                                            inAngle=k["ia"], inWeight=k["iw"])
                        except Exception:
                            pass
                    if k["ot"] == "fixed" and k["oa"] is not None:
                        try:
                            cmds.keyTangent(plug, time=(t, t), edit=True,
                                            outAngle=k["oa"], outWeight=k["ow"])
                        except Exception:
                            pass

    @staticmethod
    def bake(tgt_list, flw_list, start, end):
        """
        [start, end] 구간을 **컨스트레인트 없이** 프레임마다 매칭+키 해서 베이크한다.

        2026-06-29: 임시 parentConstraint + bakeResults 방식을 폐기하고 레거시
        JUN_cmd_bake_IK_FK 의 per-frame 매칭 방식으로 되돌렸다. parentConstraint 를 거는
        순간 Maya 가 pairBlend 를 끼워 기존 animCurve 를 플러그에서 분리하는데, 컨트롤러가
        여러 애니메이션 레이어에 키를 가진 경우 이 분리/머지가 베이크 구간 "밖"의 포즈까지
        바꿔버렸다(_snapshot/_restore 우회도 레이어를 인식하지 못해 실패). 컨스트레인트를
        쓰지 않으면 이 문제가 원천적으로 사라진다.

        각 프레임에서:
          1) currentTime(f) 로 이동,
          2) 각 (tgt, flw) 쌍을 matchTransform(position+rotation)으로 매칭
             (rotateOrder 가 서로 달라도 정확, A00145 Match 탭과 동일),
          3) follower 의 translate/rotate 에만 그 프레임 키를 찍는다.

        setKeyframe 은 **현재 활성 애니메이션 레이어**에 키를 쓰므로, 베이크 구간 밖의 키와
        다른 레이어의 키는 전혀 건드리지 않는다(원본 동작과 동일).

        scale 은 매칭/키 대상이 아니다. 반환값(end - start + 1)은 기존과 동일.
        Maya 2023(Python 3.9) 포함 동작.
        """
        if not tgt_list or not flw_list:
            return 0

        count = min(len(tgt_list), len(flw_list))
        tgt = tgt_list[:count]
        flw = flw_list[:count]

        start_i = int(round(start))
        end_i = int(round(end))
        if start_i > end_i:
            return 0

        cur = cmds.currentTime(q=True)

        with undo_chunk():
            # 프레임마다 리드로우하지 않도록 suspend_refresh 로 감싼다(블록 종료 시 복원).
            with suspend_refresh():
                for frame in range(start_i, end_i + 1):
                    cmds.currentTime(frame, edit=True)

                    for i in range(count):
                        try:
                            cmds.matchTransform(
                                flw[i], tgt[i], position=True, rotation=True
                            )
                        except Exception as e:
                            cmds.warning(
                                "FKIK bake: skip pair %s -> %s @%d (%s)"
                                % (tgt[i], flw[i], frame, e)
                            )

                    # 매칭한 채널(translate/rotate)에만 현재 프레임 키를 찍는다.
                    # 잠긴/연결된 채널은 건너뛰도록 compound 단위로 감싼다.
                    for comp in ("translate", "rotate"):
                        try:
                            cmds.setKeyframe(flw, time=frame, attribute=comp)
                        except Exception as e:
                            cmds.warning(
                                "FKIK bake: setKeyframe %s @%d failed (%s)"
                                % (comp, frame, e)
                            )

            cmds.currentTime(cur, edit=True)

        return end_i - start_i + 1

    @staticmethod
    def bake_constraint(tgt_list, flw_list):
        """
        parentConstraint 로 묶어 bakeSimulation. (레거시 JUN_cmd_bake_IK_to_FK 복원)

        개선: range(0, 8) 하드코딩 -> 쌍 개수 기반, 베이크 후 임시 컨스트레인트 삭제.
        """
        if not tgt_list or not flw_list:
            return 0

        count = min(len(tgt_list), len(flw_list))
        flw = flw_list[:count]

        sim_attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]

        time_start = cmds.playbackOptions(minTime=True, q=True)
        time_end = cmds.playbackOptions(maxTime=True, q=True)

        # 재생 범위 밖(타임라인 바깥)의 기존 키도 컨스트레인트로 분리되어 사라지므로
        # bake() 와 동일하게 스냅샷 후 복원한다. preserveOutsideKeys 보강.
        snap = FKIKMatcher._snapshot_outside_keys(
            flw, sim_attrs, time_start, time_end
        )

        cmds.undoInfo(openChunk=True)
        constraints = []
        try:
            for i in range(count):
                con = cmds.parentConstraint(
                    tgt_list[i], flw_list[i], maintainOffset=True
                )
                constraints.extend(con)

            cmds.bakeSimulation(
                flw,
                sb=1,
                t=(time_start, time_end),
                at=sim_attrs,
                hi="none",
                preserveOutsideKeys=True,
            )
        finally:
            # 베이크 후 임시 컨스트레인트 정리 (레거시는 남겨뒀음 -> 개선).
            # finally 로 옮겨 bakeSimulation 이 실패해도 컨스트레인트가 남지 않게 한다.
            for con in constraints:
                if cmds.objExists(con):
                    cmds.delete(con)
            if constraints and snap:
                try:
                    FKIKMatcher._restore_outside_keys(snap)
                except Exception as e:
                    cmds.warning(
                        "FKIK bake_constraint: outside-key restore failed (%s)" % e
                    )
            cmds.undoInfo(closeChunk=True)

        return count
