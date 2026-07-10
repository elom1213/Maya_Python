---
name: prefer-pyside-for-new-tools
description: "User prefers new/merged Maya tools built with PySide(Qt) UI, not maya.cmds UI"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9966ac63-dd35-4fbb-8a39-89e85f8514ba
---

When building or merging Maya tools, the user may require the UI be built with **PySide (Qt)** — architecture (B), QTabWidget — rather than maya.cmds UI, even when porting from a maya.cmds/MEL source.

**Why:** stated as a hard requirement mid-task ("제작한 툴은 pythonQT로 ui를 구성해야해") when merging the MEL JointTool V05.03 + A00060 into A00060_jointTool_V02.

There are TWO PySide flavors — confirm which the tool needs: (1) **in-Maya** PySide (arch B, clone `A00110_animTool`: launch.py run(), `__dragDrop_<id>.py` shelf installer, maya.cmds logic in app/core); (2) **standalone Windows app**, Maya-independent (clone `A00080_KWI_creator_V02`: launch.py main() with QApplication+sys.exit(app.exec()), PySide6, `launch.spec`/`build_exe.bat` PyInstaller exe, NO dragDrop/shelf/maya imports). User has explicitly asked for the standalone form ("A00080처럼 윈도우 운영체제에서 실행시킬 수 있는 툴") — e.g. A00210_FileManager.

**How to apply:** Reuse `Framework.qt.JUN_mod_tsl_qt` for list widgets, `from Framework.qt.qt import *` for PySide2/6 compat. Theme: in-Maya uses `ThemeManager.load_theme_to_widget(w, "coral_dark")`; standalone uses `ThemeManager.load_theme_dev(app, "dark")`. Keep core(logic)/ui(view) separated; standalone core must stay Qt/Maya-free. Confirm the UI framework AND in-Maya-vs-standalone if unstated. Related: [[ui-text-english-only]], [[docs-go-in-jun-all-docs]].
