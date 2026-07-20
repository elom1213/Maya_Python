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
        # 지금 씬에 적용돼 있는 offset (미리보기 포함, undo 큐에 없을 수 있음)
        self.applied = 0
        # undo 큐에 '기록까지 끝난' 마지막 offset. 미리보기는 항상 이 값을 기준으로
        # 되돌린 뒤 다시 기록한다(그래야 Ctrl+Z 가 정확히 이 값으로 돌아온다).
        self.settled = 0
        # 씬이 세션의 가정과 어긋났는지(예: 사용자가 Ctrl+Z) 확인하는 탐침.
        # 첫 '움직이는' 항목(index>0)의 구간 내 첫 키를 기준으로 삼는다.
        self.probe_plug = ""
        self.probe_index = 0
        self.probe_base = 0.0

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
        session._set_probe()

        msg = "Stagger session: {0} object(s), range [{1}-{2}f].".format(
            len(entries), start, end)
        if skipped:
            msg += "  ({0} skipped: missing or no keys)".format(len(skipped))
        if risky:
            msg += ("  WARNING: {0} object(s) have keys outside the range; "
                    "shifted keys may overwrite them: {1}").format(
                        len(risky), ", ".join(risky[:5]) + (" ..." if len(risky) > 5 else ""))
        return (session, msg)

    # ------------------------------------------------------- 씬 동기화 확인(탐침)

    def _set_probe(self):
        """세션의 가정이 아직 맞는지 확인할 '탐침 키' 를 잡아 둔다.

        첫 번째로 '실제 움직이는' 항목(index > 0)의 **구간 안 첫 키**를 기준으로 삼는다.
        (index 0 은 절대 안 움직이므로 탐침이 될 수 없다.)
        """
        for idx, obj in self.entries:
            if idx <= 0:
                continue
            for plug in self._target_plugs(obj, self.attrs):
                times = cmds.keyframe(
                    plug, q=True, time=(self.start, self.end), timeChange=True) or []
                if times:
                    self.probe_plug = plug
                    self.probe_index = idx
                    self.probe_base = min(times)
                    return

    def scene_in_sync(self):
        """씬이 세션의 가정(applied)과 일치하는가.

        사용자가 Ctrl+Z 로 되돌리면 씬은 이전 상태인데 세션은 그걸 모른다. 그 상태로 계속
        밀면 엉뚱한 구간을 건드리게 되므로, 탐침 키가 '있어야 할 자리' 에 있는지 확인한다.
        어긋나면 호출측(UI)이 세션을 버리고 새로 만든다.
        """
        if not self.probe_plug:
            return True
        if not cmds.objExists(self.probe_plug):
            return False

        expected = self.probe_base + self.probe_index * self.applied
        hits = cmds.keyframe(
            self.probe_plug, q=True,
            time=(expected - self.EPS, expected + self.EPS),
            timeChange=True) or []
        return bool(hits)

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
        """슬라이더/스핀박스를 움직이는 동안의 즉시 반영. undo 큐에 안 올라간다.

        조작이 멎으면 UI 가 settle() 을 불러 '한 덩어리' 로 undo 큐에 기록한다.
        (드래그 한 번에 undo 항목 수백 개가 쌓이는 걸 막는다.)
        """
        with _undo_disabled():
            return self._shift_to(offset)

    def settle(self, offset):
        """지금까지의 미리보기를 undo 큐에 **한 항목으로** 기록한다. 반환: (이동 수, 메시지)

        핵심: undo 는 '그 명령의 역연산' 을 현재 상태에 적용한다. 그래서 기록 전에 반드시
        **마지막으로 기록된 상태(settled)로 되돌린 뒤**(undo 미기록) 거기서 offset 까지
        한 번에 이동시켜야, Ctrl+Z 가 정확히 settled 로 돌아온다.
        (미리보기 값이 남은 채 기록하면 Ctrl+Z 가 미리보기 상태로 돌아가 버린다 —
         A00380_MeshTool 에서 검증한 restore-before-commit 패턴)

        settled 가 0 인 첫 기록이면 Ctrl+Z = 원위치 = Reset 과 같은 결과가 된다.
        """
        if offset == self.settled:
            # 기록할 변화가 없다. 혹시 미리보기가 떠 있으면 조용히 맞춰만 둔다.
            if self.applied != self.settled:
                with _undo_disabled():
                    self._shift_to(self.settled)
            return (0, "")

        with _undo_disabled():
            self._shift_to(self.settled)

        with undo_chunk():
            moved = self._shift_to(offset)

        previous = self.settled
        self.settled = offset

        scope = ("channels: " + ", ".join(self.attrs)) if self.attrs else "all curves"
        return (
            moved,
            "Stagger offset {0:+d}f on {1} object(s) in [{2}-{3}f]  ({4})  "
            "[Ctrl+Z -> {5:+d}f]".format(
                offset, len(self.entries), self.start, self.end, scope, previous)
        )

    def restore(self):
        """세션 시작 상태(offset 0)로 되돌린다.

        undo 큐에 이미 기록된 게 있으면(settled != 0) 이 되돌리기도 **기록해야** 큐가
        어긋나지 않는다. 아무것도 기록된 적 없으면 settle(0) 은 미리보기만 되돌리고
        undo 항목을 만들지 않는다.
        """
        return self.settle(0)

    # 하위호환: 예전 이름(commit)으로도 부를 수 있게 둔다.
    commit = settle
