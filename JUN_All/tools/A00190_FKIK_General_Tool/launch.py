# Python Script by Ji Hun Park
# last Update date : 2026-06-16
# A00190_FKIK_General_Tool - launch entry point (Qt)
#
# 레거시 maya.cmds 툴(JUN_PY_FKIK_General_Tool_V01_02.py)을 PySide(Qt)로 리팩토링한 버전.
# 로직은 app/core 가 담당하고, UI 는 app/ui/main_window.py 가 담당한다.

import sys, os

# JUN_All 루트를 sys.path 에 추가 (Framework / tools 패키지 import 용)
ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

if ROOT not in sys.path:
    sys.path.append(ROOT)


import config as jun_config
from Framework.themes.theme_manager import ThemeManager


window_instance = None


def run(reload_module=True):
    """UI 실행 진입점. reload_module=True 이고 DEV_MODE 면 자기 자신 + Framework 를 reload."""

    global window_instance

    if reload_module and getattr(jun_config, "DEV_MODE", False):
        # 전체 tools reload 는 다른 툴 창을 닫으므로 자기 자신 + Framework 만 reload 한다.
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00190_FKIK_General_Tool")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import.
    from tools.A00190_FKIK_General_Tool.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
    from Framework.qt.qt import QApplication

    # 기존 인스턴스 정리: objectName 으로 떠 있는 창을 모두 닫는다.
    for w in QApplication.topLevelWidgets():
        if w.objectName() == WINDOW_OBJECT_NAME:
            try:
                w.close()
                w.deleteLater()
            except:
                pass

    window_instance = MainWindow()

    ThemeManager.load_theme_to_widget(window_instance, "blue_dark")

    window_instance.show()

    return window_instance
