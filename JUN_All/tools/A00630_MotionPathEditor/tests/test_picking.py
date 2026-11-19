# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 화면 투영 · 키 고르기 · 드래그 평면 시험 (순수 numpy - 마야 없이 돈다, numpy 가 있는 mayapy 로)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_picking.py
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
from tools.A00630_MotionPathEditor.app.core import picking as pk   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if str(extra) else ""))


# 정사영 같은 단순 행렬 : x, y 를 -10..10 -> NDC -1..1, w = 1 (행 벡터 규약)
VP = np.diag([0.1, 0.1, 0.1, 1.0])
pts = np.array([[0.0, 0.0, 0.0], [5.0, 5.0, 0.0], [-10.0, -10.0, 0.0], [9.0, -9.0, 0.0]])
px, front = pk.project(pts, VP, 200, 100)
check("project: centre -> middle of the view", np.allclose(px[0], [100, 50]), px[0])
check("project: corner -> pixel 0, 0", np.allclose(px[2], [0, 0]), px[2])
check("project: all in front", front.all())
check("nearest within the radius", pk.nearest(px, front, 151, 74) == 1)
check("nothing within the radius -> None", pk.nearest(px, front, 30, 90) is None)
check("box select picks what is inside", pk.inside_box(px, front, 90, 40, 160, 80) == [0, 1])
check("box works dragged either way", pk.inside_box(px, front, 160, 80, 90, 40) == [0, 1])
# 카메라 뒤 (w < 0) 는 고르지 않는다
VPb = VP.copy()
VPb[3, 3] = -1.0
pxb, frontb = pk.project(pts, VPb, 200, 100)
check("points behind the camera are never picked", not frontb.any() and pk.nearest(pxb, frontb, 100, 50) is None)

# 평면 · 축
o = np.array([0.0, 10.0, 0.0])
d = np.array([0.0, -1.0, 0.0])
hit = pk.ray_plane(o, d, [3.0, 2.0, 1.0], [0.0, 1.0, 0.0])
check("ray hits the ground plane through the anchor", np.allclose(hit, [0.0, 2.0, 0.0]), hit)
check("parallel ray -> None", pk.ray_plane(o, [1.0, 0.0, 0.0], [0, 0, 0], [0, 1, 0]) is None)
anchor = np.array([1.0, 2.0, 3.0])
on_x = pk.drag_target(pk.AXIS_X, np.array([5.0, 10.0, 3.0]), np.array([0.0, -1.0, 0.0]), anchor, [0, 0, -1])
check("X axis drag stays on the X line through the anchor", np.allclose(on_x[1:], anchor[1:]) and
      abs(on_x[0] - 5.0) < 1e-9, on_x)
view = pk.drag_target(pk.PLANE_VIEW, np.array([4.0, 6.0, 10.0]), np.array([0.0, 0.0, -1.0]), anchor, [0, 0, -1])
check("View plane drag keeps the anchor's depth", np.allclose(view, [4.0, 6.0, 3.0]), view)
ground = pk.drag_target(pk.PLANE_GROUND, np.array([7.0, 9.0, -2.0]), np.array([0.0, -1.0, 0.0]), anchor, [0, 0, -1])
check("Ground drag keeps the anchor's height", np.allclose(ground, [7.0, 2.0, -2.0]), ground)

print("\nRESULT: {0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
