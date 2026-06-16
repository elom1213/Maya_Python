# -*- coding: utf-8 -*-
"""
matching - FK/IK 매칭 & 베이크 코어 로직.

레거시 JUN_MATCH_twoObjects / JUN_matcher_FKIK_Gen / JUN_cmd_bake_IK_FK_Gen 를 이식했다.
UI(textScrollList) 의존을 제거하고 plain list[str] / (pose, ctl) 쌍을 직접 받는다.

레거시 대비 수정:
- 베이크 프레임 루프가 마지막 프레임을 누락하던 range(start, end) → range(start, end+1).
- 단일/구간 분기를 is_bake 정수 플래그 대신 frame_range=None 여부로 명시.
- 매칭 방향(FK/IK)을 bake_ik 정수 대신 use_ik bool 로 명시.
"""

from contextlib import nullcontext

import maya.cmds as cmds
import maya.mel as mel


# ----------------------------------------------------------------------
# 매칭 원자 연산
# ----------------------------------------------------------------------

def match_two_objects(tgt_list, flw_list,
                      rot_order=True, rot_axis=True, trs=True, rot=True):
    """flw_list[i] 를 tgt_list[i] 에 맞춘다(월드 T/R 복사). (구 JUN_MATCH_twoObjects)

    tgt 의 rotateOrder 를 잠시 적용해 회전을 정확히 세팅한 뒤, flw 원래 rotateOrder 로 복원한다.
    """
    for i in range(len(tgt_list)):
        tgt_rot_order = cmds.xform(tgt_list[i], q=True, rotateOrder=True)
        tgt_rot_axis = cmds.xform(tgt_list[i], q=True, rotateAxis=True)
        tgt_trs = cmds.xform(tgt_list[i], q=True, worldSpace=True, translation=True)
        tgt_rot = cmds.xform(tgt_list[i], q=True, worldSpace=True, rotation=True)

        flw_rot_order_ori = cmds.xform(flw_list[i], q=True, rotateOrder=True)

        if rot_order:
            cmds.xform(flw_list[i], rotateOrder=tgt_rot_order)
        if rot_axis:
            cmds.xform(flw_list[i], rotateAxis=tgt_rot_axis)
        if trs:
            cmds.xform(flw_list[i], worldSpace=True, translation=tgt_trs)
        if rot:
            cmds.xform(flw_list[i], worldSpace=True, rotation=tgt_rot)

        cmds.xform(flw_list[i], rotateOrder=flw_rot_order_ori)


# ----------------------------------------------------------------------
# 데이터 컨테이너
# ----------------------------------------------------------------------

class MatchData:
    """매칭 대상(tgt=pose objects) / 추종(flw=controls) 리스트. (구 JUN_matcher_FKIK_Gen)"""

    def __init__(self):
        self.tgt = []
        self.flw = []

    def clear(self):
        self.tgt = []
        self.flw = []

    def extend(self, tgt, flw):
        self.tgt.extend(tgt)
        self.flw.extend(flw)


# ----------------------------------------------------------------------
# 뷰포트 정지 컨텍스트 (베이크 가속)
# ----------------------------------------------------------------------

class OGSFreeze:
    """베이크 동안 OGS(뷰포트)를 일시정지해 속도를 높인다. (구 OGSFreeze)"""

    def __enter__(self):
        self.was_paused = bool(mel.eval('ogs -query -pause;'))
        if not self.was_paused:
            mel.eval('ogs -pause;')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 원래 정지 상태가 아니었으면 재개(토글).
        mel.eval('ogs -pause;')


# ----------------------------------------------------------------------
# 매칭 / 베이크
# ----------------------------------------------------------------------

def run_match_bake(fk_pairs, ik_pairs, enabled, use_ik, frame_range=None):
    """선택된 limb 의 컨트롤을 pose object 에 매칭(+키프레임)한다. (구 JUN_cmd_bake_IK_FK_Gen)

    Args:
        fk_pairs / ik_pairs: limb 4개 [arm_l, arm_r, leg_l, leg_r] 각각 (pose_objs:list, ctls:list) 튜플.
                             매칭은 ctls(flw) 를 pose_objs(tgt) 에 맞춘다.
        enabled: [bool, bool, bool, bool] — 처리할 limb.
        use_ik: True 면 ik_pairs, False 면 fk_pairs 사용.
        frame_range: None 이면 현재 프레임 1회 매칭, (start, end) 면 구간 베이크(end 포함).

    Returns:
        매칭된 follower 개수.
    """
    pairs = ik_pairs if use_ik else fk_pairs

    data = MatchData()
    for i, on in enumerate(enabled):
        if not on or i >= len(pairs):
            continue
        pose_objs, ctls = pairs[i]
        data.extend(pose_objs, ctls)

    if not data.flw:
        return 0

    if frame_range is None:
        current = int(cmds.currentTime(query=True))
        frames = [current]
        ctx = nullcontext()
    else:
        start, end = frame_range
        frames = range(int(start), int(end) + 1)   # end 포함 (레거시 누락 버그 수정)
        ctx = OGSFreeze()

    with ctx:
        for frame in frames:
            cmds.currentTime(frame, edit=True)
            # 2회 반복: 부모/자식 종속 컨트롤이 한 번에 안 맞는 경우 보정(레거시 동작 유지).
            for _ in range(2):
                match_two_objects(data.tgt, data.flw)
            cmds.setKeyframe(data.flw, t=frame)

    return len(data.flw)
