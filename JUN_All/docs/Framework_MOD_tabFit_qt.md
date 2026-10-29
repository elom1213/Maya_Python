---
title: Framework 공용 위젯 — MOD_tabFit_qt (탭마다 창 높이 자동 맞춤)
aliases: [JUN_mod_tabFit_qt, tabFit, 창 높이 자동, 탭 높이 맞춤, fit window to tab]
tags: [framework, qt, widget, maya-python, window-size]
updated: 2026-10-29
---

# `JUN_mod_tabFit_qt_v01` — 탭을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다

| 파일 | 역할 |
|------|------|
| `JUN_All/Framework/qt/MOD_tabFit_qt_v01.py` | 창 + 루트 `QTabWidget` 에 붙는 `QObject`. 중첩 탭 · `QScrollArea` 페이지를 모두 따라간다 |

**첫 적용: `A00275_skinTool_V01` v01.38 (2026-10-29).** 잘 되면 같은 한 줄로 모든 PySide 툴에 적용한다.

## 왜

툴 창의 탭 페이지는 길이가 제각각인데 `QTabWidget` 의 sizeHint / minimumSizeHint 는 **안 보이는 페이지까지
포함한 모든 페이지의 최댓값**이다. 그래서 창을 고정 높이(A00275 는 710)로 열고 긴 페이지는 `QScrollArea` 로
스크롤해 봐야 했다. 사용자 요청: "탭마다 세로 길이에 맞춰 툴의 길이가 자동으로 조절되어 스크롤 없이 모든
UI 가 보이면 좋겠다".

## 사용법

```python
from Framework.qt.MOD_tabFit_qt_v01 import JUN_mod_tabFit_qt_v01

self.tabs = QTabWidget()
...                                   # 페이지(중첩 탭 · QScrollArea 포함)를 다 넣은 뒤
main_layout.addWidget(self.tabs)
self.tab_fit = JUN_mod_tabFit_qt_v01(self, self.tabs)

self.tab_fit.fit_later()              # 페이지 내용이 바뀌어 높이가 달라졌을 때(접기 · 숨김 등)
self.tab_fit.set_enabled(False)       # 끄기 - 정책을 되돌리고 더는 창을 건드리지 않는다
```

- `tabs` 아래의 `QTabWidget` 은 **전부(중첩 포함)** 자동으로 `currentChanged` 에 연결된다. 나중에 생긴 탭도 다음 fit 때 잡는다.
- 처음 보일 때(`showEvent` 다음 이벤트 루프)와 탭을 바꿀 때마다 맞춘다. **폭은 건드리지 않는다.**
- 창의 다른 위젯(로그창 등)은 레이아웃 sizeHint 그대로 더해진다. 로그창처럼 늘어나는 위젯은
  `setMaximumHeight` 가 있어야 창이 그만큼만 커진다(A00275 로그창은 90 ~ 160).

## 동작 규칙

1. **안 보이는 페이지의 세로 size policy 를 `Ignored`** 로 둔다. `QStackedLayout` 은 `Ignored` 방향의
   sizeHint 를 0 으로 치므로 탭 위젯의 sizeHint 가 **현재 페이지만** 따른다. 현재 페이지는 원래 정책으로
   되돌린다(원래 값은 위젯 property 에 기억). 중첩 탭도 같은 규칙 → 바깥 → 안쪽 사슬의 현재 페이지만 남는다.
   덤으로 **창 최소 높이도 현재 페이지 기준**이 되어 [[qtabwidget-min-size-hidden-pages]] 증상(가장자리를 끌어도 안 줄어듦)도 사라진다.
2. **`QScrollArea.sizeHint()` 는 믿지 않는다** — Qt 가 글자 높이의 24배(12px 글꼴이면 약 350px)로 잘라 돌려준다
   (`QScrollArea::sizeHint` 의 `boundedTo(36h, 24h)`, `sizeAdjustPolicy` 와 무관). 보이는 사슬의 스크롤 페이지마다
   **(안 내용 `sizeHint` + 테두리) − 스크롤 영역 `sizeHint`** 를 창 sizeHint 에 더한다. 내용이 작으면 0.
3. 목표 높이 = 그 값을 **모니터 작업 영역 − 타이틀 바**로 자른 것. `resize(폭 유지, 높이)`.
   창 아래가 화면 밖이면 위로 올린다([[window-taller-than-screen-ghost]]).
4. **보정 한두 번** — 레이아웃이 남는 높이를 로그창 같은 다른 Expanding 위젯에도(최대 높이까지) 나눠 주면 스크롤
   페이지가 몇 px 모자란다. 실제 뷰포트를 재서(`shortfall()`) 모자란 만큼 다시 늘린다. A00275 는 8px.
5. 페이지가 화면보다 길면 화면 높이에서 멈추고 **그 페이지만 스크롤**된다. 창을 손으로 줄여도 스크롤.
   `QScrollArea` 의 minimumSizeHint 는 그대로 작으므로 스크롤 영역이 안전망으로 남는다.

## 조심할 것

- **오프스크린 px 은 실제 마야보다 크다**([[offscreen-size-needs-theme]]). 시험의 1295px(Expand Bind) 같은 절대값을 믿지 말고
  "창 높이 = 내용 높이, 뷰포트 ≥ 내용" 같은 **상대 조건**으로 본다. 1080 모니터에선 긴 페이지가 화면 제한에 걸려 스크롤될 수 있다.
- `fit()` 은 창이 보인 뒤에 불러야 뷰포트 보정이 맞는다. 생성자에서 직접 부르지 말고 `fit_later()`.
- 페이지가 `QScrollArea` 가 아니면(내용 위젯을 바로 페이지로) 규칙 1 만으로 맞는다 — A00110 의 `JUN_mod_fit_tab_page_v01` 과 같은 결과.
- 버튼 + `QStackedWidget` 식 페이지 전환은 `QTabWidget` 이 아니라 따라가지 않는다. 그 툴은 `fit_later()` 를 직접 부른다.

## 검증 (2026-10-29, A00275 v01.38, mayapy 2024 + 오프스크린 Qt + green_dark 테마) — 34/34

`tools/A00275_skinTool_V01/tests/test_tab_fit_ui.py`. 모니터 작업 영역은 함수를 바꿔 끼워(2560 x 1392 / 1200 x 600) 두 경로를 다 본다.

- 처음 보일 때 현재 페이지에 맞춤(고정 710 이 아님), 폭 620 유지, 세로 스크롤바 없음 · 뷰포트 = 내용 높이.
- 하위 탭 12개 전부 — 창 높이 = 내용 높이 + 8px 보정, 스크롤바 없음. 가장 긴 Expand Bind 1295 / 가장 짧은 Edit Mesh 619(오프스크린 px).
- 긴 → 짧은 탭이면 **줄어들고**, 다시 가면 되돌아온다(grow only 아님).
- 창 최소 높이 304 — 손으로 400 까지 줄이면 그대로 두고 스크롤바가 생기며, 다음 탭 전환에 다시 맞춘다.
- 작은 화면(600) — 높이 596(작업 영역 − 타이틀 바)에서 멈추고 스크롤, 창 아래가 작업 영역 안.
- 끄면 숨은 페이지 11개의 `Ignored` 정책이 전부 원래대로, 켜면 다시 맞춤.
- 기존 회귀: 하위 페이지는 전부 `QScrollArea`, 상위는 `QTabWidget`(이중 스크롤 없음), `test_move_ui.py` 15/15.
- **마야 GUI 확인 아직.**
