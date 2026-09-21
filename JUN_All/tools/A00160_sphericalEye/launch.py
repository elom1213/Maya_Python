# -*- coding: utf-8 -*-
"""
Spherical Eye Tool - 런처.

Maya 안에서 PySide 윈도우를 띄운다. 사용 예 (Maya Script Editor):
    from tools.A00160_sphericalEye import run
    run(True)
"""

import sys
import os

# dev 트리와 릴리즈본은 배치가 다르다 - 경로는 "있는 것"을 보고 정한다.
#   dev 트리 : Framework · config.py · dev/ 가 JUN_All 에 있고 모든 툴이 공유한다
#   릴리즈본 : Framework 는 툴 폴더 안에 동봉되고, config.py 와 dev/ 는 실리지 않는다
# 자세한 것은 docs/Release_Layout.md
TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))

# tools 패키지를 담은 폴더 (dev: JUN_All, 릴리즈: 저장소 루트)
ROOT = os.path.abspath(
    os.path.join(
        TOOL_ROOT,
        "..",
        "..",
    )
)

# 툴 폴더 안에 Framework 가 동봉돼 있으면 릴리즈본이다.
IS_RELEASE = os.path.isdir(os.path.join(TOOL_ROOT, "Framework"))

# Framework 가 실제로 있는 곳과 tools 패키지 루트를 둘 다 sys.path 에 올린다.
for _path in ((TOOL_ROOT, ROOT) if IS_RELEASE else (ROOT,)):
    if _path not in sys.path:
        sys.path.append(_path)

from Framework.qt.qt import *  # noqa: F401,F403
from Framework.themes.theme_manager import ThemeManager

if IS_RELEASE:
    # 릴리즈본에는 config.py 도 dev/reloader_v02 도 없다 - 리로드 없이 그냥 연다.
    DEV_MODE = False
else:
    import config as jun_config                 # JUN_All/config.py
    DEV_MODE = bool(getattr(jun_config, "DEV_MODE", False))


window_instance = None


def run(reload_module=True):
    global window_instance

    if reload_module and DEV_MODE:
        # 전체 tools reload 는 다른 툴 launch 모듈의 window_instance 전역을 초기화해
        # 떠 있던 다른 툴 창을 닫는다. 자기 자신 + Framework 만 reload 한다.
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00160_sphericalEye")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import
    from tools.A00160_sphericalEye.app.ui.main_window import MainWindow

    try:
        window_instance.close()
        window_instance.deleteLater()
    except Exception:
        pass

    window_instance = MainWindow()
    ThemeManager.load_theme_to_widget(window_instance, "teal_dark")
    window_instance.show()
    return window_instance
