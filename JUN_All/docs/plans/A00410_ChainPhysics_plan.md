---
title: A00410_ChainPhysics 개발 계획서 — FK 본 체인 관성/찰랑임 애니메이션
aliases: [ChainPhysics, SecondaryMotion, A00410, 찰랑이, KawaiiPhysics Maya]
tags: [maya-python, plan, animation, secondary-motion, physics, kawaiiphysics, game-asset]
updated: 2026-07-29
status: 계획 (구현 전)
---

# A00410_ChainPhysics 개발 계획서

FK 로 애니메이션되는 **컨트롤러 체인**에 언리얼 **KawaiiPhysics** 같은 **관성(follow-through / overlap)**
을 얹어 **키 애니메이션으로 재현**하는 in-Maya PySide 툴.

> **핵심 요구**: 체인의 맨 위 부모가 움직이면, 부모에서 **먼 자식일수록 원래 자리에 남으려 하고**,
> **가까운 자식일수록 부모를 더 따라간다**. 게임 에셋용이므로 **리얼한 시뮬레이션은 불필요**하고,
> **빠르고 실시간으로 확인** 가능해야 한다.

---

## 1. 결론 먼저

**마야의 기존 시뮬레이션 솔버(nucleus/nHair/nCloth/Bullet)는 응용하지 않는다.**
대신 **KawaiiPhysics 와 같은 계열의 경량 위치기반(position-based) 스프링 솔버를 순수 파이썬으로 직접
구현**하고, **구간 전체를 한 번에 풀어서 애님 레이어에 통째로 굽는다.**

실측(mayapy, Maya 2024, 20본 × 300프레임) 근거:

| 단계 | 시간 |
|------|------|
| 드라이버 월드행렬 300프레임 샘플링 (`getAttr -time`) | **0.013 s** |
| 스프링 솔버 20본 × 300프레임 (순수 파이썬) | **0.006 s** |
| 회전 키 18,000개 기록 (`MFnAnimCurve.addKeys` 벌크) | **0.007 s** |
| **합계 (전 구간 재계산 + 키 기록)** | **≈ 0.03 s** |

> [!important] 이 수치가 이 툴의 설계를 통째로 결정한다.
> **전 구간을 다시 푸는 데 30ms** 밖에 안 걸리므로, 파라미터 슬라이더를 드래그할 때마다 **구간 전체를
> 재계산해서 프리뷰 레이어에 다시 구워도 60fps 가 나온다.** 그리고 재생은 **그냥 애님커브 재생**이라
> 씬이 전혀 무거워지지 않는다 — 즉 "실시간 피직스"를 **런타임 시뮬 없이** 얻는다.

참고로 키 기록 방식 선택도 성능 차이가 크다: 같은 18,000키를 `cmds.setKeyframe` 로 쓰면 **0.529 s**,
`MFnAnimCurve.addKeys` 벌크로 쓰면 **0.007 s** — **약 74배**. 벌크 API 를 기본으로 한다.

---

## 2. 마야 기존 기능을 응용할 수 있는가

가능은 하지만 **이 목적에는 전부 부적합**하다. (성능 이전에 **작업 흐름**이 안 맞는다.)

| 방식 | 결과 품질 | 왜 쓰지 않는가 |
|------|-----------|----------------|
| **nHair 다이나믹 커브 + IK Spline** (가장 흔한 "다이나믹 체인" 리그) | 좋음, 충돌 지원 | nucleus 는 **시작 프레임부터 순차 재생**해야 결과가 나온다 → **스크럽 불가**, 파라미터 하나 바꿀 때마다 처음부터 다시 재생. 결과 확인에 실시간성이 없고, 최종적으로 또 베이크 단계가 필요 |
| **nCloth / Bullet** | 더 리얼 | 위 문제 + 훨씬 무겁다. 게임 에셋에는 과한 리얼리즘 |
| **Jiggle Deformer** | 간단 | **메시 포인트 전용** — 조인트/컨트롤러 회전에 못 쓴다 |
| **`spring` 컨스트레인트(레거시)** | 가벼움 | 단순 지연만 가능. **길이 구속·각도 제한·체인 전파 제어·감쇠 튜닝**이 없고 안정성이 낮다 |
| **expression 기반 지연** | 가벼움 | 상태가 시간 순서에 의존해 **스크럽 시 꼬인다**. 저장소 내 선례: `A00390_WindTool` v01.07 은 이 문제를 적분 표현식으로 풀었지만, 표현식이 **매 평가마다 start→현재 프레임을 훑어서** 무겁다 |

> [!note] 헤드리스 nucleus 성능은 측정하지 않았다.
> mayapy 배치에서 다이나믹 커브를 만들어 재생해 봤으나, 출력 커브 끝점이 **루트 이동량과 정확히 일치**해
> (delta = 30.0 = 루트 translateX) 다이나믹스가 실제로 평가되지 않은 것으로 보인다. 따라서 배치에서 나온
> 재생 시간은 **의미 없는 수치라 인용하지 않는다.** 위 표의 근거는 성능 수치가 아니라 **구조적 제약**
> (순차 재생 의존 / 스크럽 불가 / 별도 캐시·베이크 단계)이며, 이는 문서화된 nucleus 동작이다.

**공통 결론**: 시뮬 솔버는 "상태를 시간 순으로 쌓는" 물건이라 **애니메이터의 반복 튜닝 루프와 상극**이다.
반대로 우리가 만들 솔버는 **결정적(deterministic)**이고 **전 구간 일괄 계산**이라, 스크럽/되감기/파라미터
변경이 전부 즉시 반영된다.

---

## 3. 알고리즘 — KawaiiPhysics 식 경량 솔버

KawaiiPhysics 는 물리 엔진이 아니라 **본 위치에 대한 질량-스프링 근사**다. 같은 모델을 그대로 쓴다.
(파라미터 이름도 KWI 와 맞춘다 → 4장)

### 3.1 프레임 루프

입력: 체인 노드 `c0..cn`(애니메이터가 이미 FK 로 애니메이션한 상태), 드라이버 = `c0` 의 부모.

```text
for f in frames:
    T[i] ← 프레임 f 에서의 "강체 FK" 월드 위치      # 원본 애니 그대로일 때의 위치 = 목표
    for i in 1..n:                                  # i=0(루트)은 100% 드라이버를 따른다
        v      = (P[i] - P_prev[i]) * (1 - Damping[i])          # 베를레 속도 + 감쇠
        P'[i]  = P[i] + v + (T[i] - P[i]) * Stiffness[i]        # 원래 자리로 당기는 스프링
                     + Gravity + Wind                            # 외력(선택)
        P'[i]  = lerp(P'[i], T[i], WorldDamping)                # 월드 감쇠(KWI WorldDampingLocation)
        P'[i]  = P'[i-1] + normalize(P'[i] - P'[i-1]) * Len[i]  # 길이 구속(뼈 늘어남 방지)
        P'[i]  = clampAngle(P'[i], T 방향, LimitAngle[i])       # 각도 제한
        P'[i]  = resolveCollision(P'[i], colliders)             # 선택
    P_prev, P = P, P'
    회전 재구성 → 키 값 저장
```

**"멀수록 남으려 한다"** 는 요구는 `Stiffness[i]` / `Damping[i]` 에 **root→tip 폴오프 커브**를 곱해서
만든다. 루트 쪽 = 높은 stiffness(부모를 잘 따라감), 팁 쪽 = 낮은 stiffness(제자리에 남으려 함).
이게 KWI 의 커브 파라미터와 동일한 개념이고, 사용자가 말한 물리 성질 그 자체다.

### 3.2 위치 → 회전 재구성 (핵심)

시뮬은 **점**으로 풀고, 결과는 **컨트롤러 회전 키**여야 한다. root→tip 순서로:

```text
rest_dir = normalize(T[i+1] - T[i])          # 원본(강체) 방향
sim_dir  = normalize(P[i+1] - P[i])          # 시뮬 방향
q_swing  = quaternion_from_to(rest_dir, sim_dir)      # 순수 스윙 (트위스트 없음)
world_new = q_swing * world_orig[i]
local_new = inverse(parent_world_new) * world_new     # 부모는 이미 갱신됨
rotate[i] = euler(local_new, 컨트롤러의 rotateOrder)
```

- `q_swing` 이 **순수 스윙**이라 원본 애니의 **트위스트(롤)가 보존**된다.
- 길이 구속 덕분에 `|P[i+1]-P[i]| = Len[i]` 가 항상 성립하므로, i 를 회전시키면 자식이 **정확히**
  `P[i+1]` 에 놓인다 → 점 시뮬과 회전 결과가 **모순 없이 일치**한다. (이 성질이 없으면 체인이 벌어진다.)

### 3.3 결정적/무상태 (중요)

- 항상 **구간 시작 프레임에서 `P = T`, 속도 0** 으로 시작 → 같은 입력이면 항상 같은 결과.
- 프레임 단위 dt 는 **씬 FPS 로 정규화**해 24/30/60fps 에서 같은 느낌이 나오게 한다.
- 서브스텝(`Substeps`) 옵션으로 빠른 모션에서의 안정성 확보(계산량이 워낙 싸서 부담 없음).

---

## 4. 파라미터 (KawaiiPhysics 매핑)

이름과 의미를 UE KWI 와 맞춘다 → **마야에서 튠 → 그 값을 그대로 UE 로 이관**할 수 있고,
저장소의 `A00080_KWI_creator_V03`(UE KWI 노드 텍스트 생성기)와 자연스럽게 이어진다.

| 툴 UI | KWI 대응 | 의미 |
|-------|----------|------|
| **Stiffness** | `Stiffness` | 원래(FK) 자리로 돌아가려는 힘. 높을수록 부모를 잘 따라감 |
| **Damping** | `Damping` | 속도 감쇠. 높을수록 빨리 멎음 |
| **World Damping** | `WorldDampingLocation` | 월드 기준으로 결과를 원본 쪽으로 끌어당기는 비율 |
| **Falloff (root→tip)** | KWI 의 각 커브 | 체인 위치별 Stiffness/Damping 배율 — **관성 표현의 핵심** |
| **Limit Angle** | `LimitAngle` | 원본 방향에서 벗어날 수 있는 최대 각 |
| **Gravity** | `Gravity` | 중력 벡터(월드) |
| **Wind** | `WindStrength` 등 | 선택. `A00390_WindTool` 의 싸인 파형을 외력으로 주입 가능 |
| **Collision (Sphere/Capsule/Plane)** | `SphericalLimits` / `CapsuleLimits` / `PlanarLimits` | 선택(후반 단계) |
| **Blend %** | — | 결과 강도. `lerp(T, P, blend)` — 0 이면 원본과 동일 |

---

## 5. 아키텍처

`A00390_WindTool` / `A00400_CurveTool` 과 동일한 **arch (B) in-Maya PySide** 구조를 클론한다.

```
JUN_All/tools/A00410_ChainPhysics/
├── __init__.py                  # from .launch import run
├── launch.py                    # MainWindow + ThemeManager("coral_dark")
├── __dragDrop_A00410.py         # 셸프 설치 (툴별 고유 파일명 규칙)
├── app/
│   ├── config/version.py        # VERSION / LAST_UPDATE
│   ├── core/
│   │   ├── chain_solver.py      # ★ DCC 비의존 순수 파이썬 솔버 (벡터/쿼터니언 포함)
│   │   ├── scene_sampler.py     # 체인 수집 · 프레임별 드라이버/로컬 행렬 샘플링
│   │   └── bake_manager.py      # 애님 레이어 생성 · MFnAnimCurve 벌크 기록 · 프리뷰 갱신
│   └── ui/main_window.py        # UI 전용
└── CHANGELOG.md
```

- **`chain_solver.py` 는 maya 임포트 없이** 테스트 가능하게 둔다(헤드리스 유닛 테스트 용이).
- **Framework 재사용**: `JUN_mod_tsl_qt`(체인 리스트 — 이번에 추가한 **`Order` 체크박스**로 선택 순서 지정
  가능), `JUN_mod_timeRange_qt`(Start/End), `Framework.core.maya_undo.undo_chunk`, coral_dark 테마.

### 5.1 성능 설계 (측정에 근거)

- 드라이버 **루트 하나만** `getAttr -time` 으로 샘플링한다(300프레임 **0.013 s**).
  체인 전 노드를 프레임마다 `getAttr -time` 하면 **0.374 s** 로 **약 29배** 비싸진다 — 이 경로는 피한다.
- 체인에 **자체 FK 애니가 있는 경우**(애니메이터가 체인도 직접 포즈)에는 각 노드의 로컬 애님커브를
  `MFnAnimCurve.evaluate()` 로 직접 평가한다(DG 평가 없이 커브만 읽음).
- 키 기록은 **`MFnAnimCurve.addKeys` 벌크 고정**(setKeyframe 대비 74배).

---

## 6. 실시간 미리보기 설계

**scriptJob 으로 매 프레임 시뮬을 돌리지 않는다.** (되감기·재생속도·언두 문제를 전부 떠안게 된다.)

대신:

1. 파라미터가 바뀌면 **구간 전체를 다시 풀어(≈30ms) 프리뷰 애님 레이어에 통째로 다시 굽는다.**
2. 재생/스크럽은 **평범한 애님커브 재생** → 씬 부하 0, 되감기·역재생 전부 정상.
3. 슬라이더 드래그 중에는 **디바운스(예: 30~50ms)** 로 재계산을 묶고, 놓는 순간 확정
   (`A00380_MeshTool` / `A00110` 의 **settle 커밋 모델** 재사용 — 제스처 1회 = Ctrl+Z 1회).
4. 프리뷰 중 언두 폭주 방지: 프리뷰 갱신은 언두 큐에 남기지 않고, **커밋 시 한 번만** `undo_chunk` 로 묶는다.
   (`stateWithoutFlush` 관련 함정은 `A00380` 경험 참고.)

> 긴 구간(예: 2000프레임 × 체인 5개)에서 30ms 가 200ms 로 늘면 디바운스만으로는 뻑뻑해질 수 있다.
> 그때는 **드래그 중에는 현재 프레임 주변 ±N 프레임만** 풀고, 놓을 때 전 구간을 푸는 2단 전략을 쓴다.

---

## 7. 출력

| 모드 | 설명 |
|------|------|
| **Additive 애님 레이어** (기본 권장) | 원본 애니를 건드리지 않고 `<chain>_secondary_LYR` 에 차분만 기록. 레이어 웨이트로 **강도 조절**, 마음에 안 들면 레이어만 삭제 |
| **키 직접 굽기 (Replace)** | 컨트롤러 rotate 에 직접 기록(최종 확정용) |
| **프리뷰 레이어** | 미리보기 전용. Apply 시 위 두 모드 중 하나로 확정, Cancel 시 삭제 |

**검증됨**: additive 레이어(`animLayer -override false`) 생성 → 대상 어트리뷰트 추가 → 레이어 커브에
`MFnAnimCurve.addKeys` 로 **300키 벌크 기록 0.0001 s**, 베이스 애니와 합성값 정상
(`f50 = 55.78` = 베이스 + 애디티브). 레이어 커브는 `cmds.animLayer(layer, q=True, animCurves=True)` 로 얻는다.

> [!warning] 애님 레이어 함정: `cmds.animLayer(q=True, selected=True)` 는 **레이어 인자 없이 못 쓴다**.
> `cmds.ls(type="animLayer")` 를 순회해 확인할 것(저장소 기존 메모 사항).

부가 옵션: **Key Reduction**(허용오차 기반 키 감축 — 게임 익스포트용), **Pre-roll/Settle**(구간 앞
N프레임을 미리 돌려 시작 튐 제거), **Bake Step**(1/2프레임 간격).

---

## 8. UI 초안

```
┌ Chain Physics ────────────────────────────┐
│ Help                                      │
│ [ Select Chain Root(s) ]                  │
│ Chains          [x] Order    Number: N    │  ← 공용 TSL (Order = 선택 순서 유지)
│ ┌───────────────────────────────────────┐ │
│ │ ctrl_hair_01                          │ │
│ └───────────────────────────────────────┘ │
│ [Add][Del][Up][Down]                      │
│ ( ) Chain (리스트 그대로)  (o) Root(계층 자동) │  ← A00390 방식 재사용
│ ┌ Range ────────────────────────────────┐ │
│ │ Start [1] End [300] [Get Current][Sel]│ │  ← 공용 timeRange 위젯
│ └───────────────────────────────────────┘ │
│ ┌ Physics ──────────────────────────────┐ │
│ │ Stiffness    ──●───────  0.35         │ │
│ │ Damping      ────●─────  0.12         │ │
│ │ World Damp.  ●─────────  0.00         │ │
│ │ Falloff      root ──●── tip           │ │
│ │ Limit Angle  [ 45 ]°   Gravity [0,-1,0]│ │
│ │ Blend        ────────●─  100 %        │ │
│ └───────────────────────────────────────┘ │
│ [x] Live Preview            [ Reset ]     │
│ Output: (o) Additive Layer ( ) Bake Keys  │
│ [            Apply             ]          │
│ [ log ... ]                               │
└───────────────────────────────────────────┘
```

---

## 9. 개발 단계

| 버전 | 범위 |
|------|------|
| **v01.00** | 단일 체인 / 루트 구동 / Stiffness·Damping·Falloff·Blend / 전 구간 solve → 프리뷰 레이어 / Additive 베이크 |
| v01.01 | Limit Angle, Gravity, World Damping, Substeps |
| v01.02 | 다중 체인, **Bone Root 모드**(계층 자동 수집, `A00390` BFS 방식 이식) |
| v01.03 | 콜라이더(Sphere / Capsule / Plane) |
| v01.04 | Key Reduction, Pre-roll/Settle, Bake Step |
| v01.05 | **KWI 파라미터 내보내기** — `A00080_KWI_creator_V03` 로 값 전달(마야 프리뷰 = UE 세팅) |

---

## 10. 검증 계획 (mayapy 헤드리스)

솔버가 `maya` 비의존이라 대부분 순수 유닛 테스트로 검증 가능하다.

1. **관성 특성**: 루트를 급가속시켰을 때 **팁의 피크 프레임이 루트보다 늦다**(지연 프레임 수를 수치로 확인).
   그리고 **팁으로 갈수록 지연이 커진다** — 사용자가 요구한 성질의 직접 검증.
2. **길이 보존**: 모든 프레임에서 `|P[i+1]-P[i]| == Len[i]` (오차 1e-6).
3. **감쇠 수렴**: 루트 정지 후 진폭이 단조 감소하고 N프레임 내 rest 로 수렴.
4. **무회귀**: `Blend=0` 또는 `Stiffness=1, Damping=0` → 원본 애니와 동일(오차 1e-6).
5. **FPS 불변**: 24/30/60fps 에서 같은 초 시점의 결과가 유사(정규화 확인).
6. **레이어 합성**: additive 레이어 웨이트 0/0.5/1 에서 합성값 검증(이미 경로 확인됨).
7. **성능 회귀**: 20본 × 300프레임 파이프라인 **≤ 50 ms** 유지.
8. **트위스트 보존**: 원본에 롤 애니가 있는 체인에서 롤 값이 유지되는지.

> Qt UI 는 mayapy 에서 띄울 수 없다(`maya.standalone` 이 `QGuiApplication` 을 선점 → `QWidget` 생성 실패).
> UI 배선은 stub `maya.cmds` + 시스템 파이썬 PySide6 로 테스트한다(이번 TSL 작업에서 쓴 방식).

---

## 11. 리스크 / 열린 결정

| 항목 | 내용 | 대응 |
|------|------|------|
| 오일러 연속성 | 회전 재구성 후 짐벌/±180 점프로 커브가 튈 수 있음 | 키 기록 전 **각도 언랩(unwind)** 적용, `rotateOrder` 존중 |
| 컨트롤러 계층 | 컨스트레인트/스케일/기존 애님 레이어가 걸린 컨트롤러 | 로컬 변환은 **부모 월드행렬 역행렬**로 계산, 스케일은 정규화 후 처리 |
| 대상 선택 | **컨트롤러**에 굽는가, **조인트**에 굽는가 | 기본 = 선택한 **컨트롤러**. 조인트 직접 모드는 옵션으로 |
| 긴 구간 | 2000프레임 × 다중 체인에서 프리뷰 지연 | 6장의 2단 전략(주변 프레임 우선) |
| 툴 이름 | `A00410_ChainPhysics` (대안: `A00410_SecondaryMotion`) | **결정 필요** |
| A00390 과의 관계 | WindTool = 입력 무관 절차적 바람 / 본 툴 = 부모 애니 반응형 관성 | 별도 툴로 두되, Wind 를 **외력 입력**으로 받는 연동 지점만 남김 |

---

## 12. 요약

- 마야 시뮬 솔버는 **성능 이전에 작업 흐름(순차 재생·스크럽 불가)** 때문에 부적합하다.
- KawaiiPhysics 와 같은 **위치기반 스프링 근사**를 순수 파이썬으로 구현하면
  **20본 × 300프레임을 6ms** 에 푼다.
- 전 구간 재계산 + 벌크 키 기록이 **≈30ms** 이므로, **파라미터를 만질 때마다 전 구간을 다시 구워도**
  실시간이고, 재생은 그냥 커브 재생이라 씬이 무겁지 않다 → **런타임 시뮬 없는 "실시간 피직스"**.
- 결과는 **additive 애님 레이어**로 나가서 원본 애니를 보존하고 강도 조절이 가능하다.
- 파라미터를 **KWI 와 동일하게** 두어 마야 프리뷰 값을 언리얼로 이관하는 길(`A00080` 연계)까지 연결한다.
