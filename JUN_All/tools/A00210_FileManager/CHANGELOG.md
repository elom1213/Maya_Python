# Changelog — A00210_FileManager

All notable changes to this tool are documented here.

## [01.23] - 2026-06-26
### Added
- **File Manager** tab — **Source Mode** selector (Settings group). Choose where
  records/thumbnails are read from and written to:
  - **Remote (Git)** — the existing behavior: a central git data-repo synced with
    **Pull / Push** (uses the **Store Repo** clone path).
  - **Local (Shared / NAS)** — a new **Shared Folder** path is read and written
    **directly, with no git**. Intended for teams sharing a NAS, where the file
    server keeps the data in sync instead of pushing/pulling a git remote each
    time. In this mode the git inputs (Store Repo, Remote, Branch, Remote URL) and
    the **Pull / Push** buttons are disabled; use **Scan** to refresh.
  - The mode is saved **per profile** (alongside the new `local_dir`), so e.g. a
    `Work (NAS)` profile can use Local mode while a `Home` profile stays on Git.
    All tabs (File Manager / Path Structure / Lineage) follow the active mode's
    folder automatically.

## [01.21] - 2026-06-22
### Added
- **File Manager** tab — **Edit** button on the **Log history** header. Opens an
  *Edit Log History* dialog where each past entry's **author** and **note** can be
  edited and individual entries **deleted** (timestamps are kept). OK replaces the
  record's logs in order; press **Save Record** to persist (same flow as Add Log
  Entry). Editing is structured per-entry, so timestamps/entry boundaries can't be
  corrupted by free-text edits.

## [01.20] - 2026-06-22
### Added
- **File Manager** tab — **settings Profiles**. A new **Profile** group (combo +
  **New / Rename / Delete**) saves every user setting — Project Root, Store Repo,
  Scan Dir, Remote, Branch, Remote URL, Author, Recursive, Show Recorded Only — as
  a named profile (one JSON each, under `~/.jun_filemanager/profiles/`). Switch
  profiles to instantly load that environment's settings (e.g. Home / Work).
  - Switching a profile **auto-saves the current fields** to the outgoing profile
    first (no lost edits), then loads the new one and **refreshes the Lineage /
    Path Structure** saved-lists against the new Store Repo. The window also saves
    the active profile on close, and remembers it across launches (`active.json`).
  - **Save Settings** now writes to the active profile. The old single
    `prefs.json` is **migrated once** into a `Default` profile (original kept as
    `prefs.json.bak`); `prefs.load()/save()` stay back-compatible (they target the
    active profile), so A00211_RefLineage keeps working unchanged.

## [01.19] - 2026-06-22
### Changed
- **Lineage** tab — node right-click **Reveal in File Explorer**: if the file
  exists on this machine it is revealed in File Explorer as before (no popup). If
  it doesn't (e.g. a graph generated on another machine by **A00211_RefLineage**),
  the file's **path is popped up** in a dialog (selectable/copyable) instead of
  silently failing. The menu item is enabled whenever the node has a `key` (no
  longer greyed out just because the file is missing locally).

## [01.18] - 2026-06-22
### Added
- **Lineage** tab — **convert an edge's type by selecting it and switching the
  edge-type dropdown**. Select one or more edges, then change the
  `Lineage (parent)` / `Reference (dashed)` dropdown beside *Connect Mode* — the
  selected arrows switch type in place (solid open-V ↔ dashed filled-triangle),
  keeping their direction. The underlying relationship moves between the lineage
  DAG (`parents`) and the `references` list, any custom edge color carries over,
  and a conversion that would create a cycle is rejected. (Previously the dropdown
  only chose what a *new* node→node drag created.)

## [01.17] - 2026-06-22
### Added
- **Lineage** tab — **edge colors are now editable too**. Select one or more edges
  (lineage and/or reference) and use **Set Color...** to recolor them, or **Reset
  Color** to revert to the default (lineage = child lane color, reference = gray).
  `Set Color... / Reset Color` now act on the combined node + edge selection. The
  per-edge override is stored in the graph JSON (`edge_colors`, keyed by
  `kind:src>dst`; back-compatible) and cleaned up when an endpoint node is deleted.

### Fixed
- **Lineage** tab — **overlapping arrows between the same two nodes are fanned
  apart**. When a node pair had both a lineage and a reference edge (or otherwise
  shared endpoints), the arrows were drawn on top of each other. Edges sharing the
  same node pair are now spread horizontally by a fixed spacing so each arrow (and
  its arrowhead) is distinct.

## [01.16] - 2026-06-22
### Added
- **Lineage** tab — **Reference edges (dashed)**: a node can now point a **gray
  dashed arrow** at another node to show a Maya **reference** relationship
  (referenced file → the file that loads it), separate from the solid
  version/branch lineage. Drawn in **Connect Mode** via the new **edge-type
  dropdown** (`Lineage (parent)` / `Reference (dashed)`) beside the *Connect Mode*
  button — pick *Reference*, then drag from the referenced node to the referencing
  node. Reference edges are independent of the lineage DAG, so they **do not affect
  lane/color/auto-layout**; they have their own cycle guard and a filled-triangle
  arrowhead to tell them apart from lineage's open V. Stored as a new per-node
  `references` list in the graph JSON (back-compatible: older graphs load fine).
- **Lineage** tab — **Set Color... / Reset Color**: rubber-band select one or more
  nodes and set a **custom fill color** on all of them at once (`Set Color...`,
  color picker), or **Reset Color** to revert the selection to the automatic lane
  color. The manual color is stored per node (`color`); lineage edges keep their
  lane color, so the git-graph lane reading is preserved.

## [01.15] - 2026-06-22
### Fixed
- **Lineage** tab — **middle-mouse pan no longer hits a wall**. Panning moves the
  scrollbars, whose travel was bounded by the scene rect (content bounds + a small
  200 px margin), so dragging stopped once you reached just past the nodes. The
  pannable area is now a full viewport-worth of margin around the content, and the
  scene rect grows on demand while you keep dragging toward an edge — so you can
  pan freely well beyond the nodes (effectively unlimited). The margin resets to
  the content on the next render, so it never bloats permanently.

## [01.14] - 2026-06-19
### Added
- **File Manager** tab — **right-click a file → Show in File Explorer**: opens the
  file's folder with the file selected (Windows `explorer /select,`, macOS `open
  -R`, Linux `xdg-open`).
- **File Manager** tab — **Name filter** bar above the file list: a text field +
  **Filter** button (or Enter). Empty shows all; a keyword shows only files whose
  name contains it (case-insensitive). Stacks with the other filters.
- **File Manager** tab — **File Types** checkable dropdown next to *Show Recorded
  Only*: lists the extensions found in the last scan, each toggleable (plus
  **All**), so you can show only chosen types. Re-filters instantly; the menu
  stays open while toggling multiple types.
- **File Manager** tab — **Expand** button by *Log history* opens the log in a
  large, resizable read-only window (the side panel is narrow for long logs).

### Changed
- **File Manager** tab — **Scan now lists all file types**, not just `.mb`/`.ma`
  (`.fbx`/`.obj`/`.png` etc. are included); narrow the result with the new
  **File Types** / **Name filter** controls.

## [01.13] - 2026-06-19
### Changed
- **Settings** — the **Branch** field is now an editable dropdown. Opening it lists
  the Store Repo's actual git branches (local + remote-tracking, deduped) so you can
  pick a valid one instead of typing it. You can still type a branch name manually
  (e.g. before the first clone/fetch). This avoids the common `src refspec <branch>
  does not match any` push error caused by a branch-name mismatch (e.g. `main` vs
  `master`). Backed by new `GitSync.list_branches()` (reads local refs, no network).

## [01.12] - 2026-06-19
### Changed
- **File Manager** tab — *Load Image...* now opens in the Store Repo's `thumbs`
  folder instead of the home directory, so a thumbnail already saved there can be
  reused for several files. Falls back to home if the Store Repo is unset or its
  `thumbs` folder does not exist yet.

## [01.11] - 2026-06-19
### Added
- **File Manager** tab — **Show Recorded Only** checkbox next to *Recursive*. When
  checked, the file list keeps only files that have a saved record (created via
  *Save Record*), so a recursive scan that lists every file can be narrowed to the
  ones tracked through this tool. Re-filters instantly on toggle (no re-scan
  needed) and the state is remembered in prefs.

## [01.10] - 2026-06-19
### Changed
- **Lineage** tab — rubber-band selection is now **intersect** mode: dragging a box
  selects any node or connection the rectangle **touches**, instead of only the
  ones fully enclosed by it (was `ContainsItemShape`, now `IntersectsItemShape`).

## [01.09] - 2026-06-19
### Added
- **Lineage** tab — delete nodes **and connections**, with multi-select:
  - **Click a connection (edge)** to select it (hit area widened so thin curves are
    easy to hit; the selected edge is highlighted white/thick).
  - **Delete / Backspace** removes the current selection — any mix of nodes and
    connections — with no confirmation popup. Deleting a connection drops only that
    parent link from the child; deleting a node also cleans up orphaned references.
  - **Rubber-band multi-select**: drag on empty canvas to box-select nodes fully
    inside the rectangle. Disabled while **Connect Mode** is on (so line-drawing is
    unaffected); restored when Connect Mode turns off.
### Changed
- **Delete Node** button now deletes **all selected nodes at once** and no longer
  shows a confirmation dialog (was: single node + Yes/No popup).

## [01.08] - 2026-06-19
### Added
- **Lineage** tab — the **Node** panel now shows the selected node's **log history**
  (read-only), loaded from the same record the File Manager tab's *Save Record*
  writes (`records/<key>.json`). It is re-read from disk on node select and when
  the Lineage tab regains focus, so entries stay in sync with the File Manager tab.
  Shown only for nodes that map to a record (not for planned / out-of-root nodes).

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
