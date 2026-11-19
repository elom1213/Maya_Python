# -*- coding: utf-8 -*-
"""
JUN_mod_sliderStyle_qt_v01 - 슬라이더를 테마 색으로 **잘 보이게** 칠하는 공용 위젯 (2026-11-19~).

왜 필요한가
-----------
`Framework/styles/*.qss` 테마 어디에도 `QSlider` 규칙이 없다. 그래서 어두운 테마(배경 `#2b2b2b`)에서는 마야 · Qt 의
기본 홈(groove)이 배경에 묻혀 **손잡이(세로 막대)만 보인다** — 어디가 끝이고 지금 얼마인지 알 수 없다.
지금까지는 툴마다 비슷한 슬라이더 스타일을 복사해 썼다(A00290 · A00380 · A00410 · A00450 …). 이 모듈이 그 공용판이다.

쓰는 법 (한 줄)
--------------
    from Framework.qt.MOD_sliderStyle_qt_v01 import JUN_mod_sliderStyle_qt_v01
    self.slider_style = JUN_mod_sliderStyle_qt_v01(self)      # self = 슬라이더들을 담은 위젯(탭 · 창)

- 위젯이 **화면에 보일 때마다**(Show) 그 아래 `QSlider` 를 **지금 테마 색**으로 칠한다. 툴의 `launch.py` 는 창을 만든 **뒤**
  테마를 입히므로, 만들 때가 아니라 보일 때 칠해야 테마를 읽을 수 있다.
- 색은 테마 qss 에서 읽는다: 강조색 = `QPushButton` 테두리, 홈 바탕 = 입력칸(`QLineEdit …`) 배경, 창 배경 = `QWidget` 배경.
  밝은 테마(`*_light`)는 손잡이를 강조색으로, 어두운 테마는 밝은 손잡이 + 강조색 테두리로 칠한다.
- **이미 자기 스타일시트를 가진 슬라이더는 건드리지 않는다**(툴이 일부러 칠한 것, 예: 중앙 0 인 양방향 슬라이더).
- `fill=True`(기본) 면 손잡이 왼쪽(값이 찬 쪽)을 강조색으로 채운다. 중앙이 0 인 양방향 슬라이더처럼 채움이 오해를 주는
  리스트에서는 `fill=False` (홈만 테두리로 그린다 - A00380 Peak 와 같은 이유).
- 가로 · 세로 슬라이더 모두, 비활성(회색) 상태도 따로 칠한다.

함수만 쓰고 싶으면 `slider_style(theme_name, fill)` 이 스타일시트 문자열을 돌려준다.
"""

import os
import re

from Framework.qt.qt import *


#: 테마 qss 를 못 읽을 때 쓸 색 (green_dark 와 같다)
FALLBACK_COLORS = {"accent": "#6f9e80", "field": "#353835", "window": "#2b2b2b"}

#: 이 위젯이 칠한 슬라이더 표식 (dynamic property) - 다시 칠할 때 남이 칠한 것과 구별한다
STYLED_PROPERTY = "junSliderStyle"

_COLOR_CACHE = {}


def _styles_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles")


def _block_value(qss, selector_pattern, prop):
    """`selector { ... prop: #rrggbb ... }` 에서 첫 블록의 색. 없으면 None."""
    match = re.search(selector_pattern + r"\s*\{([^}]*)\}", qss)
    if not match:
        return None
    found = re.search(r"(?<![-\w])" + re.escape(prop) + r"\s*:\s*[^;#]*?(#[0-9a-fA-F]{6})", match.group(1))
    return found.group(1).lower() if found else None


def theme_colors(theme_name=None):
    """테마 qss 에서 `{"accent", "field", "window"}` 색. 못 읽으면 FALLBACK_COLORS."""
    if not theme_name:
        try:
            from Framework.themes.theme_manager import ThemeManager
            theme_name = ThemeManager.current_theme()
        except Exception:
            theme_name = None
    theme_name = theme_name or "green_dark"
    if theme_name in _COLOR_CACHE:
        return dict(_COLOR_CACHE[theme_name])
    colors = dict(FALLBACK_COLORS)
    try:
        with open(os.path.join(_styles_dir(), theme_name + ".qss"), "r", encoding="utf-8") as handle:
            qss = handle.read()
        accent = _block_value(qss, r"(?m)^QPushButton", "border")
        field = _block_value(qss, r"(?m)^QLineEdit[^{]*", "background-color")
        window = _block_value(qss, r"(?m)^QWidget", "background-color")
        # 무채색 `dark` 처럼 버튼 테두리 · 입력칸 규칙이 없는 테마 : 버튼 배경을 밝혀 강조색, 창 배경을 살짝 밝혀 홈 바탕.
        # (대체 초록을 섞으면 회색 테마에 초록 슬라이더가 뜬다)
        if not accent:
            button = _block_value(qss, r"(?m)^QPushButton", "background-color")
            if button:
                accent = _mix(button, "#ffffff", 0.4)
        if not field and window:
            field = _mix(window, "#ffffff", 0.06)
        colors.update({k: v for k, v in (("accent", accent), ("field", field), ("window", window)) if v})
    except Exception:
        pass
    _COLOR_CACHE[theme_name] = dict(colors)
    return colors


def _is_dark(theme_name):
    try:
        from Framework.themes.theme_manager import ThemeManager
        return ThemeManager.is_dark_theme(theme_name)
    except Exception:
        return not str(theme_name or "").lower().endswith("_light")


def _mix(color_a, color_b, t):
    """두 색을 t(0~1) 로 섞은 #rrggbb."""
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("{0:02x}".format(int(round(x + (y - x) * t))) for x, y in zip(a, b))


def slider_style(theme_name=None, fill=True):
    """테마 색으로 칠한 QSlider 스타일시트 (가로 · 세로 · 비활성)."""
    if not theme_name:
        try:
            from Framework.themes.theme_manager import ThemeManager
            theme_name = ThemeManager.current_theme()
        except Exception:
            theme_name = None
    c = theme_colors(theme_name)
    dark = _is_dark(theme_name)
    accent, field, window = c["accent"], c["field"], c["window"]
    groove = _mix(field, accent, 0.18) if dark else _mix(field, accent, 0.25)
    handle = "#e8e8e8" if dark else accent
    handle_border = accent if dark else _mix(accent, "#000000", 0.35)
    handle_hover = "#ffffff" if dark else _mix(accent, "#ffffff", 0.25)
    filled = accent if fill else groove
    off_groove = _mix(window, "#808080", 0.15)
    off_line = _mix(window, "#808080", 0.35)
    off_handle = _mix(window, "#808080", 0.55)

    parts = []
    for o, size, across, handle_margin in (("horizontal", "height", "width", "margin: -5px 0;"),
                                            ("vertical", "width", "height", "margin: 0 -5px;")):
        sub, add = ("sub-page", "add-page") if o == "horizontal" else ("add-page", "sub-page")
        parts.append(
            "QSlider:{o} {{ min-{size}: 20px; }}"
            "QSlider::groove:{o} {{ {size}: 6px; background: {groove}; border: 1px solid {accent}; border-radius: 3px; }}"
            "QSlider::{sub}:{o} {{ background: {filled}; border: 1px solid {accent}; border-radius: 3px; }}"
            "QSlider::{add}:{o} {{ background: {groove}; border: 1px solid {accent}; border-radius: 3px; }}"
            "QSlider::handle:{o} {{ {across}: 12px; {handle_margin} background: {handle};"
            " border: 1px solid {handle_border}; border-radius: 3px; }}"
            "QSlider::handle:{o}:hover {{ background: {handle_hover}; }}"
            "QSlider::groove:{o}:disabled, QSlider::{sub}:{o}:disabled, QSlider::{add}:{o}:disabled"
            " {{ background: {off_groove}; border: 1px solid {off_line}; }}"
            "QSlider::handle:{o}:disabled {{ background: {off_handle}; border: 1px solid {off_line}; }}".format(
                o=o, size=size, across=across, handle_margin=handle_margin, sub=sub, add=add, groove=groove,
                accent=accent, filled=filled, handle=handle, handle_border=handle_border, handle_hover=handle_hover,
                off_groove=off_groove, off_line=off_line, off_handle=off_handle))
    return "".join(parts)


class JUN_mod_sliderStyle_qt_v01(QObject):
    """root 아래 QSlider 들을 **보일 때마다** 지금 테마 색으로 칠한다 (모듈 독스트링)."""

    def __init__(self, root, fill=True, theme=None):
        super().__init__(root)
        self.root = root
        self.fill = fill
        self.theme = theme              # None = ThemeManager 의 지금 테마
        root.installEventFilter(self)
        if root.isVisible():
            self.apply()

    def eventFilter(self, obj, event):
        if obj is self.root and event.type() == QEvent.Show:
            self.apply()
        return False

    def sliders(self):
        """칠할 슬라이더 - 자기 스타일시트가 없거나 이 위젯이 칠한 것만."""
        out = []
        for slider in self.root.findChildren(QSlider):
            if slider.styleSheet() and not slider.property(STYLED_PROPERTY):
                continue                # 툴이 일부러 칠한 슬라이더
            out.append(slider)
        return out

    def apply(self):
        """지금 테마 색으로 칠한다. 칠한 수를 돌려준다."""
        style = slider_style(self.theme, self.fill)
        sliders = self.sliders()
        for slider in sliders:
            if slider.styleSheet() != style:
                slider.setStyleSheet(style)
            slider.setProperty(STYLED_PROPERTY, True)
        return len(sliders)
