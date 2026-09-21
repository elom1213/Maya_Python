# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00460_ControllerTool - launch entry point (Qt)
#
# 키프레임 애니메이션용 컨트롤러(FK 등)를 생성하는 in-Maya PySide 툴.

import sys, os

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
        ".."
    )
)

# 툴 폴더 안에 Framework 가 동봉돼 있으면 릴리즈본이다.
IS_RELEASE = os.path.isdir(os.path.join(TOOL_ROOT, "Framework"))

# Framework 가 실제로 있는 곳과 tools 패키지 루트를 둘 다 sys.path 에 올린다.
for _path in ((TOOL_ROOT, ROOT) if IS_RELEASE else (ROOT,)):
    if _path not in sys.path:
        sys.path.append(_path)


if IS_RELEASE:
    # 릴리즈본에는 config.py 도 dev/reloader_v02 도 없다 - 리로드 없이 그냥 연다.
    DEV_MODE = False
else:
    import config as jun_config                 # JUN_All/config.py
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
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00460_ControllerTool")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import.
    from tools.A00460_ControllerTool.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
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

    ThemeManager.load_theme_to_widget(window_instance, "brown_dark")

    window_instance.show()

    return window_instance
