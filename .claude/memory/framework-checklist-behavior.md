---
name: framework-checklist-behavior
description: 체크박스 QListWidget 의 다중 선택+다중 체크는 공용 동작 MOD_checkList_qt_v01 을 붙인다 (직접 eventFilter 짜지 말 것)
metadata: 
  node_type: memory
  type: project
  originSessionId: 8fc27b42-f7ec-4155-b340-da985ee075b0
  modified: 2026-09-18T01:03:44.229Z
---

`Framework/qt/MOD_checkList_qt_v01.py` (`JUN_mod_checkList_qt`, 2026-09-18 신설, A00145 v01.49 첫 사용).
기존 `QListWidget` 에 `JUN_mod_checkList_qt_v01(lw)` 한 줄로 붙인다 — Shift/Ctrl 선택, 고른 행 체크박스(또는 Space) = 보이는 고른 행 전부.

**Why:** Qt 기본 처리는 체크박스 누르기가 선택을 한 행으로 풀어 다중 체크가 첫 번만 된다(A00275 에서 실측, [[wip-a00275-select-by-weight]]). 사용자가 "이런 tsl + 체크박스 UI 를 공용으로 만들지 판단" 을 요청 → 새 위젯이 아니라 붙이는 동작으로 결정(필터 [[framework-filter-widget]]·라벨을 그대로 두려고).

**How to apply:** 체크 목록에 다중 체크가 필요하면 이걸 붙인다. 가려진 행 · 비활성(회색) 행은 안 바꾼다. 신호는 `checksChanged(바뀐 전부)` → `itemChanged(누른 행)` 한 번 순서 — **행마다 라벨 등을 고쳐야 하면 checksChanged 를 받을 것**(A00290 Sources 가 그 예). 코드의 `setCheckState` 는 전파 안 됨. maya 없이 import 되므로 standalone 툴에도 쓴다.
적용(2026-09-18): A00145 Edit/Create, A00290_V02 Mix 두 목록, A00275 By Weight(자체 eventFilter 대체), A00210 Scan 다이얼로그/Folders. 제외: 트리·표(QListWidget 전용), A00290 V01(옛 버전).
