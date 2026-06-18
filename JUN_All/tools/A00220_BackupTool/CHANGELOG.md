# Changelog — A00220_BackupTool

## [01.01] - 2026-06-18

### Added
- Countdown display (`Next save in MM:SS`) showing the time remaining until the
  next backup, updated every second. Shows `--:--` while deactivated.

## [01.00] - 2026-06-18

### Added
- Initial release. Standalone PySide periodic backup tool.
- Target file list (multiple files): each file is copied into a `backup`
  folder next to the original, named `{base}_{suffix}{ext}` (e.g. `scene_BU.mb`).
- Backup folder name and suffix are user-configurable.
- Interval configurable in minutes and seconds.
- Save modes:
  - **Overwrite** (default): always overwrites the single backup file.
  - **Version Up**: writes `{base}_{suffix}_{NN}{ext}`, keeping only the latest
    N versions (oldest pruned automatically).
- Status indicator: `Stat : Deactive` / `Stat : Active...` (animated dots) /
  `Stat : Saving`.
- Settings (file list, options, interval) persisted to
  `%USERPROFILE%/.jun_backuptool/prefs.json` and restored on next launch.
