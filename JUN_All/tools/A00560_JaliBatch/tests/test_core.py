# -*- coding: utf-8 -*-
# A00560_JaliBatch - 코어 시험 (T2: source_scan · manifest · jobs, Maya 비의존 - python 또는 mayapy)
#   python test_core.py
import json
import os
import shutil
import sys
import tempfile
import wave

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00560_JaliBatch.app.core import source_scan, manifest, jobs, prefs   # noqa: E402
from Framework.jali import lipsync_data   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


REAL = r"C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI_Voice\0060_Vivian_voice\out_en_002"
SRC = r"C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI_Voice\0060_Vivian_voice\src_en"
work = tempfile.mkdtemp(prefix="a00560_core_")
idx = {c: i for i, c in enumerate(lipsync_data.MODEL_COLUMNS)}


def write_txt(folder, name, n_rows):
    row = [0.0] * 22
    row[idx["Aa"]] = 0.5
    path = os.path.join(folder, name + ".txt")
    with open(path, "w") as f:
        for _ in range(n_rows):
            f.write(" ".join("%g" % v for v in row) + "\n")
    return path


def write_wav(folder, name, seconds):
    path = os.path.join(folder, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00\x10" * int(seconds * 44100))
    return path


# ---------------------------------------------------------------- source_scan
if os.path.isdir(REAL):
    res = source_scan.scan(REAL)
    check("S1 real folder: 5 clips", len(res.clips) == 5, [c.name for c in res.clips])
    check("S1 real folder: all runnable (json + wav)", len(res.runnable) == 5 and all(c.json and c.wav for c in res.clips))
    check("S1 natural order", [c.name for c in res.clips] == sorted([c.name for c in res.clips], key=source_scan._natural_key))
    c0 = res.clips[0]
    check("S1 frames at 30 fps = wav length (10.8 s -> 324)", c0.frames(30) == int(c0.wav_seconds * 30 + 1e-6), (c0.frames(30), c0.wav_seconds))
    check("S1 frames at 24 fps smaller", c0.frames(24) < c0.frames(30))
    check("S1 no hint", res.hint == "")
else:
    print("SKIP S1 (no real folder)")

if os.path.isdir(SRC):
    res = source_scan.scan(SRC)
    check("S2 transcript folder: 0 clips, 5 skipped, hint", len(res.clips) == 0 and len(res.skipped) == 5 and "VisemeNet Converter" in res.hint,
          (len(res.clips), len(res.skipped), res.hint))
else:
    print("SKIP S2 (no src folder)")

# 합성: json 없음 · wav 없음 · 이름에 _fNNNN 가 있어도 없어도 같은 결과
syn = os.path.join(work, "syn")
os.makedirs(syn)
write_txt(syn, "a_f0105_0429", 120); write_wav(syn, "a_f0105_0429", 1.5)
write_txt(syn, "b_plain", 120); write_wav(syn, "b_plain", 1.5)
write_txt(syn, "c_nowav", 120)
with open(os.path.join(syn, "notes.txt"), "w") as f:
    f.write("hello world transcript\n")
res = source_scan.scan(syn)
names = [c.name for c in res.clips]
check("S3 three 22-col txt listed, transcript skipped", names == ["a_f0105_0429", "b_plain", "c_nowav"] and len(res.skipped) == 1, (names, res.skipped))
a, b, c = res.clips
check("S3 json missing -> WARN only (still runnable)", a.ok and any(l == "WARN" and "json" in m for l, m in a.problems))
check("S3 wav missing -> ERROR (excluded)", not c.ok and len(res.runnable) == 2)
check("S3 name with _f0105_0429 gives the SAME frames as plain name (name not read)", a.frames(30) == b.frames(30) == 45, (a.frames(30), b.frames(30)))
check("S3 as_job_clip start comes from the argument", a.as_job_clip(7, work)["start"] == 7 and a.as_job_clip(1, work)["out_mb"].endswith("a_f0105_0429.mb"))
check("S3 summary text", "3 clip(s)" in res.summary() and "1 excluded" in res.summary() and "1 other txt" in res.summary(), res.summary())
try:
    source_scan.scan(os.path.join(work, "nope"))
    check("S4 missing folder raises", False)
except ValueError:
    check("S4 missing folder raises", True)
empty = os.path.join(work, "empty"); os.makedirs(empty)
check("S4 empty folder hint", source_scan.scan(empty).hint == "No txt files in this folder.")

# ---------------------------------------------------------------- manifest
mf = os.path.join(work, "out")
data = manifest.load(mf, "01.00")
check("M1 empty manifest skeleton", data["clips"] == {} and data["format"] == 1 and data["version"] == "01.00")
manifest.set_settings(data, {"fps": 30})
manifest.update_clip(data, "b_plain", start=12, status="generated")
path = manifest.save(mf, data)
check("M1 saved file exists", os.path.isfile(path) and os.path.basename(path) == "jali_clips.manifest.json")
data2 = manifest.load(mf)
check("M1 reload keeps clip + settings", data2["clips"]["b_plain"]["start"] == 12 and data2["settings"]["fps"] == 30)
check("M1 start_of override / default", manifest.start_of(data2, "b_plain", 1) == 12 and manifest.start_of(data2, "zzz", 1) == 1)
manifest.update_clip(data2, "b_plain", status="edited")
check("M1 edited_names", manifest.edited_names(data2, ["b_plain", "a"]) == ["b_plain"])
manifest.update_clip(data2, "a_10", status="x"); manifest.update_clip(data2, "a_2", status="y")
check("M1 ordered_clips natural", [c["name"] for c in manifest.ordered_clips(data2)] == ["a_2", "a_10", "b_plain"])
with open(path, "w") as f:
    f.write("{broken")
try:
    manifest.load(mf)
    check("M2 broken manifest raises", False)
except ValueError:
    check("M2 broken manifest raises", True)

# ---------------------------------------------------------------- jobs
check("J1 fps unit names", [jobs.fps_unit_name(f) for f in (24, 25, 30, 60, 29.97, 12)] == ["film", "pal", "ntsc", "ntscf", "29.97fps", "12fps"])
check("J1 parse_fps", jobs.parse_fps(" 30 ") == 30.0 and jobs.parse_fps("23.976fps") == 23.976)
try:
    jobs.parse_fps("abc"); check("J1 parse_fps bad raises", False)
except ValueError:
    check("J1 parse_fps bad raises", True)
clips = [a.as_job_clip(5, mf), b.as_job_clip(1, mf)]
job = jobs.generate_job("ctl.ma", "jali_slider_dummy_in", 30, 1, "fixed", (0.6, 0.6), None, None, "backup", True, mf,
                        manifest.path_for(mf), "A00560 01.00", clips)
check("J2 generate job fields", job["job"] == "generate" and job["jali"] == {"mode": "fixed", "fixed": [0.6, 0.6], "scale": None}
      and job["clips"][0]["start"] == 5 and job["clips"][1]["start"] == 1 and job["overwrite"] == "backup")
check("J2 json serialisable", json.dumps(job) is not None)
for bad in (dict(controller=""), dict(clips=[]), dict(overwrite="zap")):
    kw = dict(controller="ctl.ma", mapping="m", fps=30, default_start=1, jali_mode="data", jali_fixed=(0.6, 0.6), jali_scale=1.0,
              viseme_scale=1.0, overwrite="skip", copy_wav=True, out_dir=mf, manifest_path="m.json", tool="t", clips=clips)
    kw.update(bad)
    try:
        jobs.generate_job(**kw); ok = False
    except ValueError:
        ok = True
    check("J2 bad job raises ({0})".format(list(bad)[0]), ok)
vj = jobs.validate_job(["a.mb"], "m.json", "t", repath="new.ma")
check("J3 validate job", vj["job"] == "validate" and vj["repath"] == "new.ma" and vj["clips"] == ["a.mb"])

# ---------------------------------------------------------------- prefs (실제 홈 폴더를 건드리지 않게 경로를 바꿔서)
prefs.PREFS_DIR = os.path.join(work, "prefs")
prefs.PREFS_PATH = os.path.join(prefs.PREFS_DIR, "prefs.json")
p = prefs.load()
check("P1 defaults", p["fps"] == "30" and p["default_start"] == 1 and p["overwrite"] == "skip" and p["copy_wav"] is True)
p["controller"] = "x.ma"
check("P1 save + reload", prefs.save(p) and prefs.load()["controller"] == "x.ma")

shutil.rmtree(work, ignore_errors=True)
print("RESULT", "OK" if all(R) else "FAIL", "{0}/{1}".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
