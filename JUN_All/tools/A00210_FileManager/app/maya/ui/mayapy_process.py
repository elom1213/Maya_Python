# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00210_FileManager / Maya 탭 - mayapy 워커를 QProcess 로 띄우고 진행률 팝업에 잇는다 (PySide)
#
#   result = run_job(parent, mayapy, job, title, log)      # 끝날 때까지 로컬 이벤트 루프로 기다린다(창은 살아 있다)
#
# 워커의 프로토콜 줄(mayapy_runner.parse_line)을 받아 log 콜백 · 진행률 팝업에 전달한다. 팝업의 Cancel 은
# 취소 플래그 파일을 만들고(워커가 파일 경계에서 멈춘다), 그래도 안 끝나면 Close 로 프로세스를 죽인다.
# 마야 자체 출력(프로토콜이 아닌 줄)은 작업 폴더의 raw.log 에만 남긴다.

import os

from Framework.qt.qt import (
    QProcess,
    QEventLoop,
    QTimer,
)
from Framework.qt.MOD_progress_qt_v01 import JUN_mod_progress_qt_v01

from ..core import mayapy_runner

# 취소를 눌렀는데 워커가 이 시간 안에 안 끝나면 프로세스를 끊는다(초). 파일 하나 저장이 끝날 여유.
CANCEL_GRACE_SEC = 120


class JobOutcome(object):
    def __init__(self):
        self.result = None        # 워커가 쓴 결과 dict
        self.error = ""           # 프로토콜 error 또는 프로세스 실패
        self.cancelled = False
        self.exit_code = None
        self.job_dir = ""


def run_job(parent, mayapy, job, title="Maya", message="", log=None):
    """mayapy 워커를 돌리고 JobOutcome 을 돌려준다. 끝날 때까지 블로킹(이벤트 루프는 돈다)."""
    outcome = JobOutcome()
    if not mayapy or not os.path.isfile(mayapy):
        outcome.error = "mayapy.exe not found : {0!r}".format(mayapy)
        return outcome

    job_dir = mayapy_runner.new_job_dir()
    outcome.job_dir = job_dir
    job_path, result_path, cancel_flag = mayapy_runner.write_job(job_dir, job)
    raw_log = open(os.path.join(job_dir, "raw.log"), "w", encoding="utf-8", errors="replace")

    dlg = JUN_mod_progress_qt_v01(parent, title=title, message=message or "Starting mayapy...",
                                  cancellable=True)
    dlg.start()
    cb = dlg.callback()

    proc = QProcess(parent)
    proc.setProcessChannelMode(QProcess.MergedChannels)
    loop = QEventLoop()
    state = {"buffer": "", "cancel_sent": False, "killed": False}

    def _handle(line):
        raw_log.write(line + "\n")
        msg = mayapy_runner.parse_line(line)
        if msg is None:
            return
        kind = msg.get("type")
        if kind == "log":
            if log:
                log(msg.get("text", ""))
        elif kind == "progress":
            cb(msg.get("done", 0), msg.get("total", 1) or 1, msg.get("message") or None)
        elif kind == "result":
            try:
                outcome.result = mayapy_runner.read_result(msg.get("path") or result_path)
            except Exception as exc:  # noqa: BLE001
                outcome.error = "could not read result : {0}".format(exc)
        elif kind == "error":
            outcome.error = msg.get("text", "error")

    def _on_ready():
        data = bytes(proc.readAllStandardOutput().data()).decode("utf-8", errors="replace")
        state["buffer"] += data
        while "\n" in state["buffer"]:
            line, state["buffer"] = state["buffer"].split("\n", 1)
            _handle(line.rstrip("\r"))
        # 취소 요청을 플래그로 전달 (한 번만)
        if dlg.was_cancelled() and not state["cancel_sent"]:
            state["cancel_sent"] = True
            outcome.cancelled = True
            mayapy_runner.request_cancel(cancel_flag)
            if log:
                log("[WARN] Cancel requested - stopping after the current file.")
            QTimer.singleShot(CANCEL_GRACE_SEC * 1000, _force_stop)

    def _force_stop():
        if proc.state() != QProcess.NotRunning:
            state["killed"] = True
            proc.kill()

    def _on_finished(code, _status):
        outcome.exit_code = code
        if state["buffer"]:
            _handle(state["buffer"])
            state["buffer"] = ""
        loop.quit()

    proc.readyReadStandardOutput.connect(_on_ready)
    proc.finished.connect(_on_finished)
    # Cancel 버튼은 readyRead 가 올 때 확인되므로, 출력이 뜸할 때를 위해 타이머로도 본다.
    poll = QTimer(parent)
    poll.setInterval(500)
    poll.timeout.connect(_on_ready)
    poll.start()

    cmd = mayapy_runner.command(mayapy, job_path)
    if log:
        log("mayapy : {0}".format(mayapy))
    proc.start(cmd[0], cmd[1:])
    if not proc.waitForStarted(10000):
        outcome.error = "could not start mayapy : {0}".format(proc.errorString())
    else:
        loop.exec_()

    poll.stop()
    raw_log.close()
    dlg.finish()

    if state["killed"]:
        outcome.error = outcome.error or "mayapy was stopped (killed after cancel)"
    elif outcome.exit_code not in (0, None) and not outcome.error:
        outcome.error = "mayapy exited with code {0} (see {1})".format(
            outcome.exit_code, os.path.join(job_dir, "raw.log"))
    return outcome
