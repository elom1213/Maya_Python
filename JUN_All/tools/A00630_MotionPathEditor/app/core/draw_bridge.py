# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 툴 <-> 플러그인 데이터 다리
"""
`cmds.loadPlugin` 으로 읽힌 플러그인 모듈은 툴이 `import` 한 모듈과 **다른 객체**다(그리고 `__file__` 이 없다 —
메모 maya-loadplugin-no-file). 그래서 둘이 함께 보는 상태는 이 모듈 하나에 두고, 플러그인도 이 모듈을 **정식 경로**
(`tools.A00630_MotionPathEditor.app.core.draw_bridge`)로 import 한다. A00180 의 undo_bridge 와 같은 방식.

DATA    : {path_key: dict} — draw override 가 그릴 것 (툴이 바뀔 때만 만든다, 아래 키 설명)
HUD     : 2D 로 그릴 것 — {"box": (x0, y0, x1, y1), "text": (x, y, str), "owner": 경로 키} 또는 {}
          (text = 폴오프 반경을 끄는 동안 커서 옆 글자, v01.09)
PENDING : 다음 `junMotionPathSetKeys` 명령이 가져갈 (undo 기록 MAnimCurveChange, 다시 계산을 표시할 노드들)
DIRTY   : 다음 `junMotionPathDirty` 명령이 가져갈 노드들 (v01.03)

DATA[path_key] 키 (값은 OpenMaya 2.0 객체 - 그리기 때 변환하지 않게 미리 만든다):
    "line"      : MPointArray  경로 선 (프레임 순서)
    "dots"      : MPointArray  프레임 점
    "keys"      : MPointArray  키 점 (선택 안 된 것)
    "selected"  : MPointArray  선택된 키 점
    "current"   : MPointArray  현재 프레임 점 (0 또는 1 개)
    "labels"    : [(MPoint, str)]  키 옆 프레임 번호 (끄면 빈 목록)
    "ghost"     : MPointArray  원래 경로 (그래프 Smooth 미리보기 중에만 - 회색 점선, v01.04)
    "selected_dots" : MPointArray  고른 프레임 점 (키 아닌 것, v01.09)
    "fall_dots" / "fall_colors" : MPointArray / MColorArray  폴오프 범위의 점과 가중치 색 (v01.09, mesh kPoints)
    "fall_lines": [(MColor, MPointArray)]  폴오프 범위의 선 - 색 단계마다 한 조각 (v01.09, mesh 선은 x-ray 가 안 먹어 lineStrip)
    "color"     : MColor  경로 색
    "locked"    : bool  편집 불가 경로 (회색으로)
    "line_width", "dot_size", "key_size" : float
"""

DATA = {}
HUD = {}
PENDING = None
DIRTY = None


def put(path_key, payload):
    DATA[path_key] = payload


def drop(path_key):
    DATA.pop(path_key, None)


def clear():
    DATA.clear()
    HUD.clear()


def stage(change, nodes=()):
    """다음 undo 명령이 가져갈 기록(과 undo · redo 뒤 다시 계산을 표시할 노드)을 둔다."""
    global PENDING
    PENDING = (change, list(nodes))


def take():
    """명령이 기록을 가져간다(한 번만). (change, nodes) 또는 (None, [])."""
    global PENDING
    payload, PENDING = PENDING, None
    return payload if payload is not None else (None, [])


def stage_dirty(nodes):
    global DIRTY
    DIRTY = list(nodes)


def take_dirty():
    global DIRTY
    nodes, DIRTY = DIRTY, None
    return nodes or []
