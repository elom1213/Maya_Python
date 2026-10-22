# -*- coding: utf-8 -*-
# A00540_JaliLipSync - UI 시험 (T-U, mayapy 오프스크린, 합성 리그)
#   mayapy test_ui.py
# QApplication 은 maya.standalone.initialize() 보다 먼저 만든다.
import os
import sys
import tempfile
import wave

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide2.QtWidgets import QApplication   # noqa: E402
app = QApplication.instance() or QApplication(sys.argv)
import maya.standalone   # noqa: E402
maya.standalone.initialize()
import maya.cmds as cmds   # noqa: E402

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00540_JaliLipSync.app.core import mapping as mapping_mod, lipsync_data   # noqa: E402
from tools.A00540_JaliLipSync.app.ui.main_window import COL_START, COL_TXT, COL_WAV   # noqa: E402
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


def column(win, col):
    return [win.table.item(r, col).text() for r in range(win.table.rowCount())]


new = mapping_mod.load_mapping("jali_slider_dummy_in")
cmds.file(new=True, force=True)
cmds.currentUnit(time="film")
for role, name in new["nodes"].items():
    node = cmds.createNode("transform", n=name)
    for t in new["targets"]:
        if t["role"] == role:
            cmds.addAttr(node, ln=t["attr"].split(".", 1)[1], at="double", min=0.0, max=1.0, k=True)

# 합성 txt (30줄, Aa 0.5, Jaw 0.4) / 두 번째 클립 (50줄, Aa 0.2) + wav 둘 다
idx = {c: i for i, c in enumerate(lipsync_data.MODEL_COLUMNS)}
work = tempfile.mkdtemp()


def write_txt(name, n_rows, aa, jaw):
    row = [0.0] * 22
    row[idx["Aa"]], row[idx["Jaw"]] = aa, jaw
    path = os.path.join(work, name + ".txt")
    with open(path, "w") as f:
        for _ in range(n_rows):
            f.write(" ".join("%g" % v for v in row) + "\n")
    return path


def write_wav(name, seconds):
    path = os.path.join(work, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x10\x00" * int(seconds * 44100))
    return path


txt = write_txt("synthetic", 30, 0.5, 0.4)
txt2, wav2 = write_txt("second", 50, 0.2, 0.1), write_wav("second", 0.82)
wav1 = write_wav("synthetic", 0.62)

win = tool.run(False)
pump()

# U1 기본 상태
check("U1 default Auto, manual fields disabled", win.rb_auto.isChecked() and not win.le_roles["phonemes"].isEnabled()
      and win.cmb_rig.isEnabled())
check("U1 empty clip table", win.table.rowCount() == 0 and win.lb_info.text() == "No clips")

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

# U4 클립 추가 (wav 자동) · Manual 전부 빈 채 Apply
clip = win.add_txt(txt); pump()
check("U4 add_txt: row with auto wav, start 1, length from wav", clip is not None and win.table.rowCount() == 1
      and column(win, COL_TXT) == ["synthetic.txt"] and column(win, COL_WAV) == ["synthetic.wav"] and column(win, COL_START) == ["1"]
      and "1 clip(s): frames 1-15" in win.lb_info.text())
check("U4 bad txt -> ERROR, not added", win.add_txt(os.path.join(work, "missing.txt")) is None and win.table.rowCount() == 1
      and "[ERROR] TXT file not found" in log_text(win))
win.on_apply(); pump()
check("U4 manual all empty -> ERROR, no keys", "[ERROR] Manual target" in log_text(win)
      and not cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, keyframeCount=True))

# U5 Manual phonemes 만 → 건너뜀 표시 (단일 클립, 오디오 = 그 클립의 wav)
win.le_roles["phonemes"].setText("DUMMY_IN_PHONEMES")
win.on_apply(); pump()
txt_log = log_text(win)
check("U5 manual phonemes only -> DONE + skipped coartic, jali", "[DONE]" in txt_log and "skipped: coartic, jali" in txt_log
      and cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, keyframeCount=True) == 8
      and not cmds.keyframe("DUMMY_IN_JALI.Jaw", q=True, keyframeCount=True))
check("U5 single clip: its own wav attached, no sequence wav", "[OK] Audio 'jali_lipsync_audio' at frame 1" in txt_log
      and "Sequence WAV written" not in txt_log and cmds.objExists("jali_lipsync_audio"))
win.on_remove(); pump()
check("U5 remove manual", "[OK] Removed keys on 16" in log_text(win) and not cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, keyframeCount=True))

# U6 Auto + 새 규칙 Apply
win.rb_auto.setChecked(True); pump()
win.on_apply(); pump()
check("U6 auto apply -> 23 attrs keyed, Jaw 0.4", "[DONE] 23 attributes keyed on '(root)': 1 clip(s)" in log_text(win)
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
win.rb_jali_fixed.setChecked(False); win.rb_jali_data.setChecked(True)

# U9 창 크기 (v01.02 클립 표가 들어 1005 / 831 - 1080p 화면에 맞는다)
check("U9 window height sane", win.sizeHint().height() < 1100 and win.minimumSizeHint().height() < 850)

# ---------------------------------------------------------------- v01.02 여러 클립
win.rb_auto.setChecked(True)
win.cmb_mapping.setCurrentText("jali_slider_dummy_in"); pump()
win.on_remove(); pump()

# U10 두 번째 클립 + Hold → 표의 Start 열 · 정보 줄
win.add_txt(txt2); pump()
win.sb_start.setValue(10); win.sb_hold.setValue(6); pump()
# synthetic: wav 0.62 s -> span int(0.62*24) = 14 -> 10-24 ; next = 24 + 1 + 6 = 31 ; second: wav 0.82 -> span 19 -> 31-50
check("U10 table starts follow Start frame + Hold", column(win, COL_START) == ["10", "31"]
      and "2 clip(s): frames 10-50" in win.lb_info.text() and "hold 6" in win.lb_info.text())
win.sb_hold.setValue(0); pump()
check("U10 hold 0 -> second starts right after", column(win, COL_START) == ["10", "25"])
win.sb_hold.setValue(6); pump()

# U11 순서 바꾸기 · Apply → 클립별 로그 · 합친 wav · 사운드 노드 · 재생 범위
win.table.selectRow(1); win.on_move(-1); pump()
check("U11 Up moves 'second' first", column(win, COL_TXT) == ["second.txt", "synthetic.txt"] and column(win, COL_START) == ["10", "36"])
win.table.selectRow(0); win.on_move(1); pump()
check("U11 Down moves it back", column(win, COL_TXT) == ["synthetic.txt", "second.txt"])
seq_wav = os.path.join(work, "seq_out.wav")
win.le_seq_wav.setText(seq_wav)
win.on_apply(); pump()
txt_log = log_text(win)
check("U11 apply logs each clip", "[OK] 1/2 synthetic.txt: frames 10-24" in txt_log and "[OK] 2/2 second.txt: frames 31-50" in txt_log
      and "[DONE] 23 attributes keyed on '(root)': 2 clip(s), frames 10-50 @ 24 fps, hold 6" in txt_log)
check("U11 sequence wav written + attached at 10", os.path.isfile(seq_wav) and "Sequence WAV written: {0}".format(seq_wav) in txt_log
      and cmds.objExists("jali_lipsync_audio") and cmds.getAttr("jali_lipsync_audio.offset") == 10)
with wave.open(seq_wav, "rb") as w:
    n_seq = w.getnframes()
check("U11 sequence wav length = second clip offset + its length", n_seq == int(round(21 / 24.0 * 44100)) + int(0.82 * 44100))
check("U11 keys: AAA 0.5 in clip 1, held through the gap (frame 28), 0.2 in clip 2",
      abs(cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, eval=True, t=(12, 12))[0] - 0.5) < 1e-6
      and abs(cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, eval=True, t=(28, 28))[0] - 0.5) < 1e-6
      and abs(cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, eval=True, t=(40, 40))[0] - 0.2) < 1e-6)
check("U11 playback range 10-50", cmds.playbackOptions(q=True, minTime=True) == 10 and cmds.playbackOptions(q=True, maxTime=True) == 50)

# U12 Remove Keys 는 전체 구간 · No WAV · Remove · Clear
win.on_remove(); pump()
check("U12 remove keys over the sequence range", "[OK] Removed keys on 23 attribute(s), frames 10-50" in log_text(win)
      and not cmds.keyframe("DUMMY_IN_PHONEMES.AAA", q=True, keyframeCount=True))
win.table.selectRow(1); win.on_clear_wav(); pump()
check("U12 No WAV -> (none), length from txt (0.5 s -> 12 f)", column(win, COL_WAV) == ["synthetic.wav", "(none)"]
      and win.table.item(1, 4).text().startswith("0.50 s / 12 f"))
win.table.selectRow(0); win.on_remove_clip(); pump()
check("U12 Remove row", column(win, COL_TXT) == ["second.txt"] and column(win, COL_START) == ["10"])
win.on_clear_clips(); pump()
check("U12 Clear", win.table.rowCount() == 0 and win.lb_info.text() == "No clips")
win.on_apply(); pump()
check("U12 apply with no clips -> ERROR", "[ERROR] No clips" in log_text(win))

print("RESULT", "OK" if all(R) else "%d FAILED" % R.count(False))
maya.standalone.uninitialize()
sys.exit(0 if all(R) else 1)
