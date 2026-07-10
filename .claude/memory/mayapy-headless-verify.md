---
name: mayapy-headless-verify
description: Verify maya.cmds behavior headlessly with mayapy + maya.standalone before shipping a Maya tool
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2af83ce7-788e-4c2c-83e0-9ebc68b52132
---

`C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe <script.py>` runs maya.cmds headlessly
(`import maya.standalone; maya.standalone.initialize()`). Add `JUN_All` to `sys.path` and the
tool's `app/core/*` managers import and run directly — build a tiny scene, call the manager, assert.

**Why:** it caught a real bug that looked correct on paper — `setAttr` on
`blendShape.inputTarget[g].sculptTargetIndex` sets the value but never enables sculpt capture, so
edits silently hit the base mesh. Guessing from Maya's own .mel was wrong; running it settled it in
one shot. GUI-only calls (e.g. mel `updateBlendShapeEditHUD` → `setHUDBlendShapeEdit`) error
harmlessly in standalone.

**How to apply:** for any non-obvious maya.cmds semantics (which command actually mutates state,
what a query returns), write a throwaway mayapy script in the scratchpad and run it, rather than
reasoning from docs/mel. Then say plainly whether it was verified in real Maya too.

Related: [[wip-a00290-shape-editor-tab]]
