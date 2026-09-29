---
name: window-taller-than-screen-ghost
description: "창을 레이아웃 크기로 맞추면 화면보다 커질 수 있다 — 잘린 아래쪽에 로그창 잔상/흰 영역이 생겨 \"로그창이 두 개\" 로 보고된다"
metadata:
  node_type: memory
  type: project
  originSessionId: d5b551b5-8762-40b3-a989-1e82905540b9
  modified: 2026-09-29T00:11:59.699Z
---

`resize(minimumSizeHint())` 로 창을 내용에 맞추는 툴은 내용이 길면 **모니터 작업 영역보다 커진다**.
윈도우가 창을 화면 끝에서 자르고 그 아래를 Qt 가 그리지 못해, **Win10 · Maya 2023 에선 로그창 잔상, Win11 · Maya 2024 에선 흰 영역**이
푸터 아래에 남는다. 사용자는 이것을 "로그창이 2개로 보인다" 고 말한다(A00480 v01.07, 2026-09-29, 창 592x1067 + 타이틀 바 > 1080).

**Why:** 코드에 로그창이 하나뿐이라 코드만 읽으면 원인이 안 보인다. 개발 PC(2560x1392)에선 재현이 안 된다.

**How to apply:**
- 이런 보고가 오면 먼저 창 높이 + 타이틀 바를 1080(배율 125/150% 면 더 작다) 과 비교한다.
- 고치는 방법(A00480 `main_window.fit_to_content`): 탭을 `QScrollArea`(widgetResizable, NoFrame, 가로 끔)에 담고,
  높이 = `min(내용 높이, screen.availableGeometry().height() - 타이틀 바)`, 화면 밖이면 위로 이동.
- 탭 높이는 **`sizeHint`** 로 잰다 — 스크롤 칸이 없던 때 레이아웃은 탭의 sizeHint 를 최소로 썼다(`minimumSizeHint` 면 리스트가 92px 줄었다).
- 스크롤바 폭은 탭 최소 높이보다 작아질 때만 더한다(리스트가 먼저 줄어드므로).

관련: [[offscreen-size-needs-theme]], [[framework-log-widget]]
