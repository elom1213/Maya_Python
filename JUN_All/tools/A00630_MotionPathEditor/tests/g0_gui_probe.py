# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 매니퓰레이터 · 폴오프 계획서 G0 의 **마야 GUI 실측** (G0-1 점마다 색 · G0-2 b 키 · G0-3 핫키 정보)
#
# 마야 스크립트 에디터(Python)에서:
#     import sys; sys.path.insert(0, r"C:\Users\USER\Desktop\JP\0030_maya_python_JUN\Maya_Python\JUN_All\tools\A00630_MotionPathEditor\tests")
#     import g0_gui_probe; g0_gui_probe.start()
#     ... (안내대로 키 · 마우스) ...
#     g0_gui_probe.stop()
#
# 새 씬에서 한다(start 가 새 씬을 연다 - 저장 안 한 작업이 있으면 먼저 저장). 결과는 스크립트 에디터와
# %TEMP%\a00630_g0_probe.txt 에 남는다. stop() 이 이벤트 필터 · 컨텍스트 · 임시 플러그인을 모두 내린다.
# 마야 설정(핫키 · 소프트 셀렉션)은 바꾸지 않는다 - 읽기만 한다.
import io
import os
import sys
import tempfile
import time

import maya.cmds as cmds

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:                                        # pragma: no cover
    from PySide6 import QtCore, QtWidgets

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "g0_probe_plugin.py")
LOG_PATH = os.path.join(tempfile.gettempdir(), "a00630_g0_probe.txt")
CTX = "junG0ProbeCtx"
KEYS = {QtCore.Qt.Key_B: "B", QtCore.Qt.Key_W: "W", QtCore.Qt.Key_E: "E"}
TYPES = {QtCore.QEvent.KeyPress: "KeyPress", QtCore.QEvent.KeyRelease: "KeyRelease",
         QtCore.QEvent.ShortcutOverride: "ShortcutOverride"}

_state = {"filter": None, "lines": [], "b_held": False, "consume": True, "t0": 0.0, "press": None}


def log(text):
    line = "[{0:7.3f}] {1}".format(time.time() - _state["t0"], text)
    _state["lines"].append(line)
    print(line)


def soft_state():
    return "softSelect sse={0} ssd={1:.4f}".format(cmds.softSelect(q=True, softSelectEnabled=True),
                                                  cmds.softSelect(q=True, softSelectDistance=True))


class KeyProbe(QtCore.QObject):
    """B / W / E 이벤트를 받는다. consume=True 면 KeyPress · KeyRelease · ShortcutOverride 를 먹어서 마야 핫키로 안 보낸다(시험)."""

    def eventFilter(self, obj, event):
        et = event.type()
        if et not in TYPES:
            return False
        try:
            key = event.key()
        except Exception:                                  # noqa: BLE001
            return False
        if key not in KEYS:
            return False
        if cmds.currentCtx() != CTX:                       # 프로브 컨텍스트일 때만 - 다른 툴이면 마야 그대로
            return False
        name = KEYS[key]
        rep = event.isAutoRepeat()
        if not rep:
            log("{0:<16} {1}  on {2} ({3})  | {4}".format(TYPES[et], name, type(obj).__name__, obj.objectName(), soft_state()))
        if key == QtCore.Qt.Key_B and not rep:
            if et == QtCore.QEvent.KeyPress:
                _state["b_held"] = True
            elif et == QtCore.QEvent.KeyRelease:
                _state["b_held"] = False
                QtCore.QTimer.singleShot(300, lambda: log("  300 ms after B release | " + soft_state()))
        if _state["consume"]:
            if et == QtCore.QEvent.ShortcutOverride:
                event.accept()                             # 단축키로 처리하지 말고 KeyPress 로 달라
            return True
        return False


def _press():
    x, y = cmds.draggerContext(CTX, q=True, anchorPoint=True)[:2]
    _state["press"] = (x, y)
    log("ctx press   button={0} modifier={1} b_held={2} at ({3:.0f}, {4:.0f})".format(
        cmds.draggerContext(CTX, q=True, button=True), cmds.draggerContext(CTX, q=True, modifier=True),
        _state["b_held"], x, y))


def _drag():
    pass


def _release():
    x, y = cmds.draggerContext(CTX, q=True, dragPoint=True)[:2]
    x0, y0 = _state["press"] or (x, y)
    log("ctx release b_held={0} dx={1:.0f} dy={2:.0f} | {3}".format(_state["b_held"], x - x0, y - y0, soft_state()))


def _hotkey_info():
    for key, alt, ctl in (("b", False, False), ("w", False, False), ("e", False, False)):
        try:
            name = cmds.hotkey(key, q=True, name=True)
            rel = cmds.hotkey(key, q=True, releaseName=True)
        except Exception as exc:                           # noqa: BLE001
            name, rel = "(error {0})".format(exc), ""
        log("hotkey {0}: press={1!r} release={2!r}".format(key, name, rel))
    try:
        log("hotkeySet current = {0!r}".format(cmds.hotkeySet(q=True, current=True)))
    except Exception as exc:                               # noqa: BLE001
        log("hotkeySet query failed: {0}".format(exc))


def start(consume=True):
    """consume=True: B/W/E 를 먹어 마야 핫키를 막아 본다(계획서 §3-5 안 A). False: 보기만(마야 핫키도 그대로 돈다)."""
    stop(quiet=True)
    _state.update(lines=[], b_held=False, consume=bool(consume), t0=time.time(), press=None)
    log("A00630 G0 GUI probe - consume={0} - Maya {1}".format(consume, cmds.about(version=True)))
    cmds.file(new=True, force=True)
    # G0-1 점마다 색
    if not cmds.pluginInfo(PLUGIN, q=True, loaded=True):
        cmds.loadPlugin(PLUGIN)
    tr = cmds.createNode("transform", name="g0Probe")
    cmds.createNode("junMotionPathProbe", name="g0ProbeShape", parent=tr)
    cube = cmds.polyCube(name="g0Occluder", width=3, height=6, depth=1)[0]
    cmds.move(0, 2, 2, cube)                               # 세 줄 가운데를 앞에서 가린다 → x-ray 면 그래도 보여야
    cmds.viewFit(all=True)
    # G0-2 키
    _hotkey_info()
    log("start | " + soft_state())
    app = QtWidgets.QApplication.instance()
    _state["filter"] = KeyProbe()
    app.installEventFilter(_state["filter"])
    if cmds.draggerContext(CTX, exists=True):
        cmds.deleteUI(CTX)
    cmds.draggerContext(CTX, pressCommand=_press, dragCommand=_drag, releaseCommand=_release,
                        space="screen", cursor="crossHair", undoMode="step")
    cmds.setToolTo(CTX)
    msg = ("\nG0 probe is running (consume={0}). In the viewport:\n"
           "  1. Look at the three colored rows (yellow in the middle -> red at the ends). The cube hides the middle.\n"
           "  2. Tap B once (press and release).\n"
           "  3. Hold B, drag with the LEFT mouse button left/right, release the mouse, then release B.\n"
           "  4. Drag with the left mouse button without B.\n"
           "  5. Tap W, then E.\n"
           "  Then run: g0_gui_probe.stop()   and tell what you saw in step 1.\n").format(consume)
    print(msg)


def stop(quiet=False):
    f = _state.get("filter")
    if f is not None:
        try:
            QtWidgets.QApplication.instance().removeEventFilter(f)
        except Exception:                                  # noqa: BLE001
            pass
        _state["filter"] = None
    try:
        if cmds.currentCtx() == CTX:
            cmds.setToolTo("selectSuperContext")
        if cmds.draggerContext(CTX, exists=True):
            cmds.deleteUI(CTX)
    except Exception:                                      # noqa: BLE001
        pass
    if quiet:
        return
    log("stop | " + soft_state())
    try:
        for n in cmds.ls(type="junMotionPathProbe") or []:
            cmds.delete(cmds.listRelatives(n, parent=True))
        cmds.flushUndo()
        cmds.unloadPlugin(os.path.basename(PLUGIN).replace(".py", ""))
    except Exception as exc:                               # noqa: BLE001
        log("plugin unload: {0}".format(exc))
    with io.open(LOG_PATH, "w", encoding="utf-8") as fh:
        fh.write(u"\n".join(_state["lines"]) + u"\n")
    print("\nSaved: " + LOG_PATH)
    sys.stdout.flush()

