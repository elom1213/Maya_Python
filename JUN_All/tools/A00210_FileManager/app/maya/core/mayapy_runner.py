# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 - mayapy 실행 준비 (재노출). 본체는 Framework/core/mayapy_runner.py (2026-10-26 공용 승격, v01.40).
#
# 공용 모듈은 워커 경로를 command() 의 인자로 받는다. 이 툴의 워커는 같은 폴더 maya_worker.py 이므로 여기서 감싼다
# (reference_tab.py 의 호출 - find_mayapy · candidates · command · parse_line - 은 그대로).

import os
import sys

from Framework.core.mayapy_runner import *  # noqa: F401,F403
from Framework.core import mayapy_runner as _impl

PREFIX = _impl.PREFIX


def worker_path():
    """mayapy 로 띄울 maya_worker.py 의 경로. PyInstaller 로 얼린 exe 면 _MEIPASS 아래(launch.spec datas)."""
    frozen = _impl.frozen_path("tools", "A00210_FileManager", "app", "maya", "core", "maya_worker.py")
    if frozen:
        return frozen
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "maya_worker.py")


def new_job_dir():
    return _impl.new_job_dir("jun_fm_maya")


def command(mayapy, job_path, worker=None):
    """실행 명령 [mayapy, -u, worker, job]. worker 를 안 주면 이 툴의 maya_worker.py."""
    return _impl.command(mayapy, job_path, worker or worker_path())
