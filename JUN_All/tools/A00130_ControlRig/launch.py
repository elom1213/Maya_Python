# -*- coding: utf-8 -*-
"""
Control Rig Tool - 런처.

Maya 안에서 PySide 윈도우를 띄운다. 사용 예 (Maya Script Editor):
    from JUN_All.tools.A00130_ControlRig import run
    run(True)
"""

import sys
import os

ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

if ROOT not in sys.path:
    sys.path.append(ROOT)

from Framework.qt.qt import *  # noqa: F401,F403
from Framework.themes.theme_manager import ThemeManager

import config as jun_config


window_instance = None


def run(reload_module=True):
    global window_instance

    if reload_module and getattr(jun_config, "DEV_MODE", False):
        # 전체 tools reload 는 다른 툴 launch 모듈의 window_instance 전역을 초기화해
        # 떠 있던 다른 툴 창을 닫는다. 자기 자신 + Framework 만 reload 한다.
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00130_ControlRig")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import
    from tools.A00130_ControlRig.app.ui.main_window import MainWindow

    try:
        window_instance.close()
        window_instance.deleteLater()
    except Exception:
        pass

    window_instance = MainWindow()
    ThemeManager.load_theme_to_widget(window_instance, "coral_dark")
    window_instance.show()
    return window_instance
