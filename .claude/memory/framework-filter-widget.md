---
name: framework-filter-widget
description: 공용 검색 위젯 MOD_filter_qt_v01 — 검색 있는 툴은 전부 이걸로 통일해 나가는 중
metadata: 
  node_type: memory
  type: project
  originSessionId: 85c8852e-52d8-4514-9afa-b44bf5d7ef96
  modified: 2026-08-03T01:41:15.248Z
---

공용 검색/필터 위젯 **`Framework/qt/MOD_filter_qt_v01.py`** (`JUN_mod_filter_qt`, 2026-08-03 신설).
`QListWidget` 에 붙이면 **입력 즉시 일치 항목만 남고 나머지는 `setHidden` 으로 숨는다**.
매칭은 부분 일치·대소문자 무시·**공백 여러 단어 AND**. `number_label` 을 주면
`Number: 보이는수 / 전체수` 자동 갱신.

**Why:** 사용자가 A00290 Base Shape 의 Filter UX 를 특히 마음에 들어 하며
**"점차 모든 툴의 검색 기능을 똑같은 Filter 로 대체"** 하기를 원한다. 툴마다 복사하지 말고
이 위젯을 쓸 것 — 새 툴에 검색을 넣을 때도 자체 구현하지 말 것.

**How to apply:**
- 생성 `JUN_mod_filter_qt_v01(list_widget, placeholder=..., number_label=...)`.
  **목록을 다시 채운 뒤에는 `refresh()` 필수** (새 항목은 숨김 상태가 초기화됨).
- **"보이는 것이 작업 대상"**: Qt 는 숨겨도 선택을 유지하므로 `selectedItems()` 를 그냥 쓰면
  가려진 항목까지 처리된다 → 작업 대상은 **`visible_selected()`** 로 고르고, 가려진 선택 수가
  0 이 아니면 `[INFO] ... hidden by the filter were skipped` 로 알린다.
  `Select All` 은 `selectAll` 대신 **`select_all_visible`** 에 연결.
- 적용 현황: **A00145_RigConnect v01.19**(Connect 탭 src/dst + Attribute 탭).
  **A00290_BSTool v01.12 는 아직 자체 구현** — 공용 위젯으로 이전 예정.
- **확장 지점**: A00290 Shape Editor 탭은 `QListWidget` 이 아니라 **행 위젯 목록**이라 그대로는
  못 붙는다. "무엇을 숨길지"를 콜백으로 받도록 위젯을 확장해야 한다.
- 문서: `JUN_All/docs/Framework_MOD_filter_qt.md` (docs/README.md "공용 위젯" 섹션에 등록).

관련: [[tsl-selection-order]], [[qtreewidgetitem-checkable-default-flag]], [[wip-a00290-shape-editor-tab]]
