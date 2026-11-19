# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 부모 공간 굽기 (계획서 §4-2 · §4-3)
"""
경로 점 :  P(f) = (c + T(f)) · PM(f)          (마야 행 벡터 규약)
  PM(f) : 대상의 `parentMatrix[0]` — 부모 · 컨스트레인트 · 드라이버 · 자기 offsetParentMatrix 가 다 들어 있다(0단계 0-8 확인).
  T(f)  : translate 세 채널 (애님 커브를 직접 평가 - anim_channels).
  c     : rotatePivot + rotatePivotTranslate — **상수**. 조인트와 피벗이 원점인 transform 은 0.
          마야 Move 툴이 보여 주는 회전 피벗 월드 위치(`xform -q -ws -rp`)가 바로 이 식이다. transform 행렬
          [-sp][S][Sh][sp][spt][-rp][Ra][R][rp][rpt][T] 에서 회전 피벗은 회전 · 스케일 뒤에 rp + rpt + T 로 남기 때문.
          (처음에 rp · worldMatrix 로 구웠다가 스케일이 1 이 아니면 0.43 어긋나는 것을 실측으로 찾아 고쳤다 -
           그 덕에 자기 worldMatrix 를 시간 문맥으로 읽을 일도 없어졌다. 마야는 getAttr -time worldMatrix 를 캐시해 두고
           자기 커브가 바뀌어도 옛 값을 주는 일이 있었다.)

굽기 = 프레임마다 `parentMatrix[0]` plug 만 **시간 문맥**으로 평가한다(`MDGContext.makeCurrent`). 그 plug 의 상류만 계산되므로
스킨 메시 · 상관없는 캐릭터는 계산하지 않고, 사용자의 현재 시간 · 선택 · 포즈도 그대로다.
0단계 실측(1,000 프레임): 계층 0.17초, 무거운 리그 0.14초 — 마야 Motion Trail 을 만드는 시간과 비슷하다.
시간만 옮기고 plug 를 읽는 방법은 **값이 틀려서** 버렸다(다시 계산하지 않은 값이 나온다, 차이 20).

여러 대상은 **프레임 바깥 루프**로 한 번에 굽는다(같은 프레임 문맥에서 대상들을 연달아 읽는다).
"""

import maya.api.OpenMaya as om
import maya.cmds as cmds

try:
    import numpy as np
except Exception:                                          # noqa: BLE001
    np = None

from .anim_channels import ui_time


def _plug(node, attr):
    sel = om.MSelectionList()
    sel.add("{0}.{1}".format(node, attr))
    return sel.getPlug(0)


def pivot_offset(node):
    """c = rotatePivot + rotatePivotTranslate (부모 공간 바로 안쪽, 내부 단위). 조인트는 (0, 0, 0)."""
    if cmds.objectType(node) == "joint":
        return (0.0, 0.0, 0.0)
    obj = om.MSelectionList()
    obj.add(node)
    fn = om.MFnDependencyNode(obj.getDependNode(0))
    out = []
    for i, axis in enumerate("XYZ"):
        rp = fn.findPlug("rotatePivot" + axis, False).asDouble()
        rpt = fn.findPlug("rotatePivotTranslate" + axis, False).asDouble()
        out.append(rp + rpt)
    return tuple(out)


def _matrix_rows(m):
    return [[m.getElement(r, c) for c in range(4)] for r in range(4)]


def bake(nodes, frames, progress=None, layers=()):
    """({node: (N,4,4) parentMatrix}, {레이어: (wA (N,), wB (N,))}).

    nodes  : 롱네임 목록, frames : 프레임 목록(소수 가능), progress : (done, total)
    layers : 가중치를 구울 애니메이션 레이어 (v01.03) - backgroundWeight / foregroundWeight 를 같은 시간 문맥에서 읽는다
             (블렌드 노드의 weightA / weightB 가 이 둘에서 온다 - 뮤트 · 솔로 · 가중치 애니메이션 포함).
    """
    pm_plugs = {n: _plug(n, "parentMatrix[0]") for n in nodes}
    w_plugs = {L: (_plug(L, "backgroundWeight"), _plug(L, "foregroundWeight")) for L in layers}
    out = {n: [] for n in nodes}
    weights = {L: ([], []) for L in layers}
    total = len(frames)
    for i, f in enumerate(frames):
        ctx = om.MDGContext(ui_time(f))
        prev = ctx.makeCurrent()
        try:
            for n, plug in pm_plugs.items():
                out[n].append(_matrix_rows(om.MFnMatrixData(plug.asMObject()).matrix()))
            for L, (bg, fg) in w_plugs.items():
                weights[L][0].append(bg.asDouble())
                weights[L][1].append(fg.asDouble())
        finally:
            prev.makeCurrent()
        if progress is not None and (i % 50 == 0 or i == total - 1):
            progress(i + 1, total)
    if np is not None:
        for n in nodes:
            out[n] = np.array(out[n], dtype="float64").reshape(-1, 4, 4)
        weights = {L: (np.array(a, dtype="float64"), np.array(b, dtype="float64")) for L, (a, b) in weights.items()}
    return out, weights
