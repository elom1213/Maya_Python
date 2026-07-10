---
name: memory-synced-via-repo
description: 이 프로젝트의 메모리는 repo 의 .claude/memory 가 원본이고, ~/.claude/projects/<해시>/memory 가 그쪽으로 junction 돼 있다 (PC 간 공유)
metadata:
  type: project
---

Claude Code 메모리를 **여러 PC 에서 공유**하기 위해, 2026-07-10 부터 메모리 원본을 이 repo 안에 둔다.

```
~/.claude/projects/<프로젝트경로해시>/memory   ──junction──▶   <repo>/.claude/memory
```

- 원본: `<repo>/.claude/memory/` — git 추적, `Dnable_repo`(private) 로 푸시
- 그래서 **메모리를 저장하면 곧바로 repo 의 변경으로 잡힌다.** 메모리를 새로 쓰거나 고쳤으면
  다른 코드 변경과 함께(또는 따로) **커밋 + 푸시**해야 다른 PC 에 전달된다.
- `.claude/settings.local.json` 은 PC 별 개인 설정이라 `.gitignore` 로 제외.
- 새 PC 셋업 절차는 `.claude/memory/README.md` 참고 (해시 폴더명이 PC 마다 달라 정크션은 PC 마다 1 회 필요).

**주의:** `~/.claude/projects/<해시>/` 에는 세션 전체 대화 로그(`*.jsonl`, 수십 MB)가 함께 있다.
**폴더째 올리지 말 것** — 공유 대상은 `memory/` 하위뿐이다.

관련: [[push-target-dnable-dev]], [[worklog-maintenance]]
