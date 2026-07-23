---
title: A00380_MeshTool 사용법
aliases: [Mesh Tool, MeshTool, A00380, Peak, Match]
tags: [maya-python, tool-guide, mesh, modeling, peak, normal, match, kangaroo]
updated: 2026-07-23
---

# A00380_MeshTool 사용법

Maya 안에서 도는 **메시 편집** PySide 툴이다(arch B, in-Maya). **Peak / Match** 두 탭으로 구성된다.

- **Peak** (v01.00~) = 선택한 메시/버텍스를 **각자의 노말 방향으로 팽창(+) · 수축(-)** 시킨다.
  후디니의 **peak 노드**와 같은 개념이고, 마야 기본 방식(컴포넌트 선택 → Move 툴 `axis = normal`)의
  느린 점을 해결하는 것이 목적이다.
- **Match** (v01.01~) = 리스트업한 **From 메시의 같은 인덱스 버텍스 위치**로, 선택한 메시의 버텍스를
  이동시킨다(소프트 셀렉션 falloff 반영). **Kangaroo 의 Geometry > Match** 기능을 Kangaroo 없이
  재현한 것이다.

- **버전**: `app/config/version.py` (v01.05)
- **설치**: `__dragDrop_A00380.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **MeshTool** → `tools.A00380_MeshTool.run(True)`

---

## 1. 화면 구성

```
┌ Mesh Tool ─────────────────────────┐
│ Help                               │
│ ┌ Peak ──────────────────────────┐ │
│ │ ┌ Target ────────────────────┐ │ │
│ │ │ pSphere1 | 382 vertice(s)  │ │ │  ← 로드된 대상 요약
│ │ │ [ Load Selection ] [Clear] │ │ │
│ │ │ [x] Auto load on selection │ │ │
│ │ └────────────────────────────┘ │ │
│ │ ┌ Options ───────────────────┐ │ │
│ │ │ [x] Angle weighted normals │ │ │
│ │ │ [x] Respect soft selection │ │ │
│ │ └────────────────────────────┘ │ │
│ │ ┌ Amount ────────────────────┐ │ │
│ │ │ Range  [ 1.000 ]           │ │ │  ← 슬라이더 한계 (작게 = 미세)
│ │ │ ---------[|]-------------- │ │ │  ← 좌 수축 / 우 팽창
│ │ │ Value  [ 0.0000 ]    [ 0 ] │ │ │
│ │ │ Step   [ 0.0100 ] [ - ][ + ]│ │ │  ← 미세 조정
│ │ └────────────────────────────┘ │ │
│ │  (Apply 버튼 없음 — 조절 즉시 반영) │ │
│ └────────────────────────────────┘ │
│ [ log ... ]                        │
└────────────────────────────────────┘
```

---

## 2. 사용법

1. Maya에서 **메시를 선택**하거나, 컴포넌트 모드에서 **버텍스 · 엣지 · 페이스**를 선택한다.
   (엣지/페이스는 자동으로 버텍스로 변환된다. 여러 메시를 한 번에 선택해도 된다.)
2. **Load Selection** — 현재 선택을 스냅샷으로 잡는다. `Auto load on selection change`(기본 켜짐)를
   두면 선택을 바꿀 때마다 자동으로 다시 잡으므로 보통 따로 누를 일이 없다.
3. **슬라이더를 끌면 실시간으로 형태가 변하고, 손을 떼는 순간 그 상태가 그대로 최종 결과로 반영된다**
   (v01.04~, **별도 Apply 버튼 없음**). 오른쪽 = 팽창, 왼쪽 = 수축.
   슬라이더 홈은 **coral 테두리로 좌우 끝까지 보이고, 중앙(0)·양 끝에 눈금**이 찍힌다(v01.05~,
   A00290_BSTool 슬라이더 참고 — 예전엔 홈이 배경에 묻혀 구간이 안 보였다). Match 탭 슬라이더도 동일.
   - **Range** — 슬라이더 양끝 값. **0.05 처럼 작게 잡으면 아주 미세한 조정**이 된다.
   - **Value** — 정확한 수치 입력(소수점 4자리). **입력을 마치면(Enter/포커스 아웃) 확정**된다.
     Range 를 넘겨 입력하면 Range 가 자동으로 늘어난다.
   - **Step + `-` / `+`** — 한 번 누를 때마다 Step 만큼 **즉시 확정**된다. 미세하게 톡톡 조절할 때 쓴다.
   - **`0`** — 값을 0(오프셋 없음)으로 되돌린다.
4. 각 조절은 **Ctrl+Z 한 번**으로 정확히 되돌아간다(조작 단위로 묶임). 확정 후 값이 0 으로 리셋되고
   세션이 새 스냅샷 기준이 되므로, 이어서 계속 밀거나 당기면 그만큼 **누적**된다.

> v01.03 까지 있던 **Apply / Reset 버튼은 없앴다**(사용자 요청). 슬라이더/Value/± 로 조절한 상태가
> 곧 최종 결과다. 되돌리려면 **Ctrl+Z**, 오프셋을 지우려면 **`0`** 을 쓴다.
> 창을 닫을 때 아직 손을 떼지 않은(확정 전) 미리보기는 자동으로 되돌아간다.

---

## 3. 옵션

| 옵션 | 설명 |
|------|------|
| **Angle weighted normals** (기본 켜짐) | 버텍스 노말을 인접 면의 **코너 각도로 가중 평균**한다. 면 크기가 들쭉날쭉해도 팽창 결과가 고르다. 끄면 단순 평균. |
| **Respect soft selection** (기본 켜짐) | 마야 **소프트 셀렉션**이 켜져 있으면 그 falloff 가중치를 버텍스별 배율로 쓴다. 가장자리가 부드럽게 이어지는 부분 팽창이 된다. 소프트 셀렉션이 꺼져 있으면 아무 영향 없다. |
| **Auto load on selection change** (기본 켜짐) | 씬 선택이 바뀔 때마다 스냅샷을 다시 잡는다. |

---

## 3-2. Match 탭 (v01.01~)

리스트업한 **From 메시**의 버텍스 위치로, 현재 선택한 메시의 버텍스를 **같은 인덱스끼리** 이동시킨다.
버텍스 대응이 **인덱스 기준**이라, 두 메시는 **토폴로지(버텍스 순서·개수)가 같아야** 정확히 맞는다
(예: 블렌드셰이프 타겟, 복제본, 스컬프트 전/후처럼 위상이 같은 메시). Kangaroo 의 `setModelVerts`
(Geometry > Match) 와 같은 규칙이다.

```
┌ Match ─────────────────────────────┐
│ ┌ From Mesh (vertex-index match) ─┐ │
│ │ [ From 리스트 (TSL) ]           │ │  ← [List From Mesh] 로 선택을 등록
│ └─────────────────────────────────┘ │
│ Select the mesh/verts to move, then │  ← 대상은 그냥 씬에서 선택만
│ Apply (or drag Weight to preview).  │
│ ┌ Options ────────────────────────┐ │
│ │ [x] World space                 │ │
│ │ [x] Respect soft selection      │ │
│ └─────────────────────────────────┘ │
│ ┌ Weight ─────────────────────────┐ │
│ │ --------------------[|]  (0~1)   │ │  ← 0=원본, 1=완전 매칭
│ │ Value [ 1.000 ]                 │ │
│ └─────────────────────────────────┘ │
│ [    Apply Match    ] [ Reset ]     │
└─────────────────────────────────────┘
```

**사용 순서** (v01.03~ 대상 로드 단계 제거)
1. **From 메시를 선택**하고 **List From Mesh** 로 From 리스트에 등록한다(1개).
2. 이동시킬 **대상 메시(또는 버텍스)를 씬에서 선택**한다. 소프트 셀렉션을 켜면 falloff 가 반영된다.
3. **Apply Match** — 그 순간의 선택을 대상으로 삼아 매칭하고 확정한다(**Ctrl+Z 한 번**에 되돌아감).
4. (선택) 확정 전에 결과를 보고 싶으면 **Weight 슬라이더를 끌어** 0(원본)~1(완전 매칭)을 실시간
   미리보기한다. 슬라이더를 잡는 순간의 선택이 대상이 된다. **Reset** 은 미리보기를 원본으로 되돌린다.

> 별도의 "Load Target" 버튼은 없다. Apply(또는 슬라이더를 잡는 순간)에 **현재 씬 선택**을 대상으로 읽는다.

**옵션**

| 옵션 | 설명 |
|------|------|
| **World space** (기본 켜짐) | 대상 버텍스가 From 버텍스의 **월드 위치**에 앉는다. 끄면 두 메시의 **로컬(오브젝트 공간) 좌표**를 맞춘다(둘의 트랜스폼이 달라도 로컬이 같으면 무변화). |
| **Respect soft selection** (기본 켜짐) | 소프트 셀렉션 falloff 를 **버텍스별 블렌드 배율**로 쓴다. `final = 원본 + softw·weight·(타겟-원본)`. |

> **인덱스 대응**: 대상 버텍스 `i` → From 버텍스 `i`. From 이 대상보다 버텍스가 적으면, 대응 인덱스가
> 없는 대상 버텍스는 **건너뛰고 로그로 알린다**. 버텍스 수가 다르면 "토폴로지 불일치" 경고를 남기되
> 겹치는 인덱스는 이동한다.
> **From 은 대상에서 자동 제외**된다(From 을 함께 선택해도 자기 자신엔 매칭하지 않는다).

---

## 4. 왜 마야 기본 방식보다 빠른가

마야에서 버텍스를 노말 방향으로 옮기면 **버텍스마다 명령이 하나씩** 실행된다.
이 툴은 **`shape.pnts` (tweak) 를 구간(range) `setAttr` 로 한 번에** 쓴다.

19,462 버텍스(구체 140×140) 기준 실측 (Maya 2024, mayapy):

| 방식 | 시간 |
|------|------|
| `cmds.xform` 버텍스 루프 (마야 기본 방식에 해당) | **약 7.2 초** |
| 버텍스마다 `setAttr` | 약 6.8 초 |
| **구간 `setAttr` (이 툴)** | **약 0.10 초** |

즉 같은 작업이 **약 70배** 빠르다. 미리보기도 같은 경로라 슬라이더를 끌면 바로 반응한다.

---

## 5. 구현 메모 (수정할 때 주의)

`app/core/peak_manager.py`(Peak) 와 `app/core/match_manager.py`(Match) 에 정리돼 있다.
Match 는 Peak 의 공용 헬퍼(`_undo_disabled`, `_selection_map`, `_dag_path`, `_soft_weights`,
`_contiguous_runs`, `_shape_of`)와 preview/restore/commit·`shape.pnts` 구간 setAttr 모델을
**그대로 재사용**한다. Peak 과 다른 점은 이동량 계산뿐이다:
- **대응은 버텍스 인덱스**(closest-point 아님). From 을 대상의 오브젝트 공간으로 옮긴 좌표
  `from_local` 과 대상의 현재 좌표 `orig_local` 의 차 `(from_local - orig_local)` 를 로드 시점에
  버텍스별로 미리 계산해 얼려두고, 미리보기에서 `weight × softw` 만 곱한다.
- **World 모드**는 From 을 `getPoints(kWorld)` 로 읽고 대상의 `inclusiveMatrixInverse()` 로 역변환하므로,
  결과적으로 대상 버텍스가 From 의 **월드 위치**에 앉는다. Object 모드는 각자의 로컬 좌표를 직접 맞춘다.
- 나머지(undo off 미리보기, restore-before-commit, tweak 누적)는 아래 Peak 함정과 동일하다.

mayapy 로 확인한 함정들:

- **`MFnMesh.setPoints` 로 메시 데이터(vrts)를 직접 쓰지 말 것.**
  미리보기는 0.02 초로 더 빠르지만 **기존 tweak 이 쓸려 나가고**, 그 뒤 `setAttr` 이
  "tweak 이 지워진 상태"를 undo 기준으로 잡는다. 결과적으로 Apply 를 두 번 한 뒤
  Ctrl+Z 를 누르면 **첫 번째 Apply 까지 같이 풀린다.**
- **`MPlug.setFloat` 로 pnts 를 써도 반영되지 않는다** — tweak 이 한 번도 없던 메시에서는
  `cmds.setAttr` 이 한 번 들어가야 평가가 트리거된다. 그래서 쓰기는 전부 `setAttr` 로 통일.
- **미리보기는 `undoInfo(stateWithoutFlush=False)` 로 undo 를 잠시 끈 채** 쓴다.
  `state=False` 를 쓰면 **기존 undo 히스토리가 통째로 날아가므로** 반드시 `stateWithoutFlush` 를 쓴다.
- **commit 은 반드시 "스냅샷 값으로 되돌린 뒤" 확정 기록**한다. `setAttr` 은 실행 시점의 값을
  undo 기준으로 기억하므로, 미리보기 값이 남아 있으면 Ctrl+Z 가 미리보기 상태로 돌아간다.
- **노말은 스냅샷 시점 값으로 얼려 쓴다.** 슬라이더를 끄는 동안 노말을 다시 계산하면
  결과가 스스로에게 먹여져(feedback) 형태가 뭉개진다. 형상이 크게 바뀐 뒤 새 노말로 작업하려면
  **Load Selection** 으로 세션을 다시 만든다.
- 기존 tweak 값을 읽어 **거기에 누적**하므로 이전 편집이 보존된다. 읽기는 `MPlug` 의
  `getExistingArrayAttributeIndices` 로 (19k 메시에서 0.02 초). `getAttr(".pnts")` 통짜 조회는
  *"compound with mixed type elements"* 로 실패한다.
- 히스토리 있는 메시 · 스킨 걸린 메시에서도 동작한다(스킨 메시는 마야가
  *"Tweaks can be undesirable on shapes with history"* 경고를 띄우지만 정상 동작).
- **(v01.02) 미리보기 되돌리기(`restore`)는 "미리보기가 실제로 걸려 있을 때만" 한다.**
  UI 의 `discard_preview` 를 `_preview_dirty` 플래그로 가드한다. 이걸 안 하면 **Auto load** 가
  선택이 바뀔 때마다 `restore` 를 불러, 슬라이더를 한 번도 안 건드렸어도 **사용자가 손으로 옮긴
  버텍스를 로드 시점 스냅샷으로 덮어써 원상복구**시킨다(툴만 띄워둬도 편집이 되돌려지던 버그).
  `_preview_dirty` 는 amount≠0 미리보기를 쓸 때만 True, load/commit/restore 후 False. Match 탭도
  같은 방식(`_match_preview_dirty`).

---

## 6. 앞으로

메시 관련 기능이 생기면 탭으로 추가한다(현재 Peak / Match). 새 탭도 Peak/Match 처럼
`app/core/<name>_manager.py` 에 세션 모델(preview/restore/commit)을 두고, 공용 헬퍼를 재사용한다.
