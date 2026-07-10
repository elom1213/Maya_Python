---
name: wip-a00360-sorttool
description: A00360_SortTool — new in-Maya PySide tool; sort listed objects by world X/Y/Z / name / type and reorder outliner + TSL (v01.00)
metadata: 
  node_type: memory
  type: project
  originSessionId: 746d699d-9d82-44da-b966-14caefd575fd
---

DONE (verified + pushed Dnable/dev, commit 8cf97a9), v01.00: NEW tool A00360_SortTool. Guide doc `JUN_All/docs/A00360_SortTool.md` created.

**Request:** list selected objects in a TSL, sort them by one of world X/Y/Z position (also by name, type), and reorder them in the **outliner top→bottom**; a checkbox toggles the outliner reorder (default ON); the TSL list itself also reorders to match. Must work for ANY object with a knowable position — joint/mesh/curve/cluster/lattice handle/etc. Built as PySide (arch B) per user. Reference MELs: `C:\Users\USER\Documents\maya\2024\scripts\AriSortOutliner.mel` + `AriSortOutlinerOptions.mel` (name/type sort + slot-swap reorder).

**Structure (cloned from A00060_jointTool_V02 skeleton):**
- `__init__.py` (run), `launch.py` (coral_dark theme, reload_for_tool, objectName window de-dup), `__dragDrop_A00360.py` (shelf "SortTool"), `app/{__init__,config/version(01.00),core,ui}`.
- `app/core/sort_manager.py` — pure maya.cmds logic. `sort_objects(items, mode, reverse, reorder_outliner)` → `(ordered_texts, missing)`. MODE_X/Y/Z/NAME/TYPE. Key: position via `cmds.xform(ws=True,translation)`; name = short name lower; type = (nodeType-of-shape-or-self, name). Nodes with no position (pure DG) return key None → go to `missing` (skipped, not crash). Outliner reorder = faithful port of Ari slot-swap (`_list_num`/`_obj_at`/`_num_sort` via `cmds.reorder -relative`), grouped by parent (Maya only reorders siblings), DAG-only filter. Re-selects sorted objects at end.
- `app/ui/main_window.py` — TSL (`JUN_mod_tsl_qt_v01`, show_sort=False) + "Sort By" radio grid (World X/Y/Z, Name, Type; default World X) + "Reverse (descending)" checkbox + "Reorder in Outliner" checkbox (default ON) + Sort button + log. `on_sort` wraps in `undo_chunk`, rebuilds TSL as `ordered + missing`.

Verified the slot-swap by hand on 3 cases (ascending/full-reverse/partial) — correct. py_compile passes all files. Windows-safe.

**Icon made** (repo pattern = `icon/<tool>.svg` source + 32x32 `icon/<tool>.png`): coral decreasing sort-bars + light down-arrow on the standard dark rounded-rect (#2d2d30/#4a4a4f). PNG rendered via PIL 8x supersample→LANCZOS (no SVG renderer installed: cairosvg/svglib absent). Shelf dragDrop already points at `icon/A00360_SortTool.png`.

**Next:** user verifies in Maya (list joints/meshes/curves/clusters under various hierarchies, sort by each axis + name + type, toggle outliner checkbox) → then push Dnable/dev + WORKLOG + create guide doc `JUN_All/docs/A00360_SortTool.md` (none yet). NOTE: an unrelated untracked `A00350_ArrayCreator/` exists in the tree — do NOT stage it (git add the A00360 paths explicitly). See [[uuid-safe-rename-duplicate-names]], [[prefer-pyside-for-new-tools]], [[push-includes-tool-guide-docs]], [[worklog-maintenance]], [[ui-text-english-only]].
