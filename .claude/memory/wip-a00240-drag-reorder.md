---
name: wip-a00240-drag-reorder
description: A00240_PathTool v01.28 — Path 버튼 드래그 정렬은 QDrag 아닌 _PathButton 마우스 이벤트(press/move/release)로, (cat_index, btn_index) 키, 색칠 모드는 끔 · v01.29 창 자유 크기 · v01.30 페이지별 QScrollArea + _ElideButton(setMinimumWidth + 말줄임, 전체 라벨 힌트 캐시)
metadata:
  type: project
---

A00240_PathTool **v01.28** (2026-10-23) — Shortcut 탭의 Path 버튼을 누른 채 끌어 놓아 순서 · 카테고리를 바꾼다.
사용자가 "마우스 클릭 · 홀드 · 이동 · 해제" 로 요청, 진단 뒤 **네이티브 QDrag 가 아니라 버튼 서브클래스의 마우스
이벤트만으로** 하는 안을 골랐다(클릭/드래그 구분 · 색칠 모드 예외 · 가로줄 · 자동 스크롤을 한 곳에서 제어).

**How to apply (같은 패턴을 다른 버튼 묶음에 쓸 때, 예: A00340_SelectionTool):**
- `_PathButton(QPushButton)`: press 에 전역 좌표 기억 → move 가 `QApplication.startDragDistance()` 넘으면 `owner.begin_drag`,
  이후 `update_drag(global)` → release 는 `end_drag` 로 가고 **super 를 부르지 않아 clicked 가 안 나간다**. 그 거리 안의 놓음은
  super 로 가 평소 클릭. Qt 는 누른 위젯에 move/release 를 계속 보내므로(암묵 grab) 커서가 밖으로 나가도 받는다.
- Esc 취소: 버튼 `keyPressEvent` 에서 `cancel_drag` + `_swallow_release=True` — 안 그러면 뒤따르는 release 가 클릭이 되어 경로가 열린다.
- 전역 좌표는 PySide6 `globalPosition().toPoint()` / PySide2 `globalPos()` 둘 다 대응(`_global_pos`).
- 자리 계산은 **인덱스**로: 버튼 `drag_key = (cat_index, btn_index)`. 기존 메뉴 기능은 이름으로 찾아(`_find_button`) 같은 이름이 둘이면 틀릴 수 있다.
- 가로줄 `_drop_line` 은 레이아웃 항목이 아닌 컨테이너의 자식 QFrame — 재렌더의 `takeAt` 루프에 지워지지 않고 함께 스크롤된다. `raise_()` 필요.
- 자동 스크롤은 QTimer 40ms 틱으로 마지막 전역 좌표를 다시 계산 — 커서가 멈춰 있어도 내용이 움직이니 move 이벤트만으론 안 된다.
- 색칠 모드(체크형 버튼)에서는 `drag_enabled=False` — 체크 토글과 드래그 판정이 섞이지 않게.
- `QMessageBox.warning` 은 모달이라 오프스크린 테스트에서 모듈 속성을 바꿔 가로챈다. 테스트는 `prefs_mod.PREFS_DIR/PROFILES_DIR/ACTIVE_PATH/LEGACY_PATHS` 를 스크래치로 바꿔 실데이터를 안 건드린다.

**v01.29** — 창이 어느 폭 아래로 안 줄던 것은 [[qtabwidget-min-size-hidden-pages]] (Junction 탭 TSL 둘 나란히 = 978 이 바닥).
탭을 `QScrollArea`(NoFrame) 에 담고 `fit_to_content` 를 A00210 에서 그대로 — 최소 가로 1004 → 172. Shrink 는 `tabs_scroll` 을 감춘다.

**v01.30 — 버튼이 창 폭을 따른다 (말줄임).** 사용자: "창을 줄이면 버튼도 줄고 글자가 안 잘리게".
- 바깥 스크롤 칸 하나는 **페이지를 좁히지 못한다** — `QScrollArea(widgetResizable)` 는 위젯을 `max(뷰포트, 최소)` 로 두므로 탭 위젯이
  가장 넓은 페이지 폭으로 남는다. 페이지를 창 폭에 따르게 하려면 **페이지마다** 스크롤 칸(`_wrap_page`). `fit_to_content` 는 페이지
  최소의 축별 최댓값(`_pages_min_size`)으로.
- QPushButton 이 창을 막는 이유는 최소 폭 = 글자 폭. `setMinimumWidth(n)` 을 걸면 Qt 레이아웃(`qSmartMinSize`)이 minimumSizeHint 를
  안 쓴다 → `_ElideButton`: 최소 40 + `resizeEvent` 말줄임 + `full_text` · 툴팁 첫 줄. **가로 sizePolicy Ignored 는 쓰지 말 것** —
  QHBox 에서 stretch 있는 이웃이 남는 폭을 다 가져가 버튼이 0 폭이 된다(VBox 에서만 무해).
- 함정 1: 말줄임된 글자로 sizeHint 를 재면 힌트↓ → 레이아웃이 덜 줌 → 더 말줄임 되먹임, 한 행이 고르지 않게 줄어든다. **전체 라벨 기준
  힌트를 캐시**하고(`_refresh_hints`), 재는 건 생성 · setText · StyleChange/FontChange 때만 — sizeHint() 안에서 setText(updateGeometry) 금지.
  QPushButton 힌트에는 스타일 최소 폭 바닥이 있어 "글자 폭 차로 보정" 은 틀린다(New 54 바닥) — 전체 라벨을 잠깐 넣고 잰다.
- 함정 2: 라벨 여백을 상수(24)로 두면 힌트 폭 그대로인 버튼도 말줄임된다(Category 여백 18). **힌트 폭 − 글자 폭**으로 잰다.
- ShortCut 페이지 바닥 410 → 296(offscreen) = Color 행(체크박스 + 버튼 둘). 그 아래는 가로 스크롤바.

검증: 오프스크린 PySide6 42항목(`verify_a00240.py`) + 21항목(`verify_a00240_elide.py`). **실기 눈 확인 아직.**

관련: [[wip-a00240-button-colors]], [[wip-a00240-shrink-anim]], [[qtabwidget-min-size-hidden-pages]], [[tsl-selection-order]]
