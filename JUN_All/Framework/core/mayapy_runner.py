# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.core.mayapy_runner - mayapy 하위 프로세스 실행 준비 (UI/DCC 비의존, 순수 파이썬)
#
# 2026-10-26 A00210_FileManager/app/maya/core/mayapy_runner.py (v01.35, 2026-10-12) 를 공용으로 올렸다 - A00560_JaliBatch 가
# 같은 방식으로 mayapy 워커를 돌린다. A00210 은 재노출(worker_path · command 는 자기 워커 경로로 감싼다).
#
# standalone(마야 밖) 앱이 maya.cmds 가 필요한 일을 할 때 **mayapy.exe 로 워커 스크립트를 띄운다.** 이 모듈은
#   - mayapy 찾기 (find_mayapy / candidates)                      - 작업 파일(job json) 쓰기 (write_job)
#   - 명령줄 만들기 (command)                                      - 워커가 찍는 프로토콜 줄 파싱 (parse_line)
# 만 한다. 프로세스를 실제로 띄우고 줄을 받는 것은 Framework/qt/MOD_mayapyProcess_qt_v01.run_job 또는 테스트의 subprocess.
# 워커 스크립트는 툴마다 다르다(A00210 maya_worker.py · A00560 app/maya/worker.py) - command() 에 경로로 넘긴다.
#
# 프로토콜 - 워커 stdout 의 한 줄:
#   JUNMSG {"type": "log", "text": "..."}
#   JUNMSG {"type": "progress", "done": 1.5, "total": 3, "message": "..."}
#   JUNMSG {"type": "result", "path": "<결과 json 경로>"}
#   JUNMSG {"type": "error", "text": "..."}
# 그 밖의 줄(마야 기동 로그 · 경고)은 프로토콜이 아니므로 무시한다(디버그용으로 raw 로그 파일에 남긴다).
# 워커 쪽 규약(메모리 maya-reference-import-traps): maya.standalone.initialize 뒤 모든 경로에서 uninitialize → os._exit(code).

import os
import sys
import json
import glob
import tempfile
import time

PREFIX = "JUNMSG "


# ------------------------------------------------------------------ mayapy 찾기

def candidates():
    """이 PC 의 mayapy.exe 후보들 - 새 버전이 먼저. 없으면 빈 목록."""
    found = []
    roots = []
    for env in ("PROGRAMFILES", "PROGRAMW6432"):
        base = os.environ.get(env)
        if base:
            roots.append(os.path.join(base, "Autodesk"))
    roots.append(r"C:\Program Files\Autodesk")
    seen = set()
    for root in roots:
        for path in glob.glob(os.path.join(root, "Maya*", "bin", "mayapy.exe")):
            key = os.path.normcase(path)
            if key in seen:
                continue
            seen.add(key)
            found.append(path)
    # MAYA_LOCATION 도 본다
    loc = os.environ.get("MAYA_LOCATION")
    if loc:
        path = os.path.join(loc, "bin", "mayapy.exe")
        if os.path.isfile(path) and os.path.normcase(path) not in seen:
            found.append(path)

    def _version(path):
        name = os.path.basename(os.path.dirname(os.path.dirname(path)))
        digits = "".join(ch for ch in name if ch.isdigit())
        return int(digits) if digits else 0
    found.sort(key=_version, reverse=True)
    return found


def find_mayapy(preferred=""):
    """preferred 가 실제 파일이면 그것, 아니면 후보 중 첫 번째. 없으면 ""."""
    if preferred and os.path.isfile(preferred):
        return preferred
    cands = candidates()
    return cands[0] if cands else ""


# ------------------------------------------------------------------ 워커 · 작업 파일

def frozen_path(*parts):
    """PyInstaller 로 얼린 exe 면 _MEIPASS 아래의 그 경로(있을 때만), 아니면 ""."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", "")
        if base:
            path = os.path.join(base, *parts)
            if os.path.isfile(path):
                return path
    return ""


def new_job_dir(prefix="jun_maya"):
    """작업 파일 · 결과 · 취소 플래그 · raw 로그를 둘 임시 폴더(작업마다 하나)."""
    return tempfile.mkdtemp(prefix="{0}_{1}_".format(prefix, time.strftime("%H%M%S")))


def write_job(job_dir, job):
    """job dict 를 job.json 으로 쓰고 (job 경로, 결과 경로, 취소 플래그 경로) 를 돌려준다."""
    job = dict(job)
    job["result"] = os.path.join(job_dir, "result.json")
    job["cancel_flag"] = os.path.join(job_dir, "cancel.flag")
    path = os.path.join(job_dir, "job.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(job, fh, ensure_ascii=False, indent=1)
    return path, job["result"], job["cancel_flag"]


def command(mayapy, job_path, worker):
    """실행 명령 [mayapy, -u, worker, job]. -u 로 stdout 버퍼링을 끈다(줄이 바로 온다)."""
    return [mayapy, "-u", worker, job_path]


def request_cancel(cancel_flag):
    try:
        with open(cancel_flag, "w") as fh:
            fh.write("cancel")
    except OSError:
        pass


# ------------------------------------------------------------------ 프로토콜

def parse_line(line):
    """stdout 한 줄 -> dict(프로토콜 메시지) 또는 None(마야 소음)."""
    text = line.strip()
    if not text.startswith(PREFIX):
        return None
    try:
        return json.loads(text[len(PREFIX):])
    except ValueError:
        return None


def read_result(result_path):
    with open(result_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ 워커 쪽 도우미 (워커 스크립트가 import 해서 쓴다)

def emit(**msg):
    sys.stdout.write(PREFIX + json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def emit_log(text):
    emit(type="log", text=str(text))


def emit_progress(done, total, message=None):
    emit(type="progress", done=float(done), total=float(total), message=message or "")
