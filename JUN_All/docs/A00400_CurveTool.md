---
title: A00400_CurveTool 사용법
aliases: [Curve Tool, CurveTool, A00400]
tags: [maya-python, tool-guide, curve, mesh-edge, polyToCurve, lineWidth]
updated: 2026-08-13
---

# A00400_CurveTool 사용법

Maya 안에서 도는 **커브** PySide 툴이다(arch B, in-Maya). **탭 2개**로 나뉜다(v01.01).

| 탭 | 내용 |
|----|------|
| **Create / Direction** | ① 선택한 메시 엣지에 부착된 커브 생성(엣지 덩어리마다 커브 하나) ② Reverse Direction(방향 통일) |
| **Line Width** (v01.01~) | 리스트업한 커브의 **뷰포트 표시 굵기**를 슬라이더로 조절 — 씬에서 **잘 보이고 잘 집히게** |

- **버전**: `app/config/version.py` (v01.02)
- **설치**: `__dragDrop_A00400.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **CurveTool** → `tools.A00400_CurveTool.run(True)`
- **참고**: 엣지→커브 생성은 `ref/ref_01.mel`(`duplicateCurve`+`attachCurve`)의 아이디어를, 축 비교 방식은 `A00360_SortTool` 을 이식/응용.

---

## 1. 화면 구성

```
┌ Curve Tool ─────────────────────────┐
│ Help                                │
│ ┌ Create Curves from Mesh Edges ──┐ │
│ │ Name Prefix [ edgeCurve       ] │ │
│ │ [ ] Smooth curve (degree 3)     │ │
│ │ [ Create Curves from Sel Edges ]│ │
│ └─────────────────────────────────┘ │
│ [ List Selected Curves ]            │  ← 씬에서 커브 골라 담기(선택)
│ Curves               Number: N      │
│ ┌─────────────────────────────────┐ │
│ │ edgeCurve_01                    │ │   TSL: Add / Del / Up / Down
│ │ edgeCurve_02                    │ │
│ │ edgeCurve_03                    │ │
│ └─────────────────────────────────┘ │
│ [Add][Del][Up][Down]                │
│ ┌ Reverse Direction ──────────────┐ │
│ │ Compare Axis ( )X (o)Y ( )Z     │ │
│ │ cv[0] at (o)Max end ( )Min end  │ │
│ │ [       Reverse Direction      ]│ │
│ └─────────────────────────────────┘ │
│ [ log ... ]                         │
└─────────────────────────────────────┘
```

---

## 2. 사용법

### 2-1. 엣지 → 커브 생성

1. Maya에서 메시의 **엣지**를 선택한다. 여러 개의 **떨어진 엣지 구간**을 함께 골라도 된다
   (예: `pSphere1.e[156:158]`, `pSphere1.e[196:199]`, `pSphere1.e[236:239]`).
2. 옵션:
   - **Name Prefix** — 생성 커브 이름 접두사(`<prefix>_01`, `<prefix>_02` …). 기본 `edgeCurve`.
   - **Smooth curve (degree 3)** — 끄면 엣지를 그대로 따르는 **직선(degree 1)**, 켜면 **부드러운 곡선(degree 3)**.
3. **Create Curves from Selected Edges** — 붙어 있는 엣지 덩어리마다 커브 1개씩 생성해 **Curves** 리스트에 담는다.
   위 예시는 **커브 3개**가 나온다. 생성 커브는 `constructionHistory` 로 **메시에 부착**(엣지가 움직이면 따라감)된다.
   전체가 **한 번의 undo** 로 묶인다.

> ref_01.mel 은 선택 전체를 커브 **1개**로만 묶어(떨어진 세 구간을 골라도 커브 1개), 여러 커브를 만들지 못했다.
> 이 툴은 그 한계를 풀어 **엣지 그룹마다 커브 1개**를 만든다.

### 2-2. Reverse Direction (방향 통일)

1. 방향을 맞출 커브들을 **Curves** 리스트에 둔다(생성 직후 자동으로 담겨 있거나, 씬에서 커브를 골라 **List Selected Curves**/Add).
2. **Compare Axis** — 비교할 월드 축(**X / Y / Z**, 기본 **Y**).
3. **cv[0] at** — `cv[0]` 이 와야 할 끝:
   - **Max end** (기본) — 축의 **큰 쪽**(예: Y 위쪽). "위 → 아래" 로 cv 를 정렬하고 싶을 때.
   - **Min end** — 축의 **작은 쪽**(예: Y 아래쪽).
4. **Reverse Direction** — 각 커브의 `cv[0]`/`cv[n]` 축값을 비교해, `cv[0]` 이 지정한 끝에 오도록 방향이 반대면
   `reverseCurve` 로 뒤집는다. 이미 맞는 커브는 그대로 둔다. 전체가 **한 번의 undo**.

> 예) 씬 위에서 아래로 cv 가 정렬되길 원하면 **Axis=Y, cv[0] at Max**. `cv[0]` 이 위에 있으면 방치, 아래에 있으면 뒤집는다.

---

## 3. 동작 원리 / 주의

- **엣지 그룹핑(연결 성분)**: 두 엣지가 정점을 공유하면 같은 그룹(BFS). 서로 다른 메시의 엣지는 정점을 공유할 수
  없어 자연히 다른 그룹으로 갈린다. 그룹마다 그 엣지들을 선택해 `polyToCurve(form=2, degree, ch=1)` 로 커브 1개를 만든다.
- **왜 polyToCurve 인가**: ref 의 `duplicateCurve`+`attachCurve`(각 엣지를 작은 커브로 뜬 뒤 이어붙임)와 결과는
  같은 "엣지를 따라가는 부착 커브"지만, `polyToCurve` 가 **엣지 체인의 cv 순서를 스스로 정렬**해 줘 더 견고하고
  **`cv[0]`/`cv[n]` 끝점이 명확**하다(방향 정렬에 필요). `form=2` 로 열림/닫힘을 자동 판단한다(엣지 루프면 닫힘).
- **방향 비교**: `cv[0]`/`cv[n]` 의 월드 위치(`pointPosition -w`) 축 성분을 비교한다. 두 끝의 축값이 **같으면**
  (예: 위도 링처럼 수평 커브를 Y 로 비교) 판단 불가라 **건너뛰고** 로그에 표시한다. 커브가 아니거나 cv 가 2개 미만인
  항목도 건너뛴다.
- **UUID 안전**: Reverse 대상은 TSL 의 `get_all_nodes()`(UUID 기반)로 현재 경로를 되찾아, 리네임/리페어런트 후에도 정확히 그 커브를 잡는다.

---

## 4. 구조

```
tools/A00400_CurveTool/
├── launch.py / __init__.py / __dragDrop_A00400.py
├── icon/A00400_CurveTool.svg (+ .png)   # 셸프 아이콘(커브 + CV 포인트 + 방향 화살표)
├── ref/ref_01.mel                       # 참고: 단일 커브 attach 방식 MEL
└── app/
    ├── config/version.py
    ├── core/curve_manager.py   # 엣지 그룹핑 + polyToCurve + reverseCurve (maya.cmds, UI 비의존)
    └── ui/main_window.py       # PySide UI (생성 박스 + TSL + Reverse 박스 + 로그)
```

- 핵심 API:
  - `curve_manager.curves_from_selected_edges(prefix, degree)` → `(created_curves, group_count)`
  - `curve_manager.reverse_curves_by_axis(curves, mode, cv0_at_max)` → `(reversed_names, skipped)`
    - `mode` = `MODE_X/Y/Z`, `cv0_at_max=True` 면 `cv[0]` 을 축 최대 끝에.
  - `curve_manager.group_edges(edges)` → 연결 성분별 엣지 그룹 리스트.

---

## Line Width 탭 (v01.01~) — 커브를 잘 보이고 잘 집히게

씬에 커브가 많아지면 얇은 선은 **눈에 잘 안 띄고 클릭으로 집기도 어렵다.** 이 탭은 리스트업한
커브의 `nurbsCurve.lineWidth`(뷰포트에 그려지는 선 굵기)를 한 번에 바꾼다.

> **표시 전용이다.** 커브의 형상·CV·히스토리는 전혀 건드리지 않는다. 렌더에도 영향이 없다.

### 사용법

1. 씬에서 커브를 고르고 **List Selected Curves** 로 리스트에 담는다(이 탭 전용 리스트).
2. **슬라이더를 드래그**하면 리스트의 모든 커브에 **실시간**으로 반영되고,
   **손을 떼는 순간 그 값으로 확정**된다(v01.02~ — 따로 누를 버튼이 없다).
   오른쪽 스핀박스로 정확한 값(0.1 단위)을 넣어도 된다(Enter/포커스 아웃이 곧 확정).
   둘은 항상 같이 움직인다.
3. 필요하면 **Get**(첫 커브의 값 읽어오기) / **Use Maya Default (-1)**.

| 버튼·값 | 뜻 |
|---------|-----|
| 슬라이더 · 스핀박스 | 0.0 ~ 10.0. 숫자가 클수록 굵게 그려진다. **놓는 즉시 적용**(Apply 버튼 없음) |
| **Use Maya Default (-1)** | `lineWidth = -1` — **마야 전역 라인 굵기 설정을 따른다**(커브의 원래 기본값) |
| **Get** | 리스트 첫 커브의 현재 값을 슬라이더로 가져온다. `-1` 이면 로그로 알려 주고 슬라이더는 최솟값에 둔다 |

### 알아둘 것

- **드래그 한 번이 undo 한 스텝**이다(누를 때 청크를 열고, **확정 적용까지 마친 뒤** 닫는다).
  드래그 중 수십 번 값이 바뀌어도 `Ctrl+Z` 한 번이면 원래대로 돌아온다.
  > 확정을 청크 **밖**에서 하면 드래그 하나가 undo 두 스텝으로 갈라진다(v01.02 에서 고침).
- 커브가 아닌 항목, `lineWidth` 어트리뷰트가 없는 **구버전(Maya 2019 미만)**, 잠기거나 연결된
  어트리뷰트는 **사유와 함께 건너뛰고** 나머지는 계속 처리한다.
- 리스트는 UUID 로 현재 경로를 되찾으므로 **리네임·리페어런트 후에도** 같은 커브를 잡는다.
- 커브 하나에 셰이프가 여럿이면 **모든 nurbsCurve 셰이프**에 적용한다.
