# Changelog — A00340_SelectionTool

All notable changes to this tool are documented here.

## v01.03 — 2026-07-06

- **Color Select mode (recolor across categories)**: replaced the per-category
  bulk recolor with a free multi-select. A new `Color` bar adds a `Color Select`
  toggle; while it is on, every button becomes checkable and clicking checks it
  (instead of selecting objects). Check any buttons — across different categories —
  then `Apply Color...` paints them all with one picked color, or `Clear Color`
  resets them to the theme default. Checked buttons show a highlight border and
  the checked set survives re-render. Turning the mode off clears the checks and
  restores normal click-to-select.
- Removed the category right-click `Set Buttons Color...` / `Reset Buttons Colors`
  actions (superseded by Color Select mode). Per-button right-click
  `Set Color...` / `Reset Color` stays.

## v01.02 — 2026-07-06

- **Button colors**: give each selection button a custom color. Right-click a
  button → `Set Color...` opens a color palette (with the OS eyedropper /
  `Pick Screen Color` to copy any on-screen color) and applies it; the label
  text auto-switches black/white for readability. `Reset Color` reverts the
  button to the theme's default style.
- **Recolor many at once**: right-click a category → `Set Buttons Color...`
  applies one picked color to every button in that category in a single step;
  `Reset Buttons Colors` clears them all.
- Colors are stored per button (`"color"` hex) in the profile JSON, so they
  persist across sessions.

## v01.01 — 2026-07-02

- **Always on Top toggle**: added a checkable `Pin` button to the header row
  (menu bar on the left, button on the right). When enabled, the window stays
  above other Maya windows (`Qt.WindowStaysOnTopHint`); the button label
  switches to `Pinned`. The button uses a fixed size so its position and size
  stay constant when toggling between `Pin` / `Pinned`.

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
