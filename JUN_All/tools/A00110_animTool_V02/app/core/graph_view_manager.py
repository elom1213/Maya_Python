# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-29
# A00110_animTool_V02 - Graph Editor 뷰 프레이밍 로직 (maya.cmds, UI 비의존)
#
# 선택 컨트롤러의 전체 키 구간(예: 0~6000f)을 다 보여주는 대신, 현재 프레임을
# 기준으로 앞/뒤 margin 프레임만 그래프 에디터에 확대해서 보여준다.
#   예) 현재 500f, margin 30  ->  [470f ~ 530f] 만 표시.

import maya.cmds as cmds


# Frame margin(±) 기본값. v02.30 에서 80 -> 30 (사용자 요청 - 보통 한 동작 안팎만 보면 된다).
# UI 스핀박스 초기값과 GraphFocusManager 의 getter 없을 때 폴백이 같은 값을 쓴다.
DEFAULT_FRAME_MARGIN = 30

# 그래프 에디터 아웃라이너의 애니메이션 레이어 필터(outlinerEditor -animLayerFilterOptions) 값.
# 마야 GE 의 View > Animation Layer Filter 메뉴가 바로 이 값을 바꾼다(createOutlinerPanelMenu.mel).
#   selected          : 레이어 에디터에서 **선택한** 레이어의 커브만
#   active            : **활성(preferred)** 레이어의 커브만
#   activeAndSelected : 둘 다
#   allAffecting      : 그 오브젝트에 영향을 주는 모든 레이어의 커브 (서로 겹쳐 보인다)
#   animLayerEditor   : 레이어 에디터 자체의 필터 설정(optionVar animLayerFilterOptions 1~4)을 따른다
LAYER_FILTER_MODES = ("selected", "active", "activeAndSelected", "allAffecting", "keep")
LAYER_FILTER_KEEP = "keep"          # GE 설정을 건드리지 않고 지금 값을 읽어서 따른다
_EDITOR_OPTVAR_TO_MODE = {1: "allAffecting", 2: "active", 3: "selected", 4: "activeAndSelected"}
_TIME_CURVE_TYPES = ("animCurveTL", "animCurveTA", "animCurveTU", "animCurveTT")


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
    def graph_outliners():
        """그래프 에디터 왼쪽 트리(outlinerEditor) 컨트롤 이름 목록 - 패널명 + 'OutlineEd'.
        애니메이션 레이어 필터(animLayerFilterOptions)는 이 컨트롤에 걸려 있다."""
        panels = cmds.getPanel(scriptType="graphEditor") or []
        return [p + "OutlineEd" for p in panels]

    # ------------------------------------------------------------------
    # 애니메이션 레이어
    # ------------------------------------------------------------------

    @staticmethod
    def anim_layers():
        """BaseAnimation 을 뺀 애니메이션 레이어들. 레이어가 없는 씬이면 빈 리스트."""
        root = cmds.animLayer(q=True, root=True)
        if not root:
            return []
        return [l for l in (cmds.ls(type="animLayer") or []) if l != root]

    @staticmethod
    def selected_layers():
        """레이어 에디터에서 선택한 레이어들(BaseAnimation 포함). 마야에는 전역 쿼리가 없어 레이어마다 묻는다."""
        return [l for l in (cmds.ls(type="animLayer") or []) if cmds.animLayer(l, q=True, selected=True)]

    @staticmethod
    def active_layers():
        """활성(preferred) 레이어들(BaseAnimation 포함) - 마야 UI 의 'Active' 가 이것이다(layerEditor.mel)."""
        return [l for l in (cmds.ls(type="animLayer") or []) if cmds.animLayer(l, q=True, preferred=True)]

    @staticmethod
    def editor_layer_filter(outliner):
        """그래프 에디터 아웃라이너의 지금 레이어 필터를 LAYER_FILTER_MODES 의 하나로 돌려준다.
        'animLayerEditor'(레이어 에디터 설정을 따름)면 optionVar animLayerFilterOptions(1~4)로 푼다."""
        try:
            value = cmds.outlinerEditor(outliner, q=True, animLayerFilterOptions=True)
        except RuntimeError:
            return "allAffecting"
        if value == "animLayerEditor":
            try:
                option = int(cmds.optionVar(q="animLayerFilterOptions") or 1)
            except (RuntimeError, TypeError, ValueError):
                option = 1
            return _EDITOR_OPTVAR_TO_MODE.get(option, "allAffecting")
        return value if value in LAYER_FILTER_MODES else "allAffecting"

    @staticmethod
    def resolve_layer_filter(mode, outliner=None):
        """사용자 모드 -> 실제로 적용할 필터 (GE 에 걸 값, 값 범위에 쓸 레이어 목록).

        반환: (filter, layers, note)
          filter : 'selected' | 'active' | 'activeAndSelected' | 'allAffecting'
          layers : 값 범위를 잴 레이어 목록(BaseAnimation 포함) - allAffecting 이면 None(전부)
          note   : 되돌린(fallback) 이유 문자열, 없으면 ""
        레이어가 없는 씬이면 언제나 allAffecting. 'selected' 인데 선택한 레이어가 없으면 활성 레이어로,
        그것도 없으면 allAffecting 으로 되돌린다 - GE 가 아무 커브도 안 보여 주는 빈 화면을 막는다.
        """
        if mode == LAYER_FILTER_KEEP:
            mode = GraphViewManager.editor_layer_filter(outliner) if outliner else "allAffecting"
        if not GraphViewManager.anim_layers():
            return ("allAffecting", None, "")

        selected = GraphViewManager.selected_layers()
        active = GraphViewManager.active_layers()
        note = ""
        if mode == "selected":
            if selected:
                return ("selected", selected, "")
            mode, note = "active", "no layer selected"
        if mode == "activeAndSelected":
            layers = list(dict.fromkeys(active + selected))
            if layers:
                return ("activeAndSelected", layers, "")
            mode, note = "active", "no layer active or selected"
        if mode == "active":
            if active:
                return ("active", active, note)
            note = (note + ", " if note else "") + "no active layer"
        return ("allAffecting", None, note)

    @staticmethod
    def apply_editor_layer_filter(outliner, layer_filter):
        """그래프 에디터 아웃라이너의 레이어 필터를 건다(View > Animation Layer Filter 와 같은 일)."""
        try:
            if cmds.outlinerEditor(outliner, q=True, animLayerFilterOptions=True) != layer_filter:
                cmds.outlinerEditor(outliner, e=True, animLayerFilterOptions=layer_filter)
            return True
        except RuntimeError:
            return False

    @staticmethod
    def curves_for_layers(sel, layers):
        """선택 오브젝트들의 **시간 기반** 애니메이션 커브 중, 주어진 레이어들에 속한 것만.

        layers 가 None 이면 모든 레이어(+ 베이스) 커브 전부. 'BaseAnimation' 이 layers 에 있으면
        어느 레이어에도 속하지 않은 커브(= 베이스 커브, 블렌드 노드 inputA 로 들어가는 것)를 더한다.

        ★ `cmds.keyframe(obj, q=True, name=True)` 는 **활성(preferred) 레이어의 커브만** 돌려준다
        (실측: Base 활성이면 베이스 커브, Layer1 활성이면 Layer1 커브). 그래서 GE 가 보여 주는
        커브와 어긋났다 - 여기서는 listHistory 로 블렌드 노드 위쪽까지 모든 커브를 모은 뒤 레이어로 거른다.
        """
        history = cmds.listHistory(sel, pruneDagObjects=True, leaf=False) or []
        all_curves = list(dict.fromkeys(cmds.ls(history, type=list(_TIME_CURVE_TYPES)) or []))
        if layers is None:
            return all_curves

        in_layer = {}
        for layer in GraphViewManager.anim_layers():
            for crv in (cmds.animLayer(layer, q=True, animCurves=True) or []):
                in_layer.setdefault(crv, set()).add(layer)

        root = cmds.animLayer(q=True, root=True)
        wanted = set(layers)
        picked = []
        for crv in all_curves:
            owners = in_layer.get(crv)
            if owners is None:
                if root in wanted:          # 베이스 커브
                    picked.append(crv)
            elif owners & wanted:
                picked.append(crv)
        return picked

    # 값 범위를 구할 때 커브를 시간축으로 샘플링하는 총 평가 횟수 상한.
    # (선택 오브젝트가 많아 커브 수가 많으면 커브당 샘플 수를 이 상한 안에서 줄인다.)
    _MAX_VALUE_SAMPLES = 4000

    @staticmethod
    def _value_range_in_window(start, end, layers=None):
        """선택 오브젝트들의 애니메이션 커브를 [start, end] 구간에서 '실제로 평가'해
        얻은 값의 (min, max). 구간에 키가 없어도 유효한 범위를 반환한다.

        layers : 값 범위를 잴 애니메이션 레이어 목록(BaseAnimation 포함). None 이면 전부.
                 그래프 에디터의 레이어 필터와 같은 커브만 재야 세로 맞춤이 화면과 일치한다.

        키 값만 보던 이전 방식은 구간 안에 키가 없으면(현재 프레임이 멀리 떨어진 두 키
        사이에 있을 때) 빈 값이 나와 세로축이 맞지 않았다. 여기서는 애니메이션 커브의
        `.output` 을 구간에 걸쳐 시간별로 평가하고(탄젠트 오버슛 포함), 구간 내 키 값도
        함께 반영해 항상 구간의 실제 상/하한을 얻는다. 커브가 하나도 없으면 None."""
        sel = cmds.ls(sl=True) or []
        if not sel:
            return None

        # 선택 오브젝트에 물린 애니메이션 커브 노드(레이어 필터 적용, 중복 제거).
        curves = GraphViewManager.curves_for_layers(sel, layers)
        if not curves:
            return None

        # 구간을 균일하게 샘플링(경계 포함). 커브가 많으면 커브당 샘플 수를 줄여
        # 총 평가 횟수를 _MAX_VALUE_SAMPLES 이내로 유지한다.
        span = end - start
        steps = max(2, min(120, GraphViewManager._MAX_VALUE_SAMPLES // len(curves)))
        if span > 0:
            sample_times = [start + span * i / steps for i in range(steps + 1)]
        else:
            sample_times = [start]

        vmin = None
        vmax = None

        def _acc(v):
            nonlocal vmin, vmax
            if v is None:
                return
            if vmin is None or v < vmin:
                vmin = v
            if vmax is None or v > vmax:
                vmax = v

        for crv in curves:
            out = crv + ".output"

            # 구간에 걸친 커브 값 (키가 없어도, 키 사이 오버슛도 커버).
            for t in sample_times:
                try:
                    _acc(cmds.getAttr(out, time=t))
                except (RuntimeError, ValueError):
                    continue

            # 샘플 사이에 낀 날카로운 키 값도 반영.
            for v in (cmds.keyframe(crv, q=True, time=(start, end), valueChange=True) or []):
                _acc(v)

        if vmin is None:
            return None

        return (vmin, vmax)

    @staticmethod
    def frame_around_current(margin, fit_value=True, value_pad_pct=10.0, layer_filter="selected"):
        """그래프 에디터를 현재 프레임 ± margin 구간으로 프레이밍한다.

        value_pad_pct : 세로(값) 축 위/아래 여백을 값 범위의 몇 %로 둘지(기본 10%).
                        구간 내 최댓값/최솟값이 뷰 위/아래 가장자리에 딱 붙지 않고
                        이만큼 여백을 두고 보이도록 한다.
        layer_filter  : 애니메이션 레이어가 있을 때 어느 레이어의 커브를 보이고 잴지
                        (LAYER_FILTER_MODES). 'keep' 이 아니면 그래프 에디터의
                        View > Animation Layer Filter 를 그 값으로 바꾼다. 세로 맞춤은
                        **그 필터로 보이는 커브만** 잰다 - 예전엔 활성 레이어 커브만 재서,
                        Layer1 을 선택하면 ±200 에 맞추는데 화면엔 베이스 ±400 커브도 겹쳐
                        보여 "너무 확대" 됐다.
        반환: (성공한 에디터 수, 메시지)
        """
        margin = abs(int(margin))
        cur = cmds.currentTime(q=True)
        start = cur - margin
        end = cur + margin

        editors = GraphViewManager.graph_editors()
        if not editors:
            return (0, "Graph Editor is not open.")

        # 레이어 필터 - GE 아웃라이너에 걸고, 같은 레이어 목록으로 값 범위를 잰다.
        outliners = GraphViewManager.graph_outliners()
        if layer_filter not in LAYER_FILTER_MODES:
            layer_filter = "selected"
        ge_filter, layers, note = GraphViewManager.resolve_layer_filter(
            layer_filter, outliners[0] if outliners else None)
        if layer_filter != LAYER_FILTER_KEEP and GraphViewManager.anim_layers():
            for outliner in outliners:
                GraphViewManager.apply_editor_layer_filter(outliner, ge_filter)

        # 세로(값) 범위 계산 (fit_value 이고 구간에 키가 있을 때만).
        # 구간 내 최댓값/최솟값 범위에 위/아래로 value_pad_pct % 여백을 두고 프레이밍한다
        # (값이 위아래 가장자리에 딱 붙지 않게). 평평한 구간(min==max)은 animView 가
        # 범위를 만들 수 없어, 값 크기에 비례한(또는 1.0) 최소 여백을 준다.
        v_kw = {}
        if fit_value:
            v_range = GraphViewManager._value_range_in_window(start, end, layers)
            if v_range is not None:
                v_min, v_max = v_range
                pad_frac = max(0.0, value_pad_pct) / 100.0
                if v_min == v_max:
                    pad = abs(v_min) * pad_frac or 1.0
                else:
                    pad = (v_max - v_min) * pad_frac
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

        msg = f"Graph focus: [{int(start)}-{int(end)}f]  (current {int(cur)}f  ±{margin}f)"
        if layers is not None:
            msg += "  layers: " + ", ".join(layers)
        elif GraphViewManager.anim_layers():
            msg += "  layers: all"
        if note:
            msg += f"  ({note} -> {ge_filter})"
        return (applied, msg)
