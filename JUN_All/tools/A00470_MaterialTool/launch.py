# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-21
# A00470_MaterialTool - launch entry point (Qt)
#
# 리스트업한 메시에 붙은 머티리얼을 모아, 이름이 프로파일(JSON)에 적힌 명명 규칙을
# 지키는지 진단하는 in-Maya PySide 툴.

import sys, os

# 이 툴은 두 가지 배치에서 똑같이 돌아야 한다.
#
#   dev 트리  : JUN_All/tools/A00470_MaterialTool  - Framework · config.py · dev/ 가 JUN_All 에 있다
#   릴리즈본  : <repo>/tools/A00470_MaterialTool   - Framework 는 툴 폴더 안에 동봉되고,
#                                                    config.py 와 dev/ 는 아예 없다
#
# 그래서 경로는 "있는 것"을 보고 정한다. 하드코딩한 ../.. 하나만 믿으면 릴리즈본에서
# `No module named 'config'` 로 죽는다.

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))          # .../tools/A00470_MaterialTool

# tools 패키지를 담은 폴더 (dev: JUN_All, 릴리즈: 저장소 루트)
ROOT = os.path.abspath(
    os.path.join(
        TOOL_ROOT,
        "..",
        ".."
    )
)

# 툴 폴더 안에 Framework 가 동봉돼 있으면 릴리즈본이다.
IS_RELEASE = os.path.isdir(os.path.join(TOOL_ROOT, "Framework"))

# Framework 가 실제로 있는 곳과, tools 패키지 루트를 둘 다 올린다.
for _path in ((TOOL_ROOT, ROOT) if IS_RELEASE else (ROOT,)):
    if _path not in sys.path:
        sys.path.append(_path)


if IS_RELEASE:
    # 릴리즈본에는 JUN_All/config.py 도 dev/reloader_v02 도 없다.
    # 리로드는 개발 트리에서만 쓰는 기능이므로 끄고 그냥 연다.
    DEV_MODE = False
else:
    import config as jun_config                                 # JUN_All/config.py
    DEV_MODE = bool(getattr(jun_config, "DEV_MODE", False))

from Framework.themes.theme_manager import ThemeManager


window_instance = None


def run(reload_module=True):
    """UI 실행 진입점.

    reload_module=True 이고 DEV_MODE 면 패키지 트리를 리로드한 뒤 실행한다.
    셸프 버튼은 run(True) 로 호출된다.
    """

    global window_instance

    if reload_module and DEV_MODE:
        # 자기 자신 + Framework 만 reload (다른 툴 창 닫힘 방지).
        # dev/ 는 릴리즈본에 없다 - DEV_MODE 가 꺼져 있으므로 여기까지 오지 않는다.
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00470_MaterialTool")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import.
    from tools.A00470_MaterialTool.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
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

    ThemeManager.load_theme_to_widget(window_instance, "teal_dark")

    window_instance.show()

    return window_instance
