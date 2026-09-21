# -*- coding: utf-8 -*-
# A00400_CurveTool core - 커브 **셰이프(CV)** 를 각 커브의 피벗 기준으로 scale / rotate / move
# (maya.cmds + maya.api.OpenMaya, UI 비의존)
#
# 트랜스폼의 `scale` / `rotate` / `translate` 어트리뷰트는 **건드리지 않는다.** 커브의 CV 를
# 전부 골라 스케일·회전·이동한 것과 같은 결과를 만든다 — 컨트롤러의 크기·방향·자리만 손보고
# 트랜스폼 채널은 0/1 로 깨끗하게 남겨 두려는 용도다(컨트롤은 채널이 기본값이어야 한다).
#
# ── 공간과 기준점 ─────────────────────────────────────────────────────────
# 계산은 **오브젝트 공간**에서, 기준점은 그 커브 트랜스폼의 **rotate pivot** 이다.
#   new = pivot + T + R * (S * (cv - pivot))
# 즉 스케일 -> 회전 -> 이동 순서이고, 축은 그 커브 자신의 로컬 축이다. 뷰포트에서 CV 를
# 전부 골라 Move/Rotate/Scale 툴(축 방향 Object)로 다룬 것과 같다. 트랜스폼에 회전이
# 들어가 있어도 "그 컨트롤 기준" 으로 움직이므로, 좌우 컨트롤에 같은 값을 넣으면 각자
# 자기 축으로 같은 만큼 변한다.
#
# ── mayapy 로 확인한 것 ───────────────────────────────────────────────────
#  * 쓰기는 `cmds.curve(shape, replace=True, point=...)` 한 번으로 CV 전체를 바꾼다.
#    **undo 가 되고**(API 의 `setCVPositions` 는 undo 큐에 안 남는다), 히스토리가 붙은
#    커브(예: `makeNurbCircle` 이 살아 있는 원)에서도 통하며 degree / CV 수를 보존한다.
#    `setAttr .controlPoints` 는 히스토리가 있으면 절대 위치가 아니라 **트윅(델타)** 가
#    되므로 쓰지 않는다. (같은 판단이 `smooth_manager` 에도 적혀 있다)
#  * 주기(닫힌) 커브는 `replace=True` 만으로는 거절된다
#    ("Must specify knots with the -per option") → `periodic=True` + `degree` + `knot` 까지
#    같이 넘긴다. 또 `cvPositions()` 는 `spans + degree` 개를 돌려주는데 뒤의 degree 개는
#    앞의 복사본이다 — 여기서는 **모든 CV 에 같은 변환**을 걸므로 복사본도 그대로 따라가
#    이음매가 어긋나지 않는다.
#  * 트랜스폼 아래에 셰이프가 여러 개면(합쳐진 컨트롤) **전부** 같은 피벗 기준으로 함께
#    변환한다 — 모양 하나만 움직여 어긋나지 않게.

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from tools.A00400_CurveTool.app.core.curve_manager import curve_shapes


# 중립값 — 이 값이면 그 축은 아무 것도 안 한 것과 같다.
SCALE_NEUTRAL = (1.0, 1.0, 1.0)
MOVE_NEUTRAL = (0.0, 0.0, 0.0)
ROTATE_NEUTRAL = (0.0, 0.0, 0.0)

_EPS = 1e-9


# ============================================================ 헬퍼

def _transform_of(node):
    """셰이프를 주면 그 부모 트랜스폼, 트랜스폼을 주면 자기 자신(롱네임)."""
    if cmds.objectType(node, isType="transform"):
        return (cmds.ls(node, long=True) or [node])[0]

    parents = cmds.listRelatives(node, parent=True, fullPath=True) or []

    return parents[0] if parents else None


def _pivot(transform):
    """트랜스폼의 rotate pivot — **오브젝트 공간** 값(CV 좌표와 같은 공간)."""
    values = cmds.getAttr(transform + ".rotatePivot")[0]

    return (float(values[0]), float(values[1]), float(values[2]))


def _fn_curve(shape):
    selection = om2.MSelectionList()
    selection.add(shape)

    return om2.MFnNurbsCurve(selection.getDagPath(0))


def _rotation_matrix(rotate):
    """도 단위 (rx, ry, rz) -> 회전 행렬. 없으면 None(= 회전 없음)."""
    if not rotate or all(abs(value) < _EPS for value in rotate):
        return None

    euler = om2.MEulerRotation(math.radians(rotate[0]),
                               math.radians(rotate[1]),
                               math.radians(rotate[2]),
                               om2.MEulerRotation.kXYZ)

    return om2.MMatrix(euler.asMatrix())


def is_identity(scale=None, rotate=None, translate=None):
    """세 가지 다 중립이면 True — 호출부가 '할 일 없음' 을 알리게."""
    if scale and any(abs(value - 1.0) > _EPS for value in scale):
        return False
    if rotate and any(abs(value) > _EPS for value in rotate):
        return False
    if translate and any(abs(value) > _EPS for value in translate):
        return False

    return True


# ============================================================ 변환

def _moved_points(points, pivot, scale, rotate_matrix, translate):
    """오브젝트 공간 CV 목록에 pivot 기준 S -> R -> T 를 건다."""
    px, py, pz = pivot
    sx, sy, sz = scale or SCALE_NEUTRAL
    tx, ty, tz = translate or MOVE_NEUTRAL

    result = []
    for point in points:
        x = (point.x - px) * sx
        y = (point.y - py) * sy
        z = (point.z - pz) * sz

        if rotate_matrix is not None:
            rotated = om2.MPoint(x, y, z) * rotate_matrix
            x, y, z = rotated.x, rotated.y, rotated.z

        result.append((x + px + tx, y + py + ty, z + pz + tz))

    return result


def _write_points(shape, points):
    """CV 전체를 한 번에 쓴다(undo 가능). 닫힌 커브는 매듭까지 같이 넘긴다."""
    degree = int(cmds.getAttr(shape + ".degree"))
    periodic = int(cmds.getAttr(shape + ".form")) == 2

    if not periodic:
        cmds.curve(shape, replace=True, point=points)
        return

    knots = list(_fn_curve(shape).knots())
    cmds.curve(shape, replace=True, periodic=True, degree=degree,
               point=points, knot=knots)


def transform_shapes(nodes, scale=None, rotate=None, translate=None):
    """리스트업한 커브들의 **셰이프**를 각자의 피벗 기준으로 변환한다.

    nodes     : 커브 트랜스폼(또는 nurbsCurve 셰이프) 이름 목록
    scale     : (sx, sy, sz) 배율. None 이면 스케일 안 함
    rotate    : (rx, ry, rz) 도. None 이면 회전 안 함 (XYZ 순)
    translate : (tx, ty, tz) 오브젝트 공간 이동량. None 이면 이동 안 함

    트랜스폼 채널(scale/rotate/translate 어트리뷰트)은 전혀 건드리지 않는다.

    Returns (changed, skipped)
      changed : 실제로 CV 를 바꾼 셰이프 롱네임 리스트
      skipped : (이름, 사유) 리스트 — 없는 노드 / 커브 아님 / 쓰기 실패(레퍼런스·잠김 등)
    """
    rotate_matrix = _rotation_matrix(rotate)

    changed = []
    skipped = []

    for name in nodes or []:
        if not name or not cmds.objExists(name):
            skipped.append((name, "does not exist"))
            continue

        shapes = curve_shapes(name)
        if not shapes:
            skipped.append((name, "not a curve"))
            continue

        transform = _transform_of(shapes[0])
        if not transform:
            skipped.append((name, "no transform"))
            continue

        pivot = _pivot(transform)

        for shape in shapes:
            try:
                points = _fn_curve(shape).cvPositions(om2.MSpace.kObject)
                moved = _moved_points(points, pivot, scale, rotate_matrix, translate)
                _write_points(shape, moved)
                changed.append(shape)
            except Exception as exc:                        # noqa: BLE001
                skipped.append((shape, str(exc)))

    return changed, skipped
