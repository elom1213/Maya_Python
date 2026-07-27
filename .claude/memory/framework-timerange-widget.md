---
name: framework-timerange-widget
description: Framework/qt/MOD_timeRange_qt_v01 (JUN_mod_timeRange_qt) — reusable Start/End time-range input widget (Get Current + Get Sel Range), promoted from A00110
metadata:
  node_type: memory
  type: project
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
---

`Framework/qt/MOD_timeRange_qt_v01.py`, class `JUN_mod_timeRange_qt_v01`, exposed as
`JUN_mod_timeRange_qt` via `Framework/qt/__init__.py` (like [[wip-tsl-uuid-selection]]'s JUN_mod_tsl_qt).
Reusable PySide widget for a **Start/End time-range row**:
`Start [QLineEdit][Get Current]  End [QLineEdit][Get Current]  [Get Sel Range]`.

- **Get Current** fills ONE field with `cmds.currentTime`. **Get Sel Range** fills BOTH from the
  first/last of currently-selected keyframes (`cmds.keyframe(q=True, sl=True)` min/max).
- maya.cmds is lazy (`_cmds()`), so it imports/constructs OUTSIDE Maya (and is unit-testable by
  monkeypatching module `_cmds`). English UI text; Korean comments. `log_callback` like the TSL widget.
- Ctor: `start_label/end_label`, `start_value/end_value`, `start_placeholder/end_placeholder`,
  `show_get_current=True`, `show_sel_range=True`, `min_value/max_value`, `log_callback`.
- API: `start()/end()` → int|None, `values()` → (s,e)|None, `set_start/set_end/set_range`, `clear()`,
  `set_inputs_enabled(bool)` (toggle edits+buttons, not labels — used by Bake Custom-range mode),
  `get_current_start/end()`, `selected_key_range()`, `get_selected_range()`. `changed` signal on edit/fill.
- **Exposes `start_edit` / `end_edit` (the internal QLineEdits)** so migrating tools keep their old
  `.text()/.setText()/.setValidator()/textChanged` references working — A00110 aliases
  `self.le_*_start = widget.start_edit`.

Promoted from A00110_animTool v01.36: its 6 range tabs (Move Keys/Stagger/Copy/Mirror/Bake/Follow) now
use this widget; the 5 inline helpers (`_make_get_current_btn`, `_selected_key_range`, etc.) were removed.
Verified: 21-check isolation test (Qt offscreen in mayapy WITHOUT maya.standalone — that combo does NOT
crash, unlike Qt+standalone; maya path tested via fake `_cmds`). A00110 module import + widget construct
via alias OK. **A00110 full-window Maya UI test still pending** (can't construct MainWindow headless:
needs Qt+cmds together = crash).

Related: [[wip-a00110-get-sel-range]], [[prefer-pyside-for-new-tools]], [[mayapy-headless-verify]],
[[ui-text-english-only]], [[push-only-when-asked]]
