---
title: 공용 슬라이더 색 위젯 (JUN_mod_sliderStyle_qt) 사용법
aliases: [MOD_sliderStyle_qt, JUN_mod_sliderStyle_qt, 슬라이더 스타일, slider style, 슬라이더가 안 보임]
tags: [maya-python, framework, widget, slider, theme, qss]
updated: 2026-11-19
---

# 공용 슬라이더 색 위젯 `JUN_mod_sliderStyle_qt_v01`

- **모듈**: `JUN_All/Framework/qt/MOD_sliderStyle_qt_v01.py`
- **시험**: `Framework/tests/test_slider_style.py` (오프스크린, PySide6 · mayapy 둘 다)
- **첫 적용**: `A00275_skinTool_V01` v01.45 — Weights > Flood

---

## 1. 왜 필요한가

`Framework/styles/*.qss` 테마 어디에도 `QSlider` 규칙이 없다. 그래서 어두운 테마(배경 `#2b2b2b`)에서는 기본 홈(groove)이
배경에 묻혀 **손잡이(세로 막대)만 보인다** — 슬라이더의 끝도, 지금 값이 어디쯤인지도 안 보인다.

지금까지는 툴마다 비슷한 슬라이더 스타일을 복사해 썼다(A00110 · A00290 · A00330 · A00380 · A00410 · A00450 · A00620).
이 위젯이 그 공용판이다. **새로 만드는 슬라이더는 이것을 쓴다.**

---

## 2. 쓰는 법 — 한 줄

```python
from Framework.qt.MOD_sliderStyle_qt_v01 import JUN_mod_sliderStyle_qt_v01

class MyTab(QWidget):
    def __init__(self, ...):
        ...
        self._build_ui()
        self.slider_style = JUN_mod_sliderStyle_qt_v01(self)   # 이 위젯 아래 QSlider 전부
```

- **보일 때마다(Show)** 그 아래 `QSlider` 를 **지금 테마 색**으로 칠한다. 툴의 `launch.py` 는 창을 만든 **뒤** 테마를 입히므로
  만들 때가 아니라 보일 때 칠해야 테마를 읽을 수 있다. 테마가 바뀌면 다음에 보일 때 다시 칠한다.
- 참조를 붙잡아 둘 필요는 없지만(부모가 root), `self.slider_style` 처럼 들고 있으면 `apply()` 를 직접 부를 수 있다.

| 인자 | 기본 | 뜻 |
|------|------|----|
| `root` | — | 슬라이더들을 담은 위젯(탭 · 창). 이 위젯의 Show 를 듣는다 |
| `fill` | `True` | 손잡이 왼쪽(값이 찬 쪽)을 강조색으로 채운다. **중앙이 0 인 양방향 슬라이더**는 0 에서도 반이 찬 것처럼 보이므로 `False` |
| `theme` | `None` | `None` = `ThemeManager.current_theme()`. 테마를 고정하고 싶을 때만 이름을 준다 |

- **자기 스타일시트를 가진 슬라이더는 건드리지 않는다** — 툴이 일부러 칠한 것은 그대로 둔다.
- 함수만: `slider_style(theme_name=None, fill=True)` → 스타일시트 문자열. `theme_colors(theme_name)` → `{"accent", "field", "window"}`.

---

## 3. 색은 어디서 오나

테마 qss 에서 읽는다(25개 테마 모두 같은 구조).

| 색 | 읽는 곳 | 쓰는 곳 |
|----|---------|---------|
| accent | `QPushButton { border: 1px solid ... }` | 홈 테두리 · 찬 쪽 · (어두운 테마) 손잡이 테두리 · (밝은 테마) 손잡이 |
| field | `QLineEdit, ... { background-color }` | 홈 바탕(강조색을 조금 섞는다) |
| window | `QWidget { background-color }` | 비활성 회색 계산 |

- 어두운 테마: 밝은 손잡이(`#e8e8e8`) + 강조색 테두리. 밝은 테마(`*_light`): 강조색 손잡이 + 진한 테두리.
- 버튼 테두리가 없는 무채색 `dark` 테마는 버튼 배경을 밝힌 회색을 강조색으로 쓴다(초록 대체색이 섞이지 않게).
- 가로 · 세로, 마우스 올림, 비활성 상태를 모두 칠한다.

---

## 4. 검증

`Framework/tests/test_slider_style.py` 12 항목 (PySide6 · mayapy 2024 둘 다 통과):
테마 25개의 색이 각자 qss 에서 온다 · 가로/세로/비활성 규칙 · `fill=False` · 밝은 테마 손잡이 · 보이기 전엔 안 칠함 → 보이면 칠함 ·
남이 칠한 슬라이더는 그대로 · **실제 그려진 픽셀**: 가운데 줄의 대부분이 배경과 구별되고 찬 쪽이 강조색 · 테마를 바꾸면 다시 칠함 · 비활성도 홈이 보임.

---

## 5. 적용 현황

| 툴 | 위치 | 비고 |
|----|------|------|
| `A00275_skinTool_V01` | Weights > Flood (v01.45) | 첫 적용 |
| `A00275_skinTool_V01` | Weights > Move · Smooth (v01.47) | |

기존 툴들의 자체 슬라이더 스타일(A00290 · A00380 등)은 그대로 둔다 — 옮길 때는 한 툴씩 화면을 비교하고 바꾼다.
