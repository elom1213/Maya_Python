# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-30
# A00400_CurveTool core - 커브를 따라 납작한 NURBS 서피스(리본)를 만든다. UI 비의존.
#
# ── 무엇을 만드나 ──────────────────────────────────────────────────────────
# 리깅용 "리본" — 커브 하나를 Width 만큼 양옆으로 벌려 loft 한 것과 같은 서피스.
# 샘플(`sfcTest/sample_001.mb`, loftedSurface)을 관찰한 결과:
#   * U(길이 방향) = 커브의 CV · 차수 · 노트가 **그대로**(6 CV, 차수 3, 노트 0 0 0 ⅓ ⅔ 1 1 1)
#   * V(폭 방향)   = CV 를 X 로 -1, -⅓, +⅓, +1 평행 이동한 네 줄, 차수 3, 노트 0 0 0 1 1 1
#     → 두 커브를 `loft -d 3` 한 결과와 CV 가 하나도 다르지 않다(mayapy 실측).
#   * 히스토리 없음, 트랜스폼은 identity(월드 좌표 그대로).
#
# ── 어떻게 만드나 ──────────────────────────────────────────────────────────
# 커브의 월드 CV · 차수 · 노트를 읽어 **양쪽으로 벌린 임시 커브 두 개**를 `cmds.curve` 로 직접
# 정의하고(월드에, 주기 커브는 `per=True`), 그 둘을 `loft`(히스토리 없음) 한 뒤 임시 커브를 지운다.
#   * 원본 커브는 복제하지 않는다 — 복제는 부모 · 자식 · 다른 셰이프까지 딸려 오고, 부모가
#     회전돼 있으면 로컬 이동이 월드 방향과 어긋난다. 월드 CV 로 새로 만들면 그런 문제가 없다.
#   * 노트 0..1 정규화와 U 뒤집기는 임시 커브의 **CV 순서와 노트**에 미리 반영한다. loft 는
#     커브의 노트를 U 로 그대로 쓰므로 rebuild / reverseSurface 를 돌릴 일이 없다.
#   * `cmds.surface` 로 서피스를 한 번에 정의하는 길이 더 짧지만 그 명령은 **undo 가 안 된다**
#     (mayapy 실측 — 큐에 오르지 않아 Ctrl+Z 가 이름 바꾸기만 되돌리고 서피스는 남는다). 위 조합은
#     전부 undo 되는 명령이라 한 청크로 묶으면 Ctrl+Z 한 번에 리본만 사라진다.
# 실측으로 마야 방식(복제 + 이동 + loft) 과 CV · 노트 · 차수 · 폼이 같음을 tests/test_ribbon.py 가 대조한다.
#
# ── 폭 방향(Direction) ─────────────────────────────────────────────────────
# 샘플은 YZ 평면 커브를 X 로 벌렸다 — 커브가 놓인 **평면의 노멀**이다. 기본 `Auto` 는 CV 들의
# 최적 평면 노멀(공분산 행렬의 최소 고유벡터, 3x3 야코비)을 쓴다. 직선 커브는 평면이 없으므로
# 선과 가장 수직인 월드 축으로 대신하고 그 사실을 note 로 돌려준다. World X / Y / Z 는 그대로.
#
# ── 폭(across) 차수 ────────────────────────────────────────────────────────
#  3 = 네 줄(마야 loft 기본과 같다, 폭 방향도 부드럽게 변형 가능)
#  1 = 두 줄(가장 가벼운 리본, 폭 방향은 직선)
# 폭 방향 CV 는 한 직선 위에 등간격이라 어느 차수든 **면은 같은 평면 띠**다. 차수는 나중에
# 서피스를 변형(바인드)할 때의 자유도만 정한다.

import math

import maya.cmds as cmds
import maya.api.OpenMaya as om2

# 폭 방향 선택지 (UI 콤보가 그대로 쓴다)
DIRECTION_AUTO = "Auto"
DIRECTION_X = "X"
DIRECTION_Y = "Y"
DIRECTION_Z = "Z"
DIRECTIONS = (DIRECTION_AUTO, DIRECTION_X, DIRECTION_Y, DIRECTION_Z)
DIRECTION_LABELS = {
    DIRECTION_AUTO: "Auto (normal of the curve's plane)",
    DIRECTION_X: "World X",
    DIRECTION_Y: "World Y",
    DIRECTION_Z: "World Z",
}
WORLD_AXES = {
    DIRECTION_X: (1.0, 0.0, 0.0),
    DIRECTION_Y: (0.0, 1.0, 0.0),
    DIRECTION_Z: (0.0, 0.0, 1.0),
}

# 폭 방향 차수
ACROSS_DEGREES = (3, 1)
DEFAULT_ACROSS_DEGREE = 3

DEFAULT_WIDTH = 2.0
NAME_SUFFIX = "_ribbon"

# 평면 판정 — 최소 고유값 / 최대 고유값. 이보다 크면 "평면이 아니다" 라고 알린다(만들기는 한다).
PLANAR_RATIO = 1e-3
# 직선 판정 — 두 번째 고유값 / 최대 고유값. 이보다 작으면 평면을 정할 수 없다.
LINE_RATIO = 1e-6


# ==========================================================================
# 커브 읽기
# ==========================================================================

def curve_shape(node):
    """트랜스폼이든 셰이프든 받아 **nurbsCurve 셰이프**(중간 오브젝트 제외)를 돌려준다. 없으면 None."""
    if not node or not cmds.objExists(node):
        return None

    if cmds.nodeType(node) == "nurbsCurve":
        return node

    shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True, fullPath=True) or []
    for shape in shapes:
        if cmds.nodeType(shape) == "nurbsCurve":
            return shape
    return None


def curve_data(shape):
    """커브의 차수 · 폼 · 노트 · **월드 좌표 CV** 를 dict 로.

    MFnNurbsCurve 가 주는 노트는 `(CV 수 + 차수 - 1)` 개 — `cmds.surface -ku` 가 받는 형식과
    같다. 주기 커브는 겹치는 CV(차수 개)까지 numCVs 에 들어 있고, 노트도 그 겹침을 포함한
    값이라 그대로 넘기면 주기 서피스가 된다.
    """
    sel = om2.MSelectionList()
    sel.add(shape)
    fn = om2.MFnNurbsCurve(sel.getDagPath(0))

    form = {om2.MFnNurbsCurve.kOpen: "open",
            om2.MFnNurbsCurve.kClosed: "closed",
            om2.MFnNurbsCurve.kPeriodic: "periodic"}.get(fn.form, "open")

    points = [(p.x, p.y, p.z) for p in fn.cvPositions(om2.MSpace.kWorld)]
    knots = list(fn.knots())
    start, end = fn.knotDomain

    return {
        "shape": shape,
        "degree": fn.degree,
        "form": form,
        "knots": knots,
        "domain": (start, end),
        "points": points,
    }


# ==========================================================================
# 폭 방향
# ==========================================================================

def _normalize(v):
    length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if length < 1e-12:
        return None
    return (v[0] / length, v[1] / length, v[2] / length)


def _jacobi_eigen(m):
    """대칭 3x3 행렬의 (고유값 리스트, 고유벡터 열 리스트). 순수 파이썬 야코비 회전.

    numpy 없이 돌아야 한다(Maya 2023 mayapy 에는 numpy 가 없다).
    """
    a = [list(row) for row in m]
    v = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    for _ in range(50):
        # 비대각 성분 중 가장 큰 것
        p, q = 0, 1
        biggest = abs(a[0][1])
        for i, j in ((0, 2), (1, 2)):
            if abs(a[i][j]) > biggest:
                biggest = abs(a[i][j])
                p, q = i, j
        if biggest < 1e-15:
            break

        theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
        t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
        c = 1.0 / math.sqrt(t * t + 1.0)
        s = t * c

        for k in range(3):
            akp, akq = a[k][p], a[k][q]
            a[k][p] = c * akp - s * akq
            a[k][q] = s * akp + c * akq
        for k in range(3):
            apk, aqk = a[p][k], a[q][k]
            a[p][k] = c * apk - s * aqk
            a[q][k] = s * apk + c * aqk
        for k in range(3):
            vkp, vkq = v[k][p], v[k][q]
            v[k][p] = c * vkp - s * vkq
            v[k][q] = s * vkp + c * vkq

    values = [a[0][0], a[1][1], a[2][2]]
    vectors = [(v[0][i], v[1][i], v[2][i]) for i in range(3)]
    return values, vectors


def plane_normal(points):
    """점들의 최적 평면 노멀. (normal, kind) — kind 는 'plane' | 'line' | 'point'.

    공분산 행렬의 최소 고유벡터가 노멀이다. 두 번째 고유값까지 0 이면 점들이 한 직선 위라
    평면이 없다('line', 이때 normal 은 **선의 방향**). 전부 한 점이면 'point'.
    부호는 가장 큰 성분이 양수가 되게 맞춰 같은 커브에서 늘 같은 쪽이 나오게 한다.
    """
    n = len(points)
    if n == 0:
        return None, "point"

    cx = sum(p[0] for p in points) / n
    cy = sum(p[1] for p in points) / n
    cz = sum(p[2] for p in points) / n

    m = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    for p in points:
        d = (p[0] - cx, p[1] - cy, p[2] - cz)
        for i in range(3):
            for j in range(3):
                m[i][j] += d[i] * d[j]

    values, vectors = _jacobi_eigen(m)
    order = sorted(range(3), key=lambda i: values[i], reverse=True)
    big, mid, small = (values[i] for i in order)

    if big < 1e-18:
        return None, "point"
    if mid / big < LINE_RATIO:
        axis = _normalize(vectors[order[0]])
        return _signed(axis), "line"

    normal = _normalize(vectors[order[2]])
    kind = "plane" if small / big < PLANAR_RATIO else "bent"
    return _signed(normal), kind


def _signed(v):
    """가장 큰 성분이 양수가 되게 부호를 맞춘다."""
    if v is None:
        return None
    i = max(range(3), key=lambda k: abs(v[k]))
    if v[i] < 0:
        return (-v[0], -v[1], -v[2])
    return v


def offset_direction(points, direction):
    """폭 방향 단위 벡터와 사용자에게 알릴 note 를 돌려준다. 정할 수 없으면 (None, 이유)."""
    if direction in WORLD_AXES:
        return WORLD_AXES[direction], ""

    normal, kind = plane_normal(points)

    if kind == "point":
        return None, "all CVs are at one point, no direction"

    if kind == "line":
        # 직선 — 선과 가장 수직인 월드 축. 동률이면 X, Y, Z 순.
        best = min(WORLD_AXES.items(), key=lambda kv: abs(
            kv[1][0] * normal[0] + kv[1][1] * normal[1] + kv[1][2] * normal[2]))
        return best[1], ("the curve is a straight line, so it has no plane; "
                         "World {0} was used instead".format(best[0]))

    if kind == "bent":
        return normal, "the curve is not planar; the best-fit plane's normal was used"

    return normal, ""


# ==========================================================================
# 서피스 만들기
# ==========================================================================

def _scaled_knots(knots, domain, reverse=False):
    """노트를 도메인 기준 0..1 로 정규화하고, reverse 면 뒤집는다(주기 커브의 바깥 노트도 함께)."""
    start, end = domain
    span = end - start
    if span <= 0:
        return list(knots)
    out = [(k - start) / span for k in knots]
    if reverse:
        out = [1.0 - k for k in reversed(out)]
    return out


def _reversed_knots(knots, domain):
    start, end = domain
    return [start + end - k for k in reversed(knots)]


def _short_name(node):
    return node.split("|")[-1].split(":")[-1]


def build_ribbon(curve, width=DEFAULT_WIDTH, direction=DIRECTION_AUTO,
                 across_degree=DEFAULT_ACROSS_DEGREE, normalize_u=True,
                 reverse_u=False, name=None):
    """커브 하나 → 리본 서피스 하나.

    반환 dict: ok, surface(트랜스폼), shape, message, note(방향 결정에 대한 알림), direction(단위 벡터)
    """
    shape = curve_shape(curve)
    if not shape:
        return {"ok": False, "message": "not a NURBS curve"}

    if width <= 0:
        return {"ok": False, "message": "width must be greater than 0"}

    if across_degree not in ACROSS_DEGREES:
        return {"ok": False, "message": "across degree must be one of {0}".format(ACROSS_DEGREES)}

    data = curve_data(shape)
    points = data["points"]
    if len(points) < 2:
        return {"ok": False, "message": "the curve has fewer than 2 CVs"}

    vec, note = offset_direction(points, direction)
    if vec is None:
        return {"ok": False, "message": note}

    # U 노트 : 그대로 / 0..1 / 뒤집기
    knots_u = list(data["knots"])
    if normalize_u:
        knots_u = _scaled_knots(knots_u, data["domain"], reverse=reverse_u)
    elif reverse_u:
        knots_u = _reversed_knots(knots_u, data["domain"])

    rows = points[::-1] if reverse_u else points

    base_name = (name or "").strip() or (_short_name(curve) + NAME_SUFFIX)

    # ★ `cmds.surface` 로 서피스를 직접 정의하면 가장 간단하지만 그 명령은 **undo 가 안 된다**
    #   (mayapy 실측: undo 큐에 오르지 않아 Ctrl+Z 가 이름 바꾸기만 되돌리고 서피스는 남는다).
    #   그래서 undo 되는 명령만으로 같은 결과를 만든다 — 양쪽으로 벌린 **임시 커브 두 개**를
    #   `cmds.curve`(CV + 노트 직접 지정, 주기 커브는 `per=True`) 로 월드에 만들고 `loft`(히스토리
    #   없음) 한 뒤 임시 커브를 지운다. 노트 정규화 · U 뒤집기는 임시 커브의 CV 순서와 노트에
    #   이미 반영돼 있어 rebuild / reverseSurface 가 필요 없다. 한 undo 청크 안에서 서피스만 남는다.
    periodic = data["form"] == "periodic"
    half = width * 0.5
    sides = []
    for sign in (-1.0, 1.0):
        pts = [(p[0] + vec[0] * half * sign, p[1] + vec[1] * half * sign, p[2] + vec[2] * half * sign)
               for p in rows]
        sides.append(cmds.curve(degree=data["degree"], periodic=periodic, point=pts, knot=knots_u,
                                name="JUN_tmpRibbonSide#"))

    # autoReverse 는 끈다 — 두 커브의 방향이 같다는 것을 우리가 보장하므로 마야가 한쪽을 뒤집어
    # 리본을 꼬게 둘 이유가 없다. 나머지는 마야 Loft 옵션 박스 기본값(uniform · degree · sectionSpans 1).
    transform = cmds.loft(sides[0], sides[1], name=base_name, constructionHistory=False,
                          uniform=True, close=False, autoReverse=False, degree=across_degree,
                          sectionSpans=1, range=False, polygon=0, reverseSurfaceNormals=True)[0]
    cmds.delete(sides)
    transform = cmds.ls(transform, long=True)[0]
    surface_shape = cmds.listRelatives(transform, shapes=True, fullPath=True)[0]

    if across_degree == 1:
        # loft -d 1 은 V 노트를 [0, 2] 로 둔다(실측). 폭 방향은 두 줄짜리 직선이라 uniform 으로
        # 다시 매개변수화해도 모양은 같다 — V 만(dir=1) 0..1 로, CV 는 유지(kcp).
        cmds.rebuildSurface(transform, constructionHistory=False, replaceOriginal=True,
                            rebuildType=0, endKnots=1, keepRange=0, keepControlPoints=True,
                            direction=1, degreeV=1, degreeU=data["degree"])

    return {
        "ok": True,
        "surface": transform,
        "shape": surface_shape,
        "direction": vec,
        "note": note,
        "message": "{0} <- {1}".format(_short_name(transform), _short_name(curve)),
    }


def create_ribbons(curves, width=DEFAULT_WIDTH, direction=DIRECTION_AUTO,
                   across_degree=DEFAULT_ACROSS_DEGREE, normalize_u=True,
                   reverse_u=False, name=None, select=True):
    """리스트의 커브마다 리본 하나. 이름을 주면 두 개째부터 마야가 번호를 붙인다.

    반환 dict: ok, surfaces, skipped[(curve, why)], notes[(surface, note)], message
    """
    surfaces = []
    skipped = []
    notes = []

    for curve in curves or []:
        result = build_ribbon(curve, width=width, direction=direction,
                              across_degree=across_degree, normalize_u=normalize_u,
                              reverse_u=reverse_u, name=name)
        if not result["ok"]:
            skipped.append((curve, result["message"]))
            continue
        surfaces.append(result["surface"])
        if result["note"]:
            notes.append((result["surface"], result["note"]))

    if select and surfaces:
        cmds.select(surfaces, replace=True)

    if not surfaces:
        return {"ok": False, "surfaces": [], "skipped": skipped, "notes": notes,
                "message": "No ribbon was created."}

    label = DIRECTION_LABELS.get(direction, direction)
    message = "Created {0} ribbon{1}: {2}  (width {3:g}, {4}, {5} across).".format(
        len(surfaces), "s" if len(surfaces) != 1 else "",
        ", ".join(_short_name(s) for s in surfaces),
        width, label.split(" (")[0], "cubic" if across_degree == 3 else "linear")

    return {"ok": True, "surfaces": surfaces, "skipped": skipped, "notes": notes,
            "message": message}
