# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00540_JaliLipSync - VisemeNet 결과 읽기 (Maya 비의존)
#
# 입력은 JUN_JALI 의 VisemeNet Converter(또는 README 예시)가 쓴 파일이다.
#   <이름>.txt            : 공백 구분 22열, 한 줄 = 10ms (100fps). 헤더 없음
#   <이름>.visemenet.json : 열 이름 · fps · 원본 wav 경로 (있으면 검증 + wav 자동 찾기에 쓴다)
# 줄 i 는 음성 i*10ms 시점이다. 모델 구조상 **끝 0.32초가 빠진다**(시작은 맞다) - JUN_JALI docs/0050.

import json
import os
import wave


MODEL_COLUMNS = ["Jaw", "Lip", "Ah", "Aa", "Eh", "Ee", "Ih", "Oh", "Uh", "U", "Eu", "Schwa", "R", "S",
                 "ShChZh", "Th", "JY", "LNTD", "GK", "MBP", "FV", "W"]
MODEL_FPS = 100.0
JSON_SUFFIX = ".visemenet.json"


class LipsyncData(object):
    def __init__(self, txt_path, rows, columns, fps, meta=None):
        self.txt_path = txt_path
        self.rows = rows
        self.columns = columns
        self.fps = fps
        self.meta = meta or {}

    @property
    def seconds(self):
        return len(self.rows) / self.fps

    def column_index(self):
        return {name: i for i, name in enumerate(self.columns)}


def json_path_for(txt_path):
    return os.path.splitext(txt_path)[0] + JSON_SUFFIX


def load(txt_path):
    """txt (+ json) 를 읽어 LipsyncData. 형식이 틀리면 ValueError (영어 메시지)."""
    if not txt_path or not os.path.isfile(txt_path):
        raise ValueError("TXT file not found: {0}".format(txt_path))

    rows = []
    with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != len(MODEL_COLUMNS):
                raise ValueError("Line {0} has {1} values - expected {2} (is this a VisemeNet output?)"
                                 .format(n, len(parts), len(MODEL_COLUMNS)))
            try:
                rows.append([float(v) for v in parts])
            except ValueError:
                raise ValueError("Line {0} is not numeric".format(n))
    if not rows:
        raise ValueError("TXT file is empty: {0}".format(txt_path))

    columns, fps, meta = list(MODEL_COLUMNS), MODEL_FPS, {}
    js = json_path_for(txt_path)
    if os.path.isfile(js):
        try:
            with open(js, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError) as e:
            raise ValueError("Cannot read {0}: {1}".format(os.path.basename(js), e))
        if meta.get("columns") and list(meta["columns"]) != MODEL_COLUMNS:
            raise ValueError("Columns in {0} do not match the VisemeNet layout".format(os.path.basename(js)))
        if meta.get("fps") and float(meta["fps"]) != MODEL_FPS:
            raise ValueError("fps {0} in {1} - expected {2:g}".format(meta["fps"], os.path.basename(js), MODEL_FPS))
        if meta.get("rows") and int(meta["rows"]) != len(rows):
            raise ValueError("{0} says {1} rows but the TXT has {2}".format(
                os.path.basename(js), meta["rows"], len(rows)))
    return LipsyncData(txt_path, rows, columns, fps, meta)


def find_wav(txt_path, data=None):
    """txt 에 맞는 wav 경로. json 의 source_wav -> txt 폴더의 같은 이름 -> 상위 폴더의 같은 이름. 없으면 ""."""
    if data is not None and data.meta.get("source_wav"):
        path = os.path.normpath(data.meta["source_wav"])
        if os.path.isfile(path):
            return path
    stem = os.path.splitext(os.path.basename(txt_path))[0]
    folder = os.path.dirname(os.path.abspath(txt_path))
    for candidate in (os.path.join(folder, stem + ".wav"),
                      os.path.join(os.path.dirname(folder), stem + ".wav")):
        if os.path.isfile(candidate):
            return candidate
    return ""


def wav_seconds(path):
    """wav 길이(초). 읽을 수 없으면 None (표준 wave 모듈 - PCM 만)."""
    try:
        with wave.open(path, "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except (OSError, EOFError, wave.Error):
        return None
