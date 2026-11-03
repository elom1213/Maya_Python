# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-03
# A00110_animTool_V02 - Bake > Locator : 리스트의 오브젝트마다 로케이터를 만들어 그 월드 움직임을 구간 베이크 (maya.cmds, UI 비의존)
#
# 사용자가 마야에서 쓰던 `_SmartLayer` 패키지의 `LOC + Anim` 버튼을 새로 만든 것 (v02.36, 2026-11-03).
# 원래 버튼은 "가끔 답답하거나 오류" 가 있어서 다시 만든다. 달라진 점:
#   - 대상 = 씬 선택이 아니라 리스트(TSL)의 항목.  - 구간 = Start / End 입력(Get Current · Get Sel Range).
#   - 베이크 중 진행 팝업(게이지).
#
# 흐름 (오브젝트 N 개, 한 번의 undo):
#   1. 로케이터 `<이름>_LOC` 를 월드에 만들고 회전 순서를 원본과 맞춘다(네임스페이스 · 경로는 뺀 잎 이름).
#   2. 임시 parentConstraint(원본 -> 로케이터, 오프셋 없음) (+ Scale 이면 scaleConstraint).
#   3. **bakeResults 한 번**(simulation, 전 로케이터 · 전 구간) - C++ 베이커라 빠르다.
#      진행률은 `MDGMessage.addTimeChangeCallback` 으로 받는다: simulation 베이크는 프레임마다 시간을 옮기며
#      콜백을 부른다(mayapy 2024 실측: 1~200 -> 201 회). 구간을 쪼개 여러 번 부르면 첫 호출이 컨스트레인트를
#      끊어(disableImplicitControl) 다음 구간이 안 따라오므로 쪼개지 않는다.
#   4. 임시 컨스트레인트 삭제 -> (옵션) 회전 커브 오일러 필터 -> 현재 시간 복원 -> 로케이터 선택.
# 중간에 실패하면 이번에 만든 로케이터 · 컨스트레인트를 지우고 끝낸다(반쯤 만든 결과를 남기지 않는다).

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_refresh import suspend_refresh
from Framework.core.maya_undo import undo_chunk


class LocatorBakeManager:
    """오브젝트 -> 로케이터 월드 베이크. 정적 메서드 + (결과, msg) 반환 (다른 manager 와 같은 모양)."""

    SUFFIX = "_LOC"

    # progress(done, total, message) 의 단계 이름 (UI 의 진행 팝업 phases 와 맞춘다)
    PHASE_CREATE = "Creating locators"
    PHASE_BAKE = "Baking"
    PHASE_CLEANUP = "Cleaning up"

    # ------------------------------------------------------------------ 대상

    @staticmethod
    def resolve_targets(objects):
        """리스트 항목 -> 베이크할 트랜스폼(긴 경로, 중복 제거, 순서 유지) + 건너뛴 항목 [(항목, 이유)].

        셰이프가 담겨 있으면 그 부모 트랜스폼을 쓴다. 없는 노드 · 트랜스폼이 아닌 노드는 건너뛴다."""
        targets, skipped, seen = [], [], set()
        for obj in objects or []:
            if not obj or not cmds.objExists(obj):
                skipped.append((obj, "not found"))
                continue
            node = obj
            if "transform" not in (cmds.nodeType(node, inherited=True) or []):
                parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
                if parents and "shape" in (cmds.nodeType(node, inherited=True) or []):
                    node = parents[0]
                else:
                    skipped.append((obj, "not a transform"))
                    continue
            long_name = (cmds.ls(node, long=True) or [node])[0]
            if long_name in seen:
                continue
            seen.add(long_name)
            targets.append(long_name)
        return targets, skipped

    @staticmethod
    def locator_name(node):
        """`|grp|ns:arm_ctl` -> `arm_ctl_LOC` (같은 이름이 있으면 마야가 끝 숫자를 붙인다)."""
        leaf = node.split("|")[-1].split(":")[-1]
        return leaf + LocatorBakeManager.SUFFIX

    # ------------------------------------------------------------------ 베이크

    @staticmethod
    def bake(objects, start, end, translate=True, rotate=True, scale=False,
             euler_filter=True, select_result=True, progress=None):
        """objects 마다 로케이터를 만들어 [start, end] 를 월드 베이크한다.

        progress : progress(done, total, message=None) - 단계마다 0 -> total. None 이면 조용히.
                   단계 순서는 PHASE_CREATE -> PHASE_BAKE -> PHASE_CLEANUP 이고 단계가 바뀔 때
                   `progress.phase(name)` 이 있으면 먼저 부른다(UI 가 진행 팝업 단계를 넘긴다).
        반환     : (만든 로케이터 이름 목록, msg)
        """
        if start is None or end is None:
            return [], "[Warning] Enter Start / End."
        start, end = int(start), int(end)
        if start > end:
            return [], "[Warning] Start ({0}) is greater than End ({1}).".format(start, end)
        if not (translate or rotate or scale):
            return [], "[Warning] Enable at least one channel group."

        targets, skipped = LocatorBakeManager.resolve_targets(objects)
        if not targets:
            return [], "[Warning] Nothing to bake - add objects (transforms) to the list first."

        attrs = []
        if translate:
            attrs += ["tx", "ty", "tz"]
        if rotate:
            attrs += ["rx", "ry", "rz"]
        if scale:
            attrs += ["sx", "sy", "sz"]

        def _phase(name):
            hook = getattr(progress, "phase", None)
            if hook:
                hook(name)

        def _step(done, total, message=None):
            if progress:
                progress(done, total, message)

        current = cmds.currentTime(q=True)
        locators, constraints = [], []
        n = len(targets)

        with undo_chunk():
            try:
                with suspend_refresh():
                    # 1~2. 로케이터 + 임시 컨스트레인트
                    _phase(LocatorBakeManager.PHASE_CREATE)
                    for i, src in enumerate(targets):
                        loc = cmds.spaceLocator(name=LocatorBakeManager.locator_name(src))[0]
                        locators.append(loc)
                        try:
                            cmds.setAttr(loc + ".rotateOrder", cmds.getAttr(src + ".rotateOrder"))
                        except (RuntimeError, ValueError):
                            pass
                        if translate or rotate:
                            skip_t = [] if translate else ["x", "y", "z"]
                            skip_r = [] if rotate else ["x", "y", "z"]
                            constraints += cmds.parentConstraint(
                                src, loc, maintainOffset=False, skipTranslate=skip_t, skipRotate=skip_r)
                        if scale:
                            constraints += cmds.scaleConstraint(src, loc, maintainOffset=False)
                        _step(i + 1, n, loc)

                    # 3. 베이크 한 번 - 진행률은 시간 변경 콜백으로
                    _phase(LocatorBakeManager.PHASE_BAKE)
                    frames = end - start + 1

                    def _on_time(mtime, *_args):
                        try:
                            done = int(round(mtime.value)) - start + 1
                            if 0 < done <= frames:
                                _step(done, frames, "Frame {0} / {1}".format(int(round(mtime.value)), end))
                        except Exception:  # noqa: BLE001 - 콜백 예외가 베이크를 깨지 않게
                            pass

                    callback_id = om.MDGMessage.addTimeChangeCallback(_on_time) if progress else None
                    try:
                        cmds.bakeResults(
                            locators, simulation=True, time=(start, end), sampleBy=1,
                            attribute=attrs, disableImplicitControl=True,
                            preserveOutsideKeys=True, sparseAnimCurveBake=False)
                    finally:
                        if callback_id is not None:
                            om.MMessage.removeCallback(callback_id)
                    _step(frames, frames)

                    # 4. 정리
                    _phase(LocatorBakeManager.PHASE_CLEANUP)
                    alive = [c for c in constraints if cmds.objExists(c)]
                    if alive:
                        cmds.delete(alive)
                    constraints = []
                    if euler_filter and rotate:
                        curves = cmds.listConnections(
                            [loc + "." + a for loc in locators for a in ("rx", "ry", "rz")],
                            source=True, destination=False, type="animCurve") or []
                        if curves:
                            cmds.filterCurve(list(set(curves)), filter="euler")
                    _step(1, 1)
            except Exception as exc:  # noqa: BLE001 - 반쯤 만든 결과를 남기지 않는다
                leftovers = [x for x in constraints + locators if cmds.objExists(x)]
                if leftovers:
                    cmds.delete(leftovers)
                cmds.currentTime(current, edit=True)
                return [], "[Error] Locator bake failed : {0}".format(str(exc).strip())

            cmds.currentTime(current, edit=True)
            if select_result:
                cmds.select(locators, replace=True)

        msg = "LOC + Anim : {0} locator(s), frames {1} - {2} ({3}).".format(
            len(locators), start, end, " ".join(
                g for g, on in (("T", translate), ("R", rotate), ("S", scale)) if on))
        if skipped:
            msg += "  Skipped {0}: {1}".format(
                len(skipped), ", ".join("{0} ({1})".format(o, why) for o, why in skipped))
        return locators, msg
