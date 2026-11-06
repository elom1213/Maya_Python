# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.54 - Follow 탭 Match Follow 진행 팝업 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_follow_progress.py
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

from tools.A00110_animTool_V02.app.core.follow_match_manager import FollowMatchManager as FM   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build(n=3):
    cmds.file(new=True, force=True)
    tgts, flws = [], []
    for k in range(n):
        t = cmds.group(empty=True, name="tgt{0}".format(k))
        for f, tx in ((1, 0), (24, 5 + k)):
            cmds.setKeyframe(t, attribute="translateX", time=f, value=tx)
        w = cmds.group(empty=True, name="flw{0}".format(k))
        cmds.setKeyframe(w, attribute="translate", time=1)
        tgts.append(t)
        flws.append(w)
    return tgts, flws


def run(blend):
    tgts, flws = build()
    calls = []
    cnt, msg = FM.match_follow(tgts, flws, 1, 24, blend, do_rotate=False,
                               progress=lambda d, t, m=None: calls.append((d, t, m)))
    return cnt, calls, flws


# 1. blend 1 : 단위 = 3 페어 x 24 프레임
cnt, calls, flws = run(1.0)
check("blend 1 : 3 matched", cnt == 3)
check("blend 1 : total = pairs x frames (72)", calls and all(c[1] == 72 for c in calls), calls[-1] if calls else None)
check("blend 1 : ends at total", calls[-1][0] == calls[-1][1])
check("progress never goes back", all(b[0] >= a[0] for a, b in zip(calls, calls[1:])))
check("message names follower k/N", any("Follower 2/3 : flw1" == c[2] for c in calls))
check("bake result unchanged", abs(cmds.getAttr(flws[2] + ".translateX", time=24) - 7.0) < 1e-6)

# 2. blend < 1 : 원본 읽기 패스까지 x2
cnt, calls, _ = run(0.5)
check("blend 0.5 : total = pairs x frames x 2 (144)", calls and calls[-1][1] == 144 and calls[-1][0] == 144)
check("blend 0.5 : monotonic", all(b[0] >= a[0] for a, b in zip(calls, calls[1:])))

# 3. progress 없이도 그대로
tgts, flws = build()
cnt, msg = FM.match_follow(tgts, flws, 1, 24, 1.0, do_rotate=False)
check("no progress callback -> works as before", cnt == 3)

# 4. UI : 팝업이 뜨고 닫힌다, 로그에 경과 시간
from tools.A00110_animTool_V02.app.ui import main_window as mw   # noqa: E402
from Framework.qt import JUN_mod_progress_qt   # noqa: E402
seen = {"start": 0, "finish": 0, "steps": 0, "title": None}
Dlg = JUN_mod_progress_qt.JUN_mod_progress_qt_v01
orig_start, orig_finish, orig_step = Dlg.start, Dlg.finish, Dlg.step


def _start(self):
    seen["start"] += 1
    seen["title"] = self.windowTitle()
    return orig_start(self)


def _finish(self):
    seen["finish"] += 1
    return orig_finish(self)


def _step(self, *a, **k):
    seen["steps"] += 1
    return orig_step(self, *a, **k)


Dlg.start, Dlg.finish, Dlg.step = _start, _finish, _step
tgts, flws = build()
w = mw.MainWindow()
w.show()
w.follow_tgt_tsl.set_items(tgts)
w.follow_flw_tsl.set_items(flws)
w.le_follow_start.setText("1")
w.le_follow_end.setText("24")
w.on_follow_bake()
check("ui : popup started + finished once", seen["start"] == 1 and seen["finish"] == 1, seen)
check("ui : popup title 'Match Follow', steps reported", seen["title"] == "Match Follow" and seen["steps"] >= 72, seen)
check("ui : keys baked", abs(cmds.getAttr(flws[1] + ".translateX", time=24) - 6.0) < 1e-6)
log = w.te_log.toPlainText() if hasattr(w, "te_log") else ""
check("ui : log has elapsed time", "matched over" in log and "s)" in log.splitlines()[-1] if log else False, log[-200:])
w.close()

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
