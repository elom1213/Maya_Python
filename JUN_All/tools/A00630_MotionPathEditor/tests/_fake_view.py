# -*- coding: utf-8 -*-
# A00630_MotionPathEditor 시험 공용: 가짜 3D 뷰 (정면 정사영 카메라) - test_edit_context · test_falloff 가 함께 쓴다.
# 가짜 M3dView 의 viewToWorld 는 **마야 2024 와 같은 모양**(x, y, worldPt, worldVector 를 받아 OUT 인자를 채움).
import maya.api.OpenMaya as om
import numpy as np

from tools.A00630_MotionPathEditor.app.core import picking

W, H = 1000, 800
HALF = 20.0                      # 화면 가로 반폭이 월드 20 cm
CX, CY = 0.0, 0.0


class FakeM3dView(object):
    """마야 2024 API 2.0 과 같은 시그니처 - viewToWorld 는 OUT 인자를 채운다(돌려주지 않는다)."""

    def viewToWorld(self, x_pos, y_pos, worldPt, worldVector):
        assert isinstance(worldPt, om.MPoint) and isinstance(worldVector, om.MVector)
        worldPt.x = (x_pos / float(W) * 2.0 - 1.0) * HALF + CX
        worldPt.y = (y_pos / float(H) * 2.0 - 1.0) * HALF * H / W + CY
        worldPt.z = 100.0
        worldVector.x, worldVector.y, worldVector.z = 0.0, 0.0, -1.0
        return self


class FakeViewState(object):
    """정면(-Z 방향) 정사영 카메라."""

    def __init__(self):
        self.view = FakeM3dView()
        sx, sy = 1.0 / HALF, 1.0 / (HALF * H / W)
        # z 는 -0.01 : 카메라가 -Z 를 본다(z 가 클수록 가깝다 = NDC -1 쪽) - v01.11 기즈모가 행렬에서 시선 방향을 뽑는다
        self.view_proj = np.array([[sx, 0, 0, 0], [0, sy, 0, 0], [0, 0, -0.01, 0], [-CX * sx, -CY * sy, 0, 1.0]])
        self.width, self.height = W, H
        self.view_dir = np.array([0.0, 0.0, -1.0])

    def ray(self, x, y):
        return picking.view_ray(self.view, x, y, self.view_dir)


def to_pixel(p):
    px, _front = picking.project([p], FakeViewState().view_proj, W, H)
    return float(px[0][0]), float(px[0][1])


def to_world_xy(x, y, z):
    o, d = FakeViewState().ray(x, y)
    return np.array([o[0], o[1], z])
