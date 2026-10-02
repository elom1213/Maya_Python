---
name: framework-token-name-widget
description: 공용 토큰 이름 위젯 MOD_tokenName_qt_v01 + core/token_naming (2026-09-28) — A00330 Token · A00480 Naming 공유. 툴은 TokenRuleSet 묶음과 TokenProfileStore(data_dir) 만 고른다
metadata:
  node_type: memory
  type: project
  originSessionId: 64d856a3-210c-4001-9bbc-757c4ec50a03
  modified: 2026-09-28T02:19:24.371Z
---

**토큰으로 이름 짓는 화면(Profile + 토큰 칸)은 `Framework/qt/MOD_tokenName_qt_v01.py` 하나다.** 규칙·저장은
`Framework/core/token_naming.py`. 문서 `JUN_All/docs/Framework_MOD_tokenName_qt.md`.

- 사용자 요청(2026-09-28): A00480 Naming 을 A00330 Token 과 **같은 UI·기능**으로, SK/MANU/CH/Name/Basic/Version 이
  그대로 나오게(= A00480 기본 프로파일 `Default`), A00480 의 `Set's Name` 규칙 추가, **공유 코드는 공용 위젯으로**.
- 툴 쪽은 규칙 묶음만 고른다: `MAYA_NODE_RULES`(Custom/Numbering, 마야 글자 검사, Numbering 2 개 = 오브젝트/노드) ·
  `FILE_NAME_RULES`(+Set's Name, Numbering = 세트 순번 1 개, Windows 파일명 검사). 새 툴은 `TokenRuleSet(...)` 한 줄.
- 프로파일은 툴마다 `TokenProfileStore(<tool>/data, 기본 토큰, 묶음)` — `data/` 는 .gitignore 에 추가할 것.
- A00330 `token_ops`/`token_profile_prefs` 는 예전 이름만 노출하는 얇은 층으로 남겼다(naming_ops.rename_tokens 가 쓴다).
- `framed=False` = Profile 과 Add/Delete Token 한 줄 + `preview_row` 에 툴 버튼(A00480 Set Name). 세로를 아끼려고.
- **Numbering 칸이 4줄이라 칸 줄 높이를 정한다** — A00480 창이 960x853 → 868x970(오프스크린). 사용자에게 보고함, 마야 GUI 확인 전.

- **칸 편집은 저장하지 않는다 — `Save` 버튼만 저장**(2026-10-01, A00480 v01.08 · A00330 v01.11). 사용자 요청: 고친 칸이 알림 없이
  프로파일 기본이 되는 게 싫다, 버튼을 눌렀을 때만. `_after_edit()` 에 저장을 다시 넣지 말 것. 기준 `_saved_tokens` 는 로드 직후 `tokens()`
  (json 원본과 비교하면 형식 차이로 늘 dirty). Save 때문에 A00480 창 폭 882 → 954(오프스크린).

- **Enum 규칙(2026-10-02, A00330 v01.12)** — `{"rule": "enum", "role", "values", "value"}`, 키는 A00470 이름 규칙 json 과 같게.
  `MAYA_NODE_RULES` 에만(A00480 엔 없음). 칸 = role 라벨 · 값 콤보 · `Values...`. 팀 문서 `docs/A00330_NamingRule_Set.md`
  (프로파일 `Dnable_Set_v001`). **A00330 `data/` 는 개발 저장소에서 gitignore — 프로파일은 이 PC · 릴리즈 저장소에만 있다.**
  릴리즈 빌더는 툴 폴더를 지우고 다시 복사하며 docs 는 `JUN_All/docs/<번호>*.md` 에서 가져오므로, 릴리즈용 문서도 원본은 `JUN_All/docs/` 에.

관련: [[wip-a00330-token-tab]], [[wip-a00480-filetool]], [[offscreen-size-needs-theme]]
