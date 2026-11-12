# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00110_animTool_V02 - 리스트업한 컨트롤러를 구간 dense 키로 굽는 핵심 로직 (maya.cmds, UI 비의존)
#
# A00120_FKIK 의 native bakeResults 베이크(Python 프레임 루프 대체)를 범용 bake 로 이식.
#   - FKIK 는 타깃->팔로워 매칭이라 임시 parentConstraint 가 필요했지만, 여기서는
#     리스트의 노드 자체를 바로 굽기 때문에 컨스트레인트를 만들지 않는다.
#   - currentTime/xform 프레임 루프 없이 단일 C++ 베이커로 처리 -> 6000+프레임 × 50~100
#     컨트롤러에서 수십 배 빠르다. Maya 2023(Python 3.9) 동작 확인.
#
# v02.51 - **애니메이션 레이어에 든 오브젝트**는 bakeResults 를 쓰지 않는다 (사용자 보고: 컨스트레인트를 걸고 [10, 50] 만 구우면
#   그 밖의 기존 키가 지워진다). mayapy 실측 - 레이어 멤버 채널에서 bakeResults -time s:e -preserveOutsideKeys 는
#     ① Base 커브를 [s, e] 의 키만 남기고 바꿔 버리고(구간 밖 키 소실, preserveOutsideKeys 무시)
#     ② 최종 합성값을 Base 에 그대로 써서 구간 안에서 위 레이어 값이 한 번 더 더해진다.
#   대신 (bake_layered): 컨스트레인트가 켜진 채 [s, e] 매 프레임 채널 값을 샘플링 -> 채널마다 대상 레이어
#   (그 채널을 덮는 맨 위 override 레이어, 없으면 BaseAnimation) 커브의 [s, e] 안 키만 지우고 매 프레임
#   `setKeyframe -animLayer 대상 -value 값` (마야가 위 레이어를 빼서 역산). 다른 레이어 커브 · 구간 밖 키는 그대로.
#   실측: additive · override 모두 구간 밖 변화 0, 구간 안 = 컨스트레인트 결과(1e-4). 컨스트레인트는 bakeResults 처럼 남긴다
#   (bakeResults 도 keep / bake down 둘 다 컨스트레인트를 지우지 않았다). 레이어에 안 든 오브젝트는 예전처럼 bakeResults 한 번.
#   **Smart bake 도 구간 밖을 망가뜨렸다**(레이어 없이도: `bakeResults -smart` 는 preserveOutsideKeys 를 안 지켜 구간 밖 60 f 값이 바뀜).
#   -> smart 는 dense 로 정확히 구운 뒤 구운 커브의 [s, e] 안만 `filterCurve -filter simplify -tolerance tol -startTime s -endTime e`
#   (구간 밖 변화 0 실측). 레이어 오브젝트에도 같은 방식으로 적용된다.

import maya.cmds as cmds

from Framework.core.maya_refresh import suspend_refresh

from .layer_key_manager import LayerKeyManager
from .anim_layer_manager import AnimLayerManager


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

        # v02.51 : 레이어에 든 오브젝트는 따로 (bakeResults 가 구간 밖 키를 지운다)
        layered = BakeManager.layered_objects(objects, attrs)
        plain = [o for o in objects if o not in layered]

        # v02.51 : 언제나 dense 로 굽는다 (bakeResults -smart 는 구간 밖 키를 망가뜨린다). smart 는 뒤에서 구간 안만 simplify.
        bake_kwargs = dict(
            simulation=simulation,
            time=(start, end),
            sampleBy=1,
            attribute=attrs,
            disableImplicitControl=disable_implicit,
            preserveOutsideKeys=True,
            sparseAnimCurveBake=False,
        )

        cur = cmds.currentTime(q=True)
        used_smart = False
        notes = []
        baked_curves = []

        cmds.undoInfo(openChunk=True)
        try:
            # suspend_refresh: 블록 종료 시 refresh 복원이 항상 먼저/무조건 실행된다.
            with suspend_refresh():
                if plain:
                    cmds.bakeResults(plain, **bake_kwargs)
                    for obj in plain:
                        for attr in attrs:
                            baked_curves += cmds.keyframe("{0}.{1}".format(obj, attr), q=True, name=True) or []
                if layered:
                    notes, curves = BakeManager.bake_layered(layered, start, end, attrs)
                    baked_curves += curves
                if smart and baked_curves:
                    used_smart = BakeManager.simplify_range(baked_curves, start, end, smart_tolerance)
        finally:
            # 예외가 나도 프레임 복원 / undo 청크 닫기를 반드시 수행(refresh 는 위에서 복원됨).
            cmds.currentTime(cur, edit=True)
            cmds.undoInfo(closeChunk=True)

        n = len(objects)
        frames = end - start + 1
        kept = "kept" if not disable_implicit else "baked down"
        if used_smart:
            mode = "smart: dense bake + simplify inside the range (tol {0})".format(smart_tolerance)
        elif smart:
            mode = "dense (smart simplify failed, keys left dense)"
        else:
            mode = "dense"
        msg = "{0} object(s) baked over [{1}-{2}] ({3} frames, {4}, constraints {5}).".format(
            n, start, end, frames, mode, kept)
        if layered:
            msg += (" {0} in animation layers: baked through the layers, keys outside [{1}-{2}] kept.".format(
                len(layered), start, end))
        for line in notes:
            msg += "\n  " + line
        return (n, msg)

    # ==================================================
    # v02.51 : 애니메이션 레이어에 든 오브젝트
    # ==================================================

    @staticmethod
    def reduce_keys(times, values, tolerance):
        """Douglas-Peucker (1D) : 직선 보간으로 모든 샘플 오차 <= tolerance 가 되게 남길 인덱스 (양 끝 포함, 정렬)."""
        n = len(times)
        if n <= 2:
            return list(range(n))
        keep = {0, n - 1}
        stack = [(0, n - 1)]
        while stack:
            i0, i1 = stack.pop()
            if i1 - i0 < 2:
                continue
            t0, v0, t1, v1 = times[i0], values[i0], times[i1], values[i1]
            worst, wi = -1.0, None
            for i in range(i0 + 1, i1):
                lin = v0 + (v1 - v0) * (times[i] - t0) / (t1 - t0)
                d = abs(values[i] - lin)
                if d > worst:
                    worst, wi = d, i
            if worst > tolerance:
                keep.add(wi)
                stack.append((i0, wi))
                stack.append((wi, i1))
        return sorted(keep)

    @staticmethod
    def simplify_range(curves, start, end, tolerance):
        """구운 커브들의 [start, end] 안 키만 줄인다 (v02.51 smart). 구간 밖 키는 건드리지 않는다. 반환 성공 여부.

        `bakeResults -smart` 는 구간 밖을 망가뜨리고 `filterCurve -simplify` 는 허용오차를 안 지켰다(실측) ->
        Douglas-Peucker 로 남길 키를 고르고 나머지를 cutKey 한 번에 지운 뒤, 남은 키 탄젠트를 linear 로
        (정수 프레임 오차 <= tolerance, 채널 단위). cutKey 라 undo 에 들어간다.
        """
        curves = [c for c in dict.fromkeys(curves) if c and cmds.objExists(c)]
        if not curves:
            return False
        try:
            tol = max(0.0, float(tolerance))
            for crv in curves:
                times = cmds.keyframe(crv, q=True, time=(start, end), timeChange=True) or []
                if len(times) <= 2:
                    continue
                values = cmds.keyframe(crv, q=True, time=(start, end), valueChange=True) or []
                keep = set(BakeManager.reduce_keys(times, values, tol))
                drop = [(t, t) for i, t in enumerate(times) if i not in keep]
                if drop:
                    cmds.cutKey(crv, time=drop, clear=True)
                cmds.keyTangent(crv, e=True, time=(start, end), itt="linear", ott="linear")
            return True
        except Exception:                                   # noqa: BLE001
            return False

    @staticmethod
    def _long_attr(obj, attr):
        try:
            return cmds.attributeQuery(attr, node=obj, longName=True)
        except Exception:                                   # noqa: BLE001
            return attr

    @staticmethod
    def _members(layer):
        """레이어 멤버 plug 집합 {(uuid, 긴 어트리뷰트 이름)} - 이름 표기(네임스페이스 · DAG 경로)와 무관하게 비교."""
        out = set()
        for plug in cmds.animLayer(layer, q=True, attribute=True) or []:
            node, _sep, attr = plug.partition(".")
            uid = (cmds.ls(node, uuid=True) or [None])[0]
            if uid:
                out.add((uid, BakeManager._long_attr(node, attr)))
        return out

    @staticmethod
    def _layer_order():
        """[(레이어, layer_info)] 에디터 순서 맨 위부터 (BaseAnimation 제외). 레이어가 없으면 []."""
        return [(r["name"], r) for r in AnimLayerManager.rows() if not r.get("base")]

    @staticmethod
    def layered_objects(objects, attrs):
        """굽는 채널 중 하나라도 BaseAnimation 아닌 레이어의 멤버인 오브젝트들."""
        layers = BakeManager._layer_order()
        if not layers:
            return []
        members = set()
        for layer, _info in layers:
            members |= BakeManager._members(layer)
        out = []
        for obj in objects:
            uid = (cmds.ls(obj, uuid=True) or [None])[0]
            if uid and any((uid, BakeManager._long_attr(obj, a)) in members for a in attrs):
                out.append(obj)
        return out

    @staticmethod
    def target_layer(obj, attr, layers=None, members=None, root=None):
        """이 채널을 결정하는 레이어 = 덮는 맨 위 override 레이어(뮤트 제외), 없으면 BaseAnimation."""
        root = root or LayerKeyManager.root_layer()
        layers = BakeManager._layer_order() if layers is None else layers
        uid = (cmds.ls(obj, uuid=True) or [None])[0]
        key = (uid, BakeManager._long_attr(obj, attr))
        for layer, info in layers:
            if info.get("muted") or not info.get("override"):
                continue
            mem = members[layer] if members is not None else BakeManager._members(layer)
            if key in mem:
                return layer
        return root

    @staticmethod
    def _unwrap(prev, values):
        """회전 값 목록을 앞 값과 ±360 단위로 이어 붙인다(같은 회전, 커브 튐 없음)."""
        out = []
        for v in values:
            if prev is not None:
                v += 360.0 * round((prev - v) / 360.0)
            out.append(v)
            prev = v
        return out

    @staticmethod
    def bake_layered(objects, start, end, attrs, before_write=None, unwrap_rotation=False, edge_keys=False):
        """레이어 오브젝트를 [start, end] 만 굽는다 - 구간 밖 키 · 다른 레이어 커브 보존. 반환 (로그 줄(경고), 키를 찍은 커브).

        1) 컨스트레인트 등이 켜진 채 매 프레임 채널 값 샘플링 (currentTime 루프 = simulation)
        2) 채널마다 대상 레이어(target_layer) 커브의 [start, end] 안 키만 지움
        3) 매 프레임 setKeyframe -animLayer 대상 -value 값 (마야가 위 레이어를 빼서 역산)
        undo 묶기 · 시간 복원은 호출부(bake).

        before_write    : (v02.59) 샘플링 뒤 · 키 찍기 전에 부르는 함수. 대상 레이어는 **그 뒤에** 정한다 -
                          예) Locator 의 `LOC_Constraint` 레이어 · 컨스트레인트를 지운 뒤 그 아래 레이어에 굽기.
                          레이어가 하나도 안 남으면 오브젝트 직결 커브에 찍는다.
        unwrap_rotation : (v02.59) 회전 샘플을 Start-1 값부터 ±360 으로 이어 붙인다(컨스트레인트 출력은 -180~180 이라
                          원래 커브가 그 밖이면 경계에서 튄다).
        edge_keys       : (v02.59) 구간 바깥에 기존 키가 없는 쪽은 Start-1 / End+1 에 그때 값으로 키(아래). 컨스트레인트를
                          지운 뒤(before_write) 굽는 경우만 - 컨스트레인트를 남기는 Bake 탭은 끈다(경계 값에 컨스트레인트가 섞인다).
        """
        frames = list(range(int(start), int(end) + 1))
        notes = []

        # 채널 목록 (잠긴 채널 · 없는 어트리뷰트 제외)
        plugs = []
        for obj in objects:
            for attr in attrs:
                plug = "{0}.{1}".format(obj, attr)
                try:
                    if cmds.getAttr(plug, lock=True):
                        notes.append("[Warning] {0}: locked - skipped.".format(plug))
                        continue
                except Exception:                           # noqa: BLE001
                    continue
                plugs.append((obj, attr, plug))

        # 1) 샘플링
        values = dict((p[2], []) for p in plugs)
        prev = {}
        if unwrap_rotation:
            cmds.currentTime(int(start) - 1)
            for _o, attr, plug in plugs:
                if BakeManager._long_attr(_o, attr).startswith("rotate"):
                    prev[plug] = float(cmds.getAttr(plug))
        for f in frames:
            cmds.currentTime(f)
            for _o, _a, plug in plugs:
                values[plug].append(float(cmds.getAttr(plug)))
        for plug, first in prev.items():
            values[plug] = BakeManager._unwrap(first, values[plug])

        if before_write:
            before_write()

        # 대상 레이어 - before_write 가 레이어를 바꿨을 수 있어 샘플링 뒤에 정한다
        root = LayerKeyManager.root_layer()
        layers = BakeManager._layer_order()
        members = dict((layer, BakeManager._members(layer)) for layer, _i in layers)
        locked = set(layer for layer, info in layers if info.get("locked"))
        try:
            if root and cmds.animLayer(root, q=True, lock=True):
                locked.add(root)
        except Exception:                                   # noqa: BLE001
            pass
        plan = []
        for obj, attr, plug in plugs:
            target = BakeManager.target_layer(obj, attr, layers, members, root) if root else None
            if target and target in locked:
                notes.append("[Warning] {0}: layer '{1}' is locked - skipped.".format(plug, target))
                continue
            plan.append((obj, attr, plug, target))

        # v02.59 경계 키 - 구간 바깥에 기존 키가 없는 쪽(커브가 아예 없는 채널 포함)은 Start-1 / End+1 에 지금 값을 역산 키로.
        #   안 하면 새 키가 구간 안에만 생겨 구간 밖이 끝 키 값으로 늘어난다. 예) addSelectedObjects 로 만든 override 레이어는
        #   모든 채널이 멤버인데 대부분 커브가 없다(레이어 값 = 정적) -> 구간 안만 키를 찍으면 구간 밖이 바뀌었다(실측).
        curves = {}
        edges = {}
        for obj, attr, plug, target in plan:
            curve = LayerKeyManager.layer_curve(plug, target, root) if target else LayerKeyManager.plain_curve(plug)
            curves[plug] = curve
            times = (cmds.keyframe(curve, q=True, timeChange=True) or []) if curve else []
            need = []
            if not [t for t in times if t < start]:
                need.append(int(start) - 1)
            if not [t for t in times if t > end]:
                need.append(int(end) + 1)
            if need and edge_keys:
                edges[plug] = dict((f, None) for f in need)
        for f in sorted(set(f for d in edges.values() for f in d)):
            cmds.currentTime(f)
            for plug, d in edges.items():
                if f in d:
                    d[f] = float(cmds.getAttr(plug))

        # 2) 3) 대상 레이어 커브의 구간 안 키만 지우고 매 프레임 역산 키
        overridden = set()
        keyed_curves = []
        for obj, attr, plug, target in plan:
            curve = curves[plug]
            if curve:
                # 듬성한 커브는 구간 안 키를 지우면 구간 밖 보간 모양까지 바뀐다 -> Merge Layers 와 같은 경계 처리:
                # 바로 바깥 이웃 키 탄젠트 고정 + s-1 / e+1 에 모양 보존 키(fixed). auto 탄젠트는 이웃이 바뀌면 다시 계산된다.
                times = cmds.keyframe(curve, q=True, timeChange=True) or []
                before = [t for t in times if t < start]
                after = [t for t in times if t > end]
                if before:
                    p = max(before)
                    cmds.keyTangent(curve, e=True, time=(p, p), itt="fixed", ott="fixed")
                    LayerKeyManager._insert_fixed(curve, start - 1)
                if after:
                    q = min(after)
                    cmds.keyTangent(curve, e=True, time=(q, q), itt="fixed", ott="fixed")
                    LayerKeyManager._insert_fixed(curve, end + 1)
                cmds.cutKey(curve, time=(start, end), clear=True)
            keys = list(zip(frames, values[plug])) + sorted((edges.get(plug) or {}).items())
            for f, v in keys:
                if target:
                    cmds.setKeyframe(obj, attribute=attr, time=f, value=v, animLayer=target)
                else:
                    cmds.setKeyframe(obj, attribute=attr, time=f, value=v)
            if target and target != root:
                overridden.add("{0} -> {1}".format(plug, target))
            done = LayerKeyManager.layer_curve(plug, target, root) if target else LayerKeyManager.plain_curve(plug)
            if done:
                keyed_curves.append(done)
        if overridden:
            notes.append("Keyed on the override layer that decides the channel: {0}".format(
                LayerKeyManager._brief(sorted(overridden), limit=6)))
        return notes, keyed_curves
