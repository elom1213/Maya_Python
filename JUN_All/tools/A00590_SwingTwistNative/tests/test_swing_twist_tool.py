# -*- coding: utf-8 -*-
# A00590_SwingTwistNative v01.00 - 코어(검사 · 홀더 · undo · 저장) + UI 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_swing_twist_tool.py
# 원본 플러그인과의 수치 비교는 test_swing_twist_golden.py.
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import maya_swing_twist as ST   # noqa: E402
from tools.A00590_SwingTwistNative.app.ui import main_window as MW   # noqa: E402

R = []
TMP = tempfile.mkdtemp(prefix="a00590_")


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def raises(fn, *args, **kw):
    try:
        fn(*args, **kw)
    except ST.SwingTwistError as exc:
        return str(exc)
    return None


def joint(name):
    cmds.select(clear=True)
    return cmds.joint(name=name)


def scene():
    cmds.file(new=True, force=True)
    names = ["upperarm", "lowerarm", "swingOut", "tw0", "tw1", "tw2"]
    return [joint(n) for n in names]


def close(a, b, tol=1e-9):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


# ---------------------------------------------------------------- 1. 입력 검사
start, end, sw, t0, t1, t2 = scene()
check("1 missing start", raises(ST.build, "x", "", None, sw) is not None)
check("1 nothing to drive", raises(ST.build, "x", start) is not None)
check("1 blend count mismatch", raises(ST.build, "x", start, None, None, 0.0, [t0, t1], [0.5]) is not None)
check("1 missing node", raises(ST.build, "x", start, None, "nope") is not None)
check("1 duplicate output", raises(ST.build, "x", start, None, t0, 0.0, [t0], [0.5]) is not None)
check("1 output = input (cycle)", raises(ST.build, "x", start, None, start) is not None)
cmds.setKeyframe(t2 + ".rotateX", time=1, value=5)
msg = raises(ST.build, "x", start, None, None, 0.0, [t2], [0.5])
check("1 output rotate already driven (child key)", msg and "already driven" in msg, msg)
cmds.setAttr(t1 + ".rotateY", lock=True)
msg = raises(ST.build, "x", start, None, None, 0.0, [t1], [0.5])
check("1 locked output channel", msg and "locked" in msg, msg)
check("1 failed builds leave no nodes", ST.list_holders() == [] and not cmds.ls(type="quatSlerp"))

# ---------------------------------------------------------------- 2. 빌드 · 홀더
start, end, sw, t0, t1, t2 = scene()
logs = []
cmds.setAttr(start + ".rotateOrder", 2)
holder = ST.build("upperarm", start, end, sw, 0.25, [t0, None, t2], [0.1, 0.0, 0.9], False, log=logs.append)
check("2 holder name", holder == "upperarm_SwingTwist", holder)
check("2 holder listed", ST.list_holders() == [holder])
mem = ST.members(holder)
check("2 node count = 8 + 2 per twist", len(mem) == 8 + 2 * 2, len(mem))
check("2 rotate order warning", any("rotate order" in m for m in logs), logs)
check("2 end-joint-ignored warning", any("End joint is ignored" in m for m in logs), logs)
spec = ST.read_holder(holder)
check("2 read_holder joints", (spec["start_joint"], spec["end_joint"], spec["swing_joint"]) == (start, end, sw), spec)
check("2 read_holder twists keep empty index", spec["twist_joints"] == [t0, None, t2], spec["twist_joints"])
check("2 read_holder blends", close(spec["twist_blends"], [0.1, 0.0, 0.9]) and abs(spec["swing_blend"] - 0.25) < 1e-12)
check("2 outputs driven", all(cmds.listConnections(j + ".rotate", s=True, d=False) for j in (sw, t0, t2)))
check("2 empty index joint untouched", not cmds.listConnections(t1 + ".rotate", s=True, d=False))
check("2 holder blends keyable", cmds.getAttr(holder + ".swingBlend", keyable=True))

# twist blend 1 → 0 회전, swing blend 1 → 트위스트만 상쇄(X 축 회전만 남는다)
cmds.setAttr(start + ".rotate", 30, 40, 50)
ST.set_swing_blend(holder, 1.0)
ST.set_twist_blend(holder, 0, 1.0)
sw_rot = cmds.getAttr(sw + ".rotate")[0]
check("2 twist blend 1 = zero rotation", close(cmds.getAttr(t0 + ".rotate")[0], (0, 0, 0), 1e-9))
check("2 swing blend 1 = twist cancel only (X only)", abs(sw_rot[0]) > 1.0 and close(sw_rot[1:], (0, 0), 1e-9), sw_rot)
# blend 0 → 시작 회전을 통째로 상쇄: swingOut = inverse(q)
ST.set_swing_blend(holder, 0.0)
import maya.api.OpenMaya as om   # noqa: E402
q = om.MEulerRotation([om.MAngle(v, om.MAngle.kDegrees).asRadians() for v in (30, 40, 50)]).asMatrix()
o = om.MEulerRotation([om.MAngle(v, om.MAngle.kDegrees).asRadians() for v in cmds.getAttr(sw + ".rotate")[0]]).asMatrix()
check("2 swing blend 0 = cancel whole start rotation", (o * q).isEquivalent(om.MMatrix(), 1e-9))

# ---------------------------------------------------------------- 3. undo / redo
start, end, sw, t0, t1, t2 = scene()
cmds.undoInfo(state=True, infinity=True)
cmds.flushUndo()
holder = ST.build("arm", start, None, sw, 0.0, [t0, t1], [0.5, 0.5])
cmds.undo()
check("3 one undo removes the whole build", ST.list_holders() == [] and not cmds.ls(type="quatProd")
      and not cmds.listConnections(sw + ".rotate", s=True, d=False))
cmds.redo()
check("3 redo restores it", ST.list_holders() == ["arm_SwingTwist"] and len(ST.members("arm_SwingTwist")) == 12)

# ---------------------------------------------------------------- 4. 저장 · 다시 열기
cmds.setAttr(start + ".rotate", 10, 70, -20)
ST.set_swing_blend("arm_SwingTwist", 0.3)
before = [cmds.getAttr(j + ".rotate")[0] for j in (sw, t0, t1)]
path = os.path.join(TMP, "swing_twist.ma").replace("\\", "/")
cmds.file(rename=path)
cmds.file(save=True, type="mayaAscii")
with open(path) as fh:
    text = fh.read()
check("4 file requires quatNodes", '"quatNodes"' in text)
check("4 file does not require SwingTwist plugin", "SwingTwist" not in "".join(
    l for l in text.splitlines() if l.startswith("requires")))
cmds.file(path, open=True, force=True)
after = [cmds.getAttr(j + ".rotate")[0] for j in ("swingOut", "tw0", "tw1")]
check("4 values after reopen", all(close(a, b) for a, b in zip(before, after)), (before, after))
check("4 holder survives reopen", ST.list_holders() == ["arm_SwingTwist"])

# ---------------------------------------------------------------- 5. delete
n = ST.delete_rig("arm_SwingTwist")
check("5 delete_rig removes network + holder", n == 12 and ST.list_holders() == [] and not cmds.ls(type="quatSlerp"))
check("5 joints remain", cmds.objExists("swingOut") and cmds.objExists("tw0"))
cmds.undo()
check("5 undo delete", ST.list_holders() == ["arm_SwingTwist"])

# ---------------------------------------------------------------- 6. UI
start, end, sw, t0, t1, t2 = scene()
win = MW.MainWindow()
win.confirm_delete = False
win.show()
APP.processEvents()
check("6 window title", win.windowTitle().startswith("Swing Twist Native v"))
check("6 tabs", [win.tabs.tabText(i) for i in range(win.tabs.count())] == ["Build", "Rigs"])
cmds.select(start)
win._set_from_selection(win.le_start)
check("6 Set fills start + name", win.le_start.text() == start and win.le_name.text() == start)
cmds.select(sw)
win._set_from_selection(win.le_swing)
cmds.select([t0, t1, t2])
win.add_twist_selected()
win.add_twist_selected()
check("6 add twists (no duplicates)", [j for j, _ in win._twist_rows()] == [t0, t1, t2])
win.tbl_twist.selectRow(2)
win.move_twist_row(-1)
check("6 move up", [j for j, _ in win._twist_rows()] == [t0, t2, t1])
win.tbl_twist.selectRow(1)
win.remove_twist_rows()
check("6 remove", [j for j, _ in win._twist_rows()] == [t0, t1])
win.tbl_twist.cellWidget(1, 1).setValue(0.75)
win.sp_swing_blend.setValue(0.2)
holder = win.build_rig()
check("6 build from UI", holder == "upperarm_SwingTwist" and win.tbl_rigs.rowCount() == 1, holder)
spec = ST.read_holder(holder)
check("6 UI values reach holder", close(spec["twist_blends"], [MW.DEFAULT_TWIST_BLEND, 0.75])
      and abs(spec["swing_blend"] - 0.2) < 1e-9, spec)
check("6 second build fails cleanly (outputs driven)", win.build_rig() is None
      and "[ERROR]" in win.log_view.toPlainText())
win.clear_twists()
win.tbl_rigs.selectRow(0)
win.load_to_build()
check("6 load to build", [j for j, _ in win._twist_rows()] == [t0, t1] and win.le_swing.text() == sw
      and win.tabs.currentIndex() == 0)
win.tbl_rigs.selectRow(0)
win.select_nodes()
check("6 select nodes", len(cmds.ls(selection=True)) == len(ST.members(holder)))
win.select_joints()
check("6 select joints", set(cmds.ls(selection=True)) == {start, sw, t0, t1})
win.delete_rigs()
check("6 delete from UI", ST.list_holders() == [] and win.tbl_rigs.rowCount() == 0)
ascii_ok = all(s.isascii() for s in (win.windowTitle(), MW.BLEND_TIP, win.btn_build.toolTip(), win.log_view.toPlainText()))
check("6 UI strings are English ascii", ascii_ok)
win.close()

print("")
print("{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
