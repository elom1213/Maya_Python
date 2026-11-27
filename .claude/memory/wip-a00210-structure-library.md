---
name: wip-a00210-structure-library
description: "A00210 v01.60 Path Structure 라이브러리 독립(프로파일 무관 · 카테고리 · 탭 전용 Pull/Push) — 구현 · 시험 완료, 데이터 이전 · 코드 둘 다 푸시 완료(11-27), GUI 확인 대기"
metadata:
  node_type: memory
  type: project
  originSessionId: f4077785-9011-4665-a74f-6be71e7fa818
  modified: 2026-11-27T00:39:08.556Z
---

계획서 `JUN_All/docs/plans/A00210_FileManager_structure_library_plan.md` (2026-11-27, 기본값 D1~D8 그대로). **v01.60 구현 완료.**

- 구조 위치 `<repo>/path_structures/`(프로파일 밖), 카테고리 `_categories/<id>.json` + 구조 JSON `category` id.
  코어 `app/core/structure_library.py`(StructureLibrary) · `library_settings.py`(PC 단위 `~/.jun_filemanager/structure_library.json`, `SETTINGS_PATH=None` → 호출 시점 `prefs.PREFS_DIR` 아래).
  `GitSync(scope_rel="path_structures")` + pull --rebase 충돌 시 `rebase --abort`. 탭 생성자 `(get_store, get_project_root, get_seed_prefs, log, on_pulled)`.
- 이전 `tools/A00210_FileManager/dev/migrate_structure_library.py` — 이 PC 데이터 클론에 커밋 `0a11b35`(20개, Dnable 661ac7f0 · JUN 0ca49e97 · MUE 124b2dfd · SA 7d2cb036). **2026-11-27 origin main 푸시 완료**. Maya_Python 은 Dnable_repo dev `f0dbcf05`.
  그 전에 다른 PC 가 옛 버전으로 저장하면 이전 스크립트를 다시 돌리면 된다(멱등).
- 시험 `tests/test_structure_library.py` 51/51, 기존 전부 통과. MainWindow 를 만드는 시험은 `LS.SETTINGS_PATH` 임시 경로.
- ★ 스모크 사고: 실제 프로파일 3개의 `recreate_to` 지워짐 → [[smoke-test-real-prefs-rewrites-profiles]]. 사용자가 Recreate To 를 한 번 다시 적어야 할 수 있다.
- 남은 것: GUI 실기(계획서 6장), 다른 PC 새 버전 + Pull.

**Why:** 사용자가 저장된 구조를 File Manager 탭(프로파일)에서 독립시키고 카테고리로 관리하길 원함.
**How to apply:** Path Structure 를 다시 프로파일 데이터 폴더에 묶지 말 것(`_refresh_other_tabs` 에서 뺐다). 원격 반영은 푸시 요청 턴에만.

관련: [[wip-a00210-data-folders]] [[wip-a00210-recreate-to-rename]] [[wip-a00210-pathstructure-files]]
