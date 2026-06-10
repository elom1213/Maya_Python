# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00120_FKIK - launch entry point (Qt)

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
        from dev.reloader_v02 import reload_all_v02
        reload_all_v02()

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import (리로드 순서 문제 회피)
    from tools.A00120_FKIK.app.ui.main_window import MainWindow

    try:
        window_instance.close()
        window_instance.deleteLater()
    except:
        pass

    window_instance = MainWindow()

    ThemeManager.load_theme_to_widget(window_instance, "red")

    window_instance.show()

    return window_instance
