---
name: bash-heredoc-backslash-collapse
description: "이 PC 의 Bash 툴에서 python - <<'EOF' heredoc 안의 \ 가 \ 로 줄어든다 - 문자열에 \n 을 넣는 패치는 Write 로 스크립트 파일을 만들어 실행"
metadata:
  type: feedback
---

Bash 툴에서 `python - <<'EOF' ... EOF`(따옴표 heredoc 이어도) 안에 쓴 `\n` 이 `\n` 으로 줄어들어, 파이썬 소스 문자열 안에
**진짜 줄바꿈**이 박혔다(2026-11-25 두 번: A00275 툴팁, A00480 툴팁 → SyntaxError). `print(repr('\n'))` 가 `'\n'` 로 나온다.

**Why:** 패치가 조용히 깨지고 mayapy 시험에서야 SyntaxError 로 드러난다.

**How to apply:** `\` 가 들어가는 코드 패치는 Write 툴로 스크래치패드에 `.py` 를 만들고 `python <파일>` 로 돌리거나 Edit 툴을 쓴다.
백슬래시 없는 블록(cat >> 로 덧붙이기 등)은 heredoc 도 괜찮다. 커밋 메시지 heredoc 규칙은 전역 CLAUDE.md 4장.
