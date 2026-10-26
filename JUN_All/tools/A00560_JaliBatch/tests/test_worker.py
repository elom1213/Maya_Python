# -*- coding: utf-8 -*-
# A00560_JaliBatch - 워커 실기 시험 (T3 generate · T4 덮어쓰기 · T5 취소 · 실패 · T6 validate · repath) - mayapy 2024
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_worker.py [out_en_002] [A0030.ma]
# 워커는 **실제 mayapy 하위 프로세스**로 돌린다(UI 와 같은 경로: Framework.core.mayapy_runner 프로토콜). 결과 클립은 이
# 프로세스(maya.standalone)에서 열어 검사한다. 원본 컨트롤러 · 음성은 복사본만 쓴다.
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from Framework.core import mayapy_runner   # noqa: E402
from tools.A00560_JaliBatch.app.core import source_scan, manifest, jobs   # noqa: E402
from tools.A00560_JaliBatch.app.config import app_meta   # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI_Voice\0060_Vivian_voice\out_en_002"
CTL_SRC = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\USER\Desktop\JP\0035_maya_src_rig\02_Cage_JALI\A0030_jali_slider_ctl_direct_arkit.ma"
MAYAPY = sys.executable
R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


if not os.path.isdir(SRC) or not os.path.isfile(CTL_SRC):
    print("SKIP no example data / controller")
    print("RESULT OK (skipped)")
    sys.exit(0)

work = tempfile.mkdtemp(prefix="a00560_worker_")
CTL = os.path.join(work, "ctl", "A0030_ctl.ma")
os.makedirs(os.path.dirname(CTL))
shutil.copy2(CTL_SRC, CTL)
OUT = os.path.join(work, "maya")
TOOL = "A00560_JaliBatch 01.00 (test)"


def run_worker(job, on_progress=None):
    """UI 의 run_job 과 같은 일을 subprocess 로. Returns (result dict | None, logs, errors, progress, exit)."""
    job_dir = mayapy_runner.new_job_dir("a00560_test")
    job_path, result_path, cancel_flag = mayapy_runner.write_job(job_dir, job)
    cmd = mayapy_runner.command(MAYAPY, job_path, app_meta.worker_path())
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
                            env=dict(os.environ, PYTHONUNBUFFERED="1"))
    logs, errors, prog, result = [], [], [], None
    for line in proc.stdout:
        msg = mayapy_runner.parse_line(line)
        if msg is None:
            continue
        if msg["type"] == "log":
            logs.append(msg["text"])
        elif msg["type"] == "progress":
            prog.append((msg["done"], msg["total"], msg.get("message")))
            if on_progress:
                on_progress(msg, cancel_flag)
        elif msg["type"] == "error":
            errors.append(msg["text"])
        elif msg["type"] == "result":
            result = mayapy_runner.read_result(msg["path"])
    proc.wait()
    return result, logs, errors, prog, proc.returncode


scan = source_scan.scan(SRC)
clips_all = [c.as_job_clip(1, OUT) for c in scan.runnable]
clips_all[1]["start"] = 101            # 표에서 손으로 고친 Start (D7)
mf_path = manifest.path_for(OUT)


def gen_job(clips, overwrite="skip", **kw):
    args = dict(controller=CTL, mapping="jali_slider_dummy_in", fps=30, default_start=1, jali_mode="data",
                jali_fixed=(0.6, 0.6), jali_scale=None, viseme_scale=None, overwrite=overwrite, copy_wav=True,
                out_dir=OUT, manifest_path=mf_path, tool=TOOL, clips=clips)
    args.update(kw)
    return jobs.generate_job(**args)


# ---------------------------------------------------------------- T3 generate 5
t0 = time.time()
result, logs, errors, prog, code = run_worker(gen_job(clips_all))
dt = time.time() - t0
print("INFO generate 5: %.1fs exit %s errors %s" % (dt, code, errors))
for l in logs:
    print("   LOG", l[:150])
check("T3 worker exit 0, no protocol error", code == 0 and not errors, (code, errors))
check("T3 5 generated", result and result["generated"] == 5 and result["failed"] == 0, result and {k: result[k] for k in ("generated", "skipped", "failed")})
check("T3 five .mb + wav copies", all(os.path.isfile(c["out_mb"]) for c in clips_all) and
      all(os.path.isfile(os.path.join(OUT, c["name"] + ".wav")) for c in clips_all))
check("T3 progress messages carry clip names", any(p[2] == clips_all[0]["name"] for p in prog), prog[:3])
mf = manifest.load(OUT)
check("T3 manifest: 5 generated, start of clip 2 = 101", len(mf["clips"]) == 5 and all(c["status"] == "generated" for c in mf["clips"].values())
      and mf["clips"][clips_all[1]["name"]]["start"] == 101, {k: (v["status"], v["start"]) for k, v in mf["clips"].items()})
c2 = [c for c in result["clips"] if c["name"] == clips_all[1]["name"]][0]
check("T3 clip 2 keyed from 101", c2["start"] == 101 and c2["end"] == 101 + c2["span"], (c2["start"], c2["end"], c2["span"]))
check("T3 24 channels baked each (16 PH + 6 CO sliders + JaLi tx/ty; the unmapped coartic is sampled flat)", all(c["baked"] == 24 for c in result["clips"]), [c["baked"] for c in result["clips"]])

# 클립 검사 (이 프로세스에서 연다)
import maya.standalone   # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds   # noqa: E402
from Framework.jali import bake, clip_stamp, lipsync_data, sequence   # noqa: E402

first = clips_all[0]
cmds.file(first["out_mb"], open=True, force=True, prompt=False)
data = lipsync_data.load(first["txt"])
n_frames = sequence.key_frames(data, 30.0)
check("T3 reopened: unit ntsc", cmds.currentUnit(q=True, time=True) == "ntsc")
check("T3 reopened: JALI reference loaded", cmds.referenceQuery("JALIRN", isLoaded=True))
check("T3 reopened: failedEdits 0", not (cmds.referenceQuery("JALIRN", editStrings=True, failedEdits=True, successfulEdits=False) or []))
check("T3 reopened: CTL_PH_AAA.ty keys = frames + 1", cmds.keyframe("JALI:CTL_PH_AAA.ty", q=True, keyframeCount=True) == n_frames + 1)
check("T3 reopened: DUMMY_IN curves 0", bake.dummy_in_curve_count("JALI:") == 0)
check("T3 reopened: curves named JALI_<ctl>_<attr>", cmds.objExists("JALI_CTL_PH_AAA_ty") and cmds.objExists("JALI_CNT_JaLi_tx"))
check("T3 reopened: sound node offset = start, file = copy", cmds.getAttr("jali_lipsync_audio.offset") == 1 and
      os.path.normcase(cmds.getAttr("jali_lipsync_audio.filename")) == os.path.normcase(os.path.join(OUT, first["name"] + ".wav")))
stamp = clip_stamp.read()
check("T3 reopened: stamp", stamp and stamp["controller"] == CTL and stamp["fps"] == 30.0 and stamp["start"] == 1 and stamp["frames"] == n_frames, stamp)
check("T3 reopened: playback range", (cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)) == (1, stamp["end"]))
vs = [cmds.getAttr("JALI:ARKIT_OUT.jawOpen", t=f) for f in range(1, n_frames, 9)]
check("T3 reopened: ARKIT_OUT.jawOpen follows keys", max(vs) - min(vs) > 0.01)
# JaLi 값 = 데이터 (Jaw 열 × scale 1): 프레임 f 의 CNT_JaLi.tx == 모델 행 round(f/30*100) 의 Jaw
f = 30            # 프레임 F 의 값 = 모델 행 round((F - start) / fps * 100)  (start = 1)
row = data.rows[min(int(round((f - 1) / 30.0 * 100)), len(data.rows) - 1)]
check("T3 reopened: CNT_JaLi.tx at f30 == model Jaw", abs(cmds.getAttr("JALI:CNT_JaLi.tx", t=f) - min(max(row[0], 0), 1)) < 1e-4,
      (cmds.getAttr("JALI:CNT_JaLi.tx", t=f), row[0]))
cmds.file(new=True, force=True)

# ---------------------------------------------------------------- T4 덮어쓰기
mtimes = {c["name"]: os.path.getmtime(c["out_mb"]) for c in clips_all}
result, logs, errors, prog, code = run_worker(gen_job(clips_all, overwrite="skip"))
check("T4 skip: 5 skipped, files untouched", result["skipped"] == 5 and result["generated"] == 0 and
      all(os.path.getmtime(c["out_mb"]) == mtimes[c["name"]] for c in clips_all))
time.sleep(1.1)
one = [clips_all[2]]
result, logs, errors, prog, code = run_worker(gen_job(one, overwrite="overwrite"))
check("T4 overwrite: regenerated, mtime changed, no backup folder", result["generated"] == 1 and
      os.path.getmtime(one[0]["out_mb"]) > mtimes[one[0]["name"]] and not os.path.isdir(os.path.join(OUT, "backup")))
result, logs, errors, prog, code = run_worker(gen_job(one, overwrite="backup"))
bk = os.path.join(OUT, "backup", one[0]["name"] + "_01.mb")
check("T4 backup: backup/<name>_01.mb written", result["generated"] == 1 and os.path.isfile(bk) and result["clips"][0]["backup"] == bk, result["clips"][0].get("backup"))
result, logs, errors, prog, code = run_worker(gen_job(one, overwrite="backup"))
check("T4 backup: second time -> _02", os.path.isfile(os.path.join(OUT, "backup", one[0]["name"] + "_02.mb")))

# ---------------------------------------------------------------- T5 취소 (3번째 시작 알림이 오면 플래그) · 실패 클립
OUT2 = os.path.join(work, "maya2")
clips2 = [dict(c, out_mb=os.path.join(OUT2, c["name"] + ".mb")) for c in clips_all]


def cancel_at_third(msg, cancel_flag):
    if msg["done"] >= 2 and msg.get("message") == clips2[2]["name"]:
        mayapy_runner.request_cancel(cancel_flag)


result, logs, errors, prog, code = run_worker(gen_job(clips2, out_dir=OUT2, manifest_path=manifest.path_for(OUT2)), on_progress=cancel_at_third)
n_files = sum(1 for c in clips2 if os.path.isfile(c["out_mb"]))
check("T5 cancel: cancelled flag, exit 0, stopped at a clip boundary (3 made: flag arrives while #3 runs)",
      result and result["cancelled"] and code == 0 and result["generated"] == n_files == 3, (code, result and result["generated"], n_files))

OUT3 = os.path.join(work, "maya3")
bad_dir = os.path.join(work, "bad_src")
os.makedirs(bad_dir)
for c in clips_all[:2]:
    for ext in (".txt", ".wav", ".visemenet.json"):
        p = os.path.join(SRC, c["name"] + ext)
        if os.path.isfile(p):
            shutil.copy2(p, bad_dir)
bad_txt = os.path.join(bad_dir, clips_all[0]["name"] + ".txt")
with open(bad_txt, "a") as f:
    f.write("\nthis line is broken\n")
# json 의 rows 검증이 먼저 걸린다 - 어느 쪽이든 ValueError 면 된다
clips3 = [dict(c, txt=os.path.join(bad_dir, c["name"] + ".txt"), wav=os.path.join(bad_dir, c["name"] + ".wav"),
               out_mb=os.path.join(OUT3, c["name"] + ".mb")) for c in clips_all[:2]]
result, logs, errors, prog, code = run_worker(gen_job(clips3, out_dir=OUT3, manifest_path=manifest.path_for(OUT3)))
check("T5 broken txt: that clip failed, the other generated, exit 0", result and result["failed"] == 1 and result["generated"] == 1 and code == 0,
      (code, result and [(c["name"][-7:], c["status"]) for c in result["clips"]]))
mf3 = manifest.load(OUT3)
check("T5 manifest records failed + error text", mf3["clips"][clips3[0]["name"]]["status"] == "failed" and mf3["clips"][clips3[0]["name"]]["error"])
check("T5 failed clip has no .mb", not os.path.isfile(clips3[0]["out_mb"]))

# ---------------------------------------------------------------- T6 validate · repath
paths = [c["out_mb"] for c in clips_all]
result, logs, errors, prog, code = run_worker(jobs.validate_job(paths, mf_path, TOOL))
rows = result["rows"]
check("T6 validate 5 ok", result["ok"] == 5 and all(r["baked_channels"] == 24 and r["dummy_in_curves"] == 0 and r["failed_edits"] == 0
                                                     and r["sound"] and r["stamp"] for r in rows), [(r["name"][-7:], r["problems"]) for r in rows])
check("T6 validate reports controller path + stamp start", os.path.normcase(os.path.normpath(rows[1]["controller"])) == os.path.normcase(CTL) and rows[1]["start"] == 101, rows[1]["controller"])

# 컨트롤러 파일을 "수정" (내용 같은 복사본을 다른 경로에, mtime 새로) -> stamp 와 어긋남 경고 · repath
time.sleep(1.1)
CTL2 = os.path.join(work, "ctl", "A0030_ctl_v2.ma")
shutil.copy(CTL, CTL2)
with open(CTL, "a") as f:
    f.write("\n// touched\n")
result, logs, errors, prog, code = run_worker(jobs.validate_job(paths[:1], mf_path, TOOL))
check("T6 controller changed -> warn", result["warn"] == 1 and any("changed" in p for p in result["rows"][0]["problems"]), result["rows"][0]["problems"])
# 이름 바꾼 컨트롤러로 repath -> failedEdits
CTL3 = os.path.join(work, "ctl", "A0030_ctl_renamed.ma")
with open(CTL2, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()
with open(CTL3, "w", encoding="utf-8") as f:
    f.write(text.replace('"CTL_PH_AAA"', '"CTL_PH_AAX"').replace("CTL_PH_AAA|", "CTL_PH_AAX|"))
result, logs, errors, prog, code = run_worker(jobs.validate_job(paths[:1], mf_path, TOOL, repath=CTL3))
r0 = result["rows"][0]
check("T6 repath to renamed controller -> failedEdits >= 1, saved", r0.get("repathed") and r0["failed_edits"] >= 1 and r0.get("saved"), (r0.get("failed_edits"), r0["problems"]))
cmds.file(paths[0], open=True, force=True, prompt=False)
check("T6 repath persisted in the clip", os.path.normcase(cmds.referenceQuery("JALIRN", filename=True, withoutCopyNumber=True)) == os.path.normcase(CTL3))
cmds.file(new=True, force=True)
result, logs, errors, prog, code = run_worker(jobs.validate_job(paths[:1], mf_path, TOOL, repath=CTL2))
check("T6 repath back to good copy -> failedEdits 0, keys intact", result["rows"][0]["failed_edits"] == 0 and result["rows"][0]["baked_channels"] == 24
      and result["rows"][0]["keys"] == rows[0]["keys"], (result["rows"][0]["failed_edits"], result["rows"][0]["keys"], rows[0]["keys"]))

print("RESULT", "OK" if all(R) else "FAIL", "{0}/{1}".format(sum(R), len(R)))
maya.standalone.uninitialize()
shutil.rmtree(work, ignore_errors=True)
os._exit(0 if all(R) else 1)
