# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.jali.sequence - 여러 클립을 한 타임라인에 이어 붙이기 (Maya 비의존). 2026-10-26 A00540 app/core 에서 승격.
#
# v01.02: txt(+wav) 여러 개를 사용자가 정한 순서로 나열하면 클립마다 시작 프레임을 정한다(layout).
#   클립이 차지하는 길이 = wav 길이(있으면, 모델 출력은 끝 0.32 s 가 빠지므로) 아니면 txt 길이. 씬 fps 로 내림.
#   다음 클립 시작 = 이전 클립 끝 + 1 + hold.   hold = 클립 사이 정지 프레임 수(사용자 값, 0 이상).
# 음성은 클립별 wav 를 각자의 프레임 자리(프레임 -> 샘플)에 놓은 wav 하나로 합쳐(write_sequence_wav) 사운드 노드
# 하나에 붙인다 - 마야 타임슬라이더는 사운드 노드 하나만 보여 주고, 합친 파일이면 재생 순서가 파일 자체에 박힌다.
# 합칠 wav 는 샘플레이트 · 채널 · 비트가 같아야 한다(변환기 출력은 전부 44.1 kHz 모노 16-bit).

import os
import wave

from . import lipsync_data


class Clip(object):
    """txt 하나(+ wav). seconds 는 타임라인에서 차지하는 길이."""

    def __init__(self, txt_path, data, wav_path=""):
        self.txt_path = txt_path
        self.data = data
        self.wav_path = wav_path or ""
        self.wav_seconds = lipsync_data.wav_seconds(self.wav_path) if self.wav_path else None

    @property
    def label(self):
        return os.path.basename(self.txt_path)

    @property
    def seconds(self):
        """wav 가 있으면 wav 길이(txt 보다 짧을 일은 없지만 긴 쪽), 없으면 txt 길이."""
        if self.wav_seconds:
            return max(self.wav_seconds, self.data.seconds)
        return self.data.seconds

    def set_wav(self, wav_path):
        self.wav_path = wav_path or ""
        self.wav_seconds = lipsync_data.wav_seconds(self.wav_path) if self.wav_path else None


def load_clip(txt_path, wav_path=None):
    """txt 를 읽고 wav 를 정한다. wav_path None = 자동(find_wav), "" = 없음. 형식이 틀리면 ValueError."""
    data = lipsync_data.load(txt_path)
    if wav_path is None:
        wav_path = lipsync_data.find_wav(txt_path, data)
    return Clip(txt_path, data, wav_path)


class Segment(object):
    """타임라인에 놓인 클립. 구간은 start ~ end(포함), 키는 start ~ start + key_frames(포함)."""

    def __init__(self, clip, start, span, key_frames):
        self.clip = clip
        self.start = int(start)
        self.span = int(span)
        self.key_frames = int(key_frames)

    @property
    def end(self):
        return self.start + self.span

    @property
    def data(self):
        return self.clip.data

    @property
    def wav_path(self):
        return self.clip.wav_path

    @property
    def label(self):
        return self.clip.label


_EPS = 1e-6     # 2.3 s * 30 fps = 68.99999... 같은 부동소수점 오차로 한 프레임이 빠지지 않게


def key_frames(data, fps):
    """키를 거는 프레임 수 - keyer.sample 과 같은 식(내림). 키는 0 ~ key_frames (포함)."""
    return int(len(data.rows) / data.fps * fps + _EPS)


def layout(clips, start, hold, fps):
    """clips 를 start 부터 순서대로 놓는다. Returns [Segment]. hold < 0 이면 ValueError."""
    hold = int(hold)
    if hold < 0:
        raise ValueError("Hold must be 0 or more frames")
    segments = []
    frame = int(start)
    for clip in clips:
        kf = key_frames(clip.data, fps)
        span = max(kf, int(clip.seconds * fps + _EPS))
        segments.append(Segment(clip, frame, span, kf))
        frame = frame + span + 1 + hold
    return segments


def sequence_wav_path(clips):
    """합친 wav 의 기본 경로 - 첫 txt 의 폴더에 jali_sequence.wav. 클립이 없으면 ""."""
    if not clips:
        return ""
    return os.path.join(os.path.dirname(os.path.abspath(clips[0].txt_path)), "jali_sequence.wav")


def write_sequence_wav(segments, out_path, fps):
    """클립 wav 들을 각자의 프레임 자리에 놓은 wav 하나를 out_path 에 쓴다.

    wav 가 없는 클립 자리는 무음. 모든 wav 는 샘플레이트 · 채널 · 비트가 같아야 한다.
    Returns out_path. wav 가 하나도 없으면 None. 형식이 다르거나 읽을 수 없거나 원본을 덮게 되면 ValueError.
    """
    with_wav = [s for s in segments if s.wav_path]
    if not with_wav:
        return None
    out_norm = os.path.normcase(os.path.normpath(out_path))
    for s in with_wav:
        if os.path.normcase(os.path.normpath(s.wav_path)) == out_norm:
            raise ValueError("Sequence WAV would overwrite a clip WAV: {0}".format(out_path))

    params = None
    pieces = []
    for s in with_wav:
        try:
            with wave.open(s.wav_path, "rb") as w:
                fmt = (w.getnchannels(), w.getsampwidth(), w.getframerate())
                frames = w.readframes(w.getnframes())
        except (OSError, EOFError, wave.Error) as e:
            raise ValueError("Cannot read WAV {0}: {1}".format(os.path.basename(s.wav_path), e))
        if params is None:
            params = fmt
        elif fmt != params:
            raise ValueError("WAV format differs: {0} is {1} Hz / {2} ch / {3}-bit, the first clip is {4} Hz / {5} ch / {6}-bit"
                             .format(os.path.basename(s.wav_path), fmt[2], fmt[0], fmt[1] * 8,
                                     params[2], params[0], params[1] * 8))
        pieces.append((s, frames))

    nch, width, rate = params
    block = nch * width
    origin = segments[0].start
    buf = bytearray()
    for s, frames in pieces:
        offset = int(round((s.start - origin) / float(fps) * rate)) * block
        end = offset + len(frames)
        if len(buf) < end:
            buf.extend(b"\x00" * (end - len(buf)))
        buf[offset:end] = frames            # layout 이 겹치지 않게 놓으므로 덮어쓰는 일은 없다
    try:
        with wave.open(out_path, "wb") as w:
            w.setnchannels(nch)
            w.setsampwidth(width)
            w.setframerate(rate)
            w.writeframes(bytes(buf))
    except (OSError, wave.Error) as e:
        raise ValueError("Cannot write {0}: {1}".format(out_path, e))
    return out_path
