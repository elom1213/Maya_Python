# -*- coding: utf-8 -*-
# A00210_FileManager - Maya > Export 워커 시험 (mayapy). 합성 씬을 만들고 **실제 워커 프로세스**(mayapy -u maya_worker.py job.json)로
# probe / export(bake) / export only / cancel 을 돌린 뒤, 이 프로세스(mayapy)에서 FBX 를 다시 임포트해 확인한다.
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" test_export_worker.py
import os
import sys
import json
import time
import hashlib
import tempfile
import subprocess

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
import maya.standalone  # noqa: E402
maya.standalone.initialize(name="python")
import maya.cmds as cmds  # noqa: E402
cmds.loadPlugin("fbxmaya", quiet=True)

from Framework.core import mayapy_runner  # noqa: E402
from tools.A00210_FileManager.app.maya.core import mayapy_runner as tool_runner  # noqa: E402
from tools.A00210_FileManager.app.maya.core import export_jobs  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


MAYAPY = sys.executable
WORK = tempfile.mkdtemp(prefix="a00210_export_")
OUT = os.path.join(WORK, "out")
FRAMES = 120
RULE = {"set_name": "Bake", "match": "exact", "ignore_namespace": True}


def sha(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def build_rig(frames=FRAMES, root_under_group=True, nested_set=True):
    cmds.file(new=True, force=True)
    cmds.currentUnit(time="ntsc")
    cmds.select(clear=True)
    root = cmds.joint(n="root", p=(0, 0, 0))
    cmds.setKeyframe(root, at="ty", t=0, v=0); cmds.setKeyframe(root, at="ty", t=frames, v=10)
    chain = [root]
    for i in range(1, 8):
        chain.append(cmds.joint(n="spine_%02d" % i, p=(0, i * 2.0, 0)))
    if root_under_group:
        grp = cmds.group(em=True, n="rig_grp")
        cmds.setKeyframe(grp, at="tx", t=0, v=0); cmds.setKeyframe(grp, at="tx", t=frames, v=50)
        cmds.setKeyframe(grp, at="ry", t=0, v=0); cmds.setKeyframe(grp, at="ry", t=frames, v=90)
        cmds.parent(root, grp)
    for i, j in enumerate(chain[1:4]):
        loc = cmds.spaceLocator(n="drv_%02d" % i)[0]
        cmds.setKeyframe(loc, at="tx", t=0, v=0); cmds.setKeyframe(loc, at="tx", t=frames, v=5 + i)
        cmds.setKeyframe(loc, at="rz", t=0, v=0); cmds.setKeyframe(loc, at="rz", t=frames, v=45)
        cmds.parentConstraint(loc, j, mo=True)
    cube = cmds.polyCube(n="skin_mesh")[0]
    cmds.parent(cube, chain[2])
    jl = cmds.spaceLocator(n="joint_loc")[0]
    cmds.parent(jl, chain[3])
    bake_set = cmds.sets(root, n="Bake")
    if nested_set:
        cmds.sets(bake_set, n="Sets")
    cmds.playbackOptions(min=2, max=frames, ast=0, aet=frames + 50)
    return chain


def save(path, ascii_=False):
    cmds.file(rename=path)
    cmds.file(save=True, type="mayaAscii" if ascii_ else "mayaBinary", force=True)
    return path


def world_mats(nodes, frames):
    out = {}
    for f in frames:
        cmds.currentTime(f)
        out[f] = {n.split("|")[-1].split(":")[-1]: cmds.xform(n, q=True, ws=True, m=True) for n in nodes}
    return out


def worst_diff(a, b):
    worst = 0.0
    for f in a:
        for n in a[f]:
            if n not in b[f]:
                return 1e9
            worst = max(worst, max(abs(x - y) for x, y in zip(a[f][n], b[f][n])))
    return worst


def run_worker(job, cancel_after_first=False):
    job_dir = mayapy_runner.new_job_dir("a00210_test")
    job_path, result_path, cancel_flag = mayapy_runner.write_job(job_dir, job)
    cmd = mayapy_runner.command(MAYAPY, job_path, tool_runner.worker_path())
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    msgs, logs = [], []
    seen_first = False
    for line in proc.stdout:
        msg = mayapy_runner.parse_line(line)
        if msg is None:
            continue
        msgs.append(msg)
        if msg.get("type") == "log":
            logs.append(msg["text"])
            if cancel_after_first and not seen_first and "[OK]" in msg["text"]:
                seen_first = True
                mayapy_runner.request_cancel(cancel_flag)
    proc.wait()
    result = None
    if any(m.get("type") == "result" for m in msgs):
        result = mayapy_runner.read_result(result_path)
    errors = [m["text"] for m in msgs if m.get("type") == "error"]
    return proc.returncode, result, logs, errors, msgs


# ---------------------------------------------------------------- scenes
os.makedirs(OUT)
chain = build_rig()
rig_mb = save(os.path.join(WORK, "anim_01.mb"))
ref_world = world_mats(chain, range(2, FRAMES + 1, 6))

cmds.file(new=True, force=True); cmds.currentUnit(time="ntsc")
cmds.file(rig_mb, reference=True, namespace="CHN", prompt=False)
cmds.playbackOptions(min=0, max=FRAMES, ast=0, aet=FRAMES)
ref_scene = save(os.path.join(WORK, "anim_02.mb"))

cmds.file(new=True, force=True); cmds.currentUnit(time="film")
cmds.polyCube(n="lonely"); cmds.sets("lonely", n="Other")
cmds.playbackOptions(min=1, max=48)
noset_ma = save(os.path.join(WORK, "anim_03.ma"), ascii_=True)

build_rig(root_under_group=False, nested_set=False)
direct_ma = save(os.path.join(WORK, "anim_04.ma"), ascii_=True)

hashes = {p: sha(p) for p in (rig_mb, ref_scene, noset_ma, direct_ma)}

# ---------------------------------------------------------------- probe
t0 = time.time()
code, result, logs, errors, msgs = run_worker(export_jobs.probe_job([rig_mb, ref_scene, noset_ma, direct_ma, os.path.join(WORK, "missing.mb")], RULE))
check("probe exit 0, no error", code == 0 and not errors, (code, errors[:1]))
check("probe progress messages", any(m.get("type") == "progress" for m in msgs))
files = {os.path.basename(f["file"]): f for f in result["files"]} if result else {}
check("probe 5 entries", len(files) == 5)
f1 = files.get("anim_01.mb", {})
check("anim_01 : set Bake nested in Sets found, members 1, nodes>=8", [s["name"] for s in f1.get("sets", [])] == ["Bake"]
      and f1["sets"][0]["members"] == 1 and f1["sets"][0]["nodes"] >= 8, f1.get("sets"))
check("anim_01 : playback 2-120, anim 0-170, fps 30, version 2024", f1.get("playback") == [2.0, 120.0] and f1.get("anim") == [0.0, 170.0]
      and f1.get("fps") == 30.0 and f1.get("version") == "2024", (f1.get("playback"), f1.get("anim"), f1.get("fps"), f1.get("version")))
f2 = files.get("anim_02.mb", {})
check("anim_02 : set inside reference seen as CHN:Bake, references loaded 1", [s["name"] for s in f2.get("sets", [])] == ["CHN:Bake"]
      and f2.get("references", {}).get("loaded") == 1, f2.get("sets"))
f3 = files.get("anim_03.ma", {})
check("anim_03 : no set, fps 24, playback 1-48", f3.get("ok") and f3.get("sets") == [] and f3.get("fps") == 24.0 and f3.get("playback") == [1.0, 48.0])
check("missing file : ok False + error", files.get("missing.mb", {}).get("ok") is False and "not found" in files.get("missing.mb", {}).get("error", ""))
check("probe log line format", any("anim_01.mb : Bake (1 -> " in l and "2 - 120 @ 30 fps | Maya 2024" in l for l in logs), [l for l in logs if "anim_01" in l][:1])
print("  probe took %.1fs" % (time.time() - t0))

# ---------------------------------------------------------------- export (bake)
rows = [{"file": rig_mb, "start": 2, "end": FRAMES, "out_fbx": os.path.join(OUT, "bake_anim_01.fbx")},
        {"file": ref_scene, "start": 0, "end": FRAMES, "out_fbx": os.path.join(OUT, "bake_anim_02.fbx")},
        {"file": noset_ma, "start": 1, "end": 48, "out_fbx": os.path.join(OUT, "bake_anim_03.fbx")},
        {"file": os.path.join(WORK, "missing.mb"), "start": 0, "end": 10, "out_fbx": os.path.join(OUT, "bake_missing.fbx")}]
report = export_jobs.report_path(OUT)
job = export_jobs.export_job(RULE, rows, bake=True, channels=["translate", "rotate", "scale"], joints_only=True,
                             euler_filter=False, import_references=True, report_path=report)
t0 = time.time()
code, result, logs, errors, msgs = run_worker(job)
check("export exit 0, no protocol error", code == 0 and not errors, (code, errors[:1]))
check("export counts: 2 exported, 1 skipped, 1 failed", result and (result["exported"], result["skipped"], result["failed"]) == (2, 1, 1),
      result and (result["exported"], result["skipped"], result["failed"]))
res = {os.path.basename(r["file"]): r for r in result["results"]} if result else {}
check("anim_01 exported, root moved, pruned>0", res.get("anim_01.mb", {}).get("status") == "exported" and res["anim_01.mb"]["roots_moved"] == 1
      and res["anim_01.mb"]["pruned"] >= 2 and res["anim_01.mb"]["nodes"] == 8, res.get("anim_01.mb"))
check("anim_02 exported with 1 imported reference + namespaces removed", res.get("anim_02.mb", {}).get("status") == "exported"
      and res["anim_02.mb"]["imported_references"] == 1 and res["anim_02.mb"]["namespaces_removed"] >= 1 and res["anim_02.mb"]["sets"] == ["Bake"])
check("anim_03 skipped (no set)", res.get("anim_03.ma", {}).get("status") == "skipped")
check("missing failed", res.get("missing.mb", {}).get("status") == "failed")
check("report json written", os.path.isfile(report) and json.load(open(report, encoding="utf-8"))["result"]["exported"] == 2)
check("no __part left", not [f for f in os.listdir(OUT) if "__part" in f])
check("seconds per step logged", set(res["anim_01.mb"]["seconds"]) >= {"open", "import", "bake", "export"})
print("  export took %.1fs" % (time.time() - t0))

# verify FBX 1 - names, hierarchy, keys, world motion
cmds.file(new=True, force=True); cmds.currentUnit(time="ntsc")
cmds.file(os.path.join(OUT, "bake_anim_01.fbx"), i=True, type="FBX", ignoreVersion=True)
joints = cmds.ls(type="joint", long=True)
check("fbx1 : 8 joints only (mesh, locator, constraints pruned)", len(joints) == 8 and not cmds.ls(type="mesh") and not cmds.ls(type="locator")
      and not cmds.ls(type="constraint"), (len(joints), cmds.ls(type="mesh"), cmds.ls(type="locator")))
check("fbx1 : root at top level (no rig_grp)", "|root" in joints and not cmds.objExists("rig_grp"))
fbx_world = world_mats(joints, range(2, FRAMES + 1, 6))
check("fbx1 : world motion == original (incl. animated group, constraints)", worst_diff(ref_world, fbx_world) < 1e-3, worst_diff(ref_world, fbx_world))
curves = cmds.ls(type="animCurve")
times_ = sorted(set(t for c in curves for t in cmds.keyframe(c, q=True, tc=True) or []))
check("fbx1 : keys 2..120 on every frame", times_ and times_[0] == 2.0 and times_[-1] == float(FRAMES) and len(times_) == FRAMES - 1, (times_[:2], times_[-1], len(times_)))
check("fbx1 : constrained spine_01 has keys", bool(cmds.keyframe("spine_01", q=True, kc=True)))

# verify FBX 2 - namespace gone
cmds.file(new=True, force=True)
cmds.file(os.path.join(OUT, "bake_anim_02.fbx"), i=True, type="FBX", ignoreVersion=True)
names = cmds.ls(type="joint")
check("fbx2 : joint names without namespace", names and all(":" not in n for n in names) and "root" in names, names[:3])

check("originals untouched (hash)", all(sha(p) == h for p, h in hashes.items()))

# ---------------------------------------------------------------- export only
rows = [{"file": direct_ma, "start": 0, "end": FRAMES, "out_fbx": os.path.join(OUT, "only_anim_04.fbx")},
        {"file": rig_mb, "start": 2, "end": FRAMES, "out_fbx": os.path.join(OUT, "only_anim_01.fbx")}]
job = export_jobs.export_job(RULE, rows, bake=False, channels=[], joints_only=True, import_references=True, report_path="")
code, result, logs, errors, msgs = run_worker(job)
check("export only exit 0", code == 0 and not errors and result["exported"] == 2, (code, errors[:1], result and [(os.path.basename(r["file"]), r["status"], r.get("error")) for r in result["results"]]))
check("export only warns about animated parent for anim_01", any("[WARN]" in l and "former parent is animated" in l for l in logs))
cmds.file(new=True, force=True); cmds.currentUnit(time="ntsc")
cmds.file(os.path.join(OUT, "only_anim_04.fbx"), i=True, type="FBX", ignoreVersion=True)
check("export only : root keys kept as-is (2 keys on ty), constrained joint has none",
      cmds.keyframe("root.ty", q=True, kc=True) == 2 and not cmds.keyframe("spine_01", q=True, kc=True))
check("export only : root stays top-level", cmds.listRelatives("root", p=True) is None)

# ---------------------------------------------------------------- cancel between files
rows = [{"file": rig_mb, "start": 2, "end": 30, "out_fbx": os.path.join(OUT, "c1.fbx")},
        {"file": rig_mb, "start": 2, "end": 30, "out_fbx": os.path.join(OUT, "c2.fbx")},
        {"file": rig_mb, "start": 2, "end": 30, "out_fbx": os.path.join(OUT, "c3.fbx")}]
job = export_jobs.export_job(RULE, rows, bake=True, report_path="")
code, result, logs, errors, msgs = run_worker(job, cancel_after_first=True)
check("cancel : stopped at a file boundary", code == 0 and result and result["cancelled"] and 1 <= result["exported"] < 3, result and result["exported"])

# ---------------------------------------------------------------- unknown job
code, result, logs, errors, msgs = run_worker({"job": "nope"})
check("unknown job -> error, exit 2", code == 2 and errors)

print("\nRESULT %d/%d   (work dir %s)" % (sum(R), len(R), WORK))
maya.standalone.uninitialize()
os._exit(0 if all(R) else 1)
