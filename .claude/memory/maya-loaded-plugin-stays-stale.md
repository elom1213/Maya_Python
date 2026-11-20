---
name: maya-loaded-plugin-stays-stale
description: A loaded .py Maya plugin is not refreshed by tool reloads; check a version and reload it; unloadPlugin refuses while the undo queue holds its commands
metadata:
  type: reference
---

Measured 2026-11-20 (A00630 v01.07, user error "[FAIL] Drag : module 'maya.cmds' has no attribute 'junMotionPathDirty'"):

- `if not pluginInfo(loaded): loadPlugin(...)` keeps whatever plugin the Maya session loaded first. DEV reload / copying a
  new tool version refreshes the Python modules but **not** the plugin → commands added later are missing, draw code is old.
- Fix pattern: plugin file defines `PLUGIN_VERSION` (passed to `MFnPlugin(obj, author, PLUGIN_VERSION)`) and `COMMANDS`;
  the tool imports the plugin file as a normal module to read them and compares with `pluginInfo -q -version` plus
  MEL `exists "<cmd>"` (Python `cmds` has no `exists`). Mismatch → delete plugin-type nodes → `unloadPlugin` → `loadPlugin`.
  **Bump PLUGIN_VERSION whenever the plugin file changes.**
- `unloadPlugin` raises "cannot be unloaded because it is still in use" while the **undo queue holds that plugin's commands**
  (even with no nodes left). `cmds.flushUndo()` then unload works — tell the user the undo queue was cleared once.
- Test: write a copy of the current plugin with version "1.0" and a command removed to a temp dir, load it, then open the tool.

Related: [[maya-loadplugin-no-file]] · [[wip-a00630-motion-path]]
