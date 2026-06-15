# Python Script by Ji Hun Park
# last Update date : 2026-06-11
# A00110_animTool - launch entry point (Qt)

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
        # 전체 tools reload 는 다른 툴 launch 모듈의 window_instance 전역을 초기화해
        # 떠 있던 다른 툴 창을 닫는다. 자기 자신 + Framework 만 reload 한다.
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00110_animTool")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import (리로드 순서 문제 회피)
    from tools.A00110_animTool.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
    from Framework.qt.qt import QApplication

    # 기존 인스턴스 정리.
    # reload 시 모듈 전역 window_instance 가 None 으로 초기화되므로 그것에 의존하지 않고
    # objectName 으로 떠 있는 창을 모두 찾아 닫는다 (창이 여러 개 쌓이는 문제 방지).
    for w in QApplication.topLevelWidgets():
        if w.objectName() == WINDOW_OBJECT_NAME:
            try:
                # 닫기 전에 Shift+A 핫키 복원 (closeEvent 도 호출하지만 안전망, idempotent)
                if hasattr(w, "hotkey_mgr"):
                    w.hotkey_mgr.restore()
                w.close()
                w.deleteLater()
            except:
                pass

    window_instance = MainWindow()

    ThemeManager.load_theme_to_widget(window_instance, "coral_dark")

    window_instance.show()

    return window_instance
