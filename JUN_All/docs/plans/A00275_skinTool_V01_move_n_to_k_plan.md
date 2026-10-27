---
title: A00275_skinTool_V01 — 조인트 n 개 → k 개 웨이트 이동 (Kangaroo SkinCluster > Move 이식) 계획서
aliases: [A00275 Move, move n to k, moveSkinClusterWeights port]
tags: [plan, maya-python, skin, skincluster, weights, kangaroo, A00275]
updated: 2026-10-27
---

# A00275_skinTool_V01 — 조인트 n 개 → k 개 웨이트 이동 계획서

> 작성 2026-10-27 · 상태: **설계 완료 · 결정 Q1~Q6 대기(§10) · 구현 전** · 아키텍처 (B) Maya 내 PySide 툴(기존 툴에 기능 추가)
>
> 원본(읽기 전용, 저장소 밖): `0020_maya_plugin/0010_kangaroo/scripts/`
> `kangarooTabTools/weights.py` `moveSkinClusterWeights()` (2767~2938행) ·
> `kangarooTools/xforms.py` `findClosestJoints()` (1058~1160행) ·
> `kangarooTools/patch.py` `smoothValues2d()` · `getNeighborDataForSmoothing()` · `setSkinClusterWeights()` · `getBorderMask()` · `_applyJointLocks()`.
> 아래 알고리즘 설명은 이 코드를 직접 읽고 쓴 것이다. Kangaroo 가 mayapy 에서 돌아가는 것도 확인했다(§8-1).

---

## 0. 요약

- **요청**: From 에 조인트 n 개, To 에 조인트 k 개를 나열하고, **From 조인트들이 웨이트를 가진 범위**의 웨이트를 To 조인트들로 옮긴다.
  Kangaroo `SkinCluster > Move` 와 **같은 결과**여야 한다.
- **Kangaroo Move 가 하는 일**:
  - 버텍스마다 **가장 가까운 To 조인트**를 고르고, From 웨이트를 그 조인트에 준다. 거리는 조인트 점이 아니라 **조인트 → 자식 조인트 선분**까지 잰다.
  - k 가 2 이상이면, To 조인트 사이 경계를 **이웃 평균 스무딩(기본 5회)** 으로 부드럽게 한다. 버텍스마다 옮기는 양의 합은 그대로 둔다.
  - 마지막으로 Blend · 소프트 셀렉션 · Joint Locks · Border Edges 마스크로 원래 웨이트와 섞는다.
- **지금 Classic 은 1:1 이다.** `Joints to Joints` 는 `From[i] → To[i]` 로 행 순서대로 짝짓고 개수가 다르면 거부한다. n → k 는 의미가 다른 새 기능이다.
- **구현 방침**:
  - 플러그인 없이 동작하는 **Native 이식**을 기본으로 한다. Kangaroo 엔진도 같은 버튼에서 고를 수 있게 한다(Classic · Transfer 와 같은 Engine 라디오).
  - 이웃 · 보더 마스크 · Joint Locks · 선택 파싱 · undo 되는 쓰기 · numpy 선택적 경로는 **Weights > Smooth(v01.31, Kangaroo Smooth 이식)에 이미 있다.** 이것을 재사용한다.
- **UI 위치** — 추천은 **Weights 아래 새 하위 탭 `Move`** 이다. 요청대로 Classic 에 버튼을 더하는 안도 같은 코어로 된다(§3, Q1).
- **검증** — 같은 씬에서 Native 결과와 Kangaroo `moveSkinClusterWeights` 결과를 **숫자로 대조**한다(허용 1e-6).

---

## 1. Kangaroo `moveSkinClusterWeights` — 알고리즘 (원본 그대로)

### 1-1. 입력과 기본값

```python
moveSkinClusterWeights(_pSelection=None, xJoints={}, fStrength=1.0, iSmoothSteps=5,
    iJointLocks=JointLocks.ignore, fBlend=1.0, iCheckMissingInfluences=askToAddOrCreateInfluences,
    xDistanceMeshes=None, iBorderEdges=BorderEdges.doEverything, iSmoothBorderMask=2,
    bDisableIslandCheck=False, iJointLines=JointLines.Yes, sChooseSkinCluster=None,
    bProjectSquashToMainJoints=True)
```

- `xJoints` = `{From: "To1; To2; ..."}`. 키와 값에 리스트 리터럴 문자열을 주면 펼친다.
  **n → k 는 `{"['f1', ..., 'fn']": "['t1', ..., 'tk']"}`** — From 마다 같은 To 목록 k 개가 된다.
  mayapy 에서 이 형식으로 실제로 돌려 확인했다(§8-1).
- 선택: 메시 통째 = 전체 버텍스, 컴포넌트 = 그 버텍스(`pSelected.aIds`), 소프트 셀렉션 = `aSofts`.

### 1-2. 단계

| # | 단계 | 원본 동작 |
|---|------|-----------|
| 1 | 섬 검사 | 컴포넌트 선택이 **섬(island) 2개 이상**에 걸치면 `confirmDialog("more than one islands ... Continue?")` (`bDisableIslandCheck` 로 끔) |
| 2 | From 거르기 | 선택 버텍스에서 웨이트가 **0 이 아닌** 인플루언스만 From 으로 남긴다(`_removeZeroInfluencesNumpy`, 1e-8 미만은 0). 남는 게 없으면 그 메시는 경고 후 건너뜀 |
| 3 | To 인플루언스 | To 가 skinCluster 에 없으면 `checkInfluences` — 기본은 **더할지 묻는다** |
| 4 | 웨이트 다시 읽기 | 선택 버텍스 행 x 인플루언스 열, `aWeightsOld` 복사 |
| 5 | **최근접 To** | k = 1 이면 전부 0번. 아니면 `findClosestJointsToPatchComponents` (§1-3) → 버텍스마다 To 인덱스 |
| 6 | From 마다 분배 | `A[i, v] = w_from[v]` (v 의 최근접이 To i 일 때), `w_from[v] -= 같은 값` (= 0) |
| 7 | **스무딩** (k ≥ 2, `iSmoothSteps` > 0) | `A` 를 버텍스 x k 로 놓고 `smoothValues2d(iIterations=iSmoothSteps)` (§1-4). 그 뒤 버텍스마다 **스무딩 전 합 / 스무딩 후 합**을 곱해 옮기는 양을 보존(합 0 이면 분모 1) |
| 8 | 더하기 | `w_to[i] += A[i]` |
| 9 | 쓰기 | `setSkinClusterWeights(aWeights, aOldWeights2d=aWeightsOld, fBlend=fBlend*fStrength, iJointLocks, iBorderEdges, iSmoothBorderMask, xDistanceMeshes)` (§1-5) |

- 6 ~ 8 은 **From 마다 따로** 돈다(원본 루프 그대로). 7 의 합 보존 때문에, From 들을 먼저 더하고 한 번에 스무딩하면 결과가 **달라진다**. 그래서 이식도 From 마다 따로 한다.
  최근접 To(5)는 From 과 상관없이 같으므로 **한 번만** 계산해도 결과가 같다(원본은 매번 다시 계산한다 — 성능만 다르다).
- From 조인트가 웨이트를 갖지 않은 버텍스는 `A` 가 0 이다. 스무딩으로 값이 번져 들어와도 7 의 "전 합 = 0" 때문에 0 으로 되돌아간다.
  → **From 이 영향을 미치는 범위 밖은 바뀌지 않는다**(요청의 "n 개 조인트가 영향을 미치는 범위").

### 1-3. 최근접 To 조인트 (`xforms.findClosestJoints`)

- 버텍스 위치 = `getPoints(bWorld=True)` — **지금 변형된 메시**의 월드 좌표다(바인드 포즈가 아니다).
- 조인트 위치 = `xform(ws, t)`. `bProjectSquashToMainJoints=True` 면 To 조인트에 `skinParent` 문자열 어트리뷰트가 있을 때 그 조인트 위치를 쓴다(Kangaroo 리그의 squash 조인트용, 없으면 아무 일 없음).
- **조인트 선분** (`iJointLines`):

| 값 | 원본 이름 | 동작 |
|----|-----------|------|
| 0 | `No` | 조인트 **점**까지 거리 |
| 1 | `Yes` (기본) | 조인트 → **자식 조인트** 선분까지 거리. 자식은 **To 목록에 든 것만** |
| 2 | `YesAndIncludeChildrenNotInInputForClosestJoints` | 자식이 To 목록 밖이어도 포함 |

  - 자식과 거리가 0.00001 이하면 선분을 만들지 않는다. 선분 끝은 **0.999 배**로 줄인다(자식 조인트 자리에서는 자식 쪽이 이기게).
  - 한 조인트에 자식이 여럿이면 그중 **가장 가까운 선분**이 그 조인트의 거리다. 자식이 없으면 점까지 거리다.
  - 버텍스마다 거리 최소인 To 를 고른다(`argmin`, 같으면 앞 번호).

### 1-4. 스무딩 (`smoothValues2d`, Move 에서 부르는 형태)

```
new[v] = ( A[v] + Σ A[nb] ) / (1 + 이웃 수)        # iIterations 번, Jacobi(전부 옛 값으로)
```

- **이웃은 선택 버텍스 안에서만 센다**(`bIncludeNeighborsNotInIds=False`). 여기가 Smooth 탭과 다르다 — Smooth 탭은 원본 `smoothSkinWeights` 를 따라 선택 밖 이웃도 읽는다.
- 이웃 = 엣지로 이어진 버텍스(`getNeighbors`), 자기 자신 포함, 가중치 없음(`bBarycentricWeighted=False`).

### 1-5. 쓰기 단계의 섞기 (`setSkinClusterWeights`, Move 가 넘기는 인자만)

순서대로:
1. `fBlend*fStrength != 1` → `w = w*b + old*(1-b)`
2. 소프트 셀렉션 → `w = w*soft + old*(1-soft)`
3. `xDistanceMeshes` (마스크 메시, `kt_findClosestPoints` 플러그인 필요) → **이식하지 않는다**(Smooth 와 같은 결정)
4. Joint Locks (`_applyJointLocks`) — `liw` 가 켜진 조인트: 1 = 값 고정 / 2 = 늘기만 / 3 = 줄기만, 나머지(free) 열을 `1 - 잠긴 합` 으로 다시 맞춤
5. Border Edges — `getBorderMask(iSmoothSteps=iSmoothBorderMask)`(메시 전체에서 경계 버텍스 1, 경계는 고정한 채 스무딩) 로 `w*mask + old*(1-mask)`. `onlyDoBorderEdges` 면 반전

---

## 2. A00275 에서 재사용할 것

| 필요한 것 | 이미 있는 곳 | 비고 |
|-----------|--------------|------|
| 선택 파싱(메시 · 컴포넌트 · 소프트 falloff, shell 제한) | `weight_smooth_manager.parse_selection` | Smooth 와 같은 선택 규칙 |
| 이웃 목록 | `weight_smooth_manager.connected_vertices` | Move 용으로 **선택 안으로 제한**하는 래퍼를 더한다 |
| 보더 마스크 | `weight_smooth_manager.border_mask(dag, steps, invert)` | 원본 `getBorderMask` 이식, 테스트 고정됨 |
| Joint Locks | `_lock_columns` · `_apply_locks_row` (+ numpy 경로) | 원본 `_applyJointLocks` 이식, 값까지 같은 상수(`LOCKS_*`) |
| 웨이트 읽기 / 쓰기 | `_read_weights`(API bulk) · `_write_weights`(**구간 setAttr → undo 됨**) | `MFnSkinCluster.setWeights` 는 undo 기록에 안 남는다(Classic Native 의 약점) |
| numpy 있으면 numpy, 없으면 순수 파이썬 | Smooth 의 두 경로 구조 | 결과가 같다는 테스트 방식도 그대로 |
| 인플루언스 추가 | `skin_migrate_manager._move_joints_native` 의 `skinCluster -addInfluence -weight 0` | |
| 셰이프 · skinCluster 찾기 | `Framework.core.maya_shape` · `maya_skin` | 셰이프가 여럿인 트랜스폼 대응이 이미 들어 있다 |
| Kangaroo import | `skin_migrate_manager._import_kangaroo` | Kangaroo 엔진용 |
| UI 리스트 | `JUN_mod_tsl_qt_v01` (Classic From/To 와 같은 위젯) | |

Smooth 의 내부 함수(`_read_weights` 등)를 Move 가 가져다 쓰게 되므로, 구현 첫 단계에서 둘이 같이 쓰는 함수를 `app/core/skin_weights_common.py` 로 옮기고 Smooth 는 그것을 import 한다.
이름과 동작은 그대로 두고, 회귀 시험(T1)으로 확인한다.

---

## 3. UI

### 3-1. 추천 — `Weights > Move` 새 하위 탭

Smooth 탭(Kangaroo Smooth 이식)과 같은 짜임이다. Classic 은 "레거시 2버튼 UI" 로 남긴다.

```
┌ Weights ─ Classic │ Transfer │ Migrate A -> B │ Copy Weights │ Layer │ Smooth │ [Move] ┐
│ Move weights from n joints to k joints (Kangaroo SkinCluster > Move).                 │
│ Engine    (o) Native   ( ) Kangaroo                                                   │
│ ┌ From (n) ─────────────────┐  ┌ To (k) ──────────────────┐                           │
│ │ jnt_A                      │  │ jnt_1                    │                           │
│ │ jnt_B                      │  │ jnt_2                    │                           │
│ │ [Select From][Add][Del]... │  │ [Select To][Add][Del]... │                           │
│ └────────────────────────────┘  └──────────────────────────┘                           │
│ ┌ Options ────────────────────────────────────────────────────────────────────────┐   │
│ │ Smooth Steps      [ 5 ]          Blend [=========|] 1.00                         │   │
│ │ Joint Lines       (o) Children in To list  ( ) All children  ( ) Points only     │   │
│ │ Joint Locks       (o) Ignore ( ) Keep locked ( ) Only add ( ) Only remove        │   │
│ │ Border Edges      (o) All ( ) Ignore borders ( ) Only borders   Mask Steps [ 2 ] │   │
│ │ [x] Use soft selection   [x] Project squash joints (skinParent)  [x] Island check │   │
│ │                                                          [Reset Options]         │   │
│ └──────────────────────────────────────────────────────────────────────────────────┘   │
│ [               Move weights  n -> k  on selected mesh / vertices               ]     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

- From · To 는 Classic 과 같은 `JUN_mod_tsl_qt_v01`. **개수 제약이 없다**(n, k ≥ 1, 같아도 된다).
  From 과 To 에 같은 조인트가 있으면 원본처럼 계산하고 `[Info]` 로그만 남긴다. 그 조인트의 웨이트도 To 들 사이에 거리대로 다시 나뉜다(Q5).
- 버튼 글자는 리스트 개수를 따라 `Move weights 2 -> 3` 처럼 바뀐다.
- Options 기본값 = 원본 기본값(Smooth Steps 5 · Blend 1 · Joint Lines Yes · Locks Ignore · Border All · Mask Steps 2 · Project squash ON · Island check ON).
- 앞으로 Move 쪽 기능(원본의 행별 매핑, 이름 치환 `"^, ns:"` 같은 것)이 더해지면 이 탭에 붙는다. "앞으로 요구할 사항에 더 적절한 UI" 라는 요청에 맞춘 배치다.

### 3-2. 대안 — Classic 탭에 버튼 하나

```
│ [ Joints to Joints (single mesh) ]
│ [ Meshes to Meshes ]
│ [ Joints n -> k (Kangaroo Move) ]   + 접이식 Move Options 그룹
```

- 요청 문구 그대로의 위치다. 기존 From/To 리스트를 같이 쓴다.
- 단점: 같은 두 리스트가 버튼마다 **1:1 짝 / 메시 짝 / n → k** 로 뜻이 바뀐다. Options 그룹 때문에 "레거시 2버튼" 화면이 길어진다.

**어느 쪽이든 코어(§4)는 같다.** 결정은 Q1.

---

## 4. 코어 설계 — `app/core/weight_move_manager.py` (신규, UI 비의존)

```python
JOINT_LINES_NO, JOINT_LINES_YES, JOINT_LINES_ALL_CHILDREN = 0, 1, 2      # 원본 JointLines 값 그대로
# LOCKS_* · BORDER_* 는 skin_weights_common 에서 (원본 값 그대로)

def move_weights(joints_from, joints_to, *, smooth_steps=5, blend=1.0,
                 joint_lines=JOINT_LINES_YES, joint_locks=LOCKS_IGNORE,
                 border_edges=BORDER_ALL, border_mask_steps=2,
                 use_soft_selection=True, project_squash=True, island_check=True,
                 confirm=None, engine="native"):
    """선택 메시(들)의 skinCluster 에서 joints_from(n) 의 웨이트를 joints_to(k) 로 옮긴다.
    confirm : 섬이 여럿일 때 부를 콜백(질문 문자열 -> bool). UI 가 QMessageBox 를 준다. None 이면 진행.
    반환 (ok, [로그])."""

def closest_targets(points, joints, joint_lines, project_squash):   # §1-3, 반환 버텍스마다 To 인덱스
def smooth_columns(values, ids, neighbors_in_ids, iterations):       # §1-4 (numpy / 순수 파이썬)
def distribute(weights, col_from, cols_to, closest, smooth_steps, smooth):   # §1-2 의 6~8
def finish(weights, old, blend, soft, locked, free, joint_locks, border, border_steps)   # §1-5
```

- 메시마다 하나의 undo chunk. 쓰기는 `_write_weights`(구간 setAttr)라 **Ctrl+Z 한 번에 원래대로**.
- From 중에 skinCluster 인플루언스가 아니거나 선택 범위에서 웨이트가 0 인 조인트는 `[SKIP]` 로그를 남긴다(원본은 조용히 건너뛴다).
- To 가 인플루언스가 아니면 weight 0 으로 더하고 `[Info]` 로그를 남긴다(Q4).
- Kangaroo 엔진은 `ktw.moveSkinClusterWeights(xJoints={"[f...]": "[t...]"}, ...)` 에 같은 옵션을 넘긴다.
  이 경우 `bDisableIslandCheck` 는 UI 의 Island check 를 반대로 넣고, To 추가는 원본처럼 Kangaroo 가 묻는다.
- 여러 메시를 선택하면 메시마다 따로 돈다(원본 `for pSelected in ...`).

### 성능 메모

- 최근접 계산은 버텍스 V x 선분 L. numpy 면 원본처럼 한 번에, 순수 파이썬이면 버텍스 루프(5만 버텍스 x 선분 30개 = 150만 번, 수 초)다.
- 스무딩은 Smooth 탭과 같은 비용이다(1.4만 버텍스 x 3열 x 4회 = 0.4초, numpy).
- 원본은 From 마다 최근접을 다시 구하지만 이식은 한 번만 구한다(§1-2, 결과 같음).

---

## 5. 파일

```
tools/A00275_skinTool_V01/
├── app/core/skin_weights_common.py   # 신규 - Smooth 에서 옮긴 공용 함수 (읽기/쓰기 · 이웃 · 보더 · 락 · 선택)
├── app/core/weight_smooth_manager.py # 위 모듈을 import (동작 불변)
├── app/core/weight_move_manager.py   # 신규 - n -> k 이동
├── app/ui/move_tab.py                # 신규 (Q1 = 하위 탭일 때) - 또는 main_window._build_classic_tab 에 버튼 + 옵션
├── app/ui/main_window.py             # WEIGHTS_PAGES 에 ("Move", ..., "_build_move_tab") 한 줄 + 핸들러
├── app/config/version.py             # 01.37
└── tests/test_weight_move.py         # 신규 - mayapy (아래 §8)
docs/A00275_skinTool_V01.md           # 탭 표 + "Weights > Move" 절
docs/WORKLOG.md · .claude/memory
```

---

## 6. 경계 사례

| 사례 | 처리 |
|------|------|
| From 과 To 가 겹침 | 원본처럼 계산 — 겹친 조인트의 웨이트도 To 들 사이에 거리대로 재분배된다. `[Info]` 로그 (Q5) |
| k = 1 | 최근접 · 스무딩을 건너뛴다(원본과 같음) — 단순 합치기 |
| 선택 버텍스가 From 웨이트 0 | 그 메시는 `[SKIP] no weight on From joints in the selection` |
| To 조인트에 자식 없음 | 점 거리(원본과 같음) |
| 조인트가 아닌 항목 · 없는 노드 | 리스트에서 빼고 `[WARN]`(원본은 `ls(et='joint')` 로 거름) |
| skinCluster 여럿 | Smooth 탭과 같이 첫 번째. 고르는 UI 는 Phase 2 (원본 `sChooseSkinCluster`) |
| 원본의 이름 패턴(`*`, `?`, `"찾기, 바꾸기"`) | Phase 1 은 리스트에 든 정확한 이름만. 패턴은 Kangaroo 엔진을 고르면 원본이 처리한다 |
| `xDistanceMeshes` | 이식 안 함(플러그인 명령 필요, Smooth 와 같은 결정) |

---

## 7. 작업 순서

| # | 작업 | 완료 조건 |
|---|------|-----------|
| T1 | `skin_weights_common.py` 로 공용 함수 옮기기 | Smooth 기존 동작 불변. Smooth 시험 스크립트는 저장소에 없으므로(문서의 53 항목은 당시 임시 스크립트) **옮기기 전에** 고정 씬의 Smooth 결과를 저장해 두고 옮긴 뒤 같은지 본다 → `tests/test_weight_smooth_regression.py` |
| T2 | `closest_targets` (§1-3) | Kangaroo `xforms.findClosestJoints` 와 인덱스 **완전히 같음**(Joint Lines 3모드, skinParent 유무, 자식 0 길이) |
| T3 | `smooth_columns` + `distribute` (§1-2 의 6~8, §1-4) | numpy = 순수 파이썬(1e-12), 버텍스별 이동량 합 보존 |
| T4 | `finish` (§1-5) + `move_weights` | **Kangaroo 대조 (§8-1) 1e-6 이내**, undo 한 번에 복원 |
| T5 | Kangaroo 엔진 경로 | Native 와 같은 씬에서 같은 결과 |
| T6 | UI (Q1 에 따라) + 핸들러 + 버전 01.37 | 오프스크린: 기본값 · 버튼 글자 · 리스트 · 실제 클릭 = 이동 + undo |
| T7 | 문서 · WORKLOG · 메모리 | |
| T8 | 마야 GUI 확인 (사용자) | 실제 캐릭터 메시에서 Kangaroo 탭 결과와 눈으로 비교 |

---

## 8. 검증

### 8-1. Kangaroo 대조 — 실행 가능 확인 (2026-10-27)

mayapy 2024 에서 Kangaroo 를 헤드리스로 돌렸다.

```python
sys.path.insert(0, r"...\0010_kangaroo\scripts")
cmds.loadPlugin(r"...\0010_kangaroo\plug-ins\win64\2024\kt_cmdUndo.py")   # 2022 ~ 2025 빌드가 있다
import kangarooTabTools.weights as ktw
import kangarooTools.report as rep
rep.report = _Dummy()          # UI 진행률 객체 - 헤드리스에서는 None 이라 빈 객체로 바꾼다
ktw.moveSkinClusterWeights(xJoints={"['fA','fB']": "['t1','t2','t3']"}, bDisableIslandCheck=True)
```

평면(21x5) · From 2 · To 3 에서 정상으로 돌았다. 예를 들어 버텍스 10 은 `t1 0.371 / t2 0.629` 로, 경계가 스무딩으로 섞여 있다.
→ 테스트는 **같은 씬을 두 번 만들어** Native 와 Kangaroo 를 각각 돌리고 웨이트 행렬 차이를 본다.

### 8-2. 대조 케이스 (전부 max |ΔW| < 1e-6)

| # | 씬 · 옵션 |
|---|-----------|
| 1 | 평면, n = 2, k = 3, 기본 옵션 |
| 2 | k = 1 (합치기) |
| 3 | 원통 + 조인트 체인(자식 있음), Joint Lines 0 / 1 / 2 |
| 4 | 컴포넌트 선택(일부 버텍스) — 선택 밖 불변, 선택 안 이웃 규칙 |
| 5 | 소프트 셀렉션 |
| 6 | Smooth Steps 0 / 5 / 20 |
| 7 | Blend 0.5 |
| 8 | Joint Locks 1 / 2 / 3 (잠긴 조인트 섞어서) |
| 9 | Border Edges 1 / 2, Mask Steps 0 / 2 (열린 경계가 있는 평면) |
| 10 | To 가 인플루언스가 아님 → 추가 후 이동 (Kangaroo 는 `iCheckMissingInfluences=onlyAddMissingInfluencesInSkinCluster` 로 묻지 않게) |
| 11 | `skinParent` 어트리뷰트가 있는 To 조인트 |
| 12 | 메시 2개 동시 선택 |

여기에 더해 항상 확인하는 것: 행 합 1 · From 범위 밖 불변 · **undo 한 번에 원래대로** · numpy 끈 경로 = numpy 경로 · 큰 메시(2만 버텍스) 시간.

### 8-3. 받아들임 기준

- A1 §8-2 의 12개 케이스 모두 Kangaroo 와 1e-6 이내
- A2 Ctrl+Z 한 번에 전부 복원
- A3 numpy 유무와 상관없이 같은 결과
- A4 기존 Classic · Smooth 동작 불변(회귀 시험)

---

## 9. 대상 환경

- Maya 2024(이 PC 확인)에 더해, 저장소 관례대로 **Maya 2023 에서도 돌게** 한다. Python 3.7 문법, numpy 는 선택(없으면 순수 파이썬), API 2.0 · PySide2.
  2023 실기 확인은 이 PC 에서는 못 한다.

---

## 10. 결정이 필요한 것

| # | 질문 | 추천 |
|---|------|------|
| Q1 | UI 위치 | **`Weights > Move` 새 하위 탭** — Classic 의 1:1 리스트와 뜻이 섞이지 않고, Kangaroo Move 의 옵션 8개와 앞으로 붙을 Move 기능을 담을 자리가 있다. 요청대로 Classic 에 버튼을 더하는 것도 코어는 같다 |
| Q2 | 엔진 | **Native(기본) + Kangaroo 라디오** — Classic · Transfer 와 같은 짜임. Native 는 undo 가 되고 플러그인이 필요 없다 |
| Q3 | 섬 검사 | **원본처럼 묻는다**(Yes / No, 옵션으로 끔) |
| Q4 | To 가 인플루언스가 아닐 때 | **묻지 않고 weight 0 으로 더한다** + 로그 (Classic Native 와 같은 동작). 원본은 묻는다 |
| Q5 | From · To 겹침 | **원본처럼 계산**(겹친 조인트의 웨이트도 To 들 사이에 거리대로 재분배) + 로그. "Kangaroo 와 정확히 같게" 가 요청이라서다. 빼면 그 조인트의 웨이트가 그대로 남아 결과가 달라진다 |
| Q6 | 버텍스 위치 | **원본처럼 지금 변형된 메시** 기준. 포즈를 잡은 상태에서 돌리면 그 포즈 기준으로 최근접이 정해진다는 것을 문서에 적는다 |
