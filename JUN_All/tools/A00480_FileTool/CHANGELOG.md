# Changelog — A00480_FileTool

## v01.03 (2026-09-18)
- **Export rules** - checks that run before anything is exported. Pick them in the new
  `Rules (n/m)` drop-down next to Type Filter; `Check` runs them without exporting.
  - Every checked rule runs on **every listed set first**. If any rule fails, **no file is
    exported at all** - not even the sets that passed. All problems are logged in one go.
  - First rule: **Check Hide Mesh** (off by default). Looks at every mesh in the listed
    sets (members and everything under them, nested sets and component members too) and
    fails if any of them is hidden in the scene: its own, its shape's or any parent's
    `visibility` / `lodVisibility` is off, or a display layer / drawing override hides it.
    The log lists each set and hidden mesh with the reason. Intermediate (orig) shapes are
    ignored.
  - New rules are one entry in `app/core/export_rules.py` (`EXPORT_RULES`); the drop-down
    and Export / Check pick them up without UI changes.

## v01.02 (2026-09-17)
- Fix: the Pin button label was clipped. The button keeps its 72 x 22 size; its
  vertical padding is now 0 (the theme's 8px padding left only 4px for the text).

## v01.01 (2026-09-17)
- The window now opens at the same size as `A00040_file_exporter_V02`
  (960 x 853 with slate_dark). v01.00 measured its size before the theme reached
  the child widgets and opened at about 1290 x 890.
  - The size is fitted to the layout minimum on the event loop right after show().
  - Export tab page margins removed, window side margins reduced by the tab
    frame, Pin button height 22 so the header row matches the menu bar.

## v01.00 (2026-09-17)
- New tool: file import / export / path helpers in one window, three tabs.
  - **Export** — the whole `A00040_file_exporter_V02` (v02.09) window: Export Path
    (Browse / Paste), Set Up, Naming tokens, Move to scene root, Joints only under
    joints, Type Filter. Same results as the original (same files, same FBX
    contents, same log lines).
  - **Import** — `Import FBX normal` from `A00030_quickTool_V02`.
  - **Path** — `Copy Scene Folder` / `Open Scene Folder` from `A00030_quickTool_V02`.
- NEW **Scene** button next to the export path: fills it with the current scene's
  folder (an unsaved scene leaves the path unchanged and logs a warning).
- Export now loads the FBX plugin up front; without it the export logs
  `[FAIL] Cannot export FBX without the plugin.` instead of raising.
- One shared log for all tabs, Pin (always on top), common menu bar.
- Internal: the pasted-path cleanup moved from the UI into
  `core.normalize_pasted_path`; the exporter's private `undo_chunk` copy was
  replaced by `Framework.core.maya_undo.undo_chunk`.
- The two source tools are untouched and can run side by side with this one.
