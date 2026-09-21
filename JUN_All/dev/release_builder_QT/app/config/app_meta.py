# -*- coding: utf-8 -*-
# app_meta.py - 아이콘 경로 + Windows 작업 표시줄 ID (v01.02)
#
# 이 툴은 터미널에서 `python launch.py` 로도 뜨고 마야 안에서도 뜬다.
# 터미널로 띄우면 프로세스가 `python.exe` 라서, `setWindowIcon` 만으로는 **작업 표시줄에
# 파이썬 아이콘**이 그대로 남는다. 그래서 `QApplication` 을 만들기 **전에**
# AppUserModelID 를 지정한다 — 자세한 배경은 `docs/taskbar_icon_guide.md`.

import os

from Framework.qt.qt import QIcon


#: 작업 표시줄이 이 프로세스를 "파이썬" 이 아니라 이 툴로 묶게 하는 ID.
APP_USER_MODEL_ID = "Junny.MayaPython.ReleaseBuilder"

#: 아이콘 이름(확장자 뺀 것). icon/ 폴더에 .svg / .png / .ico 가 함께 있다.
ICON_STEM = "release_builder_QT"


def icon_dir():
    """<release_builder_QT>/icon 절대 경로."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "icon")


def icon_path(ext="ico"):
    """아이콘 파일 경로. 없으면 None."""
    path = os.path.join(icon_dir(), "{0}.{1}".format(ICON_STEM, ext))

    return path if os.path.exists(path) else None


def window_icon():
    """창에 걸 QIcon. `.ico`(다중 크기) 를 먼저 쓰고 없으면 `.png`. 둘 다 없으면 None."""
    path = icon_path("ico") or icon_path("png")

    if not path:
        return None

    icon = QIcon(path)

    return None if icon.isNull() else icon


def set_app_user_model_id():
    """윈도우에서만 의미가 있다. 실패해도 조용히 넘어간다(아이콘이 전부는 아니다)."""
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID)
        return True
    except Exception:                                       # noqa: BLE001
        return False
