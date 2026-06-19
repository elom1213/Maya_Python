# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00230_StartupTool - boot coordinator: open folders + launch standalone tools
#
# 부팅(로그인) 시 config/startup.json 에 적힌 폴더들을 탐색기로 팝업하고,
# tools 목록의 standalone PySide 툴(각 launch.py)을 별 프로세스로 실행한다.
# 경로는 환경변수(%USERPROFILE% 등)와 repo 상대 위치로 풀리므로 PC 가 바뀌어도 동작한다.
#
#   python startup.py        (단독 실행 / 테스트)
#   install.py 로 Startup 에 등록하면 부팅 시 자동 실행된다.

import os
import sys
import json
import subprocess

# folder 로직은 open_folders 모듈을 재사용한다.
import open_folders

# config/startup.json 위치는 이 스크립트 기준으로 해석 (repo 경로가 어디든 동작)
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(HERE)  # .../JUN_All/tools  (모든 A000XX_* 툴의 부모)
CONFIG_PATH = os.path.join(HERE, "config", "startup.json")


def load_config(path=CONFIG_PATH):
    """Read startup.json. Returns (folders, tools, open_missing). Tolerates full-line // comments."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    data = json.loads(open_folders._strip_line_comments(text))
    folders = data.get("folders", [])
    tools = data.get("tools", [])
    open_missing = bool(data.get("open_missing", False))
    return folders, tools, open_missing


def interpreter():
    """Prefer pythonw.exe (no console) next to the running interpreter; fall back to python.exe.

    부팅 시 .vbs 가 pythonw 로 이 스크립트를 호출하므로, 같은(=PySide 가 깔린) 파이썬으로
    각 툴의 launch.py 를 띄우게 된다."""
    base = os.path.dirname(sys.executable)
    candidate = os.path.join(base, "pythonw.exe")
    if os.path.isfile(candidate):
        return candidate
    return sys.executable


def tool_launch_path(entry):
    """Resolve a tool entry to its launch.py absolute path.

    - {"tool": "A00210_FileManager"} -> <tools>/A00210_FileManager/launch.py
    - {"launch": "<path>/launch.py"} -> 환경변수/~ 확장한 절대경로 (override)
    Returns the path or "" when the entry is malformed.
    """
    raw = entry.get("launch")
    if raw:
        return open_folders.resolve_path(raw)
    name = entry.get("tool", "")
    if not name:
        return ""
    return os.path.normpath(os.path.join(TOOLS_DIR, name, "launch.py"))


def launch_tools(tools):
    """Launch each enabled tool's launch.py as a detached process. Returns (launched, skipped, missing)."""
    # Windows 에서 부모(코디네이터)가 끝나도 자식 GUI 가 살아있도록 분리 실행.
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | \
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    py = interpreter()
    launched, skipped, missing = [], [], []
    seen = set()

    for entry in tools:
        if not entry.get("enabled", True):
            skipped.append(entry.get("tool") or entry.get("launch") or "?")
            continue

        path = tool_launch_path(entry)
        if not path:
            continue

        key = path.lower()
        if key in seen:
            continue
        seen.add(key)

        if not os.path.isfile(path):
            missing.append(path)
            continue

        try:
            subprocess.Popen(
                [py, path],
                cwd=os.path.dirname(path),
                creationflags=flags,
                close_fds=True,
            )
            launched.append(path)
        except OSError as exc:
            print("[A00230] failed to launch: %s (%s)" % (path, exc), file=sys.stderr)
            missing.append(path)

    return launched, skipped, missing


def main():
    try:
        folders, tools, open_missing = load_config()
    except FileNotFoundError:
        print("[A00230] config not found: %s" % CONFIG_PATH, file=sys.stderr)
        return 1
    except (ValueError, OSError) as exc:
        print("[A00230] failed to read config: %s" % exc, file=sys.stderr)
        return 1

    opened, fskip, fmiss = open_folders.open_folders(folders, open_missing)
    launched, tskip, tmiss = launch_tools(tools)

    print("[A00230] folders: opened %d, skipped %d, missing %d"
          % (len(opened), len(fskip), len(fmiss)))
    print("[A00230] tools: launched %d, skipped %d, missing %d"
          % (len(launched), len(tskip), len(tmiss)))
    for p in fmiss:
        print("[A00230] folder missing (skipped): %s" % p, file=sys.stderr)
    for p in tmiss:
        print("[A00230] tool missing (skipped): %s" % p, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
