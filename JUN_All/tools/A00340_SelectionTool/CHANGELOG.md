# Changelog — A00340_SelectionTool

All notable changes to this tool are documented here.

## v01.17 — 2026-10-28

- **Shared profiles and rules.** Besides the local ones in `data/` (this PC only, not tracked by
  git), the tool now also reads the `shared/` folder (`shared/profiles`, `shared/rules`), which IS
  tracked by git - commit and push a file there and other PCs get it.
  - Buttons tab: shared profiles appear as `Name  [Shared]` in the profile list (a local and a
    shared profile may have the same name). The group title reads `Profile (shared)` while one is
    open. New profiles are created locally.
  - `Share` moves the current local profile into the shared folder; `Copy to Local` copies the
    current shared profile to this PC. Both refuse when the other side already has that name.
  - Renaming or deleting a shared profile asks once more.
  - Rules tab: new `Scope` column (`Local` / `Shared`), `Share` / `Copy to Local` buttons and
    right-click items, the same extra question for shared rules.
  - View > `Show Shared Folder`, `Shared Folder...` (point it somewhere else on this PC - a NAS
    or another data repo; saved in `data/active.json`), `Use Default Shared Folder`.
    `Show Profile` opens the shared file for a shared profile.
  - Old `active.json` files keep working (no scope = local).

## v01.16 — 2026-10-28

- The `Add` checkbox moved from the Create group to the top of the button area, so it stays
  visible when Controls is collapsed or hidden (View > Show Controls).

## v01.15 — 2026-10-27

- **Drag a selection button to reorder it** (same as A00240_PathTool): press, hold, move and
  release - inside a category it changes the order, onto another category it moves there (blocked
  with a message when that category already has a button with the same name). While dragging, a
  line shows where it will land and the list scrolls by itself at the top / bottom edge. `Esc`
  cancels. A press-and-release without moving is still a normal click (selects the objects).
  In Color Select mode buttons are only checked, not dragged. `Move Up / Down` and
  `Change Category` stay in the right-click menu. The new order is saved to the profile JSON.

## v01.14 — 2026-10-27

- The log panel starts collapsed (Shrink on): only its button row shows; press `Show` to open it.

## v01.13 — 2026-10-27

- The `Pin` button turns light red while it is on (`Pinned`), like the other tools
  (shared `Framework.qt.pin_style`).

## v01.12 — 2026-10-27

- **The window can be made narrow freely by dragging.** The Rules tab status line printed the
  full rules folder path - one long word that never wraps - and that set the window's minimum
  width (a tab widget keeps the widest page's minimum, so it happened on the Buttons tab too).
  - The status line now shows the last two folders (`3 rule(s) in .../data/rules`); the full path
    is its tooltip (and `Show Folder` opens it).
  - The Rules page sits in a scroll area like the Buttons page: narrower than its button rows, a
    horizontal scroll bar appears instead of the window refusing to shrink.
  - The copyright line wraps.
  - Minimum width went from 1494 to 286 px (offscreen measure). What is left is the shared log
    panel's button row.

## v01.11 — 2026-10-26

- **Top-level tabs `Buttons` / `Rules`**: everything that existed is the `Buttons`
  tab; the last tab you looked at is remembered (`active_tab` in `data/active.json`).
- **Rules tab**: a rule is a named list of objects saved as ONE json file
  (`data/rules/<name>.json` with `name` / `description` / `objects`), so sharing
  rules between PCs is copying files. `New Rule from Selection` saves the current
  Maya selection; `Select` (or double-click) selects those objects in any scene -
  several highlighted rules select their union, `Add to current selection`
  accumulates. Missing names are skipped (red in the Objects list, `[WARN]` in the
  Log); a name that matches several nodes selects all of them with a warning
  (orange). `Update Objects` / right-click `Add Objects` recapture the selection,
  `Rename` renames the json file too, `Delete` removes the file(s) after one
  confirmation, `Description` is saved when the field loses focus, `Reload` /
  `Show Folder` / `View > Show Rules Folder` for files dropped in from outside.
- Core: `app/core/select_rules.py` (pure json, DCC-free) and
  `maya_select.name_status` / `select_names` (per-name `cmds.ls` so duplicate
  short names do not make `cmds.select` fail).

## v01.10 — 2026-10-19

- **View > Show Profile**: opens Explorer with the active profile's JSON file
  selected - the file this tool reads and writes on this PC
  (`<tool>/data/profiles/<profile>.json`). If the file is missing, the
  `profiles` folder is opened instead and the Log says so.

## v01.09 — 2026-10-13

- **Back to the stacked layout**: the side-by-side layout of v01.08 is reverted -
  the control panel is on top again, the button collection below, and the window
  opens at 360 x 620 as before (Profile / Create / Color are single rows again).
- **Controls fully visible by default**: on first show the top pane is sized to
  the control panel's content height, so Profile / Create / Color are all visible
  without scrolling. Expanding the collapsed `Controls` bar restores that height.
- **Log at the bottom of the window**: the Log view moved out of the control
  panel to a fixed group at the bottom, so it stays visible when `Controls` is
  collapsed or hidden via `View > Show Controls`.

## v01.08 — 2026-10-12

- **Side-by-side layout**: the splitter is now horizontal - the control panel
  (Profile / Create / Color / Log) sits on the **left**, the button collection on
  the **right**. Profile / Create / Color are laid out in two rows each (widget
  row + button row) so they fit the narrow column. The window opens wider
  (760 x 600) and the Log group takes the spare height of the left column
  instead of a fixed 90 px. Collapsing the
  `Controls` bar now shrinks the left column to the header's width; `View > Show
  Controls` still removes it entirely.

## v01.07 — 2026-10-12

- **View > Show Controls**: a new `View` menu (left of `Help`) with a checkable
  `Show Controls` item. Unchecking it hides the whole control pane (Profile /
  Create / Color / Log) **and the splitter handle**, so the button collection fills
  the window. Collapsing the `Controls` bar still left its header and the scroll
  area's minimum height; hiding removes the area entirely. Re-checking restores
  the pane at the sizes it had before. The state is saved in `data/active.json`
  (`show_controls`) and applied on the next launch.
- `prefs.get_setting` / `set_setting` for window settings in `active.json`;
  `set_active` now preserves the other keys of that file.

## v01.04 — 2026-07-06

- **Split layout + one-click collapsible controls**: the window is now a vertical
  splitter — the control panel (Profile / Create / Color / Log) sits on top, the
  created button collection below, with a draggable handle to rebalance them. The
  whole control panel is wrapped in a single collapsible `Controls` box: click its
  title bar (▾/▸) to fold Profile/Create/Color/Log away **all at once**; the top
  pane shrinks to the header and the button area takes the freed space (restored on
  expand). The Log view moved from a fixed bottom group into the control panel.

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
