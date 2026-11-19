# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-19
# A00630_MotionPathEditor - 화면 투영 · 키 고르기 · 드래그 평면 (계획서 §4-6)
"""
순수 계산(numpy, 헤드리스 시험 가능)과 마야 뷰에서 행렬 · 광선을 읽는 부분(`ViewState`)을 나눴다.

화면 좌표 = M3dView 의 픽셀 좌표 (왼쪽 아래가 원점). draggerContext(space="screen") 가 주는 좌표와 같다.
"""

import numpy as np

PICK_RADIUS_PX = 10.0

PLANE_VIEW = "view"
PLANE_GROUND = "ground"
AXIS_X = "x"
AXIS_Y = "y"
AXIS_Z = "z"
PLANES = (PLANE_VIEW, PLANE_GROUND, AXIS_X, AXIS_Y, AXIS_Z)


# ---------------------------------------------------------------------- 순수 계산
def project(points, view_proj, width, height):
    """(N,3) 월드 점 → (N,2) 픽셀, (N,) 카메라 앞인지. view_proj = 모델뷰 · 투영 (행 벡터 4x4)."""
    pts = np.asarray(points, dtype="float64").reshape(-1, 3)
    if not len(pts):
        return np.zeros((0, 2)), np.zeros((0,), dtype=bool)
    clip = np.hstack([pts, np.ones((len(pts), 1))]) @ np.asarray(view_proj, dtype="float64")
    w = clip[:, 3]
    front = w > 1e-9
    safe = np.where(front, w, 1.0)
    ndc = clip[:, :2] / safe[:, None]
    px = np.empty((len(pts), 2))
    px[:, 0] = (ndc[:, 0] * 0.5 + 0.5) * width
    px[:, 1] = (ndc[:, 1] * 0.5 + 0.5) * height
    return px, front


def nearest(px, front, x, y, radius=PICK_RADIUS_PX):
    """(x, y) 에서 radius 안의 가장 가까운 점 인덱스, 없으면 None."""
    if not len(px):
        return None
    d = np.hypot(px[:, 0] - x, px[:, 1] - y)
    d = np.where(front, d, np.inf)
    i = int(np.argmin(d))
    return i if d[i] <= radius else None


def inside_box(px, front, x0, y0, x1, y1):
    """박스 안 점 인덱스 목록."""
    if not len(px):
        return []
    lo_x, hi_x = min(x0, x1), max(x0, x1)
    lo_y, hi_y = min(y0, y1), max(y0, y1)
    ok = front & (px[:, 0] >= lo_x) & (px[:, 0] <= hi_x) & (px[:, 1] >= lo_y) & (px[:, 1] <= hi_y)
    return [int(i) for i in np.nonzero(ok)[0]]


def ray_plane(origin, direction, point, normal):
    """광선과 평면의 교점, 평행하면 None."""
    o, d, p, n = (np.asarray(v, dtype="float64") for v in (origin, direction, point, normal))
    den = float(d @ n)
    if abs(den) < 1e-12:
        return None
    t = float((p - o) @ n) / den
    return o + d * t


def ray_axis(origin, direction, point, axis):
    """광선에 가장 가까운 축 직선(point + s·axis) 위의 점."""
    o, d, p, a = (np.asarray(v, dtype="float64") for v in (origin, direction, point, axis))
    a = a / np.linalg.norm(a)
    d = d / np.linalg.norm(d)
    w = p - o
    b = float(a @ d)
    den = 1.0 - b * b
    if den < 1e-12:
        return p.copy()
    s = (b * float(w @ d) - float(w @ a)) / den
    return p + a * s


def drag_target(plane, origin, direction, anchor, view_dir):
    """드래그 평면 · 축에서 마우스 광선이 가리키는 점."""
    axes = {AXIS_X: (1.0, 0.0, 0.0), AXIS_Y: (0.0, 1.0, 0.0), AXIS_Z: (0.0, 0.0, 1.0)}
    if plane in axes:
        return ray_axis(origin, direction, anchor, axes[plane])
    normal = (0.0, 1.0, 0.0) if plane == PLANE_GROUND else view_dir
    return ray_plane(origin, direction, anchor, normal)


# ---------------------------------------------------------------------- 마야 뷰
class ViewState(object):
    """지금 3D 뷰의 행렬 · 크기 · 광선 (GUI 에서만)."""

    def __init__(self):
        import maya.api.OpenMayaUI as omui
        self.view = omui.M3dView.active3dView()
        mv = self.view.modelViewMatrix()
        pr = self.view.projectionMatrix()
        self.view_proj = np.array([[(mv * pr).getElement(r, c) for c in range(4)] for r in range(4)])
        self.width = self.view.portWidth()
        self.height = self.view.portHeight()
        cam = self.view.getCamera()
        import maya.api.OpenMaya as om
        fn = om.MFnCamera(cam)
        vd = fn.viewDirection(om.MSpace.kWorld)
        self.view_dir = np.array([vd.x, vd.y, vd.z])

    def ray(self, x, y):
        """화면 (x, y) 의 월드 광선 (원점, 단위 방향)."""
        return view_ray(self.view, x, y, self.view_dir)


def view_ray(view, x, y, fallback_dir):
    """M3dView 의 화면 (x, y) → 월드 광선 (원점, 단위 방향).

    v01.01 - 마야 2024 API 2.0 의 `viewToWorld(x, y, worldPt, worldVector)` 는 결과를 **돌려주지 않고 인자로 넘긴
    MPoint / MVector 를 채운다**(OUT 인자). 처음에 결과를 돌려받는 줄 알고 인자 2개로 불러
    "function takes exactly 4 arguments (2 given)" 로 드래그가 실패했다 - 시험 `test_picking.py` 가 이 모양을 고정한다.
    """
    import maya.api.OpenMaya as om
    point, vector = om.MPoint(), om.MVector()
    view.viewToWorld(int(x), int(y), point, vector)
    o = np.array([point.x, point.y, point.z])
    d = np.array([vector.x, vector.y, vector.z])
    n = np.linalg.norm(d)
    return o, (d / n if n > 1e-12 else np.asarray(fallback_dir, dtype="float64"))

    def refresh(self):
        self.view.refresh(False, True)
