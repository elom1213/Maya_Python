---
name: study-docs-number-prefix
description: docs/study 학습 노트는 5자리 번호 접두사(간격 100)로 주제순 정렬한다
metadata:
  node_type: memory
  type: project
---

`JUN_All/docs/study/` 학습 노트 파일명은 **`00100_영문주제.md`** — 5자리 제로패딩 번호 접두사 +
영문 주제명 (`tools/A000XX_` 와 같은 방식). 2026-08-21 도입.

- **간격은 100** (`00100`, `00200` …). 사이에 끼울 때는 중간값(`00250` → `00225` → `00212` …)을 써서
  **뒤 문서를 밀지 않는다**. 간격 10 이면 3번 만에 막혀 전체 renumber → 링크 연쇄 파손이 난다.
- 번호는 연대순이 아니라 **주제 근접성**을 뜻한다. "번호가 가까움 = 관련 문서".
  최초 배치만 주제순으로 잡았고(모델링 → 스킨 → 페이셜 → 베이크 → 시뮬 → 스크립팅),
  이후 새 문서는 **끝에 +100 이 아니라 주제가 가장 가까운 문서 옆 번호**로 넣는다.
- 파일명에 한글 금지(영문만). `README.md` 는 번호 없이 유지 — GitHub 이 폴더 인덱스로 자동 렌더하는 이름.

**Why:** 탐색기 "만든 날짜" 컬럼은 git clone·복사·백업 복원 때마다 리셋되어 신뢰할 수 없다.
번호를 파일명에 박으면 순서가 파일과 함께 다니고, 사용자가 tools 폴더에서 이미 쓰던 방식이라 학습 비용이 0.

**How to apply:** 번호를 바꾸면 인바운드 링크가 깨진다. 리네임은 `git mv` + 링크 일괄 치환 +
`study/README.md` 목록 표 갱신을 **한 커밋에** 함께 한다. 참조처는 `docs/*.md`, `docs/WORKLOG.md`,
`tools/*/README.md`. `docs/` 는 Obsidian vault 지만 `.obsidian/` 은 gitignore 라 건드리지 않는다.
관련: [[docs-go-in-jun-all-docs]]
