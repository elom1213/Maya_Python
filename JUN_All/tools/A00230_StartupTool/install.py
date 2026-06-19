# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00230_StartupTool - register a boot launcher into the Windows Startup folder
#
# Startup 폴더에 A00230_StartupTool.vbs 런처를 생성한다. 로그인 시 이 런처가
# startup.py 를 pythonw 로(콘솔창 없이) 실행해 폴더 팝업 + standalone 툴들을 띄운다.
# 런처에는 "이 PC 의 절대경로" 가 박히므로, 새 PC 에서는 한 번만 실행하면 된다.
# (기존 설치자도 startup.py 로 갱신하려면 install.py 를 1회 재실행하면 된다.)
#
#   python install.py

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_SCRIPT = os.path.join(HERE, "startup.py")
LAUNCHER_NAME = "A00230_StartupTool.vbs"


def startup_dir():
    """Return the current user's Startup folder path."""
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(appdata, "Microsoft", "Windows",
                        "Start Menu", "Programs", "Startup")


def pythonw_path():
    """Prefer pythonw.exe (no console) next to the running interpreter; fall back to python.exe."""
    base = os.path.dirname(sys.executable)
    candidate = os.path.join(base, "pythonw.exe")
    if os.path.isfile(candidate):
        return candidate
    return sys.executable


def build_vbs(py_exe, script):
    """Build a .vbs that runs the target script hidden (window style 0)."""
    return (
        'Set sh = CreateObject("WScript.Shell")\r\n'
        'sh.Run """%s"" ""%s""", 0, False\r\n' % (py_exe, script)
    )


def main():
    if os.name != "nt":
        print("[A00230] install is Windows-only.", file=sys.stderr)
        return 1

    dest_dir = startup_dir()
    if not os.path.isdir(dest_dir):
        print("[A00230] Startup folder not found: %s" % dest_dir, file=sys.stderr)
        return 1

    launcher = os.path.join(dest_dir, LAUNCHER_NAME)
    content = build_vbs(pythonw_path(), TARGET_SCRIPT)

    with open(launcher, "w", encoding="utf-8") as f:
        f.write(content)

    print("[A00230] installed launcher: %s" % launcher)
    print("[A00230] runs on login: %s -> %s" % (pythonw_path(), TARGET_SCRIPT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
