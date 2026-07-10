---
name: wip-tsl-uuid-selection
description: Framework MOD_tsl_qt_v01 holds UUIDs so list→scene selection survives rename/reparent/dup names
metadata: 
  node_type: memory
  type: project
  originSessionId: 2af83ce7-788e-4c2c-83e0-9ebc68b52132
---

IMPLEMENTED on branch `dev_tsl` (2026-07-10), pushed; **Maya runtime check still pending** — it's the
shared TSL widget, so 18 tools are affected.

`Framework/qt/MOD_tsl_qt_v01.py` now stores `(uuid, component)` on each scene-node item
(`Qt.UserRole + 1`) and resolves it via `cmds.ls(uuid, long=True)` when a row is clicked.

**Why:** `_on_selection_changed` selected by NAME and swallowed errors (`except Exception: pass`).
`cmds.ls(sl=True, fl=True)` actually returns a shortest-UNIQUE path, so dup names work *at add time* —
failures only appear once the stored name goes stale (rename/reparent → "No object matches name";
a new same-named node → "More than one object matches name"). Silent either way.

**How to apply / gotchas:**
- non-node lists (attr names, file names, node types) get no uuid → name fallback, skip silently if
  the name isn't in the scene
- components: `cmds.ls("<uuid>.vtx[0]")` is a parse error → store node uuid + suffix, reassemble
- Up/Down/Sort go through `set_items(get_all_items())` → would drop uuids; reorder by records instead
- `set_items` must keep `addItems` (one `rowsInserted`); A00150/A00160/A00170/A00290 listen to that
  model signal
- `get_all_items()` still returns text (all tools feed it to maya.cmds); new `get_all_nodes()` /
  `selected_nodes()` resolve via uuid
- `append_unique` now dedupes by uuid, so same-named different objects can coexist

Related: [[uuid-safe-rename-duplicate-names]], [[mayapy-headless-verify]]
