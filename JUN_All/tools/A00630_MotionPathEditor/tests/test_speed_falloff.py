# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - v01.12 Speed 탭 Edit Path · 폴오프 [a, b] 띠 · Frames > Falloff · 폴오프 Smooth Range 시험 (계획서 G4)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_speed_falloff.py
# QApplication 은 maya.standalone 보다 먼저 (메모 qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
import numpy as np   # noqa: E402

import _common   # noqa: E402
from _common import check, world_pivot   # noqa: E402
import scenes   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import arc_length as al   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_cache as pc   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_manager as pm   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import main_window as mw   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import speed_graph as sg   # noqa: E402

cmds.undoInfo(state=True, infinity=True)
saved = {k: cmds.optionVar(q=mw.OPTVAR + k) for k in pm.DEFAULT_SETTINGS if cmds.optionVar(exists=mw.OPTVAR + k)}
for k in pm.DEFAULT_SETTINGS:
    cmds.optionVar(remove=mw.OPTVAR + k)
FR = np.arange(1, 121, dtype="float64")

# 울퉁불퉁한 매 프레임 키 (모캡 같은) 경로
scenes.new(120)
node = cmds.polyCube(name="jitter")[0]
rng = np.random.RandomState(3)
noise = rng.normal(0.0, 0.15, size=(121, 2))
scenes._key_translate(node, range(1, 121), lambda f: (f * 0.1, np.sin(f * 0.08) * 3 + noise[f, 0], noise[f, 1]))


def track():
    return np.array([world_pivot(node, f) for f in FR])


logs = []
try:
    win = mw.MainWindow()
    win.log = logs.append
    win.speed_panel.log = logs.append
    win.show()
    app.processEvents()
    panel = win.speed_panel
    mgr = win.manager
    win.tsl_paths.set_items([node])
    app.processEvents()
    cache = mgr.cache_list()[0]

    # ---- v01.15 Edit 묶음은 Speed 탭 맨 아래 (Path 탭에는 없다), Speed 탭 위쪽 Edit Path 는 숨김
    path_page = win.tabs.widget(0)
    check("v01.15: the Edit group (Edit Path, manipulator, falloff) lives in the Speed tab, not the Path tab",
          panel.isAncestorOf(win.btn_edit) and panel.isAncestorOf(win.cb_falloff) and
          panel.isAncestorOf(win.manip_buttons.buttons()[0]) and not path_page.isAncestorOf(win.btn_edit))
    check("v01.15: only one Edit Path button shows in the Speed tab", panel.btn_edit.isHidden() and not win.btn_edit.isHidden())
    # ---- 두 Edit Path 버튼
    check("Speed tab has an Edit Path button (checkable, pin style)", panel.btn_edit.isCheckable())
    win._set_edit_buttons(True)
    check("both Edit Path buttons always show the same state", win.btn_edit.isChecked() and panel.btn_edit.isChecked())
    win._sync_edit_button()                     # 헤드리스: 편집 툴이 실제로 켜지지 않았다 → 둘 다 끔
    check("they follow the real tool state together", not win.btn_edit.isChecked() and not panel.btn_edit.isChecked())
    del logs[:]
    panel.btn_edit.click()                      # 헤드리스에선 draggerContext 를 못 만든다 → 실패하면 둘 다 꺼진다
    app.processEvents()
    check("the Speed tab button drives the same edit mode (both buttons stay in step)",
          win.btn_edit.isChecked() == panel.btn_edit.isChecked(), (win.btn_edit.isChecked(), panel.btn_edit.isChecked(), logs))

    # ---- [a, b] 띠
    f60 = [k for _c, k in mgr.pickable_frames() if k.t == 60.0]
    if not f60:                                 # 매 프레임 키라 60 은 키다
        f60 = [k for k in cache.keys if k.t == 60.0]
    mgr.select([(cache, f60[0])], "replace")
    mgr.settings.update({"falloff_on": True, "falloff_radius": 10.0})
    mgr.redraw()
    data = panel.graph.data
    ft, fw, fsel = data["falloff"]
    check("graph gets the falloff weights of the selected point", fsel == [60.0] and
          np.count_nonzero(fw) == 19 and fw[list(ft).index(60.0)] == 1.0, np.count_nonzero(fw))
    panel.graph.grab()                          # 띠까지 그리는 paintEvent 가 에러 없이
    check("graph paints the falloff band without error", "Graph error" not in str(panel.graph.data.get("empty", "")))
    mgr.settings["falloff_on"] = False
    mgr.redraw()
    check("falloff off: only the selected frame is marked", np.count_nonzero(panel.graph.data["falloff"][1]) == 1)
    mgr.settings["falloff_on"] = True
    mgr.select([], "replace")
    check("nothing selected: no band", panel.graph.data.get("falloff") is None)
    mgr.select([(cache, f60[0])], "replace")

    # ---- Frames > Falloff
    [b for b in panel.range_buttons.buttons() if b.property("value") == sg.RANGE_FALLOFF][0].click()
    app.processEvents()
    check("Frames > Falloff shows [a, b] plus the radius around it", panel.graph_range(cache) == (41.0, 79.0) and
          mgr.settings["graph_range"] == sg.RANGE_FALLOFF, panel.graph_range(cache))
    mgr.select([], "replace")
    check("Frames > Falloff with nothing selected = whole path", panel.graph_range(cache) == (1.0, 120.0))
    mgr.select([(cache, f60[0])], "replace")

    # ---- 라이브: 뷰포트에서 끄는 동안(관리자 미리보기) 그래프가 따라 바뀐다
    before_ys = np.array(panel.graph.data["series"][-1]["ys"])
    moved = cache.points.copy()
    moved[59] += np.array([0.0, 3.0, 0.0])
    mgr.preview[cache.key] = moved
    mgr.redraw()
    live = np.array(panel.graph.data["series"][-1]["ys"])
    check("live: the graph follows a viewport drag preview (grey original underneath)",
          np.abs(live - before_ys).max() > 1.0 and panel.graph.data["ghost"] is not None)
    mgr.preview.pop(cache.key)
    mgr.redraw()

    # ---- 폴오프 Smooth Range (위치)
    panel.cmb_brush.setCurrentIndex(panel.cmb_brush.findData(sg.BRUSH_SHAPE))
    mgr.settings.update({"falloff_radius": 15.0})
    panel.sp_radius.setValue(4.0)
    panel.sl_strength.setValue(100)
    t0 = track()
    w = panel.falloff_weights(cache)
    acc0 = al.accel(cache.times, cache.points, FR)
    cmds.flushUndo()
    del logs[:]
    panel.btn_smooth.click()
    app.processEvents()
    t1 = track()
    inside, outside = w > 0.5, w <= 0
    acc1 = al.accel(np.asarray(cache.times), t1, FR)
    check("Smooth Range with a selection: only the falloff range changes (outside exact)",
          np.abs((t1 - t0)[outside]).max() < 1e-3 * al.size(t0), np.abs((t1 - t0)[outside]).max())
    check("Smooth Range with a selection: the range gets smoother (acceleration down by 40% or more - Smooth Shape keeps big arcs)",
          acc1[inside].mean() < 0.6 * acc0[inside].mean(), (acc0[inside].mean(), acc1[inside].mean()))
    check("weight 1 moves more than weight ~0.3", np.linalg.norm((t1 - t0)[59]) > 0 and
          np.abs(t1 - t0)[np.argmin(np.abs(w - 0.3))].max() <= np.abs(t1 - t0)[w >= 0.99].max() + 1e-6)
    check("logged the weighted falloff smoothing", any(m.startswith("[OK] Smoothed the falloff range [46, 74]") for m in logs), logs)
    cmds.undo()
    check("one undo puts it back", np.abs(track() - t0).max() < 1e-9)
    mgr.refresh_all()
    # Smooth Speed 브러시면 위치는 Smooth Shape 로 하고 알린다
    panel.cmb_brush.setCurrentIndex(panel.cmb_brush.findData(sg.BRUSH_SPEED))
    del logs[:]
    panel.btn_smooth.click()
    app.processEvents()
    check("Smooth Speed brush + selection -> smooths the position with Smooth Shape and says so",
          any("used Smooth Shape" in m for m in logs) and np.abs(track() - t0).max() > 1e-3, logs)
    cmds.undo()
    mgr.refresh_all()
    # 고른 것이 없으면 예전처럼 보이는 구간 전체
    mgr.select([], "replace")
    panel.cmb_brush.setCurrentIndex(panel.cmb_brush.findData(sg.BRUSH_SHAPE))
    [b for b in panel.range_buttons.buttons() if b.property("value") == sg.RANGE_PATH][0].click()
    del logs[:]
    panel.btn_smooth.click()
    app.processEvents()
    t2 = track()
    check("no selection: Smooth Range smooths the whole graph range as before",
          np.abs(t2 - t0)[:10].max() > 1e-4 and np.abs(t2 - t0)[60:70].max() > 1e-4 and
          not any("falloff range" in m for m in logs))
    cmds.undo()
    check("no error logged", not any(m.startswith("[FAIL]") for m in logs if "Edit Path" not in m),
          [m for m in logs if m.startswith("[FAIL]")])
    win.close()
    app.processEvents()
finally:
    for k in pm.DEFAULT_SETTINGS:
        cmds.optionVar(remove=mw.OPTVAR + k)
    for k, v in saved.items():
        if isinstance(v, int):
            cmds.optionVar(intValue=(mw.OPTVAR + k, v))
        elif isinstance(v, float):
            cmds.optionVar(floatValue=(mw.OPTVAR + k, v))
        else:
            cmds.optionVar(stringValue=(mw.OPTVAR + k, v))
_common.finish()
