# Changelog — A00240_PathTool

All notable changes to this tool are documented here.

## [01.11] - 2026-09-18
### Added
- **Shrink: a small file tree grows next to the buttons.** Only the top file icon shows at first;
  0.5 s later three files unfold out of it, and 0.5 s after that each of them unfolds one more
  file below it. Each step takes 0.25 s - the new icon slides from its parent to its row while
  the branch line grows with it and it fades in. When the tree is complete the animation stops
  (no timer keeps running while the window sits shrunk), and it plays again from the start every
  time Shrink is turned on.
- The icons are drawn in code (a 7 x 9 pixel file with a folded corner) in the theme's text
  colour, like the dino in A00220_BackupTool.
- While shrunk the window's inner margin is 2 px instead of 11 px so the seven rows fit in the
  same 350 x 78 window (about 10 px per row).

## [01.10] - 2026-09-18
### Added
- **Menu bar with `Help`** - the shared menu bar every tool uses, so `Help > Copy Tool Name`
  (and any common item added later) works here too.
- **Shrink toggle**, next to `Pin`. Hides the tabs and the menu bar and makes the window
  350 x 78 px - the width of A00220_BackupTool when it is shrunk, and half its height.
  Press again to go back to the size it had before. The empty space left of the buttons is
  where a small file tree animation will play (planned for v01.11).

## [01.09] - 2026-09-17
### Changed
- **Tree tab: the Filter no longer expands the tree.** Before, every folder on the way to a
  match was opened - and since a folder name (`charA`) matches every path below it, searching
  for a folder expanded the whole subtree. Now the filter only hides what does not match; the
  tree keeps its current expanded/collapsed state and you open what you need (Shift + expand
  still opens everything below).
- Clearing the filter no longer folds the tree back to the default - folders you opened while
  searching stay open. `Build`, `Depth` and `Show files` still start folded as before.

## [01.08] - 2026-09-16
### Added
- **Tree tab: `Refresh`.** Reads the folders again and updates the tree **without losing the
  view** - what is expanded stays expanded, the selection and the scroll position are kept,
  and only what actually changed on disk moves (new / removed / renamed entries).
  - **`Selected`** (on by default) - refresh only the folder(s) selected in the tree; a
    selected file means its folder. Off = the whole tree from the root path.
  - **`Recursive`** - also refresh everything below. Off = that folder's own contents only,
    and whatever is already known deeper is kept as it is.
  - The refresh never scans past the `Depth` setting, and `Show files` / `File Types` /
    `Filter` stay applied afterwards.
  - With `Selected` on and nothing selected, nothing happens and the tool says what to do -
    quietly re-reading the whole tree would be worse.

## [01.07] - 2026-09-16
### Added
- **Pin (always on top).** A `Pin` toggle sits at the top-right of the window. Turning
  it on keeps Path Tool above other windows (the label becomes `Pinned`).
- **Tree tab: Filter.** Find items by **name or path** - matching is done against the
  full path, so a file name (`skin_color`), a folder name (`tex`) or a path fragment
  (`charA/tex`) all work. Several words are **AND**. Separators `/` and `\` are treated
  the same. Matches keep their parent folders visible and the tree opens down to the
  hit; `N match(es)` is shown next to the box. Clearing the filter folds the tree back.
- **Tree tab: Copy file path.** The right-click menu now has `Copy file path` next to
  `Reveal in File Explorer`. It puts the item's **absolute path** on the clipboard
  (folder or file), in OS-native form so it can be pasted into Explorer or a file dialog.

### Changed
- **Tree tab: the tree no longer opens fully expanded.** Build (and a Depth change) now
  leaves **only the root expanded** - every folder under it is folded.
  - plain expand -> one level
  - **Shift + expand** -> everything below, down to the leaves
  - **Shift + collapse** -> everything below folds
  - after a Shift-collapse, a plain expand opens **one level** again
  Qt remembers a child's expanded state when you fold a parent, so a plain fold/unfold
  re-opens what was open; **Shift + collapse is how that memory is cleared**. The rule
  applies at every depth.
- **App / taskbar icon is now yellow**, matching the `yellow_mid` UI theme (it was
  purple, left over from an earlier theme). Same artwork, recoloured from the qss
  palette (`#c8b86f` / `#e6d68f` / `#a09150`); `.svg` -> `.png` + multi-size `.ico`
  (16-256 px) rebuilt.

## [01.06] - 2026-07-03
### Added
- **App / taskbar icon.** Added a purple folder-tree icon
  (`icon/A00240_PathTool.svg` → `.png` + multi-size `.ico` 16–256px) matching the
  purple_dark theme. `launch.py` now sets it as the application/window icon and — on
  Windows — sets an explicit **AppUserModelID** (`Dnable.JUN.A00240.PathTool`) so the
  taskbar shows this icon instead of the generic `python.exe` icon when run from a
  terminal. Path resolves in dev and PyInstaller builds (`app/config/app_meta.py`);
  `build_exe.bat` embeds/bundles the icon. (Method: `docs/taskbar_icon_guide.md`.)

## [01.05] - 2026-06-26
### Added
- **ShortCut** tab — reorder path buttons inside a category. A path button's
  right-click menu now has **Move Up** / **Move Down** (disabled at the ends),
  mirroring the category reordering; the new order is saved to the profile JSON.

## [01.03] - 2026-06-19
### Added
- **ShortCut** tab — a path button's right-click menu now has **Change Category**:
  pick another category to move the button into (blocked if a button with the same
  name already exists there). The button (path included) is moved to the end of the
  target category and saved to the profile JSON.

## [01.02] - 2026-06-19
### Added
- **Tree** tab — show an input folder as a tree view. Options: **Depth** (how many
  levels deep; 0 = All), **Show files** (off = folders only), **File Types**
  checkable dropdown (show only chosen extensions, found after Build), **Expand**
  (open the tree in a larger window), and **right-click → Reveal in File Explorer**
  (folder opens; file is selected). Folders and files are distinguished by
  folder/file icons. Build scans the path (cached); Show files / File Types
  re-filter instantly without a re-scan. New `core/tree_scanner.py`.

## [01.01] - 2026-06-19
### Added
- **ShortCut** tab — reorder categories. The category right-click menu now has
  **Move Up** / **Move Down** (disabled at the ends), so categories no longer
  stay stuck in creation order; the new order is saved to the profile JSON.

## [01.00] - 2026-06-19
### Added
- Initial release. Standalone (Maya-independent) PySide6 Windows app.
- **ShortCut** tab — build your own categorized path launcher:
  - **Profile** group — keep separate path sets per environment (e.g. Home vs
    Work), each stored as its own JSON. Switch via the combo; manage with
    **New / Rename / Delete**. At least one profile always remains.
  - **Create** group with **Category** and **Path** buttons.
    - **Category** creates a new category (shown as its own `QGroupBox`).
    - **Path** opens a single dialog to set **category** (which one to add into),
      **button name**, and **path** (with Browse) all at once; the new button
      appears inside the chosen category.
  - Clicking a path button **opens that path in the file explorer** (folder is
    opened; a file is revealed/selected in its folder). Windows-first with
    macOS/Linux fallbacks.
  - **Edit / delete via right-click context menu** (keeps the view clean and
    scales as items grow):
    - Category header → **Rename Category** / **Delete Category**.
    - Path button → **Rename** / **Change Path** / **Delete**.
  - Categories are scrollable so the list can keep growing.
- Tabbed window (`QTabWidget`) designed for more tabs later — currently just
  **ShortCut**.
- Config stored **inside the tool folder** at `data/profiles/<name>.json`
  (+ `data/active.json`). When run as a one-file exe, it is saved next to the
  `.exe` instead of the temp extraction dir, so it persists. (`data/` is
  git-ignored.) Legacy `~/.jun_pathtool/shortcuts.json` auto-migrates to a
  `Default` profile on first run.
- PyInstaller build (`build_exe.bat`, `launch.spec`).
