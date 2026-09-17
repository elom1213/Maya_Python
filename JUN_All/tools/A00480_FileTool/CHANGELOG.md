# Changelog — A00480_FileTool

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
