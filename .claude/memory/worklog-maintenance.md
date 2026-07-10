---
name: worklog-maintenance
description: How to maintain the daily WORKLOG.md (git-derived daily work journal)
metadata: 
  node_type: memory
  type: project
  originSessionId: 8d1aa5aa-0636-4c1c-9528-1b7a254c8130
---

작업 일지는 `JUN_All/docs/WORKLOG.md` (단일 누적 파일, 최신 날짜가 위). 수동 갱신 — 사용자가
"일지/WORKLOG 갱신" 류 요청 시 git 기록을 읽어 해당 날짜 섹션을 추가/갱신한다.

**How to apply:**
- 추출: `git log --since="YYYY-MM-DD 00:00" --until="(다음날) 00:00" --pretty=format:"%h | %s"` (머지 커밋 제외).
- 스코프(툴명) 기준 그룹화 → 한국어 한 줄 요약 + 관련 커밋 해시 + 줄 끝 `#툴태그`.
- `## YYYY-MM-DD` 섹션을 머리말 아래 **최신이 위**로 prepend (같은 날짜 있으면 갱신, 중복 헤딩 금지).
- frontmatter `updated:` 를 그날 날짜로 변경.
- 포맷: YAML frontmatter + `> [!summary]` 콜아웃 + 표준 마크다운 링크(`[[wikilink]]` 금지 — GitHub 깨짐).
  Obsidian + GitHub 양쪽 호환 유지. 요약은 한국어, 식별자는 영어 ([[explain-in-korean]], [[docs-go-in-jun-all-docs]]).
- 계획서: [[docs-go-in-jun-all-docs]] 경로의 `plans/worklog_doc_plan.md` 참고.
