# Changelog — A00490_KeyboardTool

All notable changes to this tool are documented here.

## [01.02] - 2026-10-26
### Added
- **`Run_KeyboardTool.bat` - double-click to open the tool.** Picks, in order: the tool's own
  environment `%USERPROFILE%\.jun_keyboardtool\venv`, then an installed 64-bit Python 3.10+ that
  already has PySide6 (`py -3.14 .. -3.10`, `python` on PATH - each one is run and its version read),
  and only when none has PySide6 builds the environment once (venv + PySide6 Essentials, outside the
  tool folder because of the 260-character path limit) and runs `app/selftest.py`. Then opens the
  window with `pythonw` (no console). Options `--setup` / `--force` / `--console` / `--no-launch`.
  A half-installed environment is removed on failure so the next run does not treat it as ready.
- `app/selftest.py` - Python / PySide6 / tool imports / offscreen window check (exit code 0 = pass).

## [01.01] - 2026-10-01
### Fixed
- **Every checked Chrome window now gets the keys, not only the one you clicked.** Chrome-type
  windows (Chrome, Edge, Whale, VS Code, Discord ...) ignore keys while they are not the active
  window. They are now brought to the front one after another - about 10 ms per window - so
  they look like they move together.

### Added
- **Send Method: Auto** (new default). Chrome-type windows are sent Foreground, all other windows
  Background. The start log marks each window `[front]` or `[back]`.
- Foreground waits until each window has actually read the key before moving to the next window,
  so keys no longer land in the wrong window (faster than the old fixed 30 ms hold, too).
- Background mode warns when Chrome-type windows are checked.

### Changed
- **Interval is now start-to-start.** With many windows a round takes some time; the wait after
  it is shortened so a 1 s interval still starts a round every second.

## [01.00] - 2026-10-01
### Added
- **First version.** Presses a list of keys in order - each key a set number of times with a set
  interval - and can loop the whole list (a set number of times, or until Stop).
- **Key Sequence table** (Key / Count / Interval). Click the Key field and press a key (Ctrl / Shift /
  Alt combos too), or pick one from the `...` menu. Add / Remove / Up / Down / Clear.
- **Target Windows** - check the windows that should get the keys; other windows are left alone.
  Filter by title or process, Refresh, Check All / Uncheck All. Or send to whatever window is active.
- **Send Method** - Background (posts key messages, no focus change, all windows at once) or
  Foreground (brings each window to the front and presses like a real keyboard).
- **Start Delay**, **Stop** button and the **F9** stop key (works from any window).
- **Presets** saved in `data/presets/` (sequence, loop, delay, method). `Down_Up_Loop` included.
- Windows 10 and 11. Taskbar icon.
