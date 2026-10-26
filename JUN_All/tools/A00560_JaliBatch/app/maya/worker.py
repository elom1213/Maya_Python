# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - mayapy 워커 (mayapy.exe 가 실행한다. UI 프로세스에서 import 하지 않는다)
#
#   mayapy -u worker.py <job.json>        (job 형식은 app/core/jobs.py, 프로토콜은 Framework/core/mayapy_runner.py)
#
# generate : 클립마다 (계획 §3, M0-6 실측 2026-10-26)
#   1 file new · currentUnit(time=fps)      - fps 를 먼저 (keyer 는 씬 fps 로 샘플한다)
#   2 컨트롤러 레퍼런스 ns "JALI"           - 모든 클립 동일 (검수 씬 연결 CLIP:JALI:ARKIT_OUT.* 이 늘 같아야 교체 뒤 살아 있다)
#   3 txt 읽기 · layout(start) · 재생 범위   - 클립 길이는 wav 길이 (모델 출력은 끝 0.32 s 가 빠진다)
#   4 keyer.apply_sequence -> DUMMY_IN_*    - 23 어트리뷰트
#   5 bake(copy) -> 컨트롤러 · DUMMY_IN 커브 삭제 · 커브 이름 JALI_<ctl>_<attr>
#   6 wav 를 클립 옆에 복사 -> sound 노드 (offset = start)
#   7 fileInfo 도장 · <name>.mb 저장 (Skip / Overwrite / backup)
#   8 진행률 · 매니페스트 갱신 · 취소 플래그 확인. 실패 클립은 failed 로 적고 **다음 클립 계속** (Q7)
# validate : 클립마다 열어(읽기만) 컨트롤러 경로 · 로드 · failedEdits · 베이크 채널 · 키 · DUMMY_IN 잔여 · 도장 ↔ 컨트롤러 mtime.
#            repath 가 있으면 file -loadReference 새 경로 -> 저장 (이때만 쓴다).
#
# sys.path: dev 트리(JUN_All) 또는 릴리즈본(툴 폴더 안 Framework) 둘 다 - launch.py 와 같은 규칙 (docs/Release_Layout.md).
# 끝낼 때 모든 경로에서 maya.standalone.uninitialize() 뒤 os._exit (메모리 maya-reference-import-traps).

import os
import sys
import json
import time
import shutil
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))                  # .../A00560_JaliBatch/app/maya
TOOL_ROOT = os.path.dirname(os.path.dirname(HERE))                  # .../A00560_JaliBatch
ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))                  # JUN_All (dev) 또는 저장소 루트 (릴리즈)
for _path in ((TOOL_ROOT, ROOT) if os.path.isdir(os.path.join(TOOL_ROOT, "Framework")) else (ROOT,)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from Framework.core.mayapy_runner import emit, emit_log as log, emit_progress as progress   # noqa: E402

NAMESPACE = "JALI"
SOUND_NODE = "jali_lipsync_audio"


def _shutdown():
    try:
        import maya.standalone
        maya.standalone.uninitialize()
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------
def _backup_existing(out_mb):
    """backup/<name>_NN.mb 로 복사 (A00210 · A00220 과 같은 자리). Returns 백업 경로."""
    folder = os.path.join(os.path.dirname(out_mb), "backup")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stem = os.path.splitext(os.path.basename(out_mb))[0]
    n = 1
    while True:
        candidate = os.path.join(folder, "{0}_{1:02d}.mb".format(stem, n))
        if not os.path.exists(candidate):
            break
        n += 1
    shutil.copy2(out_mb, candidate)
    return candidate


def _manifest_update(job, name, **fields):
    """매니페스트에 클립 상태를 적는다 (UI 와 같은 모듈을 쓰지 않고 json 직접 - 워커는 tools 패키지를 import 하지 않는다)."""
    path = job.get("manifest")
    if not path:
        return
    data = {"format": 1, "tool": "A00560_JaliBatch", "version": job.get("tool", ""), "settings": {}, "clips": {}}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict) and isinstance(loaded.get("clips"), dict):
                data = loaded
        except (OSError, ValueError):
            pass
    entry = data["clips"].setdefault(name, {"name": name})
    entry.update(fields)
    data["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)


def generate_one(cmds, job, clip, mapping):
    """클립 하나를 만든다. Returns dict(상태 · 수치). 예외는 호출자가 잡는다."""
    from Framework.jali import keyer, lipsync_data, sequence, bake, clip_stamp

    t0 = time.time()
    name, txt, wav, out_mb, start = clip["name"], clip["txt"], clip.get("wav", ""), clip["out_mb"], int(clip["start"])
    exists = os.path.isfile(out_mb)
    policy = job.get("overwrite", "skip")
    if exists and policy == "skip":
        return {"status": "skipped", "reason": "exists", "out_mb": out_mb}
    out_dir = os.path.dirname(out_mb)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    fps = float(job["fps"])
    cmds.file(new=True, force=True)
    cmds.currentUnit(time=_unit_name(fps))
    ref = cmds.file(job["controller"], reference=True, namespace=NAMESPACE, prompt=False)
    rn = cmds.referenceQuery(ref, referenceNode=True, topReference=True)
    ns = NAMESPACE + ":"

    data = lipsync_data.load(txt)
    clip_obj = sequence.Clip(txt, data, wav)
    seg = sequence.layout([clip_obj], start, 0, keyer.scene_fps())[0]
    cmds.playbackOptions(min=seg.start, max=seg.end, ast=seg.start, aet=seg.end)

    jali = job.get("jali") or {}
    fixed = tuple(jali.get("fixed") or []) if jali.get("mode") == "fixed" else None
    res = keyer.apply_sequence([seg], mapping, ns, viseme_scale=job.get("viseme_scale"),
                               jali_scale=jali.get("scale"), jali_fixed=fixed)
    baked = bake.bake_ctl_keys(nodes=bake.controllers(ns), mode="copy", namespace=ns)
    removed = bake.cleanup_dummy_in(ns)
    renamed = bake.rename_curves(baked)

    sound = ""
    wav_used = wav
    if wav:
        if job.get("copy_wav", True):
            wav_used = os.path.join(os.path.dirname(out_mb), os.path.basename(wav))
            if os.path.normcase(os.path.abspath(wav_used)) != os.path.normcase(os.path.abspath(wav)):
                shutil.copy2(wav, wav_used)
        sound = cmds.sound(file=wav_used, offset=seg.start, name=SOUND_NODE)

    stamp = clip_stamp.make(wav_used, txt, job["controller"], job["mapping"], fps, seg.start, seg.end,
                            seg.key_frames, res["keys"], job.get("tool", "A00560_JaliBatch"))
    clip_stamp.write(stamp)

    backup = ""
    if exists and policy == "backup":
        backup = _backup_existing(out_mb)
    cmds.file(rename=out_mb)
    cmds.file(save=True, type="mayaBinary", force=True)
    return {"status": "generated", "out_mb": out_mb, "start": seg.start, "end": seg.end, "frames": seg.key_frames,
            "span": seg.span, "keys": res["keys"], "baked": len(baked), "dummy_curves_removed": removed,
            "renamed": len(renamed), "sound": sound, "wav": wav_used, "backup": backup, "reference_node": rn,
            "seconds": round(time.time() - t0, 2), "stamp": stamp}


def _unit_name(fps):
    table = ((15.0, "game"), (24.0, "film"), (25.0, "pal"), (30.0, "ntsc"), (48.0, "show"), (50.0, "palf"),
             (60.0, "ntscf"), (23.976, "23.976fps"), (29.97, "29.97fps"), (59.94, "59.94fps"))
    for value, unit in table:
        if abs(fps - value) < 1e-6:
            return unit
    return "{0}fps".format(int(round(fps))) if abs(fps - round(fps)) < 1e-9 else "{0:g}fps".format(fps)


def run_generate(cmds, job, should_cancel):
    from Framework.jali import mapping as mapping_mod
    mapping = mapping_mod.load_mapping(job["mapping"])
    clips = job.get("clips", [])
    total = len(clips)
    summary = {"generated": 0, "skipped": 0, "failed": 0, "cancelled": False, "clips": []}
    log("generate: {0} clip(s) -> {1} (fps {2:g}, mapping {3}, controller {4})".format(
        total, job.get("out_dir", ""), float(job["fps"]), job["mapping"], os.path.basename(job["controller"])))
    for i, clip in enumerate(clips):
        if should_cancel():
            summary["cancelled"] = True
            log("[WARN] Cancelled before {0}".format(clip["name"]))
            break
        progress(i, total, clip["name"])
        try:
            res = generate_one(cmds, job, clip, mapping)
        except Exception as exc:  # noqa: BLE001 - 클립은 서로 독립: 실패를 적고 다음으로
            text = str(exc).strip() or exc.__class__.__name__
            res = {"status": "failed", "error": text, "out_mb": clip["out_mb"], "traceback": traceback.format_exc()}
            log("[ERROR] {0}: {1}".format(clip["name"], text))
        res["name"] = clip["name"]
        summary["clips"].append(res)
        status = res["status"]
        summary[status if status in ("generated", "skipped", "failed") else "failed"] += 1
        if status == "generated":
            log("[OK] {0}: frames {1}-{2}, {3} keys on {4} channel(s), {5:.1f}s{6}".format(
                clip["name"], res["start"], res["end"], res["keys"], res["baked"], res["seconds"],
                " (backup {0})".format(os.path.basename(res["backup"])) if res.get("backup") else ""))
            _manifest_update(job, clip["name"], txt=clip["txt"], wav=res.get("wav", ""), mb=res["out_mb"],
                             start=res["start"], end=res["end"], frames=res["frames"], fps=float(job["fps"]),
                             keys=res["keys"], status="generated", generated_at=res["stamp"]["generated_at"],
                             controller=job["controller"], controller_mtime=res["stamp"]["controller_mtime"],
                             mapping=job["mapping"], error="")
        elif status == "skipped":
            log("[INFO] {0}: skipped ({1})".format(clip["name"], res.get("reason", "")))
            _manifest_update(job, clip["name"], start=int(clip["start"]))
        else:
            _manifest_update(job, clip["name"], txt=clip["txt"], mb=clip["out_mb"], start=int(clip["start"]),
                             status="failed", error=res.get("error", ""))
    progress(total, total, "done")
    return summary


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------
def validate_one(cmds, path, repath):
    from Framework.jali import bake, clip_stamp
    row = {"mb": path, "name": os.path.splitext(os.path.basename(path))[0], "problems": []}
    if not os.path.isfile(path):
        row["problems"].append("file not found")
        row["status"] = "missing"
        return row
    cmds.file(path, open=True, force=True, prompt=False, loadReferenceDepth="all")
    refs = [r for r in (cmds.ls(type="reference") or []) if not r.endswith("sharedReferenceNode")]
    jali = [r for r in refs if cmds.referenceQuery(r, namespace=True, shortName=True) == NAMESPACE] if refs else []
    if not jali:
        row["problems"].append("no reference with namespace JALI")
        row["controller"] = ""
        row["loaded"] = False
    else:
        rn = jali[0]
        row["reference_node"] = rn
        row["controller"] = cmds.referenceQuery(rn, filename=True, withoutCopyNumber=True)
        row["loaded"] = bool(cmds.referenceQuery(rn, isLoaded=True))
        if not row["loaded"]:
            row["problems"].append("controller reference not loaded")
        if not os.path.isfile(row["controller"]):
            row["problems"].append("controller file missing on disk")
        if repath and os.path.normcase(os.path.abspath(repath)) != os.path.normcase(os.path.abspath(row["controller"])):
            cmds.file(repath, loadReference=rn, prompt=False)
            row["controller"] = cmds.referenceQuery(rn, filename=True, withoutCopyNumber=True)
            row["repathed"] = True
        failed = cmds.referenceQuery(rn, editStrings=True, failedEdits=True, successfulEdits=False) or []
        row["failed_edits"] = len(failed)
        row["failed_edit_samples"] = [e[:160] for e in failed[:5]]
        if failed:
            row["problems"].append("{0} failed reference edit(s)".format(len(failed)))
    ns = NAMESPACE + ":"
    channels = bake.baked_channels(ns)
    row["baked_channels"] = len(channels)
    row["keys"] = sum(k for _, _, k in channels)
    if not channels:
        row["problems"].append("no baked controller channel")
    row["dummy_in_curves"] = bake.dummy_in_curve_count(ns)
    if row["dummy_in_curves"]:
        row["problems"].append("{0} animCurve(s) left on DUMMY_IN".format(row["dummy_in_curves"]))
    row["sound"] = bool(cmds.objExists(SOUND_NODE))
    if row["sound"]:
        snd_file = cmds.getAttr(SOUND_NODE + ".filename")
        if not snd_file or not os.path.isfile(snd_file):
            row["problems"].append("sound file missing: {0}".format(snd_file))
    stamp = clip_stamp.read()
    row["stamp"] = stamp
    if stamp:
        changed = clip_stamp.controller_changed(stamp, row.get("controller") or None)
        row["controller_changed"] = changed
        if changed:
            row["problems"].append("controller file changed since the clip was made")
        row["start"], row["end"], row["fps"] = stamp.get("start"), stamp.get("end"), stamp.get("fps")
    else:
        row["problems"].append("no jun_jali_clip stamp (not made by A00560?)")
    row["unit"] = cmds.currentUnit(q=True, time=True)
    if row.get("repathed"):
        cmds.file(save=True, type="mayaBinary", force=True)
        row["saved"] = True
    row["status"] = "ok" if not row["problems"] else "warn"
    return row


def run_validate(cmds, job, should_cancel):
    clips = job.get("clips", [])
    total = len(clips)
    repath = job.get("repath") or ""
    out = {"rows": [], "cancelled": False, "ok": 0, "warn": 0, "failed": 0}
    for i, path in enumerate(clips):
        if should_cancel():
            out["cancelled"] = True
            break
        progress(i, total, os.path.basename(path))
        try:
            row = validate_one(cmds, path, repath)
        except Exception as exc:  # noqa: BLE001
            row = {"mb": path, "name": os.path.splitext(os.path.basename(path))[0], "status": "failed",
                   "problems": [str(exc).strip() or exc.__class__.__name__], "traceback": traceback.format_exc()}
            log("[ERROR] {0}: {1}".format(row["name"], row["problems"][0]))
        out["rows"].append(row)
        out[row["status"] if row["status"] in ("ok", "warn", "failed") else "failed"] += 1
        tag = {"ok": "[OK]", "warn": "[WARN]"}.get(row["status"], "[ERROR]")
        log("{0} {1}: {2}".format(tag, row["name"], "; ".join(row["problems"]) or "ok"))
    progress(total, total, "done")
    return out


# ---------------------------------------------------------------------------
def main(argv):
    if len(argv) < 2:
        emit(type="error", text="usage: worker.py <job.json>")
        return 2
    with open(argv[1], "r", encoding="utf-8") as fh:
        job = json.load(fh)
    result_path = job.get("result", "")
    cancel_flag = job.get("cancel_flag", "")

    log("mayapy {0} starting Maya...".format(sys.version.split()[0]))
    progress(0, 1, "Starting Maya (mayapy)...")
    try:
        import maya.standalone
        maya.standalone.initialize(name="python")
        import maya.cmds as cmds
    except Exception as exc:  # noqa: BLE001
        emit(type="error", text="Could not start Maya in mayapy : {0}".format(exc))
        return 3
    log("Maya ready.")

    def should_cancel():
        return bool(cancel_flag) and os.path.exists(cancel_flag)

    try:
        kind = job.get("job")
        if kind == "generate":
            result = run_generate(cmds, job, should_cancel)
        elif kind == "validate":
            result = run_validate(cmds, job, should_cancel)
        else:
            emit(type="error", text="unknown job : {0!r}".format(kind))
            _shutdown()
            return 2
    except Exception:  # noqa: BLE001
        emit(type="error", text=traceback.format_exc())
        _shutdown()
        return 1

    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1, default=str)
    emit(type="result", path=result_path)
    _shutdown()
    return 0


if __name__ == "__main__":
    code = main(sys.argv)
    sys.stdout.flush()
    os._exit(code)      # mayapy 가 종료 때 플러그인 정리로 머무는 일이 있어 바로 끝낸다
