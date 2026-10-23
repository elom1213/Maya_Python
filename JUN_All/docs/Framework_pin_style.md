---
title: Framework pin_style — Pin 버튼 켜짐 색
aliases: [pin_style, apply_pin_style, Pinned 색]
tags: [maya-python, framework, qt]
updated: 2026-10-23
---

# Framework `qt/pin_style.py` — Pin(Always on Top) 버튼의 켜짐 색

여러 툴이 같은 모양의 체크형 **`Pin`** 버튼(켜면 창이 다른 창 위에 고정, 라벨 `Pinned`)을 갖는다. 테마 qss 에는
`QPushButton:checked` 규칙이 없어 켜져도 색이 그대로였다. 이 모듈의 qss 를 버튼에 붙이면 **켜진 동안 연한 빨강**이 된다.

| 상태 | 색 |
|------|----|
| 켜짐(`:checked`) | 바탕 `#f2a0a0` · 글자 `#4a1414` · 테두리 `#dd8888` |
| 켜짐 + hover | `#f6b4b4` |
| 켜짐 + pressed | `#e68c8c` |
| 꺼짐 | 테마 그대로 |

```python
from Framework.qt.pin_style import apply_pin_style

self.pin_button = QPushButton("Pin")
self.pin_button.setCheckable(True)
apply_pin_style(self.pin_button)          # 켜진 동안 연한 빨강
```

- **`:checked` 의 색만 적는다.** padding · border-radius 를 적지 않으므로 버튼 크기와 평소 모양은 테마(앱/창 qss) 그대로다
  (위젯 qss 가 padding 을 덮으면 버튼 높이가 바뀐다 — [A00240 색 버튼](A00240_PathTool.md)에서 겪은 것).
- 버튼 자신의 qss 는 테마 위에 겹쳐지므로 standalone(앱 qss, `load_theme_dev`) · in-Maya(창 qss, `load_theme_to_widget`) 둘 다 같다.
- 사용처: `A00240_PathTool` v01.26 · `A00220_BackupTool` v01.21 · `A00370_ToolLauncher` v01.13.
  (`A00210_FileManager` v01.37 에도 같은 Pin 이 있다 — 아직 적용 안 함.)
- 검증(2026-10-23, offscreen PySide6): 세 테마(yellow_mid · green_mid)에서 버튼을 그려 가운데 픽셀을 읽어 꺼짐 = 테마 색,
  켜짐 = `#f2a0a0` 확인. 마야 · 실기 확인 아직.
