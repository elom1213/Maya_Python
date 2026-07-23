---
name: wip-a00380-meshtool-peak
description: "A00380_MeshTool Peak tab (inflate/shrink along normals, Houdini peak-like); v01.04 removed Apply/Reset (slider settle auto-commits) + v01.05 slider groove style — IMPLEMENTED (Maya UI test pending)"
metadata: 
  node_type: memory
  type: project
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
---

A00380_MeshTool v01.00 — new in-Maya PySide tool (arch B). Tab 1 "Peak": inflates(+)/shrinks(-)
selected mesh/verts along their own vertex normals, like Houdini's peak node. Live slider preview,
Range (slider limit, lower = finer) + Step `-`/`+` nudges for micro control. Options: angle-weighted
normals, respect soft selection, auto-load on selection change.
Core in `app/core/peak_manager.py`; guide in `JUN_All/docs/A00380_MeshTool.md`.

**v01.04 (IMPLEMENTED, Maya UI test pending, per user request): removed the Apply and Reset buttons.**
Now the slider adjustment IS the final result — `commit_stroke()` (extracted from old `on_apply`) is
called on `sliderReleased` / spinbox `editingFinished` / nudge ±; it commits the current amount
(undoable), then resets amount to 0 and re-snapshots so strokes accumulate. Model = drag shows live
preview (undo-disabled), releasing bakes it as one Ctrl+Z. `0` button zeroes the offset; Ctrl+Z undoes
a stroke. Core `peak_manager.commit()` unchanged (already restore→write→re-snapshot). Core flow
verified headless (preview→commit repeated accumulates; undo per stroke). UI itself not run
(Qt+maya.standalone crashes headless).

**v01.05 (IMPLEMENTED, Maya UI test pending): gave both sliders (Peak + Match) a `SLIDER_STYLE`** (no
theme qss styles QSlider so the groove blended into the dark bg — only the handle showed). Same
approach as A00290's SLIDER_STYLE but colored for A00380's **coral_dark** theme (accent #d08778, track
#383534, handle #efcabf). Peak slider is bipolar so groove is a uniform bar (sub/add-page same color,
no directional fill) + TicksBelow(interval=SLIDER_TICKS) marks center 0 and both ends. Verified by
pure-PySide render (groove visible; no maya needed for styling render).

Status: DONE — core verified headless via mayapy (34 checks pass, incl. undo/redo, history +
skinned meshes, existing tweaks, multi-mesh, soft select, undo_chunk combo), UI confirmed working
in Maya by the user, pushed to Dnable_repo/dev. Note the UI can't be driven headlessly: plain
`QWidget()` crashes mayapy standalone (exit 127), so Qt-side changes always need a Maya check.

Speed (19,462 verts, measured): `cmds.xform` per-vertex loop ~7.2s (= Maya's native
"Move tool axis=normal" path the user found slow) vs ranged `setAttr` ~0.10s, ~70x faster.

**Why it writes `shape.pnts` via ranged `setAttr` only** (all four learned the hard way with mayapy):
1. `MFnMesh.setPoints` (vrts) is 5x faster for preview BUT wipes existing tweaks, so a later
   `setAttr` records the wiped state as its undo baseline → Ctrl+Z after two Applies unwinds both.
2. `MPlug.setFloat` on `pnts` silently does nothing on a mesh whose `pnts` array is empty
   (the common case); a `cmds.setAttr` must trigger evaluation first.
3. Preview must run inside `undoInfo(stateWithoutFlush=False)` — plain `state=False` **flushes the
   whole undo history**.
4. commit must `restore()` to snapshot values *before* the real `setAttr`, because `setAttr` takes
   its undo baseline from the value live at execution time.

Also: `getAttr("<shape>.pnts")` whole-array fails with "compound with mixed type elements";
read via MPlug `getExistingArrayAttributeIndices` instead (0.02s on 19k). Per-index `setAttr`
is 6.8s on 19k — always chunk into contiguous runs.

Related: [[undo-chunk-by-default]], [[mayapy-headless-verify]], [[prefer-pyside-for-new-tools]],
[[push-includes-tool-guide-docs]], [[ui-text-english-only]]
