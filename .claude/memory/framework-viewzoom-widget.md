---
name: framework-viewzoom-widget
description: "리스트 · 트리를 키우려면 Framework MOD_viewZoom_qt_v01 한 줄 — 체크박스는 직접 그려야 커지고, 글자는 테마 qss 때문에 뷰 스타일시트 px 로"
metadata:
  node_type: memory
  type: project
  originSessionId: 3b72b09f-82c3-4ab7-acb4-add90da912f7
  modified: 2026-11-04T00:14:40.746Z
---

`Framework/qt/MOD_viewZoom_qt_v01.py` (2026-11-04, A00110 v02.38 Layers 에서 처음). `JUN_mod_viewZoom_qt_v01(view, key=..., default=1.5)` + `controls()`.
배율 하나로 글자 · 헤더 · 행 높이 · 체크박스 · 들여쓰기, Ctrl + 휠, QSettings `JUN/viewZoom` 기억, 텍스트 없는 체크 칸은 칸 전체 클릭(행 선택 안 바뀜).

- ★ **아이템 뷰 체크박스는 스타일이 13px 고정** — qss(`QTreeView::indicator`)·행 높이로 안 커진다 → 델리게이트가 직접 그림.
- ★ **테마 `QWidget { font-size: 12px }` 가 `setFont` 를 덮는다** → 뷰 자신의 스타일시트에 `font-size: Npx`. 기준 100% = **부모 글꼴**
  (뷰 자기 글꼴을 기준으로 하면 적용할 때마다 커지는 되먹임 — 부모 없는 뷰는 처음 값). 테마가 창 생성 뒤에 입혀지므로 **Show 때 재적용**.
- ★ 오프스크린에서 `QFontInfo(font).pixelSize()` 가 **-1** → `font_px_of()`(QFont px, 없으면 pt × DPI/72).
- 시험 `Framework/tests/test_view_zoom.py` PySide6 · PySide2 32/32. 문서 `docs/Framework_MOD_viewZoom_qt.md`.

**Why:** 사용자가 Layers 행 · 체크박스가 작다며 "툴마다 공유 가능한 확대 / 축소 공용 기능" 을 요청.
**How to apply:** 다른 툴에서 리스트가 작다는 요청이 오면 행 높이를 박지 말고 이 위젯을 붙인다. 커스텀 델리게이트 쓰는 뷰엔 못 붙인다. [[offscreen-size-needs-theme]]
