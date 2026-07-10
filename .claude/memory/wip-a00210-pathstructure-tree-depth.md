---
name: wip-a00210-pathstructure-tree-depth
description: A00210 Path Structure tab tree-preview + depth/selective recreate (DONE: verified + pushed v01.24)
metadata: 
  node_type: memory
  type: project
  originSessionId: 1a790789-b405-42c4-94d0-962e30c742f9
---

IMPLEMENTED (PySide 실기 test + push pending): A00210_FileManager v01.23→**v01.24** — Path Structure 탭 개편.

**feature 1 (Preview 트리뷰)**: `path_structure_tab.py` 의 Preview 를 `QPlainTextEdit` → `QTreeWidget` 로 교체. **Show files** 체크박스(기본 OFF; ON 이면 로컬 파일시스템에서 실제 파일도 표시 — 확인용, 재생성 안 함) + **Expand** 버튼(큰 QDialog, 체크 상태 공유). 폴더/파일 표준 아이콘.

**feature 2 (깊이·선택 재생성)**: Save 그룹 *Recursive* 체크박스 → **Capture Depth** 스핀박스(1=top만, 0=All). Saved 그룹 **Depth** 스핀박스(Preview 표시 겸 Recreate 깊이 제한) + 트리 폴더별 체크박스(해제=Recreate 제외, `self._excluded` set 로 추적; 루트 base 는 항상 생성, 체크 자식의 상위는 makedirs 로 자동 생성).

**core `path_structure.py`**: `PathStructure.max_depth` 필드(구버전 JSON `recursive`→깊이 매핑으로 하위호환: True=0/All, False=1/top). `_collect_folders(base, max_depth, include_top)`, `limit_depth(folders, max_depth)`, `build_structure_tree(structure, base_abs, show_files, max_depth)`, `recreate(structure, project_root, folders=None)`. 옛 `build_tree_lines()` 는 미사용이나 남겨둠.

DONE: PySide 실기 확인 완료 + push 완료(2026-07-02, Dnable/dev, commit 7d8be11). 다중 선택(Shift/Ctrl) 후 체크박스 일괄 토글 + 토글 후 선택 유지(QTimer.singleShot 로 선택 복원), Saved 목록 높이 축소도 포함. 문서: 가이드 §4-C + CHANGELOG/version.py + WORKLOG 갱신.

관련: [[docs-go-in-jun-all-docs]] [[push-includes-tool-guide-docs]] [[worklog-maintenance]] [[prefer-pyside-for-new-tools]]
