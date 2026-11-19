---
name: framework-tsl-name-display
description: Shared TSL name_display option (2026-11-19) - Outliner Name (default) / Full Path drawn by a delegate, item text never changes; only A00275 opted in, rollout to all tools planned
metadata:
  type: project
---

Shared TSL `JUN_mod_tsl_qt_v01(name_display=True)` (2026-11-19) draws `A|dup` as `dup` (Outliner Name, default) and shows the
current full path as a tooltip; right-click `Show Names` switches Outliner Name / Full Path for **every opted-in list**, stored in
QSettings `JUN/tsl` `name_display`. Plan: `JUN_All/docs/plans/Framework_MOD_tsl_qt_name_display_plan.md`.

**Why a delegate, never the item text:** tools read the list text as node names (`get_all_items()` in 44 files, `item.text()` in
33 more places). Shortening the text to `dup` would hit the wrong node or raise when names clash. `displayText` + `helpEvent` only.

**State (user decisions):** same-name rows are told apart by tooltip only; phase 1 = A00275 only (11 lists, v01.44); default
Outliner Name; phase 2 (later) = all tools — flip the default, check non-node lists, custom delegates, viewZoom on a TSL (plan §5).

**How to apply:**
- New list in A00275 → pass `name_display=True`. Other tools: leave off until phase 2 is asked for.
- Shared filter (`MOD_filter_qt_v01`) matches the shown text via the view's delegate.
- Tests that touch the mode must save/restore the QSettings key (`Framework/tests/test_tsl_name_display.py` shows how).
- `Framework/tests/test_tab_fit_rollout.py` has 3 pre-existing A00620 failures unrelated to this (seen before the change too).

Related: [[wip-tsl-uuid-selection]] · [[framework-tsl-attach-uuids]] · [[wip-a00275-flood]] · [[framework-viewzoom-widget]]
