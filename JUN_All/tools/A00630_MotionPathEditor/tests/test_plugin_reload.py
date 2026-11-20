# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 옛 플러그인이 마야에 남아 있을 때 (v01.07)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_plugin_reload.py
# 사용자 보고 1: 마야를 켠 채 툴만 새 버전이 되면 v01.00~02 플러그인(1.0, junMotionPathDirty 없음)이 남아
#   "[FAIL] Drag : module 'maya.cmds' has no attribute 'junMotionPathDirty'".
# 사용자 보고 2 (v01.07 첫 판): 같은 경로에서 다시 읽으면 새 코드인데도 pluginInfo -version 이 "1.0" 그대로라
#   "옛것" 으로 보고 "Could not load the plugin" → 창이 안 열림 + closeEvent 에서 'speed_panel' 없음 에러.
# 실제 상황처럼 **같은 경로**의 파일을 옛 내용 → 새 내용으로 바꿔 시험한다 (임시 폴더, draw_nodes.PLUGIN_FILE 을 그쪽으로).
import io
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtGui import QCloseEvent   # noqa: E402
from PySide2.QtWidgets import QApplication, QWidget   # noqa: E402
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

new_src = io.open(draw_nodes.PLUGIN_FILE, encoding="utf-8").read()
old_src = new_src.replace('PLUGIN_VERSION = "{0}"'.format(plugin_source.PLUGIN_VERSION), 'PLUGIN_VERSION = "1.0"')
old_src = "\n".join(l for l in old_src.split("\n")
                    if "DIRTY_COMMAND_NAME, JunMotionPathDirtyCmd" not in l and "deregisterCommand(DIRTY_COMMAND_NAME)" not in l
                    and "VERSION_COMMAND_NAME, JunMotionPathVersionCmd" not in l and "deregisterCommand(VERSION_COMMAND_NAME)" not in l)
plug_dir = tempfile.mkdtemp(prefix="a00630_plug_")
PLUG = os.path.join(plug_dir, "jun_motion_path.py")
draw_nodes.PLUGIN_FILE = PLUG                     # 툴이 읽는 플러그인 = 이 파일 (내용을 옛 → 새로 바꾼다)


def write(text):
    io.open(PLUG, "w", encoding="utf-8").write(text)


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
write(old_src)
cmds.loadPlugin(PLUG, quiet=True)
check("old plugin loaded (1.0, no junMotionPathDirty, no version command)",
      draw_nodes.loaded_plugin_version() == "1.0" and not draw_nodes.command_exists("junMotionPathDirty")
      and not draw_nodes.command_exists("junMotionPathVersion"))
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
check("old plugin: dragging fails like report 1", "junMotionPathDirty" in err, err)

# ---- 툴 업데이트: 같은 경로의 파일이 새 내용이 된다 → 툴 창을 열면 바꿔 읽는다
write(new_src)
from tools.A00630_MotionPathEditor.app.ui import main_window as mw   # noqa: E402
logs = []
mw.MainWindow.log = lambda self, text: logs.append(text)
win = mw.MainWindow()
check("opening the tool replaces the old plugin (same path)", draw_nodes.plugin_is_current(NAME) and
      draw_nodes.loaded_plugin_version() == plugin_source.PLUGIN_VERSION, draw_nodes.loaded_plugin_version())
check("Maya's pluginInfo version label is stale after a same-path reload (why the command exists)",
      cmds.pluginInfo(NAME, q=True, version=True) == "1.0", cmds.pluginInfo(NAME, q=True, version=True))
check("the window says so once", sum("Replaced the old Motion Path plugin (v1.0)" in m for m in logs) == 1, logs)
check("old draw nodes gone", not cmds.ls(type="junMotionPath"))
cmds.junMotionPathSetKeys()                     # 새 플러그인 명령도 undo 큐에 (다음 열기에서 다시 읽지 않아야 한다)
win.close()
app.processEvents()
check("a second ensure_plugin keeps it (no reload, undo queue kept)",
      draw_nodes.ensure_plugin() == NAME and not draw_nodes.replaced_plugin)
logs[:] = []
win = mw.MainWindow()
check("reopening the tool: no replace message", not any("Replaced" in m for m in logs), logs)
win.close()
app.processEvents()

cache = pc.PathCache(node, 1, 120)
cache.rebake()
key = cache.keys[1]
p0 = cache.points[key.row].copy()
cmds.flushUndo()
check("dragging works after the reload", drag_once(cache, key) and abs(world_pivot(node, key.t)[0] - (p0[0] + 1.0)) < 1e-6)
cmds.undo()
check("and undoes in one step", np.abs(np.array(world_pivot(node, key.t)) - p0).max() < 1e-6)

# ---- 사용자 보고 2의 두 번째 에러: __init__ 가 중간에 실패한 창을 닫아도 에러가 없다
half = mw.MainWindow.__new__(mw.MainWindow)
QWidget.__init__(half)
try:
    half.closeEvent(QCloseEvent())
    err = ""
except Exception as exc:                       # noqa: BLE001
    err = str(exc)
check("closing a half-built window raises nothing", err == "", err)

_common.finish()
