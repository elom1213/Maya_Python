---
title: A00400_CurveTool 사용법
aliases: [Curve Tool, CurveTool, A00400]
tags: [maya-python, tool-guide, curve, mesh-edge, polyToCurve]
updated: 2026-07-29
---

# A00400_CurveTool 사용법

Maya 안에서 도는 **커브** PySide 툴이다(arch B, in-Maya). 두 가지를 한다.

1. **선택한 메시 엣지에 부착된 커브 생성** — 떨어져 있는 엣지 덩어리(연결 성분)마다 **커브를 따로** 만든다.
2. **Reverse Direction** — 리스트업한 커브들의 `cv[0]`/`cv[n]` 월드 위치를 지정 축으로 비교해 **방향을 통일**한다.

- **버전**: `app/config/version.py` (v01.00)
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
