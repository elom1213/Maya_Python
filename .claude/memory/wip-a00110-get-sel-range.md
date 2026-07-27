---
name: wip-a00110-get-sel-range
description: A00110_animTool v01.35 — "Get Sel Range" button fills Start/End from selected keyframes' first/last frame (all range tabs)
metadata:
  node_type: memory
  type: project
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
---

A00110_animTool v01.35 (IMPLEMENTED, headless-verified, Maya UI test + push pending).

New **`Get Sel Range`** button next to the existing `Get Current` in every tab that has Start/End
(Move Keys · Stagger · Copy · Mirror · Bake · Follow). Unlike `Get Current` (fills ONE field with the
current frame), it finds the **first and last of the currently-selected keyframes** and fills **both**
Start and End (e.g. select a curve's keys 6~15 → Start=6, End=15).

Impl in `app/ui/main_window.py`:
- `_selected_key_range()` → `cmds.keyframe(query=True, selected=True)` returns times of ALL selected
  keys globally (across objects/attrs; no object arg needed), returns `(int min, int max)` or None.
- `_set_selected_key_range(le_start, le_end)` fills both; warns via `self.log` if no keys selected.
- `_make_get_selected_range_btn(le_start, le_end)` factory (label "Get Sel Range", tooltip). Same
  `lambda *_a` checked-bool absorption trick as `_make_get_current_btn` (see [[wip-a00110-fkik-bake-constraintfree]] era Get Current work).
- Bake tab: stored as `self.btn_bake_get_range`, added to the Custom-range enable/disable block
  (`_bake_update_range_mode`) alongside the get-current buttons.

Verified with mayapy: `selectKey(time=(6,15))` → range (6,15); no selection → None. Qt UI itself not
exercised (Qt+standalone crashes headless).

Related: [[wip-a00110-stagger-offset]], [[wip-a00110-graph-focus]], [[mayapy-headless-verify]],
[[ui-text-english-only]], [[push-only-when-asked]]
