---
name: wip-a00275-transfer-tab
description: "A00275_skinTool_V01 v01.07 — Classic Engine choice + Transfer tab (many source meshes -> ALL selected meshes/verts; Native soft-falloff + Kangaroo engine choice) — IMPLEMENTED, Maya test pending"
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

**v01.05**: Transfer tab also got an **Engine(Native/Kangaroo) radio** (user request, matching Classic/
Migrate). Kangaroo path = `ktw.transferSkinCluster(sFrom=sources, _pSelection=None (live selection =
target), iMode=2 closestPoint, bAutoCreateNewSkinCluster=(target has no skin))`. Component/partial
handling follows Kangaroo; the soft-falloff checkbox is Native-only (disabled when Kangaroo is picked).
Default = Native. Note: in this mayapy env `kangarooTabTools` imports but `report.report` is None so the
call errors — the tool catches it as `[Error]` (no crash); works in real Maya with Kangaroo Builder loaded.

**v01.07 (bug fix, user-reported): soft-selection on a COMBINED mesh — (a) `(kInvalidParameter): Object
is incompatible with this method` error, (b) transfer bled into disconnected-but-near shells that Volume
falloff picked up.** Fixes: `_soft_weights` matches the rich-selection component by **shape MObject node**
(`_shape_node`) instead of string paths (rich sel gives a SHAPE dag; string compares failed on combine/
rename) + try/except per component + out-of-range vtx guard. `_connected_island` restricts soft selection
to the connected shell of the HARD selection so disconnected near shells are left alone; it builds face-
vertex adjacency from **ONE `MFnMesh.getVertices()` bulk call** + Python BFS (no per-vertex iteration).
Partial transfer = copySkinWeights whole → maya.api bulk read before/after → selected verts blended
`before+(after-before)*f`, non-selected restored to before → **one bulk `setWeights`**.

**v01.07 REGRESSION FIX (same version, not yet pushed — user feedback on first v01.07 attempt):** the
first attempt used **shape full-path string** compare (still failed in real Maya → `_soft_weights`
returned empty → soft range ignored, only hard verts transferred = "same as no soft"), and a **per-vertex
`MItMeshVertex` island BFS + temp-duplicate `cmds.skinPercent`** partial (very slow). Reworked to the
node-compare + bulk-getVertices island + bulk-setWeights partial above. Verified headless: island excludes
shell B and is fast (0.007s on 3124-vert combine); graded falloff (f=1→full, 0.5→half, unsel→untouched);
soft partial transfer 0.055s. Tradeoff: bulk `setWeights` partial is FAST but **not granularly undoable**
(one Ctrl+Z may not fully revert partial) — accepted per user's speed priority. getRichSelection is empty
headless so the soft path is tested via a `_soft_weights` mock; user verifies real soft in Maya. NOTE:
couldn't reproduce the kInvalidParameter directly headless — fix inferred from the shape-name bug + guards.

**v01.06 (bug fix, user-reported): Transfer only hit ONE of several selected target meshes.** Root cause:
`parse_target_selection()` returned just the first mesh. Added `parse_target_selections()` (plural) that
groups the selection **by mesh** (whole-mesh → full transfer; verts on a mesh → partial on that mesh;
soft per mesh). Native now loops all targets (`_transfer_one_native` per mesh) inside ONE undo_chunk;
Kangaroo already handled multiple via `_pSelection=None`. Also fixed source-exclusion: TSL names (short)
vs `ls -l` (full path) mismatched so a co-selected source wasn't filtered → it transferred onto itself
and errored. Fix: `_mesh_transform` now normalizes to the **full DAG path** so the compare works.

Testing: Qt+maya.standalone crashes headless → core tested with real meshes via mayapy (single/multi
source, partial verts, soft falloff, Classic native move/transfer — all pass; Kangaroo branch routed
gracefully). UI not exercised.

Related: [[wip-a00275-skintool-bindpose]], [[kangaroo-plugin-external-readonly]], [[mayapy-headless-verify]],
[[push-only-when-asked]], [[ui-text-english-only]]
