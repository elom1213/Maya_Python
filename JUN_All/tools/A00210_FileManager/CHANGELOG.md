# Changelog — A00210_FileManager

All notable changes to this tool are documented here.

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
