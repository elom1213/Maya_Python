# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00110_animTool - Offset & Hold (포즈 유지 + 구간 보간 재배치) 핵심 로직 (maya.cmds, UI 비의존)

import maya.cmds as cmds

from .keyframe_manager import KeyframeManager


class OffsetHoldManager:
    """
    리스트업한 컨트롤러/오브젝트의 키프레임을 'hold(포즈 유지) + offset(보간)' 구조로 재배치한다.

    각 원본 '포즈 프레임'(= 오브젝트의 대상 커브들에서 키가 있는 프레임의 합집합)의 포즈를
    hold 프레임 길이만큼 평평하게 유지(plateau)하고, 인접 포즈 사이를 offset 프레임만큼
    보간(ramp)한다.

    프레임 배치 (P = hold + offset, start = 시작 앵커, i = 0..n-1):
        plateau_start_i = start + i*P
        plateau_end_i   = start + i*P + hold
        ramp_i          = [plateau_end_i, plateau_start_{i+1}]   (길이 = offset)

    예) offset=30, hold=10, 포즈 3개, start=0
        0→10 유지 / 10→40 보간 / 40→50 유지 / 50→80 보간 / 80→90 유지

    탄젠트: plateau 양 끝 안쪽(start out / end in)은 flat, 보간 구간 바깥(end out /
    다음 start in)은 spline 으로 두어 부드러운 가속·감속(spline ease).

    채널 스코프는 KeyframeManager 와 동일 — 채널박스에서 어트리뷰트를 선택해 두면 그 채널만,
    선택이 없으면 오브젝트의 모든 (시간 기반) 애니메이션 커브가 대상.

    값은 어트리뷰트 플러그를 시점별로 평가(getAttr time=)해 샘플링하므로, 포즈 프레임에 키가
    없던 커브도 그 시점의 보간값으로 포즈가 잡힌다. 모든 대상 채널이 동일한 plateau 구조로
    동기화된다.
    """

    # 정수/실수 프레임 비교용 미세 오차
    EPS = 1e-4

    @staticmethod
    def _selection(objects):
        return objects if objects else (cmds.ls(sl=True) or [])

    @staticmethod
    def _target_plugs(obj, attrs):
        """
        오브젝트의 대상 애니메이션 플러그(키가 1개 이상인 것)를 반환.
        attrs 가 있으면 그 채널만, 없으면 listAnimatable 전체에서 키 있는 것만.
        """
        if attrs:
            candidates = ["{0}.{1}".format(obj, at) for at in attrs]
        else:
            candidates = cmds.listAnimatable(obj) or []

        plugs = []
        for plug in candidates:
            if not cmds.objExists(plug):
                continue
            if (cmds.keyframe(plug, q=True, keyframeCount=True) or 0) > 0:
                plugs.append(plug)
        return plugs

    @staticmethod
    def apply_offset_hold(objects, offset, hold, start=None):
        """
        리스트(또는 선택)의 각 오브젝트 키를 hold/offset 구조로 재배치.

        offset : 포즈 사이 보간 구간 길이(프레임, >=0)
        hold   : 각 포즈 유지 구간 길이(프레임, >=0)
        start  : 첫 plateau 시작 프레임. None 이면 오브젝트별 첫 키 프레임을 앵커로 사용.

        반환: (처리한 오브젝트 수, 메시지)
        """
        sel = OffsetHoldManager._selection(objects)
        if not sel:
            return (0, "No objects selected.")

        period = hold + offset
        if period <= 0:
            return (0, "Hold + Offset must be greater than 0.")

        attrs = KeyframeManager.get_target_channels()

        done = 0
        skipped = 0

        cmds.undoInfo(openChunk=True)
        try:
            for obj in sel:

                plugs = OffsetHoldManager._target_plugs(obj, attrs)
                if not plugs:
                    skipped += 1
                    continue

                # 1) 포즈 프레임 = 대상 플러그들의 키 시점 합집합 (수정 전에 수집)
                frame_set = set()
                for plug in plugs:
                    times = cmds.keyframe(plug, q=True, timeChange=True) or []
                    frame_set.update(times)

                pose_frames = sorted(frame_set)
                if not pose_frames:
                    skipped += 1
                    continue

                anchor = pose_frames[0] if start is None else start
                last_i = len(pose_frames) - 1

                # 2) 플러그별: 원본 시점값 샘플링 -> 기존 키 제거 -> plateau/ramp 재생성
                for plug in plugs:

                    # 포즈 프레임마다 현재 커브를 평가(보간 포함)해 값 확보 (수정 전)
                    values = []
                    for f in pose_frames:
                        try:
                            values.append(cmds.getAttr(plug, time=f))
                        except Exception:
                            v = cmds.keyframe(plug, q=True, time=(f, f), valueChange=True) or []
                            values.append(v[0] if v else 0.0)

                    # 기존 키 전부 제거 후 재배치
                    cmds.cutKey(plug, clear=True)

                    for i, val in enumerate(values):
                        ps = anchor + i * period
                        pe = ps + hold

                        cmds.setKeyframe(plug, time=ps, value=val)
                        if hold > 0:
                            cmds.setKeyframe(plug, time=pe, value=val)

                        # plateau 시작: in 은 보간 착지(spline), out 은 유지 시작(flat)
                        cmds.keyTangent(
                            plug, edit=True, time=(ps, ps),
                            inTangentType="spline",
                            outTangentType=("flat" if hold > 0 else "spline"),
                        )
                        # plateau 끝: in 은 유지(flat), out 은 보간 출발(spline)
                        if hold > 0:
                            cmds.keyTangent(
                                plug, edit=True, time=(pe, pe),
                                inTangentType="flat",
                                outTangentType=("spline" if i < last_i else "flat"),
                            )

                done += 1
        finally:
            cmds.undoInfo(closeChunk=True)

        if done == 0:
            return (0, "No animated objects to process. ({0} skipped: no keys)".format(skipped))

        scope = ("channels: " + ", ".join(attrs)) if attrs else "all curves"
        msg = "{0} object(s) re-timed (hold {1}f / offset {2}f)  ({3})".format(
            done, hold, offset, scope)
        if skipped:
            msg += "  ({0} skipped: no keys)".format(skipped)
        return (done, msg)
