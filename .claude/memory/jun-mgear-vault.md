---
name: jun-mgear-vault
description: "mgear study notes live in JUN_mgear Obsidian vault, synced to elom1213/JUN_mgear GitHub repo"
metadata: 
  node_type: memory
  type: project
  originSessionId: bdff8dcc-b27c-45f6-9afa-15e0f9b9cfb6
---

mgear(리깅 프레임워크) 공부 노트는 `C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_mgear` 폴더에 **Obsidian vault**로 관리한다 (작업 repo `Maya_Python` 밖의 형제 폴더). MOC + 분할 노트 구조, 한국어 본문, `[[위키링크]]` 연결. 노트는 번호 접두사(`00_MOC_mgear`, `01`~`05`, `99_참고링크`).

GitHub 동기화: 원격 `https://github.com/elom1213/JUN_mgear.git`, 기본 브랜치 **`main`**.
- ⚠️ **계정 분리**: 커밋 author는 전역 `Dnable_JunnyPark`로 찍히지만, push 권한자는 git credential manager에 캐시된 **`elom1213`**(repo 소유자)다. gh는 미로그인이어도 push 됨(git 자격증명과 별개).
- `.obsidian/`는 `.gitignore`로 제외(.md 노트만 푸시).
- 이 repo의 push 대상은 `origin`(elom1213) — Maya_Python의 [[push-target-dnable-dev]]와 **무관**하니 헷갈리지 말 것.

**Why:** 학습 노트가 계속 누적되는 별도 프로젝트라, 매번 경로/원격/계정 구조를 재확인하지 않으려고 기록.
**How to apply:** mgear 노트 추가/수정 시 JUN_mgear 폴더에서 작업하고, 동기화는 `git add -A && git commit && git push`(origin main). 새 질문에서 시작된 노트는 `05_질문_기록.md`에 기원을 누적한다.
