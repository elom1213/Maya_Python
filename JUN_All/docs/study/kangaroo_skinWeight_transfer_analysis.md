# Kangaroo 스킨 웨이트 전이 — 코드 레벨 심층 분석

> **주제**: Kangaroo Builder(Thomas Bittner) 플러그인이 스킨 웨이트를 실제로 어떻게 전이하는지
> **소스 코드를 직접 분석**하고, Maya 기본 `Copy Skin Weights`(`copySkinWeights`)와 무엇이 다른지 정리.
>
> **분석 대상**(외부/서드파티, **읽기 전용** — 절대 수정 금지):
> - `...\0020_maya_plugin\0010_kangaroo\scripts\kangarooTabTools\weights.py`
>   — `transferSkinCluster`(L1823), `intTransferSkinCluster`(L2134), `moveSkinClusterWeights`(L2774)
> - `...\kangarooTools\barycentric.py` — `getVertexCoordinates`(L34), `getBarycentricCoords`(L132)
> - `...\kangarooTools\patch.py` — `setSkinClusterWeights`(L320), enum(`BorderEdges`/`MissingInfluencesOptions`/`JointLocks`)
> - `kt_findClosestPoints.mll` — 최근접점 질의를 담당하는 **C++ 컴파일 플러그인**(소스 비공개)
>
> 관련 문서: [skinWeight_transfer_workflow.md](skinWeight_transfer_workflow.md)(작업 워크플로우 관점),
> 연계 툴: `JUN_All/tools/A00020_move_skineWeightTool`, 계획: `A00270_skinMigrate`.

---

## 0. 먼저 — "전이"는 사실 **두 개의 다른 기능**이다

기존 워크플로우 노트는 둘을 뭉뚱그렸지만, 코드상 완전히 별개의 함수·알고리즘이다. 혼동하면 안 된다.

| 기능 | 함수 | 방향 | 하는 일 |
|------|------|------|---------|
| **Transfer** | `transferSkinCluster` | **메시 A → 메시 B** | 토폴로지가 다른 두 메시 사이에서, 공간 최근접 대응으로 웨이트를 옮긴다 |
| **Move** | `moveSkinClusterWeights` | **조인트 X → 조인트 Y** (같은 메시 내) | 한 본이 가진 웨이트를 다른 본(들)으로 재분배한다. 본 이름이 바뀐 리그로 넘어갈 때 사용 |
| (보조) IntTransfer | `intTransferSkinCluster` | **같은 메시 내 영역 → 영역** | 선택 안 된 부분에서 선택된 버텍스로 웨이트를 채운다(구멍 메꾸기) |

A00020 툴이 부르는 `transferSkinCluster`(전이) + `moveSkinClusterWeights`(본 이동)가 바로 이 둘이다.
아래 2장이 Transfer, 3장이 Move 다.

---

## 1. 전체 파이프라인 한눈에 (Transfer)

```
 대상 메시 B (무웨이트)                     소스 메시 A (웨이트 O)
        │                                          │
        │  ① 각 B 버텍스마다 A 표면 최근접점 질의    │
        └──────────►  cmds.kt_findClosestPoints  ◄──┘   (C++ .mll)
                          │  returnFaces=True, returnDistances=True
                          ▼
        각 B 버텍스 → (닿은 A 면 faceId, 최근접점 xyz, 거리)
                          │
        ② 소스가 여러 개면 argmin(거리)로 per-vertex 최근접 소스 선택
                          │
        ③ barycentric.getBarycentricCoords : 최근접점을 그 A 면의
           꼭짓점(3~4개)에 대한 **무게중심 좌표**로 분해
                          │
        ④ numpy: 대상 웨이트 = Σ(면 꼭짓점 웨이트 × 무게중심 좌표)
           - 인플루언스(조인트)는 **이름 기준**으로 union/합산
                          │
        ⑤ patch.setSkinClusterWeights : 0-인플루언스 prune → 누락 본 처리
           → 조인트 잠금 → 경계엣지 스무딩 → blend → normalize → 적용
                          ▼
                    대상 메시 B 의 skinCluster
```

핵심은 **③ 무게중심 보간**과 **①의 C++ 최근접점 질의**, 그리고 **전 과정이 numpy 벡터 연산**이라는 점이다.

---

## 2. Transfer 상세 분석

### 2-1. TransferMode — 6가지 대응 방식 (`weights.py` L1808)

```python
class TransferMode:
    vertexIndex   = 0   # 버텍스 인덱스 1:1 (동일 토폴로지 전용)
    closestVertex = 1   # 최근접 '버텍스' → 그 버텍스 웨이트를 그대로 복사
    closestPoint  = 2   # 최근접 '표면점' → 그 면의 무게중심 보간 (기본값)
    closestUV     = 3   # UV 공간 최근접 버텍스
    closestUVPoint= 4   # UV 공간 최근접 표면점 (무게중심 보간)
    spikes        = 5   # 헤어/커브용 특수 모드 (아일랜드 중심을 잇는 커브로 대응)
```

- **직접 복사** 계열(`vertexIndex`, `closestVertex`, `closestUV`, 코드상 `iMode in [0,1,3]`, L2074):
  대응된 소스 버텍스의 웨이트 행을 **그대로** 대상에 복사한다.
- **무게중심 보간** 계열(`closestPoint`, `closestUVPoint`, `spikes`, `iMode in [2,4,5]`, L2076):
  `대상웨이트 = Σ(면꼭짓점웨이트 × 무게중심좌표)` — 최근접점이 면 안에서 어디에 찍혔는지에 따라
  3~4개 꼭짓점 웨이트를 섞는다. 기본값 `closestPoint`가 여기 속한다.

### 2-2. ① 최근접점 질의 = C++ 플러그인 (`barycentric.py` L71)

```python
fClosestArray = cmds.kt_findClosestPoints(
    fromMesh=대상B, toMesh=소스A, skip=제외컴포넌트,
    vertex=bClosestVertex, returnFaces=True, mirror=..., doUvs=..., returnDistances=True)
```

- 각 **대상 B 버텍스**에 대해 **소스 A 표면의 최근접점**을 찾는다. 면 모드 반환은 버텍스당
  `[closestX, closestY, closestZ, distance, faceId]` 5개 값(L87), 버텍스 모드는 `[vertId, distance]`.
- 이 질의는 **`kt_findClosestPoints.mll`(컴파일된 C++)** 이 담당한다 → Python 루프 없이 빠르다.
  (스킨클러스터 툴은 이 플러그인 라이선스가 필요한 이유이기도 하다.)
- `skip=` 로 **소스의 특정 면/버텍스를 대응에서 제외**할 수 있다(영역 한정 전이의 기반).

### 2-3. ② 멀티 소스 = per-vertex 최근접 소스 선택 (`barycentric.py` L92)

```python
aClosestMeshes = np.argmin(aDistances, axis=0)
```

소스 메시를 **여러 개** 줄 수 있고, **대상 버텍스마다** 그중 표면이 가장 가까운 소스를 고른다.
즉 "몸통은 A1에서, 손은 A2에서" 같은 혼합 전이가 **한 번의 호출**로 된다.
(Maya 기본 `copySkinWeights`는 소스가 원칙적으로 하나다.)

### 2-4. ③ 무게중심 좌표 — 삼각형/쿼드/라인/포인트 모두 지원 (`barycentric.py` L132)

- **삼각형**(L201): 표준 **부분삼각형 넓이비**로 무게중심 좌표를 구한다
  (`w_i = area(반대편 서브삼각형) / area(전체)`).
- **쿼드**(L136): 삼각화하지 않고, 네 변에 대한 최근접 파라미터로 중점을 잡아 **넓이 기반 이중선형(bilinear)
  유사** 좌표를 직접 계산한다. → **Maya가 쿼드를 삼각화하며 생기는 대각선 편향이 없다.**
- **라인/포인트**(L221, L232): 커브·단일점 대상까지 커버(길이비 / 100%).
- 퇴화면(넓이 0)은 `0.25×4`(쿼드) 등으로 안전 폴백.

### 2-5. ④ 인플루언스(조인트) 대응 = **이름 기준 union** (`weights.py` L2037~L2077)

```python
aAllInfluences = np.unique(sReducedInfluences)        # 모든 소스의 조인트 이름을 합집합
dAllInfluences = {이름: 열인덱스}                       # 이름 → 웨이트 행렬 열
```

- 대응은 인덱스가 아니라 **조인트 이름**으로 한다. 여러 소스의 조인트를 **union**해 하나의 웨이트 행렬로 합친다.
- 같은 이름 조인트가 소스에 중복되면 **웨이트를 합산**해 하나로 접는다(L2040~L2050).
- **`funcMapJoint`**(L2038): 전이 도중 조인트 이름을 **매핑(치환)** 하는 콜백. 소스와 타겟의 본 이름
  체계가 달라도 전이 시점에 이름을 바꿔 맞출 수 있다. (별도 Move 단계 없이 이름 차이 흡수)
- `sJointsOverride`(L2056): 소스 조인트 목록을 통째로 다른 목록으로 교체.
- 메시 이름 `"찾을것,바꿀것"` 패턴(L1885)으로 **다수 메시를 이름 규칙으로 짝지어 일괄 전이**.

### 2-6. ⑤ 적용 전 후처리 (`transferSkinCluster` 끝 + `patch.setSkinClusterWeights`)

전이한 raw 웨이트를 바로 쓰지 않고 일련의 후처리를 **인자 하나로** 태운다:

| 인자 | 의미 |
|------|------|
| `_removeZeroInfluencesNumpy` (L2101) | 기여 0인 조인트 열을 **prune** 후 적용(불필요 인플루언스 미생성) |
| `iCheckMissingInfluences` | 타겟 skinCluster에 소스 본이 없을 때: skip / **skinCluster에만 추가** / **씬에 본 생성+추가** / 물어보기 |
| `iJointLocks` | 잠긴 조인트 보존 / 잠긴 곳에만 추가 / 잠긴 곳에서만 제거 등 |
| `iBorderEdges` + `iSmoothBorderMask` | **열린 경계 엣지** 밴드를 N링 **스무딩**(경계는 최근접 전이가 가장 불안정한 곳) |
| `fBlend` | 기존 웨이트와 전이 결과를 0~1로 **블렌드**(부분 적용) |
| `bPostNormalize` | 적용 후 재정규화 |
| `bAutoCreateNewSkinCluster` | 타겟에 skinCluster가 없으면 **정확히 필요한 본만으로 새로 생성**(L2079~) |
| `xDistanceMeshes` | 거리 마스크 메시로 영향 범위 제한 |

> 이 "전이 + prune + 누락본 처리 + 경계 스무딩 + normalize + skinCluster 생성"이 **한 함수 호출**에
> 들어있다는 점이 Kangaroo의 특징이다.

---

## 3. Move 상세 분석 — 조인트→조인트 재분배 (`weights.py` L2774)

`transferSkinCluster`와 **완전히 다른 알고리즘**이다. 메시는 그대로 두고 **본 사이에서** 웨이트를 옮긴다.

1. **매핑 파싱**: `xJoints = {소스본: "타겟본들"}`. 소스 이름에 `* ?` **와일드카드**, 타겟에 `"찾기,바꾸기"`
   **정규식 치환**·네임스페이스 지정 가능(L2782, L2844). 예: `"^, ns0:"` → 같은 본을 `ns0:` 네임스페이스로.
2. **다중 타겟이면 per-vertex 최근접 본 배정**(L2901):
   `xforms.findClosestJointsToPatchComponents(...)` — 각 버텍스를 **가장 가까운 타겟 본**에 배정한다.
   이때 `JointLines`(본을 잇는 **선분/세그먼트** 기준 거리)·`skinParent` 투영 옵션으로 스쿼시 조인트를
   메인 조인트로 투영하는 등 리깅 구조를 반영한다.
3. **소스 본 웨이트를 그 배정에 따라 타겟 본들로 이전**(L2905~L2908): 소스 열에서 빼고 타겟 열에 더한다.
4. **스무딩 + 재정규화**(L2911~L2920): 분배 결과를 N스텝 스무딩하되, **이전량 총합을 보존**하도록
   스무딩 전/후 합의 비로 되돌린다(경계가 매끄러우면서 총 웨이트 불변).
5. `setSkinClusterWeights`로 2-6과 동일한 후처리를 태워 적용.

→ Maya 기본 기능에는 이 "본→본 재분배(최근접 본 배정 + 스무딩)"에 **정확히 대응하는 단일 명령이 없다**.
   (수작업이면 `skinPercent`로 일일이 옮기거나 Influence를 지워 재분배해야 한다.)

---

## 4. Maya 기본 `Copy Skin Weights`와의 차이

Maya 네이티브 `copySkinWeights`(Copy Skin Weights)도 내부적으로 C++ 최근접점 대응을 쓴다. 큰 그림
("표면 최근접 대응으로 웨이트를 옮긴다")은 같다. 다른 점은 **주변부와 통합·제어**에 있다.

| 항목 | Maya `copySkinWeights` | Kangaroo `transferSkinCluster` |
|------|------------------------|-------------------------------|
| 표면 대응 | `surfaceAssociation` = closestPoint / closestComponent / rayCast / **uvSpace** | closestPoint / closestVertex / **closestUV / closestUVPoint** / vertexIndex / **spikes** |
| 쿼드 보간 | 내부 **삼각화** 후 보간 | **쿼드 전용 넓이기반** 무게중심(대각선 편향 없음) |
| 소스 개수 | 원칙적으로 **1개** 소스 deformer | **N개** 소스, **버텍스마다 최근접 소스 자동 선택** |
| 인플루언스 대응 | `influenceAssociation` = closestJoint / closestBone / label / **name** / oneToOne (휴리스틱 폴백 최대 3단) | **이름 union + 중복 합산**, `funcMapJoint`로 **이름 매핑**, override 목록 |
| 본 이름 다를 때 | label/closestJoint 휴리스틱에 의존 | 전이 중 이름 치환 or 이후 **Move**로 명시적 재배정 |
| 타겟 준비 | 타겟에 **skinCluster 선존재** 필요(없으면 별도 바인드) | `bAutoCreateNewSkinCluster`로 **필요한 본만으로 자동 생성** |
| 경계 처리 | 별도 옵션 없음 | **열린 경계 엣지 스무딩 마스크**(`iBorderEdges`/`iSmoothBorderMask`) |
| 게임 후처리 | 명령 안에 없음(별도 `skinPercent -pruneWeights`, maxInf) | prune 0-inf, `fBlend`, `bPostNormalize`, 조인트 잠금 처리 **내장** |
| 영역 한정 | 컴포넌트 선택으로 대상만 제한 | 대상 **및 소스** 면/버텍스 `skip` 제한 |
| 미러 | 없음(별도 미러 도구 필요) | `bMirror`로 **같은 호출에서 미러 전이** |
| 구현 | Maya deformer/명령(블랙박스) | **numpy 벡터 연산 + C++ 최근접점**(중간 결과 접근·조합 가능) |
| 본→본 재분배 | 대응 명령 없음 | 별도 **`moveSkinClusterWeights`** 제공 |

**요지**: 대응 원리(closest-point + 무게중심)는 네이티브와 본질적으로 같다. Kangaroo가 실질적으로
다른 부분은 ① **쿼드 정확도**, ② **멀티 소스 per-vertex 선택**, ③ **이름 기반 인플루언스 통합·매핑**,
④ **경계 스무딩·prune·normalize·skinCluster 자동생성 같은 후처리를 한 호출에 통합**, ⑤ **본→본
Move라는 별도 도구**다. 즉 "더 똑똑한 대응"이라기보다 **파이프라인 전체를 제어·자동화**하는 데 강점이 있다.

---

## 5. 게임 파이프라인 관점 시사점 (이 repo 연계)

- [skinWeight_transfer_workflow.md](skinWeight_transfer_workflow.md)의 "Shrink Wrap 정렬 → 전이 → 정리"
  워크플로우에서, **전이 단계**가 바로 `transferSkinCluster(closestPoint)`이다. 정렬이 좋을수록
  최근접점이 올바른 면에 찍혀 무게중심 보간이 정확해진다 — **정렬 = 대응 오차 최소화**라는 그 문서의
  통찰이 코드로 확인된다.
- 게임용 후처리(maxInfluences 4, prune, normalize)는 Kangaroo가 `bPostNormalize`·prune·`iJointLocks`로
  일부 내장하지만, **maxInfluences 제한(`reduceInfluences`, L3117)·`checkMaxInfluences`(L3100)** 는
  전이와 **별도 호출**이다 → A00020/A00270에서 전이 직후 이 단계를 반드시 이어붙여야 한다.
- **본 이름이 다른 리그로 이관**할 때: `funcMapJoint`(전이 중 매핑) 또는 전이 후 `moveSkinClusterWeights`
  (본→본 재배정) 두 경로가 있다. A00270_skinMigrate가 묶으려는 "Transfer + Move"가 바로 이 조합이다.
- 경계·손가락 사이 등 최근접 전이의 약점 구역은 `iBorderEdges`/`iSmoothBorderMask`·`skip`(영역 한정)으로
  Kangaroo가 이미 완화 장치를 제공한다 — 워크플로우 노트의 "구역별 분할 전이" 개선안과 맞닿는다.

---

## 6. 한 줄 요약

> Kangaroo의 웨이트 전이는 **C++ 최근접점 질의 + 면 무게중심 보간 + 전(全)과정 numpy 벡터화**가 뼈대이며,
> Maya `copySkinWeights`와 대응 원리는 같지만 **쿼드 정확도·멀티소스 per-vertex 선택·이름 기반 인플루언스
> 통합/매핑·경계 스무딩과 prune/normalize/skinCluster 자동생성의 한-호출 통합·본→본 Move**로 차별화된다.
> 즉 강점은 "더 똑똑한 대응"이 아니라 **전이 파이프라인의 제어·자동화·게임 후처리 친화성**이다.
