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
# v02.41 - `use_current` (Key > Pose Key 의 `Use current values` 체크박스): 켜져 있으면 현재 프레임 키를 Pose 값 대신
#   **지금 그 채널의 현재 값**으로 찍는다(축 선택은 그대로 Pose Key 체크 축). 값은 run_hold 가 **Hold 전에** capture_current()
#   로 읽어 넘긴다 - Hold 가 커브를 바꾸면 키 없이 움직여 둔 값이 다시 평가돼 사라지기 때문이다.
#   찍는 방식은 Pose 키와 같은 obj 경로(`setKeyframe -animLayer -v`) -> 그 프레임의 최종 값이 지금 값 그대로 남는다.
#
# v02.42 - 대상은 **마야에서 지금 선택한 오브젝트만** (사용자 요구: 레이어에 든 다른 오브젝트에는 키가 가면 안 된다).
#   selected_objects() : `ls -sl -objectsOnly` 에서 animLayer · objectSet · character(세트에 setKeyframe 하면 멤버 전체에 키)를
#   뺀 노드만. run_hold 는 누른 순간의 선택을 한 번 읽어 capture_current / apply 에 같은 목록을 넘긴다.
#   키는 그 오브젝트의 plug(obj.attr)와 그 plug 를 구동하는 레이어 커브에만 쓴다. 메시지에 키를 찍은 오브젝트 이름을 보인다.
#
# v02.43 - **보기 게이트** `view_layer` (UI `Run only when viewing`, 기본 BaseAnimation): 지금 **보고 있는 레이어**가
#   정확히 그 레이어 하나일 때만 Layer Blend 가 돈다. AnimLayer1 을 보며 그 커브 키를 골라 Shift+A(= AnimLayer1 Hold)할 때
#   Layer Blend 가 끼어들지 않게 하려는 안전장치(사용자 요구). Hold 는 게이트와 무관하게 그대로 돈다.
#   보고 있는 레이어 = Animation Layer Editor 에서 **선택된** 레이어들(그래프 에디터 필터 Selected 가 보이는 것) ->
#   없으면 활성(preferred) 레이어 -> 그것도 없으면 루트(BaseAnimation). 여러 개를 같이 보고 있으면 통과 못 한다.
#   view_layer 저장값 "" = 루트 레이어(이름이 BaseAnimation 이 아니어도). 씬에 레이어가 하나도 없으면 게이트는 통과(루트 취급).
#
# v02.44 - `Use current values` 를 **축마다** (사용자 요구). 전역 use_current(bool) -> `current_axes`(축 목록, optionVar JSON).
#   Pose Key 행마다 `Current` 체크박스 - 켠 축만 현재 값, 나머지 축은 입력 값. capture_current 도 그 축만 읽는다.
#   옛 optionVar use_current=1 이 남아 있고 current_axes 가 없으면 체크된 축 전부를 current 로 옮겨 읽는다.
# v02.45 - 저장된 current_axes 가 없을 때의 기본 = DEFAULT_CURRENT_AXES (rotate Y · translate X · translate Z, 사용자 요구).
# v02.46 - **`Current` 를 켠 축은 축 체크가 꺼져 있어도 키를 찍는다** (키 축 = 체크 축 ∪ current 축, effective_axes).
#   v02.44~45 는 체크 축 ∩ current 만 current 로 다뤄, 기본값(체크 rx rz ty / current ry tx tz)에서 current 축이
#   하나도 안 찍혔다(사용자 보고: AnimLayer1 에 current 축 키가 없다).
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

# v02.45 Pose Key `Current` 기본으로 켜 둘 축 (저장값이 없을 때)
DEFAULT_CURRENT_AXES = ("ry", "tx", "tz")


class HoldLayerManager:

    settings = {
        "enabled": False,      # 추가 기능 On/Off
        "layer": "",           # 대상 animLayer 이름
        "offset": 10,          # N (프레임, int >= 1)
        "axis_values": {},     # Pose Key 탭에서 체크된 축 {"rx": 0.0, ...}
        "current_axes": list(DEFAULT_CURRENT_AXES),    # v02.44 현재 값으로 찍을 축 (Pose Key 행마다 `Current`). v02.41 전역 use_current 대체
        "view_layer": "",      # v02.43 이 레이어를 보고 있을 때만 동작. "" = 루트(BaseAnimation)
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
        if "current_axes" in kw:
            cmds.optionVar(stringValue=(pre + "current_axes", json.dumps(list(kw["current_axes"] or []))))
            if cmds.optionVar(exists=pre + "use_current"):      # v02.41 전역 플래그는 더 안 쓴다
                cmds.optionVar(remove=pre + "use_current")
        if "view_layer" in kw:
            cmds.optionVar(stringValue=(pre + "view_layer", str(kw["view_layer"] or "")))

    @classmethod
    def load_settings(cls):
        """optionVar 에서 설정을 읽는다. 없는 키는 기본값."""
        pre = OPTVAR_PREFIX
        out = {"enabled": False, "layer": "", "offset": 10, "axis_values": {},
               "current_axes": list(DEFAULT_CURRENT_AXES),
               "view_layer": ""}
        old_use_current = False
        try:
            if cmds.optionVar(exists=pre + "enabled"):
                out["enabled"] = bool(cmds.optionVar(q=pre + "enabled"))
            if cmds.optionVar(exists=pre + "layer"):
                out["layer"] = str(cmds.optionVar(q=pre + "layer") or "")
            if cmds.optionVar(exists=pre + "offset"):
                out["offset"] = int(cmds.optionVar(q=pre + "offset"))
            if cmds.optionVar(exists=pre + "view_layer"):
                out["view_layer"] = str(cmds.optionVar(q=pre + "view_layer") or "")
            if cmds.optionVar(exists=pre + "current_axes"):
                out["current_axes"] = [str(a) for a in json.loads(cmds.optionVar(q=pre + "current_axes") or "[]")]
            elif cmds.optionVar(exists=pre + "use_current"):
                old_use_current = bool(cmds.optionVar(q=pre + "use_current"))
            if cmds.optionVar(exists=pre + "axis_values"):
                raw = json.loads(cmds.optionVar(q=pre + "axis_values") or "{}")
                out["axis_values"] = {str(k): float(v) for k, v in raw.items()}
        except (TypeError, ValueError):
            pass
        if old_use_current:
            # v02.41 전역 Use current values 를 쓰던 설정 -> 체크된 축 전부 current
            out["current_axes"] = list(out["axis_values"])
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
    def viewed_layers():
        """지금 보고 있는 레이어 목록 : 에디터 선택 -> 없으면 활성(preferred) -> 없으면 [루트]. 레이어가 없으면 []."""
        layers = cmds.ls(type="animLayer") or []
        if not layers:
            return []

        def flagged(flag):
            out = []
            for layer in layers:
                try:
                    if cmds.animLayer(layer, q=True, **{flag: True}):
                        out.append(layer)
                except Exception:                           # noqa: BLE001
                    pass
            return out

        root = LayerKeyManager.root_layer()
        return flagged("selected") or flagged("preferred") or ([root] if root else [])

    @classmethod
    def view_gate(cls, view_layer=None):
        """(통과 여부, 메시지). view_layer "" / None = 루트. 레이어가 없는 씬은 통과."""
        if view_layer is None:
            view_layer = cls.load_settings().get("view_layer", "")
        viewed = cls.viewed_layers()
        if not viewed:
            return (True, "")
        root = LayerKeyManager.root_layer()
        want = view_layer or root
        if viewed == [want]:
            return (True, "")
        return (False, "Layer Blend: skipped - viewing {0} (runs only when viewing '{1}').".format(
            ", ".join("'{0}'".format(v) for v in viewed), want))

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

    # 선택에 섞여도 대상이 아닌 노드 타입 (세트 · 캐릭터는 setKeyframe 이 멤버 전체로 퍼진다)
    NON_TARGET_TYPES = ("animLayer", "objectSet", "character")

    @classmethod
    def selected_objects(cls, objects=None):
        """키를 찍을 오브젝트 = objects(명시) 또는 **지금 마야 선택**, 레이어 · 세트 · 캐릭터 노드 제외, 순서 유지 중복 제거."""
        src = list(objects) if objects else (cmds.ls(sl=True, objectsOnly=True) or [])
        out = []
        for obj in src:
            if not cmds.objExists(obj) or obj in out:
                continue
            try:
                if cmds.nodeType(obj) in cls.NON_TARGET_TYPES:
                    continue
            except Exception:                               # noqa: BLE001
                continue
            out.append(obj)
        return out

    @staticmethod
    def effective_axes(s):
        """키를 찍을 축 {축: 값} = 체크 축(axis_values) ∪ current 축(값 0.0 자리표시 - 지금 값으로 바뀐다), 순서 유지."""
        out = dict(s.get("axis_values") or {})
        for a in (s.get("current_axes") or []):
            out.setdefault(a, 0.0)
        return out

    @classmethod
    def capture_current(cls, objects=None):
        """current 축이 있으면 선택 오브젝트 x current 축의 **지금 값** {(obj, 축): float}. 없으면 None (v02.46 체크와 무관).

        run_hold 가 Hold **전에** 부른다. 읽을 수 없는 채널은 빠진다(apply 가 그때 다시 읽는다).
        """
        s = cls.load_settings()
        axes = list(dict.fromkeys(s.get("current_axes") or []))
        if not (s.get("enabled") and axes):
            return None
        if not cls.view_gate(s.get("view_layer", ""))[0]:
            return None
        sel = cls.selected_objects(objects)
        out = {}
        for obj in sel:
            for short in axes:
                try:
                    out[(obj, short)] = float(cmds.getAttr("{0}.{1}".format(obj, short)))
                except Exception:                           # noqa: BLE001
                    pass
        return out

    @classmethod
    def apply(cls, objects=None, frame=None, current_values=None):
        """현재 프레임-N 에 '그 시점 레이어 값' 키, 현재 프레임에 Pose 값 키.

        current 축(v02.44 축마다)은 현재 프레임 키를 Pose 값 대신 **지금 값**으로
        (current_values {(obj, 축): 값} 이 있으면 그것, 없으면 여기서 읽는다).

        undo 묶기는 호출부(HotkeyManager.run_hold)가 Hold 와 함께 한다.
        반환 (처리한 오브젝트 수, 메시지). 옵션이 꺼져 있으면 (0, "").
        """
        s = cls.load_settings()
        cls.settings.update(s)
        if not s.get("enabled"):
            return (0, "")

        # v02.43 보기 게이트 - 정한 레이어(기본 BaseAnimation)를 보고 있을 때만
        ok, gate_msg = cls.view_gate(s.get("view_layer", ""))
        if not ok:
            return (0, gate_msg)

        sel = cls.selected_objects(objects)
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

        axis_values = cls.effective_axes(s)    # v02.46 체크 축 ∪ current 축
        if not axis_values:
            return (0, "[Warning] Layer Blend: no Pose Key axis checked. Skipped.")

        try:
            n = max(1, int(s.get("offset", 10)))
        except (TypeError, ValueError):
            n = 10
        now = float(cmds.currentTime(q=True))
        t1 = now if frame is None else float(frame)
        t0 = t1 - n
        current_axes = set(s.get("current_axes") or []) & set(axis_values)
        current_values = current_values or {}

        def current_of(obj, short):
            if (obj, short) in current_values:
                return current_values[(obj, short)]
            plug = "{0}.{1}".format(obj, short)
            if t1 == now:
                return float(cmds.getAttr(plug))
            return float(cmds.getAttr(plug, time=t1))

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
                    pose.append((long_name, current_of(obj, short) if short in current_axes else float(val)))
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

        msg = "Layer Blend: {0} object(s) keyed on '{1}' (f{2} -> f{3}{4}){5}.".format(
            len(keyed), layer, fmt(t0), fmt(t1),
            ", current: " + ", ".join(a for a in axis_values if a in current_axes) if current_axes else "",
            ": " + LayerKeyManager._brief(keyed, limit=5) if keyed else "")
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
