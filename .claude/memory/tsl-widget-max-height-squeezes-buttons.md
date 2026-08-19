---
name: tsl-widget-max-height-squeezes-buttons
description: "Never setMaximumHeight on the whole shared TSL widget - the list's min height won't shrink so the layout steals the height from the buttons and their text gets clipped; cap list_widget instead, and measure with the theme qss applied"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 064559b4-a50c-475d-865d-675d82033aad
  modified: 2026-08-19T01:20:31.045Z
---

공용 TSL(`Framework/qt/MOD_tsl_qt_v01.py`) **위젯 전체**에 `setMaximumHeight` 를 걸면 안 된다.

TSL 안에는 select 버튼 + 헤더 + 리스트 + `Add`/`Del` 행이 있고 **리스트의 최소 높이는 줄지 않는다**
(`DEFAULT_LIST_MIN_HEIGHT = 100`). 그래서 모자란 높이를 레이아웃이 **버튼에서 빼앗아** 버튼이
sizeHint 보다 낮아지고 **글자가 잘린다.**

**대신 리스트에만 건다:**

```python
JUN_mod_tsl_qt_v01(..., list_min_height=44)   # 리스트 바닥값을 낮추고
tsl.list_widget.setMaximumHeight(70)          # 천장도 리스트에만
```

이러면 버튼은 제 크기를 지키고, 창이 작아질 때 리스트가 대신 줄어든다.
`list_widget` 은 여러 툴이 이미 쓰는 공개 속성이다.

**⚠️ 재는 방법이 결과를 바꾼다 — 테마 qss 를 입힌 상태로 재야 한다.**
헤드리스에서 `MainWindow()` 만 만들면 버튼 sizeHint 가 23px 라 눌려도 티가 안 나
"ALL BUTTONS FIT" 이 나온다. `ThemeManager.load_theme_to_widget(w, "<툴 테마>")` 를 적용하면
qss 패딩이 더해져 30px 가 되고 그제서야 25px 로 눌린 게 보인다. `show()` + `processEvents()` 로
레이아웃을 돌린 뒤 `btn.height()` 와 `btn.sizeHint().height()` 를 **비교**할 것.

발견: A00380_MeshTool Match 탭 v01.06 ([[wip-a00380-match-tab.md]] 참고). 이 repo 에서 TSL 위젯에
`setMaximumHeight` 를 걸던 곳은 거기 하나뿐이었다.

관련: [[framework-tsl-list-limit]], [[wip-tsl-uuid-selection]], [[mayapy-headless-verify]],
[[qapplication-before-maya-standalone]], [[prefer-subtabs-over-stacked-collapsibles]].
