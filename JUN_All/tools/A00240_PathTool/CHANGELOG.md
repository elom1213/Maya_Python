# Changelog — A00240_PathTool

All notable changes to this tool are documented here.

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
