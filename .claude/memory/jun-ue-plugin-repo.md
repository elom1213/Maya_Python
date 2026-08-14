---
name: jun-ue-plugin-repo
description: "언리얼 툴은 마야 repo 가 아니라 별도 JUN_UE repo (루트=플러그인, origin=elom1213, main)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-08-14T02:16:22.714Z
---

언리얼 에디터 툴은 `JUN_All` 이 아니라 **별도 저장소**에서 작업한다 (2026-08-14 시작).

- 경로: `C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_UE`
- 원격: `https://github.com/elom1213/JUN_UE.git`, 브랜치 **`main`**
  → 마야 repo 의 기본 push 대상(Dnable_repo/dev)과 **다르다**. [[push-target-dnable-dev]] 적용 안 됨
- **저장소 루트 자체가 플러그인 폴더**. 플러그인 식별자는 `JUNTools.uplugin` (= 에셋 마운트 경로 `/JUNTools/`, 변경 금지)
- C++ 모듈 없는 **Python 콘텐츠 플러그인** — 컴파일 없이 어느 UE 5.7+ 프로젝트에나 배치
- 툴은 `Content/Python/jun_tools/tools/A00NNN_<name>/` 에 `core.py`(로직) + `ui.py`(다이얼로그), `registry.py` 에 한 줄 등록
- 설계 근거·함정은 repo 의 `Docs/00_UE_Tool_Plugin_Guide.md` 에 정리돼 있으니 작업 전 열어볼 것

**Why:** 언리얼 플러그인은 배치 경로가 고정이고(`<Project>/Plugins/<Name>/`), 엔진 버전이라는
버전 축이 하나 더 붙으며, 이식이 submodule/junction 단위라 마야 파이썬 트리에 섞을 수 없다.

**How to apply:** 언리얼 툴 얘기가 나오면 `JUN_All` 이 아니라 `JUN_UE` 로 간다.
푸시는 `origin main` (그 턴에 요청이 있을 때만 — [[push-only-when-asked]]).
