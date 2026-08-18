# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00400_CurveTool core - 리스트 순서대로 오브젝트/컴포넌트의 월드 위치를 잇는 커브. UI 비의존.
#
# 오브젝트든 조인트든 컴포넌트든 "월드 위치" 하나로 환원해서, 리스트에 담긴 **순서대로**
# 커브 하나를 만든다.
#
# ── 두 가지 모드 ───────────────────────────────────────────────────────────
#  * Exact  : `cmds.curve(ep=...)` — **에디트 포인트** 커브라 모든 위치를 정확히 지난다
#             (mayapy 실측: 최대 거리 0.0).
#  * Smooth : 그렇게 만든 커브의 **CV 를 라플라시안으로 이완**한다. 양 끝 CV 는 고정하므로
#             시작/끝은 그대로 두고 중간만 완만해진다. Smoothness 0 이면 Exact 와 같다.
#
# 완화를 `rebuildCurve` 의 span 수로 하려다 접었다 — span 을 5→4→3 으로 줄일 때 입력점까지의
# 최대 거리가 0.30 → 1.73 → 1.44 로 **단조롭게 늘지 않아** 슬라이더로 쓰기에 나쁘다(실측).
# 라플라시안은 반복할수록 단조롭게 완만해지므로 슬라이더 감각이 예측 가능하다.

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from Framework.core.maya_undo import undo_chunk

# 라플라시안 반복 횟수. Smoothness 는 회당 세기(0 ~ 0.5)로 들어간다.
RELAX_ITERATIONS = 12
RELAX_MAX_STRENGTH = 0.5

# 지원 차수 (1 = 직선 연결)
DEGREES = [1, 2, 3, 5]
DEFAULT_DEGREE = 3


# ==========================================================================
# 월드 위치
# ==========================================================================

def world_position(item):
    """오브젝트 / 조인트 / 컴포넌트의 **월드 위치**. 얻을 수 없으면 None.

    `cmds.xform(q=True, ws=True, t=True)` 하나로 전부 처리한다(mayapy 로 확인).
      * 트랜스폼 · 조인트        -> [x, y, z]
      * 버텍스 · CV · 래티스 포인트 -> [x, y, z]
      * **엣지 -> 6개, 페이스 -> 12개** (구성 정점들) → 평균 내서 중심을 쓴다
    `cmds.pointPosition` 은 엣지/페이스에서 에러가 나므로 쓰지 않는다.
    """
    if not item:
        return None

    node = item.split(".")[0]

    if not cmds.objExists(node):
        return None

    try:
        values = cmds.xform(item, query=True, worldSpace=True, translation=True)
    except Exception:
        return None

    if not values or len(values) < 3:
        return None

    count = len(values) // 3

    if count == 1:
        return tuple(values[:3])

    # 엣지/페이스 등 여러 점이 나오는 컴포넌트는 중심을 쓴다.
    return tuple(
        sum(values[i * 3 + axis] for i in range(count)) / float(count)
        for axis in range(3)
    )


def gather_positions(items):
    """리스트 순서대로 월드 위치를 모은다. (위치들, 건너뛴 항목) 을 돌려준다."""
    points = []
    skipped = []

    for item in items or []:
        position = world_position(item)

        if position is None:
            skipped.append((item, "no world position"))
            continue

        points.append(position)

    return points, skipped


# ==========================================================================
# 완화 (라플라시안)
# ==========================================================================

def relax(points, smoothness, iterations=RELAX_ITERATIONS):
    """양 끝을 고정한 채 중간 점들을 이웃 평균 쪽으로 당긴다.

    smoothness 0 이면 그대로, 1 이면 완전히 이완된 상태다.

    **세기를 smoothness 에 비례시키지 않고, "완전히 이완한 결과"를 한 번 구한 뒤 원본과
    smoothness 로 선형 보간한다.** 세기에 비례시키면 반복 효과가 지수적으로 쌓여 슬라이더
    앞쪽 25% 에서 변화가 거의 끝나 버린다(실측: 0 → 2.57 → 2.68 → 3.03 → 3.27).
    선형 보간이면 편차가 슬라이더에 비례해 늘어 조작감이 예측 가능하다.
    """
    if smoothness <= 0.0 or len(points) < 3:
        return [tuple(p) for p in points]

    blend = max(0.0, min(1.0, float(smoothness)))
    current = [list(p) for p in points]

    for _ in range(iterations):
        updated = [current[0]]

        for i in range(1, len(current) - 1):
            updated.append([
                current[i][axis] + RELAX_MAX_STRENGTH * (
                    (current[i - 1][axis] + current[i + 1][axis]) * 0.5 - current[i][axis])
                for axis in range(3)
            ])

        updated.append(current[-1])
        current = updated

    return [
        tuple(origin[axis] + blend * (relaxed[axis] - origin[axis]) for axis in range(3))
        for origin, relaxed in zip(points, current)
    ]


# ==========================================================================
# 측정
# ==========================================================================

def distances_to_curve(curve, points):
    """입력 위치들이 커브에서 얼마나 떨어졌는지 (최대, 평균). 월드 기준."""
    if not points:
        return 0.0, 0.0

    selection = om2.MSelectionList()
    selection.add(curve)
    fn = om2.MFnNurbsCurve(selection.getDagPath(0))

    gaps = []

    for point in points:
        target = om2.MPoint(*point)
        closest, _param = fn.closestPoint(target, space=om2.MSpace.kWorld)
        gaps.append((closest - target).length())

    return max(gaps), sum(gaps) / len(gaps)


# ==========================================================================
# 생성
# ==========================================================================

def create_curve(items, degree=DEFAULT_DEGREE, smoothness=0.0, name=None):
    """리스트 순서대로 월드 위치를 잇는 커브 하나를 만든다.

    smoothness 0 이면 모든 위치를 정확히 지나고, 키우면 완만해진다(양 끝은 항상 고정).
    """
    points, skipped = gather_positions(items)

    if len(points) < 2:
        return {
            "ok": False,
            "message": "Need at least 2 items with a world position (got {0}).".format(
                len(points)),
            "skipped": skipped,
        }

    degree = int(degree)

    # 차수가 점 개수보다 크면 마야가 커브를 못 만든다. 가능한 최대 차수로 낮춘다.
    effective_degree = min(degree, max(1, len(points) - 1))

    with undo_chunk():
        curve = cmds.curve(editPoint=points, degree=effective_degree)

        if name:
            curve = cmds.rename(curve, name)

        if smoothness > 0.0:
            # 정확히 지나는 커브의 **CV** 를 이완한다. 커브는 원점에 생기므로
            # 로컬 좌표 = 월드 좌표이고, 노트/차수는 그대로 유지된다.
            shape = cmds.listRelatives(curve, shapes=True, fullPath=True)[0]
            cv_count = cmds.getAttr(shape + ".spans") + cmds.getAttr(shape + ".degree")

            cvs = [cmds.pointPosition("{0}.cv[{1}]".format(curve, i), world=True)
                   for i in range(cv_count)]

            for index, position in enumerate(relax(cvs, smoothness)):
                cmds.xform("{0}.cv[{1}]".format(curve, index),
                           worldSpace=True, translation=position)

    max_gap, avg_gap = distances_to_curve(curve, points)

    return {
        "ok": True,
        "curve": curve,
        "message": ("Created '{0}' through {1} point(s), degree {2}{3} - "
                    "max distance from the points {4:.4f}, avg {5:.4f}").format(
            curve, len(points), effective_degree,
            "" if effective_degree == degree else " (lowered from {0})".format(degree),
            max_gap, avg_gap),
        "points": points,
        "skipped": skipped,
        "max_gap": max_gap,
        "avg_gap": avg_gap,
    }
