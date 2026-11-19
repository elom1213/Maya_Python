# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - translate 채널 <-> 애님 커브 · 애니메이션 레이어 (계획서 §4-4, v01.03 레이어)
"""
대상(transform · joint)의 translate 세 채널을 애님 커브로 읽고 쓴다. **마야 API 의 내부 단위(cm)** 만 쓴다 —
`cmds.keyframe` · `getAttr` 은 UI 단위라 섞지 않는다(키 맞추기의 `cmds.setKeyframe` 만 예외: 값을 주지 않거나 내부 단위를 UI 로 바꿔 준다).

애니메이션 레이어 (v01.03, mayapy 실측)
----------------------------------------
레이어가 있으면 translate 위에 레이어마다 `animBlendNodeAdditiveDL` 이 하나씩 쌓인다:

    Base 커브 ─inputA─▶ [addL 블렌드] ─inputA─▶ [ovrL 블렌드] ─output─▶ translateX
                 addL 커브 ─inputB─┘      ovrL 커브 ─inputB─┘

블렌드는 모두 **output = weightA · inputA + weightB · inputB** 이고, weightA / weightB 는 레이어의
`backgroundWeight` / `foregroundWeight` 에서 온다(뮤트 · 솔로 · 가중치 애니메이션이 이미 들어 있다):

    additive 레이어 : weightA = 1,        weightB = 가중치
    override 레이어 : weightA = 1 - 가중치, weightB = 가중치   (0.5 일 때 0.5·2 + 0.5·7 = 4.5 실측)
    뮤트           : weightA = 1,        weightB = 0

그래서 최종 translate 는 **고른 레이어(L)의 커브 값 v 에 대해 1차식**이다:  T = α + β·v
    β(L) = weightB(L) · Π(L 위 블렌드들의 weightA)        (Base 는 Π(모든 블렌드의 weightA))
→ 경로는 모든 레이어를 합친 실제 움직임으로 그리고(values), 끌면 L 의 키 값만 정확히 역산해 바꾼다(path_cache.solve).
레이어 가중치는 프레임마다 굽는다(parent_space.bake) - 커브는 굽지 않고 직접 계산한다.

채널 상태 (편집 레이어 기준):
    curve  : 그 레이어에 애님 커브가 있다 → 편집 가능
    static : 그 레이어에 커브가 없다(값만) → 편집하면 그때 그 레이어에 커브를 만든다
    driven : 컨스트레인트 · 표현식 · pairBlend 등이 구동 → 경로 잠금
    locked : plug 가 lock, 또는 커브 노드가 잠김 → 그 축은 편집 불가
    absent : 이 축은 그 레이어에 들어 있지 않다 → 그 축은 편집 불가
"""

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

try:
    import numpy as np
except Exception:                                          # noqa: BLE001
    np = None

AXES = ("translateX", "translateY", "translateZ")
KEY_ROUND = 3                   # 키 시간 비교 자리수 (원본과 같은 생각: 1/1000 프레임)
BASE_LAYER = "BaseAnimation"    # 레이어가 하나도 없을 때도 이 이름으로 부른다
BLEND_TYPE = "animBlendNodeAdditiveDL"


def ui_time(frame):
    return om.MTime(float(frame), om.MTime.uiUnit())


def depend_node(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDependNode(0)


def dag_path(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDagPath(0)


def long_name(name):
    found = cmds.ls(name, long=True) or []
    return found[0] if len(found) == 1 else None


def short_name(name):
    return (cmds.ls(name) or [name])[0]


# ---------------------------------------------------------------------- 레이어 목록
def root_layer():
    """루트(Base) 레이어 이름. 레이어가 없으면 BASE_LAYER."""
    try:
        root = cmds.animLayer(q=True, root=True)
    except Exception:                                      # noqa: BLE001
        root = None
    return root or BASE_LAYER


def scene_layers():
    """씬의 애니메이션 레이어 - Base 먼저, 그다음 레이어 에디터 순서(깊이 우선). 레이어가 없으면 [BASE_LAYER]."""
    root = root_layer()
    out = [root]

    def walk(layer):
        for child in cmds.animLayer(layer, q=True, children=True) or []:
            out.append(child)
            walk(child)

    if cmds.objExists(root) and cmds.nodeType(root) == "animLayer":
        walk(root)
    return out


def is_base(layer):
    return not layer or layer == root_layer()


def layer_locked(layer):
    if is_base(layer) or not cmds.objExists(layer):
        return False
    try:
        return bool(cmds.getAttr(layer + ".lock"))
    except Exception:                                      # noqa: BLE001
        return False


# ---------------------------------------------------------------------- 한 층
class Level(object):
    """블렌드 쌓임의 한 층 : 레이어 하나의 값(커브 또는 고정값)."""

    __slots__ = ("layer", "fn", "curve_name", "static", "blend", "locked_curve")

    def __init__(self, layer, plug=None, blend=None):
        self.layer = layer
        self.blend = blend
        self.fn = None
        self.curve_name = ""
        self.static = plug.asDouble() if plug is not None else 0.0
        self.locked_curve = False
        src = plug.source() if plug is not None else om.MPlug()
        if not src.isNull:
            node = src.node()
            if node.hasFn(om.MFn.kAnimCurve):
                self.fn = oma.MFnAnimCurve(node)
                self.curve_name = om.MFnDependencyNode(node).name()
                self.locked_curve = om.MFnDependencyNode(node).isLocked

    def value(self, frame):
        return self.fn.evaluate(ui_time(frame)) if self.fn is not None else self.static

    def values(self, frames):
        if self.fn is None:
            return [self.static] * len(frames)
        ev = self.fn.evaluate
        return [ev(ui_time(f)) for f in frames]


def _plug_of(node_name, attr):
    return om.MFnDependencyNode(depend_node(node_name)).findPlug(attr, False)


def _layer_of_blend(blend):
    """블렌드 노드의 weightB 를 대는 animLayer."""
    src = cmds.listConnections(blend + ".weightB", source=True, destination=False, type="animLayer") or []
    return src[0] if src else ""


class Axis(object):
    """translate 한 축 - 레이어 쌓임(아래 → 위)과 편집할 층."""

    def __init__(self, node_obj, attr, layer=None):
        self.attr = attr
        self.plug = om.MFnDependencyNode(node_obj).findPlug(attr, False)
        self.levels = []            # 아래(Base) → 위
        self.source = ""
        self.state = "static"
        self.edit = None            # 편집할 층 (Level) 또는 None
        self._walk()
        base = root_layer()
        want = base if is_base(layer) else layer
        if self.state == "driven":
            return
        for lv in self.levels:
            if lv.layer == want:
                self.edit = lv
        if self.plug.isLocked:
            self.state = "locked"
        elif self.edit is None:
            self.state = "absent"
        elif self.edit.locked_curve or layer_locked(self.edit.layer):
            self.state = "locked"
        else:
            self.state = "curve" if self.edit.fn is not None else "static"

    def _walk(self):
        src = self.plug.source()
        base = root_layer()
        if src.isNull:
            self.levels = [Level(base, plug=None)]
            self.levels[0].static = self.plug.asDouble()
            return
        node = src.node()
        name = om.MFnDependencyNode(node).name()
        kind = om.MFnDependencyNode(node).typeName
        if node.hasFn(om.MFn.kAnimCurve):
            self.levels = [Level(base, plug=self.plug)]
            return
        if kind != BLEND_TYPE:
            self.state = "driven"
            self.source = name
            return
        stack = []
        blend = name
        while True:
            stack.append(Level(_layer_of_blend(blend), plug=_plug_of(blend, "inputB"), blend=blend))
            a_plug = _plug_of(blend, "inputA")
            a_src = a_plug.source()
            if a_src.isNull:
                stack.append(Level(base, plug=a_plug))
                break
            a_node = a_src.node()
            a_kind = om.MFnDependencyNode(a_node).typeName
            if a_kind == BLEND_TYPE:
                blend = om.MFnDependencyNode(a_node).name()
                continue
            if a_node.hasFn(om.MFn.kAnimCurve):
                stack.append(Level(base, plug=a_plug))
                break
            self.state = "driven"
            self.source = om.MFnDependencyNode(a_node).name()
            return
        self.levels = list(reversed(stack))

    # 편집 층 (예전 Axis 와 같은 이름 - 편집 세션이 쓴다)
    @property
    def fn(self):
        return self.edit.fn if self.edit is not None else None

    @property
    def static(self):
        return self.edit.static if self.edit is not None else 0.0

    @property
    def editable(self):
        return self.state in ("curve", "static")

    def layers(self):
        return [lv.layer for lv in self.levels if lv.blend]

    def key_times(self):
        fn = self.fn
        if fn is None:
            return []
        unit = om.MTime.uiUnit()
        return [fn.input(i).asUnits(unit) for i in range(fn.numKeys)]

    def key_index(self, frame):
        """그 시간의 키 인덱스 (편집 층), 없으면 -1."""
        fn = self.fn
        if fn is None:
            return -1
        found = fn.find(ui_time(frame))
        return -1 if found is None else found

    # ---------------------------------------------------------------- 합치기
    def composite(self, frames, weights):
        """최종 translate (N,) = 블렌드를 아래부터 차례로. weights = {레이어: (wA (N,), wB (N,))}."""
        if not self.levels:
            return np.full(len(frames), self.plug.asDouble())
        out = np.array(self.levels[0].values(frames), dtype="float64")
        for lv in self.levels[1:]:
            wa, wb = _weights(weights, lv.layer, len(frames))
            out = wa * out + wb * np.array(lv.values(frames), dtype="float64")
        return out

    def coefficient(self, frames, weights):
        """β (N,) = 편집 층 값이 최종 translate 에 곱해지는 양. 편집 층이 없으면 0."""
        n = len(frames)
        if self.edit is None:
            return np.zeros(n)
        idx = self.levels.index(self.edit)
        beta = np.ones(n)
        if idx > 0:
            beta = _weights(weights, self.edit.layer, n)[1].copy()
        for lv in self.levels[idx + 1:]:
            beta = beta * _weights(weights, lv.layer, n)[0]
        return beta


def _weights(weights, layer, n):
    if weights and layer in weights:
        wa, wb = weights[layer]
        return np.asarray(wa, dtype="float64"), np.asarray(wb, dtype="float64")
    return np.ones(n), np.ones(n)


class Channels(object):
    """대상 하나의 translate 세 축 (편집 레이어 기준)."""

    def __init__(self, node, layer=None):
        self.node = node
        self.layer = root_layer() if is_base(layer) else layer
        self.obj = depend_node(node)
        self.axes = [Axis(self.obj, a, self.layer) for a in AXES]

    # ---------------------------------------------------------------- 상태
    def lock_reason(self):
        """경로 전체를 편집할 수 없으면 이유(영어, 로그 · 툴팁), 아니면 ""."""
        driven = [a for a in self.axes if a.state == "driven"]
        if driven:
            src = driven[0].source
            kind = cmds.nodeType(src) if cmds.objExists(src) else ""
            return "Translate is driven by {0} ({1}) - edit that instead".format(src, kind)
        if all(a.state == "absent" for a in self.axes):
            return "Not in the animation layer {0} - add it in the Layer Editor or pick another layer".format(
                self.layer)
        if layer_locked(self.layer):
            return "The animation layer {0} is locked".format(self.layer)
        if not any(a.editable for a in self.axes):
            return "Translate is locked"
        return ""

    def editable_mask(self):
        return [a.editable for a in self.axes]

    def dirty_nodes(self):
        """undo · redo 뒤 다시 계산을 표시할 노드 = 대상 + translate 블렌드 체인 (plugin _dirty)."""
        out = [self.node]
        for a in self.axes:
            for lv in a.levels:
                if lv.blend and lv.blend not in out:
                    out.append(lv.blend)
        return out

    def layers_used(self):
        """블렌드에 쓰인 레이어들 (가중치를 구워야 할 것)."""
        seen = []
        for a in self.axes:
            for name in a.layers():
                if name and name not in seen:
                    seen.append(name)
        return seen

    # ---------------------------------------------------------------- 평가
    def values(self, frames, weights=None):
        """(N, 3) - 프레임마다 **최종** translate (모든 레이어를 합친 값, 내부 단위)."""
        return np.stack([a.composite(frames, weights) for a in self.axes], axis=1)

    def coefficients(self, frames, weights=None):
        """(N, 3) - 편집 레이어 값 1 이 최종 translate 를 움직이는 양(β)."""
        return np.stack([a.coefficient(frames, weights) for a in self.axes], axis=1)

    def layer_values(self, frames):
        """(N, 3) - 편집 레이어의 지금 값(커브 또는 고정값). 층이 없는 축은 0."""
        cols = [a.edit.values(frames) if a.edit is not None else [0.0] * len(frames) for a in self.axes]
        return np.array(cols, dtype="float64").T.copy()

    def key_times(self):
        """편집 레이어 세 축 키 시간의 합집합 (정렬)."""
        seen = {}
        for a in self.axes:
            for t in a.key_times():
                seen.setdefault(round(t, KEY_ROUND), t)
        return [seen[k] for k in sorted(seen)]

    def key_indices(self, frame):
        """축마다 그 시간의 키 인덱스 (-1 = 없음)."""
        return [a.key_index(frame) for a in self.axes]

    # ---------------------------------------------------------------- 키 맞추기
    def ensure_keys(self, frames):
        """편집할 프레임마다 **편집 가능한 모든 축**(편집 레이어)에 키가 있게 한다 (모양은 그대로). 바뀌었으면 True.

        - 커브는 있는데 그 프레임에 키가 없는 축 : `setKeyframe(insert=True)` — 마야가 모양을 지키며 넣는다.
        - 그 레이어에 커브가 없는 축(static) : 기존 키 시간 + frames 에 키를 만든다.
            레이어가 없는 씬의 Base : 지금 값(내부 단위 → UI 단위)으로.
            레이어가 있으면 `setKeyframe(animLayer=L)` 를 값 없이 - 마야가 최종 결과가 그대로가 되게 그 레이어 값을 정한다
            (레이어 쪽 `-value` 는 최종값으로 역산되므로 쓰지 않는다 - 메모 wip-a00110-hold-layer-blend).
        cmds 로 하므로 undo 큐에 들어간다 - 호출부(편집 세션)가 열어 둔 undo 묶음 안에서 부른다.
        """
        changed = False
        has_layers = cmds.objExists(root_layer()) and bool(self.layers_used())
        layer_kw = {"animLayer": self.layer} if has_layers else {}
        union = sorted(set(round(t, KEY_ROUND) for t in self.key_times()) | set(round(f, KEY_ROUND) for f in frames))
        for a in self.axes:
            if not a.editable:
                continue
            plug = "{0}.{1}".format(self.node, a.attr)
            if a.state == "static":
                ui_value = om.MDistance(a.static, om.MDistance.internalUnit()).asUnits(om.MDistance.uiUnit())
                if has_layers:
                    # 그 레이어의 값은 상수(static)였다 → 새 커브도 모든 키가 그 상수여야 모양이 그대로다.
                    # setKeyframe -animLayer 는 값을 주면 최종값으로 역산하고, 안 주면 "그 프레임의 최종 결과를 지키는" 값을
                    # 넣는다 - override 레이어는 아래 레이어가 프레임마다 달라 키마다 다른 값이 들어가 커브가 굽었다
                    # (v01.03 실측: 첫 키 앞 프레임이 0.54 바뀜). 그래서 키를 만든 뒤 그 레이어 커브의 값을 상수로 다시 쓴다.
                    for t in union:
                        cmds.setKeyframe(plug, time=t, **layer_kw)
                    fresh = Axis(self.obj, a.attr, self.layer)
                    if fresh.edit is not None and fresh.edit.curve_name:
                        cmds.keyframe(fresh.edit.curve_name, edit=True, absolute=True, valueChange=ui_value)
                else:
                    for t in union:
                        cmds.setKeyframe(plug, time=t, value=ui_value)
                changed = True
                continue
            for f in frames:
                if a.key_index(f) < 0:
                    cmds.setKeyframe(plug, time=f, insert=True, **layer_kw)
                    changed = True
        if changed:
            self.__init__(self.node, self.layer)
        return changed
