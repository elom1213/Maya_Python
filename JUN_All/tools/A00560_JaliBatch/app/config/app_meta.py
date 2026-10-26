# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - app metadata (taskbar id + icon path resolver + Start menu launch spec)
#
# A00240 · A00210 과 같은 모양 (docs/taskbar_icon_guide.md · docs/Framework_shell_integration.md). UI/DCC 비의존.

import os
import sys

# 작업표시줄 아이콘·그룹핑용 고유 ID (역-DNS). 이 값을 프로세스에 지정해야 python.exe 아이콘 대신 이 앱 아이콘이 뜬다.
APP_USER_MODEL_ID = "Dnable.JUN.A00560.JaliBatch"

# 시작 메뉴 바로가기 이름(= 시작 메뉴 · 검색에 보이는 앱 이름)과 설명.
APP_NAME = "JUN JALI Batch"
APP_DESCRIPTION = "JUN JALI Batch - VisemeNet output folder -> JALI clip .mb files (mayapy), validate clips"

_ICON_BASENAME = "A00560_JaliBatch"


def tool_root():
    """툴 루트 폴더(launch.py 가 있는 곳)의 절대경로."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def start_menu_launch_spec():
    """시작 메뉴 바로가기가 실행할 명령(공용 shell_integration.LaunchSpec). Framework 는 lazy import."""
    from Framework.core import shell_integration
    return shell_integration.launch_spec(tool_root(), icon_path())


def icon_path(prefer_ico=True):
    """존재하는 아이콘 파일의 절대경로(없으면 ""). dev 는 tool/icon/, PyInstaller exe 는 _MEIPASS 아래."""
    exts = ("ico", "png") if prefer_ico else ("png", "ico")
    bases = [os.path.join(tool_root(), "icon")]
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            bases.insert(0, os.path.join(meipass, "icon"))
            bases.insert(1, meipass)
    for base in bases:
        for ext in exts:
            candidate = os.path.join(base, "{0}.{1}".format(_ICON_BASENAME, ext))
            if os.path.isfile(candidate):
                return candidate
    return ""


def worker_path():
    """mayapy 가 실행할 워커(app/maya/worker.py). 얼린 exe 면 _MEIPASS 아래(launch.spec datas)."""
    from Framework.core import mayapy_runner
    frozen = mayapy_runner.frozen_path("tools", "A00560_JaliBatch", "app", "maya", "worker.py")
    if frozen:
        return frozen
    return os.path.join(tool_root(), "app", "maya", "worker.py")


def guide_doc():
    """안내 문서 경로 - dev 트리는 JUN_All/docs, 릴리즈본은 툴 폴더 안 docs."""
    root = tool_root()
    for candidate in (os.path.join(root, "docs", "A00560_JaliBatch.md"),
                      os.path.join(os.path.dirname(os.path.dirname(root)), "docs", "A00560_JaliBatch.md")):
        if os.path.isfile(candidate):
            return candidate
    return candidate
