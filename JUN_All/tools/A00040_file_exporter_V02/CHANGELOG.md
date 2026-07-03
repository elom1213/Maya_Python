# Changelog — A00040_file_exporter_V02

## v02.05 (2026-07-03)
- Fix/rediagnose: excluded meshes could stay in the FBX not because they were
  *referenced*, but because their transforms are locked/connected/constrained
  (common for rigged meshes), which makes `parent -world` fail. The v02.04 code
  mislabeled this as "referenced".
  - Shape-based excluded types (mesh, ...) are now excluded by flagging their
    shapes `intermediateObject` as the **primary** method — no reparenting, so it
    is immune to locked/connected/referenced/namespace situations. Only shapeless
    types (joint) still use unparent.
  - The leftover warning no longer says "referenced"; it now reads "no shape to
    hide and cannot be unparented".
  - Note: excluded descendant meshes leave an empty transform (null) in the FBX
    since only the shape is hidden.

## v02.04 (2026-07-03)
- Fix: excluded meshes that are **referenced** (nested under a group) stayed in
  the FBX (previously reported as `[WARN] could not exclude ... still in FBX`),
  because referenced nodes can't be unparented out of the hierarchy. Such nodes
  now have their matching shapes flagged `intermediateObject` during export (FBX
  skips intermediate shapes), then restored — so referenced meshes are excluded
  without reparenting. Only shapeless excluded types (e.g. a referenced joint)
  remain in the `could not exclude` warning.

## v02.03 (2026-07-03)
- NEW **Move to scene root** checkbox (Export section, on by default).
  - On (default): each object is exported at the scene root (parents removed) —
    `grp>joint_01` becomes `joint_01` (previous behavior).
  - Off: the current scene hierarchy is kept — `grp>joint_01` stays
    `grp>joint_01` (export in place; ancestors preserved, sibling branches not).
  - Type filter (excluding mesh/joint at any depth) works in both modes.

## v02.02 (2026-07-03)
- Fix: exporting a set that contains **referenced objects** crashed with
  `Referenced objects parented to referenced objects may not be reparented`
  (the move-to-world step is forbidden for referenced-under-referenced nodes).
  The unparent step is now guarded: nodes that cannot be moved to world are
  exported in place and not restored. Handles scenes where reference namespaces
  create same-named objects (`Test` + `namespace:Test`).
- Excluded-type nodes that cannot be unparented (referenced) are reported with a
  `[WARN] could not exclude ... still in FBX` log line instead of failing.

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
