# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# Framework.core.euler_math - 순수 파이썬 오일러 동치 · 언랩 · 3x3 회전 행렬 (maya · numpy 없이)
#
# 회전 순서 문자열은 **앞 글자가 먼저 적용**된다 ("XZY" = X 다음 Z 다음 Y). 마야 rotateOrder xyz 와 같은 뜻이다.
# 행렬은 열 벡터 규약 - matrix(v, "XYZ") = Rz · Ry · Rx.
#
# 같은 방향을 주는 오일러는 (2π 배수 말고도) 하나 더 있다 - first+180, 180-middle, last+180.
# 마야 FBX 임포터는 이 동치를 회전 순서와 상관없이 XYZ 꼴 (x+180, 180-y, z+180) 로 써서 비 XYZ 조인트를 뒤집는다
# (계획서 docs/plans/A00480_FileTool_fbx_exact_import_plan.md §2-3). 여기서는 순서마다 맞는 꼴을 쓴다.

import math

_AXIS = {"X": 0, "Y": 1, "Z": 2}
_DEG = math.pi / 180.0


def alternate(v, order):
    """같은 방향을 주는 다른 해 (도). v 는 (x, y, z) 축 슬롯 순서."""
    f, m, l = _AXIS[order[0]], _AXIS[order[1]], _AXIS[order[2]]
    out = [v[0], v[1], v[2]]
    out[f] += 180.0
    out[m] = 180.0 - out[m]
    out[l] += 180.0
    return out


def _near(value, ref):
    """value 에 360 의 배수를 더해 ref 에 가장 가깝게."""
    return value + 360.0 * round((ref - value) / 360.0)


def closest(v, prev, order):
    """v 와 같은 방향인 해 중 prev 에 가장 가까운 것 (두 해 x 2π 배수)."""
    best, best_d = None, None
    for cand in (v, alternate(v, order)):
        c = [_near(cand[0], prev[0]), _near(cand[1], prev[1]), _near(cand[2], prev[2])]
        d = abs(c[0] - prev[0]) + abs(c[1] - prev[1]) + abs(c[2] - prev[2])
        if best_d is None or d < best_d:
            best, best_d = c, d
    return best


def unwrap_triples(xs, ys, zs, order):
    """세 축이 같은 키 시간일 때. 반환 (xs, ys, zs) 새 리스트 - 행렬은 그대로, 연속 키 차이는 최소."""
    n = len(xs)
    if n == 0:
        return [], [], []
    ox, oy, oz = [xs[0]], [ys[0]], [zs[0]]
    prev = [xs[0], ys[0], zs[0]]
    f, m, l = _AXIS[order[0]], _AXIS[order[1]], _AXIS[order[2]]
    for i in range(1, n):
        a = [xs[i], ys[i], zs[i]]
        b = [a[0], a[1], a[2]]
        b[f] += 180.0
        b[m] = 180.0 - b[m]
        b[l] += 180.0
        p0, p1, p2 = prev
        a0 = a[0] + 360.0 * round((p0 - a[0]) / 360.0)
        a1 = a[1] + 360.0 * round((p1 - a[1]) / 360.0)
        a2 = a[2] + 360.0 * round((p2 - a[2]) / 360.0)
        b0 = b[0] + 360.0 * round((p0 - b[0]) / 360.0)
        b1 = b[1] + 360.0 * round((p1 - b[1]) / 360.0)
        b2 = b[2] + 360.0 * round((p2 - b[2]) / 360.0)
        if abs(b0 - p0) + abs(b1 - p1) + abs(b2 - p2) < abs(a0 - p0) + abs(a1 - p1) + abs(a2 - p2):
            prev = [b0, b1, b2]
        else:
            prev = [a0, a1, a2]
        ox.append(prev[0]); oy.append(prev[1]); oz.append(prev[2])
    return ox, oy, oz


def unwrap_single(values):
    """한 축만 키일 때 - 2π 배수만 맞춘다(동치 해는 세 축을 함께 바꾸므로 쓸 수 없다)."""
    if not values:
        return []
    out = [values[0]]
    prev = values[0]
    for v in values[1:]:
        prev = v + 360.0 * round((prev - v) / 360.0)
        out.append(prev)
    return out


def count_jumps(values, limit=180.0):
    """연속 키 차이가 limit 를 넘는 곳의 수."""
    return sum(1 for a, b in zip(values, values[1:]) if abs(b - a) > limit)


# ================================================================
# 행렬 (3x3, 리스트의 리스트)
# ================================================================

def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


_MAKERS = {"X": _rx, "Y": _ry, "Z": _rz}


def mat_mul(a, b):
    return [[a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j] for j in range(3)] for i in range(3)]


def transpose(a):
    return [[a[0][0], a[1][0], a[2][0]], [a[0][1], a[1][1], a[2][1]], [a[0][2], a[1][2], a[2][2]]]


def matrix(v, order="XYZ"):
    """오일러(도) -> 회전 행렬 (열 벡터 규약, 앞 글자가 먼저)."""
    axes = {"X": v[0], "Y": v[1], "Z": v[2]}
    m0 = _MAKERS[order[0]](axes[order[0]] * _DEG)
    m1 = _MAKERS[order[1]](axes[order[1]] * _DEG)
    m2 = _MAKERS[order[2]](axes[order[2]] * _DEG)
    return mat_mul(m2, mat_mul(m1, m0))


def decompose_xyz(m):
    """회전 행렬 -> XYZ 오일러(도), 한 해. m = Rz · Ry · Rx.

    y 는 asin 이 아니라 atan2(-m20, cy) - y ≈ ±90 근처에서도 정확하다(asin + 근사 분기는 0.05° 까지 틀렸다, 2026-10-27).
    """
    cy = math.sqrt(m[0][0] * m[0][0] + m[1][0] * m[1][0])
    y = math.atan2(-m[2][0], cy)
    if cy > 1e-12:
        x = math.atan2(m[2][1], m[2][2])
        z = math.atan2(m[1][0], m[0][0])
    else:  # 정확히 짐벌일 때만 - z 를 0 으로 두고 x 에 몰아준다
        z = 0.0
        x = math.atan2(-m[1][2], m[1][1])
    return [x / _DEG, y / _DEG, z / _DEG]


def angle_between(a, b):
    """두 회전 행렬 사이 각도(도). ||A-B||_F = 2√2 · sin(θ/2) 로 구한다 - acos(trace) 는 작은 각에서 1e-6° 쯤 뭉개진다."""
    s = 0.0
    for i in range(3):
        for k in range(3):
            d = a[i][k] - b[i][k]
            s += d * d
    h = math.sqrt(s) / (2.0 * math.sqrt(2.0))
    h = 1.0 if h > 1.0 else h
    return math.degrees(2.0 * math.asin(h))


# ================================================================
# 정규화 - (jointOrient · rotateOrder · rotateAxis) -> XYZ 회전만 (A00480 Normalize joints)
# ================================================================

def _quat(v, order):
    """오일러(도) -> 쿼터니언 (w, x, y, z), 열 벡터 규약 q = q_last · q_mid · q_first."""
    h = 0.5 * _DEG
    q = (1.0, 0.0, 0.0, 0.0)
    for axis in order:                       # 먼저 적용되는 축부터 왼쪽에 곱해 나간다
        a = v[_AXIS[axis]] * h
        c, s = math.cos(a), math.sin(a)
        e = (c, s, 0.0, 0.0) if axis == "X" else ((c, 0.0, s, 0.0) if axis == "Y" else (c, 0.0, 0.0, s))
        q = _qmul(e, q)
    return q


def _qmul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def normalize_xyz(xs, ys, zs, order, jo=(0.0, 0.0, 0.0), ra=(0.0, 0.0, 0.0), start=None):
    """키마다 로컬 회전 JO · R(order) · RA (열 벡터) 를 XYZ 오일러로 다시 쓴다. 연속 해(순서 XYZ 의 동치 + 2π).

    jo · ra 는 XYZ 순서(마야 jointOrient · rotateAxis 와 같다). start 를 주면 첫 키를 그 값에 가깝게 고른다.
    반환 (xs, ys, zs) 새 리스트.
    """
    q_jo = _quat(jo, "XYZ")
    q_ra = _quat(ra, "XYZ")
    makers = (_AXIS[order[0]], _AXIS[order[1]], _AXIS[order[2]])
    h = 0.5 * _DEG
    atan2, cos, sin, sqrt = math.atan2, math.cos, math.sin, math.sqrt
    to_deg = 1.0 / _DEG
    ox, oy, oz = [], [], []
    prev = list(start) if start is not None else None
    for i in range(len(xs)):
        v = (xs[i], ys[i], zs[i])
        # q_r = q_last · q_mid · q_first
        q = (1.0, 0.0, 0.0, 0.0)
        for idx in makers:
            a = v[idx] * h
            c, s = cos(a), sin(a)
            if idx == 0:
                e = (c, s, 0.0, 0.0)
            elif idx == 1:
                e = (c, 0.0, s, 0.0)
            else:
                e = (c, 0.0, 0.0, s)
            q = _qmul(e, q)
        w, x, y, z = _qmul(_qmul(q_jo, q), q_ra)
        # 쿼터니언 -> 행렬 원소 -> XYZ 오일러 (decompose_xyz 와 같은 식)
        m00 = 1.0 - 2.0 * (y * y + z * z)
        m10 = 2.0 * (x * y + w * z)
        cy = sqrt(m00 * m00 + m10 * m10)
        ay = atan2(-2.0 * (x * z - w * y), cy)
        if cy > 1e-12:
            ax = atan2(2.0 * (y * z + w * x), 1.0 - 2.0 * (x * x + y * y))
            az = atan2(m10, m00)
        else:  # 정확히 짐벌일 때만 - z 를 0 으로 두고 x 에 몰아준다
            az = 0.0
            ax = atan2(-2.0 * (y * z - w * x), 1.0 - 2.0 * (x * x + z * z))
        a0, a1, a2 = ax * to_deg, ay * to_deg, az * to_deg
        if prev is None:
            prev = [a0, a1, a2]
        else:
            p0, p1, p2 = prev
            b0, b1, b2 = a0 + 180.0, 180.0 - a1, a2 + 180.0
            a0 += 360.0 * round((p0 - a0) / 360.0)
            a1 += 360.0 * round((p1 - a1) / 360.0)
            a2 += 360.0 * round((p2 - a2) / 360.0)
            b0 += 360.0 * round((p0 - b0) / 360.0)
            b1 += 360.0 * round((p1 - b1) / 360.0)
            b2 += 360.0 * round((p2 - b2) / 360.0)
            if abs(b0 - p0) + abs(b1 - p1) + abs(b2 - p2) < abs(a0 - p0) + abs(a1 - p1) + abs(a2 - p2):
                prev = [b0, b1, b2]
            else:
                prev = [a0, a1, a2]
        ox.append(prev[0]); oy.append(prev[1]); oz.append(prev[2])
    return ox, oy, oz


def same_angles(a, b, tol=1e-4):
    """세 각이 360 배수 차이까지 같으면 True (행렬 계산 없이 빠르게 거른다)."""
    for i in range(3):
        d = (a[i] - b[i]) % 360.0
        if min(d, 360.0 - d) > tol:
            return False
    return True
