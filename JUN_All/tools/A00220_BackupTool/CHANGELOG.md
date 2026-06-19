# Changelog — A00220_BackupTool

## [01.03] - 2026-06-19

### Changed
- **Settings** is now a collapsible section (click the header to fold/unfold);
  the window height auto-fits the content on toggle (shared
  `JUN_mod_collapsible_qt` widget, same as A00110).
- Narrower window (opens ~350px vs the previous 560). The original
  label-beside-field grid layout is kept; to reduce width the Save Mode radios
  and the interval min/sec fields are stacked vertically, the spinboxes are
  narrowed, the longest label is shortened (`Backup Folder Name` -> `Folder
  Name`), the file buttons are shortened (`Add...` / `Remove` / `Clear`), and
  the status label drops its `Stat : ` prefix (`Deactive` / `Active...` /
  `Saving`). Exact half-width isn't reachable with the side-by-side grid kept.

### Fixed
- Spinbox up/down arrows are now clickable. They were unreachable (text cursor
  shown on hover) because the shared theme QSS styled `QSpinBox` without
  defining the `::up-button` / `::down-button` sub-controls — fixed across all
  `Framework/styles/*.qss` themes.

## [01.02] - 2026-06-19

### Added
- A `log.txt` file is written into the backup folder. Every backup appends one
  timestamped line (`[YYYY-MM-DD HH:MM:SS] saved: <source> -> <backup>`) so the
  full save history accumulates over time.

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
