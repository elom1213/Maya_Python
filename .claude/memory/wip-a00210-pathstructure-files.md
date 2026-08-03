---
name: wip-a00210-pathstructure-files
description: "A00210 Path Structure 가 폴더뿐 아니라 파일도 캡처/재생성 — 0바이트 + '__' 표식 (v01.29)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 85c8852e-52d8-4514-9afa-b44bf5d7ef96
  modified: 2026-08-03T00:46:36.491Z
---

A00210_FileManager **Path Structure** 탭이 폴더만이 아니라 **파일 목록도** 캡처/재생성한다
(2026-08-03, v01.28→01.29, core 24 + UI 12 항목 검증 + **실기 확인 완료**).
체크박스 2개, 둘 다 기본 켬 — **`Include files`**(Save 쪽, Capture 가 `structure.files` 기록) /
**`Create files`**(Preview 행, 구 *Show files* 대체 — 기록된 파일을 트리에 체크박스와 함께 보여주고
Recreate 가 생성).

**Why:** 생성 파일은 **0바이트 빈 파일**이고 이름 끝에 **`__`** 를 붙인다(`test.ma` → `test.ma__`).
확장자를 바꾸지 않고 뒤에 덧붙여야 원래 이름을 그대로 읽으면서도 탐색기·DCC 가 빈 껍데기를
진짜 씬으로 열려 하지 않는다. 이름만 기록하고 내용은 안 담는 건 "원본 mb/ma 는 공유 대상 아님"
이라는 이 툴의 원칙 그대로.

**How to apply:**
- `Show files`(표시 전용)를 남기지 않고 `Create files` 로 **흡수**했다. 파일이 생성 대상이 된 이상
  표시와 생성을 따로 두면 *안 보이는데 만들어지는* 항목이 생겨 Depth 규칙과 어긋난다 →
  **트리에 보이는 것이 만들어지는 것**으로 통일. 새 옵션 추가할 때 이 규칙을 깨지 말 것.
- `marked_name()` 은 **멱등** — 이미 `__` 로 끝나면 안 붙인다(재캡처→재생성 시 `____` 방지).
- 기존 파일은 **덮어쓰지도 비우지도 않는다**. `open(..., "x")` 배타 생성 → 검사와 생성 사이
  경쟁 상태에서도 안전. 있으면 `existing_files` 로만 집계.
- 깊이·최상위 체크리스트는 폴더와 같은 규칙. **단 base 직속 파일은 체크리스트와 무관하게 항상 포함**
  (어느 최상위 폴더에도 속하지 않는 base 자체의 내용물).
- 하위호환: `files` 키 없는 구버전 JSON → `[]` 로 읽혀 **폴더만 재생성**. `recreate()` 반환을
  **`RecreateResult`**(폴더/파일 따로)로 바꾸면서 `created, existing = recreate(...)` 2-튜플
  언패킹(`__iter__`)을 남겨 호출부 무변경.
- 문서: `JUN_All/docs/A00210_FileManager.md` §4-C "파일 재생성", CHANGELOG `[01.29]`.

관련: [[wip-a00210-recreate-to-rename]], [[wip-a00210-pathstructure-tree-depth]],
[[qtreewidgetitem-checkable-default-flag]]
