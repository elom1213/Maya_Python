# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-22
# Framework.core.log_levels - 로그 한 줄의 `[LEVEL]` 표식 -> 색. 저장소 전체 공용 규칙.
#
# 저장소의 로그 문장은 이미 같은 관례를 쓰고 있다(55개 파일, `[WARN]` 233회 · `[OK]` 151회 ·
# `[ERROR]` 22 · `[INFO]` 20 · `[FAIL]` 11 · `[SKIP]` 7). 색을 툴마다 각자 칠하면 같은
# `[WARN]` 이 툴마다 다른 노랑이 되고, 새 툴은 칠하는 것을 잊는다. 그래서 **표식과 색의 대응을
# 이 파일 하나에** 두고, 공용 로그창(`JUN_mod_log_qt_v01`)이 쓰도록 했다 - 툴은 지금처럼
# `self._log("[WARN] ...")` 만 하면 색이 붙는다.
#
# ★ 테마가 밝은 것과 어두운 것 둘 다 있다 (`Framework/styles/*_light.qss` 는 배경이 `#eef…`,
#   나머지는 `#2b2b2b` / `#4a4a4a`). **한 색으로는 양쪽에서 읽히지 않는다** - 어두운 배경에서
#   잘 보이는 노랑(`#ffcc33`)은 밝은 배경에서 거의 안 보이고, 밝은 배경용 진한 노랑
#   (`#8a6100`)은 어두운 배경에서 탁하다. 그래서 색은 **(어두운 배경용, 밝은 배경용) 한 쌍**으로
#   갖고, 어느 쪽인지는 `ThemeManager.is_dark_theme()` 이 답한다.
#
# 이 모듈은 Qt · maya 를 import 하지 않는다 - 순수 문자열 규칙이라 헤드리스로 그대로 테스트된다.

import re

#: `[LEVEL]` -> (어두운 배경용 색, 밝은 배경용 색).
#: 키는 대문자 표식 그대로다. 같은 뜻의 별칭(`WARNING`, `DONE`)도 등록해 둔다.
LEVEL_COLORS = {
    # 요청의 두 가지 - 경고는 노랑, 성공은 초록.
    "WARN":    ("#ffcc33", "#8a6100"),
    "WARNING": ("#ffcc33", "#8a6100"),
    "OK":      ("#5fd75f", "#1d7a2e"),
    "DONE":    ("#5fd75f", "#1d7a2e"),
    "PASS":    ("#5fd75f", "#1d7a2e"),
    # 같은 관례로 이미 쓰이고 있는 나머지. 실패는 빨강, 안내는 파랑, 건너뜀은 회색.
    "ERROR":   ("#ff6b6b", "#b3261e"),
    "FAIL":    ("#ff6b6b", "#b3261e"),
    "INFO":    ("#61afef", "#1b5e9c"),
    "SKIP":    ("#b0b0b0", "#6b6b6b"),
}

#: 한 줄에서 `[WORD]` 를 찾는다. 대괄호 안이 글자뿐인 것만 본다 -
#: `[1/3]` `[2026-09-22]` 같은 것은 표식이 아니다.
_TAG_RE = re.compile(r"\[([A-Za-z]+)\]")


def register(level, dark_color, light_color):
    """표식을 더한다(이미 있으면 색을 갈아 끼운다). 툴이 자기 표식을 쓰고 싶을 때.

    level 은 대괄호 없이 준다 - `register("TODO", "#c678dd", "#6b3fa0")`.
    """
    LEVEL_COLORS[str(level).upper()] = (dark_color, light_color)


def levels():
    """등록된 표식 이름들(정렬)."""
    return sorted(LEVEL_COLORS)


def color(level, dark=True):
    """그 표식의 색. 모르는 표식이면 None."""
    pair = LEVEL_COLORS.get(str(level).upper())
    if not pair:
        return None
    return pair[0] if dark else pair[1]


def find_level(text):
    """줄에서 **처음 나오는 등록된 표식**의 이름(대문자). 없으면 None.

    표식이 줄 앞에 오는 것이 저장소 관례지만(`[WARN] Select ...`), 들여쓴 줄
    (`  - [OK] ...`)도 있어서 위치를 따지지 않는다. 등록되지 않은 대괄호 낱말
    (`[Set_v001]` 등)은 지나친다.
    """
    if not text:
        return None
    for match in _TAG_RE.finditer(str(text)):
        name = match.group(1).upper()
        if name in LEVEL_COLORS:
            return name
    return None


def escape(text):
    """HTML 특수문자만 막는다(`<node>` 가 태그로 먹히지 않게)."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def looks_like_html(text):
    """이미 HTML 로 쓰인 문장인가. `<` 가 있으면 그렇게 본다.

    `A00300_meshDoctor` · `A00410_SecondaryMotion` · `A00430_DemBone` 처럼 자기 손으로
    `<span style="color:…">` 를 넣는 툴이 있다. 그런 문장은 **건드리지 않는다** -
    escape 하면 태그가 글자로 보이고, 덧칠하면 툴이 고른 색을 덮는다.
    """
    return "<" in str(text or "")


def to_html(text, dark=True):
    """표식이 있으면 **그 색으로 칠한 HTML 한 줄**을, 없으면 None.

    - 글자는 escape 하므로 `<`, `&` 가 들어 있어도 그대로 보인다.
    - `white-space: pre-wrap` 을 준다 - 그러지 않으면 QTextDocument 가 **들여쓰기 공백을
      하나로 줄여** 색깔 줄만 왼쪽으로 당겨진다(평문 줄과 눈에 띄게 어긋난다).
    """
    level = find_level(text)
    if not level:
        return None
    return '<span style="color:{0}; white-space: pre-wrap;">{1}</span>'.format(
        color(level, dark), escape(text))
