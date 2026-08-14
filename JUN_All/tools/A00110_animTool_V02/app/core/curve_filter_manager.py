# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-14
# A00110_animTool_V02 - Curve 필터 (Smooth / Intensity / Interpolate) 핵심 로직
#                       (maya.cmds + OpenMaya, UI 비의존)
#
# 구간 [start, end] 안의 **키 값**을 다듬는다. 키 시점은 건드리지 않는다(그건 Timing 탭).
#
# ## 세 가지 필터
#
#   Smooth      이웃 키와 평균을 내 요철을 줄인다(가우시안). 반대로 밀면 요철을 키운다(Rough).
#   Intensity   구간 평균을 기준으로 진폭을 키우거나 줄인다(과장 / 완화).
#   Interpolate 구간 **양 끝 키를 잇는 이징 곡선**으로 값을 끌어당긴다(Ease-In/Out/Linear/S).
#
# ## 공통 규칙
#
# - **양방향 슬라이더는 가운데가 0(변화 없음)** 이다. 부호가 방향, 절댓값이 세기다.
# - 값은 **항상 원본 스냅샷에서 다시 계산**한다(누적 금지). 슬라이더를 좌우로 흔들어도
#   원래 값으로 정확히 돌아온다.
# - **구간 밖 키는 건드리지 않는다.** 구간 안 키만 값이 바뀐다.
# - 키를 지웠다 다시 만들지 않고 `keyframe -e -valueChange` 로 **값만** 바꾼다
#   → 탄젠트 · 인피니티 · 애님 레이어 소속이 그대로 보존된다(Stagger Offset 과 같은 규칙).
# - 미리보기는 undo 를 기록하지 않고, 조작이 멎으면 **한 번의 undo 청크**로 확정한다.
#
# ## Use Quaternions
#
# 회전을 오일러 채널 3개로 따로 필터링하면 짐벌락 근처에서 축끼리 어긋나 흔들린다.
# 켜면 rotateX/Y/Z 를 **한 묶음(쿼터니언)** 으로 보고 필터를 적용한 뒤 오일러로 되돌린다.
# 되돌릴 때는 **직전 키 값에 가장 가까운 해**를 골라 ±360 점프를 만들지 않는다.
# 세 축의 키 시간이 서로 다르면 쿼터니언으로 묶을 수 없으므로 **그 오브젝트만** 채널별
# 처리로 물러나고 보고한다.
#
# ## SmartLayer 와의 관계
#
# 같은 이름의 세 필터를 **직접 구현**한 것이다. 원본은 컴파일된 배포본이라 코드를 보지 않았고,
# 화면에 있는 파라미터 구성(Iterations / Strength / 양방향 슬라이더 / 프리셋 4개)만 참고했다.
# 수식은 아래 주석에 적힌 대로이며, 원본과 수치가 같지는 않을 수 있다.

import contextlib

import maya.cmds as cmds
import maya.mel as mel
from maya.api import OpenMaya as om

from Framework.core.maya_undo import undo_chunk


ROTATE_ATTRS = ("rotateX", "rotateY", "rotateZ")

# rotateOrder 인덱스 -> MEulerRotation 회전 순서 (마야 enum 순서와 같다)
_ROTATE_ORDERS = (
    om.MEulerRotation.kXYZ, om.MEulerRotation.kYZX, om.MEulerRotation.kZXY,
    om.MEulerRotation.kXZY, om.MEulerRotation.kYXZ, om.MEulerRotation.kZYX,
)

EPS = 1e-6

# Interpolate 이징 종류
EASE_IN = "easeIn"
EASE_OUT = "easeOut"
LINEAR = "linear"
EASE_IN_OUT = "easeInOut"
EASES = (EASE_IN, EASE_OUT, LINEAR, EASE_IN_OUT)


@contextlib.contextmanager
def _undo_disabled():
    """블록 안의 cmds 호출을 undo 큐에 남기지 않는다 (미리보기용).

    stateWithoutFlush 는 "큐를 비우지 않고" 기록만 끈다. state=False 는 히스토리를 통째로
    날리므로 쓰지 않는다. 예외가 나도 finally 에서 되돌린다.
    """
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=True)


# ============================================================ 순수 계산 (마야 무관)

def gaussian_smooth(values, iterations=1):
    """[1 2 1]/4 커널을 `iterations` 번 돌린 값 목록. 양 끝 값은 고정한다.

    양 끝을 고정하는 이유: 구간 밖 애니메이션과 이어지는 지점이라 값이 움직이면
    경계에 이음매가 생긴다.
    """
    out = list(values)
    if len(out) < 3:
        return out
    for _ in range(max(0, int(iterations))):
        prev = list(out)
        for i in range(1, len(prev) - 1):
            out[i] = (prev[i - 1] + 2.0 * prev[i] + prev[i + 1]) * 0.25
    return out


def mix(original, target, t):
    """original 에서 target 쪽으로 t 만큼. t<0 이면 **반대로** 밀어낸다(요철 강조)."""
    return [o + (g - o) * t for o, g in zip(original, target)]


def smooth_values(values, amount, iterations=3, strength=100.0):
    """Smooth 결과.

    amount    : -100(Rough) ~ +100(Smooth). 0 이면 원본 그대로.
    iterations: 가우시안 패스 수(클수록 넓게 뭉갠다).
    strength  : 0~100. amount 에 곱해지는 전체 세기.
    """
    t = (amount / 100.0) * (strength / 100.0)
    if abs(t) < EPS or len(values) < 3:
        return list(values)
    return mix(values, gaussian_smooth(values, iterations), t)


def intensity_values(values, amount):
    """Intensity 결과 — 구간 **평균**을 기준으로 진폭을 조절한다.

    amount : -100(평평하게) ~ +100(2배 과장). 0 이면 원본 그대로.
    평균을 기준으로 삼으므로 전체가 위/아래로 밀리지 않는다(오프셋이 생기지 않는다).
    """
    if not values or abs(amount) < EPS:
        return list(values)
    ref = sum(values) / float(len(values))
    scale = 1.0 + amount / 100.0
    return [ref + (v - ref) * scale for v in values]


def ease(u, shape):
    """0~1 을 이징 곡선에 통과시킨다."""
    u = min(1.0, max(0.0, u))
    if shape == EASE_IN:
        return u * u
    if shape == EASE_OUT:
        return 1.0 - (1.0 - u) * (1.0 - u)
    if shape == EASE_IN_OUT:
        return u * u * (3.0 - 2.0 * u)          # smoothstep
    return u                                     # LINEAR


def interpolate_values(times, values, shape, amount):
    """Interpolate 결과 — 구간 **양 끝 키를 잇는 이징 곡선**으로 끌어당긴다.

    shape  : EASE_IN / EASE_OUT / LINEAR / EASE_IN_OUT
    amount : 0~100. 100 이면 이징 곡선 그 자체가 된다(중간 키의 원래 값은 사라진다).
    양 끝 키는 목표 곡선의 양 끝과 같으므로 값이 변하지 않는다.
    """
    n = len(values)
    if n < 3 or abs(amount) < EPS:
        return list(values)
    span = times[-1] - times[0]
    if abs(span) < EPS:
        return list(values)

    v0, v1 = values[0], values[-1]
    t = amount / 100.0
    out = []
    for time, value in zip(times, values):
        u = (time - times[0]) / span
        target = v0 + (v1 - v0) * ease(u, shape)
        out.append(value + (target - value) * t)
    return out


# ============================================================ 쿼터니언 경로

def _to_quats(euler_triples, order):
    return [om.MEulerRotation(om.MAngle(x, om.MAngle.kDegrees).asRadians(),
                              om.MAngle(y, om.MAngle.kDegrees).asRadians(),
                              om.MAngle(z, om.MAngle.kDegrees).asRadians(),
                              order).asQuaternion()
            for x, y, z in euler_triples]


def _align(quats):
    """이웃한 쿼터니언의 부호를 맞춘다(q 와 -q 는 같은 회전이라 보간이 뒤집힌다)."""
    out = [om.MQuaternion(quats[0])] if quats else []
    for q in quats[1:]:
        cur = om.MQuaternion(q)
        prev = out[-1]
        dot = (prev.x * cur.x + prev.y * cur.y + prev.z * cur.z + prev.w * cur.w)
        if dot < 0.0:
            cur = om.MQuaternion(-cur.x, -cur.y, -cur.z, -cur.w)
        out.append(cur)
    return out


def _slerp(a, b, t):
    return om.MQuaternion.slerp(a, b, t)


def _quat_average(quats):
    """부호를 맞춘 뒤 성분 평균 + 정규화(nlerp 평균). 작은 각도 범위에서 충분하다."""
    n = float(len(quats))
    x = sum(q.x for q in quats) / n
    y = sum(q.y for q in quats) / n
    z = sum(q.z for q in quats) / n
    w = sum(q.w for q in quats) / n
    q = om.MQuaternion(x, y, z, w)
    return q.normal()


def _to_eulers(quats, order, reference):
    """쿼터니언 -> 오일러(도). `reference` 의 각 키 값에 가장 가까운 해를 고른다.

    쿼터니언은 ±360 정보를 잃으므로 그대로 되돌리면 커브에 점프가 생긴다. 원래 값에
    ±360 을 더해 가장 가까운 쪽을 택해 **연속성을 지킨다**.
    """
    out = []
    for q, ref in zip(quats, reference):
        euler = q.asEulerRotation().reorder(order)
        degrees = [om.MAngle(v, om.MAngle.kRadians).asDegrees()
                   for v in (euler.x, euler.y, euler.z)]
        fixed = []
        for value, ref_value in zip(degrees, ref):
            turns = round((ref_value - value) / 360.0)
            fixed.append(value + turns * 360.0)
        out.append(tuple(fixed))
    return out


def smooth_quats(triples, order, amount, iterations=3, strength=100.0):
    t = (amount / 100.0) * (strength / 100.0)
    if abs(t) < EPS or len(triples) < 3:
        return list(triples)

    quats = _align(_to_quats(triples, order))
    smoothed = [om.MQuaternion(q) for q in quats]
    for _ in range(max(0, int(iterations))):
        prev = [om.MQuaternion(q) for q in smoothed]
        for i in range(1, len(prev) - 1):
            neighbour = _slerp(prev[i - 1], prev[i + 1], 0.5)
            smoothed[i] = _slerp(prev[i], neighbour, 0.5)
    result = [_slerp(q, s, t) if t > 0 else _slerp(s, q, 1.0 - t)
              for q, s in zip(quats, smoothed)]
    return _to_eulers(result, order, triples)


def intensity_quats(triples, order, amount):
    if len(triples) < 2 or abs(amount) < EPS:
        return list(triples)
    quats = _align(_to_quats(triples, order))
    ref = _quat_average(quats)
    scale = 1.0 + amount / 100.0
    result = [_slerp(ref, q, scale) for q in quats]
    return _to_eulers(result, order, triples)


def interpolate_quats(times, triples, order, shape, amount):
    n = len(triples)
    if n < 3 or abs(amount) < EPS:
        return list(triples)
    span = times[-1] - times[0]
    if abs(span) < EPS:
        return list(triples)

    quats = _align(_to_quats(triples, order))
    q0, q1 = quats[0], quats[-1]
    t = amount / 100.0
    result = []
    for time, q in zip(times, quats):
        u = (time - times[0]) / span
        target = _slerp(q0, q1, ease(u, shape))
        result.append(_slerp(q, target, t))
    return _to_eulers(result, order, triples)


# ============================================================ 세션

class CurveFilterSession(object):
    """슬라이더 한 번의 조작을 담는 세션.

    시작할 때 구간 안 키의 **원본 값**을 전부 스냅샷하고, 이후 모든 계산은 그 스냅샷에서
    한다(누적 없음). `preview()` 는 undo 를 남기지 않고, `settle()` 은 원본으로 되돌린 뒤
    undo 청크 하나로 다시 적용해 **Ctrl+Z 한 번**이면 조작 직전으로 돌아간다.
    """

    def __init__(self, channels, groups, start, end, skipped=None, fallback=None):
        self.channels = channels     # 채널별 항목 (쿼터니언 그룹에 속하지 않은 것 포함)
        self.groups = groups         # 회전 3축 묶음
        self.start = start
        self.end = end
        self.skipped = skipped or []
        self.fallback = fallback or []
        self.source = "range"        # 무엇을 대상으로 잡았는지(로그용)
        self.alive = True

    # ---------------------------------------------------------------- 생성
    @staticmethod
    def _curve_of(plug):
        found = cmds.keyframe(plug, query=True, name=True) or []
        return found[0] if found else None

    @classmethod
    def _channel_entry(cls, obj, attr, start, end):
        plug = "{0}.{1}".format(obj, attr)
        if not cmds.objExists(plug):
            return None
        curve = cls._curve_of(plug)
        if not curve:
            return None

        times = cmds.keyframe(curve, query=True, timeChange=True) or []
        values = cmds.keyframe(curve, query=True, valueChange=True) or []
        picked = [(i, t, v) for i, (t, v) in enumerate(zip(times, values))
                  if start - EPS <= t <= end + EPS]
        if len(picked) < 2:
            return None
        return {
            "obj": obj,
            "attr": attr,
            "curve": curve,
            "indices": [i for i, _, _ in picked],
            "times": [t for _, t, _ in picked],
            "original": [v for _, _, v in picked],
        }

    # ------------------------------------------------- 씬 선택에서 바로 만들기
    @classmethod
    def from_selection(cls, quaternion=True):
        """**지금 선택한 것**으로 세션을 만든다. (세션 또는 None, 메시지)

        우선순위:
          1. **그래프 에디터에서 고른 키** — 그 키들만 정확히 필터한다(가장 좁고 명확하다).
          2. 키를 안 골랐으면 **타임 슬라이더에서 드래그한 구간** + 씬에서 선택한 오브젝트.

        둘 다 없으면 **아무것도 하지 않는다.** 선택이 없다고 전 구간을 조용히 건드리는 쪽이
        훨씬 위험하기 때문이다(Euler 탭에서 세운 것과 같은 규칙).
        """
        selected = cls._selected_key_entries()
        if selected:
            channels, groups, fallback = cls._group_rotations(selected, quaternion)
            times = [t for e in selected for t in e["times"]]
            session = cls(channels, groups, min(times), max(times),
                          skipped=[], fallback=fallback)
            session.source = "selected keys"
            return (session, "")

        objects = cmds.ls(selection=True, long=False) or []
        if not objects:
            return (None, "Select the keys to filter in the Graph Editor "
                          "(or a time range in the Time Slider, plus the objects).")

        span = cls.selected_time_range()
        if span is None:
            return (None, "No keys selected. Drag over the keys in the Graph Editor, "
                          "or highlight a range in the Time Slider.")

        session, message = cls.create(objects, span[0], span[1],
                                      attrs=selected_channel_attrs(),
                                      quaternion=quaternion)
        if session is not None:
            session.source = "time slider range"
        return (session, message)

    @staticmethod
    def selected_time_range():
        """타임 슬라이더에서 드래그로 고른 구간 (start, end). 없으면 None.

        `timeControl -q -rangeArray` 는 드래그가 없어도 **현재 프레임 ~ +1** 을 돌려주므로
        폭이 1 프레임 이하면 "고르지 않았다"로 본다.
        """
        if cmds.about(batch=True):
            return None                       # UI 가 없으면 타임 슬라이더도 없다
        try:
            control = mel.eval("$tmp = $gPlayBackSlider")
            span = cmds.timeControl(control, query=True, rangeArray=True) or []
        except Exception:
            return None
        if len(span) != 2 or (span[1] - span[0]) <= 1.0 + EPS:
            return None
        return (span[0], span[1])

    @classmethod
    def _selected_key_entries(cls):
        """그래프 에디터에서 **선택된 키**만 담은 채널 항목들.

        `keyframe -q -sl` 은 오브젝트를 안 줘도 **선택된 모든 키**를 전역으로 돌려준다.
        커브별로 인덱스/시간/값을 모아 두면 이후 처리는 구간 방식과 완전히 같다.
        """
        curves = cmds.keyframe(query=True, selected=True, name=True) or []
        out = []
        for curve in curves:
            indices = cmds.keyframe(curve, query=True, selected=True,
                                    indexValue=True) or []
            times = cmds.keyframe(curve, query=True, selected=True,
                                  timeChange=True) or []
            values = cmds.keyframe(curve, query=True, selected=True,
                                   valueChange=True) or []
            if len(indices) < 2:
                continue                      # 키 1개는 다듬을 것이 없다
            obj, attr = cls._driven_plug(curve)
            out.append({
                "obj": obj, "attr": attr, "curve": curve,
                "indices": [int(i) for i in indices],
                "times": list(times), "original": list(values),
            })
        return out

    @staticmethod
    def _driven_plug(curve):
        """그 애님 커브가 결국 무엇을 구동하나 -> (오브젝트, 어트리뷰트).

        애니메이션 레이어가 끼면 커브 -> animBlendNode* -> 대상 이므로 몇 홉 따라간다.
        못 찾으면 (None, None) — 쿼터니언 묶음에서만 빠지고 나머지는 그대로 동작한다.
        """
        node, attr = curve, "output"
        for _ in range(4):
            found = cmds.listConnections("{0}.{1}".format(node, attr), source=False,
                                         destination=True, plugs=True) or []
            if not found:
                return (None, None)
            target = found[0]
            target_node, target_attr = target.split(".", 1)
            if cmds.objectType(target_node, isAType="transform"):
                return (target_node, target_attr)
            node, attr = target_node, "output"
        return (None, None)

    @classmethod
    def _group_rotations(cls, entries, quaternion):
        """채널 항목들에서 rotateX/Y/Z 3종 세트를 묶어 낸다.

        반환: (채널 목록, 쿼터니언 그룹 목록, 폴백한 오브젝트 목록)
        """
        if not quaternion:
            return (list(entries), [], [])

        by_object = {}
        for entry in entries:
            if entry["obj"] and entry["attr"] in ROTATE_ATTRS:
                by_object.setdefault(entry["obj"], {})[entry["attr"]] = entry

        channels, groups, fallback = [], [], []
        grouped = set()
        for obj, found in by_object.items():
            rot = [found.get(a) for a in ROTATE_ATTRS]
            if not all(rot):
                continue
            base = rot[0]["times"]
            same = all(len(e["times"]) == len(base)
                       and all(abs(a - b) < EPS for a, b in zip(e["times"], base))
                       for e in rot)
            if not same:
                fallback.append(obj)
                continue
            order = _ROTATE_ORDERS[cmds.getAttr(obj + ".rotateOrder")]
            groups.append({
                "obj": obj, "order": order, "entries": rot, "times": list(base),
                "original": [tuple(e["original"][i] for e in rot)
                             for i in range(len(base))],
            })
            grouped.update(id(e) for e in rot)

        channels = [e for e in entries if id(e) not in grouped]
        return (channels, groups, fallback)

    @classmethod
    def create(cls, objects, start, end, attrs=None, quaternion=True):
        """세션을 만든다. (세션 또는 None, 메시지)

        attrs 를 주면 그 채널만, 없으면 키가 있는 모든 채널이 대상이다.
        """
        if not objects:
            return (None, "No objects in the list.")
        if end <= start:
            return (None, "End must be greater than Start.")

        channels, groups, skipped, fallback = [], [], [], []

        for obj in objects:
            if not cmds.objExists(obj):
                skipped.append((obj, "not found in the scene"))
                continue

            wanted = attrs or (cmds.listAttr(obj, keyable=True, unlocked=True) or [])
            entries = {}
            for attr in wanted:
                entry = cls._channel_entry(obj, attr, start, end)
                if entry:
                    entries[attr] = entry

            if not entries:
                skipped.append((obj, "no keys inside the range"))
                continue

            rot = [entries.get(a) for a in ROTATE_ATTRS]
            use_quat = quaternion and all(rot)
            if use_quat:
                # 세 축의 키 시간이 같아야 한 묶음으로 볼 수 있다.
                base = rot[0]["times"]
                same = all(len(e["times"]) == len(base)
                           and all(abs(a - b) < EPS for a, b in zip(e["times"], base))
                           for e in rot)
                if same:
                    order = _ROTATE_ORDERS[cmds.getAttr(obj + ".rotateOrder")]
                    groups.append({
                        "obj": obj,
                        "order": order,
                        "entries": rot,
                        "times": list(base),
                        "original": [tuple(e["original"][i] for e in rot)
                                     for i in range(len(base))],
                    })
                    for attr in ROTATE_ATTRS:
                        entries.pop(attr, None)
                else:
                    fallback.append(obj)

            channels.extend(entries.values())

        if not channels and not groups:
            return (None, "No animation curves with keys inside the range. "
                          "({0} object(s) skipped)".format(len(skipped)))

        return (cls(channels, groups, start, end, skipped, fallback), "")

    # ---------------------------------------------------------------- 적용
    def _write(self, entry, values):
        curve = entry["curve"]
        for index, value in zip(entry["indices"], values):
            cmds.keyframe(curve, edit=True, index=(index, index),
                          valueChange=value, absolute=True)

    def _apply(self, kind, params):
        for entry in self.channels:
            values = self._compute_channel(kind, entry, params)
            self._write(entry, values)

        for group in self.groups:
            triples = self._compute_group(kind, group, params)
            for axis, entry in enumerate(group["entries"]):
                self._write(entry, [t[axis] for t in triples])

    @staticmethod
    def _compute_channel(kind, entry, p):
        values, times = entry["original"], entry["times"]
        if kind == "smooth":
            return smooth_values(values, p["amount"], p["iterations"], p["strength"])
        if kind == "intensity":
            return intensity_values(values, p["amount"])
        return interpolate_values(times, values, p["shape"], p["amount"])

    @staticmethod
    def _compute_group(kind, group, p):
        triples, times, order = group["original"], group["times"], group["order"]
        if kind == "smooth":
            return smooth_quats(triples, order, p["amount"], p["iterations"],
                                p["strength"])
        if kind == "intensity":
            return intensity_quats(triples, order, p["amount"])
        return interpolate_quats(times, triples, order, p["shape"], p["amount"])

    def preview(self, kind, **params):
        """undo 를 남기지 않고 결과를 씬에 반영한다(슬라이더 드래그 중)."""
        if not self.alive:
            return
        with _undo_disabled():
            self._apply(kind, params)

    def settle(self, kind, **params):
        """조작이 멎었을 때 **undo 한 항목**으로 확정한다.

        먼저 원본으로 되돌린 뒤 청크 안에서 다시 적용한다 — undo 는 *역연산을 현재 상태에
        적용*하므로, 이렇게 해야 Ctrl+Z 한 번이 조작 직전으로 정확히 돌아간다.
        """
        if not self.alive:
            return
        with _undo_disabled():
            self._restore_values()
        with undo_chunk():
            self._apply(kind, params)

    def _restore_values(self):
        for entry in self.channels:
            self._write(entry, entry["original"])
        for group in self.groups:
            for axis, entry in enumerate(group["entries"]):
                self._write(entry, [t[axis] for t in group["original"]])

    def restore(self):
        """원본 값으로 되돌린다(undo 기록 없음)."""
        if not self.alive:
            return
        with _undo_disabled():
            self._restore_values()

    # ---------------------------------------------------------------- 보고
    def summary(self):
        keys = sum(len(e["indices"]) for e in self.channels)
        keys += sum(len(g["times"]) * 3 for g in self.groups)
        parts = ["{0} curve(s), {1} key(s) in [{2:g}-{3:g}f] from {4}".format(
            len(self.channels) + len(self.groups) * 3, keys, self.start, self.end,
            self.source)]
        if self.groups:
            parts.append("{0} object(s) filtered as quaternions".format(
                len(self.groups)))
        if self.fallback:
            parts.append("{0} object(s) fell back to per-channel "
                         "(rotate keys are not on the same frames)".format(
                             len(self.fallback)))
        if self.skipped:
            parts.append("{0} skipped".format(len(self.skipped)))
        return ".  ".join(parts) + "."


# ============================================================ 씬 헬퍼

def selected_objects():
    return cmds.ls(selection=True, long=False) or []


def selected_channel_attrs():
    """채널박스에서 고른 어트리뷰트(없으면 None = 전 채널)."""
    attrs = cmds.channelBox("mainChannelBox", query=True,
                            selectedMainAttributes=True) or []
    return list(attrs) or None
