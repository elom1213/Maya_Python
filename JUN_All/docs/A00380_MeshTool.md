---
title: A00380_MeshTool 사용법
aliases: [Mesh Tool, MeshTool, A00380, Peak, Match, By Weight]
tags: [maya-python, tool-guide, mesh, modeling, peak, normal, match, kangaroo, layout, skin-weight, corrective]
updated: 2026-09-18
---

# A00380_MeshTool 사용법

Maya 안에서 도는 **메시 편집** PySide 툴이다(arch B, in-Maya). **Peak / Match** 두 탭으로 구성된다.

- **Peak** (v01.00~) = 선택한 메시/버텍스를 **각자의 노말 방향으로 팽창(+) · 수축(-)** 시킨다.
  후디니의 **peak 노드**와 같은 개념이고, 마야 기본 방식(컴포넌트 선택 → Move 툴 `axis = normal`)의
  느린 점을 해결하는 것이 목적이다.
- **Match** (v01.01~) = **Source 메시의 같은 인덱스 버텍스 위치**로 다른 메시의 버텍스를 이동시킨다.
  **Kangaroo 의 Geometry > Match** 기능을 Kangaroo 없이 재현한 것이다. v01.09 부터 하위 탭 두 개:
  - **Default** — 좌(Source) / 우(Targets) 리스트. **우측 메시들을 좌측 모양으로** 바꾼다(v01.10~).
    좌 1개면 `1 <= n`, 여러 개면 `n <= n`(리스트 순서대로 짝, 개수가 다르면 작은 쪽만큼).
  - **By Weight** (v01.09~) — 스킨 메시의 **조인트 웨이트를 마스크로** 써서, 메시들을 타깃 모양 쪽으로
    `웨이트 × 델타` 만큼 옮긴다. 블렌드셰이프 타깃에 웨이트 맵(마스크)을 칠한 것과 결과가 같다.

- **버전**: `app/config/version.py` (v01.11)
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

v01.09 부터 Match 탭은 **하위 탭 두 개**다 — `Default`(이 절) 와 `By Weight`(3-3 절).
하위 탭을 옮기면 Default 의 확정 안 한 미리보기는 되돌아간다(둘 다 같은 메시의 `pnts` 에 쓰므로).

### Match > Default

**좌측 Source 메시**의 버텍스 위치로, **우측 Targets 메시들**의 버텍스를 **같은 인덱스끼리** 이동시킨다
(v01.10~. 그 전에는 From 한 칸 + 씬 선택이었다). 버텍스 대응이 **인덱스 기준**이라, 두 메시는 **토폴로지(버텍스 순서·개수)가 같아야** 정확히 맞는다
(예: 블렌드셰이프 타겟, 복제본, 스컬프트 전/후처럼 위상이 같은 메시). Kangaroo 의 `setModelVerts`
(Geometry > Match) 와 같은 규칙이다.

```
┌ Match ──────────────────────────────────────────┐
│ ┌ Meshes (vertex-index match) ────────────────┐ │
│ │ [List Selected]        [List Selected]      │ │
│ │ Source    Number: 1    Targets   Number: 3  │ │
│ │ ┌───────────┐          ┌───────────┐        │ │
│ │ │ head_A    │          │ head_01   │        │ │  ← 우측이 바뀐다
│ │ │           │          │ head_02   │        │ │
│ │ └───────────┘          │ head_03   │        │ │
│ │ [Add][Del][Up][Down]   [Add][Del][Up][Down] │ │
│ └─────────────────────────────────────────────┘ │
│ 1 <= 3 : every Target takes the Source's shape. │  ← 모드 줄
│ ┌ Source ────────┬ Target (modified) ─────────┐ │  ← 짝 미리보기 (짝 없는 줄은 회색)
│ │ head_A         │ head_01                    │ │
│ │ head_A         │ head_02 ...                │ │
│ └────────────────┴────────────────────────────┘ │
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

**사용 순서** (v01.10~)
1. 모양의 기준이 될 메시를 선택 → 좌측 **Source** 의 `List Selected`.
2. 바꿀 메시들을 선택 → 우측 **Targets** 의 `List Selected`. 짝 순서는 `Up` / `Down` 으로 맞춘다
   (메시 오브젝트는 고른 순서대로 담긴다).
3. 모드 줄과 짝 미리보기 표로 확인하고 **Apply Match** — 확정(**Ctrl+Z 한 번**에 전부 되돌아감).
4. (선택) **Weight 슬라이더를 끌어** 0(원본)~1(완전 매칭)을 실시간 미리보기. **Reset** 은 원본으로.

**짝짓기 규칙**

| 좌 Source | 우 Targets | 결과 |
|---|---|---|
| **1개** | n개 | **`1 <= n`** — 우측 n개가 전부 그 하나의 모양이 된다 |
| n개 | n개 | **`n <= n`** — k 번째 Target 이 k 번째 Source 모양이 된다 |
| a개 | b개 (a ≠ b, a > 1) | **작은 쪽 수(min)만큼만** 짝짓는다. 남는 메시는 **로그에 이름과 순번**을 적는다 — 남은 Source 는 "no Target - skipped", 남은 Target 은 "no Source - left unchanged" |

- 같은 메시가 양쪽에 있으면 그 짝은 건너뛰고 로그에 적는다.
- 리스트를 바꾸면 **이전 미리보기는 되돌리고 버린다** — 옛 짝으로 확정되는 일이 없다.
- 로그에는 확정한 짝이 `Target <= Source` 로 한 줄씩 남는다.

> v01.09 까지는 From 한 칸 + **씬 선택**이 대상이었다. v01.10 부터 대상은 **우측 리스트**다.

**진행률 팝업 (v01.11~)** — `Apply Match` 를 누르면 공용 위젯
[`JUN_mod_progress_qt_v01`](Framework_MOD_progress_qt.md) 팝업이 뜨고, 게이지 · 단계 이름 · 지금 처리 중인
메시(`Reading head_02` / `Writing head_02`) · 경과 시간을 보여 준다. 끝나면 스스로 닫히고 로그에 걸린 시간이
붙는다(`... at weight 1.000 (0.4s).`).

| 단계 | 비중 | 언제 |
|---|---|---|
| Reading meshes | 30 | 짝마다 Source / Target 점을 읽는다 — **미리보기 세션이 이미 있으면 빠진다**(그땐 Writing 이 0~100%) |
| Writing vertices | 70 | Target 메시마다 `pnts` 에 쓴다 |

- 닫기 버튼 · Esc 없음(모달) — 도는 중에 창만 닫히거나 Apply 를 또 누르는 일이 없다.
- 코어(`match_manager`)는 위젯을 모르고 `progress(done, total, message)` 콜백만 받는다. 슬라이더 미리보기에는
  넘기지 않으므로 팝업이 뜨지 않는다.

**옵션**

| 옵션 | 설명 |
|------|------|
| **World space** (기본 켜짐) | Target 버텍스가 Source 버텍스의 **월드 위치**에 앉는다. 끄면 두 메시의 **로컬(오브젝트 공간) 좌표**를 맞춘다(둘의 트랜스폼이 달라도 로컬이 같으면 무변화). |
| **Respect soft selection** (기본 켜짐) | 소프트 셀렉션이 켜져 있고 **Target 메시의 버텍스를 골라 두었으면** 그 버텍스만 falloff 를 **버텍스별 블렌드 배율**로 움직인다. `final = 원본 + softw·weight·(Source-원본)`. 버텍스를 고르지 않았으면 메시 전체. |

> **인덱스 대응**: Target 버텍스 `i` → Source 버텍스 `i`. Source 가 Target 보다 버텍스가 적으면, 대응
> 인덱스가 없는 Target 버텍스는 **건너뛰고 로그로 알린다**. 버텍스 수가 다르면 짝마다 "토폴로지 불일치"
> 경고를 남기되 겹치는 인덱스는 이동한다.

**검증 (v01.10, mayapy 2024 + 오프스크린 Qt, 테마 적용)** — 짝짓기 순수 함수 3종(1<=3 · 3<=2 · 2<=3),
1<=n 세 메시가 Source 와 같아짐 + Ctrl+Z 한 번에 셋 다 원위치, 3<=2 · 2<=3 짝 + 남는 메시 로그,
미리보기 0.5 / discard, 양쪽에 같은 메시 건너뜀, 리스트를 바꾼 뒤 옛 미리보기 세션으로 확정되지 않음.
창 최소 크기 540 x 732(좌우 리스트 두 개가 폭을 정한다 — TSL 머리줄의 `Order` 체크박스를 빼서 291 → 238px 씩).
마야 GUI 에서는 아직 안 눌러 봄.

---

## 3-3. Match > By Weight (v01.09~)

스킨 웨이트를 **마스크**로 써서 메시를 타깃 모양 쪽으로 옮긴다. 블렌드셰이프에서 타깃마다 웨이트 맵을
칠해 "이 타깃이 원본을 얼마나 바꿀지" 정하는 것과 **보이는 결과가 같다.** 조인트별로 영역을 나눈
코렉티브(예: 스컬프트 하나를 `jnt_01` 영역 / `jnt_02` 영역으로 쪼개기)를 만들 때 쓴다.

| 이름 | 뜻 |
|------|-----|
| **Weight Mesh** (M_w) | 조인트에 바인드된 메시. **웨이트만 읽는다** — 움직이지 않는다 |
| **Joints** (jnt_i) | M_w 를 바인드한 조인트. 체크한 것만 쓴다 |
| **Target Mesh** (M_tgt) | 목표 모양. M_w 와 같은 메시(토폴로지) |
| **Meshes to Move** (M_j) | 옮길 메시들. M_w 와 같은 메시(토폴로지) |

```
┌ By Weight ─────────────────────────┐
│ ┌ Weight Mesh (skinned) ─────────┐ │
│ │ Weight Mesh [ body_skin ][Load]│ │
│ │ Joints              Number: 3  │ │
│ │ [v] jnt_01                     │ │  ← 체크박스 (Shift/Ctrl 다중 체크)
│ │ [v] jnt_02                     │ │
│ │ [ ] jnt_03   (회색 = 웨이트 0) │ │
│ │ [Filter ...]                   │ │
│ │ [Check All] [Clear]            │ │
│ └────────────────────────────────┘ │
│ Target Mesh [ body_sculpt ][Load]  │
│ ┌ Meshes to Move ────────────────┐ │
│ │ [ M_01 ]  (Up / Down 로 순서)  │ │
│ │ [ M_02 ]                       │ │
│ └────────────────────────────────┘ │
│ ┌ Pairing (joint weights -> mesh)┐ │
│ │ (o) Joint k -> Mesh k          │ │
│ │ ( ) Sum -> every mesh          │ │
│ │ Mesh   Joint weights           │ │  ← 짝 미리보기
│ │ M_01   jnt_01                  │ │
│ │ M_02   jnt_02                  │ │
│ └────────────────────────────────┘ │
│ Strength [ 1.000 ]                 │
│ [       Apply By Weight        ]   │
└────────────────────────────────────┘
```

**계산** — 버텍스 인덱스로 대응하고 **오브젝트(로컬) 공간**에서 계산한다(블렌드셰이프와 같다).

```
new[v] = cur[v] + mask[v] × Strength × (M_tgt[v] − cur[v])
mask[v] = M_j 에 짝지은 조인트들의 M_w 웨이트 합 (1 로 자름)
```

예: `jnt_01` 웨이트가 0.2 인 `vtx[0]`, 1.0 인 `vtx[1]` → M_01 의 `vtx[0]` 은 M_tgt 까지 델타의 **20%**,
`vtx[1]` 은 **100%**(M_tgt 에 정확히 안착) 움직인다. 웨이트 0 인 버텍스는 그대로다.

**사용 순서**
1. 스킨 메시를 선택하고 Weight Mesh 의 **Load** — 바인드한 조인트가 **이름순**으로 나온다. 웨이트가 하나도
   없는 인플루언스는 회색이다. 체크박스는 공용 동작 `MOD_checkList_qt`(Shift/Ctrl 로 여러 행 골라 한 번에
   체크), 필터는 공용 `MOD_filter_qt`.
2. 목표 메시를 선택하고 Target Mesh 의 **Load**.
3. 옮길 메시들을 선택하고 Meshes to Move 의 **List Selected**.
4. **Pairing** 을 고른다.
   - **Joint k -> Mesh k** (기본): 체크한 조인트 k 번째(목록 순서) → 메시 리스트 k 번째.
     `jnt_01 -> M_01`, `jnt_02 -> M_02`. 순서는 메시 리스트의 `Up` / `Down` 으로 맞춘다.
     개수가 다르면 남는 쪽은 건너뛴다(표에 회색으로).
   - **Sum -> every mesh**: 체크한 조인트 웨이트를 **더한 하나의 마스크**를 모든 메시에.
   짝 미리보기 표가 체크 · 리스트 · 방식이 바뀔 때마다 갱신된다.
5. **Apply By Weight** — 한 번에 적용된다. **Ctrl+Z 한 번**에 전부 되돌아간다.

**알아둘 것**
- 버텍스 수가 M_w 와 다른 메시는 건너뛰고 로그로 알린다. M_tgt 가 다르면 아무것도 하지 않는다.
- 이동은 Default 와 같은 방식(`shape.pnts` 구간 setAttr)이라 히스토리 · 스킨이 걸린 M_j 에서도 동작한다.
- M_tgt 의 트랜스폼(위치)은 결과에 영향을 주지 않는다 — 로컬 좌표끼리 비교한다.
- `Strength` 는 모든 마스크에 곱해진다(0~1).

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
By Weight 는 `app/core/weight_match_manager.py` — 웨이트는 `MFnSkinCluster.getWeights` 로 한 번에 읽고,
이동은 Match 의 `MatchTarget` 을 그대로 쓴다(버텍스별 가중치 자리에 소프트 셀렉션 대신 마스크를 넣는다).
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


### UI 레이아웃 함정 (v01.06)

**공용 TSL 위젯 **전체**에 `setMaximumHeight` 를 걸지 말 것.**
Match 탭의 From 리스트가 `tsl_from.setMaximumHeight(120)` 으로 묶여 있었는데,
TSL 안에는 `List From Mesh` 버튼 + 헤더 + 리스트 + `Add`/`Del` 행이 들어 있고
**리스트의 최소 높이는 줄지 않는다**(`DEFAULT_LIST_MIN_HEIGHT = 100`).
그래서 모자란 높이를 레이아웃이 **버튼에서 빼앱가** 글자가 잘렸다.

실측(테마 qss 적용 상태, `mayapy`) — 버튼이 필요로 하는 높이는 **30px** 인데 **25px** 로 눌렸고,
TSL 자체도 sizeHint 290 을 111 에 집어넣고 있었다. 테마를 안 입히면 버튼이 23px 로
작아져 증상이 안 나타난다 — **qss 패딩이 더해진 상태로 재야 보인다.**

고친 방법: 높이 제한을 **리스트에만** 건다.

```python
JUN_mod_tsl_qt_v01(..., list_min_height=44)     # 리스트 바닥값을 낮추고
self.tsl_from.list_widget.setMaximumHeight(70)  # 천장은 리스트에만
```

버튼은 제 크기(30px)를 지키고, 창을 380x380 까지 줄여도 눌리지 않는다(리스트가 대신 줄어든다).
대가는 From 박스가 111 → 159px 로 커져 **창 최소 높이가 573 → 595px** 로 늘어난 것이다.

---

## 6. 앞으로

메시 관련 기능이 생기면 탭으로 추가한다(현재 Peak / Match). 새 탭도 Peak/Match 처럼
`app/core/<name>_manager.py` 에 세션 모델(preview/restore/commit)을 두고, 공용 헬퍼를 재사용한다.

---

## 로그창 (v01.07)

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다. 오른쪽 위에 작은 버튼 셋이 붙어 있다.

| 버튼 | 동작 |
|------|------|
| `Expand` | 로그를 **별도 창으로 옮겨** 크게 본다. 확장 중에 들어온 로그도 같은 곳에 쌓이고, 창을 닫으면 제자리로 돌아온다 |
| `Clear` | 로그를 비운다 |
| `Copy` | 로그 **전문**을 클립보드로 |

자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).
