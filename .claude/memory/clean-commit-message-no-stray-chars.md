---
name: clean-commit-message-no-stray-chars
description: "Commit messages must not start with stray chars like a leading '@'; verify + fix the message before committing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 91ab0dea-4b6f-4134-a5cd-3d3ccc44c43a
---

커밋 전에 커밋 메시지에 불필요한 글자(맨 앞 `@` 등)가 섞이지 않았는지 확인하고, 있으면 고친 뒤
커밋할 것. 사용자가 최근 서밋 3개가 전부 `@` 로 시작한다고 지적했다.

**Why:** 메시지 첫 줄(subject)에 붙은 `@` 는 오타/문법 유출이라 로그를 지저분하게 만든다. 원인은
**Bash 툴에서 PowerShell 히어스트링 문법 `@'...'@` 을 쓴 것** — Bash 에선 `@'` 가 히어스트링이
아니라 리터럴이라 `@` 한 글자가 메시지 맨 앞에 그대로 들어간다.

**How to apply:**
- 멀티라인 커밋 메시지는 **툴에 맞는 문법**으로:
  - PowerShell 툴 → `git commit -m @'...'@` (여는 `@'` 와 닫는 `'@` 는 각자 자기 줄, `'@` 는 0열).
  - Bash 툴 → 진짜 heredoc: `git commit -F - <<'EOF' ... EOF` (또는 `-m $'...'`). `@'...'@` 쓰지 말 것.
- 커밋 직후 `git log -1 --format=%B` (또는 `%s`)로 **첫 줄에 `@` 등 이물질이 없는지 확인**하고,
  있으면 `git commit --amend` 로 고친 뒤(아직 안 밀었으면) 진행.

관련: [[push-target-dnable-dev]]
