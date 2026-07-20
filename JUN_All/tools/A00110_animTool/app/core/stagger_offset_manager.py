# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-20
# A00110_animTool - Stagger Offset (리스트 순서대로 계단식 키 오프셋) 핵심 로직 (maya.cmds, UI 비의존)
#
# 리스트업한 컨트롤러들의 [start, end] 구간 키를, **리스트 순서 × offset** 만큼 계단식으로 민다.
#
#   리스트 0번 : +0 * offset   (제자리)
#   리스트 1번 : +1 * offset
#   리스트 2번 : +2 * offset   ...
#
# 예) ctl_01/02/03 모두 0~5f 에 키, 구간 0~5f, offset 3
#     -> [0, 5] / [3, 8] / [6, 11]
#
# 팔로우스루·웨이브(순차 지연) 를 만들 때 쓰는 조작으로, 스핀박스로 offset 을 바꾸면
# 값이 누적되지 않고 **항상 원래 위치 기준**의 결과가 즉시 보이도록 세션으로 관리한다.
#
# 동작 방식(중요):
#   키 이동은 cmds.keyframe(relative=True, timeChange=) '상대 이동' 하나만 쓴다.
#   커브를 지웠다 다시 만들지 않으므로 **탄젠트/인피니티/애님 레이어가 그대로 보존**된다.
#   (cutKey 로 비우고 setKeyframe 으로 재생성하면 커브 노드가 새로 만들어져 애님 레이어
#    소속이 바뀔 수 있다. 그래서 재생성 방식은 쓰지 않는다.)
#
#   미리보기는 undo 기록을 끄고(_undo_disabled) '지금 적용된 값과의 차이'만 이동시킨다.
#   i 번째 오브젝트의 키는 항상 [start + i*applied, end + i*applied] 에 있으므로,
#   그 구간을 i*delta 만큼 밀면 [start + i*new, end + i*new] 가 된다.
#
# 주의(덮어쓰기): 구간 밖에 키가 있는 오브젝트는, 밀려온 키가 그 위에 얹히면서 원래 키를
#   덮어쓸 수 있다(마야의 키 이동 기본 동작). 세션 시작 시 그런 오브젝트를 미리 찾아 경고한다.
#   Apply 로 확정한 결과는 undo 청크 하나라 Ctrl+Z 로 전부 되돌아가지만, 미리보기 상태에서
#   Reset 으로 되돌릴 때는 덮어써 사라진 키까지는 복구되지 않는다.

import contextlib

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk
from .keyframe_manager import KeyframeManager


@contextlib.contextmanager
def _undo_disabled():
    """블록 안의 cmds 호출을 undo 큐에 남기지 않는다 (미리보기용).

    stateWithoutFlush 는 "큐를 비우지 않고" undo 기록만 잠시 끈다. state=False 를 쓰면
    지금까지 쌓인 undo 히스토리가 통째로 날아가므로 반드시 이쪽을 쓴다.
    예외가 나도 finally 에서 다시 켜, undo 가 꺼진 채 남는 사고를 막는다.
    (A00380_MeshTool 에서 검증한 패턴과 동일.)
    """

    cmds.undoInfo(stateWithoutFlush=False)
    try:
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=True)


class StaggerOffsetSession(object):
    """계단식 오프셋 '한 세션'. 스핀박스를 돌리는 동안의 상태를 들고 있는다.

    세션은 (오브젝트 순서 + 구간 + 채널 스코프) 를 시작 시점에 고정한다. 리스트나 구간이
    바뀌면 세션을 버리고 새로 만들어야 한다(UI 가 그렇게 한다).
    """

    # 정수/실수 프레임 비교용 미세 오차
    EPS = 1e-4

    def __init__(self, entries, start, end, attrs, risky=None, skipped=None):
        # entries: [(리스트에서의 원래 index, 오브젝트 이름), ...]
        # 오프셋 배수는 '리스트 위치' 라서, 중간 항목이 빠져도 뒤 항목의 배수가 당겨지지
        # 않도록 원래 index 를 그대로 들고 다닌다.
        self.entries = list(entries)
        self.start = start
        self.end = end
        self.attrs = list(attrs or [])
        # 구간 밖에도 키가 있어 덮어쓰기가 일어날 수 있는 오브젝트 이름들
        self.risky = list(risky or [])
        # 씬에 없거나 키가 없어 제외된 항목들
        self.skipped = list(skipped or [])
        # 지금 씬에 적용돼 있는 offset (미리보기 포함)
        self.applied = 0

    @property
    def objects(self):
        """세션이 실제로 다루는 오브젝트 이름 목록."""
        return [obj for _i, obj in self.entries]

    # ------------------------------------------------------------------ 생성

    @staticmethod
    def _target_plugs(obj, attrs):
        """오브젝트의 대상 애니메이션 플러그(키가 1개 이상인 것)를 반환.

        attrs 가 있으면 그 채널만, 없으면 listAnimatable 전체에서 키 있는 것만.
        (OffsetHoldManager 와 동일한 채널 스코프 규칙)
        """
        if attrs:
            candidates = ["{0}.{1}".format(obj, at) for at in attrs]
        else:
            candidates = cmds.listAnimatable(obj) or []

        plugs = []
        for plug in candidates:
            if not cmds.objExists(plug):
                continue
            if (cmds.keyframe(plug, q=True, keyframeCount=True) or 0) > 0:
                plugs.append(plug)
        return plugs

    @classmethod
    def create(cls, objects, start, end):
        """세션 생성. 반환: (session 또는 None, 메시지)

        리스트에 있지만 씬에 없거나 키가 없는 오브젝트는 제외한다. 순서는 리스트 순서를
        그대로 유지한다 — 오프셋 배수(i)가 그 순서에서 나오기 때문이다.
        """
        if not objects:
            return (None, "No objects in the list.")

        if end < start:
            return (None, "End must be greater than or equal to Start.")

        # 채널 스코프는 세션 시작 시점에 고정한다(도중에 채널박스 선택이 바뀌어도 흔들리지 않게).
        attrs = KeyframeManager.get_target_channels()

        entries = []
        risky = []
        skipped = []
        for idx, obj in enumerate(objects):
            if not cmds.objExists(obj):
                skipped.append(obj)
                continue

            plugs = cls._target_plugs(obj, attrs)
            if not plugs:
                skipped.append(obj)
                continue

            # index 는 '리스트에서의 위치' 를 그대로 쓴다. 빠진 항목이 있어도 뒤 항목의
            # 오프셋 배수가 당겨지지 않아, 리스트를 보고 예상한 결과와 어긋나지 않는다.
            entries.append((idx, obj))

            # 구간 '밖' 에 키가 있으면, 밀려온 키가 그 위를 덮을 수 있다.
            for plug in plugs:
                times = cmds.keyframe(plug, q=True, timeChange=True) or []
                if any(t < start - cls.EPS or t > end + cls.EPS for t in times):
                    risky.append(obj)
                    break

        if not entries:
            return (None, "No animated objects in the list. (missing in scene, or no keys)")

        session = cls(entries, start, end, attrs, risky, skipped)

        msg = "Stagger session: {0} object(s), range [{1}-{2}f].".format(
            len(entries), start, end)
        if skipped:
            msg += "  ({0} skipped: missing or no keys)".format(len(skipped))
        if risky:
            msg += ("  WARNING: {0} object(s) have keys outside the range; "
                    "shifted keys may overwrite them: {1}").format(
                        len(risky), ", ".join(risky[:5]) + (" ..." if len(risky) > 5 else ""))
        return (session, msg)

    # ------------------------------------------------------------------ 이동

    def _shift_to(self, new_offset):
        """지금 적용값(applied) 에서 new_offset 으로 '차이만큼' 이동한다.

        i 번째 오브젝트의 키는 [start + i*applied, end + i*applied] 에 있으므로,
        그 구간을 i*delta 만큼 밀면 정확히 [start + i*new, end + i*new] 가 된다.
        (원래 위치에서 다시 계산하므로 스핀박스를 왕복해도 값이 누적되지 않는다.)

        반환: 실제로 이동시킨 오브젝트 수
        """
        delta = new_offset - self.applied
        if delta == 0:
            return 0

        kw = {"attribute": self.attrs} if self.attrs else {}

        moved = 0
        for i, obj in self.entries:
            step = i * delta
            if step == 0:              # 0번 오브젝트는 언제나 제자리
                continue
            if not cmds.objExists(obj):
                continue

            cur_start = self.start + i * self.applied
            cur_end = self.end + i * self.applied

            cmds.keyframe(
                obj,
                edit=True,
                time=(cur_start, cur_end),
                relative=True,
                timeChange=step,
                **kw
            )
            moved += 1

        self.applied = new_offset
        return moved

    def preview(self, offset):
        """미리보기. undo 큐에 안 올라간다."""
        with _undo_disabled():
            return self._shift_to(offset)

    def restore(self):
        """미리보기를 세션 시작 상태(offset 0)로 되돌린다. undo 큐에 안 올라간다."""
        with _undo_disabled():
            return self._shift_to(0)

    def commit(self, offset):
        """확정 기록. Ctrl+Z 한 번으로 되돌아간다. 반환: (이동 수, 메시지)

        미리보기로 이미 키가 옮겨져 있으면 그 상태가 undo 기준이 되어 Ctrl+Z 가 미리보기
        상태로 돌아가 버린다. 그래서 **원위치로 되돌린 뒤** undo 청크 안에서 한 번에 적용한다.
        (A00380_MeshTool 에서 검증한 restore-before-commit 패턴)
        """
        if offset == 0:
            return (0, "Offset is 0, nothing to apply.")

        self.restore()

        with undo_chunk():
            moved = self._shift_to(offset)

        scope = ("channels: " + ", ".join(self.attrs)) if self.attrs else "all curves"
        return (
            moved,
            "Stagger offset {0:+d}f applied to {1} object(s) in [{2}-{3}f]  ({4})".format(
                offset, len(self.entries), self.start, self.end, scope)
        )
