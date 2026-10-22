---
name: wip-a00220-drag-drop
description: "A00220_BackupTool v01.18 — 탐색기 드래그&드롭으로 Target Files 추가. 드롭은 QListWidget 뷰포트로 오고, 비활성 위젯은 드롭을 못 받으니 그룹 박스에도 필터"
metadata:
  type: project
---

`A00220_BackupTool` **v01.18** (2026-10-22) — 탐색기에서 파일을 `Target Files` 그룹 어디에든 놓으면
`Add...` 와 같이 담긴다. 폴더는 **바로 안의 파일만**(하위 폴더 X — 폴더째 트리를 끌어오면 수백 개가
들어올 수 있어 1단계만, 사용자 미확인 결정). 중복은 `os.path.normcase` 로 건너뛰고 로그 한 줄
`Dropped: N file(s), M folder(s) expanded, K already listed.`. `Add...` 와 드롭이 `add_paths()` 하나.

**함정 둘**
- 드롭 이벤트는 `QListWidget` 본체가 아니라 **`viewport()`** 로 온다 → 뷰포트에 `setAcceptDrops` +
  `installEventFilter` (A00240 Junction 탭 `_dropped_paths` 와 같은 모양).
- **비활성(`setEnabled(False)`) 위젯은 드롭을 받지 못한다.** 이 툴은 실행 중 목록을 비활성으로 두므로
  그룹 박스(`QGroupBox`)에도 같은 필터를 걸어 실행 중에도 담기게 했다(`Add...` 는 원래 실행 중에도 됨).
  실행 중 + Auto Backup 이면 추가 직후 `_rewatch_files()` — mtime 폴링은 처음 본 파일을 기준선만 잡고
  저장으로 치지 않아 오탐 없음.

검증: 오프스크린 PySide6 로 `QDragEnterEvent`/`QDropEvent`(`QMimeData.setUrls`) 를 `sendEvent` 로
직접 보내 16항목 통과. **실제 탐색기 드롭은 GUI 미확인.**
관련: [[wip-a00220-shrink]], [[wip-a00240-junction-tab]]
