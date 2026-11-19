# -*- coding: utf-8 -*-
# A00630_MotionPathEditor - 툴 창 오프스크린 시험 (계획서 §7-2)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" -u test_ui.py
# QApplication 은 maya.standalone 보다 먼저 (메모 qapplication-before-maya-standalone).
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication, QSlider, QPushButton   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

import _common   # noqa: E402
from _common import check   # noqa: E402
import scenes   # noqa: E402
from Framework.themes.theme_manager import ThemeManager   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import draw_bridge   # noqa: E402
from tools.A00630_MotionPathEditor.app.core import path_manager as pm   # noqa: E402
from tools.A00630_MotionPathEditor.app.ui import main_window as mw   # noqa: E402

# 사용자 optionVar 를 시험이 바꾸지 않게 - 끝에서 되돌린다
saved_vars = {k: cmds.optionVar(q=mw.OPTVAR + k) for k in pm.DEFAULT_SETTINGS if cmds.optionVar(exists=mw.OPTVAR + k)}
for k in pm.DEFAULT_SETTINGS:
    cmds.optionVar(remove=mw.OPTVAR + k)

names = scenes.hierarchy(120)
win = mw.MainWindow()
ThemeManager.load_theme_to_widget(win, "blue_dark")
logs = []
win.log = lambda text: logs.append(text)
win.manager.log = win.log
win.range_edit.log_callback = win.log      # 위젯은 만들 때의 로그 함수를 들고 있다
win.show()
app.processEvents()

check("window title has the version", "Motion Path Editor v" in win.windowTitle())
check("defaults: playback range, view plane, dots and keys on",
      win.manager.settings["range"] == pm.RANGE_PLAYBACK and win.manager.settings["plane"] == "view"
      and win.cb_dots.isChecked() and win.cb_keys.isChecked() and not win.cb_numbers.isChecked())
check("custom range fields and Get buttons are off unless Custom",
      not win.range_edit.start_edit.isEnabled() and not any(
          b.isEnabled() for b in win.range_edit.findChildren(QPushButton)))
check("range row has Get Current x2 + Get Sel Range (same widget as A00110)",
      [b.text() for b in win.range_edit.findChildren(QPushButton)] == ["Get Current", "Get Current", "Get Sel Range"])
check("Edit Path button turns light red when on (shared pin style)", "#f2a0a0" in win.btn_edit.styleSheet())

# ---- 경로 추가 (TSL Set Selected 와 같은 효과: set_items)
cmds.select([names["ctrl"], "j3", names["driven"]])
win.tsl_paths.set_items(cmds.ls(sl=True))
app.processEvents()
check("three paths baked from the list", len(win.manager.caches) == 3, list(win.manager.caches))
check("one draw node per path", len(cmds.ls(type="junMotionPath")) == 3)
check("bake is logged", any(m.startswith("[OK] Baked 3 path(s)") for m in logs), logs)
check("locked path reason is logged", any("driven by" in m for m in logs))

# ---- 표시 옵션 → 그리기 데이터 · optionVar
ctrl_key = [c.key for c in win.manager.cache_list() if c.node.endswith("|ctrl")][0]
win.cb_dots.setChecked(False)
check("Frame dots off empties the dot array", len(draw_bridge.DATA[ctrl_key]["dots"]) == 0)
check("the setting is remembered", cmds.optionVar(q=mw.OPTVAR + "show_dots") == 0)
win.cb_dots.setChecked(True)
win.sl_key.setValue(14)
check("Key size slider reaches the draw data", draw_bridge.DATA[ctrl_key]["key_size"] == 14.0)
win.cb_numbers.setChecked(True)
check("Frame numbers adds a label per key", len(draw_bridge.DATA[ctrl_key]["labels"]) ==
      len(win.manager.caches[ctrl_key].keys))
win.cb_numbers.setChecked(False)

# ---- 드래그 평면 옵션
[b for b in win.plane_buttons.buttons() if b.property("plane") == "y"][0].click()
check("Drag plane option is stored", win.manager.settings["plane"] == "y" and
      cmds.optionVar(q=mw.OPTVAR + "plane") == "y")

# ---- 범위 : Custom 이면 다시 굽는다
[b for b in win.range_buttons.buttons() if b.property("rangeMode") == pm.RANGE_CUSTOM][0].click()
check("Custom turns the fields and buttons on", win.range_edit.start_edit.isEnabled() and all(
    b.isEnabled() for b in win.range_edit.findChildren(QPushButton)))
win.range_edit.set_range(10, 50)
app.processEvents()
c = win.manager.caches[ctrl_key]
check("Custom range re-bakes the paths", c.start == 10 and c.end == 50 and c.times[0] == 10.0, (c.start, c.end))
# Get Current : 현재 프레임으로 끝 칸
cmds.currentTime(80)
win.range_edit.get_current_end()
check("Get Current fills End with the current frame and re-bakes", win.range_edit.end() == 80 and c.end == 80,
      (win.range_edit.end(), c.end))
# Get Sel Range : 고른 키의 처음 · 끝
cmds.selectKey(clear=True)
cmds.selectKey(names["ctrl"], time=(30, 70), attribute="translateY")
win.range_edit.get_selected_range()
check("Get Sel Range fills Start / End from the selected keys and re-bakes",
      win.range_edit.values() == (30, 70) and (c.start, c.end) == (30, 70), (win.range_edit.values(), c.start, c.end))
logs[:] = []
cmds.selectKey(clear=True)
win.range_edit.get_selected_range()
check("Get Sel Range with no selected keys warns and keeps the range",
      any("No keyframes selected" in m for m in logs) and (c.start, c.end) == (30, 70), logs)
# 같은 범위로 다시 changed 가 와도 다시 굽지 않는다
logs[:] = []
win.range_edit.start_edit.editingFinished.emit()
check("same range again does not re-bake", not any("Re-baked" in m for m in logs), logs)
[b for b in win.range_buttons.buttons() if b.property("rangeMode") == pm.RANGE_PLAYBACK][0].click()

# ---- 슬라이더가 테마 색으로 (메모 feedback-sliders-use-shared-style)
sliders = win.findChildren(QSlider)
check("sliders are painted by the shared slider style", sliders and all(s.styleSheet() for s in sliders),
      len(sliders))

# ---- Edit Path 버튼 = 실제 편집 툴 상태 (v01.02). GUI 에서 생긴 순서를 그대로 재현한다:
#      켜는 순간 "툴이 바뀌었다" 알림이 오는데 그때 currentCtx 는 아직 이전 툴 → 바로 판단하면 버튼을 껐다(빨강이 안 됨).
#      이제 알림은 확인을 idle 로 미루기만 한다(헤드리스엔 idle 이 없어 _sync_edit_button 을 직접 부른다).
class FakeCtx(object):
    def __init__(self):
        self.active = False
        self.finalized = 0

    def is_active(self):
        return self.active

    def _finalize(self):
        self.finalized += 1

    def deactivate(self):
        self.active = False


# mayapy(배치) 의 evalDeferred 는 미루지 않고 바로 실행한다 - GUI 처럼 idle 까지 미루도록 줄에 쌓는 대역으로 바꾼다
DEFERRED = []
_real_eval_deferred = cmds.evalDeferred
cmds.evalDeferred = lambda fn, **kw: DEFERRED.append(fn)


def idle():
    while DEFERRED:
        DEFERRED.pop(0)()


fake = FakeCtx()
win.context = fake
win.btn_edit.blockSignals(True)
win.btn_edit.setChecked(True)                  # Edit Path 를 눌렀다
win.btn_edit.blockSignals(False)
win._tool_sync_pending = False
win._on_tool_changed()                         # 툴 전환 알림 - 이 순간 마야는 아직 이전 툴
check("tool-change notice does not judge at once (button stays on)", win.btn_edit.isChecked() and
      win._tool_sync_pending)
win._on_tool_changed()                         # 알림이 몰려도 확인은 한 번
check("several notices queue only one check", len(DEFERRED) == 1, len(DEFERRED))
fake.active = True                             # 마야가 전환을 끝냈다
idle()
check("after Maya finished switching, the button stays on = light red", win.btn_edit.isChecked() and
      "#f2a0a0" in win.btn_edit.styleSheet() and not win._tool_sync_pending)
fake.active = False                            # Q / 다른 툴
win._on_tool_changed()
idle()
check("Q / another tool turns the button off (and cancels a running drag)",
      not win.btn_edit.isChecked() and fake.finalized == 1)
win.context = None
cmds.evalDeferred = _real_eval_deferred

# ---- 애니메이션 레이어 목록 (v01.03)
check("layer list starts with Base only (no layers yet)",
      [win.layer_list.item(i).text() for i in range(win.layer_list.count())] == ["BaseAnimation"] and
      "Editing: BaseAnimation" in win.lbl_layer.text())
cmds.select(names["ctrl"])
lay = cmds.animLayer("animLayer_01", addSelectedObjects=True)
for f, v in ((1, 0.0), (45, 1.5), (120, 0.0)):
    cmds.setKeyframe(names["ctrl"], attribute="translateY", time=f, value=v, animLayer=lay)
cmds.select(clear=True)
win.reload_layers()
check("Reload Layers lists Base + animLayer_01",
      [win.layer_list.item(i).text() for i in range(win.layer_list.count())] == ["BaseAnimation", "animLayer_01"])
logs[:] = []
win.layer_list.item(1).setSelected(True)
cc = win.manager.caches[ctrl_key]
check("picking animLayer_01 shows its keys and logs it", [k.t for k in cc.keys] == [1.0, 45.0, 120.0] and
      any("Editing the animation layer animLayer_01" in m for m in logs) and "animLayer_01" in win.lbl_layer.text(),
      ([k.t for k in cc.keys], logs))
check("the edit layer is remembered", cmds.optionVar(q=mw.OPTVAR + "edit_layer") == "animLayer_01")
j3 = [c for c in win.manager.cache_list() if c.node.endswith("|j3")][0]
check("a path not in that layer turns grey (locked) with the reason", j3.locked and "Not in the animation layer" in
      j3.lock_reason and draw_bridge.DATA[j3.key]["locked"])
cmds.delete(lay)
win.on_refresh()
check("Refresh after deleting the layer falls back to Base",
      win.manager.edit_layer() == "BaseAnimation" and win.layer_list.count() == 1 and
      win.layer_list.item(0).isSelected())

# ---- 대상 빼기
win.tsl_paths.set_items([names["ctrl"]])
app.processEvents()
check("removing from the list removes the path and its node", len(win.manager.caches) == 1 and
      len(cmds.ls(type="junMotionPath")) == 1)

# ---- Refresh 버튼
logs[:] = []
win.on_refresh()
check("Refresh re-bakes and logs", any(m.startswith("[OK] Re-baked 1 path(s)") for m in logs), logs)

# ---- 창을 닫으면 다 정리
win.close()
app.processEvents()
check("closing the window removes the draw nodes and the draw data",
      not cmds.ls(type="junMotionPath") and not draw_bridge.DATA)
check("closing the window stops the callbacks", not win.watcher.ids and win._tool_cb is None)

# 사용자 optionVar 되돌리기
for k in pm.DEFAULT_SETTINGS:
    cmds.optionVar(remove=mw.OPTVAR + k)
for k, v in saved_vars.items():
    if isinstance(v, int):
        cmds.optionVar(intValue=(mw.OPTVAR + k, v))
    elif isinstance(v, float):
        cmds.optionVar(floatValue=(mw.OPTVAR + k, v))
    else:
        cmds.optionVar(stringValue=(mw.OPTVAR + k, v))

_common.finish()
