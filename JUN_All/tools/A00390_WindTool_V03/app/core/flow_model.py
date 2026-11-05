# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00390_WindTool_V03 core - Flow 모드의 **순수 파이썬 기준 모델** (UI · Maya 비의존)
#
# 블렌더 애드온 Waves Gen(Guillaume Bissieres, GPL-3.0-or-later)의 바람 움직임을 **같은 수식으로** 다시 쓴 것이다.
# 코드를 복사하지 않고 움직임의 수학(계획서 docs/plans/A00390_WindTool_wavesgen_port_plan.md 1-3)을 옮겼다.
# 이 툴은 개인 작업용(배포 안 함 - 사용자 확인 2026-11-05).
#
# 쓰임
#   1) 마야 노드망(flow_manager)이 맞는지 숫자로 대조하는 기준
#   2) 블렌더에서 뽑은 기준 데이터(골든)와 대조해 모델 자체가 맞는지 확인
#
# 좌표 약속 (블렌더 뼈와 같다): 뼈의 로컬 Y = 진행 방향, 바람 회전은 로컬 X(=p1) · Z(=p2) 두 축, 오일러 XYZ(X 먼저).
# 행렬은 열벡터 규약(M @ v), 3x3 은 list[3][3].

import math

TWO_PI = 2.0 * math.pi

# ---------------------------------------------------------------- 파형 상수
# 축 방향 파 a / 옆 파 b 의 시간 계수(위상 Φ = 시간 × 속도, 24 fps 프레임 단위)와 공간 · 위상 상수.
# (값은 Waves Gen 과 같다 - 같은 움직임을 내기 위한 상수)
A_MAIN = 0.13
A_WANDER, A_WANDER_GAIN, A_WANDER_STEP = 0.031, 1.6, 0.15
A_RIPPLE, A_RIPPLE_GAIN, A_RIPPLE_SPACE, A_RIPPLE_PHASE, A_RIPPLE_STEP = 0.29, 0.4, 1.7, 1.7, 0.1
B_MAIN, B_SPACE, B_PHASE = 0.11, 0.8, 1.9
B_WANDER, B_WANDER_GAIN, B_WANDER_PHASE, B_WANDER_STEP = 0.027, 1.3, 2.0, 0.12
B_RIPPLE, B_RIPPLE_GAIN, B_RIPPLE_SPACE, B_RIPPLE_PHASE, B_RIPPLE_STEP = 0.23, 0.4, 1.3, 4.1, 0.1

LEAN_BASE, LEAN_GROW = 0.3, 0.7     # 기울기 = Lean * (0.3 + 0.7u)
FOLLOW_GAIN = 0.7                   # 보정 1 / (1 - 0.7 q)
FOLLOW_TIP_DROP = 0.45              # 끝 따라가기 영향력: 뿌리 k=1 -> 끝 k=0.55
FOLLOW_CAP = 0.999
REF_BONES = 12.0                    # 뼈 개수 정규화 기준 (k0 = 12 / n)

# 가닥(체인)마다 리듬 차이 - 황금각 간격의 사인으로 고르게 흩는다(i >= 1, 0 번 체인은 기준).
VARY_STEP = 2.399
VARY_SPEED = (0.5, 0.4)             # (위상, 크기)
VARY_LENGTH = (2.1, 0.35)
VARY_FLUTTER = (3.7, 0.25)


def k0_of(n):
    return REF_BONES / float(n)


def u_of(i, n):
    return i / float(max(1, n - 1))


def vary_factors(chain_index, variation):
    """(속도, 파장, 진폭) 배수. 0 번 체인 · variation 0 이면 전부 1."""
    if chain_index <= 0:
        return 1.0, 1.0, 1.0
    out = []
    for phase, size in (VARY_SPEED, VARY_LENGTH, VARY_FLUTTER):
        out.append(1.0 + math.sin(chain_index * VARY_STEP + phase) * size * variation)
    return tuple(out)


def waves(phi, i, n, wavelength, random):
    """뼈 i 의 두 파 (a, b). phi = (시간 + 지연) × 속도 (24 fps 프레임 단위)."""
    s = i * k0_of(n)
    a = (math.sin(phi * A_MAIN - TWO_PI * s / wavelength
                  + random * A_WANDER_GAIN * math.sin(phi * A_WANDER + A_WANDER_STEP * s))
         + random * A_RIPPLE_GAIN * math.sin(phi * A_RIPPLE - TWO_PI * s * A_RIPPLE_SPACE / wavelength
                                             + A_RIPPLE_PHASE + A_RIPPLE_STEP * s))
    b = (math.sin(phi * B_MAIN - TWO_PI * s / wavelength * B_SPACE + B_PHASE
                  + random * B_WANDER_GAIN * math.sin(phi * B_WANDER + B_WANDER_PHASE + B_WANDER_STEP * s))
         + random * B_RIPPLE_GAIN * math.sin(phi * B_RIPPLE - TWO_PI * s * B_RIPPLE_SPACE / wavelength
                                             + B_RIPPLE_PHASE + B_RIPPLE_STEP * s))
    return a, b


def bone_angles(p, phi, i, n, follow_on=True):
    """뼈 i 의 로컬 회전 (rx, rz) 도. p = 파라미터 dict(아래 PARAMS 이름).

    lean · flutter 는 '뼈 12개 기준' 도 - 뼈가 많으면 k0 로 나눠 같은 모양."""
    u = u_of(i, n)
    a, b = waves(phi, i, n, p["wavelength"], p["random"])
    env = u ** p["stiffness"] if not (u == 0.0 and p["stiffness"] == 0.0) else 1.0
    gain = k0_of(n) * p.get("envelope", 1.0)
    if follow_on:
        gain /= (1.0 - FOLLOW_GAIN * p["follow"])
    along = (p["lean"] * (LEAN_BASE + LEAN_GROW * u) + p["flutter"] * env * a) * gain
    across = (p["cross"] * p["flutter"] * env * b) * gain
    d = math.radians(p["direction"])
    rx = along * math.cos(d) + across * math.sin(d)
    rz = along * math.sin(d) - across * math.cos(d)
    return rx, rz


def follow_weight(q, i, n):
    """끝 따라가기 영향력(뼈 i)."""
    k = 1.0 - FOLLOW_TIP_DROP * (i / float(max(1, n - 1)))
    return 1.0 - (1.0 - min(FOLLOW_CAP, q * k)) ** (REF_BONES / n)


# ---------------------------------------------------------------- 3D 도우미 (열벡터)

def mat_mul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)] for r in range(3)]


def mat_vec(m, v):
    return [sum(m[r][k] * v[k] for k in range(3)) for r in range(3)]


def transpose(m):
    return [[m[c][r] for c in range(3)] for r in range(3)]


def axis_angle(axis, ang):
    x, y, z = axis
    c, s = math.cos(ang), math.sin(ang)
    t = 1.0 - c
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def euler_xz(rx_deg, rz_deg):
    """오일러 XYZ (Y=0) = Rz @ Rx."""
    return mat_mul(axis_angle((0, 0, 1), math.radians(rz_deg)), axis_angle((1, 0, 0), math.radians(rx_deg)))


def norm(v):
    l = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / l for x in v]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def rotation_between(v1, v2):
    """v1 -> v2 최소 회전(3x3)."""
    v1, v2 = norm(v1), norm(v2)
    c = max(-1.0, min(1.0, dot(v1, v2)))
    ax = cross(v1, v2)
    s = math.sqrt(dot(ax, ax))
    if s < 1e-12:
        return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    return axis_angle([x / s for x in ax], math.atan2(s, c))


def mat_to_quat(m):
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return [0.25 * s, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s]
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        return [(m[2][1] - m[1][2]) / s, 0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s]
    if m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        return [(m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s]
    s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
    return [(m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s]


def quat_to_mat(q):
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def slerp(q1, q2, t):
    d = dot(q1, q2)
    if d < 0:
        q2, d = [-x for x in q2], -d
    if d > 0.9995:
        r = [a + (b - a) * t for a, b in zip(q1, q2)]
    else:
        th = math.acos(d)
        s1, s2 = math.sin((1 - t) * th) / math.sin(th), math.sin(t * th) / math.sin(th)
        r = [a * s1 + b * s2 for a, b in zip(q1, q2)]
    l = math.sqrt(dot(r, r))
    return [x / l for x in r]


# ---------------------------------------------------------------- 체인 평가

def evaluate_chain(base_rot, base_pos, rest, p, phi, tip, follow_on=True):
    """체인 하나를 평가해 뼈마다 (월드 회전 3x3, 월드 머리 위치)를 돌려준다.

    base_rot, base_pos : 첫 뼈의 부모 공간(월드)
    rest : 뼈마다 (부모 기준 rest 회전 3x3, 부모 기준 머리 위치) - 뼈 축 약속은 위(Y 진행, X/Z 바람)
    tip  : 끝 따라가기 목표(월드). follow_on 이 False 면 쓰지 않는다.
    """
    n = len(rest)
    out = []
    pr, pp = base_rot, base_pos
    for i, (r_rot, r_pos) in enumerate(rest):
        rx, rz = bone_angles(p, phi, i, n, follow_on)
        head = [pp[k] + mat_vec(pr, r_pos)[k] for k in range(3)]
        rot = mat_mul(mat_mul(pr, r_rot), euler_xz(rx, rz))
        if follow_on:
            y_axis = [rot[0][1], rot[1][1], rot[2][1]]
            target = [tip[k] - head[k] for k in range(3)]
            tracked = mat_mul(rotation_between(y_axis, target), rot)
            w = follow_weight(p["follow"], i, n)
            rot = quat_to_mat(slerp(mat_to_quat(rot), mat_to_quat(tracked), w))
        out.append((rot, head))
        pr, pp = rot, head
    return out


PARAMS = ("lean", "direction", "flutter", "cross", "speed", "wavelength", "stiffness", "random", "follow")
