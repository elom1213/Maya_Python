# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - translate 채널 <-> 애님 커브 (계획서 §4-4)
"""
대상(transform · joint)의 translate 세 채널을 애님 커브로 읽고 쓴다. **마야 API 의 내부 단위(cm)** 만 쓴다 —
`cmds.keyframe` · `getAttr` 은 UI 단위라 섞지 않는다(키 맞추기의 `cmds.setKeyframe` 만 예외: 값을 주지 않거나 내부 단위를 UI 로 바꿔 준다).

채널 상태:
    curve  : 애님 커브(animCurveTL)가 translate 에 **직결** → 편집 가능
    static : 입력 연결 없음 → 그 값 그대로 (편집하면 그때 커브를 만든다)
    driven : 그 밖의 노드가 구동(컨스트레인트 · 표현식 · 애니메이션 레이어 · pairBlend …) → 그 축은 편집 불가
    locked : plug 가 lock → 편집 불가
세 축이 다 편집 불가거나 하나라도 driven 이면 경로 전체를 잠근다(이유 문자열). driven 축이 섞이면 결과가 예측 안 되기 때문.
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

#: 애니메이션 레이어 · 블렌드 노드 (1단계는 잠금 - 계획서 Q3)
_LAYER_TYPES = ("animBlendNodeAdditiveDL", "animBlendNodeAdditiveFA", "animBlendNodeAdditiveRotation",
                "animBlendNodeAdditive", "animBlendNodeBase", "pairBlend", "blendWeighted")


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


class Axis(object):
    """translate 한 축의 상태."""

    __slots__ = ("attr", "plug", "curve", "fn", "static", "state", "source")

    def __init__(self, node_obj, attr):
        self.attr = attr
        self.plug = om.MFnDependencyNode(node_obj).findPlug(attr, False)
        self.curve = None
        self.fn = None
        self.static = self.plug.asDouble()
        self.source = ""
        src = self.plug.source()
        if self.plug.isLocked:
            self.state = "locked"
        elif src.isNull:
            self.state = "static"
        else:
            node = src.node()
            self.source = om.MFnDependencyNode(node).name()
            if node.hasFn(om.MFn.kAnimCurve) and om.MFnDependencyNode(node).typeName == "animCurveTL":
                self.curve = node
                self.fn = oma.MFnAnimCurve(node)
                self.state = "curve"
                # 레퍼런스에서 온 커브도 마야는 키 편집을 허락한다(레퍼런스 편집으로 남는다) - 노드 자체가 잠긴 것만 막는다.
                if om.MFnDependencyNode(node).isLocked:
                    self.state = "locked"
            else:
                self.state = "driven"

    @property
    def editable(self):
        return self.state in ("curve", "static")

    def value(self, frame):
        if self.fn is not None:
            return self.fn.evaluate(ui_time(frame))
        return self.static

    def values(self, frames):
        if self.fn is None:
            return [self.static] * len(frames)
        ev = self.fn.evaluate
        return [ev(ui_time(f)) for f in frames]

    def key_times(self):
        if self.fn is None:
            return []
        unit = om.MTime.uiUnit()
        fn = self.fn
        return [fn.input(i).asUnits(unit) for i in range(fn.numKeys)]

    def key_index(self, frame):
        """그 시간의 키 인덱스, 없으면 -1."""
        if self.fn is None:
            return -1
        found = self.fn.find(ui_time(frame))
        return -1 if found is None else found


class Channels(object):
    """대상 하나의 translate 세 축."""

    def __init__(self, node):
        self.node = node
        self.obj = depend_node(node)
        self.axes = [Axis(self.obj, a) for a in AXES]

    # ---------------------------------------------------------------- 상태
    def lock_reason(self):
        """경로 전체를 편집할 수 없으면 이유(영어, 로그 · 툴팁), 아니면 ""."""
        driven = [a for a in self.axes if a.state == "driven"]
        if driven:
            src = driven[0].source
            kind = cmds.nodeType(src) if cmds.objExists(src) else ""
            if kind in _LAYER_TYPES:
                return "Translate goes through {0} ({1}) - animation layers / blends are not supported yet".format(
                    src, kind)
            return "Translate is driven by {0} ({1}) - edit that instead".format(src, kind)
        if not any(a.editable for a in self.axes):
            return "Translate is locked"
        return ""

    def editable_mask(self):
        return [a.editable for a in self.axes]

    # ---------------------------------------------------------------- 평가
    def values(self, frames):
        """(N, 3) - 프레임마다 translate (내부 단위)."""
        cols = [a.values(frames) for a in self.axes]
        if np is not None:
            return np.array(cols, dtype="float64").T.copy()
        return [list(row) for row in zip(*cols)]

    def key_times(self):
        """세 축 키 시간의 합집합 (정렬)."""
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
        """편집할 프레임마다 **편집 가능한 모든 축**에 키가 있게 한다 (모양은 그대로). 바뀌었으면 True.

        - 커브는 있는데 그 프레임에 키가 없는 축 : `setKeyframe(insert=True)` — 마야가 모양을 지키며 넣는다.
        - 커브가 없는 축(static) : 기존 키 시간 + frames 에 지금 값으로 키를 만든다(원본과 같은 동작).
        cmds 로 하므로 undo 큐에 들어간다 - 호출부(편집 세션)가 열어 둔 undo 묶음 안에서 부른다.
        """
        changed = False
        union = sorted(set(round(t, KEY_ROUND) for t in self.key_times()) | set(round(f, KEY_ROUND) for f in frames))
        for a in self.axes:
            if not a.editable:
                continue
            plug = "{0}.{1}".format(self.node, a.attr)
            if a.state == "static":
                ui_value = om.MDistance(a.static, om.MDistance.internalUnit()).asUnits(om.MDistance.uiUnit())
                for t in union:
                    cmds.setKeyframe(plug, time=t, value=ui_value)
                changed = True
                continue
            for f in frames:
                if a.key_index(f) < 0:
                    cmds.setKeyframe(plug, time=f, insert=True)
                    changed = True
        if changed:
            self.__init__(self.node)
        return changed
