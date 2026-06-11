# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-11
# A00110_animTool - 키프레임 이동/삭제/hold 핵심 로직 (maya.cmds, UI 비의존)

import maya.cmds as cmds


class KeyframeManager:
    """
    선택한 오브젝트들의 키프레임을 지정 구간에 대해 일괄 이동/삭제한다.

    성능: 오브젝트별 파이썬 루프를 만들지 않고, 선택 리스트 전체 +
    attribute 플래그를 cmds.keyframe / cmds.cutKey 에 단 한 번 넘겨
    Maya 네이티브로 일괄 처리한다. (100+ 오브젝트 대응)
    """

    # --------------------------------------------------
    # 채널 스코프
    # --------------------------------------------------

    @staticmethod
    def get_target_channels():
        """
        채널박스에서 선택된 어트리뷰트를 우선 반환.
        선택이 없으면 빈 리스트 -> 호출부에서 attribute 플래그를 생략
        (= 오브젝트의 모든 애니메이션 커브 대상).
        """
        attrs = cmds.channelBox(
            "mainChannelBox",
            q=True,
            selectedMainAttributes=True
        ) or []

        return attrs

    @staticmethod
    def _selection(objects):
        return objects if objects else (cmds.ls(sl=True) or [])

    # --------------------------------------------------
    # 이동
    # --------------------------------------------------

    @staticmethod
    def move_keys(start, end, offset, objects=None):
        """
        [start, end] 구간의 키를 offset 프레임만큼 상대 이동.
        offset < 0 : 앞으로(earlier),  offset > 0 : 뒤로(later).
        반환: (처리한 오브젝트 수, 메시지)
        """
        sel = KeyframeManager._selection(objects)

        if not sel:
            return (0, "No objects selected.")

        if offset == 0:
            return (0, "Offset is 0.")

        attrs = KeyframeManager.get_target_channels()
        kw = {"attribute": attrs} if attrs else {}

        cmds.undoInfo(openChunk=True)
        try:
            cmds.keyframe(
                sel,
                edit=True,
                time=(start, end),
                relative=True,
                timeChange=offset,
                **kw
            )
        finally:
            cmds.undoInfo(closeChunk=True)

        scope = ("channels: " + ", ".join(attrs)) if attrs else "all curves"
        return (
            len(sel),
            f"{len(sel)} objects : keys in [{start}-{end}f] moved {offset:+d}f  ({scope})"
        )

    # --------------------------------------------------
    # 삭제
    # --------------------------------------------------

    @staticmethod
    def delete_keys(start, end, objects=None):
        """
        [start, end] 구간의 키를 삭제 (클립보드 미사용).
        반환: (처리한 오브젝트 수, 메시지)
        """
        sel = KeyframeManager._selection(objects)

        if not sel:
            return (0, "No objects selected.")

        attrs = KeyframeManager.get_target_channels()
        kw = {"attribute": attrs} if attrs else {}

        cmds.undoInfo(openChunk=True)
        try:
            cmds.cutKey(
                sel,
                time=(start, end),
                clear=True,
                **kw
            )
        finally:
            cmds.undoInfo(closeChunk=True)

        scope = ("channels: " + ", ".join(attrs)) if attrs else "all curves"
        return (
            len(sel),
            f"{len(sel)} objects : keys in [{start}-{end}f] deleted  ({scope})"
        )

    # --------------------------------------------------
    # Hold (그래프 에디터 선택 구간 유지)
    # --------------------------------------------------

    @staticmethod
    def hold_selected_keys():
        """
        그래프 에디터에서 선택된 키들을 커브별로 독립 처리한다.

        커브마다:
          start(선택 최소 프레임) 값을 읽고,
          (start, end] 구간의 키를 삭제한 뒤,
          end 에 start 값을 다시 삽입한다.
          start out / end in 탄젠트를 flat 으로 만들어 구간을 평평하게 유지.

        오브젝트 선택이 아니라 '선택된 키' 기준이므로 어떤 어트리뷰트든 동일하게 동작.
        반환: (처리한 커브 수, 메시지)
        """
        # 미세 오차로 start 키는 보존하고 end 키까지 삭제 (정수/실수 프레임 모두 대응)
        EPS = 1e-4

        # 선택된 키를 가진 애니메이션 커브 노드 목록 (중복 제거됨)
        curves = cmds.keyframe(q=True, name=True, selected=True) or []

        if not curves:
            return (0, "No keys selected in Graph Editor.")

        done = 0
        skipped = 0

        cmds.undoInfo(openChunk=True)
        try:
            for crv in curves:

                times = cmds.keyframe(
                    crv, q=True, selected=True, timeChange=True
                ) or []

                if len(times) < 2:
                    skipped += 1
                    continue

                start = min(times)
                end = max(times)

                vals = cmds.keyframe(
                    crv, q=True, time=(start, start), valueChange=True
                ) or []

                if not vals:
                    skipped += 1
                    continue

                start_val = vals[0]

                # (start, end] 구간 삭제 -> end 에 start 값 재삽입
                cmds.cutKey(crv, time=(start + EPS, end), clear=True)
                cmds.setKeyframe(crv, time=end, value=start_val)

                # 구간을 평평하게: start out / end in 탄젠트 flat
                cmds.keyTangent(crv, edit=True, time=(start, start), outTangentType="flat")
                cmds.keyTangent(crv, edit=True, time=(end, end), inTangentType="flat")

                done += 1
        finally:
            cmds.undoInfo(closeChunk=True)

        msg = f"{done} curve(s) held flat at start value."
        if skipped:
            msg += f"  ({skipped} skipped: <2 keys / no value)"

        return (done, msg)
