# -*- coding: utf-8 -*-
# Framework/qt/MOD_progress_qt_v01 - Cancel = 실행 전으로 자동 되돌리기 (run_undoable) 시험 (mayapy + 오프스크린 PySide2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_progress_cancel.py
# 판정 : Cancel 을 누르면 다음 진행 보고에서 멈추고, 작업 전체가 undo 한 번으로 되돌아가며(키 · 노드 · 시간),
#        **그 전에 사용자가 한 작업은 그대로** 남는다(첫 변경 전에 취소해도). 취소 안 하면 결과는 그대로이고 Ctrl+Z 한 번에 통째로.
# QApplication 은 maya.standalone.initialize() 보다 먼저 (qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402

APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, JUN_ALL)
from Framework.qt import JUN_mod_progress_qt   # noqa: E402
from Framework.qt.MOD_progress_qt_v01 import ProgressCancelled   # noqa: E402
from tools.A00120_FKIK.app.core.fkik_matcher import FKIKMatcher   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build():
    """tgt(키 1~100) 와 flw(키 없음). 사용자가 '그 전에 한 작업' = flw.sx = 3 (undo 대상이 아니어야 한다)."""
    cmds.file(new=True, force=True)
    cmds.playbackOptions(min=1, max=100, ast=1, aet=100)
    tgt = cmds.spaceLocator(name="tgt")[0]
    for t, v in ((1, 0), (100, 50)):
        cmds.setKeyframe(tgt, at="tx", t=t, v=v)
        cmds.setKeyframe(tgt, at="ry", t=t, v=v * 3)
    flw = cmds.spaceLocator(name="flw")[0]
    cmds.currentTime(7)
    cmds.flushUndo()
    cmds.setAttr(flw + ".sx", 3)              # 사용자의 직전 작업 (mayapy 는 시간 변경도 undo 큐에 쌓여 그보다 먼저)
    return tgt, flw


def keys(node):
    return cmds.keyframe(node, q=True, timeChange=True) or []


def dialog(cancellable=True):
    dlg = JUN_mod_progress_qt.JUN_mod_progress_qt_v01(None, title="Test", phases=[("Baking frames", 1)],
                                                      cancellable=cancellable)
    dlg.start()
    dlg.begin_phase()
    return dlg


def cancel_at(dlg, n):
    """n 번째 진행 보고에서 Cancel 버튼을 누르는 콜백 (사용자가 도중에 누른 것과 같다)."""
    base = dlg.callback()
    count = [0]

    def _cb(done, total, message=None):
        count[0] += 1
        if count[0] == n:
            dlg.btn_cancel.click()
        base(done, total, message)
    return _cb, count


# ---------------------------------------------------------------- 1. FKIK 베이크 도중 취소
tgt, flw = build()
dlg = dialog()
check("Cancel button visible when cancellable", not dlg.btn_cancel.isHidden())
cb, count = cancel_at(dlg, 20)
res, cancelled = dlg.run_undoable(FKIKMatcher.bake, [tgt], [flw], 1, 100, progress=cb)
dlg.finish()
check("cancelled flag + reverted", cancelled and dlg.reverted and res is None, (res, cancelled, dlg.reverted))
check("stopped right after the click (not all 100 frames)", count[0] <= 21, count[0])
check("no keys left on the follower", keys(flw) == [], keys(flw))
check("follower back to the pose before the bake", cmds.getAttr(flw + ".t")[0] == (0.0, 0.0, 0.0), cmds.getAttr(flw + ".t"))
check("current time restored", cmds.currentTime(q=True) == 7, cmds.currentTime(q=True))
check("the user's previous action is kept (sx = 3)", cmds.getAttr(flw + ".sx") == 3)
check("no marker node left", not cmds.ls("JUN_progress_marker*"))
cmds.undo()
check("one more Ctrl+Z = the user's previous action (queue intact)", cmds.getAttr(flw + ".sx") == 1)

# ---------------------------------------------------------------- 2. 첫 변경 전에 취소 (빈 덩어리 함정)
tgt, flw = build()
dlg = dialog()
dlg.btn_cancel.click()                         # 아무것도 하기 전에 취소
res, cancelled = dlg.run_undoable(FKIKMatcher.bake, [tgt], [flw], 1, 100, progress=dlg.callback())
dlg.finish()
check("cancel before any change: cancelled", cancelled and dlg.reverted)
check("cancel before any change: the user's previous action is NOT undone", cmds.getAttr(flw + ".sx") == 3)

# ---------------------------------------------------------------- 3. 예외를 삼키는 core 도 되돌린다


def swallowing_core(node, progress):
    for f in range(1, 51):
        try:
            cmds.setKeyframe(node, at="tx", t=f, v=f)
            progress(f, 50)
        except Exception:                       # noqa: BLE001 - BaseException 인 ProgressCancelled 는 지나간다
            pass
    return "done"


tgt, flw = build()
dlg = dialog()
cb, count = cancel_at(dlg, 10)
res, cancelled = dlg.run_undoable(swallowing_core, flw, cb)
dlg.finish()
check("core with `except Exception`: cancel still stops and reverts",
      cancelled and keys(flw) == [] and count[0] == 10, (count[0], keys(flw)[:3]))


def eat_everything(node, progress):
    for f in range(1, 51):
        try:
            cmds.setKeyframe(node, at="tx", t=f, v=f)
            progress(f, 50)
        except BaseException:                   # noqa: BLE001 - 끝까지 삼키는 core
            pass
    return "done"


tgt, flw = build()
dlg = dialog()
cb, count = cancel_at(dlg, 10)
res, cancelled = dlg.run_undoable(eat_everything, flw, cb)
dlg.finish()
check("core that swallows everything: was_cancelled -> still reverted", cancelled and keys(flw) == [], keys(flw)[:3])

# ---------------------------------------------------------------- 4. 취소 안 함 -> 결과 그대로, Ctrl+Z 한 번에 통째로
tgt, flw = build()
dlg = dialog()
res, cancelled = dlg.run_undoable(FKIKMatcher.bake, [tgt], [flw], 1, 100, progress=dlg.callback())
dlg.finish()
check("not cancelled: result returned, keys baked", res == 100 and not cancelled and len(keys(flw)) >= 100, res)
cmds.undo()
check("not cancelled: one Ctrl+Z removes the whole bake", keys(flw) == [] and cmds.getAttr(flw + ".sx") == 3)

# ---------------------------------------------------------------- 5. 취소 못 하는 팝업
tgt, flw = build()
dlg = dialog(cancellable=False)
check("non-cancellable: no Cancel button", dlg.btn_cancel.isHidden())
dlg._on_cancel()
res, cancelled = dlg.run_undoable(FKIKMatcher.bake, [tgt], [flw], 1, 20, progress=dlg.callback())
dlg.finish()
check("non-cancellable: runs to the end", res == 20 and not cancelled)

# ---------------------------------------------------------------- 6. C++ 한 번 호출(bakeResults) - 끝난 직후 멈추고 되돌림
from tools.A00110_animTool_V02.app.core.bake_manager import BakeManager   # noqa: E402
tgt, flw = build()
cmds.parentConstraint(tgt, flw)
dlg = dialog()
cb, count = cancel_at(dlg, 5)
res, cancelled = dlg.run_undoable(BakeManager.bake, [flw], 1, 100, progress=cb)
dlg.finish()
check("bakeResults path: cancelled and reverted", cancelled and dlg.reverted)
check("bakeResults path: no baked keys left", not cmds.keyframe(flw + ".tx", q=True), cmds.keyframe(flw + ".tx", q=True))

# ---------------------------------------------------------------- 7. undo 가 꺼져 있으면 멈추기만
tgt, flw = build()
cmds.undoInfo(state=False)
dlg = dialog()
cb, count = cancel_at(dlg, 10)
res, cancelled = dlg.run_undoable(FKIKMatcher.bake, [tgt], [flw], 1, 100, progress=cb)
dlg.finish()
cmds.undoInfo(state=True)
check("undo off: stops but cannot revert", cancelled and not dlg.reverted and count[0] <= 11)

# ---------------------------------------------------------------- 8. ProgressCancelled 는 BaseException
check("ProgressCancelled is not an Exception subclass",
      issubclass(ProgressCancelled, BaseException) and not issubclass(ProgressCancelled, Exception))

print("RESULT {0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
