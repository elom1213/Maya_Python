# Changelog — A00240_PathTool

All notable changes to this tool are documented here.

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
