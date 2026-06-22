# Changelog — A00120_FKIK

All notable changes to this tool are documented here.

## [01.05] - 2026-06-22
### Fixed
- **Partial-range bake no longer deletes keys outside the baked range.** Baking a
  sub-range (e.g. frames 500–600 on a clip keyed 0–1000) wiped every key outside
  that range, leaving keys only inside `[start, end]`. Cause: each bake applies a
  temporary `parentConstraint` to the follower, which disconnects the existing
  `animCurve` from the plug (Maya inserts a `pairBlend`), so `bakeResults`'
  `preserveOutsideKeys=True` could no longer see — and therefore could not preserve
  — the original keys outside the bake range.
  - `bake()` now **snapshots the keys outside `[start, end]` before applying the
    constraint** (value + tangent type, plus angle/weight for `fixed` tangents) and
    **restores them after** the bake and constraint cleanup, so only the baked range
    is replaced and the rest of the animation is kept intact.
  - `bake_constraint()` got the same snapshot/restore guard (against the playback
    range) and now passes `preserveOutsideKeys=True` to `bakeSimulation`.
  - New helpers `FKIKMatcher._snapshot_outside_keys()` /
    `_restore_outside_keys()`; the restore pass runs inside `suspend_refresh()` to
    avoid a viewport redraw per re-keyed frame.

## [01.04] - 2026-06-19
### Fixed
- **Viewport freeze after bake** — the bake's refresh-suspend could leak when the
  temporary constraint `delete` failed, leaving the viewport frozen (Graph Editor
  edits not showing until you scrubbed frames). `bake()` now wraps the work in a
  `suspend_refresh()` context manager so the refresh state is always restored first
  and unconditionally; `bake_constraint()` moves its constraint cleanup into a
  `finally` block.
### Added
- **Force Refresh (Unfreeze Viewport)** button — clears a stuck global
  refresh-suspend and redraws once, for the rare case the viewport stays frozen.

## [01.03] - 2026-06-15
### Changed
- **Bake rewritten on native `bakeResults`.** Replaced the old per-frame Python loop
  (`currentTime` + `xform`) with a single `bakeResults` over `[start, end]` using a
  temporary `parentConstraint` per pair — tens of times faster on large ranges. World
  result is equivalent to the previous `match_transforms` bake. Verified on Maya 2023
  (Python 3.9).

## [01.00] - 2026-06-17
### Added
- Qt (PySide) UI rewrite of the legacy MEL/`maya.cmds` FKIK tool
  (`PY_JUN_makeUI_FKIKTool`), running inside Maya via the shared `Framework.qt`
  window. Drag-and-drop install through `__dragDrop_A00120.py`.
- **Setup** — select rig controls and auto-resolve Targets / Followers.
- **Limb** filters (Arm L/R, Leg L/R) to scope which pairs are matched/baked.
- **Targets / Followers** reusable list widgets (Select / Add / Del / Up / Down /
  Sort), shared with `A00140_ConnectClosest`.
- **Search** by token (with Invert) to select matching list items in the scene.
- **Match IK / Match FK** (single-frame pose match) and **Bake IK / Bake FK**
  (range bake) plus **Bake (Constraint)** for a constraint-driven full-range bake.
