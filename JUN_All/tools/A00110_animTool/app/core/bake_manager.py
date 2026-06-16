# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-16
# A00110_animTool - 리스트업한 컨트롤러를 구간 dense 키로 굽는 핵심 로직 (maya.cmds, UI 비의존)
#
# A00120_FKIK 의 native bakeResults 베이크(Python 프레임 루프 대체)를 범용 bake 로 이식.
#   - FKIK 는 타깃->팔로워 매칭이라 임시 parentConstraint 가 필요했지만, 여기서는
#     리스트의 노드 자체를 바로 굽기 때문에 컨스트레인트를 만들지 않는다.
#   - currentTime/xform 프레임 루프 없이 단일 C++ 베이커로 처리 -> 6000+프레임 × 50~100
#     컨트롤러에서 수십 배 빠르다. Maya 2023(Python 3.9) 동작 확인.

import maya.cmds as cmds


class BakeManager:
    """
    리스트업된 노드의 [start, end] 구간을 native bakeResults 로 굽는다.

    다른 manager 와 동일 스타일: 정적 메서드 + undoInfo 청크 + (count, msg) 반환.
    """

    # match/FKIK 와 동일: scale 제외가 기본. 필요 시 호출부에서 channels 로 확장.
    DEFAULT_CHANNELS = ["tx", "ty", "tz", "rx", "ry", "rz"]

    @staticmethod
    def bake(objects, start, end, channels=None, simulation=True,
             disable_implicit=False):
        """
        objects 의 [start, end] 구간을 native bakeResults 로 굽는다.

        objects          : 베이크할 노드 리스트(리스트 위젯에 리스트업된 항목).
        start, end       : 정수 프레임 구간(포함).
        channels         : 베이크 attr 리스트(기본 translate/rotate). scale 포함 시 호출부 지정.
        simulation       : True = 프레임 순차 평가(컨스트레인트/익스프레션 의존 리그 안전).
        disable_implicit : bakeResults 의 disableImplicitControl 로 그대로 전달.
                           False(기본) = 컨스트레인트 유지(pairBlend 로 키 공존),
                           True        = 구동 컨스트레인트 정리(bake down).
        반환             : (baked_count, msg)
        """
        if not objects:
            return (0, "[Warning] No objects to bake. Add controllers to the list first.")

        if start > end:
            return (0, "[Warning] Start ({0}) is greater than End ({1}).".format(start, end))

        attrs = list(channels) if channels else list(BakeManager.DEFAULT_CHANNELS)

        cur = cmds.currentTime(q=True)

        cmds.undoInfo(openChunk=True)
        cmds.refresh(suspend=True)
        try:
            cmds.bakeResults(
                objects,
                simulation=simulation,
                time=(start, end),
                sampleBy=1,
                attribute=attrs,
                disableImplicitControl=disable_implicit,
                preserveOutsideKeys=True,
                sparseAnimCurveBake=False,
            )
        finally:
            # 예외가 나도 뷰포트 억제 해제 / 프레임 복원 / undo 청크 닫기를 반드시 수행
            cmds.refresh(suspend=False)
            cmds.currentTime(cur, edit=True)
            cmds.undoInfo(closeChunk=True)

        n = len(objects)
        frames = end - start + 1
        kept = "kept" if not disable_implicit else "baked down"
        return (n, "{0} object(s) baked over [{1}-{2}] ({3} frames, constraints {4}).".format(
            n, start, end, frames, kept))
