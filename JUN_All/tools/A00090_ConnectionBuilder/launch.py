import sys, os

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

    global window_instance

    if reload_module and getattr(jun_config, "DEV_MODE", False):
        # 전체 tools reload 는 다른 툴 launch 모듈의 window_instance 전역을 초기화해
        # 떠 있던 다른 툴 창을 닫는다. 자기 자신 + Framework 만 reload 한다.
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00090_ConnectionBuilder")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import
    from tools.A00090_ConnectionBuilder.app.ui.main_window import (
        MainWindow, WINDOW_OBJECT_NAME)
    from Framework.qt.qt import QApplication

    # objectName 으로 떠 있는 기존 창을 모두 닫는다 (창 누적 방지).
    # 전역 window_instance 가 리셋된 뒤(리로드 등)에도 이전 창을 확실히 닫는다.
    for w in QApplication.topLevelWidgets():
        if w.objectName() == WINDOW_OBJECT_NAME:
            try:
                w.close()
                w.deleteLater()
            except:
                pass

    window_instance = MainWindow()

    ThemeManager.load_theme_to_widget(window_instance, "red")

    window_instance.show()

    return window_instance
