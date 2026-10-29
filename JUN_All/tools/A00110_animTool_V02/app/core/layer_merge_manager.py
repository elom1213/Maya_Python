# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# A00110_animTool_V02 - Bake > Merge Layers : 애니메이션 레이어를 **프레임 구간 안에서만** 병합 (maya.cmds, UI 비의존)
#
# "레이어 a, b 가 [0, 1000] 에 키를 갖고 있을 때 [50, 300] 만 a + b => b (기존 레이어) 또는 a + b => c (새 레이어) 로
#  합친다. 합침은 마야 Merge Layers 와 같은 의미이고, 전후 컨트롤러의 월드 움직임은 같아야 한다."
#
# 계획서 : docs/plans/A00110_animTool_V02_layer_range_merge_plan.md (mayapy 실측 13/13 + 깨진 가정 11 개가 설계 근거)
#
# ## 마야 Merge Layers 의 본체 = bakeResults 한 줄
# performAnimLayerMerge.mel 의 animLayerMerge() 는 새 레이어를 만들고
#   bakeResults -destinationLayer Merged_Layer -resolveWithoutLayer a -resolveWithoutLayer b -time ":" <attrs>
# 로 "a, b 를 뺀 스택에서 같은 결과가 나오는 값" 을 굽고 소스를 지운다. 레이어 모드 · 누적 모드(쿼터니언 by-layer 포함) ·
# weight · 위 레이어의 가림을 전부 마야 C++ 가 푼다. 그래서 이 모듈은 **값을 다시 계산하지 않는다** - 같은 명령에
# `-time s:e -preserveOutsideKeys` 를 주고, 마야가 소스를 지우던 자리에서 **구간 안 기여만 없애고**(중화) **경계**를 지킨다.
#
# ## 세 경로
#   A  a + b => b (기존 레이어)   : b 커브에 경계 키 -> bake(dest b, rwl a b, 구간) -> b 에 없던 채널은 경계 identity 키 -> a 중화
#   B  a + b => c (새 레이어)     : 마야 Auto 규칙(override 하나라도 있으면 override, 누적 모드는 과반)으로 c 를 **가장 위 소스
#                                  바로 위**에 만들고 mute 한 채 bake -> c 의 구간 밖 기여 제거(additive: identity 키 / override:
#                                  weight 를 밖 0 안 1) -> a, b 중화
#   C  a + Base => Base          : `-destinationLayer BaseAnimation` 은 소스 커브를 **통째로 지우므로**(bake-to-base) 못 쓴다.
#                                  임시 additive(by-component · additive scale) 레이어를 **맨 아래**에 굽고 base'(f) = base(f) + c(f)
#                                  로 base 커브에 접은 뒤 지운다.
#
# ## 소스 중화 - "구간 안에서 이 레이어가 없는 것처럼"
#   additive : 커브마다 s-1 · e+1 에 `setKeyframe -insert` + `keyTangent fixed`(auto 탄젠트는 이웃 키에 반응한다) ->
#              `cutKey (s, e)` -> s 에 identity 키 `-ott step`, e 에 identity 키. identity = 0, 스케일이고
#              scaleAccumulationMode == Multiply(1) 이면 1. weight x identity = identity 라 weight 는 안 봐도 된다.
#   override : 값으로는 "없음" 을 표현할 수 없다(어떤 값이든 덮는다) -> `weight` 를 s-1:현재(step) · s:0(step) · e:0(step) ·
#              e+1:현재 로 계단 키. 레이어 전체에 걸리므로 "선택 오브젝트만" 과 양립하지 않는다(거부).
#              override 멤버는 **키가 없어도 정적 값으로 덮고 있으므로** 모든 멤버 plug 를 bake 에 넣는다(마야와 같음).
#
# ## 정확도 계약 (실측)
#   정수 프레임은 구간 안팎 전부 동일(1e-15) · 구간 밖은 반 프레임도 동일 · 구간 안 프레임 사이는 bake 보간이라 다르다
#   (마야 자체 Merge Layers 도 반 프레임 7.9e-4 다르다). Smart bake 는 근사(정수 프레임 7.9 차이) -> 기본 OFF + 경고.
#
# ## 실측으로 확인한 함정 (계획서 §4.2 + 구현 중 추가)
#   - 대상 기존 레이어의 weight 가 1 이 아니거나 애니메이션이면 틀린다(bakeResults 가 되돌려 나누지 않는다) -> 거부.
#   - 대상에 없던 채널의 새 커브는 키가 s..e 뿐이라 **끝값이 구간 밖으로 샌다** -> s-1 · e+1 identity 키.
#   - **override 기존 대상**: 멤버인데 키 없는 채널은 bake 뒤 정적 값(blend 노드 inputB)을 s-1 · e+1 에 키로 박아야 하고,
#     멤버가 **아니던** 채널은 밖에서 identity 가 없어(override) 구간 밖이 바뀐다 -> 새 레이어를 권하며 거부. (구현 중 실측)
#   - `setKeyframe(plug, animLayer=L, value=V)` 는 "최종값이 V" 가 되도록 **역산**한다 -> 커브 값은 전부 **커브 노드**에 쓴다.
#   - lock 레이어 편집 · 잠긴 plug 의 bake 는 **조용히 무시**된다 -> 레이어 lock 은 거부, 잠긴 plug 는 건너뛰고 경고.
#   - `animLayer -q -children root` 의 첫 원소가 **맨 아래**(먼저 평가). `moveLayerAfter X` = X 위, `moveLayerBefore X` = X 아래.
#   - `animLayer -q -attribute` 는 동명 노드를 `g1|ctl.translateX` 처럼 부분 경로로 준다 -> 오브젝트 비교는 `ls -long`.
#   - 키 하나 ≈ 0.22 ms (50 ctl x 300 plug x 251 f = 16.5 s, 마야 자체 Merge Layers 는 같은 씬 139 s) -> 진행 콜백.

import math
import time

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.core.maya_refresh import suspend_refresh

from .layer_key_manager import LayerKeyManager


class LayerMergeManager:
    """애니메이션 레이어를 [start, end] 구간 안에서만 병합한다 (마야 Merge Layers 의 구간판)."""

    TAG = "[Merge Layers]"

    DEFAULT_NEW_NAME = "Merged_Layer"
    TEMP_BASE_NAME = "JUN_tmpMergeToBase"

    # Verify : 병합 전후 채널 값을 [start - PAD, end + PAD] 정수 프레임에서 비교. 이 허용치를 넘으면 로그 경고.
    VERIFY_TOL = 1e-4
    VERIFY_PAD = 5

    # UI 가 진행 팝업을 띄울 기준 (plug x 샘플). 실측 0.22 ms/키 -> 약 1 초.
    PROGRESS_THRESHOLD = 4000

    # bakeResults 호출을 이 plug 수 단위로 나눠 진행률을 낸다(채널은 서로 독립이라 결과는 같다).
    BAKE_CHUNK_PLUGS = 32

    # enum (실측) : scaleAccumulationMode Additive(0):Multiply(1), rotationAccumulationMode By Component(0):By Layer(1)
    SCALE_ADDITIVE, SCALE_MULTIPLY = 0, 1
    ROT_BY_COMPONENT, ROT_BY_LAYER = 0, 1

    DEFAULT_SMART_TOLERANCE = 0.5

    # ==================================================
    # 조회 (UI 목록 채우기)
    # ==================================================

    @staticmethod
    def root_layer():
        return LayerKeyManager.root_layer()

    @staticmethod
    def stack(root=None):
        """root 의 직계 자식 레이어를 **맨 아래부터**(= 평가 순서, `children[0]` 이 바닥)."""
        root = root or LayerMergeManager.root_layer()
        if not root:
            return []
        return list(cmds.animLayer(root, q=True, children=True) or [])

    @staticmethod
    def layer_info(layer, root=None):
        """레이어 하나의 상태 사전 (UI 태그 · 검사 공용)."""
        root = root or LayerMergeManager.root_layer()
        is_root = (layer == root)

        def q(flag):
            try:
                return bool(cmds.animLayer(layer, q=True, **{flag: True}))
            except Exception:
                return False

        info = {
            "name": layer,
            "base": is_root,
            "override": (not is_root) and q("override"),
            "locked": q("lock"),
            "muted": (not is_root) and q("mute"),
            "solo": (not is_root) and q("solo"),
            "selected": q("selected"),
            "children": [] if is_root else list(cmds.animLayer(layer, q=True, children=True) or []),
            "parent": None if is_root else cmds.animLayer(layer, q=True, parent=True),
            "weight": 1.0,
            "weight_animated": False,
            "referenced": False,
            "scale_mode": LayerMergeManager.SCALE_MULTIPLY,
            "rot_mode": LayerMergeManager.ROT_BY_COMPONENT,
        }
        if not is_root:
            try:
                info["weight"] = float(cmds.getAttr(layer + ".weight"))
                info["weight_animated"] = bool(cmds.listConnections(
                    layer + ".weight", source=True, destination=False))
                info["scale_mode"] = int(cmds.getAttr(layer + ".scaleAccumulationMode"))
                info["rot_mode"] = int(cmds.getAttr(layer + ".rotationAccumulationMode"))
            except Exception:
                pass
        try:
            info["referenced"] = bool(cmds.referenceQuery(layer, isNodeReferenced=True))
        except Exception:
            pass
        info["mode"] = "base" if is_root else ("override" if info["override"] else "additive")
        return info

    @staticmethod
    def list_layers_stack():
        """(스택 순서 **맨 위부터** 의 layer_info 목록 + 마지막에 BaseAnimation, 에디터에서 선택된 이름들).

        레이어가 없으면 ([], []). 자식 레이어는 그 부모 줄의 `children` 으로만 보인다(v1 은 root 직계만 병합).
        선택 여부는 전역 질의가 없어 레이어마다 묻는다(animlayer-no-global-selected-query).
        """
        root = LayerMergeManager.root_layer()
        if not root:
            return [], []
        rows = [LayerMergeManager.layer_info(l, root)
                for l in reversed(LayerMergeManager.stack(root))]
        rows.append(LayerMergeManager.layer_info(root, root))
        selected = [r["name"] for r in rows if r["selected"]]
        return rows, selected

    @staticmethod
    def row_label(info):
        """체크 목록 한 줄 : `a    override  w 1.00  [muted]`."""
        if info["base"]:
            return "{0}    base".format(info["name"])
        tags = []
        if info["weight_animated"]:
            tags.append("animated weight")
        if info["locked"]:
            tags.append("locked")
        if info["muted"]:
            tags.append("muted")
        if info["solo"]:
            tags.append("solo")
        if info["children"]:
            tags.append("{0} child layer(s)".format(len(info["children"])))
        text = "{0}    {1}  w {2:.2f}".format(info["name"], info["mode"], info["weight"])
        if tags:
            text += "  [" + ", ".join(tags) + "]"
        return text

    @staticmethod
    def auto_result(sources):
        """마야 Auto 규칙으로 새 레이어의 (override?, scale_mode, rot_mode).

        performAnimLayerMerge.mel : 소스 중 override 가 하나라도 있으면 override. 누적 모드는 과반
        (`total*2 >= n ? 1 : 0` - 동률이면 1 = Multiply / By Layer).
        """
        infos = [LayerMergeManager.layer_info(l) for l in (sources or []) if cmds.objExists(l)]
        infos = [i for i in infos if not i["base"]]
        n = len(infos)
        if not n:
            return (False, LayerMergeManager.SCALE_MULTIPLY, LayerMergeManager.ROT_BY_COMPONENT)
        override = any(i["override"] for i in infos)
        scale_total = sum(1 for i in infos if i["scale_mode"] == 1)
        rot_total = sum(1 for i in infos if i["rot_mode"] == 1)
        return (override, 1 if scale_total * 2 >= n else 0, 1 if rot_total * 2 >= n else 0)

    @staticmethod
    def member_plugs(layer):
        try:
            return list(cmds.animLayer(layer, q=True, attribute=True) or [])
        except Exception:
            return []

    @staticmethod
    def source_key_range(sources):
        """소스 레이어 커브들의 전체 키 범위 (min, max) 정수. 키가 없으면 None. (Start/End 를 비웠을 때의 기본값)"""
        root = LayerMergeManager.root_layer()
        lo, hi = None, None
        for layer in (sources or []):
            if not cmds.objExists(layer):
                continue
            for plug in LayerMergeManager.member_plugs(layer):
                curve = LayerKeyManager.layer_curve(plug, layer, root)
                if not curve:
                    continue
                times = cmds.keyframe(curve, q=True, timeChange=True) or []
                if not times:
                    continue
                lo = min(times) if lo is None else min(lo, min(times))
                hi = max(times) if hi is None else max(hi, max(times))
        if lo is None:
            return None
        return (int(math.floor(lo)), int(math.ceil(hi)))

    # ==================================================
    # 대상 채널
    # ==================================================

    @staticmethod
    def _long_node(name):
        try:
            found = cmds.ls(name, long=True) or []
        except Exception:
            found = []
        return found[0] if found else name

    @staticmethod
    def merge_plugs(layers, objects=None, root=None, complete_rotation=False):
        """병합에 들어갈 plug 목록 (중복 없이, 레이어 순서대로).

        additive 레이어는 **커브가 있는 멤버 + 정적 값이 identity 가 아닌 멤버**(레이어가 활성일 때 setAttr 로 넣은 값은
        키 없이도 더해진다), override 레이어는 **모든 멤버**(키 없는 멤버도 정적 값으로 덮는다). BaseAnimation 은 건너뛴다
        (소스로서 중화하지 않는다). `objects` 가 있으면 그 노드의 plug 만(긴 이름으로 비교).
        `complete_rotation` 이면 회전 채널이 하나라도 있는 노드는 rotateX/Y/Z **셋 다** 넣는다 - by-layer(쿼터니언) 누적은
        세 채널을 한 회전으로 풀기 때문에 하나가 빠지면 bake 가 맞출 수 없다(실측: 새 by-layer 레이어에서 2.0 차이).

        Returns:
            (plugs, static_override, static_additive)
            static_override = {override layer: [키 없는 멤버 plug, ...]}
            static_additive = {additive layer: {키 없는 멤버 plug: 정적 값}}  (identity 가 아닌 것만)
        """
        root = root or LayerMergeManager.root_layer()
        wanted = None
        if objects:
            wanted = set(LayerMergeManager._long_node(o) for o in objects)
        plugs, seen = [], set()
        static_ov, static_add = {}, {}
        for layer in layers:
            if layer == root:
                continue
            override = bool(cmds.animLayer(layer, q=True, override=True))
            for plug in LayerMergeManager.member_plugs(layer):
                if wanted is not None:
                    node = plug.split(".", 1)[0]
                    if LayerMergeManager._long_node(node) not in wanted:
                        continue
                has_curve = LayerKeyManager.layer_curve(plug, layer, root) is not None
                if not has_curve:
                    if override:
                        static_ov.setdefault(layer, []).append(plug)
                    else:
                        value = LayerMergeManager._blend_input_value(layer, plug, numeric_only=True)
                        if value is None or abs(value - LayerMergeManager._identity(plug, layer)) <= 1e-9:
                            continue
                        static_add.setdefault(layer, {})[plug] = value
                if plug in seen:
                    continue
                seen.add(plug)
                plugs.append(plug)
        if complete_rotation:
            nodes = []
            for p in plugs:
                node, attr = p.split(".", 1)
                if attr in ("rotateX", "rotateY", "rotateZ") and node not in nodes:
                    nodes.append(node)
            for node in nodes:
                for attr in ("rotateX", "rotateY", "rotateZ"):
                    p = node + "." + attr
                    if p not in seen and cmds.objExists(p):
                        seen.add(p)
                        plugs.append(p)
        return plugs, static_ov, static_add

    @staticmethod
    def _blend_input_plug(layer, plug):
        """이 레이어가 plug 에 대해 갖는 blend 노드의 입력(inputB[X]) plug. 레이어가 그 plug 의 멤버가 아니면 None.

        plug <- bnTop.output[X] <- bnTop.inputA[X] <- bnNext.output[X] ... 사슬을 내려가며 이 레이어의 blend 노드를 찾는다
        (`animLayer -q -blendNodes`). 커브 없는 멤버의 정적 값이 여기(inputB) 에 있다.
        """
        try:
            nodes = set(cmds.animLayer(layer, q=True, blendNodes=True) or [])
        except Exception:
            nodes = set()
        if not nodes:
            return None
        cur = plug
        for _ in range(128):
            srcs = cmds.listConnections(cur, source=True, destination=False, plugs=True,
                                        skipConversionNodes=True) or []
            if not srcs:
                return None
            node, attr = srcs[0].split(".", 1)
            if not cmds.nodeType(node).startswith("animBlendNode") or not attr.startswith("output"):
                return None
            suffix = attr[len("output"):]
            if node in nodes:
                return node + ".inputB" + suffix
            cur = node + ".inputA" + suffix
        return None

    @staticmethod
    def _blend_input_value(layer, plug, numeric_only=False):
        """커브 없는 멤버가 레이어에 들고 있는 정적 값. 못 찾으면 None.

        numeric_only : 더하기 노드(animBlendNodeAdditive*)만. visibility 같은 Boolean / Enum 블렌드는 identity 가 없어
                       정적 감지에서 뺀다(마야도 그런 채널은 값 그대로 굽는다).
        """
        ib = LayerMergeManager._blend_input_plug(layer, plug)
        if not ib:
            return None
        if numeric_only and not cmds.nodeType(ib.split(".", 1)[0]).startswith("animBlendNodeAdditive"):
            return None
        try:
            return float(cmds.getAttr(ib))
        except Exception:
            return None

    # ==================================================
    # 검사
    # ==================================================

    @staticmethod
    def validate(sources, target, start, end, objects=None, sample_by=1.0):
        """실행 가능 여부. (error | None, ctx). ctx 는 merge_range 가 그대로 쓰는 재료.

        sources : 병합할 레이어 이름들(대상 기존 레이어를 포함해도, 안 해도 된다 - 대상은 늘 bake 의 rwl 에 들어간다).
        target  : 기존 레이어 이름(BaseAnimation 포함) 또는 None(새 레이어).
        """
        TAG = LayerMergeManager.TAG
        warnings = []
        ctx = {"warnings": warnings}

        root = LayerMergeManager.root_layer()
        if not root:
            return ("{0} Skipped : no animation layer in the scene.".format(TAG), ctx)
        ctx["root"] = root

        layers = []
        for l in (sources or []):
            if l and l not in layers:
                layers.append(l)
        if target and target not in layers:
            layers.append(target)
        if not layers:
            return ("{0} Skipped : check at least one layer to merge.".format(TAG), ctx)

        for l in layers:
            if not cmds.objExists(l) or cmds.nodeType(l) != "animLayer":
                return ("{0} Skipped : '{1}' is not an animation layer (gone?). Press Refresh."
                        .format(TAG, l), ctx)

        try:
            start, end = int(start), int(end)
        except (TypeError, ValueError):
            return ("{0} Skipped : Start / End must be integers.".format(TAG), ctx)
        if start > end:
            return ("{0} Skipped : Start ({1}) is greater than End ({2}).".format(TAG, start, end), ctx)
        try:
            sample_by = float(sample_by)
        except (TypeError, ValueError):
            sample_by = 0.0
        if sample_by <= 0.0:
            return ("{0} Skipped : Sample by must be greater than 0.".format(TAG), ctx)
        ctx["start"], ctx["end"], ctx["sample_by"] = start, end, sample_by

        # ---- 스택 순서 (맨 아래부터). Base 는 맨 앞.
        order = LayerMergeManager.stack(root)
        infos = dict((l, LayerMergeManager.layer_info(l, root)) for l in layers)

        def index_of(l):
            return -1 if l == root else (order.index(l) if l in order else 10 ** 6)

        layers.sort(key=index_of)
        ctx["sources"] = layers
        ctx["infos"] = infos

        neutralize = [l for l in layers if l != target and l != root]
        ctx["neutralize"] = neutralize

        if root in layers and target != root:
            return ("{0} Skipped : BaseAnimation can only be merged into itself - set Result to "
                    "'Into existing layer' = BaseAnimation (Base -> new layer is not supported yet)."
                    .format(TAG), ctx)
        if target is not None and not neutralize:
            return ("{0} Skipped : nothing to merge into '{1}' - check at least one other layer."
                    .format(TAG, target), ctx)

        for l in layers:
            info = infos[l]
            if info["referenced"]:
                return ("{0} Skipped : '{1}' is a referenced layer (Maya refuses to merge those too)."
                        .format(TAG, l), ctx)
            if info["locked"]:
                return ("{0} Skipped : '{1}' is locked - curve edits on a locked layer are silently "
                        "ignored. Unlock it first.".format(TAG, l), ctx)
            if l == root:
                continue
            if info["muted"]:
                return ("{0} Skipped : '{1}' is muted - a muted layer is not part of the result, so "
                        "there is nothing to merge. Unmute it first.".format(TAG, l), ctx)
            if info["parent"] != root:
                return ("{0} Skipped : '{1}' is a child layer (parent '{2}'). Only top-level layers "
                        "can be merged in this version.".format(TAG, l, info["parent"]), ctx)
            if info["children"]:
                return ("{0} Skipped : '{1}' has child layers ({2}). Merge or remove the children first."
                        .format(TAG, l, ", ".join(info["children"])), ctx)

        soloed = [l for l in (cmds.ls(type="animLayer") or [])
                  if l != root and cmds.getAttr(l + ".solo")]
        if soloed:
            return ("{0} Skipped : Solo is on ({1}). Turn solo off first - it changes what the stack "
                    "evaluates to.".format(TAG, ", ".join(soloed)), ctx)

        # ---- 경로
        if target is None:
            path = "new"
        elif target == root:
            path = "base"
        else:
            path = "existing"
            tinfo = infos[target]
            if tinfo["weight_animated"] or abs(tinfo["weight"] - 1.0) > 1e-9:
                return ("{0} Skipped : target layer '{1}' weight is {2} - it must be 1.0 and not "
                        "animated (bakeResults does not divide the weight back out; Maya always bakes "
                        "into a fresh weight-1 layer). Merge into a new layer instead.".format(
                            TAG, target, "animated" if tinfo["weight_animated"]
                            else "{0:g}".format(tinfo["weight"])), ctx)
        ctx["path"] = path
        ctx["target"] = target

        # ---- plug 집합 : 중화되는 소스들의 합집합 (대상 자신의 채널은 다시 굽지 않는다)
        if objects:
            ov = [l for l in neutralize if infos[l]["override"]]
            if ov:
                return ("{0} Skipped : 'Selected objects only' cannot be combined with an override "
                        "source ({1}) - its weight gates the whole layer.".format(TAG, ", ".join(ov)),
                        ctx)
        # by-layer(쿼터니언) 회전이 끼면 rotateX/Y/Z 를 세트로 다룬다.
        by_layer = any(infos[l]["rot_mode"] == LayerMergeManager.ROT_BY_LAYER for l in neutralize)
        if path == "existing":
            by_layer = by_layer or infos[target]["rot_mode"] == LayerMergeManager.ROT_BY_LAYER
        elif path == "new":
            by_layer = by_layer or LayerMergeManager.auto_result(neutralize)[2] == LayerMergeManager.ROT_BY_LAYER
        plugs, static, static_add = LayerMergeManager.merge_plugs(neutralize, objects, root, by_layer)
        if not plugs:
            if objects:
                return ("{0} Skipped : the selected objects have no keyed channels on {1}."
                        .format(TAG, ", ".join(neutralize)), ctx)
            return ("{0} Skipped : no keyed channels on {1}.".format(TAG, ", ".join(neutralize)), ctx)

        locked = [p for p in plugs if LayerMergeManager._plug_locked(p)]
        if locked:
            plugs = [p for p in plugs if p not in locked]
            warnings.append("Skipped locked channel(s) (bakeResults ignores them): {0}.".format(
                LayerMergeManager._brief(locked)))
            if not plugs:
                return ("{0} Skipped : every channel is locked.".format(TAG), ctx)
        ctx["plugs"] = plugs
        ctx["static_sources"] = static
        ctx["static_additive"] = static_add

        for l, ps in static.items():
            warnings.append("'{0}' (override) : {1} member channel(s) without keys baked as static "
                            "override values (same as Maya): {2}.".format(
                                l, len(ps), LayerMergeManager._brief(ps)))
        for l, pv in static_add.items():
            warnings.append("'{0}' (additive) : {1} member channel(s) without keys hold a non-zero "
                            "value - merged too, and keyed on the layer to hold it outside the range: "
                            "{2}.".format(l, len(pv), LayerMergeManager._brief(list(pv))))

        # ---- override 기존 대상 : 멤버가 아니던 채널은 밖에서 identity 가 없다
        ctx["dest_static"] = []
        if path == "existing" and infos[target]["override"]:
            members = set(LayerMergeManager.member_plugs(target))
            new_members = [p for p in plugs if p not in members]
            if new_members:
                return ("{0} Skipped : target '{1}' is an override layer and the sources key channels "
                        "it does not have ({2}) - an override layer cannot be transparent outside the "
                        "range on those. Merge into a new layer instead.".format(
                            TAG, target, LayerMergeManager._brief(new_members)), ctx)
            ctx["dest_static"] = [p for p in plugs
                                  if LayerKeyManager.layer_curve(p, target, root) is None]

        # ---- 경고 : 위에서 같은 채널을 덮는 비병합 override 레이어 (마야도 같은 빈틈)
        if path == "base":
            above = order
        elif path == "existing":
            above = order[order.index(target) + 1:]
        else:
            top_src = max(neutralize, key=index_of)
            above = order[order.index(top_src) + 1:]
        plug_set = set(plugs)
        for l in above:
            if l in layers:
                continue
            try:
                if not cmds.animLayer(l, q=True, override=True) or cmds.getAttr(l + ".mute"):
                    continue
            except Exception:
                continue
            hit = [p for p in LayerMergeManager.member_plugs(l) if p in plug_set]
            if hit:
                warnings.append("Warning : override layer '{0}' above the result masks {1} merged "
                                "channel(s) ({2}) - the baked values there are arbitrary (Maya's merge "
                                "has the same gap). Mute it or merge it too.".format(
                                    l, len(hit), LayerMergeManager._brief(hit)))
        return (None, ctx)

    # ==================================================
    # 메인 동작
    # ==================================================

    @staticmethod
    def merge_range(sources, target, start, end, sample_by=1.0, smart=False,
                    smart_tolerance=DEFAULT_SMART_TOLERANCE, objects=None, new_name=None,
                    verify=True, select_result=True, progress=None):
        """`sources` 를 [start, end] 안에서만 `target` 으로 병합한다.

        Args:
            sources        : 레이어 이름들. 기존 레이어가 대상이면 그 레이어를 포함해도 안 해도 된다.
            target         : 기존 레이어 이름(BaseAnimation 가능) 또는 None(새 레이어).
            start, end     : 정수 구간(양 끝 포함). 구간 밖은 손대지 않는다.
            sample_by      : bakeResults -sampleBy (기본 1.0 = 정수 프레임마다).
            smart          : bakeResults -smart. **근사** - 결과가 원본과 허용치 안에서만 같다. 기본 OFF.
            smart_tolerance: smart 허용치.
            objects        : 이 노드들의 채널만 병합(None = 소스의 모든 채널). override 소스와 함께 쓸 수 없다.
            new_name       : 새 레이어 이름(target None 일 때). 비면 'Merged_Layer'. 중복이면 마야가 번호를 붙인다.
            verify         : 병합 전후 채널 값을 [start-5, end+5] 정수 프레임에서 비교해 최대 편차를 로그에.
            select_result  : 끝나면 결과 레이어만 에디터에서 선택(마야 Merge Layers 관례).
            progress       : progress(done, total, message=None) 콜백.

        Returns:
            (merged_channel_count, msg)  거부되면 (0, "[Merge Layers] Skipped : ...").
        """
        error, ctx = LayerMergeManager.validate(sources, target, start, end, objects, sample_by)
        if error:
            return (0, " ".join([error] + ctx.get("warnings", [])))

        root, plugs = ctx["root"], ctx["plugs"]
        start, end, sample_by = ctx["start"], ctx["end"], ctx["sample_by"]
        path = ctx["path"]
        samples = int(round((end - start) / sample_by)) + 1
        objs = len(set(p.split(".", 1)[0] for p in plugs))

        # 진행 단위 : bake 키 1 = 1. verify 는 getAttr 라 싸다 - 프레임 x plug x 0.1 로 친다. base 접기는 키마다 setKeyframe.
        bake_units = len(plugs) * samples
        verify_units = int(len(plugs) * (end - start + 1 + 2 * LayerMergeManager.VERIFY_PAD) * 0.1) if verify else 0
        fold_units = bake_units if path == "base" else 0
        total = bake_units + 2 * verify_units + fold_units
        done = [0]

        def report(message=None):
            if progress:
                progress(min(done[0], total), total, message)

        t0 = time.time()
        saved_time = cmds.currentTime(q=True)
        used_smart = [bool(smart)]
        before = after = None
        result = None

        with undo_chunk(), suspend_refresh():
            try:
                if verify:
                    before = LayerMergeManager._sample(
                        plugs, start - LayerMergeManager.VERIFY_PAD, end + LayerMergeManager.VERIFY_PAD)
                    done[0] += verify_units
                    report("Sampling before")

                bake = dict(start=start, end=end, sample_by=sample_by, smart=smart,
                            smart_tol=smart_tolerance, used_smart=used_smart, done=done, report=report)
                if path == "new":
                    result = LayerMergeManager._merge_to_new(ctx, new_name, bake)
                elif path == "base":
                    result = LayerMergeManager._merge_to_base(ctx, bake)
                else:
                    result = LayerMergeManager._merge_to_existing(ctx, bake)

                for layer in ctx["neutralize"]:
                    LayerMergeManager._neutralize(layer, plugs, start, end, root,
                                                  ctx.get("static_additive", {}).get(layer))

                if select_result and result and result != root:
                    LayerMergeManager._select_only(result)

                if verify:
                    report("Verifying")
                    after = LayerMergeManager._sample(
                        plugs, start - LayerMergeManager.VERIFY_PAD, end + LayerMergeManager.VERIFY_PAD)
                    done[0] += verify_units
                report("Done")
            finally:
                try:
                    cmds.currentTime(saved_time)
                except Exception:
                    pass

        elapsed = time.time() - t0

        # ---- 로그
        srcs = " + ".join(ctx["neutralize"])
        if path == "new":
            override, _s, _r = LayerMergeManager.auto_result(ctx["neutralize"])
            dest_txt = "new layer '{0}' ({1})".format(result, "override" if override else "additive")
        elif path == "base":
            dest_txt = "BaseAnimation"
        else:
            dest_txt = "'{0}' ({1})".format(target, ctx["infos"][target]["mode"])
        rng = "frames {0}-{1} ({2} samples{3})".format(
            start, end, samples, "" if sample_by == 1.0 else ", every {0:g}f".format(sample_by))
        msg = "{0} {1} -> {2} : {3} channel(s) on {4} object(s), {5}, {6:.1f}s.".format(
            LayerMergeManager.TAG, srcs, dest_txt, len(plugs), objs, rng, elapsed)
        if path == "new":
            msg += " Placed just above '{0}'.".format(ctx["neutralize"][-1])
        if verify and before is not None and after is not None:
            dev, frame, plug = LayerMergeManager._compare(before, after, plugs)
            if dev > LayerMergeManager.VERIFY_TOL:
                msg += (" [Warning] Verified: max deviation {0:.3g} @ f{1} ({2}) - the result does NOT "
                        "match the original on integer frames (masked by an override above? smart "
                        "bake?). Undo if that is not what you want.".format(dev, frame, plug))
            else:
                msg += " Verified: max deviation {0:.1e} @ f{1} ({2}).".format(dev, frame, plug)
        if smart:
            if used_smart[0]:
                msg += (" Warning : Smart bake is on (tol {0:g}) - the result matches the original only "
                        "within that tolerance.".format(smart_tolerance))
            else:
                msg += " (Smart bake unsupported in this Maya - baked every sample instead.)"
        if ctx["warnings"]:
            msg += " " + " ".join(ctx["warnings"])
        msg += " One undo step."
        return (len(plugs), msg)

    # ==================================================
    # 경로 A : 기존 레이어
    # ==================================================

    @staticmethod
    def _merge_to_existing(ctx, bake):
        root, plugs, dest = ctx["root"], ctx["plugs"], ctx["target"]
        start, end = bake["start"], bake["end"]
        override = ctx["infos"][dest]["override"]

        had = {}
        for p in plugs:
            had[p] = LayerKeyManager.layer_curve(p, dest, root)

        # 대상의 키 없는 멤버 : bake 뒤 구간 밖에 되돌려 놓을 정적 값을 **bake 전에** 읽는다
        # (bake 가 inputB 에 커브를 붙이면 그 뒤로는 커브 값이 읽힌다).
        static = {}
        if override and ctx["dest_static"]:
            static = LayerMergeManager._static_values(ctx["dest_static"], keep=dest, root=root)
        elif not override:
            for p, curve in had.items():
                if curve:
                    continue
                value = LayerMergeManager._blend_input_value(dest, p, numeric_only=True)
                if value is not None:
                    static[p] = value

        for p, curve in had.items():
            if curve:
                LayerMergeManager._insert_fixed(curve, start - 1)
                LayerMergeManager._insert_fixed(curve, end + 1)

        LayerMergeManager._bake(dest, ctx["sources"], plugs, bake)

        for p in plugs:
            if had[p]:
                continue
            curve = LayerKeyManager.layer_curve(p, dest, root)
            if not curve:
                continue
            if override:
                if p not in static:
                    continue
                value = static[p]
            else:
                # 대상이 이미 멤버였다면 커브 없이 들고 있던 정적 값(보통 identity, 아닐 수도 있다)을 밖에 되돌린다.
                value = static.get(p, LayerMergeManager._identity(p, dest))
            cmds.setKeyframe(curve, time=(start - 1, start - 1), value=value)
            cmds.setKeyframe(curve, time=(end + 1, end + 1), value=value)
        return dest

    # ==================================================
    # 경로 B : 새 레이어
    # ==================================================

    @staticmethod
    def _merge_to_new(ctx, new_name, bake):
        root, plugs, srcs = ctx["root"], ctx["plugs"], ctx["neutralize"]
        start, end = bake["start"], bake["end"]
        override, scale_mode, rot_mode = LayerMergeManager.auto_result(srcs)

        name = (new_name or "").strip() or LayerMergeManager.DEFAULT_NEW_NAME
        layer = cmds.animLayer(name, override=override)
        cmds.setAttr(layer + ".scaleAccumulationMode", scale_mode)
        cmds.setAttr(layer + ".rotationAccumulationMode", rot_mode)
        cmds.animLayer(layer, e=True, parent=root)
        cmds.animLayer(layer, e=True, moveLayerAfter=srcs[-1])      # 가장 위 소스 바로 위
        for p in plugs:
            cmds.animLayer(layer, e=True, attribute=p, addRelatedKG=False)

        # override 멤버는 들어가는 순간 정적 값으로 덮는다 -> bake 가 끝날 때까지 mute (마야와 같음)
        cmds.animLayer(layer, e=True, mute=True)
        try:
            LayerMergeManager._bake(layer, srcs, plugs, bake)
        finally:
            cmds.animLayer(layer, e=True, mute=False)

        if override:
            LayerMergeManager._gate_weight(layer, start, end, inside=1.0, outside=0.0)
        else:
            for p in plugs:
                curve = LayerKeyManager.layer_curve(p, layer, root)
                if not curve:
                    continue
                idv = LayerMergeManager._identity(p, layer)
                cmds.setKeyframe(curve, time=(start - 1, start - 1), value=idv)
                cmds.setKeyframe(curve, time=(end + 1, end + 1), value=idv)
        return layer

    # ==================================================
    # 경로 C : BaseAnimation
    # ==================================================

    @staticmethod
    def _merge_to_base(ctx, bake):
        root, plugs, srcs = ctx["root"], ctx["plugs"], ctx["neutralize"]
        start, end = bake["start"], bake["end"]

        # base 에 커브가 없는 plug 의 정적 값 (모든 레이어를 뮤트하고 읽는다)
        base_curves = dict((p, LayerKeyManager.layer_curve(p, root, root)) for p in plugs)
        static = LayerMergeManager._static_values(
            [p for p, c in base_curves.items() if c is None], keep=None, root=root)

        # 임시 additive 레이어를 맨 아래(= base 바로 위)에. by-component · additive scale 이라야 단순 덧셈으로 접힌다.
        tmp = cmds.animLayer(LayerMergeManager.TEMP_BASE_NAME)
        cmds.setAttr(tmp + ".scaleAccumulationMode", LayerMergeManager.SCALE_ADDITIVE)
        cmds.setAttr(tmp + ".rotationAccumulationMode", LayerMergeManager.ROT_BY_COMPONENT)
        cmds.animLayer(tmp, e=True, parent=root)
        bottom = LayerMergeManager.stack(root)[0]
        if bottom != tmp:
            cmds.animLayer(tmp, e=True, moveLayerBefore=bottom)
        for p in plugs:
            cmds.animLayer(tmp, e=True, attribute=p, addRelatedKG=False)
        cmds.animLayer(tmp, e=True, mute=True)
        try:
            LayerMergeManager._bake(tmp, srcs, plugs, bake)   # Base 는 rwl 에 넣지 않는다

            # ---- 접기 : base'(f) = base(f) + tmp(f). 값은 자르기 **전에** 떠 둔다.
            for p in plugs:
                tcurve = LayerKeyManager.layer_curve(p, tmp, root)
                if not tcurve:
                    continue
                frames = [t for t in (cmds.keyframe(tcurve, q=True, timeChange=True) or [])
                          if start - 1e-6 <= t <= end + 1e-6]
                if not frames:
                    continue
                add = LayerMergeManager._evals(tcurve, frames)
                bcurve = base_curves[p]
                if bcurve is None:
                    # 정적 base : 커브는 setKeyframe(plug, animLayer=root) 로 만들고, 값은 커브 노드에 직접 쓴다(역산 금지).
                    cmds.setKeyframe(p, animLayer=root, time=(start - 1, start - 1))
                    bcurve = LayerKeyManager.layer_curve(p, root, root)
                    if not bcurve:
                        continue
                    base0 = static.get(p, 0.0)
                    cmds.setKeyframe(bcurve, time=(start - 1, start - 1), value=base0)
                    cmds.setKeyframe(bcurve, time=(end + 1, end + 1), value=base0)
                    values = [base0 + a for a in add]
                else:
                    base_vals = LayerMergeManager._evals(bcurve, frames)
                    values = [b + a for b, a in zip(base_vals, add)]
                    LayerMergeManager._insert_fixed(bcurve, start - 1)
                    LayerMergeManager._insert_fixed(bcurve, end + 1)
                    cmds.cutKey(bcurve, time=(start, end), clear=True)
                for f, v in zip(frames, values):
                    cmds.setKeyframe(bcurve, time=(f, f), value=v)
                bake["done"][0] += len(frames)
                bake["report"]("Folding into Base : {0}".format(p))
        finally:
            if cmds.objExists(tmp):
                cmds.delete(tmp)
        return root

    # ==================================================
    # 공용 조각
    # ==================================================

    @staticmethod
    def _bake(dest, rwl, plugs, bake):
        """마야 animLayerMerge 와 같은 bakeResults + 구간 / preserveOutsideKeys. 오브젝트 묶음으로 나눠 진행률을 낸다."""
        start, end = bake["start"], bake["end"]
        samples = int(round((end - start) / bake["sample_by"])) + 1
        kw = dict(time=(start, end), sampleBy=bake["sample_by"], simulation=False,
                  disableImplicitControl=False, preserveOutsideKeys=True,
                  destinationLayer=dest, resolveWithoutLayer=list(rwl))
        if bake["smart"]:
            kw["smart"] = (1, float(bake["smart_tol"]))

        # 같은 노드의 plug 는 함께, BAKE_CHUNK_PLUGS 가 차면 한 호출.
        groups, cur, cur_node = [], [], None
        for p in plugs:
            node = p.split(".", 1)[0]
            if cur and node != cur_node and len(cur) >= LayerMergeManager.BAKE_CHUNK_PLUGS:
                groups.append(cur)
                cur = []
            cur.append(p)
            cur_node = node
        if cur:
            groups.append(cur)

        for i, group in enumerate(groups):
            try:
                cmds.bakeResults(group, **kw)
            except TypeError:
                # 이 마야에 smart 플래그가 없다 -> 매 샘플 bake
                kw.pop("smart", None)
                bake["used_smart"][0] = False
                cmds.bakeResults(group, **kw)
            bake["done"][0] += len(group) * samples
            bake["report"]("Baking {0}/{1} : {2}".format(i + 1, len(groups), group[0].split(".", 1)[0]))

    @staticmethod
    def _neutralize(layer, plugs, start, end, root, static_values=None):
        """구간 안에서 이 소스 레이어의 기여를 없앤다 (additive = identity 키, override = weight 0).

        static_values : {plug: 값} - 커브 없이 정적 값을 들고 있던 additive 멤버. 커브를 만들어 밖은 그 값, 안은 identity.
        """
        if cmds.animLayer(layer, q=True, override=True):
            LayerMergeManager._gate_weight(layer, start, end, inside=0.0)
            return
        statics = static_values or {}
        for p in plugs:
            curve = LayerKeyManager.layer_curve(p, layer, root)
            if not curve:
                if p not in statics:
                    continue
                # 커브는 setKeyframe(plug, animLayer=L) 로 만들고(값은 역산이라 믿지 않는다) 값은 커브 노드에 직접 쓴다.
                cmds.setKeyframe(p, animLayer=layer, time=(start - 1, start - 1))
                curve = LayerKeyManager.layer_curve(p, layer, root)
                if not curve:
                    continue
                cmds.setKeyframe(curve, time=(start - 1, start - 1), value=statics[p])
                cmds.setKeyframe(curve, time=(end + 1, end + 1), value=statics[p])
            else:
                LayerMergeManager._insert_fixed(curve, start - 1)
                LayerMergeManager._insert_fixed(curve, end + 1)
                # s-1 / e+1 키가 있으므로 구간을 다 지워도 커브 노드는 남는다.
                cmds.cutKey(curve, time=(start, end), clear=True)
            idv = LayerMergeManager._identity(p, layer)
            cmds.setKeyframe(curve, time=(start, start), value=idv, outTangentType="step")
            cmds.setKeyframe(curve, time=(end, end), value=idv)

    @staticmethod
    def _gate_weight(layer, start, end, inside, outside=None):
        """레이어 weight 를 [start, end] 에서 `inside`, 밖에서는 지금 값(또는 `outside`)으로 계단 키."""
        w = layer + ".weight"
        curves = cmds.listConnections(w, source=True, destination=False) or []
        curve = curves[0] if curves and cmds.nodeType(curves[0]).startswith("animCurve") else None
        if curve and outside is None:
            LayerMergeManager._insert_fixed(curve, start - 1)
            LayerMergeManager._insert_fixed(curve, end + 1)
            cmds.cutKey(curve, time=(start, end), clear=True)
            cmds.setKeyframe(curve, time=(start, start), value=inside, outTangentType="step")
            cmds.setKeyframe(curve, time=(end, end), value=inside, outTangentType="step")
            return
        cur = cmds.getAttr(w) if outside is None else outside
        cmds.setKeyframe(w, time=(start - 1, start - 1), value=cur, outTangentType="step")
        cmds.setKeyframe(w, time=(start, start), value=inside, outTangentType="step")
        cmds.setKeyframe(w, time=(end, end), value=inside, outTangentType="step")
        cmds.setKeyframe(w, time=(end + 1, end + 1), value=cur)

    @staticmethod
    def _insert_fixed(curve, t):
        """모양 보존 키(`setKeyframe -insert`) + 탄젠트 고정. 이미 키가 있으면 값은 그대로, 탄젠트만 고정된다."""
        cmds.setKeyframe(curve, insert=True, time=(t, t))
        cmds.keyTangent(curve, e=True, time=(t, t), itt="fixed", ott="fixed")

    @staticmethod
    def _identity(plug, layer):
        """additive 레이어에서 "기여 없음" 인 값. 스케일이고 Multiply 누적이면 1, 아니면 0."""
        attr = plug.split(".")[-1]
        if attr.startswith("scale"):
            try:
                if int(cmds.getAttr(layer + ".scaleAccumulationMode")) == LayerMergeManager.SCALE_MULTIPLY:
                    return 1.0
            except Exception:
                return 1.0
        return 0.0

    @staticmethod
    def _static_values(plugs, keep, root):
        """`keep` 이외의 모든 레이어를 잠깐 뮤트하고 plug 값을 읽는다 = 그 레이어(또는 base)의 정적 값."""
        out = {}
        if not plugs:
            return out
        muted = []
        for l in LayerMergeManager.stack(root):
            if l == keep:
                continue
            try:
                if not cmds.getAttr(l + ".mute"):
                    cmds.animLayer(l, e=True, mute=True)
                    muted.append(l)
            except Exception:
                pass
        try:
            for p in plugs:
                try:
                    out[p] = cmds.getAttr(p)
                except Exception:
                    pass
        finally:
            for l in muted:
                cmds.animLayer(l, e=True, mute=False)
        return out

    @staticmethod
    def _evals(curve, frames):
        """커브를 프레임마다 평가한 값 (UI 단위 - 각도 커브는 도)."""
        return [cmds.keyframe(curve, q=True, eval=True, time=(f, f))[0] for f in frames]

    @staticmethod
    def _plug_locked(plug):
        try:
            return bool(cmds.getAttr(plug, lock=True))
        except Exception:
            return False

    @staticmethod
    def _sample(plugs, start, end):
        """정수 프레임마다 plug 값. {frame: [v, ...]} (currentTime 루프가 getAttr(time=) 보다 빠르다)."""
        out = {}
        for f in range(int(start), int(end) + 1):
            cmds.currentTime(f)
            row = []
            for p in plugs:
                try:
                    row.append(cmds.getAttr(p))
                except Exception:
                    row.append(None)
            out[f] = row
        return out

    @staticmethod
    def _compare(before, after, plugs):
        """(최대 편차, 프레임, plug)."""
        worst = (0.0, None, None)
        for f, row in before.items():
            now = after.get(f)
            if now is None:
                continue
            for i, (a, b) in enumerate(zip(row, now)):
                if a is None or b is None:
                    continue
                d = abs(a - b)
                if d > worst[0]:
                    worst = (d, f, plugs[i])
        if worst[1] is None:
            worst = (0.0, min(before) if before else 0, plugs[0] if plugs else "")
        return worst

    @staticmethod
    def _select_only(layer):
        """결과 레이어만 선택 + preferred (마야 Merge Layers 가 끝에 하는 것과 같다)."""
        for l in cmds.ls(type="animLayer") or []:
            try:
                cmds.animLayer(l, e=True, selected=(l == layer))
            except Exception:
                pass
        try:
            cmds.animLayer(layer, e=True, preferred=True)
        except Exception:
            pass

    @staticmethod
    def _brief(names, limit=6):
        uniq = sorted(set(names))
        if len(uniq) <= limit:
            return ", ".join(uniq)
        return "{0} (+{1} more)".format(", ".join(uniq[:limit]), len(uniq) - limit)
