---
name: wip-a00480-filetool
description: "A00480_FileTool v01.00 (2026-09-17) — A00040_file_exporter_V02 + quickTool File/Import option 을 Export/Import/Path 탭으로 통합. 원본은 보존, 앞으로 파일 입출력·경로 기능은 여기에 더한다"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5782f0ec-e7f6-4339-aa79-6790d10548f6
  modified: 2026-09-17T04:09:52.536Z
---

**A00480_FileTool** = 파일 임포트 · 익스포트 · 경로 설정/조작을 모아 **계속 늘려 갈** in-Maya PySide 툴(slate_dark).
탭 `Export`(A00040_V02 화면 그대로 + `Scene` 버튼) · `Import`(Import FBX normal) · `Path`(Copy/Open Scene Folder).

**사용자 결정(2026-09-17)**: 이름 `FileTool`, **`A00040_file_exporter_V02` 와 `A00030_quickTool_V02` 의 버튼은 보존**
(지우거나 "옮겨짐" 처리하지 말 것), 탭 이름 `Export / Import / Path`.

**Why:** 두 툴이 이미 짝으로 쓰였다(quickTool Copy Scene Folder → exporter Paste). 한 창으로 모으고 확장 지점을 만들려는 것.

**How to apply:**
- 새 파일 입출력 · 경로 기능 요청은 이 툴에 더한다. Import/Path 탭은 `SECTIONS` 표 한 줄 + 핸들러,
  로직은 `app/core/*_ops.py`(로그 리스트 반환). 섹션이 3~4개 넘으면 하위 탭 → [[prefer-subtabs-over-stacked-collapsibles]].
- FBX 명령 전에는 `core/fbx_plugin.ensure_fbx_plugin()`.
- Export 로직을 고칠 때 원본 A00040_V02 와 갈라지게 되는 것은 괜찮다(원본은 보존만). 동등성 검증 스크립트 방식:
  같은 씬을 두 core 로 내보내고 **FBX 를 재임포트한 계층**을 비교했다 → [[fbx-export-selected-scope]].
- **창 크기는 A00040_V02 와 같게(960 x 853)** — 사용자 요청(v01.01). 테마 qss 는 show() 뒤 polish 때 자식에 입혀져서,
  그 전(테마 직후 · show 직전)에 재거나 resize 하면 글자 큰 상태의 최소 크기(~1290)로 창이 커진다.
  launch 가 `QTimer.singleShot(0, fit_to_content)` 로 show 다음 루프에서 `resize(minimumSizeHint())`.
  탭 테두리만큼(+4 x +6)은 Export 페이지 여백 0 · 창 좌우 여백 -2 · Pin 높이 22 로 상쇄. → [[offscreen-size-needs-theme]]
- 마야 GUI 육안 확인은 아직.
