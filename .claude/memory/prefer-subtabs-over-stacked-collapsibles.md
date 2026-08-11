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

**관련 요청(2026-08-10, 같은 날)**: 최상위 탭이 많아도 같은 정리를 원한다 — "Connect,
List Connected, Connect Closest 도 하나의 탭의 하위탭이 되도록". 성격이 같은 최상위 탭들은
상위 탭 하나로 묶고 하위 탭으로 내린다.

**이중 스크롤 주의**: 원래 최상위 탭이던 화면은 스스로 `QScrollArea` 를 반환하는 경우가 있다.
하위 탭으로 내릴 때 `_scrolled()` 로 또 감싸면 스크롤이 겹치므로, 페이지는 평범한 `QWidget` 을
반환하게 고칠 것.

**창이 콘텐츠에 맞춰 자동 리사이즈되는 툴에서는 스크롤 영역을 쓰면 안 된다.**
A00110_animTool 은 `_fit_window` 로 창 높이를 현재 탭 내용에 맞춘다. 이 방식은 숨은 페이지가
sizeHint 0 을 보고해야 성립하는데(`QStackedLayout` 은 모든 페이지 sizeHint 의 **최댓값**을 쓴다),
`QScrollArea` 는 콘텐츠와 무관한 sizeHint 를 가져 그 규칙을 깨뜨린다. 이런 툴에서는 스크롤 대신
**상위 페이지도 하위 페이지도 `Framework/qt/MOD_collapsible_qt_v01.JUN_mod_fit_tab_page_v01`** 로
둔다. 하위 탭 전환에도 상위 탭 전환과 같은 규칙으로 창을 맞춘다(`_fit_window_later(grow_only=True)`).

적용 사례:
- A00145_RigConnect — Constrain 탭 v01.22(접이식 5개 → 하위 탭),
  Connect 탭 v01.23(최상위 3탭 → 하위 탭, 최상위 6→4탭). 페이지는 `QScrollArea` 로 감싼다.
- A00110_animTool — Key Edit 탭 v01.39(접이식 5개 → 하위 탭). **스크롤 없이 fit page** 사용.

모두 `<GROUP>_PAGES` 테이블 + 공통 `_build_sub_tabs(pages)` 헬퍼로 만든다.
