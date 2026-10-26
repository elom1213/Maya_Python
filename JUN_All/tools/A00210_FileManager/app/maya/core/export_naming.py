# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - 출력 FBX 이름 규칙 · 미리보기 (UI/DCC 비의존, 순수 파이썬)  (v01.41)
#
# 원본 마야 파일 이름(확장자 없는 stem)에서 FBX 이름을 만든다. 순서:
#   ① Find / Replace  : 평문, 전부 치환, Case 토글. find 가 비면 그대로.
#   ② Insert          : 글자를 끼워 넣는다.
#        Token 모드 (기본) : 이름을 `_` 로 나눈 토큰 사이에 **새 토큰**으로. position 0 = 맨 앞 토큰, k = k 번째 토큰 뒤, -1 = 맨 끝.
#                           `anim_01` + (0, "bake") -> `bake_anim_01`   (사용자 결정 Q6: bake 토큰은 첫 토큰, 글자는 사용자가 바꾼다)
#                           `anim_01` + (1, "bake") -> `anim_bake_01`
#        Char 모드         : A00330 Quick Rename > Insert 와 같은 자리 규칙 - 0 맨 앞 · n 앞 n 글자 뒤 · -1 맨 끝 · -n 뒤 (n-1) 글자 앞.
#                           이름 밖을 가리키면 끝/앞으로 당기고 notes 에 적는다(길이가 제각각인 이름에 한 번에 쓰므로 막지 않는다).
#        text 가 비면 그대로.
#   ③ 확장자 .fbx
# 결과 이름이 서로 겹치는 행(같은 폴더 · 같은 이름, 대소문자 무시)은 collision - UI 가 실행을 막는다.
# Windows 금지 문자가 들어가면 invalid.

import os

MODE_TOKEN, MODE_CHAR = "token", "char"
MODES = (MODE_TOKEN, MODE_CHAR)
MODE_LABELS = {MODE_TOKEN: "Token", MODE_CHAR: "Char"}
EXT = ".fbx"
SEP = "_"

_INVALID = '\\/:*?"<>|'

DEFAULT_SPEC = {"find": "", "replace": "", "case": True, "mode": MODE_TOKEN, "position": 0, "text": "bake"}


class NamingSpec(object):
    def __init__(self, find="", replace="", case_sensitive=True, mode=MODE_TOKEN, position=0, text="bake", ext=EXT):
        self.find = find or ""
        self.replace = replace or ""
        self.case_sensitive = bool(case_sensitive)
        self.mode = mode if mode in MODES else MODE_TOKEN
        self.position = int(position)
        self.text = text or ""
        self.ext = ext or EXT

    @classmethod
    def from_dict(cls, data):
        data = dict(DEFAULT_SPEC, **(data or {}))
        return cls(data.get("find", ""), data.get("replace", ""), data.get("case", True), data.get("mode", MODE_TOKEN),
                   data.get("position", 0), data.get("text", "bake"))

    def to_dict(self):
        return {"find": self.find, "replace": self.replace, "case": self.case_sensitive, "mode": self.mode,
                "position": self.position, "text": self.text}


class Row(object):
    """미리보기 한 줄."""

    def __init__(self, file, stem, out_name, out_path, notes=None, collision=False, invalid=False):
        self.file = file
        self.stem = stem
        self.out_name = out_name
        self.out_path = out_path
        self.notes = list(notes or [])
        self.collision = collision
        self.invalid = invalid

    @property
    def ok(self):
        return not (self.collision or self.invalid)


# ------------------------------------------------------------------ pieces

def replace_text(stem, find, replace, case_sensitive=True):
    if not find:
        return stem
    if case_sensitive:
        return stem.replace(find, replace)
    out, i, low, lf = [], 0, stem.lower(), find.lower()
    while True:
        j = low.find(lf, i)
        if j < 0:
            out.append(stem[i:])
            break
        out.append(stem[i:j])
        out.append(replace)
        i = j + len(find)
    return "".join(out)


def insert_index(length, position):
    """(index, clamped) - A00330 insert_ops 와 같은 규칙."""
    position = int(position)
    if position >= 0:
        index = position
    else:
        index = length + position + 1       # -1 -> length (맨 끝), -2 -> length-1 ...
    clamped = False
    if index > length:
        index, clamped = length, True
    if index < 0:
        index, clamped = 0, True
    return index, clamped


def insert_char(stem, position, text):
    if not text:
        return stem, False
    index, clamped = insert_index(len(stem), position)
    return stem[:index] + text + stem[index:], clamped


def insert_token(stem, position, text, sep=SEP):
    """토큰 사이에 새 토큰. 0 = 맨 앞, k = k 번째 토큰 뒤, -1 = 맨 끝. 빈 stem 이면 text 만."""
    if not text:
        return stem, False
    if not stem:
        return text, False
    tokens = stem.split(sep)
    index, clamped = insert_index(len(tokens), position)
    tokens.insert(index, text)
    return sep.join(tokens), clamped


def output_stem(stem, spec):
    """(새 stem, notes)."""
    notes = []
    out = replace_text(stem, spec.find, spec.replace, spec.case_sensitive)
    if spec.mode == MODE_CHAR:
        out, clamped = insert_char(out, spec.position, spec.text)
    else:
        out, clamped = insert_token(out, spec.position, spec.text)
    if clamped:
        notes.append("position outside the name - placed at the end/start")
    if not out:
        notes.append("empty name")
    return out, notes


def invalid_characters(name):
    return "".join(sorted(set(c for c in (name or "") if c in _INVALID)))


# ------------------------------------------------------------------ preview

def preview(files, spec, out_dir=""):
    """[Row] - out_dir 가 비면 원본 폴더. 겹치는 out_path 는 collision."""
    rows = []
    for path in files or []:
        stem = os.path.splitext(os.path.basename(path))[0]
        new_stem, notes = output_stem(stem, spec)
        bad = invalid_characters(new_stem)
        invalid = bool(bad) or not new_stem
        if bad:
            notes.append("invalid characters : {0}".format(bad))
        out_name = new_stem + spec.ext
        folder = out_dir or os.path.dirname(os.path.abspath(path))
        out_path = os.path.normpath(os.path.join(folder, out_name))
        rows.append(Row(path, stem, out_name, out_path, notes, invalid=invalid))
    seen = {}
    for row in rows:
        seen.setdefault(os.path.normcase(row.out_path), []).append(row)
    for group in seen.values():
        if len(group) > 1:
            for row in group:
                row.collision = True
                row.notes.append("same output name as another file")
    return rows


def existing_outputs(rows):
    """이미 디스크에 있는 출력 경로들 (실행 전 Overwrite / Cancel 팝업용, 설계 D13)."""
    return [row.out_path for row in rows if os.path.isfile(row.out_path)]
