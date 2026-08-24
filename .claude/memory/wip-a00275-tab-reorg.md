---
name: wip-a00275-tab-reorg
description: A00275 탭 재분류 — 평평한 탭 7개를 Weights/Bind/Edit 카테고리 3 → 기능 7 의 2단 구조로 (v01.15)
metadata: 
  node_type: memory
  type: project
  originSessionId: cce9837c-ee83-4545-8532-e6317949f1f2
  modified: 2026-08-24T08:42:34.260Z
---

A00275_skinTool_V01 **탭 재분류** (v01.14→**01.15**, 2026-08-24).
계획서: `JUN_All/docs/plans/A00275_skinTool_V01_tab_reorg_plan.md`.
**상위 탭 = 카테고리, 하위 탭 = 기능** — [[wip-a00110-tab-taxonomy]] 와 같은 원칙,
구현 골격은 `A00145_RigConnect` 의 `_build_sub_tabs` + `_scrolled`.

| 상위 | 뜻 | 하위 |
|---|---|---|
| **Weights** | 웨이트를 다른 곳으로 옮긴다 | Classic · Transfer · Migrate A -> B |
| **Bind** | 바인드를 만들거나 바인드 상태를 갱신 | Bind Pose · Expand Bind |
| **Edit** | 웨이트를 그대로 둔 채 리그를 고친다(Edit 토글) | [[wip-a00275-move-joints]] · [[wip-a00275-edit-mesh]] |

기능·이름·레이아웃은 **하나도 바꾸지 않았다.** 기존 `_build_*_tab()` 7개를 그대로 둔 채
`CATEGORIES` 표 하나 + 골격 3개로 **묶기만** 했다. 탭을 더할 때는 그 표에 줄만 넣는다.

**이 작업의 진짜 위험은 분류가 아니라 `_on_tab_changed` 였다.**
상위 탭 인덱스로 갈라지고 있었는데(`index == self.je_tab_index`), 중첩하면 그 인덱스가
**카테고리 인덱스**가 되어 영영 일치하지 않는다. 그러면 **에러 하나 없이** Move Joints ·
Edit Mesh 의 씬 상태 재조회가 죽어서, 툴을 껐다 켰을 때 편집 중이던 대상을 못 되찾는다
(두 탭의 핵심 약속). **중첩 탭으로 바꿀 때는 인덱스로 판단하는 코드를 먼저 찾을 것.**
지금은 상위 = 위젯 동일성(`self.edit_page`), 하위 = `EDIT_PAGES` 순서와 묶인 상수
(`JE_SUB_INDEX` / `ME_SUB_INDEX`). 상위·하위 두 `currentChanged` 를 같은 슬롯에 연결한다.

그 밖에:
- 하위 페이지마다 `QScrollArea`. **상위에는 씌우지 않는다**(이중 스크롤) —
  [[prefer-subtabs-over-stacked-collapsibles]]. 창을 콘텐츠에 맞춰 늘리는 툴이 아니라
  A00110 의 fit page 가 아니라 스크롤이 맞다. `tabs.widget(i)` 가 이제 `QScrollArea` 다.
- 실측: 하위 탭 바 폭 최대 246px(창 620), 가장 긴 페이지 `Expand Bind` 850px
  → 창 높이 680→710. `find_editing_in_scene()` 은 메시 5,000개에서 205ms
  (`cmds.ls("*.<attr>")` 는 21ms 지만 중복·네임스페이스 결과가 달라 미적용).
- 검증: UI 스모크 25→**52항목**(라벨·툴팁·스크롤 래핑·위젯 12개 접근 +
  **씬 동기화 회귀 4종**) + 코어 51항목 그대로 통과.
