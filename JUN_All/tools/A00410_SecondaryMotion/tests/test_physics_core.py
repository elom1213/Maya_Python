# -*- coding: utf-8 -*-
"""Physics Asset 솔버 코어 시험 (maya 없이 순수 파이썬).

    python tests/test_physics_core.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, JUN_ALL)

from tools.A00410_SecondaryMotion.app.core import physics_solver as ps  # noqa: E402

passed = 0
failed = 0


def check(label, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print("PASS", label, extra)
    else:
        failed += 1
        print("FAIL", label, extra)


I = (0.0, 0.0, 0.0, 1.0)
N = 6
BONE = 5.0


def chain_input(nf, parent_q=None, root_pos=None, kin=None, rel=None):
    root = root_pos or [(0.0, 100.0, 0.0)] * nf
    par = parent_q or [I] * nf
    bl = [(BONE, 0.0, 0.0)] * N
    init = [(root[0][0] + BONE * j, root[0][1], root[0][2]) for j in range(N + 1)]
    return ps.PhysicsChainInput(root, par, rel or [I] * N, bl, init, kin)


def angle(a, b):
    a = ps._normalize(a)
    b = ps._normalize(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, ps._dot(a, b)))))


# ---- 0. 쿼터니언 규약: qm(a, b) = a 먼저
qa = ps.qaxis_angle((0, 0, 1), math.radians(90))
qb = ps.qaxis_angle((1, 0, 0), math.radians(90))
v = ps.rot(ps.rot((1.0, 0.0, 0.0), qa), qb)
v2 = ps.rot((1.0, 0.0, 0.0), ps.qm(qa, qb))
check("qm = a then b", max(abs(v[k] - v2[k]) for k in range(3)) < 1e-12)

# ---- V1 (코어판). 정지 + Free -> 중력 방향으로 매달림, 노드 0 도 시뮬레이션
nf = 24 * 10
p = ps.PhysicsParams(swing1_mode=ps.LIMIT_FREE, swing2_mode=ps.LIMIT_FREE,
                     kinematic_root=False)
pts, W = ps.solve_physics(chain_input(nf), p)
worst = max(angle(ps._sub(pts[-1][j + 1], pts[-1][j]), (0, -1, 0)) for j in range(N))
check("V1 static chain hangs along gravity", worst < 5.0, "%.3f deg" % worst)
check("V1 first frame = animation pose",
      ps._max_gap(pts[0], chain_input(nf).init_points) < 1e-9)

# ---- V6 길이
worst = 0.0
for row in pts:
    for j in range(N):
        worst = max(worst, abs(ps._length(ps._sub(row[j + 1], row[j])) - BONE))
check("V6 bone length kept", worst < 1e-9, "%.2e" % worst)

# ---- 월드 회전이 뼈 방향과 맞는가 (W 로 돌린 기준 뼈 = 점 사이 방향)
worst = 0.0
for f in (0, 50, nf - 1):
    for i in range(N):
        d = ps.rot((1.0, 0.0, 0.0), W[f][i])
        worst = max(worst, angle(d, ps._sub(pts[f][i + 1], pts[f][i])))
check("W matches bone direction", worst < 1e-6, "%.2e deg" % worst)

# ---- 키네마틱 루트: 노드 0 은 애니메이션 회전 그대로
kin = [ps.qaxis_angle((0, 0, 1), math.radians(10 * math.sin(f * 0.2))) for f in range(nf)]
p_k = ps.PhysicsParams(swing1_mode=ps.LIMIT_FREE, swing2_mode=ps.LIMIT_FREE)
pts_k, W_k = ps.solve_physics(chain_input(nf, kin=kin), p_k)
worst = max(abs(sum(W_k[f][0][k] * kin[f][k] for k in range(4))) for f in range(nf))
worst2 = min(abs(sum(W_k[f][0][k] * kin[f][k] for k in range(4))) for f in range(nf))
check("kinematic root follows animation", worst2 > 1 - 1e-12, "%.3e" % (1 - worst2))
worst = max(angle(ps._sub(pts_k[-1][j + 1], pts_k[-1][j]), (0, -1, 0)) for j in range(1, N))
check("kinematic root: rest still hangs", worst < 10.0, "%.3f deg" % worst)

# ---- V4 한계: 부모가 크게 흔들려도 각 노드 스윙이 타원 안
nf4 = 200
par = [ps.qaxis_angle((0, 0, 1), math.radians(80 * math.sin(f * 0.15))) for f in range(nf4)]
p4 = ps.PhysicsParams(swing1=30.0, swing2=10.0, kinematic_root=False)
ch4 = chain_input(nf4, parent_q=par)
pts4, W4 = ps.solve_physics(ch4, p4)
lim1, lim2 = math.radians(30.0), math.radians(10.0)
worst = 0.0
for f in range(nf4):
    for i in range(N):
        wp = par[f] if i == 0 else W4[f][i - 1]
        R_ref = ps.qm(ch4.ref_rel[i], wp)
        d = ps.rot(ps.rot(ch4.bone_dir[i], W4[f][i]), ps.qinv(R_ref))
        b = ch4.bone_dir[i]
        c = ps._cross(b, d)
        sn = ps._length(c)
        ang = math.atan2(sn, ps._dot(b, d))
        if sn < 1e-12:
            continue
        ax = ps._scale(c, 1.0 / sn)
        s1, s2 = ch4.swing_frames[i]
        e = (ang * ps._dot(ax, s1) / lim1) ** 2 + (ang * ps._dot(ax, s2) / lim2) ** 2
        worst = max(worst, e)
check("V4 swing inside ellipse cone", worst <= 1.0 + 1e-6, "max %.6f" % worst)
# 같은 입력을 Free 로 풀면 한계를 넘는다(시험이 비어 있지 않음을 확인)
p4f = p4.copy()
p4f.swing1_mode = p4f.swing2_mode = ps.LIMIT_FREE
_, W4f = ps.solve_physics(ch4, p4f)
check("V4 control: free exceeds the cone", any(
    angle(ps.rot((1, 0, 0), W4f[f][1]), ps.rot((1, 0, 0), W4f[f][0])) > 31
    for f in range(nf4)))

# Locked 두 축 = 부모에 고정
p4l = p4.copy()
p4l.swing1_mode = p4l.swing2_mode = ps.LIMIT_LOCKED
_, W4l = ps.solve_physics(ch4, p4l)
worst = max(1 - abs(sum(W4l[f][i][k] * ps.qm(ch4.ref_rel[i], par[f] if i == 0 else W4l[f][i - 1])[k]
                        for k in range(4)))
            for f in range(nf4) for i in range(N))
check("locked swing = rigid to parent", worst < 1e-9, "%.2e" % worst)

# ---- V3 진자: 감쇠 0 이면 진폭 유지, 감쇠 > 0 이면 줄어든다
nf3 = 24 * 12


def tip_amplitude(pts_, a, b):
    xs = [row[-1][0] for row in pts_[a:b]]
    return max(xs) - min(xs)


p3 = ps.PhysicsParams(swing1_mode=ps.LIMIT_FREE, swing2_mode=ps.LIMIT_FREE,
                      linear_damping=0.0, angular_damping=0.0, kinematic_root=False,
                      substeps=8)
pts3, _ = ps.solve_physics(chain_input(nf3), p3)
early = tip_amplitude(pts3, 24, 24 * 4)
late = tip_amplitude(pts3, 24 * 8, 24 * 12)
check("V3 no damping keeps swinging", late > 0.5 * early, "early %.2f late %.2f" % (early, late))
p3d = p3.copy()
p3d.linear_damping = 1.0
p3d.angular_damping = 2.0
pts3d, _ = ps.solve_physics(chain_input(nf3), p3d)
late_d = tip_amplitude(pts3d, 24 * 8, 24 * 12)
check("V3 damping settles", late_d < 0.2 * late, "late %.2f -> %.2f" % (late, late_d))

# ---- V9 fps 독립: 24 fps x 8 서브스텝 / 48 fps x 4 서브스텝(같은 dt)에서 같은 초 시점 팁 위치.
# 파라미터가 초 단위라 프레임레이트가 바뀌어도 같은 움직임이어야 한다. (서브스텝 dt 자체가 다르면
# 적분 오차가 달라 혼돈 진자는 갈라진다 — 그건 fps 의존이 아니라 시간 해상도 차이다.)
def run_fps(fps, substeps, seconds=3.0):
    nfx = int(fps * seconds) + 1
    par_ = [ps.qaxis_angle((0, 0, 1), math.radians(40 * math.sin(2.0 * f / fps)))
            for f in range(nfx)]
    pp = ps.PhysicsParams(fps=fps, substeps=substeps, kinematic_root=False)
    pts_, _ = ps.solve_physics(chain_input(nfx, parent_q=par_), pp)
    return pts_, fps


a24, _ = run_fps(24.0, 8)
a48, _ = run_fps(48.0, 4)
worst = 0.0
for sec in (1.0, 2.0, 3.0):
    worst = max(worst, ps._length(ps._sub(a24[int(sec * 24)][-1], a48[int(sec * 48)][-1])))
check("V9 fps independent (< 1% chain length)", worst < 0.01 * N * BONE, "%.4f" % worst)

# ---- V10 Settled: 첫 프레임부터 매달려 정지
p10 = ps.PhysicsParams(swing1_mode=ps.LIMIT_FREE, swing2_mode=ps.LIMIT_FREE,
                       start=ps.START_SETTLED, settle_seconds=10.0, kinematic_root=False)
pts10, _ = ps.solve_physics(chain_input(48), p10)
gap = ps._max_gap(pts10[0], pts10[-1])
check("V10 settled: first == last on static input", gap < 1e-3, "%.2e" % gap)
worst = max(angle(ps._sub(pts10[0][j + 1], pts10[0][j]), (0, -1, 0)) for j in range(N))
check("V10 settled: already hanging at frame 0", worst < 5.0, "%.3f deg" % worst)

# ---- 바닥: 아무 점도 바닥 아래로 가지 않는다(반복 횟수 안에서), 끄면 내려간다
p_g = ps.PhysicsParams(swing1_mode=ps.LIMIT_FREE, swing2_mode=ps.LIMIT_FREE,
                       kinematic_root=False, collision=ps.COLLISION_GROUND,
                       ground_height=90.0, iterations=4)
pts_g, _ = ps.solve_physics(chain_input(240), p_g)
low = min(pt[1] for row in pts_g for pt in row[1:])
check("ground keeps points above (tol 0.5)", low > 90.0 - 0.5, "min y %.3f" % low)
low_n = min(pt[1] for pt in pts[-1][1:])
check("no collision falls through", low_n < 80.0, "min y %.3f" % low_n)

# ---- Loop
nfl = 49
par_l = [ps.qaxis_angle((0, 0, 1), math.radians(30 * math.sin(2 * math.pi * f / (nfl - 1))))
         for f in range(nfl)]
pl = ps.PhysicsParams(kinematic_root=False, loop=True, linear_damping=1.0)
ptsl, Wl, info = ps.solve_physics_loop(chain_input(nfl, parent_q=par_l), pl)
check("loop seam closes", info.converged and ps._max_gap(ptsl[0], ptsl[-1]) < 1e-4,
      "cycles %d residual %.2e" % (info.cycles, info.residual))

print("\n{0}/{1} passed".format(passed, passed + failed))
sys.exit(1 if failed else 0)
