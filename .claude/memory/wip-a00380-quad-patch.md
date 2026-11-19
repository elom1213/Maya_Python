---
name: wip-a00380-quad-patch
description: "A00380 v01.21 Quad Patch tab (hole -> quad grid, Edge Border/Faces/Extrude) — independent re-implementation because the reference script's licence forbids copying; polyAppendVertex commit; GUI check pending"
metadata:
  type: project
---

A00380_MeshTool v01.21 (2026-11-19) — **Quad Patch** tab (between Match and LOD). Core
`app/core/quad_patch.py`, tab `app/ui/quad_patch_tab.py`, test `tests/test_quad_patch.py` (40/40 mayapy +
offscreen UI). Guide §3-7 of `JUN_All/docs/A00380_MeshTool.md`. **GUI check in real Maya still pending.**

**Licence decision:** the reference `.ref/quadPatcher_v1.0.py` (Toshi Kosaka, 2021) says "do not copy,
distribute, or modify without permission". The user chose an **independent implementation** (idea only,
no code). Don't paste code from `.ref/` scripts into the repo — check their licence header first and ask.

**Why these choices (measured with mayapy):**
- Commit = one `polyAppendVertex(append=[int | (x,y,z)...], ch=True)` per face on the original shape, then
  `delete -ch` if the mesh had no history before. Keeps transform/shape/UUID. ~14 ms/face on a 90k mesh.
  Mesh with history (skin) keeps one node per face; new points unskinned (logged).
- Rejected: temp mesh `outMesh -> inMesh` connect + delete — **undo does not restore the old geometry**
  (the mesh keeps its last evaluated data).
- Don't `cmds.select` after commit — it enters the undo queue and breaks "one Ctrl+Z".
- Preview = API-created wireframe (`MDagModifier`, `MFnMesh.create/createInPlace`) → not in undo queue.
- Faces mode ref surface = in-memory `MFnMeshData` + `MMeshIntersector` (projection + `getUVAtPoint`).

Related: [[wip-a00380-meshtool-peak]] · [[mayapy-headless-verify]] · [[undo-chunk-by-default]]
