---
name: wip-a00145-constraint-transfer
description: "A00145_RigConnect Constrain tab — Constraint Transfer (move an existing constraint onto a different object, same settings, MO kept)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 69869261-0a63-4176-a92b-1d8fb4705fb7
---

DONE (Maya-verified + pushed to Dnable_repo/dev): A00145_RigConnect v01.14 — new **Constraint Transfer** collapsible box (4th section) in the **Constrain** tab (after Group Create), default collapsed.

**What:** move an already-applied constraint so it drives a DIFFERENT object. Left TSL `Constraints` = constraint nodes (or transforms carrying constraints — auto-expanded via `listRelatives(type='constraint')`). Right TSL `Apply To` = new driven objects. On run: for ANY constraint type, delete the original and re-create the SAME constraint (type, targets, per-target weights, aim/up/worldUp for aim, parent/orient interpType) on the right object. **Maintain Offset guaranteed**: new constraint always made with `maintainOffset=True` (types that don't support MO retry without it), and the old driven's world matrix is restored after delete — so BOTH old and new object keep world pos/rot across the command. All **UUID-based** (constraint/targets/driven/new objects held by UUID; dup names safe) per [[uuid-safe-rename-duplicate-names]].

**Mapping:** right count 1 → all constraints go to that one object; equal counts → index 1:1; else min + warning.

**How** (`app/core/constraint_transfer_manager.py`, `transfer_constraints(constraint_names, object_names)`): `_read_constraint` uses `cmds.nodeType` → `getattr(cmds, ctype)`, `targetList`/`weightAliasList`(+getAttr) queries, driven = constraint node's parent transform, `_read_aim` for aimVector/upVector/worldUpVector/worldUpType/worldUpObject, interpType via getAttr. `_recreate` builds `cmd(*target_paths, new_driven, maintainOffset=True, **aimKw)`; on RuntimeError/TypeError retries without MO; reapplies weights by new weightAliasList order + interpType. Order per pair: **create new first (original still alive) → delete original → restore original driven world matrix** (skipped if driven is itself a target obj). Created constraints captured by UUID right after creation. UI wraps in `_run` (undo chunk).

**Files:** new `app/core/constraint_transfer_manager.py`; wired into `app/core/__init__.py`, `app/ui/main_window.py` (`_build_constraint_transfer_box`, `on_transfer_constraint`, import `cxfer_mgr`, added to `_build_constrain_tab`). version 01.14, docs `JUN_All/docs/A00145_RigConnect.md` (Constrain → Constraint Transfer). No CHANGELOG file in this tool. See [[push-includes-tool-guide-docs]], [[wip-a00145-group-create]] (sibling Group Create box). Push target [[push-target-dnable-dev]].
