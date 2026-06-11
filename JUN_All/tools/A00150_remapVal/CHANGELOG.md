# Changelog

## v01.01 (2026-06-11)
- Added a second build mode **Sine Wave** (`build_sine_wave` / `run_build_wave`); the original Slerp Ramp build is unchanged.
- Per object it creates a `plusMinusAverage -> animCurveUU -> remapValue` chain that propagates a phase-offset sine wave:
  - `plusMinusAverage.input1D[1]` = object index (0, 1, 2, …) for the per-object phase offset; `input1D[0]` is the shared Driver Attr.
  - `animCurveUU`: keys `(0,0)`..`(N-1,N-1)` Linear, Pre/Post Infinity = **Constant**.
  - `remapValue`: value curve is a 3-key spline peak `(0,0)(0.5,1)(1,0)`; its Input/Output Min·Max are connected from controller attrs (below).
- The remapValue ranges are exposed on the Main Controller as `{prefix}_input_min` / `_input_max` / `_output_min` / `_output_max` (double) and **connected** to every remapValue node, so they can be tuned live after build (`_output_max` = amplitude). `In Max` 0 defaults to object count - 1.
- New UI: **Driver Attr** field (custom keyable attr added to the Main Controller), a **Range** row (In Min / In Max / Out Min / Out Max — defaults for the controller range attrs), and a second **Build (Sine Wave)** button. Build buttons renamed to clarify the two modes.

## v01.00 (2026-06-11)
- Initial release. PySide UI for `sample_01.py`'s `build_slerp_ramp` (remapValue-based interpolation).
- Inputs: Main Controller (QLineEdit + Get), Prefix (QLineEdit), Joints list and Attributes list (reusable `JUN_mod_tsl_qt_v01`).
- "List Attributes" fills the attribute list from the first joint's keyable attributes; Attribute Search filter.
- Build wraps the whole node creation in a single undo chunk; input validation + read-only log; Help > About menu.
