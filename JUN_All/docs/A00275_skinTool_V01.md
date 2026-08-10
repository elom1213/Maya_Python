---
title: A00275_skinTool_V01 사용법
aliases: [Skin Tool, SkinTool, A00275, Update Bind Pose, Move Joints]
tags: [maya-python, tool-guide, skin, skincluster, bind-pose, rigging]
updated: 2026-08-10
---

# A00275_skinTool_V01 사용법

스킨 관련 **범용** in-Maya PySide 툴(arch B). `A00270_skinMigrate` 의 기능을 그대로 담고,
**Transfer · Bind Pose 탭**을 추가했다. (`A00270_skinMigrate` 는 그대로 남아 있다.)

- **버전**: `app/config/version.py` (v01.08)
- **설치**: `__dragDrop_A00275.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **SkinTool** → `tools.A00275_skinTool_V01.run(True)`

| 탭 | 내용 |
|----|------|
| **Classic** | 레거시 2버튼 UI — `Joints to Joints (single mesh)` / `Meshes to Meshes`. **Engine(Kangaroo/Native) 선택**(v01.04~) |
| **Transfer** (v01.04~) | **여러 소스 메시 → 현재 선택한 하나의 메시**로 웨이트 전이. **Engine(Native/Kangaroo) 선택**(v01.05~). 선택 버텍스에만/소프트 falloff 반영(Native) |
| **Migrate A -> B** | 토폴로지가 다른 두 메시 사이 Transfer + Move 통합 마이그레이션 |
| **Bind Pose** | **조인트를 이동·회전한 현재 상태를 새 바인드 포즈로** |
| **Move Joints** (v01.08~) | **Edit 토글** — 켜면 조인트를 옮겨도 메시가 변형되지 않고, 다시 끄면 그 자리에서 재바인드. **웨이트 불변** |

Migrate 탭 사용법은 [[A00270_skinMigrate]] 문서와 동일하다.

> **Bind Pose 와 Move Joints 의 차이**
> 둘 다 "조인트를 옮기고 다시 바인드" 지만 **순서가 반대**다.
> - **Bind Pose** : 먼저 조인트를 옮긴다(메시가 변형된다) → 버튼을 눌러 **그 결과를 굳힌다**.
> - **Move Joints** : 먼저 Edit 을 켠다 → **메시가 전혀 안 변하는 상태로** 조인트를 옮긴다 → Edit 을 끈다.
>
> 스켈레톤 배치를 손보는 게 목적이면 **Move Joints** 가 맞다. 형상 델타를 굽지 않으므로
> Orig 셰이프도 blendShape 도 건드리지 않는다.

---

## Classic 탭 — Engine 선택 (v01.04~)

`Joints to Joints (single mesh)` / `Meshes to Meshes` 두 버튼은 이제 **Engine** 을 고를 수 있다.

- **Kangaroo** — Kangaroo Builder 플러그인 사용(로드돼 있어야 함).
- **Native** — 플러그인 무의존.
  - `Joints to Joints` = 선택 메시 skinCluster 에서 **From 본 컬럼 → To 본 컬럼**으로 이동(`maya.api`).
  - `Meshes to Meshes` = rebind 후 `cmds.copySkinWeights`(Transfer Mode 의 surfaceAssociation).
  - Native 이동은 `setWeights` 를 써서 undo 가 세밀하지 않다(전체가 한 스텝).

---

## Transfer 탭 — 여러 소스 → 선택 메시 (v01.04~)

Kangaroo 의 *SkinCluster > Transfer* 를 흉내낸 기능. **여러 소스 메시로부터 현재 선택한
메시(들)** 로 스킨 웨이트를 전이한다. **Engine** 을 고를 수 있다(v01.05~):

- **Native**(기본) — 플러그인 무의존. **선택 버텍스에만 전이 + 소프트 falloff** 를 지원한다(아래).
- **Kangaroo** — Kangaroo `transferSkinCluster`(플러그인 필요). 컴포넌트/부분 전이는 Kangaroo 로직을
  따른다. soft falloff 옵션은 Native 전용이라 Kangaroo 를 고르면 비활성된다.

### 사용법

1. 소스 메시들을 선택 → **Select Source Meshes** 로 `Source Meshes` 리스트에 담는다(여러 개 가능).
2. 씬에서 **대상 메시(들)를 선택**한다(v01.06~ **여러 개 동시 가능**). 어떤 메시의 **버텍스를 선택하면
   그 메시는 그 버텍스에만** 전이된다. (소프트 셀렉션을 켜면 falloff 까지 반영된다.)
3. **TRANSFER to selected mesh(es)** — 선택한 **모든** 대상 메시에 전이되고, 전체가 **한 번의 undo** 로 묶인다.

### 동작

- **여러 대상 메시** (v01.06~) — 선택한 메시를 **각각** 전이한다. 소스로 쓴 메시가 선택에 섞여 있으면
  자동으로 대상에서 제외한다.
- **Mode = Closest Point** 고정. 소스가 여럿이면 **버텍스별로 가장 가까운 소스**를 자동 선택한다.
- **선택 버텍스에만 전이** — 타겟의 버텍스를 골라두면 **그 버텍스만** 바뀌고 나머지는 **아예 손대지 않는다**.
- **소프트 셀렉션 falloff** — `Respect soft selection falloff` 가 켜져 있고 소프트 셀렉션이 활성이면,
  falloff 비율 `f` 로 `원본 ↔ 전이결과` 를 블렌드한다(중심 f=1, 가장자리 f→0).
- **연결 shell 로 제한** (v01.07~) — 소프트 셀렉션은 **하드 선택이 속한 연결 shell(island)** 로 제한된다.
  여러 조각이 하나로 **combine 된 메시**에서 소프트 셀렉션 **Volume** falloff 가 붙어 있지 않은 근접
  shell 까지 범위로 잡더라도, 그 떨어진 shell 은 **전이 대상에서 제외(방치)** 된다.

### 구현 메모 (mayapy 로 검증)

- 무거운 최근접-점 계산(면 barycentric 샘플링)은 `cmds.copySkinWeights(surfaceAssociation="closestPoint")`
  가 정확히 해 준다. **소스 메시 여러 개를 함께 선택하면 버텍스별 최근접 소스를 알아서 고른다**(검증됨).
- **전체 전이**(버텍스 선택 없음)는 대상에 바로 copySkinWeights 한다(undo 깔끔, 빠름).
- **부분 전이**(버텍스 선택)는 대상에 copySkinWeights(전체) 한 뒤, 선택 전/후 웨이트를 **maya.api 벌크
  read** 로 읽어 선택 버텍스는 `before + (after-before)*f`(f=falloff) 로 블렌드하고 미선택은 `before`
  로 되돌려 **한 번의 벌크 `setWeights`** 로 쓴다. 대용량 메시에서도 빠르다(3.1k 버텍스 combine 메시에서
  약 0.05s). 단, 벌크 `setWeights` 라 **부분 전이의 undo 는 세밀하지 않다**(속도 우선).
- **소프트 falloff 는 셰이프 MObject 노드로 매칭**한다(v01.07~). 리치 셀렉션 컴포넌트는 셰이프 DAG 를
  주므로 문자열 경로로 비교하면 combine/rename 메시에서 틀어져 `kInvalidParameter` 로 이어졌다.
  이제 컴포넌트의 셰이프 노드와 대상 셰이프 노드를 직접 비교한다(`_shape_node`).
- **연결 shell 은 `MFnMesh.getVertices()` 한 번의 벌크 호출 + 파이썬 BFS**(`_connected_island`)로 구한다.
  하드 선택에서 이어진 버텍스만 남겨, combine 메시의 떨어진 shell 을 소프트 셀렉션에서 걸러낸다
  (버텍스별 반복 없이 빠름 — 3.1k 버텍스에서 0.007s).

---

## 1. Bind Pose 탭 — 무엇을 하는 기능인가

리깅된 캐릭터의 조인트를 옮기거나 돌리면 바인드된 메시가 따라 변형된다.
이때 마야의 **Go to Bind Pose** 를 누르면 **원래** 바인드 포즈로 되돌아간다.

이 탭은 **지금 이 상태가 바인드 포즈가 되게** 만든다. 실행 후에는 Go to Bind Pose 가
이 상태로 돌아온다.

```
┌ Bind Pose ─────────────────────────────┐
│ ┌ Target ────────────────────────────┐ │
│ │ skinCluster1 | body | 54 influence │ │
│ │ [ Load Selection ]      [ Clear ]  │ │
│ └────────────────────────────────────┘ │
│ ┌ Mode ──────────────────────────────┐ │
│ │ (o) Keep current shape             │ │  ← 기본
│ │ ( ) Snap mesh to rest shape        │ │
│ │ [x] Rebuild bindPose node          │ │
│ └────────────────────────────────────┘ │
│ [       UPDATE BIND POSE       ]       │
└────────────────────────────────────────┘
```

### 사용법

1. 조인트를 원하는 대로 이동·회전한다.
2. **바인드된 메시를 선택**하거나 **그 조인트들을 선택**한 뒤 **Load Selection**.
3. 모드를 고르고 **UPDATE BIND POSE**. 전체가 **한 번의 Ctrl+Z** 로 되돌아간다.

### 두 가지 모드

| 모드 | 메시 | 쓰는 상황 |
|------|------|-----------|
| **Keep current shape** (기본) | **눈에 띄게 움직이지 않는다.** 지금 보이는 변형된 형상이 그대로 새 rest 가 된다 | 포즈를 잡아 놓고 "이 모양을 기준으로" 굳히고 싶을 때 |
| **Snap mesh to rest shape** | 변형이 풀려 **원래 형상으로 돌아간다**(조인트는 옮긴 자리 그대로) | 조인트 위치만 고치고 메시는 원래대로 두고 싶을 때. 마야의 `Move Skinned Joints Tool` 과 같은 결과 |

**Rebuild bindPose node**(기본 켜짐)를 끄면 `bindPose` 노드를 건드리지 않는다. 즉 스킨 계산은
갱신되지만 Go to Bind Pose 는 옛 포즈로 간다. 특별한 이유가 없으면 켜 둔다.

### 지원 범위

- 메시 선택 / 조인트 선택 둘 다 가능
- **여러 skinCluster 동시 처리**
- **blendShape 등 다른 히스토리가 있어도 동작**하고, 그 히스토리는 보존된다(스킨 앞/뒤 무관)
- 메시 트랜스폼이 원점이 아니어도, 루트 조인트 자체를 옮겨도 동작

### 로그에 뜨는 경고 대응법

| 메시지 | 뜻 / 대응 |
|--------|-----------|
| `... is not polygon mesh data` / `input geometry is nurbsSurface` | 대상이 **폴리곤 메시가 아니다**(nurbsSurface·curve·lattice). `Keep current shape` 는 메시에서만 형상을 구울 수 있다. **`Snap mesh to rest shape` 로 실행**하면 정상 동작한다(바인드 행렬만 갱신하므로 지오 타입과 무관). |
| `bindPreMatrix is locked or connected for ...` | 해당 인플루언스의 `bindPreMatrix` 가 **잠겨 있거나 다른 노드에서 연결**돼 있어 건드리지 않았다. 그 조인트만 갱신에서 빠진다. 포함하려면 잠금 해제 또는 연결 해제 후 다시 실행. |
| `bind matrices only - shape NOT kept: <이유>` | `Keep current shape` 를 요청했지만 형상을 굽지 못했다. **콜론 뒤에 이유가 함께 나온다** — 아래 표 참고. 바인드 행렬은 갱신됐다. |
| `still has live target geometry with a non-zero weight` | 아래 항목 참고. |

#### `shape NOT kept` 이 떴을 때 대응 순서

1. **요약 줄의 콜론 뒤 이유를 읽는다.** 이유별 대응:

| 이유 | 대응 |
|------|------|
| `input geometry is nurbsSurface` 등 / `is not polygon mesh data` | 폴리곤 메시가 아니다 → **`Snap mesh to rest shape` 모드로 실행** |
| `could not resolve the input (Orig) shape from the deformer chain` | 히스토리 체인이 특이해 입력 셰이프를 못 찾았다 → **Diagnose** 로 어디서 끊겼는지 확인 |
| `input shape ... has a different vertex count (N vs M)` | 입력(Orig) 셰이프와 스킨 입력의 버텍스 수가 다르다. 히스토리에 버텍스 수를 바꾸는 노드(deleteComponent, polyReduce 등)가 섞여 있을 수 있다 → 히스토리 정리 후 재시도 |
| `skin input/output vertex counts differ` | 스킨 입출력 버텍스 수가 다르다 → 히스토리 확인 |

2. **Diagnose 버튼을 누른다.** 씬을 건드리지 않는 읽기 전용 리포트로,
   디포머 체인을 **실제 연결 그대로** 한 줄씩 찍어 준다. 어느 단계에서 멈췄는지 바로 보인다.

```
--- skinCluster1 ---
  geometry     : body (mesh)
  geo index    : 0  (input indices [0])
  influences   : 12  (matrix indices [0, 1, 2, ...])
  skin input   : 8204 verts
  skin output  : 8204 verts
  chain walk   :
    <- blendShape1.outputGeometry[0]  [blendShape]
    <- bodyShapeOrig.worldMesh  [mesh]
    == input shape: bodyShapeOrig (8204 verts)
  resolved head: |body|bodyShapeOrig
```

3. 그래도 원인이 불분명하면 이 리포트 내용을 그대로 공유하면 된다.

> 참고: 체인 워크가 실패해도 툴은 같은 트랜스폼 아래에서 **버텍스 수가 같은 intermediate
> 셰이프**를 찾아 자동으로 재시도한다(성공 시 `[Info] ... resolved by fallback`).
> 버텍스 수가 다르면 고르지 않으므로 엉뚱한 셰이프에 굽지 않는다.

### 주의 (blendShape 타겟이 라이브인 경우)

blendShape의 **타겟 메시가 아직 씬에 남아 연결돼 있고** 그 weight 가 0 이 아니면,
델타가 매 평가마다 `타겟 − 베이스` 로 재계산되어 이 툴이 구운 값이 **상쇄된다.**
툴이 이 상황을 감지해 로그에 경고를 띄운다. 다음 중 하나로 해결한다.

- 타겟 메시를 삭제해 델타를 고정한다(가장 일반적인 프로덕션 상태), 또는
- blendShape weight 를 0 으로 둔 채 실행한다(보통 바인드 포즈 갱신은 뉴트럴에서 한다)

---

## 1-B. Move Joints 탭 — 메시를 건드리지 않고 조인트만 옮기기 (v01.08~)

바인드된 메시는 그대로 둔 채 **스켈레톤 배치만 고치고 싶을 때** 쓴다. 조인트 위치를 잘못 잡아
바인드했거나, 리깅 후에 관절 피벗을 조금 옮겨야 할 때가 대표적이다.

### 사용법

1. 바인드된 메시(또는 그 조인트)를 선택하고 **`Load Selection`**.
2. **`EDIT JOINTS`** 를 누른다. 버튼이 주황색 **`EDIT ON`** 으로 바뀐다.
   → 이제 조인트를 아무리 옮기고 돌려도 **메시는 화면에서 1픽셀도 움직이지 않는다.**
3. 뷰포트에서 조인트를 옮긴다. (`Select Influences` 버튼으로 인플루언스 전체를 한 번에 선택할 수 있다)
4. 버튼을 **다시 누른다** → 지금 조인트 배치가 새 바인드 상태로 굳는다.
   메시 형상도 그대로, **버텍스별 웨이트도 편집 전과 완전히 동일**하다.

A00290_BSTool 의 Shape Editor Edit 토글과 같은 조작감이다(켜고 → 고치고 → 다시 꺼서 반영).

- **`Cancel Edit (restore joints)`** — 편집을 버리고 조인트와 바인드 행렬을 **Edit 을 켠 시점으로**
  되돌린다. 시작 시점의 값을 skinCluster 의 `JUN_jointEditBackup` 문자열 어트리뷰트에 JSON 으로
  저장해 두므로, 씬을 저장했다 열어도 취소할 수 있다.
- **`Rebuild bindPose node`**(기본 ON) — 끝낼 때 dagPose 를 다시 만들어 마야의 **Go to Bind Pose** 가
  새 조인트 배치로 돌아오게 한다.
- 편집 중에는 `Load Selection` / `Clear` 가 잠긴다(대상을 바꾸면 임시 노드가 씬에 남기 때문).
- 툴을 닫았다 다시 열어도 **씬을 훑어 편집 중이던 skinCluster 를 되찾는다**(상태는 UI 가 아니라
  노드에 있다). 탭을 열 때마다 씬 상태로 버튼을 맞춘다.

### 원리

skinCluster 의 인플루언스별 스킨 행렬은 `bindPreMatrix[i] * matrix[i]` 다(`matrix[i]` = 조인트의
`worldMatrix`). 편집 중 **이 곱을 상수로 유지**하면 조인트가 어디로 가든 출력이 변하지 않는다.
편집 시작 시점의 값을 `C_i` 로 잡고

```
C_i                = bindPreMatrix_i(0) * worldMatrix_i(0)      (상수)
bindPreMatrix_i(t) = C_i * worldInverseMatrix_i(t)              (라이브)
```

를 인플루언스마다 **multMatrix 노드 하나**로 걸어 준다(`matrixIn[0]` = `C_i`,
`matrixIn[1]` ← 조인트의 `worldInverseMatrix[0]`). `t = 0` 이면 원래 값 그대로라 **켜는 순간에도
무변화**다. Edit 을 끄면 multMatrix 의 현재 출력을 `bindPreMatrix` 에 정적으로 굽고 임시 노드를 지운다.

> **`worldInverseMatrix` 를 `bindPreMatrix` 에 그냥 직결하면 안 된다.**
> 그러면 스킨 행렬이 항등이 되어 메시가 **rest 셰이프로 튄다.** 리그가 바인드 포즈에 있을 때만
> 우연히 결과가 같고, **포즈된 리그에서는 눈에 띄게 점프한다**(실측 3.6 유닛). 위 `C_i` 보정은
> 포즈와 무관하게 항상 무변화다(실측 오차 1e-16).

**웨이트는 어느 단계에서도 건드리지 않는다** — `weightList` 를 읽지도 쓰지도 않으므로 버텍스별
웨이트 동일성은 정의상 보장된다(테스트에서도 배열 전체를 비교해 확인).

### 한계

- `bindPreMatrix` 가 **잠겨 있거나 이미 다른 노드에 연결된** 인플루언스는 잡아둘 수 없다.
  그 조인트(및 그 조인트를 자식으로 갖는 부모)를 움직이면 메시가 따라 변형된다. 어떤 조인트가
  빠졌는지 로그로 알려 준다.
- 조인트를 옮기는 것이지 **웨이트를 다시 계산하지는 않는다.** 관절 위치를 크게 바꾸면 웨이트가
  그 자리에 맞지 않을 수 있고, 그건 의도된 동작이다(웨이트 보존이 요구사항).

---

## 2. 왜 툴이 필요한가 — 마야 네이티브로는 안 된다

mayapy 로 직접 검증한 결과다.

| 시도 | 결과 |
|------|------|
| `skinCluster -e -recacheBindMatrices` | **`bindPreMatrix` 가 전혀 바뀌지 않는다.** 무효 |
| `dagPose -reset` | **bindPose 가 갱신되지 않는다.** Go to Bind Pose 가 여전히 옛 포즈로 감 |
| `Move Skinned Joints Tool` | 목적이 다르다 — "메시를 변형시키지 않고 조인트만 이동". 이미 변형된 상태를 굳히지는 못한다. (그 목적이라면 v01.08 의 **Move Joints 탭**을 쓴다 — 마야 툴과 달리 다중 skinCluster·취소·bindPose 재생성을 함께 처리한다) |

그래서 3단계를 직접 수행한다 (`app/core/bind_pose_manager.py`).

1. **`bindPreMatrix[i] = 인플루언스의 현재 worldInverseMatrix`**
   → 스킨 변형 행렬이 항등이 되어 `skinCluster 출력 == 입력` 이 된다.
2. **(Keep 모드) 스킨이 만들던 변형량을 체인 입력에 굽는다**
   `delta = skinCluster 출력 − 입력` 을 **체인 헤드 셰이프**에 더한다.
   → 새 입력이 곧 예전 출력이 되어 화면상 형상이 그대로 유지된다.
   blendShape 는 정적 델타를 더하는 선형 연산이라 `f(orig + d) = f(orig) + d` 가 성립하므로,
   블렌드셰이프가 스킨 앞이든 뒤든 성립한다.
3. **`bindPose`(dagPose) 노드를 현재 포즈로 재생성**하고 `skinCluster.bindPose` 에 재연결한다.

---

## 3. 구현 메모 (수정할 때 주의)

mayapy 로 확인한, 전부 **조용히 틀리는** 종류의 함정이다.

- **델타를 구울 때 `MFnMesh.setPoints` 를 쓰면 안 된다.** undo 큐에 안 올라가서, Ctrl+Z 를 누르면
  `bindPreMatrix` 만 되돌아가고 구운 형상은 남아 **메시가 어긋난 채 방치**된다.
  `pnts` 구간(range) `setAttr` 로 쓴다(undo 가능).
- **`pnts` 는 반드시 기존 값에 더해야 한다.** 프리즈한 트랜스폼이 이미 tweak 으로 들어가 있는 경우가
  흔하다(예: `ty=2` 를 freeze 하면 전 버텍스에 `(0,2,0)` 이 남는다). 덮어쓰면 그 값이 통째로 날아간다.
- **체인 헤드는 연결을 타고 올라가 찾는다.** 중간(Orig) 셰이프가 여러 개일 수 있어
  `intermediateObject` 를 이름/순서로 고르면 틀린 셰이프를 잡는다.
- **스킨의 출력은 `skinCluster.outputGeometry` 에서 읽는다.** 화면의 shape 을 읽으면 하류 디포머까지
  섞여 델타가 틀어진다. 입력도 마찬가지로 `input[].inputGeometry` 에서 읽는다.
- **`bindPreMatrix` 인덱스를 `enumerate(skinCluster -q -inf)` 로 매기면 안 된다.**
  인플루언스 목록의 **순서는 `matrix[]`/`bindPreMatrix[]` 의 논리 인덱스와 다를 수 있다.**
  인플루언스를 뺐다 다시 넣은 리그에서는 인덱스가 성겨진다(예: `[0,1,3,4,5,6]` vs `[0,1,2,3,4,5]`).
  그러면 **엉뚱한 조인트 슬롯에 행렬이 들어가 더블 트랜스폼처럼 보인다.**
  반드시 `matrix[i]` 연결을 읽어 `{논리 인덱스: 인플루언스}` 매핑을 만든다(`_influence_index_map`).
  ← **v01.01 에서 고친 실제 버그.** 단순 테스트 씬은 인덱스가 우연히 일치해 통과하므로 못 잡는다.
- **`input[0]` / `outputGeometry[0]` 으로 인덱스를 고정하면 안 된다.** 한 디포머가 여러 지오를 변형하거나
  지오를 뺐다 넣으면 논리 인덱스가 0 이 아니다. 없는 인덱스를 읽으면 빈 데이터가 나와
  **`(kInvalidParameter): Object is incompatible with this method`** 로 터진다.
  `outputGeometry[i]` 가 대상 shape 으로 이어지는 i 를 찾아 쓴다(`_geometry_index`).
- **`bindPose` 노드는 원래 이름을 물려준다.** 안 그러면 실행할 때마다 `bindPose37` 처럼 번호가 튀는
  노드가 새로 생겨 씬이 지저분해진다.
- `getAttr("<shape>.pnts")` 통짜 조회는 *"compound with mixed type elements"* 로 실패한다.
  `MPlug.getExistingArrayAttributeIndices` 로 읽는다.
- `bindPose` 노드를 새로 만든 뒤 **`skinCluster.bindPose` 로 재연결하는 것을 빼먹으면**
  마야의 Go to Bind Pose 가 포즈를 못 찾는다.

---

## 4. 검증

headless(mayapy) 로 확인한 항목:

- 현재 형상 유지 / rest 스냅 두 모드
- 조인트를 되돌리면 변형되고, 다시 오면 새 rest 로 복귀
- Go to Bind Pose 가 새 포즈(위치·회전)로 정확히 복귀
- blendShape 가 스킨 **앞** / **뒤** 양쪽, 히스토리 보존 및 계속 동작
- 메시 트랜스폼이 원점이 아닌 경우, 루트 조인트 자체를 옮긴 경우
- 여러 조인트 동시 이동+회전, **여러 skinCluster 동시 처리**
- **undo 한 번으로 형상·bindPreMatrix 완전 복원**
- 라이브 blendShape 타겟 경고 출력

v01.01 회귀 테스트(실제 리그에서 보고된 버그):

- **인플루언스 인덱스가 성긴 skinCluster**(뺐다 다시 넣어 `[0,1,3,4,5,6]`) 에서 형상 유지 — 더블 트랜스폼 없음
- nurbsSurface 스킨에서 **예외로 죽지 않고** 안내 출력, `Snap` 모드는 정상 동작
- `bindPreMatrix` 가 연결/잠긴 인플루언스가 있어도 죽지 않고 어떤 조인트가 빠졌는지 안내
- 3회 반복 실행해도 **`bindPose` 이름 유지 + dagPose 노드 개수 불변**
- 지오가 2개인 skinCluster 에서 두 번째 지오의 논리 인덱스(=1)를 정확히 찾음

Move Joints 탭 (v01.08):

- 리그가 **바인드 포즈일 때 / 이미 포즈된 상태일 때** 모두 Edit ON·조인트 이동·확정 전 구간 무변화(오차 1e-16)
- `skinMethod` **linear / dual quaternion / blended** 세 방식 모두
- **버텍스별 웨이트 배열 전체 비교** — 편집 전후 완전 동일
- 확정 후 새 배치에서 정상 디폼되고, 확정 시점 포즈로 되돌리면 형상도 복귀
- `Cancel` 이 조인트 트랜스폼·`bindPreMatrix`·메시 형상을 모두 시작 시점으로 복원
- **인덱스가 성긴 skinCluster**(`[0,1,2,4]`), **여러 skinCluster 동시** 편집
- `bindPreMatrix` 가 잠긴 인플루언스는 경고 후 나머지만 홀드(잠긴 조인트를 움직이면 변형됨을 명시)
- Edit ON 중복 호출 / 편집 아닌 대상 확정은 조용한 no-op, 임시 multMatrix 노드 잔류 없음
- **툴을 새로 띄워도** 씬을 훑어 편집 중이던 skinCluster 를 되찾고 그 창에서 확정 가능
- 확정 후 `Go to Bind Pose` 가 새 조인트 배치로 복귀
