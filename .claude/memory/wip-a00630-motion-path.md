---
name: wip-a00630-motion-path
description: A00630_MotionPathEditor v01.00 - Blender Editable Motion Paths (GPL) re-implemented independently; bake parentMatrix only, curves evaluated directly; phase 1 done, GUI check pending, next = phase 1.5
metadata:
  type: project
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

Related: [[maya-time-context-traps]] · [[wip-a00380-quad-patch]] · [[mayapy-headless-verify]] · [[feedback-sliders-use-shared-style]]
