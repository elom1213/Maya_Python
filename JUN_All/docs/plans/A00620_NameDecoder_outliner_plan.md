---
title: A00620_NameDecoder Outliner 탭 계획서
tags: [maya-python, plan, fbx, fbxasc, unicode, outliner, hierarchy, icon]
updated: 2026-11-11
---

# A00620_NameDecoder — Outliner 탭 계획서

풀린 이름(`FBXASC…` → `まばたき` · `口左` · `1_003`)을 **마야 아웃라이너처럼** 노드 타입 아이콘과 부모-자식 계층으로
보여 준다. 마야 아웃라이너는 일본어 · 중국어 이름을 표시할 수 없다(원본 계획서 §2-3) — 그래서 이 창이
**"읽을 수 있는 아웃라이너"** 역할을 한다.

- 대상 버전: **v01.02** (현재 v01.01)
- 원본 계획서: [`A00620_NameDecoder_plan.md`](A00620_NameDecoder_plan.md) · 사용법: [`../A00620_NameDecoder.md`](../A00620_NameDecoder.md)

## 1. 요구 (2026-11-11 사용자)

| # | 요구 | 결정 |
|---|------|------|
| 1 | 풀린 이름을 아웃라이너 UI 처럼 — 오브젝트 아이콘 | 마야 내장 아이콘 `:/out_<nodeType>.png` (§3 실측) |
| 2 | 각 오브젝트의 계층 구조가 보이게 | DAG 부모-자식 트리, 씬 순서 그대로 |
| 3 | 새 탭 vs **Names 탭 업데이트** 판단 | **새 탭 `Outliner`** + Names 탭엔 아이콘만 추가 (§2) |

## 2. 판단 — 새 탭 `Outliner`

### 2-1. 비교

| 기준 | Names 탭을 트리로 바꾸기 | **새 탭 `Outliner`** |
|------|--------------------------|----------------------|
| 보여 줄 노드 | `Encoded only`(기본 켬) 라 **FBXASC 가 없는 조상이 빠진다** → 계층이 끊긴다 | 범위 안 DAG 를 **전부** 보여야 계층이 선다. 목적이 다르다 |
| 정렬 | 열 클릭 정렬이 핵심(타입 · Owner 별로 모으기) | 아웃라이너는 **씬 순서**. 정렬하면 계층이 무너진다 |
| 열 | `Type` · `Owner` 열 | 트리에선 아이콘 = Type, 부모 = Owner → 두 열이 필요 없다 |
| DG 노드 · 어트리뷰트 · enum | 그대로 표에 있다 | 계층에 자리가 없다(blendShape 만 메시 아래에 붙인다, §4-3) |
| 기존 기능 의존 | Filter(최상위 행만 숨김) · `Export List` · `Export Map Template` · `Sync` · **Rename 탭 Preview** 가 전부 Names 의 평평한 `entries` 를 쓴다 → 트리로 바꾸면 다 다시 짜야 한다 | Names 는 손대지 않는다 |
| 위험 | 이미 쓰는 화면이 바뀐다 | 탭 하나 추가, 기존 시험 61 개 그대로 |

**결론**: 두 화면은 질문이 다르다 — Names 는 **"어떤 이름이 깨져 있나 (찾기 · 내보내기 · 번역)"**,
Outliner 는 **"이 이름이 씬 어디에 있나 (구조 보기 · 고르기)"**. 한 위젯에 List/Tree 토글로 합치면
`Encoded only` 의 의미가 모드마다 달라지고 필터 · 내보내기 동작도 갈라진다 → **새 탭**으로 한다.

요청의 "아이콘" 부분은 Names 탭에도 싸게 붙는다 → **Names `Decoded` 열에도 같은 아이콘**(§4-6). 계층만 Outliner 전용.

### 2-2. 탭 순서

`Outliner` · `Names` · `Blend Shapes` · (`Rename to ASCII`). Outliner 를 **첫 탭**으로 둔다 — 창을 열자마자
"마야 아웃라이너 대신 읽는 화면" 이 보이게. Names 는 찾기 · 내보내기 · 번역 출발점으로 그대로.
(첫 탭 인덱스를 쓰는 `_on_tab_changed` 의 `index == 1` 비교는 **페이지 객체 비교로** 바꾼다.)

## 3. 실측 (mayapy 2024 오프스크린, 2026-11-11)

### 3-1. 마야 내장 아이콘 (Qt 리소스)

| 경로 | 결과 |
|------|------|
| `:/out_transform.png` `out_mesh` `out_joint` `out_nurbsCurve` `out_nurbsSurface` `out_locator` `out_camera` `out_ikHandle` `out_parentConstraint` `out_objectSet` `out_shadingEngine` `out_lambert` `out_displayLayer` `out_reference` `out_animCurveTL` `out_dagNode` `out_default` | **있음** (20×20) |
| `:/out_blendShape.png` `out_skinCluster` `out_network` `out_geometryFilter` `out_deformer` · `blendShape.png` | **없음** |
| `:/<type>.svg` · `:/out_<type>.svg` | 전부 없음 → **png 만** 쓴다 |

- mayapy + `QApplication` 에서도 리소스가 읽힌다 → 오프스크린 시험에서 아이콘 null 검사가 가능.
- 없는 타입 대비 **대체 순서**: `out_<type>` → `cmds.nodeType(type, inherited=True, isTypeName=True)` 를 거꾸로
  (예: 플러그인 조인트 → `joint`) → DAG 면 `out_dagNode` → `out_default`. 타입당 한 번만 찾고 캐시.
- blendShape 노드 · 타겟 행은 마야 리소스가 없다 → **툴 로컬 svg 2 개**(`icon/outliner_blendShape.svg`,
  `icon/outliner_bsTarget.svg`).

### 3-2. 예시 씬 `0010_Miyabi_base_02.mb`

| 항목 | 값 |
|------|----|
| DAG 노드 | 637 (joint 517 · transform 61 · mesh 54 · camera 4 · locator 1) |
| 최상위(assemblies) | 8 |
| 가장 깊은 계층 | 25 단 (조인트 체인) |
| 아이콘 없는 DAG 타입 | **0** |

→ 깊이 25 라 **들여쓰기 폭을 줄인다**(`setIndentation(14)` 정도, 마야 아웃라이너와 비슷). 637 개는 한 번에 만들어도 빠르다.

## 4. 기능 설계 — `Outliner` 탭

```
┌ Scope [Scene ▾]  ☐ Shapes  ☑ Blend Shapes  ☐ Encoded branches only        [Refresh] ┐
│ Filter [ まば                                                    ]                    │
│ ▾ 📁 Miyabi                                  Miyabi                                   │
│   ▾ 🦴 Root                                  Root                                     │
│     ▾ 🦴 1_003                               FBXASC049_003                            │
│         🦴 Arm饰                             ArmFBXASC233FBXASC165FBXASC176           │
│   ▾ ◆ 口左                                   FBXASC229FBXASC143…                      │
│       ▾ ⬡ Miyabi_ncl1_3 (blendShape)        Miyabi_ncl1_3                            │
│           • まばたき  [3]                    FBXASC227FBXASC129…                      │
│ Number: 637   ☐ Sync with Selection                                    - 100% +      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 4-1. 위쪽 행

| 항목 | 설명 |
|------|------|
| `Scope` | Names 와 같은 세 값. `Scene` = DAG 전부 / `Selected` = 고른 노드 **+ 그 조상 경로**(위치를 보이게) / `Selected + Hierarchy` = 그 아래 전부도 |
| `Shapes` | 셰이프 노드 표시(기본 끔 — 마야 아웃라이너 기본과 같다). 끄면 셰이프 이름은 트랜스폼 툴팁에 |
| `Blend Shapes` | 메시 트랜스폼 아래에 blendShape 노드와 타겟(풀린 alias)을 자식 행으로(기본 켬 — 실제 고통점이 타겟 이름) |
| `Encoded branches only` | FBXASC 이름이 **하나라도 든 가지만**. 조상은 FBXASC 가 없어도 남긴다(계층 유지). 기본 끔 |
| `Refresh` | 트리를 다시 만든다. **펼침 상태 · 고른 행은 UUID 로 유지** |

Names 의 `Scan` 과 Outliner 의 `Refresh` 는 **따로 돈다**(한 탭의 버튼이 다른 탭을 바꾸지 않는다).
단, `Apply ASCII Names` · `Restore Original Names` 뒤에는 둘 다 다시 읽는다(이름이 바뀌었으니까).

### 4-2. 트리 행

| 열 | 내용 |
|----|------|
| `Name` | 아이콘 + 풀린 짧은 이름. 툴팁 = 풀린 전체 경로(`|Miyabi|Root|1_003`) + raw |
| `Raw (Maya name)` | 마야 짧은 이름. 헤더 우클릭으로 숨김(optionVar 기억) |

- 글자 색은 Names 와 같은 규칙: **깨진 FBXASC = 노랑**, FBXASC 없는 이름 = 회색, 풀린 이름 = 기본색.
- **숨겨진 노드(visibility 끔 · 조상 숨김)는 흐리게** — 마야 아웃라이너와 같은 단서. `cmds.ls(dag, invisible=True)` 한 번으로.
- 레퍼런스 노드는 이름 앞 네임스페이스를 raw 그대로 두고 잎 이름만 푼다(`ns:口左`).
- 인스턴스(부모가 여럿)는 부모마다 한 행 — 마야 아웃라이너와 같다. UUID 가 같으므로 선택은 둘 다 켜진다.
- 순서 = `cmds.ls(dag=True, long=True)` 순서(씬 순서). **정렬 끔.**

### 4-3. blendShape 자식 행

- 메시 트랜스폼(셰이프 표시 중이면 셰이프) 아래: `⬡ <풀린 blendShape 이름> (blendShape)` → 그 아래 타겟 `• まばたき  [index]`.
- 데이터는 이미 있는 `MFN.blendshape_targets(bs)` 와 `scope_nodes` 의 히스토리 검색 방식을 그대로 쓴다.
- 타겟 행 더블클릭 = **Blend Shapes 탭으로 가서 그 blendShape 를 고르고 그 행으로 스크롤**(웨이트 편집은 그 탭 몫).

### 4-4. 읽기 동작

| 동작 | 설명 |
|------|------|
| 행 클릭 | 마야에서 그 노드 선택(UUID 기준, 다중 선택 가능). 타겟 행 = blendShape 노드 |
| `Sync with Selection` | 마야 선택 → 그 행들을 고르고 **조상을 펼치고 스크롤**. scriptJob 은 Names 의 것과 **하나로 공유**(콜백에서 두 탭 다 갱신) |
| 펼치기 | 공용 `JUN_mod_treeExpand_qt_v01(tree)` — 화살표 = 한 단계, Shift = 아래 전부 (메모: 모든 트리에 붙인다) |
| Filter | 풀린 글자 · raw 로 찾는다. **맞는 행 + 그 조상만 보이고 조상은 펼친다**(§4-5) |
| 우클릭 | `Copy Decoded` · `Copy Raw` · `Copy Decoded Path` · `Select Hierarchy` · `Expand All Below` · `Collapse All` |
| 확대 | 공용 `JUN_mod_viewZoom_qt_v01(tree, key="A00620/outliner")` — 아이콘도 함께 커지도록 `setIconSize` 를 배율에 맞춘다 |

씬을 바꾸지 않는다(선택만). undo 가 쌓이지 않는다.

### 4-5. Framework 필터 — 계층 모드 추가

현재 `MOD_filter_qt_v01` 의 트리 모드는 **최상위 행만 `setHidden`** 한다 → 깊이 25 트리에선 쓸 수 없다.

- 옵션 `tree_recursive=False`(기본, 기존 동작 그대로) 추가. `True` 면:
  모든 항목을 재귀로 보고, **맞는 항목 + 그 조상**을 보이고, 맞는 항목의 조상을 펼친다. 나머지는 숨긴다.
  `Number` 는 맞는 항목 수. 글이 비면 전부 보이고 펼침 상태는 필터 전으로 되돌린다.
- 기존 사용처는 인자를 안 주므로 영향 없음. 사용처 수를 `grep tree_widget=` 로 세어 시험에 회귀 한 줄.

### 4-6. Names 탭 — 아이콘만

- `Decoded` 열에 같은 아이콘(`node_type` 으로). 타겟 행 = 타겟 svg, attr · enum 행 = 아이콘 없음.
- 우클릭에 `Show in Outliner` — Outliner 탭으로 가서 그 노드 행을 고르고 조상 펼침. 표 구조 · 정렬 · 내보내기는 그대로.

## 5. 구조

```
Framework/qt/maya_icons.py               # 새 공용: node_icon(node_type) -> QIcon, 대체 순서 + 캐시 (§3-1)
Framework/qt/MOD_filter_qt_v01.py        # tree_recursive 옵션 추가 (§4-5)
tools/A00620_NameDecoder/
├─ app/core/outline.py                   # 새: 범위 → [OutlineNode(path, parent, type, uuid, raw, decoded, ok, hidden, kind)]
│                                        #     build_rows(dag_rows, ...) 는 마야 없이 시험 가능한 순수 함수
├─ app/ui/main_window.py                 # _build_outliner_tab · refresh_outliner · 공유 sync · Names 아이콘
├─ icon/outliner_blendShape.svg · outliner_bsTarget.svg
└─ tests/test_name_decoder.py            # 시험 추가 (§6)
```

- **마야 질의는 한 번씩 묶어서**: `cmds.ls(dag=True, long=True, showType=True)` (경로 + 타입 쌍),
  `cmds.ls(nodes, uuid=True)`, `cmds.ls(nodes, invisible=True)`. 노드마다 getAttr 금지 — 큰 씬(1 만+) 대비.
- 부모 찾기는 경로 문자열(`rsplit("|", 1)`)로 — 노드마다 `listRelatives` 를 부르지 않는다.
- 아이콘 헬퍼를 Framework 에 두는 이유: 노드 타입 → 아웃라이너 아이콘은 다른 툴 트리(A00440 SetTool, A00480 등)도 쓸 만하다.
  **툴 간 import 금지** 규칙과도 맞다.
- PySide 바인딩은 기존처럼 `Framework.qt.qt` 로만 — `QIcon` · `QPixmap` 이 거기 노출돼 있는지 확인하고 없으면 추가.

## 6. 시험 (mayapy 오프스크린, 기존 61 개 + 추가)

| # | 내용 |
|---|------|
| 1 | `node_icon`: 예시 씬 DAG 타입 전부 null 아님, 없는 타입(`blendShape` · `network`)은 대체 아이콘, 캐시 재사용 |
| 2 | `build_rows`(순수): 경로 목록 → 부모-자식이 `cmds.listRelatives(parent=True)` 와 일치, 순서 = 입력 순서 |
| 3 | Scope 3 종: Selected 는 조상 경로 포함 · Hierarchy 는 아래 전부 |
| 4 | `Shapes` 끔/켬 · `Blend Shapes` 켬 → 메시 아래 blendShape · 타겟 52 개(예시 씬) |
| 5 | `Encoded branches only`: FBXASC 없는 조상은 남고, FBXASC 없는 잎 가지는 빠진다 |
| 6 | 숨김 노드 흐림 · 깨진 FBXASC 노랑 · 인스턴스 두 행 |
| 7 | 행 클릭 → 마야 선택 UUID 일치 · Sync → 조상 펼침 · undo 큐 변화 없음 |
| 8 | Refresh 후 펼침 · 선택 유지(UUID) · Rename Apply/Restore 뒤 두 탭 다 갱신 |
| 9 | 필터 `tree_recursive`: 맞는 행 + 조상만 보임, 비우면 원래 펼침 / **기존 트리 모드 사용처 회귀** |
| 10 | Names 아이콘 · `Show in Outliner` · 탭 순서 바뀐 뒤 Blend Shapes 첫 진입 자동 Refresh 유지 |
| 11 | 예시 씬 637 DAG 트리 생성 시간 기록, 합성 1 만 노드 씬 시간 기록(목표 1 초 안쪽 — 넘으면 지연 생성 검토) |

GUI 확인(마야 실기): 아이콘이 테마 위에서 보이는지, 일본어 · 중국어 글꼴 □ 깨짐, 깊은 체인 들여쓰기, 확대 시 아이콘 크기.

## 7. 단계

| 단계 | 내용 | 버전 |
|------|------|------|
| 1 | `maya_icons` + `outline.py` + Outliner 탭(아이콘 · 계층 · Scope · Shapes · 선택 · Sync · 펼치기 · 확대 · Refresh 유지) | v01.02 |
| 2 | blendShape 자식 행 + 타겟 더블클릭 → Blend Shapes 탭 · Filter 계층 모드 · 우클릭 · `Encoded branches only` | v01.02 |
| 3 | Names 아이콘 + `Show in Outliner` · Rename 뒤 두 탭 갱신 | v01.02 |
| 나중 | 씬 변경 자동 갱신(scriptJob `NameChanged` · `DagObjectCreated` · `Undo` + QTimer 디바운스) — 실기에서 Refresh 가 번거로운지 보고 정한다 | v01.03 후보 |

한 버전(v01.02)으로 묶는다 — 단계 1 만으로는 필터가 깊은 트리에서 안 맞아 반쪽 기능이다.

## 8. 하지 않는 것

- **마야 아웃라이너 자체의 글자 바꾸기** — 불가(원본 계획서 §2-3).
- 드래그로 부모 바꾸기 · 이름 고치기 · 보이기 토글 등 **씬을 바꾸는 아웃라이너 기능**. 이 툴은 읽기 툴이다.
- DG 노드 전체(머티리얼 · 디포머 일반) 계층 표시 — Names 탭이 맡는다. blendShape 만 예외.

## 9. 문서 · 기록

- `docs/A00620_NameDecoder.md` — `## 2. Outliner 탭` 절 추가, 뒤 절 번호 밀기, 구조 · 시험 수 갱신
- `app/config/version.py` — 01.02 이력
- `docs/WORKLOG.md` · portfolio EN/KR · 메모리 `wip-a00620-*`
- `Framework/qt/maya_icons.py` 는 공용 위젯 메모와 함께 기록(새 트리 툴도 쓸 수 있게)
