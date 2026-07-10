---
name: maya-loadplugin-no-file
description: "Maya loadPlugin'd .py modules have no __file__; don't compute paths from it in plugins"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 7238afb4-fe86-488e-aae6-9c11e31308cb
---

Maya `cmds.loadPlugin("/path/to/foo.py")` executes the plugin module in a namespace where **`__file__` is NOT defined** (unlike a normal `import`). Computing paths via `os.path.dirname(__file__)` inside a loaded `.py` plugin raises `NameError: name '__file__' is not defined` and the plugin fails to load.

**Why:** Maya runs the plugin file through its plugin loader, not the normal import machinery, so module-level `__file__` is absent (observed in this project's Maya on Windows).

**How to apply:** In an OpenMaya 2.0 (`maya_useNewAPI = True`) MPxCommand plugin, don't derive `sys.path` or resource paths from `__file__`. Instead rely on the package already being importable — these plugins are loaded from the running tool (e.g. `mesh_io.ensure_undo_plugin()` in [[A00180_abSymMesh]]), so `JUN_All` is already on `sys.path` and a canonical absolute import like `from tools.A00180_abSymMesh.core import undo_bridge` works directly. Use a normal-import "bridge" module (single object identity) to pass payloads between the plugin copy and the tool, since loadPlugin's module is a separate instance from the tool's `import`.
