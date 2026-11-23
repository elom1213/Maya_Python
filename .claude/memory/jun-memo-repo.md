---
name: jun-memo-repo
description: "JUN_Memo = 스티커 메모 같은 독립 실행 PySide6 앱, Maya_Python 바깥 별도 저장소(로컬 main, 원격 origin elom1213/JUN_Memo - GitHub 저장소 생성은 gh 로그인 대기)"
metadata:
  node_type: memory
  type: reference
  originSessionId: 066c4609-b2f7-4781-b343-f8edfa187d49
  modified: 2026-11-23T01:26:01.530Z
---

- 경로: `C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_Memo` (2026-11-23 v01.00). Maya_Python 의 Framework 를 쓰지 않는 혼자 도는 앱.
- git: 로컬 `main`, 원격 `origin` = `https://github.com/elom1213/JUN_Memo.git`. **푸시 대상 = origin main** (요청이 있을 때만 - 전역 규칙 2장).
- 2026-11-23: 사용자가 저장소 생성을 요청했으나 `gh` 미로그인으로 GitHub 쪽 저장소는 아직 없음 → `! gh auth login` 뒤 `gh repo create`.
- 데이터: `%APPDATA%\JUN_Memo\notes.json`(+ .bak). 시험 `python tests/test_memo.py`(오프스크린, 글꼴 보려면 `QT_QPA_FONTDIR=C:/Windows/Fonts`).
- 전역 라우팅 표(JUN_Claude/CLAUDE.md 5장)에는 아직 없다.
