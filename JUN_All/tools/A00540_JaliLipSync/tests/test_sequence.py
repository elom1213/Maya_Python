# -*- coding: utf-8 -*-
# A00540_JaliLipSync - 클립 이어 붙이기 시험 (T-S, Maya 비의존 - mayapy 또는 python)
#   mayapy test_sequence.py
import os
import sys
import tempfile
import wave

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00540_JaliLipSync.app.core import lipsync_data, sequence   # noqa: E402

R = []


def check(name, cond):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


work = tempfile.mkdtemp()
idx = {c: i for i, c in enumerate(lipsync_data.MODEL_COLUMNS)}


def write_txt(name, n_rows, aa):
    row = [0.0] * 22
    row[idx["Aa"]] = aa
    path = os.path.join(work, name + ".txt")
    with open(path, "w") as f:
        for _ in range(n_rows):
            f.write(" ".join("%g" % v for v in row) + "\n")
    return path


def write_wav(name, seconds, rate=44100, nch=1, width=2, value=1000):
    path = os.path.join(work, name + ".wav")
    n = int(round(seconds * rate))
    sample = value.to_bytes(width, "little", signed=True) * nch
    with wave.open(path, "wb") as w:
        w.setnchannels(nch)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(sample * n)
    return path


# 클립 A: txt 1.00 s + wav 1.32 s (모델 출력은 끝 0.32 s 가 빠진다) / B: txt 0.50 s, wav 없음 / C: txt 2.00 s + wav 2.30 s
txt_a, wav_a = write_txt("a", 100, 0.5), write_wav("a", 1.32)
txt_b = write_txt("b", 50, 0.7)
txt_c, wav_c = write_txt("c", 200, 0.9), write_wav("c", 2.30)

# S1 load_clip - wav 자동 찾기 (같은 이름) / 없음 / 명시
a = sequence.load_clip(txt_a)
b = sequence.load_clip(txt_b)
c = sequence.load_clip(txt_c, wav_c)
check("S1 wav found by name, seconds = wav length", os.path.normpath(a.wav_path) == os.path.normpath(wav_a)
      and abs(a.seconds - 1.32) < 1e-4 and abs(a.data.seconds - 1.0) < 1e-9)
check("S1 no wav -> seconds = txt length", b.wav_path == "" and abs(b.seconds - 0.5) < 1e-9)
check("S1 explicit wav", os.path.normpath(c.wav_path) == os.path.normpath(wav_c) and abs(c.seconds - 2.3) < 1e-4)
b2 = sequence.load_clip(txt_b, "")
check("S1 wav_path '' = no audio even if a wav exists", b2.wav_path == "")

# S2 layout @ 24 fps, start 1, hold 0: A span = int(1.32*24) = 31 (keys 0..24), B 12, C 55
segs = sequence.layout([a, b, c], 1, 0, 24.0)
check("S2 starts back to back", [(s.start, s.end, s.key_frames) for s in segs] == [(1, 32, 24), (33, 45, 12), (46, 101, 48)])
check("S2 span >= key_frames", all(s.span >= s.key_frames for s in segs))

# S3 hold 12 -> 다음 시작이 12 프레임 늦다
segs = sequence.layout([a, b, c], 10, 12, 24.0)
check("S3 hold 12", [(s.start, s.end) for s in segs] == [(10, 41), (54, 66), (79, 134)])
try:
    sequence.layout([a], 1, -1, 24.0)
    check("S3 hold < 0 -> ValueError", False)
except ValueError:
    check("S3 hold < 0 -> ValueError", True)
check("S3 30 fps spans (2.3 s * 30 = 69, not 68 by float error)", [s.span for s in sequence.layout([a, b, c], 1, 0, 30.0)] == [39, 15, 69])
check("S3 key_frames float-safe: 230 rows at 30 fps = 69", sequence.key_frames(lipsync_data.LipsyncData("x", [[0.0] * 22] * 230, list(lipsync_data.MODEL_COLUMNS), 100.0), 30.0) == 69)

# S4 write_sequence_wav - A 와 C 를 자리에, B 는 무음. 24 fps, hold 12
out = os.path.join(work, "seq.wav")
res = sequence.write_sequence_wav(segs, out, 24.0)
with wave.open(out, "rb") as w:
    rate, nch, width, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
    frames = w.readframes(n)
exp_c_offset = int(round((79 - 10) / 24.0 * 44100))
n_a, n_c = int(round(1.32 * 44100)), int(round(2.30 * 44100))
exp_len = exp_c_offset + n_c
check("S4 format kept, length = C offset + C length", res == out and (rate, nch, width) == (44100, 1, 2) and n == exp_len)


def sample_at(i):
    return int.from_bytes(frames[i * 2:i * 2 + 2], "little", signed=True)


check("S4 A audio at 0, silence after A (B has none), C at its frame offset",
      sample_at(0) == 1000 and sample_at(n_a - 1) == 1000 and sample_at(n_a + 10) == 0
      and sample_at(exp_c_offset - 1) == 0 and sample_at(exp_c_offset) == 1000 and sample_at(exp_len - 1) == 1000)
check("S4 default path next to the first txt", sequence.sequence_wav_path([a]) == os.path.join(work, "jali_sequence.wav")
      and sequence.sequence_wav_path([]) == "")

# S5 오류: 형식 다름 / 원본 덮기 / wav 없음
d = sequence.load_clip(write_txt("d", 10, 0.1), write_wav("d", 0.1, rate=48000))
try:
    sequence.write_sequence_wav(sequence.layout([a, d], 1, 0, 24.0), out, 24.0)
    check("S5 format differs -> ValueError", False)
except ValueError as e:
    check("S5 format differs -> ValueError", "48000 Hz" in str(e))
try:
    sequence.write_sequence_wav(segs, wav_a, 24.0)
    check("S5 overwrite a clip wav -> ValueError", False)
except ValueError as e:
    check("S5 overwrite a clip wav -> ValueError", "overwrite" in str(e))
check("S5 no wav at all -> None", sequence.write_sequence_wav(sequence.layout([b], 1, 0, 24.0), out, 24.0) is None)

# S6 단일 클립 layout 은 예전 apply 와 같은 구간 (start .. start + key_frames)
segs = sequence.layout([b], 5, 0, 24.0)
check("S6 single clip without wav: span == key_frames", segs[0].start == 5 and segs[0].end == 17 and segs[0].key_frames == 12)

print("RESULT", "OK" if all(R) else "%d FAILED" % R.count(False))
sys.exit(0 if all(R) else 1)
