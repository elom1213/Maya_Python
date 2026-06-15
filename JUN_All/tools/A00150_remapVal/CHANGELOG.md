# Changelog

## v01.04 (2026-06-15)
- **Slerp Ramp**: the controller's `{prefix}_interpolation` control attr is now an **enum** (`Linear` / `Smooth` / `Spline`, default **Linear**) instead of a `long` (0–2). The enum's internal values are `1` / `2` / `3`, matching the remapValue `value_Interp`, so it connects directly with no extra node. This also makes **Spline** selectable (the old `long` max of 2 could only reach Smooth) and removes the `none` (0) option that could disable interpolation by accident.
- UI: added an **Interpolation** combo box (Linear / Smooth / Spline) that sets the enum's default at build time; the build log now reports the chosen interpolation. Sine Wave mode is unchanged.
- Note: rigs already built with the old `long` attr are not auto-converted — `add_attr` reuses an existing attr, so rebuilding on the same controller keeps the old `long`. New builds create the enum.

## v01.02 (2026-06-12)
- Unified both build modes on a **controller attr → master remapValue → child remapValue** fan-out (matches the intended Maya setup where one master remapValue drives the rest).
- **Slerp Ramp**: the master now also connects its `outputMin`/`outputMax` to every child remapValue (previously only `value[0]`/`value[1]` were driven, so amplitude could not be set from one place). The values are exposed as new controller attrs `{prefix}_output_min` / `_output_max`; their defaults come from the UI **Out Min** / **Out Max** spin boxes.
- **Sine Wave**: added a master node `{prefix}_wave_master_MAP`. The controller range attrs now drive the master, and the master drives every child's Input/Output Min·Max and peak curve (`value[0~2]`). The peak curve is set once on the master instead of being duplicated per child; `inputValue` stays per-node (its animCurve output).
- The **master Input Max is now always (object count - 1)** in both modes, so the master input range is `0 .. N-1`, aligned with the animCurve output. The Sine Wave `_input_max` attr default is forced to N-1 (the UI In Max input is ignored).
- UI: **In Max** is now **read-only** and updates live to `Joints count - 1` whenever the Joints list changes (Select / Add / Del / Sort) — wired via the Joints list model signals. **Out Min** / **Out Max** are shared by both modes (Slerp Ramp passes them to `run_build`); tooltips updated. No layout change.

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
