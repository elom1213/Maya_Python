---
name: study-docs-number-prefix
description: 학습 노트는 JUN_Study repo, 5자리 도메인 대역 번호(간격 100)로 정렬한다
metadata:
  node_type: memory
  type: project
---

리깅·애니메이션·그래픽 **학습 노트는 별도 저장소 `JUN_Study`** 에 있다 (2026-08-21 이전 완료).

- 로컬 `JP/0030_maya_python_JUN/JUN_Study` (Maya_Python 과 형제 폴더)
- 원격 `https://github.com/elom1213/JUN_Study.git`, 브랜치 **`master`**, **private**
- 저장소 루트 = Obsidian vault 루트. `.obsidian/` 는 gitignore.
- 예전 위치였던 `Maya_Python/JUN_All/docs/study/` 에는 이전 안내 README 만 남아 있다.
- 옛 `JUN_mgear` repo 노트도 여기로 흡수됨 → [[jun-mgear-vault]]

**파일명**: `01000_영문주제.md` — 5자리 번호 + 영문 주제명. 한글 파일명 금지.

**도메인 대역**: 01000 모델링/지오메트리 · 02000 스킨/웨이트 · 03000 리깅/컴포넌트(mgear) ·
04000 페이셜/MetaHuman · 05000 애님/베이크 · 06000 시뮬/피직스 · 07000 셰이딩/렌더/수학 ·
08000 스크립팅/API · 09000 DCC 외(언리얼·후디니·블렌더).

- 대역 안에서 **간격 100**. 사이에 끼울 때는 중간값(`03150` → `03125` → `03112` …)으로
  **뒤 문서를 밀지 않는다**. 간격 10 이면 3번 만에 막혀 전체 renumber → 링크 연쇄 파손.
- 번호는 연대순이 아니라 **주제 근접성**을 뜻한다. 새 문서는 끝에 +100 이 아니라
  **주제가 가장 가까운 문서 옆 번호**로 넣는다.
- **폴더로 쪼개지 않는다.** 1단계 평면 + 번호 대역 + 태그. (`_meta/` 만 예외 — 보조/과정 문서)
- 링크는 **표준 마크다운만**. `[[wikilink]]` 는 GitHub 에서 깨진다.
- `README.md` 는 번호 없이 유지 — GitHub 이 저장소 인덱스로 자동 렌더하는 이름.

**Why:** 탐색기 "만든 날짜" 는 clone·복사 때마다 리셋되어 못 믿는다. 번호를 파일명에 박으면
순서가 파일과 함께 다닌다. 저장소를 분리한 이유는 학습 노트가 근무 환경(집·회사·이직처)을
따라다니는 개인 자산이라, 툴 소스 1,300여 개가 든 Maya_Python 을 통째로 clone 해야만
볼 수 있는 상태가 부적절했기 때문. 부수 효과로 서드파티 역분석 노트가 public → private 로 이동.

**How to apply:** 새 학습 노트는 JUN_Study 에 만들고 루트 README 목록 표에 한 줄 등록.
번호를 바꾸면 링크가 깨지니 `git mv` + 링크 치환 + README 갱신을 **한 커밋에**.
**회사 고유 정보(프로젝트명·캐릭터명·에셋 경로·사내 수치)는 적지 않는다** — 원리만, 사례는 익명화.
관련: [[docs-go-in-jun-all-docs]]
