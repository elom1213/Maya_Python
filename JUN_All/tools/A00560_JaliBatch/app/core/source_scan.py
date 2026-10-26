# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - 변환 결과 폴더 -> 클립 후보 (Maya 비의존, 순수 파이썬 + Framework.jali.lipsync_data)
#
# 입력 폴더 = JUN_JALI VisemeNet Converter 의 출력 폴더: <이름>.txt(22열 · 100fps) + <이름>.visemenet.json + <이름>.wav (+ .phones.json).
#   - 22열 txt 가 읽히는 이름만 클립 후보. 대본 txt(src_en 처럼 글이 든 것)는 "not a VisemeNet output" 으로 건너뛴다.
#   - json 없음 -> WARN (열 이름 검증 · source_wav 를 못 쓴다, 길이는 wav 로), wav 없음 -> ERROR (제외 - 클립엔 소리가 있어야 한다).
#   - **파일 이름에서 프레임을 읽지 않는다** (계획 D7, 사용자 지시 2026-10-23). 이름은 클립 .mb 이름에만 쓴다.
# 22열 txt 가 하나도 없으면 hint 에 "Run VisemeNet Converter first (JUN_JALI)" 를 담는다.

import os
import re

from Framework.jali import lipsync_data, sequence

HINT_NO_OUTPUT = "No VisemeNet output (22-column txt) in this folder - run VisemeNet Converter first (JUN_JALI)."


def _natural_key(name):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", name)]


class ClipSource(object):
    """클립 후보 하나. ok 가 False 면 Run 에 들어가지 않는다 (problems 에 이유)."""

    def __init__(self, name, txt):
        self.name = name
        self.txt = txt
        self.json = ""
        self.wav = ""
        self.rows = 0
        self.model_seconds = 0.0
        self.wav_seconds = None
        self.problems = []          # [(level, message)]  level = "WARN" | "ERROR"
        self._data = None

    @property
    def ok(self):
        return not any(level == "ERROR" for level, _ in self.problems)

    @property
    def seconds(self):
        """타임라인에서 차지하는 길이 - wav 가 있으면 wav(모델 출력은 끝 0.32 s 가 빠진다), 없으면 txt."""
        if self.wav_seconds:
            return max(self.wav_seconds, self.model_seconds)
        return self.model_seconds

    def frames(self, fps):
        """start 부터 차지하는 프레임 수(span) - A00540 sequence.layout 과 같은 식."""
        if self._data is None:
            return 0
        seg = sequence.layout([sequence.Clip(self.txt, self._data, self.wav)], 0, 0, float(fps))[0]
        return seg.span

    def as_job_clip(self, start, out_dir):
        return {"name": self.name, "txt": self.txt, "json": self.json, "wav": self.wav,
                "out_mb": os.path.join(out_dir, self.name + ".mb"), "start": int(start)}


class ScanResult(object):
    def __init__(self, folder):
        self.folder = folder
        self.clips = []             # [ClipSource] 이름 순 (자연 정렬)
        self.skipped = []           # [(파일 이름, 이유)]  - txt 이지만 VisemeNet 출력이 아닌 것
        self.hint = ""

    @property
    def runnable(self):
        return [c for c in self.clips if c.ok]

    def summary(self):
        n_ok = len(self.runnable)
        parts = ["{0} clip(s)".format(len(self.clips))]
        if n_ok != len(self.clips):
            parts.append("{0} excluded".format(len(self.clips) - n_ok))
        if self.skipped:
            parts.append("{0} other txt skipped".format(len(self.skipped)))
        return ", ".join(parts)


def scan(folder):
    """폴더를 훑어 ScanResult. 폴더가 없으면 ValueError."""
    if not folder or not os.path.isdir(folder):
        raise ValueError("Source folder not found: {0}".format(folder))
    result = ScanResult(os.path.normpath(folder))
    names = sorted((f for f in os.listdir(folder) if f.lower().endswith(".txt")), key=_natural_key)
    for fname in names:
        stem = fname[:-4]
        txt = os.path.join(folder, fname)
        clip = ClipSource(stem, txt)
        try:
            data = lipsync_data.load(txt)
        except ValueError as e:
            result.skipped.append((fname, str(e)))
            continue
        clip._data = data
        clip.rows = len(data.rows)
        clip.model_seconds = data.seconds
        js = lipsync_data.json_path_for(txt)
        if os.path.isfile(js):
            clip.json = js
        else:
            clip.problems.append(("WARN", "no .visemenet.json (length from WAV, columns assumed)"))
        clip.wav = lipsync_data.find_wav(txt, data)
        if not clip.wav:
            clip.problems.append(("ERROR", "no WAV found (json source_wav / same name) - excluded"))
        else:
            clip.wav_seconds = lipsync_data.wav_seconds(clip.wav)
            if clip.wav_seconds is None:
                clip.problems.append(("ERROR", "WAV cannot be read (PCM wav only) - excluded"))
            else:
                gap = clip.wav_seconds - clip.model_seconds
                if gap > 0.5 or gap < -0.05:
                    clip.problems.append(("WARN", "WAV / TXT length differ by {0:+.2f} s - check the pair".format(gap)))
        result.clips.append(clip)
    if not result.clips:
        result.hint = HINT_NO_OUTPUT if names else "No txt files in this folder."
    return result
