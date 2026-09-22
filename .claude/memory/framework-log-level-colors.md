---
name: framework-log-level-colors
description: "로그 줄의 [WARN]/[OK] 색은 Framework.core.log_levels 공용 규칙 — 색 한 쌍(밝은/어두운 테마) · QTextEdit 는 앞 줄 색을 물려받는다"
metadata:
  node_type: memory
  type: project
---

로그 한 줄의 `[LEVEL]` 표식 색은 **툴이 아니라 `Framework/core/log_levels.py`** 가 정한다
(2026-09-22, 사용자 요청 "A00480 로그창의 `[WARN]` 노랑 · `[OK]` 초록 — 모든 툴 규칙으로
만들 만하면 그렇게"). 칠하는 곳은 공용 로그창 [[framework-log-widget]]
(`JUN_mod_log_qt_v01`, `colorize_levels=True` 기본). 문서 `docs/Framework_log_levels.md`.

**Why:** 표식은 이미 관례였지만(`.py` 55개 파일, `[WARN]` 233 · `[OK]` 151 · `[ERROR]` 22 ·
`[INFO]` 20 · `[FAIL]` 11 · `[SKIP]` 7) **색은 아니었다** — 칠하는 툴이 셋(A00300 `#ffd166` ·
A00410/A00430 `#ffb454`)이고 값이 서로 달랐다. 규칙으로 두면 47툴이 같은 색을 쓰고 새 툴은
아무것도 안 해도 색이 붙는다.

**How to apply:**
- 툴은 그냥 `self._log("[WARN] ...")`. 새 표식이 필요하면 `log_levels.register("TODO", dark, light)`.
- ★ **색은 (어두운 배경용, 밝은 배경용) 한 쌍**이다. `Framework/styles/*_light.qss` 는 배경이
  `#eef…` 라서 어두운 배경용 노랑(`#ffcc33`)이 거의 안 보인다.
- ★ **qss 는 `QPalette` 를 바꾸지 않는다** — 위젯 배경색을 읽어 밝기를 재는 방법은 통하지 않는다.
  그래서 `ThemeManager` 가 마지막으로 불러온 테마 이름을 기억한다(`current_theme()` ·
  `is_dark_theme()`, 판정은 이름의 `_light` 하나). 다른 "배경에 맞춰야 하는 값" 도 이걸 쓴다.
- ★ **`QTextEdit` 의 커서는 글자 포맷을 이어 쓴다** — 색깔 줄 뒤의 평문 줄이 그 색으로 찍힌다
  (첫 `[WARN]` 뒤 전부 노랑). 평문을 넣기 전과 색깔 줄을 넣은 뒤 `QTextCharFormat()` 을 다시 건다.
- 색깔 줄은 HTML 이므로 **`white-space: pre-wrap`** 을 줘야 들여쓰기(`  - [OK] ...`)가 안 줄어든다.
  `Copy` / `toPlainText()` 는 평문 그대로여야 한다(테스트로 고정).
- `append()` 에 들어온 문장에 `<` 가 있으면 **툴이 쓴 HTML** 로 보고 통과시킨다 — A00300 ·
  A00410 · A00430 은 자기 색을 그대로 유지한다(공용 표로 옮기는 것은 아직 안 한 일).
- 등록 안 된 대괄호는 지나친다(`[Set_v001]` · `[1/3]`). 표식 대소문자는 안 가린다(`[Info]` 도 파랑).
