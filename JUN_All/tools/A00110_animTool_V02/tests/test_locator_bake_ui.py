# -*- coding: utf-8 -*-
# A00110_animTool_V02 v02.36 - Bake > Locator 탭 UI 시험 (mayapy + 오프스크린 PySide2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_locator_bake_ui.py
# QApplication 은 maya.standalone.initialize() 보다 먼저 (qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402

APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


cmds.file(new=True, force=True)
cmds.playbackOptions(min=1, max=40, ast=1, aet=40)
a = cmds.polyCube(name="cube_a")[0]
b = cmds.spaceLocator(name="pt_b")[0]
for obj, k in ((a, 1.0), (b, -2.0)):
    cmds.setKeyframe(obj, at="tx", t=1, v=0)
    cmds.setKeyframe(obj, at="tx", t=40, v=10 * k)
    cmds.setKeyframe(obj, at="rz", t=1, v=0)
    cmds.setKeyframe(obj, at="rz", t=40, v=400 * k)

from Framework.qt import JUN_mod_progress_qt   # noqa: E402

# 진행 팝업 기록 (실제 위젯 그대로 쓰고 호출만 엿본다)
REAL = JUN_mod_progress_qt.JUN_mod_progress_qt_v01
SEEN = {"created": 0, "phases": [], "steps": 0, "finished": 0, "max_value": 0}


class Spy(REAL):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        SEEN["created"] += 1
        SEEN["title"] = self.windowTitle()

    def begin_phase(self, label=None, index=None):
        SEEN["phases"].append(label)
        return super().begin_phase(label, index)

    def step(self, done, total, message=None):
        SEEN["steps"] += 1
        r = super().step(done, total, message)
        SEEN["max_value"] = max(SEEN["max_value"], self._fraction)
        return r

    def finish(self):
        SEEN["finished"] += 1
        return super().finish()


JUN_mod_progress_qt.JUN_mod_progress_qt_v01 = Spy

from tools.A00110_animTool_V02.app.ui.main_window import MainWindow   # noqa: E402

win = MainWindow()
win.show()
APP.processEvents()

names = [win.tabs.tabText(i) for i in range(win.tabs.count())]
win.tabs.setCurrentIndex(names.index("Bake"))
sub = [win.bake_tabs.tabText(i) for i in range(win.bake_tabs.count())]
check("Bake has Locator sub tab", "Locator" in sub, sub)
win.bake_tabs.setCurrentIndex(sub.index("Locator"))
APP.processEvents()

check("range prefilled with timeline", win.lb_range.values() == (1, 40), win.lb_range.values())
from PySide2.QtWidgets import QPushButton   # noqa: E402
labels = [w.text() for w in win.lb_range.findChildren(QPushButton)]
check("Get Current / Get Sel Range buttons", labels.count("Get Current") == 2 and "Get Sel Range" in labels, labels)

# Get Sel Range : 선택 키 5~30
cmds.setKeyframe(a, at="ty", t=5, v=1)
cmds.setKeyframe(a, at="ty", t=30, v=2)
cmds.selectKey(clear=True)
cmds.selectKey(a, time=(5, 30), attribute="ty")
[w for w in win.lb_range.findChildren(QPushButton) if w.text() == "Get Sel Range"][0].click()
check("Get Sel Range fills 5-30", win.lb_range.values() == (5, 30), win.lb_range.values())
cmds.currentTime(12)
[w for w in win.lb_range.findChildren(QPushButton) if w.text() == "Get Current"][0].click()
check("Get Current fills Start", win.lb_range.values() == (12, 30), win.lb_range.values())
win.btn_lb_timeline.click()
check("Get Timeline resets 1-40", win.lb_range.values() == (1, 40), win.lb_range.values())

# 빈 리스트 -> 경고, 팝업 없음
win.btn_lb_bake.click()
check("empty list: no popup", SEEN["created"] == 0)

# 리스트업 (Select Objects 와 같은 경로: 선택 -> 리스트 버튼)
cmds.select([a, b])
win.lb_tsl.btn_select.click() if hasattr(win.lb_tsl, "btn_select") else win.lb_tsl._on_select()
check("list has 2 items", win.lb_tsl.get_all_items() == ["cube_a", "pt_b"], win.lb_tsl.get_all_items())

win.lb_range.set_range(5, 35)
win.btn_lb_bake.click()
APP.processEvents()
check("progress popup shown once", SEEN["created"] == 1 and SEEN["title"] == "LOC + Anim", SEEN)
check("three phases", SEEN["phases"] == ["Creating locators", "Baking", "Cleaning up"], SEEN["phases"])
check("gauge stepped per frame", SEEN["steps"] >= 31, SEEN["steps"])
check("gauge reached 100%", SEEN["max_value"] >= 0.999, SEEN["max_value"])
check("popup closed", SEEN["finished"] == 1)
locs = cmds.ls("cube_a_LOC", "pt_b_LOC")
check("two locators made", len(locs) == 2, locs)
check("keys 5-35", cmds.keyframe("cube_a_LOC.tx", q=True, tc=True)[::30] == [5.0, 35.0],
      cmds.keyframe("cube_a_LOC.tx", q=True, tc=True)[::30])
check("follows world tx @20", abs(cmds.getAttr("pt_b_LOC.tx", time=20) - cmds.getAttr(b + ".tx", time=20)) < 1e-6)
check("rz continuous (400 deg)", abs(cmds.getAttr("cube_a_LOC.rz", time=35) - cmds.getAttr(a + ".rz", time=35)) < 1e-4,
      (cmds.getAttr("cube_a_LOC.rz", time=35), cmds.getAttr(a + ".rz", time=35)))
check("locators selected", sorted(cmds.ls(sl=True)) == ["cube_a_LOC", "pt_b_LOC"])

# 리네임 뒤에도 (UUID) 맞는 노드
cmds.rename(a, "cube_renamed")
win.btn_lb_bake.click()
check("after rename: locator from new name", cmds.objExists("cube_renamed_LOC"))

# Start > End -> 경고, 팝업 없음
before = SEEN["created"]
win.lb_range.set_range(30, 10)
win.btn_lb_bake.click()
check("start > end: no popup", SEEN["created"] == before)

# ---- v02.37 Constrain Objects to Locators ----
check("constrain group off by default", not win.grp_lb_constrain.isChecked())
check("constrain: Parent default", win.cb_lb_con_parent.isChecked()
      and not (win.cb_lb_con_point.isChecked() or win.cb_lb_con_orient.isChecked() or win.cb_lb_con_scale.isChecked()))
check("constrain off -> no types", win.lb_constrain_types() == [])
win.grp_lb_constrain.setChecked(True)
check("constrain on -> parent", win.lb_constrain_types() == ["parent"])
win.cb_lb_con_point.setChecked(True)
check("point turns parent off", not win.cb_lb_con_parent.isChecked() and win.lb_constrain_types() == ["point"])
win.cb_lb_con_orient.setChecked(True)
win.cb_lb_con_scale.setChecked(True)
check("point + orient + scale", win.lb_constrain_types() == ["point", "orient", "scale"])
win.cb_lb_con_parent.setChecked(True)
check("parent turns point / orient off", win.lb_constrain_types() == ["parent", "scale"])
# Scale 컨스트레인트인데 Scale 을 굽지 않음 -> 경고, 팝업 없음
win.lb_range.set_range(5, 35)
before = SEEN["created"]
win.btn_lb_bake.click()
check("scale constraint without Scale bake: no popup", SEEN["created"] == before)
# 종류 없음 -> 경고
for cb in (win.cb_lb_con_parent, win.cb_lb_con_scale):
    cb.setChecked(False)
win.btn_lb_bake.click()
check("constrain on with no type: no popup", SEEN["created"] == before)
# Parent 로 실행 -> 4 단계 팝업, 오브젝트에 parentConstraint
win.cb_lb_con_parent.setChecked(True)
SEEN["phases"] = []
win.btn_lb_bake.click()
check("constrain run: four phases", SEEN["phases"] == ["Creating locators", "Baking", "Cleaning up", "Constraining"],
      SEEN["phases"])
check("constrain run: objects constrained",
      all(cmds.listRelatives(n, children=True, type="parentConstraint") for n in ("cube_renamed", b)))
# (v02.58) Blend only in Frame Range - 기본 켬, 켜면 LOC_Constraint 레이어 weight 가 구간에만 1
check("range blend: default on", win.cb_lb_con_range.isChecked())
_lay = [l for l in cmds.ls(type="animLayer") if l.startswith("LOC_Constraint")]
check("range blend: layer weight keyed 0 / 1 / 1 / 0 around 5 - 35",
      len(_lay) == 1 and [round(cmds.getAttr(_lay[0] + ".weight", time=f)) for f in (4, 5, 35, 36)] == [0, 1, 1, 0], _lay)

# (v02.56) Fast - parents don't move : 기본 끔, 켜면 시간을 옮기지 않고 같은 결과
check("fast: default off", not win.cb_lb_fast.isChecked())
win.grp_lb_constrain.setChecked(False)
win.cb_lb_fast.setChecked(True)
cmds.currentTime(7)
SEEN["phases"] = []
before_locs = set(cmds.ls("*_LOC*", type="transform"))
win.btn_lb_bake.click()
new_locs = sorted(set(cmds.ls("*_LOC*", type="transform")) - before_locs)
check("fast: popup phases", SEEN["phases"] == ["Creating locators", "Baking", "Cleaning up"], SEEN["phases"])
check("fast: two locators, a key per frame", len(new_locs) == 2 and all(
    cmds.keyframe(l + ".tx", q=True, kc=True) == 31 for l in new_locs), new_locs)
check("fast: time untouched", cmds.currentTime(q=True) == 7)
check("fast: log says fast", "Fast mode" in win.te_log.toPlainText())

print("RESULT {0}/{1}".format(sum(R), len(R)))
win.close()
maya.standalone.uninitialize()
