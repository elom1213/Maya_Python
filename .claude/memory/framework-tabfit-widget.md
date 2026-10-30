---
name: framework-tabfit-widget
description: 공용 JUN_mod_tabFit_qt_v01 (Framework/qt/MOD_tabFit_qt_v01, 2026-10-29) - 탭마다 창 높이를 현재 페이지에 맞춤. 숨은 페이지 세로 Ignored 는 최소에만 듣고 QTabWidget.sizeHint 는 숨은 페이지 최댓값을 그대로 센다(Qt 5.15) → tab_correction 보정(10-30) + QScrollArea.sizeHint 는 24h 로 잘려 있어 내용으로 보정. 탭 있는 PySide 툴 31곳 전부 적용(A00110_V02 제외), 한 창에 하나만
metadata:
  type: project
---

**탭마다 창 높이를 지금 보이는 페이지에 맞추려면 `Framework/qt/MOD_tabFit_qt_v01.JUN_mod_tabFit_qt_v01(window, root_tabs)` 한 줄.**
사용자 요청(2026-10-29): "스크롤 대신 탭마다 창 길이가 자동으로 조절되어 스크롤 없이 다 보이게. A00275 에 먼저, 잘 되면 모든 툴".
A00275_skinTool_V01 v01.38 이 첫 적용, 사용자 마야 확인("잘 된다") 뒤 같은 날 **탭 있는 PySide 툴 31곳 전부 적용**. 문서 `JUN_All/docs/Framework_MOD_tabFit_qt.md`(사용처 표).
**새 PySide 툴에 탭이 있으면 이 한 줄을 넣는다.** 자체 `fit_to_content` 가 있으면 `enabled=False` 로 만들고 그 끝에서 `set_enabled(True)`.
A00110_V02 만 미적용(다른 세션 작업 중이었음, 자체 grow-only fit 있음) — 손댈 때 같은 방식으로 붙일 것.

- 원리: 안 보이는 탭 페이지의 **세로 size policy 를 `Ignored`** 로(원래 값은 property 에 기억) → `QStackedLayout` 이 0 으로 쳐서
  탭 **minimumSizeHint**(창 최소)가 현재 페이지만 따른다. 모든 중첩 `QTabWidget` 에 같은 규칙. 탭 전환 → `QTimer.singleShot(0)` → `resize(폭 유지, 높이)`,
  모니터 작업 영역 − 타이틀 바로 자르고 창 아래가 화면 밖이면 위로. 첫 `showEvent` 다음 루프에도 한 번(테마 polish 뒤 측정).
- ★★ **`QTabWidget.sizeHint()` 는 그 `Ignored` 를 보지 않는다**(2026-10-30, Qt 5.15.2 실측: Ignored 줘도 951 그대로, minimumSizeHint 만 501→201).
  `QTabWidget::sizeHint` 가 스택 레이아웃을 거치지 않고 **보이는 탭의 모든 페이지 sizeHint 최댓값**을 직접 구한다. 현재 페이지에 글줄 바꿈 라벨(hfw)이
  있으면 `heightForWidth` 경로 = **hfw 가진 페이지들(숨은 것 포함) 최댓값**. 그래서 `tab_correction(within=None)` 이 보이는 사슬의 탭 위젯마다
  (현재 페이지 − 최댓값) 을 같은 규칙으로 재서 `content_height` 에 더하고, `shortfall()` 의 스크롤 내용 sizeHint 에도 `tab_correction(within=내용)` 을 더한다
  (없으면 `tabs_scroll` 툴 A00480 · A00550 · A00240 이 늘 가장 긴 페이지로 되돌아간다). 10-29 에는 페이지가 전부 QScrollArea(sizeHint 24h 로 잘려 다 비슷)인
  A00275 로만 확인해 몰랐다 — **페이지가 맨 위젯인 툴은 모든 탭이 가장 긴 페이지 높이로 열렸다**(A00170 Seal 1080 → Remap 리스트 650px, 사용자 보고).
- 리스트가 길게 열리면 `QListWidget` 기본 sizeHint **192px** 탓 — 공용 TSL `list_hint_height`(A00170 v01.35 = 100, 창 늘리면 따라 늘어남). [[framework-tsl-list-limit]]
- ★ **`QScrollArea.sizeHint()` 는 글자 높이 24배(12px 글꼴 ≈ 350px)로 잘려 있다**(`QScrollArea::sizeHint` 의 `boundedTo(36h, 24h)`,
  `sizeAdjustPolicy` 를 AdjustToContents 로 해도 소용없다 - QScrollArea 가 override). 그래서 보이는 사슬의 스크롤 페이지마다
  (내용 `sizeHint` + 테두리) − 스크롤 `sizeHint` 를 창 sizeHint 에 더한다.
- ★ 레이아웃이 남는 높이를 **로그창(최대 160)에도 나눠 줘** 스크롤 페이지가 8px 모자랐다 → `shortfall()`(내용 − 뷰포트)을 재서 한두 번 더 늘린다.
  `fit()` 은 창이 보인 뒤에만 뜻이 있다(뷰포트 보정).
- ★ **한 창에 인스턴스 하나만** — 둘이면 두 번째 `fit()` 이 창을 최소 높이로 줄인다(A00010 이중 적용 실측 1060 → 793). 한 인스턴스 연속 호출은 안정.
- ★ `self.layout = QVBoxLayout(self)` 로 `layout()` 을 가린 툴(A00080)이 있어 창 레이아웃은 `QWidget.layout(window)` 로 부른다.
- 루트 탭을 감싼 바깥 `tabs_scroll`(A00210 · A00480 · A00550)도 같은 24h 잘림 보정 대상(`scroll_areas()` = 조상 스크롤 + 보이는 스크롤 페이지).
- 전수 시험 `Framework/tests/test_tab_fit_rollout.py`(31 툴 132 검사) - 창 높이 = content_height(+16) · shortfall<=0 · 폭 불변 · **보이는 페이지 높이 ≥ sizeHint(+중첩 보정)** ·
  **더 긴 숨은 페이지가 있으면 tab_correction ≠ 0**, 화면 제한은 통과 처리. 바깥(카테고리) 페이지의 sizeHint 는 중첩 탭 최댓값을 품으니 `tab_correction(page)` 를 더해 비교.
- 스크롤 영역은 그대로 둔다(안전망): 화면보다 긴 페이지 · 손으로 줄인 창은 스크롤. 최소 높이는 늘리지 않는다(A00275 304px).
- 시험은 상대 조건으로: 창 높이 = `content_height()`(+16 이내), 뷰포트 ≥ 내용, 스크롤바 안 보임. 작업 영역은 `_available_geometry` 를 바꿔 끼워 두 경로.
  오프스크린 px 은 마야보다 크다([[offscreen-size-needs-theme]]) - Expand Bind 1295 는 1080 모니터에서 화면 제한에 걸린다.
- A00110_V02 의 `JUN_mod_fit_tab_page_v01` + `_fit_window(grow_only)` 는 같은 목적의 툴별 구현(페이지 위젯 교체 필요). 이 위젯은 **기존 페이지를 바꾸지 않고** 붙는다.

관련: [[qtabwidget-min-size-hidden-pages]], [[window-taller-than-screen-ghost]], [[framework-log-widget]]
