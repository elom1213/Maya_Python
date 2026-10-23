# Changelog — A00370_ToolLauncher

All notable changes to this tool are documented here.

## v01.12 — 2026-10-23

- **Shrunk window is narrower: 272 x 155.** While shrunk, `Pin` now sits **under** `Shrunk`
  (the two buttons stack in a small grid) instead of to its right, and the window loses the
  column `Pin` used to take (72 px + 6 px gap: 350 -> 272). Height and the rocket area are
  unchanged. Restoring puts `Pin` back to the right of `Shrink` on one row.
- Verified offscreen (PySide6, 32 checks incl. Pin position in both states, no empty column).
  Not yet checked inside Maya.

## v01.11 — 2026-10-23

- **Shrink.** A checkable `Shrink` button left of `Pin` (same 72 x 28). On, it hides the
  menu bar, the whole launcher area (Controls / Filter / buttons) and the copyright line and
  resizes the window to **350 x 155** - the same size `A00220_BackupTool` and `A00240_PathTool`
  get when shrunk. Press again (`Shrunk`) to restore the previous window size (width and height).
  Only the display is hidden: profiles, buttons and the log stay as they were.
- **Rocket launch animation while shrunk** (`app/ui/rocket_anim.py`, `RocketAnimWidget`).
  The tool icon's rocket is drawn as a code bitmap (body in the theme text colour, window /
  fins / flame in the icon's coral) in the space left of the two buttons, and **loops forever**:
  0.6 s ignition on the pad (flickering flame, slight shake) -> 1.2 s lift-off accelerating
  (ease-in) out of the top, leaving a fading exhaust trail -> 0.6 s empty sky -> again. One loop
  is 2.4 s. Restarts from the pad every time Shrink is turned on, stops when it is turned off.
  Repaints only when the picture changes (no redraw during the idle phases).
- Verified offscreen (PySide6, 29 checks: button place / size, hidden widgets, 350 x 155,
  round-trip restore, repeated toggles, Pin while shrunk, animation phases / loop wrap / trail)
  plus captures at several times. Not yet checked inside Maya.

## v01.10 — 2026-10-22

- **Profiles reorganised (data only, no code change).** Plan:
  `docs/plans/A00370_ToolLauncher_profile_classification_plan.md`.
  - `Mesh` renamed to **`MESH`** (file `data/profiles/MESH.json`).
  - New profiles **`FACIAL`** (Shape · Lip Sync) and **`UTIL`** (Select & Name · Scene · File).
  - Existing buttons keep their category (`Main`) and order; new tools go into **new categories
    appended after `Main`** - RIG `Control` · `Skin & Motion`, ANIM `Motion`, MESH `Edit`.
    Buttons: 13 -> **38** (22 tools added, `SecondaryMotion` · `BSTool_V02` · `abSymMesh` listed in two
    profiles on purpose).
  - **Every button is coloured per profile**: RIG `#3f6fb5` · ANIM `#c7762e` · MESH `#3f9a5a` ·
    FACIAL `#c25a86` · UTIL `#6b7280` · UE `#7a5bbf`.
  - `A00430_DemBone` had no icon; `icon/A00430_DemBone.svg/.png` added (icon builder).
  - Verified headless: all 38 buttons `validate` OK, icon found, no duplicate path inside a profile,
    paths portable (`tools/...`), the 13 old buttons keep their order. Not yet checked inside Maya.

## v01.09 — 2026-10-22

- **Menu `Profile > Show Profiles Folder`.** New `Profile` menu left of `Help`. The item
  opens the folder that holds the profile JSON files (`data/profiles/*.json`) in File
  Explorer (creating it if missing) and writes the path to the Log. Same shape as
  `A00550_PoseMapper`'s `Library > Show Libraries Folder`. `main_window.py` only.

## v01.08 — 2026-10-22

- **Search (Filter).** A `Filter` row sits right above the button area (outside the
  collapsible `Controls`, so it is there even when Controls is folded). Type any part
  of a **button name, category name or tool folder name** (`A00080`, `unreal`, `skin`),
  case-insensitive; space-separated words all have to match. Only matching buttons stay,
  and a **category with no remaining button is hidden** as a whole. `Number: shown / total`
  on the right, `Clear` restores everything. The filter survives re-rendering (rename,
  move, Color Select on/off, profile switch).
  - Built on the shared `JUN_mod_filter_qt_v01` in `rows_provider` mode (the button
    area is stacked row widgets, not a `QListWidget`) - no tool-local search code.
  - Verified offscreen (PySide6, 15 checks). Not yet checked inside Maya.

## v01.07 — 2026-09-22

- Default profiles cleaned up to point at current tools (data only; see `version.py`).

## v01.04 — 2026-07-20

- **Relative button paths — no more cross-PC git churn.** Buttons now store their
  tool path **relative to the JUN_All root** (`tools/A000XX_name`) instead of an
  absolute path. The relative form is **identical on every PC**, so profile JSONs
  no longer change when different machines open/refresh them — the tracked
  `data/profiles/` stays clean in git. The actual absolute path is resolved at
  launch time from this PC's root (`tool_launcher.resolve`), and a foreign
  absolute path (from an older commit) self-heals via its `tools/` anchor.
- **Per-PC state moved out of git.** The JUN_All root is auto-detected from where
  the launcher runs, so you normally set nothing. An optional root **override**
  (to point at a different JUN_All) is saved to a **gitignored** `data/local_env.json`,
  and `data/active.json` (last-open profile) is now gitignored too. Both are
  per-PC, so they never conflict between machines.
- **Environment box reworked**: `Detect` (reset to auto-detected root, clears
  override), `Browse...` + `Apply Root` (save this PC's override, or clear it if
  it equals the auto-detected root), and **`Make Paths Portable`** (one-time
  migration that rewrites any old absolute button paths to relative — idempotent,
  so it's safe and produces the same result on every PC). Replaces the old
  `Refresh Paths`, which rewrote absolute paths per-PC and caused the churn.

## v01.03 — 2026-07-13

- **Portable across PCs (JUN_All Root + Refresh Paths)**: buttons store an
  absolute tool-folder path, so a profile made on one PC broke on another where
  JUN_All lives elsewhere. New `Environment` box at the top of the controls:
  - **JUN_All Root** field, pre-filled with the JUN_All this launcher is running
    from (auto-detected from the tool's own location — always correct for the
    current PC). `Browse...` to pick it, `Detect` to re-fill it.
  - **Refresh Paths** re-points *every button in every profile* to that root:
    each path's tail from its `tools/` segment (`tools/A000XX_name`) is re-joined
    onto the new root. Buttons outside `JUN_All/tools` (no `tools` anchor) are
    left untouched and reported as skipped. This is the one-click restore/share
    when you open a profile on a different PC.
- **Self-healing launch**: even before you press Refresh Paths, clicking a button
  whose stored path is broken now tries the same path rebased onto this PC's
  auto-detected JUN_All root, and launches from there if it exists — so shared
  profiles mostly just work.

## v01.02 — 2026-07-08

- **Larger icon beside the button**: the tool icon moved out of the button and
  now sits as a square tile to its left, sized to the button's height, so it
  reads much bigger. Buttons have a fixed height; the icon is a matching square.
  Icon-less tools still show a plain full-width button.

## v01.01 — 2026-07-08

- **Tool icons on buttons**: each button now shows the target tool's own icon
  next to its label. The icon is found in the tool folder (`icon/<folder>.png`,
  falling back to any `.png` / `.svg` in `icon/`); tools without an icon just
  show text as before. Resolved live at render time, so it appears as soon as
  the tool has an icon and updates when the button's path changes.

## v01.00 — 2026-07-08

Initial release.

- In-Maya PySide tool: one window of shortcut buttons that pop up your JUN
  tools, so you don't have to install a separate shelf icon for every tool.
- **Tool buttons**: each button holds one tool folder path (e.g. the folder of
  `A00080_KWI_creator_V03`). Click it and the tool launches — the launcher
  imports `tools.<folder>` and calls its `run()`, exactly like the tool's own
  shelf button. Any JUN tool folder that exposes `run()` works, so it is fully
  extensible: paste a path and you have a shortcut.
- **Add a button** with `Tool`: pick the tool folder with `Browse...`, give it a
  name (auto-filled from the folder name), choose a category. The path is
  validated (folder exists + has `__init__.py`) before it is saved.
- **Reload on launch** (default on): re-imports the tool before showing it,
  matching the shelf button (`run(True)`). Turn it off to just re-show an
  already-loaded tool.
- **Categories**: group buttons in boxes. Right-click a category to rename /
  reorder (Move Up/Down) / delete.
- **Profiles**: keep separate button sets per situation (rigging / facial / UE
  export). Each profile is its own JSON under the tool's `data/` folder;
  New / Rename / Delete supported.
- Right-click a button to Rename, Move Up/Down, Change Path (re-pick the folder),
  Reveal in Explorer, Set / Reset Color, Change Category, or Delete.
- **Button colors + Color Select mode**: give each button a custom color
  (palette + OS eyedropper). Turn on `Color Select` to check many buttons across
  categories and paint them all with one color at once (`Apply Color` /
  `Clear Color`). Colors persist per button in the profile JSON.
- **Layout**: vertical splitter between the control panel (Profile / Create /
  Color / Log) and the button collection; the whole control panel folds away
  with the single collapsible `Controls` bar.
- Ships with a `Default` profile holding a `Maya to Unreal` category wired to
  `A00080_KWI_creator_V03` and `A00260_ConstraintConverter` as examples.
- Structure, profile/category/color system and layout ported from
  A00340_SelectionTool; the click action launches a tool (from
  `app/core/tool_launcher.py`) instead of selecting objects.
- Shelf icon (`icon/A00370_ToolLauncher.png` + `.svg`): a rocket launching above
  a coral play button.
