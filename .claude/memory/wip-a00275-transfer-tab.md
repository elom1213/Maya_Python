---
name: wip-a00275-transfer-tab
description: "A00275_skinTool_V01 v01.04 — Classic tab Engine(Kangaroo/Native) choice + new Transfer tab (many source meshes -> selected mesh/verts, Kangaroo-free, soft-falloff) — IMPLEMENTED, Maya test pending"
metadata: 
  node_type: memory
  type: project
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
---

A00275_skinTool_V01 v01.04 (IMPLEMENTED headless-verified, Maya UI test + push pending). Two adds:

1. **Classic tab gets an Engine radio (Kangaroo / Native)** like the Migrate tab. Native paths added to
   `SkinMigrateManager.move_joints_in_mesh(engine=)` and `transfer_meshes(engine=)`:
   `_move_joints_native` (maya.api column move on the selected mesh's skinCluster) and
   `_transfer_meshes_native` (rebind + `cmds.copySkinWeights`).

2. **New "Transfer" tab** (core `app/core/weight_transfer_manager.py`, `transfer_to_mesh`): mimics
   Kangaroo's SkinCluster>Transfer but **works WITHOUT Kangaroo**. Transfers from N source meshes (TSL)
   to the **currently-selected target mesh (or its selected vertices)**. Required feature = transfer to
   only the selected verts; soft-selection falloff respected.

**How it works (all measured with mayapy):**
- `cmds.copySkinWeights(surfaceAssociation="closestPoint")` does the heavy closest-point/barycentric
  sampling. **Selecting multiple source meshes + the target and calling copySkinWeights uses the
  per-vertex NEAREST source automatically** (verified: left verts→left src, right verts→right src).
- BUT copySkinWeights **ignores component selection — it always writes the whole mesh** (verified: 80
  unselected verts changed). So for partial/soft transfer: read `before` weights (maya.api bulk
  getWeights) → copySkinWeights whole mesh → read `after` → for selected verts blend
  `before + (after-before)*f` (f = soft falloff weight, 1.0 hard), non-selected restored to `before` →
  bulk `setWeights`. No vertex selection → leave the copy result (clean undo). Partial uses setWeights
  (undo is one step). Target skinCluster is created if missing / union of all source influences added
  (weight 0) so copy's name/closestJoint mapping lands.
- Soft weights via `cmds.softSelect(q,softSelectEnabled)` + `MGlobal.getRichSelection()` (same pattern
  as A00380). Selection parsed by `parse_target_selection()` (components → mesh+vtx ids+soft; whole mesh
  → ids=None).

Kangaroo plugin at `C:\Users\USER\Desktop\JP\0020_maya_plugin\0010_kangaroo` is read-only reference
(see [[kangaroo-plugin-external-readonly]]); the relevant funcs are `weights.transferSkinCluster` /
`intTransferSkinCluster` (numpy/barycentric — NOT copied, only used as UI/behavior reference).

Testing: Qt+maya.standalone crashes headless → core tested with real meshes via mayapy (single/multi
source, partial verts, soft falloff, Classic native move/transfer — all pass). UI not exercised.

Related: [[wip-a00275-skintool-bindpose]], [[kangaroo-plugin-external-readonly]], [[mayapy-headless-verify]],
[[push-only-when-asked]], [[ui-text-english-only]]
