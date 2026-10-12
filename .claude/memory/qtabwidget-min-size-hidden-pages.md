---
name: qtabwidget-min-size-hidden-pages
description: QTabWidget 의 최소 크기는 숨은 페이지까지 모든 페이지 최소의 최댓값 — 창이 거기에 붙어 가장자리로 못 줄인다(화면만큼 크면 못 늘린다). 탭을 QScrollArea 에 담고 여는 크기는 fit_to_content 로
metadata:
  node_type: memory
  type: project
  originSessionId: 9851bc3c-33e0-43d3-9d39-fe7b39c172be
  modified: 2026-10-12T02:37:45.390Z
---

**증상**: 툴 창의 가장자리를 끌어도 크기가 안 바뀐다 (A00210 v01.36, 2026-10-12 사용자 보고. A00480 v01.07 의 "로그창 두 개" 도 뿌리가 같다).

**원인**: `QTabWidget` 의 `minimumSizeHint` 는 **현재 안 보이는 페이지까지 포함한** 모든 페이지 최소 크기의 최댓값이다.
탭 하나가 크면(A00210 은 File Manager 탭 세로 · Lineage 탭 가로) 창 전체 최소가 그 크기가 되고, 레이아웃이 창 최소를 강제하므로
창이 최소에 붙어 줄일 수 없다. 화면 작업 영역보다 크면 늘릴 수도 없어 "아무 반응이 없다" 로 보인다. 오프스크린 측정값은
실제 마야/화면 px 보다 크므로([[offscreen-size-needs-theme]]) 숫자 자체보다 **어느 탭이 최대인가**를 본다.

**고치는 법**: 탭을 `QScrollArea(widgetResizable=True, NoFrame)` 에 담아 최소 크기를 작게 하고, **여는 크기는 예전과 같게**
`fit_to_content()` 로 — `tabs.minimumSizeHint()` + (창 최소 − 스크롤 칸 최소) 를 모니터 `availableGeometry` 까지로 잘라
`resize`, 창 아래/오른쪽이 화면 밖이면 `move`. 첫 `showEvent` 다음 이벤트 루프(`QTimer.singleShot(0, ...)`)에서 재야
테마 polish 뒤 글자 크기로 잰다. 내용보다 작게 열리면 스크롤바 폭만큼 더해 잘림을 막는다.
구현: `tools/A00210_FileManager/app/ui/main_window.py` `fit_to_content`, `tools/A00480_FileTool/app/ui/main_window.py` 동일.

**검증**: 오프스크린에서 `minimumSizeHint` 가 작아졌는지 · `resize(600, 400)` 이 먹는지 · 여는 높이가 `min(탭 최소, 화면)` 인지.

관련: [[window-taller-than-screen-ghost]], [[offscreen-size-needs-theme]]
