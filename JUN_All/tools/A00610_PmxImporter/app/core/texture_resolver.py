# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00610_PmxImporter - 텍스처 경로 찾기 · 알파 판정 · 코드페이지 복사 (마야 비의존)
#
# PMX 의 텍스처 경로는 PMX 폴더 기준 상대 경로이고 구분자가 '\' 다 (예: "tex\\颜.png").
#
# ★ 마야 2024 는 시스템 코드페이지(이 PC = cp949)로 표현할 수 없는 글자가 든 경로의 이미지를 읽지 못한다
#   (fileTextureName 이 '?' 로 바뀌고 outSize = 0, 2026-11-09 mayapy 실측: '颜' · '体' 실패).
#   그런 파일은 PMX 옆 maya_textures/ 에 FBXASC 이름으로 복사해 연결한다 (원본은 건드리지 않는다).

import os
import shutil
import struct

from .pmx_convert import encode_name

COPY_FOLDER = "maya_textures"


def normalize_rel(path):
    return (path or "").replace("\\", "/").strip()


def resolve(pmx_dir, rel_path, search_depth=3):
    """PMX 텍스처 경로 -> (절대 경로, 상태). 상태: "found" | "case" | "search" | "missing" | "empty"."""
    rel = normalize_rel(rel_path)
    if not rel:
        return "", "empty"
    path = rel if os.path.isabs(rel) else os.path.join(pmx_dir, rel)
    path = os.path.normpath(path)
    if os.path.isfile(path):
        return path, "found"
    # 대소문자 무시
    found = _case_insensitive(pmx_dir, rel)
    if found:
        return found, "case"
    # 같은 파일 이름을 PMX 폴더 아래에서
    base = os.path.basename(rel).lower()
    hits = []
    root_depth = pmx_dir.rstrip("\\/").count(os.sep)
    for root, dirs, files in os.walk(pmx_dir):
        if root.count(os.sep) - root_depth >= search_depth:
            dirs[:] = []
        for f in files:
            if f.lower() == base:
                hits.append(os.path.join(root, f))
    if hits:
        hits.sort(key=len)
        return os.path.normpath(hits[0]), "search"
    return path, "missing"


def _case_insensitive(base_dir, rel):
    cur = base_dir
    for part in rel.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            cur = os.path.dirname(cur)
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return None
        match = [n for n in names if n.lower() == part.lower()]
        if not match:
            return None
        cur = os.path.join(cur, match[0])
    return os.path.normpath(cur) if os.path.isfile(cur) else None


# ----------------------------------------------------------------------------
# 알파
# ----------------------------------------------------------------------------

def has_alpha(path):
    """헤더만 읽어 알파 채널이 있는지. 모르면 None."""
    try:
        with open(path, "rb") as f:
            head = f.read(64)
            ext = os.path.splitext(path)[1].lower()
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                if head[25] in (4, 6):
                    return True
                return _png_has_trns(f)
            if head[:2] == b"BM" and len(head) >= 30:
                return struct.unpack("<H", head[28:30])[0] == 32
            if head[:4] == b"DDS " and len(head) >= 64:
                f.seek(80)
                pf = f.read(12)
                flags = struct.unpack("<I", pf[0:4])[0]
                fourcc = pf[4:8]
                return bool(flags & 0x1) or fourcc in (b"DXT2", b"DXT3", b"DXT4", b"DXT5")
            if ext == ".tga" and len(head) >= 18:
                return head[16] == 32 or (head[17] & 0x0F) > 0
            if head[:3] == b"\xff\xd8\xff":
                return False
    except (OSError, IndexError, struct.error):
        return None
    return None


def _png_has_trns(f):
    f.seek(8)
    while True:
        hdr = f.read(8)
        if len(hdr) < 8:
            return False
        length, kind = struct.unpack(">I4s", hdr)
        if kind == b"tRNS":
            return True
        if kind in (b"IDAT", b"IEND"):
            return False
        f.seek(length + 4, 1)


# ----------------------------------------------------------------------------
# 코드페이지
# ----------------------------------------------------------------------------

def codepage_safe(path, codepage):
    """이 코드페이지로 경로를 표현할 수 있는가 (마야가 이미지를 읽을 수 있는가)."""
    if not codepage:
        return True
    try:
        path.encode(codepage)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def ascii_copy_path(pmx_dir, rel_path):
    """복사본 경로: <PMX 폴더>/maya_textures/<FBXASC(상대 경로, 확장자 제외)>.<확장자>

    '/' 도 FBXASC047 로 바뀌어 decode_name 으로 원래 상대 경로를 되찾을 수 있다.
    """
    rel = normalize_rel(rel_path)
    stem, ext = os.path.splitext(rel)
    return os.path.join(pmx_dir, COPY_FOLDER, encode_name(stem) + ext.lower())


def copy_if_needed(src, dst):
    """dst 가 없거나 크기 · 수정 시각이 다르면 복사. 복사했으면 True."""
    try:
        if os.path.isfile(dst):
            a, b = os.stat(src), os.stat(dst)
            if a.st_size == b.st_size and int(a.st_mtime) == int(b.st_mtime):
                return False
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        shutil.copy2(src, dst)
        return True
    except OSError:
        raise
