---
name: wip-a00220-pin
description: "A00220_BackupTool Pin (Always on Top) toggle button, ported from A00110 pattern"
metadata: 
  node_type: memory
  type: project
  originSessionId: ba4273fe-f76d-4e80-a559-f9d7a6aeeb4c
---

DONE (verified + pushed Dnable/dev, commit ca92466): A00220_BackupTool v01.13 — added a **Pin (Always on Top)** toggle button, same pattern as [[wip-a00110-graph-focus]]'s host tool A00110_animTool (v01.24).

Checkable `Pin` QPushButton at the top-right of the window in a new header row (`_build_ui`, QHBoxLayout with addStretch(1) + fixed-size 72x28 button). `toggle_always_on_top(enabled)` does `setWindowFlag(Qt.WindowStaysOnTopHint, enabled)` → setText Pin/Pinned → `self.show()` (re-show needed because changing flags hides the window) → logs via existing `self.log()`. A00220 is a standalone Qt window (`super().__init__()`, no maya parent), so the flag toggle works the same as A00110. Default off (normal Z-order), opt-in. Not persisted in prefs (matches A00110).

Files: `app/ui/main_window.py` only; version 01.13, CHANGELOG, docs `JUN_All/docs/A00220_BackupTool.md` (§3 화면 구성). See [[push-includes-tool-guide-docs]].
