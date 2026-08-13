---
title: A00430_DemBone — 작업 계획서
aliases: [A00430, DemBone, SkinningDecomposition]
tags: [plan, maya-python, skinning, A00430]
updated: 2026-08-13
---

# A00430_DemBone — 작업 계획서 (ref 분석 + 마야 이식 설계)

> **상태: ✅ v01.03 까지 구현 완료** (2026-08-13). 이 문서는 `ref/`(EA Dem Bones 1.2.1) 를 읽고
> 분석한 결과와 마야 이식 타당성 실측, 그리고 구현 계획을 담는다. 작성: 2026-08-13
>
> - 사용 안내(구현 결과): [A00430_DemBone.md](../A00430_DemBone.md)
> - v01.03(조인트 자체 생성) 준비: [A00430_DemBone_v0103_ref_requirements.md](A00430_DemBone_v0103_ref_requirements.md)
>
> 실측은 전부 `Maya2024/bin/mayapy.exe` 헤드리스로 돌린 값이다(추정치 아님).

---

## 0. 요약 (읽는 시간이 1분이라면)

- `ref/` 는 **EA SEED 의 Dem Bones 1.2.1** — *Smooth Skinning Decomposition with Rigid Bones*
  (Le & Deng, SIGGRAPH Asia 2012) 의 공식 구현. C++ 헤더 온리 라이브러리 + FBX/Alembic 커맨드라인 툴.
- **사용자의 기억은 정확하다.** "알렘빅 캐시 + 조인트 애니메이션을 비교해서 웨이트를 칠한다"는
  이 툴의 **여러 모드 중 하나**(`--nTransIters=0`, `run.bat` 의 *"Solve skinning weights from input
  meshes sequence and input bone transformations"*)다. 다만 원본은 그보다 넓어서, 웨이트만 아니라
  **본 트랜스폼**도 풀고, 심지어 **본 자체를 없는 상태에서 생성**할 수도 있다(§1.6).
- **마야 이식은 가능하다.** 우리가 필요한 핵심 경로(웨이트 솔브)는 scipy 없이 **numpy 만으로**
  구현 가능하며, 실측으로 **20,000 버텍스 / 40 조인트 / 100 프레임 → 약 12초**가 나왔다(§2.3).
  데이터 취득(캐시 샘플링 + 조인트 행렬 수집)은 **프레임당 약 12ms**로 무시할 수준이다(§2.4).
- 권장 전략: **네이티브 파이썬(numpy) 재구현**. `bin/Windows/DemBones.exe` 래핑은 FBX/ABC
  왕복 비용과 이름·계층 훼손 리스크가 커서 **후순위 옵션**으로만 둔다(§3).
- 산출물: `JUN_All/tools/A00430_DemBone/` — 아키텍처 (B) PySide 마야 툴. 3단계로 나눠 구현(§6).

---

## 1. `ref/` 코드 분석

### 1.1 무엇인가 / 구성

```
ref/
├── include/DemBones/        ← 알고리즘 전부가 여기 (헤더 온리, Eigen + OpenMP)
│   ├── DemBones.h           ← 코어 솔버 (29KB) — 이 문서의 §1.3~1.5 가 이 파일이다
│   ├── DemBonesExt.h        ← 계층 스켈레톤/바인드 확장 (로컬 rot/trans 복원)
│   ├── ConvexLS.h           ← 버텍스 1개용 제약 최소자승 솔버 (NNLS + 합=1)
│   ├── Indexing.h           ← Eigen 인덱싱 헬퍼
│   └── MatBlocks.h          ← blk4/rotMat/transVec/vec3 매크로 (행렬 블록 접근)
├── src/command/             ← 커맨드라인 툴 소스 (알고리즘 아님, I/O 만)
│   ├── AbcReader.cpp        ← .abc → 메시 시퀀스 v
│   ├── FbxReader.cpp        ← .fbx → rest u / 웨이트 w / 조인트 m·bind·parent
│   ├── FbxWriter.cpp        ← 결과 → .fbx (스킨클러스터 + 조인트 애님)
│   └── mainCmd.cpp          ← tclap 인자 파싱 + 파이프라인
├── bin/Windows/DemBones.exe ← 사전 컴파일 실행 파일 (1.2.0)
└── data/                    ← 샘플 + `run.bat` (6가지 사용 모드가 그대로 들어있다)
```

라이선스: 소스는 **BSD 3-Clause**(`LICENSE.md`), exe 는 Eigen/tclap/Alembic/FBXSDK/zlib 를 포함(`3RDPARTYLICENSES.md`).
→ 파이썬 재구현물에 **출처·논문 인용 표기 필요**(§9).

### 1.2 수학 모델 — 무엇을 푸는 문제인가

Linear Blend Skinning(LBS) 로 애니메이션 메시를 근사한다. 프레임 `k`, 버텍스 `i` 에서

```
v(k,i)  ≈  Σ_j  w(j,i) · M(k,j) · u(i)
```

| 기호 | 의미 | DemBones 필드 |
|------|------|---------------|
| `u(i)` | rest 포즈 버텍스 위치 (동차좌표) | `u` — `[3·nS, nV]` |
| `v(k,i)` | 프레임 k 의 목표(캐시) 위치 | `v` — `[3·nF, nV]` |
| `w(j,i)` | 본 j 가 버텍스 i 에 주는 웨이트 | `w` — 희소 `[nB, nV]` |
| `M(k,j)` | 본 j 의 **상대(relative)** 4×4 변환 | `m` — `[4·nF, 4·nB]` |

**`m` 의 정의가 이식의 핵심이다.** `DemBones.h:136` 주석 그대로 *"relative — rest 포즈에서
프레임 k 포즈로 가져가는 글로벌 변환"*. `FbxReader.cpp:197` 이 실제 계산식을 보여준다:

```cpp
m[name].blk4(k,0) = EvaluateGlobalTransform(t_k) * bind[name].inverse();
```

즉 `M(k,j) = (조인트 j 의 프레임 k 월드행렬) × (조인트 j 의 바인드 월드행렬)⁻¹`.
→ **마야의 `skinCluster` 와 정확히 같은 식**이다: `matrix[j] × bindPreMatrix[j]` (§4.4).

최소화 대상은 재구성 오차 `Σ_k Σ_i |Σ_j w·M·u − v|²` 이고, 제약은
**`w ≥ 0`, `Σ_j w(j,i) = 1`, 버텍스당 비영(非零) 웨이트 ≤ `nnz`**, 그리고 `M` 은 **강체(rigid)**
(회전+이동만, 스케일/전단 없음).

### 1.3 전체 흐름 — `compute()` (DemBones.h:344)

```
init()                                  ← 없는 데이터(w 또는 m)를 채운다
repeat nIters:
    computeTranformations()             ← w 고정하고 m 갱신 (nTransIters 회)
    computeWeights()                    ← m 고정하고 w 갱신 (nWeightsIters 회)
    cbIterEnd()  → rmse() 로 수렴 판정
```

전형적인 **교대 최적화(alternating optimization)**. `nTransIters=0` 으로 두면 트랜스폼 갱신이
통째로 스킵되어(`DemBones.h:238` 조기 return) **웨이트만 푸는 모드**가 된다 ← 우리 주 용도.
반대로 `nWeightsIters=0` 이면 웨이트를 고정하고 본 애니메이션만 푼다.

`init()` (DemBones.h:186) 의 분기가 툴의 성격을 결정한다:

| 입력 상태 | init 동작 |
|-----------|-----------|
| `w`, `m` 둘 다 있음 | 아무것도 안 함 (둘 다 최적화) |
| `m` 만 있음 (조인트 애님만) | `initWeights()` — 각 버텍스를 오차 최소 본에 강체 바인드 후 라벨 확산 |
| `w` 만 있음 (스킨만) | `m` 을 단위행렬로 초기화 |
| 둘 다 없음 | **LBG-VQ 클러스터링**으로 `nB` 개 본을 새로 만들어냄 (§1.6) |

### 1.4 웨이트 갱신 `computeWeights()` (DemBones.h:276) — **우리가 이식할 핵심**

버텍스 `i` 하나에 대해 `A x ≈ b` 형태의 작은 최소자승 문제를 푼다.
`A` 는 `[3·nF, nB]` (열 j = 본 j 만으로 변환했을 때의 궤적), `b` 는 캐시 궤적 `v.col(i)`.
버텍스마다 독립이므로 완전 병렬.

정규방정식을 **미리 계산해 재사용**하는 게 성능의 전부다:

1. `compute_mTm()` (:728) — `mTm[j1,j2] = Σ_k M3(k,j1)ᵀ M3(k,j2)` (4×4 블록, `nB×nB` 개).
   프레임 루프가 여기서 **한 번만** 돈다.
2. `compute_aTa(i)` (:868) — `aTa(j1,j2) = u(i)ᵀ · mTm[j1,j2] · u(i)`.
   → 버텍스별 `nB×nB` 행렬이 **프레임 수와 무관하게** 4×4 이차형식 하나로 나온다.
3. `compute_aTb()` (:754) — `aTb(j,i) = Σ_k v(k,i) · (M3(k,j) u(i))`.
4. 정규화 항 추가 (:302):
   `aTa ← (1−lockW)·(aTa/scale + weightsSmooth·I) + lockW·I`,
   `aTb ← (1−lockW)·(aTb/scale + weightsSmooth·ws) + lockW·w_prev`
   여기서 `ws` 는 **라플라시안 스무딩된 웨이트**, `lockW(i)∈[0,1]` 는 버텍스별 소프트 락.
5. **후보 본 추리기** (:306~309) — 스무딩된 웨이트 `ws.col(i)` 를 내림차순 정렬해
   **상위 `nnz` 개만** 남기고 나머지는 아예 문제에서 뺀다. → 실제로 푸는 계는 `nnz×nnz` (기본 8×8).
6. `ConvexLS::solve()` (:316) — 아래.

**`ConvexLS` (ConvexLS.h:65)**: `min |Ax−b|²  s.t.  x ≥ 0, Σx = 1`.
- 비음(非陰) 제약은 **active set method**(Lawson-Hanson NNLS 계열).
- 합=1 제약은 `ones` 벡터의 **Householder QR** 로 얻은 널스페이스 기저 `Q2` 에 투영해서 처리
  (`solveP`, :120). `q2[n]` 를 크기별로 미리 만들어 캐시한다(:48).
- warm start 지원 — 반복 사이에 이전 해에서 이어 푼다.

**라플라시안 스무딩** (`computeSmoothSolver` :774, `compute_ws` :847):
- 메시 엣지 기반 가중 라플라시안을 만드는데, 가중치가 기하 거리가 아니라
  **"이 엣지의 길이가 시퀀스 내내 얼마나 안 변했나"** 다 (:812): `1/(rms(|v_i−v_j| − |u_i−u_j|) + eps)`.
  → 잘 늘어나는(=서로 다른 본에 속할 법한) 엣지는 약하게, 뻣뻣한 엣지는 강하게 묶는다. **영리한 부분.**
- 스무딩은 **암시적(implicit)**: `(I + step·L) ws = w` 를 **SparseLU** 로 푼다(:839, :850).
  → 마야에는 scipy 가 없다. 이식 시 대체가 필요하다(§2.2, §4.6).

### 1.5 트랜스폼 갱신 `computeTranformations()` (DemBones.h:237)

프레임 k, 본 j 마다 **최적 강체 변환**을 닫힌 형태로 구한다.

- `compute_vuT()` (:647) — 공분산 `Σ_i w(j,i)·v(k,i)·u(i)ᵀ`.
  여기에 **translations affinity** 소프트 제약을 섞는다(:660): 웨이트를 `transAffineNorm` 제곱해
  가중한 공분산을 `transAffine` 배로 더한다 → 본이 자기 영향권 **중심** 쪽으로 이동하도록 유도.
- `compute_uuT()` (:673) — 본끼리 웨이트를 공유하는 쌍만 담은 희소 블록 행렬.
- 본 j 갱신 시 다른 본들의 기여를 빼고(:254) `qpT2m()` (:411) 호출.
- `qpT2m()` = **Kabsch/Procrustes**: 3×3 공분산의 **SVD → U·diag(1,1,det)·Vᵀ** 로 회전을 만들고
  (반사 방지), 이동은 무게중심 차로. → 스케일/전단이 절대 안 생긴다(= rigid bones).

### 1.6 본이 없을 때 — LBG-VQ 초기화 (DemBones.h:190~213)

`w`, `m` 이 둘 다 없으면 조인트를 **만들어낸다**:
`nB=1` 에서 시작 → `split()` (:532) 로 오차·중심거리 곱이 최대인 시드에서 클러스터를 쪼개고 →
`computeTransFromLabel()`/`computeLabel()` 반복(라플라시안 이웃을 따라 우선순위 큐로 라벨 확산) →
`pruneBones()` (:597) 로 버텍스가 적은 본 제거. `targetNB` 에 도달할 때까지.
→ 이게 `-b 20` 옵션의 정체다. **애니메이션 메시를 게임 엔진용 스켈레톤으로 변환**하는 용도.

### 1.7 `DemBonesExt` — 계층 스켈레톤 복원 (DemBonesExt.h)

코어는 "상대 행렬 `m`" 까지만 안다. 실제 DCC 는 **부모 기준 로컬 rot/trans** 가 필요하다.
`computeRTB()` (:133) 가 그 변환을 한다:

```
lm = preMulInv · (m_parent · bind_parent)⁻¹ · m_j · bind_j        (부모 있음)
lm = preMulInv · m_j · bind_j                                      (루트)
```
그리고 `toRot()` (:245) 로 회전행렬 → **오일러**. 여기가 재미있는데, 단순 `eulerAngles()` 가 아니라
**부호 반전·±π 배수 조합을 전수 탐색해 직전 프레임 값에 가장 가까운 해**를 고른다(:251~272).
= 오일러 플립 방지(마야에서 Euler Filter 로 하는 일을 애초에 안 생기게).
`bindUpdate` 옵션: 0=바인드 유지, 1=조인트 위치를 p-norm 무게중심으로, 2=1 + 전체를 한 루트 밑으로 재편.

### 1.8 커맨드라인 파이프라인 (mainCmd.cpp) 과 6가지 사용 모드

`readABCs` → `readFBXs` → `compute()` → `writeFBXs`.
- `AbcReader.cpp:89` — abc 샘플마다 포지션을 읽어 `v` 채우고 `fTime` 기록. 알렘빅의 xform 을 곱해 월드로.
- `FbxReader.cpp` — 메시(rest `u`, 토폴로지 `fv`), 스킨클러스터(`w`), 스켈레톤(`bind`, `parent`,
  `preMulInv`, `rotOrder`, `orient`), 조인트 키(`m`), `demLock` 어트리뷰트(`lockM`),
  버텍스 컬러 그레이스케일(`lockW`) 을 읽는다. **키가 하나도 없으면 `m` 을 버린다**(:322).

`data/run.bat` 이 사실상 기능 명세다:

| 명령 | 의미 |
|------|------|
| `-b 5/10/20` | 본 없이 **스켈레톤+웨이트+애님 생성** (LBG-VQ) |
| `--bindUpdate=2` | 위 + 조인트를 한 루트 밑으로 그룹핑 |
| `-i Bone_Trans.fbx --nTransIters=0` | **캐시 + 조인트 애님 → 웨이트 솔브** ← **사용자가 기억하는 그것** |
| `-i Bone_Skin.fbx --nWeightsIters=0` | 캐시 + 웨이트 → **본 애님 솔브** |
| `-i Bone_All.fbx --bindUpdate=1` | 둘 다 주고 **동시 최적화** |
| `-i Bone_Helpers.fbx` | `demLock` 걸린 본은 고정, **헬퍼 본만** 풂 |
| `-i Bone_PartiallySkinned.fbx --nTransIters=0` | 버텍스 컬러로 **일부 웨이트만** 다시 풂 |

> 툴 자체 제약(usage.txt:86): *"clean input data — 메시 하나, 스킨클러스터 하나, 불필요한 조인트 없음"*.

---

## 2. 마야에서 되는가 — 타당성 (실측)

### 2.1 결론

**된다.** 그리고 생각보다 싸다. 병목은 알고리즘이 아니라 (예상과 달리) 후보 본 선별 단계였고,
그마저도 실무 규모에서 10초대다.

### 2.2 환경 제약 (실측)

`mayapy.exe -c "import numpy, scipy"` 결과:

| 항목 | 결과 |
|------|------|
| Python | 3.10.8 (Maya 2024) |
| **numpy** | **2.2.6 사용 가능** |
| **scipy** | **없음** |
| maya.api.OpenMaya | 사용 가능 |

→ scipy 가 없으므로 **직접 구현해야 하는 것 2가지**:
1. `ConvexLS` (NNLS + 합=1) — active set. 원본이 300줄도 안 되니 이식 부담 적음. **완료 확인**(§2.3).
2. 희소 라플라시안 **암시적 스무딩의 SparseLU** — 대안: (a) 자코비/가우스-자이델 반복 몇 회,
   (b) 명시적(explicit) 스무딩 `w ← w + step·(mean_neighbors − w)` 를 n 회.
   품질 차이는 정규화 항 하나이므로 **(b) 로 시작하고 필요하면 (a)** 로 올린다.

### 2.3 알고리즘 실측 — numpy 프로토타입

`ConvexLS` + `mTm/aTa/aTb` + 후보 선별을 numpy 로 이식해, 합성 데이터(원통 + 조인트 체인 +
정답 웨이트로 LBS 베이크한 시퀀스 = 알렘빅 캐시 대역)에서 **웨이트를 되찾아오는** 실험을 했다.

| 규모 (nV / nB / nF) | 후보 선별 | 사전계산 | 버텍스 솔브 | **합계** | 재구성 RMSE |
|---|---|---|---|---|---|
| 8,000 / 12 / 60 | 0.40s | 0.16s | 0.89s | **1.45s** | 모델 크기의 **0.065%** |
| 20,000 / 40 / 100 | 6.08s | 0.70s | 4.99s | **11.78s** | 모델 크기의 **0.019%** |

- 웨이트 행 합 = 1.0000 (제약 정확히 만족), 버텍스당 비영 웨이트 ≤ 4 (`nnz=8` 상한 안).
- **주의할 관찰**: RMSE 는 0.02% 인데 **정답 웨이트와의 최대 차이는 0.94** 였다.
  → 웨이트 해는 **유일하지 않다**(같은 움직임을 내는 웨이트 조합이 많다). 그래서 원본이
  스무딩 정규화(`weightsSmooth`)를 넣은 것이고, **우리도 반드시 넣어야** 손으로 만졌을 때
  말이 되는 웨이트가 나온다. 프레임이 다양할수록(포즈 커버리지) 해가 조여진다.
- 스케일 특성: 후보 선별이 `O(nV·nB·nF)` 로 지배적. `nB=100, nF=200` 이면 30초대로 늘어난다.
  완화책: **프레임 서브샘플링(stride)**, 청크 처리, 또는 조인트-버텍스 거리로 1차 컷.

### 2.4 데이터 취득 실측 — 마야 측

20,100 버텍스 메시 + 조인트 20개 + 100 프레임을 헤드리스 마야에서 샘플링:

| 작업 | 실측 |
|------|------|
| 프레임별 메시 포인트 (`currentTime` + `MFnMesh.getPoints(kWorld)`) | **11.8 ms/frame** (총 1.18s) |
| 프레임별 조인트 월드행렬 (`MDagPath.inclusiveMatrix()`) | 0.1 ms/frame (총 0.01s) |
| 둘 다 한 패스에서 | 11.9 ms/frame |
| 웨이트 쓰기 (`MFnSkinCluster.setWeights`, 20k×20) | **0.04s** |

→ 취득/쓰기는 **무시해도 되는 비용**. 단, 위는 skinCluster 로 만든 합성 애니메이션이고
**실제 알렘빅 캐시는 디스크 I/O 때문에 더 느릴 수 있다**(실기 확인 항목, §8).

### 2.5 종합 예상

실무 규모(캐릭터 메시 2만 버텍스, 조인트 40, 캐시 100프레임) 기준
**총 15초 내외**. 진행률 표시와 취소만 있으면 UX 문제 없음.

---

## 3. 구현 전략 비교

| | **A. 네이티브 파이썬 재구현** | **B. `DemBones.exe` 래핑** | **C. 하이브리드** |
|---|---|---|---|
| 방식 | numpy 로 솔버 이식, 씬에서 직접 읽고 씀 | 씬 → fbx+abc 내보내기 → exe → fbx 읽어오기 | A 를 기본, 전체 분해만 B |
| 정확도 | 동일 알고리즘(스무딩 솔버만 근사) | 원본 그대로 | 상황별 최선 |
| 속도 | 실측 12s (§2.3) | exe 자체는 더 빠름(C++/OpenMP), 그러나 **왕복 I/O** | — |
| 리스크 | 이식 버그 | **fbx 왕복에서 조인트 이름/계층/rotateOrder/단위 훼손**, exe 가 요구하는 "clean data" 제약, 결과 웨이트를 원본 메시로 다시 옮기는 단계 필요 | 코드 2배 |
| 반복 작업성 | 씬에서 바로 → **툴답다** | 파일 왕복 → 배치엔 좋지만 인터랙티브엔 나쁨 | — |
| 배포 | 코드만 (release 빌더가 툴+Framework 만 복사) | **exe + ref 폴더 동봉** 필요 | 무거움 |

**권장: A.** 사용자 주 용도(캐시+조인트애님 → 웨이트)는 알고리즘 전체가 아니라 **웨이트 솔브 한 갈래**뿐이고,
그 갈래는 §2.3 에서 이미 numpy 로 돌려 검증했다. 씬 안에서 즉시 반복하는 게 툴의 가치다.
**B 는 §6 의 v01.03 이후 "Full Decomposition" 이 정말 필요해질 때** 선택지로 남긴다
(그때는 exe 가 LBG-VQ 까지 다 해주므로 이득이 크다).

---

## 4. 툴 설계

### 4.1 형태

- 아키텍처 **(B) — 마야 내 PySide 툴** (`prefer-pyside-for-new-tools`). `A00420_Wrapper` 를 복제해 시작.
- 로직(`app/core`)은 **마야 비의존 numpy 코드**와 **마야 I/O 코드**를 파일 단위로 분리한다.
  솔버가 순수 numpy 여야 mayapy 헤드리스로 단위 검증할 수 있다(§7).

```
tools/A00430_DemBone/
├── __init__.py / launch.py / __dragDrop_A00430.py
├── app/
│   ├── config/version.py
│   ├── core/
│   │   ├── convex_ls.py          # ConvexLS 이식 (numpy, 마야 무관)
│   │   ├── solver_weights.py     # computeWeights 이식 (mTm/aTa/aTb/후보/스무딩)
│   │   ├── solver_transforms.py  # computeTranformations 이식 (Kabsch/SVD)
│   │   ├── laplacian.py          # 시퀀스 기반 엣지 가중 + 스무딩(반복법)
│   │   ├── scene_sampler.py      # 캐시 메시/조인트 → numpy 배열 (마야 의존)
│   │   ├── skin_writer.py        # 결과 웨이트 → skinCluster (마야 의존)
│   │   └── alembic_cache.py      # abc 임포트/프레임 평가 (A00280 것을 복사)
│   └── ui/main_window.py
└── ref/                          # 원본 (읽기 전용, 배포 제외)
```

> `A00280` 의 `alembic_cache.py` 는 **import 하지 않고 복사**한다 — 릴리스 빌더가 툴 하나 +
> Framework 만 복사하므로 툴끼리 물리면 패키지가 깨진다(A00170 에서 같은 판단).

### 4.2 탭 구성 (중첩 탭 — `prefer-subtabs-over-stacked-collapsibles`)

| 탭 | 내용 | 단계 |
|----|------|------|
| **Solve Weights** | 캐시 + 조인트 애님 → 스킨 웨이트 (`--nTransIters=0`) | v01.00 |
| **Solve Transforms** | 캐시 + 기존 스킨 → 조인트 애님 키 (`--nWeightsIters=0`) | v01.01 |
| **Refine** | 둘 다 주고 교대 최적화 (`compute()`), 본/버텍스 락 | v01.02 |
| **Options** | nnz / smooth / iters / 프레임 stride / 정규화 등 공용 파라미터 | v01.00 |

### 4.3 Solve Weights 탭 — 입력과 검증

| 입력 | 위젯 | 비고 |
|------|------|------|
| Cache Mesh | TSL 1개 (또는 `.abc` 파일 → 임포트 버튼) | 애니메이션되는 메시 |
| Rest Mesh | TSL 1개 (옵션) | 비우면 **Rest Frame 의 캐시**를 rest 로 사용 |
| Target Mesh | TSL 1개 | 웨이트를 칠할 실제 리깅 메시. 비우면 Rest Mesh |
| Joints | TSL N개 (+ 계층 자동 수집 버튼) | 순서가 인플루언스 순서 |
| Time Range | 공용 `MOD_timeRange_qt_v01` | Start/End + Get Current |
| Rest Frame | 스핀박스 | 바인드 포즈로 볼 프레임 |
| Frame Stride | 스핀박스 | 속도용 서브샘플링 (§2.3) |

**사전 검증(하나라도 실패하면 즉시 중단 + 로그)**:
1. Cache / Rest / Target 의 **버텍스 수 일치** (토폴로지 시그니처 비교).
2. 셰이프 확정은 반드시 **`Framework.core.maya_shape`** 사용 — `extendToShape` 금지
   (`extendtoshape-picks-wrong-shape`). `polyEvaluate` 도 셰이프에 건다.
3. 조인트 최소 2개, 프레임 최소 2개(정지 포즈만 있으면 해가 무의미 — 경고).
4. 이미 skinCluster 가 있으면 **바인드 포즈를 거기서** 가져올지(`bindPreMatrix`) 물어본다.

### 4.4 좌표·행렬 규약 — **이식에서 제일 틀리기 쉬운 곳**

| 항목 | DemBones (Eigen) | Maya | 대응 |
|------|------------------|------|------|
| 벡터 규약 | **열벡터** `M·p` | **행벡터** `p·M` (translate 가 마지막 **행**) | 로드 시 **한 번 전치**하거나, 전 코드를 마야 규약(행벡터)으로 통일. **후자를 택한다** — 마야에서 읽은 값을 그대로 쓰는 게 버그가 적다 |
| rest `u` | 월드 공간 (fbx gMat 곱함, `FbxReader.cpp:140`) | `geomMatrix` 를 곱한 월드 위치 | Rest Frame 에서 `MFnMesh.getPoints(kWorld)` |
| 캐시 `v` | 알렘빅 xform 곱해 월드 (`AbcReader.cpp:94`) | 동일 | 프레임별 `getPoints(kWorld)` |
| 상대변환 `m` | `globalTransform(t)·bind⁻¹` | `matrix[j] × bindPreMatrix[j]` | **정확히 같은 것** |
| 바인드 | fbx 조인트 글로벌 | skinCluster `bindPreMatrix[i]` 또는 Rest Frame 의 `worldMatrix` 역행렬 | skinCluster 가 있으면 그쪽 우선 |

> **바인드 인덱스 함정**: `bindPreMatrix[i]` 의 `i` 는 인플루언스 논리 인덱스이며
> **`matrix[]` 연결에서 얻어야** 한다 (메모: `wip-a00275-skintool-bindpose`). 배열 순서 가정 금지.

### 4.5 알고리즘 파이프라인 (Solve Weights)

```
1. 검증 (§4.3)
2. 취득  (프레임 루프 1회, 실측 12ms/frame)
     U (nV,3)      ← Rest Frame 의 rest 메시 월드 포인트
     V (nF,nV,3)   ← 프레임별 캐시 메시 월드 포인트
     M (nF,nB,4,4) ← 프레임별 joint.worldMatrix × bindPre
3. 후보 본 선별   E[i,j] = Σ_k |u_i·M(k,j) − v(k,i)|²  → 버텍스별 상위 nnz 개
     (원본은 스무딩 웨이트로 고르지만, 초기에는 웨이트가 없으므로 원본 initWeights 와 같은 강체오차 기준)
4. 사전계산       mTm[j1,j2] (4×4) → 버텍스별 aTa (nnz×nnz), aTb (nnz)
5. 정규화         aTa += weightsSmooth·I ,  aTb += weightsSmooth·ws
                  ws = 라플라시안 스무딩된 현재 웨이트 (첫 회는 후보 균등분배)
6. 버텍스 솔브    ConvexLS(active set): x ≥ 0, Σx = 1
7. 반복           nWeightsIters 회 (3~5) — 3~6 을 ws 갱신하며 반복
8. 적용           기존 skinCluster 재사용 또는 새로 바인드 → MFnSkinCluster.setWeights
                  maxInfluences = nnz, normalizeWeights 설정 확인 후 복원
9. 리포트         RMSE(절대 + 모델 크기 대비 %), 소요 시간, 버텍스당 평균 인플루언스
```

전 과정을 `Framework.core.maya_undo.undo_chunk()` 로 감싼다(`undo-chunk-by-default`).

### 4.6 근사로 가는 지점 (원본과 의도적으로 다른 부분 — 문서에 명시할 것)

1. **라플라시안 스무딩**: SparseLU 암시적 → 반복법(명시적 n회 또는 자코비). 결과가 살짝 덜 매끄러움.
2. **후보 본 선별 시점**: 원본은 매 반복마다 스무딩 웨이트로 재선별. 우리는 1회 선별 후
   반복 내에서는 고정(속도). 필요하면 옵션으로 재선별 켜기.
3. **다중 subject(`nS`)**: 원본은 여러 rest/시퀀스 쌍을 동시에 푼다. **단일 subject 만 지원**(범위 밖).
4. OpenMP 병렬 → numpy 벡터화. 버텍스 루프만 파이썬 루프로 남는다(실측상 문제 없음).

---

## 5. 마야 고유 주의사항 (메모리에서 끌어온 것들)

- **셰이프 확정**: `Framework.core.maya_shape` 만 사용. `extendToShape` 금지 — 다중 셰이프 메시에서
  조용히 다른 셰이프를 읽는다(`extendtoshape-picks-wrong-shape`).
- **undo**: 반복 씬 변경은 `undo_chunk()` 로 1회 undo (`undo-chunk-by-default`).
- **UI 문자열/로그 전부 영어**, 한국어는 주석·독스트링만 (`ui-text-english-only`).
- **QDoubleSpinBox** 는 값을 되쓰면 `setKeyboardTracking(False)` (`qdoublespinbox-keyboard-tracking`).
- **`clicked` 시그널**은 `checked`(bool) 를 넘긴다 — 기본 인자 있는 슬롯에 직결 금지
  (`qt-clicked-passes-checked-bool`).
- **긴 연산의 UI**: 프레임 취득/솔브 단계마다 진행률 + Cancel. 마야 메인 스레드에서 돌리되
  단계 경계에서 `processEvents`. (별도 스레드는 마야 API 호출 때문에 위험 — 취득은 반드시 메인 스레드.)
- **numpy 부재 대비**: import 를 감싸고, 없으면 UI 에 명확한 안내(마야 2024 는 기본 포함).

---

## 6. 단계별 구현 계획

| 버전 | 내용 | 검증 |
|------|------|------|
| **v01.00** ✅ | 골격 + **Solve Weights 탭**. `convex_ls.py`/`solver_weights.py`/`scene_sampler.py`/`skin_writer.py`. Options 탭. 진행률/취소. | 완료 — 합성 왕복 + 마야 통합 |
| **v01.01** ✅ | **Solve Transforms 탭** — Kabsch/SVD 로 본 애님 솔브 후 키 베이크. 오일러 연속성은 **`cmds.filterCurve`** 로 대체(원본 `toRot` 전수탐색 불필요) | 완료 — 망가뜨린 애님 복원 확인 |
| **v01.02** ✅ | **Refine 탭** — 교대 최적화 + 본 하드락 / 버텍스 소프트락 + RMSE 수렴 로그 | 완료 — RMSE 0.68 → 0.003 |
| **v01.03** ✅ | **Decompose 탭** — 캐시만으로 본 클러스터 생성(LBG-VQ) + 조인트 생성 + 바인드 + 베이크. 원본을 그대로 옮기면 동작하지 않아 **분할 씨앗 크기**와 **라벨 확산 우선순위**를 바꿨다: [v01.03 문서 §9](A00430_DemBone_v0103_ref_requirements.md) | 완료 — 20k 버텍스에서 본 20개 32.6초, 오차 1.02% |

**구현하며 §4.6(원본과 다른 점) 대비 달라진 결정**:
- 로컬 회전 복원은 `DemBonesExt::computeRTB` + `toRot` 을 옮기지 않고 **`cmds.xform(ws=True, matrix=)`
  + Euler Filter** 로 대체했다 — 마야가 부모공간·jointOrient 를 이미 처리한다.
- **본 솔브의 공분산은 4×3 이 아니라 4×4 로 들고 다녀야 한다.** 질량(3,3)을 다른 행렬에서 가져오면
  Translation Affinity 를 켰을 때 무게중심이 어긋나 결과가 무너진다(실측 오차 460% → 1.4%).
  자세한 내용은 [가이드 §9](../A00430_DemBone.md).

각 단계 산출물: 코드 + `JUN_All/docs/A00430_DemBone.md` 가이드 + WORKLOG + portfolio 반영
(`push-includes-tool-guide-docs`).

---

## 7. 검증 계획

**A. 합성 왕복 (핵심 — 정답을 아는 유일한 방법)**
mayapy 헤드리스에서: 조인트 체인 + 메시 + **손으로 만든 웨이트**로 스킨 → 애니메이션 베이크 →
그 결과를 "캐시"로 삼아 웨이트를 지우고 다시 푼다 → **재구성 RMSE**와 **웨이트 차이**를 본다.
(§2.3 프로토타입이 이미 이 구조. 마야 데이터로 갈아끼우면 그대로 회귀 테스트가 된다.)

**B. 실제 데이터** — `ref/data/Bone_Anim.abc` 를 마야로 임포트 + `Bone_Trans.fbx` 의 조인트로
Solve Weights → `data/SolvedWeights.fbx`(원본 exe 결과)와 웨이트 비교.
**원본과 직접 대조할 수 있는 유일한 케이스**라 반드시 한다.

**C. 성능 회귀** — 20k/40/100 케이스 시간 기록(§2.3 표를 기준선으로).

**D. 방어 케이스** — 버텍스 수 불일치, 조인트 1개, 프레임 1개, 스킨클러스터 이미 존재,
다중 셰이프 메시, 레퍼런스된 메시, 캐시가 LBS 로 표현 불가능한 경우(천 시뮬 등 — 오차가 크게 나오는지 로그).

---

## 8. 리스크 / 확인 필요

1. **알렘빅 캐시 평가 속도** — §2.4 는 skinCluster 합성 애니메이션 기준. 실제 `.abc` 는
   디스크 I/O 로 더 느릴 수 있다. → 실기에서 프레임당 시간 측정 후 stride 기본값 조정.
2. **웨이트 해의 비유일성** (§2.3) — RMSE 는 좋은데 웨이트가 "손으로 만진 것 같지 않을" 수 있다.
   스무딩 강도 기본값을 실기 데이터로 튜닝해야 한다. **최종 품질을 좌우하는 유일한 노브.**
3. **천/근육 시뮬 캐시** — LBS 로 표현 불가능한 변형(볼륨 보존, 주름)은 원리상 못 맞춘다.
   → 툴이 "얼마나 못 맞췄는지"(RMSE)를 반드시 보여줘야 오해가 없다.
4. **조인트 수가 많을 때(100+)** 후보 선별 비용 — §2.3 스케일 노트 참고, 청크+stride 로 대응.
5. **scipy 부재로 스무딩이 근사** — 품질 차이가 실기에서 유의미하면 자코비 반복 횟수를 옵션화.

---

## 9. 라이선스 / 출처 표기

- 원본: **Dem Bones © 2019 Electronic Arts, BSD 3-Clause** (`ref/LICENSE.md`).
- 파이썬 재구현물은 파생물이므로 각 core 모듈 헤더에 **BSD-3 고지 + 논문 인용**을 넣는다:
  > Le & Deng, *Smooth Skinning Decomposition with Rigid Bones*, ACM TOG 31(6), SIGGRAPH Asia 2012.
  > Weights smoothing: Le & Deng, *Robust and Accurate Skeletal Rigging from Mesh Sequences*, ACM TOG 33(4), 2014.
- `ref/`(exe 포함)는 **배포 대상에서 제외**(릴리스 빌더 제외 목록에 추가). exe 브리지를 채택할 때만 재검토.

---

## 10. 참고 인덱스 (원본 코드 위치)

| 무엇 | 파일:줄 |
|------|---------|
| 데이터 정의 (`u/v/w/m/fv/nnz`...) | `ref/include/DemBones/DemBones.h:113~157` |
| `init()` 분기 | `DemBones.h:186` |
| 트랜스폼 갱신 | `DemBones.h:237` / 공분산 `:647` / 희소쌍 `:673` / **Kabsch** `:411` |
| **웨이트 갱신** | `DemBones.h:276` / `mTm` `:728` / `aTb` `:754` / `aTa` `:868` |
| 라플라시안(시퀀스 기반 가중) | `DemBones.h:774` / 스무딩 `:847` |
| LBG-VQ 초기화 | `DemBones.h:532`(split) `:597`(prune) `:447`(label) |
| **ConvexLS (NNLS+합=1)** | `ref/include/DemBones/ConvexLS.h:65` / 널스페이스 투영 `:120` |
| 로컬 rot/trans 복원 | `ref/include/DemBones/DemBonesExt.h:133` / 오일러 연속성 `:245` |
| `m` 계산식 (이식 기준) | `ref/src/command/FbxReader.cpp:197` |
| 캐시 읽기 | `ref/src/command/AbcReader.cpp:89` |
| 사용 모드 6종 | `ref/data/run.bat` |
| CLI 옵션 전체 | `ref/bin/usage.txt` |
