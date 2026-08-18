# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00450_manipulatorTool core - 매니퓰레이터(이동/회전/스케일 축) 굵기 조절. UI 비의존.
#
# ## 마야가 실제로 무엇을 조절할 수 있는가 (Maya 2024 mayapy 로 실측)
#
#   cmds.manipOptions -lineSize     축 선의 굵기.        기본 2.0  / 1.0 미만은 전부 1.0 으로 잘림
#   cmds.manipOptions -linePick     축의 클릭 판정 반경. 기본 4.0  / 1.0 미만은 1.0 으로 잘림
#   cmds.manipOptions -handleSize   핸들(화살촉 등) 크기. 기본 30.0 / 0 은 무시(값 유지)
#   cmds.manipOptions -scale        매니퓰레이터 전체 배율. 기본 1.0  / 0 은 무시(값 유지)
#   cmds.manipOptions -forceRefresh 지금 떠 있는 매니퓰레이터를 다시 그린다(라이브 반영용)
#
#   위쪽 한계는 없다시피 하다(lineSize 200 도 그대로 들어간다). 슬라이더 상한은 실용 범위로 정한 값.
#
# ## ⚠️ 이동/회전/스케일별 굵기는 마야에 없다
#
# `manipMoveContext` / `manipRotateContext` / `manipScaleContext` 의 플래그에는 크기·굵기 관련이
# 하나도 없다(activeHandle 류뿐). **`manipOptions` 는 전역**이라 세 도구가 같은 값을 공유한다.
#
# 그래서 이 툴은 값을 셋으로 나눠 들고 있다가 **도구가 바뀌는 순간 그 도구의 값을 전역에 밀어 넣는다.**
# 사용자에게는 "이동/회전/스케일 굵기를 따로 정한다"로 보이지만, 실제로는 전역 값 하나를
# 도구 전환 시점에 갈아 끼우는 것이다. 마야가 그 이상을 제공하지 않는다.
#
# ## 굵게 한다고 잘 집히는 것은 아니다
#
# `lineSize` 는 **그려지는 두께**이고, 실제로 클릭이 먹는 범위는 `linePick` 이다. 둘은 따로다.
# "매니퓰레이터가 잘 안 집힌다" 가 목적이라면 `linePick` 을 같이 올려야 한다.

import maya.cmds as cmds


# =========================================================================
# 상수
# =========================================================================

# 도구 구분 키
MOVE = "move"
ROTATE = "rotate"
SCALE = "scale"
TOOLS = (MOVE, ROTATE, SCALE)

TOOL_LABELS = {MOVE: "Move", ROTATE: "Rotate", SCALE: "Scale"}

# 마야 기본값(실측). 실제 복구는 툴을 열 때 캡처한 값으로 한다.
DEFAULT_LINE_SIZE = 2.0
DEFAULT_LINE_PICK = 4.0
DEFAULT_HANDLE_SIZE = 30.0
DEFAULT_MANIP_SCALE = 1.0

# 슬라이더 범위. 하한은 마야가 자르는 값, 상한은 실용 범위.
LINE_SIZE_MIN, LINE_SIZE_MAX = 1.0, 20.0
LINE_PICK_MIN, LINE_PICK_MAX = 1.0, 30.0
HANDLE_SIZE_MIN, HANDLE_SIZE_MAX = 5.0, 120.0
MANIP_SCALE_MIN, MANIP_SCALE_MAX = 0.2, 5.0

# manipOptions 플래그 <-> snapshot 키
_FLAGS = ("lineSize", "linePick", "handleSize", "scale")


# =========================================================================
# manipOptions 얇은 래퍼
# =========================================================================

def _query(flag):
    """manipOptions 질의는 리스트로 돌아온다."""
    value = cmds.manipOptions(query=True, **{flag: True})

    if isinstance(value, (list, tuple)):
        return value[0] if value else None

    return value


def _apply(flag, value):
    """값을 쓰고, 마야가 실제로 받아들인 값을 되돌려준다(하한 클램프 때문에 되읽는다)."""
    cmds.manipOptions(**{flag: float(value)})

    refresh()

    return float(_query(flag))


def refresh():
    """지금 떠 있는 매니퓰레이터를 다시 그린다. 슬라이더 라이브 반영용."""
    try:
        cmds.manipOptions(forceRefresh=True)
    except Exception:
        pass


def get_line_size():
    return float(_query("lineSize"))


def set_line_size(value):
    """축 굵기를 쓴다. 1.0 미만은 마야가 1.0 으로 자른다."""
    return _apply("lineSize", value)


def get_pick_radius():
    return float(_query("linePick"))


def set_pick_radius(value):
    return _apply("linePick", value)


def get_handle_size():
    return float(_query("handleSize"))


def set_handle_size(value):
    return _apply("handleSize", value)


def get_manip_scale():
    return float(_query("scale"))


def set_manip_scale(value):
    return _apply("scale", value)


def snapshot():
    """지금 값을 담아 둔다(Reset 이 되돌릴 기준)."""
    return {flag: float(_query(flag)) for flag in _FLAGS}


def restore(state):
    """snapshot 으로 담아 둔 값으로 되돌린다."""
    if not state:
        return None

    for flag in _FLAGS:

        if flag in state:
            cmds.manipOptions(**{flag: float(state[flag])})

    refresh()

    return snapshot()


# =========================================================================
# 활성 도구 판별
# =========================================================================

def current_tool():
    """지금 활성 도구가 이동/회전/스케일 중 무엇인가. 아니면 None.

    컨텍스트 이름은 `moveSuperContext` / `RotateSuperContext` / `scaleSuperContext` 인데
    **회전만 대문자로 시작한다.** 그래서 이름을 소문자로 낮춰 부분 일치로 본다.
    (컨텍스트는 GUI 마야에서만 생성된다 - headless 에서는 항상 None)
    """
    try:
        ctx = cmds.currentCtx() or ""
    except Exception:
        return None

    name = ctx.lower()

    for tool in TOOLS:

        if tool in name:
            return tool

    return None


# =========================================================================
# 도구별 굵기 상태
# =========================================================================

class ManipState(object):
    """이동/회전/스케일 굵기를 따로 들고 있다가, 활성 도구의 값을 전역에 밀어 넣는다.

    마야에는 도구별 굵기가 없으므로(위 주석 참고) 이 클래스가 그 환상을 만든다.
    """

    def __init__(self):

        # 툴을 연 시점의 값. Reset 은 여기로 되돌린다.
        self.baseline = snapshot()

        base_size = self.baseline.get("lineSize", DEFAULT_LINE_SIZE)

        self.sizes = {tool: base_size for tool in TOOLS}

        self._job = None

    # ------------------------------------------------------------------
    # 굵기
    # ------------------------------------------------------------------

    def get_size(self, tool):
        return self.sizes.get(tool, DEFAULT_LINE_SIZE)

    def set_size(self, tool, value):
        """도구의 굵기를 기억하고, 그 도구가 지금 활성이면 즉시 반영한다.

        Returns: 마야에 실제로 들어간 값(비활성 도구면 기억한 값 그대로)
        """
        if tool not in self.sizes:
            return None

        self.sizes[tool] = float(value)

        if current_tool() == tool:
            return set_line_size(value)

        return float(value)

    def set_all_sizes(self, value):
        """세 도구를 한 값으로 맞춘다(마스터 슬라이더)."""
        for tool in TOOLS:
            self.sizes[tool] = float(value)

        return set_line_size(value)

    def apply_for_current(self):
        """활성 도구에 해당하는 굵기를 전역에 밀어 넣는다.

        Returns: (적용한 도구, 적용된 값) - 활성 도구가 셋 중 아니면 (None, 현재값)
        """
        tool = current_tool()

        if tool is None:
            return None, get_line_size()

        return tool, set_line_size(self.sizes[tool])

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self):
        """툴을 연 시점의 값으로 전부 되돌린다."""
        state = restore(self.baseline)

        base_size = self.baseline.get("lineSize", DEFAULT_LINE_SIZE)

        for tool in TOOLS:
            self.sizes[tool] = base_size

        return state

    # ------------------------------------------------------------------
    # 도구 전환 감시
    # ------------------------------------------------------------------

    def start_watch(self, callback=None):
        """도구가 바뀔 때마다 그 도구의 굵기를 전역에 밀어 넣는 scriptJob 을 건다.

        callback : 적용 후 호출(UI 갱신용). 인자 없음.
        Returns  : scriptJob 번호 (실패하면 None)
        """
        self.stop_watch()

        def _on_tool_changed():

            self.apply_for_current()

            if callback:
                callback()

        try:
            self._job = cmds.scriptJob(event=["ToolChanged", _on_tool_changed], protected=False)
        except Exception:
            self._job = None

        return self._job

    def stop_watch(self):
        """창을 닫을 때 반드시 부른다. 안 그러면 죽은 UI 를 가리키는 job 이 남는다."""
        if self._job is None:
            return

        try:
            if cmds.scriptJob(exists=self._job):
                cmds.scriptJob(kill=self._job, force=True)
        except Exception:
            pass

        self._job = None
