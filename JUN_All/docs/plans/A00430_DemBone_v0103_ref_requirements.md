---
title: A00430_DemBone v01.03 — 조인트 자체 생성에 필요한 ref 코드
aliases: [A00430 v0103, DemBone Full Decomposition]
tags: [plan, maya-python, skinning, A00430]
updated: 2026-08-13
---

# A00430_DemBone v01.03 — 조인트 자체 생성에 필요한 `ref/` 코드 정리

> **목적**: v01.03 에서 "캐시만 주면 **조인트까지 만들어 내는**" 모드(원본 `-b N`)를 붙이려면
> `ref/` 의 **어떤 코드가 더 필요한지**를 미리 확정해 둔다.
> 작성: 2026-08-13 / 상태: **✅ v01.03 구현 완료** (가이드: [A00430_DemBone.md](../A00430_DemBone.md))
>
> **중요**: 여기서 말하는 "필요한 ref 코드"는 **알고리즘을 읽는 대상**일 뿐이다. 구현은 전부
> `app/core/solver_init.py` / `joint_builder.py` 에 **파이썬으로 새로 작성**했고, 툴은 런타임에
> `ref/` 를 읽거나 import 하지 않는다. `ref/` 는 git 추적에서 제외되어 있다.
>
> 구현하며 계획과 달라진 점은 §9 에 정리했다.

---

## 0. 한 줄 요약

`ref/include/DemBones/DemBones.h` 의 **초기화 5개 함수**(`init` 분기 · `split` · `pruneBones` ·
`computeLabel` · `computeTransFromLabel` / `labelToWeights`)와
`ref/include/DemBones/DemBonesExt.h` 의 **바인드 위치 계산 2개**(`computeCentroids` · `computeRoot`)
— 이 7개만 더 옮기면 된다. 나머지(솔버 본체·ConvexLS·라플라시안·Kabsch)는 **v01.02 에서 이미 이식했다.**

가장 큰 리스크는 알고리즘이 아니라 **초기화 비용**이다(§4).

---

## 1. v01.03 이 해야 하는 일

지금은 조인트를 사용자가 준다. v01.03 은 **캐시만** 받아서:

```
알렘빅 캐시  →  [본 개수 N]  →  조인트 N 개 생성 + 웨이트 + 조인트 애니메이션
```

원본 커맨드라인으로는 `DemBones -a cache.abc -i rest.fbx -b 20 -o out.fbx`
(`ref/data/run.bat` 의 첫 3줄). 용도는 "**애니메이션 메시를 게임 엔진에 넣을 수 있는 스켈레톤으로
변환**"이다 — 후디니/클로스/블렌드셰이프 결과를 LBS 리그로 바꾸는 것.

옵션 `--bindUpdate` 는 생성된 조인트의 배치 방식이다:
| 값 | 뜻 | 마야에서 |
|----|-----|---------|
| 0 | 바인드 유지 | 입력에 조인트가 있을 때만 의미 |
| 1 | 조인트 위치를 **p-norm 무게중심**으로 | 생성 모드의 사실상 기본 |
| 2 | 1 + **전체를 루트 하나 밑으로** 묶기 | 계층이 있는 스켈레톤으로 |

---

## 2. 이미 이식이 끝난 것 (추가 작업 없음)

| 원본 | 위치 | 우리 쪽 |
|------|------|---------|
| 웨이트 갱신 `computeWeights()` | `DemBones.h:276` | `app/core/solver_weights.py` |
| 제약 최소자승 `ConvexLS::solve` | `ConvexLS.h:65` | `app/core/convex_ls.py` |
| 트랜스폼 갱신 `computeTranformations()` | `DemBones.h:237` | `app/core/solver_transforms.py` |
| **최적 강체 추출 `qpT2m()`** | `DemBones.h:411` | `solver_transforms.rigid_from_normal()` |
| **버텍스-본 오차 `errorVtxBone()`** | `DemBones.h:426` | `solver_common.bone_errors()` (전체 표를 벡터화로 한 번에) |
| 라플라시안 + 스무딩 | `DemBones.h:774`, `:847` | `app/core/laplacian.py` |
| 교대 최적화 `compute()` | `DemBones.h:344` | `app/core/solver_refine.py` |
| 수렴 판정 | `mainCmd.cpp:38` | `solver_refine.refine()` |

→ **v01.03 은 "초기화(initialization)" 부분만 추가하면 된다.**

---

## 3. 새로 필요한 ref 코드 — 7개

### 3-1. `DemBones.h:186` `init()` 의 "둘 다 없음" 분기 — **뼈대**

```cpp
int targetNB = nB;
nB = 1;  label = 0;  computeTransFromLabel();
while (cont) {
    int prev = nB;
    split(targetNB, 3);
    for (rep < nInitIters) { computeTransFromLabel(); computeLabel(); pruneBones(3); }
    cont = (nB < targetNB) && (nB > prev);
}
labelToWeights();
```

본 1개에서 시작해 **쪼개고 → 다듬고 → 솎아내기**를 목표 개수에 닿을 때까지 반복하는
LBG-VQ(Linde-Buzo-Gray Vector Quantization) 구조. 이 루프 자체는 그대로 옮기면 된다.

> 주의: 주석(`:182`)이 밝히듯 **정확히 `nB` 개가 나오지 않는다**. 분할·솎아내기 결과로 개수가
> 달라질 수 있어서 UI 는 "target"으로 표기해야 한다.

### 3-2. `DemBones.h:532` `split(maxB, threshold)` — 클러스터 쪼개기 ★핵심

무엇을 하는지:
1. 클러스터별 **중심 `cu`** 와, 버텍스별 **중심까지 거리 `d`** / **강체 피팅 오차 `e`** 를 구한다.
2. 시드 선택 기준이 특이하다 — `|(e(i) - minE(j)) * (d(i) - minD(j))|` 가 **최대**인 버텍스.
   = "오차도 크고 중심에서도 먼" 지점. 둘 다여야 쪼갤 가치가 있다는 판단이다.
3. 쪼갤 자격: `버텍스 수 > threshold*2` **그리고** `클러스터 총오차 > 평균오차/100`.
4. 시드의 **라플라시안 이웃**에 새 라벨을 뿌리고 `nB` 를 늘린다.

이식 난이도: **낮음**. `d`/`e` 는 벡터화되고, `minE`/`minD`/`ce` 는 `np.minimum.at` /
`np.bincount` 로 접을 수 있다. 시드 선택도 `argmax`.
필요한 우리 쪽 준비: `bone_errors()` 는 이미 있고, **라플라시안 이웃 목록 API** 가 하나 필요하다(§5).

### 3-3. `DemBones.h:447` `computeLabel()` — 라벨 확산 ★핵심 · ★리스크

각 클러스터에서 **오차가 가장 작은 버텍스(seed)** 를 뽑아 우선순위 큐에 넣고, 큐에서 꺼낸
버텍스에 라벨을 확정하면서 **메시 이웃으로 퍼뜨린다**. 단순히 "오차 최소 본"을 고르는 것과 달리
**메시 연결성을 따라 퍼지므로 클러스터가 조각나지 않는다**(= 본이 몸 반대편까지 튀지 않는다).

```cpp
heap.push(seed of each bone)
while (!heap.empty()) {
    (j, i, err) = heap.pop()
    if (dirty[i]) { label(i)=j; dirty[i]=false;
        for (i2 in neighbors(i)) if (dirty[i2]) heap.push(j, i2, errorVtxBone(i2, j)); }
}
남은 label==-1 은 오차 최소 본으로
```

이식 난이도: **중**. 로직은 그대로지만 **파이썬 힙 루프**라 비용이 든다(§4).
다행인 점: 원본은 `errorVtxBone(i2, j)` 를 그때그때 계산하지만, 우리는 `bone_errors()` 로
**(nV × nB) 표를 이미 통째로 갖고 있으므로 O(1) 조회**로 바뀐다. 힙 연산만 남는다.

### 3-4. `DemBones.h:597` `pruneBones(threshold)` — 쓸모없는 본 제거

버텍스가 `threshold`(3) 개 미만인 본을 지우고, 남은 본을 앞으로 당겨 재번호(`newID`)한 뒤
`m` 을 압축하고 `computeLabel()` 을 다시 부른다.
이식 난이도: **낮음**. 인덱스 재매핑만 조심하면 된다(라벨/변환/웨이트 열이 함께 움직여야 한다).

### 3-5. `DemBones.h:507` `computeTransFromLabel()` — 라벨 → 강체 변환

라벨이 같은 버텍스들로 프레임마다 공분산을 쌓고 `qpT2m()` 으로 최적 강체를 뽑는다.
**우리는 `rigid_from_normal()` 을 이미 갖고 있어서**, 공분산 누적만 벡터화하면 끝난다
(`np.add.at` 또는 라벨별 마스크 행렬곱). 이식 난이도: **낮음**.

> 여기서 만드는 공분산은 `sum_i v_h ⊗ u_h^T` 형태로, v01.02 의 `compute_vuT` 와 같은 4×4 구조다.
> **질량(3,3 성분)을 반드시 함께 들고 다녀야 한다** — v01.02 에서 이걸 놓쳐 버그가 났었다
> (가이드 §9 참고).

### 3-6. `DemBones.h:520` `labelToWeights()` — 라벨 → 0/1 웨이트

한 줄짜리. 라벨 위치에 1을 넣은 희소 행렬. 이식 난이도: **없음**.

### 3-7. `DemBonesExt.h:194` `computeCentroids()` + `:208` `computeBind()` — **조인트를 어디에 놓을 것인가** ★핵심

생성된 본의 **실제 위치**를 정하는 코드다. 이게 없으면 웨이트는 나와도 조인트를 만들 수 없다.

```cpp
c.col(j) += pow(w(j,i), transAffineNorm) * u_h(i)     // p 제곱 가중 누적
b.transVec(0,j) = c.col(j).head<3>() / c(3,j)         // p-norm 무게중심
```

즉 **웨이트를 4제곱해 가중한 무게중심**에 조인트를 놓는다. 제곱을 높게 주는 이유는
"그 본이 확실히 지배하는 영역"의 중심으로 당기기 위해서다(경계에 걸친 버텍스의 영향 축소).
회전은 **단위행렬**(축 정렬)로 둔다.

이식 난이도: **낮음** (`np.power` + 가중합).

### 3-8. `DemBonesExt.h:225` `computeRoot()` — 루트 본 고르기 (bindUpdate=2 용)

모든 버텍스를 자기 혼자로 설명했을 때 오차가 가장 작은 본 = 가장 "몸통"에 가까운 본을 루트로 삼는다.
`bone_errors()` 표의 **열 합이 최소인 열** 하나면 끝난다. 이식 난이도: **없음**.

---

## 4. 실제 리스크는 알고리즘이 아니라 **초기화 비용**

초기화 루프는 `split` → (`computeTransFromLabel` → `computeLabel` → `pruneBones`) × `nInitIters`
를 목표 본 개수에 닿을 때까지 반복한다. 본 개수가 1 → 2 → 4 → … 로 늘어나므로 바깥 루프가
`log2(nB)` 번쯤 돈다.

**매 안쪽 반복마다 `bone_errors()`(= `O(nV × nB × nF)`)가 필요하다.** v01.02 실측으로
20,000 버텍스 / 40 본 / 100 프레임에서 이 한 번이 **약 6초**다.

```
log2(20) ≈ 5 회  ×  nInitIters 10 회  =  50 회  ×  (본 개수에 비례하는 시간)
```

→ 그대로 옮기면 **수 분 ~ 십수 분**이 나온다. 완화책을 처음부터 설계에 넣어야 한다:

1. **초기화 전용 다운샘플링** — 초기화 단계에서만 버텍스를 (예: 1/4) 솎아 클러스터링하고,
   최종 라벨을 전체 버텍스에 최근접으로 퍼뜨린다. 비용이 선형으로 준다. **1순위 권장.**
2. **초기화 전용 프레임 서브샘플링** — 클러스터 구조를 잡는 데는 모든 프레임이 필요 없다.
   `Init Stride` 옵션(기본 4 정도).
3. **`nInitIters` 기본값을 낮게** — 원본 기본 10, 우리는 3~5로 시작하고 UI 에 노출.
4. **힙 루프는 `heapq`** (C 구현) 사용. `errorVtxBone` 은 표 조회이므로 힙 연산만 남는다
   (20k 버텍스 × 이웃 6 = 120k push ≈ 0.1초대).
5. **진행률/취소** — 이미 있는 `Progress` 를 초기화 단계에도 그대로 물린다.

---

## 5. 우리 코드에 필요한 소소한 추가

| 필요한 것 | 어디에 | 이유 |
|-----------|--------|------|
| **이웃 목록 API** `neighbors(i)` | `app/core/laplacian.py` | `split`/`computeLabel` 이 라플라시안을 **인접 구조로** 쓴다. 지금은 `(rows, cols, vals)` 만 있어 CSR 스타일 인덱스(`indptr`)를 하나 만들어 두면 된다 |
| 라벨 → 공분산 누적 | 새 `app/core/solver_init.py` | 3-5 |
| 조인트 생성 | 새 `app/core/joint_builder.py` | 계산된 바인드 위치에 `cmds.joint` 생성, 이름/계층/반경. 원본의 `FbxWriter.cpp:47 createJoints()` 가 참고가 된다(루트 vs limb, radius) |
| Full Decomposition 탭 | `app/ui/main_window.py` | Target Bones / Init Iterations / Init Stride / Bind Update(0·1·2) |

생성 후에는 **v01.02 자산을 그대로 재사용**한다: 웨이트는 `skin_writer.apply_weights`,
애니메이션은 `joint_writer.bake` (월드행렬 → xform → 키 → Euler Filter).

---

## 6. 참고만 하고 **옮기지 않는** ref 코드

| 코드 | 왜 안 옮기나 |
|------|--------------|
| `DemBonesExt.h:133` `computeRTB()` | 로컬 rot/trans 복원. 마야는 `cmds.xform(ws=True, matrix=)` 가 부모공간·jointOrient 까지 처리한다 |
| `DemBonesExt.h:245` `toRot()` | 오일러 플립 방지 전수탐색. 마야는 `cmds.filterCurve(filter="euler")` |
| `src/command/AbcReader.cpp` | 알렘빅 읽기. 우리는 씬에 임포트된 메시를 직접 평가한다 |
| `src/command/FbxReader.cpp` / `FbxWriter.cpp` | FBX I/O. 단 `FbxWriter.cpp:47` 의 조인트 생성 규칙은 **참고** |
| `LogMsg.*`, tclap, `MatBlocks.h`, `Indexing.h` | 로깅/인자파싱/Eigen 매크로 — numpy 에 대응물이 있거나 불필요 |
| `bin/Windows/DemBones.exe` | 브리지 방식은 fbx 왕복 리스크로 후순위 (계획서 §3) |

---

## 7. 검증 계획 — **원본 결과와 직접 대조할 수 있다**

`ref/data/` 에 원본 exe 가 만든 결과가 그대로 들어 있다. v01.03 은 이걸 정답지로 쓸 수 있는
**유일한 모드**다.

| 입력 | 원본 결과 | 확인할 것 |
|------|-----------|-----------|
| `Bone_Anim.abc` + `Bone_Geom.fbx`, `-b 5` | `Decomposition_05.fbx` | 본 개수, 조인트 위치 분포, 재구성 RMSE |
| 같은 입력, `-b 10` / `-b 20` | `Decomposition_10.fbx` / `_20.fbx` | 본 개수가 늘 때 RMSE 가 단조 감소하는지 |
| `-b 20 --bindUpdate=2` | `Decomposition_20_grouped.fbx` | 루트 선택 + 계층 구성 |

> **웨이트/조인트 위치가 원본과 똑같이 나올 것을 기대하면 안 된다.** 클러스터 초기화는 시드 선택에
> 민감하고, 해 자체가 유일하지 않다(계획서 §2.3 에서 확인한 성질). **비교 기준은 RMSE 와 본 개수**로
> 잡고, 위치는 "비슷한 분포인가"까지만 본다.

추가로 v01.02 와 같은 합성 왕복 검증을 한다: 아는 스켈레톤으로 만든 애니메이션을 캐시로 주고,
**조인트를 지운 뒤** 생성 모드로 복원 → 원래 조인트 개수/위치와 얼마나 가까운지.

---

## 8. 착수 시 순서 (제안)

1. `laplacian.py` 에 이웃 인덱스(CSR) 추가 + 단위 검증.
2. `solver_init.py`: `compute_trans_from_label` → `label_to_weights` → `compute_label` →
   `split` → `prune_bones` → `initialize(target_nb)`. **순수 numpy, mayapy 헤드리스로 검증.**
3. 다운샘플링/프레임 stride 를 붙여 20k 버텍스에서 **1분 이내**가 나오는지 실측.
4. `joint_builder.py`: 바인드 위치 → `cmds.joint` 생성(+ `bindUpdate=2` 면 루트 밑으로).
5. `dembone_manager.decompose_job()` + UI 탭.
6. `ref/data` 대조 검증 → 가이드/WORKLOG/포트폴리오 갱신.


---

## 9. 구현 결과 — 계획과 달라진 점 (2026-08-13)

세 가지가 계획과 달랐다. 둘은 **원본을 그대로 옮기면 동작하지 않아서** 바꾼 것이다.

### 9-1. 분할 씨앗을 키워야 했다 (원본 대비 변경)

원본 `split()` 은 새 클러스터를 **시드의 1링**(4~5 버텍스)만으로 심는다(DemBones.h:589).
그런데 그 몇 개로 맞춘 강체는 표본이 자유도에 비해 적어 오차가 크고, 바로 다음 `computeLabel`
에서 옆의 큰 클러스터에 통째로 먹힌 뒤 `pruneBones` 로 사라진다.

실측: 20,100 버텍스 원통에 목표 20개를 줘도 **2개에서 멈췄다**.
→ 씨앗을 클러스터 크기에 비례해(1/8, 최소 8개, 최대 절반) BFS 로 키우도록 `grow_patch()` 추가.

### 9-2. 라벨 확산의 우선순위를 바꿔야 했다 (원본 대비 변경) ★

원본은 우선순위 큐에 **절대 오차 `errorVtxBone(i, j)`** 를 넣는다(DemBones.h:485).
힙이 하나뿐이라 오차가 작은 본이 먼저 메시를 훑고 지나가고, 뒤늦게 차례가 온 본은
**이웃이 이미 전부 점령되어 확장할 곳이 없다**. 시드 하나만 쥔 채 굶다가 솎여 사라진다.

실측: 4개로 쪼갠 클러스터가 매 라운드 `[1, 1, 431, 359]` 로 무너져 목표 개수에 영영 도달하지 못했다.

→ 우선순위를 **"그 버텍스에서 최선의 본 대비 얼마나 나쁜가"** (`E - E.min(axis=1)`) 로 바꿨다.
그 버텍스의 주인은 0 에 가까운 값으로 즉시 자기 자리를 잡고, 남의 영역으로 넘어가려는 본은 값이
튀어 그 자리에서 멈춘다. **메시 연결성을 따라 자란다는 성질(클러스터가 조각나지 않는다)은 그대로**다.
검증에서 연결 성분 검사로 확인했다.

덤으로 각 본의 시드를 **미리 확정**해(다중 소스 다익스트라의 소스) 어떤 본도 0 버텍스로 굶지 않게 했다.

### 9-3. 다운샘플링은 프레임만 (계획 §4 대비 축소)

계획은 "초기화 전용 **버텍스** 다운샘플링"을 1순위로 뒀지만, 버텍스를 솎으면 **인접 그래프가
끊어져** 라벨 확산의 전제(연결성)가 깨진다(제대로 하려면 메시 데시메이션이 필요하다).
→ **프레임만 솎았다**(`Init Frames`, 기본 30). 클러스터 구조를 잡는 데는 포즈의 다양성이면 충분하다.

결과 실측: 20,100 버텍스 / 100 프레임에서 본 20개 생성이 **32.6초**(계획의 "수 분대" 우려 대비 충분).

### 9-4. 그 외

- `computeRoot` 는 계획대로 오차표의 열 합 최소로 구현(단일 루트 옵션).
- `computeCentroids` 는 계획대로 웨이트 p제곱 가중 무게중심(`joint_builder.bind_positions`).
- 조인트 생성 후 **바인드 행렬은 만든 노드에서 다시 읽는다** — 계층/jointOrient 로 값이 달라져도
  M 과 짝이 맞도록.
- `ref/data/Decomposition_*.fbx` 대조 검증은 **아직 못 했다**(§7). 합성 왕복 + 씬 재현 검증으로 대신했다.
