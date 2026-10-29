---
name: framework-tabfit-widget
description: 공용 JUN_mod_tabFit_qt_v01 (Framework/qt/MOD_tabFit_qt_v01, 2026-10-29) - 탭마다 창 높이를 현재 페이지에 맞춤. 숨은 페이지 세로 Ignored + QScrollArea.sizeHint 는 24h 로 잘려 있어 내용으로 보정. A00275 v01.38 첫 적용, 잘 되면 전 툴
metadata:
  type: project
---

**탭마다 창 높이를 지금 보이는 페이지에 맞추려면 `Framework/qt/MOD_tabFit_qt_v01.JUN_mod_tabFit_qt_v01(window, root_tabs)` 한 줄.**
사용자 요청(2026-10-29): "스크롤 대신 탭마다 창 길이가 자동으로 조절되어 스크롤 없이 다 보이게. A00275 에 먼저, 잘 되면 모든 툴".
A00275_skinTool_V01 v01.38 이 첫 적용 — **마야 GUI 확인 뒤 전 툴 롤아웃 예정**(아직 안 함). 문서 `JUN_All/docs/Framework_MOD_tabFit_qt.md`.

- 원리: 안 보이는 탭 페이지의 **세로 size policy 를 `Ignored`** 로(원래 값은 property 에 기억) → `QStackedLayout` 이 0 으로 쳐서
  탭 sizeHint · 최소가 현재 페이지만 따른다. 모든 중첩 `QTabWidget` 에 같은 규칙. 탭 전환 → `QTimer.singleShot(0)` → `resize(폭 유지, 높이)`,
  모니터 작업 영역 − 타이틀 바로 자르고 창 아래가 화면 밖이면 위로. 첫 `showEvent` 다음 루프에도 한 번(테마 polish 뒤 측정).
- ★ **`QScrollArea.sizeHint()` 는 글자 높이 24배(12px 글꼴 ≈ 350px)로 잘려 있다**(`QScrollArea::sizeHint` 의 `boundedTo(36h, 24h)`,
  `sizeAdjustPolicy` 를 AdjustToContents 로 해도 소용없다 - QScrollArea 가 override). 그래서 보이는 사슬의 스크롤 페이지마다
  (내용 `sizeHint` + 테두리) − 스크롤 `sizeHint` 를 창 sizeHint 에 더한다.
- ★ 레이아웃이 남는 높이를 **로그창(최대 160)에도 나눠 줘** 스크롤 페이지가 8px 모자랐다 → `shortfall()`(내용 − 뷰포트)을 재서 한두 번 더 늘린다.
  `fit()` 은 창이 보인 뒤에만 뜻이 있다(뷰포트 보정).
- 스크롤 영역은 그대로 둔다(안전망): 화면보다 긴 페이지 · 손으로 줄인 창은 스크롤. 최소 높이는 늘리지 않는다(A00275 304px).
- 시험은 상대 조건으로: 창 높이 = `content_height()`(+16 이내), 뷰포트 ≥ 내용, 스크롤바 안 보임. 작업 영역은 `_available_geometry` 를 바꿔 끼워 두 경로.
  오프스크린 px 은 마야보다 크다([[offscreen-size-needs-theme]]) - Expand Bind 1295 는 1080 모니터에서 화면 제한에 걸린다.
- A00110_V02 의 `JUN_mod_fit_tab_page_v01` + `_fit_window(grow_only)` 는 같은 목적의 툴별 구현(페이지 위젯 교체 필요). 이 위젯은 **기존 페이지를 바꾸지 않고** 붙는다.

관련: [[qtabwidget-min-size-hidden-pages]], [[window-taller-than-screen-ghost]], [[framework-log-widget]]
