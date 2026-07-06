# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-06
# A00110_animTool - 선택 변경 시 그래프 에디터 자동 프레이밍 라이프사이클
#                   (maya.cmds, UI 비의존)
#
# 토글이 켜져 있는 동안 SelectionChanged 를 감시하다가, 선택이 바뀔 때마다
# 그래프 에디터를 현재 프레임 ± margin 구간으로 다시 프레이밍한다.
# 닫힐 때/끌 때 scriptJob 을 정리한다.
#
# 주의:
#  - 마야가 (Auto Frame 등으로) 선택 시 자체 프레이밍을 하므로, evalDeferred 로
#    한 틱 미뤄 마야 처리 뒤에 우리 프레이밍이 마지막에 적용되도록 한다.

import maya.cmds as cmds

from .graph_view_manager import GraphViewManager


class GraphFocusManager:
    """SelectionChanged scriptJob 으로 선택 시 그래프 에디터 자동 프레이밍을 관리."""

    def __init__(self):
        self._job = None
        self._margin_getter = None
        self._fit_getter = None
        self._pad_getter = None

    def is_active(self):
        return self._job is not None

    # --------------------------------------------------
    # install / uninstall
    # --------------------------------------------------

    def install(self, margin_getter, fit_getter=None, pad_getter=None):
        """SelectionChanged 감시를 시작한다.

        margin_getter : 호출 시 현재 margin(정수) 를 반환하는 콜러블.
        fit_getter    : 호출 시 세로 값 맞춤 여부(bool) 를 반환하는 콜러블(선택).
        pad_getter    : 호출 시 세로 여백 퍼센트(float) 를 반환하는 콜러블(선택).
        반환: (성공여부, 메시지)
        """
        self._margin_getter = margin_getter
        self._fit_getter = fit_getter
        self._pad_getter = pad_getter

        if self._job is not None and cmds.scriptJob(exists=self._job):
            return (True, "Graph focus already active.")

        self._job = cmds.scriptJob(
            event=["SelectionChanged", self._on_selection_changed],
            killWithScene=False,
        )

        # 토글을 켠 순간의 현재 선택에도 즉시 적용.
        return self.apply_now()

    def uninstall(self):
        """scriptJob 을 제거한다(멱등)."""
        if self._job is not None:
            try:
                if cmds.scriptJob(exists=self._job):
                    cmds.scriptJob(kill=self._job, force=True)
            except RuntimeError:
                pass
            self._job = None

    # --------------------------------------------------
    # 적용
    # --------------------------------------------------

    def _margin(self):
        try:
            return int(self._margin_getter()) if self._margin_getter else 80
        except (TypeError, ValueError):
            return 80

    def _fit_value(self):
        return bool(self._fit_getter()) if self._fit_getter else True

    def _pad_pct(self):
        try:
            return float(self._pad_getter()) if self._pad_getter else 10.0
        except (TypeError, ValueError):
            return 10.0

    def _on_selection_changed(self):
        # 마야 자체 프레이밍(Auto Frame 등) 뒤에 우리가 마지막으로 덮어쓰도록 defer.
        cmds.evalDeferred(self._apply_silent, lowestPriority=True)

    def _apply_silent(self):
        """scriptJob 경로: 로그 없이 조용히 프레이밍(그래프 에디터가 닫혀 있으면 무시).

        단, 그래프 에디터에서 '키가 선택돼 있으면' 자동 프레이밍을 건너뛴다.
        사용자가 특정 키를 선택해 f(Frame Selection) 로 그 범위만 보려는 상황에서,
        키 선택으로 발생한 SelectionChanged 의 지연 콜백이 뒤늦게 현재 프레임으로
        덮어쓰는 것을 막기 위함이다. (컨트롤러만 새로 선택했을 땐 선택 키가 없어 정상 동작.)"""
        try:
            if cmds.keyframe(q=True, selected=True, name=True):
                return
            GraphViewManager.frame_around_current(
                self._margin(), fit_value=self._fit_value(), value_pad_pct=self._pad_pct())
        except RuntimeError:
            pass

    def apply_now(self):
        """토글 ON / 값 변경 / 수동 버튼에서 즉시 한 번 프레이밍하고 결과 메시지를 반환."""
        count, msg = GraphViewManager.frame_around_current(
            self._margin(), fit_value=self._fit_value(), value_pad_pct=self._pad_pct()
        )
        return (count > 0, msg)
