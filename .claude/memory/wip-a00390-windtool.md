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

**v01.08 — per-driver global timing offset `windPhaseOffset`.** New driver attr (`DRIVER_PHASE_OFFSET`)
shifts the WHOLE driver's phase: `_wire_group` now computes a shared `base = windPhaseTime -
windPhaseOffset` (plusMinusAverage `<drv>_phaseBase`) and every joint uses `base - i*windOffset`. Different
values per driver ⇒ different sway timing — the point is Bone Root mode where each root had identical
timing. UI **Node Offset** field (node-only) → `apply_wind(node_offset=...)` → `_apply_nodes` sets driver k's
`windPhaseOffset = k*node_offset` (auto-stagger roots; 0 = all same = old behavior; user can then edit each
driver's windPhaseOffset). mayapy-verified: windPhaseOffset=3 shifts peak t=3→t=6; root A/B/C get 0/3/6 →
peaks t=3/6/9 (distinct). Note: `windOffset`=per-joint step within a chain vs `windPhaseOffset`=whole-driver.

**v01.07 — windSpeed is fully auto & correct via an integrating EXPRESSION.** v01.06's live
`time*windSpeed` mult reversed again when windSpeed was KEYED (animated 0.25→0.05) — same phase-reversal
(speed must be the time-integral, not a product). Fix: `windPhaseTime` is now driven by a MEL
**expression** (`_make_phase_expression`, node `<drv>_windInteg`, `alwaysEvaluate`) computing
`startFrame + ∫_start^frame windSpeed dt` — trapezoidal over integer frames PLUS the fractional remainder
of the current frame (needed or sub-frame times like t=1.5 undershoot: integer-only integration gave 34.64
instead of 40). Samples windSpeed via `getAttr -time` (stateless ⇒ scrub-safe). So changing windSpeed by
VALUE **or by KEYS** updates instantly with NO button and NO reversal (monotonic). windSpeed=1 ⇒
windPhaseTime=frame (matches curve mode). Removed the Apply Speed button + `bake_speed`/`_bake_phase_time`/
`_disconnect_phase_input`. Perf caveat: expression walks start→frame each eval (O(frames) per driver per
frame). mayapy-verified: keyed 0.25→0.05 monotonic + auto + live key-edit; value tweaks live; 0=frozen;
fractional t=1.5 speed2 = 40.

**v01.06 — windSpeed value changes are LIVE (no Apply Speed needed).** `windPhaseTime` is now driven by a
live **`time1.outTime * windSpeed`** multDoubleLinear connection (`_connect_live_phase`, node
`<drv>_phaseTime`) by default, so tweaking the windSpeed VALUE updates speed instantly (constant speed:
multiply == integral, mathematically correct; 0=frozen). **Apply Speed (bake_speed) is now only for KEYED
(time-varying) windSpeed** — multiply reverses on ramps, so it disconnects the live mult
(`_disconnect_phase_input`, deletes the `_phaseTime` mult) and bakes the integral animCurve. So: constant
value → live; keyed profile → click Apply Speed. mayapy-verified: setAttr windSpeed=2 (no bake) → t=1.5
peak live, windSpeed=0 → frozen, keyed+bake_speed → monotonic no-reversal.

**v01.05 — Node speed = `windSpeed` (value=speed) + integrated `windPhaseTime`.** v01.04's `windTime`
(a time VALUE) froze the anim when held constant (user: "constant value should keep playing"). Now the
driver has **`windSpeed`** (value = speed, 1=normal, default from Speed field) and an internal
**`windPhaseTime`** = the time-integral of windSpeed, baked as a per-frame animCurve (`_bake_phase_time`,
trapezoidal). Start value = minf so speed 1 ⇒ phaseTime = frame (same phase as curve mode — earlier bug:
starting at 0 shifted phase by minf → 34.64 instead of 40). Net reads windPhaseTime. **Constant windSpeed
keeps playing** (linear phaseTime), **varying windSpeed = correct speed with NO reversal** (monotonic
integral). windSpeed is live only after re-baking: **`bake_speed(drivers=None)`** (public) re-integrates —
UI **"Apply Speed"** button (node-only) runs it on selected wind drivers else all `*_windDriver*`. So:
constant speed instant; key windSpeed → click Apply Speed. (time*speed reverses on ramps; windTime freezes
when constant; windSpeed+integral fixes both.) `DRIVER_SPEED="windSpeed"`, `DRIVER_PHASE="windPhaseTime"`.

**v01.04 — Node speed fix: `windSpeed` multiplier → `windTime` retime.** v01.03's clock was
`time * windSpeed`; keying windSpeed to vary speed gave instantaneous frequency
`speed + time*(dspeed/dt)`, so on a speed RAMP-DOWN the phase goes BACKWARD (sway reverses) and returns
misaligned — user-reported. Fix: driver now has a **`windTime`** attr (the phase clock), keyed over the
playback range with slope = speed (`windTime(f)=f*speed`, linear tangents + linear infinity). The net
wires `(windTime - i*offset)/period → sineLUT → *amplitude` (the shared `time*speed` mult node is gone).
**Retiming the windTime curve = varying playback speed correctly** (slope = speed; time-warp = phase
integral, so monotonic ⇒ no reversal). The Speed UI field now sets windTime's initial slope. mayapy proof:
`phase=time*speed` gives 19 reversal frames on a 1→0.2→1 speed ramp; `windTime=∫speed` gives 0
(monotonic). `DRIVER_PARAMS=(windPeriod,windAmplitude,windOffset)`, `DRIVER_TIME="windTime"`.

**v01.03 — Curve / Node output radio:** `apply_wind(..., output=OUTPUT_CURVE|OUTPUT_NODE, speed=1.0)`.
**curve** (default) = bake keys (old path, now `_apply_curve`). **node** = build a **null (spaceLocator)
driver** per group with keyable attrs `windPeriod/windAmplitude/windOffset/windSpeed`, wired to each joint
via nodes so the sine is reproduced LIVE:
`value = windAmplitude * sineLUT((time*windSpeed - i*windOffset)/windPeriod)`. Editing the attrs updates
the anim in real time; keying `windSpeed` controls playback speed per frame. **Bone Chain → 1 driver;
Bone Root → one driver per root** (`_resolve_groups` now returns per-driver groups; curve flattens them).
Nodes per joint: multDoubleLinear(offset*i, skip if i=0) → plusMinusAverage(subtract) → multiplyDivide
(÷period) → **sine LUT** → multDoubleLinear(×amplitude) → joint.attr (existing key/connection cleared
first). Shared per driver: multDoubleLinear(time*speed).
**sine LUT = `animCurveUU`** with 17 samples of sin(2π u) over u∈[0,1], spline tangents, **preInfinity/
postInfinity = 3** for endless cycle. KEY GOTCHA (mayapy-verified): `cmds.setInfinity(curveNode, ...)`
does NOT work on animCurveUU (query returns None, enum stays 0); must **setAttr .preInfinity/.postInfinity
= 3** (enum 2 also failed; 3 works, and endpoints both 0 so no cycle drift). Avoids the Maya-2023 no-sin-
node problem entirely (A00170 Remap idea). Each joint needs its own LUT copy (duplicated from a per-driver
template that's deleted after). UI: Output radio + Speed spinbox (node-only); `_on_output_changed` disables
range/clear/keep-zero in node mode and speed in curve mode, and toggles button label
(Apply Wind Keys / Build Wind Node). Re-building node output orphans the previous driver network
(disconnected, not deleted). mayapy-verified: chain 1 driver / root N drivers, live attr edits (amp/period/
offset/speed) all change eval, cycle repeats, per-root offset reset.

**v01.02 — Bone Chain / Bone Root mode radio:** `apply_wind(..., mode=MODE_CHAIN|MODE_ROOT)`.
**chain** (default, old behavior) = listed joints are ONE chain, offset index = list order.
**root** = each listed joint is a chain ROOT; `_resolve_targets` expands it via `_chain_from_root` (BFS,
`listRelatives type="joint" fullPath`) to (joint, depth) and keys every descendant with **offset index =
depth from root** (offset resets per root; same-depth branch siblings share offset; joints seen under an
earlier root are deduped). `_resolve_targets` returns (pairs, missing); apply loops pairs. Message reports
"root mode: N key(s) on M joint(s) from R root(s)". mayapy-verified: rootA chain depths 0/1/2 → offset
0/10/20, rootB resets, branch leaves same depth = same phase, chain mode still ignores descendants.

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
