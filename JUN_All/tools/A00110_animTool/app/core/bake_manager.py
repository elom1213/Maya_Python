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

    # native smart bake 의 기본 허용오차(도). 값이 클수록 키를 더 많이 제거(거칠게)한다.
    DEFAULT_SMART_TOLERANCE = 0.5

    @staticmethod
    def bake(objects, start, end, channels=None, simulation=True,
             disable_implicit=False, smart=False,
             smart_tolerance=DEFAULT_SMART_TOLERANCE):
        """
        objects 의 [start, end] 구간을 native bakeResults 로 굽는다.

        objects          : 베이크할 노드 리스트(리스트 위젯에 리스트업된 항목).
        start, end       : 정수 프레임 구간(포함).
        channels         : 베이크 attr 리스트(기본 translate/rotate). scale 포함 시 호출부 지정.
        simulation       : True = 프레임 순차 평가(컨스트레인트/익스프레션 의존 리그 안전).
        disable_implicit : bakeResults 의 disableImplicitControl 로 그대로 전달.
                           False(기본) = 컨스트레인트 유지(pairBlend 로 키 공존),
                           True        = 구동 컨스트레인트 정리(bake down).
        smart            : True = native smart bake. 매 프레임 dense 대신 허용오차 이내의
                           중간 키를 C++ 내부에서 제거해 키 수를 줄인다(bakeResults -smart).
                           Maya 2020+ 에서 동작(2023 확인). 미지원 버전은 dense 로 폴백.
        smart_tolerance  : smart 허용오차(도). 클수록 더 적은 키(거친 결과).
        반환             : (baked_count, msg)
        """
        if not objects:
            return (0, "[Warning] No objects to bake. Add controllers to the list first.")

        if start > end:
            return (0, "[Warning] Start ({0}) is greater than End ({1}).".format(start, end))

        attrs = list(channels) if channels else list(BakeManager.DEFAULT_CHANNELS)

        # smart 모드에서는 키를 솎아내야 하므로 sparseAnimCurveBake 를 켠다.
        bake_kwargs = dict(
            simulation=simulation,
            time=(start, end),
            sampleBy=1,
            attribute=attrs,
            disableImplicitControl=disable_implicit,
            preserveOutsideKeys=True,
            sparseAnimCurveBake=bool(smart),
        )
        if smart:
            # -smart 는 [on, tolerance] 형태. 구버전(<2020)은 플래그 미인식 -> 폴백 처리.
            bake_kwargs["smart"] = (1, float(smart_tolerance))

        cur = cmds.currentTime(q=True)

        cmds.undoInfo(openChunk=True)
        cmds.refresh(suspend=True)
        try:
            try:
                cmds.bakeResults(objects, **bake_kwargs)
                used_smart = bool(smart)
            except TypeError:
                # 이 Maya 버전에 smart 플래그가 없는 경우: dense 로 다시 굽는다.
                bake_kwargs.pop("smart", None)
                bake_kwargs["sparseAnimCurveBake"] = False
                cmds.bakeResults(objects, **bake_kwargs)
                used_smart = False
        finally:
            # 예외가 나도 뷰포트 억제 해제 / 프레임 복원 / undo 청크 닫기를 반드시 수행
            cmds.refresh(suspend=False)
            cmds.currentTime(cur, edit=True)
            cmds.undoInfo(closeChunk=True)

        n = len(objects)
        frames = end - start + 1
        kept = "kept" if not disable_implicit else "baked down"
        if used_smart:
            mode = "smart bake (tol {0})".format(smart_tolerance)
        elif smart:
            mode = "dense (smart unsupported, fell back)"
        else:
            mode = "dense"
        return (n, "{0} object(s) baked over [{1}-{2}] ({3} frames, {4}, constraints {5}).".format(
            n, start, end, frames, mode, kept))
