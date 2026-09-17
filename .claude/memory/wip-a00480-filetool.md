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
- 창 최소 폭은 테마 기준 ~982(Naming 6칸 줄, 원본도 960). launch 가 테마 뒤에 `fit_to_theme()` → [[offscreen-size-needs-theme]].
  오프스크린에선 `show()` 가 화면 폭(800) 때문에 창을 1294 로 키우지만 오프스크린 착시다(quickTool 도 같다).
- 마야 GUI 육안 확인은 아직.
