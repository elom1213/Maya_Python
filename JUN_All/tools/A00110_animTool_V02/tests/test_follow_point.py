# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.23 - Follow 탭 Point(위치만 pointConstraint 처럼) 시험 (mayapy 오프스크린)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_follow_point.py
# 같은 장면에 실제 pointConstraint / parentConstraint(maintainOffset) 를 걸어 구운 값과 비교한다.
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)   # maya.standalone 보다 먼저 - 다른 'tools' 패키지가 먼저 잡히지 않게
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

from tools.A00110_animTool_V02.app.core.follow_match_manager import FollowMatchManager as FM   # noqa: E402

R = []
TOL = 1e-3
FRAMES = range(1, 25)


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def build(parent_rotated=False):
    """target 은 움직이면서 Y 로 크게 돈다. follower 는 옆에 떨어져 있다."""
    cmds.file(new=True, force=True)
    tgt = cmds.group(empty=True, name="tgt")
    for f, tx, ry, rz in ((1, 0, 0, 0), (12, 5, 90, 20), (24, 2, 200, -30)):
        cmds.setKeyframe(tgt, attribute="translateX", time=f, value=tx)
        cmds.setKeyframe(tgt, attribute="rotateY", time=f, value=ry)
        cmds.setKeyframe(tgt, attribute="rotateZ", time=f, value=rz)
    flw = cmds.group(empty=True, name="flw")
    if parent_rotated:
        grp = cmds.group(empty=True, name="flw_parent")
        cmds.xform(grp, rotation=(30, 45, 0), translation=(1, 2, 3), scale=(1, 1, 1))
        flw = cmds.parent(flw, grp)[0]
    cmds.xform(flw, worldSpace=True, translation=(3, 1, 0))
    cmds.xform(flw, worldSpace=True, rotation=(10, 0, 0))
    cmds.setKeyframe(flw, attribute=["translate", "rotate"], time=1)
    return tgt, flw


def reference(kind, parent_rotated):
    """실제 컨스트레인트로 구운 follower 로컬 translate 값 {frame: (x,y,z)}."""
    tgt, flw = build(parent_rotated)
    cmds.currentTime(1)
    if kind == "point":
        con = cmds.pointConstraint(tgt, flw, maintainOffset=True)[0]
    else:
        con = cmds.parentConstraint(tgt, flw, maintainOffset=True, skipRotate=["x", "y", "z"])[0]
    out = {}
    for f in FRAMES:
        cmds.currentTime(f)
        out[f] = tuple(cmds.getAttr(flw + ".translate")[0])
    cmds.delete(con)
    return out


def ours(point, parent_rotated):
    tgt, flw = build(parent_rotated)
    cmds.currentTime(1)
    FM.match_follow([tgt], [flw], 1, 24, 1.0, do_translate=True, do_rotate=False,
                    maintain_offset=True, point_translate=point)
    out = {}
    for f in FRAMES:
        out[f] = tuple(cmds.getAttr(flw + ".translate", time=f)[0])
    return out


def max_err(a, b):
    return max(abs(x - y) for f in FRAMES for x, y in zip(a[f], b[f]))


for parent_rotated in (False, True):
    tag = "rotated parent" if parent_rotated else "world parent"
    ref_point = reference("point", parent_rotated)
    ref_parent = reference("parent", parent_rotated)
    got_point = ours(True, parent_rotated)
    got_parent = ours(False, parent_rotated)
    check("{0} : Point = pointConstraint(mo)".format(tag), max_err(got_point, ref_point) < TOL,
          max_err(got_point, ref_point))
    check("{0} : off = parentConstraint(mo) - unchanged".format(tag), max_err(got_parent, ref_parent) < TOL,
          max_err(got_parent, ref_parent))
    check("{0} : the two really differ (target rotates)".format(tag), max_err(ref_point, ref_parent) > 0.5,
          max_err(ref_point, ref_parent))

# Maintain Offset 꺼짐 -> Point 는 차이 없음
tgt, flw = build()
FM.match_follow([tgt], [flw], 1, 24, 1.0, do_rotate=False, maintain_offset=False, point_translate=True)
a = {f: tuple(cmds.getAttr(flw + ".translate", time=f)[0]) for f in FRAMES}
tgt, flw = build()
FM.match_follow([tgt], [flw], 1, 24, 1.0, do_rotate=False, maintain_offset=False, point_translate=False)
b = {f: tuple(cmds.getAttr(flw + ".translate", time=f)[0]) for f in FRAMES}
check("no offset : Point makes no difference", max_err(a, b) < 1e-6)

# Point + Rotate : 회전은 parent 방식 그대로(= orientConstraint mo)
tgt, flw = build()
cmds.currentTime(1)
con = cmds.orientConstraint(tgt, flw, maintainOffset=True)[0]
ref_r = {f: None for f in FRAMES}
for f in FRAMES:
    cmds.currentTime(f)
    ref_r[f] = cmds.xform(flw, q=True, worldSpace=True, matrix=True)
cmds.delete(con)
tgt, flw = build()
cmds.currentTime(1)
cnt, msg = FM.match_follow([tgt], [flw], 1, 24, 1.0, do_translate=True, do_rotate=True,
                           maintain_offset=True, point_translate=True)
err = 0.0
for f in FRAMES:
    cmds.currentTime(f)
    m = cmds.xform(flw, q=True, worldSpace=True, matrix=True)
    err = max(err, max(abs(m[i] - ref_r[f][i]) for i in (0, 1, 2, 4, 5, 6, 8, 9, 10)))
check("Point + Rotate : rotation = orientConstraint(mo)", err < TOL, err)
check("log says point translate", "point translate" in msg, msg)

# UI : Point 는 Maintain Offset + Translate 일 때만 켤 수 있다
from tools.A00110_animTool_V02.app.ui import main_window as MW   # noqa: E402
w = MW.MainWindow()
cb = w.cb_follow_point
check("ui : Maintain Offset on by default (v02.24), Point enabled but off",
      w.cb_follow_offset.isChecked() and cb.isEnabled() and not cb.isChecked())
w.cb_follow_offset.setChecked(False)
check("ui : disabled without Maintain Offset", not cb.isEnabled())
w.cb_follow_offset.setChecked(True)
check("ui : enabled with Maintain Offset + Translate", cb.isEnabled())
w.cb_follow_t.setChecked(False)
check("ui : disabled when Translate is off", not cb.isEnabled())
w.cb_follow_t.setChecked(True)

# UI 실행 : 버튼 경로로 Point 가 전달되는지
tgt, flw = build()
w.follow_tgt_tsl.set_items([tgt])
w.follow_flw_tsl.set_items([flw])
w.le_follow_start.setText("1")
w.le_follow_end.setText("24")
w.cb_follow_r.setChecked(False)
cb.setChecked(True)
cmds.currentTime(1)
w.on_follow_bake()
c = {f: tuple(cmds.getAttr(flw + ".translate", time=f)[0]) for f in FRAMES}
check("ui : Match Follow with Point = pointConstraint(mo)", max_err(c, reference("point", False)) < TOL)

print("\n{0}/{1} passed".format(sum(R), len(R)))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
