# Python Script by Ji Hun Park
# last Update date : 2026-06-15
# A00180_abSymMesh - launch entry point (Qt)
#
# Brendan Ross 의 abSymMesh(origin.mel)를 Python/OpenMaya 2.0 으로 재구현한 뒤
# UI 를 PySide(Qt)로 재작업한 버전. 로직은 app/core 가 담당.

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
    """UI 실행 진입점. reload_module=True 이고 DEV_MODE 면 자기 자신 + Framework 를 reload."""

    global window_instance

    if reload_module and getattr(jun_config, "DEV_MODE", False):
        # 전체 tools reload 는 다른 툴 창을 닫으므로 자기 자신 + Framework 만 reload 한다.
        from dev.reloader_v02 import reload_for_tool
        reload_for_tool("tools.A00180_abSymMesh")

    # 리로드 후 갱신된 클래스를 잡기 위해 지역 import.
    from tools.A00180_abSymMesh.app.ui.main_window import MainWindow, WINDOW_OBJECT_NAME
    from tools.A00180_abSymMesh.app.core import mesh_io
    from Framework.qt.qt import QApplication

    # undo 커맨드 플러그인 로드(실패해도 창은 뜬다; 실제 편집 직전 재시도).
    try:
        mesh_io.ensure_undo_plugin()
    except Exception as exc:
        print("[A00180_abSymMesh] undo plugin load deferred: {0}".format(exc))

    # 기존 인스턴스 정리: objectName 으로 떠 있는 창을 모두 닫는다.
    for w in QApplication.topLevelWidgets():
        if w.objectName() == WINDOW_OBJECT_NAME:
            try:
                w.close()
                w.deleteLater()
            except:
                pass

    window_instance = MainWindow()

    ThemeManager.load_theme_to_widget(window_instance, "yellow_dark")

    window_instance.show()

    return window_instance
