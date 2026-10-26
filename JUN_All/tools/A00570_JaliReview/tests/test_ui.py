# -*- coding: utf-8 -*-
# A00570_JaliReview - UI 시험 (T8, mayapy 오프스크린, 합성 아바타 + A00560 워커가 만든 클립 2개)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_ui.py
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다 (메모리 qapplication-before-maya-standalone).
import os
import shutil
import subprocess
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication, QMessageBox   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import mayapy_runner   # noqa: E402
from Framework.jali import clip_manifest   # noqa: E402
from tools.A00570_JaliReview.app.core import review_scene as rs, arkit_connect   # noqa: E402
from tools.A00570_JaliReview.app.ui import main_window as mw   # noqa: E402
import tools.A00570_JaliReview as tool   # noqa: E402

SRC = r"C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI_Voice\0060_Vivian_voice\out_en_002"
CTL_SRC = r"C:\Users\USER\Desktop\JP\0035_maya_src_rig\02_Cage_JALI\A0030_jali_slider_ctl_direct_arkit.ma"
WORKER = os.path.join(JUN_ALL, "tools", "A00560_JaliBatch", "app", "maya", "worker.py")
R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


def pump():
    app.processEvents()
    app.processEvents()


def log_text(w):
    pump()
    return w.log_view.toPlainText()


def finish():
    print("RESULT", "OK" if all(R) else "FAIL", "{0}/{1}".format(sum(R), len(R)))
    maya.standalone.uninitialize()
    os._exit(0 if all(R) else 1)


if not os.path.isdir(SRC) or not os.path.isfile(CTL_SRC):
    print("SKIP no example data / controller")
    print("RESULT OK (skipped)")
    maya.standalone.uninitialize()
    os._exit(0)

work = tempfile.mkdtemp(prefix="a00570_ui_")
CTL = os.path.join(work, "A0030_ctl.ma")
shutil.copy2(CTL_SRC, CTL)
OUT = os.path.join(work, "maya")
names = ["0030_vivian_en_02_f0445_0490", "0030_vivian_en_03_f0490_0600"]
clips = [{"name": n, "txt": os.path.join(SRC, n + ".txt"), "json": os.path.join(SRC, n + ".visemenet.json"),
          "wav": os.path.join(SRC, n + ".wav"), "out_mb": os.path.join(OUT, n + ".mb"), "start": 1} for n in names]
job = {"job": "generate", "controller": CTL, "mapping": "jali_slider_dummy_in", "fps": 30.0, "default_start": 1,
       "jali": {"mode": "data", "fixed": [0.6, 0.6], "scale": None}, "viseme_scale": None, "overwrite": "skip", "copy_wav": True,
       "out_dir": OUT, "manifest": clip_manifest.path_for(OUT), "tool": "test", "clips": clips}
job_path, result_path, _ = mayapy_runner.write_job(mayapy_runner.new_job_dir("a00570_ui"), job)
subprocess.run(mayapy_runner.command(sys.executable, job_path, WORKER), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
if not all(os.path.isfile(c["out_mb"]) for c in clips):
    check("P0 clips generated", False)
    finish()

# 아바타: blendShape 51 타겟
AVATAR = os.path.join(work, "avatar.mb")
cmds.file(new=True, force=True)
cmds.file(CTL, reference=True, namespace="TMP", prompt=False)
arkit52 = cmds.listAttr("TMP:ARKIT_OUT", userDefined=True)
cmds.file(CTL, removeReference=True)
base = cmds.polyPlane(n="face", sx=2, sy=2, ch=False)[0]
ts = []
for nm in arkit52:
    if nm == "tongueOut":
        continue
    t = cmds.duplicate(base, n=nm)[0]
    cmds.move(0, 0.1, 0, t + ".vtx[0]", r=True)
    ts.append(t)
cmds.blendShape(ts, base, n="face_bs")
cmds.delete(ts)
cmds.file(rename=AVATAR)
cmds.file(save=True, type="mayaBinary")
cmds.file(new=True, force=True)
for key in ("clip_dir", "avatar", "blendshape", "rules"):
    cmds.optionVar(remove=mw.prefs.KEYS[key])

# ---- 창
w = tool.run(False)
pump()
check("U1 run() opens the window", w is not None and w.isVisible() and w.objectName() == mw.WINDOW_OBJECT_NAME)
w.le_folder.setText(OUT)
w.load_folder()
pump()
check("U2 clip folder -> 2 rows with frames + status", w.table.rowCount() == 2 and w.table.item(0, mw.COL_FRAMES).text().startswith("1-")
      and w.table.item(0, mw.COL_STATUS).text() == "generated", [w.table.item(0, c).text() for c in range(3)])
check("U2 no CLIP ref yet: Swap/Save disabled, label", not w.btn_swap.isEnabled() and "no CLIP" in w.lb_current.text())
w.le_avatar.setText(AVATAR)
w.table.selectRow(0)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
w.on_build()
pump()
rn = rs.find_clip_ref()
check("U3 Build: avatar + CLIP referenced, range set, fps ntsc", bool(rn) and len(rs.other_references()) == 1
      and cmds.playbackOptions(q=True, max=True) > 1 and cmds.currentUnit(q=True, time=True) == "ntsc", rn)
check("U3 current label + Swap enabled + edits 0", names[0] in w.lb_current.text() and w.btn_swap.isEnabled() and w.lb_edits.text().startswith("Edits: 0"))
check("U3 blendShape combo filled", w.cmb_bs.count() == 1 and w.cmb_bs.currentText().endswith("face_bs"))

# ---- Connect
res = w.on_connect()
pump()
check("U4 Connect: 51 connected, tongueOut missing, label", res and res["connected"] == 51 and "tongueOut" in log_text(w)
      and "51 connected" in w.lb_connect.text())
check("U4 optionVar prefs saved", cmds.optionVar(q=mw.prefs.KEYS["avatar"]) == AVATAR and cmds.optionVar(q=mw.prefs.KEYS["clip_dir"]) == OUT)

# ---- Edits
w.cb_allow.setChecked(False)
pump()
check("U5 allow OFF -> label warns", not rs.anim_curve_edits_enabled() and "OFF" in w.lb_edits.text())
w.cb_allow.setChecked(True)
pump()
curve = "CLIP:JALI_CTL_PH_AAA_ty"
cmds.keyframe(curve, e=True, t=(10, 10), valueChange=0.9)
w.refresh_state()
check("U5 one pending edit listed, Save/Discard enabled", w.lb_edits.text().startswith("Edits: 1") and w.lst_edits.count() == 1
      and w.btn_save.isEnabled() and w.btn_discard.isEnabled())
# Swap with pending -> dialog: Cancel
class _Box(object):
    choice = "cancel"
    def __init__(self, *a, **k):
        self.buttons = {}
    def setWindowTitle(self, *a): pass
    def setText(self, *a): pass
    def addButton(self, label, role):
        key = "save" if label.startswith("Save") else "discard" if label.startswith("Discard") else "cancel"
        self.buttons[key] = object()
        return self.buttons[key]
    def exec_(self): pass
    def clickedButton(self):
        return self.buttons[_Box.choice]
_RealBox = mw.QMessageBox
mw.QMessageBox = type("QMB", (), {"question": staticmethod(lambda *a, **k: _RealBox.Yes), "Yes": _RealBox.Yes, "No": _RealBox.No,
                                    "AcceptRole": 0, "DestructiveRole": 1, "RejectRole": 2, "information": staticmethod(lambda *a, **k: None)})
mw.QMessageBox = _Box
_Box.AcceptRole, _Box.DestructiveRole, _Box.RejectRole = 0, 1, 2
w.table.selectRow(1)
w.on_swap()
pump()
check("U6 Swap with pending + Cancel -> stays on clip 1", names[0] in w.lb_current.text() and "cancelled" in log_text(w))
_Box.choice = "save"
mtime0 = os.path.getmtime(clips[0]["out_mb"])
w.on_swap()
pump()
check("U6 Swap with pending + Save -> saved into clip 1, now on clip 2, status edited", names[1] in w.lb_current.text()
      and os.path.getmtime(clips[0]["out_mb"]) > mtime0 and w.table.item(0, mw.COL_STATUS).text() == "edited"
      and clip_manifest.load(OUT)["clips"][names[0]]["status"] == "edited")
check("U6 connections survive swap", arkit_connect.connected_count(rs.arkit_out_node(), w.cmb_bs.currentText()) == 51)
cmds.keyframe(curve, e=True, t=(5, 5), valueChange=0.33)
w.refresh_state()
_Box.choice = "discard"
w.table.selectRow(0)
w.on_swap()
pump()
check("U6 Swap with pending + Discard -> on clip 1, edits 0", names[0] in w.lb_current.text() and w.lb_edits.text().startswith("Edits: 0"))
mw.QMessageBox = _RealBox

# Prev / Next
w.on_step(1)
pump()
check("U7 Next swaps to clip 2", names[1] in w.lb_current.text())
w.on_step(-1)
pump()
check("U7 Prev swaps back to clip 1", names[0] in w.lb_current.text())
w.on_step(-1)
pump()
check("U7 Prev at the first clip stays", names[0] in w.lb_current.text() and "already the current" in log_text(w))

# Save Clip Edits 직접 + Discard 직접
cmds.keyframe(curve, e=True, t=(12, 12), valueChange=0.8)
w.refresh_state()
check("U8 Save Clip Edits returns True and clears", w.on_save_edits() and w.lb_edits.text().startswith("Edits: 0"))
cmds.keyframe(curve, e=True, t=(13, 13), valueChange=0.1)
w.refresh_state()
w.on_discard()
pump()
check("U8 Discard clears", w.lb_edits.text().startswith("Edits: 0") and "Discarded 1" in log_text(w))

# Disconnect
w.on_disconnect()
pump()
check("U9 Disconnect -> 0 connected", "Disconnected 51" in log_text(w) and arkit_connect.connected_count(rs.arkit_out_node(), w.cmb_bs.currentText()) == 0)

# Open Clip / Save & Close
w.table.selectRow(1)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)
w.on_open_clip()
pump()
check("U10 Open Clip opens the .mb with a temp avatar", cmds.file(q=True, sceneName=True).lower().replace("/", "\\") == clips[1]["out_mb"].lower()
      and rs.temp_avatar_ref() != "" and rs.arkit_out_node() == "JALI:ARKIT_OUT")
cmds.setKeyframe("JALI:CTL_PH_AAA.ty", t=300, v=0.7)
w.on_save_close()
pump()
check("U10 Save Clip & Close: saved, temp avatar gone, new scene, manifest edited",
      not cmds.file(q=True, sceneName=True) and clip_manifest.load(OUT)["clips"][names[1]]["status"] == "edited")
cmds.file(clips[1]["out_mb"], open=True, force=True, prompt=False)
check("U10 reopened clip 2 has the new key and no avatar reference", 300.0 in (cmds.keyframe("JALI_CTL_PH_AAA_ty", q=True, tc=True) or [])
      and not [r for r in cmds.ls(type="reference") if rs.TEMP_AVATAR_NS in r])

# run(True) 는 기존 창을 닫고 다시 연다
w2 = tool.run(False)
pump()
check("U11 run() again closes the old window", w2 is not w and w2.isVisible())
w2.close()
shutil.rmtree(work, ignore_errors=True)
finish()
