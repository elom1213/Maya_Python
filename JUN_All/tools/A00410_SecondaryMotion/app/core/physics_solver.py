# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-10
# A00410_SecondaryMotion core - Physics Asset 솔버 (언리얼 Physics Asset 의 시뮬레이트 바디 흉내).
#
# **DCC 비의존 순수 파이썬** — chain_solver 와 같은 성질(maya 를 import 하지 않는다).
# 계획서: JUN_All/docs/plans/A00410_PhysicsAsset_plan.md
#
# KawaiiPhysics(chain_solver) 와 다른 점
# -----------------------------------
#   chain_solver : 각 점을 **애니메이션 위치로 당기는 스프링**이 있고, 회전 재구성은
#                  **애니메이션 회전 위에** 스윙을 얹는다 -> 원래 회전값이 결과의 바탕.
#   이 솔버      : 애니메이션이 들어오는 곳은 **체인 루트의 위치**와 **루트 노드의 DAG 부모
#                  회전**(키네마틱) 둘뿐이다. 나머지 노드는 중력 · 관성 · 감쇠 · 조인트 한계로만
#                  움직인다 -> 자식 노드의 회전 키는 결과에 아무 영향이 없다.
#
# 규약
# ----
# 쿼터니언은 (x, y, z, w) 튜플. `qm(a, b)` 는 **마야 MQuaternion 의 a * b** 와 같다
# (행벡터 규약: a 를 먼저, 그다음 b). 벡터 회전 `rot(v, q)` 는 마야 `MVector.rotateBy(q)` 와 같다.
#   world = local * parentWorld          (qm(local, parentWorld))
#
# 체인 입력 (PhysicsChainInput)
# ----------------------------
#   점 j = 0..m-1 (가상 팁 포함), 회전하는 노드 i = 0..m-2 (노드 i 는 점 i -> 점 i+1 뼈를 가진다)
#   root_pos[f]       점 0 의 월드 위치(애니메이션)
#   root_parent_q[f]  노드 0 의 DAG 부모 월드 회전(애니메이션)
#   ref_rel[i]        기준 포즈에서 노드 i 의 회전을 "체인 부모"(i=0 은 DAG 부모, i>=1 은 노드 i-1)
#                     기준으로 본 것. 사이에 낀 오프셋 그룹의 회전이 들어 있다.
#   bone_local[i]     기준 포즈 뼈 벡터(점 i -> i+1)를 노드 i 의 기준 월드 회전 공간으로 옮긴 것
#   init_points       시작 프레임 점 위치(애니메이션) — `From animation` 시작 상태
#
# 서브스텝 하나 (dt = 1 / (fps * substeps))
# ----------------------------------------
#   점 적분: v = (p - p_prev)/dt, 선형 감쇠 v /= (1 + dt*linear_damping), p += v*dt + g*dt^2
#   각 감쇠: 부모 점에 대한 상대 속도 중 뼈에 수직인 성분에 /(1 + dt*angular_damping)
#   구속 (루트 -> 팁):
#       R_ref = ref_rel[i] * W_parent           # 기준대로 붙었을 때의 노드 회전
#       d_ref = rot(bone_local[i], R_ref)
#       d_sim = 한계(Swing1/Swing2 타원 콘) 안으로 자른 방향
#       p[i+1] = p[i] + d_sim * |bone_local[i]|   # 기준 길이(강체)
#       W[i] = R_ref * swing(d_ref -> d_sim)      # 최소 스윙 -> 트위스트는 부모를 따른다(1단계)

import math


_EPS = 1e-12

# 조인트 한계 모드 (UE 컨스트레인트 Swing/Twist Motion 과 같은 어휘)
LIMIT_FREE = "free"
LIMIT_LIMITED = "limited"
LIMIT_LOCKED = "locked"
LIMIT_MODES = (LIMIT_FREE, LIMIT_LIMITED, LIMIT_LOCKED)

# 시작 상태
START_ANIMATION = "animation"     # 시작 프레임 애니메이션 포즈에서 정지 출발(떨어진다)
START_SETTLED = "settled"         # 시작 프레임 루트를 고정하고 미리 풀어 매달린 채로 출발
START_MODES = (START_ANIMATION, START_SETTLED)

# 충돌
COLLISION_NONE = "none"
COLLISION_GROUND = "ground"
COLLISION_MODES = (COLLISION_NONE, COLLISION_GROUND)

# Settled 시작 상태를 만들 때 쓰는 최소 감쇠(1/s).
SETTLE_LINEAR_DAMPING = 4.0
SETTLE_ANGULAR_DAMPING = 8.0

# 루프 프리롤 (chain_solver 와 같은 값)
LOOP_MAX_CYCLES = 16
LOOP_TOL_RATIO = 1e-6
LOOP_INPUT_TOL_RATIO = 1e-3


class PhysicsParams(object):
    """Physics Asset 솔버 파라미터. UI 값 그대로(단위는 씬 리니어 단위 / 초)."""

    def __init__(self, gravity=(0.0, -980.0, 0.0), linear_damping=0.5,
                 angular_damping=1.0,
                 swing1_mode=LIMIT_LIMITED, swing1=45.0,
                 swing2_mode=LIMIT_LIMITED, swing2=45.0,
                 start=START_ANIMATION, settle_seconds=3.0,
                 substeps=4, iterations=1,
                 collision=COLLISION_NONE, ground_height=0.0, up_axis=1,
                 blend=1.0, fps=24.0, loop=False, kinematic_root=True,
                 reference=None):
        # True 면 체인 첫 노드는 애니메이션 회전 그대로(키네마틱), 시뮬레이션은 그 아래부터.
        self.kinematic_root = bool(kinematic_root)
        # 기준 포즈 프레임(None = 구간 시작 프레임). 세션이 가장 가까운 샘플 프레임을 고른다.
        self.reference = reference
        self.gravity = tuple(float(v) for v in gravity)
        self.linear_damping = max(0.0, float(linear_damping))
        self.angular_damping = max(0.0, float(angular_damping))
        self.swing1_mode = swing1_mode
        self.swing1 = float(swing1)
        self.swing2_mode = swing2_mode
        self.swing2 = float(swing2)
        self.start = start
        self.settle_seconds = max(0.0, float(settle_seconds))
        self.substeps = max(1, int(substeps))
        self.iterations = max(1, int(iterations))
        self.collision = collision
        self.ground_height = float(ground_height)
        self.up_axis = 2 if int(up_axis) == 2 else 1
        self.blend = max(0.0, min(1.0, float(blend)))
        self.fps = float(fps) or 24.0
        self.loop = bool(loop)

    def copy(self):
        p = PhysicsParams()
        p.__dict__.update(self.__dict__)
        return p

    def as_dict(self):
        return dict(self.__dict__)


class PhysicsChainInput(object):
    """솔버 입력 묶음(위 머리글 참고). 전부 순수 튜플."""

    def __init__(self, root_pos, root_parent_q, ref_rel, bone_local, init_points,
                 root_node_q=None):
        self.root_pos = root_pos
        self.root_parent_q = root_parent_q
        # [f] 노드 0 의 애니메이션 월드 회전. 주면 노드 0 은 **키네마틱**(애니메이션 그대로)이고
        # 시뮬레이션은 노드 1 부터다(UE 에서 체인 첫 바디를 Kinematic 으로 둔 것). None = 노드 0 도 시뮬레이션.
        self.root_node_q = root_node_q
        self.ref_rel = ref_rel
        self.bone_local = bone_local
        self.init_points = init_points
        self.bone_len = [_length(b) for b in bone_local]
        self.bone_dir = [_normalize(b) for b in bone_local]
        # 노드마다 Twist 축 = 뼈 방향에 가장 가까운 노드 로컬 축, Swing1/Swing2 = 나머지
        # (UE: Twist X 이면 Swing1 = Z 둘레, Swing2 = Y 둘레). 뼈에 수직이 되도록 정규직교화.
        self.twist_axis = []
        self.swing_frames = []
        for d in self.bone_dir:
            k = max(range(3), key=lambda a: abs(d[a]))
            self.twist_axis.append(k)
            s1 = [0.0, 0.0, 0.0]
            s1[(k + 2) % 3] = 1.0
            s1 = _sub(s1, _scale(d, _dot(s1, d)))
            s1 = _normalize(s1)
            s2 = _cross(d, s1)
            self.swing_frames.append((s1, s2))

    def node_count(self):
        return len(self.bone_local)

    def frame_count(self):
        return len(self.root_pos)


# --------------------------------------------------------------------- 수학 헬퍼

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
        return (0.0, 0.0, 0.0)
    return (a[0] / L, a[1] / L, a[2] / L)


def _lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def _hamilton(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qm(a, b):
    """마야 MQuaternion 의 a * b (a 를 먼저 적용, 그다음 b)."""
    return _hamilton(b, a)


def qinv(q):
    """단위 쿼터니언의 역(켤레)."""
    return (-q[0], -q[1], -q[2], q[3])


def qnorm(q):
    L = math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
    if L < _EPS:
        return (0.0, 0.0, 0.0, 1.0)
    return (q[0] / L, q[1] / L, q[2] / L, q[3] / L)


def rot(v, q):
    """벡터 v 를 q 로 돌린다(마야 MVector.rotateBy 와 같다)."""
    qx, qy, qz, qw = q
    # t = 2 * cross(q.xyz, v); v' = v + w*t + cross(q.xyz, t)
    tx = 2.0 * (qy * v[2] - qz * v[1])
    ty = 2.0 * (qz * v[0] - qx * v[2])
    tz = 2.0 * (qx * v[1] - qy * v[0])
    return (v[0] + qw * tx + (qy * tz - qz * ty),
            v[1] + qw * ty + (qz * tx - qx * tz),
            v[2] + qw * tz + (qx * ty - qy * tx))


def qswing(a, b):
    """단위벡터 a 를 b 로 보내는 최소 회전(트위스트 없음)."""
    d = _dot(a, b)
    if d < -1.0 + 1e-9:
        # 정반대 — 아무 수직축으로 180도.
        tmp = (1.0, 0.0, 0.0) if abs(a[0]) < 0.9 else (0.0, 1.0, 0.0)
        ax = _normalize(_cross(a, tmp))
        return (ax[0], ax[1], ax[2], 0.0)
    c = _cross(a, b)
    return qnorm((c[0], c[1], c[2], 1.0 + d))


def qaxis_angle(axis, angle):
    s = math.sin(angle * 0.5)
    return (axis[0] * s, axis[1] * s, axis[2] * s, math.cos(angle * 0.5))


def qslerp(a, b, t):
    d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
    if d < 0.0:
        b = (-b[0], -b[1], -b[2], -b[3])
        d = -d
    if d > 0.9995:
        return qnorm(tuple(a[k] + (b[k] - a[k]) * t for k in range(4)))
    th = math.acos(d)
    s = math.sin(th)
    wa = math.sin((1.0 - t) * th) / s
    wb = math.sin(t * th) / s
    return tuple(a[k] * wa + b[k] * wb for k in range(4))


# --------------------------------------------------------------------- 조인트 한계

def _limit_halfangles(params):
    """(Swing1, Swing2) 반각(rad). Free = None, Locked = 0."""
    out = []
    for mode, deg in ((params.swing1_mode, params.swing1),
                      (params.swing2_mode, params.swing2)):
        if mode == LIMIT_FREE:
            out.append(None)
        elif mode == LIMIT_LOCKED:
            out.append(0.0)
        else:
            out.append(math.radians(max(0.0, deg)))
    return out


def clamp_swing(d_loc, b, s1, s2, lim1, lim2):
    """노드 기준 공간의 방향 d_loc 를 Swing1/Swing2 타원 콘 안으로 자른다.

    b = 기준 뼈 방향(단위), s1/s2 = 뼈에 수직인 Swing1/Swing2 축.
    스윙 회전벡터 w = angle * axis(b x d) 를 두 축 성분 (a1, a2) 로 나눠
    (a1/lim1)^2 + (a2/lim2)^2 <= 1 이 되게 반지름 방향으로 줄인다. 한계 0(Locked)은 그 성분 0.
    반환: (새 방향, 잘렸는가)
    """
    if lim1 is None and lim2 is None:
        return d_loc, False
    c = _cross(b, d_loc)
    sn = _length(c)
    cs = _dot(b, d_loc)
    ang = math.atan2(sn, cs)
    if ang < 1e-12:
        return d_loc, False
    if sn < 1e-12:
        # 정반대 — 축이 없다. s1 둘레로 본다.
        axis = s1
    else:
        axis = (c[0] / sn, c[1] / sn, c[2] / sn)
    a1 = ang * _dot(axis, s1)
    a2 = ang * _dot(axis, s2)

    clipped = False
    if lim1 is not None and lim1 <= 0.0 and a1 != 0.0:
        a1 = 0.0
        clipped = True
    if lim2 is not None and lim2 <= 0.0 and a2 != 0.0:
        a2 = 0.0
        clipped = True
    e = 0.0
    if lim1 is not None and lim1 > 0.0:
        e += (a1 / lim1) ** 2
    if lim2 is not None and lim2 > 0.0:
        e += (a2 / lim2) ** 2
    if e > 1.0:
        k = 1.0 / math.sqrt(e)
        # Free 축은 줄이지 않는다(그 축 성분은 타원 식에 들어가지 않았다).
        if lim1 is not None:
            a1 *= k
        if lim2 is not None:
            a2 *= k
        clipped = True
    if not clipped:
        return d_loc, False

    w = (s1[0] * a1 + s2[0] * a2, s1[1] * a1 + s2[1] * a2, s1[2] * a1 + s2[2] * a2)
    wl = _length(w)
    if wl < 1e-15:
        return b, True
    return rot(b, qaxis_angle(_scale(w, 1.0 / wl), wl)), True


# --------------------------------------------------------------------- 솔버 본체

class _State(object):
    def __init__(self, points):
        self.p = [tuple(v) for v in points]
        self.p_prev = [tuple(v) for v in points]
        self.W = []


def _constrain(state, chain, root_p, par_q, lims, node_q=None):
    """루트 -> 팁 한 번: 길이 구속 + 스윙 한계 + 노드 월드 회전 갱신.

    node_q 를 주면 노드 0 은 그 회전 그대로(키네마틱) — 점 1 은 애니메이션 뼈 방향에 놓인다.
    """
    p = state.p
    p[0] = root_p
    W = [None] * chain.node_count()
    W_parent = par_q
    lim1, lim2 = lims
    for i in range(chain.node_count()):
        if i == 0 and node_q is not None:
            d0 = rot(chain.bone_dir[0], node_q)
            L0 = chain.bone_len[0]
            p[1] = (p[0][0] + d0[0] * L0, p[0][1] + d0[1] * L0, p[0][2] + d0[2] * L0)
            W[0] = node_q
            W_parent = node_q
            continue
        R_ref = qm(chain.ref_rel[i], W_parent)
        b = chain.bone_dir[i]
        L = chain.bone_len[i]
        if L < _EPS:
            W[i] = R_ref
            p[i + 1] = p[i]
            W_parent = R_ref
            continue
        d_ref = rot(b, R_ref)
        d = _sub(p[i + 1], p[i])
        dl = _length(d)
        if dl < _EPS:
            d_sim = d_ref
        else:
            d_sim = (d[0] / dl, d[1] / dl, d[2] / dl)
        if lim1 is not None or lim2 is not None:
            R_inv = qinv(R_ref)
            d_loc = rot(d_sim, R_inv)
            s1, s2 = chain.swing_frames[i]
            d_loc, clipped = clamp_swing(d_loc, b, s1, s2, lim1, lim2)
            if clipped:
                d_sim = _normalize(rot(d_loc, R_ref))
        p[i + 1] = (p[i][0] + d_sim[0] * L, p[i][1] + d_sim[1] * L,
                    p[i][2] + d_sim[2] * L)
        W[i] = qm(R_ref, qswing(d_ref, d_sim))
        W_parent = W[i]
    state.W = W


def _ground(state, params):
    ax = params.up_axis
    h = params.ground_height
    p = state.p
    for j in range(1, len(p)):
        if p[j][ax] < h:
            v = list(p[j])
            v[ax] = h
            p[j] = tuple(v)
            # 바닥으로 파고드는 속도를 없앤다(이전 위치도 바닥 높이로).
            q = list(state.p_prev[j])
            if q[ax] < h:
                q[ax] = h
                state.p_prev[j] = tuple(q)


def _substep(state, chain, root_p, par_q, params, dt, lims, node_q=None):
    p = state.p
    pp = state.p_prev
    g = params.gravity
    lin = 1.0 / (1.0 + dt * params.linear_damping)
    ang = 1.0 / (1.0 + dt * params.angular_damping)
    dt2 = dt * dt

    m = len(p)
    vel = [None] * m
    # 루트 속도(키네마틱) — 각 감쇠의 기준.
    vel[0] = ((root_p[0] - p[0][0]) / dt, (root_p[1] - p[0][1]) / dt,
              (root_p[2] - p[0][2]) / dt)
    new = [root_p]
    for j in range(1, m):
        v = ((p[j][0] - pp[j][0]) / dt, (p[j][1] - pp[j][1]) / dt,
             (p[j][2] - pp[j][2]) / dt)
        v = (v[0] * lin, v[1] * lin, v[2] * lin)
        if ang < 1.0:
            # 부모 점 대비 상대 속도의 뼈 수직 성분 = 각속도. 그것만 줄인다.
            vp = vel[j - 1]
            rel = (v[0] - vp[0], v[1] - vp[1], v[2] - vp[2])
            bd = _normalize(_sub(p[j], p[j - 1]))
            along = _dot(rel, bd)
            perp = (rel[0] - bd[0] * along, rel[1] - bd[1] * along,
                    rel[2] - bd[2] * along)
            k = 1.0 - ang
            v = (v[0] - perp[0] * k, v[1] - perp[1] * k, v[2] - perp[2] * k)
        vel[j] = v
        new.append((p[j][0] + v[0] * dt + g[0] * dt2,
                    p[j][1] + v[1] * dt + g[1] * dt2,
                    p[j][2] + v[2] * dt + g[2] * dt2))

    state.p_prev = list(p)
    state.p = new
    ground = params.collision == COLLISION_GROUND
    for _ in range(params.iterations):
        if ground:
            _ground(state, params)
        _constrain(state, chain, root_p, par_q, lims, node_q)


def _init_state(chain, params, lims):
    """시작 상태. From animation = 시작 프레임 애니메이션 포즈(정지), Settled = 미리 매단다."""
    state = _State(chain.init_points)
    root_p = tuple(chain.root_pos[0])
    par_q = tuple(chain.root_parent_q[0])
    node_q = tuple(chain.root_node_q[0]) if chain.root_node_q else None
    _constrain(state, chain, root_p, par_q, lims, node_q)   # 기준 길이로 맞춘다(W 도 채움)
    state.p_prev = list(state.p)

    if params.start == START_SETTLED and params.settle_seconds > 0.0:
        # 정착은 "매달린 정지 상태" 를 얻는 게 목적이라 감쇠를 강하게 건다
        # (정지 자세는 감쇠와 무관 — 중력 · 한계 · 기준 포즈로만 정해진다).
        sp = params.copy()
        sp.linear_damping = max(params.linear_damping, SETTLE_LINEAR_DAMPING)
        sp.angular_damping = max(params.angular_damping, SETTLE_ANGULAR_DAMPING)
        dt = 1.0 / (params.fps * params.substeps)
        steps = int(round(params.settle_seconds * params.fps * params.substeps))
        for _ in range(steps):
            _substep(state, chain, root_p, par_q, sp, dt, lims, node_q)
        state.p_prev = list(state.p)        # 속도 0 으로 출발
    return state


def _blend_world(W_sim, W_anim, blend):
    if blend >= 1.0 or W_anim is None:
        return W_sim
    return [qslerp(a, s, blend) for a, s in zip(W_anim, W_sim)]


def solve_physics(chain, params, anim_world=None):
    """반환: (points[f][j], world[f][i]) — 점 위치와 노드 월드 회전(쿼터니언 튜플).

    anim_world[f][i] 는 `Physics Blend` < 1 일 때만 쓴다(애니메이션 월드 회전).
    `params.loop` 면 solve_physics_loop 로 넘긴다.
    """
    if params.loop:
        return solve_physics_loop(chain, params, anim_world)[:2]
    return _solve_once(chain, params, anim_world)


def _solve_once(chain, params, anim_world=None, state=None):
    nf = chain.frame_count()
    if nf == 0 or chain.node_count() == 0:
        return [], []
    lims = _limit_halfangles(params)
    if state is None:
        state = _init_state(chain, params, lims)
    sub = params.substeps
    dt = 1.0 / (params.fps * sub)

    pts = [list(state.p)]
    wq = [_blend_world(list(state.W), anim_world[0] if anim_world else None,
                       params.blend)]
    for f in range(1, nf):
        r0, r1 = chain.root_pos[f - 1], chain.root_pos[f]
        q0, q1 = chain.root_parent_q[f - 1], chain.root_parent_q[f]
        kin = chain.root_node_q
        for s in range(1, sub + 1):
            u = float(s) / sub
            root_p = _lerp3(r0, r1, u) if sub > 1 else tuple(r1)
            par_q = qslerp(q0, q1, u) if sub > 1 else tuple(q1)
            node_q = None
            if kin:
                node_q = qslerp(kin[f - 1], kin[f], u) if sub > 1 else tuple(kin[f])
            _substep(state, chain, root_p, par_q, params, dt, lims, node_q)
        pts.append(list(state.p))
        wq.append(_blend_world(list(state.W),
                               anim_world[f] if anim_world else None, params.blend))
    return pts, wq


class LoopInfo(object):
    """chain_solver.LoopInfo 와 같은 모양(bake_manager.loop_report 가 그대로 읽는다)."""

    def __init__(self, cycles, residual, tolerance, input_gap, input_tolerance):
        self.cycles = cycles
        self.residual = residual
        self.tolerance = tolerance
        self.input_gap = input_gap
        self.input_tolerance = input_tolerance

    @property
    def converged(self):
        return self.residual <= self.tolerance

    @property
    def input_cyclic(self):
        return self.input_gap <= self.input_tolerance


def _max_gap(a, b):
    return max(_length(_sub(x, y)) for x, y in zip(a, b))


def _extended(chain, cycles):
    """같은 구간을 cycles 바퀴 이어 붙인 입력(마지막 바퀴 = 원본과 같은 프레임열)."""
    def ext(seq):
        body = list(seq[:-1])
        out = []
        for _ in range(cycles - 1):
            out.extend(body)
        out.extend(seq)
        return out
    return PhysicsChainInput(ext(chain.root_pos), ext(chain.root_parent_q),
                             chain.ref_rel, chain.bone_local, chain.init_points,
                             ext(chain.root_node_q) if chain.root_node_q else None)


def solve_physics_loop(chain, params, anim_world=None, max_cycles=LOOP_MAX_CYCLES):
    """구간을 사이클로 보고 푼다(chain_solver.solve_loop 와 같은 방식). 반환 (points, world, LoopInfo)."""
    nf = chain.frame_count()
    p = params.copy()
    p.loop = False
    if nf < 3:
        pts, wq = _solve_once(chain, p, anim_world)
        return pts, wq, LoopInfo(1, 0.0, 0.0, 0.0, 0.0)

    scale = sum(chain.bone_len) or 1.0
    tol = LOOP_TOL_RATIO * scale
    input_gap = _length(_sub(chain.root_pos[0], chain.root_pos[-1]))
    qa, qb = chain.root_parent_q[0], chain.root_parent_q[-1]
    dq = abs(qa[0] * qb[0] + qa[1] * qb[1] + qa[2] * qb[2] + qa[3] * qb[3])
    input_gap = max(input_gap, 2.0 * math.acos(min(1.0, dq)) * scale)
    input_tol = LOOP_INPUT_TOL_RATIO * scale

    cycles = 2
    while True:
        ext = _extended(chain, cycles)
        pts, wq = _solve_once(ext, p)
        pts, wq = pts[-nf:], wq[-nf:]
        residual = _max_gap(pts[0], pts[-1])
        if residual <= tol or cycles >= max_cycles:
            if anim_world and p.blend < 1.0:
                wq = [_blend_world(w, a, p.blend) for w, a in zip(wq, anim_world)]
            return pts, wq, LoopInfo(cycles, residual, tol, input_gap, input_tol)
        cycles = min(cycles * 2, max_cycles)
