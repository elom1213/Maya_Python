# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - 워커 입력(job dict) 만들기 (Maya 비의존, 순수 파이썬)
#
# UI 설정 -> job json. mayapy 워커(app/maya/worker.py)가 읽는다. 결과 · 취소 플래그 경로는 Framework.core.mayapy_runner.write_job 이 채운다.
#   generate : {"job": "generate", "controller", "mapping", "fps", "default_start", "jali": {"mode", "fixed", "scale"},
#               "viseme_scale", "overwrite": "skip" | "overwrite" | "backup", "copy_wav", "out_dir", "manifest", "tool",
#               "clips": [{"name", "txt", "json", "wav", "out_mb", "start"}]}
#   validate : {"job": "validate", "clips": [<.mb 경로>], "manifest", "repath": "" | <새 컨트롤러 경로>, "tool"}

OVERWRITE_SKIP, OVERWRITE_REPLACE, OVERWRITE_BACKUP = "skip", "overwrite", "backup"
OVERWRITE_LABELS = (("Skip existing", OVERWRITE_SKIP), ("Overwrite", OVERWRITE_REPLACE),
                    ("Overwrite with backup", OVERWRITE_BACKUP))
JALI_DATA, JALI_FIXED = "data", "fixed"

# 마야 시간 단위 이름 <-> fps (keyer._FPS 와 같은 표 + 29.97 · 23.976 · 59.94)
FPS_UNITS = ((15.0, "game"), (24.0, "film"), (25.0, "pal"), (30.0, "ntsc"), (48.0, "show"), (50.0, "palf"), (60.0, "ntscf"),
             (23.976, "23.976fps"), (29.97, "29.97fps"), (59.94, "59.94fps"))
FPS_CHOICES = ("24", "25", "30", "48", "60", "23.976", "29.97", "59.94")


def fps_unit_name(fps):
    """fps 숫자 -> cmds.currentUnit(time=...) 이름. 표에 없으면 '<n>fps' (정수) - 마야가 받는 형식."""
    fps = float(fps)
    for value, name in FPS_UNITS:
        if abs(fps - value) < 1e-6:
            return name
    if abs(fps - round(fps)) < 1e-9:
        return "{0}fps".format(int(round(fps)))
    return "{0:g}fps".format(fps)


def parse_fps(text):
    """콤보 글자 -> fps float. 틀리면 ValueError."""
    try:
        fps = float(str(text).strip().replace("fps", ""))
    except ValueError:
        raise ValueError("fps must be a number: {0!r}".format(text))
    if fps <= 0:
        raise ValueError("fps must be positive")
    return fps


def generate_job(controller, mapping, fps, default_start, jali_mode, jali_fixed, jali_scale, viseme_scale,
                 overwrite, copy_wav, out_dir, manifest_path, tool, clips):
    """clips = [{"name", "txt", "json", "wav", "out_mb", "start"}] (ClipSource.as_job_clip). 검사 뒤 dict."""
    if not controller:
        raise ValueError("Controller .ma / .mb is required")
    if not out_dir:
        raise ValueError("Output folder is required")
    if not clips:
        raise ValueError("No clip checked")
    if overwrite not in (OVERWRITE_SKIP, OVERWRITE_REPLACE, OVERWRITE_BACKUP):
        raise ValueError("Unknown overwrite policy {0!r}".format(overwrite))
    return {
        "job": "generate",
        "controller": controller,
        "mapping": mapping,
        "fps": float(fps),
        "default_start": int(default_start),
        "jali": {"mode": JALI_FIXED if jali_mode == JALI_FIXED else JALI_DATA,
                 "fixed": [float(jali_fixed[0]), float(jali_fixed[1])],
                 "scale": None if jali_scale is None else float(jali_scale)},
        "viseme_scale": None if viseme_scale is None else float(viseme_scale),
        "overwrite": overwrite,
        "copy_wav": bool(copy_wav),
        "out_dir": out_dir,
        "manifest": manifest_path,
        "tool": tool,
        "clips": [dict(c, start=int(c.get("start", default_start))) for c in clips],
    }


def validate_job(clip_paths, manifest_path, tool, repath=""):
    if not clip_paths:
        raise ValueError("No clip to validate")
    return {"job": "validate", "clips": list(clip_paths), "manifest": manifest_path, "repath": repath or "",
            "tool": tool}
