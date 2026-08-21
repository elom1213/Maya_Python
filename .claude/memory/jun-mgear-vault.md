---
name: jun-mgear-vault
description: "mgear 노트는 JUN_Study 로 흡수됨. JUN_mgear repo 는 채용용 공개 저장소로 보존"
metadata: 
  node_type: memory
  type: project
  originSessionId: bdff8dcc-b27c-45f6-9afa-15e0f9b9cfb6
---

> **2026-08-21 — mgear 노트는 `JUN_Study` 저장소로 흡수됨** ([[study-docs-number-prefix]]).
>
> **JUN_mgear 는 방치한다(frozen).** 사용자가 명시적으로 정한 규칙:
> - **모든 학습 노트는 `JUN_Study` 에서 만든다.** mgear 관련도 JUN_Study 의 **03000 대역**
>   (`03000_mgear_MOC.md` 등)에 쓴다. JUN_mgear 에 직접 새 노트를 만들지 않는다.
> - JUN_mgear 는 **채용 담당자용 공개 창구**(README 가 소개문, repo 가 public)이므로 삭제하지 않는다.
>   JUN_Study 는 private 이라 이 역할을 대신할 수 없다.
> - **필요한 문서만 골라 JUN_Study → JUN_mgear 로 이전**한다. 요청이 있을 때만, 선별해서.
>   자동 동기화나 전량 미러링은 하지 않는다.
> - 이전할 때 JUN_Study 의 `01000_` 대역 번호를 그대로 가져갈지, JUN_mgear 의 `00_`~`99_`
>   체계에 맞출지는 그때 확인한다.
>
> 아래는 흡수 전 기록.

~~mgear(리깅 프레임워크) 공부 노트는 `C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_mgear` 폴더에 **Obsidian vault**로 관리한다 (작업 repo `Maya_Python` 밖의 형제 폴더). MOC + 분할 노트 구조, 한국어 본문, `[[위키링크]]` 연결.~~ (JUN_Study 로 옮기며 표준 마크다운 링크로 변환됨) 노트는 번호 접두사(`00_MOC_mgear`, `01`~`05`, `99_참고링크`).

GitHub 동기화: 원격 `https://github.com/elom1213/JUN_mgear.git`, 기본 브랜치 **`main`**.
- ⚠️ **계정 분리**: 커밋 author는 전역 `Dnable_JunnyPark`로 찍히지만, push 권한자는 git credential manager에 캐시된 **`elom1213`**(repo 소유자)다. gh는 미로그인이어도 push 됨(git 자격증명과 별개).
- `.obsidian/`는 `.gitignore`로 제외(.md 노트만 푸시).
- 이 repo의 push 대상은 `origin`(elom1213) — Maya_Python의 [[push-target-dnable-dev]]와 **무관**하니 헷갈리지 말 것.

**Why:** 학습 노트가 계속 누적되는 별도 프로젝트라, 매번 경로/원격/계정 구조를 재확인하지 않으려고 기록.
**How to apply:** mgear 노트 추가/수정 시 JUN_mgear 폴더에서 작업하고, 동기화는 `git add -A && git commit && git push`(origin main). 새 질문에서 시작된 노트는 `05_질문_기록.md`에 기원을 누적한다.
