# -*- coding: utf-8 -*-
"""
Spherical Eye Tool - 런처.

Maya 안에서 PySide 윈도우를 띄운다. 사용 예 (Maya Script Editor):
    from JUN_All.tools.A00160_sphericalEye import run
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

from .app.ui.main_window import MainWindow


window_instance = None


def run(reload_module=True):
    global window_instance

    try:
        window_instance.close()
        window_instance.deleteLater()
    except Exception:
        pass

    window_instance = MainWindow()
    ThemeManager.load_theme_to_widget(window_instance, "green_dark")
    window_instance.show()
    return window_instance
