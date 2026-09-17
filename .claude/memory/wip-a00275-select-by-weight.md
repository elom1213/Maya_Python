---
name: wip-a00275-select-by-weight
description: "A00275 Select > By Weight (v01.27) — 체크한 조인트 웨이트가 Value 이상/이하인 버텍스 선택, 범위는 불러올 때 저장. QListWidget 체크박스 기본 클릭은 다중 선택을 한 행으로 푼다 → viewport eventFilter"
metadata: 
  node_type: memory
  type: project
  originSessionId: cf65e8e8-8aeb-40db-95e4-19cac03d7a7f
  modified: 2026-09-17T02:37:52.244Z
---

A00275_skinTool_V01 **Select > By Weight** (v01.26→**01.27**, 2026-09-17). 새 상위 카테고리 `Select`
(기존 Weights/Bind/Edit 어디에도 "씬을 안 바꾸고 고르기만" 이 안 맞아서). 코어 `app/core/weight_select_manager.py`,
UI `app/ui/weight_select_tab.py` (Layer 탭처럼 위젯 하나). [[wip-a00275-tab-reorg]] 의 `CATEGORIES` 표에 줄만 추가.

- **범위(메시 전체 / 버텍스 일부)는 Load 때 저장한다.** 결과 선택이 마야 선택을 바꾸고, TSL 행 클릭도 조인트를
  선택하므로 실행 시점 선택을 범위로 쓰면 Value 만 바꿔 다시 고르는 흐름이 깨진다. 전체는 `vertices=None`.
- 여러 조인트: Any(기본) / All / Sum. 경계 포함 1e-6. `getWeights` 한 번 — 19,802 버텍스 0.03s.
- **★ QListWidget 에 `ItemIsUserCheckable` 을 주고 기본 처리에 맡기면**, 여러 행을 고른 뒤 체크박스를 누를 때
  itemChanged 전파는 되지만 **선택이 누른 행 하나로 풀린다**(오프스크린 QTest 실측, PySide2). 체크박스 영역
  (`SE_ItemViewItemCheckIndicator`) 위 press/release/dblclick 을 viewport eventFilter 에서 먹고 release 에서
  한 번만 뒤집었다. QTreeWidget 쪽 함정은 [[qtreewidgetitem-checkable-default-flag]].
- 테스트 함정: 목록에 여러 행이 선택된 채 코드로 `setCheckState` 해도 전파가 일어난다(의도된 동작).
- 검증 43항목(`skinPercent` 로 센 답과 비교, 실제 클릭). 포트폴리오는 갱신 안 함(소규모 유틸).
