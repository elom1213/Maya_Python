---
name: docs-go-in-jun-all-docs
description: Analysis/comparison/explanation markdown docs should be saved under JUN_All/docs
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c0755164-090a-4301-9c0e-2a449ba68d3c
---

분석·비교·설명용 마크다운 문서는 `JUN_All/docs/` 아래에 정리해서 저장한다.
서드파티 툴(예: SmartLayer)을 분석한 문서라도 그 외부 폴더가 아니라 repo의 `JUN_All/docs/`에 둔다.

`JUN_All/docs/` 내부는 3분할이다:
- `docs/*.md` = **툴 사용법 안내 문서** (`A000XX_*.md`).
- `docs/plans/` = **기능 개발 계획·설계 결정** 문서.
- `docs/study/` = **작업 방법론·기법 학습 노트**(특정 툴 안내 아님). 주제 기반 파일명, 인덱스는 `docs/study/README.md`.

**Why:** 사용자가 SmartLayer bake 분석 문서를 외부 툴 폴더 대신 `JUN_All/docs`로 옮기라고 직접 지시했고,
이후 "docs 루트는 툴 안내만, 공부용 문서는 별도 경로로" 라고 분리를 요청해 `docs/study/`를 신설함.
**How to apply:** 새 문서를 만들 때 종류로 경로를 고른다 — 툴 사용법=`docs/`, 개발 계획=`docs/plans/`,
방법론/기법 학습 노트=`docs/study/`. 새 문서는 해당 폴더의 README 목록 표에 한 줄 등록한다.
