---
name: wip-a00390-windtool
description: A00390_WindTool (new) v01.00 — keys a bone chain with a sine wave (wind sway); per-joint fractional-frame offset; core mayapy-verified, Maya UI test pending
metadata:
  node_type: memory
  type: project
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
---

New in-Maya PySide tool `tools/A00390_WindTool/` (arch A, cloned from A00360_SortTool skeleton).
Keys a listed bone chain with a sine periodic curve to fake **wind sway**. v01.00
(core mayapy-verified; Maya UI test + push pending).

**Wave:** per joint `i` (list order), `value(t) = amplitude * sin(2π(t - i*offset)/period)`.
Keys land **every quarter period** (grid `quarter = period/4`) → values `0, +A, 0, -A, …` via
`_SIN_QUARTER=(0,1,0,-1)` indexed by `n % 4` (Python modulo handles negative grid so the wave is
continuous even when the range starts before phase 0). **spline tangents** give the sine-like shape.
Fractional `quarter` → **fractional-frame keys** (period 10 → 2.5 max / 7.5 min). Per-joint `offset`
is a **float** (unlike A00110 Stagger's integer).

**v01.01 — drop interior zero-crossing keys (smoother curve):** the 0-value keys between extrema (every
half period, e.g. 6·12·18…f for period 12) made the spline flatten/kink at the crossings. Now
`skip_zero_crossings=True` (default) keeps only the extrema (±A) and adds **anchor keys at exactly
start/end** (their true sine value) so the curve stays bounded to the range. UI checkbox
`Keep zero-crossing keys` (default OFF) restores the all-quarter behavior. `_key_times_values` returns a
sorted `{time:value}` dict so a boundary landing on a grid extremum isn't duplicated.

Core `app/core/wind_manager.py`: `apply_wind(joints, attr, start, end, period, amplitude, offset,
clear_range=True, tangent="spline")`; `AXES = rotate/translate X/Y/Z`; key times `round(shift+n*quarter,5)`;
`cutKey` clears the range first when clear_range. UI `app/ui/main_window.py`: TSL(`JUN_mod_tsl_qt`,
get_all_nodes → UUID-resolved) + `JUN_mod_timeRange_qt` + Axis combo + Period/Amplitude/Offset
QDoubleSpinBox + Clear checkbox; Apply wrapped in `undo_chunk`. WINDOW_OBJECT_NAME
`JUN_A00390_WindTool_window`; theme coral_dark; icon SVG→PNG (QtSvg offscreen render).

**mayapy-verified** (test_wind.py): user's exact example (rotateX 0~100 p12 a40 o10 → jnt_01 3=40/9=-40/
0,6,12=0, repeats every 12; jnt_02 +10f shifted; jnt_03 +20f), fractional period 10 → 2.5/7.5,
fractional offset 2.5, re-apply doesn't stack keys, spline tangents. NOTE: Maya stores angle keys in
RADIANS → 30° round-trips as 29.9999996 (not a bug; all rotation-key tools do this). MainWindow can't be
constructed headless (Qt+cmds together crash) — module import + both Framework widgets verified separately.

First consumer of [[framework-timerange-widget]] besides A00110. Related: [[prefer-pyside-for-new-tools]],
[[wip-tsl-uuid-selection]], [[mayapy-headless-verify]], [[undo-chunk-by-default]], [[ui-text-english-only]],
[[push-only-when-asked]], [[push-includes-tool-guide-docs]].
