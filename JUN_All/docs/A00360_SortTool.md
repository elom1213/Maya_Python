---
title: A00360_SortTool 사용법
aliases: [Sort Tool, SortTool, A00360]
tags: [maya-python, tool-guide, outliner, sort]
updated: 2026-07-08
---

# A00360_SortTool 사용법

Maya 안에서 도는 **오브젝트 정렬** PySide 툴이다(arch B, in-Maya). 리스트업한 오브젝트들을
**월드 X/Y/Z 위치 · 이름 · 타입** 기준으로 정렬해, **아웃라이너 순서(위→아래)** 와 **TSL 리스트 순서**
를 함께 바꾼다. 위치를 가진 노드면 **조인트·메시·커브·로케이터·클러스터/래티스 핸들** 등 무엇이든 동작한다.

- **버전**: `app/config/version.py` (v01.00)
- **설치**: `__dragDrop_A00360.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 **SortTool** → `tools.A00360_SortTool.run(True)`
- **참고**: 이름/타입 정렬 방식과 아웃라이너 슬롯 스왑 재정렬은 `AriSortOutliner.mel` / `AriSortOutlinerOptions.mel` 을 이식.

---

## 1. 화면 구성

```
┌ Sort Tool ─────────────────────────┐
│ Help                               │
│ [ Select Objects ]                 │  ← 현재 선택으로 리스트 교체
│ Objects              Number: N     │
│ ┌────────────────────────────────┐ │
│ │ pCube1                         │ │   TSL: Add / Del / Up / Down
│ │ joint3                         │ │
│ │ curve2                         │ │
│ └────────────────────────────────┘ │
│ [Add][Del][Up][Down]               │
│ ┌ Sort By ───────────────────────┐ │
│ │ (o)World X ( )World Y ( )World Z│ │
│ │ ( )Name    ( )Type             │ │
│ └────────────────────────────────┘ │
│ [ ] Reverse (descending)           │
│ [x] Reorder in Outliner            │  ← 기본 켜짐
│ [           Sort           ]       │
│ [ log ... ]                        │
└────────────────────────────────────┘
```

---

## 2. 사용법

1. Maya에서 오브젝트들을 선택 → **Select Objects**(현재 선택으로 리스트 교체) 또는 **Add**(중복 없이 추가)로
   **Objects** 리스트에 담는다. Del/Up/Down 으로 편집 가능.
2. **Sort By** 에서 기준을 하나 고른다:
   - **World X / World Y / World Z** — 각 오브젝트의 **월드 절대 위치**(`xform -ws -t`) 해당 축 값.
   - **Name** — 오브젝트 짧은 이름(대소문자 무시).
   - **Type** — 오브젝트 타입(shape 가 있으면 shape 의 nodeType, 없으면 자신), 같은 타입은 이름순.
3. 옵션:
   - **Reverse (descending)** — 내림차순(위 = 큰 값/뒤 이름). 기본은 오름차순(위 = 작은 값/앞 이름).
   - **Reorder in Outliner**(**기본 켜짐**) — 켜면 아웃라이너의 형제 순서를 정렬 순서(위→아래)로 바꾼다.
     끄면 **TSL 리스트만** 재정렬하고 아웃라이너는 건드리지 않는다.
4. **Sort** — TSL 리스트가 정렬 순서(위→아래)로 다시 채워지고(항상), 옵션에 따라 아웃라이너도 바뀐다.
   정렬 후 대상 오브젝트가 Maya에서 재선택되고, 전체가 **한 번의 undo** 로 묶인다.

---

## 3. 동작 원리 / 주의

- **아웃라이너 재정렬(슬롯 스왑, Ari 이식)**: Maya 의 `reorder` 는 **같은 부모의 형제끼리만** 순서를 바꿀 수
  있다. 그래서 대상 오브젝트를 **부모별로 그룹**지어, 각 그룹에서 선택 오브젝트가 **원래 차지하던 슬롯들**을
  정렬 순서로 다시 채운다(`reorder -relative` 스왑). 선택하지 않은 다른 형제는 제자리에 남는다.
- **어떤 오브젝트든**: 위치를 가진 DAG 노드(조인트/메시/커브/로케이터/클러스터·래티스 핸들 등)면 모두 위치
  정렬이 된다. 위치 개념이 없는 **순수 DG 노드**(예: blendShape)는 위치 정렬 시 **크래시 없이 건너뛰고**
  로그에 표시한다. 이름/타입 정렬은 어떤 노드든 가능하며, 아웃라이너 재정렬은 DAG 노드에만 적용된다.
- **이름 해석**: 리스트 항목은 저장된 이름을 정렬 시점에 `cmds.ls(long=True)` 로 재해석한다. 삭제되었거나
  이름이 중복돼 모호하면 건너뛰고(맨 아래에 남김) 로그로 알린다.

---

## 4. 구조

```
tools/A00360_SortTool/
├── launch.py / __init__.py / __dragDrop_A00360.py
├── icon/A00360_SortTool.svg (+ .png)   # 셸프 아이콘(정렬 막대 + 방향 화살표)
└── app/
    ├── config/version.py
    ├── core/sort_manager.py   # 정렬 + 아웃라이너 슬롯 스왑 재정렬 (maya.cmds, UI 비의존)
    └── ui/main_window.py      # PySide UI (TSL + Sort By + 옵션 + 로그)
```

- 핵심 API: `sort_manager.sort_objects(items, mode, reverse, reorder_outliner)` → `(ordered_texts, missing)`.
  `mode` = `MODE_X/Y/Z/NAME/TYPE`. 위치는 `xform(ws)`, 이름은 짧은이름, 타입은 (shape nodeType, 이름).
