---
name: wip-a00275-skintool-bindpose
description: "A00275_skinTool_V01 v01.03 — A00270 features + Update Bind Pose tab (freeze current joint pose as new bind pose) — DONE, Maya-verified + pushed"
metadata: 
  node_type: memory
  type: project
  originSessionId: afb475d4-578e-4345-808d-b12d9e8308c2
---

A00275_skinTool_V01 — new in-Maya PySide tool (arch B). Copy of A00270_skinMigrate (Classic +
Migrate A->B tabs, A00270 kept as-is) plus a new **Bind Pose** tab that makes the current joint
pose the new bind pose. Two modes: **Keep current shape** (default; deformed shape becomes the new
rest, mesh doesn't visibly move) and **Snap mesh to rest shape** (bindPreMatrix only = same result
as Maya's Move Skinned Joints Tool). Core: `app/core/bind_pose_manager.py`; guide:
`JUN_All/docs/A00275_skinTool_V01.md`. DONE — Maya-verified on a real avatar + pushed.

**Maya has no native equivalent** (all measured with mayapy): `skinCluster -e -recacheBindMatrices`
does not change `bindPreMatrix` at all; `dagPose -reset` does not update the bind pose;
`Move Skinned Joints Tool` solves a different problem. So the tool does 3 steps:
1. `bindPreMatrix[i] = influence's current worldInverseMatrix`
2. (Keep mode) bake `skinCluster output − input` delta into the chain-head input shape
3. rebuild the `bindPose` dagPose node and reconnect it to `skinCluster.bindPose`
Step 2 works with blendShapes before OR after the skin because a blendShape adds static deltas
(linear: `f(orig+d) = f(orig)+d`).

**Traps hit for real (each shipped as a bug, then fixed):**
- `bindPreMatrix` indices must come from the `matrix[]` connections, NOT `enumerate(skinCluster -q
  -inf)`. Influence list order ≠ logical index; a rig with removed/re-added influences goes sparse
  (`[0,1,3,4,5,6]`) → matrices land in the wrong joint slots → **looks exactly like a double
  transform**. Simple test scenes pass by coincidence.
- Never bake with `MFnMesh.setPoints` — not undoable, so Ctrl+Z restores bindPreMatrix but leaves
  the baked shape → scene left inconsistent. Use ranged `setAttr` on `pnts`, **added to existing
  values** (a frozen `ty=2` commonly lives there as `(0,2,0)` on every vertex).
- Don't hardcode `input[0]`/`outputGeometry[0]`; find the index whose output reaches the target
  shape, else empty data → `(kInvalidParameter): Object is incompatible with this method`.
- Chain walk must handle **`groupParts`/`tweak`**, which expose a scalar `inputGeometry` (deformers
  expose `input[i].inputGeometry`). A real facial mesh had **13 chained groupParts** — the walk
  stopped at the first one → "shape NOT kept".
- A still-live blendShape target cancels the baked offset **in proportion to its weight**
  (measured: w=0.25/0.5/0.75/1.0 → error 0.103/0.220/0.352/0.498), so partial weights are silently
  slightly wrong. Update at neutral (weights 0) or delete targets to freeze deltas.
- Rebuilt `bindPose` node must inherit the original node name, else `bindPoseNN` piles up.
- **Locked (user) vertex normals snapped back to rest** while positions stayed put — the skin
  was rotating them via `deformUserNormals`. Fixed in **v01.29** by re-baking the changed locked
  normals onto the chain-head shape. See [[skincluster-deforms-user-normals]].
- `_mesh_from_plug` returned an `MFnMesh` built on a local `asMObject()` result -> garbage reads.
  See [[mplug-asmobject-lifetime]].

**v01.33 (2026-09-28) — `Update blendShape targets` (default ON, Keep mode only).** User asked first
whether "skin the target mesh with the same weights, pose it, use that as the target" fixes targets
looking wrong after an update with ROTATED joints. Measured: yes, exactly (0 error, all 3 skinning
methods); the old tool is off by ~the whole delta under rotation/scale, 0 under pure translation.
Skin is per-vertex affine, so `f(orig+d) = f(orig) + A_v d` → rewrite each pre-skin target delta as
`A_v d`. A_v comes from 3 skin evaluations (unit offsets written to head `pnts`, then the ORIGINAL
pnts values are written back — do not add/subtract, pnts is float). Measure with the blendShape
`envelope` at 0 so D is taken at neutral — this also removed the old "live target with non-zero weight
cancels the bake" limitation. User decision: live-connected targets → **edit the target mesh itself**
(`new = newInput + A(p − oldInput)`, origin=world via base/target world matrices). Post-skin
blendShapes untouched; other deformers between bs and skin → approximation warning. 25 checks.

**Design lesson worth repeating:** when a user reports a symptom you can't reproduce, make the tool
report its own reason — the summary line carries `shape NOT kept: <reason>` and a read-only
**Diagnose** button prints the deformer chain as actually connected. That one round-trip located
the groupParts cause immediately.

Related: [[mayapy-headless-verify]], [[undo-chunk-by-default]], [[wip-a00380-meshtool-peak]],
[[prefer-pyside-for-new-tools]], [[push-includes-tool-guide-docs]], [[ui-text-english-only]]
