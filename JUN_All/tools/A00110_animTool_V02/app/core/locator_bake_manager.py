# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-12
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
#   5. (옵션, v02.37) 거꾸로 **로케이터 -> 원본 오브젝트** 컨스트레인트(parent 기본 · point · orient · scale).
#      로케이터를 움직여 원본을 조종하는 용도. 오프셋 없음(로케이터 월드 = 원본 월드라 구간 안에서 원본이 그대로).
#      잠긴 채널 · 키 말고 다른 것이 구동하는 채널은 그 축만 건너뛴다. 굽지 않은 채널 묶음의 컨스트레인트는 걸지 않는다.
#   6. (v02.61) **구간 블렌드** `Blend only in Frame Range`(기본 켬) - 컨스트레인트가 끼운 pairBlend 의 웨이트 attr
#      (`blendParent1` · `blendPoint1` · `blendOrient1`) 를 Start ~ End 만 1, 밖은 0(step 키) -> 구간 안은 로케이터, 밖은 원래 움직임.
#      애니메이션 레이어도 만들지 않는다. Bake 탭으로 구우면(BakeManager 가 이 오브젝트를 경계 처리 경로로) 컨스트레인트를 지워도 남는다.
#      ★ 컨스트레인트 **타깃 웨이트**를 0 으로 두면 원래 움직임이 아니라 rest 자세로 간다(mayapy 실측) - 그래서 pairBlend 웨이트.
#      ★ **애니메이션 레이어 채널**(animBlendNode 구동)에도 그냥 걸린다 - 마야가 레이어 결과 뒤에 pairBlend 를 끼운다(실측).
#        v02.57 까지는 이 채널을 "키가 아닌 구동" 으로 보고 전 축을 건너뛰어 컨스트레인트가 0 개였다(사용자 제보).
#      ★ 키가 하나도 없는 채널 묶음엔 pairBlend 가 안 생긴다 -> 구간 블렌드면 먼저 지금 값으로 키를 하나 넣는다.
#      ★ scale 은 pairBlend 가 없어 구간 블렌드를 못 한다 -> 전 프레임 + 경고.
#      (v02.58 의 LOC_Constraint override 레이어 방식 · v02.59 Bake to Keys 는 이 방식으로 바꾸며 뺐다.)
# 중간에 실패하면 이번에 만든 로케이터 · 컨스트레인트를 지우고 끝낸다(반쯤 만든 결과를 남기지 않는다).

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from Framework.core.maya_refresh import suspend_refresh
from Framework.core.maya_undo import undo_chunk


class LocatorBakeManager:
    """오브젝트 -> 로케이터 월드 베이크. 정적 메서드 + (결과, msg) 반환 (다른 manager 와 같은 모양)."""

    SUFFIX = "_LOC"

    # progress(done, total, message) 의 단계 이름 (UI 의 진행 팝업 phases 와 맞춘다)
    PHASE_CREATE = "Creating locators"
    PHASE_BAKE = "Baking"
    PHASE_CLEANUP = "Cleaning up"
    PHASE_CONSTRAIN = "Constraining"

    # 로케이터 -> 오브젝트 컨스트레인트 종류 (UI 체크박스와 같은 키). parent 는 point / orient 와 함께 쓸 수 없다.
    CONSTRAINT_TYPES = ("parent", "point", "orient", "scale")

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

    # ------------------------------------------------------------------ 컨스트레인트 (로케이터 -> 오브젝트)

    @staticmethod
    def _is_key_source(node):
        """키에서 오는 연결인가 - animCurve, 또는 애니메이션 레이어 블렌드 노드(animBlendNodeBase) (v02.61)."""
        types = cmds.nodeType(node, inherited=True) or []
        return "animCurve" in types or "animBlendNodeBase" in types

    @staticmethod
    def _blocked_axes(node, channel):
        """node 의 channel('translate' / 'rotate' / 'scale') 축 중 컨스트레인트를 걸 수 없는 축 ['x', ...].

        잠긴 축, 그리고 키(animCurve) 가 아닌 무언가가 이미 구동하는 축(다른 컨스트레인트 · 익스프레션 · 연결).
        translate / rotate 는 키가 있어도 걸 수 있다 - 마야가 pairBlend 를 끼워 컨스트레인트가 이긴다(blendParent = 1).
        ★ scale 은 pairBlend 가 없어 키 있는 축에 scaleConstraint 가 실패한다("Destination attribute must be writable",
        마야 Constrain > Scale 도 같다) -> scale 은 키 있는 축도 막힌 축으로 센다.
        v02.61: 애니메이션 레이어 블렌드 노드 구동도 키로 본다(translate / rotate 는 마야가 pairBlend 를 끼운다)."""
        short = {"translate": "t", "rotate": "r", "scale": "s"}[channel]
        parent_src = cmds.listConnections(node + "." + channel, source=True, destination=False,
                                          skipConversionNodes=True) or []
        parent_blocked = any(not LocatorBakeManager._is_key_source(x) for x in parent_src) \
            or (channel == "scale" and parent_src)
        blocked = []
        for ax in "xyz":
            plug = node + "." + short + ax
            if cmds.getAttr(plug, lock=True) or parent_blocked:
                blocked.append(ax)
                continue
            srcs = cmds.listConnections(plug, source=True, destination=False, skipConversionNodes=True) or []
            if srcs and channel == "scale":
                blocked.append(ax)
            elif any(not LocatorBakeManager._is_key_source(x) for x in srcs):
                blocked.append(ax)
        return blocked

    @staticmethod
    def _ensure_keyed(obj, channel, free_axes):
        """구간 블렌드용 - 채널 묶음의 축이 하나도 연결돼 있지 않으면(키 없음) 지금 값으로 키를 넣는다.

        pairBlend 는 키(또는 레이어) 가 있는 채널에만 생긴다 - 없으면 blendParent 가 없어 구간을 못 나눈다.
        정적 값 키라 움직임은 그대로다."""
        short = {"translate": "t", "rotate": "r"}[channel]
        plugs = [obj + "." + short + ax for ax in "xyz"]
        if cmds.listConnections(obj + "." + channel, source=True, destination=False):
            return
        if any(cmds.listConnections(p, source=True, destination=False) for p in plugs):
            return
        attrs = [short + ax for ax in free_axes]
        if attrs:
            cmds.setKeyframe(obj, attribute=attrs)

    @staticmethod
    def blend_plugs(constraint):
        """컨스트레인트가 끼운 pairBlend 들의 웨이트를 구동하는 plug (`obj.blendParent1` 등). 없으면 pairBlend.weight."""
        out = []
        for pb in set(cmds.listConnections(constraint, source=False, destination=True, type="pairBlend") or []):
            src = cmds.listConnections(pb + ".weight", source=True, destination=False, plugs=True) or []
            plug = src[0] if src else pb + ".weight"
            if "animCurve" in (cmds.nodeType(plug.split(".")[0], inherited=True) or []):
                # 이미 키가 꽂혀 있으면 그 키가 구동하는 쪽(오브젝트 attr)을 찾는다
                dst = cmds.listConnections(plug.split(".")[0], source=False, destination=True, plugs=True) or []
                plug = dst[0] if dst else pb + ".weight"
            if plug not in out:
                out.append(plug)
        return out

    @staticmethod
    def key_blend_range(plugs, start, end):
        """웨이트 plug 들에 step 키 Start-1 = 0 · Start = 1 · End = 1 · End+1 = 0."""
        start, end = int(start), int(end)
        for plug in plugs:
            node, attr = plug.split(".", 1)
            cmds.cutKey(node, attribute=attr, clear=True)
            for frame, value in ((start - 1, 0.0), (start, 1.0), (end, 1.0), (end + 1, 0.0)):
                cmds.setKeyframe(node, attribute=attr, time=frame, value=value, outTangentType="step")

    @staticmethod
    def constrain_objects(pairs, types, translate=True, rotate=True, scale=False, blend_range=None):
        """pairs = [(로케이터, 오브젝트)] 마다 로케이터 -> 오브젝트 컨스트레인트. 반환 (만든 컨스트레인트, 경고 목록).

        types : CONSTRAINT_TYPES 중 고른 것. 굽지 않은 채널 묶음은 건너뛴다(translate=False 면 point 없음 ·
        parent 는 이동 축 skip). 축 단위로 잠김 / 다른 구동을 건너뛰고, 오브젝트 하나가 실패해도 나머지는 계속한다.
        blend_range : (start, end) 면 구간 블렌드(v02.61) - pairBlend 웨이트를 구간에만 1. scale 은 못 한다(경고)."""
        chosen = set(types or ())
        types = [t for t in LocatorBakeManager.CONSTRAINT_TYPES if t in chosen]
        baked = {"translate": translate, "rotate": rotate, "scale": scale}
        need_of = {"point": "translate", "orient": "rotate", "scale": "scale"}
        made, warnings = [], []
        for loc, obj in pairs:
            short = obj.split("|")[-1]
            for ctype in types:
                try:
                    if ctype == "parent":
                        if not (translate or rotate):
                            warnings.append("{0}: parent skipped (Translate / Rotate not baked)".format(short))
                            continue
                        blk_t = LocatorBakeManager._blocked_axes(obj, "translate") if translate else []
                        blk_r = LocatorBakeManager._blocked_axes(obj, "rotate") if rotate else []
                        skip_t = blk_t if translate else ["x", "y", "z"]
                        skip_r = blk_r if rotate else ["x", "y", "z"]
                        if len(skip_t) == 3 and len(skip_r) == 3:
                            warnings.append("{0}: parent skipped (no free translate / rotate channel)".format(short))
                            continue
                        if blend_range:
                            if len(skip_t) < 3:
                                LocatorBakeManager._ensure_keyed(obj, "translate", [a for a in "xyz" if a not in skip_t])
                            if len(skip_r) < 3:
                                LocatorBakeManager._ensure_keyed(obj, "rotate", [a for a in "xyz" if a not in skip_r])
                        con = cmds.parentConstraint(loc, obj, maintainOffset=False,
                                                    skipTranslate=skip_t or "none", skipRotate=skip_r or "none")
                        made += con
                        if blend_range:
                            LocatorBakeManager.key_blend_range(LocatorBakeManager.blend_plugs(con[0]), *blend_range)
                        if blk_t or blk_r:
                            warnings.append("{0}: parent skipped axes T[{1}] R[{2}] (locked / driven)".format(
                                short, "".join(blk_t), "".join(blk_r)))
                        continue
                    need = need_of[ctype]
                    if not baked[need]:
                        warnings.append("{0}: {1} skipped ({2} not baked)".format(short, ctype, need.capitalize()))
                        continue
                    skip = LocatorBakeManager._blocked_axes(obj, need)
                    if len(skip) == 3:
                        warnings.append("{0}: {1} skipped (all {2} channels locked / driven{3})".format(short, ctype, need,
                                                                                       " / keyed" if need == "scale" else ""))
                        continue
                    fn = {"point": cmds.pointConstraint, "orient": cmds.orientConstraint,
                          "scale": cmds.scaleConstraint}[ctype]
                    if blend_range and need != "scale":
                        LocatorBakeManager._ensure_keyed(obj, need, [a for a in "xyz" if a not in skip])
                    con = fn(loc, obj, maintainOffset=False, skip=skip or "none")
                    made += con
                    if blend_range:
                        if need == "scale":
                            warnings.append("{0}: scale constraint drives every frame (scale has no blend attribute)".format(
                                short))
                        else:
                            LocatorBakeManager.key_blend_range(LocatorBakeManager.blend_plugs(con[0]), *blend_range)
                    if skip:
                        warnings.append("{0}: {1} skipped axes [{2}] (locked / driven{3})".format(
                            short, ctype, "".join(skip), " / keyed" if need == "scale" else ""))
                except RuntimeError as exc:
                    warnings.append("{0}: {1} failed - {2}".format(short, ctype, str(exc).strip()))
        return made, warnings

    # ------------------------------------------------------------------ 빠른 경로 (v02.56)
    #
    # 일반 경로는 bakeResults(simulation) 라 **프레임마다 씬 시간을 옮겨** 평가한다 - 무거운 리그가 있으면
    # 그 프레임마다 장면 전체가 다시 돈다. 빠른 경로는 시간을 옮기지 않는다:
    #   - 부모 쪽 행렬 Pm = inverse(matrix) * worldMatrix 를 **Start 프레임에서 한 번만** 읽고,
    #     프레임마다는 오브젝트의 로컬 `matrix` 만 `getAttr -time`(DG 컨텍스트 평가 - 그 노드의 상류만)으로 읽어
    #     W = matrix * Pm. 부모 체인도 장면의 나머지도 평가하지 않는다.
    #   - **"부모가 움직이지 않는다" 는 사용자가 정한다**(UI 체크). 그룹에 컨스트레인트 등이 연결돼 있어도 실제로는
    #     안 움직이는 경우가 있어서, 툴이 연결만 보고 판단하지 않는다. 틀리게 고르면 결과도 틀린다(Start 프레임만 맞다).
    #   - 부모가 움직이는 경우는 일반 경로(bakeResults)를 쓴다. 프레임마다 worldMatrix 를 컨텍스트로 읽는 방식도 재 봤지만
    #     깊은 계층에서는 호출마다 부모 체인을 다시 평가해 일반 베이크보다 느렸다(30 단계 x 5 개 x 300f: 0.91 s vs 0.17 s).
    # 키는 매 프레임 찍으므로 정수 프레임에서는 일반 경로와 같은 값이다(검증 샘플링 불필요).
    # 쓰기: 임시 커브를 createNode(undo 됨) -> API 로 값 채움 -> copyKey / pasteKey(undo 됨) -> 임시 커브 삭제.
    #   ★ animCurve 의 `ktv` 는 setAttr 로 못 쓴다("should be set with the keyframe or setKeyframe command").
    #   이 방식은 undo / redo 모두 그대로(mayapy 2024 확인), 1000 키 0.006 s.

    _CURVE_TYPE = {"t": "animCurveTL", "r": "animCurveTA", "s": "animCurveTU"}

    @staticmethod
    def _snap_to(loc, src):
        """로케이터(월드 루트)의 이동 · 회전을 src 의 현재 월드 자세로. 스케일은 1 그대로."""
        m = om.MMatrix(cmds.getAttr(src + ".worldMatrix[0]"))
        vals = LocatorBakeManager.decompose([m], cmds.getAttr(loc + ".rotateOrder"))
        cmds.setAttr(loc + ".translate", *[om.MDistance(vals[k][0]).asUnits(om.MDistance.uiUnit())
                                           for k in ("tx", "ty", "tz")])
        cmds.setAttr(loc + ".rotate", *[om.MAngle(vals[k][0]).asUnits(om.MAngle.uiUnit())
                                        for k in ("rx", "ry", "rz")])

    @staticmethod
    def _matrix_at(node, attr, frame):
        return om.MMatrix(cmds.getAttr("{0}.{1}".format(node, attr), time=frame))

    @staticmethod
    def sample_world(node, start, end, step=None):
        """[start, end] 프레임마다 node 의 월드 행렬(MMatrix 목록) - **부모가 움직이지 않는다는 가정**.

        씬 시간은 옮기지 않는다. 부모 쪽 행렬은 start 에서 한 번, 프레임마다는 로컬 matrix 만 읽는다."""
        local0 = LocatorBakeManager._matrix_at(node, "matrix", start)
        world0 = LocatorBakeManager._matrix_at(node, "worldMatrix[0]", start)
        pm = local0.inverse() * world0          # world = local * Pm (행벡터 규약)
        out = []
        for i, f in enumerate(range(int(start), int(end) + 1)):
            out.append(LocatorBakeManager._matrix_at(node, "matrix", f) * pm)
            if step:
                step(i + 1)
        return out

    @staticmethod
    def decompose(worlds, rotate_order=0):
        """월드 행렬 목록 -> {'tx': [...], ..., 'sz': [...]} (이동 cm 내부 단위, 회전 rad, 연속화)."""
        order = (om.MEulerRotation.kXYZ, om.MEulerRotation.kYZX, om.MEulerRotation.kZXY,
                 om.MEulerRotation.kXZY, om.MEulerRotation.kYXZ, om.MEulerRotation.kZYX)[int(rotate_order)]
        vals = dict((k, []) for k in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"))
        prev = None
        for m in worlds:
            tm = om.MTransformationMatrix(m)
            t = tm.translation(om.MSpace.kWorld)
            e = tm.rotation().reorder(order)
            if prev is not None:
                e = e.closestCut(prev)              # 같은 회전 그대로, ±360 만 이어 붙인다
            prev = e
            s = tm.scale(om.MSpace.kWorld)
            for k, v in zip(("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"),
                            (t.x, t.y, t.z, e.x, e.y, e.z, s[0], s[1], s[2])):
                vals[k].append(v)
        return vals

    @staticmethod
    def write_curves(node, start, values, attrs):
        """values[attr] (프레임마다) 를 node.attr 커브로 통째 기록. undo 되는 경로(임시 커브 + copy / paste)."""
        times = om.MTimeArray()
        n = len(values[attrs[0]]) if attrs else 0
        for i in range(n):
            times.append(om.MTime(int(start) + i, om.MTime.uiUnit()))
        for attr in attrs:
            tmp = cmds.createNode(LocatorBakeManager._CURVE_TYPE[attr[0]], name="LOC_fast_tmp")
            try:
                sel = om.MSelectionList()
                sel.add(tmp)
                fn = oma.MFnAnimCurve(sel.getDependNode(0))
                va = om.MDoubleArray()
                for v in values[attr]:
                    va.append(v)
                fn.addKeys(times, va)
                cmds.copyKey(tmp)
                cmds.pasteKey(node, attribute=attr, option="replaceCompletely")
            finally:
                if cmds.objExists(tmp):
                    cmds.delete(tmp)

    # ------------------------------------------------------------------ 베이크

    @staticmethod
    def bake(objects, start, end, translate=True, rotate=True, scale=False,
             euler_filter=True, select_result=True, progress=None, constrain=None,
             fast=False, constrain_range=False):
        """objects 마다 로케이터를 만들어 [start, end] 를 월드 베이크한다.

        progress : progress(done, total, message=None) - 단계마다 0 -> total. None 이면 조용히.
                   단계 순서는 PHASE_CREATE -> PHASE_BAKE -> PHASE_CLEANUP 이고 단계가 바뀔 때
                   `progress.phase(name)` 이 있으면 먼저 부른다(UI 가 진행 팝업 단계를 넘긴다).
                   constrain 이 있으면 마지막에 PHASE_CONSTRAIN 단계가 하나 더 온다.
        constrain: 베이크 뒤 로케이터 -> 오브젝트 컨스트레인트 종류(CONSTRAINT_TYPES 의 부분집합). None / 빈 것 = 안 건다.
        constrain_range : True 면 컨스트레인트가 Start ~ End 에만 영향(밖은 원래 움직임) - pairBlend 웨이트 step 키 (v02.61).
        fast     : True 면 **부모가 움직이지 않는다고 보고** 씬 시간을 옮기지 않는 빠른 경로(위 `빠른 경로` 설명).
                   임시 컨스트레인트도 만들지 않는다. 부모가 움직이면 결과가 틀린다 - 사용자가 고른다.
        반환     : (만든 로케이터 이름 목록, msg)
        """
        if start is None or end is None:
            return [], "[Warning] Enter Start / End."
        start, end = int(start), int(end)
        if start > end:
            return [], "[Warning] Start ({0}) is greater than End ({1}).".format(start, end)
        if not (translate or rotate or scale):
            return [], "[Warning] Enable at least one channel group."
        chosen = set(constrain or ())
        constrain = [t for t in LocatorBakeManager.CONSTRAINT_TYPES if t in chosen]
        if "parent" in constrain and ("point" in constrain or "orient" in constrain):
            return [], "[Warning] Parent cannot be combined with Point / Orient - pick one."

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
        made_constraints, constrain_warnings = [], []
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
                        if fast:
                            _step(i + 1, n, loc)
                            continue
                        if translate or rotate:
                            skip_t = [] if translate else ["x", "y", "z"]
                            skip_r = [] if rotate else ["x", "y", "z"]
                            # ★ parentConstraint 는 원본의 rotateAxis 를 반영하지 않는다(v02.56 발견 - rotateAxis
                            #   (10,-20,5) 원본에서 로케이터가 매 프레임 23.26 도 어긋났다). 로케이터를 원본 월드 자세에
                            #   먼저 놓고 maintainOffset 으로 걸면 그 일정한 차이가 오프셋으로 흡수된다.
                            LocatorBakeManager._snap_to(loc, src)
                            constraints += cmds.parentConstraint(
                                src, loc, maintainOffset=True, skipTranslate=skip_t, skipRotate=skip_r)
                        if scale:
                            constraints += cmds.scaleConstraint(src, loc, maintainOffset=False)
                        _step(i + 1, n, loc)

                    # 3. 베이크 한 번 - 진행률은 시간 변경 콜백으로
                    _phase(LocatorBakeManager.PHASE_BAKE)
                    frames = end - start + 1

                    if fast:
                        # 3'. 빠른 경로 - 시간을 옮기지 않고 행렬을 읽어 커브를 통째 쓴다.
                        total = frames * n
                        for i, (src, loc) in enumerate(zip(targets, locators)):
                            base = i * frames

                            def _fstep(done, _base=base, _name=src.split("|")[-1]):
                                if done % 25 == 0 or done == frames:
                                    _step(_base + done, total, "{0}  frame {1} / {2}".format(
                                        _name, start + done - 1, end))

                            worlds = LocatorBakeManager.sample_world(src, start, end, step=_fstep)
                            values = LocatorBakeManager.decompose(
                                worlds, cmds.getAttr(loc + ".rotateOrder"))
                            LocatorBakeManager.write_curves(loc, start, values, attrs)
                        _step(total, total)

                    def _on_time(mtime, *_args):
                        try:
                            done = int(round(mtime.value)) - start + 1
                            if 0 < done <= frames:
                                _step(done, frames, "Frame {0} / {1}".format(int(round(mtime.value)), end))
                        except Exception:  # noqa: BLE001 - 콜백 예외가 베이크를 깨지 않게
                            pass

                    if not fast:
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

                    # 5. (옵션) 로케이터 -> 오브젝트 컨스트레인트. 원본 키는 그대로 두고 pairBlend 로 컨스트레인트가 덮는다.
                    if constrain:
                        _phase(LocatorBakeManager.PHASE_CONSTRAIN)
                        for i, pair in enumerate(zip(locators, targets)):
                            made, warns = LocatorBakeManager.constrain_objects(
                                [pair], constrain, translate=translate, rotate=rotate, scale=scale,
                                blend_range=(start, end) if constrain_range else None)
                            made_constraints += made
                            constrain_warnings += warns
                            _step(i + 1, n, pair[1].split("|")[-1])
            except Exception as exc:  # noqa: BLE001 - 반쯤 만든 결과를 남기지 않는다
                leftovers = [x for x in constraints + made_constraints + locators if cmds.objExists(x)]
                if leftovers:
                    cmds.delete(leftovers)
                cmds.currentTime(current, edit=True)
                return [], "[Error] Locator bake failed : {0}".format(str(exc).strip())

            if not fast:      # 빠른 경로는 시간을 건드리지 않았다(되돌리는 것도 시간 변경이다)
                cmds.currentTime(current, edit=True)
            if select_result:
                cmds.select(locators, replace=True)

        msg = "LOC + Anim : {0} locator(s), frames {1} - {2} ({3}).".format(
            len(locators), start, end, " ".join(
                g for g, on in (("T", translate), ("R", rotate), ("S", scale)) if on))
        if fast:
            msg += "  Fast mode (parents treated as still - read once at frame {0}).".format(start)
        if constrain:
            msg += "  Constrained objects ({0}): {1} constraint(s).".format(
                " + ".join(c.capitalize() for c in constrain), len(made_constraints))
            if constrain_range:
                msg += "  Blend 1 only in {0} - {1} (blendParent keys).".format(start, end)
            if constrain_warnings:
                msg += "  [Warning] " + "; ".join(constrain_warnings)
        if skipped:
            msg += "  Skipped {0}: {1}".format(
                len(skipped), ", ".join("{0} ({1})".format(o, why) for o, why in skipped))
        return locators, msg
