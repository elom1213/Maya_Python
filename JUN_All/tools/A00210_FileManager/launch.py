# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - standalone launch entry point
#
# Maya 없이 Windows 에서 독립 실행되는 PySide 앱.
#   python launch.py        (개발 실행)
#   build_exe.bat           (PyInstaller exe 빌드)

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

# 툴마다 고유한 패키지 경로(tools.<tool>.app...)로 import 한다.
# 모든 standalone Qt 툴이 똑같이 최상위 `app` 으로 import 하면 한 인터프리터
# (예: Maya·공용 런처)에서 두 툴을 동시에 띄울 때 sys.modules['app'] 가 충돌한다.
from Framework.qt.qt import QApplication, QIcon

from tools.A00210_FileManager.app.ui.main_window import MainWindow
from tools.A00210_FileManager.app.config.app_meta import APP_USER_MODEL_ID, icon_path
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

    ThemeManager.load_theme_dev(app, "blue_dark")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
