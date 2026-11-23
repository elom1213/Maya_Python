---
name: jun-memo-repo
description: "JUN_Memo = 스티커 메모 같은 독립 실행 PySide6 앱, Maya_Python 바깥 별도 저장소(로컬 main, 원격 origin elom1213/JUN_Memo - GitHub 저장소 생성은 gh 로그인 대기)"
metadata:
  node_type: memory
  type: reference
  originSessionId: 066c4609-b2f7-4781-b343-f8edfa187d49
  modified: 2026-11-23T01:38:33.120Z
---

- 경로: **`D:\D__3010_JUN_Memo`** (2026-11-23 사용자가 옮김 - 처음엔 `...\0030_maya_python_JUN\JUN_Memo`, 그 자리엔 빈 폴더만). Maya_Python 의 Framework 를 쓰지 않는 혼자 도는 앱.
  코드는 상대 경로라 옮겨도 된다(공유 폴더 = 저장소 안 shared/notes). 옮긴 뒤 점검 = 시험 74 통과 · 실제 노트 읽힘 · 옛 경로 바로가기 없음.
- git: 로컬 `main`, 원격 `origin` = `https://github.com/elom1213/JUN_Memo.git`. **푸시 대상 = origin main** (요청이 있을 때만 - 전역 규칙 2장).
- 2026-11-23: 사용자가 저장소 생성을 요청했으나 `gh` 미로그인으로 GitHub 쪽 저장소는 아직 없음 → `! gh auth login` 뒤 `gh repo create`.
- 데이터 (v01.01): 이 PC 노트 = `%APPDATA%\JUN_Memo\notes.json`, 창 상태(열림 · 자리 · Pin, 목록 창 색 · Pin) = 같은 폴더 `state.json`,
  **공유 노트 = 저장소 `shared/notes/<id>.json`(내용만 - git 으로 공유, 창을 옮겨도 안 바뀜)**. 시작 메뉴 · 작업 표시줄 = `0110_JUN_Video_Tool` 의 shell_integration 을 옮긴 것.
- 시험 `test_memo.py` · `test_scope_list.py` (공유 폴더는 `JUN_MEMO_SHARED` 로 임시 폴더). 시험 `python tests/test_memo.py`(오프스크린, 글꼴 보려면 `QT_QPA_FONTDIR=C:/Windows/Fonts`).
- 전역 라우팅 표(JUN_Claude/CLAUDE.md 5장)에는 아직 없다.
