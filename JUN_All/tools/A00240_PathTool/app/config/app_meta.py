# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# A00240_PathTool - app metadata (taskbar id + icon path resolver)
#
# 작업표시줄 아이콘/그룹핑에 필요한 AppUserModelID 와, dev(소스) · exe(PyInstaller)
# 양쪽에서 동작하는 아이콘 경로 해석기를 둔다. UI/DCC 비의존.
# (방식: docs/taskbar_icon_guide.md)
# 시작 메뉴 바로가기(File > Add to Start Menu)가 쓰는 앱 이름 · 실행 명령도 여기서 준다
# (공용 Framework/core/shell_integration.py, docs/Framework_shell_integration.md).

import os
import sys

# 작업표시줄 아이콘·그룹핑용 고유 ID (역-DNS 형태). 이 값을 프로세스에 지정해야
# 터미널의 python.exe 아이콘 대신 이 앱 아이콘이 작업표시줄에 뜬다.
APP_USER_MODEL_ID = "Dnable.JUN.A00240.PathTool"

# 시작 메뉴 바로가기 이름(= 시작 메뉴 · 검색에 보이는 앱 이름)과 바로가기 설명.
APP_NAME = "JUN Path Tool"
APP_DESCRIPTION = "JUN Path Tool - path shortcuts, folder tree and junctions"

_ICON_BASENAME = "A00240_PathTool"


def _tool_root():
    # app/config/app_meta.py → app → tool root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def tool_root():
    """툴 루트 폴더(launch.py 가 있는 곳)의 절대경로."""
    return _tool_root()


def start_menu_launch_spec():
    """시작 메뉴 바로가기가 실행할 명령(공용 shell_integration.LaunchSpec).

    dev 실행이면 pythonw.exe + launch.py, PyInstaller exe 면 exe 자신. 아이콘은 .ico.
    Framework 는 launch.py 가 sys.path 를 잡은 뒤에만 import 되므로 여기서 lazy import 한다.
    """
    from Framework.core import shell_integration
    return shell_integration.launch_spec(tool_root(), icon_path())


def icon_path(prefer_ico=True):
    """존재하는 아이콘 파일의 절대경로를 반환(없으면 빈 문자열).

    Windows 작업표시줄엔 멀티 사이즈 .ico 가 가장 또렷해 기본으로 우선한다.
    dev 실행은 tool/icon/ 에서, PyInstaller exe 는 번들 임시경로(_MEIPASS)에서 찾는다.
    """
    exts = ("ico", "png") if prefer_ico else ("png", "ico")

    bases = [os.path.join(_tool_root(), "icon")]
    # PyInstaller onefile 은 add-data 로 넣은 파일을 _MEIPASS 아래에 푼다.
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            bases.insert(0, os.path.join(meipass, "icon"))
            bases.insert(1, meipass)

    for base in bases:
        for ext in exts:
            candidate = os.path.join(base, "%s.%s" % (_ICON_BASENAME, ext))
            if os.path.isfile(candidate):
                return candidate
    return ""
