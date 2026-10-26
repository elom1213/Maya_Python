# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.jali.clip_stamp - 클립 .mb 의 fileInfo 도장 (A00560_JaliBatch 가 쓰고, Validate · A00570 이 읽는다)
#
# 클립 = 대사 하나의 .mb (빈 씬 + JALI 컨트롤러 레퍼런스 + 베이크된 키 + 소리). 어느 컨트롤러 · 어느 설정으로 만들었는지를
# 파일 자체에 남겨야 컨트롤러를 바꾼 날 N 개를 한꺼번에 점검할 수 있다(평가서 §2-3).
#   fileInfo "jun_jali_clip" = json 문자열
#   {source_wav, source_txt, controller, controller_mtime, mapping, fps, start, end, frames, keys, generated_at, tool}
# 주의(M0 실측 2026-10-26): 레퍼런스로 불러온 클립의 fileInfo 는 검수 씬에서 보이지 않는다 - A00570 은 매니페스트에서 읽는다.
# make() / parse() 는 순수 파이썬(standalone UI 도 쓴다), write() / read() 만 maya.cmds.

import json
import os
import time

STAMP_KEY = "jun_jali_clip"


def make(source_wav, source_txt, controller, mapping, fps, start, end, frames, keys, tool):
    """도장 dict. controller_mtime 은 지금 파일의 수정 시각(없으면 0)."""
    try:
        mtime = os.path.getmtime(controller)
    except OSError:
        mtime = 0.0
    return {
        "source_wav": source_wav or "",
        "source_txt": source_txt or "",
        "controller": controller,
        "controller_mtime": mtime,
        "mapping": mapping,
        "fps": float(fps),
        "start": int(start),
        "end": int(end),
        "frames": int(frames),
        "keys": int(keys),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tool": tool,
    }


def parse(text):
    """fileInfo 문자열 -> dict. 없거나 깨졌으면 None. (cmds.fileInfo 는 비 ASCII 를 \\uXXXX 로 돌려주는 일이 있어 둘 다 시도)"""
    if not text:
        return None
    for candidate in (text, text.encode("utf-8", "replace").decode("unicode_escape", "replace")):
        try:
            data = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(data, dict):
            return data
    return None


def write(stamp):
    import maya.cmds as cmds
    cmds.fileInfo(STAMP_KEY, json.dumps(stamp, ensure_ascii=True))


def read():
    """현재 씬(열린 파일)의 도장. 없으면 None."""
    import maya.cmds as cmds
    values = cmds.fileInfo(STAMP_KEY, q=True) or []
    return parse(values[0]) if values else None


def controller_changed(stamp, controller_path=None):
    """도장의 controller_mtime 과 지금 파일의 mtime 이 다르면 True (파일이 없으면 None)."""
    path = controller_path or stamp.get("controller", "")
    try:
        now = os.path.getmtime(path)
    except OSError:
        return None
    return abs(now - float(stamp.get("controller_mtime", 0.0))) > 1.0
