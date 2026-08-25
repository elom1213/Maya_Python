---
name: worklog-maintenance
description: How to maintain the daily WORKLOG.md (git-derived daily work journal)
metadata: 
  node_type: memory
  type: project
  originSessionId: 8d1aa5aa-0636-4c1c-9528-1b7a254c8130
  modified: 2026-08-14T03:43:09.275Z
---

작업 일지는 **저장소마다 따로**다 (최신 날짜가 위). 수동 갱신 — 사용자가
"일지/WORKLOG 갱신" 류 요청 시 그 저장소의 git 기록을 읽어 해당 날짜 섹션을 추가/갱신한다.

**2026-08-25 — 단일 누적 파일에서 월 롤링으로 바꿨다.**
루트 `WORKLOG.md` 는 **현재 월**만 담고, 지난 달은 **`<docs>/worklog/YYYY-MM.md`** 로 내린다.
**루트 파일 경로는 절대 안 옮긴다** — 마야 저장소 기준 **60군데**가 이 경로를 가리키고,
파일만 제자리에 두면 분할해도 링크가 하나도 안 깨진다.
계기는 크기(4,742줄/497KB)가 아니라 **컨텍스트** — 15만~24만 토큰이라 세션에서 통째로 못 열었다.
`JUN_Study/UPDATELOG.md` 도 같은 기제를 쓰지만 **거기는 연도 단위**다(한 줄 색인이라 밀도가 30배 낮다).
**기제는 같고 눈금이 다르다.** 절차 전문은 `JUN_All/docs/worklog/README.md`.

- 마야: `JUN_All/docs/WORKLOG.md`
- 언리얼: `JUN_UE/Docs/WORKLOG.md` (2026-08-14 신설, 같은 포맷) — [[jun-ue-plugin-repo]]

**How to apply:**
- 추출: `git log --since="YYYY-MM-DD 00:00" --until="(다음날) 00:00" --pretty=format:"%h | %s"` (머지 커밋 제외).
- 스코프(툴명) 기준 그룹화 → 한국어 한 줄 요약 + 관련 커밋 해시 + 줄 끝 `#툴태그`.
- `## YYYY-MM-DD` 섹션을 머리말 아래 **최신이 위**로 prepend (같은 날짜 있으면 갱신, 중복 헤딩 금지).
- **월이 바뀌면 먼저 롤링한다** — 직전 달의 `## YYYY-MM-DD` 블록 전부를 `worklog/YYYY-MM.md` 로
  **본문 그대로** 옮기고, 루트의 `## 지난 달 보관` 표와 `worklog/README.md` 목록에 한 줄씩 등록.
  그다음에 새 달 첫 섹션을 prepend 한다.
- frontmatter `updated:` 를 그날 날짜로 변경.
- 포맷: YAML frontmatter + `> [!summary]` 콜아웃 + 표준 마크다운 링크(`[[wikilink]]` 금지 — GitHub 깨짐).
  Obsidian + GitHub 양쪽 호환 유지. 요약은 한국어, 식별자는 영어 ([[explain-in-korean]], [[docs-go-in-jun-all-docs]]).
- 계획서: [[docs-go-in-jun-all-docs]] 경로의 `plans/worklog_doc_plan.md` 참고.
