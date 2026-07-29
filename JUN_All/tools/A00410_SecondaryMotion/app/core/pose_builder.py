# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-29
# A00410_SecondaryMotion core - 시뮬레이션된 '점 위치' -> 각 노드의 '로컬 회전 키값'.
#
# 솔버는 점으로 풀고, 결과는 컨트롤러/조인트의 **회전 키**여야 한다. 그 변환을 담당한다.
#
# 원리 (row-vector 규약, mayapy 로 검증한 규칙)
# --------------------------------------------
#   rest_dir = normalize(T[i+1] - T[i])        # 원본(강체 FK) 방향
#   sim_dir  = normalize(P[i+1] - P[i])        # 시뮬 방향
#   q_swing  = MQuaternion(rest_dir, sim_dir)  # 두 방향 사이의 **순수 스윙**(트위스트 없음)
#   W_new    = W_orig * q_swing                # 월드 회전에 스윙을 덧붙임
#   L        = W_new * inverse(parent_world_new)      # world = local * parentWorld
#   R        = RA^-1 * L * JO^-1               # joint: local = R*JO / transform: local = RA*R
#   rotate   = euler(R, 노드의 rotateOrder)
#
# 두 가지가 이 방식의 핵심이다.
#   1) q_swing 이 **순수 스윙**이라 원본 애니메이션의 **트위스트(롤)가 보존**된다.
#   2) 솔버가 길이를 구속했기 때문에 |P[i+1]-P[i]| == |T[i+1]-T[i]| 이고, 따라서 i 를
#      회전시키면 자식이 **정확히** P[i+1] 에 놓인다 — 점 시뮬과 회전 결과가 어긋나지 않는다.
#
# 팁(마지막) 노드는 자식이 없어 방향을 정의할 수 없으므로 **원본 회전을 그대로 둔다**.

import math

from maya.api import OpenMaya as om


_EPS = 1e-9


def _dir(a, b):
    """a -> b 단위벡터. 길이가 0 이면 None."""
    v = om.MVector(b[0] - a[0], b[1] - a[1], b[2] - a[2])
    L = v.length()
    if L < _EPS:
        return None
    return v / L


def _unwrap(value, prev):
    """오일러 연속성 — 이전 프레임 값에서 ±180 이상 튀면 360 배수로 맞춰 붙인다.

    회전 재구성은 매 프레임 독립적으로 오일러를 뽑기 때문에, 그대로 두면 ±180 경계에서
    커브가 통째로 점프한다(그래프 에디터에서 뚝 끊긴다). 키를 쓰기 전에 반드시 편다.
    """
    if prev is None:
        return value
    while value - prev > 180.0:
        value -= 360.0
    while prev - value > 180.0:
        value += 360.0
    return value


def build_rotations(sample, sim_positions):
    """ChainSample + 시뮬 위치 -> 노드별 로컬 회전(도) 프레임열.

    반환: [ [ (rx, ry, rz), ... 프레임 수만큼 ], ... 회전을 쓰는 노드 수만큼 ]
          가상 팁이 있으면 **모든 실제 노드**(팁 포함)의 회전이 나오고,
          없으면 팁을 뺀 노드 수 - 1 개가 나온다.
    """
    n_pts = sample.point_count()
    if n_pts < 2:
        return []

    n_rot = min(n_pts - 1, sample.count())
    out = [[] for _ in range(n_rot)]
    prev_vals = [None] * n_rot        # 오일러 언랩용(노드별 직전 프레임 값)

    for f in range(len(sample.frames)):
        T = sample.positions[f]
        P = sim_positions[f]
        W = sample.world_quats[f]
        parents = sample.parent_quats[f]

        # 직전 체인 노드에 얹힌 월드 델타. 그 노드의 **모든 자손**(중간 오프셋 그룹
        # 포함)이 이 델타를 그대로 물려받으므로, 다음 노드의 '현재 부모 월드 회전'은
        # 원본 부모 회전 * 이 델타가 된다.
        prev_delta = None

        for i in range(n_rot):
            rest_dir = _dir(T[i], T[i + 1])
            sim_dir = _dir(P[i], P[i + 1])

            if rest_dir is None or sim_dir is None:
                # 길이 0 인 뼈 — 회전을 정의할 수 없으니 원본 로컬 회전을 그대로 둔다.
                vals = sample.rest_local[i]
                out[i].append(vals)
                prev_vals[i] = vals
                prev_delta = om.MQuaternion()
                continue

            q_swing = om.MQuaternion(rest_dir, sim_dir)
            w_new = W[i] * q_swing

            # 부모는 **실제 DAG 부모**여야 한다. 앞 체인 노드로 대신하면 그 사이의
            # 오프셋 그룹 회전이 컨트롤러 로컬값에 섞여 들어가, 스윙이 0 인 첫
            # 프레임부터 원래 포즈가 깨지고 하위 노드가 통째로 어긋난다.
            parent_q = parents[i]
            if prev_delta is not None:
                parent_q = parent_q * prev_delta

            local = w_new * parent_q.inverse()
            r = sample.ra_inv[i] * local * sample.jo_inv[i]

            # asEulerRotation() 은 kXYZ 로 주므로 노드의 rotateOrder 로 다시 푼다.
            e = r.asEulerRotation().reorder(sample.orders[i])

            vals = (math.degrees(e.x), math.degrees(e.y), math.degrees(e.z))
            if prev_vals[i] is not None:
                vals = (_unwrap(vals[0], prev_vals[i][0]),
                        _unwrap(vals[1], prev_vals[i][1]),
                        _unwrap(vals[2], prev_vals[i][2]))
            out[i].append(vals)
            prev_vals[i] = vals

            prev_delta = q_swing

    return out
