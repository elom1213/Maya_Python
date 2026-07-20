# Changelog — A00370_ToolLauncher

All notable changes to this tool are documented here.

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
