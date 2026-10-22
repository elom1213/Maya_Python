# -*- coding: utf-8 -*-
# A00540_JaliLipSync - UI 시험 (T-U, mayapy 오프스크린, 합성 리그)
#   mayapy test_ui.py
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다.
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize()
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00540_JaliLipSync.app.core import mapping as mapping_mod, lipsync_data   # noqa: E402
import tools.A00540_JaliLipSync as tool   # noqa: E402

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


def log_text(win):
    app.processEvents()
    return win.log_view.toPlainText()


def pump():
    app.processEvents()
    app.processEvents()


new = mapping_mod.load_mapping("jali_slider_dummy_in")
cmds.file(new=True, force=True)
cmds.currentUnit(time="film")
for role, name in new["nodes"].items():
    node = cmds.createNode("transform", n=name)
    for t in new["targets"]:
        if t["role"] == role:
            cmds.addAttr(node, ln=t["attr"].split(".", 1)[1], at="double", min=0.0, max=1.0, k=True)

# 합성 txt (30줄, Aa 0.5, Jaw 0.4)
idx = {c: i for i, c in enumerate(lipsync_data.MODEL_COLUMNS)}
row = [0.0] * 22
row[idx["Aa"]], row[idx["Jaw"]] = 0.5, 0.4
txt = os.path.join(tempfile.mkdtemp(), "synthetic.txt")
with open(txt, "w") as f:
    for _ in range(30):
        f.write(" ".join("%g" % v for v in row) + "\n")

win = tool.run(False)
pump()

# U1 기본 상태
check("U1 default Auto, manual fields disabled", win.rb_auto.isChecked() and not win.le_roles["phonemes"].isEnabled()
      and win.cmb_rig.isEnabled())

# U2 매핑 바꾸면 스핀박스 리셋
win.cmb_mapping.setCurrentText("jali_slider_dummy_in"); pump()
check("U2 new mapping -> scales 1 / 1, Jaw range 0-1 value 0.6",
      win.ds_scale.value() == 1.0 and win.ds_jali_scale.value() == 1.0 and win.ds_jaw.maximum() == 1.0
      and abs(win.ds_jaw.value() - 0.6) < 1e-9 and abs(win.ds_lip.value() - 0.6) < 1e-9)
check("U2 placeholder shows mapping node", win.le_roles["phonemes"].placeholderText() == "DUMMY_IN_PHONEMES")
check("U2 Auto finds (root)", win.cmb_rig.count() == 1 and win.cmb_rig.currentText() == "(root)")
win.cmb_mapping.setCurrentText("angela_jali_visemenet"); pump()
check("U2 angela mapping -> scales 10 / 10, Jaw range 0-15 value 9",
      win.ds_scale.value() == 10.0 and win.ds_jali_scale.value() == 10.0 and win.ds_jaw.maximum() == 15.0
      and win.ds_jaw.value() == 9.0)
check("U2 angela marker not in scene -> rig combo empty + WARN", win.cmb_rig.count() == 0 and "No rig with 'CNT_PHONEMES'" in log_text(win))
win.ds_scale.setValue(3.0)
win.cmb_mapping.setCurrentText("jali_slider_dummy_in"); pump()
check("U2 user value overwritten on mapping change", win.ds_scale.value() == 1.0)

# U3 Manual 전환 · 선택으로 채우기
win.rb_manual.setChecked(True); pump()
check("U3 manual: rig combo disabled, fields enabled", not win.cmb_rig.isEnabled() and win.le_roles["coartic"].isEnabled())
cmds.select("DUMMY_IN_PHONEMES")
win.on_pick_role("phonemes")
check("U3 << Sel fills the field", win.le_roles["phonemes"].text() == "DUMMY_IN_PHONEMES")
cmds.select(clear=True)
win.on_pick_role("coartic")
check("U3 << Sel with nothing selected -> WARN, field empty", "Select a node first" in log_text(win) and win.le_roles["coartic"].text() == "")
win.le_roles["phonemes"].clear()

# U4 Manual 전부 빈 채 Apply
win.le_txt.setText(txt); win._load_txt(auto_wav=False); pump()
win.on_apply(); pump()
check("U4 manual all empty -> ERROR, no keys", "[ERROR] Manual target" in log_text(win)
      and not cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, keyframeCount=True))

# U5 Manual phonemes 만 → 건너뜀 표시
win.le_roles["phonemes"].setText("DUMMY_IN_PHONEMES")
win.on_apply(); pump()
txt_log = log_text(win)
check("U5 manual phonemes only -> DONE + skipped coartic, jali", "[DONE]" in txt_log and "skipped: coartic, jali" in txt_log
      and cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, keyframeCount=True) == 8
      and not cmds.keyframe("DUMMY_IN_JALI.Jaw", q=True, keyframeCount=True))
win.on_remove(); pump()
check("U5 remove manual", "[OK] Removed keys on 16" in log_text(win) and not cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, keyframeCount=True))

# U6 Auto + 새 규칙 Apply
win.rb_auto.setChecked(True); pump()
win.on_apply(); pump()
check("U6 auto apply -> 23 attrs keyed, Jaw 0.4", "[DONE] 23 attributes keyed on '(root)'" in log_text(win)
      and abs(cmds.keyframe("DUMMY_IN_JALI.Jaw", q=True, eval=True, t=(3, 3))[0] - 0.4) < 1e-6)
win.on_select_controls(); pump()
check("U6 select controls", set(cmds.ls(selection=True)) == {"DUMMY_IN_JALI", "DUMMY_IN_PHONEMES", "DUMMY_IN_COARTIC"})

# U7 단위 경고: angela 규칙(scale 10) + Manual 로 max-1 노드
win.rb_manual.setChecked(True)
win.cmb_mapping.setCurrentText("angela_jali_visemenet"); pump()
win.le_roles["phonemes"].setText("DUMMY_IN_PHONEMES")
win.le_roles["coartic"].clear(); win.le_roles["jali"].clear()
win.on_apply(); pump()
check("U7 scale 10 on max-1 -> WARN exceeds", "exceeds the attribute maximum 1" in log_text(win))

# U8 Fixed 모드: JaLi scale 비활성, Jaw/Lip 활성
win.rb_jali_fixed.setChecked(True); pump()
check("U8 fixed -> jali scale disabled, jaw/lip enabled", not win.ds_jali_scale.isEnabled() and win.ds_jaw.isEnabled())

# U9 창 크기
check("U9 window height sane", win.sizeHint().height() < 1000 and win.minimumSizeHint().height() < 800)

print("RESULT", "OK" if all(R) else "%d FAILED" % R.count(False))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
