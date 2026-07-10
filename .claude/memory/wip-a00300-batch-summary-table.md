---
name: wip-a00300-batch-summary-table
description: A00300_meshDoctor — Target Meshes TSL + batch diagnose with per-mesh summary table (click row -> detail) (v01.02)
metadata: 
  node_type: memory
  type: project
  originSessionId: 746d699d-9d82-44da-b966-14caefd575fd
---

DONE (verified + pushed Dnable/dev, commit a3264f9), v01.02: A00300_meshDoctor.

**Request:** diagnose MANY meshes at once and see a SIMPLE per-mesh result. Previously `Diagnose Selected` only scanned the current Maya selection and dumped a long detailed report per mesh into the log.

**Decision (user picked "요약 테이블 + 클릭시 상세"):**
- New **Target Meshes** TSL (QListWidget) at top with **Add Selected / Remove / Clear**. Items held by **UUID** (display short transform name) — dup-name/reparent safe. Diagnose runs on the list; **empty list falls back to current selection** (backward compat).
- Diagnose button renamed **"Diagnose Listed"**.
- New **Summary table** (QTableWidget: Mesh | Status | Issues) between the diagnose row and the log. Status is color-coded (`● FAIL/WARN/INFO/PASS` via `_SEV_COLOR`, `setForeground(QColor)`). Issues = WARN/FAIL checks as `name(count)` (FAIL first), else `clean`. **Click a row → that mesh's full existing detailed report prints in the log view below** (`_on_summary_row` → `_print_result`). Log also gets a one-line batch summary + report paths on diagnose.

**Changes:**
- `app/core/mesh_scan.py`: added `MeshScanner.scan_nodes(nodes)` + `_resolve_meshes(nodes)` (deduped transform/shape resolution over an explicit node list); `scan_selection()` now delegates to `scan_nodes(cmds.ls(sl=True))`. `scan_one`/result dict unchanged.
- `app/ui/main_window.py`: import `shape_of`; `__init__` adds `self._results=[]`, resize 600x820; `build_ui` adds Target Meshes group + Summary table, renames button; `on_diagnose` rewritten (list-or-selection source, fill summary, batch log, report write); new `on_add_selected/on_remove_targets/on_clear_targets/_to_uuid/_listed_uuids/_listed_nodes/_issue_summary/_fill_summary/_on_summary_row`.
- version 01.02 / 2026-07-07. py_compile passes.

**v01.03 (2026-07-10, verified + pushed):** selecting rows in the Target Meshes list now selects the same meshes in the scene (like `MOD_tsl_qt_v01._on_selection_changed`), but resolved via the item's UUID (`cmds.ls(uuid, long=True)`) instead of the display name. Empty selection leaves the scene selection alone. Guide doc `JUN_All/docs/A00300_meshDoctor.md` exists.

See [[uuid-safe-rename-duplicate-names]], [[push-includes-tool-guide-docs]], [[worklog-maintenance]], [[ui-text-english-only]]. Related earlier WIP: [[wip-a00300-zero-area-quality-rework]] (that sliver/tiny + Clear Log rework is already present in current code).
