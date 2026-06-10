# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00110_animTool - 키프레임 이동/삭제 핵심 로직 (maya.cmds, UI 비의존)

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
