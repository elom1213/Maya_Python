---
name: prefer-subtabs-over-stacked-collapsibles
description: 한 탭 안에 기능 섹션이 여러 개면 접이식으로 쌓지 말고 중첩 탭으로 옆에 나열
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ee81a66a-5136-4bb8-b44a-7fa187164cdb
  modified: 2026-08-10T06:07:54.169Z
---

한 탭 안에 독립적인 기능 섹션이 **3~4개를 넘어가면** 접이식 박스(`CollapsibleBox`)로 위아래로
쌓지 말고 **중첩 `QTabWidget`(하위 탭)** 으로 옆에 나열한다.

**Why:** 2026-08-10 사용자 요청 — "이 접이식 UI 가 모두 탭으로 보여졌으면 해. 즉 Constrain 탭을
선택하면 하위의 또다른 탭으로서 옆으로 나열되도록". 섹션이 늘면 원하는 기능을 보려고 접었다 폈다
해야 하고, 전부 펼치면 창 높이를 넘겨 스크롤이 필요해진다. 탭이면 **한 번에 기능 하나만** 보인다.

**How to apply:**
- 각 섹션 빌더는 `page = QWidget()` + `layout = QVBoxLayout(page)` → `return page` 로 두고
  (탭 빌더 관용구와 동일), 상위에서 `tabs.addTab(self._scrolled(page), label)`.
- **하위 탭마다 개별 스크롤**을 건다. 탭 전체를 감싸는 스크롤보다 창 축소에 강하다.
- 라벨은 창 폭에 맞게 짧게, **전체 이름은 `setTabToolTip`** 에. `tabBar().setElideMode(Qt.ElideRight)`
  로 폭이 모자랄 때 말줄임(스크롤 화살표만 뜨는 것보다 읽기 쉽다).
- 접이식이 여전히 맞는 곳: 한 화면에서 **동시에** 봐야 하는 보조 섹션(예: A00145 Connect 탭의
  Source/Destination) — 이건 그대로 `CollapsibleBox` 를 쓴다.

적용 사례: A00145_RigConnect Constrain 탭 v01.22 ([[wip-a00145-target-replace]] 의 부수 변경 갱신).
