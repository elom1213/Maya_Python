---
name: wip-a00290-shape-editor-tab
description: "A00290_BSTool v01.02 Shape Editor tab — replaces Maya's Shape Editor Edit button via sculptTargetIndex"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2af83ce7-788e-4c2c-83e0-9ebc68b52132
---

A00290_BSTool v01.02 — new "Shape Editor" tab (tab 1). DONE (Maya-verified + pushed, 2026-07-10).

Replaces Maya's built-in Shape Editor: lists every blendShape target from `aliasAttr` (so targets
Maya's tree hides are still editable) with a per-target `Edit` toggle + weight spinbox.

**Why:** Maya's Shape Editor sometimes doesn't expose a target, so there's no Edit button and the
user can't sculpt it.

**How to apply:** Edit ON/OFF = `cmds.sculptTarget(bs, e=True, target=<weightIdx|-1>)`.
WRITING `<bs>.inputTarget[g].sculptTargetIndex` with `setAttr` does NOT work — it only changes the
value; the deformer never intercepts vertex edits, so sculpting lands in the base shape's tweak
(`.pnts`) and the ORIGINAL mesh is modified. Read the attr, write via the command.
(Verified empirically with `Maya2024/bin/mayapy.exe` + maya.standalone — a fast way to test
maya.cmds behavior headlessly from this repo.)
Core logic in `app/core/shape_editor_manager.py` (`ShapeEditorManager`). On enter it forces
weight=1.0 (backs up previous), envelope=1.0, selects base mesh, calls mel `updateBlendShapeEditHUD`;
on exit restores weight. One target per node. Window close exits all edit modes.

Related: [[ui-text-english-only]], [[push-includes-tool-guide-docs]]
