# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-29
# A00410_SecondaryMotion core - 체인 관성(2차 모션) 솔버.
#
# **DCC 비의존 순수 파이썬**. maya 를 import 하지 않으므로 헤드리스로 단독 테스트할 수 있다.
#
# 모델
# ----
# 언리얼 KawaiiPhysics 와 같은 계열의 **위치기반 질량-스프링 근사**다. 물리 엔진이 아니라
# "원래 있어야 할 자리(강체 FK 위치)로 당기는 스프링 + 속도 감쇠 + 길이 구속" 이다.
#
#   v      = (p - p_prev) * (1 - damping)            # 베를레 속도 + 감쇠
#   p_new  = p + v + (target - p) * stiffness_i      # 원래 자리로 당김
#            + gravity
#   p_new  = lerp(p_new, target, world_damping)      # 월드 감쇠
#   p_new  = parent_new + dir(p_new - parent_new) * len_i     # 길이 구속
#   p_new  = clamp_angle(p_new, rest_dir, limit_angle)        # 각도 제한
#
# "부모에서 먼 자식일수록 원래 자리에 남으려 한다" 는 성질은 **stiffness 폴오프**로 만든다.
# 루트 쪽(i 작음)은 stiffness 가 커서 부모를 잘 따라가고, 팁 쪽(i 큼)은 작아서 뒤처진다.
#
#   stiffness_i = stiffness * (1 - falloff * i/(n-1))
#
# 길이 구속이 매 프레임 성립하므로 |p[i+1]-p[i]| == len_i 가 보장되고, 그 덕분에
# 회전 재구성(pose_builder)이 점 시뮬과 정확히 일치한다(체인이 벌어지지 않는다).

import math


# 파라미터 기본값(=UI 초기값)의 기준 프레임레이트. 다른 fps 에서도 비슷한 감쇠가 되도록
# stiffness/damping 을 이 값 기준으로 보정한다.
REF_FPS = 24.0

# 방향이 사실상 0 인지 판정하는 하한.
_EPS = 1e-9


class SolverParams(object):
    """솔버 파라미터 묶음. UI 값 그대로 담는다."""

    def __init__(self, stiffness=0.35, damping=0.12, world_damping=0.0,
                 falloff=0.5, gravity=(0.0, 0.0, 0.0), limit_angle=45.0,
                 blend=1.0, substeps=1, fps=REF_FPS):
        self.stiffness = float(stiffness)        # 0~1, 원래 자리로 당기는 힘
        self.damping = float(damping)            # 0~1, 속도 감쇠
        self.world_damping = float(world_damping)  # 0~1, 결과를 원본 쪽으로 끌어당김
        self.falloff = float(falloff)            # 0~1, root→tip stiffness 감소량
        self.gravity = tuple(float(v) for v in gravity)   # 월드 유닛 / 프레임^2
        self.limit_angle = float(limit_angle)    # deg, 원본 방향에서의 최대 이탈각(<=0 이면 무제한)
        self.blend = float(blend)                # 0~1, 결과 강도(0 = 원본과 동일)
        self.substeps = max(1, int(substeps))    # 프레임당 서브스텝
        self.fps = float(fps) or REF_FPS

    def copy(self):
        return SolverParams(self.stiffness, self.damping, self.world_damping,
                            self.falloff, self.gravity, self.limit_angle,
                            self.blend, self.substeps, self.fps)

    def as_dict(self):
        return dict(stiffness=self.stiffness, damping=self.damping,
                    world_damping=self.world_damping, falloff=self.falloff,
                    gravity=self.gravity, limit_angle=self.limit_angle,
                    blend=self.blend, substeps=self.substeps, fps=self.fps)


# --------------------------------------------------------------------- 벡터 헬퍼
# (튜플/리스트 3원소. maya 비의존을 위해 직접 구현 — 호출량이 많아 함수 호출을
#  줄이려고 대부분 솔버 루프 안에 인라인되어 있고, 여기 것은 보조용이다.)

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _length(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def _normalize(a):
    L = _length(a)
    if L < _EPS:
        return (0.0, 0.0, 0.0), 0.0
    return (a[0] / L, a[1] / L, a[2] / L), L


def _lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def _rotate_axis(v, axis, angle):
    """로드리게스 회전 — v 를 단위벡터 axis 둘레로 angle(rad) 만큼 돌린다."""
    c = math.cos(angle)
    s = math.sin(angle)
    d = _dot(axis, v)
    cr = _cross(axis, v)
    return (v[0] * c + cr[0] * s + axis[0] * d * (1.0 - c),
            v[1] * c + cr[1] * s + axis[1] * d * (1.0 - c),
            v[2] * c + cr[2] * s + axis[2] * d * (1.0 - c))


def _clamp_direction(cur_dir, rest_dir, max_angle):
    """cur_dir 이 rest_dir 에서 max_angle(rad) 이상 벗어나면 그 경계로 끌어온다."""
    d = _dot(cur_dir, rest_dir)
    d = 1.0 if d > 1.0 else (-1.0 if d < -1.0 else d)
    ang = math.acos(d)
    if ang <= max_angle:
        return cur_dir
    axis, L = _normalize(_cross(rest_dir, cur_dir))
    if L < _EPS:
        # 정확히 반대 방향 — 임의 수직축을 잡는다.
        tmp = (1.0, 0.0, 0.0) if abs(rest_dir[0]) < 0.9 else (0.0, 1.0, 0.0)
        axis, _ = _normalize(_cross(rest_dir, tmp))
    return _rotate_axis(rest_dir, axis, max_angle)


# --------------------------------------------------------------------- 스텝 보정

def _fps_adjust(value, fps):
    """프레임레이트 보정.

    stiffness/damping 은 "프레임당 비율" 이라 fps 가 다르면 체감이 달라진다.
    24fps 기준값을 유지하도록 1-(1-x)^step 으로 환산한다(step = REF_FPS/fps).
    """
    if fps <= 0 or abs(fps - REF_FPS) < 1e-6:
        return value
    v = 0.0 if value < 0.0 else (1.0 if value > 1.0 else value)
    return 1.0 - math.pow(1.0 - v, REF_FPS / fps)


# --------------------------------------------------------------------- 솔버 본체

def solve(targets, params):
    """강체 FK 위치열 -> 관성이 적용된 위치열.

    targets : [frame][i] = (x, y, z)  각 프레임의 **원본(강체 FK)** 월드 위치.
              i=0 이 체인 루트이며 루트는 100% 드라이버를 따른다(수정하지 않는다).
    params  : SolverParams

    반환    : [frame][i] = (x, y, z)  시뮬레이션된 월드 위치.
              길이 구속에 의해 |p[i]-p[i-1]| == |t[i]-t[i-1]| 이 항상 성립한다.

    프레임 사이의 뼈 길이는 **그 프레임의 원본 길이**를 쓴다. 체인 자체에 이동
    애니메이션이 있어도(늘었다 줄었다 해도) 그 변화를 그대로 따라간다.
    """
    if not targets:
        return []

    n = len(targets[0])
    if n < 2:
        # 조인트가 1개면 흔들 자식이 없다 — 원본 그대로.
        return [list(f) for f in targets]

    stiff = _fps_adjust(params.stiffness, params.fps)
    damp = _fps_adjust(params.damping, params.fps)
    wdamp = params.world_damping
    blend = params.blend
    grav = params.gravity
    substeps = params.substeps
    max_ang = math.radians(params.limit_angle) if params.limit_angle > 0 else None

    # 조인트별 stiffness — 루트에서 멀수록 작아진다(= 더 뒤처진다).
    denom = float(n - 1) if n > 1 else 1.0
    stiff_i = []
    for i in range(n):
        k = stiff * (1.0 - params.falloff * (i / denom))
        stiff_i.append(max(0.0, min(1.0, k)))

    # 서브스텝을 쓰면 프레임당 힘을 나눠 적용한다.
    sub_g = _scale(grav, 1.0 / (substeps * substeps))

    # 초기 상태: 원본 포즈에 정지(속도 0) — 결정적이라 항상 같은 결과가 나온다.
    p = list(targets[0])
    p_prev = list(targets[0])

    out = [list(targets[0])]

    for f in range(1, len(targets)):
        t_cur = targets[f]
        t_pre = targets[f - 1]

        for s in range(1, substeps + 1):
            # 서브스텝에서는 이전~현재 프레임 목표를 선형 보간해서 쓴다.
            if substeps == 1:
                tgt = t_cur
            else:
                u = float(s) / substeps
                tgt = [_lerp3(t_pre[i], t_cur[i], u) for i in range(n)]

            new = [tgt[0]]                     # 루트는 항상 드라이버를 그대로 따른다
            for i in range(1, n):
                px, py, pz = p[i]
                qx, qy, qz = p_prev[i]
                tx, ty, tz = tgt[i]

                # 베를레 속도 + 감쇠
                vx = (px - qx) * (1.0 - damp)
                vy = (py - qy) * (1.0 - damp)
                vz = (pz - qz) * (1.0 - damp)

                # 원래 자리로 당기는 스프링 + 중력
                k = stiff_i[i]
                nx = px + vx + (tx - px) * k + sub_g[0]
                ny = py + vy + (ty - py) * k + sub_g[1]
                nz = pz + vz + (tz - pz) * k + sub_g[2]

                # 월드 감쇠 — 결과를 원본 쪽으로 일정 비율 끌어당긴다
                if wdamp > 0.0:
                    nx += (tx - nx) * wdamp
                    ny += (ty - ny) * wdamp
                    nz += (tz - nz) * wdamp

                # 결과 강도(blend). 0 이면 원본과 완전히 동일해진다.
                if blend < 1.0:
                    nx = tx + (nx - tx) * blend
                    ny = ty + (ny - ty) * blend
                    nz = tz + (nz - tz) * blend

                # --- 길이 구속: 부모(이미 확정된 new[i-1])와의 거리를 원본 길이로 고정
                ax, ay, az = new[i - 1]
                bx, by, bz = tgt[i - 1]
                bone = math.sqrt((tx - bx) ** 2 + (ty - by) ** 2 + (tz - bz) ** 2)

                dx, dy, dz = nx - ax, ny - ay, nz - az
                dl = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dl < _EPS:
                    # 부모와 겹쳤다 — 원본 방향으로 되돌린다.
                    if bone < _EPS:
                        new.append((ax, ay, az))
                        continue
                    dx, dy, dz = (tx - bx) / bone, (ty - by) / bone, (tz - bz) / bone
                else:
                    dx, dy, dz = dx / dl, dy / dl, dz / dl

                # --- 각도 제한: 원본 방향에서 너무 벌어지지 않게
                if max_ang is not None and bone > _EPS:
                    rest = ((tx - bx) / bone, (ty - by) / bone, (tz - bz) / bone)
                    dx, dy, dz = _clamp_direction((dx, dy, dz), rest, max_ang)

                new.append((ax + dx * bone, ay + dy * bone, az + dz * bone))

            p_prev = p
            p = new

        out.append(list(p))

    return out


def response_delay(targets, sim, index=-1, fraction=0.5):
    """검증용 - index 번째 노드가 원본보다 몇 프레임 늦게 따라오는지.

    "부모에서 먼 조인트일수록 더 늦게 따라온다" 는 이 툴의 핵심 성질을 수치로 확인한다.
    원본이 **가장 크게 움직인 축**을 골라, 원본과 시뮬이 각각 **최종 변위의 fraction
    (기본 50%)** 에 처음 도달하는 프레임을 찾아 그 차이를 돌려준다.

    상호상관을 쓰지 않는 이유:
      - 주기 입력(사인)에서는 한 주기 감긴 지연이 최대가 되어 값이 모호해지고,
      - 계단 입력에서는 평탄부가 상관값을 지배해 늘 0 이 나온다.
    "언제 절반쯤 따라왔나" 는 두 경우 모두에서 뜻이 분명하다.

    주의 — **빠른(계단에 가까운) 입력에서만 뜻이 있다.** 드라이버가 천천히 움직이면
    체인이 사실상 따라잡아 지연이 0 근처로 나오고(그게 올바른 물리다), 감쇠가 약하면
    오버슛 때문에 -1 같은 값이 나올 수도 있다. 체인 전체의 관성 정도를 보려면
    이 값보다 **각 노드의 원본 대비 편차**(팁으로 갈수록 커진다)가 더 안정적인 지표다.
    """
    nf = len(targets)
    if nf < 3:
        return 0
    n = len(targets[0])
    i = index if index >= 0 else n + index

    base_t = targets[0][i]
    cols = [[targets[f][i][k] - base_t[k] for f in range(nf)] for k in range(3)]
    axis = max(range(3), key=lambda c: sum(v * v for v in cols[c]))

    a = cols[axis]
    base_s = sim[0][i][axis]
    b = [sim[f][i][axis] - base_s for f in range(nf)]

    def _cross(seq):
        total = seq[-1]
        if abs(total) < _EPS:
            return 0
        thr = total * fraction
        for f, v in enumerate(seq):
            if (total > 0 and v >= thr) or (total < 0 and v <= thr):
                return f
        return nf - 1

    return _cross(b) - _cross(a)
