---
name: wip-a00275-flood
description: A00275 v01.40 Weights > Flood — Kangaroo SkinCluster > Flood port that works with same-name joints (all full paths); two original bugs fixed (Blend ignored, Scale All = Value/n); GUI check pending
metadata:
  type: project
---

A00275_skinTool_V01 v01.40 (2026-11-19) — `Weights > Flood` (after Move). Core `app/core/weight_flood_manager.py`,
tab `app/ui/flood_tab.py`, tests `tests/test_weight_flood.py` (51, Kangaroo golden 19 cases) · `tests/test_flood_ui.py` (16).
**GUI check in real Maya still pending.**

**User's point:** the Kangaroo original errors when the scene has joints with the same name. Cause: it keys influences by
`fullPathName().split('|')[-1]` and calls `cmds.xform(shortName)` → "More than one object matches name". The port uses
full DAG paths everywhere (list `get_all_nodes()` = UUID → path, influence columns, closest-bone, addInfluence, `skinParent`).
Ambiguous names passed in by script are skipped with `[WARN]`, never `found[0]`. Move got the same guard (`_resolve_joints`,
`_project_joints`) — results unchanged (45/45).

**Deliberate differences from the original (tell the user if asked):** Blend is honoured (original never passes `fBlend`
except Distribute) · Scale All multiplies each joint by Value (original uses Value / joint count, and with Value 1 zeroes the
others). Rows with no other influence to take the rest keep sum < 1 like the original, with a `[WARN]`. No Kangaroo engine
option on this tab (it carries the bug). Subtract All not ported (dead branch in the original).

v01.41 : `Get Bound Joints` button on the Joints list (mesh = all bound joints, components = joints weighted there) -
the user expected selecting a mesh to list its joints; plain `Select Joints` only copies the selection.

v01.42 : `Add Influence` button - Get Bound Joints remembers the mesh(es) by UUID (`Mesh :` label); scene-selected joints
are added to that skinCluster with weight 0 (`skinCluster -e -addInfluence -weight 0`) and appended to the list.

Related: [[kangaroo-headless-golden-test]] · [[wip-a00275-move-joints]] · [[framework-tsl-attach-uuids]]
