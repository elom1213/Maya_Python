# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 - mayapy 워커 QProcess (재노출). 본체는 Framework/qt/MOD_mayapyProcess_qt_v01.py
# (2026-10-26 공용 승격, v01.40). 공용 run_job 은 워커 경로를 받으므로 이 툴의 maya_worker.py 를 채워 넘긴다.

from Framework.qt.MOD_mayapyProcess_qt_v01 import JobOutcome, CANCEL_GRACE_SEC  # noqa: F401
from Framework.qt import MOD_mayapyProcess_qt_v01 as _impl

from ..core import mayapy_runner


def run_job(parent, mayapy, job, title="Maya", message="", log=None):
    """mayapy 워커(maya_worker.py)를 돌리고 JobOutcome 을 돌려준다. 끝날 때까지 블로킹(이벤트 루프는 돈다)."""
    return _impl.run_job(parent, mayapy, job, mayapy_runner.worker_path(), title=title, message=message, log=log,
                         job_prefix="jun_fm_maya")
