---
name: wip-a00060-world-space-joint-pos
description: A00060_jointTool_V02 — Curve/Divide joint creation now uses world-space absolute positions (fixes wrong placement when objects are parented) (v01.03)
metadata: 
  node_type: memory
  type: project
  originSessionId: 746d699d-9d82-44da-b966-14caefd575fd
---

DONE (verified + pushed Dnable/dev, commit f09fb21), v01.03: A00060_jointTool_V02. Guide doc `JUN_All/docs/A00060_jointTool_V02.md` §6 added.

**Bug reported:** Match to Obj (Curve tab) and Make Joint Divided (Divide tab) created joints at the wrong spot when the source objects/curves live under a transformed hierarchy — positions weren't taken as world-space absolutes.

**Root causes found (3 spots) & fixes:**
- `app/core/divide_manager.py::curves_from_pairs` — used `cmds.xform(obj, q=True, translation=True)` = **object/local space**, so the between-curve (and divided joints) landed at local coords. Fix: add `ws=True` → world-space start/end.
- `app/core/curve_joint_manager.py::_joint_at_curve_point` — `pointPosition` already returns **world**, but the code ADDED the curve's world translation on top (`cp_pos[i] + curve_pos[i]`) → **double-counted** the offset whenever the curve wasn't at the origin / was in a hierarchy. Fix: use `pointPosition` result directly (removed the `+ curve_pos`), then `cmds.xform(jnt, ws=True, translation=pos)` to lock world pos. (Harmless no-op for Divide's origin curves.)
- `app/core/obj_joint_manager.py::_joint_at_obj` (Match to Obj) — query was already `ws=True`, but `cmds.joint(p=pos)` can parent the new joint under the previously-created chain joint; added `cmds.xform(jnt, ws=True, translation=pos)` right after creation to enforce world placement regardless of parenting. Defensive, no downside.

`aim_manager.py` already uses `ws=True` everywhere → no change. version 01.03 / 2026-07-08. py_compile passes.

**Next:** user verifies in Maya (parent objects/curves under a moved/rotated group, run Match to Obj + Make Joint Divided + joint-to-Crv → joints land on the objects' world positions) → then push Dnable/dev + WORKLOG + refresh guide doc if one exists (`JUN_All/docs/A00060*`). See [[push-includes-tool-guide-docs]], [[worklog-maintenance]], [[push-target-dnable-dev]].
