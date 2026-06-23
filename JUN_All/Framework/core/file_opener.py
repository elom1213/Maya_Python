# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-23
# Framework - OS 파일 탐색기로 경로 열기/선택 공용 헬퍼 (UI/DCC 비의존).
#
# 폴더면 그 폴더를 열고, 파일이면 폴더를 열어 그 파일을 선택(하이라이트)한다.
# A00240_PathTool 이 검증한 구현을 Framework 로 승격 — A00210_FileManager /
# A00220_BackupTool 등이 각자 복붙하던 `explorer /select,` 로직을 일원화한다.
# Windows 우선(os.startfile / explorer), macOS·Linux 폴백 제공.

import os
import sys
import subprocess


def open_path(path):
    """주어진 경로를 탐색기로 연다.

    - 폴더: 그 폴더 창을 연다.
    - 파일: 파일이 든 폴더를 열고 파일을 선택(하이라이트)한다.

    경로가 비었거나 존재하지 않으면 예외를 던진다(호출부에서 안내).
    """
    if not path:
        raise ValueError("Empty path.")

    norm = os.path.normpath(os.path.expanduser(os.path.expandvars(path)))

    if not os.path.exists(norm):
        raise FileNotFoundError(norm)

    is_dir = os.path.isdir(norm)

    if sys.platform.startswith("win"):
        if is_dir:
            os.startfile(norm)  # type: ignore[attr-defined]  # Windows 전용
        else:
            # explorer /select 는 인자를 한 문자열로 받아야 안정적이다.
            subprocess.run(f'explorer /select,"{norm}"')
    elif sys.platform == "darwin":
        subprocess.run(["open", norm] if is_dir else ["open", "-R", norm])
    else:
        folder = norm if is_dir else os.path.dirname(norm)
        subprocess.run(["xdg-open", folder])
