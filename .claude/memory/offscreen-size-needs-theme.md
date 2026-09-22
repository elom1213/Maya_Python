---
name: offscreen-size-needs-theme
description: "오프스크린 Qt 로 창 크기를 잴 때는 테마 qss 를 입히고 재라 — 그리고 테마를 입혀도 오프스크린 px 은 마야보다 크므로 잰 최소 폭을 창 크기로 박지 말 것"
metadata:
  node_type: memory
  type: reference
---

**`MainWindow()` 만 만들어 재면 테마가 안 입은 상태다.** 툴은 `launch.py` 에서
`ThemeManager.load_theme_to_widget(window, "<theme>")` 로 qss 를 입고 뜨는데, qss 가
**`font-size: 12px`** 를 주므로 **위젯 최소 폭이 확 줄어든다.**

2026-09-16 `A00290_BSTool_V02` 실측 — 같은 창을 테마 없이/있게 잰 값:

| 페이지 | 테마 없음 | green_dark |
|---|---:|---:|
| Mix Targets | 1092 | **809** |
| Naming | 792 | **641** |
| Shape Editor | 579 | **444** |

이걸 빼먹고 창 기본 크기를 **1400 x 1158** 로 정했다가, 실제로는 **620 x 1000** 이면 되는 것을
두 배 넘게 키워 놨다(사용자가 "가로가 너무 길다" 고 알려 줬다).

```python
from Framework.themes.theme_manager import ThemeManager
win = MainWindow()
ThemeManager.load_theme_to_widget(win, "green_dark")   # ★ 재기 전에
win.show()
```

테마 이름은 그 툴의 `launch.py` 가 쓰는 것을 그대로 쓴다(툴마다 다르다).

**곁들여 기억할 것 — 폭을 좁히려면 "한 줄에 나란히 둔 것" 을 찾는다.** 버튼·라디오·라벨을 가로로
늘어놓으면 **그 줄의 최소 폭이 그대로 창의 최소 폭**이 되고, **좌우 `QSplitter` 안에 있으면 두 배**로
올라온다. 자리만 세로로 내리면 기능을 하나도 안 바꾸고 최소 폭이 버튼 하나 폭까지 내려간다.

**그리고 세로는 반대로 움직인다** — 창을 좁히면 글이 접혀 **필요한 세로가 늘어난다.** 가로와 세로를
동시에 "스크롤 0" 으로 맞추려다 화면보다 큰 창이 되기 쉬우므로, **가로를 먼저 맞추고 세로는
`QScrollArea` 에 맡기는** 편이 낫다.

## ★ 테마를 입혀도 오프스크린 px ≠ 마야 px (2026-09-22)

테마를 입히고 재도 **오프스크린에서 잰 최소 폭은 마야에서 보이는 것보다 크다.**
폰트가 다르기 때문이다(offscreen 플랫폼의 기본 폰트가 마야 UI 폰트보다 넓다).

**그래서 잰 최소 폭을 창 크기로 그대로 박으면 안 된다.** A00380_MeshTool 을
"A00400_CurveTool 과 같은 가로" 로 맞추라는 요청에, 오프스크린에서 잰 A00400 의 최소
**1176 을 그대로 박았다가 "너무 넓다" 는 말을 또 들었다**(위 A00290 사례와 같은 실수).
오프스크린에서 A00400 은 최소 1176 이라 나오지만 마야에서는 훨씬 좁게 열린다.

**어떻게 할 것인가**

- `resize()` 에는 **작은 값**을 두고 실제 폭은 레이아웃 최소가 정하게 맡긴다.
  "다른 툴과 같은 가로" 는 그 툴의 **`resize()` 값을 그대로** 쓰는 것이 가장 가깝다
  (A00400 은 `resize(360, 620)` 이다 — 코드의 숫자와 화면의 숫자가 다르다).
- 오프스크린 수치는 **절대 px 이 아니라 비교용**으로만 쓴다
  (같은 조건에서 A < B 인지 정도는 믿을 수 있다).
- 정확한 px 이 필요하면 **마야에서 사용자가 읽어 줘야 한다** —
  `cmds.window` 가 아니라 PySide 창이므로 `win.width()` 를 스크립트 에디터에서 찍는다.

관련: [[wip-a00290-v02-tab-reorg]], [[tsl-widget-max-height-squeezes-buttons]], [[mayapy-headless-verify]]
