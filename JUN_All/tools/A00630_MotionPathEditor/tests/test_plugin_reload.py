# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 옛 플러그인이 마야에 남아 있을 때 (v01.07)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_plugin_reload.py
# 사용자 보고: 마야를 켠 채 툴만 새 버전이 되면 v01.00~02 플러그인(1.0, junMotionPathDirty 없음)이 남아
#   "[FAIL] Drag : module 'maya.cmds' has no attribute 'junMotionPathDirty'".
# 옛 플러그인 = 지금 플러그인 파일에서 버전을 1.0 으로, junMotionPathDirty 등록을 뺀 사본 (임시 폴더).
import io
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
import scenes   # noqa: E402
from _common import check, world_pivot   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_nodes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_cache as pc   # noqa: E402
from tools.A00630_MotionPathEditor.app.core.edit_session import DragSession   # noqa: E402
from tools.A00630_MotionPathEditor.app.plugin import jun_motion_path as plugin_source   # noqa: E402

cmds.undoInfo(state=True, infinity=True)
NAME = "jun_motion_path"

src = io.open(draw_nodes.PLUGIN_FILE, encoding="utf-8").read()
old_src = src.replace('PLUGIN_VERSION = "{0}"'.format(plugin_source.PLUGIN_VERSION), 'PLUGIN_VERSION = "1.0"')
old_src = "\n".join(l for l in old_src.split("\n") if "DIRTY_COMMAND_NAME, JunMotionPathDirtyCmd" not in l
                    and "deregisterCommand(DIRTY_COMMAND_NAME)" not in l)
old_dir = tempfile.mkdtemp(prefix="a00630_oldplug_")
old_file = os.path.join(old_dir, "jun_motion_path.py")
io.open(old_file, "w", encoding="utf-8").write(old_src)


def drag_once(cache, key, dx=1.0):
    s = DragSession([(cache, [key.t])])
    s.begin()
    s.update(np.array([dx, 0.0, 0.0]))
    try:
        return s.commit()
    except Exception:
        s.cancel()
        raise


names = scenes.hierarchy(120)
node = names["ctrl"]

# ---- 옛 툴로 시작한 마야 세션: 옛 플러그인 + 그리기 노드 + undo 큐에 옛 명령
if cmds.pluginInfo(NAME, q=True, loaded=True):
    draw_nodes.delete_all()
    cmds.flushUndo()
    cmds.unloadPlugin(NAME)
cmds.loadPlugin(old_file, quiet=True)
check("old plugin loaded (1.0, no junMotionPathDirty)",
      cmds.pluginInfo(NAME, q=True, version=True) == "1.0" and not draw_nodes.command_exists("junMotionPathDirty"))
check("old plugin is not current", not draw_nodes.plugin_is_current(NAME))
draw_nodes.create_node("k", "ctrl")
cmds.junMotionPathSetKeys()
cache = pc.PathCache(node, 1, 120)
cache.rebake()
try:
    drag_once(cache, cache.keys[1])
    err = ""
except Exception as exc:                       # noqa: BLE001
    err = str(exc)
check("old plugin: dragging fails like the report", "junMotionPathDirty" in err, err)

# ---- 툴 창을 열면 바꿔 읽는다 (그리기 노드 · 큐의 옛 명령이 있어도)
from tools.A00630_MotionPathEditor.app.ui import main_window as mw   # noqa: E402
logs = []
mw.MainWindow.log = lambda self, text: logs.append(text)
win = mw.MainWindow()
check("opening the tool replaces the old plugin", draw_nodes.plugin_is_current(NAME) and
      cmds.pluginInfo(NAME, q=True, version=True) == plugin_source.PLUGIN_VERSION)
check("the new plugin comes from the tool folder",
      os.path.normcase(os.path.abspath(cmds.pluginInfo(NAME, q=True, path=True))) == os.path.normcase(draw_nodes.PLUGIN_FILE))
check("the window says so once", sum("Replaced the old Motion Path plugin (v1.0)" in m for m in logs) == 1, logs)
check("old draw nodes gone", not cmds.ls(type="junMotionPath"))
win.close()
app.processEvents()
check("a second ensure_plugin keeps it (no reload)", draw_nodes.ensure_plugin() == NAME and not draw_nodes.replaced_plugin)

cache = pc.PathCache(node, 1, 120)
cache.rebake()
key = cache.keys[1]
p0 = cache.points[key.row].copy()
cmds.flushUndo()
check("dragging works after the reload", drag_once(cache, key) and abs(world_pivot(node, key.t)[0] - (p0[0] + 1.0)) < 1e-6)
cmds.undo()
check("and undoes in one step", np.abs(np.array(world_pivot(node, key.t)) - p0).max() < 1e-6)

_common.finish()
