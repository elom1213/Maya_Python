# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00211_RefLineage - launch entry point (Maya 내 PySide)
#
# 셸프 버튼은 tools.A00211_RefLineage.run(True) 를 호출한다.

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
    """UI 실행 진입점. reload_module=True 이고 DEV_MODE 면 자기 패키지+Framework reload 후 실행."""

    global window_instance

    if reload_module and getattr(jun_config, "DEV_MODE", False):
        # 자기 자신 + Framework 만 reload (다른 툴 창은 건드리지 않음).
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00211_RefLineage")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import.
    from tools.A00211_RefLineage.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
    from Framework.qt.qt import QApplication

    # objectName 으로 떠 있는 창을 모두 닫아 중복 누적을 막는다.
    for w in QApplication.topLevelWidgets():
        if w.objectName() == WINDOW_OBJECT_NAME:
            try:
                w.close()
                w.deleteLater()
            except:
                pass

    window_instance = MainWindow()

    # A00210_FileManager 계열과 같은 테마.
    ThemeManager.load_theme_to_widget(window_instance, "blue_dark")

    window_instance.show()

    return window_instance
