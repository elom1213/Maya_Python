---
name: wip-a00210-recreate-to-rename
description: "A00210_FileManager Path Structure tab — explicit \"Recreate To\" destination field + Rename button (v01.28); v01.32 field is independent of Project Root — never auto-fill it"
metadata: 
  node_type: memory
  type: project
  originSessionId: 746d699d-9d82-44da-b966-14caefd575fd
---

**★ v01.32 (2026-09-28) — 자동 채움 제거.** 사용자 보고: Recreate 가 `Recreate To` 가 아니라 Project Root 쪽에 생성된다.
원인은 아래 v01.28 설계의 `_show_preview` 자동 채움 — 구조 선택·Refresh·저장 후·프로파일 전환 새로고침마다 칸을
`<Project Root>/<base_rel>` 로 덮어써 적어 둔 경로가 조용히 바뀌었다. **이제 칸은 Project Root/File Manager 와 무관**,
자동 채움·clear 없음, 프로파일 `recreate_to` 로 저장/복원. **다시 자동 채움을 넣지 말 것.** 같은 버전에 공용 Help 메뉴 바.

**★ v01.33 (2026-10-01) — Capture 도 Project Root 와 무관.** 사용자 요청: 루트 위 · 밖 경로도 캡처되게. JSON 에 `base_path`(절대)
를 늘 기록, `base_rel` 은 루트 안일 때만(밖 · 루트 없음 · 다른 드라이브 = ""). **Path Structure 탭에 Project Root 검사를 다시 넣지 말 것.**
`store.make_key` 는 다른 드라이브에서 ValueError 를 던지므로 core `base_rel_in_root` 를 쓴다.

DONE (verified + pushed Dnable/dev, commit 57111a8), v01.28: A00210_FileManager **Path Structure** tab.

**Problem the user reported:** Recreate was confusing — it created folders at `<File Manager tab Project Root>/<base_rel>`, and the user couldn't tell if it targeted the File Manager tab's `Scan Dir` or this tab's `Base Folder` (capture source). Also wanted a Rename button for saved structures.

**Decision (user picked option 1 "베이스 폴더 직접 지정"):** add an explicit **"Recreate To"** destination base-folder field (+Browse) in the Saved Structures group. Checked folders are created **directly inside** it. Auto-filled to `<Project Root>/<base_rel>` (= old v01.24 behavior) when a structure is selected, but freely editable → removes the ambiguity, exact path always visible. User also required the **Recreate button be visually distinct** (it actually creates paths, unlike Refresh/Rename/Delete) and **right-aligned**.

**Changes:**
- `app/core/path_structure.py`: new `rename(store_dir, old_name, new_name)` (renames JSON file + updates internal `name`; ValueError on collision; same-file case = display-name-only). `recreate(...)` gained `base_abs=None` param — if given, creates folders directly inside it; else backward-compat `project_root + base_rel`.
- `app/ui/path_structure_tab.py`: import `QInputDialog`; `_RECREATE_QSS` green accent class const; button row now `[Refresh][Rename][Delete] <stretch> [Recreate(green)]`; new "Recreate To" `ipf_recreate_to` row (+Browse) below buttons; `_show_preview` auto-fills it with `base_abs`, `_clear_preview` clears it; `on_recreate` uses the field as `base_abs` (asks to create dir if missing, no longer needs Project Root); new `on_rename` (QInputDialog).
- version 01.28 / LAST_UPDATE 2026-07-07; doc `JUN_All/docs/A00210_FileManager.md` §4-C updated (mock + Recreate To/Recreate/Rename bullets).

py_compile passes. **Next:** user verifies in Maya/standalone → then push to Dnable/dev with WORKLOG entry (see [[worklog-maintenance]], [[push-includes-tool-guide-docs]], [[push-target-dnable-dev]]). Related: [[wip-a00210-pathstructure-tree-depth]] (v01.24 tree/depth), [[ui-text-english-only]].
