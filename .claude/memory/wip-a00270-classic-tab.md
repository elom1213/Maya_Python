---
name: wip-a00270-classic-tab
description: A00270_skinMigrate v01.01 two-tab port of legacy move_skinWeightTool — Classic tab added
metadata: 
  node_type: memory
  type: project
  originSessionId: a2139496-621a-46ed-9eb8-f7e7c6c794a6
---

A00270_skinMigrate v01.01 — IMPLEMENTED (Maya test + push pending).

Ported legacy `_archive/.../JUN_PY_move_skinWeightTool_v01_04.py` (which uses external
`import kangarooTabTools.weights`) into A00270 as **two tabs**:

- **Tab 1 "Classic"** — faithful port of the legacy 2-button UI: `From`/`To` TSLs + Transfer Mode combo +
  buttons `Joints to Joints (single mesh)` (Kangaroo `moveSkinClusterWeights` on current selection) and
  `Meshes to Meshes` (Kangaroo `transferSkinCluster`, index-paired loop).
- **Tab 2 "Migrate A -> B"** — the pre-existing v01.00 unified Transfer+Move migration, unchanged.

Core (`SkinMigrateManager`): added `move_joints_in_mesh` / `transfer_meshes`; factored Kangaroo lazy import
into `_import_kangaroo()` helper (returns module or raises with a load-the-plugin message). Shared log moved
below the QTabWidget so both tabs write to it.

Kangaroo is the [[kangaroo-plugin-external-readonly]] 3rd-party plugin — handled via lazy import, never modified.
Updated: version.py 01.01, CHANGELOG, JUN_All/docs/A00270_skinMigrate.md (see [[push-includes-tool-guide-docs]]).
