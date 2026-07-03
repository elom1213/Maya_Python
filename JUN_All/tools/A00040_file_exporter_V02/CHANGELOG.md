# Changelog — A00040_file_exporter_V02

## v02.01 (2026-07-03)
- Fix: Type Filter now also affects nodes **inside groups**. Previously an
  excluded type (e.g. Mesh) was only skipped when the set member itself was that
  type; meshes nested under a group member were still exported. Now each member's
  whole hierarchy is scanned, and excluded-type nodes are temporarily unparented
  out during export, then restored (UUID-based). So unchecking Mesh drops meshes
  at any depth while keeping the group and other types.

## v02.00 (2026-07-03)
- Qt(PySide) rework of legacy `A00040_file_exporter` (maya.cmds UI).
  - Logic (`app/core/export_ops.py`) separated from UI (`app/ui/main_window.py`).
  - Ported: export path browse, Set's Name / File name lists, token naming
    (Custom / Set's Name modes), per-set FBX export with unparent → export →
    reparent. Reparent is now UUID-based, so duplicate scene names are safe.
  - Reuses the original A00040 icon.
- NEW **Type Filter** dropdown: check/uncheck node types to include/exclude in
  the export. Ships with `Mesh` and `Joint`; other types (curve, nurbs, ...) are
  always included. Unchecking `Mesh` while keeping `Joint` exports every set
  member except meshes. Extensible via `core.FILTER_TYPES` + `_TYPE_MATCHERS`.
