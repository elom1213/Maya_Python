# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-06
# A00110_animTool - Graph Editor 뷰 프레이밍 로직 (maya.cmds, UI 비의존)
#
# 선택 컨트롤러의 전체 키 구간(예: 0~6000f)을 다 보여주는 대신, 현재 프레임을
# 기준으로 앞/뒤 margin 프레임만 그래프 에디터에 확대해서 보여준다.
#   예) 현재 500f, margin 80  ->  [420f ~ 580f] 만 표시.

import maya.cmds as cmds


class GraphViewManager:
    """그래프 에디터의 표시 시간 구간(가로)을 현재 프레임 ± margin 으로 맞춘다.

    가로(시간)는 항상 현재 프레임 기준 ± margin 으로 설정하고, 세로(값)는
    fit_value 가 True 면 그 구간 안에 있는 선택 오브젝트 키 값의 범위에 맞춘다
    (구간에 키가 없으면 세로는 건드리지 않는다).
    """

    @staticmethod
    def graph_editors():
        """현재 열려 있는 그래프 에디터의 animCurveEditor 컨트롤 이름 목록.

        graphEditor 패널명(예: 'graphEditor1')에 'GraphEd' 를 붙인 것이 실제
        커브 에디터 컨트롤(예: 'graphEditor1GraphEd')이다.
        """
        panels = cmds.getPanel(scriptType="graphEditor") or []
        return [p + "GraphEd" for p in panels]

    @staticmethod
    def _value_range_in_window(start, end):
        """선택 오브젝트들의 애니메이션 커브 중 [start, end] 구간 키 값의 (min, max).
        해당 구간에 키가 하나도 없으면 None."""
        sel = cmds.ls(sl=True) or []
        if not sel:
            return None

        vals = cmds.keyframe(sel, q=True, time=(start, end), valueChange=True) or []
        if not vals:
            return None

        return (min(vals), max(vals))

    @staticmethod
    def frame_around_current(margin, fit_value=True):
        """그래프 에디터를 현재 프레임 ± margin 구간으로 프레이밍한다.

        반환: (성공한 에디터 수, 메시지)
        """
        margin = abs(int(margin))
        cur = cmds.currentTime(q=True)
        start = cur - margin
        end = cur + margin

        editors = GraphViewManager.graph_editors()
        if not editors:
            return (0, "Graph Editor is not open.")

        # 세로(값) 범위 계산 (fit_value 이고 구간에 키가 있을 때만).
        v_kw = {}
        if fit_value:
            v_range = GraphViewManager._value_range_in_window(start, end)
            if v_range is not None:
                v_min, v_max = v_range
                if v_min == v_max:
                    # 평평한 구간 -> 위아래로 약간의 여백을 준다.
                    pad = abs(v_min) * 0.1 or 1.0
                else:
                    pad = (v_max - v_min) * 0.1
                v_kw = {"minValue": v_min - pad, "maxValue": v_max + pad}

        applied = 0
        for ed in editors:
            try:
                cmds.animView(ed, startTime=start, endTime=end, **v_kw)
                applied += 1
            except RuntimeError:
                # 커브 에디터가 아직 완전히 초기화되지 않은 경우 등 -> 건너뛴다.
                pass

        if not applied:
            return (0, "Graph Editor is not open.")

        return (
            applied,
            f"Graph focus: [{int(start)}-{int(end)}f]  (current {int(cur)}f  ±{margin}f)",
        )
