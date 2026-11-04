# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-04
# A00110_animTool_V02 - Bake > Fix Sliding (v02.48, maya.cmds, UI 비의존)
#
# 계획서 docs/plans/a00110_fix_sliding_plan.md
#
# 리스트의 오브젝트마다 [Start, End] 동안 **월드 위치 속도**를 재고(선택 축), 중심 이동 평균으로 스무딩해,
# 스무딩 속도 < (Threshold % x 최대 스무딩 속도) 인 연속 프레임 = 정지 구간 [a, b] 를 찾는다.
#   대안 B : 이웃 구간 사이 움직인 프레임 <= G 면 한 구간으로 합친다 (M 판정 전에)
#   길이 b - a + 1 > M 인 구간만 적용
# 구간마다 (시간순) "그 구간 T/R 키를 고르고 Layer Blend Key 켠 채 Shift+A" 와 같은 일을 한다:
#   Hold     : 보기 레이어(Hot Key > Main `Run only when viewing`, 기본 BaseAnimation)의 T/R 커브에서 [a, b] 안 키를 Hold
#   Layer    : HoldLayerManager.apply(force=True) - Hot Key > Main 의 레이어 · N · Pose/Current 설정 그대로, 기준 a' = 그 키들의 최소 시간
#   대안 A   : 블렌드 시작 t0 = max(a' - N, 바로 앞 적용 구간의 끝)
#   대안 D   : 구간 끝 b 에도 a' 와 같은 레이어 값 + flat 탄젠트 (구간 안 레이어 값 상수)
# B · A · D 를 끄면(G=0, clamp/lock 끔) 순수 Shift+A 재현이다.
#
# 샘플링은 반드시 currentTime 루프 - 레이어가 있으면 getAttr -time / MDGContext 는 Base 값만 준다(v02.47 실측).
# 시간 이동 · 디버그 노드는 undo 기록을 끈 채로 해서, Ctrl+Z 한 번이 Fix Sliding 결과만 되돌린다.
# _SmartLayer 의 Fix Sliding 은 참고만(툴팁 문구). 디컴파일하지 않는다.

import contextlib
import math
import re

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from Framework.core.maya_refresh import suspend_refresh

from .keyframe_manager import KeyframeManager
from .hold_layer_manager import HoldLayerManager
from .layer_key_manager import LayerKeyManager

T_ATTRS = ("translateX", "translateY", "translateZ")
R_ATTRS = ("rotateX", "rotateY", "rotateZ")


@contextlib.contextmanager
def _undo_off():
    """블록 안의 작업을 undo 큐에 남기지 않는다(큐는 지우지 않는다)."""
    on = cmds.undoInfo(q=True, state=True)
    if on:
        cmds.undoInfo(stateWithoutFlush=False)
    try:
        yield
    finally:
        if on:
            cmds.undoInfo(stateWithoutFlush=True)


class FixSlidingManager:

    DEFAULT_SMOOTH = 5
    DEFAULT_THRESHOLD_PCT = 2.0
    DEFAULT_MERGE_GAP = 4          # 대안 B, 0 = 합치지 않음
    DEFAULT_MIN_SPAN = 3
    DEBUG_NODE = "_debug_speed"
    PHASES = ("Sampling", "Applying", "Debug")

    # ==================================================
    # 순수 함수 (마야 없이 시험)
    # ==================================================

    @staticmethod
    def speeds(points, axes=(True, True, True)):
        """프레임마다 이동 거리(선택 축만). 길이 = len(points). 첫 프레임은 다음 프레임과의 차."""
        n = len(points)
        if n < 2:
            return [0.0] * n

        def dist(p, q):
            return math.sqrt(sum((p[k] - q[k]) ** 2 for k in range(3) if axes[k]))

        out = [dist(points[i], points[i - 1]) for i in range(1, n)]
        return [out[0]] + out

    @staticmethod
    def smooth(values, window):
        """중심 이동 평균. 창 = 2 * (window // 2) + 1, 가장자리는 창이 줄어든다. window <= 1 이면 그대로."""
        n = len(values)
        h = max(0, int(window) // 2)
        if h == 0:
            return list(values)
        out = []
        for i in range(n):
            lo, hi = max(0, i - h), min(n, i + h + 1)
            out.append(sum(values[lo:hi]) / float(hi - lo))
        return out

    @staticmethod
    def still_spans(smoothed, start, threshold):
        """smoothed[i] < threshold 인 연속 구간 [(a, b)] (프레임 번호, a = start + i0)."""
        spans = []
        i0 = None
        for i, v in enumerate(smoothed):
            if v < threshold:
                if i0 is None:
                    i0 = i
            elif i0 is not None:
                spans.append((start + i0, start + i - 1))
                i0 = None
        if i0 is not None:
            spans.append((start + i0, start + len(smoothed) - 1))
        return spans

    @staticmethod
    def merge_gaps(spans, gap):
        """대안 B : 시간순 이웃 사이 움직인 프레임 수(a2 - b1 - 1) <= gap 이면 합친다(연쇄). 반환 (merged, merges)."""
        merged = []
        merges = []
        for a, b in spans:
            if merged and gap > 0 and (a - merged[-1][1] - 1) <= gap:
                prev = merged[-1]
                merges.append((prev, (a, b)))
                merged[-1] = (prev[0], b)
            else:
                merged.append((a, b))
        return merged, merges

    @staticmethod
    def split_spans(spans, min_span):
        """(apply, short) - 길이 b - a + 1 > min_span 이면 apply."""
        apply = [(a, b) for a, b in spans if (b - a + 1) > min_span]
        short = [(a, b) for a, b in spans if (b - a + 1) <= min_span]
        return apply, short

    @staticmethod
    def blend_start(a_prime, n, prev_end=None, clamp=True):
        """대안 A : t0 = a' - N, clamp 면 max(a' - N, 바로 앞 적용 구간의 끝)."""
        t0 = float(a_prime) - float(n)
        if clamp and prev_end is not None:
            t0 = max(t0, float(prev_end))
        return t0

    # ==================================================
    # 마야 - 샘플링 · 분석
    # ==================================================

    @staticmethod
    def sample_positions(objs, start, end, progress=None):
        """[start, end] 프레임마다 월드 위치 {obj: [(x, y, z), ...]}. currentTime 루프, undo 기록 끔, 시간 복원."""
        out = dict((o, []) for o in objs)
        frames = list(range(int(start), int(end) + 1))
        total = len(frames)
        now = cmds.currentTime(q=True)
        with _undo_off():
            try:
                with suspend_refresh():
                    for i, f in enumerate(frames):
                        cmds.currentTime(f)
                        for o in objs:
                            m = cmds.getAttr(o + ".worldMatrix[0]")
                            out[o].append((m[12], m[13], m[14]))
                        if progress:
                            progress(i + 1, total)
            finally:
                cmds.currentTime(now)
        return out

    @classmethod
    def analyze(cls, objs, start, end, axes=(True, True, True), smooth=DEFAULT_SMOOTH,
                threshold_pct=DEFAULT_THRESHOLD_PCT, merge_gap=DEFAULT_MERGE_GAP,
                min_span=DEFAULT_MIN_SPAN, progress=None):
        """오브젝트마다 {"speed", "smooth", "threshold", "max", "spans", "merges", "apply", "short", "still"}."""
        pos = cls.sample_positions(objs, start, end, progress)
        results = {}
        for o in objs:
            sp = cls.speeds(pos[o], axes)
            sm = cls.smooth(sp, smooth)
            mx = max(sm) if sm else 0.0
            thr = float(threshold_pct) / 100.0 * mx
            r = {"speed": sp, "smooth": sm, "threshold": thr, "max": mx, "spans": [], "merges": [],
                 "apply": [], "short": [], "still": mx <= 0.0}
            if mx > 0.0:
                raw = cls.still_spans(sm, int(start), thr)
                merged, merges = cls.merge_gaps(raw, int(merge_gap))
                ap, sh = cls.split_spans(merged, int(min_span))
                r.update(spans=raw, merges=merges, apply=ap, short=sh)
            results[o] = r
        return results

    # ==================================================
    # 마야 - 실행
    # ==================================================

    @staticmethod
    def _validate(objs, start, end, axes, translate, rotate):
        if not objs:
            return [], "[Warning] Fix Sliding: no objects in the list."
        missing = [o for o in objs if not cmds.objExists(o)]
        objs = [o for o in objs if cmds.objExists(o)]
        if not objs:
            return [], "[Warning] Fix Sliding: listed objects no longer exist in the scene."
        if int(end) <= int(start):
            return [], "[Warning] Fix Sliding: End must be after Start."
        if not any(axes):
            return [], "[Warning] Fix Sliding: check at least one speed component (X / Y / Z)."
        if translate is not None and not (translate or rotate):
            return [], "[Warning] Fix Sliding: check Translate and/or Rotate."
        note = ("[Warning] Fix Sliding: not in the scene, skipped: {0}".format(LayerKeyManager._brief(missing))
                if missing else "")
        return objs, note

    @staticmethod
    def layer_blend_status():
        """(ok, 레이어, N, 메시지) - Hot Key > Main 의 Layer Blend 설정이 쓸 수 있는가."""
        s = HoldLayerManager.load_settings()
        layer = (s.get("layer") or "").strip()
        n = int(s.get("offset", 10))
        root = LayerKeyManager.root_layer()
        if not layer:
            return (False, "", n, "[Warning] Fix Sliding: Layer Blend Key needs a layer - choose one in Hot Key > Main.")
        if not cmds.objExists(layer) or cmds.nodeType(layer) != "animLayer" or layer == root:
            return (False, layer, n, "[Warning] Fix Sliding: layer '{0}' (Hot Key > Main) not found.".format(layer))
        try:
            if cmds.animLayer(layer, q=True, lock=True):
                return (False, layer, n, "[Warning] Fix Sliding: layer '{0}' is locked.".format(layer))
        except Exception:                                   # noqa: BLE001
            pass
        return (True, layer, n, "")

    @staticmethod
    def hold_curves(obj, translate=True, rotate=True):
        """Hold 대상 커브 [(attr, curve)] - 보기 레이어(Hot Key > Main `Run only when viewing`, "" = 루트)의 T/R 커브."""
        view = HoldLayerManager.load_settings().get("view_layer", "") or ""
        root = LayerKeyManager.root_layer()
        layer = view or root
        out = []
        for attr in (T_ATTRS if translate else ()) + (R_ATTRS if rotate else ()):
            plug = "{0}.{1}".format(obj, attr)
            try:
                if cmds.getAttr(plug, lock=True):
                    continue
            except Exception:                               # noqa: BLE001
                continue
            if layer:
                crv = LayerKeyManager.layer_curve(plug, layer, root)
            else:
                crv = LayerKeyManager.plain_curve(plug)
            if crv:
                out.append((attr, crv))
        return out

    @staticmethod
    def _fmt_span(span):
        return "[{0}-{1}]".format(int(span[0]), int(span[1]))

    @classmethod
    def _span_lines(cls, o, r, min_span, merge_gap):
        if r["still"]:
            return ["[Warning] Fix Sliding: {0} does not move in the range. Skipped.".format(o)]
        lines = ["{0}: max {1:.4g} /f, threshold {2:.4g}".format(o, r["max"], r["threshold"])]
        for (s1, s2) in r["merges"]:
            lines.append("    merged {0} + {1} (gap {2} <= G {3})".format(
                cls._fmt_span(s1), cls._fmt_span(s2), int(s2[0] - s1[1] - 1), int(merge_gap)))
        if r["apply"]:
            lines.append("    apply: " + ", ".join(
                "{0} ({1} f)".format(cls._fmt_span(s), int(s[1] - s[0] + 1)) for s in r["apply"]))
        if r["short"]:
            lines.append("    skip (<= M {0} f): ".format(int(min_span)) + ", ".join(cls._fmt_span(s) for s in r["short"]))
        if not r["apply"] and not r["short"]:
            lines.append("    no still span")
        return lines

    @classmethod
    def preview(cls, objs, start, end, axes=(True, True, True), smooth=DEFAULT_SMOOTH,
                threshold_pct=DEFAULT_THRESHOLD_PCT, merge_gap=DEFAULT_MERGE_GAP,
                min_span=DEFAULT_MIN_SPAN, debug=True, progress=None):
        """키를 바꾸지 않고 구간만 로그. debug 면 _debug_speed (결과 = 예측: 적용 구간 속도 0). 반환 (results, lines)."""
        objs, note = cls._validate(objs, start, end, axes, None, None)
        if not objs:
            return {}, [note]
        cls._phase(progress, "Sampling")
        results = cls.analyze(objs, start, end, axes, smooth, threshold_pct, merge_gap, min_span, progress)
        lines = [note] if note else []
        for o in objs:
            lines += cls._span_lines(o, results[o], min_span, merge_gap)
        if debug:
            cls._phase(progress, "Debug")
            predicted = {}
            for o in objs:
                sp = list(results[o]["speed"])
                for a, b in results[o]["apply"]:
                    for f in range(int(a), int(b) + 1):
                        sp[f - int(start)] = 0.0
                predicted[o] = sp
            node = cls.write_debug(results, predicted, start, cls._info(start, end, smooth, threshold_pct,
                                                                         merge_gap, min_span, axes))
            lines.append("Debug curves: {0} (result = predicted)".format(node))
        n_apply = sum(len(results[o]["apply"]) for o in objs)
        lines.append("Fix Sliding preview: {0} object(s), {1} span(s) to fix (G={2}, M={3}).".format(
            len(objs), n_apply, int(merge_gap), int(min_span)))
        return results, lines

    @classmethod
    def run(cls, objs, start, end, axes=(True, True, True), smooth=DEFAULT_SMOOTH,
            threshold_pct=DEFAULT_THRESHOLD_PCT, min_span=DEFAULT_MIN_SPAN, merge_gap=DEFAULT_MERGE_GAP,
            translate=True, rotate=True, layer_blend=True, clamp_blend=True, lock_end=True,
            debug=True, progress=None):
        """정지 구간마다 Hold (+ Layer Blend Key). 한 번의 undo. 반환 (고친 구간 수, 로그 줄)."""
        objs, note = cls._validate(objs, start, end, axes, translate, rotate)
        if not objs:
            return 0, [note]
        lines = [note] if note else []
        n = 0
        if layer_blend:
            ok, layer, n, msg = cls.layer_blend_status()
            if not ok:
                return 0, lines + [msg]

        cls._phase(progress, "Sampling")
        results = cls.analyze(objs, start, end, axes, smooth, threshold_pct, merge_gap, min_span, progress)

        cls._phase(progress, "Applying")
        total = sum(len(results[o]["apply"]) for o in objs)
        done_spans = 0
        merges = 0
        short = 0
        with undo_chunk():
            for o in objs:
                r = results[o]
                lines += cls._span_lines(o, r, min_span, merge_gap)
                merges += len(r["merges"])
                short += len(r["short"])
                curves = [c for _a, c in cls.hold_curves(o, translate, rotate)]
                prev_end = None
                for (a, b) in r["apply"]:
                    # a' = [a, b] 안 키의 최소 시간 (Shift+A 의 range_start 와 같은 규칙) - Hold 전에
                    first = None
                    for crv in curves:
                        times = cmds.keyframe(crv, q=True, time=(a, b), timeChange=True) or []
                        if times:
                            first = min(times) if first is None else min(first, min(times))
                    a_p = float(a) if first is None else float(first)
                    cur = (HoldLayerManager.capture_current([o], frame=a_p, force=True)
                           if layer_blend else None)
                    held, skipped, _first = KeyframeManager.hold_range(curves, a, b)
                    text = "    {0} held {1} curve(s)".format(cls._fmt_span((a, b)), held)
                    if skipped:
                        text += " ({0} skipped: <2 keys in span)".format(skipped)
                    if layer_blend:
                        t0 = cls.blend_start(a_p, n, prev_end, clamp_blend)
                        _cnt, lmsg = HoldLayerManager.apply(
                            objects=[o], frame=a_p, current_values=cur, force=True,
                            ramp_start=t0, hold_end=(b if lock_end else None))
                        text += " | " + lmsg
                        if clamp_blend and t0 > a_p - n:
                            text += " (blend start clamped from f{0:g})".format(a_p - n)
                    lines.append(text)
                    prev_end = b
                    done_spans += 1
                    if progress:
                        progress(done_spans, total)

        if debug:
            cls._phase(progress, "Debug")
            pos = cls.sample_positions(objs, start, end)
            measured = dict((o, cls.speeds(pos[o], axes)) for o in objs)
            node = cls.write_debug(results, measured, start, cls._info(start, end, smooth, threshold_pct,
                                                                        merge_gap, min_span, axes))
            lines.append("Debug curves: {0} (result = measured after the fix)".format(node))

        lines.append("Fix Sliding: {0} object(s), {1} span(s) fixed, {2} merge(s) (G={3}), "
                     "{4} short span(s) skipped (M={5}).".format(
                         len(objs), done_spans, merges, int(merge_gap), short, int(min_span)))
        return done_spans, lines

    # ==================================================
    # 디버그 노드
    # ==================================================

    @staticmethod
    def _info(start, end, smooth, threshold_pct, merge_gap, min_span, axes):
        return "{0}-{1}, smooth {2}, threshold {3}%, G {4}, M {5}, axes {6}".format(
            int(start), int(end), int(smooth), threshold_pct, int(merge_gap), int(min_span),
            "".join(c for c, on in zip("XYZ", axes) if on))

    @staticmethod
    def _prefixes(objs):
        """오브젝트마다 어트리뷰트 접두사 (짧은 이름, `:` `|` -> `_`, 겹치면 _2 ...)."""
        out = {}
        used = set()
        for o in objs:
            base = re.sub(r"[^0-9A-Za-z_]", "_", o.split("|")[-1])
            if not base or not (base[0].isalpha() or base[0] == "_"):
                base = "o_" + base
            name, i = base, 2
            while name in used:
                name = "{0}_{1}".format(base, i)
                i += 1
            used.add(name)
            out[o] = name
        return out

    @classmethod
    def write_debug(cls, results, result_speeds, start, info=""):
        """_debug_speed 를 새로 만들고 오브젝트마다 speed / smooth / threshold / result 커브. undo 기록 안 남김."""
        import maya.api.OpenMaya as om
        import maya.api.OpenMayaAnim as oma

        objs = list(results)
        with _undo_off():
            if cmds.objExists(cls.DEBUG_NODE):
                cmds.delete(cls.DEBUG_NODE)
            node = cmds.createNode("transform", name=cls.DEBUG_NODE)
            cmds.addAttr(node, longName="info", dataType="string")
            cmds.setAttr(node + ".info", info, type="string")
            unit = om.MTime.uiUnit()
            for o, pre in cls._prefixes(objs).items():
                r = results[o]
                n = len(r["speed"])
                times = [om.MTime(float(start) + i, unit) for i in range(n)]
                series = (("speed", r["speed"]), ("smooth", r["smooth"]),
                          ("threshold", [r["threshold"]] * n), ("result", result_speeds.get(o, [])))
                for suffix, values in series:
                    attr = "{0}_{1}".format(pre, suffix)
                    cmds.addAttr(node, longName=attr, attributeType="double", keyable=True)
                    if not values:
                        continue
                    sel = om.MSelectionList()
                    sel.add("{0}.{1}".format(node, attr))
                    fn = oma.MFnAnimCurve()
                    fn.create(sel.getPlug(0), oma.MFnAnimCurve.kAnimCurveTU)
                    fn.addKeys(times, [float(v) for v in values],
                               oma.MFnAnimCurve.kTangentLinear, oma.MFnAnimCurve.kTangentLinear)
        return node

    @staticmethod
    def _phase(progress, name):
        hook = getattr(progress, "phase", None)
        if hook:
            hook(name)
