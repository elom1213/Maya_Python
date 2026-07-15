---
name: update-portfolio-on-tool-work
description: "After tool/tool-related work, reflect portfolio-worthy content into JUN_All/docs/portfolio EN+KR docs"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 91ab0dea-4b6f-4134-a5cd-3d3ccc44c43a
---

툴 또는 툴 유관 작업을 진행할 때, 포트폴리오로 어필할 만한 내용이 생기면
`JUN_All/docs/portfolio/portfolio_EN.md` 와 `portfolio_KR.md` **양쪽**을 기존 문서의
구조·톤을 참고해 추가/업데이트할 것.

**Why:** 이 두 문서는 **3D 게임 업계(실사·카툰풍 게임 프로젝트) 지원용**이다. 사용자가 특히
어필하고 싶어 하는 축:
- **메타휴먼 / 캐릭터 리깅**
- **리깅·애니메이션 관련 파이썬 스크립트 제작**
- **DCC(마야) ↔ 언리얼 간 리그 데이터 변환**

**How to apply:**
- EN/KR 두 문서를 **같은 내용으로 동기화**해서 갱신(한쪽만 고치지 말 것). EN 은 영어, KR 은 국문.
- 기존 섹션 구조 재사용: 1. MetaHuman·Facial / 2. Unreal 노드 생성(Maya→UE 브릿지) /
  3. 리깅 자동화 / 4. 애니메이션 / 5. 모델링·QC / 6. 파이프라인·프레임워크 /
  7. 강조점 / 8. 문서·저장소. 새 작업을 가장 맞는 섹션에 끼워 넣고, 위 3개 어필 축에
  해당하면 그 각도를 드러낸다(문제→한 일→결과 형식).
- frontmatter `updated:` 와 상단 기간(Period)의 끝 날짜를 오늘로 갱신.
- **통계 수치("299 commits" 등)는 큐레이션된 값**이라 `git rev-list --count`(전체 351 등)와 기준이
  다르다. 임의로 rev-list 값으로 바꾸지 말 것.
- 과장 금지: 실제 구현/검증한 것만. WORKLOG 업데이트하는 흐름에 이 포트폴리오 갱신도 함께 고려.

관련: [[worklog-maintenance]], [[docs-go-in-jun-all-docs]], [[explain-in-korean]]
