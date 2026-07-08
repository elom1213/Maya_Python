# Python Script by Ji Hun Park
# last Update date : 2026-07-08
# A00360_SortTool - launch entry point (Qt)
#
# 선택 오브젝트를 TSL 에 리스트업하고 월드 X/Y/Z 위치 · 이름 · 타입 기준으로 정렬해
# 아웃라이너 순서(위->아래)와 TSL 순서를 함께 바꾸는 in-Maya PySide 툴.

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
    """UI 실행 진입점.

    reload_module=True 이고 DEV_MODE 면 패키지 트리를 리로드한 뒤 실행한다.
    셸프 버튼은 run(True) 로 호출된다.
    """

    global window_instance

    if reload_module and getattr(jun_config, "DEV_MODE", False):
        # 자기 자신 + Framework 만 reload (다른 툴 창 닫힘 방지).
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00360_SortTool")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import.
    from tools.A00360_SortTool.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
    from Framework.qt.qt import QApplication

    # objectName 으로 떠 있는 기존 창을 모두 닫는다 (창 누적 방지).
    for w in QApplication.topLevelWidgets():
        if w.objectName() == WINDOW_OBJECT_NAME:
            try:
                w.close()
                w.deleteLater()
            except:
                pass

    window_instance = MainWindow()

    ThemeManager.load_theme_to_widget(window_instance, "coral_dark")

    window_instance.show()

    return window_instance
