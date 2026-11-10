# -*- coding: utf-8 -*-
"""Physics Asset 모드 UI 시험 (mayapy + 오프스크린 PySide2).

    "C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe" tests/test_physics_ui.py
"""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication(sys.argv)
import maya.standalone  # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, JUN_ALL)

from tools.A00410_SecondaryMotion.app.core import chain_solver  # noqa: E402
from tools.A00410_SecondaryMotion.app.core import physics_solver as ps  # noqa: E402
from tools.A00410_SecondaryMotion.app.ui import main_window as mw  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


try:
    if cmds.optionVar(exists=mw._OV_SOLVER):
        cmds.optionVar(remove=mw._OV_SOLVER)
    cmds.file(new=True, force=True)
    cmds.playbackOptions(minTime=1, maxTime=48)
    cmds.select(clear=True)
    js = [cmds.joint(p=(5 * i, 100, 0), name="tail%d" % i) for i in range(5)]
    for f, v in ((1, 0), (12, 40), (24, -30), (48, 0)):
        cmds.setKeyframe(js[0], at="rotateY", t=f, v=v)
    for j in js[1:]:
        cmds.setKeyframe(j, at="rotateZ", t=1, v=10)      # 자식 키 - Physics Asset 은 무시

    w = mw.MainWindow()
    w.show()
    APP.processEvents()

    check("default solver = Kawaii", w.rb_kawaii.isChecked() and not w._is_physics())
    check("kawaii widgets shown, physics hidden",
          w.kawaii_w.isVisible() and not w.pa_w.isVisible())
    check("kawaii params", isinstance(w._params(), chain_solver.SolverParams))

    w.rb_joint.setChecked(True)
    w.tsl.set_items([cmds.ls(j, long=True)[0] for j in js])
    w.rb_physics.setChecked(True)
    APP.processEvents()
    check("physics widgets shown, kawaii hidden",
          w.pa_w.isVisible() and not w.kawaii_w.isVisible())
    check("solver remembered in optionVar", cmds.optionVar(q=mw._OV_SOLVER) == "physics")

    p = w._params()
    check("physics params type", isinstance(p, ps.PhysicsParams))
    check("defaults: gravity Y -980, limited 45/45, kinematic root, from animation",
          p.gravity == (0.0, -980.0, 0.0) and p.swing1_mode == ps.LIMIT_LIMITED
          and p.swing1 == 45.0 and p.swing2 == 45.0 and p.kinematic_root
          and p.start == ps.START_ANIMATION and p.collision == ps.COLLISION_NONE
          and p.substeps == 4, p.as_dict())

    # Collision: None / Ground
    check("collision choices", [w.cb_pa_col.itemText(i) for i in range(w.cb_pa_col.count())]
          == ["None", "Ground"])
    check("height disabled when None", not w.sb_pa_ground.isEnabled())
    w.cb_pa_col.setCurrentIndex(1)
    w.sb_pa_ground.setValue(50.0)
    p = w._params()
    check("Ground -> collision ground at 50 cm", p.collision == ps.COLLISION_GROUND
          and abs(p.ground_height - 50.0) < 1e-9 and w.sb_pa_ground.isEnabled())
    w.cb_pa_col.setCurrentIndex(0)

    w.cb_pa_sw[1].setCurrentText("Locked")
    check("Locked disables its degree box", not w.sb_pa_sw[1].isEnabled()
          and w._params().swing2_mode == ps.LIMIT_LOCKED)
    w.cb_pa_sw[1].setCurrentText("Limited")
    w.cb_pa_start.setCurrentIndex(1)
    check("Settled enables seconds", w.sb_pa_settle.isEnabled()
          and w._params().start == ps.START_SETTLED)
    w.cb_pa_start.setCurrentIndex(0)

    # 프리뷰 -> 레이어 + 스윙 축 라벨(조인트 뼈 축 X -> Swing1 Z, Swing2 Y)
    w.chk_preview.setChecked(True)
    APP.processEvents()
    check("preview layer made", bool(cmds.ls("SM_preview_LYR", type="animLayer")))
    check("swing labels follow the bone axis",
          w.lbl_pa_sw[0].text() == "Swing 1 (around Z)"
          and w.lbl_pa_sw[1].text() == "Swing 2 (around Y)",
          (w.lbl_pa_sw[0].text(), w.lbl_pa_sw[1].text()))

    # 솔버를 바꾸면 프리뷰 레이어를 새로 만든다
    w.rb_kawaii.setChecked(True)
    check("switch clears the preview", not w.session.has_preview())
    w._timer.stop()
    w._refresh_preview()
    check("kawaii preview rebuilt", w.session.has_preview())
    w.rb_physics.setChecked(True)
    w._timer.stop()

    # Apply (Bake Keys)
    for rb, oid in w._out_buttons.items():
        if oid == "keys":
            rb.setChecked(True)
    w.on_apply()
    check("apply baked keys", cmds.keyframe(js[2] + ".rotateZ", q=True, keyframeCount=True) == 48)
    ry = cmds.getAttr(js[2] + ".rotate", time=40)[0]
    check("child key no longer the result", max(abs(ry[0]), abs(ry[1]), abs(ry[2] - 10)) > 1.0, ry)

    w.close()
finally:
    print("\n{0}/{1} passed".format(sum(R), len(R)))
    maya.standalone.uninitialize()
    os._exit(0 if all(R) else 1)
