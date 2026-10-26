# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - UI 설정 -> mayapy 워커 job dict (UI/DCC 비의존, 순수 파이썬)  (v01.41)
#
#   probe  : {"job": "probe", "files": [...], "rule": {"set_name", "match", "ignore_namespace"}}
#   export : {"job": "export", "rule": {...}, "bake": bool, "channels": ["translate","rotate","scale"], "joints_only": bool,
#             "euler_filter": bool, "import_references": bool, "report": "<json 경로>",
#             "items": [{"file", "start", "end", "out_fbx"}]}
# 결과 · 취소 플래그 경로는 Framework.core.mayapy_runner.write_job 이 채운다. 결과 형식은 계획서 §3.2 · §3.3.

import os
import time

CHANNELS = ("translate", "rotate", "scale")
CHANNEL_ATTRS = {"translate": ("tx", "ty", "tz"), "rotate": ("rx", "ry", "rz"), "scale": ("sx", "sy", "sz")}

RANGE_TIMELINE, RANGE_ANIM, RANGE_CUSTOM = "timeline", "anim", "custom"
RANGE_LABELS = ((RANGE_TIMELINE, "Timeline (per file)"), (RANGE_ANIM, "Animation range (per file)"),
                (RANGE_CUSTOM, "Custom (all files)"))

STATUS_READY, STATUS_NO_SET, STATUS_COLLISION, STATUS_INVALID = "ready", "no set", "name collision", "invalid name"
STATUS_EXPORTED, STATUS_SKIPPED, STATUS_FAILED = "exported", "skipped", "failed"


def probe_job(files, rule):
    files = [f for f in (files or []) if f]
    if not files:
        raise ValueError("No Maya file to check.")
    if not rule or not rule.get("set_name"):
        raise ValueError("Pick a rule first.")
    return {"job": "probe", "files": list(files), "rule": dict(rule)}


def export_job(rule, rows, bake=True, channels=CHANNELS, joints_only=True, euler_filter=False,
               import_references=True, report_path=""):
    """rows = [{"file", "start", "end", "out_fbx"}]. 검사 뒤 dict."""
    if not rule or not rule.get("set_name"):
        raise ValueError("Pick a rule first.")
    rows = list(rows or [])
    if not rows:
        raise ValueError("No file is ready to export (check files and press Check Sets first).")
    channels = [c for c in (channels or []) if c in CHANNELS]
    if bake and not channels:
        raise ValueError("Pick at least one channel to bake (Translate / Rotate / Scale).")
    items = []
    for row in rows:
        try:
            start, end = int(round(float(row["start"]))), int(round(float(row["end"])))
        except (KeyError, TypeError, ValueError):
            raise ValueError("Start / End of {0} is not a number.".format(os.path.basename(row.get("file", "?"))))
        if start > end:
            raise ValueError("Start is after End for {0} ({1} > {2}).".format(os.path.basename(row["file"]), start, end))
        if not row.get("out_fbx"):
            raise ValueError("Output name is empty for {0}.".format(os.path.basename(row["file"])))
        items.append({"file": row["file"], "start": start, "end": end, "out_fbx": row["out_fbx"]})
    return {"job": "export", "rule": dict(rule), "bake": bool(bake), "channels": channels,
            "joints_only": bool(joints_only), "euler_filter": bool(euler_filter),
            "import_references": bool(import_references), "report": report_path or "", "items": items}


def report_path(folder):
    """<folder>/_bake_export_report_<YYYYMMDD_HHMMSS>.json"""
    return os.path.join(folder, "_bake_export_report_{0}.json".format(time.strftime("%Y%m%d_%H%M%S")))


def summarize(result):
    """export 결과 -> 한 줄 (UI 로그)."""
    if not result:
        return "no result"
    return "{0} exported, {1} skipped, {2} failed{3}".format(
        result.get("exported", 0), result.get("skipped", 0), result.get("failed", 0),
        " (cancelled)" if result.get("cancelled") else "")
