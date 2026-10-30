# -*- coding: utf-8 -*-
# A00400_CurveTool v01.30 - Display > Shape Edit `Always Draw On Top` (nurbsCurve.alwaysDrawOnTop) 시험 (mayapy 2024)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_draw_on_top.py
# 코어(set_always_draw_on_top / get_always_draw_on_top) + Shape Edit 탭 UI 스모크(오프스크린 Qt).
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다.
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

from tools.A00400_CurveTool.app.core import curve_manager as cm   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def top(shape):
    return bool(cmds.getAttr(shape + ".alwaysDrawOnTop"))


def scene():
    cmds.file(new=True, force=True)
    a = cmds.circle(n="ctl_a", ch=False)[0]
    b = cmds.circle(n="ctl_b", ch=False)[0]
    # 셰이프 둘인 커브(Combine 결과 같은 것)
    c = cmds.circle(n="ctl_c", ch=False)[0]
    extra = cmds.circle(ch=False)[0]
    extra_shape = cmds.listRelatives(extra, s=True, f=True)[0]
    cmds.parent(extra_shape, c, s=True, r=True)
    cmds.delete(extra)
    cube = cmds.polyCube(n="notACurve", ch=False)[0]
    grp = cmds.group(em=True, n="emptyGrp")
    return a, b, c, cube, grp


# ----------------------------------------------------------------------
# 1. 코어 - ON / OFF / toggle, 트랜스폼이든 셰이프든, 셰이프 여럿, 커브 아닌 것
# ----------------------------------------------------------------------
a, b, c, cube, grp = scene()
sa = cmds.listRelatives(a, s=True, f=True)[0]
sb = cmds.listRelatives(b, s=True, f=True)[0]
sc = cmds.listRelatives(c, s=True, f=True)
check("default is off", not top(sa) and not top(sb))

changed, skipped = cm.set_always_draw_on_top([a, b], True)
check("ON via transforms : 2 shapes changed", sorted(s for s, _v in changed) == sorted([sa, sb]) and all(v for _s, v in changed), changed)
check("ON via transforms : attribute is on", top(sa) and top(sb))
check("ON via transforms : nothing skipped", skipped == [], skipped)

changed, skipped = cm.set_always_draw_on_top([a], True)
check("ON again : already on -> skipped with reason, nothing changed", changed == [] and skipped == [(sa, "already on")], (changed, skipped))

changed, skipped = cm.set_always_draw_on_top([sa], False)
check("OFF via the shape name itself", changed == [(sa, False)] and not top(sa), changed)

changed, skipped = cm.set_always_draw_on_top([c], True)
check("curve with two shapes : both set", len(changed) == 2 and all(top(s) for s in sc), changed)

changed, skipped = cm.set_always_draw_on_top([a, b, c], None)
check("toggle : a off->on, b on->off, c(2) on->off", sorted(changed) == sorted([(sa, True), (sb, False)] + [(s, False) for s in sc]), changed)
check("toggle : scene matches", top(sa) and not top(sb) and not any(top(s) for s in sc))

changed, skipped = cm.set_always_draw_on_top([cube, grp, "doesNotExist", a], True)
check("non-curves are skipped with 'not a curve' and the curve is still processed",
      [(n, w) for n, w in skipped if w == "not a curve"] == [(cube, "not a curve"), (grp, "not a curve"), ("doesNotExist", "not a curve")]
      and changed == [] and [w for n, w in skipped if n == sa] == ["already on"], (changed, skipped))

check("get : on", cm.get_always_draw_on_top(a) is True)
check("get : off", cm.get_always_draw_on_top(b) is False)
check("get : not a curve -> None", cm.get_always_draw_on_top(cube) is None)

cmds.setAttr(sb + ".alwaysDrawOnTop", lock=True)
changed, skipped = cm.set_always_draw_on_top([b], True)
check("locked attribute : skipped 'locked or connected', not changed", changed == [] and skipped == [(sb, "locked or connected")] and not top(sb), skipped)
cmds.setAttr(sb + ".alwaysDrawOnTop", lock=False)

check("empty / None input", cm.set_always_draw_on_top([], True) == ([], []) and cm.set_always_draw_on_top(None, False) == ([], []))

# ----------------------------------------------------------------------
# 2. UI - Shape Edit 탭 버튼이 코어를 부르고 한 번 누름이 undo 한 스텝
# ----------------------------------------------------------------------
from Framework.qt.qt import *   # noqa: E402,F401
from tools.A00400_CurveTool.app.ui.shape_edit_tab import ShapeEditTab   # noqa: E402

logs = []
tab = ShapeEditTab(log_callback=logs.append)
for name in ("btn_top_on", "btn_top_off", "btn_top_toggle"):
    check("UI : widget %s exists" % name, isinstance(getattr(tab, name, None), QPushButton))
check("UI : button labels are English", (tab.btn_top_on.text(), tab.btn_top_off.text(), tab.btn_top_toggle.text()) == ("On", "Off", "Toggle"))

a, b, c, cube, grp = scene()
sa = cmds.listRelatives(a, s=True, f=True)[0]
sb = cmds.listRelatives(b, s=True, f=True)[0]
sc = cmds.listRelatives(c, s=True, f=True)

tab.btn_top_on.click()
check("UI : empty list -> warning, nothing done", logs and logs[-1].startswith("[WARN] Curve list is empty"), logs[-1:] )

tab.tsl.set_items([a, b, c, cube])
cmds.undoInfo(state=True, infinity=True)
cmds.flushUndo()
tab.btn_top_on.click()
check("UI : On -> all 4 shapes on", top(sa) and top(sb) and all(top(s) for s in sc))
check("UI : On log", any("Always Draw On Top ON -> 4 curve shape(s)." in m for m in logs), logs[-2:])
check("UI : non-curve reported in log", any("Skipped 1: notACurve (not a curve)" in m for m in logs), logs[-1:])
cmds.undo()
check("UI : one Ctrl+Z undoes the whole press (4 shapes)", not top(sa) and not top(sb) and not any(top(s) for s in sc))
cmds.redo()
check("UI : redo", top(sa) and top(sb) and all(top(s) for s in sc))

tab.btn_top_off.click()
check("UI : Off -> all off", not top(sa) and not top(sb) and not any(top(s) for s in sc))
cmds.setAttr(sa + ".alwaysDrawOnTop", True)
tab.btn_top_toggle.click()
check("UI : Toggle -> a off, others on", not top(sa) and top(sb) and all(top(s) for s in sc))
check("UI : Toggle log counts", any("toggled on 4 curve shape(s): 3 now on, 1 now off." in m for m in logs), logs[-2:])
tab.btn_top_on.click()
check("UI : On when 3 already on -> 1 changed + 'already' count", any("ON -> 1 curve shape(s)." in m for m in logs) and any("3 shape(s) were already ON." in m for m in logs), logs[-3:])

# 리네임 뒤에도 UUID 로 같은 커브를 잡는다
cmds.rename(a, "ctl_a_renamed")
sa2 = cmds.ls(cmds.listRelatives("ctl_a_renamed", s=True, f=True)[0], l=True)[0]
tab.btn_top_off.click()
check("UI : renamed curve still found by UUID", not top(sa2))

n_fail = R.count(False)
print("\n%d checks, %d failed" % (len(R), n_fail))
maya.standalone.uninitialize()
sys.exit(1 if n_fail else 0)
