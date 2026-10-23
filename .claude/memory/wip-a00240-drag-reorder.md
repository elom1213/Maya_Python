---
name: wip-a00240-drag-reorder
description: A00240_PathTool v01.28 — Path 버튼 드래그 정렬은 QDrag 아닌 _PathButton 마우스 이벤트(press/move/release)로, (cat_index, btn_index) 키, 색칠 모드는 끔 · v01.29 탭 QScrollArea 로 창 자유 크기
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

검증: 오프스크린 PySide6 42항목(스크래치 `verify_a00240.py`). **실기 눈 확인 아직.**

관련: [[wip-a00240-button-colors]], [[wip-a00240-shrink-anim]], [[qtabwidget-min-size-hidden-pages]], [[tsl-selection-order]]
