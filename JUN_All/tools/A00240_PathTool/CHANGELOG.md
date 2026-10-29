# Changelog — A00240_PathTool

All notable changes to this tool are documented here.

## [01.31] - 2026-10-29

- **[UI] 탭마다 창 높이가 자동으로 맞춰진다.** 탭(중첩 포함)을 바꾸면 창 높이가 지금 보이는 페이지에 맞게 늘거나 줄어
  스크롤 없이 다 보인다. 페이지가 모니터 작업 영역보다 길면 화면 높이에서 멈춘다. 폭은 그대로(처음 여는 크기는 예전 `fit_to_content` 그대로, 그 뒤 높이만 따라간다).
  공용 `JUN_mod_tabFit_qt_v01` — A00275 v01.38 과 같은 방식 (`docs/Framework_MOD_tabFit_qt.md`). **마야 GUI 확인 아직.**

## [01.30] - 2026-10-23
### Changed
- **Buttons follow the window width.** Narrowing the window now narrows the ShortCut buttons with it;
  a label that no longer fits is elided (`...`) and the full name moves to the first line of the tooltip.
  In v01.29 the tab page kept the widest tab's width inside one outer scroll area, so the buttons stayed
  wide and their text was cut off as the window shrank.
  - Every tab page now has **its own** scroll area (instead of one around the whole tab widget), so each
    page follows the window down to its own minimum and only then shows a horizontal scrollbar.
  - All ShortCut buttons (`_ElideButton`: path buttons and the Profile / Create / Color rows) have a small
    minimum width (40 px) instead of their label width, keep full-label size hints so a squeezed row shrinks
    evenly, and elide the label to the current width. The profile combo no longer demands its longest item.
  - Remaining floor of the ShortCut page is the `Color` row (checkbox + two buttons), about 300 px
    offscreen; below that a horizontal scrollbar appears.
- Verified offscreen (PySide6, 21 checks + the 42 v01.28/29 checks): full label when wide, elided label +
  tooltip when narrow, elided text fits, page width follows the window, squeezed rows shrink evenly, rows
  with a stretch keep full labels, hints stay full-label based, drag reorder still works. Not yet checked
  by eye in the running tool.

## [01.29] - 2026-10-23
### Changed
- **The window can be resized freely.** The tabs now sit in a scroll area, so the window is no longer
  held at the widest tab's minimum width (the Junction tab's two side-by-side lists) - drag any edge to
  make it as narrow or short as you like; when it is smaller than the content a scrollbar appears.
  Opening size is unchanged (`fit_to_content`, clipped to the monitor's work area), the same approach
  `A00210_FileManager` v01.36 uses. Shrink / Pin keep working (Shrink hides the scroll area).
- Verified offscreen (PySide6): minimum width 1004 -> 172 px, `resize(300, 400)` / `(250, 300)` stick,
  opening size fits the screen, Shrink 272 x 155 and restore. Not yet checked by eye in the running tool.

## [01.28] - 2026-10-23
### Added
- **Drag a path button to move it.** Press a path button, hold, move and release - inside its category to
  reorder, or onto another category to move it there (same rule as `Change Category`: a button with the
  same name in the target blocks the move). A thin line shows where it will land, the cursor becomes a
  closed hand, and the list auto-scrolls near the top / bottom edge. `Esc` cancels. A press that moves
  less than the drag threshold is still a plain click (opens the path). While `Color Select` is on,
  buttons only check / uncheck - no dragging. `Move Up / Move Down` and `Change Category` remain.
- Implemented with mouse events on a button subclass (`_PathButton`), not native `QDrag`; buttons are
  addressed by (category index, button index), so duplicate names cannot move the wrong one.
- Verified offscreen (PySide6, 33 checks): click vs drag threshold, reorder down / up, drop on own slot,
  cross-category move, name conflict, Esc cancel + swallowed release, Color Select off, auto-scroll,
  profile JSON saved. Not yet checked by eye in the running tool.

## [01.27] - 2026-10-23
### Fixed
- **Toggling `Pin` while shrunk stopped the file-tree animation.** Changing the window flag hides and
  re-shows the window, and the animation widget's hide stopped its timer for good. It now remembers
  that it was running and resumes on show (Shrink off still stops it). Same fix in
  `A00370_ToolLauncher` v01.14 and `A00210_FileManager` v01.38.

## [01.26] - 2026-10-23
### Changed
- **`Pin` turns light red while pinned.** The checkable `Pin` button had only its label change to
  `Pinned`; now the button itself turns **light red** (dark text) while Always on Top is on, in every
  state (hover / pressed stay in the same red family), so the pinned state is visible at a glance.
  Shared rule `Framework/qt/pin_style.py` (`apply_pin_style`), the same color in `A00240_PathTool`,
  `A00220_BackupTool` and `A00370_ToolLauncher`. Only the `:checked` colors are set, so the button's
  size and the theme look are unchanged.

## [01.25] - 2026-10-23
### Changed
- **Shrunk window is narrower: 272 x 155.** While shrunk, `Pin` now sits **under** `Shrunk`
  (the two buttons stack in a small grid) instead of to its right, and the window loses the column
  `Pin` used to take (72 px + 6 px gap: 350 -> 272). Height and the file-tree area are unchanged.
  Restoring puts `Pin` back to the right of `Shrink` on one row. Same shape as `A00370_ToolLauncher`
  v01.12 and `A00220_BackupTool` v01.20. Verified offscreen (PySide6); not yet checked by eye in the
  running tool.

## [01.24] - 2026-10-23
### Added
- **`File > Add to Start Menu`.** Creates a Start menu shortcut for this tool (`JUN Path Tool.lnk` in
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs`) and tries to pin it to Start, the same as
  JUN Video Tool. The shortcut runs `pythonw.exe launch.py` (no console window; the exe itself when
  built with PyInstaller) with the tool icon and the tool's AppUserModelID, so a window started from
  the shortcut shares the taskbar button and icon with one started from a terminal. Click again after
  moving the tool folder to refresh the path. Windows 10 and 11: the shortcut always appears in the
  Start app list and search; where Windows hides the "Pin to Start" verb the dialog explains the
  one right-click to pin it by hand. The result line goes to the Junction tab's Log (the same place
  as `Help > Copy Tool Name`). Shared code: `Framework/core/shell_integration.py`.

## [01.23] - 2026-10-13
### Added
- **Junction > Create: `Tree...` on both lists.** Opens a popup with the **same tree as the Tree tab**
  (Adaptive, Depth, Show files, File Types, Expand, Refresh, Omit, Filter, right-click Reveal) - the one
  difference is a **check box on every folder**. `Add Checked to Sources` / `Add Checked to Create In`
  puts the checked folders in that list (duplicates skipped), clears the checks and closes. Files have no
  check box (a junction links a folder) and are hidden by default (Show files turns them on). The two lists
  share one popup, so the tree you built stays for the next open; the first open starts from the path typed
  in the Tree tab. Uses the shared `JUN_mod_fileTree_qt_v01` with its new `checkable_folders=True`.

## [01.22] - 2026-10-13
### Fixed
- **Junction > Create: sources with the same folder name no longer block each other.** The junction is
  named after the source folder, so in **n -> 1** (and in n -> n when two rows share a *Create In* folder)
  `D:\ProjA\Content` and `D:\ProjB\Content` both became `...\Content` and every row after the first was
  refused with *same junction path as an earlier row*. Now only the colliding rows get the parent folder
  prefixed - `ProjA_Content`, `ProjB_Content` (one more level when that still collides, `_2` as a last
  resort). Sources that do not collide keep their plain name. The same source listed twice is reported as
  *same source as an earlier row* instead of being renamed. `core/junction.unique_names()` holds the rule.

## [01.21] - 2026-10-12
### Added
- **Tree tab: junction-aware Reveal.** Right-clicking a junction (or any path that goes *through*
  a junction) now offers **Reveal in File Explorer (Junction)** - the path as shown in the tree - and
  **Reveal in File Explorer (Origin)** - the real folder the junction points to. Plain paths keep the
  single *Reveal in File Explorer*. Double-click still opens the path as shown (same as *Junction*).
  Lives in the shared `Framework/qt/path_context.py` (`origin_of`, `build_path_menu`), so the Expand
  window and the other tools using that helper get it too.

## [01.20] - 2026-10-12
### Changed
- **Tree tab moved to the shared Framework** as `JUN_mod_fileTree_qt_v01`
  (`Framework/qt/MOD_fileTree_qt_v01.py`, with `Framework/core/tree_scanner.py` and
  `Framework/core/prefetcher.py`). A00480_FileTool's new Maya tab uses the same tree to pick Maya files.
  Nothing changes in this tool: `app/ui/tree_tab.py`, `app/core/tree_scanner.py` and `app/core/prefetcher.py`
  only re-export the shared code (like `path_opener.py` already did).

## [01.19] - 2026-10-12
### Added
- **Junction tab** - `cmd /c mklink /J` from the UI, with **Create** and **Remove** sub-tabs.
  - **Create**: a *Sources* list (original folders) and a *Create In* list (folders to create the
    junctions in). Fill them with **Add...**, **Paste** (paths on the clipboard, one per line) or by
    **dragging folders from File Explorer**. **n -> 1** puts a junction for every source inside the
    first *Create In* folder; **n -> n** pairs the rows by order. The junction is named after the
    source folder; in n -> n, *Target row is the junction path* lets each row name the junction
    itself (like mklink's `<Link>`). A preview table shows every row with a reason when it cannot be
    made (source is a file, target folder missing, already exists, would loop inside its own
    source...). **Create Junctions** makes the `ready` rows and lists them in the Remove tab.
  - **Remove**: a *Junction | Target* table. Add rows the same ways, or **Scan** a folder (optionally
    recursive) for junctions. **Remove Junctions** deletes **only the links** - the original folders
    and their contents are never touched. A row that is not a junction is shown in red and skipped,
    and a confirmation says how many will be removed.
- **Tree tab: junctions are drawn in light red** (folder icon and name) with the target path in the
  tooltip. The non-Adaptive walk no longer follows a junction that points at its own ancestor
  (a loop), so Depth `All` finishes.

## [01.18] - 2026-10-12
### Added
- **Tree tab: Omit** - skip the first N levels under the root and show them as one `...` row.
  With `A/B/C/D/E` and Omit `2` the tree shows `A / ... / D / E`; with `3` it shows
  `A / ... / E`. Check **Omit** (on the Refresh row) and set the number (2 or more).
  Useful when a project always starts with the same fixed folders.
- The `...` row is one row even when the root has several branches - everything at the
  first shown level is gathered under it, and each item's tooltip shows where it came from
  (`B/C/D`). Branches and files that end inside the skipped levels are not shown.
- With Adaptive on, the skipped levels are read right away (they cannot be opened), and the
  folders under `...` are read ahead as usual. Refresh, Filter, Show files and File Types
  work on the omitted tree; `...` itself cannot be opened or copied.

## [01.17] - 2026-10-02
### Added
- **Tree tab: read ahead in the background** (Adaptive). Folders that are on screen but not
  read yet are read one level in the background, so opening them is instant. Only one level
  ahead - opening a folder starts reading its own subfolders. Up to 2000 subfolders per folder
  are read ahead; the rest are read when opened.
- **Empty folders lose their arrow before you open them** - including folders whose files are
  all hidden by *Show files* / *File Types*.
- Folders read ahead are also searched by **Filter**.

## [01.16] - 2026-10-02
### Added
- **Tree tab: Adaptive** (on by default). Build reads only the first level under the path, and a
  folder is read the first time you open it - one level at a time. A big or deep folder now shows
  right away instead of waiting for everything down to Depth. **Shift + open** still reads
  everything below that folder. Depth is used only when Adaptive is off.
- Folders not read yet show an open arrow; it disappears if the folder turns out empty.
  Extensions found while opening folders are added to **File Types** (checked).
- **Tree tab: double-click a path to open it in File Explorer** (same as *Reveal in File Explorer*:
  a folder opens, a file is selected in its folder). Double-click no longer opens/closes the
  folder in the tree - use the arrow or the Left/Right keys.
### Changed
- With Adaptive on, **Filter** searches only folders read so far, and **Refresh** re-reads only
  folders already read.
- Refresh now also adds newly found extensions to File Types.

## [01.15] - 2026-10-02
### Added
- **Button colors** (same feature as A00340_SelectionTool). Right-click a path button ->
  **Set Color...** opens a color palette (its *Pick Screen Color* is an eyedropper); **Reset Color**
  goes back to the theme color.
- **Color Select** in the new `Color` group: turn it on, click buttons in any category to check them
  (blue border), then **Apply...** paints them all with one color or **Clear** removes their color.
  While it is on, clicking a button does not open its path.
- The text color switches to black or white for readability. Colors are saved per button in the
  profile JSON and move with the button to another category or profile.

## [01.14] - 2026-10-01
### Added
- **Change Profile - move a category to another profile.** Left-click a category (its header or
  the empty space between its buttons) and a small menu shows **Change Profile**; it is also in the
  right-click menu. Pick one of the other profiles and the category moves there with every path
  button in it. Clicking a path button still just opens its path.
- If the target profile already has a category with the same name, the buttons are added to the
  end of that category. If any button name is already taken there, nothing moves and the
  clashing names are listed.
- The target profile is saved first, then the current one - if saving fails half way, the buttons
  end up in both profiles rather than in neither.

## [01.13] - 2026-09-18
### Changed
- **Shrink is now as tall as A00220_BackupTool's shrink: 350 x 155** (was 350 x 78 - too small).
  The file tree grows with it (icons 20 x 24, lines 4 px) and the window keeps its normal
  inner margin - the 2 px margin was only there to fit the tree into 78 px.

## [01.12] - 2026-09-18
### Changed
- **Shrink animation loops forever.** Each stage stays on screen 0.5 s - only the top file,
  then with its two children, then the full tree - and it starts over, one round every 1.5 s.
  It no longer stops when the tree is complete. Nothing is redrawn during the 0.5 s holds.
- **The bottom pair of files is gone** - the tree is now 5 rows: the top file, two children,
  one grandchild under each.
- **Thicker lines** - the branch lines and the file icon outline are 2 px instead of 1 px
  (the icon is now 10 x 12). With 5 rows each row is about 15 px, so it still fits the 350 x 78 window.

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
