# Changelog — A00220_BackupTool

## [01.09] - 2026-07-01

### Added
- **The dino now marks the moment a user saves a watched file** with a short
  accent-colored hop (`DinoWidget.notify_save()`), triggered from `_on_fs_changed`
  the instant a save is detected on disk. This is visually distinct from the two
  existing states — grey running/auto-jump (tool active) and the 360° spin (a
  backup actually happened) — so you can now tell the *save* moment apart from the
  *backup* moment, which the Save Delay (v01.08) separates by several seconds. The
  hop is shorter and lower than the periodic auto-jump and is drawn in the theme
  highlight color (falls back to `#4CAF50`). Priority ladder is spin > save-hop >
  jump > auto-jump; a save-hop yields to an in-progress backup spin. Only appears
  in Auto Backup mode (the periodic mode has no per-save detection).

### Removed
- Dead `DinoWidget.hop()` method (unused since v01.06 replaced it with `spin()`);
  its role is now filled by the distinct `notify_save()` hop.

## [01.08] - 2026-07-01

### Changed
- **Auto Backup now waits a settle delay before backing up a saved file**, instead
  of copying it almost immediately (~300ms debounce). When a save is detected, the
  file's backup is scheduled for `now + Save Delay` seconds; if the same file is
  saved again during the wait, its schedule is pushed to `last save + delay` (it
  backs up only once it has been quiet). This guards against the PC crashing at
  the moment of a save: the crash leaves the Maya file half-written/corrupted, but
  because the pending backup is an in-process timer, a crash within the delay
  window kills it too — so the corrupted file is **not** copied over the last good
  backup. The scheduler is a per-file due-time map polled once a second (only runs
  while backups are pending); the periodic interval timer is unchanged.

### Added
- **Save Delay (sec) setting** (Settings, default `10`, range `0–600`). Auto Backup
  only. `0` backs up on the next poll (~1s). Persisted in prefs (`save_delay`).

### Changed
- **Target Files list now shows file names only**, not full paths. Each entry
  displays `os.path.basename(path)` while the full path is kept on the item
  (`Qt.UserRole`) and shown as a tooltip on hover. Backup, duplicate-checking and
  prefs still use the full path, so behavior is unchanged — only the display is
  shortened so long paths no longer overflow the narrow list.

### Added
- **Right-click → Reveal in File Explorer** on a Target Files entry. Opens the OS
  file browser with the file selected (`explorer /select,` on Windows; `open -R`
  on macOS; `xdg-open` of the parent on Linux). Warns if the file no longer exists.

## [01.06] - 2026-06-22

### Changed
- **The dino now spins a full 360° in the air whenever a file is actually backed
  up**, so a successful backup is clearly visible. Previously the dino only did a
  small hop on each save cycle, which was easy to miss and fired even when nothing
  was copied. The spin (`DinoWidget.spin()`) is triggered from `_backup_targets`
  only when at least one file was backed up (`ok > 0`), not merely on entering the
  Saving state. The widget reserves a bit more height so the rotating sprite never
  clips at its corners, and the spin suppresses the periodic auto-jump while it
  plays. Running (jogging in place) and stopped (standing) states are unchanged.

## [01.05] - 2026-06-19

### Changed
- **Auto Backup is now save-driven.** A file is backed up the moment it is saved
  (changed on disk), instead of waiting for the next interval tick. Target files
  are watched with `QFileSystemWatcher`; changes are debounced (~300ms) to
  coalesce burst writes and tolerate temp-file replace saves, then re-added to
  the watch list. The periodic interval timer now acts as a fallback that catches
  any change the watcher missed. Toggling Auto Backup while running starts/stops
  watching live.

## [01.04] - 2026-06-19

### Changed
- **Control** — the status text (`Deactive` / `Active...` / `Saving`) is replaced
  by a **Chrome-Dino style T-Rex animation**. When backup is running the dino runs
  in place (alternating legs + scrolling ground) and jumps periodically; when
  stopped it stands still; it does an extra hop on each save. Drawn with QPainter
  from a code-embedded pixel bitmap (new `app/ui/dino_widget.py`) — no image assets,
  theme-independent, nothing extra to bundle in the exe.

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
