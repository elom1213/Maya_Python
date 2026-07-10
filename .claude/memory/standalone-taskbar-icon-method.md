---
name: standalone-taskbar-icon-method
description: how to give a standalone PySide tool a Windows taskbar icon (SVG→QtSvg multi-size .ico + AppUserModelID)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 86b4dd47-dece-4682-9f0d-ad6b37a7e9ec
---

User confirmed and wants remembered: the method for giving a standalone PySide tool (arch B, run via `python launch.py` from terminal) its own **Windows taskbar icon**. First applied in `A00210_FileManager` v01.27.

Full reusable guide: `JUN_All/docs/taskbar_icon_guide.md` (read it before doing this again).

Key steps / gotchas:
- **Design SVG** in the app's theme tone (e.g. blue_dark), store `icon/TOOL.svg` + `.png` + `.ico` in the tool's `icon/` folder.
- **Render each size directly from the SVG** with `PySide6.QtSvg.QSvgRenderer` (offscreen), NOT by downscaling one raster — and build the `.ico` with the **largest frame as base** (`Pillow` `save(sizes=[...])`), else `QIcon.availableSizes()` only sees the base size. (Both were real bugs hit.)
- **AppUserModelID is the crux**: call `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Vendor.App.Name")` **before** `QApplication()`. Without it the terminal process is `python.exe`, so the taskbar shows the python icon even though `setWindowIcon` changed the window's own icon.
- Wire it in an `app/config/app_meta.py` (holds `APP_USER_MODEL_ID` + `icon_path()` that resolves in dev and PyInstaller `_MEIPASS`); set icon in both `launch.py` (app) and `main_window.py` (window); add `--icon` + `--add-data "icon;icon"` to `build_exe.bat`.

**Why:** taskbar icon needs both the icon AND the AUMID; the AUMID requirement is non-obvious and easy to miss.
**How to apply:** for a new standalone tool, follow the checklist in [[docs taskbar_icon_guide]]. This is for OS taskbar icons of standalone Qt apps — NOT Maya shelf icons (those are the 32×32 drag-drop flow in `docs/icon_plan.md`). Related: [[prefer-pyside-for-new-tools]], [[standalone-app-package-collision]].
