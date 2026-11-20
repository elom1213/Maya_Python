---
name: wip-a00630-motion-path
description: "A00630_MotionPathEditor v01.00~v01.04 - Blender Editable Motion Paths (GPL) re-implemented; bake parentMatrix only, curves evaluated directly; v01.04 speed graph + smooth brush (refit onto Maya Bezier, one undo per stroke); GUI check pending"
metadata:
  node_type: memory
  type: project
  originSessionId: 31a00341-3a05-453d-ac3e-36ac732d1b96
  modified: 2026-11-20T00:14:13.367Z
---

A00630_MotionPathEditor v01.00 (2026-11-19) — viewport motion path of objects / joints, drag keys on it to edit translate.
Plan `JUN_All/docs/plans/A00630_MotionPathEditor_plan.md` (phases, §10 results), guide `docs/A00630_MotionPathEditor.md`.
**GUI check (draw override, draggerContext, Graph Editor follow) still pending.** Next: phase 1.5 (frame drag = insert key
then move — user's Q4 choice, proportional editing, numeric input), then phase 2 (tangent handles, auto re-bake, timing).

**Licence:** reference add-on is GPL-3.0-or-later → user chose independent implementation; never copy its code.

**Design that matters (measured in mayapy):**
- Path point = `(c + T(f)) · parentMatrix(f)`, c = rotatePivot + rotatePivotTranslate (constant; = `xform -ws -rp`).
  Only `parentMatrix[0]` is baked via `MDGContext(t).makeCurrent()` + `plug.asMObject()`; T from `MFnAnimCurve.evaluate`.
  `currentTime(update=False)` + plug read returned stale values — rejected.
- Speed: bake ≈ Maya motion trail creation; edit redraw 0.002 s vs 0.15 s (~70-90x); drag update 3.4 ms @ 1,000 frames.
- Undo: live `MFnAnimCurve.setValue(.., change)` during drag; on release the plugin command `junMotionPathSetKeys`
  takes the `MAnimCurveChange` (draw_bridge.stage) → one Ctrl+Z; ensure_keys cmds sit in the same undoInfo chunk.
- Draw nodes via MDagModifier (out of undo), doNotWrite, deleted before save (else file gets `requires` plugin line).
- MAnimMessage curve-edited callbacks arrive on idle → never in mayapy; tests call `watcher.flush()`.
- v01.01: API 2.0 `M3dView.viewToWorld(x, y, MPoint, MVector)` fills OUT args (returns self) — v01.00 called it with 2 args
  and every drag failed in the GUI. `tests/test_edit_context.py` drives press/drag/release with a fake view of the same shape.
  Before trusting a GUI-only API call, print its `__doc__` in mayapy (signatures differ from API 1.0 habits).
- v01.01: Custom range = shared `JUN_mod_timeRange_qt_v01` (A00110's Get Current / Get Sel Range); Edit Path checked = `pin_style`
  light red, kept in sync with the real tool via `MEventMessage("ToolChanged")`.
- v01.02: `MEventMessage("ToolChanged")` fires while `currentCtx()` still names the OLD tool — judging at once unchecked the
  just-pressed Edit Path button. Defer the check with `evalDeferred`. In mayapy `evalDeferred` runs immediately, so tests
  replace it with a queue to get the GUI order.
- v01.03 anim layers: each layer stacks an `animBlendNodeAdditiveDL` on translate, `out = weightA*below + weightB*layer`
  (weights from layer.backgroundWeight / foregroundWeight). Final T is linear in the picked layer's value → exact solve.
  Path = combined motion, keys = picked layer. Baked layer weights with parentMatrix. Static layer axis → curve keyed at the
  layer's constant (setKeyframe -animLayer w/o value gives per-key values on override layers → bent curve).
- v01.03: undo of an edit that created a layer curve restores data but leaves stale evaluation down the blend chain →
  `junMotionPathDirty` marker command first in the chunk dgdirties node + blends on undo/redo. Tests must compare world
  motion after undo, not only curve keys (curve-only check missed it).
- Run tests with `mayapy -u` (pipe buffering + os._exit lost output before `_common.finish` flushed).
- v01.04 Speed tab (plan `docs/plans/A00630_MotionPathEditor_speed_graph_plan.md`, §9 G0 · §10 changes): speed graph + brush.
  **Maya anim curve = Bezier with handles (x·fps/3 frames, y/3 value)** from `getTangentXY` (x seconds, y internal units);
  non-weighted handle time is always segment/3 (Hermite, slope = y/x/fps). Golden < 1e-11 for 24/30/60 fps, cm/m, weighted.
  `setTangent(.., convertUnits=False)` writes raw XY; tangents stored single precision (~1e-7 after write); `addKey` new key
  tangents are (0,0); with tangent/weight lock on, writing one side changes the other → unlock, write, relock.
  Weighted key insert must be an exact de Casteljau split (time-ratio scaling broke the shape).
- v01.04 design: **one undo per stroke** (plan said one per session — Ctrl+Z goes to the viewport and would undo an
  unrelated earlier op). No drift: targets always from the session-start path, write only the difference
  (new target = current curve + L(new) − L(prev)); session invalidated by curve signature (`StrokeSession.valid`).
  Speed smooth = time warp on the original path (shape kept), arc length conserved per run between holds → holds stay put.
- Tolerance must be relative (0.1% of path size): fixed 0.01 cm needed 25 keys on a metre-unit scene.
- v01.05 (2026-11-20): user report "after a graph stroke, Ctrl+Z / Z does not bring the graph back" = graph scrub used
  `cmds.currentTime` (one undo entry per mouse move, see [[maya-time-context-traps]] 7) → `MAnimControl.setCurrentTime`.
  Stroke / curve drag / key-line drag / Smooth Range were already one undo each and the graph followed undo/redo (diagnosed
  headlessly). Regression test: stroke → scrub → one undo removes the stroke, graph = original, redo = stroke (old code fails 3).
  Same version: **graph key-line drag (move key in time) removed** — user: not needed. Left-drag on a key line scrubs; do not re-add.
- v01.06 (2026-11-20): Speed tab Frames `Custom` = shared `MOD_timeRange_qt_v01` (Start/End/Get Sel Range) → graph shows only
  [Start, End], clipped to the path; no overlap → message instead of a graph. Settings `graph_start` / `graph_end`.
- v01.07 (2026-11-20): stale plugin from an older tool version caused "no attribute 'junMotionPathDirty'" → ensure_plugin
  compares PLUGIN_VERSION (now "1.5", asked via command junMotionPathVersion) and reloads, see [[maya-loaded-plugin-stays-stale]]. **Bump PLUGIN_VERSION on any plugin edit.**
- v01.08 (2026-11-20): Acceleration graph smoothing = brush `Smooth Acceleration` (retime.AccelSmoother: pull toward a time-axis
  Gaussian average, no Taubin push-back; session MODE_ACCEL, refit tolerance x0.2 because position error's 2nd difference is accel
  noise). Auto-picked when Show = Acceleration. Lesson: Smooth Speed can *raise* acceleration at sharp corners (0.057 -> 0.197).
- Manipulator + falloff sub-plan (docs/plans/A00630_MotionPathEditor_manipulator_falloff_plan.md, 2026-11-20). User's requests:
  move/rotate gizmo for selected path points, `b`+drag falloff with weight colors, Edit Path button on Speed tab with live graph,
  graph [a,b] colors + Smooth Range = position smoothing. Decisions (user accepted): rotate = point positions around pivot (not rotate keys),
  falloff distance = frames along the path, own-drawn gizmo, preview while dragging / write on release.
  G0: deform = existing StrokeSession with target points (no new write code). GUI: `b` blocked via app event filter, mesh(kLineStrip) not x-ray
  ([[maya-vp2-xray-and-hotkey-filter]]). **v01.09 = G1** (frame-point selection, falloff UI/colors, b tap/drag; plugin 1.6). Dragging frame
  points / with falloff still only logs "next update" → **next = G2** (MODE_DEFORM + set_state, route in edit_context._press), then G3 gizmo, G4 Speed tab.
- v01.10 = G2: frame-point / falloff drag = StrokeSession MODE_DEFORM (preview while dragging, refit on release, one undo for many paths);
  keys only + falloff off = old DragSession. Anchor = press-pixel ray ∩ drag plane (else a still click wrote keys). Lines drawn in screen 2D
  (x-ray only works for points) — plugin 1.7. User GUI-confirmed (v01.09): points visible, radius text, softSelect untouched.
- v01.11 = G3 gizmo (core/gizmo.py shared by plugin draw + context pick; centre square follows "Drag in" because pressing a selected
  point always hits the centre; centre picked before axes; W/E eaten by the key filter). refit CurveSnap.evaluate vectorized
  (6,000-key curve release 986 -> 240 ms). User GUI-confirmed v01.10 ("잘 된다").
- Next: G4 Speed tab Edit Path button / live graph from manager.preview / [a,b] weight colors / Smooth Range with falloff mask.

Related: [[maya-time-context-traps]] · [[wip-a00380-quad-patch]] · [[mayapy-headless-verify]] · [[feedback-sliders-use-shared-style]]
