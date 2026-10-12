# Changelog — A00120_FKIK

All notable changes to this tool are documented here.

## [01.12] - 2026-10-12
### Fixed
- **Setup box is back to its v01.10 height.** v01.11 put the Manual / Auto radios on their own
  row and used the shared tsl widget (with its header) for the Auto list, which made the box
  58 px taller. The box is now one row - `[list] (Manual) (Auto) [Select Objects | Refresh]` -
  with both lists fixed at 50 px (plain `QListWidget` for the Auto rigs, tooltip instead of the
  `Rigs (by namespace)` title) and only the button that matches the mode visible.

## [01.11] - 2026-10-12
### Added
- **Setup > Manual / Auto.** Manual is the old flow (select the rig, `Select Objects`). Auto
  scans the scene **by namespace** (`app/core/fkik_scan.py`, `FKIKScanner.scan`) and lists every
  rig that can switch FK / IK in a `Rigs (by namespace)` list; `Refresh` scans again, picking a
  row loads its Targets / Followers. A namespace that holds several rigs is split per top node
  (`(root) | rigB_grp`). Rigs that fail the count check are logged as `[WARN] Skipped`.
- **`Dev Mode` menu** (right of Help) — the shared `JUN_mod_devMode_qt_v01`. Developers switch
  between the **Developer** view and the **Release (shared tool)** view; the release build has no
  menu and is fixed to the Release view.
  - Release view = Auto is the default setup mode, no Targets / Followers lists, no
    `Bake (Constraint)`, log collapsed (Shrink), no `Force Refresh`.
- **Progress popup on Bake IK / Bake FK** — the shared `JUN_mod_progress_qt_v01`; `FKIKMatcher.bake`
  got an optional `progress(done, total, message)` callback that fires per frame.
### Changed
- **Targets / Followers are collapsible** (`JUN_mod_collapsible_qt_v01`, collapsed by default).
  The window height follows the collapsed / expanded state (capped to the screen).
- **Search is hidden** — the group box and `on_search` stay in the code, only `setVisible(False)`.

## [01.10] - 2026-09-17
### Changed
- Menu bar is the shared `JUN_mod_menuBar_qt_v01` (Help > Copy Tool Name on every tool).

## [01.09] - 2026-09-16
### Changed
- Log is the shared `JUN_mod_log_qt_v01` (Expand / Shrink / Clear / Copy).

## [01.08] - 2026-08-05
### Changed
- **Bake range UI replaced with the shared time-range widget.** The hand-rolled
  `Start [QSpinBox][Get Current]  End [QSpinBox][Get Current]` row in Match / Bake is
  now `Framework.qt.JUN_mod_timeRange_qt` (`JUN_mod_timeRange_qt_v01`), the same
  widget A00110 / A00390 / A00410 use.
  - Adds **Get Sel Range** — fills Start and End from the first / last selected
    keyframe in one click.
  - Local helpers `_init_frame_range()` / `_set_current_frame()` /
    `_make_get_current_btn()` dropped; `_playback_range()` only supplies the initial
    values (current playback range, as before).
  - `on_bake()` reads `self.bake_range.values()`. Unlike a spin box the fields can be
    empty or non-numeric, so an invalid range now logs
    `[Warning] Enter a valid Start / End frame.` and does nothing.

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
