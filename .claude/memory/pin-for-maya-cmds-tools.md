---
name: pin-for-maya-cmds-tools
description: How to add an always-on-top Pin toggle to a maya.cmds (arch A) tool window
metadata: 
  node_type: memory
  type: reference
  originSessionId: 2af83ce7-788e-4c2c-83e0-9ebc68b52132
---

`cmds.window` has no always-on-top flag, so the Qt Pin pattern (`self.setWindowFlag(
Qt.WindowStaysOnTopHint, on)` used by A00110 / A00220 / A00340) can't be applied directly to
architecture-A tools.

Bridge: `Framework/qt/maya_window.py` → **`maya_ui_widget(ui_name)`** wraps a maya.cmds UI as a
QWidget (`MQtUtil.findWindow` → fallback `findControl` → `wrapInstance`). Then toggle
`Qt.WindowStaysOnTopHint` on that widget and call `show()` again (changing window flags hides the
window).

First used in `A00030_quickTool` V01.13 (`cb_toggle_pin`, a `cmds.checkBox` at the top of the
window — a right-aligned button would need an extra `rowLayout`). Reuse for any other maya.cmds tool.

Related: [[wip-a00220-pin]], [[prefer-pyside-for-new-tools]]
