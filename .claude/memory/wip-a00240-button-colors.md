---
name: wip-a00240-button-colors
description: A00240 PathTool v01.15 (2026-10-02) - A00340 버튼 색 기능 이식. 색 버튼 qss 는 테마와 같은 padding 8px · radius 4px 여야 높이가 맞는다 (A00340 원본 4px · 3px 는 낮다)
metadata:
  node_type: memory
  type: project
  originSessionId: 61b22058-2a64-4823-9a3c-e5227d4bb12f
  modified: 2026-10-02T01:05:16.431Z
---

`A00240_PathTool/app/ui/shortcut_tab.py` 에 [[wip-a00340-button-colors]] 를 그대로 옮겼다:
우클릭 `Set Color...` / `Reset Color`, `Color` 그룹 `Color Select` 모드(체크 → `Apply...` / `Clear`,
켜진 동안 클릭은 경로를 안 연다), 버튼 dict `"color"`, Apply 직전 `_sync_checked_from_widgets`.
로그창이 없어 성공 로그는 뺐다.

- **색 버튼 qss 여백은 테마와 같게** — `Framework/styles/*.qss` 의 QPushButton 은 전부 `padding: 8px; border-radius: 4px`.
  위젯 qss 의 padding 이 테마 값을 덮으므로 A00340 원본(4px · 3px)을 쓰면 색 버튼만 낮아진다.
  A00340 자체는 아직 그 상태(사용자에게 알렸다, 고치지 않음).
- 라벨을 `Apply...` / `Clear` 로 줄였다 — 원본 라벨이면 Color 그룹이 Profile 그룹보다 넓어 창 최소 폭이 늘었다.
- 테스트는 `prefs.PREFS_DIR/PROFILES_DIR/ACTIVE_PATH` 를 임시 폴더로 바꿔서 — `data/profiles/*.json` 은 git 추적 중인 실데이터다.

**Why:** 사용자 요청(2026-10-02) — "A00340 과 똑같이 버튼 색 지정, 기능을 그대로 옮겨도 된다".
**How to apply:** 다른 툴에 버튼 색을 또 옮기면 qss 여백을 그 툴의 테마 값과 맞출 것. 관련 [[wip-a00240-shrink-anim]].
