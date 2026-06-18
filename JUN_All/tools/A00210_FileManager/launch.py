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
from Framework.qt.qt import QApplication

from tools.A00210_FileManager.app.ui.main_window import MainWindow
from Framework.themes.theme_manager import ThemeManager


def main():

    app = QApplication(sys.argv)

    ThemeManager.load_theme_dev(app, "blue_dark")

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
