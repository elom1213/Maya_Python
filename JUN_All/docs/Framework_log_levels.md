---
title: Framework 공용 규칙 — log_levels (로그 표식 색)
aliases: [log_levels, 로그 색, WARN 노랑, OK 초록, LEVEL_COLORS]
tags: [framework, qt, widget, maya-python, log, color]
updated: 2026-09-22
---

# `Framework.core.log_levels` — `[WARN]` 은 노랑, `[OK]` 은 초록

`JUN_All/Framework/core/log_levels.py` · 색을 실제로 칠하는 곳은
[`JUN_mod_log_qt_v01`](Framework_MOD_log_qt.md)

로그 한 줄 앞에 붙는 **`[LEVEL]` 표식과 그 색의 대응**을 정하는 파일 하나다.
툴은 아무것도 하지 않는다 — 지금처럼 `self._log("[WARN] Nothing selected.")` 라고 쓰면
그 줄이 노랗게 찍힌다.

```python
self._log("[WARN] No objectSet selected.")     # 노랑
self._log("[OK] Exported 3 set(s).")           # 초록
self._log("[FAIL] head_geo is hidden.")        # 빨강
self._log("Path : C:/scenes/shot_010")         # 표식 없음 → 테마 기본 글자색
```

## 왜 툴마다 칠하지 않고 규칙으로 뺐나

표식은 **이미 저장소 관례**다. 손으로 세어 보면 `.py` 55개 파일에
`[WARN]` 233회 · `[OK]` 151회 · `[ERROR]` 22 · `[INFO]` 20 · `[FAIL]` 11 · `[SKIP]` 7 이 있다.

그런데 색은 관례가 아니었다 — 칠하는 툴이 세 개뿐이었고 **세 개가 서로 다른 값**을 썼다.

| 툴 | 경고색 | 그 외 |
|----|--------|-------|
| `A00300_meshDoctor` | `#ffd166` | `FAIL #ff6b6b` · `INFO #8ab4f8` · `PASS #6bcf8a` |
| `A00410_SecondaryMotion` | `#ffb454` | — |
| `A00430_DemBone` | `#ffb454` | — |

툴마다 칠하면 같은 `[WARN]` 이 툴마다 다른 노랑이 되고, **새 툴은 칠하는 것을 잊는다**.
그래서 대응표를 이 파일에 두고 **공용 로그창이 모든 툴에서 같은 규칙으로** 칠한다.

## 표

| 표식 | 어두운 테마 | 밝은 테마 | 쓰임 |
|------|-------------|-----------|------|
| `[WARN]` `[WARNING]` | `#ffcc33` | `#8a6100` | 경고 — 사용자가 손봐야 하는 것 |
| `[OK]` `[DONE]` `[PASS]` | `#5fd75f` | `#1d7a2e` | 성공 |
| `[ERROR]` `[FAIL]` | `#ff6b6b` | `#b3261e` | 실패 |
| `[INFO]` | `#61afef` | `#1b5e9c` | 안내 |
| `[SKIP]` | `#b0b0b0` | `#6b6b6b` | 건너뜀 |

## ★ 색이 두 벌인 이유 — 테마가 밝은 것도 있다

`Framework/styles/` 의 테마는 두 집안이다. `*_light.qss` 는 배경이 `#eef…` 처럼 밝고,
나머지(`*_dark` `#2b2b2b` · `*_mid` `#4a4a4a` · `dark` · `red`)는 어둡다.

**한 색으로는 양쪽에서 못 읽는다.** 어두운 배경에서 잘 보이는 노랑(`#ffcc33`)은 밝은 배경에서
거의 흰 종이에 쓴 것처럼 되고, 밝은 배경용 진한 노랑(`#8a6100`)은 어두운 배경에서 탁하다.
그래서 색은 **(어두운 배경용, 밝은 배경용) 한 쌍**이고, 어느 쪽을 쓸지는
`ThemeManager.is_dark_theme()` 이 답한다([Framework_theme](Framework_theme.md)).

> **qss 는 `QPalette` 를 바꾸지 않는다.** 그래서 "위젯 배경색을 읽어서 판단" 은 통하지 않는다
> (팔레트는 테마와 무관한 기본값을 그대로 돌려준다). 대신 `ThemeManager` 가 **마지막으로 불러온
> 테마 이름**을 기억하고, 판정은 이름의 `_light` 하나로 한다.

## 규칙 (함수)

| 함수 | 하는 일 |
|------|---------|
| `find_level(text)` | 줄에서 **처음 나오는 등록된 표식**의 이름. 없으면 `None` |
| `color(level, dark=True)` | 그 표식의 색 |
| `to_html(text, dark=True)` | 표식이 있으면 **escape 한 색깔 HTML 한 줄**, 없으면 `None` |
| `looks_like_html(text)` | `<` 가 있으면 True — 툴이 손으로 쓴 HTML 로 본다 |
| `register(level, dark, light)` | 표식을 더하거나 색을 갈아 끼운다 |
| `levels()` | 등록된 표식 이름들 |

- **표식의 위치는 따지지 않는다.** 줄 앞이 관례지만(`[WARN] ...`) 들여쓴 줄(`  - [OK] head_ctl`)도
  있어서 줄 안에 있으면 칠한다.
- **등록되지 않은 대괄호 낱말은 지나친다** — `[Set_v001]`, `[1/3]`(글자가 아니라 숫자),
  `[2026-09-22]` 는 표식이 아니다. 정규식이 `[A-Za-z]+` 만 받는 이유다.
- 이 모듈은 **Qt · maya 를 import 하지 않는다.** 순수 문자열 규칙이라 헤드리스로 그대로 테스트된다.

## 끄기 · 툴 표식 추가

```python
# 이 툴만 색 없이
self.log_view = JUN_mod_log_qt_v01(..., colorize_levels=False)
self.log_view.set_colorize_levels(True)          # 도중에 켜기

# 이 툴만의 표식
from Framework.core import log_levels
log_levels.register("TODO", "#c678dd", "#6b3fa0")
self._log("[TODO] rename the export sets")
```

## 손으로 색을 칠하는 툴은 그대로 둔다

`A00300_meshDoctor` · `A00410_SecondaryMotion` · `A00430_DemBone` 은 자기 손으로
`append('<span style="color:…">…')` 를 넣는다. 그 문장은 **건드리지 않는다** —
`<` 가 있으면 툴의 HTML 로 보고 통과시킨다. escape 하면 태그가 글자로 보이고, 덧칠하면 툴이 고른
색을 덮기 때문이다. 세 툴을 공용 표로 옮기는 것은 **따로 할 일**로 남겼다(지금은 두 규칙이 한
창에서 공존한다 — 그쪽 색이 이기고, 표식만 있는 평문 줄은 공용 표를 탄다).

## 검증 (mayapy 2024 + 오프스크린 Qt)

`[WARN]`/`[OK]`/`[ERROR]`/`[SKIP]` 각 색 · 표식 없는 줄이 **앞 줄 색을 물려받지 않는지**(핵심) ·
들여쓴 줄 · `<node>` 가 글자로 남는지 · `Copy`/`toPlainText()` 가 평문인지 · `append()` 경로 ·
툴 HTML 통과 · `colorize_levels=False` · 밝은 테마 색 · Expand 창 안 · 대표 툴 5개 +
손색칠 툴 3개 회귀 — **65항목 통과**(규칙·위젯 36 · A00480 10 · 대표 툴 19).
