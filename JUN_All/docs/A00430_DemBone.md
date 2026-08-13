# A00430_DemBone — DemBone (사용 안내)

EA SEED 의 **Dem Bones**(*Smooth Skinning Decomposition with Rigid Bones*, Le & Deng 2012)를
마야로 이식한 툴이다. **애니메이션되는 메시(알렘빅 캐시 등)**와 **조인트**를 비교해,
그 움직임을 가장 잘 재현하는 **스킨 웨이트**나 **본 애니메이션**을 풀어 준다.

- 버전: `v01.03` (`app/config/version.py`) — Solve Weights / Solve Transforms / Refine / **Decompose** 4모드
- 위치: `JUN_All/tools/A00430_DemBone`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴. 로직은 numpy(솔버) + `maya.cmds`(취득·적용)
- **원본 코드에 의존하지 않는다.** 알고리즘만 읽고 파이썬으로 새로 작성했으며, 런타임에
  `ref/` 를 읽거나 import 하는 곳이 없다. `ref/` 는 참고용 로컬 사본이라 **git 추적 제외**
  (`.gitignore`). 원본: <https://github.com/electronicarts/dem-bones>
- 계획서: [A00430_DemBone_plan.md](plans/A00430_DemBone_plan.md) ·
  v01.03 준비: [A00430_DemBone_v0103_ref_requirements.md](plans/A00430_DemBone_v0103_ref_requirements.md)

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00430.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`DemBone`** 버튼 설치.

### 코드로 실행
```python
import tools.A00430_DemBone as A00430_DemBone
A00430_DemBone.run(True)     # True 면 DEV_MODE 에서 리로드
```

**numpy 가 필요하다**(Maya 2022+ 기본 내장). 없으면 창은 뜨되 기능이 잠기고 이유를 로그에 적는다.

---

## 2. 무엇을 하는 툴인가

LBS(Linear Blend Skinning) 는 이렇게 생겼다.

```
버텍스 위치(프레임 k) ≈ Σ_j  웨이트(j, i) × 본 j 의 변환(k) × rest 위치(i)
```

여기서 **모르는 것을 채워 넣는 것**이 이 툴이 하는 일의 전부다.

| 아는 것 | 모르는 것 | 탭 |
|---------|-----------|-----|
| 캐시 + 조인트 애니메이션 | **웨이트** | Solve Weights |
| 캐시 + 웨이트 | **본 애니메이션** | Solve Transforms |
| 대충 아는 둘 다 | 둘 다 (더 정확히) | Refine |
| **캐시만** | 웨이트 + 본 애님 + **조인트 자체** | **Decompose** |

> 원본 커맨드라인의 `--nTransIters=0` / `--nWeightsIters=0` / 기본 `compute()` / `-b N` 에 각각 대응한다.

---

## 3. 화면 구성

```
┌ Input ────────────────────────────────────────────┐
│ Cache   [ ............ ] << Sel [Import .abc]     │  ← 애니메이션되는 메시
│ Rest    [ ............ ] << Sel                   │  ← 비우면 Rest Frame 의 캐시
│ Target  [ ............ ] << Sel                   │  ← 웨이트를 칠할 메시
│ Start [  ] End [  ]   Rest Frame [  ]  Stride [ ] │
└───────────────────────────────────────────────────┘
┌ Joints (TSL) ─────────────────────────────────────┐
│  ... Select Joints / Add / Del / Up / Down /      │
│      Sort / Hierarchy                             │
└───────────────────────────────────────────────────┘
[ Solve Weights | Solve Transforms | Refine | Decompose | Options ]
[■■■■■■■□□□□□□□ 52% - weights 2/3 ]
[         Solve Weights          ] [ Cancel ]
[ log ............................................ ]
```

입력(위쪽 Input + Joints)은 **모든 모드가 공유**한다. 같은 데이터로 모드만 바꿔 돌리는 일이 잦아서다.
(단 **Decompose 는 조인트를 입력으로 받지 않는다** — Joints 목록을 무시한다.)

### 입력 항목

| 항목 | 설명 |
|------|------|
| **Cache** | 프레임마다 변형되는 메시. 알렘빅 캐시가 대표적이고, 씬 안의 어떤 애니메이션 메시든 된다. `Import .abc` 로 파일을 바로 임포트할 수 있다(임포트하면 프레임 범위도 알렘빅 노드에서 자동으로 채운다). |
| **Rest** | rest(바인드) 포즈 메시. 비우면 **Rest Frame 시점의 캐시**를 쓴다. |
| **Target** | 웨이트를 칠할 실제 리깅 메시. 비우면 Rest 메시. |
| **Start / End** | 샘플할 프레임 구간. 포즈가 다양할수록 해가 안정된다. |
| **Rest Frame** | 조인트가 **바인드 포즈**에 있는 프레임. 여기서 rest 메시와 바인드 행렬을 읽는다. |
| **Stride** | N 프레임마다 샘플. 캐시가 길 때 속도를 위해 올린다. |
| **Joints** | 순서가 곧 본 인덱스. `Hierarchy` 버튼은 선택한 조인트의 하위까지 한 번에 담는다. |

세 메시는 **버텍스 수가 같아야 한다**(토폴로지 동일). 다르면 실행 전에 걸러서 알려준다.

---

## 4. 탭별 사용법

### 4-1. Solve Weights — 캐시 + 조인트 애님 → 웨이트

가장 많이 쓰는 모드다. 조인트에 이미 애니메이션이 있고, 그 애니메이션이 돌 때 캐시처럼 움직이려면
웨이트가 어때야 하는지를 푼다.

1. Cache / Rest / Target / Joints / 프레임 설정.
2. (선택) `Start from existing weights` — 지금 스킨을 시작점으로.
3. (선택) `Preserve` (0~1) — 기존 웨이트를 얼마나 지킬지. `From Selected Verts` 로 **버텍스를
   골라 그 부분만** 지킬 수 있다(원본의 버텍스 컬러 소프트락에 해당).
4. `Solve Weights`.

결과는 Target 의 skinCluster 에 쓰인다. skinCluster 가 없으면 **Rest Frame 에서** 새로 만든다
(바인드 포즈가 그 시점의 조인트 위치로 잡히기 때문).

### 4-2. Solve Transforms — 캐시 + 웨이트 → 본 애니메이션

Target 에 **이미 스킨이 있어야** 한다. 그 웨이트를 고정하고, 캐시를 가장 잘 따라가는 본 변환을 풀어
조인트에 **키로 굽는다**.

- `Translate` / `Rotate` — 키를 걸 채널.
- `Euler Filter` — 구운 뒤 회전 커브에 오일러 필터(플립 방지). 기본 ON.
- `Lock Selected Joints` — 락 걸린 조인트는 **풀지도, 다시 굽지도 않는다**. 원본의 `demLock` 에 해당.
  기존 애니메이션이 그대로 보존된다.

### 4-3. Refine — 둘 다 최적화

트랜스폼 갱신 ↔ 웨이트 갱신을 번갈아 돌린다. 오차가 `Tolerance` 비율만큼도 안 줄어드는 일이
`Patience` 번 연속이면 멈춘다(원본 커맨드라인과 같은 규칙). 반복마다 RMSE 가 로그에 찍힌다.

Solve Weights 탭의 버텍스 락과 Solve Transforms 탭의 조인트 락이 여기에도 적용된다.

### 4-4. Decompose — 캐시만으로 스켈레톤까지 만들기

조인트가 **아예 없어도** 된다. 메시를 본 단위로 클러스터링해 조인트를 만들고, 바인드하고,
애니메이션까지 굽는다. 후디니 시뮬이나 블렌드셰이프 결과를 **게임 엔진에 넣을 수 있는 LBS 리그**로
바꾸는 용도다(원본 `-b N`).

| 항목 | 기본 | 의미 |
|------|------|------|
| Target Bones | 20 | 목표 본 개수. **정확히 그 개수가 나오지는 않는다** — 분할·솎아내기가 최종 개수를 정한다(원본도 같다) |
| Init Iterations | 5 | 분할 후 클러스터를 다듬는 횟수 |
| Init Frames | 30 | **클러스터링에 쓸 프레임 수**(구간에 고르게 분산). 클러스터 구조를 잡는 데는 포즈의 다양성만 있으면 되는데 이 단계 비용이 `버텍스 × 본 × 프레임` 이라 여기서만 솎는다. 이후 단계는 전체 프레임을 쓴다 |
| Joint Prefix | demBone | 조인트 이름이 `<prefix>_00`, `_01` … 로 생성된다 |
| Parent every joint under one root | off | 켜면 **혼자서 메시 전체를 가장 잘 설명하는 본**을 루트로 삼고 나머지를 그 밑에 넣는다(원본 `bindUpdate=2`) |

Refine 탭의 Global Iterations / Tolerance / Patience 가 여기에도 적용된다(0 이면 정제 생략).

절차: 클러스터링 → 본 변환 → 교대 최적화 → 조인트 생성 → 바인드 → 키 베이크.
`Apply result to the scene` 을 끄면 씬을 건드리지 않고 **몇 개의 본으로 얼마나 맞출 수 있는지만**
확인할 수 있다(본 개수를 정하기 전에 유용하다).

### 4-5. Options — 공용 파라미터

| 항목 | 기본 | 의미 |
|------|------|------|
| Max Influences | 8 | 버텍스당 최대 조인트 수 (원본 `nnz`) |
| **Smoothness** | 1e-4 | **결과 품질을 좌우하는 핵심 노브**. 웨이트가 지저분하면 올리고, 더 정확히 붙이려면 내린다 |
| Smooth Step | 1.0 | 라플라시안 스무딩 세기 |
| Smooth Iterations | 20 | 스무딩 반복(자코비) 횟수 |
| Weight Iterations | 3 | 웨이트 갱신 반복 |
| Prune Below | 0.0 | 이 값 이하 웨이트는 버리고 재정규화 |
| Transform Iterations | 5 | 본 갱신 반복 |
| Translation Affinity | 10.0 | 웨이트가 높은 **중심부**가 본 변환을 더 강하게 결정하게 한다. 웨이트가 적은 본이 튀는 것을 막지만 정확도를 조금 손해 본다. **가장 정확한 핏을 원하면 0** |
| Affinity p-Norm | 4.0 | 위 가중의 p 제곱 |
| Vertex Chunk | 2000 | 한 번에 처리할 버텍스 수(메모리 조절) |
| Apply result to the scene | ON | 끄면 **드라이런** — 씬을 건드리지 않고 오차만 리포트 |

---

## 5. 결과 읽는 법

실행이 끝나면 로그에 이렇게 찍힌다.

```
20100 verts | 40 joints | 100 frames
RMSE 0.021180  (0.1877% of model size)
influences per vertex: avg 5.11, max 8
done in 17.1s
```

- **RMSE**: 캐시와 재구성 결과의 평균 오차(월드 거리). 절대값은 씬 스케일에 좌우되므로
  **"모델 크기의 몇 %"** 쪽을 본다.
- 경험적으로 **0.5% 이하면 좋음**, **1% 를 넘으면 경고**가 함께 뜬다. 오차가 큰 이유는 보통 셋 중 하나다:
  1. 캐시가 **LBS 로 표현 불가능**한 변형(천 시뮬, 근육, 볼륨 보존)을 담고 있다 — 원리상 못 맞춘다.
  2. 조인트나 프레임 범위가 캐시와 안 맞는다.
  3. Rest Frame 이 실제 바인드 포즈가 아니다.

---

## 6. 성능 (실측, Maya 2024 헤드리스)

| 규모 | Solve Weights | Solve Transforms | Decompose (본 20개 생성) |
|------|---------------|------------------|--------------------------|
| 800 버텍스 / 30 프레임 | 0.2s | 0.3s | 0.7s (본 8개, 오차 0.99%) |
| **20,100 버텍스 / 40 조인트 / 100 프레임** | **16.5s** (오차 0.19%) | **3.0s** | **32.6s** (오차 1.02%) |

- 씬 취득(메시 + 조인트 샘플링)은 **프레임당 약 12ms** 로 병목이 아니다.
- 가장 무거운 단계는 **후보 본 선별**(`O(nV × nB × nF)`). 조인트가 100개를 넘거나 캐시가 길면
  `Stride` 를 올려 프레임을 솎는 것이 가장 효과적이다.
- 진행률 표시 + `Cancel` 이 있고, 취소하면 **씬을 건드리지 않은 상태**로 끝난다.

---

## 7. 원본과 다른 점 (의도적)

| 항목 | 원본 (C++ / Eigen) | 이 툴 |
|------|--------------------|-------|
| 웨이트 스무딩 | 희소 `(I + step·L)` 를 **SparseLU 직접 풀이** | scipy 가 없어 **자코비 반복**(수렴 인자 `step/(1+step) < 1` 로 항상 수렴, 20회면 사실상 동일) |
| 후보 본 재선별 | 매 반복 | 첫 회는 강체 오차, 이후는 스무딩 웨이트 기준 |
| 다중 subject(`nS`) | 여러 rest/시퀀스 동시 | **단일 subject 만** |
| 병렬화 | OpenMP | numpy 벡터화(버텍스 루프만 파이썬) |
| 로컬 회전 복원 | `DemBonesExt::computeRTB` + 오일러 전수탐색 | `cmds.xform(ws=True, matrix=)` + **Euler Filter** (jointOrient·부모공간을 마야가 처리) |
| 본 자체 생성 | LBG-VQ 클러스터링 (`-b N`) | 구현 — 다만 **분할 씨앗 크기**와 **라벨 확산 우선순위**를 바꿔야 실제로 동작했다(§9) |
| 초기화 비용 절감 | 없음(C++/OpenMP) | 클러스터링 단계만 **프레임을 솎아** 쓴다(`Init Frames`) |

행렬 규약도 다르다. 원본은 Eigen 열벡터(`M·p`), 이 툴은 **마야 행벡터(`p·M`)** 로 통일했다.
상대 변환의 정의는 같다: 원본 `EvaluateGlobalTransform(t) × bind⁻¹` = 이 툴 `bindPreMatrix[j] @ worldMatrix(t)`.

---

## 8. 구조

```
tools/A00430_DemBone/
├── __dragDrop_A00430.py / launch.py / __init__.py
├── app/
│   ├── config/version.py
│   ├── core/                      ← UI 비의존
│   │   │  (numpy 만 — mayapy 헤드리스로 검증 가능)
│   │   ├── convex_ls.py           # NNLS + 합=1 (active set)      ← ConvexLS.h
│   │   ├── laplacian.py           # 시퀀스 기반 엣지 가중 + 스무딩  ← DemBones.h:774
│   │   ├── solver_common.py       # 규약·공용 수식·진행률·RMSE
│   │   ├── solver_weights.py      # 웨이트 솔브                    ← DemBones.h:276
│   │   ├── solver_transforms.py   # 본 솔브 (Kabsch/SVD)           ← DemBones.h:237
│   │   ├── solver_refine.py       # 교대 최적화                    ← DemBones.h:344
│   │   │  (maya.cmds 의존)
│   │   ├── mesh_utils.py          # 셰이프 확정·포인트·토폴로지
│   │   ├── scene_sampler.py       # 씬 → U / V / M
│   │   ├── skin_writer.py         # 웨이트 읽기/쓰기
│   │   ├── joint_writer.py        # 본 변환 → 조인트 키
│   │   ├── alembic_cache.py       # .abc 임포트
│   │   └── dembone_manager.py     # 검증 → 취득 → 솔브 → 적용
│   └── ui/main_window.py
└── ref/                           # 원본 Dem Bones (읽기 전용)
```

`app/core/__init__.py` 는 **일부러 아무것도 import 하지 않는다** — 솔버(numpy 전용)와 씬 I/O(maya 의존)의
경계를 지키기 위해서다. 덕분에 솔버는 마야 없이 단위 검증할 수 있다.

---

## 9. 검증

`mayapy` 헤드리스로 5벌을 돌렸고 전부 통과한다. **마야 실기(GUI) 동작도 확인됨**(2026-08-13, 4개 모드).

1. **순수 numpy** (17항목): ConvexLS 제약 만족·알려진 해 복원, 웨이트/트랜스폼/Refine 왕복,
   본의 **강체성**(직교 오차 1.6e-15, det=1), 소프트 락, 취소.
2. **클러스터 초기화** (20항목): 인접 구조, 라벨 확산이 오차를 낮추는지, 목표 개수 도달,
   **클러스터가 메시 위에서 끊기지 않는지**(연결 성분 검사), 본이 많을수록 오차가 주는지.
3. **마야 통합** (22항목): 검증 메시지, skinCluster 생성, **씬에서 실제로 캐시를 따라가는지**
   (버텍스 최대 오차 0.025 / 모델 크기 3.19), 키 베이크, 락 조인트 커브 불변, 드라이런이 씬을
   안 건드리는지, Stride.
4. **Decompose** (18항목): 조인트 없이 검증 통과, 조인트 생성/이름/개수, **생성된 리그가 씬에서
   캐시를 따라가는지**, 조인트가 메시 범위 안에 고르게 놓이는지, 단일 루트, 드라이런.
5. **UI** (16항목): 창 생성, 탭↔버튼 연동, 슬롯 동작, 설정 조립, 잘못된 입력이 예외 대신 로그로.

검증 중 잡은 실제 버그 넷:
- **본 솔브의 질량 불일치** — 무게중심을 `uuT[j,j]` 의 질량으로 나누고 있었다. 원본은 `qpT(3,3)`,
  즉 **공분산 행렬 자신의 질량**을 쓴다. 웨이트 합이 1이고 affinity 가 0이면 우연히 같은 값이라
  평소엔 멀쩡했지만, Translation Affinity 를 켜면 질량이 달라져 결과가 무너졌다(오차 460% → 1.4%).
  → 공분산을 4×3 이 아니라 **4×4 로 들고 다니게** 고쳤다.
- **락 조인트에도 키를 굽던 것** — 락은 "풀지 않는다"이지 "다시 구워도 된다"가 아니다.
  샘플 프레임 위로만 리샘플되어 사이 키가 사라졌다. → 베이크에서 제외.
- **분할 씨앗이 너무 작아 새 본이 죽던 것**(v01.03) — 원본은 새 클러스터를 시드의 1링(4~5 버텍스)만으로
  심는다. 그 몇 개로 맞춘 강체는 표본이 적어 오차가 크고, 바로 다음 라벨 확산에서 옆의 큰 클러스터에
  통째로 먹힌 뒤 솎여 사라진다. **20,100 버텍스에 본 20개를 요청해도 2개에서 멈췄다.**
  → 씨앗을 클러스터 크기에 비례(1/8, 최소 8개)해 키웠다.
- **라벨 확산이 한 본만 편들던 것**(v01.03) — 우선순위를 절대 오차로 두면 힙이 하나뿐이라 오차가
  작은 본이 먼저 전부 훑고 지나가고, 뒤늦게 차례가 온 본은 **이웃이 이미 다 점령돼 확장할 곳이 없다**.
  4개로 쪼갠 클러스터가 매 라운드 `[1, 1, 431, 359]` 로 무너졌다. → 우선순위를 **"최선의 본 대비
  얼마나 나쁜가"(advantage)** 로 바꿨다. 주인은 0 에 가까운 값으로 자기 자리를 잡고, 남의 영역으로
  넘어가려는 본은 값이 튀어 멈춘다. 연결성을 따라 자라는 성질은 그대로다.

---

## 10. 라이선스 / 출처

- 원본: **Dem Bones © 2019 Electronic Arts, BSD 3-Clause** (`ref/LICENSE.md`).
- 논문:
  - Le & Deng, *Smooth Skinning Decomposition with Rigid Bones*, ACM TOG 31(6), SIGGRAPH Asia 2012.
  - Le & Deng, *Robust and Accurate Skeletal Rigging from Mesh Sequences*, ACM TOG 33(4), 2014. (웨이트 스무딩)
- `ref/`(사전 컴파일 exe 포함)는 배포 대상이 아니다.
