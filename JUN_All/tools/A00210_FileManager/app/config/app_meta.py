# Python Script by Ji Hun Park
# last Update date : 2026-07-03
# A00210_FileManager - app metadata (taskbar id + icon path resolver)
#
# 작업표시줄 아이콘/그룹핑에 필요한 AppUserModelID 와, dev(소스) · exe(PyInstaller)
# 양쪽에서 동작하는 아이콘 경로 해석기를 둔다. UI/DCC 비의존.

import os
import sys

# 작업표시줄 아이콘·그룹핑용 고유 ID (역-DNS 형태). 이 값을 프로세스에 지정해야
# 터미널의 python.exe 아이콘 대신 이 앱 아이콘이 작업표시줄에 뜬다.
APP_USER_MODEL_ID = "Dnable.JUN.A00210.FileManager"

_ICON_BASENAME = "A00210_FileManager"


def _tool_root():
    # app/config/app_meta.py → app → tool root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


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
