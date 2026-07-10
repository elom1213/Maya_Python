---
name: wip-a00340-selectiontool
description: "A00340_SelectionTool v01.00 — new in-Maya PySide tool, quick re-select saved object sets via buttons (profile/category/button pattern)"
metadata: 
  node_type: memory
  type: project
  originSessionId: b7ee37ed-bdf5-4d70-a327-9952147532c6
---

A00340_SelectionTool v01.00 DONE (Maya-verified + pushed 2026-07-02, Dnable/dev commit 2c7d04f). 사용자 data/ 는 .gitignore 처리(A00240 선례), README 목록 등록.

New in-Maya PySide tool: click a button to re-select a saved set of Maya objects.
Buttons are freely add/remove/reorder-able and grouped into Categories; Profiles
keep separate button sets per character/asset (JSON per profile in the tool's
`data/` folder, like A00240).

**Why:** user wanted an A00240_PathTool-style customizable-button tool, but the
buttons select Maya objects instead of opening paths.

**How to apply:**
- Structure/edit flow ported from [[wip-a00170-attachcrv-tab]]'s sibling A00240_PathTool
  (profile → category → button, right-click Move Up/Down/Rename/Delete/Change Category).
- Maya integration (launch.py run(), __dragDrop_A00340.py shelf install, Maya-parented
  window via Framework.qt.maya_window, blue_dark theme) ported from A00310_SearchTool
  (see [[wip-a00310-searchtool-merge]]).
- Button stores `{"name", "objects":[...]}`; core split: prefs.py (pure JSON, DCC-free)
  + maya_select.py (capture_selection / select_objects, skips missing objects, `Add`
  toggle accumulates). Right-click also has Update/Add Objects (recapture selection).
- Docs: JUN_All/docs/A00340_SelectionTool.md + CHANGELOG.md. Icon made
  (icon/A00340_SelectionTool.png + .svg — blue dashed selection marquee + cursor,
  A00310-style tile; PNG rendered via PIL supersample since no SVG rasterizer avail).
- Follows [[prefer-pyside-for-new-tools]], [[ui-text-english-only]],
  [[standalone-app-package-collision]] (imports via tools.A00340_SelectionTool.app.*).
