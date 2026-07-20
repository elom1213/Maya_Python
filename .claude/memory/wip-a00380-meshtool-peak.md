---
name: wip-a00380-meshtool-peak
description: "A00380_MeshTool v01.00 Peak tab (inflate/shrink along normals, Houdini peak-like) — DONE, Maya-verified + pushed"
metadata: 
  node_type: memory
  type: project
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
---

A00380_MeshTool v01.00 — new in-Maya PySide tool (arch B). Tab 1 "Peak": inflates(+)/shrinks(-)
selected mesh/verts along their own vertex normals, like Houdini's peak node. Live slider preview,
Range (slider limit, lower = finer) + Step `-`/`+` nudges for micro control, Apply commits as one
Ctrl+Z. Options: angle-weighted normals, respect soft selection, auto-load on selection change.
Core in `app/core/peak_manager.py`; guide in `JUN_All/docs/A00380_MeshTool.md`.

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
