---
name: wip-a00210-recreate-to-rename
description: "A00210_FileManager Path Structure tab — explicit \"Recreate To\" destination field + Rename button (v01.28)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 746d699d-9d82-44da-b966-14caefd575fd
---

DONE (verified + pushed Dnable/dev, commit 57111a8), v01.28: A00210_FileManager **Path Structure** tab.

**Problem the user reported:** Recreate was confusing — it created folders at `<File Manager tab Project Root>/<base_rel>`, and the user couldn't tell if it targeted the File Manager tab's `Scan Dir` or this tab's `Base Folder` (capture source). Also wanted a Rename button for saved structures.

**Decision (user picked option 1 "베이스 폴더 직접 지정"):** add an explicit **"Recreate To"** destination base-folder field (+Browse) in the Saved Structures group. Checked folders are created **directly inside** it. Auto-filled to `<Project Root>/<base_rel>` (= old v01.24 behavior) when a structure is selected, but freely editable → removes the ambiguity, exact path always visible. User also required the **Recreate button be visually distinct** (it actually creates paths, unlike Refresh/Rename/Delete) and **right-aligned**.

**Changes:**
- `app/core/path_structure.py`: new `rename(store_dir, old_name, new_name)` (renames JSON file + updates internal `name`; ValueError on collision; same-file case = display-name-only). `recreate(...)` gained `base_abs=None` param — if given, creates folders directly inside it; else backward-compat `project_root + base_rel`.
- `app/ui/path_structure_tab.py`: import `QInputDialog`; `_RECREATE_QSS` green accent class const; button row now `[Refresh][Rename][Delete] <stretch> [Recreate(green)]`; new "Recreate To" `ipf_recreate_to` row (+Browse) below buttons; `_show_preview` auto-fills it with `base_abs`, `_clear_preview` clears it; `on_recreate` uses the field as `base_abs` (asks to create dir if missing, no longer needs Project Root); new `on_rename` (QInputDialog).
- version 01.28 / LAST_UPDATE 2026-07-07; doc `JUN_All/docs/A00210_FileManager.md` §4-C updated (mock + Recreate To/Recreate/Rename bullets).

py_compile passes. **Next:** user verifies in Maya/standalone → then push to Dnable/dev with WORKLOG entry (see [[worklog-maintenance]], [[push-includes-tool-guide-docs]], [[push-target-dnable-dev]]). Related: [[wip-a00210-pathstructure-tree-depth]] (v01.24 tree/depth), [[ui-text-english-only]].
