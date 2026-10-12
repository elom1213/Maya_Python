# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00210_FileManager / Maya 탭 - mayapy 워커 (mayapy.exe 가 실행한다. UI 프로세스에서 import 하지 않는다)
#
#   mayapy -u maya_worker.py <job.json>
#
# job.json:
#   {"job": "scan",   "files": [...]}
#   {"job": "import", "scan": <scan 결과 dict>, "checked": [norm...],
#                     "remove_namespaces": bool, "make_backup": bool}
#   + "result": 결과 json 경로, "cancel_flag": 이 파일이 생기면 파일 경계에서 멈춘다  (mayapy_runner.write_job 이 넣는다)
#
# stdout 에 `JUNMSG {...}` 프로토콜 줄을 찍는다(mayapy_runner 머리글 참고). 마야 자체 출력은 섞여 나오지만
# 프로토콜 줄은 접두어로 구별된다. 결과는 result 경로에 json 으로 쓰고 마지막에 result 메시지를 찍는다.
#
# 같은 폴더의 ref_scanner / ref_importer / ma_parser / backup 을 **평범한 모듈로** import 한다 - 이 폴더를
# sys.path 에 올리고. (그 모듈들은 상대 import 가 안 되면 평범한 import 로 폴백한다.) 얼린 exe 에서도
# launch.spec 의 datas 로 이 폴더가 통째로 풀리므로 같은 방식이 된다.

import os
import sys
import json
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PREFIX = "JUNMSG "


def emit(**msg):
    sys.stdout.write(PREFIX + json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def log(text):
    emit(type="log", text=str(text))


def progress(done, total, message=None):
    emit(type="progress", done=float(done), total=float(total), message=message or "")


def _shutdown():
    """마야를 정리하고 끝낸다 - 안 하면 종료 코드가 0xC000000D 로 깨진다(에러 경로에서도 부른다)."""
    try:
        import maya.standalone
        maya.standalone.uninitialize()
    except Exception:  # noqa: BLE001
        pass


def main(argv):
    if len(argv) < 2:
        emit(type="error", text="usage: maya_worker.py <job.json>")
        return 2
    with open(argv[1], "r", encoding="utf-8") as fh:
        job = json.load(fh)
    result_path = job.get("result", "")
    cancel_flag = job.get("cancel_flag", "")

    log("mayapy {0} starting Maya...".format(sys.version.split()[0]))
    progress(0, 1, "Starting Maya (mayapy)...")
    try:
        import maya.standalone
        maya.standalone.initialize(name="python")
    except Exception as exc:  # noqa: BLE001
        emit(type="error", text="Could not start Maya in mayapy : {0}".format(exc))
        return 3
    log("Maya ready.")

    import ref_scanner
    import ref_importer

    def should_cancel():
        return bool(cancel_flag) and os.path.exists(cancel_flag)

    try:
        kind = job.get("job")
        if kind == "scan":
            result = ref_scanner.scan(job.get("files", []), progress=progress, log=log, allow_open=True)
        elif kind == "import":
            result = ref_importer.import_references(
                job["scan"], set(job.get("checked", [])),
                remove_namespaces=bool(job.get("remove_namespaces", True)),
                make_backup=bool(job.get("make_backup", True)),
                log=log, progress=progress, should_cancel=should_cancel)
        else:
            emit(type="error", text="unknown job : {0!r}".format(kind))
            _shutdown()
            return 2
    except Exception:  # noqa: BLE001
        emit(type="error", text=traceback.format_exc())
        _shutdown()
        return 1

    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    emit(type="result", path=result_path)
    _shutdown()
    return 0


if __name__ == "__main__":
    code = main(sys.argv)
    sys.stdout.flush()
    os._exit(code)      # mayapy 가 종료 때 플러그인 정리로 머무는 일이 있어 바로 끝낸다
