# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-20
# A00210_FileManager / Maya 탭 - 파일 "수정한 날짜" 바꾸기 코어 (v01.54, UI 비의존)
"""
파일 **내용은 그대로 두고** 수정한 날짜(mtime, 탐색기의 "수정한 날짜")만 바꾼다.

- `os.utime(path, (접근 시각, 새 수정 시각))` 만 쓴다 - 파일을 열어 쓰지 않으므로 내용 · 크기는 바뀌지 않는다.
  접근 시각(atime)은 원래대로 둔다. 만든 날짜(Windows creation time)는 건드리지 않는다.
- 새 시각 = 고른 **날짜** + (기본) **각 파일의 원래 시:분:초** 를 그대로, 또는 고른 시각 하나로 모두.
- 대상은 지금 `.ma` · `.mb` · `.fbx` 만(요청 2026-11-20). 그 밖의 파일 · 없는 파일은 건너뛰고 알린다.
- 바꾼 기록(원래 수정 시각)을 돌려준다 - UI 의 Undo Last 가 그것으로 되돌린다(`restore`).
- 읽기 전용 파일도 수정 시각은 바뀐다(Windows 의 읽기 전용은 내용 쓰기만 막는다 - 시험으로 확인).
"""

import datetime
import os

EXTENSIONS = (".ma", ".mb", ".fbx")


class DateChange(object):
    """파일 하나의 결과."""

    __slots__ = ("path", "old", "new", "error")

    def __init__(self, path, old=None, new=None, error=""):
        self.path = path
        self.old = old          # 원래 수정 시각 (epoch 초)
        self.new = new          # 바꾼 수정 시각
        self.error = error      # 실패 이유 (영어) - 성공이면 ""

    @property
    def ok(self):
        return not self.error


def is_target(path):
    return os.path.splitext(path)[1].lower() in EXTENSIONS


def split_targets(paths):
    """(바꿀 파일, [(건너뛸 파일, 이유)]) - 확장자 · 존재 확인, 중복 제거, 순서 유지."""
    keep, skipped, seen = [], [], set()
    for path in paths or []:
        if not path:
            continue
        key = os.path.normcase(os.path.abspath(path))
        if key in seen:
            continue
        seen.add(key)
        if not is_target(path):
            skipped.append((path, "not a .ma / .mb / .fbx file"))
        elif not os.path.isfile(path):
            skipped.append((path, "file not found"))
        else:
            keep.append(path)
    return keep, skipped


def modified(path):
    """수정 시각 (epoch 초). 못 읽으면 None."""
    try:
        return os.stat(path).st_mtime
    except OSError:
        return None


def new_timestamp(old, date, time_of_day=None):
    """새 수정 시각 (epoch 초, 로컬 시간 기준).

    date        : datetime.date - 바꿀 날짜
    time_of_day : datetime.time 또는 None. None 이면 원래 수정 시각의 시:분:초(소수 포함)를 그대로 쓴다.
    """
    if time_of_day is None:
        time_of_day = datetime.datetime.fromtimestamp(old).time() if old is not None else datetime.time(0, 0)
    return datetime.datetime.combine(date, time_of_day).timestamp()


def set_dates(paths, date, time_of_day=None):
    """paths 의 수정한 날짜를 바꾼다. [DateChange] (대상 파일만 - 건너뛸 것은 split_targets 로 먼저 거른다)."""
    out = []
    for path in paths:
        try:
            st = os.stat(path)
        except OSError as exc:
            out.append(DateChange(path, error=str(exc)))
            continue
        new = new_timestamp(st.st_mtime, date, time_of_day)
        try:
            os.utime(path, (st.st_atime, new))
        except OSError as exc:
            out.append(DateChange(path, st.st_mtime, None, str(exc)))
            continue
        after = modified(path)
        if after is None or abs(after - new) > 1.0:
            out.append(DateChange(path, st.st_mtime, after, "the new date did not stick"))
            continue
        out.append(DateChange(path, st.st_mtime, after))
    return out


def restore(changes):
    """set_dates 결과를 되돌린다(성공한 것만, 원래 수정 시각으로). 되돌린 수."""
    done = 0
    for c in changes:
        if not c.ok or c.old is None or not os.path.isfile(c.path):
            continue
        try:
            st = os.stat(c.path)
            os.utime(c.path, (st.st_atime, c.old))
            done += 1
        except OSError:
            pass
    return done


def format_time(ts):
    """표시용 'YYYY-MM-DD HH:MM:SS' (로컬)."""
    if ts is None:
        return "-"
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
