# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 - mayapy 워커 (mayapy.exe 가 실행한다. UI 프로세스에서 import 하지 않는다)
#
#   mayapy -u maya_worker.py <job.json>
#
# job.json:
#   {"job": "scan",   "files": [...]}                                                          Reference 하위탭
#   {"job": "import", "scan": <scan 결과 dict>, "checked": [norm...], "remove_namespaces": bool, "make_backup": bool}
#   {"job": "probe",  "files": [...], "rule": {"set_name", "match", "ignore_namespace"}}      Export 하위탭 (v01.41, 계획서 §3.2)
#   {"job": "export", "rule": {...}, "bake": bool, "channels": [...], "joints_only": bool, "euler_filter": bool,
#                     "import_references": bool, "report": path, "items": [{"file", "start", "end", "out_fbx"}]}   (§3.3)
#   + "result": 결과 json 경로, "cancel_flag": 이 파일이 생기면 파일 경계에서 멈춘다  (mayapy_runner.write_job 이 넣는다)
#
# stdout 에 `JUNMSG {...}` 프로토콜 줄을 찍는다(Framework/core/mayapy_runner.py 머리글). 결과는 result 경로에 json 으로 쓰고
# 마지막에 result 메시지를 찍는다.
#
# sys.path (v01.41): 같은 폴더(ref_scanner 등을 평범한 모듈로) + Framework 가 있는 루트 - dev 트리(JUN_All) 또는 릴리즈본(툴 폴더 안
# Framework), A00560 워커와 같은 규칙. 얼린 exe 는 launch.spec datas 로 이 폴더 · Framework/core · Framework/jali 가 디스크에 풀린다.

import os
import sys
import json
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))                                   # .../app/maya/core
TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))                 # .../A00210_FileManager
ROOT = os.path.dirname(os.path.dirname(TOOL_ROOT))                                   # JUN_All (dev) 또는 저장소 루트 (릴리즈)
# 얼린 exe 의 datas 도 같은 모양이다: <_MEIPASS>/tools/A00210_FileManager/app/maya/core 와 <_MEIPASS>/Framework -> ROOT = _MEIPASS
for _path in ((HERE, TOOL_ROOT, ROOT) if os.path.isdir(os.path.join(TOOL_ROOT, "Framework")) else (HERE, ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

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

    def should_cancel():
        return bool(cancel_flag) and os.path.exists(cancel_flag)

    try:
        kind = job.get("job")
        if kind == "scan":
            import ref_scanner
            result = ref_scanner.scan(job.get("files", []), progress=progress, log=log, allow_open=True)
        elif kind == "import":
            import ref_importer
            result = ref_importer.import_references(
                job["scan"], set(job.get("checked", [])),
                remove_namespaces=bool(job.get("remove_namespaces", True)),
                make_backup=bool(job.get("make_backup", True)),
                log=log, progress=progress, should_cancel=should_cancel)
        elif kind == "probe":
            import scene_probe
            result = scene_probe.probe(job.get("files", []), job.get("rule") or {}, log=log, progress=progress,
                                       should_cancel=should_cancel)
        elif kind == "export":
            import bake_export
            result = bake_export.export_all(job, log=log, progress=progress, should_cancel=should_cancel)
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
