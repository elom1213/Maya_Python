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
  Pin 을 22px 로 줄이면 테마 `QPushButton { padding: 8px }` 에 글자가 잘린다 → 버튼 stylesheet `padding: 0px 4px`(v01.02).
  오프스크린은 폰트가 안 그려져 캡처로 확인 불가 — `style().subElementRect(SE_PushButtonContents)` 높이로 확인.
- 마야 GUI 육안 확인은 아직.

**Export 규칙 (v01.03, 2026-09-18)** — `app/core/export_rules.py` 의 `EXPORT_RULES` 한 줄 = 규칙
(`ExportRule(key, label, tooltip, check(ctx)->RuleResult, default)`). UI 는 `Rules (n/m)` 드롭다운(`ui/rules_button.py`)이
목록을 읽어 만든다 — **규칙마다 UI 를 고치지 않는다.** 첫 규칙 `Check Hide Mesh`(기본 꺼짐).
**사용자 요구: 규칙에 걸리면 "도중에 멈춤" 이 아니라 파일을 단 한 개도 쓰지 않는다** → 모든 세트를 먼저 검사, 실패면
`export_sets` 를 아예 안 부른다. 켠 규칙은 첫 실패에서 멈추지 않고 전부 돈다(문제를 한 번에).
숨김 판정 = 자기·쉐입·**조상**의 visibility/lodVisibility/디스플레이 레이어/드로잉 오버라이드, Orig(intermediate) 제외.
`listRelatives(allDescendents)` 순서는 아웃라이너와 다르다(뒤집어도 안 맞음) → 자식을 직접 따라 내려간다.
창 크기 확인은 mayapy 에서 **HEAD 코드와 나란히** — `git archive` 를 스크래치에 풀고 `sys.modules` 의 tools/Framework 를
지운 뒤 import 해야 한다(mayapy 가 시작 때 tools 를 먼저 불러 옛 코드가 안 잡힌다). `tar` 는 `C:` 를 원격으로 오해 → `--force-local`.
