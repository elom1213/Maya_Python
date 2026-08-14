# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-06
# A00110_animTool_V02 - 구간 한정 오일러 필터 핵심 로직 (maya.cmds, UI 비의존)
#
# 마야 그래프 에디터의 `Curves > Euler Filter` 는 선택한 컨트롤러의 **키가 찍힌 전 구간**을
# 한꺼번에 처리한다. 이 모듈은 그것을 **[Start, End] 구간에만** 적용하고 나머지 구간의 키는
# 손대지 않는다.
#
# 왜 마야 명령을 그대로 쓰는가
# --------------------------------
#   오일러 필터 자체(±360 언와인딩 + (x+180, 180-y, z+180) 플립 표현 선택)는 직접 구현할 수도
#   있지만, `cmds.filterCurve(filter="euler")` 는 **startTime / endTime 플래그를 실제로 존중한다**
#   (Maya 2024 headless 로 확인: 구간 밖 키는 값이 바뀌지 않음). 그래서 마야의 오일러 수식·탄젠트
#   처리를 그대로 쓰면서 구간만 제한한다 — 직접 구현보다 결과가 마야와 정확히 일치한다.
#
#   메뉴 명령이 전 구간을 처리하는 건 필터에 구간 개념이 없어서가 아니라 **MEL 이 구간을 안 넘겨서**다.
#
# 앵커(Anchor) — 구간 앞쪽 이음매
# --------------------------------
#   filterCurve 는 **구간 안의 첫 키를 기준(앵커)** 으로 삼아 그 뒤 키들을 맞춘다. 앵커 키 자체는
#   절대 바뀌지 않는다. 따라서 Start 를 플립 지점 뒤에 잡으면(예: 20f 에서 뒤집혔는데 구간을
#   [20-40] 로 잡으면) 구간 안 키들끼리는 이미 일관돼 있어 **아무것도 고쳐지지 않는다**.
#
#   그래서 `anchor_previous=True`(기본) 이면 필터 구간을 **Start 직전 키까지 뒤로 넓혀** 실행한다.
#   그 키가 앵커가 되므로 값이 바뀌지 않고, 결과적으로 **구간 앞쪽이 기존 애니메이션과 매끄럽게
#   이어진다**. 넓힌 구간 안에는 그 앵커 키 하나뿐이라 "구간 밖은 그대로" 라는 약속도 지켜진다.
#
# End 쪽 이음매(seam)
# --------------------------------
#   구간 뒤쪽은 원래대로 두므로, 구간 안 키가 ±360 만큼 옮겨졌다면 End 와 그 다음 키 사이에
#   점프가 생긴다. 이건 "일부 구간만 필터" 의 필연적 결과이므로 막지 않고 **로그로 알린다**.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


class EulerFilterManager:
    """리스트업한 오브젝트의 회전 커브에 **구간 한정** 오일러 필터를 적용한다.

    대상은 `rotateX / rotateY / rotateZ` 애님 커브 세 개다(오일러 필터는 회전 3축을 한 묶음으로
    봐야 의미가 있다). 세 축 중 하나라도 애님 커브가 없으면 그 오브젝트는 건너뛴다.
    """

    # 정수/실수 프레임 비교용 미세 오차
    EPS = 1e-4

    # 필터 대상 회전 어트리뷰트(마야 오일러 필터와 동일)
    ROTATE_ATTRS = ("rotateX", "rotateY", "rotateZ")

    # ------------------------------------------------------------------ 조회

    @classmethod
    def _rotate_curves(cls, obj):
        """obj 의 rotateX/Y/Z 애님 커브 이름 3개. 하나라도 없으면 (None, False, 사유).

        애니메이션 레이어가 있어도 `cmds.keyframe(plug, q=True, name=True)` 는 **지금 선택된
        레이어의 커브 하나**만 돌려준다(Maya 2024 headless 확인). 즉 마야의 오일러 필터와 같이
        **작업 중인 레이어에만** 적용된다. 그래도 커브가 여러 개 잡히는 경우를 대비해 첫 번째만
        쓰고 layered=True 로 알려, 호출측이 경고를 남길 수 있게 한다.
        """
        curves = []
        layered = False

        for attr in cls.ROTATE_ATTRS:
            plug = "{0}.{1}".format(obj, attr)
            if not cmds.objExists(plug):
                return (None, False, "no {0} attribute".format(attr))

            found = cmds.keyframe(plug, query=True, name=True) or []
            if not found:
                return (None, False, "no animation curve on {0}".format(attr))
            if len(found) > 1:
                layered = True
            curves.append(found[0])

        return (curves, layered, "")

    @classmethod
    def _snapshot(cls, curves):
        """커브별 (시간 리스트, 값 리스트). 필터 전/후 비교용."""
        snap = []
        for crv in curves:
            times = cmds.keyframe(crv, query=True, timeChange=True) or []
            values = cmds.keyframe(crv, query=True, valueChange=True) or []
            snap.append((list(times), list(values)))
        return snap

    @classmethod
    def _previous_key_time(cls, curves, start):
        """Start 직전(< Start) 키 시간 중 **가장 가까운 것**. 없으면 None.

        세 축의 키 시간이 어긋나 있어도(축마다 다른 프레임에 키) Start 에 가장 가까운 키를
        앵커로 삼는다 — 이음매를 만드는 건 결국 Start 바로 앞 키이기 때문이다.
        """
        best = None
        for crv in curves:
            times = cmds.keyframe(crv, query=True, timeChange=True) or []
            before = [t for t in times if t < start - cls.EPS]
            if not before:
                continue
            latest = max(before)
            best = latest if best is None else max(best, latest)
        return best

    # --------------------------------------------------- 씬에서 대상/구간 감지

    @staticmethod
    def selected_objects():
        """현재 씬에서 선택한 오브젝트 목록. 없으면 빈 리스트.

        원버튼("from Selection") 실행에서 **대상**을 얻는 통로다. 그래프 에디터에서 키를
        드래그 선택해도 오브젝트 선택은 유지되므로(키 선택은 별개다), 이 값이 곧
        "지금 작업 중인 컨트롤러들" 이다.
        """
        return cmds.ls(selection=True, long=False) or []

    @classmethod
    def selected_key_range(cls):
        """선택한 키프레임들의 (최소, 최대) 프레임(int). 선택 키가 없으면 None.

        `cmds.keyframe(q=True, selected=True)` 는 그래프 에디터/타임 슬라이더에서 선택된
        **모든** 키의 시간을 오브젝트·어트리뷰트에 무관하게 전역으로 돌려준다. 그래서 여러
        컨트롤러의 커브에 걸쳐 박스 드래그로 골라도 그 묶음 전체의 앞/뒤 프레임이 잡힌다.
        """
        try:
            times = cmds.keyframe(query=True, selected=True) or []
        except Exception:
            return None
        if not times:
            return None
        return (int(round(min(times))), int(round(max(times))))

    # ------------------------------------------------------------- 변화 집계

    @classmethod
    def _diff(cls, before, after, start, end):
        """필터 전/후 스냅샷 비교.

        반환: (바뀐 키 수, 구간 밖 키가 바뀌었는지, End 이후에 이음매가 생겼는지)

        '구간 밖 변경' 은 방어용 검사다. filterCurve 가 구간을 존중하는 걸 확인했지만,
        마야 버전이 달라 동작이 바뀌면 조용히 넘어가지 않고 경고가 뜨도록 남겨 둔다.
        """
        changed = 0
        outside = False
        seam = False

        for (times_b, vals_b), (_times_a, vals_a) in zip(before, after):
            if len(vals_b) != len(vals_a):
                # 키 개수가 달라지는 일은 없어야 한다(필터는 값만 바꾼다).
                outside = True
                continue

            last_in_range_changed = False
            has_key_after_end = False

            for t, vb, va in zip(times_b, vals_b, vals_a):
                after_end = t > end + cls.EPS
                if after_end:
                    has_key_after_end = True

                if abs(va - vb) <= cls.EPS:
                    continue

                changed += 1
                if t < start - cls.EPS or after_end:
                    outside = True
                else:
                    last_in_range_changed = True

            if last_in_range_changed and has_key_after_end:
                seam = True

        return (changed, outside, seam)

    # ------------------------------------------------------------------ 실행

    @classmethod
    def filter_range(cls, objects, start, end, anchor_previous=True):
        """[start, end] 구간의 회전 키에만 오일러 필터를 적용한다.

        objects        : 대상 오브젝트 이름 목록(리스트업된 항목).
        start / end    : 필터 구간(양 끝 포함).
        anchor_previous: True 면 Start 직전 키까지 구간을 넓혀 실행한다. 그 키가 앵커가 되어
                         값은 그대로 유지되고, 구간 앞쪽이 기존 애니메이션과 매끄럽게 이어진다.

        반환: (처리한 오브젝트 수, 메시지)
        """
        if not objects:
            return (0, "No objects in the list.")

        if end < start:
            return (0, "End must be greater than or equal to Start.")

        done = 0
        total_changed = 0
        skipped = []          # (obj, 사유)
        layered = []          # 애님 레이어로 커브가 여러 개인 오브젝트
        seams = []            # End 경계에 점프가 생긴 오브젝트
        outside = []          # 구간 밖 키까지 바뀐 오브젝트(있으면 안 됨)
        anchored = 0          # 앵커 덕분에 구간을 넓혀 실행한 오브젝트 수

        with undo_chunk():
            for obj in objects:

                if not cmds.objExists(obj):
                    skipped.append((obj, "missing in scene"))
                    continue

                curves, is_layered, reason = cls._rotate_curves(obj)
                if curves is None:
                    skipped.append((obj, reason))
                    continue
                if is_layered:
                    layered.append(obj)

                # 실제로 필터에 넘길 구간. 앵커 옵션이면 Start 직전 키까지 뒤로 넓힌다.
                filter_start = start
                if anchor_previous:
                    prev = cls._previous_key_time(curves, start)
                    if prev is not None:
                        filter_start = prev
                        anchored += 1

                # 구간 안에 키가 하나도 없으면 필터를 부를 이유가 없다.
                in_range = False
                for crv in curves:
                    if (cmds.keyframe(crv, query=True,
                                      time=(start, end),
                                      keyframeCount=True) or 0) > 0:
                        in_range = True
                        break
                if not in_range:
                    skipped.append((obj, "no rotation keys in range"))
                    continue

                before = cls._snapshot(curves)

                # 레퍼런스/잠금 커브 등으로 한 오브젝트가 실패해도 나머지는 계속 처리한다.
                try:
                    cmds.filterCurve(curves, filter="euler",
                                     startTime=filter_start, endTime=end)
                except Exception as exc:
                    skipped.append((obj, "filterCurve failed: {0}".format(exc)))
                    continue

                changed, went_outside, seam = cls._diff(
                    before, cls._snapshot(curves), start, end)

                total_changed += changed
                if went_outside:
                    outside.append(obj)
                if seam:
                    seams.append(obj)

                done += 1

        return (done, cls._build_message(
            done, total_changed, start, end, anchor_previous, anchored,
            skipped, layered, seams, outside))

    # ------------------------------------------------------------- 메시지

    @staticmethod
    def _name_list(names, limit=5):
        head = ", ".join(names[:limit])
        return head + (" ..." if len(names) > limit else "")

    @classmethod
    def _build_message(cls, done, changed, start, end, anchor_previous, anchored,
                       skipped, layered, seams, outside):

        if done == 0:
            if skipped:
                return "Euler filter: nothing to do. ({0} skipped: {1})".format(
                    len(skipped),
                    cls._name_list(["{0} ({1})".format(o, r) for o, r in skipped]))
            return "Euler filter: nothing to do."

        msg = "Euler filter: {0} object(s), {1} key(s) changed in [{2}-{3}f].".format(
            done, changed, start, end)

        if anchor_previous and anchored:
            msg += "  Anchored to the key before Start on {0} object(s).".format(anchored)
        elif not anchor_previous:
            msg += ("  Anchor OFF: the first key inside the range is the reference, "
                    "so a flip that starts before Start will not be fixed.")

        if changed == 0:
            msg += ("  Rotations were already continuous inside the range "
                    "(nothing to unwind).")

        if skipped:
            msg += "  Skipped {0}: {1}".format(
                len(skipped),
                cls._name_list(["{0} ({1})".format(o, r) for o, r in skipped]))

        if layered:
            msg += ("  [Warning] {0} object(s) have more than one rotation curve "
                    "(animation layers); only the first curve of each axis was "
                    "filtered: {1}").format(len(layered), cls._name_list(layered))

        if seams:
            msg += ("  [Warning] {0} object(s) now step at the End boundary "
                    "(keys after End were left untouched, as requested): {1}").format(
                        len(seams), cls._name_list(seams))

        if outside:
            msg += ("  [Warning] {0} object(s) changed keys OUTSIDE the range - "
                    "unexpected for this Maya version: {1}").format(
                        len(outside), cls._name_list(outside))

        return msg
