# Python Script by Ji Hun Park
# last Update date : 2026-06-30
# A00330_NamingTool - launch entry point (Qt)
#
# 레거시 JUN_PY_NamingTool_V03_04(maya.cmds) 를 PySide 3-탭 UI 로 이식한 툴.
#   Naming Dyn / Copy Name / Quick Rename(ref_01.mel 이식)

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
    """
    UI 실행 진입점.
    reload_module=True 이고 DEV_MODE 면 패키지 트리를 리로드한 뒤 실행한다.
    셸프 버튼은 run(True) 로 호출된다.
    """

    global window_instance

    if reload_module and getattr(jun_config, "DEV_MODE", False):
        # 자기 자신 + Framework 만 reload (다른 툴 창 닫힘 방지).
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00330_NamingTool")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import (리로드 순서 문제 회피)
    from tools.A00330_NamingTool.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
    from Framework.qt.qt import QApplication

    # 기존 인스턴스 정리 (objectName 으로 떠 있는 창을 모두 찾아 닫는다).
    for w in QApplication.topLevelWidgets():
        if w.objectName() == WINDOW_OBJECT_NAME:
            try:
                w.close()
                w.deleteLater()
            except:
                pass

    window_instance = MainWindow()

    # 레거시 네이밍 툴의 green 정체성을 잇는 테마.
    ThemeManager.load_theme_to_widget(window_instance, "green_dark")

    window_instance.show()

    return window_instance
