# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-11
# A00110_animTool - 구간 전 프레임 키 채우기 (maya.cmds, UI 비의존)
#
# "[Start, End] 의 **모든 프레임**에 키가 있게 만든다. 이미 키가 있는 프레임은 그대로 두고,
#  없는 프레임만 지금 보이는 값 그대로 키를 찍는다(애니메이션 모양은 바뀌지 않는다)."
#
# ## 두 가지 경로 (mayapy 실측으로 갈랐다)
#
# 1) 대상 커브가 **이미 있으면** `setKeyframe(insert=True)`.
#    커브 모양을 그대로 보존한 채 키만 꽂아 준다. 값을 계산할 필요도 없고 오차도 없다
#    (실측 오차 1.8e-15). 이미 키가 있는 프레임에 insert 해도 개수가 안 늘지만, 요청대로
#    "방치" 를 확실히 하려고 있는 프레임은 아예 건너뛴다.
#
# 2) 대상 커브가 **없으면**(=아직 애니메이션이 없거나, 고른 레이어에 그 어트리뷰트 커브가
#    없으면) insert 는 **조용히 아무것도 하지 않는다**(실측: 반환 0, 커브 미생성).
#    그래서 이 경우에는 `getAttr(plug, time=f)` 로 프레임별 평가값을 읽어 값으로 키를 찍는다.
#
#    **값은 반드시 쓰기 전에 전부 미리 구한다.** 레이어 커브에 키가 하나라도 생기면 그
#    레이어의 기여가 달라져 이후 프레임의 평가값이 흔들릴 수 있다. 계산과 쓰기를 번갈아
#    하면 그 흔들린 값을 그대로 굳히게 된다.
#
# ## 애니메이션 레이어
#
# `setKeyframe(animLayer=L, value=V)` 는 레이어 커브에 V 를 그대로 쓰는 게 아니라 **최종
# 평가값이 V 가 되도록** 레이어 기여분을 역산해 넣는다(additive/override 공통). 그래서 위
# 2)번 경로에 평가값을 그대로 넘기면 레이어에서도 모양이 유지된다.
#
# 레이어의 그 어트리뷰트 커브는 `animLayer(L, q=True, findCurveForPlug=plug)` 로 찾는다.
# 어트리뷰트가 아직 그 레이어에 안 들어가 있으면 먼저 `animLayer(L, e=True, attribute=plug)`
# 로 넣어 준다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.core.maya_refresh import suspend_refresh


# 레이어를 명시하지 않을 때 콤보에 넣는 항목. 마야가 평소대로(= 애니메이션 레이어 에디터에서
# 선택된 레이어) 처리하게 둔다.
CURRENT_LAYER = "(current)"


class FillKeyManager:
    """구간의 빈 프레임을 지금 값 그대로 키로 채운다."""

    # ==================================================
    # 조회 (UI 목록 채우기)
    # ==================================================

    @staticmethod
    def list_keyable_attrs(objects):
        """오브젝트들의 **키 가능 + 채널박스 노출 + 잠기지 않은** 어트리뷰트 합집합.

        첫 등장 순서를 지킨다(선택 순서대로 채널이 나오도록).

        `listAttr(keyable=True)` 가 곧 "채널박스에 뜨는 키 가능 채널" 이다. 채널박스에만
        보이고 키는 못 찍는 채널(`setAttr -k false -cb true`)은 `-channelBox` 쪽에 잡히므로
        여기서는 제외된다 — 요청이 "키프레임을 찍을 수 있고 채널박스에 노출된" 것이라서.
        잠긴 채널은 키를 못 찍으므로 `unlocked=True` 로 걸러 낸다.
        """
        found = []
        seen = set()

        for obj in (objects or []):
            if not cmds.objExists(obj):
                continue
            try:
                attrs = cmds.listAttr(obj, keyable=True, visible=True,
                                      unlocked=True) or []
            except Exception:
                attrs = []
            for attr in attrs:
                # 중첩 이름(compound 자식 경로)은 plug 로 바로 못 쓰므로 제외.
                if "." in attr or attr in seen:
                    continue
                seen.add(attr)
                found.append(attr)

        return found

    @staticmethod
    def list_anim_layers():
        """(레이어 이름 목록, 지금 선택된 레이어 or None).

        주의: animLayer 에는 "선택된 레이어 목록"을 주는 전역 쿼리가 없다. `-selected` 는
        레이어 이름을 인자로 줘야 하는 per-layer 쿼리다. 그래서 전부 나열해 하나씩 본다.
        """
        layers = cmds.ls(type="animLayer") or []
        if not layers:
            return [], None

        # root(BaseAnimation)를 맨 앞으로.
        root = cmds.animLayer(q=True, root=True)
        if root and root in layers:
            layers = [root] + [l for l in layers if l != root]

        selected = None
        for layer in layers:
            try:
                if cmds.animLayer(layer, q=True, selected=True):
                    selected = layer
                    break
            except Exception:
                pass

        return layers, selected

    # ==================================================
    # 내부 헬퍼
    # ==================================================

    @staticmethod
    def _target_curve(plug, layer):
        """이 plug 를 이 레이어에서 구동하는 애님 커브. 없으면 None."""
        if layer:
            curves = cmds.animLayer(layer, q=True, findCurveForPlug=plug) or []
            return curves[0] if curves else None

        curves = cmds.keyframe(plug, q=True, name=True) or []
        return curves[0] if curves else None

    @staticmethod
    def _existing_times(curve, start, end):
        """커브가 [start, end] 안에 이미 갖고 있는 키 시각 집합."""
        if not curve:
            return set()
        times = cmds.keyframe(curve, q=True, timeChange=True,
                              time=(start, end)) or []
        return set(round(float(t), 4) for t in times)

    @staticmethod
    def _ensure_in_layer(plug, layer):
        """어트리뷰트가 그 레이어에 없으면 넣는다(있으면 그대로)."""
        if not layer:
            return
        try:
            if not cmds.animLayer(layer, q=True, findCurveForPlug=plug):
                cmds.animLayer(layer, edit=True, attribute=plug)
        except Exception:
            pass

    # ==================================================
    # 메인 동작
    # ==================================================

    @staticmethod
    def fill_keys(objects, attrs, start, end, layer=None, step=1):
        """[start, end] 의 모든 프레임에 키가 있도록 채운다.

        Args:
            objects: 대상 오브젝트 이름들.
            attrs: 채울 어트리뷰트 이름들(오브젝트에 없으면 그 오브젝트는 건너뛴다).
            start, end: 프레임 구간(양 끝 포함). 뒤집혀 들어와도 알아서 바로잡는다.
            layer: 키를 찍을 애니메이션 레이어. None 이면 마야 기본 동작(선택된 레이어).
            step: 프레임 간격(기본 1 = 모든 프레임).

        Returns:
            (added, skipped, messages)
            added   : 새로 찍은 키 개수
            skipped : 이미 키가 있어 건드리지 않은 프레임 수
            messages: 경고/안내 문자열 리스트
        """
        messages = []

        if not objects:
            raise ValueError("No objects. Select objects and press 'List Attributes'.")
        if not attrs:
            raise ValueError("No attributes selected. Pick the channels to fill.")

        start, end = (min(start, end), max(start, end))
        step = max(1, int(step))
        frames = [float(f) for f in range(int(start), int(end) + 1, step)]
        if not frames:
            raise ValueError("Empty frame range.")

        # ---- 1) 대상 plug 별로 '어느 프레임이 비었는지' + '어떻게 채울지' 를 먼저 정한다.
        #         (쓰기 전에 값을 다 구해 둬야 레이어 기여 변화에 흔들리지 않는다)
        insert_by_frame = {}     # {frame: [plug, ...]}  커브가 있어 insert 로 채울 것
        value_plans = []         # [(plug, [(frame, value), ...]), ...]  값으로 채울 것
        skipped = 0
        missing_attr = 0

        for obj in objects:
            if not cmds.objExists(obj):
                messages.append("[Warning] Not found, skipped: {0}".format(obj))
                continue

            for attr in attrs:
                plug = "{0}.{1}".format(obj, attr)
                if not cmds.objExists(plug):
                    missing_attr += 1
                    continue
                try:
                    if cmds.getAttr(plug, lock=True):
                        messages.append("[Warning] Locked, skipped: {0}".format(plug))
                        continue
                except Exception:
                    continue

                curve = FillKeyManager._target_curve(plug, layer)
                existing = FillKeyManager._existing_times(curve, start, end)

                todo = [f for f in frames if round(f, 4) not in existing]
                skipped += len(frames) - len(todo)
                if not todo:
                    continue

                if curve:
                    # 커브가 있으면 insert 로 모양 그대로 꽂는다. 값 계산 불필요.
                    for f in todo:
                        insert_by_frame.setdefault(f, []).append(plug)
                else:
                    # 커브가 없으면 프레임별 평가값을 **미리** 전부 읽어 둔다.
                    try:
                        plan = [(f, cmds.getAttr(plug, time=f)) for f in todo]
                    except Exception as e:
                        messages.append("[Warning] Cannot read {0}: {1}".format(
                            plug, str(e).strip()))
                        continue
                    value_plans.append((plug, plan))

        if missing_attr:
            messages.append(
                "[Info] {0} object/attribute pair(s) did not exist and were "
                "skipped.".format(missing_attr))

        if not insert_by_frame and not value_plans:
            return 0, skipped, messages

        # ---- 2) 실제로 쓴다.
        added = 0

        with undo_chunk():
            with suspend_refresh():

                # 값으로 채우는 쪽: 레이어에 없는 어트리뷰트는 먼저 넣어 준다.
                for plug, _plan in value_plans:
                    FillKeyManager._ensure_in_layer(plug, layer)

                # insert 는 프레임 단위로 여러 plug 를 한 번에 처리한다
                # (프레임 x plug 만큼 호출하지 않으려고).
                for frame in sorted(insert_by_frame):
                    plugs = insert_by_frame[frame]
                    kwargs = {"time": frame, "insert": True}
                    if layer:
                        kwargs["animLayer"] = layer
                    try:
                        added += cmds.setKeyframe(plugs, **kwargs) or 0
                    except Exception as e:
                        messages.append("[Warning] insert failed at frame {0}: "
                                        "{1}".format(frame, str(e).strip()))

                for plug, plan in value_plans:
                    for frame, value in plan:
                        kwargs = {"time": frame, "value": value}
                        if layer:
                            kwargs["animLayer"] = layer
                        try:
                            added += cmds.setKeyframe(plug, **kwargs) or 0
                        except Exception as e:
                            messages.append("[Warning] {0} @ {1}: {2}".format(
                                plug, frame, str(e).strip()))

        return added, skipped, messages
