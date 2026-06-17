# Changelog — A00210_FileManager

All notable changes to this tool are documented here.

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
