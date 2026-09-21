# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00240_PathTool - standalone launch entry point
#
# Maya 없이 Windows 에서 독립 실행되는 PySide 앱.
#   python launch.py        (개발 실행)
#   build_exe.bat           (PyInstaller exe 빌드)

import sys, os

# dev 트리와 릴리즈본은 배치가 다르다 - 경로는 "있는 것"을 보고 정한다.
#   dev 트리 : Framework 가 JUN_All 에 있고 모든 툴이 공유한다
#   릴리즈본 : Framework 는 툴 폴더 안에 동봉된다
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

# 툴마다 고유한 패키지 경로(tools.<tool>.app...)로 import 한다.
# 모든 standalone Qt 툴이 똑같이 최상위 `app` 으로 import 하면 한 인터프리터
# (예: Maya·공용 런처)에서 두 툴을 동시에 띄울 때 sys.modules['app'] 가 충돌한다.
from Framework.qt.qt import QApplication, QIcon

from tools.A00240_PathTool.app.ui.main_window import MainWindow
from tools.A00240_PathTool.app.config.app_meta import APP_USER_MODEL_ID, icon_path
from Framework.themes.theme_manager import ThemeManager


def _set_windows_app_id():
    """Windows 작업표시줄이 python.exe 아이콘 대신 이 앱의 아이콘을 쓰도록 AppUserModelID 지정.

    터미널에서 `python launch.py` 로 실행하면 프로세스가 python.exe 라, 이 ID 를 명시하지
    않으면 작업표시줄에 python 아이콘이 뜬다. exe 빌드본에서도 안전하게 그룹핑된다.
    Windows 외 OS 나 호출 실패는 조용히 무시(아이콘만 기본값이 됨).
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def main():

    # QApplication 생성 전에 AppUserModelID 를 잡아야 작업표시줄 아이콘이 올바로 적용된다.
    _set_windows_app_id()

    app = QApplication(sys.argv)

    # 앱 전역 아이콘(작업표시줄 + 창). 멀티 사이즈 .ico 로 또렷하게.
    sIcon = icon_path()
    if sIcon:
        app.setWindowIcon(QIcon(sIcon))

    ThemeManager.load_theme_dev(app, "yellow_mid")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
