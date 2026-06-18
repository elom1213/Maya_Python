# Changelog — A00210_FileManager

All notable changes to this tool are documented here.

## [01.06] - 2026-06-18
### Added
- **One-click data-repo sync for distributed users.** The tool now ships a bundled
  default data-repo config (`app/config/data_repo.py`: central repo URL, branch,
  and a default local clone path `~/.jun_filemanager/JUN_FileManager_data`). When a
  user who received the released tool clicks **Pull** and no store repo exists yet,
  it auto-clones the central data repo to the default location and pulls — no
  manual clone or path setup needed.
- New **Remote URL** field in Settings, pre-filled from the bundled config
  (editable for forks/relocated repos), persisted in prefs.
### Fixed
- Data sync never worked for distributed installs: the Pull/Push handlers read a
  `remote_url` pref that was never set (missing from defaults and UI), so the store
  was only ever `git init`-ed locally with no remote. The remote URL is now wired
  end-to-end.
- Default sync branch mismatch (`main`) vs the actual data repo (`master`); defaults
  now come from the bundled config, and legacy prefs are migrated to the correct
  branch on load.
- Clone failures no longer silently fall back to a local `git init` (which created a
  disconnected empty repo); the error is surfaced so auth/network/access issues are
  visible.

## [01.05] - 2026-06-18
### Fixed
- **Region capture** overlay showed a fully black screen, hiding what was being
  selected. The overlay widget was missing `WA_TranslucentBackground`, so the dim
  layer was painted over an opaque (black) background instead of the live desktop.
  Now the screen is only dimmed and the drag region stays clear (like Win+Shift+S).
  - Enabled `WA_TranslucentBackground` so the actual screen shows through.
  - Replaced fullscreen window **state** with explicit virtual-desktop **geometry**
    (frameless / stay-on-top / tool) — fullscreen + translucency could snap to a
    single monitor or break compositing. Works on Windows 10 and 11.
  - Painted the dim as four rects around the selection instead of
    `CompositionMode_Clear` (driver-dependent), so the selected region is reliably
    transparent.

## [01.04] - 2026-06-18
### Added
- **Lineage** tab — node **right-click context menu**: **Reveal in File Explorer**
  opens the folder containing that node's file with the file selected
  (Windows `explorer /select,`; macOS/Linux fallbacks). Enabled only when the path
  resolves (node has a project-relative key, project root is set, and the file
  still exists); disabled for planned / out-of-root / missing files. Built to be
  extended with more per-node actions later.

## [01.03] - 2026-06-18
### Added
- **Lineage** tab — manual relationship control: each node has a **Relation to
  parent** (`Auto` / `Version-up (main line)` / `Branch (variation)`). A
  `Version-up` child inherits the parent's lane color (same color = version line);
  a `Branch` child is forced onto a new lane (different color). `Auto` keeps the
  previous topology default (first child by creation order is the main line). Lets
  you flip which child is the version-up vs the branch instead of relying on add
  order.
- **Lineage** canvas navigation: mouse-**wheel zoom** (anchored under the cursor,
  0.15x–4.0x) and **pan via middle-mouse drag**. Left-click (select / node drag)
  and Connect Mode are unaffected.

## [01.02] - 2026-06-18
### Added
- **Lineage** tab: manually record branch / merge relationships between files
  (any format — `.mb`/`.ma`, `.fbx`, `.obj`, ZBrush, textures, …) and view them as
  a git-graph-style colored tree.
  - Interactive canvas (`QGraphicsView`): drag nodes to reposition; turn on
    **Connect Mode** and drag node → node to set a parent link (self-links,
    duplicates, and cycles are rejected).
  - **Auto lane coloring** — lanes (columns) are computed from the DAG topology
    like `git log --graph`; each lane cycles a color palette. Branches read as
    distinct colors; merges (multi-parent) collapse lanes.
  - **Auto Layout** arranges nodes into lanes (column = lane, row = topological
    order); positions stay user-draggable afterward and are saved.
  - **Planned** nodes ("제작 예정") for files not yet created (dashed, translucent).
  - Add nodes from a folder **scan** (any format; filter the result list by
    extension) or a single **Add File...**; both link to an existing
    record/thumbnail by project-relative key when inside the project root.
    Also add empty **planned** nodes. Node inspector to rename, mark planned,
    annotate, and preview the linked thumbnail.
  - Multiple named graphs per asset (`<store_dir>/lineage/<name>.json`); list,
    load, save, delete. Auto-synced by the existing Git Pull / Push.

## [01.01] - 2026-06-17
### Added
- **Path Structure** tab: save a folder-structure template (subfolders of a base
  folder) to JSON in the synced store, and recreate those folders on another PC.
  - Base path is stored **relative to the project root**, so recreation rebuilds
    under each PC's own project root (absolute paths may differ).
  - **Recursive** checkbox: capture the full nested subfolder tree, or only the
    immediate child folders.
  - Multiple named structures (`<store_dir>/path_structures/<name>.json`); list,
    preview, recreate, delete. Folders only — no files are created.
  - Auto-synced by the existing Git Pull / Push (records / thumbnails / structures).
### Changed
- Main window reorganized into tabs (**File Manager**, **Path Structure**); the log
  panel is shared below both tabs.

## [01.00] - 2026-06-17
### Added
- Initial release. Standalone (Maya-independent) PySide6 Windows app.
- Scan a directory for Maya scene files (`.mb` / `.ma`) and list them.
- Per-file metadata record: author + timestamped work log entries.
- Thumbnail per file via on-screen region capture (or load an image file).
- Metadata store keyed by **project-relative path** so the same file maps to the
  same record on any PC.
- Git sync (Pull / Push) of records and thumbnails only — original `.mb`/`.ma`
  files are never pushed (kept out of the data repo + `.gitignore` safety net).
- Per-PC local preferences (`%USERPROFILE%/.jun_filemanager/prefs.json`).
- PyInstaller build (`build_exe.bat`, `launch.spec`).
