---
name: wip-a00210-structure-library
description: "A00210 Path Structure 의 Saved Structures 를 프로파일에서 독립 + 카테고리 + 탭 전용 Pull/Push 계획 (v01.60 예정, 구현 전)"
metadata:
  node_type: memory
  type: project
  originSessionId: f4077785-9011-4665-a74f-6be71e7fa818
  modified: 2026-11-27T00:19:32.994Z
---

2026-11-27 계획서 `JUN_All/docs/plans/A00210_FileManager_structure_library_plan.md` 작성 (**구현 전**, 7장 결정 D1~D8 사용자 확인 대기).

- 원인: 구조 JSON 이 `<store>/profiles/<data_folder>/path_structures/` 라 프로파일의 Data Folder 를 따라 목록이 바뀐다(예: `Dnable_CH` 는 Dnable 폴더 프로파일에서만).
- 설계: 저장소 루트 `path_structures/`(같은 저장소 · 같은 클론), 카테고리 = `_categories/<id>.json` 하나씩 + 구조 JSON `category` id(동시 추가 충돌 없음),
  클론 경로 · Recreate To 는 PC 단위 `~/.jun_filemanager/structure_library.json`, 탭 전용 Push = `add -- path_structures` 만(`GitSync scope_rel`),
  Pull 은 git 한계로 브랜치 전체. 기존 20개는 `dev/migrate_structure_library.py`(dry-run · 멱등 · git mv) 로 옛 데이터 폴더 이름 = 첫 카테고리.
- 함께 고칠 것: `GitSync` pull --rebase 충돌 시 abort 안 함(클론이 rebase 중으로 남음).
- ★ 데이터 클론에 다른 작업의 records 미커밋 변경이 있다 — 경로 한정 add 만.

**Why:** 사용자가 저장된 구조를 File Manager 탭(프로파일)에서 독립시키고 카테고리로 관리하길 원함.
**How to apply:** 구현은 계획서 4장 단계 순서대로. 이전 커밋 · 데이터 저장소 Push 는 푸시 요청 턴에만.

관련: [[wip-a00210-data-folders]] [[wip-a00210-recreate-to-rename]] [[wip-a00210-pathstructure-files]]
