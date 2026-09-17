# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00480_FileTool - launch entry point (Qt)
#
# 파일 입출력 · 경로 툴. A00040_file_exporter_V02(Export 탭) 와
# A00030_quickTool_V02 의 File · Import option 버튼(Path · Import 탭)을 한 창에 모았다.
# 원본 두 툴은 그대로 남아 있다.

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
        reload_for_tool("tools.A00480_FileTool")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import (리로드 순서 문제 회피)
    from tools.A00480_FileTool.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
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

    ThemeManager.load_theme_to_widget(window_instance, "slate_dark")
    # 테마가 글자 크기를 줄이므로 크기는 테마를 입힌 뒤에 맞춘다.
    window_instance.fit_to_theme()

    window_instance.show()

    return window_instance
