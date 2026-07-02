# Changelog — A00340_SelectionTool

All notable changes to this tool are documented here.

## v01.00 — 2026-07-02

Initial release.

- In-Maya PySide tool: quickly re-select saved sets of objects with one click.
- **Selection buttons**: capture the current Maya selection into a named button;
  click to select those objects again. `Add` toggle accumulates onto the current
  selection instead of replacing it.
- **Categories**: group buttons in collapsible boxes. Right-click a category to
  rename / reorder (Move Up/Down) / delete.
- **Profiles**: keep separate button sets per character / asset. Each profile is
  its own JSON under the tool's `data/` folder; New / Rename / Delete supported.
- Right-click a button to Rename, Move Up/Down, Update Objects (replace with the
  current selection), Add Objects (append the current selection), Change Category,
  or Delete.
- Missing objects (renamed / deleted in the scene) are skipped on select and
  reported in the log.
- Structure and edit flow ported from A00240_PathTool; Maya integration
  (launch / drag&drop shelf install / Maya-parented window) from A00310_SearchTool.
- Shelf icon (`icon/A00340_SelectionTool.png` + `.svg`): blue dashed selection
  marquee with a cursor, matching the A00310 tile style.
