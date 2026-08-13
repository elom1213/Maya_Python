# -*- coding: utf-8 -*-
# A00400_CurveTool core - 메시 엣지 -> 커브 생성 · 커브 방향 정렬 로직 (maya.cmds, UI 비의존)
#
# 1) 선택한 메시 엣지에 "부착된"(히스토리로 연결된) 커브를 만든다. ref/ref_01.mel 은
#    선택 전체를 하나의 커브로만 묶었지만, 여기서는 선택한 엣지를 **연결 성분(붙어 있는
#    엣지 덩어리)별로 그룹지어 그룹마다 커브 1개**를 만든다. 예) 세 개의 떨어진 엣지 구간
#    ['pSphere1.e[156:158]', 'pSphere1.e[196:199]', 'pSphere1.e[236:239]'] -> 커브 3개.
#
# 2) 만들어진(또는 리스트업된) 커브들의 시작 cv[0] / 끝 cv[n] 월드 위치를 지정 축으로
#    비교해, 원하는 방향(cv[0] 이 축의 최대 끝 또는 최소 끝)이 되도록 `reverseCurve` 로
#    방향을 뒤집는다. A00360_SortTool 의 축 비교 방식을 참고했다.
#
# 커브 생성은 Maya 표준 `polyToCurve`(엣지->커브, 히스토리 유지 = 메시에 부착)를 쓴다.
# ref 의 duplicateCurve + attachCurve(각 엣지를 작은 커브로 뜬 뒤 이어붙임)와 결과는
# 같은 "엣지를 따라가는 부착 커브"지만, polyToCurve 가 엣지 체인의 cv 순서를 스스로
# 정렬해 주어 더 견고하고 cv[0]/cv[n] 끝점이 명확하다(방향 정렬 기능에 필요).

import maya.cmds as cmds


# 방향 비교 축
MODE_X = "x"
MODE_Y = "y"
MODE_Z = "z"

_AXIS_INDEX = {MODE_X: 0, MODE_Y: 1, MODE_Z: 2}

# 커브 굵기(nurbsCurve.lineWidth). -1 = 마야 전역 설정을 그대로 쓴다(기본값).
LINE_WIDTH_DEFAULT = -1.0
LINE_WIDTH_MIN = 0.0
LINE_WIDTH_MAX = 10.0


# ============================================================ 엣지 그룹핑

def _edge_verts(edge):
    """엣지 하나의 두 정점(월드 이름). 예: ['pSphere1.vtx[10]', 'pSphere1.vtx[11]']."""
    conv = cmds.polyListComponentConversion(edge, fromEdge=True, toVertex=True) or []
    return cmds.ls(conv, fl=True) or []


def group_edges(edges):
    """선택 엣지를 '붙어 있는 덩어리'(연결 성분)별로 그룹지어 돌려준다.

    두 엣지가 정점을 공유하면 같은 그룹. 서로 다른 메시의 엣지는 정점을 공유할 수 없어
    자연히 다른 그룹으로 갈린다. BFS 로 연결 성분을 모은다.
    반환: [[edge, ...], ...]  (발견 순서)
    """
    edge_verts = {e: _edge_verts(e) for e in edges}

    # 정점 -> 그 정점을 쓰는 엣지들
    vert_to_edges = {}
    for e, verts in edge_verts.items():
        for v in verts:
            vert_to_edges.setdefault(v, []).append(e)

    seen = set()
    groups = []
    for start in edges:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        comp = []
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for v in edge_verts[cur]:
                for nb in vert_to_edges.get(v, []):
                    if nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
        groups.append(comp)
    return groups


# ============================================================ 커브 생성

def _selected_edges():
    """현재 선택에서 폴리곤 엣지만 평탄화해 돌려준다."""
    sel = cmds.ls(sl=True, fl=True) or []
    return [s for s in sel if ".e[" in s]


def _unique_name(base):
    """씬에 없는 이름이 될 때까지 base 를 반환(있으면 Maya 가 알아서 붙이지만 예측 가능하게)."""
    return base


def curves_from_selected_edges(prefix="edgeCurve", degree=1):
    """선택한 메시 엣지로부터 그룹(연결 성분)마다 커브 1개씩 만든다.

    prefix : 생성 커브 이름 접두사 (`<prefix>_01`, `<prefix>_02`, ...)
    degree : 1=엣지를 그대로 따르는 직선(polyline), 3=부드러운 곡선
    반환   : (created_curves, group_count)
             created_curves : 생성된 커브 transform 이름 리스트
    엣지 선택이 없으면 ValueError.
    """
    edges = _selected_edges()
    if not edges:
        raise ValueError("No polygon edges selected. Select mesh edges first.")

    groups = group_edges(edges)

    created = []
    for i, group in enumerate(groups):
        cmds.select(group, replace=True)
        # form=2: 열림/닫힘을 자동 판단(엣지 루프면 닫힌 커브). ch=1: 히스토리 유지(메시 부착).
        res = cmds.polyToCurve(
            form=2, degree=degree, constructionHistory=True,
            conformToSmoothMeshPreview=0)
        crv = res[0]
        crv = cmds.rename(crv, _unique_name("{0}_{1:02d}".format(prefix, i + 1)))
        created.append(crv)

    if created:
        cmds.select(created, replace=True)
    return created, len(groups)


# ============================================================ 방향 정렬

def _cv_count(curve):
    """커브의 cv 개수."""
    return len(cmds.ls(curve + ".cv[*]", fl=True) or [])


def _cv_axis(curve, index, axis_index):
    """curve.cv[index] 의 월드 위치 중 axis_index(0=x,1=y,2=z) 성분."""
    return cmds.pointPosition("{0}.cv[{1}]".format(curve, index), world=True)[axis_index]


def curve_shapes(node):
    """transform/shape 이름 -> 그 아래 nurbsCurve shape 롱네임 리스트(없으면 빈 리스트)."""
    if not node or not cmds.objExists(node):
        return []
    if cmds.objectType(node, isType="nurbsCurve"):
        found = cmds.ls(node, l=True) or []
        return found[:1]
    return cmds.listRelatives(node, shapes=True, type="nurbsCurve", fullPath=True,
                              noIntermediate=True) or []


def get_line_width(node):
    """첫 nurbsCurve shape 의 lineWidth. 커브가 아니거나 못 읽으면 None."""
    for shape in curve_shapes(node):
        try:
            return cmds.getAttr(shape + ".lineWidth")
        except Exception:
            return None
    return None


def set_line_width(curves, width):
    """리스트업된 커브들의 **뷰포트 표시 굵기**(`nurbsCurve.lineWidth`)를 바꾼다.

    굵게 하면 씬에서 커브가 잘 보이고 클릭으로 집기도 쉬워진다. 형상·히스토리는 전혀
    건드리지 않는 **표시 전용** 어트리뷰트다.

    `-1`(LINE_WIDTH_DEFAULT)은 마야의 전역 라인 굵기 설정을 그대로 쓴다는 뜻이다.

    Returns (changed, skipped)
      changed : 실제로 값을 쓴 shape 이름 리스트
      skipped : (이름, 사유) 리스트 — 커브가 아님 / 어트리뷰트 없음(구버전) /
                잠기거나 연결됨
    """
    width = float(width)
    changed = []
    skipped = []

    for name in curves or []:
        shapes = curve_shapes(name)
        if not shapes:
            skipped.append((name, "not a curve"))
            continue
        for shape in shapes:
            # lineWidth 는 Maya 2019+ 에서만 있다.
            if not cmds.attributeQuery("lineWidth", node=shape, exists=True):
                skipped.append((shape, "no lineWidth attribute (Maya 2019+)"))
                continue
            plug = shape + ".lineWidth"
            if not cmds.getAttr(plug, settable=True):
                skipped.append((shape, "locked or connected"))
                continue
            try:
                cmds.setAttr(plug, width)
                changed.append(shape)
            except Exception as exc:                       # noqa: BLE001
                skipped.append((shape, str(exc)))
    return changed, skipped


def reverse_curves_by_axis(curves, mode, cv0_at_max=True):
    """커브들의 방향을 지정 축 기준으로 통일한다.

    각 커브의 cv[0] 와 cv[n] 의 월드 축(mode) 값을 비교해서:
      cv0_at_max=True  : cv[0] 이 축의 **최대 끝**(예: Y 위쪽)에 오도록. cv[0] 이 더
                         작으면(아래면) reverseCurve 로 뒤집는다.
      cv0_at_max=False : cv[0] 이 축의 **최소 끝**(예: Y 아래쪽)에 오도록.
    반환: (reversed_names, skipped_names)
      reversed_names : 실제로 뒤집은 커브 이름
      skipped_names  : 이미 원하는 방향이거나, 커브가 아니거나, 두 끝의 축값이 같아
                       판단 불가라 건너뛴 (이름, 사유) 튜플 리스트
    """
    axis_index = _AXIS_INDEX[mode]
    reversed_names = []
    skipped = []

    for name in curves:
        # nurbsCurve shape 이 있는지 확인
        shapes = cmds.listRelatives(name, shapes=True, type="nurbsCurve", fullPath=True)
        if not shapes:
            skipped.append((name, "not a curve"))
            continue

        n = _cv_count(name)
        if n < 2:
            skipped.append((name, "too few CVs"))
            continue

        a = _cv_axis(name, 0, axis_index)
        b = _cv_axis(name, n - 1, axis_index)

        if abs(a - b) < 1e-6:
            skipped.append((name, "endpoints equal on axis"))
            continue

        # cv[0] 이 최대 끝에 와야 하는데 더 작으면 뒤집는다 (그 반대도 대칭)
        need_reverse = (a < b) if cv0_at_max else (a > b)
        if need_reverse:
            cmds.reverseCurve(name, constructionHistory=True, replaceOriginal=True)
            reversed_names.append(name)
        else:
            skipped.append((name, "already aligned"))

    return reversed_names, skipped
