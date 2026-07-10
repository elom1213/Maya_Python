---
name: standalone-app-package-collision
description: "standalone Qt tools must import via tools.<tool>.app.* (not bare `app`) or they collide in one interpreter"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3860957e-d1c4-4524-95a0-25999701baed
---

Standalone PySide tools must NOT import their package as the bare top-level `app`
(`from app.ui.main_window import MainWindow`, `from app.core import …`). Every
standalone tool's folder is named `app/`, so two tools loaded in the **same
interpreter** (Maya, or a shared launcher) both try to own `sys.modules['app']`
— the first wins, and the second fails with `ModuleNotFoundError: No module
named 'app.core.X'` or shows the wrong window.

**Correct pattern** (matches in-Maya tools A00110 and templates A00004/A00008):
- `launch.py`: keep `JUN_All` on `sys.path`, import via the tool's unique path —
  `from tools.<ToolName>.app.ui.main_window import MainWindow`
  (release_builder_QT lives under `dev/` → `from dev.release_builder_QT.app...`).
- Internal modules: use **relative imports** — `from ..core import …`,
  `from ..config.version import VERSION`, `from .file_table import FileTable`.
- Do NOT add the tool folder itself (`TOOL_ROOT`) to `sys.path`.

Fixed 2026-06-18 in A00080, A00210, A00220, release_builder_QT. This is the same
class of bug as the dragDrop `config.py`/basename collision noted in CLAUDE.md §3.
Related: [[prefer-pyside-for-new-tools]], [[worklog-maintenance]].
