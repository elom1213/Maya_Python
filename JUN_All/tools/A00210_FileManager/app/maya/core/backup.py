# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00210_FileManager / Maya 탭 - 저장 전 원본 백업 (UI/DCC 비의존)
#
# 백업본은 원본 파일의 폴더 아래 `backup/` 에 둔다 - **A00220_BackupTool 과 같은 폴더**다(없으면 만들고
# 있으면 그대로). A00220 은 `<이름>_BU<확장자>` · `<이름>_BU_NN<확장자>` 를 쓰므로, 이 툴의 백업은
# `<이름>_REF_NN<확장자>` 로 구분한다(NN 은 비어 있는 다음 번호, 지우지 않는다). 같은 폴더의
# `log.txt` 에 A00220 과 같은 모양으로 한 줄을 남긴다.

import os
import re
import shutil
from datetime import datetime

FOLDER_NAME = "backup"
SUFFIX = "REF"
_PAD = 2
_LOG_NAME = "log.txt"


def backup_dir_for(source_path, folder_name=FOLDER_NAME):
    parent = os.path.dirname(os.path.abspath(source_path))
    backup_dir = os.path.join(parent, folder_name)
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def list_versions(backup_dir, base, ext, suffix=SUFFIX):
    """`{base}_{suffix}_{NN}{ext}` 들의 [(index, name), ...] (오름차순)."""
    if not os.path.isdir(backup_dir):
        return []
    pattern = re.compile(
        r"^" + re.escape("{0}_{1}_".format(base, suffix)) + r"(\d+)" + re.escape(ext) + r"$",
        re.IGNORECASE)
    found = []
    for name in os.listdir(backup_dir):
        m = pattern.match(name)
        if m:
            found.append((int(m.group(1)), name))
    found.sort(key=lambda item: item[0])
    return found


def backup_file(source_path, folder_name=FOLDER_NAME, suffix=SUFFIX):
    """source_path 를 `backup/<base>_REF_NN<ext>` 로 복사하고 백업 절대경로를 돌려준다.

    원본이 없으면 FileNotFoundError. 복사 실패(OSError)는 그대로 올라간다 - 호출부가 그 파일을 건너뛴다.
    """
    if not os.path.isfile(source_path):
        raise FileNotFoundError(source_path)
    backup_dir = backup_dir_for(source_path, folder_name)
    base, ext = os.path.splitext(os.path.basename(source_path))
    existing = list_versions(backup_dir, base, ext, suffix)
    index = (existing[-1][0] + 1) if existing else 1
    dst = os.path.join(backup_dir, "{0}_{1}_{2:0{pad}d}{3}".format(base, suffix, index, ext, pad=_PAD))
    while os.path.exists(dst):               # 번호 사이가 비어 있어도 덮어쓰지 않는다
        index += 1
        dst = os.path.join(backup_dir, "{0}_{1}_{2:0{pad}d}{3}".format(base, suffix, index, ext, pad=_PAD))
    shutil.copy2(source_path, dst)
    _append_log(backup_dir, source_path, dst)
    return dst


def _append_log(backup_dir, source_path, dst):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[{0}] FileTool Reference: {1} -> {2}\n".format(
        stamp, os.path.basename(source_path), os.path.basename(dst))
    try:
        with open(os.path.join(backup_dir, _LOG_NAME), "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass
