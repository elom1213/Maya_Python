---
title: A00410_SecondaryMotion — Physics Asset 모드 작업 계획서
aliases: [PhysicsAsset mode, A00410 Physics Asset, 래그돌 체인]
tags: [maya-python, plan, animation, secondary-motion, physics, physics-asset, unreal]
updated: 2026-11-10
status: 계획 (구현 전)
---

# A00410_SecondaryMotion — Physics Asset 모드 작업 계획서

`A00410_SecondaryMotion` 은 지금 언리얼 **KawaiiPhysics** 의 원리를 흉내 낸다. 여기에 언리얼
**Physics Asset**(PhAT 바디 + 컨스트레인트를 시뮬레이션하는 것)의 움직임을 재현하는 **두 번째 솔버**를 더한다.

> [!important] 이 기능에 가장 크게 기대하는 것
> **KawaiiPhysics 는 본 체인/컨트롤러 체인의 원래 회전값을 지킨다. Physics Asset 은 지키지 않는다.**
> 체인 루트만 애니메이션을 따르고, 그 아래는 **중력 · 관성 · 조인트 한계로만** 움직인다.
> 이 차이가 화면에서 **확실히** 보여야 하고, 시험으로 **숫자로** 증명돼야 한다(10장).

관련: 기존 설계 [`A00410_ChainPhysics_plan.md`](A00410_ChainPhysics_plan.md) · 툴 문서
[`../A00410_SecondaryMotion.md`](../A00410_SecondaryMotion.md) · 현재 v01.11.

---

## 1. 두 모델의 차이 — 무엇을 바꾸는가

| | KawaiiPhysics (지금) | Physics Asset (추가) |
|---|---|---|
| 각 노드를 끄는 힘 | **원래 자리(애니메이션 FK 위치)로 당기는 스프링**(`Stiffness`) | **없다.** 애니메이션 포즈를 모른다 |
| 자식 노드의 회전 키 | 결과의 **바탕**. 결과 = 원본 + 흔들림 | **무시된다.** 결과에 영향 없음 |
| 움직임을 만드는 것 | 원래 자리와의 차이(관성) | 중력 · 관성 · 감쇠 · 조인트 한계 · (충돌) |
| 가만히 있는 애니메이션 | 원본 포즈 그대로(변화 0) | **중력 방향으로 늘어진다** |
| 각도 제한의 기준 | 그 프레임의 **애니메이션** 방향 | **기준 포즈**(컨스트레인트 프레임)의 상대 방향 |
| 뼈 길이 | 그 프레임의 애니메이션 길이 | 기준 포즈 길이(강체 — 늘지 않는다) |
| 시간 단위 | 프레임(24fps 기준 보정) | **초**(중력 cm/s², 감쇠 1/s) — fps 와 무관 |

UE 에서 이 차이는 이렇다. 시뮬레이트되는 바디는 애니메이션 포즈를 읽지 않고(`Physics Blend Weight` 1),
`Kinematic` 바디(보통 체인의 부모 = 골반 · 머리 등)만 애니메이션을 따라간다. 애니메이션 쪽으로 끌어당기는
힘은 별도 기능(`Physical Animation` 컴포넌트)이고 기본은 없다.

**코드 관점의 요점은 하나다.** 지금 솔버의 `(target - p) * stiffness` 항과, 회전 재구성의
`W_new = W_orig * q_swing`(= **애니메이션 회전 위에** 스윙을 얹는 것)이 "원래 회전값을 지키는" 두 군데다.
새 모드는 **둘 다 쓰지 않는다.** 그래서 기존 `chain_solver` / `pose_builder` 를 고치지 않고 **새 모듈**을 만든다
(Kawaii 결과는 1e-12 까지 그대로 — 무회귀 조건).

---

## 2. 범위

### 1단계 (이번 작업)

- 솔버 선택: `Kawaii (keep animation)` / `Physics Asset (simulate)`.
- 체인 루트(점 0)의 **위치**와 루트의 **DAG 부모 회전**만 애니메이션을 따른다(= Kinematic). 나머지는 시뮬레이션.
- 중력(cm/s²) · 선형 감쇠 · 각 감쇠 · 서브스텝 · 반복 횟수.
- 조인트 한계: **Swing 1 / Swing 2 (타원 콘) · Twist**, 각각 `Free / Limited / Locked`.
- 시작 상태: `From animation`(시작 프레임 포즈에서 정지 출발 → 떨어진다) / `Settled`(미리 매달려 있는 상태로 출발).
- 기준 포즈: `Start frame`(기본) / `Current frame`.
- 바닥 평면 충돌(선택, 기본 끔).
- `Physics Blend`(UE `Physics Blend Weight`) — 0~1, 기본 1.
- 기존 공용 부분 그대로: Mode(Bone Chain / Bone Root), Target(Controller / Joint), Virtual Child, Rotate last node,
  Rotate Axis, Loop, Live Preview, Output(Override Layer / Bake Keys), 진행 팝업, undo.

### 2단계 (요청 시)

- **트위스트 동역학**(1단계는 트위스트를 부모 프레임에 묶는다 — 4.4절), 바디 관성 텐서.
- 씬 콜라이더(구 / 캡슐 — 마야 노드를 지정), 바디 캡슐 반경, 체인 간 충돌.
- 분기 트리를 한 번에 풀기(지금 Bone Root 는 분기를 따로 푼다).
- `Animation Drive`(UE Physical Animation 의 각 드라이브 강도, 기본 0). **0 이 아니면 애니메이션을 다시 지키기 시작**하므로
  이 모드의 정체성과 부딪친다 → 2단계에서 따로 결정한다.

### 범위 밖

- 마야 Bullet / nucleus 사용(기존 계획서 2장과 같은 이유 — 스크럽 불가 · 처음부터 재생).
- 메시 충돌, 본 사이 스프링 외 다른 컨스트레인트 종류(Prismatic 등).

---

## 3. 결론 먼저 — 솔버 방식

**위치 기반(PBD) 체인 + 노드별 월드 회전을 함께 들고 다니는 순수 파이썬 솔버**를 새로 만든다.

- 점(관절 위치)은 베를레 적분 + 중력 + 감쇠, 길이 구속은 **기준 포즈 길이**로.
- 각 노드의 월드 회전은 **부모의 시뮬레이션 회전 × 기준 상대 회전 × 최소 스윙**으로 매 서브스텝 만든다.
  애니메이션 회전(`W_orig`)은 루트의 DAG 부모 말고는 **읽지 않는다.**
- 조인트 한계는 이 회전을 기준으로 **부모 프레임 안에서** 스윙(타원 콘)을 잘라 낸다.
- 결과는 **월드 회전**으로 내보내고, 로컬 회전 키 변환은 새 함수가 맡는다(JO / RA / rotateOrder 규칙은 기존 그대로).

마야 Bullet 이나 완전한 강체 XPBD 를 1단계에서 쓰지 않는 이유:
- 체인 하나는 "점 + 길이 구속 + 각도 제한" 만으로 Physics Asset 의 **눈에 보이는 성질**(매달림, 진자, 한계)이 다 나온다.
- 기존 실측(20본 × 300f 솔브 6 ms)과 같은 계열이라 **슬라이더 프리뷰가 그대로 실시간**일 가능성이 크다(0단계에서 잰다).
- 솔버가 처음부터 노드별 월드 회전을 들고 있으므로, 2단계에서 트위스트 동역학을 붙일 자리가 이미 있다.

---

## 4. 알고리즘

규약은 기존과 같다: **행벡터, `world = local * parentWorld`**, 쿼터니언 곱 `a * b` = a 먼저.
솔버는 maya 를 import 하지 않는다 → 쿼터니언 · 벡터 헬퍼를 순수 파이썬으로 둔다(`chain_solver` 와 같은 성질).

### 4.1 입력 (샘플러가 만든다)

체인 노드 `i = 0..n-1`(가상 팁이 있으면 점은 n+1 개), 프레임 `f`.

| 이름 | 뜻 | 출처 |
|------|----|------|
| `root_pos[f]` | 점 0 의 월드 위치(애니메이션) | 기존 `positions[f][0]` |
| `root_parent_q[f]` | 노드 0 의 **DAG 부모** 월드 회전(애니메이션) | 기존 `parent_quats[f][0]` |
| `ref_rel[i]` | 기준 포즈에서 노드 i 의 회전을 그 "체인 부모" 기준으로 본 것. `i=0`: `W_ref[0] * P_ref[0]⁻¹`, `i≥1`: `W_ref[i] * W_ref[i-1]⁻¹` (사이 오프셋 그룹 회전이 들어 있다) | 기준 프레임 샘플 |
| `bone_local[i]` | 기준 포즈의 뼈 벡터(점 i → 점 i+1)를 **노드 i 의 기준 월드 회전 공간**으로 옮긴 것 | 기준 프레임 샘플 |
| `bone_len[i]` | 기준 포즈 뼈 길이 | 〃 |

가상 팁(`Rotate last node`)과 Virtual Child 는 **기준 포즈에서** 만든다(마지막 뼈 연장 / 로컬 오프셋). 그 뒤로는 바디의 일부다.

### 4.2 서브스텝 하나

`dt = 1 / (fps × substeps)`. 루트 목표는 프레임 사이를 선형 보간(위치), 루트 부모 회전은 slerp.

```
P0      = root_pos(t)                       # 키네마틱
Q_par   = root_parent_q(t)

for i in 1..n:                               # 점 이동 (적분)
    v      = (p[i] - p_prev[i]) / dt
    v     *= 1 / (1 + dt * linear_damping)   # UE 와 같은 꼴
    p_new  = p[i] + v*dt + gravity*dt²

for it in 1..iterations:                     # 구속 (루트 → 팁)
    W_parent = Q_par
    for i in 0..n-1:
        R_ref   = ref_rel[i] * W_parent                   # 이 노드가 "기준대로 붙었을 때" 의 월드 회전
        d_ref   = bone_local[i] rotated by R_ref          # 그때의 뼈 방향
        d_sim   = normalize(p_new[i+1] - p_new[i])
        d_sim   = limit(d_sim, d_ref, R_ref, swing1, swing2)   # 4.3
        p_new[i+1] = p_new[i] + d_sim * bone_len[i]       # 길이 구속(강체)
        W[i]    = R_ref * swing(d_ref -> d_sim)           # 최소 스윙(트위스트 없음) — 4.4
        W_parent = W[i]
```

- **애니메이션 회전이 들어가는 곳은 `Q_par`(루트의 부모) 하나뿐이다.** 그래서 자식 노드에 키를 아무리 넣어도 결과가 같다 —
  이게 10장 시험 V2 의 근거다.
- 각 감쇠(`angular_damping`)는 1단계에서는 **스윙 각속도**에만 건다: 구속 후 `v` 를 뼈 방향 성분과 수직 성분으로 나눠
  수직 성분에 `1/(1+dt·angular_damping)` 를 곱한다(점 기반이라 각속도 ≈ 수직 속도 / 길이).
- 반복은 루트 → 팁 한 방향 1회로 충분하다(부모가 먼저 확정되고 자식은 그 위에서 푼다 — 기존 솔버와 같은 순서).
  `iterations` 는 바닥 충돌과 한계가 서로 밀어낼 때만 의미가 있다. 기본 1, 충돌을 켜면 4.
- 바닥 충돌(선택): 점이 `y < ground + radius` 면 위로 투영, 그 프레임 접선 속도에 마찰 감쇠.

### 4.3 조인트 한계 (Swing 1 / Swing 2 / Twist)

UE 컨스트레인트는 **Twist 축 = 뼈 방향**, Swing 1 · Swing 2 는 그에 수직인 두 축 둘레 회전이다.

- 노드마다 **트위스트 축** = `bone_local[i]` 에 가장 가까운 노드 로컬 축(±X/±Y/±Z). 나머지 두 축이 Swing 1 · 2.
  UI 는 "Swing 1 (around Y)" 처럼 축 이름을 함께 보여 준다(체인 첫 노드 기준, 체인 안 노드들이 다르면 로그로 알림).
- `Limited`: 스윙 방향을 **타원 콘** `(a/s1)² + (b/s2)² ≤ 1` 안으로 투영. a, b = d_sim 을 R_ref 공간에서 본
  두 수직 축 각도(스윙-트위스트 분해의 스윙 쪽). 경계 밖이면 타원 위의 가장 가까운 방향으로(1단계는 반지름 방향 투영으로 근사).
- `Locked`: 그 축 스윙 0. 둘 다 Locked 면 그 뼈는 부모에 고정(강체 연결).
- `Free`: 제한 없음.
- 기본값(UE PhAT 의 새 컨스트레인트 기본과 비슷하게): Swing 1 · 2 = `Limited 45°`, Twist = `Limited`(1단계에서는 4.4 때문에 사실상 Locked).
- 노드별 한계를 다르게 줄 수 있게 **커브 배수**(기존 `Graph` 팝업 재사용, 루트 0 → 팁 1)를 붙인다 — 1단계 끝에서 여유 있으면.

### 4.4 트위스트 (1단계의 단순화)

`W[i] = R_ref * swing(d_ref → d_sim)` 은 **최소 회전**이라 노드의 트위스트(뼈 축 둘레 롤)는 항상 **부모 프레임을 따른다**.
UE 로 치면 Twist `Locked` 와 같다. 머리카락 · 꼬리 · 천 조각 PhAT 은 보통 트위스트를 잠그거나 몇 도만 주므로
1단계 결과로 충분하다. 트위스트가 **애니메이션에서 오는 것이 아니라 부모에서 온다**는 점은 이미 Physics Asset 답다.
트위스트 동역학(관성으로 돌아가는 롤)은 2단계.

### 4.5 시작 상태

| 옵션 | 동작 | 화면에서 |
|------|------|----------|
| `From animation` (기본) | 시작 프레임의 **애니메이션 포즈**로 놓고 속도 0. 첫 프레임 = 원본 | 재생하면 체인이 **떨어지며** 매달린다 — 차이가 가장 잘 보인다 |
| `Settled` | 시작 프레임 루트를 고정한 채 `settle_seconds`(기본 3 s) 미리 풀어 정지시킨 뒤 출발 | 첫 프레임부터 매달려 있다 — 실사용 |
| `Loop` (기존 체크) | 기존 `solve_loop` 와 같은 방식(마지막 바퀴만) | 루프 애니 |

`Settled` 는 UE 에서 시뮬레이션을 미리 켜 두고 레벨에 들어온 상태에 해당한다.

### 4.6 회전 키로 변환

새 함수 `pose_builder.build_rotations_from_world(sample, W_new)`:

```
delta_prev = 단위
for i in 0..n_rot-1:
    parent_new = parent_quats[f][i] * delta_prev        # 실제 DAG 부모(오프셋 그룹 포함)
    local      = W_new[i] * parent_new⁻¹
    R          = RA⁻¹ * local * JO⁻¹                     # 기존 규칙 그대로
    rotate     = euler(R, rotateOrder) → 언랩
    delta_prev = W_orig[f][i]⁻¹ * W_new[i]              # 다음 노드 부모에 얹힐 변화량
```

`delta_prev` 트릭은 기존 `build_rotations` 의 `prev_delta = q_swing` 과 같은 것(거기선 `W_new = W_orig·q_swing` 이라
`W_orig⁻¹·W_new = q_swing`)을 일반화한 것이다. 사이에 낀 오프셋 그룹의 정적 회전은 `parent_quats` 안에서 상쇄되므로
**자식의 애니메이션 회전은 결과에 남지 않는다.**

> 주의 — 오프셋 그룹 자체에 키가 있으면 그 회전은 남는다(체인 노드가 아니므로). 문서에 적는다.

### 4.7 Blend

`Physics Blend` < 1 이면 노드별로 `slerp(W_orig, W_new, blend)` 후 4.6. 1 이면 애니메이션은 루트 부모 말고 한 번도 안 쓰인다.
Override 레이어 weight 도 같은 효과를 내지만 이 값은 레이어 없이 Bake Keys 에도 먹는다.

---

## 5. 파라미터 · UI

UI 문자열은 영어. 기존 창의 `Physics` 박스 위에 **솔버 선택**을 둔다.

```
┌ Solver ───────────────────────────────────────────────────┐
│ (•) Kawaii (keep animation)   ( ) Physics Asset (simulate)│
└───────────────────────────────────────────────────────────┘
┌ Physics Asset ─────────────────── (Physics Asset 일 때만) ┐
│ Gravity  X [   0 ]  Y [ -980 ]  Z [   0 ]  cm/s²          │
│ Linear Damping   [====|-----] 0.5                         │
│ Angular Damping  [===|------] 1.0                         │
│ Swing 1 (around Y) [Limited ▼]  [ 45 ]°                   │
│ Swing 2 (around Z) [Limited ▼]  [ 45 ]°                   │
│ Twist   (around X) [Locked  ▼]   (dynamic twist: phase 2) │
│ Start   [From animation ▼]  Settle [ 3.0 ] s              │
│ Reference pose [Start frame ▼]                            │
│ Substeps [ 4 ]  Iterations [ 1 ]                          │
│ [ ] Ground  Height [ 0 ]                                   │
│ Physics Blend    [=========|] 1.0                         │
└───────────────────────────────────────────────────────────┘
```

- Kawaii 전용 컨트롤(`Stiffness`, `Falloff`, `World Damp`, 그 `Graph` 들, `Limit Angle`)은 Physics Asset 일 때 **숨긴다**
  (비활성으로 두면 "Stiffness 0 이면 같은 것 아닌가" 오해가 생긴다 — 같지 않다: 4장의 회전 기준과 단위가 다르다).
- 공용으로 남는 것: Mode · Target · Range · Virtual Child · Rotate last node · Rotate Axis · Loop · Live Preview · Output.
- 중력 단위: UI 는 **cm/s²**(UE 기본 -980 과 같은 수). 씬 리니어 단위가 cm 가 아니면 `cmds.currentUnit` 으로 환산하고 로그에 한 줄.
  월드 업 축이 Z 인 씬이면 기본값을 Z -980 으로(`cmds.upAxis -q`).
- 솔버 선택과 파라미터는 `optionVar` 로 기억(기존 방식).
- 솔버를 바꾸면 **프리뷰 레이어를 다시 만든다**(Rotate Axis 를 바꿀 때와 같은 이유 — 살아 있는 커브가 남는다). 샘플 캐시는 재사용
  (기준 포즈는 캐시에서 고른다. `Reference pose = Current frame` 이 캐시 구간 밖이면 그 프레임만 추가 샘플링).
- 툴팁에 1장 표의 핵심 한 줄을 쓴다: *"Only the chain root follows the animation. Rotation keys on the other nodes are ignored."*

---

## 6. 파일 · 모듈

| 파일 | 작업 |
|------|------|
| `app/core/physics_solver.py` | **신규.** 순수 파이썬. `PhysicsParams`, `JointLimit`, `solve_physics(chain_input, params) -> (positions, world_quats)`, `solve_physics_loop`, 쿼터니언 헬퍼, `settle()` |
| `app/core/scene_sampler.py` | `reference_pose(sample, frame_index)` → `ref_rel`, `bone_local`, `bone_len`, 트위스트 축. 쿼터니언을 튜플로 넘기는 변환. 기존 함수는 그대로 |
| `app/core/pose_builder.py` | `build_rotations_from_world()` 추가(4.6). 기존 `build_rotations` 손대지 않음 |
| `app/core/bake_manager.py` | `SecondaryMotionSession.solve()` 가 `params` 종류로 갈라진다(`SOLVER_KAWAII` / `SOLVER_PHYSICS`). 출력(`outputs.py`)은 `writes` 형식이 같아서 **변경 없음** |
| `app/ui/main_window.py` | Solver 라디오, Physics Asset 박스, 보이기/숨기기, optionVar, 프리뷰 재생성 |
| `tests/test_physics_core.py` | **신규.** maya 없이(파이썬만) 솔버 시험 |
| `tests/test_physics_maya.py` | **신규.** mayapy 헤드리스 — 10장 V1~V10 |
| `app/config/version.py` · `CHANGELOG.md` · `docs/A00410_SecondaryMotion.md` | v01.12 (1단계 완료 시) |

---

## 7. 개발 단계

| 단계 | 내용 | 끝났다는 기준 |
|------|------|---------------|
| 0 | **성능 측정 게이트.** 20본 × 300f × substeps 4 로 4.2 루프 시제품을 재 본다 | 솔브 + 회전 변환 ≤ 60 ms 면 슬라이더 실시간 그대로. 넘으면 프리뷰만 substeps 1 로 내리고 Apply 때 정식 값(로그에 표시) |
| 1 | `physics_solver` 코어 + 순수 파이썬 시험 | V1 · V3 · V4 · V6 · V9 통과(점/회전 수준) |
| 2 | 샘플러 기준 포즈 + `build_rotations_from_world` | V5 왕복 오차 < 1e-9 (JO · RA · rotateOrder 섞은 씬) |
| 3 | 세션 분기 + 출력 연결 | V2 · V7 · V8 통과, Override Layer / Bake Keys 둘 다 |
| 4 | UI | 오프스크린 시험(보이기/숨기기, optionVar, 솔버 전환 시 프리뷰 재생성) |
| 5 | 시작 상태 `Settled` · Loop · 바닥 | V10 + Loop 이음매 1e-6 |
| 6 | 문서 · CHANGELOG · WORKLOG · 포트폴리오 | — |

---

## 8. 기존 함정 (메모리에서 — 그대로 지킨다)

- 회전 재구성은 **실제 DAG 부모**로(앞 체인 노드로 가정하면 오프셋 그룹 회전이 구워진다 — v01.01 버그).
- joint `local = R·JO` → JO 를 벗긴다. transform `local = RA·R`.
- 키는 `MFnAnimCurve.addKeys` 벌크로. 샘플링은 한 번만 하고 캐시.
- 오일러 언랩.
- 시험 씬은 **JO · rotateAxis · rotateOrder 를 0 아닌 값으로 섞는다** — 0 인 씬은 아무것도 검증하지 못한다.
- Bone Root + Controller 는 셰이프 있는 노드만 체인 노드(그룹은 통과).
- Rotate Axis 를 바꾸면 프리뷰 레이어 삭제. Apply 는 항상 다시 푼다.

---

## 9. 리스크

| 리스크 | 대응 |
|--------|------|
| Python 속도(서브스텝 × 반복) | 0단계 게이트. 넘으면 프리뷰 저품질 + Apply 정식 |
| 루트가 빠르게 움직일 때 길이 구속만으로 체인이 "튄다"(PBD 의 에너지 증가) | 서브스텝 기본 4, 속도 상한(`max_speed`, 내부값) |
| 타원 콘 투영 근사가 경계에서 떨림 | 1단계는 반지름 방향 투영 + 시험으로 경계 위 값만 확인. 떨림이 보이면 2단계에서 정확한 최근접점 |
| `From animation` 이 첫 몇 프레임 크게 떨어져 "버그처럼" 보임 | 툴팁 + 로그 한 줄. 실사용은 `Settled` 를 권하는 문구 |
| 분기 체인(Bone Root)이 공통 부모를 두 번 풂 | 1단계는 기존처럼 `owners` 로 첫 체인만 기록, 로그에 알림. 2단계 트리 솔브 |
| Twist Locked 가 롤 애니메이션을 지운다 | 그게 Physics Asset 동작이다. 문서와 툴팁에 명시 |

---

## 10. 검증 계획 — "원래 회전값을 유지하지 않는다" 를 숫자로

mayapy 2024 헤드리스. 시험 씬은 컨트롤러 체인(오프셋 그룹 포함)과 조인트 체인 둘, JO · RA · rotateOrder 를 섞는다.

| # | 시나리오 | Kawaii 기대 | Physics Asset 기대 (판정) |
|---|----------|-------------|---------------------------|
| **V1** | 애니메이션 없음(정지), 체인이 수평으로 뻗어 있음 | 결과 = 원본(편차 0) | 마지막 프레임에 **모든 뼈가 중력 방향**과 이루는 각 < 5°(한계 Free), 원본 대비 회전 차이 > 60° |
| **V2** | 루트 정지, **자식들에만 회전 키**(꼬리 말기) | 말린 모양이 결과에 남는다 | **자식 키를 지운 씬의 결과와 1e-9 이내로 같다** — 자식 애니메이션과 독립 (이 기능의 핵심 판정) |
| V3 | 루트만 Y 축 회전 왕복 | 따라가며 흔들림 | 진자 운동. 감쇠 0 이면 자유 진동 진폭이 10 주기 동안 5% 이상 줄지 않는다, 감쇠 > 0 이면 단조 감소 |
| V4 | 한계 Limited 30° / 10° | — | 매 프레임 각 노드의 스윙(부모 기준) 이 타원 안(+1e-6) |
| V5 | 왕복 검증 | — | 구운 회전으로 계산한 실제 월드 위치 == 솔버 위치 (< 1e-9) |
| V6 | 길이 | — | 매 프레임 `|p[i+1]-p[i]| == bone_len[i]` (< 1e-9) |
| V7 | 루트 | — | 루트 노드의 **위치**는 원본 그대로(회전은 시뮬레이션 — Kawaii 와 같다) |
| V8 | 무회귀 | 기존 결과와 1e-12 이내 | — |
| V9 | fps 독립 | — | 24 fps 와 48 fps 씬에서 같은 초 시점 팁 위치 차 < 체인 길이의 1% |
| V10 | `Settled` | — | 첫 프레임 속도 ≈ 0, 정지 애니면 첫 프레임 = 마지막 프레임 (< 1e-4) |

추가로 **화면 확인용 데모 씬**(`tests/demo_physics_asset.py`): 같은 꼬리 체인을 둘 복제해 하나는 Kawaii, 하나는 Physics Asset 으로
구워 나란히 둔다. 루트가 정지 → 회전 → 정지하는 30f 애니 + 자식에 말기 키. 뷰포트에서 차이가 바로 보여야 한다(GUI 확인은 사용자).

---

## 11. 열린 결정 (진행 전에 정할 것 — 괄호 안이 추천)

1. **시작 상태 기본값** — `From animation`(차이가 가장 잘 보임) vs `Settled`(실사용). (추천: `From animation`, Settled 는 옵션)
2. **UI 배치** — 지금 창에 Solver 라디오 vs 별도 탭. (추천: 라디오. TSL · 구간 · 출력이 전부 공용)
3. **1단계 트위스트를 부모에 묶는 것** 괜찮은가. (추천: 괜찮다 — 헤어 · 꼬리 PhAT 기본과 같음, 동역학 트위스트는 2단계)
4. **충돌 범위** — 1단계는 바닥 평면만. (추천: 그렇다. 씬 콜라이더는 2단계)
5. **Animation Drive**(애니메이션 쪽으로 끄는 힘) — 넣지 않음 vs 2단계 옵션. (추천: 1단계 제외. 넣는 순간 Kawaii 와 경계가 흐려진다)
