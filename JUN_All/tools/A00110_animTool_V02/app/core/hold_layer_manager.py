# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-04
# A00110_animTool_V02 - Shift+A 추가 기능 : Layer Blend Key (v02.39, maya.cmds, UI 비의존)
#
# Shift+A(Hold Selected Range) 를 누를 때 옵션이 켜져 있으면, 사용자가 고른 애니메이션 레이어에
#   - (현재 프레임 - N) : 선택 오브젝트의 **레이어 멤버 keyable 채널 전부** 에 "그 시점의 레이어 값" 으로 키
#   - (현재 프레임)     : Key > Pose Key 에서 체크된 축에 그 값으로 키
# 를 찍는다. 결과 = 레이어 안에서 N 프레임 동안 원래 값 -> Pose 값으로 부드럽게 바뀐다.
# 계획서 docs/plans/a00110_hold_layer_blend_plan.md
#
# 핫키(run_hold)는 nameCommand 에서 정적으로 불려 UI 위젯을 못 읽는다
#   -> UI 가 바뀔 때마다 `HoldLayerManager.update(...)` 로 밀어 넣고, apply() 는 그걸 읽는다.
#
# v02.40 - **설정의 원본은 optionVar(OPTVAR_PREFIX)** 다. update() 가 optionVar 에 쓰고 apply() 는 optionVar 에서 읽는다.
#   v02.39 는 클래스 변수 settings 를 원본으로 썼는데, DEV 리로드(같은 깊이 모듈을 sys.modules 등록 순서대로 reload)에서
#   hotkey_manager 가 hold_layer_manager 보다 먼저 reload 되면 `from .hold_layer_manager import HoldLayerManager` 가
#   **리로드 전 옛 클래스**를 잡는다 -> UI 는 새 클래스에, 핫키는 옛 클래스(enabled=False)를 읽어 Shift+A 가 레이어 키를
#   **조용히** 건너뛰었다(v02.38 세션에서 툴을 다시 연 경우 재현). optionVar 는 클래스가 몇 벌이든 하나다.
#   settings 클래스 변수는 마지막 값을 보여 주는 거울로만 남긴다.
#
# 결정 사항 (2026-11-04 사용자):
#   1. -N 키 값 = 그 시점의 레이어 값 유지 (레이어 커브 평가값, 커브가 없으면 그 레이어 blend 입력(inputB)의 정적값)
#   2. 레이어가 없거나 오브젝트가 멤버가 아니면 경고하고 건너뜀 (레이어를 만들거나 멤버로 넣지 않는다)
#   3. -N 위치에 이미 키가 있으면 덮어쓴다 (setKeyframe 이 같은 시간의 값만 바꾼다)
#
# 값의 의미 (mayapy 실측):
#   - -N 키 : 레이어 커브에 **레이어 값 그대로** 쓴다 (_key_raw). `setKeyframe -animLayer -value` 는 additive 에서
#             값을 최종 합성값으로 받아 역산하므로 커브 노드에 직접 쓴다.
#   - Pose 키 : Pose Key 탭과 **같은 호출** `setKeyframe obj -at a -v val -animLayer L` -> 그 프레임의 **최종 값이 Pose 값**
#             (additive 면 마야가 레이어 값을 역산). 그래서 "원래 값 -> Pose 값" 으로 N 프레임 동안 바뀐다.
#
# 멤버 판정은 이름 비교가 아니라 plug 앞단 blend 사슬에 그 레이어의 blend 노드가 있는지로 한다
# (네임스페이스 · DAG 경로 · 짧은/긴 어트리뷰트 이름과 무관). 사슬 헬퍼는 LayerKeyManager 것을 그대로 쓴다.

import json

import maya.cmds as cmds

from .layer_key_manager import LayerKeyManager

OPTVAR_PREFIX = "JUN_A00110_holdLayer_"


class HoldLayerManager:

    settings = {
        "enabled": False,      # 추가 기능 On/Off
        "layer": "",           # 대상 animLayer 이름
        "offset": 10,          # N (프레임, int >= 1)
        "axis_values": {},     # Pose Key 탭에서 체크된 축 {"rx": 0.0, ...}
    }

    @classmethod
    def update(cls, **kw):
        """설정을 optionVar 에 쓴다(원본). settings 클래스 변수도 같이 맞춘다."""
        cls.settings.update(kw)
        pre = OPTVAR_PREFIX
        if "enabled" in kw:
            cmds.optionVar(intValue=(pre + "enabled", int(bool(kw["enabled"]))))
        if "layer" in kw:
            cmds.optionVar(stringValue=(pre + "layer", str(kw["layer"] or "")))
        if "offset" in kw:
            cmds.optionVar(intValue=(pre + "offset", int(kw["offset"])))
        if "axis_values" in kw:
            cmds.optionVar(stringValue=(pre + "axis_values", json.dumps(dict(kw["axis_values"] or {}))))

    @classmethod
    def load_settings(cls):
        """optionVar 에서 설정을 읽는다. 없는 키는 기본값."""
        pre = OPTVAR_PREFIX
        out = {"enabled": False, "layer": "", "offset": 10, "axis_values": {}}
        try:
            if cmds.optionVar(exists=pre + "enabled"):
                out["enabled"] = bool(cmds.optionVar(q=pre + "enabled"))
            if cmds.optionVar(exists=pre + "layer"):
                out["layer"] = str(cmds.optionVar(q=pre + "layer") or "")
            if cmds.optionVar(exists=pre + "offset"):
                out["offset"] = int(cmds.optionVar(q=pre + "offset"))
            if cmds.optionVar(exists=pre + "axis_values"):
                raw = json.loads(cmds.optionVar(q=pre + "axis_values") or "{}")
                out["axis_values"] = {str(k): float(v) for k, v in raw.items()}
        except (TypeError, ValueError):
            pass
        return out

    # --------------------------------------------------
    # 조회
    # --------------------------------------------------

    @staticmethod
    def list_layers():
        """BaseAnimation 을 뺀 animLayer 이름 목록 (씬 순서)."""
        root = LayerKeyManager.root_layer()
        return [l for l in (cmds.ls(type="animLayer") or []) if l != root]

    @staticmethod
    def _layer_node_for(plug, layer_nodes):
        """plug 의 blend 사슬에서 이 레이어의 (node, suffix). 멤버가 아니면 (None, None)."""
        for node, suffix in LayerKeyManager._blend_chain(plug):
            if node in layer_nodes:
                return node, suffix
        return None, None

    @staticmethod
    def _long_name(obj, attr):
        try:
            return cmds.attributeQuery(attr, node=obj, longName=True)
        except Exception:                                   # noqa: BLE001
            return None

    @staticmethod
    def _layer_value(plug, layer, node, suffix, t0, kind):
        """t0 시점의 '레이어 값'. 커브 > blend inputB 정적값 > 폴백(identity / 합성값)."""
        curve = LayerKeyManager.layer_curve(plug, layer)
        if curve:
            vals = cmds.keyframe(curve, q=True, eval=True, time=(t0, t0), valueChange=True) or []
            if vals:
                return float(vals[0])
        static = LayerKeyManager._static("{0}.inputB{1}".format(node, suffix))
        if static is not None:
            return static
        # 폴백 (계획서 4.3)
        if kind == "override":
            return float(cmds.getAttr(plug, time=t0))
        if cmds.nodeType(node) == "animBlendNodeAdditiveScale":
            try:
                if int(cmds.getAttr(layer + ".scaleAccumulationMode")) == LayerKeyManager.SCALE_MULTIPLY:
                    return 1.0
            except Exception:                               # noqa: BLE001
                pass
        return 0.0

    @staticmethod
    def _key_raw(obj, attr, layer, t, raw):
        """레이어 커브에 **레이어 값 그대로** 키 (덮어쓰기).

        `setKeyframe obj -animLayer L -value v` 는 additive 레이어에서 v 를 **최종(합성) 값**으로 받아
        레이어 값을 역산한다(mayapy 실측). 그래서 커브가 있으면 커브 노드에 직접 찍고, 없으면 만든 뒤
        그 키 값을 절대값으로 고친다. override 는 둘이 같지만 같은 경로로 처리한다.
        """
        plug = "{0}.{1}".format(obj, attr)
        curve = LayerKeyManager.layer_curve(plug, layer)
        if not curve:
            cmds.setKeyframe(obj, attribute=attr, time=t, animLayer=layer)
            curve = LayerKeyManager.layer_curve(plug, layer)
            if not curve:
                return False
        cmds.setKeyframe(curve, time=t, value=raw)
        cmds.keyframe(curve, edit=True, time=(t, t), valueChange=raw, absolute=True)
        return True

    # --------------------------------------------------
    # 실행
    # --------------------------------------------------

    @classmethod
    def apply(cls, objects=None, frame=None):
        """현재 프레임-N 에 '그 시점 레이어 값' 키, 현재 프레임에 Pose 값 키.

        undo 묶기는 호출부(HotkeyManager.run_hold)가 Hold 와 함께 한다.
        반환 (처리한 오브젝트 수, 메시지). 옵션이 꺼져 있으면 (0, "").
        """
        s = cls.load_settings()
        cls.settings.update(s)
        if not s.get("enabled"):
            return (0, "")

        sel = list(objects) if objects else (cmds.ls(sl=True) or [])
        sel = [o for o in sel if cmds.objExists(o)]
        if not sel:
            return (0, "[Warning] Layer Blend: no objects selected.")

        layer = (s.get("layer") or "").strip()
        root = LayerKeyManager.root_layer()
        if not layer:
            return (0, "[Warning] Layer Blend: no layer chosen (Hot Key > Main > Layer). Skipped.")
        if (not cmds.objExists(layer)
                or cmds.nodeType(layer) != "animLayer" or layer == root):
            return (0, "[Warning] Layer Blend: layer '{0}' not found. Skipped.".format(layer))

        try:
            locked = bool(cmds.animLayer(layer, q=True, lock=True))
        except Exception:                                   # noqa: BLE001
            locked = False
        if locked:
            return (0, "[Warning] Layer Blend: layer '{0}' is locked. Skipped.".format(layer))

        axis_values = dict(s.get("axis_values") or {})
        if not axis_values:
            return (0, "[Warning] Layer Blend: no Pose Key axis checked. Skipped.")

        try:
            n = max(1, int(s.get("offset", 10)))
        except (TypeError, ValueError):
            n = 10
        t1 = float(cmds.currentTime(q=True) if frame is None else frame)
        t0 = t1 - n

        layer_nodes = LayerKeyManager._layer_nodes(layer)
        kind = LayerKeyManager._layer_kind(layer, root)

        keyed = []
        skipped = []
        not_member_axes = set()

        for obj in sel:
            try:
                attrs = cmds.listAttr(obj, keyable=True, unlocked=True) or []
            except Exception:                               # noqa: BLE001
                attrs = []

            # 멤버 채널 : attr(긴 이름) -> (node, suffix)
            members = {}
            for attr in attrs:
                if "." in attr:
                    continue
                plug = "{0}.{1}".format(obj, attr)
                node, suffix = cls._layer_node_for(plug, layer_nodes)
                if node:
                    members[attr] = (node, suffix)

            if not members:
                skipped.append(obj)
                continue

            # Pose 축 -> 긴 이름 (멤버만)
            pose = []
            for short, val in axis_values.items():
                long_name = cls._long_name(obj, short)
                if long_name in members:
                    pose.append((long_name, float(val)))
                else:
                    not_member_axes.add(short)

            # 값을 먼저 전부 읽고 나서 키를 찍는다 (키를 찍으면 다른 채널 평가가 바뀔 수 있다)
            before = []
            for attr, (node, suffix) in members.items():
                plug = "{0}.{1}".format(obj, attr)
                before.append((attr, cls._layer_value(plug, layer, node, suffix, t0, kind)))

            for attr, val in before:
                cls._key_raw(obj, attr, layer, t0, val)
            for attr, val in pose:
                cmds.setKeyframe(obj, attribute=attr, time=t1, value=val, animLayer=layer)

            keyed.append(obj)

        def fmt(t):
            return "{0:g}".format(t)

        msg = "Layer Blend: {0} object(s) keyed on '{1}' (f{2} -> f{3}).".format(
            len(keyed), layer, fmt(t0), fmt(t1))
        try:
            if cmds.animLayer(layer, q=True, mute=True):
                msg += " (layer muted)"
        except Exception:                                   # noqa: BLE001
            pass
        if skipped:
            msg += " Skipped: {0} (not in layer).".format(LayerKeyManager._brief(skipped))
        if not_member_axes and keyed:
            msg += " Pose axes not in layer: {0}.".format(", ".join(sorted(not_member_axes)))
        if not keyed:
            msg = "[Warning] " + msg
        return (len(keyed), msg)
