# Changelog — A00330_NamingTool

## v01.01 (2026-07-03)
- Fix: `Naming Dynamics` failing with `RuntimeError: Invalid path ...` when the
  scene contains multiple objects sharing the same name (e.g. two `joint_02`
  under different roots). Renaming now resolves each node by UUID instead of by
  short name, so duplicate names in the scene no longer break the tool.
- Same UUID-based hardening applied to `Copy Name` and all `Quick Rename`
  actions (Front Insert / Change New / Last Add / -1 trim), which also renamed
  by ambiguous names before.

## v01.00 (2026-06-30)
- Initial Qt(PySide) port of legacy `JUN_PY_NamingTool_V03_04.py`.
  Tabs: Naming Dyn / Copy Name / Quick Rename.
