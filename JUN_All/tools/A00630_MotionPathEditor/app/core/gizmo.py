# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00630_MotionPathEditor - 이동 · 회전 매니퓰레이터 (매니퓰레이터 · 폴오프 계획서 §3-4, G3) - 마야 · Qt 비의존
"""
고른 경로 점들의 무게중심에 그리는 기즈모. **모양 · 고르기 · 끌기 수학**이 모두 여기 있고,
편집 컨텍스트(고르기 · 끌기)와 플러그인(그리기)이 같은 `geometry()` 를 쓴다 - 보이는 것과 잡히는 것이 늘 같다.

    move   : 축 화살표 x / y / z · 평면 사각형 xy / yz / zx · 가운데 사각형 (화면 평면 이동)
    rotate : 축 고리 rx / ry / rz · 바깥 화면 고리 rv (시선 축 회전)

- 크기는 **화면 픽셀 고정**(SIZE_PX) - 그 깊이에서 1 px 의 월드 길이를 투영으로 재서 곱한다(원근 · 정사영 모두).
- 축 = World 또는 Path(고른 점 자리의 접선 · 위쪽 · 옆 - path_frame).
- 행렬 규약은 picking 과 같다: 행 벡터 · view_proj (4x4), 픽셀은 왼쪽 아래 원점.
"""

import numpy as np

SIZE_PX = 90.0          # 화살표 길이 · 고리 반지름 (픽셀)
HIT_PX = 8.0            # 이만큼 가까우면 잡힌다
VIEW_RING = 1.2         # 화면 고리 반지름 = SIZE_PX 의 배수
PLANE_LO, PLANE_HI = 0.25, 0.45     # 평면 사각형 (축 길이 비율)
CENTER = 0.09           # 가운데 사각형 반폭 (축 길이 비율)
RING_SEGMENTS = 64
LINE_WIDTH = 3.0        # v01.12 사용자 요청으로 1.5 배 (2.0 → 3.0)
ACTIVE_WIDTH = 4.5      # 잡은 부분 (3.0 → 4.5)
HEAD_LEN, HEAD_HALF = 18.0, 7.5     # 화살표 머리 (픽셀, 12 / 5 의 1.5 배)

MODE_MOVE = "move"
MODE_ROTATE = "rotate"
AXES_WORLD = "world"
AXES_PATH = "path"

COLORS = {"x": (0.95, 0.25, 0.25), "y": (0.35, 0.9, 0.3), "z": (0.3, 0.5, 1.0),
          "xy": (0.3, 0.5, 1.0), "yz": (0.95, 0.25, 0.25), "zx": (0.35, 0.9, 0.3),
          "center": (0.95, 0.95, 0.6), "rx": (0.95, 0.25, 0.25), "ry": (0.35, 0.9, 0.3), "rz": (0.3, 0.5, 1.0),
          "rv": (0.7, 0.85, 0.95)}
ACTIVE_COLOR = (1.0, 0.9, 0.1)
_PLANE_AXES = {"xy": (0, 1), "yz": (1, 2), "zx": (2, 0)}
_PLANE_NORMAL = {"xy": 2, "yz": 0, "zx": 1}
_AXIS = {"x": 0, "y": 1, "z": 2, "rx": 0, "ry": 1, "rz": 2}


# ---------------------------------------------------------------------- 뷰
def project(points, view_proj, width, height):
    """(N,3) → (N,2) 픽셀, (N,) 카메라 앞."""
    P = np.asarray(points, dtype="float64").reshape(-1, 3)
    clip = np.hstack([P, np.ones((len(P), 1))]) @ np.asarray(view_proj, dtype="float64")
    w = clip[:, 3]
    front = w > 1e-9
    safe = np.where(front, w, 1.0)
    px = np.empty((len(P), 2))
    px[:, 0] = (clip[:, 0] / safe * 0.5 + 0.5) * width
    px[:, 1] = (clip[:, 1] / safe * 0.5 + 0.5) * height
    return px, front


def view_dir(view_proj):
    """view_proj 에서 시선 방향 (월드, 단위) - 화면 가운데의 가까운 면 → 먼 면."""
    inv = np.linalg.inv(np.asarray(view_proj, dtype="float64"))
    a = np.array([0.0, 0.0, -1.0, 1.0]) @ inv
    b = np.array([0.0, 0.0, 1.0, 1.0]) @ inv
    d = b[:3] / b[3] - a[:3] / a[3]
    n = np.linalg.norm(d)
    return d / n if n > 1e-12 else np.array([0.0, 0.0, -1.0])


def world_per_px(pivot, view_proj, width, height, vdir=None):
    """pivot 깊이에서 화면 1 px 의 월드 길이."""
    vdir = view_dir(view_proj) if vdir is None else np.asarray(vdir, dtype="float64")
    side = np.cross(vdir, [0.0, 1.0, 0.0])
    if np.linalg.norm(side) < 1e-6:
        side = np.cross(vdir, [1.0, 0.0, 0.0])
    side /= np.linalg.norm(side)
    pivot = np.asarray(pivot, dtype="float64")
    eps = 1.0
    for _ in range(3):              # 원근에서 eps 가 너무 크거나 작지 않게 한두 번 맞춘다
        px, front = project([pivot, pivot + side * eps], view_proj, width, height)
        d = float(np.linalg.norm(px[1] - px[0]))
        if not front.all() or d < 1e-9:
            return 1.0
        eps_new = eps * 10.0 / d    # 10 px 쯤 되는 길이로 다시
        if abs(eps_new / eps - 1.0) < 0.05:
            break
        eps = eps_new
    return eps / d


# ---------------------------------------------------------------------- 축
def path_frame(points, row):
    """(3,3) 행 = 축 x(접선) · y(위쪽에 가장 가까운 수직) · z(옆). 경로가 멈춘 곳이면 월드."""
    P = np.asarray(points, dtype="float64")
    a, b = max(row - 1, 0), min(row + 1, len(P) - 1)
    t = P[b] - P[a]
    if np.linalg.norm(t) < 1e-9:
        return np.eye(3)
    t /= np.linalg.norm(t)
    up = np.array([0.0, 1.0, 0.0])
    if abs(float(t @ up)) > 0.98:
        up = np.array([0.0, 0.0, 1.0])
    y = up - t * float(up @ t)
    y /= np.linalg.norm(y)
    return np.vstack([t, y, np.cross(t, y)])


# ---------------------------------------------------------------------- 모양
def _ring(center, normal, radius, segments=RING_SEGMENTS):
    n = np.asarray(normal, dtype="float64")
    n = n / np.linalg.norm(n)
    b1 = np.cross(n, [0.3, 0.5, 0.7])
    if np.linalg.norm(b1) < 1e-6:
        b1 = np.cross(n, [1.0, 0.0, 0.0])
    b1 /= np.linalg.norm(b1)
    b2 = np.cross(n, b1)
    ang = np.linspace(0.0, 2.0 * np.pi, segments + 1)
    return center + radius * (np.outer(np.cos(ang), b1) + np.outer(np.sin(ang), b2))


def geometry(pivot, axes, mode, length, vdir):
    """[(부분 이름, (k,3) 폴리라인)] - 그리기와 고르기가 같이 쓴다. length = 화살표 월드 길이."""
    p = np.asarray(pivot, dtype="float64")
    A = np.asarray(axes, dtype="float64")
    out = []
    if mode == MODE_ROTATE:
        for name in ("rx", "ry", "rz"):
            out.append((name, _ring(p, A[_AXIS[name]], length)))
        out.append(("rv", _ring(p, vdir, length * VIEW_RING)))
        return out
    for name in ("x", "y", "z"):           # 가운데 사각형 바깥에서 시작 (가운데를 누르면 화면 평면 이동)
        out.append((name, np.vstack([p + A[_AXIS[name]] * length * CENTER * 1.6, p + A[_AXIS[name]] * length])))
    for name, (i, j) in _PLANE_AXES.items():
        u, v = A[i] * length, A[j] * length
        out.append((name, np.vstack([p + u * PLANE_LO + v * PLANE_LO, p + u * PLANE_HI + v * PLANE_LO,
                                     p + u * PLANE_HI + v * PLANE_HI, p + u * PLANE_LO + v * PLANE_HI,
                                     p + u * PLANE_LO + v * PLANE_LO])))
    s1 = np.cross(vdir, [0.0, 1.0, 0.0])
    if np.linalg.norm(s1) < 1e-6:
        s1 = np.cross(vdir, [1.0, 0.0, 0.0])
    s1 = s1 / np.linalg.norm(s1) * length * CENTER
    s2 = np.cross(vdir, s1)
    s2 = s2 / np.linalg.norm(s2) * length * CENTER
    out.append(("center", np.vstack([p - s1 - s2, p + s1 - s2, p + s1 + s2, p - s1 + s2, p - s1 - s2])))
    return out


def tips(pivot, axes, length):
    """[(이름, 점)] - 화살표 끝 (큰 점으로 그린다)."""
    p = np.asarray(pivot, dtype="float64")
    A = np.asarray(axes, dtype="float64")
    return [(n, p + A[_AXIS[n]] * length) for n in ("x", "y", "z")]


# ---------------------------------------------------------------------- 고르기
def _dist_to_polyline(px, x, y):
    a, b = px[:-1], px[1:]
    d = b - a
    dd = np.maximum((d * d).sum(axis=1), 1e-12)
    q = np.array([x, y], dtype="float64")
    t = np.clip(((q - a) * d).sum(axis=1) / dd, 0.0, 1.0)
    return float(np.linalg.norm(a + d * t[:, None] - q, axis=1).min())


def hit(pivot, axes, mode, view_proj, width, height, x, y, radius=HIT_PX):
    """화면 (x, y) 에서 잡히는 부분 이름 또는 None.

    순서: 가운데 사각형 안쪽 → 축 화살표 · 고리 선(가까운 것) → 평면 사각형(테두리 근처 또는 안쪽) → 가운데 테두리 근처.
    가운데가 먼저인 이유: 카메라 쪽을 향한 축은 화면에서 짧아져 시작점이 가운데와 겹친다(원근 시험이 잡음) - 마야도 가운데가 먼저다.
    """
    vdir = view_dir(view_proj)
    length = SIZE_PX * world_per_px(pivot, view_proj, width, height, vdir)
    shapes = []
    for name, line in geometry(pivot, axes, mode, length, vdir):
        px, front = project(line, view_proj, width, height)
        if front.all():
            shapes.append((name, px))
    for name, px in shapes:
        if name == "center" and _inside(px, x, y):
            return name
    best, part = radius, None
    for name, px in shapes:
        if name in _PLANE_AXES or name == "center":
            continue
        d = _dist_to_polyline(px, x, y)
        if d < best:
            best, part = d, name
    if part is not None:
        return part
    for name, px in shapes:
        if name in _PLANE_AXES and (_inside(px, x, y) or _dist_to_polyline(px, x, y) < radius * 0.5):
            return name
    for name, px in shapes:
        if name == "center" and (_inside(px, x, y) or _dist_to_polyline(px, x, y) < radius * 0.5):
            return name
    return None


def _inside(poly, x, y):
    """닫힌 폴리곤(볼록) 안인가."""
    p = poly[:-1]
    n = len(p)
    sign = 0.0
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        c = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
        if abs(c) < 1e-12:
            continue
        if sign == 0.0:
            sign = np.sign(c)
        elif np.sign(c) != sign:
            return False
    return True


# ---------------------------------------------------------------------- 끌기
def _ray_plane(o, d, p, n):
    den = float(d @ n)
    if abs(den) < 1e-12:
        return None
    return o + d * (float((p - o) @ n) / den)


def _ray_axis(o, d, p, a):
    a = a / np.linalg.norm(a)
    w = p - o
    b = float(a @ d)
    den = 1.0 - b * b
    if den < 1e-12:
        return p.copy()
    s = (b * float(w @ d) - float(w @ a)) / den
    return p + a * s


def move_point(part, pivot, axes, origin, direction, vdir):
    """그 부분을 잡고 끌 때, 마우스 광선이 가리키는 월드 점 (시작 점과의 차이 = 이동량). 평행하면 None."""
    p = np.asarray(pivot, dtype="float64")
    A = np.asarray(axes, dtype="float64")
    o, d = np.asarray(origin, dtype="float64"), np.asarray(direction, dtype="float64")
    if part in ("x", "y", "z"):
        return _ray_axis(o, d, p, A[_AXIS[part]])
    if part in _PLANE_NORMAL:
        return _ray_plane(o, d, p, A[_PLANE_NORMAL[part]])
    return _ray_plane(o, d, p, np.asarray(vdir, dtype="float64"))      # center = 화면 평면


def rotate_axis(part, axes, vdir):
    if part == "rv":
        return np.asarray(vdir, dtype="float64") / np.linalg.norm(vdir)
    return np.asarray(axes, dtype="float64")[_AXIS[part]]


def rotate_angle(part, pivot, axes, vdir, ray0, ray1, view_proj=None, width=None, height=None, px0=None, px1=None):
    """고리를 ray0 → ray1 로 끈 각도 (라디안, 축 둘레 오른손).

    고리 평면이 시선과 거의 나란하면(고리가 선으로 보임) 평면 교점이 튄다 → 화면에서 고리 접선 방향 이동량 / 반지름 으로 대신
    (마야 회전 툴과 같은 처리).
    """
    p = np.asarray(pivot, dtype="float64")
    n = rotate_axis(part, axes, vdir)
    if abs(float(n @ np.asarray(vdir))) > 0.2 or px0 is None:
        h0 = _ray_plane(np.asarray(ray0[0]), np.asarray(ray0[1]), p, n)
        h1 = _ray_plane(np.asarray(ray1[0]), np.asarray(ray1[1]), p, n)
        if h0 is not None and h1 is not None:
            v0, v1 = h0 - p, h1 - p
            if np.linalg.norm(v0) > 1e-9 and np.linalg.norm(v1) > 1e-9:
                return float(np.arctan2(float(np.cross(v0, v1) @ n), float(v0 @ v1)))
    # 화면 접선 방식: 고리 위 잡은 점의 접선을 화면에 투영
    c_px = project([p], view_proj, width, height)[0][0]
    r = np.asarray(px0, dtype="float64") - c_px
    if np.linalg.norm(r) < 1e-6:
        return 0.0
    tangent = np.array([-r[1], r[0]]) / np.linalg.norm(r)       # 화면에서 반시계 방향
    if float(n @ np.asarray(vdir)) > 0:                         # 축이 화면 안쪽을 향하면 방향이 반대
        tangent = -tangent
    move = np.asarray(px1, dtype="float64") - np.asarray(px0, dtype="float64")
    return float(move @ tangent) / max(SIZE_PX, 1.0)


def rotate_points(P, pivot, axis, angle, weights):
    """점마다 weights·angle 만큼 axis 둘레 회전 (Rodrigues). P (N,3)."""
    k = np.asarray(axis, dtype="float64")
    k = k / np.linalg.norm(k)
    v = np.asarray(P, dtype="float64") - pivot
    a = (np.asarray(weights, dtype="float64") * angle)[:, None]
    cos, sin = np.cos(a), np.sin(a)
    kv = np.cross(np.broadcast_to(k, v.shape), v)
    kd = (v @ k)[:, None]
    return pivot + v * cos + kv * sin + k[None, :] * kd * (1.0 - cos)
